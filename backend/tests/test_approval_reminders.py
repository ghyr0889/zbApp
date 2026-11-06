"""Approval reminders must match the actual review permissions and status."""

import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from database import Base
from services.approval_reminder_service import list_approval_reminders


class ApprovalReminderTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.engine = engine
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        for user_id, role in (("department", "DEPARTMENT"), ("leader", "LEADER"),
                              ("admin", "ADMIN"), ("employee", "EMPLOYEE")):
            self.db.add(models.User(id=user_id, username=user_id, password="x", role=role, job_grade="P1"))
        self.db.add(models.WorkPackageCategory(name="type"))
        self.db.flush()
        project = models.Project(code="P", name="project", owner_id="employee")
        self.db.add(project)
        self.db.flush()
        package = models.WorkPackage(code="W", name="package", owner_id="employee",
                                     project_id=project.id, category_name="type")
        self.db.add(package)
        self.db.flush()
        self.db.add_all([
            models.WorkPackageSplitRequest(work_package_id=package.id, applicant_id="employee",
                                           reason="split", split_items="[]", status="PENDING"),
            models.WorkPackageSplitRequest(work_package_id=package.id, applicant_id="employee",
                                           reason="split", split_items="[]", status="SUBMITTED"),
            models.WorkPackageChangeRequest(action="update", work_package_id=package.id,
                                            project_id=project.id, applicant_id="employee", status="PENDING"),
        ])
        item = models.WorkItem(name="item", work_package_id=package.id, owner_id="employee",
                               tech_owner_id="department", difficulty="P1", importance="I",
                               innovation="low", score=1, deadline=datetime(2026, 11, 1))
        self.db.add(item)
        self.db.flush()
        self.db.add(models.WorkItemCompletionReview(work_item_id=item.id, applicant_id="employee", status="PENDING"))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_role_specific_approvals(self):
        expected = {
            "department": {"split_approval", "completion_approval"},
            "leader": {"split_approval", "package_change_approval"},
            "admin": {"split_approval"},
            "employee": set(),
        }
        for user_id, kinds in expected.items():
            with self.subTest(user=user_id):
                viewer = self.db.get(models.User, user_id)
                rows = list_approval_reminders(self.db, viewer)
                self.assertEqual({row["kind"] for row in rows}, kinds)
                self.assertTrue(all(row["tab"] in ("review", "complete", "packageChanges") for row in rows))


if __name__ == "__main__":
    unittest.main()
