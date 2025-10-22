from fastapi import APIRouter, HTTPException
from typing import Any
from db.sqlalchemy import SessionLocal
from db.models import Job as JobORM
from pydantic import BaseModel
from db.sqlalchemy import Base, engine
from fastapi import status

router = APIRouter()


class JobStatus(BaseModel):
    job_id: str
    status: str
    processed: int
    total: int
    error: Any = None


@router.get("/api/v1/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    with SessionLocal() as session:
        job = session.query(JobORM).filter(JobORM.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return JobStatus(
            job_id=job.job_id,
            status=job.status,
            processed=job.processed or 0,
            total=job.total or 0,
            error=job.error,
        )


@router.post("/api/v1/jobs/create_tables", status_code=status.HTTP_200_OK)
def create_tables():
    """Dev helper: create DB tables from SQLAlchemy Base metadata."""
    Base.metadata.create_all(bind=engine)
    return {"status": "ok"}
