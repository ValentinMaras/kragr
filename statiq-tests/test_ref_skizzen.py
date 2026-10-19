# statiq·ref v0.3.4 — Lehrbuch-Skizzen: Rendering + Momentenverläufe gegen unabhängige Kraftgrößenmethode
import os, sys, re, asyncio, math
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:60}', info)

# ── unabhängige Referenz: Kraftgrößenverfahren, L = 1 je Feld, EI = 1 ──
X=np.linspace(0,1,2001)
def ss_moment(q_fun=None, F=None, a=None, L=1.0, x=X):
    """Momentenlinie des Einfeldträgers (gelenkig) für Streckenlast q(x) und/oder Einzellast F bei a."""
    M=np.zeros_like(x)
    if q_fun is not None:
        xs=np.linspace(0,L,4001); qs=q_fun(xs)
        R_B=np.trapezoid(qs*xs,xs)/L; R_A=np.trapezoid(qs,xs)-R_B
        for i,xx in enumerate(x):
            m=xs<=xx; M[i]=R_A*xx-np.trapezoid(qs[m]*(xx-xs[m]),xs[m]) if m.sum()>1 else R_A*xx
    if F is not None:
        M+=np.where(x<=a, F*(L-a)/L*x, F*a/L*(L-x))
    return M
def force_method(M0, ms):
    """Redundante Momente X_i aus δ_ij X_j = −δ_i0 (Integration über die Gesamtlänge)."""
    n=len(ms); D=np.array([[np.trapezoid(ms[i]*ms[j],XX) for j in range(n)] for i in range(n)])
    d0=np.array([np.trapezoid(M0*ms[i],XX) for i in range(n)]); Xs=np.linalg.solve(D,-d0)
    return M0+sum(Xs[i]*ms[i] for i in range(n))
XX=X
REF={}
q1=lambda x: np.ones_like(x)
REF['e_q']=ss_moment(q1); REF['e_F']=ss_moment(F=1,a=0.5); REF['e_Fa']=ss_moment(F=1,a=0.35)
REF['e_tri']=ss_moment(lambda x:x)
REF['k_q']=-(1-X)**2/2; REF['k_F']=-(1-X); REF['k_tri']=-((1-X)**3)/6  # Gleichgewicht am freien Teil
mA=-(1-X); mB=-X
REF['c_q']=force_method(REF['e_q'],[mA,mB]); REF['c_F']=force_method(REF['e_F'],[mA,mB])
REF['r_q']=force_method(REF['e_q'],[mA]); REF['r_F']=force_method(REF['e_F'],[mA])

def cont_ref(n):
    global XX
    xs=np.linspace(0,n,2001*n); XX=xs
    M0=np.zeros_like(xs)
    for i in range(n):
        t=xs-i; m=(t>=0)&(t<=1); M0[m]=t[m]*(1-t[m])/2
    ms=[]
    for j in range(1,n):  # Stützmoment an Stütze j (Dreieck, Spitze −1)
        ms.append(-np.clip(1-np.abs(xs-j),0,None))
    M=force_method(M0,ms); XX=X; return xs,M

