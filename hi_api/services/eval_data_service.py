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

    def list_by_eval_set_paginated(self, eval_set_id: int, page: int = 1, page_size: int = 10, q: str | None = None):
        """Return (items, total) for the given eval_set_id. If q provided, perform server-side search across content/expected/intent."""
        logger.info(f"list_by_eval_set_paginated called for set={eval_set_id} page={page} page_size={page_size} q={q}")
        with SessionLocal() as session:
            base_q = session.query(EvalDataORM).filter(EvalDataORM.eval_set_id == eval_set_id, EvalDataORM.deleted == False)
            if q:
                like = f"%{q}%"
                base_q = base_q.filter(
                    (EvalDataORM.content.like(like)) | (EvalDataORM.expected.like(like)) | (EvalDataORM.intent.like(like))
                )
            total = base_q.count()
            items = base_q.order_by(EvalDataORM.id).offset((page - 1) * page_size).limit(page_size).all()
            logger.info(f"list_by_eval_set_paginated: returning {len(items)}/{total} rows for set={eval_set_id} q={q}")
            return [EvalData.model_validate(r, from_attributes=True) for r in items], total

    def list_all_search_paginated(self, q: str | None = None, page: int = 1, page_size: int = 10):
        """Search across all eval sets (non-deleted rows) with pagination."""
        logger.info(f"list_all_search_paginated called page={page} page_size={page_size} q={q}")
        with SessionLocal() as session:
            base_q = session.query(EvalDataORM).filter(EvalDataORM.deleted == False)
            if q:
                like = f"%{q}%"
                base_q = base_q.filter(
                    (EvalDataORM.content.like(like)) | (EvalDataORM.expected.like(like)) | (EvalDataORM.intent.like(like))
                )
            total = base_q.count()
            items = base_q.order_by(EvalDataORM.id).offset((page - 1) * page_size).limit(page_size).all()
            logger.info(f"list_all_search_paginated: returning {len(items)}/{total} rows q={q}")
            return [EvalData.model_validate(r, from_attributes=True) for r in items], total

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
            # perform a transaction that:
            # 1) mark the target row as deleted and set its corpus_id to -1
            # 2) decrement corpus_id by 1 for all rows in the same eval_set with corpus_id > deleted_corpus
            # 3) update eval_results.eval_data_id (which stores corpus_id) for same eval_set accordingly
            deleted_corpus = r.corpus_id
            eval_set_id = r.eval_set_id
            try:
                # mark deleted and set corpus_id to -1
                r.deleted = True
                r.corpus_id = -1
                session.add(r)

                if deleted_corpus is not None:
                    # shift subsequent eval_data corpus_id values down by 1
                    session.query(EvalDataORM).filter(
                        EvalDataORM.eval_set_id == eval_set_id,
                        EvalDataORM.deleted == False,
                        EvalDataORM.corpus_id > deleted_corpus
                    ).update({EvalDataORM.corpus_id: EvalDataORM.corpus_id - 1}, synchronize_session=False)

                    # update eval_results entries that reference corpus_id (stored in eval_data_id)
                    # do a raw SQL update via session.execute for broader compatibility
                    try:
                        session.execute(
                            "UPDATE eval_results SET eval_data_id = eval_data_id - 1 WHERE eval_set_id = :esid AND eval_data_id > :dc",
                            {"esid": eval_set_id, "dc": deleted_corpus}
                        )
                    except Exception:
                        logger.warning(f"failed to update eval_results eval_data_id for set={eval_set_id}")

                session.commit()
            except Exception as e:
                session.rollback()
                logger.exception(f"delete_eval_data transaction failed for id={id}: {e}")
                return False

            try:
                eval_set_service.refresh_count(eval_set_id)
            except Exception as e:
                logger.warning(f"refresh_count failed after delete for set={eval_set_id}: {e}")

            logger.info(f"delete_eval_data: id={id} marked deleted and corpus_id reassigned; shifted corpus ids for set={eval_set_id}")
            return True

        def update_eval_data(self, id: int, content: Optional[str] = None, expected: Optional[str] = None, intent: Optional[str] = None) -> Optional[EvalData]:
            logger.info(f"update_eval_data called id={id}")
            with SessionLocal() as session:
                r = session.get(EvalDataORM, id)
                if not r or r.deleted:
                    logger.warning(f"update_eval_data: id={id} not found or deleted")
                    return None
                if content is not None:
                    r.content = content
                if expected is not None:
                    r.expected = expected
                if intent is not None:
                    r.intent = intent
                session.add(r)
                session.commit()
                session.refresh(r)
                logger.info(f"update_eval_data: id={id} updated")
                return EvalData.model_validate(r, from_attributes=True)


eval_data_service = EvalDataService()
