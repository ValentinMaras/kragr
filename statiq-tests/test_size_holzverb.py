# statiq·size: Holzverbindungen (EN 1995-1-1, Abschnitt 8) — Johansen-Modi unabhängig in Python nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:64}', str(info)[:160])
RHO={'C24':350,'GL24h':385,'C30':380}
KMOD={(1,2):0.8,(2,2):0.8,(1,3):0.9,(3,2):0.65}
def ref(c):
    vm=c['vm']; d=c['d']; rk=RHO[c.get('kl','C24')]
    de = 1.1*c['dk'] if vm=='schraube' else d
    nag = vm=='nagel' or (vm=='schraube' and de<=6)
    fu = c.get('fu',360) if vm=='sdue' else 600
    My = 0.3*fu*de**2.6
    if nag: fh0 = 0.082*(1-0.01*de)*rk if c.get('vorg') else 0.082*rk*de**-0.3
    else:   fh0 = 0.082*(1-0.01*de)*rk
    k90=1.35+0.015*de
    fh = lambda a: fh0 if nag else fh0/(k90*math.sin(math.radians(a))**2+math.cos(math.radians(a))**2)
    f1=fh(c.get('al1',0)); f2=f1 if c['an'][0]=='S' else fh(c.get('al2',0)); b=f2/f1
    t1=c['t1']; t2=c.get('t2',0); ts=c.get('ts',0)
    # Ausziehen
    Fax=0
    if vm=='schraube': Fax=c.get('fax',0)*1000
    if vm=='nagel':
        tp = t2 if c['an']=='HH1' else t1
        kp = 1 if tp>=12*de else (tp/(4*de)-2 if tp>=8*de else 0)
        Fax=min(kp*20e-6*rk*rk*de*tp, 70e-6*rk*rk*(2*de)**2)
    lim = 1.0 if vm=='schraube' else 0.15 if vm=='nagel' else 0
    rope = lambda J: J+min(Fax/4, lim*J)
    s=math.sqrt; an=c['an']
    if an=='HH1':
        modes={'a':f1*t1*de,'b':f2*t2*de,
          'c':rope(f1*t1*de/(1+b)*(s(b+2*b*b*(1+t2/t1+(t2/t1)**2)+b**3*(t2/t1)**2)-b*(1+t2/t1))),
          'd':rope(1.05*f1*t1*de/(2+b)*(s(2*b*(1+b)+4*b*(2+b)*My/(f1*de*t1**2))-b)),
          'e':rope(1.05*f1*t2*de/(1+2*b)*(s(2*b*b*(1+b)+4*b*(1+2*b)*My/(f1*de*t2**2))-b)),
          'f':rope(1.15*s(2*b/(1+b))*s(2*My*f1*de))}
    elif an=='HH2':
        modes={'g':f1*t1*de,'h':0.5*f2*t2*de,'j':rope(1.05*f1*t1*de/(2+b)*(s(2*b*(1+b)+4*b*(2+b)*My/(f1*de*t1**2))-b)),'k':rope(1.15*s(2*b/(1+b))*s(2*My*f1*de))}
    elif an=='SHi':
        modes={'f':f1*t1*de,'g':rope(f1*t1*de*(s(2+4*My/(f1*de*t1**2))-1)),'h':rope(2.3*s(My*f1*de))}
    else:
        if an=='SHa': thin={'j':0.5*f1*t2*de,'k':rope(1.15*s(2*My*f1*de))}; thick={'l':0.5*f1*t2*de,'m':rope(2.3*s(My*f1*de))}
        else: thin={'a':0.4*f1*t1*de,'b':rope(1.15*s(2*My*f1*de))}; thick={'c':rope(f1*t1*de*(s(2+4*My/(f1*de*t1**2))-1)),'d':rope(2.3*s(My*f1*de)),'e':f1*t1*de}
        w = 0 if ts<=0.5*de else 1 if ts>=de else (ts-0.5*de)/(0.5*de)
        Ft=min(thin.values()); Fk=min(thick.values()); F=Ft+(Fk-Ft)*w
        gid = min(thin,key=thin.get) if w<0.5 else min(thick,key=thick.get)
        return F, gid, f1, My
    gid=min(modes,key=modes.get); return modes[gid], gid, f1, My
