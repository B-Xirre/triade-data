"""Snapshot normalization, explicit coverage and immutable item variants."""
import copy,hashlib,json,re
from pathlib import Path
from fractions import Fraction
from .numeric import checked,q,SCALE
from .schema import TABLES,KEYS

def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(value):return hashlib.sha256(encoded(value).encode('utf-8')).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def stable_id(table,row,registry):return row[registry['stable_id_columns'][table]]
def normalize(snapshot,reg):
    ids={t:{r['id']:r['fields'].get(reg['stable_id_columns'][t]) for r in d['records']} for t,d in snapshot.items()}
    output={'schema_version':'1.1.0','design_version':'0.47.0','tables':{}}
    for table,defs in reg['tables'].items():
        rows=[]
        for record in snapshot[table]['records']:
            row={}
            for name,definition in defs.items():
                if name in reg['canonical_excluded_columns'].get(table,[]):continue
                value=record['fields'].get(name);typ=definition['type']
                if typ.startswith('Ref:'):
                    target=typ[4:]
                    if isinstance(value,list) and len(value)==3 and value[0]=='R':value=value[2]
                    if value in (None,0,''):value=None
                    elif value in ids[target]:value=ids[target][value]
                    else:raise ValueError('unresolved_reference:'+table+'.'+name)
                elif isinstance(value,list):raise ValueError('formula_or_typed_cell_error')
                if isinstance(value,float):raise ValueError('canonical_float')
                if typ=='Int' and value is not None:checked(value)
                if table=='Design_parameters' and record['fields']['value_state']=='unset' and name in ('value_q','value_int','value_text'):value=None
                row[name]=value
            rows.append(row)
        key=reg['stable_id_columns'][table];rows.sort(key=lambda r:(r.get('sort_order') or 0,r[key]))
        if len({r[key] for r in rows})!=len(rows) or any(not r[key] for r in rows):raise ValueError('stable_id_collision')
        output['tables'][table]=rows
    return output

RULE_ADAPTERS={
 'M-C1':'content','M-C2':'combat','M-C4':'combat','M-C9':'combat','M-C10':'combat','M-C11':'combat',
 'M-C19':'combat','M-C20':'combat','M-C21':'combat','M-C22':'combat','M-C23':'combat','M-C24':'combat',
 'K-C21':'combat','K-C22':'combat','K-C23':'combat','K-C25':'combat','K-C26':'combat','K-C27':'combat','K-C28':'combat',
 'H-C11':'combat','H-C12':'combat','H-C13':'combat','H-C14':'combat','H-C15':'combat','H-H5':'combat','H-H6':'combat',
 'P-C2':'numeric','P-C3':'content','P-C5':'lab','P-C12':'numeric','P-C15':'content','P-C24':'lab','P-C25':'lab','P-C26':'combat','P-C27':'combat','P-C28':'lab','P-C29':'lab','P-C30':'lab',
 'P-C31':'lab','P-C32':'lab','P-C33':'lab','P-C34':'lab','P-C35':'lab','P-C36':'lab',
 'T-C1':'triade','T-C2':'triade','T-C14':'content','T-C19':'content','P-C20':'tarot','P-C21':'tarot','P-C22':'tarot','P-C23':'tarot'
}
PARAMETER_BINDINGS={
 'S-K11':('combat','rating_q','normalized_rating','0','48000'),
 'combat.group_step_calibration':('combat','step_rating_q','normalized_rating','0','24000'),
 'S-K13':('combat','cap_q','deflected_fraction','1','11999'),
 'S-H09':('combat','aim_ceiling_q','aim_weight','1','11999'),
 'S-M06':('combat','source_unit_q','damage_per_pip','0','12000000'),
 'S-M07':('combat','reinforcement_q','threshold_multiplier','0','48000'),
 'S-H12':('combat','divine_coefficient_q','damage_per_load','0','120000'),
 'S-P01':('numeric','scale','correctness_constant','12000','12000')
}
def coverage(data):
    rows=[]
    for r in data['tables']['Ref_rules']:
        adapter=RULE_ADAPTERS.get(r['rule_id']);rows.append({'coverage_id':'rule:'+r['rule_id'],'kind':'rule','source_id':r['rule_id'],'classification':'contract_probe' if adapter else 'capability_gap','adapter':adapter,'blocking_reason':None if adapter else 'Source requirement needs an unimplemented domain adapter or external evidence','source_reference':r['source_reference']})
    for r in data['tables']['Design_parameters']:
        pid=r['parameter_id'];binding=PARAMETER_BINDINGS.get(pid)
        classification='constant' if r['value_state']=='locked' else 'coefficient' if binding else 'compound_family' if r['value_kind']=='text' else 'unbound_coefficient'
        if pid.startswith('S-V'):classification='external_usability'
        if pid in {'S-W07','S-W09','S-W10','S-P02'}:classification='external_performance'
        rows.append({'coverage_id':'parameter:'+pid,'kind':'parameter','source_id':pid,'classification':classification,'adapter':binding[0] if binding else None,'symbol':binding[1] if binding else None,'value_state':r['value_state'],'blocking_reason':None if binding and r['value_state']=='locked' else ('Production coefficient unset; declared experiment inputs can run this mathematical probe' if binding else 'Explicit numeric binding or domain capability required'),'source_reference':r['source_reference']})
    return {'registered':len(rows),'rules':len(data['tables']['Ref_rules']),'parameters':len(data['tables']['Design_parameters']),'executable_contract_bindings':sum(bool(r['adapter']) for r in rows),'rows':rows}

