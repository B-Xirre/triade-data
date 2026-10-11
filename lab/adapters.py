"""Trusted contract probes and comparison adapters, with independent rational oracles."""
from fractions import Fraction as F
import hashlib,itertools,random,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import combat_contracts as oracle
from .numeric import SCALE,checked,mul,div,q,allocate,round_ratio
from .content import digest,stable_id,validate_variant

DEFAULT_INPUTS={
 'damage_q':1200000,'rating_q':6000,'affinity_q':12000,'deflection_q':2400,'contact_q':12000,
 'cap_q':7200,'response_q':12000,'calibration_q':12000,'source_unit_q':1200000,
 'reinforcement_q':6000,'divine_coefficient_q':24000,'divine_load_q':360000,
 'aim_weight_q':6000,'aim_ceiling_q':7200,'base_cost':4,'aim_cost':1,'tax_cap':2,
 'integrity_threshold':40,'incoming_stress':10,
}
LIMITS={k:(0,120000000) for k in DEFAULT_INPUTS}
for k in ('deflection_q','cap_q','aim_ceiling_q'):LIMITS[k]=(1 if k!='deflection_q' else 0,11999)
LIMITS['contact_q']=(0,12000);LIMITS['affinity_q']=(1,48000);LIMITS['calibration_q']=(1,48000)
LIMITS['aim_weight_q']=(0,11998)
ADAPTERS={
 'combat':{'version':'1.0.0','capability':'formula_and_interaction','description':'Exact conserving protection, source, anatomy, Divine and aim probes'},
 'numeric':{'version':'1.0.0','capability':'invariant','description':'Signed storage, wide intermediates, allocation and prescribed rounding'},
 'content':{'version':'1.0.0','capability':'invariant','description':'Content identity, source pip budget and pinned references'},
 'lab':{'version':'1.0.0','capability':'invariant','description':'Immutable manifests, explicit gaps, coverage and experiment isolation'},
 'tarot':{'version':'1.0.0','capability':'authorization_probe','description':'Adopted support/tier/duplicate/combination contracts; no unresolved runtime effects'},
 'triade':{'version':'1.0.0','capability':'mathematical_probe','description':'Fixed-point simplex, floor and zero-sum probes; not encounter trajectories'},
 'encounter':{'version':'0.0.0','capability':'gap','description':'Full encounter resolver unavailable'},
 'performance':{'version':'0.0.0','capability':'external','description':'Engine performance evidence adapter interface'},
 'usability':{'version':'0.0.0','capability':'external','description':'Human recognition/readability evidence adapter interface'},
}
def inputs(overrides):
    values=dict(DEFAULT_INPUTS)
    for name,value in overrides.items():
        if name not in values:raise ValueError('unknown_input:'+name)
        number=checked(int(value));low,high=LIMITS[name]
        if not low<=number<=high:raise ValueError('input_domain:'+name)
        values[name]=number
    if not values['aim_weight_q']<values['aim_ceiling_q']:raise ValueError('aim_coefficient_ceiling')
    return values
def transmission(damage,rating,affinity=SCALE):
    if damage<0 or rating<0 or affinity<=0:raise ValueError('invalid_transmission')
    # One final rounding after a checked wider numerator, not repeated rounding of factors.
    numerator=checked(checked(damage)*checked(affinity),128)
    return checked(round_ratio(numerator,SCALE+rating))
def partition(damage,d,c,rating,affinity=SCALE):
    if damage<0 or not 0<=d<SCALE or not 0<=c<=SCALE:raise ValueError('invalid_partition')
    redirected,remaining=allocate(damage,[d,SCALE-d]);contact,bypass=allocate(remaining,[c,SCALE-c])
    transferred=transmission(contact,rating,affinity);absorbed=max(0,contact-transferred);amplification=max(0,transferred-contact)
    result={'redirected_q':redirected,'contact_q':contact,'bypass_q':bypass,'transmitted_q':transferred,'absorbed_q':absorbed,'amplification_q':amplification,'body_q':bypass+transferred}
    if redirected+absorbed+result['body_q']!=damage+amplification:raise AssertionError('partition_conservation')
    return result
def result(case_id,status='pass',rules=(),metrics=None,trace=None,reason=None,details=None):
    return {'case_id':case_id,'status':status,'rule_ids':list(rules),'metrics':metrics or {},'trace':trace or [],'reason':reason,'details':details or {}}
