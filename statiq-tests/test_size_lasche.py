# size v0.7.34: Laschenstoß (geschraubter Universalstoß) — Ergebnisse gegen unabhängige Handrechnung in Python,
# Varianten (zweischnittig, lange Verbindung, große Querkraft), Abhilfe, Bericht, Position speichern/laden, EN/FR/ES. Ohne Playwright: SKIP.
import os, sys, re, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
near=lambda a,b,r=1e-3: abs(a-b)<=r*max(1,abs(b))
GO="setMat('stahl'); setStMode('lasche')"
# Profilwerte IPE 300 / HEB 300 (h, b, t_w, t_f, r, I_y [cm⁴]); Schrauben: d, A_s, d_0; Klassen: f_ub, α_v
PR={'IPE 300':(300,150,7.1,10.7,15,8356),'HEB 300':(300,300,11,19,27,25166)}
BOLT={'M20':(20,245,22),'M24':(24,353,26)}; KL={'8.8':(800,0.6),'10.9':(1000,0.5)}
def bearing(e1,p1,e2,p2,d,d0,fub,fu,t):
    ad=min(e1/(3*d0), p1/(3*d0)-0.25 if p1>0 else 9e9); ab=min(ad,fub/fu,1)
    k1=min(2.8*e2/d0-1.7, 1.4*p2/d0-1.7 if p2>0 else 9e9, 2.5); return k1*ab*fu*d*t/1.25/1000
def hand(prof='IPE 300', bolt='M20', kl='8.8', M=80, V=60, ga='a', ta=12, ti=10, n1=2, e1=40, p1=70, w=90, ts=8, nv=3, pv=70, nh=2, ph=70, es=45, e=85, fy=235, fu=360):
    h,b,tw,tf,r,Iy=PR[prof]; Iy*=1e4; d,As,d0=BOLT[bolt]; fub,av=KL[kl]
    Iw=tw*(h-2*tf)**3/12; Mw=M*Iw/Iy; Ff=(M-Mw)/(h-tf)*1000
    m=2 if ga=='ai' else 1; Fv=m*av*fub*As/1.25/1000; tL=ta+(ti if ga=='ai' else 0)
    Fb=bearing(e1, p1 if n1>1 else 0, (b-w)/2, w, d, d0, fub, fu, min(tf,tL))
    Lj=(n1-1)*p1; beta=1 if Lj<=15*d else min(1,max(0.75,1-(Lj-15*d)/(200*d)))
    Rf=2*n1*min(Fv*beta, Fb)
    bi=math.floor(((b-tw)/2-r)/5)*5; A=b*ta+(2*bi*ti if ga=='ai' else 0); An=A-2*d0*tL
    NL=min(A*fy/1000, 0.9*An*fu/1.25/1000); Nf=min(b*tf*fy/1000, 0.9*(b-2*d0)*tf*fu/1.25/1000)
    zs=[(i-(nv-1)/2)*pv for i in range(nv)]; xs=[(j-(nh-1)/2)*ph for j in range(nh)]
    Ip=sum(x*x+z*z for x in xs for z in zs); Ms=Mw+V*e/1000
    Fx=Ms*1000*max(abs(z) for z in zs)/Ip; Fz=V/(nv*nh)+Ms*1000*max(abs(x) for x in xs)/Ip; F=math.hypot(Fx,Fz)
    pm=min(pv, ph if nh>1 else 9e9); FS=min(2*av*fub*As/1.25/1000, bearing(es,pm,es,pm,d,d0,fub,fu,min(tw,2*ts)))
    hs=(nv-1)*pv+2*es; Vpl=2*ts*hs*fy/math.sqrt(3)/1000; rho=(2*V/Vpl-1)**2 if V>0.5*Vpl else 0; Mel=2*ts*hs*hs/6*fy*(1-rho)/1e6
    return dict(Mw=Mw, Ff=Ff, RgrF=Rf, NL=NL, Nf=Nf, Ms=Ms, Fr=F, FS=FS, Mel=Mel, Vpl=Vpl, hs=hs, bi=bi, beta=beta)
async def res(pg, vals={}):
    await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(120)
    await pg.evaluate(GO); await pg.wait_for_timeout(40)
    for k,v in vals.items(): await pg.evaluate(f"$('{k}').value='{v}'; $('{k}').dispatchEvent(new Event('change',{{bubbles:true}}))")
    await pg.evaluate("run()")
    return await pg.evaluate("Object.fromEntries(Object.entries(LAST.res).filter(([k,v])=>typeof v==='number'))")
