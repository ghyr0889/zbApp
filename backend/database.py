import os

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ============ 数据库连接（默认 MySQL，旧 SQLite 已废弃）============
# 优先级：DATABASE_URL > 各 MYSQL_* 单独配置 > 默认值
# Windows 一次性设置（设置后需重开终端生效）：
#   setx MYSQL_PASSWORD "你的MySQL root密码"
#   setx MYSQL_HOST "127.0.0.1"   （可选，默认即可）
#   setx MYSQL_PORT "3306"        （可选，默认即可）
#   setx MYSQL_USER "root"        （可选，默认即可）
#   setx MYSQL_DB   "work_stat"   （可选，默认即可）
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


def _columns_of(insp, table):
    """跨方言获取表的列名（SQLite / MySQL 通用）。"""
    try:
        return [c["name"] for c in insp.get_columns(table)]
    except Exception:
        return []


def ensure_database_schema():
    """轻量迁移：为旧版数据库补全缺失的列（跨 SQLite / MySQL 方言）。

    create_all 只新建表、不会修改已存在的表，
    因此对历史库需要手动 ALTER TABLE 补列。
    """
    with engine.begin() as conn:
        insp = inspect(conn)

        def has_col(table, col):
            return col in _columns_of(insp, table)

        def add_col(table, col, ddl):
            if not has_col(table, col):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))

        def rename_col(table, old, new):
            cols = _columns_of(insp, table)
            if new not in cols and old in cols:
                conn.execute(text(f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}"))

        def drop_col(table, col):
            if has_col(table, col):
                conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {col}"))

        # 项目级别列：列名必须与 models.Project.level 一致
        add_col("projects", "level", "VARCHAR(10) DEFAULT 'C'")

        # ---- work_items 补全质量分 / 计算得分 / 完成时间 ----
        add_col("work_items", "quality_score", "FLOAT DEFAULT 0.0")
        add_col("work_items", "calculate_score", "FLOAT DEFAULT 0.0")
        add_col("work_items", "completed_at", "DATETIME")

        # ---- work_item_monthly_scores 补全计算得分 / 质量分 ----
        add_col("work_item_monthly_scores", "calculate_score", "FLOAT DEFAULT 0.0")
        add_col("work_item_monthly_scores", "quality_score", "FLOAT")
        add_col("work_item_monthly_scores", "quality_score_updated_at", "DATETIME")

        # ---- score_dimension_levels 重命名列（dimension_key/level_key → variable/level）----
        rename_col("score_dimension_levels", "dimension_key", "variable")
        rename_col("score_dimension_levels", "level_key", "level")
        add_col("score_dimension_levels", "job_grade", "VARCHAR(50)")
        # 清理已废弃的 level_label 列（旧库遗留，NOT NULL 会阻碍新插入）
        drop_col("score_dimension_levels", "level_label")

        # 若还没有按职级展开的数据（job_grade 全空）→ 重建为「职级 × 档位」矩阵
        graded = conn.execute(
            text("SELECT COUNT(*) FROM score_dimension_levels WHERE job_grade IS NOT NULL AND TRIM(job_grade) != ''")
        ).fetchone()[0]
        if graded == 0:
            old = {
                (r[0], r[1]): r[2]
                for r in conn.execute(text("SELECT variable, level, factor FROM score_dimension_levels")).fetchall()
            }
            conn.execute(text("DELETE FROM score_dimension_levels"))
            grades = ["P2", "P3", "P4", "P5", "P6", "P7", "P8"]
            # 难度 / 重要度：7 职级 × 档位
            for g in grades:
                for lv in grades:
                    conn.execute(
                        text("INSERT INTO score_dimension_levels (variable, job_grade, level, factor) VALUES (:v, :g, :l, :f)"),
                        {"v": "difficulty", "g": g, "l": lv, "f": old.get(("difficulty", lv), 0)},
                    )
                for lv in ["Ⅰ级", "Ⅱ级", "Ⅲ级", "Ⅳ级"]:
                    conn.execute(
                        text("INSERT INTO score_dimension_levels (variable, job_grade, level, factor) VALUES (:v, :g, :l, :f)"),
                        {"v": "importance", "g": g, "l": lv, "f": old.get(("importance", lv), 0)},
                    )
            # 创新度：不挂职级
            for lv in ["无", "低", "中", "高"]:
                conn.execute(
                    text("INSERT INTO score_dimension_levels (variable, job_grade, level, factor) VALUES (:v, :g, :l, :f)"),
                    {"v": "innovation", "g": "", "l": lv, "f": old.get(("innovation", lv), 0)},
                )

        # ---- 初始化档位字典表 score_level_defs（表空时插入默认档位）----
        def_rows = conn.execute(text("SELECT COUNT(*) FROM score_level_defs")).fetchone()[0]
        if def_rows == 0:
            def_defaults = [
                ("job_grade", "P1"), ("job_grade", "P2"), ("job_grade", "P3"), ("job_grade", "P4"),
                ("difficulty", "P1"), ("difficulty", "P2"), ("difficulty", "P3"), ("difficulty", "P4"),
                ("importance", "Ⅰ级"), ("importance", "Ⅱ级"), ("importance", "Ⅲ级"), ("importance", "Ⅳ级"),
                ("innovation", "无"), ("innovation", "低"), ("innovation", "中"), ("innovation", "高"),
            ]
            for i, (cat, name) in enumerate(def_defaults):
                conn.execute(
                    text("INSERT INTO score_level_defs (category, name, sort_order, is_active) VALUES (:c, :n, :s, :a)"),
                    {"c": cat, "n": name, "s": i, "a": 1},
                )

        # ---- 大数据量性能：常用外键/查询索引（跨方言幂等创建）----
        def ensure_index(table, index_name, columns_sql):
            try:
                existing = [i["name"] for i in insp.get_indexes(table)]
            except Exception:
                existing = []
            if index_name not in existing:
                conn.execute(text(f"CREATE INDEX {index_name} ON {table} ({columns_sql})"))

        ensure_index("work_packages", "idx_work_packages_project_id", "project_id")
        ensure_index("work_items", "idx_work_items_work_package_id", "work_package_id")
        ensure_index("work_item_monthly_scores", "idx_ms_work_item_id", "work_item_id")
        ensure_index("work_item_monthly_scores", "idx_ms_month", "month")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
