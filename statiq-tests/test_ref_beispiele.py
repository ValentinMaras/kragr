# statiq·ref v0.3.10: Beispielrechnungen — Lastkombination, Träger mit Kragarm, zusammengesetzter Querschnitt,
# quadratische Gleichung, Cramer 2×2, Gauß 3×3. Unabhängig nachgerechnet (Python, numpy, shapely).
import os, sys, math, asyncio
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
de=lambda v,d=1: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
def has(txt,v,d): t=txt.replace('\n',' '); return de(v,d) in t or de(v,d) in t.replace('.','')

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        # ── Lastkombination ──
        await pg.goto(URL+'#/lastannahmen/grundlagen/kombinationen'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.getElementById('main').innerText")
        G,N,S,W=180,90,60,20; p0={'N':.7,'S':.5,'W':.6}; p1={'N':.5,'S':.2,'W':.2}; p2={'N':.3,'S':0,'W':0}; Q={'N':N,'S':S,'W':W}
        gz={L:1.35*G+1.5*Q[L]+sum(1.5*p0[k]*Q[k] for k in Q if k!=L) for L in Q}
        ch={L:G+Q[L]+sum(p0[k]*Q[k] for k in Q if k!=L) for L in Q}
        hf={L:G+p1[L]*Q[L]+sum(p2[k]*Q[k] for k in Q if k!=L) for L in Q}
        qs=G+sum(p2[k]*Q[k] for k in Q)
        check(f'GZT: N {gz["N"]:.1f}, S {gz["S"]:.1f}, W {gz["W"]:.1f} → max {max(gz.values()):.1f} kN (Schnee führend)',
              all(has(t,v,1) for v in gz.values()) and f'NEd = {de(max(gz.values()))} kN' in t.replace('\n',' ') and max(gz,key=gz.get)=='S')
        check(f'GZG: charakteristisch max {max(ch.values()):.1f}, häufig max {max(hf.values()):.1f}, quasi-ständig {qs:.1f}',
              all(has(t,v,1) for v in list(ch.values())+list(hf.values())+[qs]))
        # Kragarm: unabhängig als Balken mit Überstand (Gleichgewicht + Schnittgrößen numerisch)
        l,a,g,q=6,2,10,8
        def beam(w1,w2):
            B=(w1*l*l/2 + w2*a*(l+a/2))/l; A=w1*l+w2*a-B
            xs=np.linspace(0,l,60001); M=A*xs-w1*xs**2/2; return A,B,M.max()
        A1,_,M1=beam(1.35*g+1.5*q,1.35*g); MB=-(1.35*g+1.5*q)*a*a/2
        Aeq,_,_=beam(0.9*g,1.1*g+1.5*q)   # Feld stabilisierend, Kragarm destabilisierend
        check(f'Kragarm: A = {A1:.2f}, max M = {M1:.2f}, M_B = {MB:.2f}, A_d,min (EQU) = {Aeq:.2f}',
              has(t,A1,2) and has(t,M1,2) and has(t,MB,2) and has(t,Aeq,2), '')
        # ── zusammengesetzter Querschnitt ──
        await pg.goto(URL+'#/stahlbau/nachweise/querschnitt'); await pg.wait_for_timeout(300)
        async def zq(o, st):
            for k,v in o.items(): await pg.fill('#zq-'+k, str(v))
            await pg.select_option('#zq-st', st); await pg.wait_for_timeout(150)
            return await pg.evaluate("document.getElementById('zq-out').innerText")
        def indep(o, fy):
            bo,to,hw,tw,bu,tu,aw=o['bo'],o['to'],o['hw'],o['tw'],o['bu'],o['tu'],o['a']; h=to+hw+tu
            # Geometrie mit y nach oben (Oberkante bei y = h)
            g=unary_union([box(-bo/2,h-to,bo/2,h), box(-tw/2,tu,tw/2,h-to), box(-bu/2,0,bu/2,tu)])
            A=g.area; yc=g.centroid.y
            Iy=sum(b_*t_**3/12+b_*t_*(yy-yc)**2 for b_,t_,yy in [(bo,to,h-to/2),(tw,hw,tu+hw/2),(bu,tu,tu/2)])
            lo,hi=0,h
            for _ in range(80):
                m=(lo+hi)/2
                if g.intersection(box(-1e4,m,1e4,h+1)).area>A/2: lo=m
                else: hi=m
            yp=(lo+hi)/2; up=g.intersection(box(-1e4,yp,1e4,h+1)); dn=g.intersection(box(-1e4,-1,1e4,yp))
            Wpl=up.area*(up.centroid.y-yp)+dn.area*(yp-dn.centroid.y)
            eps=math.sqrt(235/fy); w=math.sqrt(2)*aw
            cf=(bo-tw)/2-w; rf=cf/to; kf=1 if rf<=9*eps else 2 if rf<=10*eps else 3 if rf<=14*eps else 4
            c=hw-2*w; rw=c/tw; ytop=h-to-w; ybot=tu+w
            al=min(1,max(0,(ytop-yp)/c))
            g1=396*eps/(13*al-1) if al>0.5 else 36*eps/al; g2=456*eps/(13*al-1) if al>0.5 else 41.5*eps/al
            psi=(ybot-yc)/(ytop-yc); g3=42*eps/(0.67+0.33*psi) if psi>-1 else 62*eps*(1-psi)*math.sqrt(-psi)
            kw=1 if rw<=g1 else 2 if rw<=g2 else 3 if rw<=g3 else 4
            return dict(A=A, zs=h-yc, Iy=Iy, Wpl=Wpl, zpl=h-yp, al=al, psi=psi, kf=kf, kw=kw, kl=max(kf,kw), Wel=min(Iy/(h-yc),Iy/yc))
        cases=[({'bo':250,'to':15,'hw':600,'tw':10,'bu':300,'tu':20,'a':5},'S355',355),
               ({'bo':300,'to':20,'hw':600,'tw':8,'bu':200,'tu':15,'a':4},'S235',235),
               ({'bo':400,'to':12,'hw':900,'tw':6,'bu':400,'tu':12,'a':4},'S355',355),
               ({'bo':200,'to':25,'hw':300,'tw':12,'bu':200,'tu':25,'a':6},'S235',235)]
        for o,st,fy in cases:
            out=await zq(o,st); r=indep(o,fy)
            W = r['Wpl'] if r['kl']<=2 else r['Wel']; MRd=W*fy/1e6
            ok = has(out,r['zs'],1) and has(out,r['zpl'],1) and has(out,r['Wpl']/1e3,1) and has(out,r['al'],3) and has(out,r['psi'],3) and f'Klasse {r["kl"]}' in out and has(out,MRd,1)
            check(f'geschweißt {o["bo"]}×{o["to"]}/{o["hw"]}×{o["tw"]}/{o["bu"]}×{o["tu"]} {st}: α={r["al"]:.3f}, ψ={r["psi"]:.3f}, Klasse {r["kl"]}, M_Rd={MRd:.1f}', ok, out[-160:].replace('\n',' '))
        check('Skizze des Querschnitts wird gezeichnet', await pg.evaluate("!!document.querySelector('#zq-fig svg polygon')"))
        # ── Gleichungen ──
        await pg.goto(URL+'#/mathematik/algebra/gleichungen'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.getElementById('main').innerText")
        x=np.roots([30/2, 15*12.6, -15*12.6*46]); xp=max(x); xn=min(x)
        check(f'Zustand II: x = {xp:.2f} cm (zweite Lösung {xn:.2f})', has(t,xp,2) and has(t,xn,2))
        Am=np.array([[-math.cos(math.pi/6), math.cos(math.pi/3)],[0.5, math.sin(math.pi/3)]]); s12=np.linalg.solve(Am,[0,10])
        check(f'Cramer: S1 = {s12[0]:.3f}, S2 = {s12[1]:.3f} kN, D = {np.linalg.det(Am):.4f}', has(t,s12[0],3) and has(t,s12[1],3) and has(t,np.linalg.det(Am),4))
        async def gauss(A,b):
            for i in range(3):
                for j in range(3): await pg.fill(f'#gs-a{i}{j}', str(A[i][j]))
                await pg.fill(f'#gs-b{i}', str(b[i]))
            await pg.wait_for_timeout(150); return await pg.evaluate("document.getElementById('gs-out').innerText")
        for A,b,lab in [([[2,1,-1],[-3,-1,2],[-2,1,2]],[8,-11,-3],'Lehrbuch'),([[0,2,1],[1,1,1],[2,1,3]],[5,6,13],'Pivot 0 → Zeilentausch'),([[4,-2,1],[3,6,-4],[2,1,8]],[12,-25,32],'zufällig')]:
            out=await gauss(A,b); sol=np.linalg.solve(np.array(A,float),np.array(b,float))
            dt=np.linalg.det(np.array(A,float))
            check(f'Gauß {lab}: x = {np.round(sol,4).tolist()}, det = {dt:.3f}', all(has(out,v,4) for v in sol) and has(out,dt,3) and ('tauschen' in out)==(lab.startswith('Pivot')), out[-120:].replace('\n',' '))
        out=await gauss([[1,2,3],[2,4,6],[1,0,1]],[1,2,3])
        check('singuläre Matrix wird erkannt', 'keine eindeutige' in out.lower(), out[-80:])
        # mobil
        await pg.set_viewport_size({'width':390,'height':844}); bad=[]
        for tp in ['lastannahmen/grundlagen/kombinationen','stahlbau/nachweise/querschnitt','mathematik/algebra/gleichungen']:
            await pg.goto(URL+'#/'+tp); await pg.wait_for_timeout(200)
            w=await pg.evaluate("document.documentElement.scrollWidth")
            if w>390: bad.append((tp,w))
        check('Handy: drei Seiten ohne Querscrollen', not bad, bad)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
