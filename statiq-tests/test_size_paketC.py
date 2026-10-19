# statiq·size v0.5.22 Paket C: Stütze mit zweiachsiger Biegung, zweiachsig gespannte Platte (Marcus), Stirnplattenstoß, Holz-Beton-Verbund
# (γ-Verfahren), Spundwand nach Blum, Bohrpfahl axial, Grundwasserabsenkung mit Brunnen, sommerlicher Wärmeschutz.
# Geprüft: Ergebnisse gegen unabhängige Handrechnung in Python, Abhilfe mit Stellschraube, Bericht, Speichern/Laden, Englisch. Ohne Playwright: SKIP.
import os, sys, re, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
SIZE='file://'+BASE+'/size.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
near=lambda a,b,r=1e-3: abs(a-b)<=r*max(1,abs(b))
GO={'zweiachsig':"setMat('beton'); setTyp('zweiachsig')", 'platte2':"setMat('beton'); setTyp('platte2')", 'stirnplatte':"setMat('stahl'); setStMode('stirnplatte')",
    'verbund':"setMat('holz'); setHoMode('verbund')", 'spundwand':"setMat('grund'); setGrMode('spundwand')", 'pfahl':"setMat('grund'); setGrMode('pfahl')",
    'brunnen':"setMat('wasser'); setWbMode('brunnen')", 'sommer':"setMat('bauph'); setBpMode('sommer')"}
FYD=500/1.15; ES=200000
# ── unabhängige Handrechnungen ──
def mrd(b, h, d2, As, fcd, N):
    """Momententragfähigkeit eines Rechteckquerschnitts mit zwei gleichen Bewehrungslagen bei Normalkraft N (N, mm).
    Eigene Umsetzung: Dehnungsebene über die Druckzonenhöhe, Parabel-Rechteck, B500 bilinear."""
    d=h-d2
    def sc(e): return 0 if e<=0 else (fcd*(1-(1-e/2)**2) if e<2 else fcd)
    def ss(e): return math.copysign(min(ES*abs(e)/1000, FYD), e)
    def eps(x):
        if x<=h:
            et = 3.5 if d<=x else min(3.5, 25*x/(d-x))
            return lambda y: et*(x-y)/x
        return lambda y: 2*(x-y)/(x-3*h/7)
    def st(x):
        e=eps(x); xc=min(x,h); n=400; Nn=0; M=0
        for i in range(n):
            y=(i+0.5)*xc/n; f=sc(e(y))*b*xc/n; Nn+=f; M+=f*(h/2-y)
        s2=ss(e(d2)); s1=ss(e(d)); Nn+=As/2*(s2+s1); M+=As/2*(s2-s1)*(h/2-d2)
        return Nn, M
    lo, hi = 1e-4*h, 1e5*h
    if st(hi)[0]<N: return None
    for _ in range(90):
        m=math.sqrt(lo*hi)
        if st(m)[0]<N: lo=m
        else: hi=m
    return st(math.sqrt(lo*hi))[1]
def zweiachsig(b,h,fck,N,My,Mz,n,ds,dsw):
    fcd=0.85*fck/1.5; cw=max(10,dsw,10)+10; cl=max(10,ds,10)+10; cv=max(cw,cl-dsw); d2=cv+dsw+ds/2
    A=math.pi*ds*ds/4; Alay=2*n*A; Atot=4*(n-1)*A
    MRy=mrd(b,h,d2,Alay,fcd,N*1e3)/1e6; MRz=mrd(h,b,d2,Alay,fcd,N*1e3)/1e6; NRd=(b*h*fcd+Atot*FYD)/1e3; r=N/NRd
    a=1 if r<=0.1 else (1+0.5*(r-0.1)/0.6 if r<=0.7 else (1.5+0.5*(r-0.7)/0.3 if r<=1 else 2))
    return dict(MRy=MRy, MRz=MRz, NRd=NRd, a=a, ia=(Mz/MRz)**a+(My/MRy)**a)
