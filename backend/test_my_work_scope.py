"""个人工作筛选回归测试，仅使用内存数据库。"""
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from database import Base
import models
from repositories import work_logs_repository as repo
from services import work_logs_service as service
from routers import work_logs as router
from services import score_board_service as score_service
from routers import score_board as score_router
from schemas import ConfirmCompletionIn, ConfirmClosed


class MyWorkScopeTests(unittest.TestCase):
    def test_project_reopen_roles_and_target_boundaries(self):
        project = self.db.get(models.Project, 1)
        for role in ('DEPARTMENT', 'LEADER', 'ADMIN'):
            self.user.role = role
            project.complete_status = True
            project.isclosed = True
            self.db.commit()
            service.confirm_closed(ConfirmClosed(target_type='project', target_id=1, user_id='a', confirmed=False), self.db)
            self.assertFalse(project.isclosed)
            service.confirm_completion(ConfirmCompletionIn(target_type='project', target_id=1, user_id='a', confirmed=False), self.db)
            self.assertFalse(project.complete_status)
        for role in ('EMPLOYEE', 'DEPARTMENT', 'LEADER'):
            self.user.role = role
            self.db.commit()
            if role == 'EMPLOYEE':
                with self.assertRaises(HTTPException):
                    service.confirm_closed(ConfirmClosed(target_type='project', target_id=1, user_id='a', confirmed=False), self.db)
                with self.assertRaises(HTTPException):
                    service.confirm_completion(ConfirmCompletionIn(target_type='project', target_id=1, user_id='a', confirmed=False), self.db)
            if role == 'DEPARTMENT':
                with self.assertRaises(HTTPException):
                    service.confirm_closed(ConfirmClosed(target_type='project', target_id=1, user_id='a', confirmed=True), self.db)
            with self.assertRaises(HTTPException):
                service.confirm_closed(ConfirmClosed(target_type='work_package', target_id=1, user_id='a', confirmed=False), self.db)

    def test_completion_routes_use_authenticated_user(self):
        for route, method, schema in ((router.confirm_closed, 'confirm_closed', ConfirmClosed),
                                       (router.confirm_completion, 'confirm_completion', ConfirmCompletionIn)):
            body = schema(target_type='project', target_id=1, user_id='other', confirmed=False)
            with patch.object(service, method, return_value={}) as call:
                route(body, db=self.db, user=self.user)
                self.assertEqual(call.call_args.kwargs['data'].user_id, self.user.id)
                self.assertEqual(body.user_id, 'other')

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = models.User(id='a', username='A', job_grade='P1', role='ADMIN')
        self.db.add_all([self.user, models.User(id='b', username='B', job_grade='P1'),
                         models.Project(id=1, code='P', name='P', category='test'),
                         models.WorkPackage(id=1, code='mixed', project_id=1, category_name='test'),
                         models.WorkPackage(id=2, code='owned-package', owner_id='a', project_id=1, category_name='test'),
                         models.WorkPackage(id=3, code='un-decomposed', owner_id='a', project_id=1, category_name='test')])
        for item_id, package_id, owner_id in [(1, 1, 'a'), (2, 1, 'b'), (3, 2, 'b')]:
            self.db.add(models.WorkItem(id=item_id, name=str(item_id), work_package_id=package_id,
                         owner_id=owner_id, tech_owner_id='a', difficulty='', importance='',
                         innovation='', deadline=datetime(2030, 1, 1), score=10))
        self.db.add(models.WorkItemMonthlyScore(work_item_id=1, user_id='a', month='2026-10', score=5))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_packages_and_items_are_scoped_to_owner(self):
        total, packages = repo.list_my_packages_page(self.db, 'a', 1, 20)
        self.assertEqual((total, [p.id for p in packages]), (3, [1, 2, 3]))
        empty_package = service.get_my_work_packages_paged('a', db=self.db)['data']['items'][2]
        self.assertFalse(empty_package['is_decomposed'])
        self.assertEqual(empty_package['work_item_count'], 0)
        self.assertEqual(empty_package['package_progress'], 0)
        self.assertEqual(repo.list_my_packages_page(self.db, 'a', 1, 1)[0], 3)
        self.assertEqual([i.id for i in repo.list_package_items(self.db, 1, 'a')], [1])
        self.assertEqual([i.id for i in repo.list_package_items(self.db, 1)], [1, 2])

    def test_personal_progress_and_transfer(self):
        result = service.get_my_work_packages_paged('a', db=self.db)['data']['items']
        self.assertEqual(result[0]['work_item_count'], 1)
        self.assertEqual(result[0]['package_progress'], 50)
        self.db.get(models.WorkItem, 1).owner_id = 'b'
        self.db.commit()
        self.assertEqual(repo.list_my_packages_page(self.db, 'a', 1, 20)[0], 2)

    def test_leader_assignment_list_and_personal_view(self):
        leader = models.User(id='l', username='Leader', job_grade='P1', role='LEADER')
        self.db.add(leader)
        self.db.commit()
        result = router.list_assignments(db=self.db, user=leader)['data']
        rows = {row['user_id']: row for row in result['items']}
        self.assertEqual(result['total'], 3)
        self.assertEqual(rows['a']['work_item_count'], 1)
        self.assertEqual(rows['a']['total_score'], 10)
        self.assertEqual(rows['b']['work_item_count'], 2)
        self.assertEqual(rows['l']['work_item_count'], 0)
        personal = service.get_my_work_packages_paged('a', db=self.db, show_completed=False)
        observed = router.assigned_packages('a', db=self.db, user=leader)
        self.assertEqual(observed['data']['items'], personal['data']['items'])
        items = router.get_work_items('1', view_user_id='a', db=self.db, user=leader)
        self.assertEqual([item['id'] for item in items['data']['work_items']], [1])
        with self.assertRaises(HTTPException):
            router.list_assignments(db=self.db, user=self.user)
        with self.assertRaises(HTTPException):
            router.assigned_packages('a', db=self.db, user=self.user)
        with self.assertRaises(HTTPException):
            router.get_work_items('1', view_user_id='b', db=self.db, user=self.user)
        with self.assertRaises(HTTPException):
            router.assigned_packages('missing', db=self.db, user=leader)

    def test_completion_and_related_filters(self):
        self.db.get(models.WorkItem, 1).complete_status = True
        self.db.commit()
        self.assertEqual(repo.list_my_packages_page(self.db, 'a', 1, 20, False)[0], 2)
        self.assertEqual(repo.list_package_items(self.db, 1, 'a', False), [])
        self.assertEqual([i.id for i in repo.list_package_items(self.db, 1, 'a', True)], [1])
        # 无需转办记录，同包他人工作项可只读查看，但不能跨到无本人工作项的包。
        self.assertEqual([i.id for i in repo.list_package_items(self.db, 1, 'a', False, True)], [2])
        self.assertEqual([i.id for i in repo.list_package_items(self.db, 1, 'a', True, True)], [1, 2])
        self.assertEqual(repo.list_my_packages_page(self.db, 'a', 1, 20, False, True)[0], 3)
        self.assertEqual(repo.list_package_items(self.db, 2, 'a', True, True), [])
        result = service.get_work_items('1', db=self.db, owner_id='a', show_related=True)
        self.assertEqual([r['is_related'] for r in result['data']['work_items']], [False, True])
        # 项目详情默认不受个人完成状态筛选影响。
        self.assertEqual(len(repo.list_package_items(self.db, 1)), 2)
        self.db.get(models.WorkItem, 2).complete_status = True
        self.db.commit()
        self.assertEqual(repo.list_package_items(self.db, 1, 'a', False, True), [])
        self.assertEqual(repo.list_my_packages_page(self.db, 'a', 1, 20, False, True)[0], 2)
        self.assertEqual(len(repo.list_package_items(self.db, 1, 'a', True, True)), 2)

    def test_route_uses_authenticated_identity(self):
        with self.assertRaises(HTTPException) as error:
            router.get_my_work_packages_paged('b', db=self.db, user=self.user)
        self.assertEqual(error.exception.status_code, 403)
        with patch.object(service, 'get_work_items', return_value={}) as query:
            router.get_work_items('1', only_mine=True, db=self.db, user=self.user)
            self.assertEqual(query.call_args.kwargs['owner_id'], 'a')
            router.get_work_items('1', only_mine=False, db=self.db, user=self.user)
            self.assertIsNone(query.call_args.kwargs['owner_id'])

    def test_assignments_totals_and_permissions(self):
        leader = models.User(id='l', username='Leader', job_grade='P1', role='LEADER')
        removed = models.User(id='gone', username='Gone', job_grade='P1', is_deleted=True)
        self.db.add_all([leader, removed])
        self.db.commit()
        result = router.list_assignments(db=self.db, user=leader)['data']
        rows = {row['user_id']: row for row in result['items']}
        self.assertEqual(result['total'], 3)
        self.assertEqual((rows['a']['work_item_count'], rows['a']['total_score']), (1, 10))
        self.assertEqual((rows['b']['work_item_count'], rows['b']['total_score']), (2, 20))
        self.assertEqual((rows['l']['work_item_count'], rows['l']['total_score']), (0, 0))
        self.assertEqual(router.list_assignments(keyword='Leader', db=self.db, user=leader)['data']['total'], 1)
        self.assertEqual(len(router.list_assignments(page_size=1, db=self.db, user=leader)['data']['items']), 1)
        for caller in [self.user, self.db.get(models.User, 'b')]:
            with self.assertRaises(HTTPException) as error:
                router.list_assignments(db=self.db, user=caller)
            self.assertEqual(error.exception.status_code, 403)
            with self.assertRaises(HTTPException):
                router.get_work_items('1', view_user_id='a', db=self.db, user=caller)

    def test_leader_view_matches_personal_view(self):
        leader = models.User(id='l', username='Leader', job_grade='P1', role='LEADER')
        self.db.add(leader)
        self.db.commit()
        self.db.get(models.WorkItem, 1).complete_status = True
        self.db.commit()
        for completed in (False, True):
            for related in (False, True):
                leader_data = router.assigned_packages('a', show_completed=completed, show_related=related,
                                                       db=self.db, user=leader)['data']
                personal = service.get_my_work_packages_paged('a', db=self.db, show_completed=completed,
                                                              show_related=related)['data']
                self.assertEqual(leader_data['items'], personal['items'])
                leader_items = router.get_work_items('1', view_user_id='a', show_completed=completed,
                                                     show_related=related, db=self.db, user=leader)
                personal_items = router.get_work_items('1', only_mine=True, show_completed=completed,
                                                       show_related=related, db=self.db, user=self.user)
                self.assertEqual(leader_items, personal_items)
        with self.assertRaises(HTTPException) as error:
            router.assigned_packages('missing', db=self.db, user=leader)
        self.assertEqual(error.exception.status_code, 404)

    def test_personal_score_deductions_include_items_without_scores(self):
        now = datetime.now(timezone(timedelta(hours=8)))
        self.db.get(models.WorkItem, 1).deadline = now - timedelta(days=14)
        self.db.get(models.WorkItem, 2).deadline = now - timedelta(days=44)
        unscored = self.db.get(models.WorkItem, 3)
        unscored.owner_id = 'a'
        unscored.deadline = now - timedelta(days=37)
        self.db.commit()
        data = score_service.get_my_progress_deductions(self.db, 'a')['data']
        self.assertEqual([row['work_item_id'] for row in data['details']], [1, 3])
        self.assertEqual(data['deducted_score'], 4)
        self.assertEqual(data['details'][1]['score'], 0)
        # 两个工作项转办后，本人的累计扣分应归零。
        for item_id in (1, 3):
            self.db.get(models.WorkItem, item_id).owner_id = 'b'
        self.db.commit()
        self.assertEqual(score_service.get_my_progress_deductions(self.db, 'a')['data']['details'], [])

    def test_score_board_period_includes_overdue_item_without_monthly_score(self):
        item = self.db.get(models.WorkItem, 2)
        item.deadline = datetime(2026, 9, 15, 23, 59, 59)
        self.db.commit()

        september = score_service.calculate_public_score_board(
            'month', 2026, 9, db=self.db, as_of=date(2026, 9, 30))['data']['people']
        september_owner = next(row for row in september if row['user_id'] == 'b')
        self.assertEqual(september_owner['deducted_score'], 1.0)
        self.assertEqual(september_owner['total_calculated'], -1.0)
        self.assertEqual([(row['work_item_id'], row['score'], row['deducted_score'])
                          for row in september_owner['details']], [(2, 0.0, 1.0)])

        october = score_service.calculate_public_score_board(
            'month', 2026, 10, db=self.db, as_of=date(2026, 10, 23))['data']['people']
        october_owner = next(row for row in october if row['user_id'] == 'b')
        self.assertEqual(october_owner['deducted_score'], 2.0)
        self.assertEqual(october_owner['details'][0]['deducted_score'], 2.0)

        quarter = score_service.calculate_public_score_board(
            'quarter', 2026, quarter=3, db=self.db, as_of=date(2026, 10, 23))['data']['people']
        quarter_owner = next(row for row in quarter if row['user_id'] == 'b')
        self.assertEqual(quarter_owner['deducted_score'], 1.0)

        self.db.add(models.ScoreConfirmationConfig(id=1, start_month='2026-10'))
        self.db.commit()
        with patch('services.score_confirmation_service.now_local', return_value=datetime(2026, 10, 23)):
            fourth_quarter = score_service.get_my_period_progress_deductions(
                self.db, 'b', 'quarter', 2026, quarter=4)['data']
            self.assertEqual(fourth_quarter['deducted_score'], 2.0)
            self.assertEqual([(row['month'], row['deducted_score'])
                              for row in fourth_quarter['details']], [('2026-10', 2.0)])
            year = score_service.get_my_period_progress_deductions(
                self.db, 'b', 'year', 2026)['data']
            self.assertEqual(year['deducted_score'], 3.0)

    def test_confirmed_progress_deduction_stays_frozen_after_deadline_change(self):
        from services import score_confirmation_service as confirmations

        item = self.db.get(models.WorkItem, 2)
        item.deadline = datetime(2026, 9, 15, 23, 59, 59)
        self.db.add(models.ScoreConfirmationConfig(id=1, start_month='2026-10'))
        self.db.commit()
        user = self.db.get(models.User, 'b')
        record = confirmations.mine(self.db, user, datetime(2026, 11, 1))['data']['records'][0]
        original_penalty = record['score']['deducted_score']
        self.assertEqual(original_penalty, 3.0)
        self.assertEqual(record['score']['details'][0]['deducted_score'], 3.0)
        confirmations.confirm(self.db, user, record['id'], record['fingerprint'], datetime(2026, 11, 2))
        item.deadline = datetime(2027, 1, 1)
        self.db.commit()
        with patch('services.score_confirmation_service.now_local', return_value=datetime(2026, 11, 2)):
            result = score_service.get_my_period_progress_deductions(
                self.db, 'b', 'month', 2026, month=10)['data']
        self.assertEqual(result['deducted_score'], original_penalty)

    def test_personal_deduction_route_uses_login(self):
        with patch.object(score_service, 'get_my_progress_deductions', return_value={}) as query:
            score_router.get_my_progress_deductions(db=self.db, user=self.user)
            query.assert_called_once_with(self.db, 'a')



if __name__ == '__main__':
    unittest.main()
