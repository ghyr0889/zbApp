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