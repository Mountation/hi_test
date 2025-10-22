from pydantic import BaseModel
from typing import Optional


class EvalDataBase(BaseModel):
    eval_set_id: int
    content: str
    expected: Optional[str] = None
    intent: Optional[str] = None


class EvalDataCreate(EvalDataBase):
    pass


class EvalData(EvalDataBase):
    id: int
    deleted: bool

    class Config:
        orm_mode = True
