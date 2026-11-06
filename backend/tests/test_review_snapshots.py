import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from fastapi import HTTPException
from services import review_service as service


class ReviewSnapshotTests(unittest.TestCase):
    def proposal(self, item_id=8):
        return NS(client_id='c1', work_item_id=item_id, name='new', standard='goal',
                  difficulty='1', importance='1', innovation='1', deadline='2026-12-01',
                  score=12, owner_id='1', tech_owner_id='2', notes='')

    def target(self):
        return NS(**{**vars(self.proposal()), 'name': 'old', 'score': 10, 'work_package_id': 3})

    @patch.object(service.repo, 'get_item')
    def test_capture_and_preserve(self, get_item):
        get_item.return_value = self.target()
        saved = json.loads(service._split_items_payload([self.proposal()], object(), package_id=3))
        self.assertEqual(saved[0]['_before']['score'], 10)
        get_item.reset_mock()
        edited = json.loads(service._split_items_payload([self.proposal()], object(), saved, 3))
        self.assertEqual(edited[0]['_before'], saved[0]['_before'])
        get_item.assert_not_called()

    @patch.object(service.repo, 'get_item')
    def test_create_has_no_before(self, get_item):
        saved = json.loads(service._split_items_payload([self.proposal(None)], object(), package_id=3))
        self.assertNotIn('_before', saved[0])
        get_item.assert_not_called()

    @patch.object(service.repo, 'get_item')
    def test_reject_wrong_package(self, get_item):
        get_item.return_value = self.target()
        with self.assertRaises(HTTPException):
            service._split_items_payload([self.proposal()], object(), package_id=4)

    @patch.object(service.repo, 'get_item')
    def test_client_cannot_inject_before(self, get_item):
        get_item.return_value = self.target()
        proposed = self.proposal()
        proposed._before = {'score': 999}
        saved = json.loads(service._split_items_payload([proposed], object(), package_id=3))
        self.assertEqual(saved[0]['_before']['score'], 10)


if __name__ == '__main__':
    unittest.main()
