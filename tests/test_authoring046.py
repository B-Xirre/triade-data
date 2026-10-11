from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from authoring046 import validate,export
from migrate_authoring046 import plans

class Authoring046Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'content/canonical/authoring.json').read_text(encoding='utf-8'))
        cls.registry=json.loads((ROOT/'schema/authoring-registry-1.0.0.json').read_text(encoding='utf-8'))
        cls.manifest=json.loads((ROOT/'content/authoring-manifest.json').read_text(encoding='utf-8'))
        cls.schema=json.loads((ROOT/'schema/authoring.schema.json').read_text(encoding='utf-8'))
    def check(self,data):return validate(data,self.registry,self.manifest,self.schema)
    def test_pinned_census(self):
        proof=self.check(self.data)
        self.assertEqual((proof['table_count'],proof['row_count'],proof['rule_count'],proof['unset_parameters']),(108,768,245,105))
        self.assertFalse(proof['runtime_ready'])
    def test_rule_loss_rejected(self):
        data=copy.deepcopy(self.data);data['tables']['Ref_rules'].pop()
        with self.assertRaisesRegex(ValueError,'census'):self.check(data)
    def test_unset_zero_rejected(self):
        data=copy.deepcopy(self.data)
        row=next(r for r in data['tables']['Design_parameters'] if r['value_state']=='unset');row['value_q']=0
        with self.assertRaisesRegex(ValueError,'unset'):self.check(data)
    def test_wrong_scale_rejected(self):
        data=copy.deepcopy(self.data)
        next(r for r in data['tables']['Design_parameters'] if r['parameter_id']=='S-P01')['value_int']=10000
        with self.assertRaisesRegex(ValueError,'constant'):self.check(data)
    def test_persisted_q_overflow_rejected(self):
        for value in [-(1<<63)-1,1<<63]:
            data=copy.deepcopy(self.data);data['tables']['Fixture_builds'][0]['floor_m_q']=value
            with self.assertRaises(Exception):self.check(data)
    def test_stable_identity_collision_rejected(self):
        data=copy.deepcopy(self.data);data['tables']['Ref_rules'][1]['rule_id']=data['tables']['Ref_rules'][0]['rule_id']
        with self.assertRaisesRegex(ValueError,'duplicate'):self.check(data)
    def test_unresolved_reference_rejected(self):
        data=copy.deepcopy(self.data);data['tables']['Faculty_profile_members'][0]['profile']='missing@1'
        with self.assertRaisesRegex(ValueError,'unresolved'):self.check(data)
    def test_missing_protection_scope_rejected(self):
        data=copy.deepcopy(self.data);data['tables']['Defence_profile_entries'][0]['protection_scope']=''
        with self.assertRaises(Exception):self.check(data)
    def test_fixture_integer_floor_rejected(self):
        data=copy.deepcopy(self.data);data['tables']['Fixture_builds'][0]['floor_m_q']=3001
        with self.assertRaisesRegex(ValueError,'floor'):self.check(data)
    def test_fake_fixture_readiness_rejected(self):
        data=copy.deepcopy(self.data);data['tables']['Fixture_builds'][0]['validation_state']='ready'
        with self.assertRaises(Exception):self.check(data)
    def test_exports_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a';b=Path(tmp)/'b';digest=export(self.data,a);self.assertEqual(digest,export(self.data,b))
            self.assertEqual(digest,hashlib.sha256((a/'authoring.json').read_bytes()).hexdigest())
            paths=sorted(p.relative_to(a) for p in a.rglob('*') if p.is_file())
            self.assertEqual(paths,sorted(p.relative_to(b) for p in b.rglob('*') if p.is_file()))
            for path in paths:self.assertEqual((a/path).read_bytes(),(b/path).read_bytes())
    def test_schema_plan_idempotent(self):
        snapshot={t:{'columns':[{'id':n,'fields':d} for n,d in columns.items()]} for t,columns in self.registry['tables'].items()}
        self.assertEqual(plans(snapshot,self.registry,{}),[])

if __name__=='__main__':unittest.main()
