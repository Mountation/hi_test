from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from .sqlalchemy import Base


class EvalSet(Base):
    __tablename__ = 'eval_set'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment='评测集名称')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    count = Column(Integer, default=0, nullable=False, comment='数量')
    deleted = Column(Boolean, default=False, nullable=False, comment='软删除标记')


class EvalData(Base):
    __tablename__ = 'eval_data'

    id = Column(Integer, primary_key=True, index=True)
    eval_set_id = Column(Integer, nullable=False, index=True, comment='评测集id')
    corpus_id = Column(Integer, nullable=True, comment='语料在所属评测集内的序号（从1开始）')
    content = Column(String(2000), nullable=False, comment='语料')
    expected = Column(String(2000), nullable=True, comment='预期结果')
    intent = Column(String(255), nullable=True, comment='意图')
    deleted = Column(Boolean, default=False, nullable=False, comment='软删除标记')


class EvalResult(Base):
    __tablename__ = 'eval_results'

    id = Column(Integer, primary_key=True, index=True)
    eval_set_id = Column(Integer, nullable=False, index=True, comment='评测集id')
    eval_data_id = Column(Integer, nullable=False, index=True, comment='评测数据id')
    actual_result = Column(String(2000), nullable=True, comment='实际结果')
    actual_intent = Column(String(255), nullable=True, comment='实际意图')
    score = Column(Integer, nullable=True, comment='分数')
    exec_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='执行时间')
    deleted = Column(Boolean, default=False, nullable=False, comment='软删除标记')
    agent_version = Column(String(100), nullable=True, comment='Agent版本')
    kdb = Column(Integer, default=0, nullable=False, comment='是否命中知识库(0否,1是)')


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), nullable=False, unique=True, index=True, comment='外部使用的 job id（UUID）')
    eval_set_id = Column(Integer, nullable=True, index=True, comment='关联的评测集 id')
    status = Column(String(32), nullable=False, default='pending', comment='pending|running|success|failed')
    processed = Column(Integer, default=0, nullable=False, comment='已处理条数')
    total = Column(Integer, default=0, nullable=False, comment='总条数（估算）')
    file_path = Column(String(1000), nullable=True, comment='上传的临时文件路径')
    error = Column(Text, nullable=True, comment='错误信息（若失败）')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