CASES=[
 ('Stabdübel 12, Schlitzblech 8 mm, C24, t1 = 60', dict(vm='sdue',d=12,an='SHi',t1=60,ts=8)),
 ('Stabdübel 16 S355, Holz-Holz-Holz, α2 = 90°', dict(vm='sdue',d=16,fu=490,an='HH2',t1=60,t2=100,al2=90)),
 ('Stabdübel 12, Holz-Holz einschnittig 40/60', dict(vm='sdue',d=12,an='HH1',t1=40,t2=60)),
 ('Stabdübel 10, Bleche außen 4 mm (dünn)', dict(vm='sdue',d=10,an='SHa',t1=80,t2=100,ts=4)),
 ('Stabdübel 10, Bleche außen 7 mm (interpoliert)', dict(vm='sdue',d=10,an='SHa',t1=80,t2=100,ts=7)),
 ('Stabdübel 12, Blech einschnittig 12 mm (dick)', dict(vm='sdue',d=12,an='SH1',t1=80,ts=12)),
 ('Nagel 4,0 nicht vorgebohrt, HH1 40/60', dict(vm='nagel',d=4,an='HH1',t1=40,t2=60)),
 ('Nagel 5,0 vorgebohrt, HH1 30/70', dict(vm='nagel',d=5,an='HH1',t1=30,t2=70,vorg=True)),
 ('Holzschraube 8/5,4, Fax = 6 kN, HH1 40/80', dict(vm='schraube',d=8,dk=5.4,an='HH1',t1=40,t2=80,fax=6)),
 ('Holzschraube 10/7, Fax = 8 kN, Blech einschnittig 5 mm', dict(vm='schraube',d=10,dk=7,an='SH1',t1=100,ts=5,fax=8)),
]
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('holz'); setHoMode('verbindung')")
        for name,c in CASES:
            await pg.select_option('#hv-vm', c['vm']); await pg.select_option('#hv-an', c['an'])
            vals={'hv-d':c['d'],'hv-t1':c['t1'],'hv-t2':c.get('t2',80),'hv-ts':c.get('ts',8),'hv-al1':c.get('al1',0),'hv-al2':c.get('al2',0),'hv-dk':c.get('dk',5.4),'hv-fax':c.get('fax',0)}
            for k,v in vals.items(): await pg.evaluate(f"$('{k}').value='{v}'")
            await pg.evaluate(f"$('hv-fu').value='{c.get('fu',360)}'")
            await pg.evaluate(f"$('hv-vorg').checked={'true' if c.get('vorg') else 'false'}; run()")
            F,gid,f1,My=ref(c)
            got=await pg.evaluate("[LAST.res.FvRk, LAST.res.gov.id, LAST.res.f1, LAST.res.K.My]")
            ok = abs(got[0]-F)<0.5 and got[1]==gid and abs(got[2]-f1)<1e-6 and abs(got[3]-My)<1e-3
            check(f'{name}: F_v,Rk = {F/1000:.3f} kN, Modus {gid}', ok, f'App {got[0]/1000:.3f} kN ({got[1]})')
        # wirksame Anzahl und Gesamttragfähigkeit: Stabdübel 12, n = 4, a1 = 84 (7d), m = 2, zweischnittig
        await pg.select_option('#hv-vm','sdue'); await pg.select_option('#hv-an','SHi')
        for k,v in {'hv-d':12,'hv-t1':60,'hv-ts':8,'hv-al1':0,'hv-n':4,'hv-m':2,'hv-a1':84,'hv-F':40}.items(): await pg.evaluate(f"$('{k}').value='{v}'")
        await pg.evaluate("run()")
        F,_,_,_=ref(dict(vm='sdue',d=12,an='SHi',t1=60,ts=8))
        nef=min(4, 4**0.9*(84/(13*12))**0.25); R=2*nef*2*0.8*F/1.3
        t=await pg.inner_text('#details')
        check(f'n_ef = {nef:.2f}, F_v,Rd,ges = {R/1000:.1f} kN', f'= {nef:.2f}'.replace('.',',') in t and f'= {R/1000:.1f} kN'.replace('.',',') in t)
        # Abstände: a1 = 50 < 5d = 60 → nicht erfüllt
        await pg.evaluate("$('hv-a1').value='50'; run()")
        ab=await pg.evaluate("LAST.res.C.find(c=>c.id==='hvabst')")
        check('a₁ = 50 mm < (3+2)·12 = 60 mm → Abstände nicht erfüllt', not ab['ok'])
        # Nagel nicht vorgebohrt: zu dünnes Holz
        await pg.select_option('#hv-vm','nagel'); await pg.select_option('#hv-an','HH1')
        for k,v in {'hv-d':5,'hv-t1':24,'hv-t2':60,'hv-a1':80,'hv-a2':30,'hv-a3':80,'hv-a4':30}.items(): await pg.evaluate(f"$('{k}').value='{v}'")
        await pg.evaluate("$('hv-vorg').checked=false; run()")
        t=await pg.inner_text('#n-hvabst')
        treq=max(7*5,(13*5-30)*350/400)
        check(f'Nagel 5 mm: Mindestholzdicke {treq:.1f} mm > 24 mm → nicht erfüllt', f'{treq:.1f}'.replace('.',',') in t and not (await pg.evaluate("LAST.res.C.find(c=>c.id==='hvabst').ok")))
        await pg.evaluate("showReport()"); r=await pg.inner_text('#report')
        check('Bericht: Johansen-Modi und Abstände', 'Holzverbindung' in r or 'Anschluss V1' in r)
        await pg.evaluate("hideReport()"); await pg.reload(); await pg.wait_for_timeout(300)
        check('Neuladen: Modus Verbindung bleibt erhalten', await pg.is_visible('#ho-verb') and await pg.input_value('#hv-d')=='5')
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
