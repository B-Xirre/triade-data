import {describe,it,expect} from 'vitest';
import {commonAxes,missingAxes,plotNumber,radarValues,heatmap} from './charts';
describe('provenance-safe chart preparation',()=>{
 it('omits missing axes rather than substituting zero',()=>{expect(commonAxes({a:'0'},{a:'12000'},['a','b'])).toEqual(['a']);expect(missingAxes({a:'0'},{a:'12000'},['a','b'])).toEqual(['b']);});
 it('uses shared reference normalization',()=>{expect(radarValues({a:'6000',b:'12000'},['a','b'],12000)).toEqual([.5,1]);});
 it('accepts exact integer wire strings for display conversion',()=>{expect(plotNumber('6000')).toBe(.5);expect(()=>plotNumber('0.5')).toThrow();});
 it('builds a deterministic matrix and preserves unavailable cells',()=>{const m=heatmap([{inputs:{a:'0',b:'0'},metrics:{body_q:'12000'}},{inputs:{a:'12000',b:'0'},metrics:{body_q:'6000'}},{inputs:{a:'0',b:'12000'},metrics:{}}]);expect(m.z).toEqual([[1,.5],[null,null]]);});
});
