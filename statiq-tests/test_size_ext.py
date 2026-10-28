# statiq·size v0.3: Stahl-Erweiterungen, Anschlüsse, Holz — im Browser, Sollwerte unabhängig in Python. Ohne Playwright: SKIP.
import os, sys, re, json, math, asyncio
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
src=open(os.path.join(HERE,'..','size.html'),encoding='utf-8').read()
PROF={p[0]:p for p in json.loads(re.search(r'const PROFILE = (\[\[.*?\]\]);',src).group(1))}
E,G=210000.,81000.

# ── Torsion: Differentialgleichung numerisch (Differenzenverfahren), unabhängig von der geschlossenen Lösung ──
def torsion_fd(It, Iw, L, art, val, n=4000):
    x=np.linspace(0,L,n+1); dx=x[1]-x[0]; m=np.zeros(n+1)
    if art=='T': m[n//2]=val/dx
    else: m[:]=val
    # E·Iw·ψ'' − G·It·ψ = −m  mit ψ = φ'', ψ(0)=ψ(L)=0
    N=n-1; main=np.full(N,-2*E*Iw/dx**2-G*It); off=np.full(N-1,E*Iw/dx**2)
    Amat=np.diag(main)+np.diag(off,1)+np.diag(off,-1); psi=np.zeros(n+1); psi[1:-1]=np.linalg.solve(Amat,-m[1:-1])
    A2=np.diag(np.full(N,-2/dx**2))+np.diag(np.full(N-1,1/dx**2),1)+np.diag(np.full(N-1,1/dx**2),-1)
    phi=np.zeros(n+1); phi[1:-1]=np.linalg.solve(A2,psi[1:-1])
    B=np.abs(E*Iw*psi).max(); Tt0=G*It*(phi[1]-phi[0])/dx
    return B, abs(Tt0)
def prof(n):
    _,h,b,tw,tf,r,A,Gk,Iy,Wely,Wply,iy,Iz,Welz,Wplz,iz=PROF[n]
    a1=-0.042+0.2204*tw/tf+0.1355*r/tf-0.0865*r*tw/tf**2-0.0725*tw**2/tf**2
    D1=((tf+r)**2+tw*(r+tw/4))/(2*r+tf)
    It=(2/3*b*tf**3+1/3*(h-2*tf)*tw**3+2*a1*D1**4-0.42*tf**4); Iw=tf*b**3/24*(h-tf)**2
    return dict(h=h,b=b,tw=tw,tf=tf,r=r,A=A*100,Iy=Iy*1e4,Iz=Iz*1e4,Wply=Wply*1e3,Wely=Wely*1e3,Wplz=Wplz*1e3,Welz=Welz*1e3,It=It,Iw=Iw)

# ── wirksamer Querschnitt: Faserintegration über ein Gitter (unabhängig von der Flächenbilanz der App) ──
def weff_grid(h,b,tw,tf,r,fy):
    eps=math.sqrt(235/fy); cw=h-2*tf-2*r; yTop=tf+r
    ny=6000; y=(np.arange(ny)+0.5)*h/ny; dy=h/ny
    width=np.where((y<tf)|(y>h-tf), b, tw).astype(float)
    # Ausrundung als Rechteckstreifen-Näherung NICHT berücksichtigen → nur Vergleich der Löcher-Logik: Brutto aus Tabelle korrigieren
    yc=h/2
    for _ in range(30):
        psi=(yc-(h-yTop))/(yc-yTop)
        if psi>-1: ks=7.81-6.29*psi+9.78*psi*psi if psi<0 else 8.2/(1.05+psi)
        else: ks=23.9 if psi==-1 else 5.98*(1-psi)**2
        lp=(cw/tw)/(28.4*eps*math.sqrt(ks))
        rho=1 if lp<=0.5+math.sqrt(0.085-0.055*psi) else min(1,(lp-0.055*(3+psi))/lp**2)
        bc=cw/(1-psi); beff=rho*bc; be1=0.4*beff
        w=width.copy(); hole=(y>yTop+be1)&(y<yTop+be1+(bc-beff)); w[hole]-=tw
        ycn=(w*y).sum()/w.sum()
        if abs(ycn-yc)<1e-4: break
        yc=ycn
    I=(w*(y-yc)**2).sum()*dy; Ig=(width*(y-h/2)**2).sum()*dy
    return I/max(yc,h-yc), Ig/(h/2), rho, psi

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto('file://'+HTML); await pg.wait_for_timeout(300)
        out=lambda: pg.evaluate("document.querySelector('.col-out').innerText + '\\n' + (()=>{ const d=document.createElement('div'); return (LAST&&LAST.res&&LAST.res.C||[]).flatMap(c=>c.steps).map(s=>{ d.innerHTML=s.replace(/^§/,''); return d.innerText||d.textContent; }).join('\\n'); })()")
        await pg.evaluate("setMat('stahl')")
        # seit size v0.7.13 liegen M_z, Torsion und Gurtlast unter „Erweitert“ in der Schnittgrößen-Karte: aufklappen
        await pg.wait_for_timeout(300); await pg.evaluate("document.querySelectorAll('.col-in .card.fold.closed').forEach(c=>c.classList.remove('closed')); const a=document.getElementById('st-adv'); if(a && a.classList.contains('k5-closed')) kragrK5.setClosed(a,false,true)")
        P=prof('IPE 300')
        # 1) Torsion Einzelmoment / Streckenmoment gegen Differenzenverfahren
        for art,val,lab in [('T',2.0,'Einzeltorsionsmoment 2 kNm'),('m',0.5,'Streckentorsion 0,5 kNm/m')]:
            await pg.select_option('#sn-tors',art); await pg.fill('#sn-Tw',str(val)); t=await out()
            B,Tt0=torsion_fd(P['It'],P['Iw'],6000,art, val*1e6 if art=='T' else val*1e3)
            Bapp=float(re.search(r'B = ([\d,]+) kNm²',t).group(1).replace(',','.'))
            Tapp=float(re.search(r'St\. Venant\) Tt = ([\d,]+) kNm',t).group(1).replace(',','.'))
            check(f'Torsion ({lab}): B = {B/1e9:.3f} kNm², Tt = {Tt0/1e6:.2f} kNm', abs(Bapp-B/1e9)<=0.002*max(1,B/1e9)+0.0015 and abs(Tapp-Tt0/1e6)<=0.011, f'App: {Bapp} / {Tapp}')
        await pg.select_option('#sn-tors','0')
        # 2) Biegung um z, Querschnitt (6.41) bei N = 0: (My/Mpl,y)² + (Mz/Mpl,z)¹
        await pg.fill('#sn-Mz','8'); t=await out()
        u=(90/(P['Wply']*235/1e6))**2+(8/(P['Wplz']*235/1e6))**1
        check(f'Zweiachsig (6.41): {de(u,3)}', f'= {de(u,3)} ≤ 1' in t)
        # 3) Lasteinleitung am Trägerende (Typ c), Handrechnung
        await pg.fill('#sn-Mz','0'); await pg.fill('#sn-F','120'); await pg.select_option('#sn-lage','c'); await pg.fill('#sn-ss','80'); await pg.fill('#sn-cE','0'); t=await out()
        hw=300-2*10.7; kF=min(6,2+6*80/hw); Fcr=0.9*kF*E*7.1**3/hw; m1=150/7.1
        def ly(m2):
            le=min(kF*E*7.1**2/(2*235*hw), 80)
            return min(80+2*10.7*(1+math.sqrt(m1+m2)), le+10.7*math.sqrt(m1/2+(le/10.7)**2+m2), le+10.7*math.sqrt(m1+m2))
        m2=0.02*(hw/10.7)**2; l=ly(m2); lF=math.sqrt(l*7.1*235/Fcr)
        if lF<=0.5: l=ly(0); lF=math.sqrt(l*7.1*235/Fcr)
        FRd=235*min(1,0.5/lF)*l*7.1/1.1/1000
        check(f'Lasteinleitung Typ c: kF = {de(kF,2)}, ly = {de(l,1)} mm, FRd = {de(FRd,1)} kN', f'≤ 6 = {de(kF,2)}' in t and f'ly = {de(l,1)} mm' in t and f'= {de(FRd,1)} kN' in t)
        await pg.fill('#sn-F','0')
        # 4) wirksamer Querschnitt: synthetisches schlankes Profil (Steg Klasse 4 unter Biegung) direkt in der App
        h,b,tw,tf,r,fy=1000.,300.,6.,20.,0.,355
        A=(2*b*tf+(h-2*tf)*tw)/100; Iy=(b*h**3-(b-tw)*(h-2*tf)**3)/12/1e4
        app=await pg.evaluate(f"""(()=>{{ const P={{h:{h},b:{b},tw:{tw},tf:{tf},r:{r},A:{A},Iy:{Iy}}}; const e=effektiv(P,{fy}); return [e.Weff, e.rw, e.psi]; }})()""")
        W,Wg,rho,psi=weff_grid(h,b,tw,tf,r,fy)
        check(f'W_eff synthetisch (h/t_w = 160): {W/1e3:.0f} cm³, ρ = {rho:.3f}', abs(app[0]-W)/W<0.003 and abs(app[1]-rho)<0.003, f'App {app[0]/1e3:.1f} / ρ {app[1]:.3f} / ψ {app[2]:.3f}')
        # 5) IPE 600 S355 mit N = 1500 kN: Klasse 4, A_eff
        await pg.select_option('#sn-prof','IPE 600'); await pg.select_option('#sn-stahl','S355'); await pg.fill('#sn-N','1500'); await pg.fill('#sn-M','100'); t=await out()
        P6=prof('IPE 600'); eps=math.sqrt(235/355); cw=600-38-48; lp=(cw/12)/(28.4*eps*2); rho=1 if lp<=0.673 else (lp-0.22)/lp**2
        Aeff=P6['A']-(1-rho)*cw*12
        check(f'IPE 600 Klasse 4: A_eff = {de(Aeff/100,2)} cm² (ρ = {de(rho,3)})', 'Querschnittsklasse 4' in t and f'Aeff = {de(Aeff/100,2)} cm²' in t)
        await pg.select_option('#sn-prof','IPE 300'); await pg.select_option('#sn-stahl','S235'); await pg.fill('#sn-N','0'); await pg.fill('#sn-M','90')
        # ── Anschluss ──
        await pg.evaluate("setStMode('anschluss')")
        await pg.fill('#an-n1','2'); await pg.fill('#an-n2','2'); await pg.fill('#an-e1','40'); await pg.fill('#an-e2','35'); await pg.fill('#an-p1','65'); await pg.fill('#an-p2','70')
        await pg.fill('#an-V','200'); await pg.fill('#an-N','60'); await pg.select_option('#an-ms','2'); t=await out()
        d,As,d0,fub,fu,tt=20,245,22,800,360,10
        Fv=2*0.6*fub*As/1.25/1000
        def fb(end,edge):
            ad=40/(3*d0) if end else 65/(3*d0)-0.25; ab=min(ad,fub/fu,1)
            k1=min(2.8*35/d0-1.7,1.4*70/d0-1.7,2.5) if edge else min(1.4*70/d0-1.7,2.5)
            return k1*ab*fu*d*tt/1.25/1000
        F=[fb(i==0, True) for i in range(2) for j in range(2)]   # 2 Spalten → beide Randschrauben
        grp=sum(F) if all(Fv>=x for x in F) else 4*min(Fv,min(F))
        Ft=0.9*fub*As/1.25/1000; inter=200/4/Fv+60/4/(1.4*Ft)
        check(f'Schrauben 2×2 M20 8.8 zweischnittig: Gruppe = {de(grp,1)} kN', f'= {de(grp,1)} kN' in t)
        check(f'Abscheren + Zug: {de(inter,3)}', f'= {de(inter,3)} ≤ 1' in t)
        await pg.fill('#an-e1','20'); t=await out()
        check('e₁ = 20 mm < 1,2·d₀ → Abstände nicht erfüllt', 'Rand- und Lochabstände' in t and 'nicht erf' in t)
        await pg.fill('#an-e1','40')
        fvw=360/(math.sqrt(3)*0.8*1.25);
        check(f'Kehlnaht: F_w,Rd = {de(fvw*4,0)} N/mm', re.search(r'Fw,Rd = fvw,d·a = [\d,]+·4,0 = '+de(fvw*4,0)+' N/mm', t) is not None)
        # ── Holz ──
        await pg.evaluate("setMat('holz')")
        # Kippen: BSH GL24h 120/400, L = 7 m, L_K = 7 m, Gleichlast am oberen Rand
        await pg.select_option('#ho-art','bsh'); await pg.select_option('#ho-kl','GL24h'); await pg.fill('#ho-b','120'); await pg.fill('#ho-h','400'); await pg.fill('#ho-L','7')
        await pg.fill('#ho-Llt','7'); await pg.select_option('#ho-zg','1'); await pg.fill('#ho-M','40'); await pg.fill('#ho-V','23'); await pg.fill('#ho-F','23'); await pg.fill('#ho-lA','120'); t=await out()
        lef=0.9*7000+2*400
        def itr(b,h):
            s_,l_=min(b,h),max(b,h); S=sum(math.tanh(n*math.pi*l_/(2*s_))/n**5 for n in range(1,200,2)); return s_**3*l_/3*(1-192/math.pi**5*s_/l_*S)
        scrit=math.pi*math.sqrt(1.4*9600*400*120**3/12*540*itr(120,400))/(lef*120*400**2/6); lrel=math.sqrt(24/scrit)   # BSH: allgemeine Formel, NA-Faktor 1,4
        kcrit=1 if lrel<=0.75 else (1.56-0.75*lrel if lrel<=1.4 else 1/lrel**2)
        kh=min((600/400)**0.1,1.1); fmd=kh*0.8*24/1.3; sm=40e6/(120*400**2/6)
        check(f'Kippen BSH: l_ef = {lef:.0f} mm, k_crit = {de(kcrit,3)}, η = {de(sm/(kcrit*fmd),2)}', f'= {lef:.0f} mm' in t and f'= {de(kcrit,3)}' in t and f'σm,d = {de(sm,2)} N/mm² ≤ kcrit·fm,d = {de(kcrit*fmd,2)}' in t)
        check(f'Schub BSH: kcr = 2,5/3,5 = {de(2.5/3.5,3)}', f'kcr = 2,5/fv,k = {de(2.5/3.5,3)}' in t)
        # Knicken: Stütze C24 140/140, L = 3 m, N = 120 kN
        await pg.select_option('#ho-art','vh'); await pg.select_option('#ho-kl','C24'); await pg.fill('#ho-b','140'); await pg.fill('#ho-h','140'); await pg.fill('#ho-L','3')
        await pg.fill('#ho-Llt','0'); await pg.fill('#ho-M','0'); await pg.fill('#ho-V','0'); await pg.fill('#ho-F','0'); await pg.fill('#ho-N','120'); await pg.fill('#ho-MG','0'); await pg.fill('#ho-MQ','0'); t=await out()
        lam=3000/(140/math.sqrt(12)); lr=lam/math.pi*math.sqrt(21/7400); k=0.5*(1+0.2*(lr-0.3)+lr*lr); kc=1/(k+math.sqrt(k*k-lr*lr))
        sc=120e3/140**2; fc=0.8*21/1.3
        check(f'Knicken C24 140/140, L = 3 m: k_c = {de(kc,3)}, η = {de(sc/(kc*fc),3)}', f'kc,z = {de(kc,3)}' in t and f'= {de(sc/(kc*fc),3)} ≤ 1' in t)
        # Auto-Höhe: VH C24 b = 80, L = 4,5 m, M = 9, Durchbiegung → kleinste Höhe
        await pg.fill('#ho-N','0'); await pg.fill('#ho-b','80'); await pg.fill('#ho-L','4.5'); await pg.fill('#ho-M','9'); await pg.fill('#ho-V','8'); await pg.fill('#ho-F','8'); await pg.fill('#ho-lA','80')
        await pg.fill('#ho-MG','2.5'); await pg.fill('#ho-MQ','3.5'); await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#ho-auto'); t=await out()
        best=None
        for hh in [100,120,140,160,180,200,220,240,260,280]:
            khh=min((150/hh)**0.2,1.3) if hh<150 else 1; ok=9e6/(80*hh*hh/6) <= khh*0.8*24/1.3 and 1.5*8e3/(0.5*80*hh) <= 0.8*4/1.3 and 8e3/(80*110) <= 1.5*0.8*2.5/1.3
            Iyy=80*hh**3/12; wG=5/48*2.5e6*4500**2/(11000*Iyy); wQ=5/48*3.5e6*4500**2/(11000*Iyy)
            ok = ok and wG+wQ<=15 and wG*1.6+wQ*(1+0.3*0.6)<=22.5 and (wG+0.3*wQ)*1.6<=15
            if ok: best=hh; break
        hsel=await pg.evaluate("document.getElementById('ho-h').value")
        check(f'Holz automatische Höhe: h = {best} mm', str(best)==hsel and 'Alle Nachweise erfüllt' in t, hsel)
        # Bericht + Positionen
        await pg.click('text=Bericht ansehen'); r=await pg.evaluate("document.getElementById('report').innerText")
        check('Bericht Holz', 'DIN EN 1995-1-1' in r and 'ZUSAMMENFASSUNG' in r.upper()); await pg.click('text=Zurück zur Eingabe')
        await pg.evaluate('mulyAltProj()'); await pg.click('#proj-panel >> text=Speichern'); await pg.evaluate("setMat('stahl')"); await pg.evaluate("setStMode('anschluss')"); await pg.evaluate('mulyAltProj()'); await pg.click('#proj-panel >> text=Speichern')
        await pg.evaluate('mulyAltProj()'); await pg.click('.pos-item:nth-child(1) >> text=Laden')
        m=await pg.evaluate("MAT")
        check('Positionen: Holz und Anschluss speichern, Holz lädt zurück', m=='holz' and await pg.evaluate("document.querySelectorAll('.pos-item').length")==2, m)
        await pg.evaluate('mulyAltProj()'); await pg.click('.pos-item:nth-child(2) >> text=Laden')
        check('Anschluss-Position lädt in Stahl → Anschluss', await pg.evaluate("MAT+'/'+STMODE")=='stahl/anschluss')
        await pg.evaluate("$('proj-panel').classList.remove('open')"); await pg.click('text=Bericht ansehen'); r=await pg.evaluate("document.getElementById('report').innerText")
        check('Bericht Anschluss', 'DIN EN 1993-1-8' in r and 'Schraubenbild' in r)
        check('Keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:',fails)
