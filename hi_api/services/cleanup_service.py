import os
import time
from typing import Tuple
from loguru import logger
from db.sqlalchemy import SessionLocal, engine
from db.models import EvalData as EvalDataORM, EvalSet as EvalSetORM, EvalResult as EvalResultORM
from sqlalchemy import delete, select


def _chunked_delete(session, orm_cls, batch: int = 500) -> Tuple[int, int]:
    """Delete rows where deleted==True in chunks.

    Returns (deleted_rows, scanned_rows)
    """
    total_deleted = 0
    total_scanned = 0
    while True:
        # select up to batch ids to delete
        ids = [r[0] for r in session.execute(select(orm_cls.id).where(orm_cls.deleted == True).limit(batch)).all()]
        if not ids:
            break
        total_scanned += len(ids)
        res = session.execute(delete(orm_cls).where(orm_cls.id.in_(ids)))
        total_deleted += res.rowcount if res is not None else 0
        session.commit()
        logger.info(f"Deleted {res.rowcount if res is not None else 0} rows from {orm_cls.__tablename__}")
        # small pause to avoid long locks
        time.sleep(0.05)
    return total_deleted, total_scanned


def run_cleanup(dry_run: bool = False) -> dict:
    """Run cleanup once. If dry_run True, will only count rows.

    Returns a summary dict with counts.
    """
    logger.info("Starting cleanup job (dry_run=%s)" % dry_run)
    summary = {
        'eval_data_deleted': 0,
        'eval_set_deleted': 0,
        'eval_results_deleted': 0,
    }

    with SessionLocal() as session:
        # count first
        ed_count = session.execute(select(EvalDataORM.id).where(EvalDataORM.deleted == True).limit(1)).all()
        es_count = session.execute(select(EvalSetORM.id).where(EvalSetORM.deleted == True).limit(1)).all()
        er_count = session.execute(select(EvalResultORM.id).where(EvalResultORM.deleted == True).limit(1)).all()
        # if dry run, return counts
        if dry_run:
            summary['eval_data_deleted'] = len(session.execute(select(EvalDataORM.id).where(EvalDataORM.deleted == True)).all())
            summary['eval_set_deleted'] = len(session.execute(select(EvalSetORM.id).where(EvalSetORM.deleted == True)).all())
            summary['eval_results_deleted'] = len(session.execute(select(EvalResultORM.id).where(EvalResultORM.deleted == True)).all())
            logger.info(f"Dry run counts: {summary}")
            return summary

    # not a dry run: perform chunked deletes in a new session per table
    with SessionLocal() as session:
        dd, ds = _chunked_delete(session, EvalResultORM)
        summary['eval_results_deleted'] = dd

    with SessionLocal() as session:
        dd, ds = _chunked_delete(session, EvalDataORM)
        summary['eval_data_deleted'] = dd

    with SessionLocal() as session:
        dd, ds = _chunked_delete(session, EvalSetORM)
        summary['eval_set_deleted'] = dd

    logger.info(f"Cleanup finished: {summary}")
    return summary


def schedule_cleanup(interval_seconds: int = 24 * 3600):
    """Simple scheduler that runs cleanup in a loop. This is intended to be started in a background task.

    Default: once per day. Caller should run this in a background thread or task to avoid blocking.
    """
    logger.info("Starting scheduled cleanup loop, interval_seconds=%s" % interval_seconds)
    try:
        while True:
            try:
                run_cleanup(dry_run=False)
            except Exception as e:
                logger.exception("Cleanup run failed: %s" % e)
            time.sleep(interval_seconds)
    except Exception:
        logger.info("Cleanup scheduler terminating")
