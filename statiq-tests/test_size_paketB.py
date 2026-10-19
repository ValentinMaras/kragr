# statiq·size v0.5.21 Paket B: Brandschutz Stahlbeton (Tabellen), Zugkraftdeckung am Durchlaufträger, Zugstab mit Lochschwächung
# und Blockversagen, Stumpfnaht, Querzug (Holz), Durchbruch (Holz), Pfette mit Doppelbiegung, Ausfachungswand.
# Geprüft: Ergebnisse gegen unabhängige Handrechnung in Python, Abhilfe mit Stellschraube, Bericht, Speichern/Laden, Englisch. Ohne Playwright: SKIP.
import os, sys, re, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
SIZE='file://'+BASE+'/size.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
near=lambda a,b,r=1e-3: abs(a-b)<=r*max(1,abs(b))
GO={'brandschutz':"setMat('beton'); setTyp('brandschutz')", 'zugkraft':"setMat('beton'); setTyp('zugkraft')", 'zugstab':"setMat('stahl'); setStMode('zugstab')",
    'stumpf':"setMat('stahl'); setStMode('stumpf')", 'querzug':"setMat('holz'); setHoMode('querzug')", 'durchbruch':"setMat('holz'); setHoMode('durchbruch')",
    'doppel':"setMat('holz'); setHoMode('doppel')", 'ausfach':"setMat('mauer'); setMwMode('ausfach')"}
FYD=500/1.15
# ── unabhängige Handrechnungen ──
TAB55={60:[(120,40),(160,35),(200,30),(300,25)], 90:[(150,55),(200,45),(300,40),(400,35)]}
def brand_balken(R,b,cv,dsw,ds,einlagig):
    T=TAB55[R]; a=cv+dsw+ds/2
    if b<T[0][0]: return dict(a=a, areq=None)
    ar=T[-1][1]
    for (b1,a1),(b2,a2) in zip(T,T[1:]):
        if b<=b2: ar=a1+(a2-a1)*(b-b1)/(b2-b1); break
    if einlagig and b<T[3][0]: ar+=10
    return dict(a=a, areq=ar)
def cnom(ds, cmin_dur=10, dev=10): return max(ds, cmin_dur, 10)+dev     # XC1
def zugkraft(b,h,l,q,MA,MB,cot,dsw,ds,nd,ng,dso,no,fctk=2.0):
    cu=max(cnom(dsw), cnom(ds)-dsw); co=max(cnom(dsw), cnom(dso)-dsw)
    du=h-cu-dsw-ds/2; dob=h-co-dsw-dso/2; zu=0.9*du; zo=0.9*dob; al=zu*cot/2; L=l*1000
    N=600; X=[i*L/N for i in range(N+1)]; M=[-MA*(1-x/L)-MB*x/L+q*x*(L-x)/2/1e6 for x in X]
    Fu=[max(max(M[j],0) for j in range(N+1) if abs(X[j]-x)<=al+1e-9)*1e6/zu/1000 for x in X]
    fbd=2.25*fctk/1.5; lb=ds/4*FYD/fbd; lbd=max(lb,10*ds,100)
    Fd=nd*math.pi*ds*ds/4*FYD/1000; idx=[i for i,f in enumerate(Fu) if f>Fd+1e-9]
    g1=max(0,X[idx[0]]-lbd) if idx else None; g2=min(L,X[idx[-1]]+lbd) if idx else None
    fbo=2.25*(1 if h<=300 else 0.7)*fctk/1.5; lbo=max(dso/4*FYD/fbo, 10*dso, 100)
    Fo=[max(max(-M[j],0) for j in range(N+1) if abs(X[j]-x)<=al+1e-9)*1e6/zo/1000 for x in X]
    eB=L
    for i in range(N,-1,-1):
        if Fo[i]>1e-9: eB=X[i]
        else: break
    return dict(al=al, Fumax=max(Fu), Mmax=max(M), g1=g1, g2=g2, lenB=(L-eB)+lbo if MB>0 else 0, FoS=Fo[N])
