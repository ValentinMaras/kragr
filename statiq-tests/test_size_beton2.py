# statiq·size v0.4: Druckbewehrung, Zugkraftdeckung/Staffelung, Stahlbetonstütze — im Browser, Sollwerte unabhängig in Python. Ohne Playwright: SKIP.
import os, sys, re, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:62}', str(info)[:160])
de = lambda v,d=2: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
fyd=500/1.15; Es=200000.; eyd=fyd/Es
def fcd(fck): return 0.85*fck/1.5
def A(ds): return math.pi*ds*ds/4

# Parabel-Rechteck-Block durch numerische Integration (unabhängig von den Formeln der App)
def block(xi):                       # ε_c = 3,5 ‰ am Rand → αR, ka
    y=np.linspace(0,1,200001)[:-1]+0.5/200000; e=3.5*(1-y)
    s=np.where(e<2, 1-(1-e/2)**2, 1.0); aR=s.mean(); ka=(s*y).mean()/aR
    return aR, ka

# Querschnitt mit symmetrischer Bewehrung: N(x), M(x) mit feinem Streifenmodell, Nulllinie per Bisektion
def qs(b,h,d2,As,fc):
    d=h-d2
    def eps(x,y):
        if x<=h:
            et=min(3.5, 25*x/(d-x)) if d>x else 3.5
            return et*(x-y)/x
        return 2*(x-y)/(x-3*h/7)
    def sc(e): return np.where(e<=0,0,np.where(e<2,fc*(1-(1-e/2)**2),fc))
    def ss(e): return np.sign(e)*np.minimum(Es*np.abs(e)/1000,fyd)
    def st(x):
        xc=min(x,h); y=(np.arange(4000)+0.5)*xc/4000; f=sc(eps(x,y))*b*xc/4000
        N=f.sum()+As/2*(ss(eps(x,d2))+ss(eps(x,d))); M=(f*(h/2-y)).sum()+As/2*(ss(eps(x,d2))-ss(eps(x,d)))*(h/2-d2)
        return N,M
    def atN(NEd):
        lo,hi=math.log(1e-4*h),math.log(1e5*h)
        for _ in range(80):
            m=(lo+hi)/2
            if st(math.exp(m))[0]<NEd: lo=m
            else: hi=m
        return st(math.exp((lo+hi)/2))[1]
    return atN

