import unittest
from datetime import datetime
from types import SimpleNamespace as NS
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import models
from services import historical_score_service as history
from services import score_confirmation_service as service
from routers.score_confirmations import HistoricalScoreBody

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite:///:memory:")
        for model in (models.User,models.ScoreConfirmationConfig,models.MonthlyScoreConfirmation,models.MonthlyScoreSelfEvaluation,models.HistoricalScoreDraft):
            model.__table__.create(self.engine)
        self.db=sessionmaker(bind=self.engine)()
        self.db.add(models.User(id="u1",username="One",job_grade="P1",role="EMPLOYEE"))
        self.db.add(models.ScoreConfirmationConfig(id=1,start_month="2026-10"))
        self.db.commit()
        self.admin=NS(id="admin",role="ADMIN")
        self.body=HistoricalScoreBody(user_id="u1",month="2026-09",month_score=10,calculate_score=12,deducted_score=1,tech_improve=3,daily_manage=-1,tech_growth_score=5,total_calculated=13,converted_score=95,grade="A",reason="old ledger")
    def tearDown(self):
        self.db.close();self.engine.dispose()
    def save_publish(self):
        history.save(self.db,self.admin,self.body)
        row=history.listing(self.db,self.admin)["data"]["drafts"][0]
        history.publish(self.db,self.admin,row["id"],row["fingerprint"])
    def test_draft_then_locked_publication(self):
        history.save(self.db,self.admin,self.body)
        self.assertEqual(self.db.query(models.MonthlyScoreConfirmation).count(),0)
        self.save_publish()
        rec=self.db.query(models.MonthlyScoreConfirmation).one()
        self.assertEqual(rec.status,"IMPORTED")
        self.assertEqual(service.evaluation_info(self.db,rec)["status"],"NOT_REQUIRED")
        with self.assertRaises(HTTPException):history.save(self.db,self.admin,self.body)
        with self.assertRaises(HTTPException):service.assert_editable(self.db,"u1","2026-09")
    def test_permissions_date_existing_and_stale(self):
        with self.assertRaises(HTTPException):history.save(self.db,NS(id="u1",role="EMPLOYEE"),self.body)
        with self.assertRaises(HTTPException):history.save(self.db,self.admin,self.body.model_copy(update={"month":"2026-10"}))
        history.save(self.db,self.admin,self.body)
        row=history.listing(self.db,self.admin)["data"]["drafts"][0]
        history.save(self.db,self.admin,self.body.model_copy(update={"reason":"changed"}))
        with self.assertRaises(HTTPException):history.publish(self.db,self.admin,row["id"],row["fingerprint"])
        self.db.add(models.MonthlyScoreConfirmation(user_id="u1",month="2026-09",status="CONFIRMED",snapshot="{}",fingerprint="x"))
        self.db.commit()
        with self.assertRaises(HTTPException):history.save(self.db,self.admin,self.body)
    def test_month_quarter_year_use_import_once(self):
        self.save_publish()
        def raw(period,*args,**kwargs):
            return {"data":{"people":[{"user_id":"u1","username":"One","role":"EMPLOYEE","total_calculated":999,"details":[]}]}}
        with patch.object(service,"now_local",return_value=datetime(2026,10,20)), patch.object(service.scores,"calculate_public_score_board",side_effect=raw), patch.object(service.scores.repo,"list_all_month_scores",return_value=[]), patch.object(service.scores.repo,"list_period_extra_scores",return_value=[]):
            month=service.official_board(self.db,"month",2026,9,None)["data"]["people"][0]
            self.assertEqual(month["total_calculated"],13)
            self.assertEqual(month["converted_score"],95)
            self.assertIsNone(month["patent_score"])
            self.assertTrue(month["month_locked"])
            # Other legacy months retain their old values; September is replaced, never added twice.
            quarter=service.official_board(self.db,"quarter",2026,None,3)["data"]["people"][0]
            self.assertEqual(quarter["total_calculated"],999*2+13)
            year=service.official_board(self.db,"year",2026,None,None)["data"]["people"][0]
            self.assertEqual(year["total_calculated"],999*8+13)

if __name__ == "__main__":unittest.main()