def zugstab(fy,fu,b,t,d0,n1,n2,e1,p1,p2):
    e2=(b-(n2-1)*p2)/2; Npl=b*t*fy; Nu=0.9*(b-n2*d0)*t*fu/1.25
    Anv=2*(e1+(n1-1)*p1-(n1-0.5)*d0)*t
    VI=fu*(n2-1)*(p2-d0)*t/1.25+fy*Anv/math.sqrt(3) if n2>1 else float('inf'); VA=fu*2*(e2-d0/2)*t/1.25+fy*Anv/math.sqrt(3)
    return dict(Npl=Npl, Nu=Nu, Veff=min(VI,VA), e2=e2)
def stumpf_voll(fy,t,l,N,V,M):
    A=t*l; W=t*l*l/6; sN=N*1e3/A; sM=abs(M)*1e6/W; tau=1.5*abs(V)*1e3/A
    return dict(sR=abs(sN)+sM, sv=max(abs(sN)+sM, math.sqrt(sN**2+3*tau**2)), eta=max(abs(sN)+sM, math.sqrt(sN**2+3*tau**2))/fy)
def stumpf_teil(fu,bw,a,l,N,V,M):
    A=a*l; W=a*l*l/6; s=abs(N*1e3/A)+abs(M)*1e6/W; t=abs(V)*1e3/A
    return max(math.sqrt(s*s+3*t*t)/(fu/(bw*1.25)), s/(0.9*fu/1.25))
def querzug(ft90d,h,a,ar,tef):
    al=a/h; ks=max(1,0.7+1.4*ar/h); return ks*(6.5+18*al*al)*(tef*h)**0.8*ft90d/1000
def durchbruch(form,b,h,hd,hro,V,M,ft90d):
    hru=h-hro-hd; hr=min(hro,hru)+(0.15*hd if form=='k' else 0)
    Ft=V*hd/(4*h)*(3-hd**2/h**2)+0.008*M*1000/hr
    lt=0.353*hd+0.5*h if form=='k' else 0.5*(hd+h); kt=min(1,math.sqrt(450/h))
    return dict(Ft=Ft, R=0.5*lt*b*kt*ft90d/1000)
def doppel(b,h,L,qv,qn,al,fmd,bsh=True):
    a=math.radians(al); qz=qv*math.cos(a)+qn; qy=qv*math.sin(a); My=qz*L*L/8; Mz=qy*L*L/8
    kh=lambda x: min((600/x)**0.1,1.1) if (bsh and x<600) else (min((150/x)**0.2,1.3) if (not bsh and x<150) else 1)
    sy=My*1e6/(b*h*h/6); sz=Mz*1e6/(h*b*b/6); fy=fmd*kh(h); fz=fmd*kh(b)
    return dict(My=My, Mz=Mz, eM=max(sy/fy+0.7*sz/fz, 0.7*sy/fy+sz/fz))
AF={115:[(12,8),None],150:[(12,8),(8,5)],175:[(20,14),(13,9)],240:[(36,25),(23,16)],300:[(50,33),(35,23)]}   # DIN EN 1996-3/NA Tab. NA.C.1
def ausfach(t,h,l,z,sfk):
    eps=max(h,l)/min(h,l); row=AF[t][[8,20].index(z)]
    if row is None: return dict(A=h*l, Azul=0)
    f=4/3 if sfk>=12 and t<=150 else 1; a1,a2=row[0]*f,row[1]*f; A=a1+(a2-a1)*min(max(eps-1,0),1)
    return dict(A=h*l, Azul=A)

async def res(pg, go, vals={}):
    await pg.evaluate(go); await pg.wait_for_timeout(40)
    for k,v in vals.items(): await pg.evaluate(f"$('{k}').value='{v}'; $('{k}').dispatchEvent(new Event('change',{{bubbles:true}})); run()")
    return await pg.evaluate("LAST && LAST.res ? Object.fromEntries(Object.entries(LAST.res).filter(([k,v])=>typeof v==='number' || typeof v==='boolean' || v===null)) : null")