def platte2(lx,ly,q,h,fck,fctm,dsx,sx,dsy,sy):
    lx,ly=min(lx,ly),max(lx,ly); kx=ly**4/(lx**4+ly**4); ky=1-kx; nx=1-5/6*(lx/ly)**2*kx; ny=1-5/6*(ly/lx)**2*ky
    mx=nx*kx*q*lx*lx/8; my=ny*ky*q*ly*ly/8; fcd=0.85*fck/1.5
    dx=h-(max(10,dsx,10)+10)-dsx/2; dy=dx-(dsx+dsy)/2
    def As(m,d):
        mu=m*1e6/(1000*d*d*fcd); return max((1-math.sqrt(1-2*mu))*1000*d*fcd/FYD, max(0.26*fctm/500,0.0013)*1000*d)
    return dict(mx=mx, my=my, Ax=As(mx,dx), Ay=As(my,dy))
def stirnplatte(h,b,tw,tf,Wpl,fy,tp,bp,d,fub,av,w,pf,aw):
    As={16:157,20:245,22:303,24:353,27:459,30:561}[d]; Ft=0.9*fub*As/1.25
    m=(w-tw)/2-0.8*aw*math.sqrt(2); e=(bp-w)/2; n=min(e,1.25*m); l1=min(2*math.pi*m, 4*m+1.25*e); l2=4*m+1.25*e
    M1=0.25*l1*tp*tp*fy; M2=0.25*l2*tp*tp*fy
    F=min(4*M1/m, (2*M2+n*2*Ft)/(m+n), 2*Ft, l1*tw*fy, Wpl*1000*fy/(h-tf))
    return dict(Ft=F, Mj=F*(h-tf-pf-tf/2)/1e6, FvRd=av*fub*As/1.25)
def verbund(E1,b1,h1,E2,b2,h2,L,K,s,M,V):
    A1=b1*h1; A2=b2*h2; I1=b1*h1**3/12; I2=b2*h2**3/12; L*=1000
    g1=1/(1+math.pi**2*E1*A1*s/(K*L*L)); a2=g1*E1*A1*(h1+h2)/2/(g1*E1*A1+E2*A2); a1=(h1+h2)/2-a2
    EI=E1*I1+E2*I2+g1*E1*A1*a1*a1+E2*A2*a2*a2
    return dict(g1=g1, EI=EI, s2=E2*a2*M*1e6/EI, sm2=0.5*E2*h2*M*1e6/EI, sc=(g1*E1*a1+0.5*E1*h1)*M*1e6/EI, F1=g1*E1*A1*a1*s*V*1e3/EI)
def blum(h,q,phi,g,gG=1.35,gQ=1.5,gR=1.4):
    Ka=math.tan(math.radians(45-phi/2))**2; Kp=math.tan(math.radians(45+phi/2))**2
    A=gG*Ka*g; B=gQ*Ka*q; C=Kp*g/gR
    f=lambda t: A*(h+t)**3/6+B*(h+t)**2/2-C*t**3/6
    lo,hi=0,100
    for _ in range(200):
        m=(lo+hi)/2
        if f(m)>0: lo=m
        else: hi=m
    t0=lo
    Q=lambda z: A*(h+z)**2/2+B*(h+z)-C*z*z/2
    lo,hi=0,t0
    for _ in range(200):
        m=(lo+hi)/2
        if Q(m)>0: lo=m
        else: hi=m
    z=lo
    return dict(t0=t0, treq=1.2*t0, Mmax=A*(h+z)**3/6+B*(h+z)**2/2-C*z**3/6)