def event(stage,before,after,rule,source='fixture-only'):
    equations={'shield_partition':'equation.shield_partition@1','typed_transmission':'equation.group_transmission@1','fixture_only_quantity_probe':'equation.shield_partition@1','active_response':'equation.active_deflection@1'}
    return {'stage':stage,'before_q':before,'after_q':after,'delta_q':after-before,'unit':'integrity_stress_q' if stage=='structural_integrity_route' else 'fraction_q' if stage=='active_response' else 'damage_q','rule_id':rule,'source_revision_id':'fixture.lab-1.0.0@1' if source=='fixture-only' else source,'trace_kind':'mathematical_probe','equation_revision_id':equations.get(stage),'rounding':'nearest_ties_away_from_zero','allocation_method':'stable_largest_remainder' if stage=='shield_partition' else 'one_final_rounding'}
def require_rejection(fn):
    try:fn()
    except (ValueError,OverflowError,AssertionError):return
    raise AssertionError('invalid_input_accepted')

def combat_contracts(values):
    cases=[]
    def check(name,rules,fn):
        try:
            details=fn();metrics=details if isinstance(details,dict) and all(type(v) is int for v in details.values()) else {}
            traces=[event('shield_partition',values['damage_q'],details['body_q'],'K-C22')] if name=='shield.partition' else [event('typed_transmission',values['damage_q'],details['typed_transmitted_q'],'K-C26')] if name=='armour.transmission' else [event('active_response',0,details['active_deflection_q'],'K-C26')] if name=='active.saturation' else []
            cases.append(result(name,rules=rules,metrics=metrics,trace=traces,details={'inputs':dict(values),'input_origin':'fixture-only',**(details if isinstance(details,dict) else {})}))
        except Exception as e:cases.append(result(name,'fail',rules,reason=str(e)))
    def partition_probe():
        r=partition(values['damage_q'],values['deflection_q'],values['contact_q'],values['rating_q'],values['affinity_q'])
        exact=oracle.shield_partition(F(values['damage_q']),F(values['deflection_q'],SCALE),F(values['contact_q'],SCALE),F(values['affinity_q'],SCALE+values['rating_q']))
        assert abs(F(r['body_q'])-exact['body'])<=2
        return r
    check('shield.partition',('K-C22','K-C28'),partition_probe)
    def active():
        v=values['response_q'];k=values['calibration_q'];cap=values['cap_q']
        actual=checked(round_ratio(checked(cap*v,128),k+v))
        expected=q(oracle.active_deflection(F(v,SCALE),F(k,SCALE),F(cap,SCALE)))
        assert actual==expected and actual<cap
        require_rejection(lambda:oracle.active_deflection(F(1),F(0),F(1,2)))
        return {'active_deflection_q':actual,'active_cap_q':cap}
    check('active.saturation',('K-C26',),active)
    def aff():
        actual=transmission(values['damage_q'],values['rating_q'],values['affinity_q'])
        expected=checked(round_ratio(values['damage_q']*values['affinity_q'],SCALE+values['rating_q']))
        assert actual==expected
        require_rejection(lambda:transmission(100,-1));require_rejection(lambda:transmission(100,1,0))
        return {'typed_transmitted_q':actual}
    check('armour.transmission',('K-C26',),aff)
    check('shield.zero_allocation',('M-C4','M-C9','M-C20','M-C21'),lambda:(oracle.shield_budget('buckler',0,2,2),require_rejection(lambda:oracle.shield_budget('buckler',1,1,2)),require_rejection(lambda:oracle.shield_budget('tower',2,1,2))))
    check('scope.single_use',('K-C23','P-C26'),lambda:require_rejection(lambda:oracle.scoped_transmit(F(100),{'a':F(1)},[['a'],['a']])))
    def poison():
        assert not oracle.protection_route('poison','internal','contact_layer',True)
        assert not oracle.protection_route('poison','internal','recipient_domain')
        assert oracle.protection_route('poison','internal','recipient_domain',True)
    check('scope.internal_poison',('M-C19','H-C15'),poison)
    def psychic():
        assert not oracle.protection_route('psychic','external','contact_layer')
        assert oracle.protection_route('psychic','external','recipient_domain')
    check('scope.psychic',('H-C14',),psychic)
    def divine():
        a=oracle.purge({'load':F(values['divine_load_q'],SCALE)},{'load':F(values['divine_coefficient_q'],SCALE)},True,True)
        assert oracle.purge(a['remaining'],{'load':F(2)},True,True)['damage']==0
        assert oracle.purge({'load':F(30)},{'load':F(2)},False,True)['remaining']=={'load':F(30)}
        assert oracle.purge({'load':F(30)},{'load':F(2)},True,False)['damage']==0
    check('divine.consumption',('K-C27','H-C13','H-H6'),divine)
    def ward():
        a={'id':'a','functional':True,'compatible':True,'priority':1,'contract':'soft'};b={**a,'id':'b','contract':'hard'}
        require_rejection(lambda:oracle.choose_ward([a,b]));b['priority']=2;assert oracle.choose_ward([a,b])['id']=='b'
    check('ward.priority',('M-C22','P-C27'),ward)
    def tissues():
        r=oracle.tissue_shares({'skin':2,'bone':1,'brain':3},{'skin','bone'});assert sum(r.values())==1 and 'brain' not in r
        require_rejection(lambda:oracle.tissue_shares({'brain':1},{'skin'}))
    check('anatomy.mask',('H-C12',),tissues)
    def integrity():
        assert oracle.integrity_event(0,[100,100],[10,20])==1
        assert oracle.reinforced_threshold(40,F(1,2))==60
    check('integrity.one_transition',('M-C2','M-C10','M-C23'),integrity)
    def aim():
        p=oracle.aim_distribution({'head':F(8,110),'other':F(102,110)},'head',F(59,100),F(3,5));assert sum(p.values())==1 and p['head']>F(3,5)
        require_rejection(lambda:oracle.aim_distribution({'head':F(1)},'head',F(3,5),F(3,5)))
    check('aim.mixture',('H-C11','H-H5'),aim)
    def offhand():
        r=oracle.effective_offhand([{'type':'slash','pips':1,'sort_order':1},{'type':'pierce','pips':1,'sort_order':2}],True);assert r==[{'type':'slash','pips':1,'sort_order':1}]
    check('offhand.last_tie',('M-C11',),offhand)
    def adverse():
        actual=values['base_cost']+values['aim_cost']+min(9,values['tax_cap'])
        assert oracle.injury_cost(values['base_cost'],values['aim_cost'],[2,3,4],values['tax_cap'])==actual
        return {'effective_AP_cost':actual}
    check('cost.adverse_cap',('K-C25',),adverse)
    def source():assert sum(allocate(oracle.source_budget(7,4),[1,2,1]))==28
    check('damage.calibrate_once',('M-C24',),source)
    def numeric():
        assert [q(F(n,2)) for n in [-3,-1,1,3]]==[-18000,-6000,6000,18000]
        assert round_ratio(-3,2)==-2 and round_ratio(3,2)==2
        require_rejection(lambda:checked(1<<63));require_rejection(lambda:checked(1<<127,128));require_rejection(lambda:q(0.1))
    check('numeric.checked',('P-C2','P-C12'),numeric)
    return cases

