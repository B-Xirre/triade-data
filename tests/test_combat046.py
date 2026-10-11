from pathlib import Path
from fractions import Fraction as F
import copy,json,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from combat_contracts import *
from authoring046 import canonical,validate
from authoring_api import GristAPI

class Combat046Tests(unittest.TestCase):
    def test_shield_partition_conserves(self):
        for di in range(10):
            for ci in range(11):
                for transmission in [F(0),F(2,3),F(1),F(5,4)]:
                    r=shield_partition(F(100),F(di,10),F(ci,10),transmission)
                    self.assertEqual(r['redirected']+r['absorbed']+r['body'],100+r['amplification'])
    def test_role_crossing(self):
        self.assertEqual(shield_partition(F(100),F(2,5),F(1,5),F(1))['body'],60)
        self.assertEqual(shield_partition(F(100),F(1,20),F(9,10),F(2,3))['body'],F(133,2))
        self.assertGreater(60+3*100,F(133,2)+3*70)
    def test_duplicate_scope_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):scoped_transmit(F(100),{'plate':F(1)},[['plate'],['plate']])
    def test_recipient_scope_aggregates_once(self):
        self.assertEqual(scoped_transmit(F(100),{'a':F(1),'b':F(1)},[['a','b']]),F(100,3))
    def test_aim_weight_not_probability_cap(self):
        result=aim_distribution({'head':F(8,110),'other':F(102,110)},'head',F(59,100),F(3,5))
        self.assertEqual(sum(result.values()),1);self.assertGreater(result['head'],F(3,5))
        with self.assertRaises(ValueError):aim_distribution({'head':F(1)},'head',F(3,5),F(3,5))
    def test_conservative_integer_split(self):self.assertEqual(allocate_integer(7,[1,1,1]),[3,2,2])
    def test_affinity_domains(self):
        with self.assertRaises(ValueError):transmit(100,F(-1))
        with self.assertRaises(ValueError):transmit(100,F(1),F(0))
    def test_active_response_saturates_and_requires_route(self):
        self.assertEqual(active_deflection(F(1),F(1),F(3,5)),F(3,10))
        self.assertEqual(active_deflection(F(1),F(1),F(3,5),False),0)
        self.assertLess(active_deflection(F(100000),F(1),F(3,5)),F(3,5))
    def test_offhand_tie_uses_last(self):
        rows=[{'type':'slash','pips':1,'sort_order':1},{'type':'pierce','pips':1,'sort_order':2}]
        self.assertEqual(effective_offhand(rows,True),[rows[0]])
    def test_ward_priority_not_chain(self):
        a={'id':'a','priority':1,'functional':True,'compatible':True,'contract':'soft'}
        b={'id':'b','priority':1,'functional':True,'compatible':True,'contract':'hard'}
        with self.assertRaises(ValueError):choose_ward([a,b])
        b['priority']=2;self.assertEqual(choose_ward([a,b]),b)
    def test_reinforcement_threshold_not_second_damage_factor(self):self.assertEqual(reinforced_threshold(40,F(1,2)),60)
    def test_divine_consumption_not_refunded(self):
        state={'corruption':F(30)};coeff={'corruption':F(2)}
        result=purge(state,coeff,True,True,F(1,2),F(4,5));self.assertEqual(result['damage'],32);self.assertEqual(result['consumed'],30)
        self.assertEqual(purge(result['remaining'],coeff,True,True)['damage'],0)
        self.assertEqual(purge(state,coeff,False,True)['remaining'],state)
        self.assertEqual(purge(state,coeff,True,False)['damage'],0)
    def test_loopback_and_candidate_guards(self):
        with self.assertRaises(ValueError):GristAPI(base_url='https://example.com')
        with self.assertRaises(ValueError):GristAPI().apply_candidate('active','active','backup',[])
    def test_internal_poison_explicit_recipient_only(self):
        self.assertFalse(protection_route('poison','internal','contact_layer',True))
        self.assertFalse(protection_route('poison','internal','recipient_domain'))
        self.assertTrue(protection_route('poison','internal','recipient_domain',True))
    def test_psychic_bypasses_contact_layer(self):
        self.assertFalse(protection_route('psychic','external','contact_layer'))
        self.assertTrue(protection_route('psychic','external','recipient_domain'))
    def test_buckler_zero_passive_and_budget_conservation(self):
        self.assertEqual(shield_budget('buckler',0,4,4),(0,4))
        with self.assertRaisesRegex(ValueError,'buckler'):shield_budget('buckler',1,3,4)
        with self.assertRaisesRegex(ValueError,'budget'):shield_budget('tower',4,2,5)
    def test_absent_tissue_mask_and_empty_rejection(self):
        self.assertEqual(tissue_shares({'skin':2,'bone':1,'brain':3},{'skin','bone'}),{'skin':F(2,3),'bone':F(1,3)})
        with self.assertRaises(ValueError):tissue_shares({'brain':1},{'skin'})
    def test_simultaneous_integrity_one_transition(self):
        self.assertEqual(integrity_event(0,[5,5],[10,20]),1)
        self.assertEqual(integrity_event(0,[100,100],[10,20]),1)
        self.assertEqual(integrity_event(1,[9,9],[10,20]),1)
    def test_ties_away_from_zero(self):
        self.assertEqual([round_away(F(n,2)) for n in [-3,-1,1,3]],[-2,-1,1,2])
    def test_checked_signed64_boundaries(self):
        self.assertEqual(checked_int64(-(1<<63)),-(1<<63))
        self.assertEqual(checked_int64((1<<63)-1),(1<<63)-1)
        for value in [-(1<<63)-1,1<<63,True,F(1,2)]:
            with self.assertRaises(ValueError):checked_int64(value)
    def test_source_calibration_once_and_redistribution_conserves(self):
        raw=source_budget(7,4);self.assertEqual(raw,28)
        self.assertEqual(sum(allocate_integer(raw,[1,2,1])),raw)
    def test_only_aggregated_adverse_tax_capped(self):
        self.assertEqual(injury_cost(12,5,[2,3,4],6),23)

if __name__=='__main__':unittest.main()
