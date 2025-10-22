from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from models.eval_set import EvalSet
from services.eval_set_service import eval_set_service
from models.eval_set import EvalSetCreate
from fastapi import Body
from fastapi import Response
from models.eval_set import EvalSetUpdate
from fastapi import Path
from fastapi import UploadFile, File
import tempfile
import openpyxl
import uuid
import os
from services.eval_data_service import eval_data_service
from db.sqlalchemy import SessionLocal
from db.models import Job as JobORM
from services.upload_job_worker import process_upload_job

router = APIRouter()


@router.get("/", response_model=List[EvalSet])
def list_eval_sets():
    return eval_set_service.list_eval_sets()


@router.post("/", response_model=EvalSet)
def create_eval_set(payload: EvalSetCreate = Body(...)):
    return eval_set_service.create_eval_set(payload)


@router.get("/{id}", response_model=EvalSet)
def get_eval_set(id: int):
    e = eval_set_service.get_eval_set(id)
    if not e:
        raise HTTPException(status_code=404, detail="Eval set not found")
    return e


@router.delete("/{id}", status_code=204)
def delete_eval_set(id: int):
    ok = eval_set_service.delete_eval_set(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Eval set not found")
    return Response(status_code=204)


@router.patch("/{id}", response_model=EvalSet)
def update_eval_set(id: int, payload: EvalSetUpdate = Body(...)):
    updated = eval_set_service.update_eval_set(id, name=payload.name)
    if not updated:
        raise HTTPException(status_code=404, detail="Eval set not found")
    return updated


@router.post("/upload", summary="上传 Excel 导入评测数据")
def upload_evalset_excel(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    try:
        # 文件名（不含扩展名）视为评测集名称
        name = file.filename.rsplit('.', 1)[0]
        # 保存上传文件到临时目录
        tmp_dir = tempfile.gettempdir()
        unique_name = f"upload_{uuid.uuid4().hex}_{file.filename}"
        tmp_path = os.path.join(tmp_dir, unique_name)
        with open(tmp_path, "wb") as f:
            content = file.file.read()
            f.write(content)

        # 创建或查找评测集（先不刷新计数，等待后台任务完成）
        existing = eval_set_service.get_by_name(name)
        if existing:
            eval_set_id = existing.id
        else:
            new_set = eval_set_service.create_eval_set(EvalSetCreate(name=name))
            eval_set_id = new_set.id

        # 在 jobs 表创建任务记录
        job_uuid = uuid.uuid4().hex
        with SessionLocal() as session:
            job = JobORM(job_id=job_uuid, eval_set_id=eval_set_id, status='pending', processed=0, total=0, file_path=tmp_path)
            session.add(job)
            session.commit()

        # 将后台处理任务加入 BackgroundTasks（或立即异步触发）
        if background_tasks is not None:
            background_tasks.add_task(process_upload_job, job_uuid)
        else:
            # best-effort: spawn in a new thread if BackgroundTasks not available
            import threading
            threading.Thread(target=process_upload_job, args=(job_uuid,)).start()

        return {"job_id": job_uuid, "eval_set_id": eval_set_id}
    except Exception as e:
        from utils.log import get_logger
        logger = get_logger('evalset_upload')
        logger.exception(f"upload_evalset_excel failed: {e}")
        raise HTTPException(status_code=500, detail=f"upload failed: {e}")
 
