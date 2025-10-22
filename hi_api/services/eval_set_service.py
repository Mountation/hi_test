from typing import List, Optional
from sqlalchemy.orm import Session
from db.models import EvalSet as EvalSetORM
from models.eval_set import EvalSetCreate, EvalSet
from db.sqlalchemy import SessionLocal
from db.models import EvalData as EvalDataORM

from utils.log import get_logger

logger = get_logger("eval_set_service")


class EvalSetService:
    def __init__(self):
        pass

    def create_eval_set(self, payload: EvalSetCreate) -> EvalSet:
        logger.info(f"create_eval_set called: name={getattr(payload, 'name', None)}")
        with SessionLocal() as session:
            # 创建评测集（初始 count 为 0）
            obj = EvalSetORM(name=payload.name, count=0)
            session.add(obj)
            session.commit()
            session.refresh(obj)

            # 从 eval_data 表计算实际数量（以防数据已存在）
            actual_count = session.query(EvalDataORM).filter(EvalDataORM.eval_set_id == obj.id, EvalDataORM.deleted == False).count()
            if actual_count != obj.count:
                obj.count = actual_count
                session.add(obj)
                session.commit()
                session.refresh(obj)

            logger.info(f"eval_set created id={obj.id} name={obj.name} count={obj.count}")
            return EvalSet.model_validate(obj, from_attributes=True)

    def refresh_count(self, eval_set_id: int) -> int:
        """重新计算并持久化指定评测集的 eval_data 数量"""
        logger.info(f"refresh_count called for eval_set_id={eval_set_id}")
        with SessionLocal() as session:
            obj = session.get(EvalSetORM, eval_set_id)
            if not obj:
                logger.warning(f"refresh_count: eval_set id={eval_set_id} not found")
                return 0
            cnt = session.query(EvalDataORM).filter(EvalDataORM.eval_set_id == eval_set_id, EvalDataORM.deleted == False).count()
            obj.count = cnt
            session.add(obj)
            session.commit()
            logger.info(f"refresh_count: eval_set id={eval_set_id} count updated to {cnt}")
            return cnt

    def delete_eval_set(self, eval_set_id: int) -> bool:
        """对指定评测集执行软删除，同时软删除其所有评测数据，并将 count 置为 0"""
        logger.info(f"delete_eval_set called for id={eval_set_id}")
        with SessionLocal() as session:
            obj = session.get(EvalSetORM, eval_set_id)
            if not obj:
                logger.warning(f"delete_eval_set: eval_set id={eval_set_id} not found")
                return False
            # 标记评测集为删除
            obj.deleted = True
            obj.count = 0
            session.add(obj)
            # 标记相关 eval_data 为删除
            session.query(EvalDataORM).filter(EvalDataORM.eval_set_id == eval_set_id).update({EvalDataORM.deleted: True})
            session.commit()
            logger.info(f"delete_eval_set: eval_set id={eval_set_id} and related data marked deleted")
            return True

    def update_eval_set(self, eval_set_id: int, name: Optional[str] = None) -> Optional[EvalSet]:
        """更新评测集名称"""
        logger.info(f"update_eval_set called id={eval_set_id} name={name}")
        with SessionLocal() as session:
            obj = session.get(EvalSetORM, eval_set_id)
            if not obj or obj.deleted:
                logger.warning(f"update_eval_set: eval_set id={eval_set_id} not found or deleted")
                return None
            if name is not None:
                obj.name = name
            session.add(obj)
            session.commit()
            session.refresh(obj)
            logger.info(f"update_eval_set: eval_set id={eval_set_id} updated name={obj.name}")
            return EvalSet.model_validate(obj, from_attributes=True)

    def list_eval_sets(self) -> List[EvalSet]:
        logger.info("list_eval_sets called")
        with SessionLocal() as session:
            rows = session.query(EvalSetORM).filter(EvalSetORM.deleted == False).all()
            logger.info(f"list_eval_sets: found {len(rows)} sets")
            return [EvalSet.model_validate(r, from_attributes=True) for r in rows]

    def get_eval_set(self, id: int) -> Optional[EvalSet]:
        logger.info(f"get_eval_set called id={id}")
        with SessionLocal() as session:
            r = session.get(EvalSetORM, id)
            if not r or r.deleted:
                logger.warning(f"get_eval_set: id={id} not found or deleted")
                return None
            logger.info(f"get_eval_set: id={id} found name={r.name}")
            return EvalSet.model_validate(r, from_attributes=True)

    def get_by_name(self, name: str) -> Optional[EvalSet]:
        """根据名称查找评测集（返回 Pydantic 模型）"""
        logger.info(f"get_by_name called name={name}")
        with SessionLocal() as session:
            r = session.query(EvalSetORM).filter(EvalSetORM.name == name, EvalSetORM.deleted == False).first()
            if not r:
                logger.warning(f"get_by_name: name={name} not found")
                return None
            logger.info(f"get_by_name: name={name} found id={r.id}")
            return EvalSet.model_validate(r, from_attributes=True)


eval_set_service = EvalSetService()
