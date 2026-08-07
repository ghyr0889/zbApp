# xiangmu/backend/reset_db.py
import os
from database import engine, Base, SessionLocal
import models

if os.path.exists("work_stat.db"):
    try:
        os.remove("work_stat.db")
        print("🗑️ 旧 SQLite 数据库已成功删除！")
    except Exception as e:
        print(f"❌ 删除数据库失败，请先停止 uvicorn 服务: {e}")
        exit(1)

Base.metadata.create_all(bind=engine)
db = SessionLocal()


try:
    # 1. 创建账号 (0123:项目负责人, 1234:员工)
    owner = models.User(id="0123", username="林棠", password="123456", role="OWNER")
    employee = models.User(id="1234", username="陈默", password="123456", role="EMPLOYEE")
    admin = models.User(id="0001", username="周琰", password="123456", role="ADMIN")
    db.add_all([owner, employee, admin])
    db.commit()

    # 2. 项目 (绑定项目负责人 0123)
    ac1 = models.Project(id=1, name="项目1", owner_id="0123")
    ac2 = models.Project(id=2, name="项目2", owner_id="0123")
    db.add_all([ac1, ac2])
    db.commit()

    # 3. 工作类型
    for cat_name in models.FIXED_WORK_CATEGORIES:
        db.add(models.WorkCategory(name=cat_name))
    db.commit()

    # 4. 工作包（含分值和完成节点要求）
    pkg1 = models.WorkPackage(
        id=1,
        name="工作1",
        score=5.0,
        deadline="2026.7.29",
        project_id=1,
        category_name="类型1"
    )
    pkg2 = models.WorkPackage(
        id=2,
        name="工作2",
        score=6.0,
        deadline="2028.9.20",
        project_id=1,
        category_name="类型2"
    )

    # 示例：无人机2 的工作包
    pkg3 = models.WorkPackage(
        id=3,
        name="工作1",
        score=8.0,
        deadline="2028.5.8",
        project_id=2,
        category_name="类型1"
    )
    pkg4 = models.WorkPackage(
        id=4,
        name="工作2",
        score=7.0,
        deadline="2026.4.9",
        project_id=2,
        category_name="类型3"
    )
    db.add_all([pkg1, pkg2, pkg3, pkg4])
    db.commit()

    

    print("✅ 数据库重置成功！三级数据与预置任务构建完成。")
finally:
    db.close()