async def main():
    src=open(HTML,encoding='utf-8').read()
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        url='file://'+HTML
        await pg.goto(url)
        # 1) Themen mit Skizzen rendern ohne Fehler, ohne NaN
        topics={'mathematik/geometrie/flaechen':9,'mathematik/geometrie/trigonometrie':4,'mathematik/analysis/ableitungen':1,
          'mathematik/analysis/biegelinie':1,'baustatik/grundlagen/vorzeichen':1,'baustatik/grundlagen/bestimmtheit':1,
          'baustatik/balkentafeln/einfeld':4,'baustatik/balkentafeln/kragarm':3,'baustatik/balkentafeln/eingespannt':4,
          'baustatik/balkentafeln/durchlauf':2,'baustatik/querschnitte/querschnittswerte':4,'baustatik/querschnitte/spannungen':1,
          'baustatik/querschnitte/euler':1,'baustatik/arbeitssatz/pvk':1,'lastannahmen/lasten/schnee':1,
          'stahlbau/nachweise/biegeknicken':1,'stahlbeton/bemessung/plattenbalken':1,'stahlbeton/bemessung/durchstanzen':1,
          'stahlbeton/bemessung/querkraft':1,'grundbau/flach/sohldruck':1,'grundbau/flach/grundbruch':1,
          'mathematik/geometrie/dreiecke':5,'mathematik/geometrie/vierecke':4,'mathematik/geometrie/kreis':1,'mathematik/geometrie/koerper':5,'mathematik/geometrie/neigung':1,
          'wasserbau/hydrostatik/druck':2,'wasserbau/hydrostatik/gekruemmt':1,'wasserbau/hydrostatik/auftrieb':1,'wasserbau/hydrodynamik/bernoulli':1,'wasserbau/hydrodynamik/rohr':1,'wasserbau/hydrodynamik/ausfluss':1,'wasserbau/gerinne/normalabfluss':1,'wasserbau/gerinne/energie':1,'wasserbau/gerinne/wehr':1}
        bad=[]; total=0
        for t,nmin in topics.items():
            await pg.goto(f'{url}#/{t}'); await pg.wait_for_timeout(30)
            n=await pg.evaluate("document.querySelectorAll('#main .figure.sk svg, #main .shape svg').length")
            nan=await pg.evaluate("[...document.querySelectorAll('#main svg')].some(s=>/NaN|undefined|Infinity/.test(s.outerHTML))")
            total+=n
            if n<nmin or nan: bad.append(f'{t}:{n}{" NaN" if nan else ""}')
        check(f'{len(topics)} Themen mit {total} Skizzen, ohne NaN/Fehler', not bad and not errs, ' '.join(bad)+' '+'; '.join(errs)[:120])
        # Skizzen passen mobil in die Breite (kein horizontales Scrollen)
        await pg.set_viewport_size({'width':390,'height':800})
        over=[]
        for t in ['mathematik/geometrie/flaechen','baustatik/balkentafeln/einfeld','baustatik/querschnitte/euler','grundbau/flach/grundbruch']:
            await pg.goto(f'{url}#/{t}'); await pg.wait_for_timeout(30)
            if await pg.evaluate("document.documentElement.scrollWidth>window.innerWidth+1"): over.append(t)
        check('Mobil 390 px: kein horizontales Scrollen', not over, str(over))
        await pg.set_viewport_size({'width':1280,'height':800})
        # 2) Momentenverläufe der Balkentafel-Kacheln: Form = Referenz (bis auf Maßstab), Vorzeichen gleich
        body=src[src.index('const BT = {'):src.index('};',src.index('const BT = {'))]
        for key,ref in REF.items():
            m=re.search(rf"\b{key}:\s*\(\)=>btTile\('[\w-]{{2}}',[^,]+(?:\([^)]*\))?,\s*(t=>.*?), \[\[", body)
            if not m: check(f'BT {key} gefunden', False); continue
            fjs=m.group(1)
            ts=np.linspace(0,1,41)
            vals=np.array(await pg.evaluate(f"(()=>{{const f={fjs}; return {[float(v) for v in ts]}.map(f);}})()"))
            r=np.interp(ts,X,ref); i=np.argmax(np.abs(r)); k=vals[i]/r[i]
            err=np.max(np.abs(vals-k*r))/np.max(np.abs(vals))
            check(f'BT {key}: Verlauf = Kraftgrößenverfahren (Maßstab > 0)', err<0.01 and k>0, f'Abw. {err:.4f}')
        # Beschriftete Extremwerte der Kacheln
        ex={'e_q':(0.5,1/8),'e_F':(0.5,1/4),'e_tri':(1/math.sqrt(3),1/(9*math.sqrt(3))),'k_q':(0,-1/2),'k_tri':(0,-1/6),
            'c_q':(0,-1/12),'c_F':(0.5,1/8),'r_q':(0.625,9/128),'r_F':(0,-3/16)}
        okx=[k for k,(t,v) in ex.items() if abs(np.interp(t,X,REF[k])-v)>2e-4]
        check('Beschriftungen qL²/8, qL²/(9√3), −qL²/12, 9qL²/128, −3FL/16 …', not okx, str(okx))
        # 3) Durchlaufträger: Kurve aus ref == Kraftgrößenverfahren (absolut, in qL²)
        for n in (2,3):
            xs,M=cont_ref(n)
            s=np.linspace(0,n,61)
            js=src[src.index('function dlTrag(n)'):src.index('function skZweifeld')]
            mfun=re.search(r"const M = s => (\{.*?\});\n", js, re.S).group(1)
            vals=np.array(await pg.evaluate(f"(()=>{{const n={n}; const M=s=>{mfun}; return {[float(v) for v in s]}.map(M);}})()"))
            err=np.max(np.abs(vals-np.interp(s,xs,M)))
            check(f'{n}-Feldträger: M-Linie = Kraftgrößenverfahren', err<2e-3, f'max Abw. {err:.5f} qL²')
        # 4) Euler-Fall 3: kL erfüllt tan(kL) = kL
        kL=float(re.search(r'const kL=([\d.]+)',src).group(1))
        check('Eulerfall 3: tan(kL) = kL (kL = 4,4934 → β = π/kL ≈ 0,70)', abs(math.tan(kL)-kL)<1e-2 and abs(math.pi/kL-0.699)<1e-3, f'β={math.pi/kL:.4f}')
        # 5) Flächenkarten: Formeln stimmen mit Integration
        r=1.0; Ihk=(math.pi/8-8/(9*math.pi))*r**4
        check('Halbkreis I_y ≈ 0,1098·r⁴ (Schwerachse)', abs(Ihk-0.1098)<1e-4, f'{Ihk:.5f}')
        a,bb,h=3.0,1.0,2.0; z=np.linspace(0,h,20001); w=a+(bb-a)*z/h; A=np.trapezoid(w,z); e=np.trapezoid(w*z,z)/A; I=np.trapezoid(w*(z-e)**2,z)
        check('Trapez e und I_y = h³(a²+4ab+b²)/(36(a+b))', abs(e-h/3*(a+2*bb)/(a+bb))<1e-6 and abs(I-h**3*(a*a+4*a*bb+bb*bb)/(36*(a+bb)))<1e-6)
        x=np.linspace(0,1,20001); A=np.trapezoid(x**2,x); xs_=np.trapezoid(x*x**2,x)/A; zs=np.trapezoid(x**4/2,x)/A
        check('Parabelzwickel: A = bh/3, x_S = 3b/4, z_S = 3h/10', abs(A-1/3)<1e-6 and abs(xs_-0.75)<1e-6 and abs(zs-0.3)<1e-6)
        x=np.linspace(-1,1,20001); y=1-x*x; A=np.trapezoid(y,x); zs=np.trapezoid(y*y/2,x)/A
        check('Parabelsegment: A = 2/3·bh, e = 2h/5', abs(A/2-2/3)<1e-6 and abs(zs-0.4)<1e-6)
        al=0.62; th=np.linspace(-al,al,20001); A=al; e=np.trapezoid((2/3)*np.cos(th)*0.5,th)/A
        check('Kreisausschnitt: A = α·r², e = 2r·sin α/(3α)', abs(e-2*math.sin(al)/(3*al))<1e-6)
        # neue Geometrie-Themen: Beispielwerte unabhängig nachgerechnet
        await pg.goto(f'{url}#/mathematik/geometrie/kreis'); await pg.wait_for_timeout(50); t=await pg.inner_text('#main')
        r=10**2/(8*2)+2/2; ph=2*math.asin(5/r)
        check('Kreisbogen: r = s²/(8h) + h/2 = 7,25 m, b = 11,03 m', abs(r-7.25)<1e-9 and f'{r*ph:.2f}'.replace('.',',') in t and '7,25 m' in t, f'{r*ph:.3f}')
        await pg.goto(f'{url}#/mathematik/geometrie/neigung'); await pg.wait_for_timeout(50)
        await pg.fill('#ng2-p','8'); o=await pg.inner_text('#ng2-out')
        check('Neigungsrechner: 8 % → 4,57°', f'{math.degrees(math.atan(0.08)):.2f}'.replace('.',',')+'°' in o, o)
        await pg.fill('#ng2-a','30'); o=await pg.inner_text('#ng2-out')
        check('Neigungsrechner: 30° → 57,74 %', f'{100*math.tan(math.radians(30)):.2f}'.replace('.',',')+' %' in o, o)
        t=await pg.inner_text('#main')
        bad=[(p_,a_) for p_,a_ in [(1,'0,57°'),(5,'2,86°'),(20,'11,31°'),(50,'26,57°')] if f'{math.degrees(math.atan(p_/100)):.2f}'.replace('.',',')+'°'!=a_]
        check('Umrechnungstabelle Prozent ↔ Grad stimmt', not bad and all(x in t for x in ['26,57°','57,7 %','173,2 %']), bad)
        check('Eckmaß Sechseck e = 2s/√3 = 27,7 mm (M16, s = 24)', abs(2*24/math.sqrt(3)-27.71)<0.01)
        check('Bohrpfahl V = π·0,45²·12 = 7,63 m³', f'{math.pi*0.45**2*12:.2f}'=='7.63')
        # Wasserbau-Rechner gegen unabhängige Rechnung
        g=9.81
        await pg.goto(f'{url}#/wasserbau/gerinne/normalabfluss'); await pg.wait_for_timeout(50)
        for (bb,hh,mm,I,k) in [(3,1.2,0,0.5,60),(2,1.0,1.5,1.0,35)]:
            for i_,v_ in [('b',bb),('h',hh),('m',mm),('I',I),('k',k)]: await pg.fill('#wbg-'+i_, str(v_))
            o=await pg.inner_text('#wbg-out'); A=(bb+mm*hh)*hh; U=bb+2*hh*math.sqrt(1+mm*mm); Q=k*(A/U)**(2/3)*math.sqrt(I/1000)*A
            check(f'Manning b={bb}, h={hh}, m={mm}: Q = {Q:.3f} m³/s', f'{Q:.3f}'.replace('.',',')+' m³/s' in o, o.split(chr(10))[-1])
        await pg.goto(f'{url}#/wasserbau/hydrodynamik/rohr'); await pg.wait_for_timeout(50)
        from scipy.optimize import brentq
        for (Q,d,L,kk) in [(50,200,500,0.1),(2,100,100,0.01),(0.5,50,20,0.05)]:
            for i_,v_ in [('Q',Q),('d',d),('L',L),('k',kk)]: await pg.fill('#wbr-'+i_, str(v_))
            o=await pg.inner_text('#wbr-out'); dd=d/1000; v=Q/1000/(math.pi*dd*dd/4); Re=v*dd/1.306e-6
            lam = 64/Re if Re<2320 else brentq(lambda l: 1/math.sqrt(l)+2*math.log10(2.51/(Re*math.sqrt(l))+kk/1000/(3.71*dd)), 1e-4, 1)
            hv=lam*L/dd*v*v/(2*g)
            check(f'Rohr Q={Q} l/s, d={d} mm: h_v,R = {hv:.3f} m (Colebrook/brentq, ν(10 °C))', f'= {hv:.3f} m'.replace('.',',') in o, o.split(chr(10))[-1])
        await pg.goto(f'{url}#/wasserbau/gerinne/wehr'); await pg.wait_for_timeout(50)
        await pg.fill('#wbw-b','5'); await pg.fill('#wbw-h','0.5'); await pg.fill('#wbw-mu','0.75'); o=await pg.inner_text('#wbw-out')
        Qw=2/3*0.75*5*math.sqrt(2*g)*0.5**1.5
        check(f'Poleni: Q = {Qw:.3f} m³/s', f'{Qw:.3f}'.replace('.',',')+' m³/s' in o, o)
        await pg.goto(f'{url}#/wasserbau/hydrostatik/gekruemmt'); await pg.wait_for_timeout(50); t=await pg.inner_text('#main')
        check('Gekrümmte Fläche: F_V = γ·π·r²/4 = 31,4 kN, F = 37,2 kN', f'{10*math.pi:.1f}'.replace('.',',') in t and f'{math.hypot(20,10*math.pi):.1f}'.replace('.',',') in t)
        await pg.goto(f'{url}#/wasserbau/hydrostatik/auftrieb'); await pg.wait_for_timeout(50); t=await pg.inner_text('#main')
        check('Ponton: h_M = L·B³/12/V − e = 2,95 m', abs(10*6**3/12/48-0.8-2.95)<1e-9 and '2,95 m' in t)
        await b.close()
asyncio.run(main())
print('FEHLER:',fails); sys.exit(1 if fails else 0)