SUBJECTS={'Equipment':'equipment_revision_id','Techniques':'revision_id','Tarot_cards':'revision_id','Fixture_builds':'fixture_build_id'}
EDITABLE={'Equipment','Equipment_text','Chassis_profiles','Construction_profiles','Damage_profile_entries','Defence_profile_entries','Protection_profiles','Protection_contributions','Active_defence_profiles','Ward_profiles','Ward_transformations','Integrity_profiles','Integrity_states','Integrity_thresholds','Triade_effects','Stat_modifiers','Techniques','Technique_levels','Technique_sources','Technique_payloads','Payloads','Tarot_cards','Tarot_contribution_contracts','Tarot_contribution_fields','Fixture_builds'}
EDITABLE.add('Design_parameters')
READONLY={'revision_number','revision_id','equipment_revision_id','schema_version','content_version','lifecycle_status','design_status','source_document_ref','provenance_ref','sort_order','base_pip_total','effective_pip_total','m_c11_state','floor_sum','floor_valid','faculty_id','faculty_revision_id','is_secret','is_relic','is_unique','is_transgressive','demand_tier','approved_by','approved_at','content_hash'}
READONLY.update({'equipment_id','technique_id','tarot_card_id','protection_profile_id','owner_revision_id','source_revision_id','equipment_revision'})
def catalogue(data,reg):
    rows=[];source_hash=game_hash(data)
    for table in SUBJECTS:
        for row in data['tables'][table]:
            key=reg['stable_id_columns'][table];sid=table+':'+str(row[key])
            kind=str(row.get('category') or table)
            rows.append({'subject_id':sid,'kind':kind,'source_table':table,'source_revision_id':row[key],'source_snapshot_hash':source_hash,'display_name':row.get('display_name') or row.get('equipment_id') or row.get('technique_id') or row[key],'is_template':False})
    for kind,table in [('armour','Equipment'),('shield','Equipment'),('weapon','Equipment'),('Technique','Techniques'),('Tarot','Tarot_cards')]:
        rows.append({'subject_id':'template:'+kind,'kind':kind,'source_table':table,'source_revision_id':None,'source_snapshot_hash':source_hash,'display_name':'Experimental '+kind+' template','is_template':True})
    return rows
def game_hash(data):return digest({'schema_version':data['schema_version'],'design_version':data['design_version'],'tables':{t:r for t,r in data['tables'].items() if not t.startswith('Lab_')}})
VOLATILE={'Lab_subject_catalog','Lab_experiments','Lab_experiment_revisions','Lab_changes','Lab_dependencies','Lab_adoption_requests','Lab_result_summaries','Lab_coverage'}
def frozen_content(data):
    result=copy.deepcopy(data)
    for table in VOLATILE:result['tables'][table]=[]
    return result
def snapshot_hash(data):return digest(frozen_content(data))
def dependencies(data,subject,reg):
    if subject['is_template']:return []
    # A complete pinned game snapshot is the dependency closure; enumerate all exact content identities.
    return [{'source_table':t,'source_revision_id':r[reg['stable_id_columns'][t]]} for t,rows in data['tables'].items() if not t.startswith('Lab_') for r in rows]
