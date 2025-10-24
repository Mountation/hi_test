import sys, os
# ensure hi_api package dir is on sys.path so `db` package can be imported
ROOT = os.path.dirname(__file__)
HI_API = os.path.join(ROOT, 'hi_api')
if HI_API not in sys.path:
    sys.path.insert(0, HI_API)

from db.sqlalchemy import SessionLocal
from db.models import Job as JobORM, EvalData as EvalDataORM

def latest_job_info(limit_rows=30):
    with SessionLocal() as s:
        j = s.query(JobORM).order_by(JobORM.created_at.desc()).first()
        if not j:
            print('No jobs found')
            return
        print('Latest job:', j.job_id, 'eval_set_id=', j.eval_set_id, 'status=', j.status, 'processed=', j.processed, 'total=', j.total, 'file_path=', j.file_path, 'error=', j.error)
        rows = s.query(EvalDataORM).filter(EvalDataORM.eval_set_id == j.eval_set_id).order_by(EvalDataORM.corpus_id.desc()).limit(limit_rows).all()
        print(f'Recent {len(rows)} eval_data rows for set', j.eval_set_id)
        for r in rows:
            print('corpus_id=', r.corpus_id, 'id=', r.id, 'content=', (r.content[:200] if r.content else None), 'expected=', (r.expected[:200] if r.expected else None))

if __name__ == '__main__':
    latest_job_info()
