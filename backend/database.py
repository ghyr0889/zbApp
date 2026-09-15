import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ============ 加载 .env（位于 database.py 的上级目录 = 项目根目录）============
# 基于 __file__ 定位，而不是当前工作目录，确保从任何位置启动都能找到 .env
import sys
if getattr(sys, 'frozen', False):      # 打包成 exe 时
    BASE_DIR = Path(sys.executable).resolve().parent   # exe 所在目录
else:                                   # 开发时
    BASE_DIR = Path(__file__).resolve().parent.parent  # 项目根目录
load_dotenv(BASE_DIR / ".env")

# ============ 数据库连接（默认 MySQL，旧 SQLite 已废弃）============
# 优先级：DATABASE_URL > 各 MYSQL_* 单独配置 > 默认值
# 如需整体覆盖连接串（优先级最高）：
#   setx DATABASE_URL "mysql+pymysql://root:密码@127.0.0.1:3306/work_stat?charset=utf8mb4"
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "work_stat")

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4",
)

engine_kwargs = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # 仅当显式回退到 SQLite 时才需要该参数
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # MySQL：连接池健康检查 + 定期回收，避免长连接被服务端断开
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