def editable(data,subject,reg):
    if subject['is_template']:return []
    owner=subject['source_revision_id'];root=subject['source_table'];output_fields=[]
    profile_ids=set()
    selected=next(r for r in data['tables'][root] if stable_id(root,r,reg)==owner)
    for name,value in selected.items():
        if name.endswith(('_profile_id','_profile')) and value:profile_ids.add(value)
    for table in ('Chassis_profiles','Construction_profiles'):
        for row in data['tables'][table]:
            if row[reg['stable_id_columns'][table]] in profile_ids:
                for name,value in row.items():
                    if name.endswith(('_profile_id','_profile')) and value:profile_ids.add(value)
    parameter_ids=set()
    for table,rows in data['tables'].items():
        if table.startswith('Lab_'):continue
        for row in rows:
            related=(table==root and row[reg['stable_id_columns'][table]]==owner) or row.get('owner_revision_id')==owner or row.get('defence_profile_id') in profile_ids
            if related:
                for name,definition in reg['tables'][table].items():
                    if definition['type']=='Ref:Design_parameters' and row.get(name):parameter_ids.add(row[name])
    for table in EDITABLE:
        for row in data['tables'][table]:
            key=reg['stable_id_columns'][table]
            attached=(table==root and row[key]==owner) or row.get('equipment_revision')==owner or row.get('technique')==owner or row[key] in profile_ids or any(row.get(k) in profile_ids for k in ('profile_id','defence_profile_id','integrity_profile_id','integrity_profile')) or row.get('owner_revision_id')==owner or (table=='Design_parameters' and row[key] in parameter_ids and row['value_state']!='locked')
            if not attached:continue
            for column,definition in reg['tables'][table].items():
                if column in READONLY or column==key or definition['isFormula']:continue
                if table=='Design_parameters' and column not in {'value_int','value_q','value_text','value_state','blocking_reason','notes'}:continue
                typ=definition['type']
                output_fields.append({'table':table,'row_key':row[key],'column':column,'type':typ,'value':row.get(column),'choices':sorted({stable_id(typ[4:],r,reg) for r in data['tables'][typ[4:]]}) if typ.startswith('Ref:') else None})
    return output_fields
def apply_variant(data,subject,changes,reg):
    result=copy.deepcopy(data);allowed={(f['table'],f['row_key'],f['column']):f for f in editable(data,subject,reg)};seen=set()
    for change in changes:
        key=(change.table,change.row_key,change.column)
        if key in seen:raise ValueError('duplicate_change')
        seen.add(key)
        if key not in allowed:raise ValueError('derived_or_unrelated_field')
        field=allowed[key];typ=field['type'];value=change.value
        if typ=='Int':
            if value is not None and type(value) is not str:raise ValueError('integer_wire_string_required')
            value=None if value is None else checked(int(value))
        elif typ=='Bool':
            if type(value) is not bool:raise ValueError('boolean_required')
        elif typ.startswith('Ref:') and value is not None and value not in field['choices']:raise ValueError('unresolved_reference')
        row=next(r for r in result['tables'][change.table] if stable_id(change.table,r,reg)==change.row_key);row[change.column]=value
    validate_variant(result,reg)
    from .validation import validate_rows
    validate_rows(result,reg);return result
def validate_variant(data,reg):
    for table,rows in data['tables'].items():
        for row in rows:
            for name,value in row.items():
                if isinstance(value,float):raise ValueError('canonical_float')
                if reg['tables'][table].get(name,{}).get('type')=='Int' and value is not None:checked(value)
    for row in data['tables']['Damage_profile_entries']:
        if row['base_pips'] is None or row['base_pips']<0:raise ValueError('missing_or_negative_pips')
    totals={}
    for row in data['tables']['Damage_profile_entries']:totals[row['profile_id']]=totals.get(row['profile_id'],0)+row['base_pips']
    for row in data['tables']['Equipment']:
        category=row.get('category');chassis=next((c for c in data['tables']['Chassis_profiles'] if c['chassis_profile_id']==row.get('chassis_profile')),None)
        profile=chassis.get('base_martial_profile_id') if chassis else None
        if category=='weapon' and profile in totals:
            hand=chassis.get('handedness');expected=3 if hand=='one_handed' else 4 if hand=='two_handed' else None
            if expected is not None and totals[profile]!=expected:raise ValueError('weapon_pip_budget')
        if category=='shield' and profile in totals:
            steps=sum(p['allocation_steps'] for p in data['tables']['Protection_profiles'] if p['owner_revision_id']==row['equipment_revision_id'])
            if totals[profile]+steps!=2:raise ValueError('shield_pooled_budget')
            if chassis and chassis['chassis_family']=='buckler' and steps!=0:raise ValueError('buckler_passive_allocation')
    for row in data['tables']['Protection_profiles']:
        if row['allocation_steps'] is None or row['allocation_steps']<0 or row['allocation_group']=='structural':raise ValueError('illegal_protection_allocation')
    for row in data['tables']['Fixture_builds']:
        values=[row[k] for k in ('floor_m_q','floor_f_q','floor_i_q')]
        if min(values)<0 or max(values)>3000 or sum(values)>5400:raise ValueError('floor_budget')
    for row in data['tables']['Tarot_contribution_contracts']:
        # Actual optional fields are validated by the registered schema and adapter, not invented here.
        if row.get('tier') is not None and row['tier']<0:raise ValueError('negative_tier')
