import json
from datetime import datetime
from types import SimpleNamespace as NS
from unittest.mock import patch
from fastapi import HTTPException
import test_score_confirmation as confirmation_tests
from services import score_confirmation_service as service
import models


class SelfEvaluationTests(confirmation_tests.ScoreConfirmationTests):
    def test_evaluation_waits_for_everyone(self):
        r = self.pending()
        with patch.object(service, "now_local", return_value=datetime(2026, 11, 2)):
            with self.assertRaises(HTTPException):
                service.save_evaluation(self.db, NS(id="u1"), r["id"], "review")
            service.confirm(self.db, NS(id="u1"), r["id"], r["fingerprint"])
            other = models.MonthlyScoreConfirmation(user_id="u2", month="2026-10", status="PENDING", snapshot="{}", fingerprint="x")
            self.db.add(other)
            self.db.commit()
            with self.assertRaises(HTTPException):
                service.save_evaluation(self.db, NS(id="u1"), r["id"], "review")
            other.status = "AUTO"
            self.db.commit()
            service.save_evaluation(self.db, NS(id="u1"), r["id"], "first")
            service.save_evaluation(self.db, NS(id="u1"), r["id"], "latest")
            self.assertEqual(self.db.query(models.MonthlyScoreSelfEvaluation).count(), 1)
            self.assertEqual(self.db.query(models.MonthlyScoreSelfEvaluation).first().content, "latest")
            rec = self.db.get(models.MonthlyScoreConfirmation, r["id"])
            self.assertEqual(json.loads(rec.snapshot)["total_calculated"], 20)
            self.assertEqual(service.evaluation_info(self.db, rec)["status"], "SUBMITTED")

    def test_owner_grade_and_content_validation(self):
        r = self.pending()
        with patch.object(service, "now_local", return_value=datetime(2026, 11, 2)):
            service.confirm(self.db, NS(id="u1"), r["id"], r["fingerprint"])
            with self.assertRaises(HTTPException) as error:
                service.save_evaluation(self.db, NS(id="u2"), r["id"], "review")
            self.assertEqual(error.exception.status_code, 404)
            service.save_evaluation(self.db, NS(id="u1"), r["id"], "评" * 500)
            self.assertEqual(len(self.db.query(models.MonthlyScoreSelfEvaluation).first().content), 500)
            for content in ("   ", "x" * 501):
                with self.assertRaises(HTTPException):
                    service.save_evaluation(self.db, NS(id="u1"), r["id"], content)
            rec = self.db.get(models.MonthlyScoreConfirmation, r["id"])
            snapshot = json.loads(rec.snapshot)
            snapshot["grade"] = "B"
            rec.snapshot = json.dumps(snapshot)
            self.db.commit()
            with self.assertRaises(HTTPException):
                service.save_evaluation(self.db, NS(id="u1"), r["id"], "review")
