"""Loopback Grist API migration/read client; credentials remain in environment."""
import json,os,time
from urllib.parse import urlparse,quote
from urllib.request import Request,urlopen
from urllib.error import HTTPError

class GristAPI:
    def __init__(self, base_url=None, api_key=None):
        self.base=(base_url or os.environ.get('GRIST_BASE_URL','http://localhost:8484')).rstrip('/')
        host=urlparse(self.base).hostname
        if host not in {'localhost','127.0.0.1','::1'}:raise ValueError('loopback_endpoint_required')
        self.key=api_key if api_key is not None else os.environ.get('GRIST_API_KEY','')

    def request(self,method,path,data=None):
        headers={'Content-Type':'application/json'}
        if self.key:headers['Authorization']='Bearer '+self.key
        body=json.dumps(data).encode('utf-8') if data is not None else None
        for attempt in range(4):
            try:
                with urlopen(Request(self.base+path,data=body,headers=headers,method=method),timeout=60) as reply:
                    return json.load(reply)
            except HTTPError as error:
                if error.code!=429 or method!='GET' or attempt==3:raise
                time.sleep(min(2**attempt,4))

    def snapshot(self,document):
        prefix='/api/docs/'+quote(document,safe=''); result={}
        for table in self.request('GET',prefix+'/tables')['tables']:
            name=table['id'];path=prefix+'/tables/'+quote(name,safe='')
            result[name]={'columns':self.request('GET',path+'/columns')['columns'],
                          'records':self.request('GET',path+'/records?sort=id&limit=5000&cellFormat=typed')['records']}
            if len(result[name]['records'])>=5000:raise ValueError('bounded_snapshot_requires_pagination:'+name)
        return result

    def apply_candidate(self,document,active,backup,actions):
        if document in {active,backup}:raise ValueError('candidate_only_mutation')
        return self.request('POST','/api/docs/'+quote(document,safe='')+'/apply',actions)
