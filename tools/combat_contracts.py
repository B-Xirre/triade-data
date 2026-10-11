"""Pure exact arithmetic for authoring validation, not a gameplay engine."""
from fractions import Fraction

def transmit(damage, rating, affinity=Fraction(1)):
    if rating < 0 or affinity <= 0: raise ValueError('invalid_defence_domain')
    return damage * affinity / (1 + rating)

def shield_partition(damage, deflection, contact, transmission):
    if not (0 <= deflection < 1 and 0 <= contact <= 1) or transmission < 0:
        raise ValueError('invalid_shield_domain')
    redirected=damage*deflection
    hit=(damage-redirected)*contact
    bypass=damage-redirected-hit
    transferred=hit*transmission
    absorbed=max(0,hit-transferred)
    amplification=max(0,transferred-hit)
    return dict(redirected=redirected,absorbed=absorbed,body=bypass+transferred,amplification=amplification)

def active_deflection(value, calibration, cap, compatible=True):
    if value<0 or calibration<=0 or not 0<cap<1: raise ValueError('invalid_active_domain')
    return cap*value/(calibration+value) if compatible else Fraction(0)

def aim_distribution(probabilities, target, weight, ceiling):
    if not 0<=weight<ceiling<1 or target not in probabilities or sum(probabilities.values())!=1:
        raise ValueError('invalid_aim_domain')
    return {key:(1-weight)*value+(weight if key==target else 0) for key,value in probabilities.items()}

def allocate_integer(total, weights):
    if total<0 or any(v<0 for v in weights) or sum(weights)<=0: raise ValueError('invalid_allocation')
    denominator=sum(weights); values=[total*w//denominator for w in weights]
    ordered=sorted(range(len(weights)),key=lambda i:(-(total*weights[i]%denominator),i))
    for i in ordered[:total-sum(values)]: values[i]+=1
    return values

def scoped_transmit(damage, contributions, stages):
    seen=set()
    for stage in stages:
        if seen.intersection(stage):raise ValueError('duplicate_protection_stage')
        seen.update(stage);damage=transmit(damage,sum((contributions[key] for key in stage),Fraction(0)))
    return damage

def effective_offhand(entries, apply):
    result=[dict(entry) for entry in sorted(entries,key=lambda e:e['sort_order'])]
    if len({e['sort_order'] for e in result})!=len(result):raise ValueError('ambiguous_priority')
    if apply and result:
        highest=max(e['pips'] for e in result)
        index=max(i for i,e in enumerate(result) if e['pips']==highest)
        result[index]['pips']-=1
    return [e for e in result if e['pips']>0]

def reinforced_threshold(base, resilience):
    if base<0 or resilience<0:raise ValueError('invalid_integrity_domain')
    return base*(1+resilience)

def choose_ward(profiles):
    eligible=[p for p in profiles if p['functional'] and p['compatible']]
    if not eligible:return None
    top=max(p['priority'] for p in eligible); tied=[p for p in eligible if p['priority']==top]
    if len({p['contract'] for p in tied})>1:raise ValueError('incompatible_ward_priority')
    return min(tied,key=lambda p:p['id'])

def purge(state, coefficients, committed, hostile, rating=Fraction(0), affinity=Fraction(1)):
    if not committed:return dict(remaining=dict(state),consumed=Fraction(0),damage=Fraction(0))
    raw=sum((amount*coefficients[key] for key,amount in state.items()),Fraction(0))
    return dict(remaining={},consumed=sum(state.values(),Fraction(0)),damage=transmit(raw,rating,affinity) if hostile else Fraction(0))

def protection_route(damage_type, delivery, scope, explicit_internal=False):
    if delivery=='internal':return scope=='recipient_domain' and explicit_internal
    if damage_type=='psychic':return scope=='recipient_domain'
    return scope in {'contact_layer','recipient_domain'}

def shield_budget(shield_class, passive, active, total):
    if min(passive,active,total)<0 or passive+active>total:raise ValueError('invalid_shield_budget')
    if shield_class=='buckler' and passive!=0:raise ValueError('buckler_passive_allocation')
    return passive,active

def tissue_shares(weights,present):
    eligible={k:v for k,v in weights.items() if k in present and v>0}
    if any(v<0 for v in weights.values()) or not eligible:raise ValueError('empty_or_invalid_tissue_route')
    total=sum(eligible.values());return {k:Fraction(v,total) for k,v in eligible.items()}

def integrity_event(state,stress,thresholds):
    if any(v<0 for v in stress):raise ValueError('negative_integrity_stress')
    return state+1 if state<len(thresholds) and sum(stress)>=thresholds[state] else state

def round_away(value):
    value=Fraction(value);sign=-1 if value<0 else 1;value=abs(value)
    return sign*((2*value.numerator+value.denominator)//(2*value.denominator))

def source_budget(unit,pips):
    if unit<0 or pips<0:raise ValueError('invalid_source_budget')
    return unit*pips

def injury_cost(base,aim,taxes,cap):
    if min(base,aim,cap)<0 or any(v<0 for v in taxes):raise ValueError('invalid_cost')
    return base+aim+min(sum(taxes),cap)
