"""Production clock ignores former page-test environment variables."""
import os
import unittest
from datetime import datetime
from unittest.mock import patch
from services import score_confirmation_service as service

class ScoreConfirmationClockTests(unittest.TestCase):
    def test_real_time_even_with_stale_test_settings(self):
        for environment in ("test", "production", ""):
            with self.subTest(environment=environment), patch.dict(os.environ, {
                "APP_ENV": environment, "SCORE_CONFIRMATION_TEST_NOW": "2026-11-04T09:00:00"
            }):
                before = datetime.now(service.TZ).replace(tzinfo=None)
                actual = service.now_local()
                after = datetime.now(service.TZ).replace(tzinfo=None)
                self.assertLessEqual(before, actual)
                self.assertLessEqual(actual, after)
