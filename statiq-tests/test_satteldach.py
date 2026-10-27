# Satteldachrahmen (calc v0.11.3 · size v0.7.5 · projekt v0.1.21): Riegel als Polygonzug über den First (Stich f, Firstlage xF).
# Sollwerte unabhängig von Hand: Dreigelenk-Satteldachrahmen b = 10 m, h = 4 m, f = 2 m, q = 10 kN/m Grundriss:
#   V = q·b/2 = 50 kN, H = q·b²/(8·(h+f)) = 20,833 kN, M_Ecke = −H·h = −83,33 kNm, M_First = 0,
#   M(x = 2,4) = V·2,4 − H·(4+0,96) − q·2,4²/2 = −12,13 kNm, Riegelanfang N = −(H·cos α + V·sin α), Q = V·cos α − H·sin α (tan α = 0,4).
# Einzellast 20 kN im First: H = 10·5/6 = 8,333 kN. Wind rechtwinklig auf die linke Dachfläche (q = 1 kN/m, Länge √29):
#   Resultierende waagerecht q·f = 2 kN, lotrecht q·5 = 5 kN. Dazu Skizze, Knoten (First = eigener Knoten), Speichern, Bericht, Übergabe.
import os, sys, asyncio, math, json
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
near=lambda a,b,t=0.01: abs(a-b)<=t
def end(K, i, k):
    for b in K['bars']:
        if b['i']==i and b['k']==k: return b['ik']
        if b['k']==i and b['i']==k: return b['ki']
SETUP="""fB.value=10; gableSyncB(); fH.value=4; syncFrameHeights('h'); setRoof(true); fF.value=2; fXF.value=5;
  frameLoads.horiz=[]; frameLoads.vert=[{id:900,enabled:true,values:{member:'rafter',qa:10,qb:10,a:0,b:10,rdir:'v'}}];
  renderFrameLoads('vert'); renderFrameLoads('horiz'); applyFramePreset('%s'); liveCalc(true)"""