def cmp(r,e,keys): return all(near(r[k],e[k]) for k in keys), {k:(round(r[k],3),round(e[k],3)) for k in keys if not near(r[k],e[k])}
async def fresh(pg): await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(150)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1400,'height':1000}); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+BASE+'/size.html'); await fresh(pg)
        K=['Mw','Ff','RgrF','NL','Nf','Ms','Fr','FS','Mel','Vpl','hs']
        r=await res(pg); e=hand(); ok,info=cmp(r,e,K)
        check(f'Vorgabe IPE 300, M20 8.8: M_w = {e["Mw"]:.2f} kNm, F_f = {e["Ff"]:.1f} kN, Steg F = {e["Fr"]:.1f} kN', ok, info)
        C=await pg.evaluate("LAST.res.C.map(c=>[c.id,c.ok])"); check('Vorgabe: alle Nachweise erfüllt', all(x[1] for x in C), C)
        r=await res(pg, {'ls-ga':'ai'}); e=hand(ga='ai'); ok,info=cmp(r,e,K+['bi'])
        check(f'außen und innen: zweischnittig, Innenlaschen 2 × {e["bi"]} mm, Netto mit Σt', ok, info)
        r=await res(pg, {'ls-n1':'6','ls-p1':'80'}); e=hand(n1=6,p1=80); ok,info=cmp(r,e,K)
        check(f'lange Verbindung L_j = 400 mm > 15d: β_Lf = {e["beta"]:.4f}', ok and 'β<sub>Lf</sub>' in await pg.evaluate("LAST.res.C.find(c=>c.id==='lsfs').steps.join(' ')"), info)
        r=await res(pg, {'ls-V':'250','ls-M':'40'}); e=hand(V=250,M=40); ok,info=cmp(r,e,K)
        check('große Querkraft V > 0,5·V_pl: Abminderung ρ der Steglaschen', ok and e['Mel']<2*8*230**2/6*235/1e6, info)
        r=await res(pg, {'ls-prof':'HEB 300','ls-d':'M24','ls-kl':'10.9','ls-w':'160','ls-M':'250','ls-V':'120','ls-ta':'20','ls-ts':'10','ls-pv':'62.5','ls-es':'40','ls-e':'90'}); e=hand('HEB 300','M24','10.9',M=250,V=120,w=160,ta=20,ts=10,pv=62.5,es=40,e=90)
        ok,info=cmp(r,e,K); check('HEB 300, M24 10.9, Steg 3 × 2 mit p_v = 62,5 mm', ok, info)
        bad=await pg.evaluate("$('ls-w').value='20'; run(); document.getElementById('summary').innerText")
        check('Eingabefehler: w passt nicht zu Steg', 'Querabstand' in bad, bad[:80])
        # Abhilfe
        await fresh(pg); await res(pg, {'ls-M':'150'})
        await pg.wait_for_function("document.querySelector('.fixbox')", timeout=15000)
        bad=await pg.evaluate("LAST.res.C.filter(c=>!c.ok).map(c=>c.id)")
        cid=bad[0] if bad else ''; fx=dict(await pg.evaluate(f"(LAST.res.C.find(c=>c.id==='{cid}').fix||[]).map(f=>[f.id,f.v])")) if cid else {}
        check(f'Abhilfe bei M = 150 kNm ({cid}): Stellschrauben', len(fx)>0, fx)
        if fx:
            k=list(fx)[0]; await pg.evaluate(f"document.querySelector('#n-{cid} .fixbox button[data-fix=\"{k}\"]').click()"); await pg.wait_for_timeout(150)
            check(f'Abhilfe: „Übernehmen“ ({k}) erfüllt {cid}', await pg.evaluate(f"LAST.res.C.find(c=>c.id==='{cid}').ok"))
        # Bericht, Position
        await fresh(pg); await res(pg); rep=await pg.evaluate("buildReport()")
        check('Bericht mit Eingaben, Skizze und Nachweisen', '<h1>' in rep and 'Gurtlaschen' in rep and 'Steglaschen' in rep and '<svg' in rep and 'Stegstoß' in rep)
        await pg.evaluate(GO+"; $('ls-prof').value='HEB 300'; $('ls-w').value='160'; $('ls-ga').value='ai'; run(); savePos()")
        await pg.evaluate("setMat('beton'); setTyp('balken'); run()"); await pg.evaluate("loadPos(0)"); await pg.wait_for_timeout(100)
        check('Position speichern und laden (Profil, Anordnung)', await pg.evaluate("MAT==='stahl' && STMODE==='lasche' && $('ls-prof').value==='HEB 300' && $('ls-ga').value==='ai'"))
        # Sprachen
        for L,w in (('en','Flange splice'),('fr','Joint de semelle'),('es','Empalme de ala')):
            await pg.evaluate(f"localStorage.clear(); localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(250)
            await pg.evaluate(GO+"; run(); document.querySelectorAll('#details details').forEach(d=>d.open=true)"); await pg.wait_for_timeout(80)
            t=await pg.evaluate("document.getElementById('details').textContent+document.getElementById('fig').textContent")
            check(f'{L.upper()}: Rechenweg übersetzt', w in t and 'Schrauben' not in t and 'Gurt' not in t, t[:100])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
