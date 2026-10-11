"""Single-worker analytical catalogue and normalized Parquet facts."""
import collections,json,threading
from pathlib import Path
import duckdb,pandas as pd,pandera.pandas as pa,pyarrow as arrow,pyarrow.parquet as parquet
from . import config
from .content import encoded,digest
LOCK=threading.RLock()
CASE_SCHEMA=pa.DataFrameSchema({'case_id':pa.Column(str,unique=True),'status':pa.Column(str,pa.Check.isin(['pass','fail','blocked','error','not_applicable']))},strict=False)
METRIC_SCHEMA=pa.DataFrameSchema({'case_id':pa.Column(str),'metric_id':pa.Column(str),'value_q':pa.Column('Int64',nullable=True),'value_int':pa.Column('Int64',nullable=True),'unit':pa.Column(str)},strict=True)
def write_facts(directory,run_id,cases):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    primary=[];metrics=[];traces=[];rules=[];input_rows=[]
    for case in cases:
        primary.append({'case_id':case['case_id'],'status':case['status'],'reason':case['reason']})
        for key,value in sorted(case['metrics'].items()):
            if type(value) is not int:raise ValueError('non_integer_metric')
            metrics.append({'case_id':case['case_id'],'metric_id':key,'value_q':value if key.endswith('_q') else None,'value_int':value if not key.endswith('_q') else None,'unit':'fixed_point' if key.endswith('_q') else 'integer'})
        case_inputs=case['details'].get('inputs',{k:v for k,v in case['details'].items() if type(v) is int})
        for key,value in sorted(case_inputs.items()):input_rows.append({'case_id':case['case_id'],'input_name':key,'value_q':value if key.endswith('_q') else None,'value_int':value if not key.endswith('_q') else None,'input_origin':'fixture-only'})
        for i,event in enumerate(case['trace']):traces.append({'event_id':case['case_id']+'.'+str(i),'case_id':case['case_id'],'run_id':run_id,'parent_event_id':case['case_id']+'.'+str(i-1) if i else None,**event})
        rules.extend({'case_id':case['case_id'],'rule_id':rid} for rid in case['rule_ids'])
    if primary:CASE_SCHEMA.validate(pd.DataFrame(primary))
    if metrics:
        frame=pd.DataFrame(metrics)
        for column in ['value_q','value_int']:frame[column]=pd.array([r[column] for r in metrics],dtype='Int64')
        METRIC_SCHEMA.validate(frame)
    schemas={
      'cases':arrow.schema([('case_id',arrow.string()),('status',arrow.string()),('reason',arrow.string())]),
      'metrics':arrow.schema([('case_id',arrow.string()),('metric_id',arrow.string()),('value_q',arrow.int64()),('value_int',arrow.int64()),('unit',arrow.string())]),
      'inputs':arrow.schema([('case_id',arrow.string()),('input_name',arrow.string()),('value_q',arrow.int64()),('value_int',arrow.int64()),('input_origin',arrow.string())]),
      'requirements':arrow.schema([('case_id',arrow.string()),('rule_id',arrow.string())]),
      'traces':arrow.schema([('event_id',arrow.string()),('case_id',arrow.string()),('run_id',arrow.string()),('parent_event_id',arrow.string()),('stage',arrow.string()),('before_q',arrow.int64()),('after_q',arrow.int64()),('delta_q',arrow.int64()),('unit',arrow.string()),('rule_id',arrow.string()),('source_revision_id',arrow.string()),('trace_kind',arrow.string()),('equation_revision_id',arrow.string()),('rounding',arrow.string()),('allocation_method',arrow.string())])}
    for name,rows in [('cases',primary),('metrics',metrics),('requirements',rules),('traces',traces),('inputs',input_rows)]:parquet.write_table(arrow.Table.from_pylist(rows,schema=schemas[name]),directory/(name+'.parquet'),compression='zstd')
    return {'case_rows':len(primary),'metric_rows':len(metrics),'trace_rows':len(traces),'requirement_rows':len(rules)}
def index_run(run_id,directory,report):
    config.initialize()
    with LOCK,duckdb.connect(str(config.DATA/'warehouse/triade.duckdb')) as db:
        db.execute('CREATE SCHEMA IF NOT EXISTS analytics');db.execute('CREATE SCHEMA IF NOT EXISTS trace')
        db.execute('CREATE TABLE IF NOT EXISTS analytics.runs(run_id VARCHAR PRIMARY KEY,case_count BIGINT,result_hash VARCHAR,trace_hash VARCHAR,report_path VARCHAR)')
        db.execute('INSERT OR REPLACE INTO analytics.runs VALUES (?,?,?,?,?)',[run_id,sum(report['counts'].values()),report['result_hash'],report['trace_hash'],str(Path(directory)/'report.json')])
        for name in ['cases','metrics','requirements','traces','inputs']:
            table='trace.'+name;path=str(Path(directory)/(name+'.parquet'))
            db.execute(f'CREATE TABLE IF NOT EXISTS {table} AS SELECT ?::VARCHAR AS lab_run_id,* FROM read_parquet(?) WHERE FALSE',[run_id,path])
            current={c[1] for c in db.execute(f"PRAGMA table_info('{table}')").fetchall()}
            for column,typ,*_ in db.execute('DESCRIBE SELECT * FROM read_parquet(?)',[path]).fetchall():
                if column not in current:db.execute(f'ALTER TABLE {table} ADD COLUMN "{column}" {typ}')
            db.execute(f'DELETE FROM {table} WHERE lab_run_id=?',[run_id]);db.execute(f'INSERT INTO {table} BY NAME SELECT ?::VARCHAR AS lab_run_id,* FROM read_parquet(?)',[run_id,path])
def query_run(run_id,kind,limit=200,offset=0):
    if kind not in {'cases','metrics','traces','requirements','inputs'}:raise ValueError('query_kind_not_allowed')
    limit=max(1,min(int(limit),1000));offset=max(0,int(offset))
    with LOCK,duckdb.connect(str(config.DATA/'warehouse/triade.duckdb')) as db:
        result=db.execute(f'SELECT * EXCLUDE(lab_run_id) FROM trace.{kind} WHERE lab_run_id=? ORDER BY case_id LIMIT ? OFFSET ?',[run_id,limit,offset]);names=[c[0] for c in result.description]
        return [dict(zip(names,row)) for row in result.fetchall()]
def rebuild():
    count=0
    for path in sorted((config.DATA/'runs').glob('run.*/report.json')):
        report=json.loads(path.read_text(encoding='utf-8'))
        if not (path.parent/'inputs.parquet').exists():write_facts(path.parent,path.parent.name,json.loads((path.parent/'cases.json').read_text(encoding='utf-8')))
        index_run(path.parent.name,path.parent,report);count+=1
    return count
