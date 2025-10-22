from fastapi import APIRouter, HTTPException
from typing import List
from models.eval_data import EvalData
from services.eval_data_service import eval_data_service
from services.eval_set_service import eval_set_service
from models.eval_data import EvalDataCreate
from fastapi import Body

router = APIRouter()


@router.get("/evalsets/{id}/data", response_model=List[EvalData])
def list_eval_data(id: int):
    # 确认评测集存在
    if not eval_set_service.get_eval_set(id):
        raise HTTPException(status_code=404, detail="Eval set not found")
    return eval_data_service.list_by_eval_set(id)


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
