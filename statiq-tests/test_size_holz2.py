# statiq·size v0.5.10: Holz — Ausklinkung (6.5.2), Satteldach-/Pultdachträger (6.4), Versatz (6.2.2) — unabhängig nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio
import numpy as np
from scipy.optimize import minimize_scalar
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
# Kennwerte EN 338 / EN 14080: f_m, f_t90, f_c0, f_c90, f_v
MAT={'C24':(24,0.4,21,2.5,4.0),'C30':(30,0.4,23,2.7,4.0),'GL24h':(24,0.5,24,2.5,3.5),'GL28h':(28,0.5,28,2.5,3.5),'GL30c':(30,0.5,24.5,2.5,3.5)}
KMOD={1:[.6,.7,.8,.9,1.1],2:[.6,.7,.8,.9,1.1],3:[.5,.55,.65,.7,.9]}
def mat(kl,nkl,kled):
    fm,ft90,fc0,fc90,fv=MAT[kl]; k=KMOD[nkl][kled]/1.3; bsh=kl.startswith('GL')
    return dict(fmd=fm*k,ft90d=ft90*k,fc0d=fc0*k,fc90d=fc90*k,fvd=fv*k,kcr=(2.5 if bsh else 2.0)/fv,bsh=bsh)
def ausklink(kl,nkl,kled,lage,b,h,hef,x,i,V):
    m=mat(kl,nkl,kled); a=hef/h; kn=6.5 if m['bsh'] else 5.0
    kv=1.0 if lage=='o' else min(1.0, kn*(1+1.1*i**1.5/math.sqrt(h))/(math.sqrt(h)*(math.sqrt(a*(1-a))+0.8*x/h*math.sqrt(1/a-a*a))))
    tau=1.5*V*1e3/(m['kcr']*b*hef); return kv, tau/(kv*m['fvd'])
def sattel(kl,nkl,kled,form,L,b,h0,hap,q):
    m=mat(kl,nkl,kled); run=L/2 if form=='sattel' else L; ta=(hap-h0)/(run*1000)
    h=lambda x: h0+ta*1000*(min(x,L-x) if form=='sattel' else x)
    sig=lambda x: 6*q*x*(L-x)/2*1e6/(b*h(x)**2)
    r=minimize_scalar(lambda x:-sig(x), bounds=(1e-6, run), method='bounded', options={'xatol':1e-10})
    xm=r.x; hx=h(xm); kh=min((600/hx)**0.1,1.1) if hx<600 else 1.0; fmd=kh*m['fmd']
    kma=1/math.sqrt(1+(fmd/(1.5*m['fvd'])*ta)**2+(fmd/m['fc90d']*ta**2)**2)
    out={'xm':xm,'kma':kma,'sdm':sig(xm)/(kma*fmd)}
    if form=='sattel':
        Map=q*L*L/8; s0=6*Map*1e6/(b*hap**2); kl_=1+1.4*ta+5.4*ta**2; khap=min((600/hap)**0.1,1.1) if hap<600 else 1.0
        out['sdf']=kl_*s0/(khap*m['fmd'])
        kp=0.2*ta; st=kp*s0; V=b/1000*(hap/1000)**2*(1-ta/4); Vb=b/1000*L*(h0+hap)/2/1000; V=min(V,2/3*Vb)
        out['sdt']=st/(1.4*(0.01/V)**0.2*m['ft90d'])
    out['sdv']=1.5*q*L/2*1e3/(m['kcr']*b*h0)/m['fvd']
    return out
