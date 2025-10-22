from typing import List, Optional
from db.models import EvalData as EvalDataORM
from models.eval_data import EvalDataCreate, EvalData
from db.sqlalchemy import SessionLocal
from services.eval_set_service import eval_set_service

from utils.log import get_logger

logger = get_logger("eval_data_service")


class EvalDataService:
    def create_eval_data(self, payload: EvalDataCreate) -> EvalData:
        logger.info(f"create_eval_data called for set={payload.eval_set_id}")
        with SessionLocal() as session:
            # compute next corpus_id within the eval_set (start from 1)
            try:
                max_corpus = session.query(EvalDataORM).filter(EvalDataORM.eval_set_id == payload.eval_set_id).order_by(EvalDataORM.corpus_id.desc()).with_entities(EvalDataORM.corpus_id).first()
                next_corpus_id = 1
                if max_corpus and max_corpus[0] is not None:
                    next_corpus_id = int(max_corpus[0]) + 1
            except Exception:
                next_corpus_id = 1

            obj = EvalDataORM(eval_set_id=payload.eval_set_id, corpus_id=next_corpus_id, content=payload.content, expected=payload.expected, intent=payload.intent)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            # 刷新所属评测集的 count
            try:
                eval_set_service.refresh_count(payload.eval_set_id)
            except Exception as e:
                logger.warning(f"refresh_count failed for set={payload.eval_set_id}: {e}")
            logger.info(f"eval_data created id={obj.id} for set={payload.eval_set_id}")
            return EvalData.model_validate(obj, from_attributes=True)

    def list_by_eval_set(self, eval_set_id: int) -> List[EvalData]:
        logger.info(f"list_by_eval_set called for set={eval_set_id}")
        with SessionLocal() as session:
            rows = session.query(EvalDataORM).filter(EvalDataORM.eval_set_id == eval_set_id, EvalDataORM.deleted == False).all()
            logger.info(f"list_by_eval_set: found {len(rows)} rows for set={eval_set_id}")
            return [EvalData.model_validate(r, from_attributes=True) for r in rows]

    def get_eval_data(self, id: int) -> Optional[EvalData]:
        logger.info(f"get_eval_data called id={id}")
        with SessionLocal() as session:
            r = session.get(EvalDataORM, id)
            if not r or r.deleted:
                logger.warning(f"get_eval_data: id={id} not found or deleted")
                return None
            logger.info(f"get_eval_data: id={id} found for set={r.eval_set_id}")
            return EvalData.model_validate(r, from_attributes=True)

    def delete_eval_data(self, id: int) -> bool:
        """对单条 eval_data 执行软删除，并刷新父评测集计数"""
        logger.info(f"delete_eval_data called id={id}")
        with SessionLocal() as session:
            r = session.get(EvalDataORM, id)
            if not r or r.deleted:
                logger.warning(f"delete_eval_data: id={id} not found or already deleted")
                return False
            r.deleted = True
            session.add(r)
            session.commit()
            try:
                eval_set_service.refresh_count(r.eval_set_id)
            except Exception as e:
                logger.warning(f"refresh_count failed after delete for set={r.eval_set_id}: {e}")
            logger.info(f"delete_eval_data: id={id} marked deleted")
            return True


eval_data_service = EvalDataService()
