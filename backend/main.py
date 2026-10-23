# xiangmu/backend/main.py
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from exceptions import BusinessError, PermissionDenied, NotFound
import sys
import logging, os

from database import engine, Base, SessionLocal, get_db
from routers import auth, work_logs, review, admin, tasks, score_board, complete_review, pending, announcement, information
from routers import work_time, dashboard, work_package_changes, score_confirmations

log_file = os.path.join(os.path.dirname(sys.executable), 'calculate_score.log')
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(log_file), logging.StreamHandler()])

# 建表 + 轻量迁移（为旧库补列，如 projects.level）
Base.metadata.create_all(bind=engine)

# 建立统一科室字典，并收录旧人员记录中的科室；不修改已有人员内容。
with SessionLocal() as db:
    information.seed_departments(db)

def score_settlement_guard(request: Request, db=Depends(get_db)):
    # All API writes acquire the same settlement lock before modifying source data.
    # This ensures overdue scores are frozen before a late edit can affect them.
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        from services.score_confirmation_service import synchronize
        synchronize(db)

app = FastAPI(
    dependencies=[Depends(score_settlement_guard)],
    title="工作内容统计系统 API",
    description="支持项目→工作包→工作项三级结构、日志提交、Owner 审核与自动积分结算",
    version="1.0.0"
)

# 跨域配置
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
app.include_router(complete_review.router)
app.include_router(pending.router)
app.include_router(announcement.router)
app.include_router(information.router)
app.include_router(work_time.router)
app.include_router(dashboard.router)
app.include_router(work_package_changes.router)
app.include_router(score_confirmations.router)

import threading
_settlement_stop = threading.Event()
_settlement_thread = None

def _settle_scores():
    from services.score_confirmation_service import synchronize
    with SessionLocal() as db:
        try:
            synchronize(db)
            db.commit()
        except Exception:
            db.rollback()
            raise

def _settlement_loop():
    while not _settlement_stop.wait(60):
        try:
            _settle_scores()
        except Exception:
            logging.exception("Monthly score settlement failed; retrying in 60 seconds")

@app.on_event("startup")
def start_score_settlement():
    from services.score_confirmation_service import initialize
    global _settlement_thread
    with SessionLocal() as db:
        initialize(db)
    _settle_scores()  # Finish overdue settlement before serving requests.
    _settlement_stop.clear()
    _settlement_thread = threading.Thread(target=_settlement_loop, daemon=True)
    _settlement_thread.start()

@app.on_event("shutdown")
def stop_score_settlement():
    _settlement_stop.set()
    if _settlement_thread:
        _settlement_thread.join(timeout=2)


@app.exception_handler(BusinessError)
async def handle_business_error(request, exc):
    if isinstance(exc, PermissionDenied):
        status_code = 403
    elif isinstance(exc, NotFound):
        status_code = 404
    else:
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )

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
