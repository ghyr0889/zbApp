from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./work_stat.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_database_schema():
    """轻量迁移：为旧版数据库补全缺失的列（保留已有数据）。

    SQLite 的 create_all 只新建表、不会修改已存在的表，
    因此对历史库需要手动 ALTER TABLE 补列。
    """
    with engine.begin() as conn:
        project_columns = [
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(projects)").fetchall()
        ]
        # 项目级别列：列名必须与 models.Project.level 一致
        if "level" not in project_columns:
            conn.exec_driver_sql(
                "ALTER TABLE projects ADD COLUMN level VARCHAR(10) DEFAULT 'C'"
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
