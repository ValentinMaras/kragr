# statiq·ref v0.3.11 Holzbau: Querschnittstabellen, Beiwerte, Einfeldträger, Knicken, Kippen, Druck unter Winkel, Abbrand.
# Unabhängig nachgerechnet in Python (EN 1995-1-1/-1-2 mit NA), Torsion per Reihenlösung (Saint-Venant).
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
de=lambda v,d=2: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
def has(t,v,d): t=t.replace('\n',' '); return de(v,d) in t or de(v,d) in t.replace('.','')
def rel(a,b): return abs(a-b)/max(abs(b),1e-12)
# Materialwerte (EN 338 / EN 14080): fm, fv, fc90, fc0, E0mean, E005, Gmean
MAT={'C24':(24,4.0,2.5,21,11000,7400,690),'C30':(30,4.0,2.7,23,12000,8000,750),'C16':(16,3.2,2.2,17,8000,5400,500),
     'GL24h':(24,3.5,2.5,24,11500,9600,650),'GL28h':(28,3.5,2.5,28,12600,10500,650),'GL24c':(24,3.5,2.5,21.5,11000,9100,650)}
KMOD=[[0.6,0.7,0.8,0.9,1.1],[0.6,0.7,0.8,0.9,1.1],[0.5,0.55,0.65,0.7,0.9]]
def kmod(nkl,k): r=KMOD[nkl]; return (r[3]+r[4])/2 if k=='wind' else r[int(k)]
def kh(bsh,h): return (min((600/h)**0.1,1.1) if h<600 else 1) if bsh else (min((150/h)**0.2,1.3) if h<150 else 1)
def it_series(b,h):
    s,l=min(b,h),max(b,h); S=sum(math.tanh(n*math.pi*l/(2*s))/n**5 for n in range(1,200,2))
    return s**3*l/3*(1-192/math.pi**5*s/l*S)

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL+'#/holzbau/baustoffe/querschnitte'); await pg.wait_for_timeout(300)
        vh=await pg.evaluate("QS_VH"); bsh=await pg.evaluate("QS_BSH")
        bad=[]
        for r in vh+bsh:
            b,h=r['b'],r['h']
            for k,v in [('A',b*h/100),('Iy',b*h**3/12e4),('Wy',b*h*h/6e3),('Iz',h*b**3/12e4),('iy',h/math.sqrt(12)/10),('G',b*h*420/1e6)]:
                if rel(r[k],v)>1e-9: bad.append((r['n'],k))
            if rel(r['It'],it_series(b,h)/1e4)>1e-6: bad.append((r['n'],'It',r['It'],it_series(b,h)/1e4))
        check(f'{len(vh)} VH- und {len(bsh)} BSH-Querschnitte: A, I, W, i, G exakt; I_t = Reihenlösung', not bad and len(vh)>=70 and len(bsh)>=200, bad[:3])
        beta=await pg.evaluate("[1,1.5,2,3,4,6,10].map(k=>itRect(100,100*k)/(100**4*k))")
        ref=[0.1406,0.196,0.229,0.263,0.281,0.299,0.312]   # Tabellenwerte (Timoshenko/Goodier)
        check('I_t = β·b³·h: β für h/b = 1 … 10 wie Tabellenwerte (±0,5 %)', all(rel(a,b)<0.005 for a,b in zip(beta,ref)), [round(x,4) for x in beta])
        kv=[r['n'] for r in vh if r['kvh']]
        check('KVH-Vorzugsquerschnitte markiert (25 Stück, z. B. 60×120, 100×200)', len(kv)==25 and '60×120' in kv and '100×200' in kv, len(kv))
        await pg.click('.chip[data-bb="200"]')
        n=await pg.evaluate("[...document.querySelectorAll('#bsh-tbl tbody tr')].map(r=>r.cells[0].textContent)")
        check('BSH-Breite 200 wählen → Höhen 240 … 1200', n[0]=='200×240' and n[-1]=='200×1200' and len(n)==25, (n[0],n[-1],len(n)))
        await pg.fill('.tbl-filter input','100×2'); await pg.wait_for_timeout(100)
        vis=await pg.evaluate("[...document.querySelectorAll('#vh-tbl tbody tr')].filter(r=>r.style.display!=='none').length")
        check('Filter „100×2“ in der Vollholztabelle (200 … 280)', vis==5, vis)
        # Beiwerte
        await pg.goto(URL+'#/holzbau/baustoffe/beiwerte'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.getElementById('main').innerText")
        check('k_h-Tabelle (VH 100 mm, BSH 200 mm) und k_cr (C24 0,500, GL24h 0,714)', has(t,(150/100)**0.2,3) and has(t,min((600/200)**0.1,1.1),3) and '0,500' in t and '0,714' in t)
        # ── Einfeldträger ──
        await pg.goto(URL+'#/holzbau/gzt/biegung'); await pg.wait_for_timeout(300)
        QA={'nA':('2',0.3),'nC':('3',0.6),'s':('3',0.0),'w':('wind',0.0)}
        async def hef(o):
            await pg.evaluate("o=>{ for(const [k,v] of Object.entries(o)) document.getElementById('hef-'+k).value=String(v); updateHEF(); }", o); await pg.wait_for_timeout(80)
            return await pg.evaluate("document.getElementById('hef-out').innerText")
        for o in [dict(cls='C24',nkl=0,b=120,h=240,L=4.0,lA=100,g=2.0,q=2.5,qa='nA'),
                  dict(cls='GL24h',nkl=1,b=140,h=400,L=7.5,lA=120,g=3.5,q=4.0,qa='s'),
                  dict(cls='C30',nkl=2,b=80,h=140,L=3.0,lA=80,g=0.8,q=0.6,qa='nC'),
                  dict(cls='C24',nkl=0,b=100,h=200,L=3.5,lA=100,g=5.0,q=0.5,qa='nA')]:
            out=await hef(o); fm,fv,fc90,fc0,E0,E05,G=MAT[o['cls']]; bshf=o['cls'].startswith('GL')
            kG=kmod(o['nkl'],'0'); kq,p2=QA[o['qa']]; kQ=kmod(o['nkl'],kq)
            w1=1.35*o['g']; w2=1.35*o['g']+1.5*o['q']; w,km=(w1,kG) if w1/kG>w2/kQ else (w2,kQ)
            Md=w*o['L']**2/8; Vd=w*o['L']/2; W=o['b']*o['h']**2/6; I=o['b']*o['h']**3/12
            sm=Md*1e6/W; fmd=km*kh(bshf,o['h'])*fm/1.3
            kcr=min(1,(2.5 if bshf else 2.0)/fv); tau=1.5*Vd*1e3/(kcr*o['b']*o['h']); fvd=km*fv/1.3
            sc90=Vd*1e3/(o['b']*(o['lA']+30)); e90=sc90/((1.75 if bshf else 1.5)*km*fc90/1.3)
            L=o['L']*1000; wG=5*o['g']*L**4/(384*E0*I); wQ=5*o['q']*L**4/(384*E0*I); kd=[0.6,0.8,2.0][o['nkl']]
            wi=wG+wQ; wf=wG*(1+kd)+wQ*(1+p2*kd); wn=(wG+p2*wQ)*(1+kd)
            vals=[(Md,2),(sm/fmd,3),(tau/fvd,3),(e90,3),(wi,1),(wf,1),(wn,1)]
            okk=all(has(out,v,d) for v,d in vals)
            check(f'Einfeldträger {o["cls"]} {o["b"]}/{o["h"]} L={o["L"]} NKL{o["nkl"]+1} {o["qa"]}: M={Md:.2f}, η_m={sm/fmd:.3f}, η_v={tau/fvd:.3f}, w_fin={wf:.1f}', okk,
                  [ (v,d,has(out,v,d)) for v,d in vals if not has(out,v,d)])
        check('Voreinstellung Einfeldträger: alle Nachweise erfüllt', 'nicht erfüllt' not in await hef(dict(cls='C24',nkl=0,b=120,h=240,L=4.0,lA=100,g=2.0,q=2.5,qa='nA')))
        # ── Knicken ──
        await pg.goto(URL+'#/holzbau/gzt/knicken'); await pg.wait_for_timeout(300)
        async def kn(o):
            await pg.evaluate("o=>{ for(const [k,v] of Object.entries(o)) document.getElementById('hkn-'+k).value=String(v); updateHKN(); }", o); await pg.wait_for_timeout(80)
            return await pg.evaluate("document.getElementById('hkn-out').innerText")
        for o in [dict(cls='C24',b=140,h=140,ly=3.0,lz=3.0,N=80,M=2,nkl=0,kled='2'),dict(cls='GL24h',b=120,h=240,ly=4.5,lz=2.25,N=150,M=6,nkl=1,kled='3'),dict(cls='C16',b=100,h=100,ly=1.0,lz=1.0,N=60,M=0,nkl=0,kled='1')]:
            out=await kn(o); fm,fv,fc90,fc0,E0,E05,G=MAT[o['cls']]; bshf=o['cls'].startswith('GL'); bc=0.1 if bshf else 0.2; km=kmod(o['nkl'],o['kled'])
            def kc(lef,i):
                lr=lef*1000/i/math.pi*math.sqrt(fc0/E05)
                if lr<=0.3: return lr,1.0
                k=0.5*(1+bc*(lr-0.3)+lr*lr); return lr,1/(k+math.sqrt(k*k-lr*lr))
            lry,ky=kc(o['ly'],o['h']/math.sqrt(12)); lrz,kz=kc(o['lz'],o['b']/math.sqrt(12))
            sc=o['N']*1e3/(o['b']*o['h']); fc0d=km*fc0/1.3; sm=o['M']*1e6/(o['b']*o['h']**2/6); fmd=km*kh(bshf,o['h'])*fm/1.3
            e1=sc/(ky*fc0d)+sm/fmd; e2=sc/(kz*fc0d)+0.7*sm/fmd
            vals=[(lry,3),(lrz,3),(e1,3),(e2,3)]+([(ky,3)] if lry>0.3 else [])+([(kz,3)] if lrz>0.3 else [])
            check(f'Knicken {o["cls"]} {o["b"]}/{o["h"]}: λrel {lry:.3f}/{lrz:.3f}, kc {ky:.3f}/{kz:.3f}, (6.23) {e1:.3f}, (6.24) {e2:.3f}', all(has(out,v,d) for v,d in vals), out[-120:].replace('\n',' '))
        # ── Kippen ──
        await pg.goto(URL+'#/holzbau/gzt/kippen'); await pg.wait_for_timeout(300)
        A={'eq':0.9,'eF':0.8,'eM':1.0,'kq':0.5,'kF':0.8}
        async def ki(o):
            await pg.evaluate("o=>{ for(const [k,v] of Object.entries(o)) document.getElementById('hki-'+k).value=String(v); updateHKI(); }", o); await pg.wait_for_timeout(80)
            return await pg.evaluate("document.getElementById('hki-out').innerText")
        for o in [dict(cls='GL24h',b=120,h=480,L=8,sys='eq',lp='o',M=55,nkl=0,kled='2'),dict(cls='C24',b=80,h=240,L=4,sys='eF',lp='s',M=8,nkl=0,kled='2'),
                  dict(cls='GL28h',b=160,h=800,L=12,sys='kq',lp='u',M=200,nkl=1,kled='3'),dict(cls='C24',b=60,h=240,L=6,sys='eM',lp='o',M=4,nkl=0,kled='0')]:
            out=await ki(o); fm,fv,fc90,fc0,E0,E05,G=MAT[o['cls']]; bshf=o['cls'].startswith('GL'); km=kmod(o['nkl'],o['kled'])
            lef=A[o['sys']]*o['L']*1000+{'o':2*o['h'],'s':0,'u':-0.5*o['h']}[o['lp']]
            W=o['b']*o['h']**2/6
            if bshf: sc=math.pi*math.sqrt(1.4*E05*o['h']*o['b']**3/12*540*it_series(o['b'],o['h']))/(lef*W)   # NA: E·G × 1,4 bei BSH
            else: sc=0.78*o['b']**2*E05/(o['h']*lef)
            lr=math.sqrt(fm/sc); kc_=1 if lr<=0.75 else 1.56-0.75*lr if lr<=1.4 else 1/lr**2
            eta=o['M']*1e6/W/(kc_*km*kh(bshf,o['h'])*fm/1.3)
            tolok = has(out,lr,3) or has(out,lr+0.001,3) or has(out,lr-0.001,3)   # I_t-Näherung vs. Reihenlösung
            check(f'Kippen {o["cls"]} {o["b"]}/{o["h"]} {o["sys"]}/{o["lp"]}: l_ef = {lef:.0f}, λrel,m = {lr:.3f}, k_crit = {kc_:.3f}, η = {eta:.3f}',
                  has(out,lef,0) and tolok and any(has(out,eta+d,3) for d in (0,0.001,-0.001)), out[-140:].replace('\n',' '))
        check('Voreinstellung Kippen erfüllt', 'nicht erfüllt' not in await ki(dict(cls='GL24h',b=120,h=480,L=8,sys='eq',lp='o',M=55,nkl=0,kled='2')))
        # ── Druck unter Winkel ──
        await pg.goto(URL+'#/holzbau/gzt/zugdruck'); await pg.wait_for_timeout(300)
        for a,kc90 in [(30,1.0),(0,1.0),(90,1.5),(60,1.25)]:
            await pg.evaluate(f"document.getElementById('hwi-a').value='{a}'; document.getElementById('hwi-kc').value='{kc90}'; updateHWI()")
            out=await pg.evaluate("document.getElementById('hwi-out').innerText")
            k=0.8; f0=k*21/1.3; f9=k*2.5/1.3; s=math.sin(math.radians(a)); c=math.cos(math.radians(a))
            fca=f0/(f0/(kc90*f9)*s*s+c*c)
            check(f'Druck unter {a}° (k_c,90 = {kc90}): f_c,α,d = {fca:.2f} N/mm²', has(out,fca,2) and has(out,40000/6000/fca,3))
        # ── Abbrand ──
        await pg.goto(URL+'#/holzbau/gzt/brand'); await pg.wait_for_timeout(300)
        for cls,b,h,t,sd,M in [('GL24h',160,400,30,3,40),('C24',120,240,15,4,5),('GL28h',200,600,90,3,150)]:
            await pg.evaluate(f"(()=>{{ const v={{cls:'{cls}',b:{b},h:{h},t:{t},s:'{sd}',M:{M}}}; for(const [k,x] of Object.entries(v)) document.getElementById('hbr-'+k).value=String(x); updateHBR(); }})()")
            out=await pg.evaluate("document.getElementById('hbr-out').innerText")
            bsh_=cls.startswith('GL'); bn=0.7 if bsh_ else 0.8; k0=1 if t>=20 else t/20; d=bn*t+k0*7
            bef=b-2*d; hef=h-(2 if sd==4 else 1)*d; W=bef*hef**2/6; ffi=(1.15 if bsh_ else 1.25)*MAT[cls][0]
            check(f'Abbrand {cls} {b}/{h} R{t} {sd}-seitig: d_ef = {d:.1f}, Rest {bef:.1f}×{hef:.1f}, η = {M*1e6/W/ffi:.3f}', has(out,d,1) and has(out,bef,1) and has(out,hef,1) and has(out,M*1e6/W/ffi,3))
        # mobil + Fehler
        await pg.set_viewport_size({'width':390,'height':844}); bad=[]
        for tp in ['baustoffe/querschnitte','baustoffe/beiwerte','gzt/biegung','gzt/zugdruck','gzt/knicken','gzt/kippen','gzt/brand']:
            await pg.goto(URL+'#/holzbau/'+tp); await pg.wait_for_timeout(150)
            r=await pg.evaluate("[document.documentElement.scrollWidth, /NaN|undefined|Infinity/.test(document.getElementById('main').innerText)]")
            if r[0]>390 or r[1]: bad.append((tp,r))
        check('7 Holzbau-Seiten: keine NaN, Handy ohne Querscrollen', not bad, bad)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
