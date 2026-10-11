"""Authoring 1.0.0 canonical export and versioned contracts-first validation."""
from pathlib import Path
import argparse,collections,csv,hashlib,json
import jsonschema
from authoring_api import GristAPI

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def canonical(snapshot,registry):
    expected=registry['tables']
    if set(snapshot)!=set(expected):raise ValueError('table_set_mismatch')
    ids={}
    for table,data in snapshot.items():
        key=registry['stable_id_columns'][table]
        ids[table]={r['id']:r['fields'].get(key) for r in data['records']}
        values=list(ids[table].values())
        if any(not isinstance(v,str) or not v for v in values):raise ValueError('missing_stable_id:'+table)
        if len(values)!=len(set(values)):raise ValueError('duplicate_stable_id:'+table)
    result={'schema_version':'1.0.0','design_version':'0.46.0','tables':{}}
    reference_count=0
    for table,definitions in expected.items():
        rows=[]
        excluded=registry['canonical_excluded_columns'].get(table,[])
        for record in snapshot[table]['records']:
            row={}
            for name,definition in definitions.items():
                if name in excluded:continue
                value=record['fields'].get(name)
                typ=definition['type']
                if isinstance(value,list):
                    if len(value)==3 and value[0]=='R':
                        target=typ.removeprefix('Ref:');number=value[2]
                        if number==0:value=None
                        elif number not in ids.get(target,{}):raise ValueError('unresolved_reference:'+table+'.'+name)
                        else:value=ids[target][number];reference_count+=1
                    elif value and value[0]=='E':raise ValueError('formula_error:'+table+'.'+name)
                    else:raise ValueError('unsupported_typed_value:'+table+'.'+name)
                elif typ.startswith('Ref:'):
                    target=typ[4:]
                    if value in (None,0,''):value=None
                    elif isinstance(value,int) and value in ids[target]:value=ids[target][value];reference_count+=1
                    else:raise ValueError('unresolved_reference:'+table+'.'+name)
                if isinstance(value,float):raise ValueError('canonical_float:'+table+'.'+name)
                if table=='Design_parameters' and record['fields'].get('value_state')=='unset' and name in {'value_q','value_int','value_text'}:value=None
                row[name]=value
            rows.append(row)
        key=registry['stable_id_columns'][table]
        rows.sort(key=lambda r:(r.get('sort_order') or 0,r[key]))
        result['tables'][table]=rows
    return result,reference_count

def validate(data,registry,manifest,schema):
    jsonschema.Draft202012Validator(schema).validate(data)
    tables=data['tables'];rules=tables['Ref_rules']
    identities={}
    for table,rows in tables.items():
        key=registry['stable_id_columns'][table]
        values=[r[key] for r in rows]
        if len(values)!=len(set(values)):raise ValueError('duplicate_stable_id:'+table)
        identities[table]=set(values)
    for table,rows in tables.items():
        for name,definition in registry['tables'][table].items():
            if name in registry['canonical_excluded_columns'].get(table,[]):continue
            if definition['type'].startswith('Ref:'):
                target=definition['type'][4:]
                for row in rows:
                    if row[name] is not None and row[name] not in identities[target]:
                        raise ValueError('unresolved_reference:'+table+'.'+name)
    severities=collections.Counter(r['severity'] for r in rules)
    if len(rules)!=manifest['expected_rule_total'] or dict(severities)!=manifest['expected_severities']:
        raise ValueError('source_rule_census_mismatch')
    faculties=tables['Faculties']
    if {r['faculty_id'] for r in faculties}!={'faculty.arcana','faculty.mudra','faculty.psyche','faculty.somatic'}:
        raise ValueError('faculty_identity_mismatch')
    if len(tables['Faculty_profiles'])!=8 or len(tables['Faculty_technique_authorizations'])!=32:
        raise ValueError('faculty_profile_vocabulary_census')
    if any(r['faculty_family_id']=='innate' for r in tables['Ref_faculty_families']):raise ValueError('retired_innate_family')
    params={r['parameter_id']:r for r in tables['Design_parameters']}
    scale=params['S-P01']
    if scale['value_kind']!='integer' or scale['value_state']!='locked' or scale['value_int']!=12000:
        raise ValueError('fixed_point_constant_invalid')
    for row in params.values():
        if row['value_state'] not in {'unset','provisional','locked'}:raise ValueError('invalid_parameter_state')
        if row['value_state']=='unset' and any(row[k] is not None for k in ('value_q','value_int','value_text')):
            raise ValueError('unset_parameter_became_zero')
    for row in tables['Faculty_profiles']:
        if row['has_pull'] and row['pull_dm']+row['pull_df']+row['pull_di']!=0:raise ValueError('profile_pull_not_zero_sum')
    members=collections.Counter(r['profile'] for r in tables['Faculty_profile_members'])
    for row in tables['Faculty_profiles']:
        count=members[row['revision_id']]
        if count!=(1 if row['profile_kind']=='base' else 2):raise ValueError('profile_member_cardinality')
    for row in tables['Fixture_encounter_members']:
        if row['quantity']<1:raise ValueError('invalid_encounter_quantity')
    for row in tables['Defence_profile_entries']:
        if row['entry_kind']=='group' and row['damage_group']=='structural':raise ValueError('structural_typed_defence')
        if not row['protection_scope'] or not row['contribution_id'] or not row['consuming_stage']:
            raise ValueError('missing_defence_scope')
    seen=set()
    for row in tables['Protection_contributions']:
        key=(row['source_revision_id'],row['damage_type'],row['effect_field'])
        if key in seen:raise ValueError('duplicate_protection_contribution')
        seen.add(key)
    for row in tables['Fixture_builds']:
        q=[row['floor_m_q'],row['floor_f_q'],row['floor_i_q']]
        if sum(q)>5400 or max(q)>3000:raise ValueError('fixture_floor_q_invalid')
        if row['validation_state']!='blocked' or not row['blocking_reason']:raise ValueError('fixture_readiness_fabricated')
    return {'table_count':len(tables),'row_count':sum(map(len,tables.values())),'rule_count':len(rules),'severity_counts':dict(severities),'unset_parameters':sum(r['value_state']=='unset' for r in params.values()),'runtime_ready':False}

def export(data,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    raw=encoded(data)+'\n';(directory/'authoring.json').write_text(raw,encoding='utf-8',newline='\n')
    csv_dir=directory/'csv';csv_dir.mkdir(exist_ok=True)
    for table,rows in data['tables'].items():
        if not rows:continue
        fields=sorted(rows[0])
        with (csv_dir/(table+'.csv')).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot');parser.add_argument('--doc-id');parser.add_argument('--registry',required=True);parser.add_argument('--manifest',required=True);parser.add_argument('--schema',required=True);parser.add_argument('--output',required=True);parser.add_argument('--profile',choices=['authoring','approved-runtime'],default='authoring');args=parser.parse_args()
    if args.profile=='approved-runtime':raise SystemExit('BLOCKED: authoring-only release; unbound coefficients and runtime gates remain')
    snapshot=load(args.snapshot) if args.snapshot else GristAPI().snapshot(args.doc_id)
    registry=load(args.registry);data,references=canonical(snapshot,registry)
    proof=validate(data,registry,load(args.manifest),load(args.schema));proof['references_verified']=references;proof['canonical_sha256']=export(data,args.output)
    Path(args.output,'proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
if __name__=='__main__':main()
