"""工作包变更的数据访问；事务由服务层统一提交。"""
import models
from sqlalchemy import case

# 查找工作包
def package(db, package_id):
    return db.query(models.WorkPackage).filter_by(id=package_id).with_for_update().first()

# 按申请编号查找一条申请
def request(db, request_id):
    return db.query(models.WorkPackageChangeRequest).filter_by(id=request_id).with_for_update().first()

# 查找工作包是否已有待审核申请
def pending(db, package_id):
    return db.query(models.WorkPackageChangeRequest).filter_by(
        work_package_id=package_id, status="PENDING").first()

# 查询当前用户可以查看的申请列表
def requests(db, user):
    query = db.query(models.WorkPackageChangeRequest)
    if user.role.upper() != "LEADER":
        query = query.filter_by(applicant_id=user.id)
    return query.order_by(
        case(
            (models.WorkPackageChangeRequest.status == "PENDING", 0),
            else_=1,
        ),
        models.WorkPackageChangeRequest.created_at.desc(),
        models.WorkPackageChangeRequest.id.desc(),
    ).all()
