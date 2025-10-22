from db.sqlalchemy import SessionLocal
from db.models import Job as JobORM, EvalData as EvalDataORM
from services.eval_set_service import eval_set_service
import openpyxl
from sqlalchemy import insert
from models.eval_data import EvalDataCreate
from utils.log import get_logger
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

logger = get_logger("upload_job_worker")

BATCH_SIZE = 500


def process_upload_job(job_id: str):
    logger.info(f"process_upload_job started for job={job_id}")
    with SessionLocal() as session:
        job = session.query(JobORM).filter(JobORM.job_id == job_id).first()
        if not job:
            logger.error(f"job {job_id} not found")
            return
        # mark running
        job.status = 'running'
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()
        file_path = job.file_path

    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        # skip header
        try:
            header = next(rows_iter)
        except StopIteration:
            header = None
        batch = []
        total = 0
        processed = 0
        # compute starting corpus_id for this eval_set (max existing corpus_id)
        try:
            with SessionLocal() as s2:
                max_row = s2.query(EvalDataORM).filter(EvalDataORM.eval_set_id == job.eval_set_id).order_by(EvalDataORM.corpus_id.desc()).with_entities(EvalDataORM.corpus_id).first()
                start_corpus = int(max_row[0]) if (max_row and max_row[0] is not None) else 0
        except Exception:
            start_corpus = 0
        # Count total approximate by iterating once? For memory concerns, we will not load all rows to count.
        # Instead update total as we go (best-effort).
        for row in rows_iter:
            total += 1
            content = row[0] if len(row) > 0 else None
            if not content:
                continue
            expected = row[1] if len(row) > 1 else None
            intent = row[2] if len(row) > 2 else None
            # assign corpus_id sequentially
            start_corpus += 1
            batch.append({
                'eval_set_id': job.eval_set_id,
                'corpus_id': start_corpus,
                'content': str(content),
                'expected': str(expected) if expected is not None else None,
                'intent': str(intent) if intent is not None else None,
                'deleted': False
            })
            if len(batch) >= BATCH_SIZE:
                _bulk_insert_batch(batch)
                processed += len(batch)
                batch = []
                _update_job_progress(job_id, processed, total)
        # final batch
        if batch:
            _bulk_insert_batch(batch)
            processed += len(batch)
            _update_job_progress(job_id, processed, total)

        # final refresh count
        try:
            eval_set_service.refresh_count(job.eval_set_id)
        except Exception as e:
            logger.warning(f"refresh_count failed after job {job_id}: {e}")

        with SessionLocal() as session:
            job = session.query(JobORM).filter(JobORM.job_id == job_id).first()
            job.status = 'success'
            job.processed = processed
            job.total = total
            job.finished_at = datetime.utcnow()
            session.add(job)
            session.commit()
        logger.info(f"process_upload_job finished for job={job_id}, processed={processed}")
    except Exception as e:
        logger.exception(f"process_upload_job failed for job={job_id}: {e}")
        with SessionLocal() as session:
            job = session.query(JobORM).filter(JobORM.job_id == job_id).first()
            if job:
                job.status = 'failed'
                job.error = str(e)
                job.finished_at = datetime.utcnow()
                session.add(job)
                session.commit()


def _bulk_insert_batch(batch):
    # Use SQLAlchemy core bulk insert for speed
    with SessionLocal() as session:
        try:
            session.execute(insert(EvalDataORM), batch)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.exception(f"bulk insert failed: {e}")


def _update_job_progress(job_id: str, processed: int, total: int):
    with SessionLocal() as session:
        job = session.query(JobORM).filter(JobORM.job_id == job_id).first()
        if not job:
            return
        job.processed = processed
        job.total = total
        session.add(job)
        session.commit()
