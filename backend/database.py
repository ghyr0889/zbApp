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
        # ---- 为 work_items 补全新列（质量分 / 计算得分），否则查询会报 no such column ----
        wi_columns = [
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(work_items)").fetchall()
        ]
        if "quality_score" not in wi_columns:
            conn.exec_driver_sql("ALTER TABLE work_items ADD COLUMN quality_score FLOAT DEFAULT 0.0")
        if "calculate_score" not in wi_columns:
            conn.exec_driver_sql("ALTER TABLE work_items ADD COLUMN calculate_score FLOAT DEFAULT 0.0")
        if "completed_at" not in wi_columns:
            conn.exec_driver_sql("ALTER TABLE work_items ADD COLUMN completed_at DATETIME")

        # ---- 为 work_item_monthly_scores 补全计算得分列 ----
        ms_columns = [
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(work_item_monthly_scores)").fetchall()
        ]
        if "calculate_score" not in ms_columns:
            conn.exec_driver_sql("ALTER TABLE work_item_monthly_scores ADD COLUMN calculate_score FLOAT DEFAULT 0.0")

        # ---- 为 score_dimension_levels 重命名列（dimension_key/level_key → variable/level）----
        sdl_columns = [
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(score_dimension_levels)").fetchall()
        ]
        if "variable" not in sdl_columns and "dimension_key" in sdl_columns:
            conn.exec_driver_sql("ALTER TABLE score_dimension_levels RENAME COLUMN dimension_key TO variable")
        if "level" not in sdl_columns and "level_key" in sdl_columns:
            conn.exec_driver_sql("ALTER TABLE score_dimension_levels RENAME COLUMN level_key TO level")
        if "job_grade" not in sdl_columns:
            conn.exec_driver_sql("ALTER TABLE score_dimension_levels ADD COLUMN job_grade VARCHAR(50)")
        # 清理已废弃的 level_label 列（旧库遗留，NOT NULL 会阻碍新插入）
        if "level_label" in sdl_columns:
            conn.exec_driver_sql("ALTER TABLE score_dimension_levels DROP COLUMN level_label")

        # 若还没有按职级展开的数据（job_grade 全空）→ 重建为「职级 × 档位」矩阵
        graded = conn.exec_driver_sql(
            "SELECT COUNT(*) FROM score_dimension_levels WHERE job_grade IS NOT NULL AND TRIM(job_grade) != ''"
        ).fetchone()[0]
        if graded == 0:
            old = {
                (r[0], r[1]): r[2]
                for r in conn.exec_driver_sql(
                    "SELECT variable, level, factor FROM score_dimension_levels"
                ).fetchall()
            }
            conn.exec_driver_sql("DELETE FROM score_dimension_levels")
            grades = ["P2", "P3", "P4", "P5", "P6", "P7", "P8"]
            # 难度：7 职级 × 4 档位
            for g in grades:
                for lv in [ "P2", "P3", "P4", "P5", "P6", "P7", "P8"]:
                    conn.exec_driver_sql(
                        "INSERT INTO score_dimension_levels (variable, job_grade, level, factor) VALUES (?,?,?,?)",
                        ("difficulty", g, lv, old.get(("difficulty", lv), 0)),
                    )
            # 重要度：7 职级 × 4 档位
            for g in grades:
                for lv in ["Ⅰ级", "Ⅱ级", "Ⅲ级", "Ⅳ级"]:
                    conn.exec_driver_sql(
                        "INSERT INTO score_dimension_levels (variable, job_grade, level, factor) VALUES (?,?,?,?)",
                        ("importance", g, lv, old.get(("importance", lv), 0)),
                    )
            # 创新度：不挂职级
            for lv in ["无", "低", "中", "高"]:
                conn.exec_driver_sql(
                    "INSERT INTO score_dimension_levels (variable, job_grade, level, factor) VALUES (?,?,?,?)",
                    ("innovation", "", lv, old.get(("innovation", lv), 0)),
                )

            ms_columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(work_item_monthly_scores)").fetchall()]
            if "quality_score" not in ms_columns:
                conn.exec_driver_sql("ALTER TABLE work_item_monthly_scores ADD COLUMN quality_score FLOAT")
                conn.exec_driver_sql("ALTER TABLE work_item_monthly_scores ADD COLUMN quality_score_updated_at DATETIME")

        # ---- 初始化档位字典表 score_level_defs（表空时插入默认档位）----
        def_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM score_level_defs").fetchone()[0]
        if def_rows == 0:
            def_defaults = [
                ("job_grade", "P1"), ("job_grade", "P2"), ("job_grade", "P3"), ("job_grade", "P4"),
                ("difficulty", "P1"), ("difficulty", "P2"), ("difficulty", "P3"), ("difficulty", "P4"),
                ("importance", "Ⅰ级"), ("importance", "Ⅱ级"), ("importance", "Ⅲ级"), ("importance", "Ⅳ级"),
                ("innovation", "无"), ("innovation", "低"), ("innovation", "中"), ("innovation", "高"),
            ]
            for i, (cat, name) in enumerate(def_defaults):
                conn.exec_driver_sql(
                    "INSERT INTO score_level_defs (category, name, sort_order, is_active) VALUES (?,?,?,?)",
                    (cat, name, i, 1),
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