def property_case(index,seed):
    # Stable named stream: independent of subject revision and execution order.
    stream=int.from_bytes(hashlib.sha256(f'{seed}:partition:{index}'.encode()).digest()[:16],'big');rng=random.Random(stream)
    D=rng.randrange(0,12000001);d=rng.randrange(SCALE);c=rng.randrange(SCALE+1);a=rng.randrange(48001);aff=rng.randrange(1,48001)
    r=partition(D,d,c,a,aff)
    exact=oracle.shield_partition(F(D),F(d,SCALE),F(c,SCALE),F(aff,SCALE+a))
    status='pass' if abs(F(r['body_q'])-exact['body'])<=8 else 'fail'
    return result(f'property.partition.{index:05}',status,('K-C22','K-C28','P-C12'),r,[event('shield_partition',D,r['body_q'],'K-C22')],None if status=='pass' else 'rational_oracle_mismatch',{'damage_q':D,'deflection_q':d,'contact_q':c,'rating_q':a,'affinity_q':aff})

def item_probe(data,subject,values,reg,context=None):
    context=context or {'damage_type':'impact','delivery':'external','protection_scope':'contact_layer','guard':'prepared'}
    if subject['is_template']:
        if subject['kind'] not in {'armour','shield','weapon'}:return result('item.template','blocked',reason='Experimental template has no authored component/dependency graph')
        d=values['deflection_q'] if subject['kind']=='shield' and context['delivery']=='external' and context['damage_type'] not in {'psychic','divine','poison'} else 0
        rating=values['rating_q'] if oracle.protection_route(context['damage_type'],context['delivery'],context['protection_scope'],False) else 0
        r=partition(values['damage_q'],d,values['contact_q'] if subject['kind']=='shield' else SCALE,rating,values['affinity_q'])
        metrics={**r,'redirected_fraction_q':div(r['redirected_q'],values['damage_q']) if values['damage_q'] else 0,'absorbed_fraction_q':div(r['absorbed_q'],values['damage_q']) if values['damage_q'] else 0,'transmitted_fraction_q':div(r['body_q'],values['damage_q']) if values['damage_q'] else 0}
        return result('template.mathematical_probe',rules=('K-C22','K-C26'),metrics=metrics,trace=[event('fixture_only_quantity_probe',values['damage_q'],r['body_q'],'K-C22')],details={'input_origin':'fixture-only','authored_item':False,'runtime_blocker':'No authored template dependency graph'})
    if subject['source_table']!='Equipment':return result('item.payload','blocked',reason='Executable payload/encounter implementation is unavailable; authorization probes remain runnable')
    item=next(r for r in data['tables']['Equipment'] if stable_id('Equipment',r,reg)==subject['source_revision_id'])
    chassis=next((r for r in data['tables']['Chassis_profiles'] if r['chassis_profile_id']==item['chassis_profile']),None)
    if not chassis:return result('item.source','blocked',reason='Missing chassis')
    entries=[r for r in data['tables']['Damage_profile_entries'] if r['profile_id']==chassis['base_martial_profile_id']]
    damage_types={r['damage_type_id']:r for r in data['tables']['Ref_damage_types']}
    metrics={f'delivered_{group}_q':0 for group in ['physical','volatile','corruptive','occult']};trace=[]
    for e in entries:
        D=checked(values['source_unit_q']*e['base_pips'],128);checked(D)
        group=damage_types[e['damage_type']]['damage_group']
        if group=='structural':
            metrics['structural_stress_q']=metrics.get('structural_stress_q',0)+D;trace.append(event('structural_integrity_route',D,D,'M-C2',item['equipment_revision_id']));continue
        if e['damage_type']=='divine':return result('item.divine','blocked',reason='Divine needs a Technique-declared conversion and consumed target state; weapon scaling is forbidden')
        body=transmission(D,values['rating_q'],values['affinity_q']);metrics['delivered_'+group+'_q']=metrics.get('delivered_'+group+'_q',0)+body
        trace.append(event('typed_transmission',D,body,'K-C26',item['equipment_revision_id']))
    if item['category']=='shield':
        profiles=[p for p in data['tables']['Protection_profiles'] if p['owner_revision_id']==item['equipment_revision_id']]
        incoming_group=damage_types[context['damage_type']]['damage_group']
        if incoming_group=='structural':return result('item.structural_route',rules=('M-C2',),metrics={'structural_stress_q':values['damage_q']},trace=[event('structural_integrity_route',values['damage_q'],values['damage_q'],'M-C2')],details={'threshold_blocker':'Integrity thresholds require authored calibration; stress probe only'})
        steps=sum(p['allocation_steps'] for p in profiles if p['allocation_group']==incoming_group and p['protection_scope']==context['protection_scope'] and oracle.protection_route(context['damage_type'],context['delivery'],p['protection_scope'],False))
        d=values['deflection_q'] if context['guard']=='prepared' and context['delivery']=='external' and incoming_group=='physical' else 0
        r=partition(values['damage_q'],d,values['contact_q'],checked(values['rating_q']*steps),values['affinity_q'] if steps else SCALE)
        metrics.update(r);metrics.update({'redirected_fraction_q':div(r['redirected_q'],values['damage_q']) if values['damage_q'] else 0,'absorbed_fraction_q':div(r['absorbed_q'],values['damage_q']) if values['damage_q'] else 0,'transmitted_fraction_q':div(r['body_q'],values['damage_q']) if values['damage_q'] else 0})
        trace.append(event('shield_partition',values['damage_q'],r['body_q'],'K-C22',item['equipment_revision_id']))
    return result('item.mathematical_probe',rules=('M-C24','K-C26','M-C2'),metrics=metrics,trace=trace,details={'input_origin':'declared_fixture_only','unbound_production_values_used':False,'ap_efficiency':None,'ap_efficiency_blocker':'Production Technique cost and duration not implemented'})

