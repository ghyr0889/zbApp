"""回归测试：四类申请仅允许发起人在待处理阶段终止，且不可重复终止。"""

import unittest
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from database import Base
from services.approval_termination_service import terminate_request


class ApprovalTerminationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([
            models.User(id='applicant', username='Applicant', password='x', role='EMPLOYEE', job_grade='P1'),
            models.User(id='other', username='Other', password='x', role='EMPLOYEE', job_grade='P1'),
            models.WorkPackageCategory(name='type'),
        ])
        self.db.flush()
        project = models.Project(code='P', name='Project', owner_id='applicant')
        self.db.add(project)
        self.db.flush()
        package = models.WorkPackage(code='W', name='Package', owner_id='applicant',
                                     project_id=project.id, category_name='type')
        self.db.add(package)
        self.db.flush()
        item = models.WorkItem(name='Item', work_package_id=package.id, owner_id='applicant',
                               tech_owner_id='other', difficulty='P1', importance='I',
                               innovation='low', score=1, deadline=datetime(2026, 11, 1))
        self.db.add(item)
        self.db.flush()
        self.rows = [
            (models.WorkPackageSplitRequest(work_package_id=package.id, applicant_id='applicant',
                                            reason='reason', split_items='[]', status='SUBMITTED'),
             models.WorkPackageSplitRequest.applicant_id, ('PENDING', 'SUBMITTED')),
            (models.WorkPackageChangeRequest(action='update', work_package_id=package.id,
                                             project_id=project.id, applicant_id='applicant', status='PENDING'),
             models.WorkPackageChangeRequest.applicant_id, ('PENDING',)),
            (models.WorkItemCompletionReview(work_item_id=item.id, applicant_id='applicant', status='PENDING'),
             models.WorkItemCompletionReview.applicant_id, ('PENDING',)),
            (models.TaskTransfer(work_package_id=package.id, work_item_id=item.id,
                                 from_user_id='applicant', to_user_id='other', status='PENDING'),
             models.TaskTransfer.from_user_id, ('PENDING',)),
        ]
        self.db.add_all(row for row, _, _ in self.rows)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_only_applicant_can_terminate_pending_requests(self):
        for row, owner_field, statuses in self.rows:
            with self.subTest(model=type(row).__name__):
                with self.assertRaises(HTTPException) as unauthorized:
                    terminate_request(self.db, type(row), row.id, 'other', owner_field, statuses)
                self.assertEqual(unauthorized.exception.status_code, 403)
                response = terminate_request(self.db, type(row), row.id, 'applicant', owner_field, statuses)
                self.assertEqual(response['data']['status'], 'TERMINATED')
                self.assertEqual(self.db.get(type(row), row.id).status, 'TERMINATED')
                with self.assertRaises(HTTPException) as repeated:
                    terminate_request(self.db, type(row), row.id, 'applicant', owner_field, statuses)
                self.assertEqual(repeated.exception.status_code, 409)


if __name__ == '__main__':
    unittest.main()
