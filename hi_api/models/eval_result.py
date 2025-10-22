from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EvalResultBase(BaseModel):
    eval_set_id: int
    eval_data_id: int
    actual_result: Optional[str] = None
    actual_intent: Optional[str] = None  # 实际意图
    score: Optional[int] = None
    agent_version: Optional[str] = None
    kdb: int = 0  # 0 否 1 是


class EvalResultCreate(EvalResultBase):
    exec_time: Optional[datetime] = None  # 允许显式传入执行完成时间


class EvalResult(EvalResultBase):
    id: int
    exec_time: datetime
    deleted: bool

    class Config:
        orm_mode = True
