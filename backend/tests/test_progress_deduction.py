"""进度扣分边界测试：不连接业务数据库。"""
import unittest
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from services.score_board_service import compute_deducted, monthly_progress_deduction


class ProgressDeductionTests(unittest.TestCase):
    def test_cumulative_boundaries(self):
        deadline = datetime(2026, 1, 1, 23, 59, 59)
        item = SimpleNamespace(deadline=deadline, completed_at=None)
        cases = {
            -1: 0, 0: 0, 6: 0, 7: 0.5, 8: 0.5,
            13: 0.5, 14: 1, 21: 1.5, 28: 2,
            29: 2, 30: 2, 31: 2, 36: 2, 37: 3, 44: 4, 60: 6,
        }
        for days, expected in cases.items():
            with self.subTest(days=days):
                self.assertEqual(compute_deducted(item, deadline.date() + timedelta(days=days)), expected)

    def test_completed_stops_at_approval_date(self):
        item = SimpleNamespace(deadline=datetime(2026, 1, 1), complete_status=True,
                               completed_at=datetime(2026, 1, 8), completion_approved_at=datetime(2026, 1, 15))
        self.assertEqual(compute_deducted(item, date(2026, 2, 7)), 1)
        self.assertEqual(compute_deducted(item, date(2026, 3, 7)), 1)
        self.assertEqual(compute_deducted(item, date(2026, 1, 8)), 0.5)
        item.complete_status = False
        self.assertEqual(compute_deducted(item, date(2026, 2, 7)), 3)

    def test_pause_reopen_and_overlapping_ancestors(self):
        item = SimpleNamespace(deadline=datetime(2026, 9, 15), complete_status=False)
        records = [
            SimpleNamespace(closed_at=datetime(2026, 9, 23), reopened_at=datetime(2026, 9, 28)),
            SimpleNamespace(closed_at=datetime(2026, 9, 25), reopened_at=datetime(2026, 9, 30)),
            SimpleNamespace(closed_at=datetime(2026, 10, 7), reopened_at=None),
        ]
        self.assertEqual(compute_deducted(item, date(2026, 9, 22), records), 0.5)
        self.assertEqual(compute_deducted(item, date(2026, 9, 29), records), 0.5)
        self.assertEqual(compute_deducted(item, date(2026, 10, 6), records), 1.0)
        self.assertEqual(compute_deducted(item, date(2026, 11, 1), records), 1.0)
        self.assertEqual(monthly_progress_deduction(item, '2026-09', date(2026, 11, 1), close_records=records), 0.5)
        self.assertEqual(monthly_progress_deduction(item, '2026-10', date(2026, 11, 1), close_records=records), 0.5)

    def test_completion_stops_deduction_with_pause(self):
        item = SimpleNamespace(deadline=datetime(2026, 9, 15), complete_status=True,
                               completion_approved_at=datetime(2026, 10, 6))
        records = [SimpleNamespace(closed_at=datetime(2026, 9, 23), reopened_at=datetime(2026, 9, 30))]
        self.assertEqual(compute_deducted(item, date(2026, 11, 1), records), 1.0)

    def test_no_deadline(self):
        self.assertEqual(compute_deducted(SimpleNamespace(deadline=None)), 0)
        self.assertEqual(compute_deducted(None), 0)

    def test_monthly_deduction_is_increase_in_cumulative_penalty(self):
        item = SimpleNamespace(deadline=datetime(2026, 9, 15, 23, 59, 59),
                               complete_status=False, completed_at=None)
        september = monthly_progress_deduction(item, '2026-09', date(2026, 10, 23))
        october = monthly_progress_deduction(item, '2026-10', date(2026, 10, 23))
        self.assertEqual((september, october), (1.0, 2.0))
        self.assertEqual(september + october, compute_deducted(item, date(2026, 10, 23)))

    def test_confirmation_window_does_not_shift_next_month_penalty(self):
        item = SimpleNamespace(deadline=datetime(2026, 10, 25, 23, 59, 59),
                               complete_status=False, completed_at=None)
        # 11 月 1 日刚好逾期 7 天，扣分属于 11 月而非 10 月。
        self.assertEqual(monthly_progress_deduction(item, '2026-10', date(2026, 11, 5), include_grace=True), 0)
        self.assertEqual(monthly_progress_deduction(item, '2026-11', date(2026, 11, 5), include_grace=True), 0.5)


if __name__ == '__main__':
    unittest.main()
