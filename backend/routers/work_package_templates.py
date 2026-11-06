# 工作包模板接口
from datetime import date, datetime
from math import isfinite

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

import models
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/api/v1/work-package-templates", tags=["工作包模板"])


class TemplateItemInput(BaseModel):
    name: str = Field(default="", max_length=100)
    standard: str = ""
    deadline: date | None = None
    difficulty: str = Field(default="", max_length=50)
    importance: str = Field(default="", max_length=50)
    innovation: str = Field(default="", max_length=50)
    score: float = 0
    notes: str = ""


class TemplateInput(BaseModel):
    category_id: int
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    is_active: bool = True
    items: list[TemplateItemInput] = Field(..., min_length=1, max_length=100)


def require_admin(user=Depends(get_current_user)):
    if str(user.role).upper() != "ADMIN":
        raise HTTPException(403, "只有管理员可以维护工作包模板")
    return user


# 把数据库对象整理成前端使用的 JSON
def serialize(template):
    return {
        "id": template.id,
        "category_id": template.category_id,
        "name": template.name,
        "description": template.description or "",
        "is_active": template.is_active,
        "items": [{
            "id": item.id, "name": item.name, "standard": item.standard or "",
            "deadline": item.deadline.isoformat() if item.deadline else None,
            "difficulty": item.difficulty or "", "importance": item.importance or "",
            "innovation": item.innovation or "", "score": item.score,
            "notes": item.notes or "",
        } for item in template.items],
    }

# 保存前校验数据
def validate(body, db):
    if not db.get(models.WorkPackageCategory, body.category_id):
        raise HTTPException(404, "工作包类型不存在")
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "请填写模板名称")
    for index, item in enumerate(body.items, 1):
        if not isfinite(item.score) or item.score < 0:
            raise HTTPException(400, f"第 {index} 个工作项建议分值必须为非负有限数")
    return name

# 把模板工作项写入关联表
def replace_items(template, items):
    template.items = [models.WorkPackageTemplateItem(
        sort_order=index, name=item.name.strip(), standard=item.standard, deadline=item.deadline,
        difficulty=item.difficulty, importance=item.importance,
        innovation=item.innovation, score=item.score, notes=item.notes,
    ) for index, item in enumerate(items)]


@router.get("/admin")
def list_admin(category_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    rows = db.query(models.WorkPackageTemplate).options(
        selectinload(models.WorkPackageTemplate.items)
    ).filter(models.WorkPackageTemplate.category_id == category_id).order_by(
        models.WorkPackageTemplate.id.desc()
    ).all()
    return {"code": 200, "data": [serialize(row) for row in rows]}


@router.post("/admin")
def create(body: TemplateInput, db: Session = Depends(get_db), user=Depends(require_admin)):
    name = validate(body, db)
    row = models.WorkPackageTemplate(
        category_id=body.category_id, name=name, description=body.description,
        is_active=body.is_active, created_by=user.id,
    )
    replace_items(row, body.items)
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "该工作包类型下已有同名模板")
    return {"code": 200, "data": serialize(row)}


@router.put("/admin/{template_id}")
def update(template_id: int, body: TemplateInput, db: Session = Depends(get_db), user=Depends(require_admin)):
    row = db.query(models.WorkPackageTemplate).options(
        selectinload(models.WorkPackageTemplate.items)
    ).filter(models.WorkPackageTemplate.id == template_id).with_for_update().first()
    if row is None:
        raise HTTPException(404, "模板不存在")
    if row.category_id != body.category_id:
        raise HTTPException(400, "不能修改模板所属工作包类型")
    row.name = validate(body, db)
    row.description = body.description
    row.is_active = body.is_active
    row.updated_at = datetime.now()
    replace_items(row, body.items)
    try:
        db.commit()
        db.refresh(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "该工作包类型下已有同名模板")
    return {"code": 200, "data": serialize(row)}


@router.delete("/admin/{template_id}")
def delete(template_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    row = db.get(models.WorkPackageTemplate, template_id)
    if row is None:
        raise HTTPException(404, "模板不存在")
    db.delete(row)
    db.commit()
    return {"code": 200, "data": {"id": template_id}}

# 给当前工作包返回可用模板
@router.get("/for-package/{package_id}")
def list_for_package(package_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    package = db.get(models.WorkPackage, package_id)
    if package is None:
        raise HTTPException(404, "工作包不存在")
    if package.isclosed or (package.project and package.project.isclosed):
        raise HTTPException(409, "工作包或所属项目已关闭")
    if str(user.role).upper() not in ("ADMIN", "LEADER", "DEPARTMENT") and str(package.owner_id) != str(user.id):
        raise HTTPException(403, "只能导入自己负责的工作包模板")
    category = db.query(models.WorkPackageCategory).filter(
        models.WorkPackageCategory.name == package.category_name
    ).first()
    if category is None:
        return {"code": 200, "data": []}
    rows = db.query(models.WorkPackageTemplate).options(
        selectinload(models.WorkPackageTemplate.items)
    ).filter(
        models.WorkPackageTemplate.category_id == category.id,
        models.WorkPackageTemplate.is_active.is_(True),
    ).order_by(models.WorkPackageTemplate.name).all()
    return {"code": 200, "data": [serialize(row) for row in rows]}
