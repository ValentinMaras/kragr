# statiq·size v0.5.12: Längsbewehrung in zwei Lagen (Balken, Plattenbalken) — unabhängig nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
fyd=500/1.15; A=lambda ds: math.pi*ds*ds/4
def omega(mu):
    def st(t):
        ec = 3.5*t if t<=1 else 3.5; es = 25 if t<=1 else 25-(t-1)*(25-fyd/200)
        xi=ec/(ec+es); y=np.linspace(0,1,20001); e=ec*y; s=np.where(e<2,1-(1-e/2)**2,1.0)
        Ar=np.trapezoid(s,y); ka=1-np.trapezoid(s*y,y)/Ar
        return xi*Ar, xi*Ar*(1-ka*xi)
    lo,hi=1e-6,2
    for _ in range(60):
        m=(lo+hi)/2
        if st(m)[1]<mu: lo=m
        else: hi=m
    return st((lo+hi)/2)[0]
def tsolve(M, d, beff, hf, bw, fcd):
    def T(x):
        ec=min(3.5, 25*x/(d-x)); y=np.linspace(0,x,40001); e=ec*(1-y/x); bb=np.where(y<hf,beff,bw)
        s=np.where(e<2,1-(1-e/2)**2,1.0)*fcd*bb; Fc=np.trapezoid(s,y); return Fc, Fc*(d-np.trapezoid(s*y,y)/Fc)/1e6
    lo,hi=1e-3,0.6*d
    for _ in range(80):
        x=(lo+hi)/2
        if T(x)[1]<M: lo=x
        else: hi=x
    return T(x)[0]
