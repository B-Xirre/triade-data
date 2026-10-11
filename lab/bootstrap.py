"""Generate reproducible lab authoring schema and normalized seed from frozen content."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from .schema import registry,json_schema,KEYS
from .content import load,coverage,catalogue,game_hash,PARAMETER_BINDINGS
from .adapters import ADAPTERS,DEFAULT_INPUTS,LIMITS,combat_contracts
def build(rules=None):
    reg=registry(ROOT);data=load(ROOT/'content/canonical/authoring.json')
    if rules:data['tables']['Ref_rules']=rules
    data['schema_version']='1.1.0';data['design_version']='0.47.0'
    data['tables']['Combat_equation_parameters']=[{'combat_equation_parameter_id':'equation.group_transmission.step_calibration','equation':'equation.group_transmission@1','parameter':'combat.group_step_calibration','symbol':'group_step_calibration','required':True,'sort_order':1}]
    seed={t:[] for t in KEYS}
    seed['Lab_adapters']=[{'adapter_id':k,**v,'source_reference':'P·12 / reviewed repository adapter'} for k,v in sorted(ADAPTERS.items())]
    for name in ['combat-contracts','property-10000','item-comparison','tarot-contracts','triade-probes','all']:seed['Lab_suites'].append({'suite_id':name,'display_name':name.replace('-',' ').title(),'version':'1.0.0','case_budget':10000,'source_reference':'P·12'})
    for i,c in enumerate(combat_contracts(DEFAULT_INPUTS)):
        seed['Lab_cases'].append({'case_id':c['case_id'],'suite':'combat-contracts','adapter':'combat','scenario':c['case_id'],'display_name':c['case_id'].replace('.',' / '),'sort_order':i})
        for j,(key,value) in enumerate(DEFAULT_INPUTS.items()):seed['Lab_case_inputs'].append({'input_id':c['case_id']+'.'+key,'case':c['case_id'],'name':key,'value_kind':'fixed_point' if key.endswith('_q') else 'integer','value_q':value if key.endswith('_q') else None,'value_int':value if not key.endswith('_q') else None,'value_text':'','unit':'declared_fixture_only','sort_order':j})
        for j,rid in enumerate(c['rule_ids']):seed['Lab_assertions'].append({'assertion_id':c['case_id']+'.'+rid,'case':c['case_id'],'rule':rid,'metric':'status','operator':'eq','expected_int':None,'expected_q':None,'expected_text':'pass','sort_order':j})
    for row in coverage(data)['rows']:
        seed['Lab_coverage'].append({'coverage_id':row['coverage_id'],'rule':row['source_id'] if row['kind']=='rule' else None,'parameter':row['source_id'] if row['kind']=='parameter' else None,'classification':row['classification'],'adapter':row['adapter'],'blocking_reason':row['blocking_reason'] or '', 'source_reference':row['source_reference']})
    for row in data['tables']['Design_parameters']:
        b=PARAMETER_BINDINGS.get(row['parameter_id'])
        if b:seed['Lab_parameter_bindings'].append({'binding_id':'binding.'+row['parameter_id'],'parameter':row['parameter_id'],'adapter':b[0],'symbol':b[1],'target_table':'Combat_equations','target_revision_id':'equation.group_transmission@1' if b[1] in ('rating_q','step_rating_q') else '', 'target_field':b[1],'unit':b[2],'value_kind':'integer' if b[1]=='scale' else 'fixed_point','min_value':b[3],'max_value':b[4],'binding_state':'locked_constant' if row['value_state']=='locked' else 'fixture_probe_only','blocking_reason':'' if row['value_state']=='locked' else 'Production binding remains unmeasured'})
    seed['Lab_subject_catalog']=catalogue(data,reg)
    metrics=[('redirected_fraction_q','fraction','higher','Redirected part of incoming quantity'),('absorbed_fraction_q','fraction','higher','Absorbed shield quantity / input'),('transmitted_fraction_q','fraction','lower','Body input / incoming quantity'),('delivered_physical_q','damage','higher','Delivered Physical damage under common fixture input'),('delivered_volatile_q','damage','higher','Delivered Volatile damage'),('delivered_corruptive_q','damage','higher','Delivered Corruptive damage'),('delivered_occult_q','damage','higher','Delivered Occult damage'),('structural_stress_q','integrity_stress','higher','Structural route; never typed HP mitigation')]
    seed['Lab_metrics']=[{'metric_id':k,'version':'1.0.0','unit':u,'direction':d,'description':desc} for k,u,d,desc in metrics]
    seed['Lab_chart_profiles']=[{'profile_id':'defence-partition','version':'1.0.0','chart_kind':'radar','display_name':'Defence partition'},{'profile_id':'typed-delivery','version':'1.0.0','chart_kind':'radar','display_name':'Typed delivery under common fixture input'},{'profile_id':'triade-probes','version':'1.0.0','chart_kind':'ternary','display_name':'Mathematical position probes'}]
    for i,key in enumerate(['redirected_fraction_q','absorbed_fraction_q','transmitted_fraction_q']):seed['Lab_chart_axes'].append({'axis_id':'defence.'+key,'profile':'defence-partition','metric':key,'minimum_q':0,'maximum_q':12000,'sort_order':i})
    for i,key in enumerate(['delivered_physical_q','delivered_volatile_q','delivered_corruptive_q','delivered_occult_q']):seed['Lab_chart_axes'].append({'axis_id':'delivery.'+key,'profile':'typed-delivery','metric':key,'minimum_q':0,'maximum_q':6000000,'sort_order':i})
    seed['Lab_sweeps']=[{'sweep_id':'defence.response','suite':'item-comparison','method':'bounded_cartesian','case_budget':10000,'root_seed':0}]
    seed['Lab_sweep_dimensions']=[{'dimension_id':'defence.response.rating','sweep':'defence.response','binding':'binding.S-K11','input_name':'rating_q','minimum':'0','maximum':'24000','step':'6000','sort_order':0}]
    for t in KEYS:data['tables'][t]=seed[t]
    return reg,data,seed
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rules-csv');args=parser.parse_args();rules=None
    if args.rules_csv:
        import csv
        rules=list(csv.DictReader(open(args.rules_csv,encoding='utf-8')))
        for r in rules:r['sort_order']=int(r['sort_order'])
    reg,data,seed=build(rules)
    for path,value in [(ROOT/'schema/authoring-registry-1.1.0.json',reg),(ROOT/'schema/authoring-1.1.schema.json',json_schema(reg)),(ROOT/'content/lab-seed.json',seed),(ROOT/'content/canonical/authoring-1.1.0.json',data)]:path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'tables':len(reg['tables']),'lab_tables':len(KEYS),'seed_rows':sum(map(len,seed.values()))}))
if __name__=='__main__':main()
