"""Bounded Grist transport; only reviewed lab tables can be written by the app."""
import os,time
from urllib.parse import urlparse,quote
import requests
from .config import GRIST_URL,DOC_ID
from .schema import TABLES,KEYS,GENERATED,IMMUTABLE
class Grist:
    def __init__(self,url=GRIST_URL,doc=DOC_ID):
        if urlparse(url).hostname not in {'localhost','127.0.0.1','::1','grist','triade-grist'}:raise ValueError('unapproved_grist_host')
        self.url=url.rstrip('/');self.doc=doc;self.headers={};self.session=requests.Session()
        if urlparse(url).hostname in {'grist','triade-grist'}:
            # Connect over the existing private Docker alias while preserving Grist's configured home-domain routing.
            self.headers['Host']='localhost:8484'
        secret_file=os.environ.get('TRIADE_GRIST_KEY_FILE')
        key=open(secret_file,encoding='utf-8').read().strip() if secret_file else os.environ.get('GRIST_API_KEY','')
        if key:self.headers['Authorization']='Bearer '+key
    def call(self,method,path,data=None):
        for attempt in range(4):
            r=self.session.request(method,self.url+'/api/docs/'+quote(self.doc,safe='')+path,headers=self.headers,json=data,timeout=30)
            if method=='GET' and r.status_code==429 and attempt<3:time.sleep(min(2**attempt,4));continue
            r.raise_for_status();return r.json()
    def snapshot(self,reg):
        tables=self.call('GET','/tables')['tables'];expected=set(reg['tables'])
        if {r['id'] for r in tables}!=expected:raise ValueError('grist_schema_set_mismatch')
        result={}
        for table in sorted(expected):
            from .content import VOLATILE
            prefix='/tables/'+quote(table,safe='');rows=[] if table in VOLATILE else self.call('GET',prefix+'/records?sort=id&limit=5000&cellFormat=typed')['records']
            if len(rows)>=5000:raise ValueError('bounded_snapshot_requires_pagination')
            columns=self.call('GET',prefix+'/columns')['columns']
            if {c['id'] for c in columns}!=set(reg['tables'][table]):raise ValueError('grist_column_schema_changed:'+table)
            result[table]={'columns':columns,'records':rows}
        return result
    def append(self,table,records):
        if table not in TABLES:raise ValueError('production_write_forbidden')
        key=KEYS[table];existing=self.call('GET','/tables/'+table+'/records?sort=id&limit=5000')['records']
        ids={r['fields'].get(key):r['fields'] for r in existing}
        fresh=[]
        for row in records:
            if row[key] in ids:
                if any(ids[row[key]].get(k)!=v for k,v in row.items()):raise ValueError('immutable_revision_collision')
            else:fresh.append({'fields':row})
        if fresh:
            self.call('POST','/tables/'+table+'/records',{'records':fresh})
            read=self.call('GET','/tables/'+table+'/records?sort=id&limit=5000')['records']
            actual={r['fields'][key]:r['fields'] for r in read}
            for row in fresh:
                if any(actual[row['fields'][key]].get(k)!=v for k,v in row['fields'].items()):raise ValueError('grist_readback_mismatch')
        return len(fresh)
    def all_rows(self,table):
        latest=self.call('GET','/tables/'+table+'/records?sort=-id&limit=1')['records'];maximum=latest[0]['id'] if latest else 0
        if maximum>1000000:raise ValueError('authoring_table_requires_large_catalogue_adapter')
        if maximum<=5000:return self.call('GET','/tables/'+table+'/records?sort=id&limit=5000')['records']
        import json
        result=[]
        for start in range(1,maximum+1,500):
            filt=quote(json.dumps({'id':list(range(start,min(maximum+1,start+500)))}),safe='')
            result.extend(self.call('GET','/tables/'+table+'/records?filter='+filt+'&sort=id&limit=500')['records'])
        return result
    def row_ids(self,table):
        from . import config
        import json
        key=KEYS.get(table)
        if key is None:key=json.loads((config.ROOT/'schema/authoring-registry-1.1.0.json').read_text(encoding='utf-8'))['stable_id_columns'][table]
        rows=self.all_rows(table);values={r['fields'][key]:r['id'] for r in rows}
        if len(values)!=len(rows):raise ValueError('stable_identity_collision:'+table)
        return values
    def append_graph(self,records):
        if any(t not in TABLES for t in records):raise ValueError('production_write_forbidden')
        # One Grist action transaction provides all-or-nothing normalized graph creation.
        actions=[];maps={t:self.row_ids(t) for t in records}
        for table,rows in records.items():
            for row in rows:
                key=row[KEYS[table]]
                if key not in maps[table]:maps[table][key]=max(maps[table].values(),default=0)+1
        existing={t:self.row_ids(t) for t in records}
        for table,rows in records.items():
            for row in rows:
                number=maps[table][row[KEYS[table]]]
                if row[KEYS[table]] in existing[table]:continue
                fields={}
                for key,value in row.items():
                    typ=TABLES[table][key]['type']
                    if typ.startswith('Ref:'):
                        target=typ[4:]
                        if target not in maps:maps[target]=self.row_ids(target)
                        value=0 if not value else maps[target][value]
                    fields[key]=value
                actions.append(['AddRecord',table,number,fields])
        if actions:self.call('POST','/apply',actions)
        # Ensure stable identities and scalar values survive the atomic write.
        for table,rows in records.items():
            actual=self.row_ids(table)
            if any(r[KEYS[table]] not in actual for r in rows):raise ValueError('graph_readback_missing')
        return len(actions)
