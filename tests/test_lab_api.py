import json,unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from lab.api import app
from lab.models import RevisionRequest
class LabAPITests(unittest.TestCase):
    def setUp(self):self.client=TestClient(app)
    def test_cross_origin_mutations_rejected(self):
        r=self.client.post('/api/v1/sync',json={},headers={'Origin':'https://example.com'});self.assertEqual(r.status_code,403)
    def test_strict_numeric_wire_contract(self):
        r=self.client.post('/api/v1/experiments/revisions',json={'subject_id':'s','title':'t','expected_snapshot_hash':'h','changes':[{'table':'Equipment','row_key':'r','column':'x','value':1.25}]});self.assertEqual(r.status_code,422)
    def test_bounded_run_request(self):
        r=self.client.post('/api/v1/runs',json={'revision_id':'r','workers':5});self.assertEqual(r.status_code,422)
    def test_unknown_fact_kind_rejected(self):
        r=self.client.get('/api/v1/runs/r/facts/arbitrary-sql');self.assertEqual(r.status_code,422)
    def test_path_traversal_download_rejected(self):
        r=self.client.get('/api/v1/runs/r/download/..%2Fsecrets');self.assertEqual(r.status_code,404)
    def test_health_has_no_credentials(self):
        r=self.client.get('/api/v1/health');self.assertEqual(r.status_code,200);self.assertNotIn('key',r.text)