def versatz(kl,nkl,kled,art,gam,b,h,tv,lv,S,kc90):
    m=mat(kl,nkl,kled); g=math.radians(gam); a=g/2 if art=='stirn' else g
    fca=m['fc0d']/(m['fc0d']/(kc90*m['fc90d'])*math.sin(a)**2+math.cos(a)**2)
    # Kraft auf die geneigte Fläche, unabhängig über Fläche und Normalkomponente
    if art=='stirn': F=S*1e3*math.cos(g/2); A=b*tv/math.cos(g/2)
    else: F=S*1e3; A=b*tv/math.cos(g)
    sig=F/A
    tmax=h*(0.25 if gam<=50 else 1/6 if gam>=60 else np.interp(gam,[50,60],[0.25,1/6]))
    lef=min(lv,8*tv); tau=S*1e3*math.cos(g)/(b*lef)
    return {'vsc':sig/fca,'vst':tv/tmax,'vsv':tau/m['fvd'],'fca':fca}
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        setm=lambda kl,nkl,kled: f"$('hx-art').value='{'bsh' if kl.startswith('GL') else 'vh'}'; fillHxKlassen(); $('hx-kl').value='{kl}'; $('hx-nkl').value='{nkl}'; $('hx-kled').value='{kled}';"
        # ── Ausklinkung ──
        await pg.evaluate("setMat('holz'); setHoMode('ausklink')")
        s=await pg.inner_text('#summary'); check('Standard Ausklinkung erfüllt', 'Alle Nachweise erfüllt' in s, s)
        A={'BSH unten, rechtwinklig (Standard)':('GL24h',1,2,'u',120,400,300,100,0,18),
           'BSH unten, Anschnitt i = 1':('GL24h',1,2,'u',120,400,300,100,1,18),
           'Vollholz C24, x = 0, tiefe Ausklinkung':('C24',2,3,'u',100,240,150,0,0,10),
           'Vollholz, großes x':('C30',1,2,'u',140,280,200,250,0.5,12),
           'flache Ausklinkung → k_v = 1':('GL24h',1,2,'u',200,600,580,0,6,20),
           'oben ausgeklinkt (k_v = 1)':('GL28h',1,2,'o',120,400,300,100,0,40)}
        for name,(kl,nkl,kled,lage,b,h,hef,x,i,V) in A.items():
            await pg.evaluate(setm(kl,nkl,kled)+f"$('ak-lage').value='{lage}'; $('ak-b').value={b}; $('ak-h').value={h}; $('ak-hef').value={hef}; $('ak-x').value={x}; $('ak-i').value={i}; $('ak-V').value={V}; run()")
            kv,eta=ausklink(kl,nkl,kled,lage,b,h,hef,x,i,V)
            g=await pg.evaluate("[LAST.res.kv, LAST.res.C.find(c=>c.id==='akv').eta]")
            check(f'Ausklinkung: {name}', abs(g[0]-kv)<1e-12 and abs(g[1]-eta)<1e-9, f'k_v = {kv:.3f}, η = {eta:.3f}')
        await pg.evaluate("$('ak-hef').value=420; run()")
        check('h_ef ≥ h wird abgelehnt', 'h_ef' in await pg.inner_text('#summary') or await pg.evaluate("!LAST || LAST.mode!=='ausklink' || LAST.I.hef!==420"))
        await pg.evaluate("$('ak-hef').value=180; $('ak-h').value=400; $('ak-lage').value='u'; run()")
        check('α < 0,5 → Hinweis auf Verstärkung', 'erstärkung' in await pg.evaluate("LAST.res.C.find(c=>c.id==='akr').note"))
        # ── Satteldach / Pultdach ──
        await pg.evaluate("setHoMode('sattel')")
        s=await pg.inner_text('#summary'); check('Standard Satteldachträger erfüllt', 'Alle Nachweise erfüllt' in s, s)
        check('Satteldach: Holzart fest auf BSH', await pg.evaluate("$('hx-art').value==='bsh' && $('hx-art').disabled"))
        SD={'Satteldach 15 m (Standard)':('GL24h',1,2,'sattel',15,160,600,1200,12),
            'Satteldach flach, GL28h, Schnee':('GL28h',2,3,'sattel',20,200,800,1300,14),
            'Satteldach steil (≈ 10°)':('GL30c',1,2,'sattel',12,180,500,1550,9),
            'Pultdach 10 m':('GL24h',1,2,'pult',10,140,400,900,8),
            'Pultdach, h₀ < 600 → k_h':('GL28h',2,2,'pult',8,120,300,700,6)}
        for name,(kl,nkl,kled,form,L,b,h0,hap,q) in SD.items():
            await pg.evaluate(setm(kl,nkl,kled)+f"$('sd-form').value='{form}'; $('sd-L').value={L}; $('sd-b').value={b}; $('sd-h0').value={h0}; $('sd-hap').value={hap}; $('sd-q').value={q}; run()")
            r=sattel(kl,nkl,kled,form,L,b,h0,hap,q)
            g=await pg.evaluate("Object.fromEntries(LAST.res.C.filter(c=>!c.info).map(c=>[c.id,c.eta]).concat([['xm',LAST.res.xm],['kma',LAST.res.kma]]))")
            keys=['sdm','sdv']+(['sdf','sdt'] if form=='sattel' else [])
            ok=abs(g['xm']-r['xm'])<1e-4 and abs(g['kma']-r['kma'])<1e-9 and all(abs(g[k]-r[k])<1e-6 for k in keys) and (form=='sattel' or 'sdf' not in g)
            check(f'{name}', ok, f"x = {r['xm']:.3f} m, k_m,α = {r['kma']:.3f}, η: "+', '.join(f'{k} {r[k]:.3f}' for k in keys))
        # Lage des Maximums gegen die geschlossene Formel
        check('x_max Satteldach = L·h₀/(2·h_ap)', abs(sattel('GL24h',1,2,'sattel',15,160,600,1200,12)['xm']-15*600/2400)<1e-6)
        check('x_max Pultdach = L·h₀/(h₀ + h_ap)', abs(sattel('GL24h',1,2,'pult',10,140,400,900,8)['xm']-10*400/1300)<1e-6)
        await pg.evaluate("$('sd-h0').value=600; $('sd-hap').value=550; run()")
        check('h_ap ≤ h₀ wird abgelehnt', await pg.evaluate("!LAST || LAST.I.hap!==550") and 'hap' in await pg.inner_text('#summary') and '<sub>ap</sub>' in await pg.inner_html('#summary'))
        # ── Versatz ──
        await pg.evaluate("setHoMode('versatz'); $('sd-hap').value=1200; $('sd-form').value='sattel'")
        s=await pg.inner_text('#summary'); check('Standard Versatz erfüllt', 'Alle Nachweise erfüllt' in s, s)
        VS={'Stirnversatz 40° (Standard)':('GL24h',1,2,'stirn',40,120,200,40,300,34,1),
            'Stirnversatz 55°, Vollholz, Grenze interpoliert':('C24',2,3,'stirn',55,100,200,35,250,25,1),
            'Fersenversatz 30°':('C24',1,2,'ferse',30,120,220,50,600,30,1),
            'Fersenversatz 65°, k_c,90 = 1,5':('C30',1,4,'ferse',65,140,240,30,200,22,1.5),
            'Vorholz länger als 8·t_v':('GL24h',1,2,'stirn',35,120,200,30,400,30,1)}
        for name,(kl,nkl,kled,art,gam,b,h,tv,lv,S,kc) in VS.items():
            await pg.evaluate(setm(kl,nkl,kled)+f"$('vs-art').value='{art}'; $('vs-gam').value={gam}; $('vs-b').value={b}; $('vs-h').value={h}; $('vs-tv').value={tv}; $('vs-lv').value={lv}; $('vs-S').value={S}; $('vs-kc90').value={kc}; run()")
            r=versatz(kl,nkl,kled,art,gam,b,h,tv,lv,S,kc)
            g=await pg.evaluate("Object.fromEntries(LAST.res.C.filter(c=>!c.info).map(c=>[c.id,c.eta]).concat([['fca',LAST.res.fca]]))")
            check(f'Versatz: {name}', all(abs(g[k]-r[k])<1e-9 for k in ['vsc','vst','vsv','fca']), f"f_c,α,d = {r['fca']:.2f}, η = {r['vsc']:.3f} / {r['vst']:.3f} / {r['vsv']:.3f}")
        check('f_c,α: α = 0 → f_c,0,d, α = 90° → k_c,90·f_c,90,d', await pg.evaluate("(()=>{const M=hxMat(); return Math.abs(fcAlpha(M,0,1)-M.fc0d)<1e-12 && Math.abs(fcAlpha(M,Math.PI/2,1.5)-1.5*M.fc90d)<1e-12})()"))
        # Berichte, Positionen, Speichern
        for m,word in [('ausklink','k'),('sattel','Querzug'),('versatz','Vorholz')]:
            await pg.evaluate(f"setHoMode('{m}'); run(); showReport()"); rp=await pg.inner_text('#report')
            check(f'Bericht {m}', word in rp and 'eingaben' in rp.lower())
        await pg.evaluate("document.body.classList.remove('show-report')")
        await pg.evaluate("setHoMode('sattel'); $('sd-name').value='Binder Test'; run(); mulyAltProj(); savePos()")
        lst=await pg.evaluate("posRead().map(p=>[p.name,p.typ])")
        check('Position Satteldach gespeichert (typ holz_sattel)', ['Binder Test','holz_sattel'] in lst, lst)
        await pg.evaluate("setHoMode('versatz'); $('vs-tv').value=33; run(); save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden stellt Versatz wieder her', await pg.evaluate("MAT==='holz' && HOMODE==='versatz' && $('vs-tv').value==='33' && LAST.mode==='versatz'"))
        await pg.evaluate("loadPos(posRead().findIndex(p=>p.name==='Binder Test'))")
        check('Position laden → Satteldachträger', await pg.evaluate("HOMODE==='sattel' && LAST.mode==='sattel'"))
        await pg.evaluate("setHoMode('bauteil')")
        check('zurück zu Träger/Stütze funktioniert', await pg.evaluate("LAST.mat==='holz' && $('ho-x').style.display==='none'"))
        # Mobil: kein Querscrollen
        await pg.set_viewport_size({'width':390,'height':800}); over=[]
        for m in ['ausklink','sattel','versatz']:
            await pg.evaluate(f"setHoMode('{m}')"); await pg.wait_for_timeout(50)
            if await pg.evaluate("document.documentElement.scrollWidth>window.innerWidth+1"): over.append(m)
        check('Mobil 390 px: kein horizontales Scrollen', not over, over)
        check('Auswahlmenü enthält die neuen Holz-Themen', await pg.evaluate("(buildPick(), ['Ausklinkung','Satteldachträger','Versatz'].every(t=>$('pick-menu').innerText.includes(t)))"))
        await pg.evaluate("buildPick(); [...$('pick-menu').querySelectorAll('.pick-item')].find(b=>b.textContent==='Versatz').click()")
        check('Auswahlmenü → Versatz öffnet das Thema', await pg.evaluate("MAT==='holz' && HOMODE==='versatz' && LAST.mode==='versatz'"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