REAC="[...document.querySelectorAll('#frame-reactions-body tr')].map(r=>[...r.querySelectorAll('td')].map(td=>td.textContent))"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[getComputedStyle(document.getElementById('gable-row')).display, document.getElementById('btn-roof-flat').classList.contains('active'), document.querySelectorAll('#frame-svg .k-raf').length]")
        check('Voreinstellung: gerader Riegel, Felder f und xF verborgen', r==['none',True,0], r)
        await pg.evaluate(SETUP % 'three'); await pg.wait_for_timeout(700)
        r=await pg.evaluate("[getComputedStyle(document.getElementById('gable-row')).display, document.getElementById('btn-roof-gable').classList.contains('active'), document.querySelectorAll('#frame-svg .k-raf').length, frameHinges.map(h=>[h.member,h.pos])]")
        check('Satteldach an: Felder sichtbar, Riegel als Polygonzug, Dreigelenk-Vorlage setzt das Gelenk in den First', r[0]!='none' and r[1] and r[2]==1 and r[3]==[['rafter',5]], r)
        K=await pg.evaluate("lastCalc.frame.knoten")
        check('Knoten: 1 A · 2 Ecke links · 3 First (Gelenk) · 4 Ecke rechts · 5 B', [(n['kind'],n['lab'],n['gelenk']) for n in K['nodes']]==[('sup','A',False),('ecke','L',False),('first','F',True),('ecke','R',False),('sup','B',False)], K['nodes'])
        rc=await pg.evaluate(REAC)
        check('Auflager: V = 50 kN, H = q·b²/(8·(h+f)) = 20,83 kN (Hand)', rc[0][1:3]==['20.83','50.00'] and rc[1][1:3]==['-20.83','50.00'], rc)
        check('Eckmoment M21 = M23 = −H·h = −83,33 kNm, Firstmoment M32 = M34 = 0', near(end(K,2,1)['M'],-83.333) and near(end(K,2,3)['M'],-83.333) and end(K,3,2)['M']==0 and end(K,3,4)['M']==0, (end(K,2,3), end(K,3,2)))
        ca, sa = 5/math.sqrt(29), 2/math.sqrt(29); H=1000/48
        check('Riegelanfang: N23 = −(H·cos α + V·sin α) = −37,91, Q23 = V·cos α − H·sin α = 38,69 kN', near(end(K,2,3)['N'],-(H*ca+50*sa)) and near(end(K,2,3)['Q'],50*ca-H*sa), end(K,2,3))
        check('First links: N32 = −H·cos α = −19,34, Q32 = −H·sin α = −7,74 kN; rechts symmetrisch', near(end(K,3,2)['N'],-H*ca) and near(end(K,3,2)['Q'],-H*sa) and near(end(K,3,4)['N'],-H*ca) and near(end(K,3,4)['Q'],H*sa), (end(K,3,2), end(K,3,4)))
        m=await pg.evaluate("(()=>{ const f=lastCalc.frame.plot.fine.rafter; let k=0; f.t.forEach((t,i)=>{ if(Math.abs(t-0.24)<Math.abs(f.t[k]-0.24)) k=i; }); return [f.t[k], f.M[k]]; })()")
        check('Riegelmoment bei x = 2,4 m: V·2,4 − H·4,96 − q·2,4²/2 = −12,13 kNm (Hand)', near(m[0],0.24,1e-6) and near(m[1],120-H*4.96-28.8), m)
        t=await pg.evaluate("document.querySelector('#frame-results .k-knoten').textContent")   # Karte ist mit k5 zugeklappt
        check('Knotenkarte: „First (mit Gelenk)“, Stäbe „Riegel links“ und „Riegel rechts“', 'First (mit Gelenk)' in t and 'Stab 2–3 · Riegel links' in t and 'Stab 3–4 · Riegel rechts' in t, t[:300])
        r=await pg.evaluate("[document.querySelectorAll('#frame-svg .k-knr').length, document.querySelectorAll('#frame-svg .k-faser polyline').length, [...document.querySelectorAll('#frame-svg text')].some(e=>e.textContent==='f=2m')]")
        check('Skizze: fünf Knotennummern, Faser als Polygonzug, Stichmaß f = 2 m', r==[5,1,True], r)
        r=await pg.evaluate("[...['M','Q','N','W']].map(m=>{ setDiagMode('frame',m); return document.querySelectorAll('#diag-svg-frame polyline').length; })")
        check('Verläufe M, Q, N, w: Riegel mit Knick am First gezeichnet', all(x>=1 for x in r), r)
        await pg.evaluate("setDiagMode('frame','M')")
        # Einzellast im First (Winkelhalbierende = lotrecht)
        await pg.evaluate("frameLoads.vert=[]; frameLoads.horiz=[{id:901,enabled:true,values:{member:'rafter',F:20,H:0,z:5}}]; renderFrameLoads('vert'); renderFrameLoads('horiz'); liveCalc(true)"); await pg.wait_for_timeout(500)
        rc=await pg.evaluate(REAC)
        check('Einzellast 20 kN im First: V = 10 kN, H = 10·5/6 = 8,33 kN', rc[0][1:3]==['8.33','10.00'] and rc[1][1:3]==['-8.33','10.00'], rc)
        # Wind rechtwinklig auf die linke Dachfläche, Zweigelenkrahmen (statisch unbestimmt): nur die Gleichgewichtsprobe ist von Hand sicher
        await pg.evaluate("frameLoads.horiz=[]; frameLoads.vert=[{id:902,enabled:true,values:{member:'rafter',qa:1,qb:1,a:0,b:5,rdir:'n'}}]; renderFrameLoads('vert'); renderFrameLoads('horiz'); applyFramePreset('two'); liveCalc(true)"); await pg.wait_for_timeout(500)
        rc=await pg.evaluate(REAC); K=await pg.evaluate("lastCalc.frame.knoten")
        sh=sum(float(x[1]) for x in rc); sv=sum(float(x[2]) for x in rc)
        check('Wind ⊥ linke Dachfläche: ΣH_Lager = −q·f = −2 kN, ΣV_Lager = q·5 = 5 kN', near(sh,-2,0.02) and near(sv,5,0.02), rc)
        check('Zweigelenkrahmen: First ohne Gelenk, Moment am First stetig (M32 = M34)', K['nodes'][2]['kind']=='first' and not K['nodes'][2]['gelenk'] and near(end(K,3,2)['M'],end(K,3,4)['M'],0.002), (end(K,3,2), end(K,3,4)))
        # Speichern, Entwurf, Bericht
        await pg.evaluate(SETUP % 'three'); await pg.wait_for_timeout(600)
        sdf=await pg.evaluate("buildSDF()")
        check('SDF: Geometrie mit Satteldach (f, xF) und Riegellänge im Verlauf', sdf['system']['geometry'].get('gable')=={'f':2,'xF':5} and near(sdf['plot']['Lraf'], 2*math.sqrt(29), 1e-3), (sdf['system']['geometry'], sdf['plot'].get('Lraf')))
        await pg.evaluate("k4Save(true)"); await pg.reload(); await pg.wait_for_timeout(900); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[document.getElementById('fGable').checked, fF.value, fXF.value, getComputedStyle(document.getElementById('gable-row')).display, document.querySelectorAll('#frame-svg .k-raf').length]")
        check('Neu laden: Satteldach mit f und xF wiederhergestellt', r[0] and r[1]=='2' and r[2]=='5' and r[3]!='none' and r[4]==1, r)
        await pg.evaluate("liveCalc(true)"); await pg.wait_for_timeout(500)
        g=await pg.evaluate("reportGeometry({type:'frame', geometry:lastCalc.frame.geometry})")
        check('Bericht: Geometrie nennt Satteldach mit f und xF', 'Satteldach' in g and 'f = 2' in g and 'x<sub>F</sub> = 5' in g, g)
        r=await pg.evaluate("(()=>{ const s=document.createElementNS('http://www.w3.org/2000/svg','svg'); document.body.appendChild(s); const p=lastCalc.frame.plot;"
            "renderFrameDiagram(p.b,p.h,p.allM,p.allQ,p.allN,p.NP,p.supA,p.supB,p.rafHingeIdx,p.hA,p.hB,p.fine,{target:{svg:s,mode:'M',idp:'t'},hinges:p.hinges,gable:p.gable}); const n=s.querySelectorAll('polyline').length; s.remove(); return n; })()")
        check('Bericht-Diagramm aus dem gespeicherten Verlauf: Riegel mit Knick', r>=1, r)
        # Breite ändern: mittiger First bleibt mittig
        await pg.evaluate("fB.value=12; fB.dispatchEvent(new Event('input'))")
        check('Breite 12 m: mittiger First wandert mit (xF = 6 m)', await pg.evaluate("fXF.value")=='6')
        await pg.evaluate("setRoof(false); liveCalc(true)"); await pg.wait_for_timeout(400)
        K=await pg.evaluate("lastCalc.frame.knoten")
        check('Zurück auf gerade: kein First-Knoten, Riegel wieder eine Linie', all(n['kind']!='first' for n in K['nodes']) and await pg.evaluate("document.querySelectorAll('#frame-svg .k-raf').length")==0)
        # Englisch
        await pg.evaluate("setCalcLang('en'); setRoof(true); liveCalc(true)"); await pg.wait_for_timeout(400)
        t=await pg.evaluate("document.getElementById('tab-frame').textContent")
        check('Englisch: „Gable roof“, „Rise f“, Knoten „Ridge“', 'Gable roof' in t and 'Rise f' in t and 'Ridge' in t, '')
        # Projekte: Schweißnaht am First anbieten
        src=open(os.path.join(HERE,'..','projekt.html'),encoding='utf-8').read()
        check('Projekte: Knotenmenü kennt den First (Schweißnaht an beiden Riegelenden)', "n.kind==='first'" in src and "kn_first:'First'" in src)
        src=open(os.path.join(HERE,'..','size.html'),encoding='utf-8').read()
        check('Bemessung: Riegellänge aus dem Polygonzug (P.Lraf)', 'L:P.Lraf ?? P.b' in src)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print(f"\n{'ALLE OK' if not fails else str(fails)+' FEHLER'}"); sys.exit(1 if fails else 0)
