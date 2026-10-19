# statiq·size v0.5.20 Paket A: Torsion, Übergreifungsstoß, Abbrand, Deckenschwingung, hydraulischer Grundbruch, Zeitsetzung,
# Böschungsbruch, Druckstoß, Pumpe (NPSH), Teilfüllung, Gebäudeklasse. Geprüft: Ergebnisse gegen unabhängige Handrechnung in Python,
# reine Kernfunktionen gegen statiq·ref, Abhilfe mit Stellschraube, Bericht, Speichern/Laden und Englisch. Ohne Playwright: SKIP.
import os, sys, re, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
SIZE='file://'+BASE+'/size.html'; REF='file://'+BASE+'/ref.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
near=lambda a,b,r=1e-3: abs(a-b)<=r*max(1,abs(b))
GO={'torsion':"setMat('beton'); setTyp('torsion')", 'stoss':"setMat('beton'); setTyp('stoss')", 'brand':"setMat('holz'); setHoMode('brand')",
    'schwingung':"setMat('holz'); setHoMode('schwingung')", 'hyd':"setMat('grund'); setGrMode('hyd')", 'zeit':"setMat('grund'); setGrMode('zeit')",
    'boesch':"setMat('grund'); setGrMode('boesch')", 'druckstoss':"setMat('wasser'); setWbMode('druckstoss')", 'pumpe':"setMat('wasser'); setWbMode('pumpe')",
    'teil':"setMat('wasser'); setWbMode('teil')", 'gk':"setMat('bauph'); setBpMode('gk')"}

# ── unabhängige Handrechnungen ──
def torsion(b,h,fck,T,V,cot,dsw,sw,dsl,nl):           # XC1: c_min,dur 10, Δc_dev 10
    cw=max(10,dsw,10)+10; cl=max(10,dsl,10)+10; cv=max(cw,cl-dsw); c=cv+dsw+dsl/2
    fcd=0.85*fck/1.5; fyd=500/1.15; A=b*h; u=2*(b+h); tef=max(A/u,2*c); Ak=(b-tef)*(h-tef); uk=2*(b+h-2*tef)
    nu2=min(1.1-fck/500,1); nu=0.525*nu2; th=math.atan(1/cot)
    TRd=2*nu*fcd*Ak*tef*math.sin(th)*math.cos(th); z=0.9*(h-c); VRd=b*z*0.75*nu2*fcd/(cot+1/cot)
    inter=(T*1e6/TRd)**2+(V*1e3/VRd)**2
    asw=T*1e6/(2*Ak*fyd*cot)+V*1e3/(z*fyd*cot)/2
    Asl=T*1e6*uk*cot/(2*Ak*fyd)
    return dict(TRd=TRd, VRd=VRd, inter=inter, aswReq=asw, AslReq=Asl, c=c, tef=tef)
def stoss(ds,fctk,ssd,gut,zug,ant,haken,a):
    fbd=2.25*(1 if gut else 0.7)*fctk/1.5; lb=ds/4*ssd/fbd
    a6=1.0 if not zug else ((1.2 if ant<=33 else 1.4) if ds<16 else (1.4 if ant<=33 else 2.0)); a1=0.7 if (zug and haken) else 1.0
    l0=max(a1*a6*lb, 0.3*a6*lb, 15*ds, 200)+max(0,a-4*ds)
    return dict(fbd=fbd, lbrqd=lb, a6=a6, l0erf=l0)
def brand(b,h,t,s,bsh,fmk,fvk,M,V):
    bn=0.7 if bsh else 0.8; d=bn*t+min(1,t/20)*7; be=b-2*d; he=h-(2 if s==4 else 1)*d; kfi=1.15 if bsh else 1.25
    sm=M*1e6/(be*he*he/6); kcr=(2.5 if bsh else 2.0)/fvk; tau=1.5*V*1e3/(kcr*be*he)
    return dict(def_=d, bef=be, hef=he, sm=sm, tau=tau, fmfi=kfi*fmk, fvfi=kfi*fvk)
