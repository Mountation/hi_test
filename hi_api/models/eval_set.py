from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EvalSetBase(BaseModel):
    name: str
    count: Optional[int] = 0


class EvalSetCreate(EvalSetBase):
    pass


class EvalSet(EvalSetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted: bool

    class Config:
        orm_mode = True


class EvalSetUpdate(BaseModel):
    name: Optional[str] = None

