# statiq·size im Browser prüfen (Playwright). Sollwerte unabhängig in Python gerechnet. Ohne Playwright: SKIP.
import os, sys, math, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(os.path.join(HERE,'..','size.html'))
INDEX=os.path.abspath(os.path.join(HERE,'..','index.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
import numpy as np
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:58}', str(info)[:160])
de = lambda v,d=2: f'{v:.{d}f}'.replace('.',',')

# ── unabhängige Referenz ──
fyd=500/1.15
def omega(mu):
    """ω über numerische Integration des Parabel-Rechteck-Diagramms (ε_s ≤ 25 ‰, horizontaler Ast)"""
    def st(t):
        ec = 3.5*t if t<=1 else 3.5; es = 25 if t<=1 else 25-(t-1)*(25-fyd/200)
        xi=ec/(ec+es); y=np.linspace(0,1,20001); e=ec*y; s=np.where(e<2,1-(1-e/2)**2,1.0)
        A=np.trapezoid(s,y); ka=1-np.trapezoid(s*y,y)/A
        return xi*A, xi*A*(1-ka*xi)
    lo,hi=1e-6,2
    for _ in range(60):
        m=(lo+hi)/2
        if st(m)[1]<mu: lo=m
        else: hi=m
    return st((lo+hi)/2)[0]

def tsolve(M, d, beff, hf, bw):
    """T-Querschnitt: Suche über die Nulllinienlage x (unabhängig von der App, die über Dehnungszustände sucht)"""
    def T(x):
        ec=min(3.5, 25*x/(d-x)); y=np.linspace(0,x,40001); e=ec*(1-y/x); bb=np.where(y<hf,beff,bw)
        s=np.where(e<2,1-(1-e/2)**2,1.0)*17.0*bb; Fc=np.trapezoid(s,y); return Fc, Fc*(d-np.trapezoid(s*y,y)/Fc)/1e6
    lo,hi=1e-3,0.6*d
    for _ in range(80):
        x=(lo+hi)/2
        if T(x)[1]<M: lo=x
        else: hi=x
    return x, T(x)[0]

# Balken 30/60, C30/37, XC1, 5 Ø 16, Bügel Ø8: c_v = 20, d = 564
b,h,d,fck,fcd=300,600,564.0,30,17.0
mu=220e6/(b*d*d*fcd); AsErf=omega(mu)*b*d*fcd/fyd
As=5*math.pi*16**2/4
k=1+math.sqrt(200/d); rho=As/(b*d); VRdc=max(0.1*k*(100*rho*fck)**(1/3), 0.0525/1.5*k**1.5*math.sqrt(fck))*b*d/1000
z=min(0.9*d, max(d-2*28, d-28-30)); VRdmax=b*z*0.75*fcd/(1.2+1/1.2)/1000
# Rissbreite (Zustand II)
ae=200000/33000; r=As/(b*d); x=(-ae*r+math.sqrt((ae*r)**2+2*ae*r))*d; zz=d-x/3; ss=110e6/(As*zz)
hce=min(2.5*(h-d),(h-x)/3,h/2); rpe=As/(b*hce); sr=min(16/(3.6*rpe), ss*16/(3.6*2.9))
wk=sr*max((ss-0.4*2.9/rpe*(1+ae*rpe))/200000, 0.6*ss/200000)

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.on('dialog',lambda dg:(errs.append('dialog '+dg.message),asyncio.ensure_future(dg.dismiss())))
        await pg.goto('file://'+HTML); await pg.wait_for_timeout(300)
        async def out():   # Rechnung abwarten: unter Last kommt run() nach fill() manchmal ein Bild später (wie test_size_stahl)
            await pg.evaluate("run()"); await pg.wait_for_timeout(60); return await _out()
        _out = lambda: pg.evaluate("document.querySelector('.col-out').innerText + '\\n' + (()=>{ const d=document.createElement('div'); return (LAST&&LAST.res&&LAST.res.C||[]).flatMap(c=>c.steps).map(s=>{ d.innerHTML=s.replace(/^§/,''); return d.innerText||d.textContent; }).join('\\n'); })()")
        t=await out()
        check('Startwerte: automatisch 5 Ø 16, Bügel Ø8/15', '5 Ø 16 = 10,05 cm²' in t and 'Bügel Ø8/15,0 cm' in t, t.split('\n')[2])
        check(f'Biegung: As,erf = {de(AsErf/100)} cm² (Referenz numerisch)', f'As,erf = ω·b·d·fcd/fyd = {de(AsErf/100)} cm²' in t)
        check(f'Querkraft: VRd,c = {de(VRdc,1)}, VRd,max = {de(VRdmax,1)} kN', f'= {de(VRdc,1)} kN' in t and f'= {de(VRdmax,1)} kN' in t)
        check(f'Rissbreite: wk = {de(wk,3)} mm', f'= {de(wk,3)} mm' in t)
        check('Alle Nachweise erfüllt', 'Alle Nachweise erfüllt' in t)
        # Handeingabe: 3 Ø 20 reicht nicht
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#in-auto'); await pg.fill('#in-n','3'); await pg.select_option('#in-ds','20')
        t=await out()
        check('Hand: 3 Ø 20 → Biegung nicht erfüllt', 'nicht erfüllt' in t and 'As,vorh = 3 Ø 20 = 9,42 cm²' in t)
        await pg.fill('#in-n','8'); await pg.select_option('#in-ds','25')
        t=await out()
        check('Hand: 8 Ø 25 in b = 30 cm → Stabhinweis', 'passen nicht nebeneinander' in t)
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#in-auto')
        # Expositionsklasse / Mindestfestigkeit
        await pg.select_option('#in-expo','XD1'); await pg.select_option('#in-beton','C25/30')
        t=await out()
        check('XD1 mit C25/30 → Mindestbetonfestigkeit verletzt', 'zu niedrig (mindestens C30/37)' in t)
        await pg.select_option('#in-beton','C30/37')
        t=await out()
        check('XD1: cnom Bügel 30+10+15 = 55 mm', re.search(r'Bügel Ø\d+: cnom = max\(40; \d+; 10\) \+ 15 = 55 mm', t) is not None)
        check('XD1: wmax 0,3 mm', 'wmax = 0,3 mm (XD1' in t)
        # Zwang
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#in-zwang'); t=await out()
        ds=int(await pg.evaluate("document.getElementById('in-ds').value"))
        AsZ=0.4*(0.8-0.3*(600-300)/500)*3.0*(300*600/2)/min(math.sqrt(0.3*3.48e6/(ds*2.9/3.0)),500)
        check(f'Zwang (Ø{ds}): As,min = {de(AsZ/100)} cm²', f'= {de(AsZ/100)} cm²' in t and 'Zwang:' in t)
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#in-zwang'); await pg.select_option('#in-expo','XC1')
        # Platte
        await pg.evaluate("setTyp('platte')"); t=await out()
        check('Platte: automatisch Ø12/20, As,erf 5,61 cm²/m', 'Ø12/20,0 cm = 5,65 cm²/m' in t and '= 5,61 cm²/m' in t)
        check('Platte: VEd ≤ VRd,c (vmin maßgebend, 104,1 kN)', 'VRd,c = 104,1 kN' in t)
        await pg.fill('#in-l','8'); t=await out()
        check('Platte l = 8 m: Biegeschlankheit nicht erfüllt', 'l/d = 8000' in t and 'nicht erfüllt' in t)
        # Bericht
        await pg.click('text=Bericht ansehen')
        r=await pg.evaluate("document.getElementById('report').innerText")
        vis=await pg.evaluate("getComputedStyle(document.getElementById('report-view')).display")
        check('Bericht: Eingaben, Nachweise, Zusammenfassung', vis=='block' and 'EINGABEN' in r.upper() and 'ZUSAMMENFASSUNG' in r.upper() and 'Pos. 2' in r)
        await pg.emulate_media(media='print')
        hid=await pg.evaluate("getComputedStyle(document.querySelector('.app-header')).display")
        check('Druckansicht blendet Kopfzeile aus', hid=='none')
        await pg.emulate_media(media='screen'); await pg.click('text=Zurück zur Eingabe')
        # Eingaben bleiben nach Neuladen erhalten
        await pg.reload(); await pg.wait_for_timeout(300); t=await out()
        check('Neuladen: Platte und l = 8 m bleiben erhalten', 'l/d = 8000' in t)
        # ungültige Eingabe
        await pg.fill('#in-h',''); t=await out()
        check('Leere Höhe → Hinweis statt Fehler', 'Bitte Eingaben prüfen' in t)
        # ── Unterzug (Plattenbalken) ──
        await pg.fill('#in-h','60'); await pg.evaluate("setTyp('unterzug')"); t=await out()
        check('Unterzug: beff = 300 + 2·1020 = 2340 mm', 'beff = bw + Σ beff,i = 300 + 1020 + 1020 = 2340 mm' in t)
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#in-auto'); await pg.fill('#in-n','3'); await pg.select_option('#in-ds','28'); await pg.select_option('#in-dsw','8'); await pg.fill('#in-sw','10')
        t=await out(); x,Fc=tsolve(380,548,2340,180,300)
        check(f'Unterzug Feld: Fcd = {de(Fc/1000,1)} kN, As,erf = {de(Fc/fyd/100)} cm² (Referenz)', f'= {de(Fc/1000,1)} kN' in t and f'As,erf = Fcd/fyd = {de(Fc/fyd/100)} cm²' in t and 'Nulllinie in der Platte' in t)
        vEd=0.75*Fc*1020/2340/(180*7500/4)
        check(f'Gurtanschluss: vEd = {de(vEd,3)} N/mm²', f'vEd = ΔFd/(hf·Δx) = {de(vEd,3)} N/mm²' in t)
        FEd=210*1.2/2; lbrqd=28/4*(FEd*1000/(3*math.pi*196))/3.0; lbd=max(2/3*lbrqd, 6.7*28, 100)
        check(f'Endauflager: FEd {de(FEd,1)} kN, lbd,dir = {de(lbd,0)} mm', f'= {de(FEd,1)} kN' in t and f'= {de(lbd,0)} mm (α₁ = 1,0)' in t)
        await pg.fill('#in-t','15'); t=await out()
        check('Auflagertiefe 15 cm: Verankerung nicht erfüllt', 'Verankerungslänge reicht nicht' in t)
        await pg.fill('#in-t','25')
        # Gurt schmal → Nulllinie im Steg
        await pg.fill('#in-hf','10'); await pg.fill('#in-b1','20'); await pg.fill('#in-b2','20'); await pg.fill('#in-M','500'); await pg.fill('#in-n','4'); await pg.select_option('#in-ds','25')
        t=await out(); x,Fc=tsolve(500,552.5,700,100,300)
        check(f'Schmaler Gurt: Nulllinie im Steg, x = {de(x,1)} mm, Fcd = {de(Fc/1000,1)} kN', 'Nulllinie im Steg' in t and f'x = {de(x,1)} mm' in t and f'= {de(Fc/1000,1)} kN' in t)
        # Stützmoment
        await pg.fill('#in-hf','18'); await pg.fill('#in-b1','135'); await pg.fill('#in-b2','135'); await pg.fill('#in-M','380'); await pg.fill('#in-n','3'); await pg.select_option('#in-ds','28')
        await pg.fill('#in-Ms','300'); await pg.fill('#in-nt','9'); await pg.select_option('#in-dst','14'); t=await out()
        mus=300e6/(300*565**2*17); AsT=omega(mus)*300*565*17/fyd
        check(f'Stütze: Rechteck bw, μ = {de(mus,4)}, As,erf = {de(AsT/100)} cm²', f'= {de(mus,4)}' in t and f'dSt·fcd/fyd = {de(AsT/100)} cm²' in t)
        check('Stütze: obere Stäbe über beff,Stütze = 1200 mm verteilt', 'beff,Stütze = 1200 mm verteilt' in t)
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#in-auto'); t=await out()
        check('Unterzug automatisch: alle Nachweise erfüllt', 'Alle Nachweise erfüllt' in t, t.split('\n')[2])
        await pg.click('text=Bericht ansehen'); r=await pg.evaluate("document.getElementById('report').innerText")
        check('Bericht Unterzug: Plattenbalken, Gurtanschluss, Endauflager', 'Unterzug (Plattenbalken)' in r and 'Anschluss Gurt' in r and 'Endauflager' in r)
        await pg.click('text=Zurück zur Eingabe'); await pg.fill('#in-Ms','0')
        # ── v0.1.2: Rissbreite über der Stütze ──
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.uncheck('#in-auto'); await pg.fill('#in-n','3'); await pg.select_option('#in-ds','28'); await pg.select_option('#in-dsw','8'); await pg.fill('#in-sw','10')
        await pg.fill('#in-Ms','300'); await pg.fill('#in-nt','9'); await pg.select_option('#in-dst','14'); await pg.fill('#in-Mqps','150'); t=await out()
        AsT=9*math.pi*14**2/4; dt=565.0; aeR=200000/33000; rr=AsT/(300*dt); xs=(-aeR*rr+math.sqrt((aeR*rr)**2+2*aeR*rr))*dt; zs=dt-xs/3; sss=150e6/(AsT*zs)
        hces=min(2.5*(600-dt),(600-xs)/3,300); rps=AsT/(1200*hces); srs=min(14/(3.6*rps), sss*14/(3.6*2.9))
        wks=srs*max((sss-0.4*2.9/rps*(1+aeR*rps))/200000, 0.6*sss/200000)
        check(f'Rissbreite Stütze: σs = {de(sss,0)} N/mm², wk = {de(wks,3)} mm', 'Rissbreite über der Stütze' in t and f'= {de(sss,0)} N/mm²' in t and f'(εsm − εcm) = {de(wks,3)} mm' in t)
        # ── indirekte Lagerung ──
        await pg.select_option('#in-lager','ind'); await pg.fill('#in-t','30'); t=await out()
        check('Indirekt: lbd,ind ≥ 10·Ø = 280 mm > 262 mm → nicht erfüllt', 'lbd,ind' in t and '= 280 mm' in t and '300 − 38 = 262 mm' in t and 'Verankerungslänge reicht nicht' in t)
        check('Indirekt: Aufhängebewehrung 210/434,8 = 4,83 cm²', 'As,h = VEd/fyd = 4,83 cm²' in t)
        await pg.select_option('#in-lager','dir'); await pg.fill('#in-t','25'); await pg.fill('#in-Mqps','0'); await pg.fill('#in-Ms','0'); await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))"); await pg.check('#in-auto')
        # ── Positionen ──
        await pg.fill('#in-name','Pos. A'); await pg.evaluate('mulyAltProj()'); await pg.click('#proj-panel >> text=Speichern')
        await pg.fill('#in-name','Pos. B'); await pg.fill('#in-M','300'); await pg.evaluate('mulyAltProj()'); await pg.click('#proj-panel >> text=Speichern')
        n=await pg.evaluate("document.querySelectorAll('.pos-item').length")
        check('Positionen: zwei gespeichert', n==2, n)
        await pg.evaluate('mulyAltProj()'); await pg.click('.pos-item:nth-child(1) >> text=Laden')
        nm=await pg.evaluate("document.getElementById('in-name').value"); M=await pg.evaluate("document.getElementById('in-M').value")
        check('Position A geladen (Name und M_Ed)', nm=='Pos. A' and M=='380', f'{nm} {M}')
        await pg.evaluate('mulyAltProj()'); await pg.click('.pos-item:nth-child(2) >> text=Löschen')
        n=await pg.evaluate("document.querySelectorAll('.pos-item').length")
        check('Löschen braucht Bestätigung', n==2)
        await pg.evaluate('mulyAltProj()'); await pg.click('.pos-item:nth-child(2) >> text=Wirklich?')
        n=await pg.evaluate("document.querySelectorAll('.pos-item').length")
        check('Nach Bestätigung gelöscht', n==1)
        # Startseite verlinkt size
        await pg.goto('file://'+INDEX); await pg.wait_for_timeout(700)
        href=await pg.evaluate("document.querySelector('a.module-card[href=\"size.html\"]')?.getAttribute('href')")
        check('Startseite: size-Karte verlinkt', href=='size.html', href)
        check('Keine Skriptfehler / Pop-ups', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:',fails)
