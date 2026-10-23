"""完成说明必填、责任人权限、幂等性；不连接业务数据库。"""
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch
from fastapi import HTTPException
from pydantic import ValidationError
from schemas import ConfirmCompletionIn
from services import work_logs_service as service


class CompletionReasonTests(unittest.TestCase):
    def call_submit(self, reason, user_id="owner", existing=None):
        db = Mock()
        target = SimpleNamespace(id=1, owner_id="owner", work_package=None, complete_status=False)
        with ExitStack() as stack:
            stack.enter_context(patch.object(service.repo, "get_user", return_value=SimpleNamespace(id=user_id, role="ADMIN")))
            stack.enter_context(patch.object(service.repo, "get_item", return_value=target))
            stack.enter_context(patch.object(service, "ensure_open"))
            stack.enter_context(patch.object(service.repo, "get_pending_completion_review", return_value=existing))
            add = stack.enter_context(patch.object(service.repo, "add"))
            body = ConfirmCompletionIn(target_type="work_item", target_id=1, user_id=user_id, confirmed=True, reason=reason)
            result = service.confirm_completion(body, db)
            return result, add, db, target

    def test_reason_saved_without_marking_item_complete(self):
        result, add, db, target = self.call_submit("  已按目标完成验证。\n成果已归档。  ")
        self.assertEqual(add.call_args.args[1].reason, "已按目标完成验证。\n成果已归档。")
        self.assertEqual(add.call_args.args[1].applicant_id, "owner")
        self.assertFalse(target.complete_status)
        self.assertTrue(result["data"]["pending_complete_review"])
        db.commit.assert_called_once()

    def test_blank_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.call_submit(" \n ")
        self.assertEqual(error.exception.status_code, 400)

    def test_non_owner_admin_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.call_submit("已完成", user_id="other")
        self.assertEqual(error.exception.status_code, 403)

    def test_duplicate_does_not_replace_original_reason(self):
        existing = SimpleNamespace(reason="第一次提交说明")
        _, add, _, _ = self.call_submit("重复提交", existing=existing)
        add.assert_not_called()
        self.assertEqual(existing.reason, "第一次提交说明")

    def test_length_limit_and_other_targets_remain_optional(self):
        with self.assertRaises(ValidationError):
            ConfirmCompletionIn(target_type="work_item", target_id=1, user_id="owner", reason="字" * 2001)
        self.assertEqual(ConfirmCompletionIn(target_type="project", target_id=1, user_id="owner").reason, "")


if __name__ == "__main__":
    unittest.main()
