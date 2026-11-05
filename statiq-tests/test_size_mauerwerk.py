# statiq·size: Mauerwerk (DIN EN 1996-1-1 / DIN EN 1996-3 mit NA) — unabhängig nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
# f_k nach DIN EN 1996-3/NA, Anhang NA.D — Tabellenwerte von Hand aus mauerwerksbau-lehre.de (Anhang f_k) und KS-Verband (Tafeln 4/1–4/3) abgeschrieben
_C=[4,6,8,10,12,16,20,28,36,48,60]
NA={'A1':(_C,{2.5:[2.1,2.7,3.1,3.5,3.9,4.6,5.3,5.3,5.3,5.3,5.3],5:[2.4,3.1,3.9,4.5,5.0,5.9,6.7,6.7,6.7,6.7,6.7],10:[2.9,3.7,4.4,5.0,5.6,6.6,7.5,9.2,10.6,12.5,14.3],20:[None,None,None,5.6,6.3,7.4,8.4,10.3,11.9,14.1,16.0]}),
    'A2':([4,6,8,10,12,16,20],{2.5:[1.7,2.2,2.5,2.8,3.1,3.1,3.1],5:[2.0,2.5,3.2,3.6,4.0,4.0,4.0],10:[2.3,2.9,3.5,4.0,4.5,4.5,4.5],20:[2.6,3.3,4.0,4.5,5.0,5.0,5.0]}),
    'A3':(_C,{2.5:[2.8,3.6,4.2,4.8,5.4,6.4,7.2,8.8,10.2,10.2,10.2],5:[None,4.0,4.7,5.4,6.0,7.1,8.1,9.9,11.4,11.4,11.4],10:[None,None,None,6.0,6.7,8.0,9.1,11.0,12.7,15.1,15.1],20:[None,None,None,None,7.5,8.9,10.1,12.4,14.3,16.9,16.9]}),
    'LV':([2,4,6,8,10,12,16,20],{2.5:[1.5,2.5,3.4,3.4,3.4,3.4,3.4,3.4],5:[1.6,2.7,3.7,4.5,5.4,6.1,6.1,6.1],10:[1.8,3.0,4.0,5.0,5.9,6.7,8.3,9.8],20:[1.8,3.0,4.0,5.0,5.9,6.7,8.3,9.8]}),
    'LH':([2,4,6,8,10,12],{2.5:[1.4,2.2,2.9,2.9,2.9,2.9],5:[1.5,2.4,3.1,3.7,4.3,4.8],10:[1.7,2.6,3.3,4.0,4.6,5.1],20:[1.7,2.6,3.3,4.0,4.6,5.1]}),
    'KSP':(_C,[2.9,4.0,5.0,6.0,7.0,8.8,10.5,13.8,13.8,13.8,13.8]),'KSLP':(_C,[2.9,3.7,4.4,5.0,5.6,6.6,7.6,7.6,7.6,7.6,7.6]),
    'KSXL':(_C,[2.9,4.0,5.0,6.0,9.4,11.2,12.9,16.0,16.0,16.0,16.0]),'PP':([2,4,6,8],[1.8,3.0,4.1,5.1]),'PHLZ':([6,8,10,12,16,20],[3.1,3.7,4.2,4.7,5.5,6.3])}
TAB={'z1':{'nm':'A3'},'z2':{'nm':'A1','dm':'PHLZ'},'zw':{'nm':'A2'},'k1':{'nm':'A3','dm':'KSP'},'k2':{'nm':'A1','dm':'KSLP'},'kx':{'dm':'KSXL'},'p1':{'dm':'PP'},'l1':{'nm':'LV'},'l2':{'nm':'LH'}}
GRP={'z1':1,'z2':2,'zw':2,'k1':1,'k2':2,'kx':1,'p1':1,'l1':1,'l2':2}
def fk(art,m,fb,fm):
    t=TAB[art].get(m)
    if not t: return None
    cls,vals=NA[t]; i=max([k for k,c in enumerate(cls) if fb>=c], default=None)
    if i is None: return None
    if m=='dm': return vals[i]
    ms=[x for x in (2.5,5,10,20) if fm>=x]
    return vals[ms[-1]][i] if ms else None
