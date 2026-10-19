# statiq·ref v0.3.12 Stahlbeton: hochfester Beton, kd-Tafel, Kriechen/Schwinden, Torsion, Rechenwege.
# Unabhängig: Tabellenwerte EN 1992-1-1 Tab. 3.1; Parabel-Rechteck numerisch integriert (numpy); Formeln Anhang B in Python.
import os, sys, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
    from scipy.optimize import brentq
except ImportError:
    print('SKIP Playwright/scipy nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
de=lambda v,d=2: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
def has(t,v,d): t=t.replace('\n',' '); return de(v,d) in t or de(v,d) in t.replace('.','')
fyd=500/1.15; fcd=lambda fck: 0.85*fck/1.5

# Parabel-Rechteck numerisch: Dehnungsebene mit ε_s = 25 ‰ bzw. ε_c = 3,5 ‰ (Bereiche wie im Lehrbuch)
def state_from_mu(mu):
    def st(ec, es):
        xi=ec/(ec+es); y=np.linspace(0,1,20001)   # y: 0 = Nulllinie, 1 = Druckrand (bezogen auf x)
        e=ec*y; s=np.where(e<2, 1-(1-e/2)**2, 1.0)
        aR=np.trapezoid(s,y); m1=np.trapezoid(s*y,y); ka=1-m1/aR   # Schwerpunkt vom Druckrand: (1 − m1/aR)·x
        return xi, aR*xi, 1-ka*xi
    def f(t):
        ec,es=(3.5*t,25.0) if t<=1 else (3.5, 25-(t-1)*(25-fyd/200))
        xi,om,ze=st(ec,es); return om*ze-mu, xi, om, ze
    t=brentq(lambda t: f(t)[0], 1e-6, 2); _,xi,om,ze=f(t); return xi,om,ze

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        # Hochfester Beton gegen EN 1992-1-1 Tab. 3.1
        await pg.goto(URL+'#/stahlbeton/baustoffe/beton'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.getElementById('main').innerText")
        TAB={'C55/67':('4,2','3,0','38','2,20','3,13','1,75'),'C60/75':('4,4','3,1','39','2,29','2,88','1,59'),'C70/85':('4,6','3,2','41','2,42','2,66','1,44'),
             'C80/95':('4,8','3,4','42','2,52','2,60','1,40'),'C90/105':('5,0','3,5','44','2,60','2,60','1,40')}
        bad=[k for k,v in TAB.items() if not all(x in t.split(k,1)[1][:80] for x in v)]
        check('Hochfester Beton C55 … C90: f_ctm, f_ctk, E_cm, ε_c2, ε_cu2, n wie Tab. 3.1', not bad, bad)
        # kd-Tafel
        await pg.goto(URL+'#/stahlbeton/bemessung/kd'); await pg.wait_for_timeout(300)
        rows=await pg.evaluate("[...document.querySelectorAll('.data-table-wrap.tall tbody tr')].map(r=>[...r.cells].map(c=>c.textContent))")
        bad=[]
        for i,r in enumerate(rows):
            mu=(i+1)/100; xi,om,ze=state_from_mu(mu)
            for j,fck in enumerate([20,25,30,35,40,45,50]):
                if r[j]!=de(math.sqrt(10/(mu*fcd(fck))),2): bad.append((mu,fck,r[j]))
            ks=1000/(ze*fyd)
            if abs(float(r[7].replace(',','.'))-ks)>0.006 or abs(float(r[8].replace(',','.'))-xi)>0.0015 or abs(float(r[9].replace(',','.'))-ze)>0.0015: bad.append((mu,'ks/ξ/ζ',r[7:10],round(ks,3),round(xi,3),round(ze,3)))
        check(f'kd-Tafel: {len(rows)} Zeilen, kd für C20 … C50 und ks, ξ, ζ gegen numerische Integration', len(rows)==29 and not bad, bad[:3])
        check('kd-Tafel: kleinster ks = 2,32 (wie in den üblichen Tafeln)', rows[0][7]=='2,32')
        o=(await pg.evaluate("document.getElementById('kd-out').innerText")).replace('\n',' ')
        kd=45/math.sqrt(180/0.3); mu=10/(kd*kd*fcd(25)); xi,om,ze=state_from_mu(mu); As=1000/(ze*fyd)*180/45
        check(f'kd-Rechner C25/30, b = 0,30 m, d = 45 cm, M = 180: kd = {kd:.3f}, As = {As:.2f} cm² (= ω-Verfahren {om*30*45*fcd(25)/fyd:.2f})', has(o,kd,3) and (has(o,As,2) or has(o,As+0.01,2) or has(o,As-0.01,2)), o[-80:])
        # Kriechen und Schwinden
        await pg.goto(URL+'#/stahlbeton/baustoffe/kriechen'); await pg.wait_for_timeout(300)
        def kriech(fck,b,h,s,RH,t0,z):
            fcm=fck+8; Ac=b*h; u={'platte':2*b,'alle':2*(b+h),'drei':2*h+b}[s]; h0=2*Ac/u
            a={'S':-1,'N':0,'R':1}[z]; ds1={'S':3,'N':4,'R':6}[z]; ds2={'S':0.13,'N':0.12,'R':0.11}[z]
            phiRH = 1+(1-RH/100)/(0.1*h0**(1/3)) if fcm<=35 else (1+(1-RH/100)/(0.1*h0**(1/3))*(35/fcm)**0.7)*(35/fcm)**0.2
            t0a=max(0.5, t0*(9/(2+t0**1.2)+1)**a); phi=phiRH*16.8/math.sqrt(fcm)/(0.1+t0a**0.2)
            kh=float(np.interp(h0,[100,200,300,500],[1,0.85,0.75,0.7]))
            ecd=kh*0.85*(220+110*ds1)*math.exp(-ds2*fcm/10)*1e-6*1.55*(1-(RH/100)**3); eca=2.5*(fck-10)*1e-6
            return h0,phi,ecd+eca
        cases=[('C30/37',30,1000,200,'platte',50,28,'N'),('C20/25',20,300,300,'alle',80,7,'S'),('C40/50',40,400,600,'drei',60,3,'R'),('C25/30',25,1000,160,'platte',70,14,'N')]
        for name,fck,b,h,sd,RH,t0,z in cases:
            await pg.evaluate(f"(()=>{{ const v={{c:'{name}',b:{b},h:{h},s:'{sd}',RH:{RH},t0:{t0},z:'{z}'}}; for(const [k,x] of Object.entries(v)) document.getElementById('ks-'+k).value=String(x); updateKS(); }})()")
            o=await pg.evaluate("document.getElementById('ks-out').innerText")
            h0,phi,ecs=kriech(fck,b,h,sd,RH,t0,z)
            check(f'Kriechen {name} h0 = {h0:.1f} mm, RH {RH} %, t0 = {t0} d, {z}: φ = {phi:.2f}, εcs = {ecs*1000:.3f} ‰', has(o,h0,1) and has(o,phi,2) and has(o,ecs*1000,3), o[-120:].replace('\n',' '))
        check('Plausibilität: Innenbauteil C30/37, h0 = 200, t0 = 28 → φ ≈ 2,4 (Nomogramm Bild 3.1)', abs(kriech(30,1000,200,'platte',50,28,'N')[1]-2.4)<0.15)
        # Torsion
        await pg.goto(URL+'#/stahlbeton/bemessung/torsion'); await pg.wait_for_timeout(300)
        o=await pg.evaluate("document.getElementById('to-out').innerText")
        b,h,c,T,V,cot,fck=300,600,50,25,150,1.0,30
        tef=max(b*h/(2*(b+h)),2*c); Ak=(b-tef)*(h-tef); uk=2*((b-tef)+(h-tef)); nu=0.525*min(1.1-fck/500,1); th=math.atan(1/cot)
        TR=2*nu*fcd(fck)*Ak*tef*math.sin(th)*math.cos(th)/1e6; VR=b*0.9*(h-c)*0.75*min(1.1-fck/500,1)*fcd(fck)/(cot+1/cot)/1000
        asw=T*1e6/(2*Ak*fyd*cot)*10; Asl=T*1e6*uk*cot/(2*Ak*fyd)/100
        check(f'Torsion 30/60 C30/37, T = 25, V = 150: T_Rd,max = {TR:.1f}, Interaktion {(T/TR)**2+(V/VR)**2:.3f}, a_sw = {asw:.2f}, A_sl = {Asl:.2f}',
              has(o,TR,1) and has(o,(T/TR)**2+(V/VR)**2,3) and has(o,asw,2) and has(o,Asl,2), o[-150:].replace('\n',' '))
        # Rechenwege: alle Stahlbeton-Rechner zeigen nummerierte Schritte
        T=['dauerhaftigkeit/deckung','bemessung/biegung','bemessung/querkraft','bewehrung/verankerung','gzg/schlankheit','bemessung/plattenbalken','bemessung/durchstanzen','gzg/rissbreite','stuetzen/bemessung','baustoffe/kriechen','bemessung/kd','bemessung/torsion']
        bad=[]
        for tp in T:
            await pg.goto(URL+'#/stahlbeton/'+tp); await pg.wait_for_timeout(200)
            n=await pg.evaluate("document.querySelectorAll('.calc-out .ablauf .st').length")
            if n<2: bad.append((tp,n))
        check('12 Stahlbeton-Rechner mit Rechenweg in Schritten', not bad, bad)
        # Querkraft: Rechenweg nennt V_Rd,c und V_Rd,max mit Zwischenwerten
        await pg.goto(URL+'#/stahlbeton/bemessung/querkraft'); await pg.wait_for_timeout(200)
        o=(await pg.evaluate("document.getElementById('qk-out').innerText")).replace('\n',' ')
        d=550; k=min(1+math.sqrt(200/d),2); rho=min(1257/(300*d),0.02)
        check(f'Querkraft: k = {k:.3f}, ρl = {rho*100:.3f} % im Rechenweg', has(o,k,3) and has(o,rho*100,3))
        # mobil
        await pg.set_viewport_size({'width':390,'height':844}); bad=[]
        for tp in T+['bewehrung/matten','baustoffe/beton']:
            await pg.goto(URL+'#/stahlbeton/'+tp); await pg.wait_for_timeout(150)
            r=await pg.evaluate("[document.documentElement.scrollWidth, /NaN|undefined|Infinity/.test(document.getElementById('main').innerText)]")
            if r[0]>390 or r[1]: bad.append((tp,r))
        check('14 Stahlbeton-Seiten: keine NaN, Handy ohne Querscrollen', not bad, bad)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
