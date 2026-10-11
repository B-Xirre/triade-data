"""Durable run execution; this process alone owns the DuckDB catalogue."""
import collections,itertools,json,os,threading,time,hashlib
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from . import config,storage
from .models import RunRequest
from .service import reconstructed,reg
from .content import digest,load
from .adapters import execute,inputs,item_probe,DEFAULT_INPUTS,ADAPTERS
from .analytics import write_facts,index_run,query_run,rebuild
from .numeric import wire
from .grist import Grist
STOP=threading.Event()
def cancelled(run_id):return bool(storage.run(run_id)['cancel_requested'])
def process(job,persist_grist=True):
    rid=job['id'];request=RunRequest(**json.loads(job['request']));revision=storage.revision(request.revision_id)
    baseline,variant,subject=reconstructed(revision);r=reg();values=dict(revision['payload']['inputs']);resolved_overrides=dict(revision['payload']['input_overrides'])
    # Numeric edits stay in the experiment snapshot. Resolve only reviewed source-field relationships.
    if subject['source_table']=='Techniques' and not subject['is_template']:
        technique=next(t for t in variant['tables']['Techniques'] if t['revision_id']==subject['source_revision_id'])
        params={p['parameter_id']:p for p in variant['tables']['Design_parameters']}
        for field,symbol in [('base_cost_parameter','base_cost'),('adverse_tax_cap_parameter','tax_cap')]:
            p=params.get(technique.get(field))
            if p and p['value_kind']=='integer' and p['value_state']!='unset' and p['value_int'] is not None and symbol not in resolved_overrides:resolved_overrides[symbol]=str(p['value_int'])
    if any(c['table']=='Design_parameters' and c['row_key']=='combat.group_step_calibration' for c in revision['payload']['changes']):
        p=next(p for p in variant['tables']['Design_parameters'] if p['parameter_id']=='combat.group_step_calibration')
        if p['value_kind']=='fixed_point' and p['value_state']!='unset' and p['value_q'] is not None and 'rating_q' not in resolved_overrides:resolved_overrides['rating_q']=str(p['value_q'])
    values=inputs(resolved_overrides)
    # Worker count and wall-clock metadata are excluded from semantic proof hashes.
    utilities={'bootstrap.py','migrate.py','release_proof.py','cli.py'}
    runtime_files=[p for p in sorted(Path(__file__).parent.glob('*.py')) if p.name not in utilities]
    runtime_files += [config.ROOT/'tools/combat_contracts.py',config.ROOT/'lab/requirements.lock']
    build_hash=digest({p.relative_to(config.ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime_files})
    manifest={'lab_execution_schema':'1.0.0','runner_version':'1.0.0','runner_build_hash':build_hash,'snapshot_hash':revision['snapshot_hash'],'experiment_content_hash':digest(revision['payload']),'variant_hash':revision['payload']['variant_hash'],'fixture_version':'lab-1.0.0','suite':request.suite_id,'root_seed':int(request.root_seed),'rng_stream_manifest':{'property':'sha256(root_seed:partition:case_index)','shared_across_paired_variants':True},'adapter_versions':{k:v['version'] for k,v in ADAPTERS.items()},'metric_version':'1.0.0','case_budget':request.case_budget,'input_origin':'fixture-only','inputs':values,'sweep':request.sweep}
    directory=config.DATA/'runs'/rid;directory.mkdir(parents=True,exist_ok=True)
    storage.atomic_json(directory/'manifest.json',manifest)
    def progress(n):
        with storage.connect() as db:db.execute('UPDATE runs SET progress=? WHERE id=?',(n,rid))
    cases=execute(variant,subject,values,r,request.suite_id,int(request.root_seed),request.case_budget,request.workers,lambda:cancelled(rid),progress,resolved_overrides)
    context=revision['payload'].get('context');comparison={'baseline':item_probe(baseline,subject,DEFAULT_INPUTS,r,context),'variant':item_probe(variant,subject,values,r,context),'profile_version':'1.0.0','sample_count':1,'input_origin':'fixture-only','control_inputs':DEFAULT_INPUTS,'variant_inputs':values,'shared_context':context,'recommendation':'Review trade-offs; no automatic adoption'}
    if request.sweep:
        names=sorted(request.sweep)
        combinations=1
        for name in names:
            if name not in DEFAULT_INPUTS or not request.sweep[name]:raise ValueError('invalid_sweep_dimension')
            combinations*=len(request.sweep[name])
        if combinations>request.case_budget:raise ValueError('sweep_case_budget_exceeded')
        sweep=[]
        for i,combination in enumerate(itertools.product(*(request.sweep[n] for n in names))):
            if cancelled(rid):break
            overrides={**{k:str(v) for k,v in values.items()},**dict(zip(names,combination))};point=inputs(overrides)
            result=item_probe(variant,subject,point,r,context);result['case_id']=f'sweep.{i:05}';cases.append(result);sweep.append({'inputs':{n:point[n] for n in names},'metrics':result['metrics'],'status':result['status']})
        comparison['sweep']=sweep
        # Fractional partition dominance is advisory; different axes have independent units.
        comparable=[p for p in sweep if p['status']=='pass' and 'body_q' in p['metrics']]
        comparison['pareto_candidates']=[p for p in comparable if not any(o['metrics']['body_q']<p['metrics']['body_q'] and o['metrics']['redirected_q']>=p['metrics']['redirected_q'] for o in comparable)]
    cases.sort(key=lambda c:c['case_id']);counts=dict(collections.Counter(c['status'] for c in cases))
    trace=[{'case_id':c['case_id'],'events':c['trace']} for c in cases]
    result_hash=digest({'manifest':manifest,'cases':cases,'comparison':comparison});trace_hash=digest(trace)
    state='cancelled' if cancelled(rid) else 'failed' if counts.get('fail',0) or counts.get('error',0) else 'completed'
    report={'run_id':rid,'state':state,'counts':counts,'result_hash':result_hash,'trace_hash':trace_hash,'manifest_hash':digest(manifest),'comparison':comparison,'registered_coverage':'reported separately; passing cases do not imply all requirements pass','execution_workers':request.workers}
    storage.atomic_json(directory/'cases.json',cases);storage.atomic_json(directory/'report.json',report)
    fact_counts=write_facts(directory,rid,cases);index_run(rid,directory,report)
    if persist_grist:
        summary={'summary_id':'summary.'+rid,'run_id':rid,'revision':revision['id'],'state':state,'result_hash':result_hash,'trace_hash':trace_hash}
        summary.update({key+'_count':counts.get(key,0) for key in ('pass','fail','blocked','error','not_applicable')})
        Grist().append_graph({'Lab_result_summaries':[summary]})
    with storage.connect() as db:db.execute('UPDATE runs SET status=?,result_path=?,progress=?,completed_at=? WHERE id=?',(state,str(directory),len(cases),storage.now(),rid))
    return report
def loop():
    storage.recover()
    while not STOP.wait(.25):
        job=storage.claim()
        if not job:continue
        try:process(job)
        except Exception as e:
            with storage.connect() as db:db.execute("UPDATE runs SET status='error',error=?,completed_at=? WHERE id=?",(str(e),storage.now(),job['id']))
@asynccontextmanager
async def lifespan(app):
    config.initialize();thread=threading.Thread(target=loop,daemon=True);thread.start();yield;STOP.set();thread.join(timeout=5)
app=FastAPI(title='Triade Lab catalogue worker',lifespan=lifespan)
@app.get('/health')
def health():return {'status':'ok','duckdb_writer':'single-worker','version':'1.0.0'}
@app.get('/query/{run_id}/{kind}')
def query(run_id:str,kind:str,limit:int=200,offset:int=0):return wire(query_run(run_id,kind,limit,offset))
@app.post('/rebuild')
def rebuild_catalogue():return {'rebuilt_runs':rebuild()}
