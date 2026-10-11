import copy,json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lab import config,storage,service
from lab.content import load,coverage,catalogue,editable,apply_variant,digest,frozen_content
from lab.numeric import checked,q,mul,div,SCALE
from lab.models import RevisionRequest,RunRequest,Change,AdoptionRequest
from lab.adapters import DEFAULT_INPUTS,partition,property_case,combat_contracts,tarot_probe,item_probe
from lab.worker import process
class FakeGrist:
    def __init__(self):self.graphs=[]
    def append_graph(self,records):self.graphs.append(copy.deepcopy(records));return sum(map(len,records.values()))
class LabTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=config.DATA;config.DATA=Path(self.tmp.name);config.initialize()
        self.data=frozen_content(load(ROOT/'content/canonical/authoring-1.1.0.json'));self.reg=service.reg();self.hash=digest(self.data);path=config.DATA/'snapshots'/(self.hash+'.json');storage.atomic_json(path,self.data)
        with storage.connect() as db:db.execute('INSERT INTO snapshots VALUES(?,?,?)',(self.hash,str(path),storage.now()))
        self.client=FakeGrist();self.subject=next(s for s in service.subjects()['subjects'] if s['source_revision_id']=='shield.standard@1')
    def tearDown(self):config.DATA=self.old;self.tmp.cleanup()
    def save(self,**kw):return service.save_revision(RevisionRequest(subject_id=self.subject['subject_id'],title='Test shield',expected_snapshot_hash=self.hash,**kw),self.client)
    def test_complete_and_future_coverage(self):
        c=coverage(self.data);self.assertEqual((c['rules'],c['parameters'],c['registered']),(251,128,379))
        self.data['tables']['Design_parameters'].append({**self.data['tables']['Design_parameters'][0],'parameter_id':'future.unbound'})
        future=next(r for r in coverage(self.data)['rows'] if r['source_id']=='future.unbound');self.assertIsNotNone(future['blocking_reason']);self.assertIsNone(future['adapter'])
    def test_fixed_point_boundaries(self):
        self.assertEqual(q('1/3'),4000);self.assertEqual(q('-0.000125'),-2);self.assertEqual(mul(6000,6000),3000);self.assertEqual(div(6000,12000),6000)
        for f in [lambda:q(.1),lambda:checked(1<<63),lambda:mul((1<<63)-1,(1<<63)-1)]:
            with self.assertRaises(ValueError):f()
    def test_partition_conserves_amplification(self):
        for affinity in [6000,12000,48000]:
            r=partition(101,2400,6000,12000,affinity);self.assertEqual(r['redirected_q']+r['absorbed_q']+r['body_q'],101+r['amplification_q'])
    def test_all_combat_contract_cases_pass(self):self.assertTrue(all(c['status']=='pass' for c in combat_contracts(DEFAULT_INPUTS)))
    def test_source_and_locked_fields_rejected(self):
        with self.assertRaisesRegex(ValueError,'derived'):self.save(changes=[Change(table='Equipment',row_key='shield.standard@1',column='revision_number',value='2')])
        with self.assertRaisesRegex(ValueError,'derived'):self.save(changes=[Change(table='Design_parameters',row_key='S-P01',column='value_int',value='1')])
    def test_duplicate_changes_and_unresolved_references(self):
        change=Change(table='Protection_profiles',row_key='protection.shield_standard.physical@1',column='allocation_steps',value='1')
        with self.assertRaisesRegex(ValueError,'duplicate'):self.save(changes=[change,change])
        with self.assertRaisesRegex(ValueError,'unresolved'):self.save(changes=[Change(table='Equipment',row_key='shield.standard@1',column='chassis_profile',value='missing')])
    def test_illegal_shield_budget_rejected(self):
        with self.assertRaisesRegex(ValueError,'shield_pooled'):self.save(changes=[Change(table='Protection_profiles',row_key='protection.shield_standard.physical@1',column='allocation_steps',value='2')])
    def test_dependency_and_revision_immutability(self):
        a=self.save();b=self.save(parent_revision_id=a['id'],input_overrides={'rating_q':'12000'})
        self.assertNotEqual(a['id'],b['id']);self.assertEqual(storage.revision(a['id'])['payload']['input_overrides'],{})
        self.assertEqual(len(self.client.graphs[0]['Lab_dependencies']),sum(len(rows) for table,rows in self.data['tables'].items() if not table.startswith('Lab_')))
        self.assertEqual(service.save_revision(RevisionRequest(subject_id=self.subject['subject_id'],title='Test shield',expected_snapshot_hash=self.hash),self.client)['id'],a['id'])
    def test_snapshot_guard(self):
        with self.assertRaisesRegex(ValueError,'snapshot'):service.save_revision(RevisionRequest(subject_id=self.subject['subject_id'],title='changed',expected_snapshot_hash='wrong'),self.client)
    def test_source_values_unchanged_by_experiment(self):
        before=digest(self.data);self.save(input_overrides={'rating_q':'12000'});self.assertEqual(digest(self.data),before)
        with self.assertRaises(ValueError):self.save(input_overrides={'scale':'1'})
    def test_property_hash_repeat(self):self.assertEqual(digest(property_case(7,8)),digest(property_case(7,8)))
    def test_reports_identical_across_worker_counts(self):
        revision=self.save();reports=[]
        for workers in [1,2]:
            run=storage.submit(RunRequest(revision_id=revision['id'],suite_id='property-10000',case_budget=64,workers=workers));job=storage.claim();reports.append(process(job,persist_grist=False))
        self.assertEqual(reports[0]['result_hash'],reports[1]['result_hash']);self.assertEqual(reports[0]['trace_hash'],reports[1]['trace_hash'])
    def test_cancel_and_restart_status(self):
        revision=self.save();a=storage.submit(RunRequest(revision_id=revision['id']));storage.cancel(a['id']);self.assertEqual(storage.run(a['id'])['status'],'cancelled')
        b=storage.submit(RunRequest(revision_id=revision['id']));storage.claim();self.assertEqual(storage.recover(),1);self.assertEqual(storage.run(b['id'])['status'],'interrupted')
    def test_blocked_metrics_not_zero(self):
        subject=next(s for s in service.subjects()['subjects'] if s['source_table']=='Techniques');c=item_probe(self.data,subject,DEFAULT_INPUTS,self.reg);self.assertEqual(c['status'],'blocked');self.assertEqual(c['metrics'],{})
        self.assertTrue(any(c['status']=='blocked' for c in tarot_probe(self.data)))
    def test_adoption_requires_successful_reviewed_matching_run(self):
        a=self.save();run=storage.submit(RunRequest(revision_id=a['id']))
        with self.assertRaises(ValueError):service.adoption(AdoptionRequest(revision_id=a['id'],run_id=run['id'],reviewed=True),self.client)
    def test_no_production_write_path(self):
        from lab.grist import Grist
        with self.assertRaisesRegex(ValueError,'production'):Grist().append('Equipment',[])
        with self.assertRaisesRegex(ValueError,'host'):Grist(url='https://example.com')
    def test_field_discovery_is_read_only_and_related_parameters_are_exposed(self):
        before=digest(self.data);fields=editable(self.data,self.subject,self.reg);self.assertEqual(digest(self.data),before)
        self.assertTrue(any(f['table']=='Design_parameters' and f['row_key']=='combat.group_step_calibration' for f in fields))
        self.assertFalse(any(f['row_key']=='S-P01' for f in fields))
    def test_reviewed_draft_preserves_original_and_rebinds_components(self):
        revision=self.save(changes=[Change(table='Equipment',row_key='shield.standard@1',column='authoring_notes',value='Reviewed lab candidate')])
        run=storage.submit(RunRequest(revision_id=revision['id'],suite_id='combat-contracts'));report=process(storage.claim(),persist_grist=False)
        draft=service.adoption(AdoptionRequest(revision_id=revision['id'],run_id=run['id'],reviewed=True),self.client)
        self.assertNotEqual(draft['drafts']['Equipment'][0]['equipment_revision_id'],'shield.standard@1')
        self.assertEqual(draft['drafts']['Equipment'][0]['lifecycle_status'],'draft');self.assertFalse(draft['approved_runtime'])
        self.assertNotEqual(draft['drafts']['Equipment'][0]['chassis_profile'],'chassis.shield_standard')
if __name__=='__main__':unittest.main()
