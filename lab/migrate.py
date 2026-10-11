"""Idempotent, candidate-only schema/seed migration with immediate table readbacks."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from migrate_authoring046 import plans,apply_seed
from .grist import Grist
from .content import load
class CandidateAPI:
    def __init__(self,candidate,active,backup):
        if len({candidate,active,backup})!=3:raise ValueError('candidate_active_backup_must_differ')
        self.candidate=candidate;self.active=active;self.backup=backup;self.grist=Grist(doc=candidate)
    def snapshot(self,document):
        if document!=self.candidate:raise ValueError('candidate_only')
        result={}
        for t in self.grist.call('GET','/tables')['tables']:
            name=t['id'];path='/tables/'+name
            records=self.grist.call('GET',path+'/records?sort=id&limit=5000&cellFormat=typed')['records']
            if len(records)>=5000:raise ValueError('snapshot_bound_exceeded')
            result[name]={'records':records,'columns':self.grist.call('GET',path+'/columns')['columns']}
        return result
    def apply_candidate(self,document,active,backup,actions):
        if document!=self.candidate or document in {active,backup}:raise ValueError('candidate_only')
        result=self.grist.call('POST','/apply',actions)
        for t in {a[1] for a in actions if len(a)>1}:self.grist.call('GET','/tables/'+t+'/records?sort=id&limit=5000')
        return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--active',required=True);p.add_argument('--backup',required=True);p.add_argument('--apply',action='store_true');args=p.parse_args()
    api=CandidateAPI(args.candidate,args.active,args.backup);reg=load(ROOT/'schema/authoring-registry-1.1.0.json');seed=load(ROOT/'content/lab-seed.json');source=load(ROOT/'content/canonical/authoring-1.1.0.json')
    seed['Ref_rules']=source['tables']['Ref_rules'];seed['Combat_equation_parameters']=source['tables']['Combat_equation_parameters']
    actions=plans(api.snapshot(args.candidate),reg,seed)
    if not args.apply:print(json.dumps({'schema_actions':len(actions),'candidate_only':True,'applied':False}));return
    for i in range(0,len(actions),25):api.apply_candidate(args.candidate,args.active,args.backup,actions[i:i+25])
    snapshot=api.snapshot(args.candidate);maps={t:{r['fields'].get(reg['stable_id_columns'][t]):r['id'] for r in d['records']} for t,d in snapshot.items()};changed=0;todo={t for t,rows in seed.items() if rows}
    while todo:
        progressed=False
        for table in sorted(todo):
            defs=reg['tables'][table];key=reg['stable_id_columns'][table]
            dependencies={defs[k]['type'][4:] for row in seed[table] for k,v in row.items() if v not in (None,'') and defs[k]['type'].startswith('Ref:')}
            if (dependencies-{table})&todo:continue
            existing={r['fields'].get(key):r for r in snapshot[table]['records']};batch=[]
            for row in seed[table]:
                fields={}
                for name,value in row.items():
                    d=defs[name]
                    if d['isFormula']:continue
                    if d['type'].startswith('Ref:'):value=maps[d['type'][4:]][value] if value else 0
                    fields[name]=value
                current=existing.get(row[key])
                if current:
                    from migrate_authoring046 import plain
                    diff={k:v for k,v in fields.items() if plain(current['fields'].get(k))!=v}
                    if diff:batch.append(['UpdateRecord',table,current['id'],diff])
                else:batch.append(['AddRecord',table,None,fields])
            for i in range(0,len(batch),40):api.apply_candidate(args.candidate,args.active,args.backup,batch[i:i+40])
            records=api.grist.call('GET','/tables/'+table+'/records?sort=id&limit=5000&cellFormat=typed')['records'];snapshot[table]['records']=records;maps[table]={r['fields'][key]:r['id'] for r in records}
            if any(sum(r['fields'][key]==row[key] for r in records)!=1 for row in seed[table]):raise ValueError('seed_identity_readback')
            changed+=len(batch);todo.remove(table);progressed=True
        if not progressed:raise ValueError('seed_dependency_cycle')
    print(json.dumps({'schema_actions':len(actions),'record_actions':changed,'candidate_only':True}))
if __name__=='__main__':main()
