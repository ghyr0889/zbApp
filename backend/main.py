from fastapi import FastAPI
from database import engine, Base
from routers import auth, work_logs, review, tasks
import models
from models import User, Project, WorkCategory, WorkPackage
from database import SessionLocal
from fastapi.middleware.cors import CORSMiddleware
from routers import admin



app = FastAPI(
    title="工作内容统计系统 API",
    description="支持日志提交、多级分类、Owner 审核与自动积分结算架构",
    version="1.0.0"
)

# 2. 配置跨域允许 (CORS) - ⚠️ 这段代码必须加在 include_router 之前！
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 允许所有前端源（包括 http://localhost:5173）
    allow_credentials=True,
    allow_methods=["*"],            # 允许所有 HTTP 方法 (POST, GET 等)
    allow_headers=["*"],            # 允许所有请求头
)

# 注册 API 模块路由
app.include_router(auth.router)
app.include_router(work_logs.router)
app.include_router(review.router)
app.include_router(admin.router)
app.include_router(tasks.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Work-stat-system 后端 API 正常运行中"}


# 自动生成本地 SQLite 数据表结构
Base.metadata.create_all(bind=engine)

# 测试工具：初始化测试数据
@app.post("/api/v1/init-data", tags=["测试工具"])
def init_data():
    db = SessionLocal()
    try:
        # 如果已经有用户，不重复初始化
        if db.query(User).first():
            return {"message": "数据库已有数据，无需重新初始化"}

        # 1. 创建测试用户：1 个主管，1 个员工
        owner = User(id="0123", username="张经理", password="123456", role="OWNER")
        employee = User(id="1234", username="王工", password="123456", role="EMPLOYEE") 
        db.add_all([owner, employee])
        db.commit()

        # 2. 创建测试项目
        project1 = models.Project(name="无人机1", owner_id="0123")
        project2 = models.Project(name="无人机2", owner_id="0123")
        db.add_all([project1, project2])
        db.commit()

        # 3. 创建工作类型（关联主管）
        categories = [models.WorkCategory(name=name) for name in models.FIXED_WORK_CATEGORIES]
        db.add_all(categories)
        db.commit()


        # 4. 创建工作包（关联项目和工作类型）
        pkg1 = models.WorkPackage(
            name="视觉导航模型训练", 
            score=5.0, 
            deadline="2028.9.30",
            project_name="无人机1",
            category_name="类型1",
        )
        pkg2 = models.WorkPackage(
            name="跑道 FOD 视觉识别算子", 
            score=5.0, 
            deadline="2028.7.5",
            project_name="无人机1",
            category_name="类型1",
        )
        db.add_all([pkg1, pkg2])
        db.commit()

        assign = models.TaskAssignment(
                id="TSK001",
                assigner_id="0123",
                assignee_id="1234",
                work_package_name="跑道 FOD 视觉识别算子",
                status="IN_PROGRESS"
            )
        db.add(assign)
        db.commit()
        
        print("√初始化测试数据成功！")

    except Exception as e:
        db.rollback()
        print(f"初始化测试数据失败：{e}")

    finally:
        db.close()
