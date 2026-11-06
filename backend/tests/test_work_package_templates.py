# 工作包模板自动化测试文件
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from database import Base
from routers.work_package_templates import TemplateInput, create, list_for_package, update
from routers.information import NameInput, rename_information


def test_template_import_is_scoped_and_keeps_previous_snapshot():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        admin = models.User(id="admin", username="Admin", password="x", role="ADMIN", job_grade="P1")
        owner = models.User(id="owner", username="Owner", password="x", role="EMPLOYEE", job_grade="P1")
        outsider = models.User(id="other", username="Other", password="x", role="EMPLOYEE", job_grade="P1")
        category = models.WorkPackageCategory(name="研发")
        other_category = models.WorkPackageCategory(name="运维")
        db.add_all([admin, owner, outsider, category, other_category])
        db.flush()
        project = models.Project(code="P", name="项目", owner_id=owner.id)
        db.add(project)
        db.flush()
        package = models.WorkPackage(code="W", name="工作包", owner_id=owner.id,
                                     project_id=project.id, category_name=category.name)
        db.add(package)
        db.commit()

        payload = TemplateInput(category_id=category.id, name="常规拆分", items=[
            {"name": "设计", "standard": "完成设计文档", "deadline": "2026-11-30", "difficulty": "P2", "score": 5},
        ])
        saved = create(payload, db=db, user=admin)["data"]
        assert list_for_package(package.id, db=db, user=owner)["data"][0]["items"][0]["name"] == "设计"
        assert saved["items"][0]["deadline"] == "2026-11-30"
        assert list_for_package(package.id, db=db, user=owner)["data"][0]["items"][0]["deadline"] == "2026-11-30"
        snapshot = saved["items"][0].copy()

        updated = update(saved["id"], TemplateInput(category_id=category.id, name="常规拆分", items=[
            {"name": "评审", "score": 3},
        ]), db=db, user=admin)["data"]
        assert updated["items"][0]["name"] == "评审"
        assert updated["items"][0]["deadline"] is None
        assert snapshot["name"] == "设计"
        assert snapshot["deadline"] == "2026-11-30"

        # 模板行允许先不写名称；导入后由员工填写，模板仍保留该空行。
        unnamed = update(saved["id"], TemplateInput(category_id=category.id, name="常规拆分", items=[
            {"name": "", "standard": "按项目实际情况填写名称", "deadline": "2026-12-15"},
        ]), db=db, user=admin)["data"]
        assert unnamed["items"][0]["name"] == ""
        assert list_for_package(package.id, db=db, user=owner)["data"][0]["items"][0]["deadline"] == "2026-12-15"

        update(saved["id"], TemplateInput(category_id=category.id, name="常规拆分",
               is_active=False, items=[{"name": "评审", "score": 3}]), db=db, user=admin)
        assert list_for_package(package.id, db=db, user=owner)["data"] == []
        update(saved["id"], TemplateInput(category_id=category.id, name="常规拆分",
               items=[{"name": "评审", "score": 3}]), db=db, user=admin)

        old_category_id = category.id
        rename_information("work-categories", old_category_id, NameInput(name="新研发"), db=db, current_user=admin)
        db.refresh(package)
        assert package.category_name == "新研发"
        assert list_for_package(package.id, db=db, user=owner)["data"][0]["name"] == "常规拆分"

        from fastapi import HTTPException
        try:
            list_for_package(package.id, db=db, user=outsider)
            assert False, "another employee must not read this package's templates"
        except HTTPException as denied:
            assert denied.status_code == 403
        assert list_for_package(package.id, db=db, user=owner)["data"][0]["category_id"] != old_category_id
