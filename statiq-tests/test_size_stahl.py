# statiq·size, Stahlteil, im Browser (Playwright). Sollwerte unabhängig in Python nachgerechnet. Ohne Playwright: SKIP.
import os, sys, re, json, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:60}', str(info)[:160])
de = lambda v,d=2: f'{v+ (1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')

# ── Profilwerte aus size.html (Tabelle, mit der size rechnet) ──
src=open(os.path.join(HERE,'..','size.html'),encoding='utf-8').read()
PROF={p[0]:p for p in json.loads(re.search(r'const PROFILE = (\[\[.*?\]\]);',src).group(1))}
E,G,gM1=210000.,81000.,1.1
def prof(n):
    _,h,b,tw,tf,r,A,Gk,Iy,Wely,Wply,iy,Iz,Welz,Wplz,iz=PROF[n]
    # I_T: Näherung dünnwandig + Ausrundungsanteil (Kindmann); hier nur für M_cr benutzt
    a1=-0.042+0.2204*tw/tf+0.1355*r/tf-0.0865*r*tw/tf**2-0.0725*tw**2/tf**2
    D1=((tf+r)**2+tw*(r+tw/4))/(2*r+tf)
    It=(2/3*b*tf**3+1/3*(h-2*tf)*tw**3+2*a1*D1**4-0.42*tf**4)
    Iw=tf*b**3/24*(h-tf)**2
    Avz=max(A*100-2*b*tf+(tw+2*r)*tf, (h-2*tf)*tw)
    return dict(h=h,b=b,tw=tw,tf=tf,r=r,A=A*100,Iy=Iy*1e4,Iz=Iz*1e4,Wpl=Wply*1e3,Wel=Wely*1e3,iy=iy*10,iz=iz*10,It=It,Iw=Iw,Avz=Avz,G=Gk)
def chi(lb,a):
    if lb<=0.2: return 1.0
    ph=0.5*(1+a*(lb-0.2)+lb*lb); return min(1,1/(ph+math.sqrt(ph*ph-lb*lb)))
def mcr(P,L,C1,C2,zg):
    pz=math.pi**2*E*P['Iz']/L**2
    return C1*pz*(math.sqrt(P['Iw']/P['Iz']+L*L*G*P['It']/(math.pi**2*E*P['Iz'])+(C2*zg)**2)-C2*zg)