def pfahl(D,layers,qb,G,Q,bs='P'):   # γ_t = 1,40 in allen BS (EA-Pfähle); Einwirkungen nach BS (DIN 1054 Tab. A 2.1)
    gG,gQ={'P':(1.35,1.5),'T':(1.2,1.3),'A':(1.1,1.1)}[bs]
    Rk=qb*math.pi*D*D/4+sum(q*math.pi*D*t for t,q in layers); return dict(Rk=Rk, Rd=Rk/1.4, Ed=gG*G+gQ*Q)
def brunnen(k,H,n,A,rw,Q,s0):
    Q/=1000; s=s0
    for _ in range(5000):
        R=max(3000*s*math.sqrt(k),1.5*A); v=H*H-n*Q/(math.pi*k)*math.log(R/A)
        sn=H-math.sqrt(v)
        if abs(sn-s)<1e-12: break
        s=0.5*(s+sn)
    R=max(3000*s*math.sqrt(k),1.5*A)
    sm=math.log(R/rw)+sum(math.log(R/max(2*A*math.sin(math.pi*j/n),rw)) for j in range(1,n))
    hw=math.sqrt(H*H-Q/(math.pi*k)*sm)
    return dict(s=s, R=R, hw=hw, QF=2*math.pi*rw*hw*math.sqrt(k)/15*1000)
S1={('ohne','mittel','B'):0.067,('erhoeht','leicht','A'):0.098,('hoch','schwer','C'):0.160}
def sommer(AG,Aw,g,fc,S1v,nord=False,glas=False,kuehl=0):
    Sv=Aw*g*fc/AG; f=Aw/AG; Sz=S1v+0.060-0.231*f+(0.03 if glas else 0)+(0.10 if nord else 0)+kuehl
    return dict(Sv=Sv, Sz=Sz)

async def res(pg, go, vals={}):
    await pg.evaluate(go); await pg.wait_for_timeout(40)
    for k,v in vals.items(): await pg.evaluate(f"$('{k}').value='{v}'; $('{k}').dispatchEvent(new Event('change',{{bubbles:true}})); run()")
    return await pg.evaluate("LAST && LAST.res ? Object.fromEntries(Object.entries(LAST.res).filter(([k,v])=>typeof v==='number' || typeof v==='boolean' || v===null)) : null")
