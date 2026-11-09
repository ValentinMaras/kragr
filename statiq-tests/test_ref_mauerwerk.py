# statiq·ref v0.3.15 Mauerwerk: f_k (EN 1996-1-1 Gl. 3.1–3.3), Maßordnung, Knicklänge ρ2/ρ3/ρ4, Wand (vereinfachtes Verfahren),
# Teilflächenpressung, Kellerwand, Schubwand — gegen eigene Python-Rechnung und gegen die Rechenkerne von statiq·size.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
URL='file://'+BASE+'/ref.html'; SIZE='file://'+BASE+'/size.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
de=lambda v,d=2: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
def has(t,v,d): t=t.replace('\n',' '); return de(v,d) in t or de(v,d) in t.replace('.','')
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
fd=lambda f: 0.85*f/1.5
PAGES=['baustoffe/steine','baustoffe/massordnung','baustoffe/moertel','baustoffe/festigkeit','bemessung/knicklaenge','bemessung/wand','bemessung/teilflaeche','bemessung/keller','bemessung/schub']

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        sz=await br.new_page(); sz.on('pageerror', lambda e: errs.append('size: '+str(e))); await sz.goto(SIZE); await sz.wait_for_timeout(300)
        async def go(t): await pg.goto(URL+'#/mauerwerk/'+t); await pg.wait_for_timeout(200)
        async def setv(prefix, vals, fn):
            await pg.evaluate("([p,v,fn])=>{ for(const [k,x] of Object.entries(v)) document.getElementById(p+k).value=String(x); window[fn](); }", [prefix, vals, fn]); await pg.wait_for_timeout(40)
        async def out(id): return await pg.evaluate(f"document.getElementById('{id}').innerText")

        # ── f_k ──
        await go('baustoffe/festigkeit'); okk=True; bad=[]
        n=0
        for art in TAB:
            for m in ['nm','dm']:
                for fb,fm in [(15,10),(8,20),(25,5),(4,2.5)]:
                    await setv('fk-', {'art':art,'m':m,'fb':fb,'fm':fm}, 'updateFk'); o=await out('fk-out'); f=fk(art,m,fb,fm)
                    if f is None:
                        if 'NA' not in o: okk=False; bad.append((art,m,fb,fm,'Hinweis fehlt'))
                        continue
                    n+=1
                    if not (has(o,f,1) and has(o,fd(f),3)): okk=False; bad.append((art,m,fb,fm,f))
        check(f'f_k und f_d aus der NA-Tabelle: 9 Steinarten × 2 Mörtel × 4 Fälle ({n} mit Wert, sonst Hinweis)', okk and n>=30, bad[:3])
        await setv('fk-', {'art':'z2','m':'nm','fb':12,'fm':5}, 'updateFk'); o=await out('fk-out'); E=1100*fk('z2','nm',12,5)
        check(f'E-Modul Hochlochziegel = 1100 · f_k = {E:.0f} N/mm²', has(o,E,0), o[-120:])
        km=await pg.evaluate('[MW_NA_T, MW_NA_ART, MWR_ART]'); kz=await sz.evaluate('[MW_NA_T, MW_NA_ART, MW_ART]')
        check('NA-Tabellen und Steinarten identisch mit kragr·size', km==kz)

        # ── Maßordnung ──
        await go('baustoffe/massordnung')
        for L,typ in [(136.5,'Außenmaß'),(101,'Öffnungsmaß'),(100,'Anbaumaß'),(130,'passt nicht')]:
            await setv('ms-', {'L':L,'H':250,'s':12.5}, 'updateMass'); o=await out('ms-out')
            check(f'Maßordnung {L} cm → {typ}', typ in o, o.split('\n')[-3:])
        await setv('ms-', {'L':100,'H':255,'s':25}, 'updateMass'); o=await out('ms-out')
        check('Höhe 255 cm, Schicht 25 cm → 10 oder 11 Schichten', '10 Schichten = 250,0 cm' in o and '11 Schichten = 275,0 cm' in o)

        # ── Knicklänge ──
        await go('bemessung/knicklaenge')
        def rho(n,h,l,t,dec):
            r2=1.0 if dec=='hb' else (0.75 if t<=175 else 0.9 if t<=250 else 1.0)
            if n==3:
                if l>=15*t/1000: return r2
                return r2/(1+(r2*h/(3*l))**2) if h<=3.5*l else 1.5*l/h
            if n==4:
                if l>=30*t/1000: return r2
                return r2/(1+(r2*h/l)**2) if h<=1.15*l else 0.5*l/h
            return r2
        cases=[(2,2.6,1,175,'sb'),(2,2.6,1,240,'sb'),(2,2.6,1,300,'sb'),(2,2.6,1,175,'hb'),(3,2.6,1.5,175,'sb'),(3,2.75,0.7,240,'sb'),(3,2.6,3,175,'sb'),(4,2.6,3.5,175,'sb'),(4,3.0,2.0,240,'sb'),(4,2.6,6,175,'sb')]
        okk=True; bad=[]
        for n,h,l,t,dec in cases:
            await setv('hef-', {'n':n,'h':h,'l':l,'t':t,'d':dec}, 'updateHef'); o=await out('hef-out'); r=rho(n,h,l,t,dec); lam=r*h*1000/t
            if not (has(o,r*h,3) and has(o,lam,1) and has(o,0.85-0.0011*lam*lam,3)): okk=False; bad.append((n,h,l,t,dec,round(r,4)))
        check('Knicklänge: 10 Fälle zwei-/drei-/vierseitig inkl. 15t/30t-Grenze und h > 3,5l / 1,15l', okk, bad[:3])
        check('Halterungsskizze im Rechner', await pg.evaluate("document.querySelectorAll('#hef-fig svg').length")==1)

        # ── Wand: Python und size ──
        await go('bemessung/wand')
        def wand(art,m,fb,fm,t,h,l,lage,dec,a,lf):
            f=fk(art,m,fb,fm); A=l*t/1000; r=1.0 if dec=='hb' else (0.75 if t<=175 else 0.9 if t<=250 else 1.0); lam=r*h*1000/t
            fdd=fd(f)*(0.8 if A<0.1 else 1); P2=0.85*a/t-0.0011*lam**2
            P1=None if lage=='zw' else 0.333*a/t if lage=='dach' else min((1.6-lf/(6 if f>=1.8 else 5))*a/t, 0.9*a/t)   # NA: mit a/t
            Phi=min(P2, P1 if P1 is not None else 9); return f, Phi*fdd*A*1000, Phi
        okk=True; bad=[]
        for c in [('k1','dm',15,10,175,2.6,1.0,'end','sb',150,5.0),('z2','nm',8,5,365,2.75,2.0,'end','sb',250,6.0),('k1','nm',20,10,240,2.75,0.4,'zw','sb',240,4),
                  ('p1','dm',2,10,300,2.5,1.5,'end','sb',200,4.5),('l1','nm',4,5,175,2.5,0.5,'dach','hb',175,5),('k2','dm',12,10,115,2.5,0.8,'zw','sb',115,3)]:
            art,m,fb,fm,t,h,l,lage,dec,a,lf=c; f,NRd,Phi=wand(*c)
            await setv('mwd-', {'art':art,'m':m,'fb':fb,'fm':fm,'t':t,'h':h,'l':l,'lage':lage,'d':dec,'a':a,'lf':lf,'N':100}, 'updateMWD'); o=await out('mwd-out')
            s_=await sz.evaluate("I=>nachweiseMD(I).NRd", {'M':{'fk':f,'fd':fd(f),'grp':GRP[art]},'t':t,'h':h,'l':l,'lage':lage,'decke':dec,'a':a,'lf':lf,'N':100})
            if not (has(o,NRd,1) and has(o,Phi,3) and abs(s_-NRd)<1e-6*max(1,NRd)): okk=False; bad.append((c,round(NRd,2),round(s_,2)))
        check('Wand N_Rd: 6 Fälle (End-/Zwischenauflager, Dach, kurze Wand, f_k < 1,8) = Python = size', okk, bad[:2])

        # ── Teilflächenpressung ──
        await go('bemessung/teilflaeche'); okk=True; bad=[]
        for art,m,fb,fm,t,hc,lw,lb,bb,a1,N in [('z1','nm',15,5,240,2.5,3.0,200,175,300,110),('k1','dm',20,10,175,2.75,2.0,150,175,0,80),('z2','nm',12,10,240,2.5,3,200,240,500,100),('k1','dm',12,10,240,1.0,1.2,300,240,100,90)]:
            f=fk(art,m,fb,fm); hcm=hc*1000; sp=hcm/(2*math.sqrt(3)); left=min(a1,sp); right=min(lw*1000-a1-lb,sp); lefm=lb+left+right
            Ab=lb*bb; Aef=lefm*t; b=(1+0.3*a1/hcm)*(1.5-1.1*Ab/Aef); b=min(max(b,1),min(1.25+a1/(2*hcm),1.5));
            if GRP[art]>1: b=1
            NRd=b*Ab*fd(f)/1000
            await setv('mwt-', {'art':art,'m':m,'fb':fb,'fm':fm,'t':t,'hc':hc,'lw':lw,'lb':lb,'bb':bb,'a1':a1,'N':N}, 'updateMWT'); o=await out('mwt-out')
            s_=await sz.evaluate("I=>nachweiseMT(I).NRd", {'M':{'fk':f,'fd':fd(f),'grp':GRP[art]},'t':t,'hc':hc,'lb':lb,'bb':bb,'a1':a1,'lw':lw,'N':N})
            if not (has(o,b,3) and has(o,NRd,1) and abs(s_-NRd)<1e-6*NRd): okk=False; bad.append((art,a1,round(b,4),round(NRd,2),round(s_,2)))
        check('Teilflächenpressung: 4 Fälle (Wandende, Lochstein, kurze Wand) = Python = size', okk, bad[:2])

        # ── Kellerwand ──
        await go('bemessung/keller'); okk=True; bad=[]
        for t,h,he,bc,rho_ in [(300,2.5,2.0,4.0,19),(240,2.4,2.2,2.0,20),(365,2.6,1.5,6.0,18),(240,2.5,2.5,3.5,19)]:
            beta=20 if bc>=2*h else 40 if bc<=h else 60-20*bc/h; nreq=rho_*h*he*he/(beta*t/1000); f=fk('k1','nm',16,10); nlim=t*fd(f)/3
            await setv('mwk-', {'art':'k1','m':'nm','fb':16,'fm':10,'t':t,'h':h,'he':he,'bc':bc,'rho':rho_,'q':5,'Nmax':150,'Nmin':40}, 'updateMWK'); o=await out('mwk-out')
            s_=await sz.evaluate("I=>{const r=nachweiseMK(I); return [r.nreq,r.nlim]}", {'M':{'fk':f,'fd':fd(f),'grp':1},'t':t,'h':h,'he':he,'bc':bc,'rho':rho_,'q':5,'Nmax':150,'Nmin':40})
            if not (has(o,nreq,1) and has(o,nlim,1) and abs(s_[0]-nreq)<1e-6 and abs(s_[1]-nlim)<1e-6): okk=False; bad.append((t,bc,round(nreq,2),s_))
        check('Kellerwand: β für b_c ≥ 2h, ≤ h und dazwischen; n_min,erf und n_max,zul = size', okk, bad[:2])

        # ── Schubwand ──
        await go('bemessung/schub'); okk=True; bad=[]
        for art,m,fb,fm,l,t,h,lag,st,N,V in [('k1','dm',25,10,2.5,175,2.75,'krag','1',150,25),('z1','nm',12,10,4.0,240,2.75,'eing','0',300,60),('k2','nm',12,5,1.5,175,2.5,'krag','0',80,8),('z2','nm',8,2.5,3.0,365,2.75,'krag','0',400,20)]:
            f=fk(art,m,fb,fm); typ=art[0]
            fvk0 = 0.22 if m=='dm' else (.26 if fm>=20 else .22 if fm>=10 else .18 if fm>=5 else .08)   # DIN EN 1996-1-1/NA (Lücking Tab. 8, KS-Themenheft 9 Tafel 18)
            Mb=V*h*(1 if lag=='krag' else 0.5); e=Mb/N; lc=l if e<=l/6 else max(0,3*(l/2-e)); sd=N/(t*lc)
            fv=min((0.5 if st=='1' else 1)*fvk0+0.4*sd, 0.065*fb); VRd=fv/1.5*t*lc
            await setv('mws-', {'art':art,'m':m,'fb':fb,'fm':fm,'l':l,'t':t,'h':h,'lag':lag,'st':st,'N':N,'V':V}, 'updateMWS'); o=await out('mws-out')
            s_=await sz.evaluate("I=>nachweiseMH(I).VRd", {'M':{'fk':f,'fd':fd(f),'grp':GRP[art],'fvk0':fvk0,'fb':fb},'l':l,'t':t,'h':h,'lag':lag,'N':N,'V':V,'stoss':st=='1'})
            if not (has(o,lc,3) and has(o,VRd,1) and abs(s_-VRd)<1e-6*VRd): okk=False; bad.append((art,lag,round(lc,3),round(VRd,2),round(s_,2)))
        check('Schubwand: 4 Fälle (klaffende Fuge, eingespannt, Stoßfugen) = Python = size', okk, bad[:2])

        # ── Seiten ──
        bad=[]
        for vp in [(1440,900),(390,844)]:
            await pg.set_viewport_size({'width':vp[0],'height':vp[1]})
            for t in PAGES:
                await go(t)
                if await pg.evaluate("/NaN|undefined|Infinity/.test(document.getElementById('main').innerHTML)"): bad.append((vp[0],t,'NaN'))
                if await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth+1"): bad.append((vp[0],t,'Überlauf'))
        check(f'{len(PAGES)} Mauerwerk-Seiten Desktop + 390 px: keine NaN, kein Seitenüberlauf', not bad, bad)
        check('Keine JavaScript-Fehler', not errs, errs[:3])
        await br.close()

asyncio.run(main())
print('FEHLER:', fails); sys.exit(1 if fails else 0)
