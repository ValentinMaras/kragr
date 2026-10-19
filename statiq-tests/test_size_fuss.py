# statiq·size: gelenkiger Stützenfuß (EN 1993-1-8, 6.2.5) — wirksame Fläche unabhängig über ein Raster nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio, json, re
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:64}', str(info)[:160])
src=open(os.path.join(HERE,'..','size.html'),encoding='utf-8').read()
PROF={p[0]:p for p in json.loads(re.search(r'const PROFILE = (\[\[.*?\]\]);',src).group(1))}
FCK={'C20/25':20,'C25/30':25,'C30/37':30}
def ref(prof,B,L,t,fy,beton,Bf,Lf):
    _,h,b,tw,tf,*_ = PROF[prof]
    fcd=0.85*FCK[beton]/1.5; kj=min(Bf/B,Lf/L,3); fjd=2/3*kj*fcd; c=t*math.sqrt(fy/(3*fjd))
    # Raster: Punkt gehört zur wirksamen Fläche, wenn sein Abstand zum Profil (Gurte, Steg) ≤ c (Rechteck-Metrik) und er auf der Platte liegt
    n=1200; xs=(np.arange(n)+0.5)/n*B-B/2; ys=(np.arange(n)+0.5)/n*L-L/2; X,Y=np.meshgrid(xs,ys)
    def near(x0,x1,y0,y1): return (X>=x0-c)&(X<=x1+c)&(Y>=y0-c)&(Y<=y1+c)
    m = near(-b/2,b/2,h/2-tf,h/2) | near(-b/2,b/2,-h/2,-h/2+tf) | near(-tw/2,tw/2,-h/2+tf,h/2-tf)
    A=m.sum()*(B/n)*(L/n)
    return fjd,c,A,A*fjd/1000
CASES=[('HEB 200 auf 300×320×20, C25/30, Fundament 800×800','HEB 200',300,320,20,'S235',235,'C25/30',800,800),
       ('HEA 160 auf 220×220×15, C20/25, Fundament 400×500','HEA 160',220,220,15,'S235',235,'C20/25',400,500),
       ('IPE 300 auf 200×340×30 S355, C30/37','IPE 300',200,340,30,'S355',355,'C30/37',1000,1000)]
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('stahl'); setStMode('fuss')")
        for name,prof,B,L,t,st,fy,bet,Bf,Lf in CASES:
            await pg.evaluate(f"$('fp-reihe').value='{prof.split()[0]}'; fillFpProfile(); $('fp-prof').value='{prof}'; $('fp-B').value={B}; $('fp-L').value={L}; $('fp-t').value={t}; $('fp-st').value='{st}'; $('fp-beton').value='{bet}'; $('fp-fund').value='{Bf} x {Lf}'; run()")
            fjd,c,A,N=ref(prof,B,L,t,fy,bet,Bf,Lf)
            got=await pg.evaluate("[LAST.res.fjd, LAST.res.c, LAST.res.FA.A, LAST.res.NRd]")
            ok=abs(got[0]-fjd)<1e-9 and abs(got[1]-c)<1e-9 and abs(got[2]-A)/A<0.003
            check(f'{name}: A_eff = {A/100:.1f} cm², N_j,Rd = {N:.0f} kN', ok, f'App {got[2]/100:.1f} cm², {got[3]:.0f} kN, c = {got[1]:.1f}')
        await pg.evaluate("$('fp-N').value=5000; run()"); s=await pg.inner_text('#summary')
        check('N = 5000 kN → nicht erfüllt', 'nicht erfüllt' in s, s)
        await pg.evaluate("$('fp-N').value=200; $('fp-V').value=60; run()")
        check('V = 60 kN > 0,2·200 = 40 kN → Reibung reicht nicht', not await pg.evaluate("LAST.res.C.find(c=>c.id==='fpquer').ok"))
        await pg.evaluate("showReport()"); r=await pg.inner_text('#report')
        check('Bericht Stützenfuß', 'T-Stummel' in r and 'Fußplatte' in r)
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