async def checks(pg): return await pg.evaluate("Object.fromEntries(LAST.res.C.map(c=>[c.id,[c.eta,c.ok,!!c.info]]))")
async def fresh(pg): await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(150)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1400,'height':1000}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(SIZE); await fresh(pg)
        # Brandschutz
        r=await res(pg, GO['brandschutz']); e=brand_balken(60,300,22,8,20,True)
        check('Brandschutz Balken R 60, b = 300: a = 40 mm, a_erf = 25 mm (letzte Spalte, kein Zuschlag)', near(r['a'],e['a']) and near(r['areq'],e['areq']), (r['a'], r['areq']))
        r=await res(pg, GO['brandschutz'], {'fb-R':'90','in-b':'25'}); e=brand_balken(90,250,22,8,20,True); C=await checks(pg)
        check('R 90, b = 250: a_erf linear 42,5 + 10 (Eckstab einlagig) = 52,5 mm, nicht erfüllt', near(r['areq'],e['areq']) and near(e['areq'],52.5) and not C['fba'][1], (r['areq'], e['areq']))
        r=await res(pg, GO['brandschutz'], {'fb-lagen':'2','fb-cv':'40'}); e=brand_balken(90,300,40,8,20,False)
        check('mehrlagig, c_v = 40 vorgegeben (b wieder 300): a = 58 ≥ 40', near(r['a'],58) and near(r['areq'],e['areq']), (r['a'], r['areq']))
        r=await res(pg, GO['brandschutz'], {'in-b':'14'}); C=await checks(pg)
        check('b = 140 < b_min = 150 (R 90): Mindestbreite nicht erfüllt', not C['fbb'][1] and r['areq'] is None, C['fbb'])
        await fresh(pg); r=await res(pg, GO['brandschutz'], {'fb-art':'platte','in-h':'9','fb-R':'90','fb-ds':'10'}); C=await checks(pg)
        check('Platte R 90: h_min = 100 mm > 90 mm, a = 20 + 5 = 25 < 30 mm', not C['fbh'][1] and not C['fba'][1] and near(r['a'],25) and r['hmin']==100, (r['a'], C))
        # Zugkraftdeckung
        await fresh(pg)
        for vals,args,tag in [({},(300,600,6,40,0,150,1.2,8,16,2,2,16,4),'Endfeld'),({'zk-MA':'90','zk-MB':'120','zk-q':'50','zk-cot':'2.0','zk-ds':'20','zk-nd':'3','zk-ng':'1'},(300,600,6,50,90,120,2.0,8,20,3,1,16,4),'Innenfeld, cot 2,0')]:
            r=await res(pg, GO['zugkraft'], vals); e=zugkraft(*args)
            ok=near(r['al'],e['al']) and near(r['Fumax'],e['Fumax']) and ((r['g1'] is None and e['g1'] is None) or (near(r['g1'],e['g1']) and near(r['g2'],e['g2']))) and near(r['lenB'],e['lenB'])
            check(f'Zugkraftdeckung {tag}: a_l, max F_sd, Staffelung, Länge oben', ok, (round(r['al'],1), round(r['Fumax'],2), r['g1'], e['g1'], round(r['lenB']), round(e['lenB'])))
        r=await res(pg, GO['zugkraft'], {'zk-nd':'2','zk-ng':'7'}); C=await checks(pg)
        check('nur 2 von 9 Stäben bis zum Auflager: 22 % < 25 %', not C['zkauf'][1] and near(C['zkauf'][0],1.125), C['zkauf'])
        # Zugstab
        await fresh(pg)
        for vals,args,tag in [({},(235,360,160,12,22,3,2,50,70,80),'S235'),({'zb-st':'S355','zb-n1':'2','zb-n2':'3','zb-b':'220','zb-p2':'70','zb-e1':'40'},(355,490,220,12,22,2,3,40,70,70),'S355, 2 × 3')]:
            r=await res(pg, GO['zugstab'], vals); e=zugstab(*args)
            check(f'Zugstab {tag}: N_pl,Rd, N_u,Rd, V_eff,1,Rd', near(r['Npl'],e['Npl']) and near(r['Nu'],e['Nu']) and near(r['Veff'],e['Veff']), (round(r['Nu']/1e3,1), round(e['Nu']/1e3,1), round(r['Veff']/1e3,1), round(e['Veff']/1e3,1)))
        # Stumpfnaht
        await fresh(pg)
        r=await res(pg, GO['stumpf']); e=stumpf_voll(235,15,200,500,100,5); C=await checks(pg)
        check('Stumpfnaht durchgeschweißt: σ am Rand, σ_v in der Mitte, η', near(r['sR'],e['sR']) and near(C['bwnaht'][0],e['eta']), (round(C['bwnaht'][0],4), round(e['eta'],4)))
        r=await res(pg, GO['stumpf'], {'bw-art':'teil','bw-a':'10','bw-st':'S355'}); C=await checks(pg); e=stumpf_teil(490,0.9,10,200,500,100,5)
        check('nicht durchgeschweißt a = 10, S355: richtungsbezogen mit β_w = 0,9', near(C['bwnaht'][0],e), (round(C['bwnaht'][0],4), round(e,4)))
        # Querzug
        await fresh(pg); ft90d=0.8*0.5/1.3
        r=await res(pg, GO['querzug']);
        check('Querzug GL24h: F_90,Rd nach NA', near(r['R'],querzug(ft90d,400,200,100,120)), (round(r['R'],3), round(querzug(ft90d,400,200,100,120),3)))
        r=await res(pg, GO['querzug'], {'qz-a':'120','qz-ar':'300'})
        check('a/h = 0,3, a_r = 300 → k_s = 1,75', near(r['ks'],1.75) and near(r['R'],querzug(ft90d,400,120,300,120)), (r['ks'], round(r['R'],3)))
        r=await res(pg, GO['querzug'], {'qz-a':'300'}); C=await checks(pg)
        check('a/h = 0,75 > 0,7: kein Nachweis erforderlich (Info)', r['frei'] and C['qznw'][2], C['qznw'])
        # Durchbruch
        await fresh(pg)
        r=await res(pg, GO['durchbruch']); e=durchbruch('k',140,600,90,255,20,25,ft90d)
        check('Durchbruch rund: F_t,90,d und F_t,90,Rd', near(r['Ft'],e['Ft']) and near(r['R'],e['R']), (round(r['Ft'],3), round(e['Ft'],3), round(r['R'],3)))
        r=await res(pg, GO['durchbruch'], {'db-form':'r','db-a':'300','db-hd':'180','db-hro':'160'}); e=durchbruch('r',140,600,180,160,20,25,ft90d)
        check('Durchbruch rechteckig: h_r ohne Zuschlag, l_t,90 = 0,5·(h_d + h)', near(r['Ft'],e['Ft']) and near(r['R'],e['R']), (round(r['Ft'],3), round(e['Ft'],3)))
        r=await res(pg, GO['durchbruch'], {'db-hd':'220'}); C=await checks(pg)
        check('h_d = 220 > 0,15·h = 90: Grenze für unverstärkte Durchbrüche nicht eingehalten', not C['dbgeo'][1], C['dbgeo'])
        # Doppelbiegung
        await fresh(pg)
        r=await res(pg, GO['doppel']); e=doppel(120,240,4.5,3.0,0.5,30,0.8*24/1.3)
        check('Pfette GL24h 120/240, α = 30°: M_y, M_z, Interaktion mit k_h', near(r['My'],e['My']) and near(r['Mz'],e['Mz']) and near(r['eM'],e['eM']), (round(r['eM'],4), round(e['eM'],4)))
        r=await res(pg, GO['doppel'], {'hx-art':'vh','dp-b':'100','dp-h':'200','dp-al':'45'}); await pg.evaluate("$('hx-kl').value='C24'; run()")
        r=await pg.evaluate("Object.fromEntries(Object.entries(LAST.res).filter(([k,v])=>typeof v==='number'))"); e=doppel(100,200,4.5,3.0,0.5,45,0.8*24/1.3,False)
        check('Pfette C24 100/200, α = 45°: k_h bei Vollholz (b = 100 < 150)', near(r['eM'],e['eM']), (round(r['eM'],4), round(e['eM'],4)))
        # Ausfachung
        await fresh(pg); ok=True; info=[]
        for t,h,l,z,sfk in [(175,2.75,5.0,8,4),(115,2.5,3.0,8,4),(240,3.0,7.0,20,4),(300,3.5,4.0,20,4),(150,2.0,5.0,20,12),(115,2.5,2.5,8,12),(115,2.0,5.0,20,4)]:
            r=await res(pg, GO['ausfach'], {'af-t':t,'af-h':h,'af-l':l,'af-z':z,'af-sfk':sfk}); e=ausfach(t,h,l,z,sfk)
            if not (near(r['A'],e['A']) and near(r['Azul'],e['Azul'])): ok=False; info.append((t,h,l,z,sfk,r['Azul'],e['Azul']))
        check('Ausfachung nach Tab. NA.C.1: 7 Fälle (Dicke, ε, Höhe, SFK ≥ 12, 115 mm über 8 m)', ok, info)
        # Abhilfe
        CASES=[('brandschutz',{'fb-R':'90','in-b':'25'},'fba','fb-cv',35),('zugkraft',{'zk-ng':'0'},'zkfeld','zk-ng',None),('zugstab',{'zb-N':'420'},'zbnet','zb-t',None),
               ('stumpf',{'bw-M':'10'},'bwnaht','bw-t',None),('querzug',{'qz-F':'25'},'qznw','qz-a',None),('durchbruch',{'db-V':'60'},'dbft','db-hd',None),
               ('doppel',{'dp-qv':'5'},'dpm','dp-b',None),('ausfach',{'af-l':'6.5'},'afa','af-t','240')]
        for mode,vals,cid,lev,exp in CASES:
            await fresh(pg); await res(pg, GO[mode], vals)
            await pg.wait_for_function("document.querySelector('.fixbox') || !document.querySelector('#chk-table .tag.bad')", timeout=15000)
            fx=dict(await pg.evaluate(f"(LAST.res.C.find(c=>c.id==='{cid}').fix||[]).map(f=>[f.id,f.v])"))
            box=await pg.evaluate(f"(document.querySelector('#n-{cid} .fixbox')||{{}}).innerText||''")
            okv = lev in fx and (exp is None or str(fx[lev])==str(exp))
            check(f'Abhilfe {mode}: Ursache und Stellschraube {lev}'+(f' = {exp}' if exp else ''), 'Warum nicht erfüllt?' in box and okv, fx)
            if lev in fx:
                await pg.evaluate(f"document.querySelector('#n-{cid} .fixbox button[data-fix=\"{lev}\"]').click()"); await pg.wait_for_timeout(120)
                check(f'Abhilfe {mode}: „Übernehmen“ erfüllt {cid}', await pg.evaluate(f"LAST.res.C.find(c=>c.id==='{cid}').ok"))
        # Bericht, Positionen
        await fresh(pg); ok=True
        for m,go in GO.items():
            await pg.evaluate(go); await pg.wait_for_timeout(40); rep=await pg.evaluate("buildReport()")
            if not ('<h1>' in rep and 'Eingaben' in rep and 'Zusammenfassung' in rep and '<svg' in rep): ok=False
        check('Bericht für alle 8 neuen Modi', ok)
        await pg.evaluate(GO['zugstab']+"; $('zb-N').value='300'; run(); savePos()")
        await pg.evaluate(GO['ausfach']+"; $('af-l').value='4.4'; run(); savePos()")
        await pg.evaluate("loadPos(0)"); await pg.wait_for_timeout(80)
        check('Position Zugstab speichern und laden', await pg.evaluate("MAT==='stahl' && STMODE==='zugstab' && $('zb-N').value==='300' && $('st-zugstab').style.display===''"))
        await pg.evaluate("loadPos(1)"); await pg.wait_for_timeout(80)
        check('Position Ausfachung laden (Mauerwerkskarte ausgeblendet)', await pg.evaluate("MAT==='mauer' && MWMODE==='ausfach' && $('af-l').value==='4.4' && $('mw-mat-card').style.display==='none'"))
        check('Positionsliste kennt die Bauteilart', await pg.evaluate("posRead().map(p=>p.typ)")==['stahl_zugstab','mauer_ausfach'])
        # Englisch
        await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(250)
        GER=re.compile(r'[äöüÄÖÜß]|\b(und|der|die|das|mit|nicht|oder|für|bei|nach|ist|wird|vorhanden|erf|vorh|zul|Nachweis|Stäbe|Blech|Naht|Pfette|Wand|Querschnitt|unten|oben)\b')
        left={}
        for m,go in GO.items():
            await pg.evaluate(go); await pg.wait_for_timeout(60)
            t=await pg.evaluate("[...['summary','chk-table','details','fig','reinf-line','page-title','page-sub'].map(i=>['page-title','page-sub'].includes(i) ? document.getElementById(i).textContent : document.getElementById(i).innerText), (()=>{const d=document.createElement('div'); d.innerHTML=trFig(buildReport()); return d.innerText})()].join('\\n')")
            for line in t.split('\n'):
                mm=GER.search(line)
                if mm: left.setdefault(m, line[max(0,mm.start()-30):mm.start()+40])
        check('EN: Ergebnis, Rechenweg, Abbildung und Bericht ohne deutsche Reste (8 Modi)', not left, left)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
