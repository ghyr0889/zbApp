"""所有人员积分接口仅向领导和管理员返回月度自评内容。"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from routers import score_board


class SelfEvaluationVisibilityTests(unittest.TestCase):
    def test_public_board_hides_self_evaluation_for_other_roles(self):
        for role in ("EMPLOYEE", "DEPARTMENT"):
            with self.subTest(role=role):
                board = {"code": 200, "data": {"people": [
                    {"user_id": "a", "self_evaluation": {"status": "SUBMITTED", "content": "个人内容"}},
                ]}}
                with patch.object(score_board.service, "get_public_score_board", return_value=board):
                    result = score_board.get_public_score_board(db=None, user=SimpleNamespace(role=role))
                self.assertNotIn("self_evaluation", result["data"]["people"][0])

    def test_public_board_keeps_self_evaluation_for_leader_and_admin(self):
        for role in ("LEADER", "ADMIN"):
            with self.subTest(role=role):
                board = {"code": 200, "data": {"people": [
                    {"user_id": "a", "self_evaluation": {"status": "SUBMITTED", "content": "个人内容"}},
                ]}}
                with patch.object(score_board.service, "get_public_score_board", return_value=board):
                    result = score_board.get_public_score_board(db=None, user=SimpleNamespace(role=role))
                self.assertEqual(result["data"]["people"][0]["self_evaluation"]["content"], "个人内容")


if __name__ == "__main__":
    unittest.main()