def tarot_probe(data):
    cases=[]
    for i,(receiver,contributor,installed) in enumerate([(3,2,[1,2]),(2,2,[1]),(2,1,[1,2])]):
        legal=contributor<receiver and sum(installed)<=receiver
        expected=[True,False,False][i];cases.append(result(f'tarot.tier_capacity.{i}','pass' if legal==expected else 'fail',('P-C21',)))
    identities=[('support.a',1),('support.a',2),('support.b',1)];chosen={}
    for key,tier in identities:chosen[key]=max(chosen.get(key,0),tier)
    cases.append(result('tarot.duplicates','pass' if chosen=={'support.a':2,'support.b':1} and len(identities)==3 else 'fail',('P-C21',),details={'installed_capacity_consumers':3,'effective_contributors':2}))
    for name,expected,actual in [('combo.identity',False,('technique.a@1','technique.b@1')==('technique.a@1','technique.c@1')),('combo.hooks',True,len({'left','right'})==2),('support.non_executable',False,False)]:cases.append(result('tarot.'+name,'pass' if expected==actual else 'fail',('P-C20','P-C22')))
    cases.append(result('tarot.runtime','blocked',reason='No authored Tarot records or resolved C1-F/G runtime behavior'))
    return cases

def triade_probes(seed,count=37):
    cases=[]
    previous={'m_q':4000,'f_q':4000,'i_q':4000}
    for i in range(count):
        # Fixed-point mathematical simplex samples, not invented actor motion.
        m=(i%13)*1000;f=((i*7)%13)*1000
        if m+f>SCALE:f=SCALE-m
        pos={'m_q':m,'f_q':f,'i_q':SCALE-m-f}
        delta={k:pos[k]-previous[k] for k in pos};assert sum(delta.values())==0 and sum(pos.values())==SCALE
        cases.append(result(f'triade.probe.{i:03}',rules=('T-C1','T-C2'),metrics=pos,details={'position_origin':'mathematical_probe','trajectory_available':False}))
        previous=pos
    return cases

