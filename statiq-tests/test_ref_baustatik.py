# statiq·ref v0.3.16 Baustatik: Durchlaufträger (Dreimomentengleichung gegen FEM, Laststellungen per Durchprobieren),
# Steiner gegen shapely, Fachwerk (Ritterschnitt) gegen Knotengleichgewicht als Gleichungssystem, Dreigelenkrahmen gegen
# Starrkörpergleichgewicht, Kraftgrößenverfahren gegen FEM, Einflusslinien gegen wandernde Last.
import os, sys, math, asyncio, itertools
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
    from shapely.geometry import box
    from shapely.ops import unary_union
except ImportError:
    print('SKIP Playwright/shapely nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
de=lambda v,d=2: (f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',','))
def has(t,v,d):
    t=t.replace('\n',' ').replace('−','-'); s=de(v,d)
    return s in t or s in t.replace('.','')

def fem_beam(spans, udl, pts, ne=40):
    """Euler-Bernoulli-FEM, EI = 1. spans: Feldlängen; udl: q je Feld; pts: [(Feld, a, F)].
    Liefert Funktion M(x global) und Auflagerkräfte."""
    xs=[0.0]; edges=[0]; off=0.0
    for i,L in enumerate(spans):
        cuts=sorted(set([j*L/ne for j in range(ne+1)]+[a for (f,a,F) in pts if f==i]))
        for c in cuts[1:]: xs.append(off+c)
        off+=L; edges.append(len(xs)-1)
    xs=np.array(xs); n=len(xs); K=np.zeros((2*n,2*n)); P=np.zeros(2*n); el=[]
    for e in range(n-1):
        x1,x2=xs[e],xs[e+1]; L=x2-x1; xm=(x1+x2)/2; f=int(np.searchsorted(np.cumsum(spans),xm)); q=udl[f]
        k=np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],[-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])/L**3
        idx=[2*e,2*e+1,2*e+2,2*e+3]; K[np.ix_(idx,idx)]+=k; fe=np.array([q*L/2,q*L*L/12,q*L/2,-q*L*L/12]); P[idx]+=fe; el.append((idx,k,fe,x1,L,q))
    for (f,a,F) in pts:
        x=sum(spans[:f])+a; j=int(np.argmin(abs(xs-x))); P[2*j]+=F
    sup=[edges[i] for i in range(len(spans)+1)]; fixed=[2*j for j in sup]; free=[i for i in range(2*n) if i not in fixed]
    # w nach unten positiv → Lasten positiv
    u=np.zeros(2*n); u[free]=np.linalg.solve(K[np.ix_(free,free)],P[free]); R=K@u-P
    def M(x):
        e=min(int(np.searchsorted(xs,x,side='right'))-1,n-2); idx,k,fe,x1,L,q=el[e]; f_=k@u[idx]-fe
        Ml,Mr=f_[1],-f_[3]  # Biegemoment (Zug unten positiv) an den Elementenden
        s=x-x1; return Ml+(Mr-Ml)*s/L+q*s*(L-s)/2
    return M, [-R[2*j] for j in sup], xs

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def go(t): await pg.goto(URL+'#/baustatik/'+t); await pg.wait_for_timeout(200)
        async def setv(prefix, vals, fn):
            await pg.evaluate("([p,v,fn])=>{ for(const [k,x] of Object.entries(v)) document.getElementById(p+k).value=String(x); window[fn](); }", [prefix, vals, fn]); await pg.wait_for_timeout(40)
        async def out(id): return await pg.evaluate(f"document.getElementById('{id}').innerText")

        # ── Durchlaufträger: JS-Dreimomentengleichung gegen FEM ──
        await go('balkentafeln/durchlauf'); okk=True; bad=[]
        rng=np.random.default_rng(3)
        for n in [2,3,4,5]:
            for _ in range(3):
                ld=[float(v) for v in np.round(rng.uniform(0,2,n),2)]; r=await pg.evaluate(f"dltRechnung({n},{ld},1.7)")
                M,R,xs=fem_beam([1.7]*n, ld, [])
                Ms=[M(1.7*i-1e-9) if i>0 else 0 for i in range(n+1)]; Ms[-1]=0
                xx=np.linspace(0,1.7*n,4001); Mf=[max(M(x) for x in xx if 1.7*i<=x<=1.7*(i+1)) for i in range(n)]
                if not (np.allclose(r['Ms'],Ms,atol=1e-6) and np.allclose(r['R'],R,atol=1e-6) and np.allclose(r['Mf'],Mf,atol=2e-4)): okk=False; bad.append((n,ld))
        check('Dreimomentengleichung: 12 Durchlaufträger (2–5 Felder, beliebige q) = FEM', okk, bad[:2])
        exact={2:([0.375,1.25],[-0.125]),3:([0.4,1.1],[-0.1]),4:([11/28,32/28],[-3/28,-2/28])}
        okk=True
        for n,(Rx,Mx) in exact.items():
            r=await pg.evaluate(f"dltRechnung({n},Array({n}).fill(1),1)"); okk&=np.allclose(r['R'][:len(Rx)],Rx) and np.allclose(r['Ms'][1:1+len(Mx)],Mx)
        check('Tabellenwerte 2/3/4 Felder exakt (3/8, 5/4, 2/5, 11/10, 11/28, 8/7, −3/28 …)', okk)
        # Laststellungen per Durchprobieren mit FEM
        okk=True
        for n in [3,4]:
            E=await pg.evaluate(f"dltExtrem({n})"); bestF=-9; bestS=9
            for pat in itertools.product([0,1],repeat=n):
                M,R,xs=fem_beam([1.0]*n,list(pat),[]); xx=np.linspace(0,1,801)
                bestF=max(bestF,max(M(x) for x in xx)); bestS=min(bestS,M(1.0-1e-9))
            okk&=abs(E['maxF'][0]-bestF)<2e-4 and abs(E['minS'][1]-bestS)<1e-6
        check('Laststellungen: max Feld 1 und min M_B für 3 und 4 Felder = Durchprobieren (FEM)', okk)
        n,L,g,q=3,5,8,6; await setv('dlt-', {'n':n,'L':L,'g':g,'q':q}, 'updateDLT'); o=await out('dlt-out')
        MF1=max(max(fem_beam([L]*n,[1.35*g+1.5*q*p_ for p_ in pat],[])[0](x) for x in np.linspace(0,L,401)) for pat in itertools.product([0,1],repeat=n))
        MB=min(fem_beam([L]*n,[1.35*g+1.5*q*p_ for p_ in pat],[])[0](L-1e-9) for pat in itertools.product([0,1],repeat=n))
        check(f'Bemessung 3 Felder g=8, q=6: M_F1,d = {MF1:.2f}, M_B,d = {MB:.2f} kNm', has(o,MF1,2) and has(o,MB,2), o.split('\n')[-12:-8])

        # ── Steiner gegen shapely ──
        await go('querschnitte/querschnittswerte'); okk=True; bad=[]
        for T in [[(20,2,0),(2,18,2)],[(30,2,0),(1.2,26,2),(30,2,28)],[(16,1.5,0),(0.8,20,1.5),(24,2.5,21.5)],[(12,24,0)],[(40,4,0),(10,30,4),(25,5,34),(8,6,39)]]:
            vals={}
            for i in range(4):
                b,h,z=T[i] if i<len(T) else (0,0,0); vals.update({f'b{i+1}':b,f'h{i+1}':h,f'z{i+1}':z})
            await setv('stq-', vals, 'updateSteiner'); o=await out('stq-out')
            poly=unary_union([box(-b/2,-(z+h),b/2,-z) for b,h,z in T]); A=poly.area; cy=-poly.centroid.y
            # I_y numerisch über Streifen
            Iy=sum(b*h**3/12+b*h*((z+h/2)-cy)**2 for b,h,z in T)  # nur gültig ohne Überlappung → shapely-Fläche prüft das
            ys=np.linspace(min(-(z+h) for b,h,z in T),0,20001); dy=ys[1]-ys[0]
            from shapely.geometry import LineString
            Inum=sum(poly.intersection(LineString([(-1e3,y),(1e3,y)])).length*(-y-cy)**2*dy for y in ys[:-1]+dy/2)
            if not (has(o,A,1) and has(o,cy,2) and abs(Iy-Inum)/Inum<1e-3 and (de(Iy,0) in o.replace('.','') )): okk=False; bad.append((T,A,round(cy,3),round(Iy),round(Inum)))
        check('Steiner-Rechner: 5 Querschnitte, A und z_s = shapely, I_y = Streifenintegration', okk, bad[:2])

        # ── Fachwerk: Gleichungssystem aller Knoten ──
        await go('tragwerke/fachwerk'); okk=True; bad=[]
        for n,a,h,F,P,k in [(4,3,2,10,0,-1),(6,2.5,2,20,0,-1),(8,2,1.5,15,30,3),(6,3,2.5,0,50,1)]:
            nodes=[(i*a,0) for i in range(n+1)]+[(i*a,h) for i in range(n+1)]; U=lambda i:i; O=lambda i:n+1+i
            mem=[]; kind=[]
            for i in range(n): mem.append((O(i),O(i+1))); kind.append(('O',i))
            for i in range(n): mem.append((U(i),U(i+1))); kind.append(('U',i))
            for i in range(n): mem.append((O(i),U(i+1)) if i<n/2 else (U(i),O(i+1))); kind.append(('D',i))
            for i in range(n+1): mem.append((U(i),O(i))); kind.append(('V',i))
            nn=len(nodes); unk=len(mem)+3; Amat=np.zeros((2*nn,unk)); b=np.zeros(2*nn)
            for m,(i,j) in enumerate(mem):
                dx,dy=np.subtract(nodes[j],nodes[i]); Lm=math.hypot(dx,dy); c,s=dx/Lm,dy/Lm
                Amat[2*i,m]+=c; Amat[2*i+1,m]+=s; Amat[2*j,m]-=c; Amat[2*j+1,m]-=s
            Amat[0,len(mem)]=1; Amat[1,len(mem)+1]=1; Amat[2*n+1,len(mem)+2]=1
            for i in range(n+1): b[2*O(i)+1]+= (F/2 if i in (0,n) else F)+(P if i==k else 0)
            x=np.linalg.lstsq(Amat,b,rcond=None)[0]
            await setv('fw-', {'n':n,'a':a,'h':h,'F':F,'P':P,'k':k}, 'updateFW')
            R=await pg.evaluate(f"fachwerk({n},{a},{h},{F},{P},{k})")
            js={('O',i):R['O'][i] for i in range(n)}|{('U',i):R['U'][i] for i in range(n)}|{('D',i):R['D'][i] for i in range(n)}|{('V',i):R['V'][i] for i in range(n+1)}
            dev=max(abs(js[kk]-x[m]) for m,kk in enumerate(kind))
            o=await out('fw-out')
            if dev>1e-8 or not has(o,R['O'][n//2-1],2): okk=False; bad.append((n,round(dev,6)))
        check('Fachwerk: 4 Parallelträger (auch unsymmetrische Last) = Knotengleichgewicht (lstsq)', okk, bad)

        # ── Dreigelenkrahmen ──
        await go('tragwerke/dreigelenk'); okk=True; bad=[]
        for l,h,q,W in [(10,4,12,8),(8,5,10,0),(12,3,0,20),(6,6,15,5)]:
            # Unbekannte: Ah,Av,Bh,Bv,Gh,Gv  (G: Kraft vom rechten auf den linken Teil)
            Am=np.zeros((6,6)); bb=np.zeros(6)
            # linker Teil: Fuß A (0,0), Eck (0,h), Riegel bis G (l/2,h); Lasten W bei (0,h), q auf 0..l/2
            Am[0]=[1,0,0,0,1,0]; bb[0]=-W
            Am[1]=[0,1,0,0,0,1]; bb[1]=q*l/2
            Am[2]=[0,0,0,0,-h,l/2]; bb[2]=-(-h*W)+q*l/2*l/4   # Momente um A: x·Fy − y·Fx
            # rechter Teil: Fuß B (l,0), G-Kraft umgekehrt
            Am[3]=[0,0,1,0,-1,0]; bb[3]=0
            Am[4]=[0,0,0,1,0,-1]; bb[4]=q*l/2
            Am[5]=[0,0,0,0,h,l/2]; bb[5]=-q*l*l/8   # um B (l,0): −G bei (l/2,h) → (−l/2)·(−Gv) − h·(−Gh); q rechts: (−l/4)·(−q·l/2)
            x=np.linalg.solve(Am,bb); Ah,Av,Bh,Bv=x[:4]
            await setv('dgr-', {'l':l,'h':h,'q':q,'W':W}, 'updateDGR'); R=await pg.evaluate(f"dreigelenk({l},{h},{q},{W})"); o=await out('dgr-out')
            Mc=-Ah*h; Md=Bh*h
            if not (np.allclose([R['Ah'],R['Av'],R['Bh'],R['Bv']],[Ah,Av,Bh,Bv],atol=1e-9) and abs(R['Mc']-Mc)<1e-9 and abs(R['Md']-Md)<1e-9 and has(o,Mc,2) and has(o,Bv,2)): okk=False; bad.append((l,h,q,W,x[:4].round(3),R))
        check('Dreigelenkrahmen: 4 Fälle = Starrkörpergleichgewicht beider Teile (6 Gleichungen)', okk, bad[:1])
        Mb=await pg.evaluate("(()=>{const R=dreigelenk(10,4,12,8); return R.Mb(5)})()"); check('Riegelmoment am Gelenk = 0', abs(Mb)<1e-9, Mb)

        # ── Kraftgrößenverfahren gegen FEM ──
        await go('arbeitssatz/kraftgroessen'); okk=True; bad=[]
        for l1,l2,q1,q2,F1,F2 in [(5,4,10,10,0,20),(6,6,8,8,0,0),(4,7,0,12,30,0),(5,3,15,5,10,10)]:
            M,R,xs=fem_beam([l1,l2],[q1,q2],[(0,l1/2,F1),(1,l2/2,F2)])
            MB=M(l1); m1=max(M(x) for x in np.linspace(0,l1,2001)); m2=max(M(x) for x in np.linspace(l1,l1+l2,2001))
            await setv('kgv-', {'l1':l1,'l2':l2,'q1':q1,'q2':q2,'F1':F1,'F2':F2}, 'updateKGV'); o=await out('kgv-out')
            if not all(has(o,v,2) for v in [MB,R[0],R[1],R[2],m1,m2]): okk=False; bad.append((l1,l2,round(MB,3),[round(r,3) for r in R],round(m1,3),round(m2,3)))
        check('Kraftgrößenverfahren Zweifeldträger: 4 Fälle M_B, A, B, C, Feldmomente = FEM', okk, bad[:2])

        # ── Einflusslinien: wandernde Last ──
        await go('balkentafeln/einflusslinien'); okk=True
        for L,x0,F,q in [(8,2,50,10),(10,5,0,12),(6,1.5,40,0),(9,7,30,8)]:
            # Einflusslinien links und rechts von x₀ getrennt integrieren (Sprung der Q-Linie bei x₀)
            xl=np.linspace(0,x0,4001); xr=np.linspace(x0,L,4001)
            eMl=xl*(L-x0)/L; eMr=x0*(L-xr)/L; eQl=-xl/L; eQr=1-xr/L
            Mmax=F*max(eMl.max(),eMr.max())+q*(np.trapezoid(eMl,xl)+np.trapezoid(eMr,xr))
            Qp=F*eQr.max()+q*np.trapezoid(eQr,xr); Qn=F*eQl.min()+q*np.trapezoid(eQl,xl)
            await setv('el-', {'L':L,'x':x0,'F':F,'q':q}, 'updateEL'); o=await out('el-out')
            okk&=has(o,Mmax,2) and has(o,Qp,2) and has(o,Qn,2)
        check('Einflusslinien: max M(x₀), max/min Q(x₀) = wandernde Last + Integration (4 Fälle)', okk)

        # ── Seiten ──
        PAGES=['balkentafeln/durchlauf','balkentafeln/einflusslinien','tragwerke/fachwerk','tragwerke/dreigelenk','arbeitssatz/kraftgroessen','querschnitte/querschnittswerte']
        bad=[]
        for vp in [(1440,900),(390,844)]:
            await pg.set_viewport_size({'width':vp[0],'height':vp[1]})
            for t in PAGES:
                await go(t)
                if await pg.evaluate("/NaN|undefined|Infinity/.test(document.getElementById('main').innerHTML)"): bad.append((vp[0],t,'NaN'))
                if await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth+1"): bad.append((vp[0],t,'Überlauf'))
        check(f'{len(PAGES)} neue Baustatik-Seiten Desktop + 390 px: keine NaN, kein Seitenüberlauf', not bad, bad)
        check('Keine JavaScript-Fehler', not errs, errs[:3])
        import re
        from collections import Counter
        src=open(os.path.join(HERE,'..','ref.html'),encoding='utf-8').read()
        dup=[n for n,c in Counter(re.findall(r'^(?:function|const|let) ([A-Za-z_$][\w$]*)',src,re.M)).items() if c>1]
        check('ref.html: keine doppelt definierten Funktionen/Konstanten (überschreiben sich sonst)', not dup, dup)
        await br.close()

asyncio.run(main())
print('FEHLER:', fails); sys.exit(1 if fails else 0)