def druck(fkv,t,h,l,lage,decke,a,lf,N):
    A=l*t/1000; fd=0.85*fkv/1.5*(0.8 if A<0.1 else 1)
    rho=1.0 if decke=='hb' else (0.75 if t<=175 else 0.9 if t<=250 else 1.0); lam=rho*h*1000/t
    P2=0.85*a/t-0.0011*lam**2
    P1=None if lage=='zw' else 0.333*a/t if lage=='dach' else min(((1.6-lf/6) if fkv>=1.8 else (1.6-lf/5))*a/t, 0.9*a/t)   # DIN EN 1996-3/NA: mit a/t
    Phi=min(P2, P1 if P1 is not None else 9); return N/(Phi*fd*A*1000), Phi
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('mauer'); setMwMode('druck')")
        s=await pg.inner_text('#summary'); check('Standard Wand auf Druck erfüllt', 'Alle Nachweise erfüllt' in s, s)
        # f_k aus den NA-Tabellen (seit size v0.7.21); Sollwerte von Hand: 5,0 · 10,5 · 4,2 · 7,5 · 3,0 · 6,0 (Klasse 15 → 12) · 2,0 (HLzW 4, M 10 → 2,3? nein M 5 → 2,0)
        for art,m,fb,fm in [('z2','nm',12,5),('k1','dm',20,0),('z2','dm',10,0),('k1','nm',12,25),('p1','dm',4,0),('k1','nm',15,7),('zw','nm',4,5),('kx','dm',12,0),('l2','nm',8,10)]:
            await pg.evaluate(f"$('mw-own').checked=false; $('mw-art').value='{art}'; $('mw-m').value='{m}'; $('mw-fb').value={fb}; $('mw-fm').value={fm or 5}; run()")
            g=await pg.evaluate("LAST.I.M.fk"); r=fk(art,m,fb,fm or 5)
            check(f'f_k {art}, {m}, Klasse {fb}, M {fm or "DM"} = {r} N/mm² (NA-Tabelle)', g==r, f'{g} N/mm²')
        hand={('z2','nm',12,5):5.0,('k1','dm',20,0):10.5,('z2','dm',10,0):4.2,('k1','nm',12,25):7.5,('p1','dm',4,0):3.0,('k1','nm',15,7):6.0,('zw','nm',4,5):2.0,('kx','dm',12,0):9.4,('l2','nm',8,10):4.0}
        check('Test-Tabelle stimmt mit den von Hand gelesenen Werten', all(fk(a,m,b,f or 5)==v for (a,m,b,f),v in hand.items()))
        for art,m,fb,fm,word in [('p1','nm',4,5,'keine NA-Tabelle'),('z1','nm',4,10,'nicht vorgesehen'),('k1','nm',2,5,'kleiner als'),('k1','nm',12,1,'M 2,5')]:
            await pg.evaluate(f"$('mw-own').checked=false; $('mw-art').value='{art}'; $('mw-m').value='{m}'; $('mw-fb').value={fb}; $('mw-fm').value={fm}; run()")
            check(f'ohne NA-Wert ({art}, {m}, {fb}, M {fm}): Hinweis statt Rechnung', word in await pg.inner_text('#summary') or word in await pg.inner_text('body'), (await pg.inner_text('#summary'))[:90])
        cases={'Außenwand 240, Stahlbetondecke, Standard':('z2','nm',12,5,240,2.625,1.0,'end','sb',240,5.0,210),
               'Innenwand 175 KS Dünnbett, Zwischenauflager':('k1','dm',20,0,175,2.75,1.0,'zw','sb',175,0,380),
               'Dachgeschoss Endauflager (Φ₁ = 0,333)':('z2','nm',12,5,300,2.5,1.0,'dach','sb',300,5.5,150),
               'Holzbalkendecke, Teilauflager a = 2/3 t, kurze Wand':('z1','nm',20,10,240,2.5,0.365,'end','hb',160,4.0,60),
               'f_k = 1,8 (Porenbeton 2), Endauflager':('p1','dm',2,0,365,2.6,1.0,'end','sb',300,5.0,90),
               'f_k < 1,8 (Hbl 2, M 2,5), Endauflager':('l2','nm',2,2.5,300,2.5,1.0,'end','sb',300,5.0,60)}
        for name,(art,m,fb,fm,t,h,l,lage,decke,a,lf,N) in cases.items():
            await pg.evaluate(f"$('mw-own').checked=false; $('mw-art').value='{art}'; $('mw-m').value='{m}'; $('mw-fb').value={fb}; $('mw-fm').value={fm or 5}; $('md-t').value={t}; $('md-h').value={h}; $('md-l').value={l}; $('md-lage').value='{lage}'; $('md-decke').value='{decke}'; $('md-a').value={a}; $('md-lf').value={lf}; $('md-N').value={N}; run()")
            eta,Phi=druck(fk(art,m,fb,fm or 5),t,h,l,lage,decke,a,lf,N)
            g=await pg.evaluate("[LAST.res.C.find(c=>c.id==='mdn').eta, LAST.res.Phi]")
            check(f'Druck: {name}', abs(g[0]-eta)<1e-9 and abs(g[1]-Phi)<1e-12, f'Φ = {Phi:.3f}, η = {eta:.3f}')
        await pg.evaluate("$('md-h').value=3.2; $('md-t').value=175; $('md-a').value=175; run()")
        check('h = 3,20 m > 2,75 m → Anwendungsgrenze verletzt', not await pg.evaluate("LAST.res.C.find(c=>c.id==='mdgr').ok"))
        # eigener f_k
        await pg.evaluate("$('mw-own').checked=true; $('mw-fk').value=3.4; run()")
        check('eigener f_k wird verwendet', abs(await pg.evaluate("LAST.I.M.fd")-0.85*3.4/1.5)<1e-12)
        # Teilflächenpressung
        await pg.evaluate("setMwMode('teil'); $('mw-own').checked=true; $('mw-fk').value=6; $('mw-art').value='k1'")
        for name,(t,hc,lb,bb,a1,lw,N) in {'Auflager am Wandende (a₁ = 0)':(240,2.5,175,240,0,2.0,90),'Auflager mitten in der Wand':(240,2.5,200,240,800,3.0,150),'hohe Last, kurze Wand':(175,1.0,300,175,100,0.8,250)}.items():
            await pg.evaluate(f"$('mt-t').value={t}; $('mt-hc').value={hc}; $('mt-lb').value={lb}; $('mt-bb').value={bb}; $('mt-a1').value={a1}; $('mt-lw').value={lw}; $('mt-N').value={N}; run()")
            fd=0.85*6/1.5; hcm=hc*1000; sp=hcm/(2*math.tan(math.radians(60)))
            lefm=lb+min(a1,sp)+min(lw*1000-a1-lb,sp); Ab=lb*bb; Aef=lefm*t
            b=(1+0.3*a1/hcm)*(1.5-1.1*Ab/Aef); b=min(max(b,1),min(1.25+a1/(2*hcm),1.5)); NRd=b*Ab*fd/1000
            g=await pg.evaluate("[LAST.res.beta, LAST.res.NRd]")
            check(f'Teilfläche: {name}', abs(g[0]-b)<1e-12 and abs(g[1]-NRd)<1e-9, f'β = {b:.3f}, N_Rdc = {NRd:.1f} kN')
        await pg.evaluate("$('mw-art').value='z2'; run()"); check('Lochsteine (Gruppe 2): β = 1', await pg.evaluate("LAST.res.beta")==1)
        # Kellerwand
        await pg.evaluate("setMwMode('keller')")
        for name,(t,h,he,bc,rho,Nmax,Nmin) in {'b_c ≥ 2h (β = 20)':(365,2.5,2.0,6.0,19,180,85),'h < b_c < 2h':(300,2.5,2.2,4.0,20,150,60),'b_c ≤ h (β = 40)':(240,2.4,2.0,2.0,19,120,40)}.items():
            await pg.evaluate(f"$('mk-t').value={t}; $('mk-h').value={h}; $('mk-he').value={he}; $('mk-bc').value={bc}; $('mk-rho').value={rho}; $('mk-Nmax').value={Nmax}; $('mk-Nmin').value={Nmin}; run()")
            beta=20 if bc>=2*h else 40 if bc<=h else 60-20*bc/h; nreq=rho*h*he**2/(beta*t/1000); nlim=t*(0.85*6/1.5)*0+t*0  # placeholder
            g=await pg.evaluate("[LAST.res.beta, LAST.res.nreq, LAST.res.nlim, LAST.I.M.fd]")
            nlim=t*g[3]/3
            check(f'Kellerwand {name}', abs(g[0]-beta)<1e-12 and abs(g[1]-nreq)<1e-9 and abs(g[2]-nlim)<1e-9, f'β = {beta:.1f}, n_min,erf = {nreq:.1f} kN/m, n_max = {nlim:.1f} kN/m')
        # Schubwand
        await pg.evaluate("setMwMode('schub'); $('mw-own').checked=false; $('mw-art').value='k1'; $('mw-m').value='dm'; $('mw-fb').value=20; run()")
        for name,(l,t,h,lag,N,V,stoss) in {'Kragscheibe, ganz überdrückt':(3.0,175,2.75,'krag',180,25,False),'klaffende Fuge':(2.0,175,2.75,'krag',120,30,False),'oben eingespannt, Stoßfugen offen':(2.5,240,2.75,'ein',150,40,True)}.items():
            await pg.evaluate(f"$('mh-l').value={l}; $('mh-t').value={t}; $('mh-h').value={h}; $('mh-lag').value='{lag}'; $('mh-N').value={N}; $('mh-V').value={V}; $('mh-stoss').checked={str(stoss).lower()}; run()")
            M=V*h*(1 if lag=='krag' else 0.5); e=M/N; lc=l if e<=l/6 else 3*(l/2-e); sd=N/(t*lc)
            fvk0=(0.5 if stoss else 1)*0.40; fvk=min(fvk0+0.4*sd, 0.065*20); VRd=fvk/1.5*t*lc
            g=await pg.evaluate("[LAST.res.lc, LAST.res.VRd, LAST.res.e]")
            check(f'Schubwand {name}', abs(g[0]-lc)<1e-12 and abs(g[1]-VRd)<1e-9, f'l_c = {lc:.3f} m, V_Rd = {VRd:.1f} kN')
        for m,word in [('druck','Φ'),('teil','β'),('keller','Druckbogen'),('schub','Schub')]:
            await pg.evaluate(f"setMwMode('{m}'); run(); showReport()"); rp=await pg.inner_text('#report')
            check(f'Bericht {m}', word in rp)
        await pg.evaluate("setMwMode('keller'); $('mk-he').value=1.7; run(); save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden stellt Mauerwerk wieder her', await pg.evaluate("MAT==='mauer' && MWMODE==='keller' && $('mk-he').value==='1.7' && LAST.mode==='keller'"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