def chiLT(P,MRk,Mcr,kc):
    l=math.sqrt(MRk/Mcr); a=0.34 if P['h']/P['b']<=2 else 0.49
    if l<=0.4: return 1.0,l
    ph=0.5*(1+a*(l-0.4)+0.75*l*l); c=min(1,1/l**2,1/(ph+math.sqrt(ph*ph-0.75*l*l)))
    f=min(1,1-0.5*(1-kc)*(1-2*(l-0.8)**2)); return min(c/f,1,1/l**2),l

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto('file://'+HTML); await pg.wait_for_timeout(300)
        await pg.evaluate("setMat('stahl')")
        out=lambda: pg.evaluate("document.querySelector('.col-out').innerText + '\\n' + (()=>{ const d=document.createElement('div'); return (LAST&&LAST.res&&LAST.res.C||[]).flatMap(c=>c.steps).map(s=>{ d.innerHTML=s.replace(/^§/,''); return d.innerText||d.textContent; }).join('\\n'); })()")
        # A) Standard: IPE 300, S235, L = 6 m, M = 90 kNm, L_LT = 3 m, Last Obergurt, Gleichlast
        t=await out(); P=prof('IPE 300'); fy=235
        Mc=mcr(P,3000,1.127,0.454,P['h']/2)/1e6; MRk=P['Wpl']*fy/1e6; cL,lL=chiLT(P,MRk,Mc,0.94); Mb=cL*MRk/gM1
        check(f'IPE 300 Klasse 1 (Steg c/t = {de((300-2*10.7-30)/7.1,2)})', 'Querschnittsklasse = max(Gurt; Steg) = 1' in t and de((300-2*10.7-30)/7.1,2) in t)
        check(f'M_cr = {de(Mc,1)} kNm, λLT = {de(lL,3)}', f'= {de(Mc,1)} kNm' in t and f'= {de(lL,3)}' in t)
        check(f'χLT,mod = {de(cL,3)}, Mb,Rd = {de(Mb,1)} kNm', f'χLT,mod = χLT/f = {de(cL,3)}' in t and f'= {de(Mb,1)} kNm' in t)
        w=5/48*62e6*6000**2/(E*P['Iy'])
        check(f'Durchbiegung w = {de(w,1)} mm', f'= {de(w,1)} mm' in t)
        Vpl=P['Avz']*fy/math.sqrt(3)/1000
        check(f'V_pl,Rd = {de(Vpl,1)} kN', f'= {de(Vpl,1)} kN' in t)
        # B) Druck + Biegung, L = 4 m, L_LT = 4 m
        await pg.fill('#sn-N','300'); await pg.fill('#sn-L','4'); await pg.fill('#sn-Llt','4'); t=await out()
        NRk=P['A']*fy/1000; lam1=93.9
        lby=4000/P['iy']/lam1; lbz=4000/P['iz']/lam1; cy=chi(lby,0.21); cz=chi(lbz,0.34)
        Mc=mcr(P,4000,1.127,0.454,P['h']/2)/1e6; cL,_=chiLT(P,MRk,Mc,0.94)
        ny=300/(cy*NRk/gM1); nz=300/(cz*NRk/gM1); Cm=0.95; m=90/(cL*MRk/gM1)
        kyy=min(Cm*(1+(lby-0.2)*ny), Cm*(1+0.8*ny))
        kzy=max(1-0.1*lbz*nz/(Cm-0.25), 1-0.1*nz/(Cm-0.25)) if lbz>=0.4 else min(0.6+lbz, 1-0.1*lbz*nz/(Cm-0.25))
        e1=ny+kyy*m; e2=nz+kzy*m
        check(f'Biegeknicken χy = {de(cy,3)}, χz = {de(cz,3)}', f'χy = {de(cy,3)}' in t and f'χz = {de(cz,3)}' in t)
        check(f'Interaktion kyy = {de(kyy,3)}, kzy = {de(kzy,3)}', f'kyy = {de(kyy,3)}' in t and f'kzy = {de(kzy,3)}' in t)
        check(f'(6.61) = {de(e1,3)}, (6.62) = {de(e2,3)}', f'= {de(e1,3)} ≤ 1' in t and f'= {de(e2,3)} ≤ 1' in t)
        # B2) seitlich gehalten → Tab. B.1
        await pg.fill('#sn-Llt','0'); t=await out()
        check('L_LT = 0: kein BDK, kzy = 0,6·kyy (Tab. B.1)', 'kein Biegedrillknicken' in t and 'Tab. B.1' in t and f'kzy = {de(0.6*kyy,3)}' in t)
        # C) Klassifizierung Steg unter Druck + Biegung: IPE 600, S355, N = 1500 kN, M = 100 kNm
        await pg.select_option('#sn-prof','IPE 600'); await pg.select_option('#sn-stahl','S355'); await pg.fill('#sn-N','1500'); await pg.fill('#sn-M','100'); t=await out()
        P6=prof('IPE 600'); eps=math.sqrt(235/355); c=P6['h']-2*P6['tf']-2*P6['r']; rw=c/P6['tw']
        al=0.5*(1+1500e3/(355*c*P6['tw'])); s1=1500e3/P6['A']+100e6/P6['Iy']*c/2; s2=1500e3/P6['A']-100e6/P6['Iy']*c/2; ps=s2/s1
        g1=396*eps/(13*al-1); g2=456*eps/(13*al-1); g3=42*eps/(0.67+0.33*ps)
        kw=1 if rw<=g1 else 2 if rw<=g2 else 3 if rw<=g3 else 4
        check(f'IPE 600 S355 mit N: α = {de(al,3)}, Steg Klasse {kw}', f'α = ½·(1 + NEd/(fy·c·tw)) = {de(al,3)}' in t and f'{de(g1,1)} / {de(g2,1)} / {de(g3,1)} → Klasse {kw}' in t)
        # D) Querkraft > 0,5·Vpl → Momentenabminderung
        await pg.select_option('#sn-prof','IPE 200'); await pg.select_option('#sn-stahl','S235'); await pg.fill('#sn-N','0'); await pg.fill('#sn-M','30'); await pg.fill('#sn-V','150'); t=await out()
        P2=prof('IPE 200'); Vp=P2['Avz']*235/math.sqrt(3)/1000; rho=(2*150/Vp-1)**2; Aw=(200-2*8.5)*5.6
        MV=(P2['Wpl']-rho*Aw*Aw/(4*5.6))*235/1e6
        check(f'IPE 200, V = 150 kN: ρ = {de(rho,3)}, M_V,Rd = {de(MV,1)} kNm', f'ρ = (2·VEd/Vpl,Rd − 1)² = {de(rho,3)}' in t and f'= {de(MV,1)} kNm' in t)
        # E) automatische Profilwahl: kleinstes IPE mit allen Nachweisen (L = 6 m, M = 120, gehalten, Mk = 80)
        await pg.fill('#sn-V','60'); await pg.fill('#sn-M','120'); await pg.fill('#sn-L','6'); await pg.fill('#sn-Mk','80'); await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#sn-auto'); t=await out()
        best=None
        for n in sorted([k for k in PROF if k.startswith('IPE ')], key=lambda k: PROF[k][7]):
            Q=prof(n); MR=Q['Wpl']*235/1e6; Vp=Q['Avz']*235/math.sqrt(3)/1000
            ww=5/48*80e6*6000**2/(E*Q['Iy'])
            if 120<=MR and 60<=0.5*Vp and ww<=20: best=n; break
        sel=await pg.evaluate("document.getElementById('sn-prof').value")
        check(f'Automatisch: leichtestes IPE = {best}', sel==best and 'Alle Nachweise erfüllt' in t, sel)
        # F) lineare Endmomente: C1 aus Tabelle (ψ = −0,5 → 2,33), C2 = 0
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#sn-auto'); await pg.select_option('#sn-prof','IPE 300'); await pg.fill('#sn-Llt','6'); await pg.select_option('#sn-mv','lin'); await pg.fill('#sn-psi','-0.5'); t=await out()
        P=prof('IPE 300'); Mc=mcr(P,6000,2.33,0,0)/1e6
        check(f'Linear ψ = −0,5: C1 = 2,330, M_cr = {de(Mc,1)} kNm', 'C1 = 2,330' in t and f'= {de(Mc,1)} kNm' in t)
        await pg.select_option('#sn-mv','q')
        # G) Knicklänge z aus den seitlichen Halterungen (L = 6 m, L_LT = 3 m)
        await pg.select_option('#sn-mv','q'); await pg.fill('#sn-L','6'); await pg.fill('#sn-Llt','3'); await pg.fill('#sn-N','120'); t=await out()
        P=prof('IPE 300'); lbz=3000/P['iz']/93.9
        check(f'Knicklänge z = L_LT = 3 m: λz = {de(lbz,3)}', 'Lcr = βz·LLT = 3,00 m' in t and f'λ̄z = {de(lbz,3)}' in t)
        await pg.fill('#sn-N','0')
        # Bericht und Positionen
        await pg.click('text=Bericht ansehen'); r=await pg.evaluate("document.getElementById('report').innerText")
        check('Bericht Stahl: Profil, Klassifizierung, Zusammenfassung', 'DIN EN 1993-1-1' in r and 'Querschnittsklassifizierung' in r and 'ZUSAMMENFASSUNG' in r.upper())
        await pg.click('text=Zurück zur Eingabe')
        await pg.evaluate('mulyAltProj()'); await pg.click('#proj-panel >> text=Speichern'); await pg.evaluate("setMat('beton')")
        await pg.evaluate('mulyAltProj()'); await pg.click('.pos-item >> text=Laden')
        mat=await pg.evaluate("MAT"); vis=await pg.evaluate("getComputedStyle(document.getElementById('mat-stahl')).display")
        check('Stahl-Position lädt zurück in den Stahlteil', mat=='stahl' and vis!='none', mat)
        await pg.reload(); await pg.wait_for_timeout(300)
        check('Neuladen bleibt im Stahlteil', await pg.evaluate("MAT")=='stahl')
        check('Keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:',fails)
