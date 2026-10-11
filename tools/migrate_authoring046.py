"""API-backed candidate-only, stable-ID, idempotent authoring migration."""
import argparse,json
from pathlib import Path
from authoring_api import GristAPI

def identity(row,key):
    if key in row:return row[key]
    if key=='faculty_revision_id':return row['faculty_id']+'@'+str(row['revision_number'])
    return row[next(iter(row))]

def plain(value):return value[2] if isinstance(value,list) and len(value)==3 and value[0]=='R' else value

def plans(snapshot,registry,seed):
    actions=[]
    for table,columns in registry['tables'].items():
        if table not in snapshot:actions.append(['AddTable',table,[]])
    for table,columns in registry['tables'].items():
        existing={c['id']:c['fields'] for c in snapshot.get(table,{}).get('columns',[])}
        for name,definition in columns.items():
            metadata={k:definition[k] for k in ('type','formula','isFormula')}
            current=existing.get(name)
            if not current:actions.append(['AddColumn',table,name,metadata])
            elif any(current.get(k)!=v for k,v in metadata.items()):actions.append(['ModifyColumn',table,name,metadata])
    return actions

def apply_seed(api,candidate,active,backup,registry,seed):
    if candidate in {active,backup}:raise ValueError('candidate_only_mutation')
    snapshot=api.snapshot(candidate);todo={t for t,rows in seed.items() if rows};mutations=0
    while todo:
        progressed=False
        for table in sorted(todo):
            definitions=registry['tables'][table];key=registry['stable_id_columns'][table]
            dependencies={definitions[k]['type'][4:] for row in seed[table] for k,v in row.items() if definitions[k]['type'].startswith('Ref:') and v not in (None,'')}
            if (dependencies-{table}) & todo:continue
            existing={r['fields'].get(key):r for r in snapshot[table]['records']}
            changes=[]
            for row in seed[table]:
                payload={}
                for name,value in row.items():
                    definition=definitions[name]
                    if definition['isFormula']:continue
                    if definition['type'].startswith('Ref:'):
                        target=definition['type'][4:];target_key=registry['stable_id_columns'][target]
                        matches=[r for r in snapshot[target]['records'] if r['fields'].get(target_key)==value]
                        if value in (None,''):value=0
                        elif len(matches)!=1:raise ValueError('unresolved_or_duplicate_seed_reference')
                        else:value=matches[0]['id']
                    payload[name]=value
                record=existing.get(identity(row,key))
                if not record:changes.append(['AddRecord',table,None,payload])
                else:
                    diff={k:v for k,v in payload.items() if plain(record['fields'].get(k))!=v}
                    if diff:changes.append(['UpdateRecord',table,record['id'],diff])
            for i in range(0,len(changes),50):api.apply_candidate(candidate,active,backup,changes[i:i+50])
            mutations+=len(changes);snapshot=api.snapshot(candidate)
            for row in seed[table]:
                matches=[r for r in snapshot[table]['records'] if r['fields'].get(key)==identity(row,key)]
                if len(matches)!=1:raise ValueError('stable_identity_readback_failed')
            todo.remove(table);progressed=True
        if not progressed:raise ValueError('seed_dependency_cycle')
    return mutations

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',required=True);parser.add_argument('--active',required=True);parser.add_argument('--backup',required=True);parser.add_argument('--registry',required=True);parser.add_argument('--seed',required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if len({args.candidate,args.active,args.backup})!=3:parser.error('active, backup and candidate must be distinct')
    api=GristAPI();registry=json.loads(Path(args.registry).read_text(encoding='utf-8'));seed=json.loads(Path(args.seed).read_text(encoding='utf-8'))
    actions=plans(api.snapshot(args.candidate),registry,seed)
    if not args.apply:print(json.dumps({'schema_actions':len(actions),'candidate_only':True,'applied':False}));return
    for i in range(0,len(actions),25):api.apply_candidate(args.candidate,args.active,args.backup,actions[i:i+25])
    changed=apply_seed(api,args.candidate,args.active,args.backup,registry,seed)
    print(json.dumps({'schema_actions':len(actions),'record_actions':changed,'candidate_only':True}))
if __name__=='__main__':main()
