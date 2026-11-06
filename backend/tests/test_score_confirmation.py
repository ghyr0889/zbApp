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
        models.MonthlyScoreSettlement.__table__.create(self.engine)
        models.MonthlyScoreConversion.__table__.create(self.engine)
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
        self.assertEqual(service.source_edit_deadline("2026-12"), datetime(2027,1,6))
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

    def test_unconfirmed_remains_pending_and_can_confirm_later(self):
        record = self.pending()
        self.amount = 35
        with self.assertRaises(HTTPException) as error:
            service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"], datetime(2026,11,6))
        self.assertEqual(error.exception.status_code, 409)
        final = self.pending(datetime(2026,11,6))
        self.assertEqual(final["status"], "PENDING")
        self.assertIsNone(final["deadline"])
        self.assertEqual(final["score"]["total_calculated"], 35)
        service.confirm(self.db, NS(id="u1"), final["id"], final["fingerprint"], datetime(2026,11,20))
        self.amount = 900
        self.assertEqual(self.pending(datetime(2026,11,21))["score"]["total_calculated"], 35)

    def test_restart_catches_up_and_caps_deduction_date(self):
        self.pending(datetime(2026,11,18))
        self.assertEqual(self.mock_calculation.call_args.kwargs["as_of"].isoformat(), "2026-10-31")

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

    def test_unified_conversion_waits_for_all_and_uses_confirmed_totals(self):
        amounts = {"u1": 100, "u2": 50}
        def calculate(*args, **kwargs):
            return {"data": {"people": [dict(user_id=uid, username=uid, role="EMPLOYEE",
                total_calculated=value, total_score=value, converted_score=999,
                final_calculated=999, grade="S", details=[]) for uid, value in amounts.items()]}}
        self.mock_calculation.side_effect = calculate
        first = service.mine(self.db, NS(id="u1"), datetime(2026, 11, 1))["data"]["records"][0]
        second = service.mine(self.db, NS(id="u2"), datetime(2026, 11, 1))["data"]["records"][0]
        self.assertNotIn("converted_score", first["score"])
        service.confirm(self.db, NS(id="u1"), first["id"], first["fingerprint"], datetime(2026, 11, 2))
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 0)
        self.assertEqual(service.evaluation_info(self.db, self.db.get(models.MonthlyScoreConfirmation, first["id"]))["status"], "WAITING")
        with patch.object(service, "now_local", return_value=datetime(2026, 11, 2)), \
             patch.object(service.scores.repo, "list_all_month_scores", return_value=[]), \
             patch.object(service.scores.repo, "list_period_extra_scores", return_value=[]):
            waiting = service.official_board(self.db, "month", 2026, 10, None)["data"]["people"]
            self.assertTrue(all(row["converted_score"] is None and row["grade"] is None for row in waiting))
            self.assertTrue(all(row["settlement_status"] == "WAITING" for row in waiting))
        amounts["u1"] = 999  # 已确认的原始数据变化不会改写本人计算总分。
        service.confirm(self.db, NS(id="u2"), second["id"], second["fingerprint"], datetime(2026, 11, 5, 23, 59))
        settlement = self.db.query(models.MonthlyScoreSettlement).one()
        self.assertEqual(settlement.status, "SETTLED")
        self.assertAlmostEqual(settlement.conversion_factor, 100 / 90.01)
        conversions = {c.confirmation_id: c.converted_score for c in self.db.query(models.MonthlyScoreConversion)}
        self.assertEqual(conversions, {first["id"]: 90.01, second["id"]: 45.01})
        self.assertEqual(self.db.get(models.MonthlyScoreConfirmation, first["id"]).status, "CONFIRMED")
        self.assertEqual(service.evaluation_info(self.db, self.db.get(models.MonthlyScoreConfirmation, first["id"]))["status"], "REQUIRED")
        with patch.object(service, "now_local", return_value=datetime(2026, 11, 5)), \
             patch.object(service.scores.repo, "list_all_month_scores", return_value=[]), \
             patch.object(service.scores.repo, "list_period_extra_scores", return_value=[]):
            board = service.official_board(self.db, "month", 2026, 10, None)["data"]["people"]
            self.assertEqual({row["user_id"]: row["converted_score"] for row in board}, {"u1": 90.01, "u2": 45.01})
        service.synchronize(self.db, datetime(2026, 11, 6))
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 2)

    def test_fixed_participants_wait_for_late_confirmation(self):
        amounts = {"u1": 100, "u2": 50}
        def calculate(*args, **kwargs):
            return {"data": {"people": [dict(user_id=uid, username=uid, role="EMPLOYEE",
                total_calculated=value, total_score=value, details=[]) for uid, value in amounts.items()]}}
        self.mock_calculation.side_effect = calculate
        first = service.mine(self.db, NS(id="u1"), datetime(2026, 11, 1))["data"]["records"][0]
        service.confirm(self.db, NS(id="u1"), first["id"], first["fingerprint"], datetime(2026, 11, 2))
        amounts["u3"] = 999  # 名单固定后新增的人员不加入当月结算。
        service.synchronize(self.db, datetime(2026, 11, 6))
        self.db.commit()
        records = {r.user_id: r for r in self.db.query(models.MonthlyScoreConfirmation)}
        self.assertEqual(set(records), {"u1", "u2"})
        self.assertEqual(records["u2"].status, "PENDING")
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 0)
        service.confirm(self.db, NS(id="u2"), records["u2"].id, records["u2"].fingerprint, datetime(2026, 11, 20))
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 2)
        self.assertEqual(self.mock_calculation.call_args.kwargs["as_of"].isoformat(), "2026-10-31")

    def test_later_month_settlement_does_not_skip_earlier_pending_month(self):
        self.mock_calculation.side_effect = lambda *a, **kw: {"data": {"people": [
            dict(user_id=uid, username=uid, role="EMPLOYEE", total_calculated=value,
                 total_score=value, details=[]) for uid, value in (("u1", 100), ("u2", 50))]}}
        service.synchronize(self.db, datetime(2026, 11, 1))
        self.db.commit()
        october = {r.user_id: r for r in self.db.query(models.MonthlyScoreConfirmation).filter_by(month="2026-10")}
        service.confirm(self.db, NS(id="u1"), october["u1"].id, october["u1"].fingerprint, datetime(2026, 11, 2))
        service.synchronize(self.db, datetime(2026, 12, 2))
        self.db.commit()
        november = {r.user_id: r for r in self.db.query(models.MonthlyScoreConfirmation).filter_by(month="2026-11")}
        for uid in ("u1", "u2"):
            service.confirm(self.db, NS(id=uid), november[uid].id, november[uid].fingerprint, datetime(2026, 12, 2))
        self.assertIsNone(self.db.get(models.ScoreConfirmationConfig, 1).closed_through)
        self.assertEqual(self.db.get(models.MonthlyScoreConfirmation, october["u2"].id).status, "PENDING")
        self.assertEqual(self.db.query(models.MonthlyScoreSettlement).filter_by(month="2026-11").one().status, "SETTLED")
        old = self.db.get(models.MonthlyScoreConfirmation, october["u2"].id)
        service.confirm(self.db, NS(id="u2"), old.id, old.fingerprint, datetime(2026, 12, 3))
        self.assertEqual(self.db.get(models.ScoreConfirmationConfig, 1).closed_through, "2026-11")
        self.assertEqual(self.db.query(models.MonthlyScoreSettlement).filter_by(month="2026-10").one().status, "SETTLED")

    def test_pending_month_before_legacy_cursor_can_still_be_confirmed(self):
        record = self.pending(datetime(2026, 11, 1))
        self.db.get(models.ScoreConfirmationConfig, 1).closed_through = "2026-11"
        self.db.commit()
        service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"], datetime(2026, 12, 2))
        self.assertEqual(self.db.get(models.MonthlyScoreConfirmation, record["id"]).status, "CONFIRMED")
        self.assertEqual(self.db.query(models.MonthlyScoreSettlement).filter_by(month="2026-10").one().status, "SETTLED")
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 1)

    def test_existing_fully_confirmed_history_keeps_original_conversion(self):
        snapshot = {"user_id": "u1", "total_calculated": 20, "converted_score": 77,
                    "final_calculated": 77, "grade": "B", "details": []}
        payload, fingerprint = service.encode(snapshot)
        self.db.add(models.MonthlyScoreConfirmation(user_id="u1", month="2026-10", status="CONFIRMED",
                    snapshot=payload, fingerprint=fingerprint, confirmed_at=datetime(2026, 11, 2)))
        self.db.commit()
        record = self.pending(datetime(2026, 11, 3))
        self.assertEqual(record["score"]["converted_score"], 77)
        self.assertEqual(record["score"]["grade"], "B")
        self.assertEqual(self.db.query(models.MonthlyScoreSettlement).count(), 0)

    def test_historical_auto_record_is_not_changed(self):
        snapshot = {"user_id": "u1", "total_calculated": 20, "converted_score": 77,
                    "final_calculated": 77, "grade": "B", "details": []}
        payload, fingerprint = service.encode(snapshot)
        self.db.add(models.MonthlyScoreConfirmation(user_id="u1", month="2026-10", status="AUTO",
                    snapshot=payload, fingerprint=fingerprint, confirmed_at=datetime(2026, 11, 4)))
        self.db.commit()
        record = self.pending(datetime(2026, 11, 20))
        self.assertEqual(record["status"], "AUTO")
        self.assertEqual(record["score"]["converted_score"], 77)

    def test_source_data_lock_does_not_block_late_confirmation(self):
        record = self.pending()
        with patch.object(service, "now_local", return_value=datetime(2026, 11, 10)):
            with self.assertRaises(HTTPException):
                service.assert_editable(self.db, "u1", "2026-10")
            service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"])
        self.assertEqual(self.db.get(models.MonthlyScoreConfirmation, record["id"]).status, "CONFIRMED")

    def test_existing_partially_confirmed_month_keeps_personal_snapshot(self):
        old = {"user_id": "u1", "total_calculated": 100, "converted_score": 88,
               "final_calculated": 88, "grade": "B", "details": []}
        waiting = {"user_id": "u2", "total_calculated": 50, "details": []}
        for user, status, data in (("u1", "CONFIRMED", old), ("u2", "PENDING", waiting)):
            payload, fingerprint = service.encode(data)
            self.db.add(models.MonthlyScoreConfirmation(user_id=user, month="2026-10", status=status,
                        snapshot=payload, fingerprint=fingerprint))
        self.db.commit()
        self.mock_calculation.side_effect = lambda *a, **kw: {"data": {"people": [old, waiting]}}
        second = service.mine(self.db, NS(id="u2"), datetime(2026, 11, 2))["data"]["records"][0]
        service.confirm(self.db, NS(id="u2"), second["id"], second["fingerprint"], datetime(2026, 11, 2))
        first = self.db.query(models.MonthlyScoreConfirmation).filter_by(user_id="u1").one()
        self.assertEqual(json.loads(first.snapshot), old)
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 0)
        self.assertEqual(self.db.query(models.MonthlyScoreSettlement).one().status, "LEGACY")

    def test_settlement_failure_can_be_rolled_back_and_retried(self):
        record = self.pending()
        with patch.object(service.scores, "grade_of", side_effect=RuntimeError("failed")):
            with self.assertRaises(RuntimeError):
                service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"], datetime(2026, 11, 2))
        self.db.rollback()
        self.assertEqual(self.db.get(models.MonthlyScoreConfirmation, record["id"]).status, "PENDING")
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 0)
        service.confirm(self.db, NS(id="u1"), record["id"], record["fingerprint"], datetime(2026, 11, 2))
        self.assertEqual(self.db.query(models.MonthlyScoreConversion).count(), 1)

if __name__ == "__main__":
    unittest.main()
