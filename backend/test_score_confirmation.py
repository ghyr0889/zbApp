import json
import unittest
from datetime import datetime
from types import SimpleNamespace as NS
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import models
from services import score_confirmation_service as service

class ScoreConfirmationTests(unittest.TestCase):
# 定义测试类
    def setUp(self): # 每个测试开始前，准备环境
        self.engine = create_engine("sqlite:///:memory:")
        models.ScoreConfirmationConfig.__table__.create(self.engine)
        models.MonthlyScoreConfirmation.__table__.create(self.engine)
        models.MonthlyScoreSelfEvaluation.__table__.create(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(models.ScoreConfirmationConfig(id=1, start_month="2026-10"))
        self.db.commit()
        self.amount = 20
        self.calculation = patch.object(service.scores, "calculate_public_score_board", side_effect=self.calculate)
        self.mock_calculation = self.calculation.start()

    def tearDown(self): # 每个测试结束后，清理环境
        self.calculation.stop()
        self.db.close()
        self.engine.dispose()

    def calculate(self, *args, **kwargs): # 提供模拟积分数据
        return {"data": {"people": [{"user_id": "u1", "username": "One", "role": "EMPLOYEE",
            "total_calculated": self.amount, "total_score": self.amount,
            "converted_score": 90.01, "final_calculated": 90.01, "grade": "A", "details": []}]}}

    def pending(self, now=datetime(2026,11,1)):
        return service.mine(self.db, NS(id="u1"), now)["data"]["records"][0]

    def test_year_boundary(self):
        self.assertEqual(service.next_month("2026-12"), "2027-01")
        self.assertEqual(service.deadline("2026-12"), datetime(2027,1,4))
        self.assertEqual(service.previous_month(datetime(2027,1,1)), "2026-12")

    def test_no_retroactive_history(self):
        data = service.mine(self.db, NS(id="u1"), datetime(2026,10,21))
        self.assertEqual(data["data"]["records"], [])

    def test_manual_confirm_immutable(self):
        record = self.pending()
        service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"], datetime(2026,11,3,23,59))
        self.amount = 999
        final = service.mine(self.db, NS(id="u1"), datetime(2026,11,4))["data"]["records"][0]
        self.assertEqual(final["status"], "CONFIRMED")
        self.assertEqual(final["score"]["total_calculated"], 20)

    def test_stale_preview_rejected(self):
        record = self.pending()
        self.amount = 30
        with self.assertRaises(HTTPException) as error:
            service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"], datetime(2026,11,2))
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(self.pending()["status"], "PENDING")

    def test_wrong_user_cannot_confirm(self):
        record = self.pending()
        with self.assertRaises(HTTPException) as error:
            service.confirm(self.db, NS(id="u2"), record["id"], record["fingerprint"], datetime(2026,11,2))
        self.assertEqual(error.exception.status_code, 404)

    def test_deadline_auto_freezes(self):
        record = self.pending()
        self.amount = 35
        with self.assertRaises(HTTPException) as error:
            service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"], datetime(2026,11,4))
        self.assertEqual(error.exception.status_code, 409)
        final = self.pending(datetime(2026,11,5))
        self.assertEqual(final["status"], "AUTO")
        self.assertEqual(final["score"]["total_calculated"], 35)
        self.amount = 900
        self.assertEqual(self.pending(datetime(2026,11,7))["score"]["total_calculated"], 35)

    def test_restart_catches_up_and_caps_deduction_date(self):
        self.pending(datetime(2026,11,18))
        self.assertEqual(self.mock_calculation.call_args.kwargs["as_of"].isoformat(), "2026-11-03")

    def test_zero_score_and_idempotency(self):
        self.amount = 0
        r = self.pending()
        for _ in range(2):
            service.confirm(self.db, NS(id="u1"), r["id"], r["fingerprint"], datetime(2026,11,2))
        self.assertEqual(self.db.query(models.MonthlyScoreConfirmation).count(), 1)

    def test_monthly_preview_and_frozen_result(self):
        r = self.pending()
        with patch.object(service, "now_local", return_value=datetime(2026,11,2)),              patch.object(service.scores.repo, "list_all_month_scores", return_value=[]),              patch.object(service.scores.repo, "list_period_extra_scores", return_value=[]):
            board = service.official_board(self.db, "month", 2026, 10, None)["data"]["people"]
            self.assertEqual(board[0]["total_calculated"], 20)
            self.assertTrue(board[0]["is_provisional"])
            service.confirm(self.db, NS(id="u1"), r["id"], r["fingerprint"])
            self.amount = 999
            board = service.official_board(self.db, "month", 2026, 10, None)["data"]["people"]
            self.assertEqual(board[0]["total_calculated"], 20)
            self.assertEqual(board[0]["confirmation_status"], "CONFIRMED")

    def test_confirmed_month_rejects_extra_edits(self):
        r = self.pending()
        service.confirm(self.db, NS(id="u1"), r["id"], r["fingerprint"], datetime(2026,11,2))
        with patch.object(service, "now_local", return_value=datetime(2026,11,2)), self.assertRaises(HTTPException):
            service.assert_editable(self.db, "u1", "2026-10")

if __name__ == "__main__":
    unittest.main()
