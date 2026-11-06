"""工作待办测试."""
import unittest
from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from database import Base
from services.work_reminder_service import list_work_reminders


class WorkReminderTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.today = date(2026, 10, 25)
        self.db.add_all([
            models.User(id="owner", username="owner", password="x", role="EMPLOYEE", job_grade="P1"),
            models.User(id="other", username="other", password="x", role="EMPLOYEE", job_grade="P1"),
            models.WorkPackageCategory(name="测试类型"),
        ])
        self.db.flush()
        project = models.Project(code="P", name="项目", owner_id="owner")
        self.db.add(project)
        self.db.flush()
        self.project_id = project.id

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def package(self, owner="owner", closed=False):
        row = models.WorkPackage(code="W", name="包", owner_id=owner, project_id=self.project_id,
                                 category_name="测试类型", isclosed=closed)
        self.db.add(row)
        self.db.flush()
        return row

    def item(self, package, offset, owner="owner", complete=False):
        row = models.WorkItem(name=f"工作项{offset}", work_package_id=package.id,
                              difficulty="P1", importance="I", innovation="低", score=1,
                              deadline=datetime.combine(self.today + timedelta(days=offset), datetime.min.time()),
                              owner_id=owner, tech_owner_id="owner", complete_status=complete)
        self.db.add(row)
        self.db.flush()
        return row

    def test_deadline_boundaries_and_owner(self):
        package = self.package()
        for offset in (-3, -1, 0, 1, 3, 4):
            self.item(package, offset)
        self.item(package, -1, owner="other")
        self.item(package, -1, complete=True)
        self.db.commit()
        rows = list_work_reminders(self.db, "owner", self.today)
        self.assertEqual([row["kind"] for row in rows],
                         ["overdue", "overdue", "due_today", "due_soon", "due_soon"])
        self.assertEqual([row["days"] for row in rows], [-3, -1, 0, 1, 3])
        self.assertTrue(all(row["project_id"] == self.project_id and row["package_page"] == 1 for row in rows))

    def test_undecomposed_excludes_pending_and_closed(self):
        active = self.package()
        pending = self.package()
        self.package(owner="other")
        self.package(closed=True)
        self.db.add(models.WorkPackageSplitRequest(work_package_id=pending.id, applicant_id="owner",
                                                   reason="拆分", split_items="[]", status="PENDING"))
        self.db.commit()
        rows = list_work_reminders(self.db, "owner", self.today)
        self.assertEqual([(row["kind"], row["work_package_id"]) for row in rows],
                         [("undecomposed", active.id)])


if __name__ == "__main__":
    unittest.main()
