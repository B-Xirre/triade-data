import copy,unittest
from pathlib import Path
from lab.content import load
from lab.validation import validate_rows
from lab.schema import registry
ROOT=Path(__file__).resolve().parents[1]
class RowBoundaryTests(unittest.TestCase):
    def setUp(self):self.data=load(ROOT/'content/canonical/authoring-1.1.0.json');self.registry=registry(ROOT)
    def test_all_source_rows_validate(self):validate_rows(self.data,self.registry)
    def test_scale_change_rejected(self):
        next(r for r in self.data['tables']['Design_parameters'] if r['parameter_id']=='S-P01')['value_int']=6000
        with self.assertRaisesRegex(ValueError,'scale'):validate_rows(self.data,self.registry)
    def test_unset_zero_and_missing_reason_rejected(self):
        row=next(r for r in self.data['tables']['Design_parameters'] if r['value_state']=='unset');row['value_int']=0
        with self.assertRaisesRegex(ValueError,'null'):validate_rows(self.data,self.registry)
    def test_boolean_cannot_be_integer(self):
        self.data['tables']['Fixture_builds'][0]['floor_m_q']=True
        with self.assertRaises(ValueError):validate_rows(self.data,self.registry)
