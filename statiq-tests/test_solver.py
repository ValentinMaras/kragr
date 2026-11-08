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
src=open(os.path.join(BASE,'calc.html'),encoding='utf-8').read(); sol=open(os.path.join(BASE,'solver.js'),encoding='utf-8').read()
moved=['frameBuildModel','frameSolveDSM','frameSampleForces','frameSampleFine','lineBuildModel','lineSolve','sampleFine','sampleUniform','frameForcesAt','tempRows']
check('calc.html: Kern nicht mehr in der Seite, solver.js wird vor dem Hauptskript geladen', not any(re.search(r'\nfunction '+n+r'\(',src) for n in moved) and src.index('<script src="solver.js"></script>')<src.index('const STATIQ_VERSION'))
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
