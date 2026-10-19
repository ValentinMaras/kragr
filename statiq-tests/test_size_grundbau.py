# statiq·size: Grundbau (DIN 1054 / DIN 4017 / DIN 4019) — unabhängig nachgerechnet. Ohne Playwright: SKIP.
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
r=math.radians
def din4017(b,a,d,phi,c,g1,g2,V,H,e):
    t=math.tan(r(phi)); bp=b-2*e; strip=a is None; ap=1 if strip else a
    Nd0=math.tan(math.pi/4+r(phi)/2)**2*math.exp(math.pi*t); Nb0=(Nd0-1)*t; Nc0=(Nd0-1)/t
    if strip: q=0; bs=bp; m=2
    else: q=min(bp,ap)/max(bp,ap); bs=min(bp,ap); m=(2+bp/ap)/(1+bp/ap)
    vb,vd=1-0.3*q,1+q*math.sin(r(phi)); vc=(vd*Nd0-1)/(Nd0-1)
    A=bp*ap; k=1-H/(V+A*c/t); i_d=k**m; i_b=k**(m+1); i_c=(i_d*Nd0-1)/(Nd0-1)
    return A*(g2*bs*Nb0*vb*i_b + g1*d*Nd0*vd*i_d + c*Nc0*vc*i_c), Nd0, Nb0
def flach(form,b,a,d,hf,phi,c,g1,g2,VG,VQ,HG,HQ,MG,MQ):
    A=b*(1 if form=='streifen' else a); GF=(25*hf+g1*max(0,d-hf))*A
    VGt=VG+GF; Vk=VGt+VQ; Hk=HG+HQ; Mk=MG+MQ+Hk*hf; e=abs(Mk)/Vk
    Rk,_,_=din4017(b, None if form=='streifen' else a, d, phi, c, g1, g2, Vk, Hk, e)
    Vd=1.35*VGt+1.5*VQ; eta_gb=Vd/(Rk/1.4)
    eG=abs(MG+HG*hf)/VGt; eU=abs(Mk)/VGt; eta_e=max(eG/(b/6), eU/(b/3))
    eta_gl=(1.35*HG+1.5*HQ)/(VGt*math.tan(r(phi))/1.1) if Hk>0 else None
    return dict(gb=eta_gb, e=eta_e, gl=eta_gl, Rk=Rk)
