# statiq·size: Durchstanzen (DIN EN 1992-1-1 mit NA, 6.4) — unabhängig nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:64}', str(info)[:160])
FCK={'C20/25':20,'C25/30':25,'C30/37':30,'C35/45':35}
BETA={'innen':1.10,'rand':1.40,'ecke':1.50}
def ref(h,beton,form,pos,c1,c2,V,dsx,sx,dsy,sy,cnom):
    fck=FCK[beton]; gc=1.5; fyd=500/1.15; fcd=0.85*fck/gc
    h*=10; c1*=10; c2=c1 if form=='k' else c2*10
    dx=h-cnom-dsx/2; dy=h-cnom-dsx-dsy/2; d=(dx+dy)/2
    asx=math.pi*dsx**2/4*1000/(sx*10); asy=math.pi*dsy**2/4*1000/(sy*10)
    rl=min(math.sqrt(asx/(1000*dx)*asy/(1000*dy)), 0.02, 0.5*fcd/fyd)
    def u(a):
        if form=='k':
            full=math.pi*(c1+2*a); return {'innen':full,'rand':full/2+c1,'ecke':full/4+c1}[pos]
        return {'innen':2*(c1+c2)+2*math.pi*a,'rand':2*c1+c2+math.pi*a,'ecke':c1+c2+math.pi*a/2}[pos]
    if form=='k': u0={'innen':math.pi*c1,'rand':min(math.pi*c1/2+3*d,math.pi*c1),'ecke':min(3*d,math.pi*c1/2)}[pos]
    else: u0={'innen':2*(c1+c2),'rand':min(c2+3*d,c2+2*c1),'ecke':min(3*d,c1+c2)}[pos]
    u1=u(2*d); k=min(1+math.sqrt(200/d),2)
    CRd=max(0.18/gc*(0.1*u0/d+0.6),0.15/gc) if (pos=='innen' and u0/d<4) else 0.18/gc
    vmin=0.0525/gc*k**1.5*math.sqrt(fck)
    vc=max(CRd*k*(100*rl*fck)**(1/3), vmin); b=BETA[pos]; vEd=b*V*1000/(u1*d); vmax=1.4*vc
    R=dict(d=d,u0=u0,u1=u1,vc=vc,vEd=vEd,vmax=vmax,Asw=None)
    if vc<vEd<=vmax:
        fyw=min(250+0.25*d,fyd); sr=0.75*d; R['Asw']=(vEd-0.75*vc)*u1*sr/(1.5*fyw)
        vo=max(0.15/gc*k*(100*rl*fck)**(1/3), vmin); uout=b*V*1000/(vo*d)
        lo,hi=0,20*d
        for _ in range(80):
            m=(lo+hi)/2
            if u(m)<uout: lo=m
            else: hi=m
        R['aout']=lo; R['nRows']=max(2, math.ceil((lo-1.5*d-0.5*d)/sr+1e-9)+1)
    return R
CASES=[('Innen 40×40, h 24, 550 kN, C30/37',24,'C30/37','r','innen',40,40,550,16,12.5,16,12.5),
       ('Innen 40×40, h 24, 400 kN (ohne Bewehrung)',24,'C30/37','r','innen',40,40,400,16,12.5,16,12.5),
       ('Innen 25×25, h 30 → u0/d < 4, C25/30',30,'C25/30','r','innen',25,25,500,16,10,16,10),
       ('Innen rund D 45, h 28, 800 kN',28,'C35/45','k','innen',45,0,800,20,15,16,15),
       ('Rand 30×50, h 26, 300 kN',26,'C30/37','r','rand',30,50,300,16,12.5,14,12.5),
       ('Ecke 40×40, h 24, 150 kN',24,'C30/37','r','ecke',40,40,150,16,12.5,16,12.5),
       ('Rand rund D 40, h 24, 300 kN',24,'C30/37','k','rand',40,0,300,16,12.5,16,12.5),
       ('Innen 30×30, h 20, 900 kN → v_Rd,max überschritten',20,'C25/30','r','innen',30,30,900,12,15,12,15)]
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('beton'); setTyp('durchstanzen'); run()")
        s=await pg.inner_text('#summary'); check('Standardfall erfüllt (mit Durchstanzbewehrung)', 'Alle Nachweise erfüllt' in s and await pg.evaluate("!!LAST.res.DSB"), s)
        check('c_nom XC1, Ø16 = 26 mm', await pg.evaluate("LAST.res.cnom")==26)
        for name,h,bet,form,pos,c1,c2,V,dsx,sx,dsy,sy in CASES:
            await pg.evaluate(f"$('in-h').value={h}; $('in-beton').value='{bet}'; $('ds-form').value='{form}'; $('ds-pos').value='{pos}'; $('ds-c1').value={c1}; $('ds-c2').value={c2 or 30}; $('ds-V').value={V}; $('ds-dsx').value='{dsx}'; $('ds-sx').value={sx}; $('ds-dsy').value='{dsy}'; $('ds-sy').value={sy}; run()")
            g=await pg.evaluate("({d:LAST.res.d,u0:LAST.res.u0,u1:LAST.res.u1,vc:LAST.res.vc,vEd:LAST.res.vEd,vmax:LAST.res.vmax,cnom:LAST.res.cnom,DSB:LAST.res.DSB,ok:LAST.res.ok})")
            R=ref(h,bet,form,pos,c1,c2,V,dsx,sx,dsy,sy,g['cnom'])
            ok=all(abs(g[k]-R[k])<1e-6*max(1,abs(R[k])) for k in ['d','u0','u1','vc','vEd','vmax'])
            if R['Asw'] is None: ok = ok and g['DSB'] is None
            else: ok = ok and g['DSB'] and abs(g['DSB']['Asw']-R['Asw'])<1e-6*R['Asw'] and g['DSB']['nRows']==R['nRows'] and abs(g['DSB']['aout']-R['aout'])<0.01
            ok = ok and g['ok']==(R['vEd']<=R['vmax'])
            extra = f"A_sw = {R['Asw']/100:.2f} cm², {R['nRows']} Reihen" if R['Asw'] else ('ohne Bewehrung' if R['vEd']<=R['vc'] else 'v_Rd,max überschritten')
            check(f"{name}: v_Ed {R['vEd']:.3f} / v_Rd,c {R['vc']:.3f}", ok, extra)
        await pg.evaluate("setTyp('durchstanzen'); run(); showReport()"); r=await pg.inner_text('#report')
        check('Bericht Durchstanzen', 'Rundschnitt' in r and 'Durchstanzbewehrung' in r, r[:120])
        await pg.evaluate("$('ds-V').value=612; $('ds-pos').value='rand'; run(); save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden stellt Durchstanzen wieder her', await pg.evaluate("TYP==='durchstanzen' && $('ds-V').value==='612' && $('ds-pos').value==='rand' && LAST.res && LAST.res.beta===1.4"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
