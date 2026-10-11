"""SQLite metadata only. DuckDB and analytical writes belong to the worker."""
import contextlib,json,sqlite3,time,uuid
from pathlib import Path
from . import config
from .content import encoded,digest
def connect():
    config.initialize();db=sqlite3.connect(config.DATA/'warehouse/jobs.sqlite',timeout=30)
    db.row_factory=sqlite3.Row;db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
CREATE TABLE IF NOT EXISTS snapshots(hash TEXT PRIMARY KEY,path TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS revisions(id TEXT PRIMARY KEY,experiment_id TEXT NOT NULL,parent_id TEXT,sequence INTEGER NOT NULL,snapshot_hash TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,revision_id TEXT NOT NULL,request TEXT NOT NULL,status TEXT NOT NULL,cancel_requested INTEGER NOT NULL DEFAULT 0,progress INTEGER NOT NULL DEFAULT 0,result_path TEXT,error TEXT,created_at TEXT NOT NULL,completed_at TEXT);
CREATE TABLE IF NOT EXISTS adoptions(id TEXT PRIMARY KEY,revision_id TEXT NOT NULL,run_id TEXT NOT NULL,path TEXT NOT NULL,created_at TEXT NOT NULL);
''');return db
def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);raw=(encoded(value)+'\n').encode('utf-8')
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('immutable_file_collision')
        return
    temp=path.with_suffix('.writing');temp.write_bytes(raw);temp.replace(path)
def latest_snapshot():
    with connect() as db:row=db.execute('SELECT * FROM snapshots ORDER BY created_at DESC,rowid DESC LIMIT 1').fetchone()
    if not row:raise ValueError('snapshot_not_synchronized')
    return dict(row)
def revision(revision_id):
    with connect() as db:row=db.execute('SELECT * FROM revisions WHERE id=?',(revision_id,)).fetchone()
    if not row:raise ValueError('unknown_revision')
    result=dict(row);result['payload']=json.loads(result['payload']);return result
def runs():
    with connect() as db:return [dict(r) for r in db.execute('SELECT * FROM runs ORDER BY created_at DESC,rowid DESC LIMIT 200')]
def run(run_id):
    with connect() as db:r=db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
    if not r:raise ValueError('unknown_run')
    return dict(r)
def submit(request):
    revision(request.revision_id);rid='run.'+uuid.uuid4().hex
    with connect() as db:db.execute('INSERT INTO runs(id,revision_id,request,status,created_at) VALUES(?,?,?,?,?)',(rid,request.revision_id,encoded(request.model_dump()),'queued',now()))
    return run(rid)
def cancel(run_id):
    with connect() as db:
        db.execute("UPDATE runs SET cancel_requested=1,status=CASE WHEN status='queued' THEN 'cancelled' ELSE status END WHERE id=? AND status IN ('queued','running')",(run_id,))
    return run(run_id)
def claim():
    db=connect()
    try:
        db.execute('BEGIN IMMEDIATE');row=db.execute("SELECT * FROM runs WHERE status='queued' ORDER BY rowid LIMIT 1").fetchone()
        if row:db.execute("UPDATE runs SET status='running' WHERE id=?",(row['id'],))
        db.commit();return dict(row) if row else None
    finally:db.close()
def recover():
    with connect() as db:
        return db.execute("UPDATE runs SET status='interrupted',error='Worker restarted; partial evidence retained; resubmit exact manifest to reproduce' WHERE status='running'").rowcount
