"""后台信息管理：新增、改名科室及工作包类型，不提供删除接口。"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/api/v1/admin", tags=["信息管理"])
Kind = Literal["departments", "work-categories"]


class NameInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


def seed_departments(db):
    """启动时收录历史人员科室；已有字典数据保留，包括暂时没有人员的科室。"""
    names = {name.strip() for (name,) in db.query(models.User.department).distinct()
             if name and name.strip()}
    for name in names:
        if db.query(models.Department.id).filter(models.Department.name == name).first():
            continue
        try:
            # 多进程同时启动时，唯一约束负责去重；冲突只回滚当前插入。
            with db.begin_nested():
                db.add(models.Department(name=name))
                db.flush()
        except IntegrityError:
            pass
    db.commit()


def require_admin(current_user=Depends(get_current_user)):
    if str(current_user.role).upper() != "ADMIN":
        raise HTTPException(403, "只有管理员可以维护科室和工作包类型")
    return current_user


def model_for(kind):
    return models.Department if kind == "departments" else models.WorkPackageCategory


def normalized_name(kind, body):
    name = body.name.strip()
    limit = 255 if kind == "departments" else 100
    if not name or len(name) > limit:
        raise HTTPException(400, f"名称不能为空，且不能超过{limit}个字符")
    return name


@router.get("/departments")
def department_options(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """人员表单读取统一科室选项；新建的空科室也能选择。"""
    rows = db.query(models.Department.name).order_by(models.Department.name).all()
    return {"code": 200, "data": [name for (name,) in rows]}


@router.get("/information/{kind}")
def list_information(kind: Kind, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    Model = model_for(kind)
    rows = db.query(Model).order_by(Model.name, Model.id).all()
    return {"code": 200, "data": [{"id": row.id, "name": row.name} for row in rows]}


@router.post("/information/{kind}")
def create_information(kind: Kind, body: NameInput, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    Model = model_for(kind)
    name = normalized_name(kind, body)
    try:
        if db.query(Model.id).filter(Model.name == name).first():
            raise HTTPException(400, "该名称已存在，请勿重复新增")
        row = Model(name=name)
        db.add(row)
        db.flush()
        data = {"id": row.id, "name": row.name}
        db.commit()
        return {"code": 200, "message": "新增成功", "data": data}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "保存失败，请检查名称是否已存在")
    except Exception:
        db.rollback()
        raise


@router.put("/information/{kind}/{entry_id}")
def rename_information(kind: Kind, entry_id: int, body: NameInput, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    Model = model_for(kind)
    name = normalized_name(kind, body)
    try:
        row = db.query(Model).filter(Model.id == entry_id).with_for_update().first()
        if row is None:
            raise HTTPException(404, "记录不存在，请刷新后重试")
        if db.query(Model.id).filter(Model.name == name, Model.id != entry_id).first():
            raise HTTPException(400, "该名称已存在，不能改为同名记录")
        affected = 0
        if row.name != name:
            old_name = row.name
            if kind == "departments":
                # 包含历史停用人员，避免以后恢复人员时出现旧科室名称。
                affected = db.query(models.User).filter(func.trim(models.User.department) == old_name).update(
                    {models.User.department: name}, synchronize_session=False)
                row.name = name
            else:
                # 工作包通过类别名称外键关联，不能直接更新被引用的旧名称。
                # 先创建新名称，再迁移所有工作包，最后删除旧字典记录；整个过程一起提交。
                # 新字典 ID 由数据库分配，接口返回最新 ID，工作包本身的 ID 不变。
                replacement = Model(name=name)
                db.add(replacement)
                db.flush()
                affected = db.query(models.WorkPackage).filter(models.WorkPackage.category_name == old_name).update(
                    {models.WorkPackage.category_name: name}, synchronize_session=False)
                db.query(Model).filter(Model.id == entry_id).delete(synchronize_session=False)
                row = replacement
        db.flush()
        data = {"id": row.id, "name": row.name, "affected_count": affected}
        db.commit()
        return {"code": 200, "message": "保存成功，相关记录已同步", "data": data}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "保存失败，名称重复或仍有关联约束，请刷新后检查")
    except Exception:
        db.rollback()
        raise
