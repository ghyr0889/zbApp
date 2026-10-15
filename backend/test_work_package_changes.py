"""使用内存数据库验证审批流程，不连接或修改业务数据库。"""
import unittest
from datetime import datetime
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from database import Base
import models
from schemas import WorkPackageCreate
from services import work_package_change_service as service
from routers.pending import _package_changes_pending, get_pending_summary


class PackageChangeTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:')
        event.listen(engine, 'connect', lambda connection, _: connection.execute('PRAGMA foreign_keys=ON'))
        Base.metadata.create_all(engine)
        # SQLite 外键要求被引用列唯一；仅给测试库补索引以兼容现有 MySQL 模型。
        with engine.begin() as connection:
            connection.execute(text('CREATE UNIQUE INDEX test_category_name ON work_package_categories(name)'))
        self.db = sessionmaker(bind=engine, autoflush=False)()
        self.admin = models.User(id='a', username='admin', role='ADMIN', job_grade='P1')
        self.leader = models.User(id='l', username='leader', role='LEADER', job_grade='P1')
        self.employee = models.User(id='e', username='employee', role='EMPLOYEE', job_grade='P1')
        self.department = models.User(id='d', username='department', role='DEPARTMENT', job_grade='P1')
        self.db.add_all([self.admin, self.leader, self.employee, self.department,
                         models.Project(id=1, code='P', name='project', category='test'),
                         models.WorkPackageCategory(name='test')])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def body(self, **kwargs):
        return WorkPackageCreate(project_id=1, work_package_code='WP', category_name='test',
                                 owner_id='e', tech_owner_id='l', reason=kwargs.pop('reason', '调整工作安排'), **kwargs)

    def create(self):
        result = service.submit(self.db, self.department, self.body(name='original'))
        request_id = result['data']['request_id']
        self.assertEqual(self.db.query(models.WorkPackage).count(), 0)
        service.review(self.db, self.leader, request_id, 'APPROVE', '')
        return self.db.query(models.WorkPackage).one()

    def test_create_permissions_and_repeat_review(self):
        for user in (self.employee, self.leader):
            with self.assertRaises(HTTPException): service.submit(self.db, user, self.body())
        req_id = service.submit(self.db, self.admin, self.body())['data']['request_id']
        for user in (self.admin, self.department, self.employee):
            with self.assertRaises(HTTPException): service.review(self.db, user, req_id, 'APPROVE', '')
        service.review(self.db, self.leader, req_id, 'APPROVE', '')
        with self.assertRaises(HTTPException): service.review(self.db, self.leader, req_id, 'APPROVE', '')
        self.assertEqual(self.db.query(models.WorkPackage).count(), 1)

    def test_update_reject_conflict_and_approve(self):
        pkg = self.create()
        req_id = service.submit(self.db, self.admin, self.body(id=pkg.id, name='new'))['data']['request_id']
        self.assertEqual(pkg.name, 'original')
        with self.assertRaises(HTTPException): service.submit(self.db, self.admin, package_id=pkg.id, reason='取消任务')
        service.review(self.db, self.leader, req_id, 'REJECT', 'no')
        self.assertEqual(pkg.name, 'original')
        req_id = service.submit(self.db, self.admin, self.body(id=pkg.id, name='new'))['data']['request_id']
        pkg.name = 'changed elsewhere'
        self.db.commit()
        with self.assertRaises(HTTPException): service.review(self.db, self.leader, req_id, 'APPROVE', '')
        self.assertEqual(self.db.get(models.WorkPackageChangeRequest, req_id).status, 'PENDING')
        service.review(self.db, self.leader, req_id, 'REJECT', '')
        req_id = service.submit(self.db, self.admin, self.body(id=pkg.id, name='new'))['data']['request_id']
        service.review(self.db, self.leader, req_id, 'APPROVE', '')
        self.assertEqual(pkg.name, 'new')

    def test_delete_retains_history(self):
        pkg = self.create()
        req_id = service.submit(self.db, self.admin, package_id=pkg.id, reason='取消任务')['data']['request_id']
        self.assertEqual(self.db.query(models.WorkPackage).count(), 1)
        service.review(self.db, self.leader, req_id, 'APPROVE', '')
        self.assertEqual(self.db.query(models.WorkPackage).count(), 0)
        self.assertEqual(self.db.query(models.WorkPackageChangeRequest).count(), 2)
        self.assertTrue(all(r.work_package_id is None for r in self.db.query(models.WorkPackageChangeRequest)))

    def test_create_rejected_and_list_scope(self):
        req_id = service.submit(self.db, self.admin, self.body())['data']['request_id']
        service.review(self.db, self.leader, req_id, 'REJECT', 'no')
        self.assertEqual(self.db.query(models.WorkPackage).count(), 0)
        self.assertEqual(len(service.list_requests(self.db, self.employee)['data']), 0)
        self.assertEqual(len(service.list_requests(self.db, self.leader)['data']), 1)

    def test_delete_rechecks_dependencies(self):
        pkg = self.create()
        req_id = service.submit(self.db, self.admin, package_id=pkg.id, reason='取消任务')['data']['request_id']
        self.db.add(models.WorkItem(name='item', difficulty='P1', importance='I', innovation='none',
            deadline=datetime.now(), owner_id='e', tech_owner_id='l', work_package_id=pkg.id))
        self.db.commit()
        with self.assertRaises(HTTPException): service.review(self.db, self.leader, req_id, 'APPROVE', '')
        self.assertEqual(self.db.get(models.WorkPackageChangeRequest, req_id).status, 'PENDING')
        self.assertEqual(self.db.query(models.WorkPackage).count(), 1)
        self.assertEqual(self.db.query(models.WorkItem).count(), 1)

    def test_reason_required_and_preserved(self):
        for reason in ('   ', 'x' * 2001):
            # 绕过请求模型测试服务层，确保直接调用也无法写入无效原因。
            body = self.body()
            body.reason = reason
            with self.assertRaises(HTTPException):
                service.submit(self.db, self.admin, body)
        self.assertEqual(self.db.query(models.WorkPackageChangeRequest).count(), 0)
        pkg = self.create()
        with self.assertRaises(HTTPException):
            service.submit(self.db, self.admin, package_id=pkg.id, reason='  ')
        req_id = service.submit(self.db, self.admin, package_id=pkg.id,
                                reason='  任务取消\n无需保留空工作包  ')['data']['request_id']
        record = self.db.get(models.WorkPackageChangeRequest, req_id)
        self.assertEqual(record.reason, '任务取消\n无需保留空工作包')
        service.review(self.db, self.leader, req_id, 'APPROVE', '')
        listed = service.list_requests(self.db, self.admin)['data']
        self.assertEqual(listed[0]['reason'], record.reason)

    def test_package_pending_counts_only_leader_and_pending(self):
        first = service.submit(self.db, self.admin, self.body())['data']['request_id']
        second = service.submit(self.db, self.department, self.body())['data']['request_id']
        self.assertEqual(_package_changes_pending(self.db, 'LEADER'), 2)
        for role in ('ADMIN', 'DEPARTMENT', 'EMPLOYEE'):
            self.assertEqual(_package_changes_pending(self.db, role), 0)
        summary = get_pending_summary(user_id=self.leader.id, db=self.db)['data']
        self.assertEqual(summary['packageChanges'], 2)
        self.assertEqual(summary['total'], sum(summary[k] for k in ('review', 'complete', 'transfers', 'packageChanges')))
        service.review(self.db, self.leader, first, 'REJECT', '')
        self.assertEqual(_package_changes_pending(self.db, 'LEADER'), 1)
        service.review(self.db, self.leader, second, 'APPROVE', '')
        self.assertEqual(_package_changes_pending(self.db, 'LEADER'), 0)


if __name__ == '__main__':
    unittest.main()
