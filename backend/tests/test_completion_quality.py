import unittest
from datetime import datetime
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
from pydantic import ValidationError
from fastapi import HTTPException
from schemas import CompleteRequestReview
from services import score_board_service as scores
from routers import complete_review as route
import models


class CompletionQualityTests(unittest.TestCase):
    def test_quality_only_in_approval_month_and_owner(self):
        db = Mock()
        old = NS(month="2026-09", score=3, quality_score=7, calculate_score=10)
        future = NS(month="2026-11", score=2, quality_score=5, calculate_score=7)
        db.query.return_value.filter.return_value.with_for_update.return_value.all.return_value = [old, future]
        item = NS(id=1, owner_id="owner", owner=NS(job_grade=""), work_package=None)
        with patch.object(scores, "compute_calc_score", side_effect=lambda base, item, db, grade, q: base + q):
            month = scores.apply_completion_quality(db, item, 4.5, datetime(2026, 10, 1))
        target = db.add.call_args.args[0]
        self.assertEqual((month, target.month, target.user_id), ("2026-10", "2026-10", "owner"))
        self.assertEqual((target.score, target.quality_score, target.calculate_score), (0, 4.5, 4.5))
        self.assertEqual((old.quality_score, future.quality_score), (0, 0))
        self.assertEqual((old.calculate_score, future.calculate_score), (3, 2))
        db.commit.assert_not_called()

    def test_no_quality_carry_forward(self):
        with patch.object(scores.repo, "get_month_score", return_value=None) as lookup:
            self.assertEqual(scores.monthly_quality_score(Mock(), 1, "2026-11"), 0)
            lookup.assert_called_once()

    def test_old_endpoint_denied(self):
        with self.assertRaises(HTTPException) as error:
            scores.put_quality_score(1, NS(user_id="admin", quality_score=99), Mock())
        self.assertEqual(error.exception.status_code, 403)

    def test_nonfinite_rejected(self):
        for value in [float("nan"), float("inf"), -float("inf")]:
            with self.assertRaises(ValidationError):
                CompleteRequestReview(reviewer_id="tech", quality_percent=value)

    def setup_review(self, user_id="tech", status="PENDING", quality=3, action="APPROVE"):
        db = Mock()
        item = NS(id=1, score=10, tech_owner_id="tech", complete_status=False, completed_at=None, work_package=None)
        req = NS(id=2, work_item_id=1, work_item=item, status=status)
        q = Mock()
        q.options.return_value = q
        q.filter.return_value = q
        q.with_for_update.return_value = q
        q.populate_existing.return_value = q
        q.first.side_effect = [req, item, NS(id=user_id)]
        db.query.return_value = q
        body = CompleteRequestReview(reviewer_id="tech", action=action, quality_percent=quality, comment="reason")
        return db, item, req, body, NS(id=user_id)

    def test_identity_cannot_be_spoofed(self):
        db, item, req, body, user = self.setup_review(user_id="admin")
        with self.assertRaises(HTTPException) as error:
            route.review_complete_request(2, body, db, user)
        self.assertEqual(error.exception.status_code, 403)
        db.commit.assert_not_called()

    def test_approve_requires_score(self):
        db, item, req, body, user = self.setup_review(quality=None)
        with patch.object(route, "ensure_open"), self.assertRaises(HTTPException):
            route.review_complete_request(2, body, db, user)
        db.rollback.assert_called_once()

    def test_approve_zero_and_audit(self):
        db, item, req, body, user = self.setup_review(quality=0)
        with patch.object(route, "ensure_open"), patch.object(route, "apply_completion_quality", return_value="2026-10") as apply:
            route.review_complete_request(2, body, db, user)
        self.assertTrue(item.complete_status)
        self.assertEqual(req.status, "APPROVED")
        self.assertIn("2026-10", req.review_comment)
        apply.assert_called_once()
        db.commit.assert_called_once()

    def test_percent_calculates_quality(self):
        for percent, expected in [(90, -1), (100, 0), (120, 2), (0, -10)]:
            db, item, req, body, user = self.setup_review(quality=percent)
            with patch.object(route, "ensure_open"), patch.object(route, "apply_completion_quality", return_value="2026-10") as apply:
                route.review_complete_request(2, body, db, user)
            self.assertEqual(apply.call_args.args[2], expected)
            self.assertIn(str(percent), req.review_comment)

    def test_duplicate_rejected(self):
        db, item, req, body, user = self.setup_review(status="APPROVED")
        with self.assertRaises(HTTPException):
            route.review_complete_request(2, body, db, user)
        db.commit.assert_not_called()

    def test_reject_does_not_score(self):
        db, item, req, body, user = self.setup_review(action="REJECT", quality=None)
        with patch.object(route, "apply_completion_quality") as apply:
            route.review_complete_request(2, body, db, user)
        apply.assert_not_called()
        self.assertEqual(req.status, "REJECTED")

    def test_quality_error_rolls_back_approval(self):
        db, item, req, body, user = self.setup_review()
        with patch.object(route, "ensure_open"), patch.object(route, "apply_completion_quality", side_effect=RuntimeError("write failed")), self.assertRaises(HTTPException):
            route.review_complete_request(2, body, db, user)
        db.rollback.assert_called_once()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
