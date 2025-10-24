from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from models.eval_data import EvalData
from services.eval_data_service import eval_data_service
from services.eval_set_service import eval_set_service
from models.eval_data import EvalDataCreate
from fastapi import Body
from models.eval_data import EvalDataUpdate

router = APIRouter()


@router.get("/evalsets/{id}/data")
def list_eval_data(
    id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, description="搜索文本，可跨字段匹配 content/expected/intent"),
    global_search: bool = Query(False, description="若为 true 则忽略 path 中的 evalset id，跨所有评测集搜索")
) -> Dict[str, Any]:
    # 如果是全局搜索，则不校验 eval set 存在性
    if not global_search:
        if not eval_set_service.get_eval_set(id):
            raise HTTPException(status_code=404, detail="Eval set not found")
    # 当提供 q 时在服务端进行过滤并分页；global_search 控制是否跨表
    if global_search:
        items, total = eval_data_service.list_all_search_paginated(q=q, page=page, page_size=page_size)
    else:
        items, total = eval_data_service.list_by_eval_set_paginated(id, page=page, page_size=page_size, q=q)
    return {"items": items, "total": total}


@router.get("/evalsets/{id}/data/{dataid}", response_model=EvalData)
def get_eval_data(id: int, dataid: int):
    data = eval_data_service.get_eval_data(dataid)
    if not data or data.eval_set_id != id:
        raise HTTPException(status_code=404, detail="Eval data not found for this eval set")
    return data


@router.post("/evalsets/{id}/data", response_model=EvalData)
def create_eval_data(id: int, payload: EvalDataCreate = Body(...)):
    # 确认评测集存在
    if not eval_set_service.get_eval_set(id):
        raise HTTPException(status_code=404, detail="Eval set not found")
    # 确保请求体中的 eval_set_id 与路径 id 一致（或覆盖为路径 id）
    if payload.eval_set_id != id:
        # 覆盖为路径 id，确保关联一致
        payload.eval_set_id = id
    return eval_data_service.create_eval_data(payload)


@router.delete("/evalsets/{id}/data/{dataid}", status_code=204)
def delete_eval_data(id: int, dataid: int):
    # 确认数据存在并属于该评测集
    data = eval_data_service.get_eval_data(dataid)
    if not data or data.eval_set_id != id:
        raise HTTPException(status_code=404, detail="Eval data not found for this eval set")
    ok = eval_data_service.delete_eval_data(dataid)
    if not ok:
        raise HTTPException(status_code=404, detail="Eval data not found")
    return None


@router.patch("/evalsets/{id}/data/{dataid}", response_model=EvalData)
def patch_eval_data(id: int, dataid: int, payload: EvalDataUpdate = Body(...)):
    # confirm data exists and belongs to set
    data = eval_data_service.get_eval_data(dataid)
    if not data or data.eval_set_id != id:
        raise HTTPException(status_code=404, detail="Eval data not found for this eval set")
    updated = eval_data_service.update_eval_data(dataid, content=payload.content, expected=payload.expected, intent=payload.intent)
    if not updated:
        raise HTTPException(status_code=404, detail="Failed to update eval data")
    return updated
