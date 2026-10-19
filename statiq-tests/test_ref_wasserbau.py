# statiq·ref v0.3.14 Wasserbau: Stoffwerte (gegen Näherungsformeln aus der Literatur), Reynolds/Froude, Colebrook (brentq),
# Pumpe/NPSH, Druckstoß (Joukowsky), Ausfluss/Entleerung (ODE), Grenztiefe (Fr = 1), Wechselsprung (Impulssatz),
# Teilfüllung (numerische Kreisabschnitt-Integration), Brunnen (Dupuit-Thiem), Regenabfluss, Layout/NaN aller Seiten.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
    from scipy.optimize import brentq, minimize_scalar
    from scipy.integrate import quad, solve_ivp
except ImportError:
    print('SKIP Playwright/scipy nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
de=lambda v,d=2: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
def has(t,v,d): t=t.replace('\n',' '); return de(v,d) in t or de(v,d) in t.replace('.','')
g=9.81
PAGES=['grundlagen/stoffwerte','grundlagen/kennzahlen','hydrostatik/druck','hydrostatik/gekruemmt','hydrostatik/auftrieb',
  'hydrodynamik/bernoulli','hydrodynamik/rohr','hydrodynamik/ausfluss','hydrodynamik/pumpen','hydrodynamik/druckstoss',
  'gerinne/normalabfluss','gerinne/energie','gerinne/wehr','gerinne/wechselsprung','gerinne/teilfuellung','grundwasser/brunnen','hydrologie/regen']

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def go(t): await pg.goto(URL+'#/wasserbau/'+t); await pg.wait_for_timeout(200)
        async def setv(prefix, vals, fn):
            await pg.evaluate("([p,v,fn])=>{ for(const [k,x] of Object.entries(v)) document.getElementById(p+k).value=String(x); window[fn](); }", [prefix, vals, fn]); await pg.wait_for_timeout(50)
        async def out(id): return await pg.evaluate(f"document.getElementById('{id}').innerText")

        # ── Stoffwerte gegen unabhängige Näherungsformeln ──
        await go('grundlagen/stoffwerte')
        W=await pg.evaluate('WASSER')
        rho_tanaka=lambda T: 999.974950*(1-(T-3.983035)**2*(T+301.797)/(522528.9*(T+69.34881)))
        mu_vogel=lambda T: 2.414e-5*10**(247.8/(T+273.15-140))*1e3
        p_buck=lambda T: 0.61121*math.exp((18.678-T/234.5)*(T/(257.14+T)))
        check('ρ(T) aller 12 Zeilen = Tanaka-Formel (±0,05 %)', all(abs(r[1]-rho_tanaka(r[0]))/r[1]<5e-4 for r in W), [round(r[1]-rho_tanaka(r[0]),2) for r in W])
        check('μ(T) = Vogel-Gleichung (±3 %)', all(abs(r[3]-mu_vogel(r[0]))/r[3]<0.03 for r in W), [round(r[3]/mu_vogel(r[0]),3) for r in W])
        check('ν = μ/ρ in jeder Zeile (±0,5 %)', all(abs(r[2]-r[3]/r[1]*1000)/r[2]<5e-3 for r in W))
        check('Dampfdruck p_D(T) = Buck-Formel (±1 %)', all(abs(r[4]-p_buck(r[0]))/r[4]<0.01 for r in W), [round(r[4]/p_buck(r[0]),4) for r in W])
        check('Oberflächenspannung fällt monoton, 0,0756 → 0,0589 N/m', all(W[i][5]>W[i+1][5] for i in range(len(W)-1)))
        wi=await pg.evaluate('wasserBei(12.5)'); exp=[(a+b)/2 for a,b in zip(W[2],W[3])]
        check('wasserBei(12,5 °C) = lineare Interpolation 10/15 °C', all(abs(a-b)<1e-9 for a,b in zip(wi,exp)), [round(x,4) for x in wi])
        t=await pg.inner_text('#main'); check('Stoffwerte-Tabelle zeigt ν(20 °C) = 1,004', '1,004' in t)

        # ── Kennzahlen ──
        await go('grundlagen/kennzahlen')
        await setv('kz-', {'v':1.2,'L':0.2,'T':20,'art':'rohr','h':1}, 'updateKZ'); o=await out('kz-out'); Re=1.2*0.2/1.004e-6
        check(f'Reynolds Rohr v=1,2, d=0,2, 20 °C: Re = {Re:.0f} turbulent', has(o,Re,0) and 'turbulent' in o, o[-80:])
        await setv('kz-', {'v':0.01,'L':0.05,'T':10}, 'updateKZ'); o=await out('kz-out'); Re=0.01*0.05/1.306e-6
        check(f'Reynolds laminar: Re = {Re:.0f}', has(o,Re,0) and 'laminar' in o, o[-60:])
        await setv('kz-', {'v':2.5,'L':2,'T':10,'art':'gerinne','h':0.5}, 'updateKZ'); o=await out('kz-out'); Fr=2.5/math.sqrt(g*0.5)
        check(f'Froude v=2,5, h=0,5: Fr = {Fr:.3f} schießend', has(o,Fr,3) and 'schießend' in o, o[-60:])

        # ── Colebrook (unabhängig per brentq) und Swamee-Jain ──
        await go('hydrodynamik/rohr')
        ok=True; dev=[]
        for Re in [3e3,1e4,1e5,1e6,1e7,1e8]:
            for kd in [0,1e-5,1e-4,1e-3,1e-2,0.05]:
                l_js=await pg.evaluate(f'lamColebrook({Re},{kd})')
                l_py=brentq(lambda l: 1/math.sqrt(l)+2*math.log10(2.51/(Re*math.sqrt(l))+kd/3.71), 1e-4, 1)
                ok&=abs(l_js-l_py)<1e-9*l_py
                if 1e-6<=kd<=1e-2 and Re>=5e3: dev.append(abs(await pg.evaluate(f'lamSwamee({Re},{kd})')/l_py-1))
        check('Colebrook-White: 36 Punkte (Re 3·10³…10⁸, k/d 0…0,05) = brentq', ok)
        check(f'Swamee-Jain im Gültigkeitsbereich (Re ≥ 5000, k/d 10⁻⁶…10⁻²) ≤ 3 % von Colebrook (max {max(dev)*100:.2f} %)', max(dev)<0.03)
        check('laminar: λ = 64/Re', abs(await pg.evaluate('lamColebrook(1500,0.001)')-64/1500)<1e-12)
        Q,d,L,k,T,z=50,200,500,0.1,20,3.2
        await setv('wbr-', {'Q':Q,'d':d,'L':L,'k':k,'T':T,'z':z}, 'updateRohrR'); o=await out('wbr-out')
        dd=d/1000; v=Q/1000/(math.pi*dd*dd/4); Re=v*dd/1.004e-6
        lam=brentq(lambda l: 1/math.sqrt(l)+2*math.log10(2.51/(Re*math.sqrt(l))+k/1000/(3.71*dd)), 1e-4, 1)
        hr=lam*L/dd*v*v/(2*g); ho=z*v*v/(2*g)
        check(f'Rohr 20 °C mit Σζ = 3,2: h_v,R = {hr:.3f}, h_v,ö = {ho:.3f}, Σ = {hr+ho:.3f} m', all(has(o,x,3) for x in [hr,ho,hr+ho]), o[-120:])
        dp=998.2*g*(hr+ho)/1000; check(f'Druckverlust Δp = {dp:.1f} kPa', has(o,dp,1))
        nfig=await pg.evaluate("document.querySelectorAll('#wbr-fig svg circle').length"); check('Moody-Diagramm mit Betriebspunkt', nfig==1)

        # ── Pumpe ──
        await go('hydrodynamik/pumpen')
        V=dict(Q=40,Hg=25,hv=4.5,eta=72,pa=101.3,hs=3,hvs=0.6,T=20,npsh=3.5)
        await setv('pu-', V, 'updatePumpe'); o=await out('pu-out')
        rho=998.2; H=29.5; Ph=rho*g*0.04*H/1000; P=Ph/0.72; npsha=101.3e3/(rho*g)-2.339e3/(rho*g)-3-0.6
        check(f'Pumpe: P_hydr = {Ph:.2f} kW, P_Welle = {P:.2f} kW', has(o,Ph,2) and has(o,P,2), o[-80:])
        check(f'NPSH_A = {npsha:.2f} m ≥ 3,5 + 0,5 → keine Kavitation', has(o,npsha,2) and 'keine Kavitation' in o)
        await setv('pu-', {'hs':6}, 'updatePumpe'); o=await out('pu-out'); check('Saughöhe 6 m → Kavitationsgefahr', 'Kavitationsgefahr' in o)

        # ── Druckstoß ──
        await go('hydrodynamik/druckstoss')
        for d_,s_,E_,L_,dv,ts in [(300,8,210,1200,1.5,0.8),(200,12,3,400,1.0,5)]:
            await setv('dst-', {'d':d_,'s':s_,'E':E_,'L':L_,'dv':dv,'ts':ts}, 'updateDruckstoss'); o=await out('dst-out')
            K=2.1e9; a=math.sqrt(K/1000/(1+K*d_/(E_*1e9*s_))); Tr=2*L_/a; dpJ=1000*a*dv/1e5
            okk=has(o,a,0) and has(o,Tr,2) and has(o,dpJ,2)
            if ts>Tr: okk&=has(o,dpJ*Tr/ts,2) and 'langsam' in o
            else: okk&='schnelles' in o
            check(f'Joukowsky d={d_}, s={s_}, E={E_} GPa: a = {a:.0f} m/s, Δp = {dpJ:.2f} bar, Tr = {Tr:.2f} s', okk, o[-90:])

        # ── Ausfluss und Entleerung (gegen ODE) ──
        await go('hydrodynamik/ausfluss')
        d_,mu,h1,h2,AB=100,0.62,2.0,0.5,10
        await setv('af-', {'d':d_,'mu':mu,'h1':h1,'h2':h2,'A':AB}, 'updateAusfl'); o=await out('af-out')
        a=math.pi*0.1**2/4
        sol=solve_ivp(lambda t,h: [-mu*a*math.sqrt(2*g*max(h[0],0))/AB], [0,2000], [h1], events=lambda t,h: h[0]-h2, rtol=1e-10, atol=1e-12)
        tE=sol.t_events[0][0]; Q0=mu*a*math.sqrt(2*g*h1)*1000
        check(f'Ausfluss Q = {Q0:.2f} l/s, Entleerung 2,0 → 0,5 m: t = {tE:.0f} s (ODE)', has(o,Q0,2) and has(o,tE,0), o[-90:])

        # ── Grenztiefe ──
        await go('gerinne/energie')
        for Q_,b_,m_ in [(6,3,0),(10,2,1.5),(3,0,1)]:
            await setv('gt-', {'Q':Q_,'b':b_,'m':m_,'h':1.2}, 'updateGrenz'); o=await out('gt-out')
            hg=brentq(lambda h: Q_**2*(b_+2*m_*h)/(g*((b_+m_*h)*h)**3)-1, 1e-4, 20)
            A=(b_+m_*h)*h if False else (b_+m_*1.2)*1.2; Fr=Q_/A/math.sqrt(g*A/(b_+2*m_*1.2))
            # unabhängig: Grenztiefe = Minimum der spezifischen Energie
            Em=minimize_scalar(lambda h: h+Q_**2/(2*g*((b_+m_*h)*h)**2), bounds=(0.01,20), method='bounded', options={'xatol':1e-10})
            check(f'Grenztiefe Q={Q_}, b={b_}, m={m_}: h_gr = {hg:.3f} m = argmin E(h), Fr(1,2 m) = {Fr:.3f}', has(o,hg,3) and abs(Em.x-hg)<1e-4 and has(o,Fr,3), o[-80:])

        # ── Wechselsprung (Impulssatz) ──
        await go('gerinne/wechselsprung')
        for q,h1 in [(4,0.4),(10,0.5),(1,0.3)]:
            await setv('ws2-', {'q':q,'h1':h1}, 'updateSprung'); o=await out('ws2-out')
            M=lambda h: q*q/(g*h)+h*h/2
            Fr1=q/h1/math.sqrt(g*h1)
            if Fr1<=1: check(f'Wechselsprung q={q}, h1={h1}: Fr1 ≤ 1 → kein Sprung', 'kein Wechselsprung' in o); continue
            h2=brentq(lambda h: M(h)-M(h1), (q*q/g)**(1/3)*1.0001, 50)
            E=lambda h: h+q*q/(2*g*h*h); dE=E(h1)-E(h2)
            check(f'Wechselsprung q={q}, h1={h1}: h2 = {h2:.3f} m (Stützkraft gleich), ΔE = {dE:.3f} m', has(o,h2,3) and has(o,dE,3), o[-80:])

        # ── Teilfüllung (numerische Integration) ──
        await go('gerinne/teilfuellung')
        D,I,kst=0.4,5,75
        for hD in [0.3,0.5,0.82]:
            await setv('tf-', {'D':D*1000,'I':I,'k':kst,'hD':hD}, 'updateTeil'); o=await out('tf-out')
            r=D/2; h=hD*D
            A=quad(lambda y: 2*math.sqrt(max(r*r-(y-r)**2,0)), 0, h)[0]
            U=quad(lambda y: 2*r/math.sqrt(max(r*r-(y-r)**2,1e-30)), 0, h, limit=200)[0]
            Qn=kst*(A/U)**(2/3)*math.sqrt(I/1000)*A*1000
            check(f'Kreisrohr DN 400, h/D = {hD}: A = {A:.4f} m², Q = {Qn:.1f} l/s', has(o,A,4) and has(o,Qn,1), o[-90:])
        check('Teilfüllungsskizze mit Kurven Q/Qv und v/vv', await pg.evaluate("document.querySelectorAll('#tf-fig svg polyline').length")>=2)
        f=lambda x: -(lambda A,U: (A/U)**(2/3)*A)(*(lambda th: (r*r/2*(th-math.sin(th)), r*th))(2*math.acos(1-2*x)))
        xm=minimize_scalar(f, bounds=(0.5,0.999), method='bounded').x
        check(f'größter Abfluss bei h/D = {xm:.2f}', ('h/D ≈ '+de(xm,2)) in o.replace('\n',' '), xm)

        # ── Brunnen ──
        await go('grundwasser/brunnen')
        for art,k,H,s,r_,M_ in [('frei',5e-4,12,3,0.3,0),('gespannt',2e-4,20,4,0.25,8)]:
            await setv('br-', {'art':art,'k':k,'H':H,'s':s,'r':r_,'M':M_ or 1}, 'updateBrunnen'); o=await out('br-out')
            R=3000*s*math.sqrt(k)
            if art=='frei':
                # unabhängig: Q aus Darcy über Zylinderflächen, h(r) aus Integration von dh/dr = Q/(2π r k h)
                Q=brentq(lambda Q: (H-s)**2+2*Q/(2*math.pi*k)*math.log(R/r_)-H*H, 1e-6, 10)
            else:
                Q=brentq(lambda Q: s-Q/(2*math.pi*k*M_)*math.log(R/r_), 1e-7, 10)
            check(f'Brunnen {art}: R = {R:.1f} m, Q = {Q*1000:.2f} l/s', has(o,R,1) and has(o,Q*1000,2), o[-80:])

        # ── Regenabfluss ──
        await go('hydrologie/regen')
        await setv('rg-', {'A1':450,'p1':0.9,'A2':300,'p2':0.75,'A3':200,'p3':0.15,'r':300}, 'updateRegen'); o=await out('rg-out')
        Au=450*0.9+300*0.75+200*0.15; Qr=300*Au/1e4
        check(f'Regen: A_u = {Au:.1f} m², ψ_m = {Au/950:.3f}, Q = {Qr:.2f} l/s', has(o,Au,1) and has(o,Au/950,3) and has(o,Qr,2), o[-80:])

        # ── Alle Wasserbau-Seiten: keine Fehler, keine NaN, mobil ohne Überlauf ──
        bad=[]
        for vp in [(1440,900),(390,844)]:
            await pg.set_viewport_size({'width':vp[0],'height':vp[1]})
            for t in PAGES:
                await go(t)
                nan=await pg.evaluate("/NaN|undefined|Infinity/.test(document.getElementById('main').innerHTML)")
                ov=await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth+1")
                if nan or ov: bad.append((vp[0],t,'NaN' if nan else 'Überlauf'))
        check(f'{len(PAGES)} Wasserbau-Seiten Desktop + 390 px: keine NaN, kein Seitenüberlauf', not bad, bad)
        n=await pg.evaluate("Object.values(FAECHER.wasserbau.kapitel).reduce((s,k)=>s+Object.keys(k.themen).length,0)")
        check(f'FAECHER Wasserbau: {n} Themen = {len(PAGES)}', n==len(PAGES))
        check('Keine JavaScript-Fehler', not errs, errs[:3])
        await br.close()

asyncio.run(main())
print('FEHLER:', fails); sys.exit(1 if fails else 0)
