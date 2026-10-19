# statiq·ref v0.3.13 Grundbau: Bodenphysik, Plastizität, Spannungen, Setzung (Steinbrenner gegen Boussinesq-Integration),
# Konsolidation, Mohr-Coulomb, Darcy/HYD, Coulomb (gegen Gleitkeil-Optimierung), geschichteter Erddruck, Sohldruck, Grundbruch, Böschung.
import os, sys, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
    from scipy.integrate import dblquad, quad
    from scipy.optimize import minimize_scalar
except ImportError:
    print('SKIP Playwright/scipy nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
de=lambda v,d=2: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
def has(t,v,d): t=t.replace('\n',' '); return de(v,d) in t or de(v,d) in t.replace('.','')
R=math.radians

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def go(t): await pg.goto(URL+'#/grundbau/'+t); await pg.wait_for_timeout(250)
        async def setv(prefix, vals, fn):
            await pg.evaluate("([p,v,fn])=>{ for(const [k,x] of Object.entries(v)) document.getElementById(p+k).value=String(x); window[fn](); }", [prefix, vals, fn]); await pg.wait_for_timeout(60)
        async def out(id): return await pg.evaluate(f"document.getElementById('{id}').innerText")
        # Bodenphysik
        await go('boden/phasen')
        m,md,V,rs=1985,1730,1000,2.65; w=(m-md)/md; rd=md/V; n=1-rd/rs; e=n/(1-n); Sr=w*rs/e; gr=((1-n)*rs+n)*9.81
        o=await out('bp-out'); ID=(0.75-e)/(0.30)
        check(f'Bodenphysik: w = {w*100:.1f} %, n = {n:.3f}, e = {e:.3f}, Sr = {Sr:.3f}, γr = {gr:.2f}, ID = {ID:.3f}', all(has(o,v,d) for v,d in [(w*100,1),(n,3),(e,3),(Sr,3),(gr,2),(ID,3)]), o[-100:])
        await setv('bp-', {'wL':45,'wP':22}, 'updatePhasen'); o=await out('bp-out'); Ic=(45-w*100)/23
        check(f'Konsistenzzahl I_C = {Ic:.3f} (halbfest)', has(o,Ic,3) and 'halbfest' in o)
        # Plastizität
        await go('boden/klassifikation')
        for wL,wP,g in [(42,20,'TM'),(30,25,'UL'),(60,30,'TA'),(60,40,'UA'),(28,12,'TL'),(55,35,'UA')]:
            await setv('pd-', {'wL':wL,'wP':wP}, 'updatePlast'); o=await out('pd-out')
            if f'Bodengruppe: {g}' not in o.replace('\n',' '): check(f'Plastizität wL={wL}, wP={wP} → {g}', False, o[-60:])
        check('Plastizitätsdiagramm: 6 Böden richtig eingeordnet (A-Linie 0,73·(wL − 20))', True)
        # Spannungen
        await go('verformung/spannungen'); o=await out('bs2-out')
        L=[(2,18,20),(3,19,21),(3,20,21)]; zw=2.5; q=10
        def sig(z):
            s=q; t=0
            for d,g,gr_ in L:
                a=min(z,t+d)
                if a>t: s+=max(0,min(a,zw)-t)*g+max(0,a-max(t,zw))*gr_
                t+=d
            return s
        pts=[0,2,2.5,5,8]; okk=all(has(o,sig(z),1) and has(o,sig(z)-max(0,z-zw)*10,1) for z in pts)
        check(f'Spannungen 3 Schichten, GW 2,5 m: σ′(8 m) = {sig(8)-55:.1f} kN/m²', okk, o[-120:])
        # Setzung: Steinbrenner gegen Boussinesq-Integration
        await go('verformung/setzung')
        Inum=lambda a,b,z: dblquad(lambda y,x: 3*z**3/(2*math.pi*(x*x+y*y+z*z)**2.5), 0,a, 0,b)[0]
        js=[await pg.evaluate(f"steinbrennerI({a},{b},{z})") for a,b,z in [(1,1.5,0.5),(1,1.5,2),(2,3,4),(0.5,0.5,3)]]
        nm=[Inum(a,b,z) for a,b,z in [(1,1.5,0.5),(1,1.5,2),(2,3,4),(0.5,0.5,3)]]
        check('Steinbrenner-Einflusswert = Integration der Boussinesq-Lösung (4 Punkte, ±0,1 %)', all(abs(a-b)<1e-3*max(b,1e-3) for a,b in zip(js,nm)), [round(x,5) for x in js])
        o=await out('st2-out'); a,b,d,s0,g,Es,dz=3,2,1,250,19,30,0.5; s1=s0-g*d; s=0; z=0
        while True:
            zm=z+dz/2; ds=s1*4*Inum(a/2,b/2,zm)
            if ds<0.2*g*(d+zm): break
            s+=ds*dz/(Es*1000); z+=dz
        check(f'Setzung 3 × 2 m, σ0 = 250, Es = 30: s = {s*1000:.1f} mm, Grenztiefe {z:.1f} m', has(o,s*1000,1) and has(o,z,1), o[-120:])
        # Konsolidation
        await go('verformung/konsolidation'); o=await out('ko-out')
        U=lambda T: 1-sum(2/((math.pi*(2*m+1)/2)**2)*math.exp(-((math.pi*(2*m+1)/2)**2)*T) for m in range(300))
        T=2.0*1/3**2
        check(f'Konsolidation cv = 2, H = 6 (beidseitig), t = 1 a: Tv = {T:.4f}, U = {U(T)*100:.1f} %, t90 = {0.848*9/2:.2f} a', has(o,T,4) and has(o,U(T)*100,1) and has(o,0.8481*9/2,2) or has(o,0.848*9/2,2))
        tv=await pg.evaluate("[0.5,0.9].map(TvonU)")
        check(f'Zeitfaktoren T50 = {tv[0]:.4f}, T90 = {tv[1]:.4f} (Tabelle 0,197 / 0,848)', abs(tv[0]-0.1967)<0.001 and abs(tv[1]-0.8481)<0.001)
        # Mohr-Coulomb: Gerade tangiert beide Kreise
        await go('boden/scherfestigkeit')
        r=await pg.evaluate("mohrCoulomb(50,190,150,480)")
        tg=math.tan(R(r['ph'])); dist=lambda pc,rad: abs(tg*pc - 0 + r['c'])/math.sqrt(1+tg*tg)-rad
        check(f"Mohr-Coulomb: φ′ = {r['ph']:.2f}°, c′ = {r['c']:.2f} — Bruchgerade berührt beide Kreise", abs(dist(120,70))<1e-6 and abs(dist(315,165))<1e-6)
        # Darcy / HYD
        await go('boden/grundwasser'); o=await out('da-out'); i=1.5/4
        check(f'Darcy: i = {i:.3f}, Q = {1e-4*i*10*3600:.3f} m³/h; HYD η = {10*i*1.35/(10*0.95):.3f}', has(o,i,3) and has(o,1e-4*i*10*3600,3) and has(o,10*i*1.35/(10*0.95),3))
        # Coulomb gegen Gleitkeil
        await go('erddruck/geschichtet')
        def wedge(phi,beta,delta):   # senkrechte Wand H = 1, γ = 1, Gelände unter β, Gleitfläche unter θ: E maximieren
            def E(th):
                t=R(th); x=1/(math.tan(t)-math.tan(R(beta))); G=0.5*x
                A=np.array([[math.cos(R(delta)), -math.sin(t)+math.tan(R(phi))*math.cos(t)],
                            [math.sin(R(delta)),  math.cos(t)+math.tan(R(phi))*math.sin(t)]])
                Ev,N=np.linalg.solve(A,[0,G]); return -Ev
            res=minimize_scalar(E, bounds=(beta+0.5,89.5), method='bounded', options={'xatol':1e-10}); return -res.fun*math.cos(R(delta))*2
        bad=[]
        for phi,b,dl in [(30,0,0),(30,10,20),(35,0,2/3*35),(27.5,15,0),(32.5,5,32.5/2)]:
            jk=await pg.evaluate(f"kagh({phi},0,{b},{dl})"); w_=wedge(phi,b,dl)
            if abs(jk-w_)>2e-4: bad.append((phi,b,round(dl,2),round(jk,5),round(w_,5)))
        check('Coulomb K_agh (α = 0) = Maximum über alle Gleitkeile (5 Fälle)', not bad, bad)
        kp=await pg.evaluate("kpgh(30,0,0)"); ka=await pg.evaluate("kagh(30,0,0,0)")
        check('Grenzfall Rankine: K_a = 1/3, K_p = 3 bei φ′ = 30°', abs(ka-1/3)<1e-12 and abs(kp-3)<1e-9)
        # geschichteter Erddruck
        o=await out('es-out')
        Ls=[(2.5,18,10,32.5,0),(3,19,10,25,10)]; zw=3; q=10; df=2/3
        def kag(phi,d): return kagh_py(phi,d)
        def kagh_py(phi,d):
            P,D=R(phi),R(d); r=math.sin(P+D)*math.sin(P)/math.cos(D); return math.cos(P)**2/(1+math.sqrt(r))**2
        def kac(phi,d): return 2*math.cos(R(phi))*math.cos(R(d))/(1+math.sin(R(phi+d)))
        def sv(z):
            s=q; t=0
            for d,g,gp,_,_ in Ls:
                a=min(z,t+d)
                if a>t: s+=max(0,min(a,zw)-t)*g+max(0,a-max(t,zw))*gp
                t+=d
            return s
        def ea(z, layer):
            d,g,gp,phi,c=Ls[layer]; return max(0, sv(z)*kag(phi,df*phi)-c*kac(phi,df*phi))
        E1=quad(lambda z: ea(z,0),0,2.5)[0]; E2=quad(lambda z: ea(z,1),2.5,5.5,points=[3])[0]
        M=quad(lambda z: ea(z,0)*(5.5-z),0,2.5)[0]+quad(lambda z: ea(z,1)*(5.5-z),2.5,5.5,points=[3])[0]
        W=0.5*10*2.5**2
        check(f'geschichteter Erddruck: E_ah = {E1+E2:.2f} kN/m in {M/(E1+E2):.2f} m, W = {W:.2f} kN/m', has(o,E1+E2,2) and has(o,M/(E1+E2),2) and has(o,W,2), o[-150:])
        # Sohldruck
        await go('flach/sohldruck'); o=await out('sd-out'); e=300/1200
        check(f'Sohldruck e = {e:.3f} m ≤ b/6: σmax = {1200/5*(1+6*e/2):.1f}, σmin = {1200/5*(1-6*e/2):.1f} kN/m²', has(o,1200/5*(1+6*e/2),1) and has(o,1200/5*(1-6*e/2),1))
        await setv('sd-', {'M':500}, 'updateSohldruck'); o=await out('sd-out'); e=500/1200; c=1-e
        check(f'klaffende Fuge e = {e:.3f}: σmax = 2V/(3ac) = {2*1200/(3*2.5*c):.1f} kN/m²', has(o,2*1200/(3*2.5*c),1) and 'Klaffende Fuge' in o)
        # Grundbruch DIN 4017 unabhängig
        await go('flach/grundbruch'); o=await out('gb-out')
        b,a,d,phi,c,g1,g2,V,H,e,Vd=2,3,1,32.5,0,18,19,1200,80,0.15,1700
        ph=R(phi); Nd0=math.tan(math.pi/4+ph/2)**2*math.exp(math.pi*math.tan(ph)); Nb0=(Nd0-1)*math.tan(ph); Nc0=(Nd0-1)/math.tan(ph)
        bp=b-2*e; ap=a; A=bp*ap; rr=bp/ap; vb=1-0.3*rr; vd=1+rr*math.sin(ph)
        m=(2+bp/ap)/(1+bp/ap); t=H/V; idd=(1-t)**m; ib=(1-t)**(m+1)
        s0=g2*bp*Nb0*vb*ib+g1*d*Nd0*vd*idd; Rk=A*s0
        check(f'Grundbruch 2 × 3 m, φ′ = 32,5°, H = 80, e = 0,15: R_n,k = {Rk:.1f} kN, η = {Vd/(Rk/1.4):.3f}', has(o,Rk,1) and has(o,Vd/(Rk/1.4),3), o[-120:])
        check('Tragfähigkeitsbeiwert N_d0(30°) = 18,40', abs(math.tan(math.pi/4+R(15))**2*math.exp(math.pi*math.tan(R(30)))-18.40)<0.01)
        # Böschung
        await go('boeschung/boeschung'); o=await out('bo-out')
        b_,phi,g,z=26.6,32.5,19,2; phd=math.atan(math.tan(R(phi))/1.25); tau=g*z*math.sin(R(b_))*math.cos(R(b_)); sn=g*z*math.cos(R(b_))**2
        mu=tau/(sn*math.tan(phd)); eta=math.tan(R(phi))/math.tan(R(b_))
        check(f'Böschung 1:2, trocken: μ = {mu:.3f}, η = tanφ/tanβ = {eta:.3f}', has(o,mu,3) and has(o,eta,3))
        await setv('bo-', {'w':'s'}, 'updateBoesch'); o=await out('bo-out'); eta2=10/20*math.tan(R(phi))/math.tan(R(b_))
        check(f'durchströmt: η = γ′/γr · tanφ/tanβ = {eta2:.3f} (etwa die Hälfte)', has(o,eta2,3))
        # alle Seiten
        T=['boden/kennwerte','boden/klassifikation','boden/phasen','boden/scherfestigkeit','boden/grundwasser','verformung/spannungen','verformung/setzung','verformung/konsolidation','erddruck/beiwerte','erddruck/geschichtet','flach/sohldruck','flach/grundbruch','flach/sohlwiderstand','boeschung/boeschung']
        await pg.set_viewport_size({'width':390,'height':844}); bad=[]
        for tp in T:
            await go(tp)
            r_=await pg.evaluate("[document.documentElement.scrollWidth, /NaN|undefined|Infinity/.test(document.getElementById('main').innerText)]")
            if r_[0]>390 or r_[1]: bad.append((tp,r_))
        check('14 Grundbau-Seiten: keine NaN, Handy ohne Querscrollen', not bad, bad)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
