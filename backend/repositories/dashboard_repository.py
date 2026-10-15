"""看板数据查询：按工作项截止日期选取周期，避免多表明细连接重复计数。"""
from sqlalchemy.orm import joinedload
import models


def list_items(db, start, end):
    return (db.query(models.WorkItem)
            .options(joinedload(models.WorkItem.owner),
                     joinedload(models.WorkItem.work_package).joinedload(models.WorkPackage.project))
            .filter(models.WorkItem.deadline >= start, models.WorkItem.deadline < end)
            .all())
