"""Validated experiment creation and draft adoption, with Grist graph persistence."""
import copy,json,uuid
from pathlib import Path
import jsonschema
from . import config,storage
from .schema import registry,KEYS
from .grist import Grist
from .content import load,normalize,frozen_content,snapshot_hash,catalogue,coverage,encoded,digest,dependencies,apply_variant,validate_variant
from .adapters import inputs,DEFAULT_INPUTS
def reg():return load(config.ROOT/'schema/authoring-registry-1.1.0.json')
def source():
    info=storage.latest_snapshot();return info,load(info['path'])
def synchronize(client=None):
    client=client or Grist();r=reg();data=normalize(client.snapshot(r),r)
    jsonschema.Draft202012Validator(load(config.ROOT/'schema/authoring-1.1.schema.json')).validate(data)
    from .validation import validate_rows
    validate_rows(data,r)
    validate_variant(data,r);data=frozen_content(data);h=snapshot_hash(data);path=config.DATA/'snapshots'/f'{h}.json';storage.atomic_json(path,data)
    with storage.connect() as db:db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?)',(h,str(path),storage.now()))
    return {'snapshot_hash':h,'tables':len(data['tables']),'rows':sum(map(len,data['tables'].values())),'coverage':coverage(data)}
def subjects():
    info,data=source();rows=catalogue(data,reg())
    for row in rows:row['source_snapshot_hash']=info['hash']
    return {'snapshot_hash':info['hash'],'subjects':rows}
def save_revision(request,client=None):
    client=client or Grist();info,data=source();r=reg()
    if request.expected_snapshot_hash!=info['hash']:raise ValueError('source_snapshot_changed')
    subject=next((s for s in subjects()['subjects'] if s['subject_id']==request.subject_id),None)
    if not subject:raise ValueError('unknown_subject')
    parent=storage.revision(request.parent_revision_id) if request.parent_revision_id else None
    if parent and (parent['snapshot_hash']!=info['hash'] or parent['payload']['subject_id']!=subject['subject_id']):raise ValueError('parent_snapshot_or_subject_mismatch')
    # Each revision contains the complete patch relative to the pinned source, not a mutable delta chain.
    variant=apply_variant(data,subject,request.changes,r);values=inputs(request.input_overrides)
    context={'damage_type':'impact','delivery':'external','protection_scope':'contact_layer','guard':'prepared',**request.context}
    if set(context)!={'damage_type','delivery','protection_scope','guard'} or context['damage_type'] not in {x['damage_type_id'] for x in data['tables']['Ref_damage_types']} or context['delivery'] not in {'internal','external'} or context['protection_scope'] not in {'contact_layer','recipient_domain'} or context['guard'] not in {'prepared','unprepared'}:raise ValueError('invalid_test_context')
    payload=request.model_dump();payload['context']=context;payload['inputs']=values;payload['subject']=subject;payload['variant_hash']=digest(variant)
    eid=parent['experiment_id'] if parent else 'experiment.'+digest([subject['subject_id'],request.title])[:24]
    sequence=parent['sequence']+1 if parent else 1;h=digest(payload);rid=eid+'@'+str(sequence)+'.'+h[:12]
    created=storage.now();records={'Lab_experiments':[{'experiment_id':eid,'subject':subject['subject_id'],'display_name':request.title}],
      'Lab_experiment_revisions':[{'revision_id':rid,'experiment':eid,'parent':request.parent_revision_id,'source_snapshot_hash':info['hash'],'sequence':sequence,'content_hash':h,'created_at':created,'runner_version':'1.0.0'}],
      'Lab_changes':[],'Lab_dependencies':[]}
    for i,change in enumerate(request.changes):
        typ=r['tables'][change.table][change.column]['type'];value=change.value
        records['Lab_changes'].append({'change_id':rid+'.change.'+str(i),'revision':rid,'target_table':change.table,'row_key':change.row_key,'column_id':change.column,'operation':'replace','value_kind':typ,'value_text':value if isinstance(value,str) and typ!='Int' else '', 'value_int':int(value) if typ=='Int' and value is not None else None,'value_q':None,'value_bool':value if type(value) is bool else False,'sort_order':i})
    for i,(key,value) in enumerate(sorted(request.input_overrides.items())):
        records['Lab_changes'].append({'change_id':rid+'.input.'+key,'revision':rid,'target_table':'fixture-only','row_key':'comparison-inputs','column_id':key,'operation':'experiment_override','value_kind':'fixed_point' if key.endswith('_q') else 'integer','value_text':'','value_int':int(value) if not key.endswith('_q') else None,'value_q':int(value) if key.endswith('_q') else None,'value_bool':False,'sort_order':200+i})
    for i,(key,value) in enumerate(sorted(context.items())):records['Lab_changes'].append({'change_id':rid+'.context.'+key,'revision':rid,'target_table':'fixture-only','row_key':'test-context','column_id':key,'operation':'experiment_context','value_kind':'text','value_text':value,'value_int':None,'value_q':None,'value_bool':False,'sort_order':400+i})
    for i,d in enumerate(dependencies(data,subject,r)):records['Lab_dependencies'].append({'dependency_id':rid+'.dependency.'+str(i),'revision':rid,**d,'snapshot_hash':info['hash']})
    # Serialize experiment writes across API requests while Grist applies the entire graph atomically.
    db=storage.connect()
    try:
        db.execute('BEGIN IMMEDIATE');existing=db.execute('SELECT * FROM revisions WHERE id=?',(rid,)).fetchone()
        if existing:db.commit();return storage.revision(rid)
        client.append_graph(records)
        db.execute('INSERT INTO revisions VALUES(?,?,?,?,?,?,?)',(rid,eid,request.parent_revision_id,sequence,info['hash'],encoded(payload),created));db.commit()
    except Exception:db.rollback();raise
    finally:db.close()
    return storage.revision(rid)
