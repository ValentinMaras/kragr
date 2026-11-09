# calc v0.11.30: Rechenkern in solver.js — ohne Seite nutzbar (Node), Referenzfälle, Unbestimmtheit, calc.html nutzt den Kern,
# Offline-Speicher. Die bisherigen Rechentests (runtests*, test_calc_*) laufen unverändert über den Kern. Ohne Node/Playwright: SKIP.
import os, sys, json, subprocess, asyncio, re, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
if not shutil.which('node'): print('SKIP node fehlt'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
def node(js):
    r=subprocess.run(['node','-e',f"const S=require({json.dumps(os.path.join(BASE,'solver.js'))}); const out=(()=>{{ {js} }})(); console.log(JSON.stringify(out));"],capture_output=True,text=True)
    if r.returncode: return {'err':r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'Fehler'}
    return json.loads(r.stdout)
near=lambda a,b,t=0.006: abs(a-b)<=t
# Durchlaufträger 2 × 5 m, q = 10 kN/m: A = C = 3/8·q·l = 18,75 kN, B = 10/8·q·l = 62,5 kN, M_B = −q·l²/8 = −31,25 kNm
r=node("const r=S.lineSolve(10,{supports:[{x:0,type:'pin'},{x:5,type:'roller'},{x:10,type:'roller'}],points:[],dists:[{a:0,b:10,qa:10,qb:10}],EI:21000}); return {V:r.reac.map(x=>x.V), MB:r.at(5).M};")
check('lineSolve: Durchlaufträger 2 × 5 m, q = 10 → 18,75 / 62,5 / 18,75 kN', 'V' in r and all(near(a,b) for a,b in zip(r['V'],[18.75,62.5,18.75])), r)
check('lineSolve: Stützmoment M_B = −31,25 kNm', 'MB' in r and near(r['MB'],-31.25), r.get('MB'))
# Kragarm 3 m, F = 10 kN am Ende: M_A = −30 kNm (Zug oben), Einspannmoment der Lagerkraft ↺ +30
r=node("const r=S.lineSolve(3,{supports:[{x:0,type:'fixed'}],points:[{x:3,Fx:0,Fy:10,Me:0}],dists:[],EI:21000}); return {M0:r.at(0).M, R:r.reac[0]};")
check('lineSolve: Kragarm F = 10 kN, l = 3 m → M = −30 kNm, V_A = 10 kN', near(r['M0'],-30) and near(r['R']['V'],10), r)
# Rahmen eingespannt/eingespannt, h = 4, b = 5, q = 10: Kopf −14,88, Fuß +7,44, Feld +16,37 kNm (Referenzfall der Handoff-Notiz)
r=node("""const q=[{enabled:true,values:{member:'rafter',qa:10,qb:10,a:0,b:5}}];
const R=S.frameSolve({b:5,hA:4,hB:4,supA:'fixed',supB:'fixed',head:'none',hinges:[],vLoads:q,hLoads:[],EI_S:2100,EI_R:2100,NP:50});
const L=R.forces.left.M, F=R.forces.rafter.M; return {fuss:L[0], kopf:L[50], feld:F[25], reac:R.reac, mech:!!R.mechanism};""")
check('frameSolve: eingespannter Rahmen q = 10 → Fuß +7,44, Kopf −14,88, Feld +16,37', 'fuss' in r and near(r['fuss'],7.44,0.01) and near(r['kopf'],-14.88,0.01) and near(r['feld'],16.37,0.01), r)
check('frameSolve: Lagerkräfte V_A = V_B = 25 kN (Symmetrie)', 'reac' in r and near(r['reac']['A']['V'],25) and near(r['reac']['B']['V'],25), r.get('reac'))
r=node("""return ['three','two','fixed','mech'].map(k=>S.frameIndeterminacyOf({b:5,hA:4,hB:4,head:'none',
  supA:k==='fixed'?'fixed':k==='mech'?'roller':'pin', supB:k==='fixed'?'fixed':k==='mech'?'roller':'pin', hinges:k==='three'?[{member:'rafter',pos:2.5}]:[]}));""")
check('frameIndeterminacyOf: Dreigelenk 0, Zweigelenk 1, eingespannt 3, zwei Loslager −1', r==[0,1,3,-1], r)
r=node("const R=S.frameSolve({b:5,hA:4,hB:4,supA:'roller',supB:'roller',head:'none',hinges:[],vLoads:[],hLoads:[],EI_S:2100,EI_R:2100}); return !!R.mechanism;")
check('frameSolve: verschiebliches System wird als Mechanismus erkannt', r is True, r)
# ── Lastfälle und Kombinationen im Kern (calc v0.11.31) ──
r=node("""const a=S.lcRules({na:'de',cat:'A'}), e=S.lcRules({na:'es',cat:'E'}), c=S.lcRules({na:'ch',psiCH:{Q:0.5}}), u=S.lcRules({na:'uk',cat:'H'});
return {aQ:a.psi.Q, aI:a.gInf, eCat:e.cat, eI:e.gInf, cMode:c.mode, cQ:c.psi.Q[0], cW:c.psi.W1[0], uQ:u.psi.Q, uW:u.psi.W1, uMode:u.mode};""")
check('lcRules: DE ψ(A) 0,7/0,5/0,3, γ_G,inf 1,0 · ES 0,80 ohne Kategorie E · CH ψ0 eingegeben, leer 1,0 · UK H 0,7/0/0, Wind 0,5', r.get('aQ')==[0.7,0.5,0.3] and r['aI']==1 and r['eCat']=='A' and r['eI']==0.8 and r['cMode']=='ch' and r['cQ']==0.5 and r['cW']==1 and r['uQ']==[0.7,0,0] and r['uW']==[0.5,0.2,0] and r['uMode']=='uk', r)
r=node("""const P=[{k:'G',i:0,T:'G'},{k:'Q',i:1,T:'Q'},{k:'S',i:2,T:'S'}];
return ['de','uk'].map(na=>{ const O=S.lcOptions(S.lcRules({na}),P); return [O.filter(o=>o.uls).length, O.filter(o=>!o.uls).length]; });""")
check('lcOptions: G, Q, S → DE 6 + 3 Kombinationen, UK 6.10a/b: 6 + 3', r==[[6,3],[6,3]], r)
# Einfeldträger 5 m: g = 10, q = 5 (Q), s = 4 (S) kN/m — M_G = 31,25, M_Q = 15,625, M_S = 12,5 kNm; V_G = 25, V_Q = 12,5, V_S = 10 kN
LC="""const L=5, run=q=>{ const r=S.lineSolve(L,{supports:[{x:0,type:'pin'},{x:L,type:'roller'}],points:[],dists:q?[{a:0,b:L,qa:q,qb:q}]:[],EI:21000});
  return S.lcSample({elems:r.model.elems, reac:r.reac.map(x=>[x.H,x.V,x.M])}, ['beam'], 120); };
const runs=[run(10), run(5), run(4)], P=[{k:'G',i:0,T:'G'},{k:'Q',i:1,T:'Q'},{k:'S',i:2,T:'S'}];
const C=S.lcCombine(S.lcRules(NA), ['beam'], P, runs);
return {maxM:C.gov.maxM.v, minM:(e=>e.M2[e.t.reduce((b,t,i,a)=>Math.abs(t-0.5)<Math.abs(a[b]-0.5)?i:b,0)])(C.env.beam), VA:C.reac[0][1][0], fac:C.gov.maxM.fac, w:C.gov.sls.v};"""
r=node(LC.replace('NA',"{na:'de',cat:'A'}"))
check('lcCombine DE: max M = 1,35·31,25 + 1,5·12,5 + 1,5·0,7·15,625 = 77,34 kNm (Leiteinwirkung Schnee)', near(r.get('maxM',0),77.34375,0.01) and all(near(r['fac'][k],v,1e-9) for k,v in {'G':1.35,'Q':1.05,'S':1.5}.items()), r)
check('lcCombine DE: min M in Feldmitte = 1,0·31,25 kNm (veränderliche günstig weggelassen), max V_A = 61,88 kN', near(r['minM'],31.25,0.02) and near(r['VA'],61.875,0.01), (r['minM'],r['VA']))
r=node(LC.replace('NA',"{na:'ch',psiCH:{Q:0.7,S:0.5}}"))
check('lcCombine CH (SIA 260): Begleiteinwirkung ψ0·Q_k ohne γ_Q → max M = 71,88 kNm', near(r.get('maxM',0),71.875,0.01), r.get('maxM'))
src=open(os.path.join(BASE,'calc.html'),encoding='utf-8').read(); sol=open(os.path.join(BASE,'solver.js'),encoding='utf-8').read()
moved=['frameBuildModel','frameSolveDSM','frameSampleForces','frameSampleFine','lineBuildModel','lineSolve','sampleFine','sampleUniform','frameForcesAt','tempRows']
check('calc.html: Kern nicht mehr in der Seite, solver.js wird vor dem Hauptskript geladen', not any(re.search(r'\nfunction '+n+r'\(',src) for n in moved) and src.index('<script src="solver.js"></script>')<src.index('const STATIQ_VERSION'))
check('calc.html: Beiwerte und Überlagerung der Lastfälle nur noch im Kern (calc v0.11.31)', 'const LF_PSI' not in src and 'const LF_GSUP' not in src and '\nfunction lcCombine(' not in src and 'lcCombine(lfRules(t)' in src)
check('solver.js: keine Zugriffe auf die Seite (document, window)', not re.search(r'\bdocument\.|\bwindow\.', re.sub(r'//[^\n]*','',sol)))
check('Offline-Speicher (sw.js) enthält solver.js', '"solver.js"' in open(os.path.join(BASE,'sw.js'),encoding='utf-8').read())
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright'); print('FAILS:', fails); sys.exit(0)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+BASE+'/calc.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(800)
        r=await pg.evaluate("""()=>{ calculateFrame(); const page=parseFloat(document.getElementById('f-res-Mmax').textContent);
          const I=frameGeomInp(); const R=frameSolve({...I, vLoads:frameLoads.vert.filter(l=>l.enabled), hLoads:frameLoads.horiz.filter(l=>l.enabled), EI_S:21000, EI_R:21000, gable:frameGable(I.b,I.hA,I.hB), temps:[]});
          const core=Math.max(...['left','rafter','right'].flatMap(m=>R.fine[m].M.map(Math.abs))); return {page, core, typ:typeof KragrSolver}; }""")
        check('calc.html: Rahmen in der Seite = Kern direkt (M_max)', abs(r['page']-r['core'])<0.006 and r['typ']=='object', r)
        check('calc.html: keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
