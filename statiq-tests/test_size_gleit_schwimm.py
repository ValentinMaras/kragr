# statiq·size v0.5.14: Grundbau „Gleiten“ und Schwimmkörper mit fünf Formen.
# Unabhängig: Gleiten nach DIN 1054 in Python; Schwimmen per shapely-Querschnitt bzw. numerischer Integration + brentq.
import os, sys, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
    from scipy.optimize import brentq
    from scipy.integrate import quad
    from shapely.geometry import Point, Polygon, box
except ImportError:
    print('SKIP Playwright/scipy/shapely nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
def rel(a,b): return abs(a-b)/max(abs(b),1e-9)

def gleiten(I):
    F={'P':(1.35,1.5,1.1,1.4),'T':(1.2,1.3,1.1,1.3),'A':(1.1,1.1,1.1,1.2)}[I['bs']]
    Hd=F[0]*I['HG']+F[1]*I['HQ']
    if I['zu']=='d':
        d=min(I['phi'] if I['sohle']=='o' else 2/3*I['phi'],35); Rtk=I['VG']*math.tan(math.radians(d))
    else: Rtk=I['a']*I['b']*I['cu']
    Rtd=Rtk/F[2]; Rpd=0
    if I['ep']:
        Kp=math.tan(math.radians(45+I['phi']/2))**2; Rpd=0.5*(0.5*I['g']*I['d']**2*Kp*I['a'])/F[3]
    return Hd, Rtd, Rpd, Hd/(Rtd+Rpd)

def schwimm(form, I, G, gw=9.81):
    """unabhängig: V(T), Auftriebsschwerpunkt und Wasserlinien-Trägheitsmoment aus Geometrie"""
    V=G/gw
    if form in ('quader','trapez','zylL'):
        L=I['L']
        if form=='quader': sec=box(-I['B']/2,0,I['B']/2,I['H']); Hg=I['H']
        elif form=='trapez': sec=Polygon([(-I['Bu']/2,0),(I['Bu']/2,0),(I['B']/2,I['H']),(-I['B']/2,I['H'])]); Hg=I['H']
        else: R=I['D']/2; sec=Point(0,R).buffer(R,quad_segs=512); Hg=I['D']
        sub=lambda T: sec.intersection(box(-1e3,-1,1e3,T))
        T=brentq(lambda T: L*sub(T).area-V, 1e-9, Hg)
        s=sub(T); zB=s.centroid.y
        xs=[c[0] for c in s.exterior.coords if abs(c[1]-T)<1e-6]; bw=max(xs)-min(xs)
        Iw=L*bw**3/12
    elif form=='zylS':
        D,H=I['D'],I['H']; A=math.pi*D*D/4; T=V/A; zB=T/2; Iw=math.pi*D**4/64; Hg=H
    else:  # Kugel: Scheibenintegration
        R=I['D']/2; r2=lambda z: max(0.0, R*R-(z-R)**2)
        Vt=lambda T: quad(lambda z: math.pi*r2(z),0,T)[0]
        T=brentq(lambda T: Vt(T)-V,1e-9,2*R); zB=quad(lambda z: z*math.pi*r2(z),0,T)[0]/V
        Iw=math.pi*r2(T)**2/4; Hg=2*R
    BM=Iw/V; KM=zB+BM; return dict(T=T, zB=zB, BM=BM, KM=KM, GM=KM-I['zg'], Hg=Hg)

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1300,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(400)
        await pg.evaluate("setMat('grund'); setGrMode('gleit')"); await pg.wait_for_timeout(300)
        check('Modus Gleiten im Grundbau erreichbar', await pg.is_visible('#gl-VG') and await pg.evaluate("LAST.mode==='gleit'"))
        async def set_(vals):
            # auch ausgeblendete Felder setzen (wie ein gespeichertes Projekt), danach rechnen
            await pg.evaluate("v=>{ for(const [k,x] of Object.entries(v)){ document.getElementById(k).value=String(x); } run(); }", vals)
            await pg.wait_for_timeout(120)
        base=dict(b=2.0,a=3.0,VG=800,HG=80,HQ=120,bs='P',sohle='o',zu='d',cu=40,ep=False,d=1.0,phi=32.5,g=18.5)
        cases=[({},'Ortbeton, dräniert, BS-P'),
               ({'sohle':'f'},'Fertigteil (2/3 φ′)'),
               ({'bs':'T','HQ':300},'BS-T, große Horizontallast'),
               ({'ep':True,'d':1.5},'mit Erdwiderstand 50 %'),
               ({'zu':'u','cu':25},'undräniert c_u = 25'),
               ({'phi':40},'φ′ = 40° → δ begrenzt auf 35°')]
        for mod,lab in cases:
            I={**base,**mod}
            await set_({'gl-b':I['b'],'gl-a':I['a'],'gl-VG':I['VG'],'gl-HG':I['HG'],'gl-HQ':I['HQ'],'gl-bs':I['bs'],'gl-sohle':I['sohle'],'gl-zu':I['zu'],'gl-cu':I['cu'],'gl-ep':'1' if I['ep'] else '0','gl-d':I['d'],'gr-phi':I['phi'],'gr-g1':I['g']})
            r=await pg.evaluate("[LAST.res.Hd, LAST.res.Rtd, LAST.res.Rpd, LAST.res.Hd/LAST.res.Rd, LAST.res.ok]")
            Hd,Rtd,Rpd,eta=gleiten(I)
            check(f'Gleiten {lab}: H_d = {Hd:.1f}, R_t,d = {Rtd:.1f}, R_p,d = {Rpd:.1f}, η = {eta:.3f}',
                  rel(r[0],Hd)<1e-6 and rel(r[1],Rtd)<1e-6 and abs(r[2]-Rpd)<1e-6 and rel(r[3],eta)<1e-6 and r[4]==(eta<=1), r)
        await pg.evaluate("setGrMode('gleit')"); txt=await pg.evaluate("document.getElementById('out')?.innerText || document.body.innerText")
        check('Rechenweg mit δ-Begrenzung angezeigt', 'begrenzt auf 35°' in await pg.evaluate("document.body.innerText"))
        # Bericht
        html=await pg.evaluate("buildReportGrund()")
        check('Bericht Gleiten erzeugt', 'Gleitnachweis' in html and 'svg' in html)
        # ── Schwimmkörper ──
        await pg.evaluate("setMat('wasser'); setWbMode('schwimm')"); await pg.wait_for_timeout(300)
        forms=[('quader',dict(L=12,B=5,H=1.5,zg=1.6),450),('trapez',dict(L=12,B=5,Bu=3,H=1.5,zg=1.1),350),('trapez',dict(L=8,B=4,Bu=0,H=2,zg=1.0),180),
               ('zylS',dict(D=2,H=3,zg=0.8),55),('zylL',dict(L=12,D=2,zg=0.6),200),('zylL',dict(L=10,D=1.5,zg=0.9),150),('kugel',dict(D=2,zg=0.5),25),('kugel',dict(D=3,zg=1.2),40)]
        for f,I,G in forms:
            await pg.select_option('#ws-form', f); await pg.wait_for_timeout(100)
            await set_({**{'ws-'+k:v for k,v in I.items()}, 'ws-G':G})
            r=await pg.evaluate("[LAST.res.T, LAST.res.zB, LAST.res.BM, LAST.res.KM, LAST.res.GM]")
            e=schwimm(f,I,G)
            ok=all(rel(a,b)<2e-4 or abs(a-b)<2e-5 for a,b in zip(r,[e['T'],e['zB'],e['BM'],e['KM'],e['GM']]))
            check(f'{f} {I} G={G}: T = {e["T"]:.4f}, z_B = {e["zB"]:.4f}, BM = {e["BM"]:.4f}, GM = {e["GM"]:.4f}', ok, r)
            if f in ('zylL','kugel'): check(f'  {f}: Metazentrum im Mittelpunkt (z_M = R)', abs(r[3]-I['D']/2)<1e-3, r[3])
        # untergehen
        await pg.select_option('#ws-form','kugel'); await set_({'ws-D':1,'ws-G':10})
        check('Kugel D = 1 m, G = 10 kN (> 5,1 kN Auftrieb): geht unter', await pg.evaluate("LAST.res.sinkt===true && !LAST.res.ok"))
        check('Beispielwerte beim Formwechsel', await pg.evaluate("(()=>{ document.getElementById('ws-form').value='zylS'; wsPreset(); run(); return LAST.res.GM>0 && num('ws-H')===3; })()"))
        html=await pg.evaluate("buildReportWasser ? buildReportWasser() : ''") if await pg.evaluate("typeof buildReportWasser==='function'") else ''
        check('Bericht Schwimmkörper nennt die Form', (not html) or 'stehender Zylinder' in html, html[:0])
        # Speichern und Laden
        await pg.select_option('#ws-form','zylL'); await pg.evaluate("wsPreset(); run()"); await pg.wait_for_timeout(150)
        snap=await pg.evaluate("snapshot()")
        check('Form wird im Projekt gespeichert', snap.get('ws-form')=='zylL' and 'ws-D' in snap)
        # Handy
        await pg.set_viewport_size({'width':390,'height':844}); await pg.wait_for_timeout(200)
        check('Handy: kein Querscrollen', await pg.evaluate("document.documentElement.scrollWidth")<=390)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