async def checks(pg): return await pg.evaluate("Object.fromEntries(LAST.res.C.map(c=>[c.id,[c.eta,c.ok,!!c.info]]))")
async def fresh(pg): await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(150)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1400,'height':1000}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(SIZE); await fresh(pg)
        # Stütze zweiachsig
        for vals,args,tag in [({},(400,400,30,1500,120,80,3,20,10),'40/40, N = 1500'),({'in-h':'50','sz-N':'600','sz-My':'200','sz-Mz':'60','sz-n':'4','sz-ds':'16'},(400,500,30,600,200,60,4,16,10),'40/50, N = 600'),({'sz-N':'2900'},(400,400,30,2900,120,80,3,20,10),'N = 2900 (a > 1,5)')]:
            await fresh(pg); r=await res(pg, GO['zweiachsig'], vals); e=zweiachsig(*args)
            check(f'Stütze zweiachsig {tag}: M_Rd,y, M_Rd,z, a, Interaktion', near(r['MRy'],e['MRy'],3e-3) and near(r['MRz'],e['MRz'],3e-3) and near(r['a'],e['a']) and near(r['ia'],e['ia'],5e-3),
                  (round(r['MRy'],1), round(e['MRy'],1), round(r['MRz'],1), round(e['MRz'],1), round(r['ia'],4), round(e['ia'],4)))
        # Platte zweiachsig
        await fresh(pg)
        for vals,args in [({},(5,6.5,12,200,30,2.9,10,150,10,200)),({'pz-lx':'6','pz-ly':'6','in-h':'22','pz-q':'15'},(6,6,15,220,30,2.9,10,150,10,200)),({'pz-lx':'7.5','pz-ly':'4.5'},(7.5,4.5,12,200,30,2.9,10,150,10,200))]:
            await fresh(pg); r=await res(pg, GO['platte2'], vals); e=platte2(*args); C=await checks(pg)
            check(f'Platte {args[0]} × {args[1]} m: m_x, m_y nach Marcus und a_s,erf', near(r['mx'],e['mx']) and near(r['my'],e['my']) and near(r['X']['Areq'] if isinstance(r.get('X'),dict) else C['pzx'][0]*r['ax'], e['Ax']), (round(r['mx'],3), round(e['mx'],3), round(r['my'],3), round(e['my'],3)))
        check('quadratische Platte: m = q·l²/27,4 (Marcus) ≈ Czerny 1/27,2', near(platte2(6,6,1,200,30,2.9,10,150,10,200)['mx'], 36/27.43, 2e-3))
        # Stirnplatte
        await fresh(pg)
        r=await res(pg, GO['stirnplatte']); e=stirnplatte(300,150,7.1,10.7,628.4,235,20,150,20,1000,0.5,90,40,5)
        check('Stirnplatte IPE 300, t_p = 20, M20 10.9: F_Rd und M_j,Rd', near(r['Ft'],e['Ft']) and near(r['Mj'],e['Mj']), (round(r['Mj'],2), round(e['Mj'],2)))
        r=await res(pg, GO['stirnplatte'], {'sp-tp':'12','sp-kl':'8.8','sp-prof':'IPE 400'}); e=stirnplatte(400,180,8.6,13.5,1307.1,235,12,150,20,800,0.6,90,40,5)
        check('dünne Platte 12 mm, 8.8, IPE 400: Modus 1 maßgebend', near(r['Mj'],e['Mj']) and near(r['Ft'],r['FT1']), (round(r['Mj'],2), round(e['Mj'],2)))
        # Verbund
        await fresh(pg)
        r=await res(pg, GO['verbund']); e=verbund(31000,600,100,11500,160,280,6,50000,100,60,40)
        check('Holz-Beton-Verbund: γ₁, (EI)_ef, Spannungen, Verbinderkraft', near(r['g1'],e['g1']) and near(r['EI'],e['EI']) and near(r['s2'],e['s2']) and near(r['sc'],e['sc']) and near(r['F1'],e['F1']),
              (round(r['g1'],4), round(e['g1'],4), round(r['F1']/1e3,3), round(e['F1']/1e3,3)))
        r=await res(pg, GO['verbund'], {'vb-K':'1e9'});
        check('sehr steife Verbinder: γ₁ → 1, (EI)_ef → starrer Verbund', r['g1']>0.999 and near(r['EI'],r['EIstarr'],2e-3), (r['g1'], r['EI']/r['EIstarr']))
        # Spundwand
        await fresh(pg)
        r=await res(pg, GO['spundwand']); e=blum(4,10,32.5,18.5)
        check('Spundwand h = 4 m, Sand: t₀, t_erf, M_max', near(r['t0'],e['t0']) and near(r['treq'],e['treq']) and near(r['Mmax'],e['Mmax']), (round(r['t0'],3), round(e['t0'],3), round(r['Mmax'],1), round(e['Mmax'],1)))
        r=await res(pg, GO['spundwand'], {'sq-bs':'T','sq-h':'3','sq-q':'0'}); e=blum(3,0,32.5,18.5,1.2,1.3,1.3)
        check('BS-T, h = 3 m, ohne Auflast', near(r['t0'],e['t0']) and near(r['Mmax'],e['Mmax']), (round(r['t0'],3), round(e['t0'],3)))
        # Pfahl
        await fresh(pg)
        r=await res(pg, GO['pfahl']); e=pfahl(0.9,[(4,60),(5,90)],2500,1200,400)
        check('Bohrpfahl: R_c,k, R_c,d, E_c,d', near(r['Rk'],e['Rk']) and near(r['Rd'],e['Rd']) and near(r['Ed'],e['Ed']), (round(r['Rk'],1), round(e['Rk'],1)))
        r=await res(pg, GO['pfahl'], {'pf-t3':'2','pf-q3':'120','pf-bs':'T'}); e=pfahl(0.9,[(4,60),(5,90),(2,120)],2500,1200,400,'T')
        check('drei Schichten, BS-T (γ_t = 1,40, γ_G 1,20 / γ_Q 1,30)', near(r['Rd'],e['Rd']) and near(r['Ed'],e['Ed']), (round(r['Rd'],1), round(e['Rd'],1), round(r['Ed'],1)))
        # Brunnen
        await fresh(pg)
        for vals,args in [({},(5e-4,12,6,15,0.2,8,3)),({'gb-n':'8','gb-Q':'6','gb-A':'20','gb-k':'0.001'},(1e-3,12,8,20,0.2,6,3))]:
            r=await res(pg, GO['brunnen'], vals); e=brunnen(*args)
            check(f'Brunnen n = {args[2]}, Q = {args[5]} l/s: R, s, h_w, Q_F', near(r['s'],e['s'],1e-4) and near(r['R'],e['R'],1e-4) and near(r['hw'],e['hw'],1e-4) and near(r['QF'],e['QF'],1e-3), (round(r['s'],4), round(e['s'],4), round(r['QF'],3), round(e['QF'],3)))
        # Sommer
        await fresh(pg)
        r=await res(pg, GO['sommer']); e=sommer(25,6,0.6,0.3,0.067)
        check('Sommer: S_vorh, S_zul (B, mittel, ohne Nachtlüftung)', near(r['Sv'],e['Sv']) and near(r['Sz'],e['Sz']), (round(r['Sv'],4), round(r['Sz'],4), round(e['Sz'],4)))
        r=await res(pg, GO['sommer'], {'sx-kl':'A','sx-bau':'leicht','sx-nl':'erhoeht','sx-glas':'1','sx-ori':'nord'}); e=sommer(25,6,0.6,0.3,0.098,True,True)
        check('A, leicht, erhöhte Nachtlüftung, Sonnenschutzglas, Nord', near(r['Sz'],e['Sz']), (round(r['Sz'],4), round(e['Sz'],4)))
        await fresh(pg); r=await res(pg, GO['sommer'], {'sx-kl':'C','sx-bau':'schwer','sx-nl':'hoch','sx-kuehl':'1','sx-fcs':'x','sx-fc':'0.5'}); e=sommer(25,6,0.6,0.5,0.160,kuehl=0.06)
        check('C, schwer, hohe Nachtlüftung, passive Kühlung, F_C eigener Wert', near(r['Sz'],e['Sz']) and near(r['Sv'],e['Sv']), (round(r['Sz'],4), round(e['Sz'],4)))
        # Abhilfe
        CASES=[('zweiachsig',{'sz-My':'220'},'szia','sz-n'),('platte2',{'pz-sx':'35'},'pzx','pz-sx'),('stirnplatte',{'sp-M':'72'},'spm','sp-tp'),('verbund',{'vb-s':'200'},'vbvm','vb-s'),
               ('spundwand',{'sq-t':'5'},'sqt','sq-t'),('pfahl',{'pf-G':'2000'},'pfnw','pf-t2'),('brunnen',{'gb-Q':'3'},'gbs','gb-Q'),('sommer',{'sx-fcs':'1'},'sxnw','sx-fcs')]
        for mode,vals,cid,lev in CASES:
            await fresh(pg); await res(pg, GO[mode], vals)
            await pg.wait_for_function("document.querySelector('.fixbox') || !document.querySelector('#chk-table .tag.bad')", timeout=15000)
            fx=dict(await pg.evaluate(f"(LAST.res.C.find(c=>c.id==='{cid}').fix||[]).map(f=>[f.id,f.v])"))
            box=await pg.evaluate(f"(document.querySelector('#n-{cid} .fixbox')||{{}}).innerText||''")
            check(f'Abhilfe {mode}: Ursache und Stellschraube {lev}', 'Warum nicht erfüllt?' in box and lev in fx, fx)
            if lev in fx:
                await pg.evaluate(f"document.querySelector('#n-{cid} .fixbox button[data-fix=\"{lev}\"]').click()"); await pg.wait_for_timeout(120)
                check(f'Abhilfe {mode}: „Übernehmen“ erfüllt {cid}', await pg.evaluate(f"LAST.res.C.find(c=>c.id==='{cid}').ok"))
        # Spundwand-Abhilfe gegen Handrechnung
        await fresh(pg); await res(pg, GO['spundwand'], {'sq-t':'5'})
        await pg.wait_for_function("document.querySelector('.fixbox')", timeout=15000)
        v=await pg.evaluate("LAST.res.C.find(c=>c.id==='sqt').fix.find(f=>f.id==='sq-t').v")
        check('Abhilfe Spundwand: t = nächste 0,1 m über 1,2·t₀', near(v, math.ceil(blum(4,10,32.5,18.5)['treq']*10-1e-9)/10), v)
        # Bericht, Positionen
        await fresh(pg); ok=True
        for m,go in GO.items():
            await pg.evaluate(go); await pg.wait_for_timeout(40); rep=await pg.evaluate("buildReport()")
            if not ('<h1>' in rep and 'Eingaben' in rep and 'Zusammenfassung' in rep and '<svg' in rep): ok=False
        check('Bericht für alle 8 neuen Modi', ok)
        await pg.evaluate(GO['stirnplatte']+"; $('sp-prof').value='HEB 300'; run(); savePos()")
        await pg.evaluate(GO['sommer']+"; $('sx-AG').value='31'; run(); savePos()")
        await pg.evaluate(GO['zweiachsig']+"; $('sz-N').value='999'; run(); savePos()")
        await pg.evaluate("loadPos(0)"); await pg.wait_for_timeout(80)
        check('Position Stirnplatte (Profilauswahl) speichern und laden', await pg.evaluate("MAT==='stahl' && STMODE==='stirnplatte' && $('sp-prof').value==='HEB 300'"))
        await pg.evaluate("loadPos(1)"); await pg.wait_for_timeout(80)
        check('Position Sommer laden (Schichtkarte ausgeblendet)', await pg.evaluate("MAT==='bauph' && BPMODE==='sommer' && $('sx-AG').value==='31' && $('bp-lay-card').style.display==='none'"))
        await pg.evaluate("loadPos(2)"); await pg.wait_for_timeout(80)
        check('Position Stütze zweiachsig laden', await pg.evaluate("MAT==='beton' && TYP==='zweiachsig' && $('sz-N').value==='999' && $('beton-sz').style.display===''"))
        # Englisch
        await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(250)
        GER=re.compile(r'[äöüÄÖÜß]|\b(und|der|die|das|mit|nicht|oder|für|bei|nach|ist|wird|vorhanden|erf|vorh|zul|Nachweis|Stäbe|Platte|Brunnen|Pfahl|Schicht|Querschnitt|unten|oben|ab)\b')
        left={}
        for m,go in GO.items():
            await pg.evaluate(go); await pg.wait_for_timeout(60)
            t=await pg.evaluate("[...['summary','chk-table','details','fig','reinf-line','page-title','page-sub'].map(i=>['page-title','page-sub'].includes(i) ? document.getElementById(i).textContent : document.getElementById(i).innerText), (()=>{const d=document.createElement('div'); d.innerHTML=trFig(buildReport()); return d.innerText})()].join('\\n')")
            for line in t.replace('EA-Pfähle','EA-Piles').split('\n'):
                mm=GER.search(line)
                if mm: left.setdefault(m, line[max(0,mm.start()-30):mm.start()+40])
        check('EN: Ergebnis, Rechenweg, Abbildung und Bericht ohne deutsche Reste (8 Modi)', not left, left)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
