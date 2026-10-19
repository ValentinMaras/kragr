# statiq·size: Schweißverbindungen (EN 1993-1-8, 4.5.3.2 richtungsbezogen) — unabhängig nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio, json, re
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
src=open(os.path.join(HERE,'..','size.html'),encoding='utf-8').read()
PROF={p[0]:p for p in json.loads(re.search(r'const PROFILE = (\[\[.*?\]\]);',src).group(1))}
FU={'S235':360,'S275':430,'S355':490,'S460':540}; BW={'S235':0.8,'S275':0.85,'S355':0.9,'S460':1.0}; FY={'S235':235,'S275':275,'S355':355,'S460':460}
g2=1.25
def punkt(sw,tl,fu,bw):
    s=abs(sw)/math.sqrt(2); v=math.sqrt(s*s+3*(s*s+tl*tl)); return max(v/(fu/(bw*g2)), s/(0.9*fu/g2))
def stirn(prof,st,af,aw,N,V,M):
    _,h,b,tw,tf,r,*_=PROF[prof]; fu,bw=FU[st],BW[st]
    li=b-tw-2*r
    if li/2 < max(30,6*af): li=0
    zo=h/2+af/2; zi=h/2-tf-af/2; lw=h-2*tf-2*r
    Aw=2*af*(b+li)+2*aw*lw; Iw=2*af*(b*zo**2+li*zi**2)+2*aw*lw**3/12; As=2*aw*lw
    sig=lambda z: N*1e3/Aw+M*1e6*z/Iw
    sA=max(sig(zo),sig(-zo),key=abs); sB=max(sig(lw/2),sig(-lw/2),key=abs); tau=V*1e3/As
    return dict(Aw=Aw,Iw=Iw,eA=punkt(sA,0,fu,bw),eB=punkt(sB,tau,fu,bw))
def lasche(st,b,t,a,l,front,F):
    fu,bw=FU[st],BW[st]; lf=b if front else 0
    bL=min(1,1.2-0.2*l/(150*a)) if l>150*a else 1
    fT=min(fu/(math.sqrt(2)*bw*g2), math.sqrt(2)*0.9*fu/g2); fL=fu/(math.sqrt(3)*bw*g2)
    FRd=(a*lf*fT+2*a*l*bL*fL)/1000; Npl=b*t*FY[st]/1000
    return dict(FRd=FRd, eta=F/FRd, Npl=Npl)
