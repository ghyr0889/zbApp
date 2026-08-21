# xiangmu/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, ensure_database_schema
from routers import auth, work_logs, review, admin, tasks, score_board

# 建表 + 轻量迁移（为旧库补列，如 projects.level）
Base.metadata.create_all(bind=engine)
ensure_database_schema()

app = FastAPI(
    title="工作内容统计系统 API",
    description="支持项目→工作包→工作项三级结构、日志提交、Owner 审核与自动积分结算",
    version="1.0.0"
)

# 跨域配置（必须加在 include_router 之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 模块路由
app.include_router(auth.router)
app.include_router(work_logs.router)
app.include_router(review.router)
app.include_router(admin.router)
app.include_router(tasks.router)
app.include_router(score_board.router)
# 兼容前端历史路径（如 DELETE /api/v1/users/{id}）
app.include_router(admin.legacy_router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Work-stat-system 后端 API 正常运行中"}
