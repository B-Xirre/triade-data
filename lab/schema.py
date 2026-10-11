"""Normalized lab grain. No executable authoring cells or JSON arrays."""
import copy,json
from pathlib import Path
def columns(**definitions):
    return {name:{'type':typ,'isFormula':False,'formula':''} for name,typ in definitions.items()}
TABLES={
 'Lab_adapters':columns(adapter_id='Text',version='Text',capability='Text',source_reference='Text',description='Text'),
 'Lab_suites':columns(suite_id='Text',display_name='Text',version='Text',case_budget='Int',source_reference='Text'),
 'Lab_cases':columns(case_id='Text',suite='Ref:Lab_suites',adapter='Ref:Lab_adapters',scenario='Text',display_name='Text',sort_order='Int'),
 'Lab_case_inputs':columns(input_id='Text',case='Ref:Lab_cases',name='Text',value_kind='Text',value_int='Int',value_q='Int',value_text='Text',unit='Text',sort_order='Int'),
 'Lab_assertions':columns(assertion_id='Text',case='Ref:Lab_cases',rule='Ref:Ref_rules',metric='Text',operator='Text',expected_int='Int',expected_q='Int',expected_text='Text',sort_order='Int'),
 'Lab_coverage':columns(coverage_id='Text',rule='Ref:Ref_rules',parameter='Ref:Design_parameters',classification='Text',adapter='Ref:Lab_adapters',blocking_reason='Text',source_reference='Text'),
 'Lab_parameter_bindings':columns(binding_id='Text',parameter='Ref:Design_parameters',adapter='Ref:Lab_adapters',symbol='Text',target_table='Text',target_revision_id='Text',target_field='Text',unit='Text',value_kind='Text',min_value='Text',max_value='Text',binding_state='Text',blocking_reason='Text'),
 'Lab_sweeps':columns(sweep_id='Text',suite='Ref:Lab_suites',method='Text',case_budget='Int',root_seed='Int'),
 'Lab_sweep_dimensions':columns(dimension_id='Text',sweep='Ref:Lab_sweeps',binding='Ref:Lab_parameter_bindings',input_name='Text',minimum='Text',maximum='Text',step='Text',sort_order='Int'),
 'Lab_metrics':columns(metric_id='Text',version='Text',unit='Text',direction='Text',description='Text'),
 'Lab_chart_profiles':columns(profile_id='Text',version='Text',chart_kind='Text',display_name='Text'),
 'Lab_chart_axes':columns(axis_id='Text',profile='Ref:Lab_chart_profiles',metric='Ref:Lab_metrics',minimum_q='Int',maximum_q='Int',sort_order='Int'),
 'Lab_subject_catalog':columns(subject_id='Text',kind='Text',source_table='Text',source_revision_id='Text',source_snapshot_hash='Text',display_name='Text',is_template='Bool'),
 'Lab_experiments':columns(experiment_id='Text',subject='Ref:Lab_subject_catalog',display_name='Text'),
 'Lab_experiment_revisions':columns(revision_id='Text',experiment='Ref:Lab_experiments',parent='Ref:Lab_experiment_revisions',source_snapshot_hash='Text',sequence='Int',content_hash='Text',created_at='Text',runner_version='Text'),
 'Lab_changes':columns(change_id='Text',revision='Ref:Lab_experiment_revisions',target_table='Text',row_key='Text',column_id='Text',operation='Text',value_kind='Text',value_text='Text',value_int='Int',value_q='Int',value_bool='Bool',sort_order='Int'),
 'Lab_dependencies':columns(dependency_id='Text',revision='Ref:Lab_experiment_revisions',source_table='Text',source_revision_id='Text',snapshot_hash='Text'),
 'Lab_adoption_requests':columns(adoption_id='Text',revision='Ref:Lab_experiment_revisions',run_id='Text',state='Text',draft_hash='Text',proof_hash='Text',created_at='Text'),
 'Lab_result_summaries':columns(summary_id='Text',run_id='Text',revision='Ref:Lab_experiment_revisions',state='Text',pass_count='Int',fail_count='Int',blocked_count='Int',error_count='Int',not_applicable_count='Int',result_hash='Text',trace_hash='Text'),
}
KEYS={t:next(iter(c)) for t,c in TABLES.items()}
GENERATED={'Lab_coverage','Lab_subject_catalog','Lab_result_summaries'}
IMMUTABLE={'Lab_experiment_revisions','Lab_changes','Lab_dependencies','Lab_adapters'}
def registry(root):
    base=json.loads((Path(root)/'schema/authoring-registry-1.0.0.json').read_text(encoding='utf-8'))
    result=copy.deepcopy(base);result['schema_version']='1.1.0';result['design_version']='0.47.0'
    result['tables'].update(TABLES);result['stable_id_columns'].update(KEYS)
    return result
def json_schema(reg):
    tables={}
    for table,defs in reg['tables'].items():
        fields={}
        for name,d in defs.items():
            if name in reg['canonical_excluded_columns'].get(table,[]):continue
            typ=d['type'];types=['integer','null'] if typ=='Int' else ['boolean','null'] if typ=='Bool' else ['string','null']
            fields[name]={'type':types}
            if typ=='Int':fields[name].update(minimum=-(1<<63),maximum=(1<<63)-1)
        tables[table]={'type':'array','items':{'type':'object','properties':fields,'required':list(fields),'additionalProperties':False}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'triade-authoring-1.1.0','type':'object','properties':{'schema_version':{'const':'1.1.0'},'design_version':{'const':'0.47.0'},'tables':{'type':'object','properties':tables,'required':list(tables),'additionalProperties':False}},'required':['schema_version','design_version','tables'],'additionalProperties':False}
