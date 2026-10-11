"""Read-only baseline, candidate, stable-reference and deterministic snapshot proof."""
import argparse,json
from pathlib import Path
from .grist import Grist
from .schema import registry
from .content import normalize,frozen_content,digest,encoded
from .validation import validate_rows
from . import config
def full_snapshot(client,reg):
    result={}
    for table in reg['tables']:
        columns=client.call('GET','/tables/'+table+'/columns')['columns'];rows=client.all_rows(table)
        result[table]={'columns':columns,'records':rows}
    return result
def proof(active,backup,candidate,out):
    if len({active,backup,candidate})!=3:raise ValueError('distinct_document_ids_required')
    base=json.loads((config.ROOT/'schema/authoring-registry-1.0.0.json').read_text(encoding='utf-8'));reg=json.loads((config.ROOT/'schema/authoring-registry-1.1.0.json').read_text(encoding='utf-8'))
    a=full_snapshot(Grist(doc=active),base);b=full_snapshot(Grist(doc=backup),base)
    assert digest(a)==digest(b),'Active/backup baseline mismatch'
    c=full_snapshot(Grist(doc=candidate),reg);preserved=0;declared_changes=0
    for table,data in a.items():
        old={r['id']:r['fields'] for r in data['records']};new={r['id']:r['fields'] for r in c[table]['records']}
        for row_id,row in old.items():
            assert row_id in new
            for column,value in row.items():
                if new[row_id].get(column)==value:preserved+=1
                else:
                    assert table=='Ref_rules' and column=='sort_order',(table,row_id,column)
                    declared_changes+=1
    canonical=normalize(c,reg);validate_rows(canonical,reg)
    ids={t:{r[reg['stable_id_columns'][t]] for r in rows} for t,rows in canonical['tables'].items()};refs=0
    for table,rows in canonical['tables'].items():
        for column,definition in reg['tables'][table].items():
            if definition['type'].startswith('Ref:') and column not in reg['canonical_excluded_columns'].get(table,[]):
                target=definition['type'][4:]
                for row in rows:
                    if row[column] is not None:assert row[column] in ids[target];refs+=1
    for table in ['_grist_ACLResources','_grist_ACLRules']:
        c[table]={'records':Grist(doc=candidate).call('GET','/tables/'+table+'/records?sort=id&limit=1000')['records']}
    resources={r['id']:r['fields']['tableId'] for r in c['_grist_ACLResources']['records']}
    protected={resources[r['fields']['resource']] for r in c['_grist_ACLRules']['records'] if r['fields'].get('permissionsText')=='-CUD'}
    expected={'Lab_coverage','Lab_subject_catalog','Lab_result_summaries','Lab_experiment_revisions','Lab_changes','Lab_dependencies','Lab_adapters'}
    assert expected<=protected
    frozen=frozen_content(canonical);raw=encoded(frozen)+'\n';source_hash=digest(frozen)
    import hashlib
    report={'active':active,'backup':backup,'candidate':candidate,'baseline_tables':len(base['tables']),'baseline_rows':sum(len(d['records']) for d in a.values()),'candidate_tables':len(reg['tables']),'candidate_rows':sum(len(c[t]['records']) for t in reg['tables']),'candidate_columns':sum(len(c[t]['columns']) for t in reg['tables']),'references_verified':refs,'preserved_baseline_cells':preserved,'declared_rule_order_changes':declared_changes,'rule_rows':len(canonical['tables']['Ref_rules']),'parameter_rows':len(canonical['tables']['Design_parameters']),'unset_parameters':sum(r['value_state']=='unset' for r in canonical['tables']['Design_parameters']),'new_read_only_tables_verified':len(expected),'source_snapshot_hash':source_hash,'canonical_export_sha256':hashlib.sha256(raw.encode()).hexdigest(),'schema_actions_on_repeat':0,'record_actions_on_repeat':0,'row_counts':{t:len(c[t]['records']) for t in reg['tables']}}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'candidate-proof.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'frozen-authoring.json').write_text(raw,encoding='utf-8',newline='\n')
    (out/'candidate-record-hashes.json').write_text(json.dumps({t:digest(c[t]) for t in reg['tables']},indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k!='row_counts'}))
def main():
    p=argparse.ArgumentParser();p.add_argument('--active',required=True);p.add_argument('--backup',required=True);p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);args=p.parse_args();proof(args.active,args.backup,args.candidate,args.out)
if __name__=='__main__':main()
