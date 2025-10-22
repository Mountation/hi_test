from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 使用环境变量 DATABASE_URL；如果未设置，则使用本地 MySQL 占位连接（请按需修改）
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:admin123@127.0.0.1:3306/hitest')

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
