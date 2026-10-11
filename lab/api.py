import json
from pathlib import Path
from contextlib import asynccontextmanager
import httpx,requests
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from . import config,storage
from .models import RevisionRequest,RunRequest,AdoptionRequest,SyncRequest
from .service import synchronize,source,subjects,save_revision,adoption,reg
from .content import catalogue,coverage,editable,load
from .numeric import wire
from .adapters import DEFAULT_INPUTS,LIMITS,ADAPTERS,inputs
@asynccontextmanager
async def lifespan(app):config.initialize();yield
app=FastAPI(title='Triade Tuning Lab',version='1.0.0',lifespan=lifespan)
@app.exception_handler(ValueError)
async def value_error(request,error):return JSONResponse({'detail':str(error)},status_code=422)
@app.exception_handler(requests.RequestException)
async def grist_error(request,error):return JSONResponse({'detail':'Grist request failed; source and experiment state retained'},status_code=503)
@app.middleware('http')
async def origin_guard(request,call_next):
    origin=request.headers.get('origin')
    if request.method not in ('GET','HEAD','OPTIONS') and origin and origin not in {'http://127.0.0.1:8765','http://localhost:8765'}:return JSONResponse({'detail':'local_origin_required'},status_code=403)
    return await call_next(request)
@app.get('/api/v1/health')
def health():return {'status':'ok','version':'1.0.0'}
@app.get('/api/v1/info')
def info():
    try:current,data=source();snapshot=current['hash'];damage_types=[r['damage_type_id'] for r in data['tables']['Ref_damage_types']]
    except ValueError:snapshot=None;damage_types=[]
    return {'version':'1.0.0','design_version':'0.47.0','authoring_schema':'1.1.0','execution_schema':'1.0.0','snapshot_hash':snapshot,'grist_doc_id':config.DOC_ID,'production_tuning_unchanged':True,'default_inputs':wire(DEFAULT_INPUTS),'input_limits':wire(LIMITS),'damage_types':damage_types,'input_origin':'fixture-only'}
@app.post('/api/v1/sync')
def sync(request:SyncRequest):
    result=synchronize()
    if request.expected_source_hash and request.expected_source_hash!=result['snapshot_hash']:raise HTTPException(409,'Source changed; review the new frozen snapshot')
    return wire(result)
@app.get('/api/v1/subjects')
def list_subjects():return subjects()
@app.get('/api/v1/subjects/{subject_id}/fields')
def fields(subject_id:str):
    _,data=source();subject=next((s for s in subjects()['subjects'] if s['subject_id']==subject_id),None)
    if not subject:raise ValueError('unknown_subject')
    return wire({'fields':editable(data,subject,reg())})
@app.get('/api/v1/coverage')
def get_coverage():return wire(coverage(source()[1]))
@app.get('/api/v1/adapters')
def adapters():return ADAPTERS
@app.get('/api/v1/chart-profiles')
def chart_profiles():
    _,data=source();return wire({'profiles':data['tables']['Lab_chart_profiles'],'axes':data['tables']['Lab_chart_axes'],'metrics':data['tables']['Lab_metrics']})
@app.post('/api/v1/experiments/revisions')
def create_revision(request:RevisionRequest):return wire(save_revision(request))
@app.get('/api/v1/experiments/revisions')
def revisions():
    with storage.connect() as db:rows=[dict(r) for r in db.execute('SELECT id,experiment_id,parent_id,sequence,snapshot_hash,payload,created_at FROM revisions ORDER BY rowid DESC')]
    for row in rows:row['payload']=json.loads(row['payload'])
    return wire(rows)
@app.post('/api/v1/runs',status_code=202)
def submit_run(request:RunRequest):
    inputs({k:v[0] for k,v in request.sweep.items() if v})
    return wire(storage.submit(request))
@app.get('/api/v1/runs')
def list_runs():return wire([{k:v for k,v in r.items() if k not in ('result_path','request')} for r in storage.runs()])
@app.get('/api/v1/runs/{run_id}')
def get_run(run_id:str):return wire({k:v for k,v in storage.run(run_id).items() if k not in ('result_path','request')})
@app.post('/api/v1/runs/{run_id}/cancel')
def cancel(run_id:str):return wire(storage.cancel(run_id))
@app.get('/api/v1/runs/{run_id}/report')
def report(run_id:str):
    row=storage.run(run_id)
    if not row['result_path']:raise HTTPException(409,'Run has no completed result yet')
    return wire(load(Path(row['result_path'])/'report.json'))
@app.get('/api/v1/runs/{run_id}/facts/{kind}')
def facts(run_id:str,kind:str,limit:int=200,offset:int=0):
    if kind not in {'cases','metrics','traces','requirements','inputs'}:raise ValueError('invalid_fact_kind')
    try:
        response=httpx.get(config.WORKER_URL+f'/query/{run_id}/{kind}',params={'limit':limit,'offset':offset},timeout=30);response.raise_for_status();return response.json()
    except httpx.HTTPError:raise HTTPException(503,'Catalogue worker unavailable; retained result files are intact')
@app.get('/api/v1/runs/{run_id}/download/{artifact}')
def download(run_id:str,artifact:str):
    if artifact not in {'report.json','manifest.json','cases.json','cases.parquet','metrics.parquet','traces.parquet','requirements.parquet','inputs.parquet'}:raise HTTPException(404)
    row=storage.run(run_id)
    if not row['result_path']:raise HTTPException(409)
    path=Path(row['result_path'])/artifact
    if not path.exists():raise HTTPException(404)
    return FileResponse(path,filename=run_id+'-'+artifact)
@app.post('/api/v1/adoption-requests')
def create_adoption(request:AdoptionRequest):return wire(adoption(request))
WEB=config.ROOT/'lab/web/dist'
if WEB.exists():
    app.mount('/assets',StaticFiles(directory=WEB/'assets'),name='assets')
    @app.get('/')
    def homepage():return FileResponse(WEB/'index.html')