# Expositionsklasse XC1: c_min,dur = 10, Δc_dev = 10 (DIN EN 1992-1-1/NA)
def geo(h, ds, dsw, n, m, dg):
    cnw=max(10,dsw,10)+10; cnl=max(10,ds,10)+10; cv=max(cnw, cnl-dsw)
    d1=h-cv-dsw-ds/2; av=max(ds, dg+5, 20); return cv, d1, av, d1-m/n*(ds+av)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('beton'); setTyp('balken'); $('in-expo').value='XC1'; $('in-beton').value='C30/37'; $('in-Ms').value=0; $('in-Mqp').value=0; run()")
        check('Standardfall: Automatik bleibt bei einer Lage', await pg.evaluate("LAST.res.G.m===0 && +$('in-nl2').value===0"), await pg.inner_text('#reinf-line'))
        # Handeingabe, Rechteck
        cases={'30/60, 6 Ø 20, davon 2 oben, d_g 16':(30,60,6,20,2,8,16,330),
               '30/70, 8 Ø 25, davon 3 oben, d_g 32':(30,70,8,25,3,10,32,560),
               '25/50, 5 Ø 16, davon 1 oben (Mitte)':(25,50,5,16,1,8,16,140),
               '40/80, 10 Ø 28, davon 4 oben':(40,80,10,28,4,12,16,1200)}
        for name,(b,h,n,ds,m,dsw,dg,M) in cases.items():
            await pg.evaluate(f"$('in-auto').checked=false; $('in-b').value={b}; $('in-h').value={h}; $('in-n').value={n}; $('in-ds').value={ds}; $('in-nl2').value={m}; $('in-dsw').value={dsw}; $('in-sw').value=15; $('in-dg').value='{dg}'; $('in-M').value={M}; $('in-V').value=100; $('in-n2').value=2; $('in-ds2').value=12; run()")
            cv,d1,av,d=geo(h*10,ds,dsw,n,m,dg)
            g=await pg.evaluate("[LAST.res.G.d, LAST.res.G.d1, LAST.res.G.av, LAST.res.C.find(c=>c.id==='biegung').eta, LAST.res.C.find(c=>c.id==='regeln').eta, !!LAST.res.DZ]")
            fcd=0.85*30/1.5; mu=M*1e6/(b*10*d*d*fcd); As=n*A(ds); Asmin=2.9*(b*10)*(h*10)**2/6/(500*0.9*d)
            etaB = None if g[5] else max(omega(mu)*b*10*d*fcd/fyd, Asmin)/As
            n1=n-m; a=(b*10-2*cv-2*dsw-n1*ds)/(n1-1); etaR=max(ds,dg+5,20)/a
            ok = abs(g[0]-d)<1e-9 and abs(g[1]-d1)<1e-9 and g[2]==av and abs(g[4]-etaR)<1e-9 and (etaB is None or abs(g[3]-etaB)<2e-4)
            check(f'Rechteck {name}', ok, f'd = {d:.1f} mm (d₁ = {d1:.1f}, a_v = {av}) · η Biegung = {g[3]:.4f}' + ('' if etaB is None else f' / ref {etaB:.4f}') + f' · η Abstand = {etaR:.3f}')
        # gleiche Fläche in einer Lage: kleinere Nutzhöhe → größere Ausnutzung
        await pg.evaluate("$('in-b').value=40; $('in-h').value=60; $('in-n').value=6; $('in-ds').value=20; $('in-dsw').value=8; $('in-dg').value='16'; $('in-M').value=380; $('in-nl2').value=0; run()")
        e1=await pg.evaluate("LAST.res.C.find(c=>c.id==='biegung').eta")
        await pg.evaluate("$('in-nl2').value=2; run()"); e2=await pg.evaluate("LAST.res.C.find(c=>c.id==='biegung').eta")
        check('Zweite Lage verringert d → Biegeausnutzung steigt', e2>e1, f'{e1:.4f} → {e2:.4f}')
        # Plattenbalken
        await pg.evaluate("setTyp('unterzug'); $('in-auto').checked=false; $('in-b').value=30; $('in-h').value=60; $('in-hf').value=18; $('in-b1').value=200; $('in-b2').value=200; $('in-l').value=8; $('in-feld').value=1; $('in-n').value=6; $('in-ds').value=25; $('in-nl2').value=2; $('in-dsw').value=10; $('in-sw').value=15; $('in-dg').value='16'; $('in-M').value=480; $('in-V').value=200; run()")
        cv,d1,av,d=geo(600,25,10,6,2,16)
        g=await pg.evaluate("[LAST.res.G.d, LAST.res.BF.beff, LAST.res.C.find(c=>c.id==='biegung').eta]")
        Fc=tsolve(480, d, g[1], 180, 300, 17.0); etaT=max(Fc/fyd, 0)/(6*A(25))
        check('Plattenbalken 6 Ø 25 (4 + 2): d und Biegung (T-Querschnitt)', abs(g[0]-d)<1e-9 and abs(g[2]-etaT)<3e-3, f'd = {d:.1f} mm, b_eff = {g[1]:.0f} mm, η = {g[2]:.4f} / ref {etaT:.4f}')
        # Automatik: eine Lage reicht nicht → zweite Lage
        await pg.evaluate("setTyp('balken'); $('in-auto').checked=true; $('in-b').value=25; $('in-h').value=60; $('in-M').value=420; $('in-V').value=150; $('in-dg').value='16'; run()")
        g=await pg.evaluate("[LAST.res.ok, LAST.res.R.n, LAST.res.R.nl2, LAST.res.R.ds, +$('in-nl2').value, $('in-nl2').disabled]")
        check('Automatik 25/60, M = 420 kNm: wählt zwei Lagen, alle Nachweise erfüllt', g[0] and g[2]>0 and g[4]==g[2] and g[5], g)
        # keine Ein-Lagen-Lösung möglich? Gegenprobe: jede Ein-Lagen-Variante mit gleicher oder kleinerer Fläche fällt durch
        alt=await pg.evaluate("""(()=>{ const I=readInput(), R=LAST.res.R, A0=R.n*areaBar(R.ds); let found=null;
          for(const ds of DS_L) for(let n=2;n<=8;n++){ if(n*areaBar(ds)>A0+1e-9) continue; const r={...R, ds, n, nl2:0}; stirrups({...I,Ms:0}, r); const res=nachweise({...I,Ms:0}, r);
            if(['biegung','regeln','riss','auflager'].every(id=>res.C.filter(c=>c.id===id).every(c=>c.ok))) found=[n,ds]; } return found; })()""")
        check('Gegenprobe: keine Ein-Lagen-Bewehrung mit ≤ Fläche erfüllt alles', alt is None, alt)
        # Validierung
        await pg.evaluate("$('in-auto').checked=false; $('in-n').value=4; $('in-nl2').value=3; run()")
        check('2. Lage mit mehr Stäben als die 1. Lage wird abgelehnt', '2. Lage' in await pg.inner_text('#summary'))
        await pg.evaluate("$('in-n').value=6; $('in-nl2').value=2; $('in-ds').value=20; run()")
        # Darstellung, Text, Bericht, Speichern
        g=await pg.evaluate("""(()=>{ const ys=[...document.querySelectorAll('#fig svg circle[fill="#111"]')].map(c=>+c.getAttribute('cy')); const c={}; ys.forEach(y=>c[y.toFixed(1)]=(c[y.toFixed(1)]||0)+1); return Object.values(c).sort(); })()""")
        check('Skizze: 4 Stäbe in der 1. Lage, 2 in der 2. Lage', 4 in g and 2 in g, g)
        check('Bewehrungszeile nennt beide Lagen', '(4 + 2 in zwei Lagen)' in await pg.inner_text('#reinf-line'))
        st=await pg.evaluate("LAST.res.C.find(c=>c.id==='deckung'||c.title.includes('Deckung'))?.steps.join(' ')||''")
        check('Rechenschritt erklärt d bis zum Schwerpunkt beider Lagen', 'Schwerpunkt beider Lagen' in st)
        await pg.evaluate("showReport()"); rp=await pg.inner_text('#report'); await pg.evaluate("document.body.classList.remove('show-report')")
        check('Bericht enthält die zwei Lagen', 'zwei Lagen' in rp)
        await pg.evaluate("save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden: 2. Lage bleibt erhalten', await pg.evaluate("$('in-nl2').value==='2' && LAST.res.G.m===2"))
        await pg.evaluate("setTyp('platte'); run()")
        check('Platte: 2. Lage ohne Wirkung', await pg.evaluate("!LAST.res.G.m"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
