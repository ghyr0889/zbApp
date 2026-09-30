"""信息管理回归测试：使用开启外键校验的内存 SQLite，不连接业务数据库。"""
import os
import unittest
from types import SimpleNamespace

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi import HTTPException
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import models
from database import Base
from routers.information import (
    NameInput, create_information, department_options, list_information,
    rename_information, require_admin, seed_departments,
)


class InformationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        # SQLite 要求被外键引用的名称有唯一索引，用严格约束验证类型改名顺序。
        with self.engine.begin() as connection:
            connection.execute(text("CREATE UNIQUE INDEX test_category_name ON work_package_categories(name)"))
        self.db = sessionmaker(bind=self.engine)()
        self.admin = SimpleNamespace(id="admin", role="ADMIN")
        self.db.add_all([
            models.User(id="u1", username="人员一", job_grade="P1", department="研发科"),
            models.User(id="u2", username="人员二", job_grade="P1", department="研发科", is_deleted=True),
            models.User(id="u3", username="人员三", job_grade="P1", department=None),
            models.Project(id=1, code="P", name="项目"),
            models.WorkPackageCategory(id=1, name="设计"),
        ])
        self.db.commit()
        self.db.add(models.WorkPackage(id=1, code="W", project_id=1, category_name="设计"))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_seed_and_empty_department_are_persistent(self):
        seed_departments(self.db)
        seed_departments(self.db)
        self.assertEqual(self.db.query(models.Department).count(), 1)
        create_information("departments", NameInput(name=" 新科室 "), self.db, self.admin)
        self.assertIn("新科室", department_options(self.db, self.admin)["data"])
        seed_departments(self.db)
        self.assertEqual(self.db.query(models.Department).count(), 2)

    def test_department_rename_updates_all_people(self):
        seed_departments(self.db)
        entry = self.db.query(models.Department).one()
        result = rename_information("departments", entry.id, NameInput(name="技术科"), self.db, self.admin)
        self.assertEqual(result["data"]["affected_count"], 2)
        self.db.expire_all()
        self.assertEqual(self.db.get(models.User, "u1").department, "技术科")
        self.assertEqual(self.db.get(models.User, "u2").department, "技术科")
        self.assertIsNone(self.db.get(models.User, "u3").department)

    def test_category_rename_preserves_work_package_with_foreign_key(self):
        result = rename_information("work-categories", 1, NameInput(name="研发设计"), self.db, self.admin)
        self.assertEqual(result["data"]["affected_count"], 1)
        self.db.expire_all()
        self.assertEqual(self.db.get(models.WorkPackage, 1).category_name, "研发设计")
        self.assertEqual(self.db.query(models.WorkPackageCategory).count(), 1)
        # 返回的新字典 ID 可以继续用于下一次修改。
        rename_information("work-categories", result["data"]["id"], NameInput(name="详细设计"), self.db, self.admin)
        self.db.expire_all()
        self.assertEqual(self.db.get(models.WorkPackage, 1).category_name, "详细设计")

    def test_duplicate_and_invalid_names(self):
        for name in ("设计", "  ", "长" * 101):
            with self.assertRaises(HTTPException):
                create_information("work-categories", NameInput(name=name), self.db, self.admin)
        other = create_information("work-categories", NameInput(name="测试"), self.db, self.admin)["data"]
        with self.assertRaises(HTTPException):
            rename_information("work-categories", other["id"], NameInput(name="设计"), self.db, self.admin)
        self.assertEqual(self.db.query(models.WorkPackageCategory).count(), 2)

    def test_failed_rename_rolls_back_entire_transaction(self):
        # 模拟其他表仍引用旧类型：删除旧名称失败时，新名称与工作包修改都必须回滚。
        self.db.execute(text("CREATE TABLE test_reference (name TEXT REFERENCES work_package_categories(name))"))
        self.db.execute(text("INSERT INTO test_reference(name) VALUES ('设计')"))
        self.db.commit()
        with self.assertRaises(HTTPException):
            rename_information("work-categories", 1, NameInput(name="新名称"), self.db, self.admin)
        self.db.expire_all()
        self.assertEqual(self.db.get(models.WorkPackage, 1).category_name, "设计")
        self.assertEqual([row.name for row in self.db.query(models.WorkPackageCategory)], ["设计"])

    def test_permission_and_list(self):
        self.assertEqual(require_admin(self.admin), self.admin)
        for role in ("EMPLOYEE", "LEADER", "DEPARTMENT"):
            with self.assertRaises(HTTPException) as error:
                require_admin(SimpleNamespace(role=role))
            self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(list_information("work-categories", self.db, self.admin)["data"], [{"id": 1, "name": "设计"}])
        with self.assertRaises(HTTPException) as error:
            rename_information("departments", 999, NameInput(name="科室"), self.db, self.admin)
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