def reconstructed(revision):
    with storage.connect() as db:row=db.execute('SELECT * FROM snapshots WHERE hash=?',(revision['snapshot_hash'],)).fetchone()
    data=load(row['path']);from .models import Change
    subject=revision['payload']['subject'];changes=[Change(**c) for c in revision['payload']['changes']]
    return data,apply_variant(data,subject,changes,reg()),subject
def adoption(request,client=None):
    client=client or Grist();rev=storage.revision(request.revision_id);run=storage.run(request.run_id)
    if run['revision_id']!=rev['id'] or run['status']!='completed':raise ValueError('completed_matching_proof_required')
    report=load(Path(run['result_path'])/'report.json')
    if report['counts'].get('fail',0) or report['counts'].get('error',0):raise ValueError('failed_proof_cannot_adopt')
    baseline,variant,subject=reconstructed(rev)
    if subject['is_template']:raise ValueError('template_needs_authored_dependency_graph')
    if not rev['payload']['changes']:raise ValueError('fixture_input_only_experiment_has_no_content_change')
    root=subject['source_table'];key=reg()['stable_id_columns'][root];old=next(r for r in variant['tables'][root] if r[key]==subject['source_revision_id']);draft=copy.deepcopy(old)
    if 'revision_number' in draft:
        draft['revision_number']+=1;identity=draft.get('equipment_id') or draft.get('technique_id') or str(old[key]).split('@')[0];new_id=identity+'@'+str(draft['revision_number'])
    else:new_id=str(old[key])+'.draft.'+rev['id'].split('.')[-1]
    draft[key]=new_id
    if 'revision_id' in draft:draft['revision_id']=new_id
    if 'lifecycle_status' in draft:draft['lifecycle_status']='draft'
    if 'design_status' in draft:draft['design_status']='open'
    for field in ['approved_by','approved_at','content_hash']:
        if field in draft:draft[field]=None if field=='approved_at' else ''
    # Related modified components are immutable draft copies, and draft root references are rebound.
    from .content import editable
    components={root:[draft]};remap={subject['source_revision_id']:new_id}
    related=sorted({(f['table'],f['row_key']) for f in editable(variant,subject,reg()) if f['table']!=root})
    for table,row_key in related:
        target_key=reg()['stable_id_columns'][table];record=copy.deepcopy(next(r for r in variant['tables'][table] if r[target_key]==row_key));new=row_key+'.draft.'+rev['id'].split('.')[-1]
        record[target_key]=new;components.setdefault(table,[]).append(record);remap[row_key]=new
        for alias in ('base_martial_profile_id','defence_profile_id'):
            if record.get(alias):remap[record[alias]]=record[alias]+'.draft.'+rev['id'].split('.')[-1]
    for table,rows in components.items():
        for row in rows:
            for field,value in row.items():
                if isinstance(value,str) and value in remap:row[field]=remap[value]
    check=copy.deepcopy(baseline)
    for table,rows in components.items():check['tables'][table].extend(rows)
    validate_variant(check,reg())
    aid='adoption.'+digest([rev['id'],request.run_id])[:24];artifact={'adoption_id':aid,'state':'reviewed_draft_pending_release','source_snapshot_hash':rev['snapshot_hash'],'experiment_revision':rev['id'],'proof_run_id':request.run_id,'proof_result_hash':report['result_hash'],'drafts':components,'blocking_gaps':report['counts'].get('blocked',0),'approved_runtime':False}
    path=config.DATA/'drafts'/(aid+'.json');storage.atomic_json(path,artifact)
    client.append_graph({'Lab_adoption_requests':[{'adoption_id':aid,'revision':rev['id'],'run_id':request.run_id,'state':artifact['state'],'draft_hash':digest(artifact),'proof_hash':report['result_hash'],'created_at':storage.now()}]})
    with storage.connect() as db:db.execute('INSERT OR IGNORE INTO adoptions VALUES(?,?,?,?,?)',(aid,rev['id'],request.run_id,str(path),storage.now()))
    return artifact
