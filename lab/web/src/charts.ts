export type Metrics = Record<string,string>;
export const scale=12000;
export function plotNumber(value:string):number { return Number(BigInt(value))/scale; }
export function commonAxes(a:Metrics,b:Metrics,keys:string[]):string[] {return keys.filter(k=>a[k]!==undefined && b[k]!==undefined);}
export function radarValues(metrics:Metrics,keys:string[],reference:number):number[] {return keys.map(k=>Number(BigInt(metrics[k]))/reference);}
export function missingAxes(a:Metrics,b:Metrics,keys:string[]):string[] {return keys.filter(k=>a[k]===undefined || b[k]===undefined);}
export function heatmap(points:{inputs:Metrics,metrics:Metrics}[]):{x:number[],y:number[],z:(number|null)[][],names:string[]} {
 const names=Object.keys(points[0]?.inputs??{}).sort();if(names.length!==2)return {x:[],y:[],z:[],names};
 const xs=[...new Set(points.map(p=>p.inputs[names[0]]))].sort((a,b)=>Number(BigInt(a)-BigInt(b)));
 const ys=[...new Set(points.map(p=>p.inputs[names[1]]))].sort((a,b)=>Number(BigInt(a)-BigInt(b)));
 return {x:xs.map(plotNumber),y:ys.map(plotNumber),names,z:ys.map(y=>xs.map(x=>{const p=points.find(p=>p.inputs[names[0]]===x&&p.inputs[names[1]]===y);return p?.metrics.body_q===undefined?null:plotNumber(p.metrics.body_q);} ))};
}
