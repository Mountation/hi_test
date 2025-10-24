from pydantic import BaseModel, ConfigDict
from typing import Optional


class EvalDataBase(BaseModel):
    eval_set_id: int
    corpus_id: Optional[int] = None
    content: str
    expected: Optional[str] = None
    intent: Optional[str] = None


class EvalDataCreate(EvalDataBase):
    pass


class EvalData(EvalDataBase):
    id: int
    deleted: bool
    # Pydantic v2 config: allow creation from ORM objects
    model_config = ConfigDict(from_attributes=True)


class EvalDataUpdate(BaseModel):
    content: Optional[str] = None
    expected: Optional[str] = None
    intent: Optional[str] = None
