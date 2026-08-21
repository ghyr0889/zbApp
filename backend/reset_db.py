# xiangmu/backend/reset_db.py
import os
from datetime import datetime
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
    leader = models.User(id="0123", username="林棠", password="123456", role="LEADER",job_grade="P3")
    department = models.User(id="5678", username="李华", password="123456", role="DEPARTMENT",job_grade="P2")
    employee = models.User(id="1234", username="陈默", password="123456", role="EMPLOYEE",job_grade="P1")
    admin = models.User(id="0001", username="周琰", password="123456", role="ADMIN",job_grade="P4")
    db.add_all([leader, department, employee, admin])
    db.commit()

    # 2. 项目 (绑定项目负责人 0123)
    proj1 = models.Project(id=1, code="ABCD", name="项目1", level="A", owner_id="0123", category="类别1",complete_status = None)
    proj2 = models.Project(id=2, code="TLJC", name="项目2", level="B", owner_id="0123", category="类别2",complete_status = None)
    db.add_all([proj1, proj2])
    db.commit()

    # 3. 工作包类别（固定四类：类型1-4）
    for cat_name in models.FIXED_WORK_CATEGORIES:
        db.add(models.WorkProjectCategory(name=cat_name))
    db.commit()

    # 4. 工作包：不同项目下有不同的工作包，类别固定为 类型1-4
    #    —— 项目1 下的工作包（类别：类型1、类型2）
    pkg1 = models.WorkPackage(
        id="P1-WP01",
        project_id=1,
        category_name="类型1",
        next_step_work="完成项目1-工作包1 的下一阶段任务",
        owner_id="1234",
        objective="完成项目1-工作包1 的工作目标",
        complete_status = None
    )
    pkg2 = models.WorkPackage(
        id="P1-WP02",
        project_id=1,
        category_name="类型2",
        next_step_work="完成项目1-工作包2 的下一阶段任务",
        owner_id="1234",
        objective="完成项目1-工作包2 的工作目标",
        complete_status = None
    )
    #    —— 项目2 下的工作包（类别：类型3、类型4）
    pkg3 = models.WorkPackage(
        id="P2-WP01",
        project_id=2,
        category_name="类型3",
        next_step_work="完成项目2-工作包1 的下一阶段任务",
        owner_id="1234",
        objective="完成项目2-工作包1 的工作目标",
        complete_status = None
    )
    pkg4 = models.WorkPackage(
        id="P2-WP02",
        project_id=2,
        category_name="类型4",
        next_step_work="完成项目2-工作包2 的下一阶段任务",
        owner_id="1234",
        objective="完成项目2-工作包2 的工作目标",
        complete_status = None
    )
    db.add_all([pkg1, pkg2, pkg3, pkg4])
    db.commit()

    # 5. 工作项：不同工作包下有不同的工作项
    item1 = models.WorkItem(
        id=1,
        name="工作项1-1",
        work_package_id=pkg1.id,
        standard="按工作标准1执行",
        difficulty="P1",
        importance="Ⅰ级",
        innovation="低",
        deadline=datetime(2026, 8, 31),
        score=2.0,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    item2 = models.WorkItem(
        id=2,
        name="工作项1-2",
        work_package_id=pkg1.id,
        standard="按工作标准2执行",
        difficulty="P2",
        importance="Ⅱ级",
        innovation="高",
        deadline=datetime(2026, 9, 15),
        score=3.0,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    item3 = models.WorkItem(
        id=3,
        name="工作项2-1",
        work_package_id=pkg2.id,
        standard="按工作标准3执行",
        difficulty="P3",
        importance="Ⅲ级",
        innovation="高",
        deadline=datetime(2026, 10, 1),
        score=4.0,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    item4 = models.WorkItem(
        id=4,
        name="工作项2-2",
        work_package_id=pkg2.id,
        standard="按工作标准4执行",
        difficulty="P1",
        importance="Ⅱ级",
        innovation="低",
        deadline=datetime(2026, 10, 20),
        score=2.5,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    item5 = models.WorkItem(
        id=5,
        name="工作项3-1",
        work_package_id=pkg3.id,
        standard="按工作标准5执行",
        difficulty="P3",
        importance="Ⅰ级",
        innovation="中",
        deadline=datetime(2026, 11, 5),
        score=3.0,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    item6 = models.WorkItem(
        id=6,
        name="工作项3-2",
        work_package_id=pkg3.id,
        standard="按工作标准6执行",
        difficulty="P2",
        importance="Ⅱ级",
        innovation="中",
        deadline=datetime(2026, 11, 25),
        score=3.5,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    item7 = models.WorkItem(
        id=7,
        name="工作项4-1",
        work_package_id=pkg4.id,
        standard="按工作标准7执行",
        difficulty="P3",
        importance="Ⅲ级",
        innovation="中",
        deadline=datetime(2026, 12, 10),
        score=5.0,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    item8 = models.WorkItem(
        id=8,
        name="工作项4-2",
        work_package_id=pkg4.id,
        standard="按工作标准8执行",
        difficulty="P2",
        importance="Ⅱ级",
        innovation="低",
        deadline=datetime(2026, 12, 25),
        score=4.0,
        completed_at=None,
        category="工作类型1",
        complete_status = None
    )
    db.add_all([item1, item2, item3, item4, item5, item6, item7, item8])
    db.commit()

    ScoreDimensionLevel = models.ScoreDimensionLevel(
        id = 1,

    )

    print("✅ 数据库重置成功！项目→工作包→工作项 三级数据构建完成。")
finally:
    db.close()