def schwingung(E,b,h,e,L,B,g,tE,EE):
    EIl=E*b*h**3/12/e; m=g*1000/9.81; f1=math.pi/(2*L*L)*math.sqrt(EIl*1e-3/m)
    EIb=EE*tE**3/12; bef=max(min(L*1000/1.1*(EIb/EIl)**0.25, B*1000), e); w=2000*(L*1000)**3/(48*EIl*bef)   # Prüflast 2 kN (Hamm/Richter)
    return dict(f1=f1, bef=bef, w=w)
def hyd(dh,t,gs,gH):
    L=dh+2*t; i=dh/L; eta=10*i*gH/(gs*0.95); izul=0.95*gs/(gH*10); treq=(dh/izul-dh)/2   # γ_G,stb (HYD) = 0,95 nach DIN 1054
    return dict(i=i, eta=eta, treq=treq)
def U(T):
    if T<=0: return 0
    return 1-sum(2/M**2*math.exp(-M*M*T) for M in (math.pi*(2*m+1)/2 for m in range(400)))
def TvU(u):
    lo,hi=0,5
    for _ in range(100):
        mid=(lo+hi)/2
        if U(mid)<u: lo=mid
        else: hi=mid
    return (lo+hi)/2
def zeit(s,H,cv,dr,tN,zul):
    Hd=H/2 if dr==2 else H; u=U(cv*tN/Hd**2); rest=s*(1-u)
    return dict(U=u, rest=rest, eta=rest/zul, t90=TvU(0.9)*Hd**2/cv, treq=TvU(1-zul/s)*Hd**2/cv)
def boesch(b,z,phi,c,g,gp=1.25):
    pd=math.atan(math.tan(math.radians(phi))/gp); cd=c/gp
    mu=lambda bb: g*z*math.sin(math.radians(bb))*math.cos(math.radians(bb))/(cd+g*z*math.cos(math.radians(bb))**2*math.tan(pd))
    x=0.05
    while x<89.9 and mu(x)<=1: x+=0.05         # erste Überschreitung (bei c′ > 0 fällt μ bei sehr steilen Böschungen wieder)
    lo,hi=x-0.05,x
    for _ in range(60):
        mid=(lo+hi)/2
        if mu(mid)<=1: lo=mid
        else: hi=mid
    return dict(mu=mu(b), bmax=lo)
def druckstoss(Q,D,s,E,L,ts,p0,PN):
    K=2.1e9; d=D/1000; v=Q/1000/(math.pi*d*d/4); a=math.sqrt(K/1000/(1+K*d/(E*1e6*s/1000))); Tr=2*L/a; dpJ=1000*a*v
    dp=dpJ if ts<=Tr else dpJ*Tr/ts
    return dict(v=v, a=a, Tr=Tr, dp=dp, pmax=p0+dp/1e5, tsReq=max(Tr, dpJ/1e5*Tr/(PN-p0)))
def pumpe(Q,Hg,hv,eta,pa,hs,hvs,rho,pD,npshr):
    g=9.81; H=Hg+hv; P=rho*g*Q/1000*H/1000/(eta/100); npsha=pa*1000/(rho*g)-pD*1000/(rho*g)-hs-hvs
    return dict(H=H, P=P, npsha=npsha, hsMax=pa*1000/(rho*g)-pD*1000/(rho*g)-hvs-(npshr+0.5))
def teil(Q,D,I,k):
    D/=1000; I/=1000; Q/=1000
    def seg(x):
        th=2*math.acos(1-2*x); A=D*D/8*(th-math.sin(th)); P=D/2*th; return A, A/P
    q=lambda x: k*seg(x)[0]*seg(x)[1]**(2/3)*math.sqrt(I)
    lo,hi=1e-6,0.938
    for _ in range(100):
        mid=(lo+hi)/2
        if q(mid)<Q: lo=mid
        else: hi=mid
    x=(lo+hi)/2; v=Q/seg(x)[0]; Qv=k*(math.pi*D*D/4)*(D/4)**(2/3)*math.sqrt(I)
    return dict(x=x, v=v, Qv=Qv)
def gk(h,n,a,frei):
    if h<=7 and n<=2 and n*a<=400: return 1 if frei else 2
    if h<=7: return 3
    if h<=13 and a<=400: return 4
    return 5

