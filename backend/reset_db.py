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

# 1. 把所有存为 LEADER 或 leader 的旧角色，全部更正为 OWNER
updated_count = db.query(models.User).filter(
    models.User.role.in_(["LEADER", "leader", "owner"])
).update({models.User.role: "OWNER"}, synchronize_session=False)

db.commit()
print(f"✅ 成功修复 {updated_count} 条项目负责人角色数据！")
db.close()

try:
    # 1. 创建账号 (0123:项目负责人, 1234:员工)
    owner = models.User(id="0123", username="林棠", password="123456", role="OWNER")
    employee = models.User(id="1234", username="陈默", password="123456", role="EMPLOYEE")
    admin = models.User(id="0001", username="周琰", password="123456", role="ADMIN")
    db.add_all([owner, employee, admin])
    db.commit()

    # 2. 项目 (绑定项目负责人 0123)
    ac1 = models.Project(name="无人机1", owner_id="0123")
    ac2 = models.Project(name="无人机2", owner_id="0123")
    db.add_all([ac1, ac2])
    db.commit()

    # 3. 工作类型
    for cat_name in models.FIXED_WORK_CATEGORIES:
        db.add(models.WorkCategory(name=cat_name))
    db.commit()

    # 4. 工作包（含分值和完成节点要求）
    pkg1 = models.WorkPackage(
        name="跑道 FOD 视觉识别算子",
        score=5.0,
        deadline="2026.7.29",
        project_name="无人机1",
        category_name="类型1"
    )
    pkg2 = models.WorkPackage(
        name="无人机1云台机载嵌入式适配",
        score=6.0,
        deadline="2028.9.20",
        project_name="无人机1",
        category_name="类型2"
    )

    # 示例：无人机2 的工作包
    pkg3 = models.WorkPackage(
        name="无人机2自组网避障模块",
        score=8.0,
        deadline="2028.5.8",
        project_name="无人机2",
        category_name="类型1"
    )
    pkg4 = models.WorkPackage(
        name="无人机2地面站控制软件",
        score=7.0,
        deadline="2026.4.9",
        project_name="无人机2",
        category_name="类型3"
    )

    db.add_all([pkg1, pkg2, pkg3, pkg4])
    db.commit()

    

    print("✅ 数据库重置成功！三级数据与预置任务构建完成。")
finally:
    db.close()
