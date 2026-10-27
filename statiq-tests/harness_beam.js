// Headless harness für Einfeldträger / Kragarm / Durchlaufträger: führt das komplette
// <script> von calc.html mit einem DOM-Stub aus und fängt die Diagrammdaten ab.
const fs=require('fs'), vm=require('vm');
const src=fs.readFileSync(process.argv[2],'utf8');
const code=src.match(/<script>([\s\S]*?)<\/script>/)[1];   // nur das Hauptskript (Zusatzblöcke wie data-lf folgen danach)
function run(cfg){
  const els={};
  const mk=id=>({id,value:'',textContent:'',innerHTML:'',style:{},dataset:{},classList:{add(){},remove(){},contains(){return false},toggle(){}},
    setAttribute(){},getAttribute(){return null},appendChild(){},querySelector(){return null},querySelectorAll(){return []},addEventListener(){},
    closest(){return null}, childNodes:[]});
  const get=id=>els[id]||(els[id]=mk(id));
  const vals={bL:cfg.L,cL:cfg.L,'beam-E':210,'beam-Iy':cfg.Iy||10,'cant-E':210,'cant-Iy':cfg.Iy||10,'cont-E':210,'cont-Iy':cfg.Iy||10};
  Object.entries(vals).forEach(([k,v])=>get(k).value=String(v));
  let cap={}; const warns=[];
  const ctx={document:{getElementById:get,querySelectorAll:()=>[],querySelector:()=>null,addEventListener(){},createElement:()=>mk('x'),body:mk('body')},
    window:{addEventListener(){}}, localStorage:{getItem:()=>null,setItem(){},length:0,key:()=>null},
    console:{log(){},warn:(...a)=>warns.push(a.join(' '))}, alert:m=>{throw new Error('alert: '+m)}, setTimeout(){},
    navigator:{}, location:{}, Math, JSON, parseFloat, parseInt, isFinite, Date};
  vm.createContext(ctx);
  // Kein Rendern: Diagramm-Funktionen abfangen
  vm.runInContext(code+`
    ;renderDiagram=function(sys,data){ __cap(sys,data); };
    drawBeam=drawCantilever=renderContUI=function(){};`, ctx.__cap=undefined||ctx);
  ctx.__cap=(sys,data)=>{cap[sys]=data;};
  vm.runInContext(`
    loads.beam={point:[],dist:[],horiz:[]}; loads.cant={point:[],dist:[],horiz:[]};`,ctx);
  let err=null;
  try{
    if(cfg.sys==='beam'||cfg.sys==='cant'){
      ctx.__cfg=cfg;
      vm.runInContext(`(()=>{const c=__cfg; const s=c.sys;
        loads[s].point=(c.points||[]).map((v,i)=>({id:100+i,enabled:true,values:v}));
        loads[s].dist=(c.dists||[]).map((v,i)=>({id:200+i,enabled:true,values:v}));
        loads[s].horiz=(c.horiz||[]).map((v,i)=>({id:300+i,enabled:true,values:v}));
        s==='beam'?calculateBeam():calculateCantilever();})()`,ctx);
    } else {
      ctx.__cfg=cfg;
      vm.runInContext(`(()=>{const c=__cfg; numSpans=c.spans.length;
        const seg=(sp,k)=>({L:sp.L,k:sp.k||1,point:(sp.points||[]).map((v,i)=>({id:k*100+i,enabled:true,values:v})),
          dist:(sp.dists||[]).map((v,i)=>({id:k*100+50+i,enabled:true,values:v})),
          mom:(sp.moms||[]).map((v,i)=>({id:k*100+80+i,enabled:true,values:v}))});
        spanData=c.spans.map(seg);
        const cc=c.cont||{};
        contCfg={supL:cc.supL||'pin', supR:cc.supR||'roller', ovL:cc.ovL?seg(cc.ovL,7):{L:0,point:[],dist:[],mom:[]}, ovR:cc.ovR?seg(cc.ovR,8):{L:0,point:[],dist:[],mom:[]},
          hinges:(cc.hinges||[]).map((g,i)=>({id:900+i, span:g.span, a:g.a}))};
        calculateContinuous();})()`,ctx);
    }
  }catch(e){err=String(e.message||e);}
  const sid=cfg.sys==='cantilever'?'cant':cfg.sys;
  const d=cap[sid]; let out=null;
  if(d){ const m=d.members[0]; let w=m.w||null;
    if(!w){ // alte Version: Durchbiegung so, wie der Renderer sie berechnet hat
      const Lr=d.totalL||m.memberLen||Math.hypot(m.x1-m.x0,m.y1-m.y0);
      w = sid==='cant' ? ctx.computeDeflectionCant(sid,m.M,Lr) : ctx.computeDeflection(sid,m.M,Lr);
    }
    out={M:m.M,Q:m.Q,N:m.N,ts:m.ts||null,w,x0:m.x0,x1:m.x1}; }
  const txt={}; Object.keys(els).forEach(k=>{ if(els[k].textContent) txt[k]=els[k].textContent; });
  const msgs=(get('msg-'+sid).innerHTML||'');
  return {err,out,txt,msgs,table:(get('cont-reactions-body').innerHTML||'')};
}
module.exports={run};
if(require.main===module) console.log(JSON.stringify(run(JSON.parse(process.argv[3]))));