async def res(pg, go, vals={}):
    await pg.evaluate(go); await pg.wait_for_timeout(40)
    for k,v in vals.items(): await pg.evaluate(f"$('{k}').value='{v}'; $('{k}').dispatchEvent(new Event('change',{{bubbles:true}})); run()")
    return await pg.evaluate("LAST && LAST.res ? Object.fromEntries(Object.entries(LAST.res).filter(([k,v])=>typeof v==='number' || typeof v==='boolean')) : null")
async def checks(pg): return await pg.evaluate("Object.fromEntries(LAST.res.C.map(c=>[c.id,[c.eta,c.ok,!!c.info]]))")
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1400,'height':1000}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(SIZE); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(250)
        # Torsion
        for vals,tag in [({},'Standard'),({'in-beton':'C40/50','to-T':'50','to-V':'60','to-cot':'1.5'},'C40/50, cot 1,5')]:
            r=await res(pg, GO['torsion'], vals); fck=40 if vals else 30
            e=torsion(300,500,fck,float(vals.get('to-T',35)),float(vals.get('to-V',150)),float(vals.get('to-cot',1.0)),10,80,12,6)
            check(f'Torsion {tag}: T_Rd,max, V_Rd,max, Interaktion', near(r['TRd'],e['TRd']) and near(r['VRd'],e['VRd']) and near(r['inter'],e['inter']), (round(r['TRd']/1e6,2), round(e['TRd']/1e6,2), round(r['inter'],4)))
            check(f'Torsion {tag}: a_sw,erf und A_sl,erf', near(r['aswReq'],e['aswReq']) and near(r['AslReq'],e['AslReq']), (round(r['aswReq']*10,3), round(e['aswReq']*10,3)))
        # Stoß
        cases=[({},(16,2.0,435,True,True,100,False,0)),({'so-ds':'12'},(12,2.0,435,True,True,100,False,0)),({'so-ant':'30'},(16,2.0,435,True,True,30,False,0)),
               ({'so-art':'druck'},(16,2.0,435,True,False,100,False,0)),({'so-haken':'1'},(16,2.0,435,True,True,100,True,0)),({'so-verb':'maessig','so-ssd':'300'},(16,2.0,300,False,True,100,False,0)),
               ({'so-a':'100'},(16,2.0,435,True,True,100,False,100)),({'in-beton':'C20/25'},(16,1.5,435,True,True,100,False,0))]
        ok=True; info=[]
        for vals,args in cases:
            await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
            r=await res(pg, GO['stoss'], vals); e=stoss(*args)
            if not (near(r['fbd'],e['fbd']) and near(r['lbrqd'],e['lbrqd']) and r['a6']==e['a6'] and near(r['l0erf'],e['l0erf'])): ok=False; info.append((vals, r['l0erf'], e['l0erf']))
        check('Stoß: f_bd, l_b,rqd, α₆, l₀ in 8 Varianten (Ø, Anteil, Druck, Haken, Verbund, Abstand, Beton)', ok, info)
        r=await res(pg, GO['stoss'], {'so-ds':'25','so-ant':'50','so-l0':'250','so-dst':'12','so-st':'10'}); C=await checks(pg)
        check('Stoß Ø25, 50 %: Querbewehrung ΣA_st = ⌊l₀/s⌋·A(Ø12) ≥ A_s(Ø25)', not C['squer'][2] and near(r['Ast'], 25*math.pi*36) and near(r['Ab'], math.pi*625/4), (r['Ast'], C['squer']))
        # Abbrand
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        for vals,args,tag in [({},(200,400,60,3,True,24,3.5,40,25),'GL24h R60 dreiseitig'),({'br-t':'30','br-s':'4','br-b':'160','br-h':'320','br-M':'20','br-V':'12'},(160,320,30,4,True,24,3.5,20,12),'R30 vierseitig')]:
            r=await res(pg, GO['brand'], vals); e=brand(*args)
            check(f'Abbrand {tag}: d_ef, b_ef, h_ef, σ, τ', near(r['def'],e['def_']) and near(r['bef'],e['bef']) and near(r['hef'],e['hef']) and near(r['sm'],e['sm']) and near(r['tau'],e['tau']) and near(r['fmfi'],e['fmfi']), (r['def'],e['def_'],round(r['sm'],3),round(e['sm'],3)))
        r=await res(pg, GO['brand'], {'hx-art':'vh'}); r=await pg.evaluate("(()=>{ const q=nachweiseBR({...readBR(), t:15}); return {def:q.def, kfi:q.kfi}; })()")
        check('Abbrand Vollholz, t < 20 min: β_n = 0,8, k₀ = t/20', near(r['def'], 0.8*15+15/20*7) and r['kfi']==1.25, r['def'])
        # Schwingung
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        r=await res(pg, GO['schwingung']); e=schwingung(11500,100,220,625,4.2,4.0,1.6,50,25000)
        check('Schwingung GL24h: f₁, b_ef, w(2 kN)', near(r['f1'],e['f1']) and near(r['bef'],e['bef']) and near(r['w'],e['w']), (round(r['f1'],3),round(e['f1'],3),round(r['w'],4),round(e['w'],4)))
        r=await res(pg, GO['schwingung'], {'sv-tE':'0','sv-kl':'2'}); e=schwingung(11500,100,220,625,4.2,4.0,1.6,0,25000); C=await checks(pg)
        check('Schwingung ohne Estrich: b_ef = e, Klasse II mit 6 Hz / 1,0 mm', near(r['bef'],625) and near(r['w'],e['w']) and near(C['svf'][0],6/e['f1']), (r['bef'], C['svf'][0]))
        # HYD
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        for vals,args in [({},(4,3,10,1.35)),({'hy-dh':'6','hy-t':'2.5','hy-gs':'9','hy-gH':'1.8'},(6,2.5,9,1.8))]:
            r=await res(pg, GO['hyd'], vals); e=hyd(*args)
            check(f'HYD Δh = {args[0]} m, t = {args[1]} m: i, η, erforderliches t', near(r['i'],e['i']) and near(r['eta'],e['eta']) and near(r['treq'],e['treq']), (round(r['eta'],4), round(e['eta'],4), round(r['treq'],3)))
        r=await res(pg, GO['hyd'], {'hy-ans':'eigen','hy-L':'14'})
        check('HYD mit eigenem Sickerweg L = 14 m', near(r['i'], 6/14), r['i'])
        # Zeitsetzung
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        for vals,args in [({},(12,4,1.5,2,2,3)),({'zs-dr':'1','zs-tN':'5','zs-cv':'0.8'},(12,4,0.8,1,5,3))]:
            r=await res(pg, GO['zeit'], vals); e=zeit(*args)
            check(f'Zeitsetzung {"beidseitig" if args[3]==2 else "einseitig"}: U, Restsetzung, t₉₀, Wartezeit', near(r['U'],e['U'],1e-4) and near(r['rest'],e['rest'],1e-3) and near(r['t90'],e['t90'],1e-3) and near(r['treq'],e['treq'],1e-3), (round(r['U'],5), round(e['U'],5), round(r['treq'],3), round(e['treq'],3)))
        check('Zeitsetzung: T₉₀ = 0,848', near(TvU(0.9), 0.848, 2e-3), TvU(0.9))
        # Böschung
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        r=await res(pg, GO['boesch']); e=boesch(25,2,32.5,0,18.5)
        check('Böschung Sand (c = 0): μ = tan β/tan φ′_d, steilste Neigung = φ′_d', near(r['mu'],e['mu']) and near(r['bmax'],math.degrees(math.atan(math.tan(math.radians(32.5))/1.25)),1e-3), (round(r['mu'],4), round(e['mu'],4), round(r['bmax'],3)))
        r=await res(pg, GO['boesch'], {'gr-boden':'ts','bo-b':'35','bo-z':'3','bo-bs':'T'}); await pg.evaluate("grBodenPreset(); run()")
        r=await pg.evaluate("Object.fromEntries(Object.entries(LAST.res).filter(([k,v])=>typeof v==='number'))"); e=boesch(35,3,22.5,15,19.5,1.15)
        check('Böschung Ton steif (c′ = 15), BS-T: μ und β_max', near(r['mu'],e['mu']) and near(r['bmax'],e['bmax'],1e-3), (round(r['mu'],4), round(e['mu'],4), r['bmax'], e['bmax']))
        r=await res(pg, GO['boesch'], {'bo-w':'s','bo-gr':'20'})
        e_tau=20*3*math.sin(math.radians(35))*math.cos(math.radians(35)); e_sn=10*3*math.cos(math.radians(35))**2
        check('Böschung hangparallel durchströmt: τ mit γ_r, σ′ mit γ′ = γ_r − 10', near(r['tau'],e_tau) and near(r['sn'],e_sn), (r['tau'], r['sn']))
        # Druckstoß
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        for vals,args,tag in [({},(70,300,8,210000,1200,20,4,10),'Stahl, langsam'),({'wj-E':'1000','wj-s':'18','wj-ts':'1'},(70,300,18,1000,1200,1,4,10),'PE, schnell')]:
            r=await res(pg, GO['druckstoss'], vals); e=druckstoss(*args)
            check(f'Druckstoß {tag}: a, T_r, Δp, p_max, nötige Schließzeit', near(r['a'],e['a']) and near(r['Tr'],e['Tr']) and near(r['dp'],e['dp']) and near(r['pmax'],e['pmax']) and near(r['tsReq'],e['tsReq']), (round(r['a'],1), round(e['a'],1), round(r['dp']/1e5,3), round(e['dp']/1e5,3)))
        # Pumpe
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        r=await res(pg, GO['pumpe']); e=pumpe(25,18,3.5,70,101.3,3,0.6,999.7,1.228,3.5)
        check('Pumpe 10 °C: H_A, P_Welle, NPSH_A, zulässige Saughöhe', near(r['H'],e['H']) and near(r['P'],e['P']) and near(r['npsha'],e['npsha']) and near(r['hsMax'],e['hsMax']), (round(r['npsha'],4), round(e['npsha'],4)))
        r=await res(pg, GO['pumpe'], {'wp-T':'45'}); rho=992.2+(988.0-992.2)*0.5; pD=7.384+(12.35-7.384)*0.5; e=pumpe(25,18,3.5,70,101.3,3,0.6,rho,pD,3.5)
        check('Pumpe 45 °C: Dampfdruck linear zwischen 40 und 50 °C', near(r['npsha'],e['npsha']) and near(r['rho'],rho), (round(r['npsha'],4), round(e['npsha'],4)))
        # Teilfüllung
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        for vals,args in [({},(25,300,5,80)),({'wt-Q':'60','wt-D':'400','wt-I':'2','wt-k':'90'},(60,400,2,90))]:
            r=await res(pg, GO['teil'], vals); e=teil(*args)
            check(f'Teilfüllung Q = {args[0]} l/s, DN {args[1]}: Q_v, h/D, v', near(r['Qv'],e['Qv']) and near(r['x'],e['x'],1e-4) and near(r['v'],e['v'],1e-3), (round(r['x'],5), round(e['x'],5), round(r['v'],4), round(e['v'],4)))
        r=await res(pg, GO['teil'], {'wt-Q':'200'}); C=await checks(pg)
        check('Teilfüllung Q > Q_max (≈ 1,076·Q_v bei h/D ≈ 0,94): Druckabfluss, nicht erfüllt', r['over'] and not C['wth'][1] and near(r['best']/r['Qv'],1.076,3e-3) and near(r['hb'],0.938,2e-3), (r['best']/r['Qv'], r['hb']))
        # Gebäudeklasse
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
        ok=True; info=[]
        for h,n,a,fr in [(8.4,8,85,1),(5,1,180,1),(5,2,180,0),(6,3,90,1),(12.5,6,420,1),(18,10,90,1),(7,2,250,1)]:
            r=await res(pg, GO['gk'], {'gk-h':h,'gk-n':n,'gk-a':a,'gk-frei':fr})
            if r['gk']!=gk(h,n,a,fr): ok=False; info.append((h,n,a,fr,r['gk']))
        check('Gebäudeklasse in 7 Fällen nach MBO § 2 Abs. 3', ok, info)
        r=await res(pg, GO['gk'], {'gk-h':'8.4','gk-n':'8','gk-a':'85','gk-frei':'1','gk-lage':'ober','gk-fw':'30'}); C=await checks(pg)
        check('GK 4 oberirdisch: hochfeuerhemmend → R 30 nicht erfüllt (η = 2)', r['req']==60 and not C['gkfw'][1] and near(C['gkfw'][0],2), C['gkfw'])
        r=await res(pg, GO['gk'], {'gk-h':'5','gk-n':'1','gk-a':'150','gk-frei':'1','gk-fw':'0'}); C=await checks(pg)
        check('GK 1 oberirdisch: keine Anforderung (Info)', r['gk']==1 and r['req']==0 and C['gkfw'][2], C['gkfw'])
        r=await res(pg, GO['gk'], {'gk-h':'25'}); C=await checks(pg)
        check('h > 22 m: Hochhaus, außerhalb des Nachweises', r['hoch'] and not C['gkfw'][1], C['gkfw'])
        # Kernfunktionen gegen statiq·ref
        rp=await br.new_page(); await rp.goto(REF); await rp.wait_for_timeout(200)
        out=[]
        for expr in ["verankerung(2.0,16,true,435).lbrqd","verankerung(1.5,25,false,400).lbrqd","holzBrand({cls:'GL24h',b:200,h:400,t:60,s:3,M:40}).def","holzBrand({cls:'C24',b:120,h:240,t:15,s:4,M:5}).def",
                     "UvonT(0.3)","TvonU(0.9)","kreisTeil(0.3,0.12).A","gebaeudeklasse(8.4,8,85,true)","wasserBei(45)[4]"]:
            a=await rp.evaluate(expr)
            sx=(expr.replace("verankerung(2.0,16,true,435).lbrqd","stoss(16,2.0,435,true,true,0,false,0).lbrqd").replace("verankerung(1.5,25,false,400).lbrqd","stoss(25,1.5,400,false,true,0,false,0).lbrqd")
                .replace("holzBrand({cls:'GL24h',b:200,h:400,t:60,s:3,M:40}).def","nachweiseBR({...readBR(), b:200,h:400,t:60,s:3,Mfi:40,Vfi:1}).def"))
            if expr.startswith('holzBrand') and 'C24' in expr:
                await pg.evaluate("setMat('holz'); setHoMode('brand'); $('hx-art').value='vh'; fillHxKlassen(); $('hx-kl').value='C24'; run()")
                sx="nachweiseBR({...readBR(), b:120,h:240,t:15,s:4,Mfi:5,Vfi:1}).def"
            elif expr.startswith('holzBrand'):
                await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120); await pg.evaluate("setMat('holz'); setHoMode('brand')")
            if expr.startswith('wasserBei'): sx="wasserBei(45)[2]"
            if expr.startswith('verankerung'): b2=stoss(16,2.0,435,True,True,0,False,0)['lbrqd'] if '16' in expr else stoss(25,1.5,400,False,True,0,False,0)['lbrqd']
            else: b2=await pg.evaluate(sx)
            out.append((expr, a, b2, near(float(a),float(b2),1e-6)))
        check('Kernfunktionen wie statiq·ref (Verankerung, Abbrand, Konsolidation, Kreisabschnitt, GK, Dampfdruck)', all(o[3] for o in out), [o for o in out if not o[3]] or len(out))
        await rp.close()
        # Abhilfe: je Modus ein nicht erfüllter Nachweis, Stellschraube, „Übernehmen“ erfüllt ihn
        CASES=[('torsion',{'to-T':'80'},'tdruck','in-h',None),('stoss',{'so-l0':'90'},'sl0','so-l0',116),('brand',{'br-M':'60'},'brm','br-b',None),
               ('schwingung',{'sv-L':'4.8'},'svf','sv-h',None),('hyd',{'hy-dh':'16'},'hynw','hy-t',math.ceil(hyd(16,3,10,1.35)['treq']/0.05-1e-9)*0.05),
               ('zeit',{'zs-tN':'0.5'},'zsrest','zs-tN',math.ceil(zeit(12,4,1.5,2,0.5,3)['treq']/0.05-1e-9)*0.05),
               ('boesch',{'bo-b':'30'},'bonw','bo-b',math.floor(boesch(30,2,32.5,0,18.5)['bmax']/0.5)*0.5),('druckstoss',{'wj-ts':'2'},'wjp','wj-ts',None),
               ('pumpe',{'wp-hs':'7'},'wpnpsh','wp-hs',None),('teil',{'wt-Q':'60'},'wth','wt-D',None),('gk',{'gk-fw':'30'},'gkfw','gk-fw','60')]
        for mode,vals,cid,lev,exp in CASES:
            await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(150)
            await res(pg, GO[mode], vals)
            await pg.wait_for_function("document.querySelector('.fixbox') || !document.querySelector('#chk-table .tag.bad')", timeout=15000)
            fx=await pg.evaluate(f"(LAST.res.C.find(c=>c.id==='{cid}').fix||[]).map(f=>[f.id,f.v])")
            box=await pg.evaluate(f"(document.querySelector('#n-{cid} .fixbox')||{{}}).innerText||''")
            f=dict(fx)
            okv = lev in f and (exp is None or (f[lev]==exp if isinstance(exp,str) else near(float(f[lev]),exp,1e-6)))
            check(f'Abhilfe {mode}: Ursache und Stellschraube {lev}' + (f' = {exp:.2f}' if isinstance(exp,float) else f' = {exp}' if exp else ''), 'Warum nicht erfüllt?' in box and okv, fx)
            if lev in f:
                await pg.evaluate(f"document.querySelector('#n-{cid} .fixbox button[data-fix=\"{lev}\"]').click()"); await pg.wait_for_timeout(120)
                check(f'Abhilfe {mode}: „Übernehmen“ erfüllt {cid}', await pg.evaluate(f"LAST.res.C.find(c=>c.id==='{cid}').ok"))
        # Bericht, Positionen
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(150)
        ok=True
        for m,go in GO.items():
            await pg.evaluate(go); await pg.wait_for_timeout(40); rep=await pg.evaluate("buildReport()")
            if not ('<h1>' in rep and 'Eingaben' in rep and 'Zusammenfassung' in rep and '<svg' in rep): ok=False
        check('Bericht für alle 11 neuen Modi (Eingaben, Abbildung, Zusammenfassung)', ok)
        await pg.evaluate(GO['torsion']+"; $('to-T').value='44'; run(); savePos()")
        await pg.evaluate(GO['zeit']+"; $('zs-cv').value='2.2'; run(); savePos()")
        await pg.evaluate("loadPos(0)"); await pg.wait_for_timeout(80)
        check('Position Torsion speichern und laden', await pg.evaluate("MAT==='beton' && TYP==='torsion' && $('to-T').value==='44' && $('beton-to').style.display===''"))
        await pg.evaluate("loadPos(1)"); await pg.wait_for_timeout(80)
        check('Position Zeitsetzung laden (Bereich Grundbau, Karte Baugrund ausgeblendet)', await pg.evaluate("MAT==='grund' && GRMODE==='zeit' && $('zs-cv').value==='2.2' && $('gr-boden-card').style.display==='none'"))
        names=await pg.evaluate("posRead().map(p=>p.typ)")
        check('Positionsliste kennt die Bauteilart', names==['torsion','grund_zeit'], names)
        # Englisch
        await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(250)
        GER=re.compile(r'[äöüÄÖÜß]|\b(und|der|die|das|mit|nicht|oder|für|bei|nach|ist|wird|vorhanden|erf|vorh|zul|Nachweis|Decke|Stoß|Wasser|Jahre|Gebäudeklasse|Bügel|Querschnitt)\b')
        left={}
        for m,go in GO.items():
            await pg.evaluate(go); await pg.wait_for_timeout(60)
            t=await pg.evaluate("[...['summary','chk-table','details','fig','reinf-line','page-title','page-sub'].map(i=>['page-title','page-sub'].includes(i) ? document.getElementById(i).textContent : document.getElementById(i).innerText), (()=>{const d=document.createElement('div'); d.innerHTML=trFig(buildReport()); return d.innerText})()].join('\\n')")
            for line in t.split('\n'):
                mm=GER.search(line)
                if mm: left.setdefault(m, line[max(0,mm.start()-30):mm.start()+40])
        check('EN: Ergebnis, Rechenweg, Abbildung und Bericht ohne deutsche Reste (11 Modi)', not left, left)
        await pg.evaluate(GO['stoss']+"; $('so-l0').value='90'; run()"); await pg.wait_for_function("document.querySelector('.fixbox')", timeout=15000)
        box=await pg.evaluate("(document.querySelector('#n-sl0 .fixbox')||{}).innerText||''")
        check('EN: Abhilfe-Kasten englisch', 'Why is it not satisfied?' in box and 'lap length' in box and not re.search('[äöüß]', box), box[:120])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
