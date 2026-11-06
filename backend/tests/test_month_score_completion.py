"""填分与完成申请分离：不连接业务数据库。"""
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch

import models
from services import score_board_service as service


class MonthScoreCompletionTests(unittest.TestCase):
    def test_saving_scores_never_submits_completion(self):
        for total, old, new in [(10, None, 10), (10, 5, 10), (10, None, 6), (0, None, 0)]:
            with self.subTest(total=total, old=old, new=new), ExitStack() as stack:
                db = Mock()
                item = SimpleNamespace(
                    score=total, owner_id="u1", owner=SimpleNamespace(job_grade=""),
                    work_package=SimpleNamespace(project=None), complete_status=False,
                )
                user = SimpleNamespace(id="u1", role="EMPLOYEE")
                record = None if old is None else SimpleNamespace(score=old, user_id="u1")
                body = SimpleNamespace(user_id="u1", month="2026-10", score=new)
                for name, value in [
                    ("get_item", item), ("get_user", user), ("get_month_score", record),
                ]:
                    stack.enter_context(patch.object(service.repo, name, return_value=value))
                add = stack.enter_context(patch.object(service.repo, "add"))
                for name, value in [
                    ("ensure_open", None), ("assert_month_fillable", None),
                    ("item_filled_score", old or 0), ("monthly_quality_score", 0),
                    ("compute_calc_score", new),
                ]:
                    stack.enter_context(patch.object(service, name, return_value=value))
                result = service.save_month_score(1, body, db)
                self.assertEqual(result["message"], "本月分值已保存")
                self.assertEqual(result["data"]["score"], new)
                self.assertIsNone(result["data"]["auto_complete_request_id"])
                self.assertFalse(item.complete_status)
                db.commit.assert_called_once()
                db.add.assert_not_called()
                db.query.assert_not_called()
                if record is None:
                    add.assert_called_once()
                    self.assertIsInstance(add.call_args.args[1], models.WorkItemMonthlyScore)
                else:
                    add.assert_not_called()
                    self.assertEqual(record.score, new)


if __name__ == "__main__":
    unittest.main()
