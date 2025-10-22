from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services import eval_result_service
from models import EvalResultCreate, EvalResult
from db.sqlalchemy import SessionLocal
from db.models import EvalData as EvalDataORM
from utils.client import AIClient
from utils.scoring import score_answer
import asyncio
from pydantic import BaseModel
from services.eval_data_service import eval_data_service
from datetime import datetime
from config.settings import settings
from utils.log import get_logger

logger = get_logger("eval_results_api")

router = APIRouter(prefix="/api/v1/evalresults", tags=["evalresults"])


@router.post("/", response_model=EvalResult)
def create_eval_result(payload: EvalResultCreate):
    """创建评测结果"""
    return eval_result_service.create_result(payload)


@router.get("/byset/{eval_set_id}", response_model=List[EvalResult])
def list_results_by_set(eval_set_id: int):
    """按评测集ID列出结果"""
    return eval_result_service.list_by_eval_set(eval_set_id)


@router.get("/bydata/{eval_data_id}", response_model=List[EvalResult])
def list_results_by_data(eval_data_id: int, eval_set_id: Optional[int] = Query(None)):
    """按评测数据ID（现在为 corpus_id）列出结果。
    如果提供 query 参数 eval_set_id，则按 (eval_set_id, corpus_id) 查询；
    否则在结果表中以 corpus_id 跨所有评测集进行匹配（不建议在存在重复 corpus_id 的场景下使用）。
    """
    if eval_set_id is not None:
        # 查询指定评测集下 corpus_id 的结果
        return eval_result_service.list_by_eval_data_with_set(eval_set_id, eval_data_id)
    return eval_result_service.list_by_eval_data(eval_data_id)


@router.get("/{id}", response_model=EvalResult)
def get_eval_result(id: int):
    """获取单个评测结果"""
    r = eval_result_service.get_result(id)
    if not r:
        raise HTTPException(status_code=404, detail="评测结果不存在")
    return r


@router.delete("/{id}")
def delete_eval_result(id: int):
    """删除评测结果（软删除）"""
    ok = eval_result_service.delete_result(id)
    if not ok:
        raise HTTPException(status_code=404, detail="评测结果不存在或已删除")
    return {"success": True}


class ExecPayload(BaseModel):
    eval_data_id: int
    agent_version: Optional[str] = None


@router.post("/execute", response_model=EvalResult, summary="执行评测（异步获取答案/意图/知识库/评分）")
async def execute_eval(payload: ExecPayload):
    with SessionLocal() as session:
        data = session.get(EvalDataORM, payload.eval_data_id)
        if not data or data.deleted:
            raise HTTPException(status_code=404, detail="评测数据不存在")
        eval_set_id = data.eval_set_id
        content = data.content
        expected = data.expected

    client = AIClient()
    # 并发调用（答案/意图/知识库 + 同步获取agent信息放在线程池）
    loop = asyncio.get_running_loop()
    timeout = getattr(settings, 'external_call_timeout_seconds', 60)
    ans_task = asyncio.create_task(client.aget_answer(content))
    intent_task = asyncio.create_task(client.aget_intent(content))
    kdb_task = asyncio.create_task(client.ais_Kdb(content))
    info_task = loop.run_in_executor(None, client.get_agent_info)
    try:
        answer, intent, kdb_flag, agent_info = await asyncio.wait_for(
            asyncio.gather(ans_task, intent_task, kdb_task, info_task), timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"execute_eval timed out after {timeout}s for eval_data_id={payload.eval_data_id}")
        raise HTTPException(status_code=504, detail="evaluation timed out")
    except Exception as e:
        logger.exception(f"execute_eval failed for eval_data_id={payload.eval_data_id}: {e}")
        raise HTTPException(status_code=500, detail="evaluation failed")

    # 解析 agent 版本信息，优先 version 字段，不存在则存整个JSON字符串
    agent_version_value = None
    if agent_info:
        if isinstance(agent_info, dict):
            agent_version_value = agent_info.get('version') or agent_info.get('agent_version') or None
            if agent_version_value is None:
                import json as _json
                agent_version_value = _json.dumps(agent_info, ensure_ascii=False)
        else:
            agent_version_value = str(agent_info)

    # scoring may be blocking, run in executor and protect with timeout
    try:
        score = await loop.run_in_executor(None, lambda: score_answer(answer, expected))
    except Exception as e:
        logger.exception(f"scoring failed for eval_data_id={payload.eval_data_id}: {e}")
        score = 0

    create_payload = EvalResultCreate(
        eval_set_id=eval_set_id,
        # store corpus_id (评测集内的序号) in eval_results.eval_data_id per new requirement
        eval_data_id=data.corpus_id,
        actual_result=answer,
        actual_intent=intent,
        score=score,
        agent_version=payload.agent_version or agent_version_value,
        kdb=kdb_flag,
        exec_time=datetime.utcnow(),
    )
    return eval_result_service.create_result(create_payload)


class BatchExecResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    result_ids: List[int]
    errors: List[str]
    durations_ms: List[float]  # 每条记录耗时（毫秒）对应 result_ids 顺序或错误发生的条目位置


class MultiSetExecPayload(BaseModel):
    eval_set_ids: List[int]
    # 兼容旧字段但不再使用内部并发，保持向后兼容
    concurrency: Optional[int] = None
    global_concurrency: Optional[int] = None  # 若提供仍可限制评测集并发，否则=评测集数量


class MultiSetExecSetResult(BaseModel):
    eval_set_id: int
    total: int
    succeeded: int
    failed: int
    result_ids: List[int]
    errors: List[str]
    durations_ms: List[float]


class MultiSetExecResponse(BaseModel):
    sets: List[MultiSetExecSetResult]
    overall_total: int
    overall_succeeded: int
    overall_failed: int


@router.post("/execute/byset/{eval_set_id}", response_model=BatchExecResponse, summary="批量执行评测集内所有评测数据")
async def batch_execute_eval_set(eval_set_id: int):
    """对指定评测集的所有未删除评测数据执行评测，采用并发方式。"""
    # 获取所有评测数据
    data_items = eval_data_service.list_by_eval_set(eval_set_id)
    if not data_items:
        return BatchExecResponse(total=0, succeeded=0, failed=0, result_ids=[], errors=[])

    client = AIClient()
    loop = asyncio.get_running_loop()
    # 仅获取一次 agent 信息
    agent_info = await loop.run_in_executor(None, client.get_agent_info)
    agent_version_value = None
    if agent_info:
        if isinstance(agent_info, dict):
            agent_version_value = agent_info.get('version') or agent_info.get('agent_version') or None
            if agent_version_value is None:
                import json as _json
                agent_version_value = _json.dumps(agent_info, ensure_ascii=False)
        else:
            agent_version_value = str(agent_info)

    semaphore = asyncio.Semaphore(3)  # 并发限制，避免压垮外部服务
    result_ids: List[int] = []
    errors: List[str] = []
    durations: List[float] = []

    async def process_item(item):
        async with semaphore:
            try:
                import time
                start = time.perf_counter()
                ans_task = asyncio.create_task(client.aget_answer(item.content))
                intent_task = asyncio.create_task(client.aget_intent(item.content))
                kdb_task = asyncio.create_task(client.ais_Kdb(item.content))
                timeout = getattr(settings, 'external_call_timeout_seconds', 60)
                try:
                    answer, intent, kdb_flag = await asyncio.wait_for(
                        asyncio.gather(ans_task, intent_task, kdb_task), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError(f"item eval timed out after {timeout}s")
                # run scoring in executor
                score = await loop.run_in_executor(None, lambda: score_answer(answer, item.expected))
                create_payload = EvalResultCreate(
                    eval_set_id=item.eval_set_id,
                    # store corpus_id instead of global id
                    eval_data_id=item.corpus_id,
                    actual_result=answer,
                    actual_intent=intent,
                    score=score,
                    agent_version=agent_version_value,
                    kdb=kdb_flag,
                    exec_time=datetime.utcnow(),
                )
                res = eval_result_service.create_result(create_payload)
                result_ids.append(res.id)
                end = time.perf_counter()
                durations.append((end - start) * 1000)
            except Exception as e:
                logger.exception(f"process_item failed eval_data_id={item.id}: {e}")
                errors.append(f"eval_data_id={item.id}: {e}")

    await asyncio.gather(*[process_item(d) for d in data_items])

    return BatchExecResponse(
        total=len(data_items),
        succeeded=len(result_ids),
        failed=len(errors),
        result_ids=result_ids,
        errors=errors,
        durations_ms=durations,
    )


@router.post("/execute/bysets", response_model=MultiSetExecResponse, summary="同时执行多个评测集")
async def batch_execute_multiple_sets(payload: MultiSetExecPayload):
    """对多个评测集的全部评测数据进行并发评测。每个评测集内部使用单独的并发限制。"""
    if not payload.eval_set_ids:
        return MultiSetExecResponse(sets=[], overall_total=0, overall_succeeded=0, overall_failed=0)

    client = AIClient()
    loop = asyncio.get_running_loop()
    agent_info = await loop.run_in_executor(None, client.get_agent_info)
    agent_version_value = None
    if agent_info:
        if isinstance(agent_info, dict):
            agent_version_value = agent_info.get('version') or agent_info.get('agent_version') or None
            if agent_version_value is None:
                import json as _json
                agent_version_value = _json.dumps(agent_info, ensure_ascii=False)
        else:
            agent_version_value = str(agent_info)

    per_set_results: List[MultiSetExecSetResult] = []

    async def run_set(sid: int):
        items = eval_data_service.list_by_eval_set(sid)
        if not items:
            per_set_results.append(MultiSetExecSetResult(eval_set_id=sid, total=0, succeeded=0, failed=0, result_ids=[], errors=[], durations_ms=[]))
            return
        result_ids: List[int] = []
        errors: List[str] = []
        durations: List[float] = []
        for it in items:
            try:
                import time
                start = time.perf_counter()
                ans_task = asyncio.create_task(client.aget_answer(it.content))
                intent_task = asyncio.create_task(client.aget_intent(it.content))
                kdb_task = asyncio.create_task(client.ais_Kdb(it.content))
                timeout = getattr(settings, 'external_call_timeout_seconds', 60)
                try:
                    answer, intent, kdb_flag = await asyncio.wait_for(
                        asyncio.gather(ans_task, intent_task, kdb_task), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError(f"item eval timed out after {timeout}s")
                score = await loop.run_in_executor(None, lambda: score_answer(answer, it.expected))
                create_payload = EvalResultCreate(
                    eval_set_id=it.eval_set_id,
                    eval_data_id=it.corpus_id,
                    actual_result=answer,
                    actual_intent=intent,
                    score=score,
                    agent_version=agent_version_value,
                    kdb=kdb_flag,
                    exec_time=datetime.utcnow(),
                )
                res = eval_result_service.create_result(create_payload)
                result_ids.append(res.id)
                end = time.perf_counter()
                durations.append((end - start) * 1000)
            except Exception as e:
                errors.append(f"eval_set_id={sid} eval_data_id={it.id}: {e}")
        per_set_results.append(MultiSetExecSetResult(
            eval_set_id=sid,
            total=len(items),
            succeeded=len(result_ids),
            failed=len(errors),
            result_ids=result_ids,
            errors=errors,
            durations_ms=durations,
        ))

    # 评测集并发：如果提供 global_concurrency 则限制，否则等于评测集数量（全部并发）
    if payload.global_concurrency and payload.global_concurrency > 0:
        set_semaphore = asyncio.Semaphore(payload.global_concurrency)

        async def guarded_run(sid: int):
            async with set_semaphore:
                await run_set(sid)

        await asyncio.gather(*[guarded_run(sid) for sid in payload.eval_set_ids])
    else:
        await asyncio.gather(*[run_set(sid) for sid in payload.eval_set_ids])
