from typing import List, Optional
from db.models import EvalResult as EvalResultORM
from models.eval_result import EvalResultCreate, EvalResult
from db.sqlalchemy import SessionLocal

from utils.log import get_logger

logger = get_logger("eval_result_service")


class EvalResultService:
    def create_result(self, payload: EvalResultCreate) -> EvalResult:
        logger.info(f"create_result called for set={getattr(payload, 'eval_set_id', None)} data={getattr(payload, 'eval_data_id', None)}")
        with SessionLocal() as session:
            try:
                # attempt to log engine url if available for debugging
                engine = getattr(session.bind, 'url', None)
                logger.debug(f"DB engine url: {engine}")
            except Exception:
                logger.debug("DB engine url: unavailable")
            obj = EvalResultORM(eval_set_id=payload.eval_set_id,
                                eval_data_id=payload.eval_data_id,
                                actual_result=payload.actual_result,
                                actual_intent=payload.actual_intent,
                                score=payload.score,
                                agent_version=payload.agent_version,
                                kdb=payload.kdb)
            # 若提供 exec_time，则覆盖默认值
            if getattr(payload, 'exec_time', None):
                obj.exec_time = payload.exec_time
            session.add(obj)
            session.commit()
            session.refresh(obj)
            logger.info(f"create_result: id={obj.id} set={obj.eval_set_id} data={obj.eval_data_id} score={obj.score}")
            try:
                cnt = session.query(EvalResultORM).count()
                logger.debug(f"eval_results table row count after insert: {cnt}")
            except Exception as e:
                logger.debug(f"failed to count eval_results rows: {e}")
            return EvalResult.model_validate(obj, from_attributes=True)

    def list_by_eval_set(self, eval_set_id: int) -> List[EvalResult]:
        logger.info(f"list_by_eval_set called for set={eval_set_id}")
        with SessionLocal() as session:
            rows = session.query(EvalResultORM).filter(EvalResultORM.eval_set_id == eval_set_id,
                                                       EvalResultORM.deleted == False).all()
            logger.info(f"list_by_eval_set: found {len(rows)} results for set={eval_set_id}")
            return [EvalResult.model_validate(r, from_attributes=True) for r in rows]

    def list_by_eval_data(self, eval_data_id: int) -> List[EvalResult]:
        logger.info(f"list_by_eval_data called for data={eval_data_id}")
        with SessionLocal() as session:
            rows = session.query(EvalResultORM).filter(EvalResultORM.eval_data_id == eval_data_id,
                                                       EvalResultORM.deleted == False).all()
            logger.info(f"list_by_eval_data: found {len(rows)} results for data={eval_data_id}")
            return [EvalResult.model_validate(r, from_attributes=True) for r in rows]

    def list_by_eval_data_with_set(self, eval_set_id: int, corpus_id: int) -> List[EvalResult]:
        logger.info(f"list_by_eval_data_with_set called for set={eval_set_id} corpus_id={corpus_id}")
        with SessionLocal() as session:
            rows = session.query(EvalResultORM).filter(EvalResultORM.eval_set_id == eval_set_id,
                                                       EvalResultORM.eval_data_id == corpus_id,
                                                       EvalResultORM.deleted == False).all()
            logger.info(f"list_by_eval_data_with_set: found {len(rows)} results for set={eval_set_id} corpus_id={corpus_id}")
            return [EvalResult.model_validate(r, from_attributes=True) for r in rows]

    def get_result(self, id: int) -> Optional[EvalResult]:
        logger.info(f"get_result called id={id}")
        with SessionLocal() as session:
            r = session.get(EvalResultORM, id)
            if not r or r.deleted:
                logger.warning(f"get_result: id={id} not found or deleted")
                return None
            logger.info(f"get_result: id={id} found set={r.eval_set_id} data={r.eval_data_id} score={r.score}")
            return EvalResult.model_validate(r, from_attributes=True)

    def delete_result(self, id: int) -> bool:
        logger.info(f"delete_result called id={id}")
        with SessionLocal() as session:
            r = session.get(EvalResultORM, id)
            if not r or r.deleted:
                logger.warning(f"delete_result: id={id} not found or already deleted")
                return False
            r.deleted = True
            session.add(r)
            session.commit()
            logger.info(f"delete_result: id={id} marked deleted")
            return True


eval_result_service = EvalResultService()
