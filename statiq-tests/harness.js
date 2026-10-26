// Headless harness: extracts frame solver functions from calc.html and runs calculateFrame()
const fs=require('fs'), vm=require('vm');
const src=fs.readFileSync(process.argv[2]||'calc.html','utf8');
function extract(name){
  const i=src.indexOf('function '+name+'(');
  if(i<0) throw new Error('missing '+name);
  let j=src.indexOf('{',src.indexOf(')',i)); // first body brace after param list
  // params may contain default obj {} -> find ')' matching
  let p=src.indexOf('(',i),d=0,k=p;
  for(;k<src.length;k++){ if(src[k]==='(')d++; else if(src[k]===')'){d--; if(!d)break;} }
  j=src.indexOf('{',k); d=0;
  for(k=j;k<src.length;k++){ if(src[k]==='{')d++; else if(src[k]==='}'){d--; if(!d)break;} }
  return src.slice(i,k+1);
}
const names=['frameGableOf','frameGable','frameRafY','frameRafLen','supportDOF','frameEffectiveHinges','frameIndeterminacy','checkPos','cutRange','frameBuildModel','frameElemK','frameElemT','frameElemFeq','frameSolveDSM','frameForcesAt','frameSampleForces','sampleUniform','frameDispAt','frameSampleFine','sampleFine','calculateFrame'];
const consts=src.match(/const EPS_POS[^\n]*/)[0]+'\n'+src.match(/const FRAME_EA_FACTOR[^\n]*/)[0]+'\n'+src.match(/const GAUSS4[\s\S]*?\]\];/)[0];
const code=consts+'\n'+names.map(extract).join('\n\n');
function run(cfg){
  const els={}; const get=id=>els[id]||(els[id]={value:'',textContent:'',innerHTML:'',classList:{remove(){},add(){}}});
  get('fB').value=String(cfg.b); get('fH').value=String(cfg.hA); get('fHA').value=String(cfg.hA); get('fHB').value=String(cfg.hB);
  get('frame-E-raf').value='210'; get('frame-Iy-raf').value=String(cfg.IR||10);
  get('frame-E-col').value='210'; get('frame-Iy-col').value=String(cfg.IS||10);
  let captured=null, warns=[];
  const ctx={document:{getElementById:get}, console:{warn:(...a)=>warns.push(a.join(' ')),log(){}},
    alert:m=>{throw new Error('alert: '+m)}, Math,parseFloat,
    supportA:cfg.A, supportB:cfg.B, supportHead:cfg.head||'none', supportHeadType:cfg.headType||'roller',
    frameHinges:cfg.hinges||[], frameLoads:{vert:(cfg.q||[]).map(v=>({enabled:true,values:v})), horiz:(cfg.F||[]).map(v=>({enabled:true,values:v}))},
    renderFrameDiagram:(...a)=>{captured=a;},
    // Meldungen: Fehler wie früher als Ausnahme (err), Hinweise sammeln
    msgText:(k,...a)=>[k,...a].join(' '), tr:k=>({headRow:'H (top)'})[k]||k, trf:(k,...a)=>[k,...a].join(' '),
    calcError:(sys,k,...a)=>{ throw new Error('alert: '+[k,...a].join(' ')); },
    showCalcMsgs:(sys,items)=>{ items.forEach(m=>warns.push(m.text)); },
    // Schnappschuss/Systembild (ab v0.8.2): für die Rechentests ohne Bedeutung
    drawFrame(){}, systemSnapshot:()=> '', lastCalc:{},
    r4:a=>a.map(v=>+(+v).toFixed(4)), signedMaxOf:a=>a.reduce((m,v)=>Math.abs(v)>Math.abs(m)?v:m,0)};
  vm.createContext(ctx);
  vm.runInContext(code,ctx);
  let err=null; let r=null;
  try{ vm.runInContext('calculateFrame()',ctx);}catch(e){err=String(e.message||e);}
  const table=get('frame-reactions-body').innerHTML;
  if(captured){
    const [b,h,allM,allQ,allN,NP]=captured; const n=NP+1;
    const L=allM.slice(0,n), R=allM.slice(n,2*n), Rr=allM.slice(2*n,3*n);
    const QL=allQ.slice(0,n),QR=allQ.slice(n,2*n),QRr=allQ.slice(2*n);
    const NL=allN.slice(0,n),NR=allN.slice(n,2*n),NRr=allN.slice(2*n);
    r={NP,M:{L,R,Rr},Q:{L:QL,R:QR,Rr:QRr},N:{L:NL,R:NR,Rr:NRr}};
    const fine=captured[11];
    if(fine) r.fine={L:fine.left,R:fine.rafter,Rr:fine.right};
    r.max={M:parseFloat(get('f-res-Mmax').textContent),Q:parseFloat(get('f-res-Qmax').textContent),N:parseFloat(get('f-res-Nmax').textContent)};
  }
  return {err,warns,table,r,indet:get('f-res-indet').textContent};
}
module.exports={run};
if(require.main===module){
  const out=run(JSON.parse(process.argv[3]));
  console.log(JSON.stringify(out));
}