def konsole(st,t,l,a,e,F):
    fu,bw=FU[st],BW[st]; sw=F*e*1e3/(2*a*l*l/6); tw=F*1e3/(2*a*l)
    return dict(sw=sw, eta=punkt(sw,tw,fu,bw))
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('stahl'); setStMode('schweiss')")
        s=await pg.inner_text('#summary'); check('Standardfall Stirnplatte erfüllt', 'Alle Nachweise erfüllt' in s, s)
        # Handrechnung IPE 300, a_f = 7, a_w = 4, M = 110 kNm: σ_w außen = 110e6·153,5/I_w
        R=stirn('IPE 300','S235',7,4,0,120,110)
        g=await pg.evaluate("[LAST.res.Aw, LAST.res.Iw, LAST.res.sA]")
        check('IPE 300: A_w, I_w und σ_w außen wie Handrechnung', abs(g[0]-R['Aw'])<1e-6 and abs(g[1]-R['Iw'])<1e-3 and abs(g[2]-110e6*153.5/R['Iw'])<1e-6, f"A_w = {R['Aw']/100:.2f} cm², I_w = {R['Iw']/1e4:.0f} cm⁴, σ = {g[2]:.1f}")
        for name,(prof,reihe,st,af,aw,N,V,M) in {'HEB 240 S355, N + M + V':('HEB 240','HEB','S355',6,4,150,200,160),
                                                   'HEA 200 S235, Druck und negatives Moment':('HEA 200','HEA','S235',5,4,-80,60,-45),
                                                   'IPE 160, innere Gurtnähte zu kurz (nicht angesetzt)':('IPE 160','IPE','S235',6,3,0,30,12)}.items():
            await pg.evaluate(f"$('sw-fall').value='stirn'; $('sw-reihe').value='{reihe}'; fillSwProfile(); $('sw-prof').value='{prof}'; $('sw-st').value='{st}'; $('sw-af').value={af}; $('sw-aw').value={aw}; $('sw-N').value={N}; $('sw-V').value={V}; $('sw-M').value={M}; run()")
            R=stirn(prof,st,af,aw,N,V,M); g=await pg.evaluate("[LAST.res.C.find(c=>c.id==='swgurt').eta, LAST.res.C.find(c=>c.id==='swsteg').eta, LAST.res.li]")
            check(f'Stirnplatte {name}', abs(g[0]-R['eA'])<1e-9 and abs(g[1]-R['eB'])<1e-9, f"η Gurt {R['eA']:.3f}, Steg {R['eB']:.3f}, l_i = {g[2]:.1f}")
        for name,(st,b,t,tk,a,l,front,F) in {'120×10, Flanken 2×120 + Stirn, S235':('S235',120,10,12,4,120,True,250),
                                             'nur Flankennähte 2×200, S355':('S355',150,12,12,5,200,False,300),
                                             'lange Flankennähte l > 150a (β_Lw)':('S235',100,10,10,3,600,False,250)}.items():
            await pg.evaluate(f"$('sw-fall').value='lasche'; $('sw-st').value='{st}'; $('sw-b').value={b}; $('sw-t').value={t}; $('sw-tk').value={tk}; $('sw-a').value={a}; $('sw-l').value={l}; $('sw-front').checked={str(front).lower()}; $('sw-F').value={F}; run()")
            R=lasche(st,b,t,a,l,front,F); g=await pg.evaluate("[LAST.res.FRd, LAST.res.Npl, LAST.res.bLw]")
            check(f'Lasche {name}', abs(g[0]-R['FRd'])<1e-9 and abs(g[1]-R['Npl'])<1e-9, f"F_w,Rd = {R['FRd']:.1f} kN, N_pl = {R['Npl']:.0f} kN, β_Lw = {g[2]:.3f}")
        # Stirnnähte tragen das 1,22-fache (√3/√2) der Flankennähte
        r=await pg.evaluate("LAST.res.fT/LAST.res.fL"); check('Stirn-/Flankennaht = √(3/2) = 1,225', abs(r-math.sqrt(1.5))<1e-9, f'{r:.4f}')
        for name,(st,t,l,a,e,F) in {'S235, 200 × 15, a = 5, e = 150, F = 90':('S235',15,200,5,150,90),
                                    'S355, 300 × 20, a = 6, e = 250, F = 160':('S355',20,300,6,250,160)}.items():
            await pg.evaluate(f"$('sw-fall').value='konsole'; $('sw-st').value='{st}'; $('sw-kt').value={t}; $('sw-kl').value={l}; $('sw-ka').value={a}; $('sw-ke').value={e}; $('sw-kF').value={F}; run()")
            R=konsole(st,t,l,a,e,F); g=await pg.evaluate("[LAST.res.sw, LAST.res.C.find(c=>c.id==='swnaht').eta]")
            check(f'Konsole {name}', abs(g[0]-R['sw'])<1e-9 and abs(g[1]-R['eta'])<1e-9, f"σ_w = {R['sw']:.1f}, η = {R['eta']:.3f}")
        await pg.evaluate("$('sw-kF').value=400; run()"); s=await pg.inner_text('#summary')
        check('Konsole überlastet → nicht erfüllt', 'nicht erfüllt' in s, s)
        await pg.evaluate("$('sw-fall').value='stirn'; $('sw-aw').value=2.5; run()")
        check('a_w = 2,5 mm < 3 mm → konstruktiv nicht erfüllt', not await pg.evaluate("LAST.res.C.find(c=>c.id==='swkon').ok"))
        await pg.evaluate("showReport()"); r=await pg.inner_text('#report')
        check('Bericht Schweißverbindung', 'richtungsbezogen' in r and 'Gurtnaht' in r, r[:80])
        await pg.evaluate("$('sw-fall').value='lasche'; $('sw-l').value=135; run(); save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden stellt Schweißnaht wieder her', await pg.evaluate("STMODE==='schweiss' && $('sw-fall').value==='lasche' && $('sw-l').value==='135' && LAST.mat==='schweiss'"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
