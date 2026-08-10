# # xiangmu/backend/routers/review.py
# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session

# import models
# from database import get_db
# from schemas import ReviewDecision, ReviewApprove, TaskAssignCreate
# from utils import work_package_summary, deadline_str

# router = APIRouter(prefix="/api/v1/review", tags=["Owner Review"])


# def ensure_project_owner(db: Session, reviewer_id: str, work_log: models.WorkLog):
#     """校验审核人：必须是 OWNER/LEADER，且是该日志所属项目的负责人。"""
#     reviewer = db.query(models.User).filter(models.User.id == str(reviewer_id)).first()
#     if not reviewer or str(reviewer.role).upper() not in ["OWNER", "LEADER"]:
#         raise HTTPException(status_code=403, detail="只有项目负责人可以审核工作包申请")

#     item = work_log.work_item
#     work_package = item.work_package if item else None
#     project = work_package.project if work_package else None
#     if not project or project.owner_id != str(reviewer_id):
#         raise HTTPException(status_code=403, detail="只能审核自己负责项目下的工作包申请")


# # ---------------------------------------------------------------- 待审核列表
# @router.get("/reviews/pending")
# def get_pending_reviews(user_id: str = Query(...), db: Session = Depends(get_db)):
#     reviewer = db.query(models.User).filter(models.User.id == str(user_id)).first()
#     if not reviewer or str(reviewer.role).upper() not in ["OWNER", "LEADER"]:
#         return {"code": 200, "data": []}

#     pending_logs = (
#         db.query(models.WorkLog)
#         .join(models.WorkItem, models.WorkLog.work_item_id == models.WorkItem.id)
#         .join(models.WorkPackage, models.WorkItem.work_package_id == models.WorkPackage.id)
#         .join(models.Project, models.WorkPackage.project_id == models.Project.id)
#         .filter(
#             models.WorkLog.status == "PENDING",
#             models.Project.owner_id == str(user_id)
#         )
#         .order_by(models.WorkLog.created_at.desc())
#         .all()
#     )

#     data = []
#     for log in pending_logs:
#         item = log.work_item
#         work_package = item.work_package if item else None
#         project = work_package.project if work_package else None
#         category = work_package.category if work_package else None
#         node = deadline_str(item.deadline) if item else ""
#         data.append({
#             "id": log.id,
#             "work_package_id": work_package.id if work_package else None,
#             "work_item_id": item.id if item else None,
#             "applicant_name": log.user.username if log.user else log.user_id,
#             "user_id": log.user_id,
#             "project_id": project.id if project else None,
#             "project_name": project.name if project else "-",
#             "project_owner_id": project.owner_id if project else "-",
#             "category_name": category.name if category else "-",
#             "work_package_name": work_package.name if work_package else "-",
#             "deadline": node or "-",
#             "node_requirement": node or "-",
#             "base_score": log.base_score,
#             "created_at": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-",
#             "status": log.status,
#         })

#     return {"code": 200, "data": data}


# # ---------------------------------------------------------------- 审核
# @router.post("/{log_id}")
# def review_log(log_id: str, decision: ReviewDecision, db: Session = Depends(get_db)):
#     work_log = db.query(models.WorkLog).filter(models.WorkLog.id == str(log_id)).first()
#     if not work_log:
#         raise HTTPException(status_code=404, detail="工作日志记录不存在")
#     if work_log.status != "PENDING":
#         raise HTTPException(status_code=400, detail="该申请已处理，不能重复审核")

#     ensure_project_owner(db, decision.reviewer_id, work_log)

#     work_log.reviewer_id = str(decision.reviewer_id)
#     work_log.review_comment = decision.remark or ("审核通过" if decision.approved else "")
#     if decision.approved:
#         item = work_log.work_item
#         base_score = (item.score if item and item.score else 0.0) or work_log.base_score
#         work_log.base_score = round(base_score * float(decision.weight or 1.0), 2)
#         work_log.status = "APPROVED"
#     else:
#         work_log.status = "REJECTED"
#         work_log.base_score = 0.0

#     db.commit()
#     return {
#         "code": 200,
#         "message": "审核通过" if decision.approved else "已驳回该申请",
#         "data": {"log_id": work_log.id, "status": work_log.status, "score_earned": work_log.base_score}
#     }


# @router.post("/reviews/{log_id}/approve")
# def approve_review(log_id: str, body: ReviewApprove, db: Session = Depends(get_db)):
#     """备用审核通过接口（前端历史 api 保留），按权重直接通过。"""
#     work_log = db.query(models.WorkLog).filter(models.WorkLog.id == str(log_id)).first()
#     if not work_log:
#         raise HTTPException(status_code=404, detail="工作日志记录不存在")
#     if work_log.status != "PENDING":
#         raise HTTPException(status_code=400, detail="该申请已处理，不能重复审核")

#     item = work_log.work_item
#     base_score = (item.score if item and item.score else 0.0) or work_log.base_score
#     work_log.base_score = round(base_score * float(body.weight or 1.0), 2)
#     work_log.status = "APPROVED"
#     work_log.review_comment = "审核通过"
#     db.commit()
#     return {
#         "code": 200,
#         "message": "审核通过",
#         "data": {"log_id": work_log.id, "status": work_log.status, "score_earned": work_log.base_score}
#     }


# # ---------------------------------------------------------------- 我负责的项目
# @router.get("/projects/my/{user_id}")
# def get_projects_for_current_user(user_id: str, db: Session = Depends(get_db)):
#     my_projects = db.query(models.Project).filter(models.Project.owner_id == str(user_id)).all()
#     data = []
#     for project in my_projects:
#         package_data = []
#         for wp in project.work_packages:
#             score, deadline = work_package_summary(wp)
#             owner_id = wp.owner_id or ""
#             owner = wp.owner
#             package_data.append({
#                 "id": wp.id,
#                 "project_id": wp.project_id,
#                 "name": wp.name,
#                 "score": score,
#                 "deadline": deadline or "-",
#                 "category_name": wp.category_name or "-",
#                 "current_assignee_id": owner_id,
#                 "current_assignee_name": owner.username if owner else "",
#             })
#         data.append({
#             "project_id": project.id,
#             "project_name": project.name,
#             "work_packages": package_data,
#         })
#     return {"code": 200, "data": data}


# # ---------------------------------------------------------------- 工作包指派
# @router.post("/projects/assign")
# def assign_work_package(req: TaskAssignCreate, db: Session = Depends(get_db)):
#     pkg = db.query(models.WorkPackage).filter(
#         models.WorkPackage.id == req.work_package_id
#     ).first()
#     if not pkg:
#         raise HTTPException(status_code=404, detail="工作包不存在")

#     project = pkg.project
#     if not project or project.owner_id != str(req.assigner_id):
#         raise HTTPException(status_code=403, detail="只能指派自己负责项目下的工作包")

#     assignee = db.query(models.User).filter(models.User.id == req.assignee_id).first()
#     if not assignee:
#         raise HTTPException(status_code=404, detail="指定员工不存在")

#     pkg.owner_id = req.assignee_id
#     db.commit()
#     return {"code": 200, "message": "工作包指派成功"}