def stuetze(b,h,l,beta,N,M02,M01,phi,fck,d,As):
    fc=fcd(fck); Ac=b*h; l0=beta*l*1000; lam=l0/(h/math.sqrt(12)); n=N/(Ac*fc)
    lim=25 if n>=0.41 else 16/math.sqrt(n)
    e0=max(0.6*M02+0.4*M01,0.4*M02)*1e6/N; ei=min(1,2/math.sqrt(l))/200*l0/2
    om=As*fyd/(Ac*fc); Kr=min(1,max(0,(1+om-n)/(1+om-0.4))); Kphi=max(1,1+(0.35+fck/200-lam/150)*phi)
    e2=Kr*Kphi*eyd/(0.45*d)*l0**2/10 if lam>lim else 0
    Mend=M02*1e6+N*ei; Mmin=N*max(h/30,20)
    MEd=max(N*(e0+ei+e2),Mend,Mmin) if lam>lim else max(Mend,Mmin)
    return dict(lam=lam,lim=lim,e2=e2,MEd=MEd)

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+HTML); await pg.evaluate('localStorage.clear()'); await pg.reload(); await pg.wait_for_timeout(300)
        txt=lambda: pg.evaluate("document.getElementById('details').innerText + '\\n' + (()=>{ const d=document.createElement('div'); return (LAST&&LAST.res&&LAST.res.C||[]).flatMap(c=>c.steps).map(s=>{ d.innerHTML=s.replace(/^§/,''); return d.innerText||d.textContent; }).join('\\n'); })()")
        async def setv(i,v): await pg.fill('#'+i,str(v))
        async def sel(i,v): await pg.select_option('#'+i,str(v))

        # ── Druckbewehrung: b/h = 30/45, M = 330 kNm, von Hand 5 Ø 25 unten, 2 Ø 20 oben, Bügel Ø10 ──
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#in-auto'); await setv('in-h',45); await setv('in-M',330)
        await setv('in-n',5); await sel('in-ds',25); await sel('in-dsw',10); await setv('in-sw',15); await setv('in-n2',2); await sel('in-ds2',20)
        await pg.evaluate('run()'); t=await txt()
        aR,ka=block(0.45); xi=0.45; d=450-25-10-12.5; d2=20+10+10; fc=fcd(30)
        mul=aR*xi*(1-ka*xi); MRl=mul*300*d*d*fc/1e6; dM=330-MRl; x=xi*d; es2=3.5*(x-d2)/x; s2=min(Es*es2/1000,fyd)
        As2=dM*1e6/((d-d2)*s2); As1=(aR*xi*300*d*fc+dM*1e6/(d-d2))/fyd
        check(f'Druckbewehrung: M_Rd,lim = {de(MRl,1)} kNm, ΔM = {de(dM,1)}', f'= {de(MRl,1)} kNm' in t and f'= {de(dM,1)} kNm' in t)
        check(f'A_s2,erf = {de(As2/100)} cm², A_s1,erf = {de(As1/100)} cm²', f'= {de(As2/100)} cm²' in t and f'= {de(As1/100)} cm²' in t)
        check('2 Ø 20 oben = 6,28 cm² ≥ A_s2,erf, Nachweis erfüllt', '2 Ø 20 = 6,28 cm²' in t and await pg.evaluate("LAST.res.C.find(c=>c.id==='biegung').ok"))
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#in-auto'); await pg.evaluate('run()'); line=await pg.inner_text('#reinf-line'); s=await pg.inner_text('#summary')
        m=re.search(r'oben (\d) Ø (\d+) \(Druckbewehrung\)',line)
        check('Automatisch: Druckbewehrung gewählt, alle Nachweise erfüllt', m is not None and int(m.group(1))*A(int(m.group(2)))>=As2-1 and 'Alle Nachweise erfüllt' in s, line)

        # ── Zugkraftdeckung: Startwerte (30/60, l = 6 m, M = 220 kNm, 5 Ø 16) ──
        await pg.goto('file://'+HTML); await pg.evaluate('localStorage.clear()'); await pg.reload(); await pg.wait_for_timeout(300)
        t=await txt()
        z=float(re.search(r'max Fsd = [\d,]+·10³/([\d,]+)',t).group(1).replace(',','.'))
        zQ=float(re.search(r'al = z·cot θ/2 = ([\d,]+)·',t).group(1).replace(',','.'))
        al=zQ*1.2/2; L=6000; FR=3*A(16)*fyd; M=220e6
        # Endpunkt E numerisch: verschobene Linie M(x+al)/z = F_Rd,3
        xs=np.linspace(0,L/2-al,600001); Fx=4*M*(xs+al)/L*(1-(xs+al)/L)/z; xE=xs[np.argmax(Fx>=FR)]
        fbd=2.25*2.0/1.5; lbd=max(16/4*fyd/fbd,160,100)
        check(f'Staffelung: x_E = {de(xE/1000,2)} m, l_bd = {de(lbd,0)} mm', f'= {de(xE/1000,2)} m vom Auflager' in t and f'= {de(lbd,0)} mm (gerade' in t)
        check(f'Gestaffelte Stäbe: Länge {de((L-2*(xE-lbd))/1000,2)} m', f'= {de((L-2*(xE-lbd))/1000,2)} m' in t and 'Zugkraftdeckungsbild' in t)

        # ── Stütze: Startwerte 30/30, l = 4 m, β = 1, N = 1200, M02 = 40, M01 = 20 ──
        await pg.evaluate("setTyp('stuetze')"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#su-auto'); await setv('su-n',3); await sel('su-ds',16); await sel('su-dsw',8); await setv('su-sw',15)
        await pg.evaluate('run()'); t=await txt()
        dd=300-(max(20,26)+8+8)          # c_v = max(20; 26−8) = 20 … d2 = 20 + 8 + 8 = 36
        cv=max(10+10, (max(10,16,10)+10)-8); d2=cv+8+8; As=6*A(16)
        R=stuetze(300,300,4.0,1.0,1200e3,40,20,0,30,300-d2,As); MRd=qs(300,300,d2,As,fcd(30))(1200e3)
        check(f'Stütze: λ = {de(R["lam"],1)}, λ_lim = 25 → II. Ordnung', f'= {de(R["lam"],1)}' in t and 'schlanke Stütze' in t)
        check(f'Stütze: e2 = {de(R["e2"],1)} mm, M_Ed = {de(R["MEd"]/1e6,1)} kNm', f'= {de(R["e2"],1)} mm' in t and f'MEd = {de(R["MEd"]/1e6,1)} kNm' in t)
        check(f'Stütze: M_Rd(N_Ed) = {de(MRd/1e6,1)} kNm (Streifenmodell)', f'MRd(NEd) = {de(MRd/1e6,1)} kNm' in t, re.search(r'MRd\(NEd\) = [\d,]+',t))
        # A_s,erf durch Bisektion in Python (K_r abhängig von A_s)
        def ok(Ast):
            r=stuetze(300,300,4.0,1.0,1200e3,40,20,0,30,300-d2,Ast); return qs(300,300,d2,Ast,fcd(30))(1200e3)>=r['MEd']
        lo,hi=0,0.2*90000
        for _ in range(40):
            m=(lo+hi)/2
            if ok(m): hi=m
            else: lo=m
        got=float(re.search(r'As,tot,erf = ([\d,]+) cm²',t).group(1).replace(',','.'))
        check(f'Stütze: A_s,tot,erf = {de(hi/100)} cm² (±0,02)', abs(got-hi/100)<=0.02, got)
        # Kriechen: φef = 2 → Kφ > 1, größeres e2
        await setv('su-phi',2); await pg.evaluate('run()'); t=await txt()
        R2=stuetze(300,300,4.0,1.0,1200e3,40,20,2,30,300-d2,As)
        check(f'Kriechen φef = 2: e2 = {de(R2["e2"],1)} mm', f'= {de(R2["e2"],1)} mm' in t)
        await setv('su-phi',0)
        # gedrungene Stütze 40/40, l = 3 m, β = 0,7, N = 2500, M02 = 60, M01 = −30
        await setv('in-b',40); await setv('in-h',40); await setv('su-l',3); await sel('su-beta','0.7'); await setv('su-N',2500); await setv('su-M02',60); await setv('su-M01',-30)
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#su-auto'); await pg.evaluate('run()'); t=await txt(); s=await pg.inner_text('#summary')
        R3=stuetze(400,400,3.0,0.7,2500e3,60,-30,0,30,350,0)
        check(f'Gedrungen: λ = {de(R3["lam"],1)} ≤ 25, M_Ed = {de(R3["MEd"]/1e6,1)} kNm', 'gedrungene Stütze' in t and f'MEd = {de(R3["MEd"]/1e6,1)} kNm' in t)
        line=await pg.inner_text('#reinf-line'); mm=re.search(r'je Seite (\d) Ø (\d+)',line)
        nn,dsx=int(mm.group(1)),int(mm.group(2)); Amin=0.15*2500e3/fyd
        check('Gedrungen automatisch: A_s ≥ 0,15·N/f_yd, alle erfüllt', 2*nn*A(dsx)>=Amin and 'Alle Nachweise erfüllt' in s, line)
        # zu kleine Bewehrung von Hand → nicht erfüllt
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#su-auto'); await setv('su-n',2); await sel('su-ds',12); await setv('in-b',25); await setv('in-h',25); await setv('su-N',1800); await pg.evaluate('run()')
        s=await pg.inner_text('#summary'); check('Zu schwach bewehrt → nicht erfüllt', 'nicht erfüllt' in s, s)
        # Bericht und Positionsspeicher
        await pg.evaluate('showReport()'); r=await pg.inner_text('#report')
        check('Bericht Stütze: Modellstützenverfahren und Interaktionsdiagramm', 'Stahlbetonstütze' in r and 'Bemessungsmoment' in r and 'Interaktionsdiagramm' in r)
        await pg.evaluate('hideReport()'); await pg.reload(); await pg.wait_for_timeout(300)
        check('Neuladen: Typ Stütze bleibt erhalten', (await pg.input_value('#su-N'))=='1800' and await pg.is_visible('#beton-stuetze'))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
