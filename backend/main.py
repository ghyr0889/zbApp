# xiangmu/backend/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import sys

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

# ---- 前端静态托管（方案A：无 Nginx，由后端托管 dist）----
# 前端构建产物：backend 的上一级 frontend/dist
if getattr(sys, 'frozen', False):
    DIST_DIR = Path(sys.executable).resolve().parent / "dist"   # exe 同目录下的 dist
else:
    DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/")
def root():
    # 有前端产物则返回首页，否则返回 API 状态（开发/纯 API 场景）
    if DIST_DIR.exists():
        return FileResponse(DIST_DIR / "index.html")
    return {"status": "ok", "message": "Work-stat-system 后端 API 正常运行中"}


if DIST_DIR.exists():
    # 静态资源（Vite 构建出的 /assets/*）
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    # Vue history 路由回退：所有非 API、非静态路径都返回 index.html
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        f = DIST_DIR / full_path
        if full_path and f.is_file():
            return FileResponse(f)
        return FileResponse(DIST_DIR / "index.html")


# 直接运行（python main.py 或打包后的 exe）时启动服务
if __name__ == "__main__":
    import uvicorn
    # 默认监听 0.0.0.0:8000（局域网可访问）；如需改端口改这里
    uvicorn.run(app, host="0.0.0.0", port=8000)
