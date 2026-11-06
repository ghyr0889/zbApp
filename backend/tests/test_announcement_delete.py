"""Deletion respects publisher permissions, publication state, and role links."""
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from database import Base
from exceptions import BusinessError, PermissionDenied
from services.announcement_service import delete_announcement


class AnnouncementDeleteTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.owner = models.User(id="owner", username="owner", password="x", role="LEADER", job_grade="P1")
        self.other = models.User(id="other", username="other", password="x", role="LEADER", job_grade="P1")
        self.admin = models.User(id="admin", username="admin", password="x", role="ADMIN", job_grade="P1")
        self.db.add_all([self.owner, self.other, self.admin])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def add_announcement(self, status):
        row = models.Announcement(title="测试公告", content="正文", publisher_id=self.owner.id,
                                  audience_mode="ROLE", status=status)
        self.db.add(row)
        self.db.flush()
        self.db.add(models.AnnouncementRole(announcement_id=row.id, role="EMPLOYEE"))
        self.db.commit()
        return row.id

    def test_draft_delete_removes_role_links(self):
        announcement_id = self.add_announcement("DRAFT")
        with self.assertRaises(PermissionDenied):
            delete_announcement(self.db, announcement_id, self.other)
        self.assertIsNotNone(self.db.get(models.Announcement, announcement_id))
        delete_announcement(self.db, announcement_id, self.owner)
        self.assertIsNone(self.db.get(models.Announcement, announcement_id))
        self.assertEqual(self.db.query(models.AnnouncementRole).filter_by(announcement_id=announcement_id).count(), 0)

    def test_published_must_be_withdrawn_first(self):
        announcement_id = self.add_announcement("PUBLISHED")
        with self.assertRaises(BusinessError):
            delete_announcement(self.db, announcement_id, self.admin)
        row = self.db.get(models.Announcement, announcement_id)
        row.status = "WITHDRAWN"
        self.db.commit()
        delete_announcement(self.db, announcement_id, self.admin)
        self.assertIsNone(self.db.get(models.Announcement, announcement_id))


if __name__ == "__main__":
    unittest.main()