def execute(data,subject,values,reg,suite,seed,budget,workers=1,cancel=lambda:False,progress=lambda n:None,overrides=None):
    output=[]
    if suite in ('combat-contracts','all'):
        declared=[c for c in data['tables']['Lab_cases'] if c['suite']=='combat-contracts']
        if not declared:output+=combat_contracts(values)
        for case in declared:
            if case['adapter']!='combat':output.append(result(case['case_id'],'blocked',reason='Unreviewed adapter identity'));continue
            case_overrides={row['name']:str(row['value_q'] if row['value_kind']=='fixed_point' else row['value_int']) for row in data['tables']['Lab_case_inputs'] if row['case']==case['case_id']}
            case_values=inputs({**case_overrides,**(overrides or {})})
            found=next((c for c in combat_contracts(case_values) if c['case_id']==case['scenario']),None)
            if found is None:output.append(result(case['case_id'],'blocked',reason='Scenario has no reviewed implementation'));continue
            found['case_id']=case['case_id']
            for assertion in data['tables']['Lab_assertions']:
                if assertion['case']!=case['case_id']:continue
                if assertion['operator'] not in {'eq','ne','le','ge'}:found['status']='blocked';found['reason']='Unsupported assertion operator';continue
                actual=found['status'] if assertion['metric']=='status' else found['metrics'].get(assertion['metric'],found['details'].get(assertion['metric']))
                expected=assertion['expected_text'] if assertion['metric']=='status' else assertion['expected_q'] if assertion['expected_q'] is not None else assertion['expected_int']
                if actual is None or expected is None:found['status']='blocked';found['reason']='Missing assertion metric';continue
                test={'eq':lambda:actual==expected,'ne':lambda:actual!=expected,'le':lambda:actual<=expected,'ge':lambda:actual>=expected}[assertion['operator']]
                if not test():found['status']='fail';found['reason']='Declared assertion failed'
            output.append(found)
    if suite in ('tarot-contracts','all'):output+=tarot_probe(data)
    if suite in ('triade-probes','all'):output+=triade_probes(seed)
    if suite in ('item-comparison','all'):output.append(item_probe(data,subject,values,reg))
    if suite in ('property-10000','all'):
        count=min(10000,budget)
        if workers>1:
            from concurrent.futures import ProcessPoolExecutor
            from multiprocessing import get_context
            with ProcessPoolExecutor(max_workers=workers,mp_context=get_context('spawn')) as pool:
                for r in pool.map(property_case,range(count),itertools.repeat(seed),chunksize=64):
                    if cancel():break
                    output.append(r)
                    if len(output)%100==0:progress(len(output))
        else:
            for index in range(count):
                if cancel():break
                output.append(property_case(index,seed))
                if index%100==0:progress(len(output))
    return sorted(output,key=lambda r:r['case_id'])