def boussinesq_corner(a,b,z,n=400):
    # Integration der Boussinesq-Lösung über die Rechteckfläche (Mittelpunktregel)
    xs=(np.arange(n)+0.5)/n*a; ys=(np.arange(n)+0.5)/n*b; X,Y=np.meshgrid(xs,ys); R=np.sqrt(X**2+Y**2+z**2)
    return (3*z**3/(2*math.pi*R**5)).sum()*(a/n)*(b/n)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('grund'); setGrMode('flach')")
        s=await pg.inner_text('#summary'); check('Standard Flachgründung erfüllt', 'Alle Nachweise erfüllt' in s, s)
        # Tragfähigkeitsbeiwerte gegen DIN-4017-Tabellenwerte
        for phi,Nd in [(25,10.66),(30,18.40),(35,33.30)]:
            g=await pg.evaluate(f"grundbruch({{b:2,a:Infinity,d:1,phi:{phi},c:0,g1:18,g2:18,V:100,H:0,e:0}}).Nd0")
            check(f'N_d0(φ = {phi}°) = {Nd}', abs(g-Nd)<0.01, f'{g:.3f}')
        cases={'Einzelfundament 2×2, H und M (Standard)':('rechteck',2,2,1,0.6,32.5,0,18.5,18.5,900,400,0,60,0,120),
               'Streifen b = 1,2, Ton mit Kohäsion':('streifen',1.2,0,0.8,0.5,22.5,15,19.5,19.5,180,60,0,10,0,15),
               'Rechteck 3×1,8 (b > a getauscht), große Ausmitte':('rechteck',3,1.8,1.2,0.8,35,0,19.5,10,800,300,20,40,150,200),
               'Einzelfundament nur Vertikallast, Kies':('rechteck',1.5,2.5,1.0,0.6,35,0,20.5,20.5,700,300,0,0,0,0)}
        for name,v in cases.items():
            form,b,a,d,hf,phi,c,g1,g2,VG,VQ,HG,HQ,MG,MQ=v
            await pg.evaluate(f"$('gr-boden').value='x'; $('gf-form').value='{form}'; $('gf-b').value={b}; $('gf-a').value={a or 1}; $('gf-d').value={d}; $('gf-hf').value={hf}; $('gr-phi').value={phi}; $('gr-c').value={c}; $('gr-g1').value={g1}; $('gr-g2').value={g2}; $('gf-VG').value={VG}; $('gf-VQ').value={VQ}; $('gf-HG').value={HG}; $('gf-HQ').value={HQ}; $('gf-MG').value={MG}; $('gf-MQ').value={MQ}; run()")
            R=flach(*v); g=await pg.evaluate("Object.fromEntries(LAST.res.C.map(c=>[c.id,c.eta]))")
            ok=abs(g['gfgb']-R['gb'])<1e-9 and abs(g['gfexz']-R['e'])<1e-9 and (R['gl'] is None and 'gfgl' not in g or R['gl'] is not None and abs(g['gfgl']-R['gl'])<1e-9)
            check(f'Flachgründung {name}', ok, f"η GB {R['gb']:.3f}, e {R['e']:.3f}, Gleiten {R['gl'] if R['gl'] is None else round(R['gl'],3)}")
        # Steinbrenner gegen numerisch integrierte Boussinesq-Lösung
        for a,b,z in [(1,1,1),(2,1,0.5),(3,2,4),(1.5,1.5,0.2)]:
            g=await pg.evaluate(f"steinbrenner({a},{b},{z})"); ref=boussinesq_corner(a,b,z)
            check(f'Steinbrenner-Ecke a={a}, b={b}, z={z}', abs(g-ref)<2e-4, f'{g:.5f} / Boussinesq {ref:.5f}')
        # Setzung: unabhängige Integration, mehrere Schichten, mit und ohne Grundwasser
        def setz_ref(a,b,d,V,g0,L,gw):
            # L: [(h, γ, Es)], letzte Schicht h = None; gw: Tiefe unter Gelände oder None
            zwS = (gw-d) if gw is not None else 1e9
            above = g0*d if gw is None or gw>=d else g0*max(0,gw)+(g0-10)*(d-max(0,gw))
            bounds=[]; z=0
            for h,g,E in L: bounds.append((z, z+h if h else 1e9, g, E)); z+= h or 0
            def su(zz):
                s=above
                for z0,z1,g,E in bounds:
                    if zz<=z0: break
                    t1=min(zz,z1); dry=max(0,min(t1,zwS)-z0); wet=max(0,t1-max(z0,zwS)); s+=g*dry+(g-10)*wet
                return s
            s1=V/(a*b)-above
            iP=lambda z: sum(boussinesq_corner(A,B,z,160) for A,B in [(a/2+0.37*a,b/2+0.37*b),(a/2-0.37*a,b/2+0.37*b),(a/2+0.37*a,b/2-0.37*b),(a/2-0.37*a,b/2-0.37*b)])
            zs=np.linspace(0.02,12,600); sz=np.array([iP(z)*s1 for z in zs]); sus=np.array([su(z) for z in zs])
            zg=zs[np.argmax((sz<=0.2*sus)&(zs>0.3))]
            Es=np.array([next(E for z0,z1,g,E in bounds if z0<=z<z1)*1000 for z in zs]); m=zs<=zg
            return zg, np.trapezoid((sz/Es)[m], zs[m]) + 0.25*s1*0.02/Es[0]
        for name,(g0,L,gw,n) in {'3 Schichten Sand/Ton/Kies, ohne Grundwasser':(19,[(3,19,30),(4,19,15),(None,19,80)],None,3),
                                  'verschiedene Wichten, Grundwasser 2,5 m unter Gelände':(18,[(2,18.5,45),(4,19.5,12),(None,20.5,120)],2.5,3),
                                  'Grundwasser über der Sohle (0,5 m unter Gelände)':(18,[(1.5,18.5,45),(2,19.5,12),(3,20.5,120),(None,19.5,100)],0.5,4)}.items():
            js="setGrMode('setzung'); $('gs-a').value=3; $('gs-b').value=2; $('gs-d').value=1; $('gs-V').value=1500; $('gs-g0').value=%s; $('gs-n').value='%d'; $('gs-gw').checked=%s; $('gs-zw').value=%s;"%(g0,n,'true' if gw is not None else 'false',gw or 0)
            for i,(h,g,E) in enumerate(L,1): js+=" $('gs-b%d').value='x'; $('gs-h%d').value=%s; $('gs-g%d').value=%s; $('gs-E%d').value=%s;"%(i,i,h or 1,i,g,i,E)
            await pg.evaluate(js+" run()")
            g=await pg.evaluate("[LAST.res.zg, LAST.res.s, LAST.res.lay.reduce((t,l)=>t+l.s,0)]")
            zg,sref=setz_ref(3,2,1,1500,g0,L,gw)
            check(f'Setzung {name}: Grenztiefe', abs(g[0]-zg)<0.06, f'App {g[0]:.3f} m, Referenz {zg:.3f} m')
            check(f'Setzung {name}: s', abs(g[1]-sref)/sref<0.015 and abs(g[2]-g[1])<1e-12, f'App {g[1]*100:.3f} cm, Referenz {sref*100:.3f} cm')
        await pg.evaluate("$('gs-b2').value='ts'; gsPreset(2); run()")
        check('Bodenauswahl Schicht 2 setzt γ und E_s (Ton, steif)', await pg.evaluate("$('gs-g2').value==='19.5' && $('gs-E2').value==='12'"))
        # Stützwand: Rankine (δ = 0), Momente, Gleiten, Grundbruch
        await pg.evaluate("setGrMode('wand'); $('gr-boden').value='x'; $('gr-phi').value=30; $('gr-c').value=0; $('gr-g1').value=19; $('gr-g2').value=19; $('gw-H').value=4; $('gw-B').value=2.6; $('gw-bv').value=0.6; $('gw-tw').value=0.3; $('gw-ts').value=0.4; $('gw-d').value=0.8; $('gw-q').value=10; $('gw-delta').value='0'; run()")
        g=await pg.evaluate("[LAST.res.Kah, LAST.res.EahG, LAST.res.VG, LAST.res.MG, Object.fromEntries(LAST.res.C.map(c=>[c.id,c.eta]))]")
        H,B,bv,tw,ts,dd,q,phi,gm=4,2.6,0.6,0.3,0.4,0.8,10,30,19
        Ka=math.tan(r(45-phi/2))**2; EG=0.5*gm*H*H*Ka; EQ=q*H*Ka; hs=H-ts; bh=B-bv-tw
        parts=[(25*tw*hs,bv+tw/2),(25*B*ts,B/2),(gm*bh*hs,B-bh/2),(gm*bv*(dd-ts),bv/2)]
        VG=sum(v for v,_ in parts); MG=sum(v*(B/2-x) for v,x in parts)+EG*H/3; MQ=EQ*H/2
        eG=MG/VG; eU=(MG+MQ)/VG; eta_e=max(abs(eG)/(B/6),abs(eU)/(B/3)); eta_gl=(1.35*EG+1.5*EQ)/(VG*math.tan(r(phi))/1.1)
        Rk,_,_=din4017(B,None,dd,phi,0,gm,gm,VG,EG+EQ,abs((MG+MQ)/VG)); eta_gb=1.35*VG/(Rk/1.4)
        check('Stützwand: K_ah = tan²(45° − φ/2) und E_ah,G', abs(g[0]-Ka)<1e-12 and abs(g[1]-EG)<1e-9, f'K_a = {Ka:.4f}, E_ah,G = {EG:.2f} kN/m')
        check('Stützwand: Eigengewicht und Moment um Sohlmitte', abs(g[2]-VG)<1e-9 and abs(g[3]-MG)<1e-9, f'V_G = {VG:.2f} kN/m, M_G = {MG:.2f} kNm/m')
        check('Stützwand: Kippen, Gleiten, Grundbruch', abs(g[4]['gwexz']-eta_e)<1e-9 and abs(g[4]['gwgl']-eta_gl)<1e-9 and abs(g[4]['gwgb']-eta_gb)<1e-9, f'η {eta_e:.3f} / {eta_gl:.3f} / {eta_gb:.3f}')
        ka=await pg.evaluate("kaCoulomb(30, 20)")
        ref=math.cos(r(30))**2/(math.cos(r(20))*(1+math.sqrt(math.sin(r(50))*math.sin(r(30))/math.cos(r(20))))**2)
        check('Coulomb K_a(φ = 30°, δ = 20°) ≈ 0,297', abs(ka-ref)<1e-12 and abs(ka-0.297)<0.002, f'{ka:.4f}')
        # Auftrieb
        await pg.evaluate("setGrMode('upl'); $('gu-L').value=12; $('gu-B').value=8; $('gu-hw').value=2.5; $('gu-ts').value=0.4; $('gu-tw').value=0.3; $('gu-hwand').value=2.8; $('gu-td').value=0.25; $('gu-g').value=0; $('gu-bs').value='P'; run()")
        g=await pg.evaluate("[LAST.res.G, LAST.res.U, LAST.res.C.find(c=>c.id==='guupl').eta, LAST.res.tsReq]")
        G=25*(96*0.4+(96-11.4*7.4)*2.8+96*0.25); U=10*2.5*96; eta=1.05*U/(0.95*G); ts=(1.05*U/0.95-25*((96-11.4*7.4)*2.8+96*0.25))/(25*96)
        check('Auftrieb: G, A und η (BS-P)', abs(g[0]-G)<1e-9 and abs(g[1]-U)<1e-9 and abs(g[2]-eta)<1e-12, f'G = {G:.1f} kN, A = {U:.0f} kN, η = {eta:.3f}')
        check('Auftrieb: erforderliche Sohldicke', abs(g[3]-ts)<1e-12, f'{ts:.3f} m')
        s=await pg.inner_text('#summary'); check('h_w = 2,5 m → nicht erfüllt', 'nicht erfüllt' in s, s)
        await pg.evaluate("showReport()"); rp=await pg.inner_text('#report')
        check('Bericht Auftrieb', 'UPL' in rp and 'Auftrieb' in rp)
        await pg.evaluate("closeReport && closeReport()") if await pg.evaluate("typeof closeReport==='function'") else None
        for m,word in [('flach','Grundbruch'),('setzung','Grenztiefe'),('wand','Erddruck')]:
            await pg.evaluate(f"setGrMode('{m}'); run(); showReport()"); rp=await pg.inner_text('#report')
            check(f'Bericht {m}', word in rp)
        await pg.evaluate("setGrMode('wand'); $('gw-q').value=17; run(); save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden stellt Grundbau wieder her', await pg.evaluate("MAT==='grund' && GRMODE==='wand' && $('gw-q').value==='17' && LAST.mode==='wand'"))
        await pg.evaluate("savePos()"); check('Position speichern (Typ grund_wand)', await pg.evaluate("posRead().some(p=>p.typ==='grund_wand')"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
