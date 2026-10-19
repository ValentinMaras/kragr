# statiq·ref v0.3.17 Lastannahmen: Schneeverwehung am Höhensprung (alle Begrenzungen), Windbereiche (Geometrie,
# c_pe-Interpolation), Lastweiterleitung (Mittelauflager über Verträglichkeit der Durchbiegung, Kombinationen).
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
def has(t,v,d): t=t.replace('\n',' ').replace('−','-'); return de(v,d) in t or de(v,d) in t.replace('.','')
def sk(z,A):
    P={'1':(0.19,0.91,0.65),'2':(0.25,1.91,0.85),'3':(0.31,2.91,1.10)}; a,b,m=P[z[0]]; f=1.25 if z.endswith('a') else 1
    return f*max(a+b*((A+140)/760)**2, m)
mu1=lambda a: 0.8 if a<=30 else 0.8*(60-a)/30 if a<60 else 0

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def go(t): await pg.goto(URL+'#/lastannahmen/lasten/'+t); await pg.wait_for_timeout(200)
        async def setv(prefix, vals, fn):
            await pg.evaluate("([p,v,fn])=>{ for(const [k,x] of Object.entries(v)) document.getElementById(p+k).value=String(x); window[fn](); }", [prefix, vals, fn]); await pg.wait_for_timeout(40)
        async def out(id): return await pg.evaluate(f"document.getElementById('{id}').innerText")

        # ── Höhensprung ──
        await go('schnee'); okk=True; bad=[]; seen=set()
        for z,A,h,b1,b2,a in [('2',300,3,12,8,0),('2',300,1.0,30,20,0),('3',800,6,20,20,30),('1',100,0.8,4,3,0),('2a',500,10,40,4,20),('2',300,2,10,30,45),('3',800,1.0,6,6,0),('2',300,3,4,3,0)]:
            s_=sk(z,A); raw=(b1+b2)/(2*h); g=2*h/s_; muw=max(0.8,min(raw,g,4.0)); mus=0.5*mu1(a) if a>15 else 0; mu2=max(0.8,min(mus+muw,2.4)); ls=min(max(2*h,5),15)   # NA: 0,8 ≤ μ2 ≤ 2,4
            seen.add('max 2,4' if mus+muw>2.4 else 'γh/s' if g<min(raw,4.0) and g>0.8 else 'min 0,8' if min(raw,g,4.0)<0.8 else 'roh')
            await setv('hs-', {'zone':z,'A':A,'h':h,'b1':b1,'b2':b2,'a':a}, 'updateHS'); o=await out('hs-out')
            okk_=has(o,s_,3) and has(o,muw,3) and has(o,mu2,3) and has(o,mu2*s_,3) and has(o,ls,2)
            if b2<ls: okk_&=has(o,0.8+(mu2-0.8)*(1-b2/ls),3)
            if not okk_: okk=False; bad.append((z,h,b1,b2,a,round(muw,3),round(mu2,3)))
        check(f'Höhensprung: 8 Fälle, Begrenzungen {sorted(seen)}, l_s 5…15 m, abgeschnittener Keil', okk and len(seen)>=4, bad[:2])

        # ── Wind ──
        await go('wind'); okk=True
        cw={5:[(-1.2,-1.4),(-0.8,-1.1),(-0.5,-0.5),(0.8,1.0),(-0.7,-0.7)],1:[(-1.2,-1.4),(-0.8,-1.1),(-0.5,-0.5),(0.8,1.0),(-0.5,-0.5)],0.25:[(-1.2,-1.4),(-0.8,-1.1),(-0.5,-0.5),(0.7,1.0),(-0.3,-0.3)]}
        def cpe(c10,c1,A): return c1 if A<=1 else c10 if A>=10 else c1-(c1-c10)*math.log10(A)
        def cwand(hd,i,A):
            hd=min(max(hd,0.25),5); lo,hi=(0.25,1) if hd<=1 else (1,5); t=(hd-lo)/(hi-lo)
            return cpe(cw[lo][i][0]+(cw[hi][i][0]-cw[lo][i][0])*t, cw[lo][i][1]+(cw[hi][i][1]-cw[lo][i][1])*t, A)
        for hd,A in [(0.1,10),(0.667,5),(1,1),(3,2.5),(6,10)]:
            for i in range(5): okk&=abs(await pg.evaluate(f"cpeWand({hd},{i},{A})")-cwand(hd,i,A))<1e-12
        check('c_pe Wände A–E: Interpolation in h/d und lg A (25 Werte)', okk)
        okk=True
        for b,d,h in [(20,12,8),(30,10,4),(10,40,12),(15,15,20),(50,6,3)]:
            Z=await pg.evaluate(f"windZonen({b},{d},{h})"); e=min(b,2*h)
            # Flächen: F, G, H, I müssen zusammen die Dachfläche ergeben; Wandbereiche die Seitenwand
            t1=min(e/10,d); t2=min(e/2,d); roof=2*(e/4)*t1+(b-e/2)*t1+b*(t2-t1)+b*(d-t2)
            okk&=abs(Z['e']-e)<1e-12 and abs(sum(Z['W'].values())-d)<1e-9 and abs(roof-b*d)<1e-9 and abs(Z['W']['A']-min(e/5,d))<1e-12
        check('Windbereiche: e = min(b; 2h), A + B + C = d, F + G + H + I = Dachfläche (5 Gebäude)', okk)
        await setv('wb-', {'zone':'2','b':20,'d':12,'h':8,'A':5}, 'updateWB'); o=await out('wb-out')
        q=0.65; F=cpe(-1.8,-2.5,5); D=cwand(8/12,3,5)
        check(f'Winddruck Zone 2, h = 8 m, A = 5 m²: w_F = {F*q:.3f}, w_D = {D*q:.3f} kN/m²', has(o,F*q,3) and has(o,D*q,3), o[-150:])

        # ── Lastweiterleitung ──
        await go('lastabtrag'); okk=True; bad=[]
        for n,l1,l2,g,q_,gD,s_,gW,dl in [(3,4.5,5.0,7.2,2.3,6.5,0.68,9,1),(1,6,6,6,2,5,1.2,0,1),(4,3.5,5.5,6.8,3.0,7.0,0.85,8,0),(2,5,3,7,2.8,6,0.6,10,1)]:
            L=l1+l2; a=l1; b=L-a
            wq=a*(L**3-2*L*a*a+a**3)/24; wP=a*a*b*b/(3*L); B=wq/wP     # Mittelauflager aus Verträglichkeit (EI kürzt sich)
            be=B if dl else L/2
            Ng=n*g*be+gD*be+n*gW; Nq=n*q_*be; Ns=s_*be; Nd=max(1.35*Ng+1.5*Nq+0.75*Ns, 1.35*Ng+1.5*Ns+1.05*Nq)
            await setv('lw-', {'n':n,'l1':l1,'l2':l2,'g':g,'q':q_,'gD':gD,'s':s_,'gW':gW,'dlt':dl}, 'updateLW'); o=await out('lw-out')
            if not (has(o,be,3) and has(o,Ng,2) and has(o,Nq,2) and has(o,Nd,2)): okk=False; bad.append((n,l1,l2,dl,round(B,4),round(Nd,2)))
        check('Lastweiterleitung: Mittelauflager = Verträglichkeit der Durchbiegung, N_G, N_Q, n_Ed (4 Fälle)', okk, bad[:2])

        # ── Seiten ──
        bad=[]
        for vp in [(1440,900),(390,844)]:
            await pg.set_viewport_size({'width':vp[0],'height':vp[1]})
            for t in ['schnee','wind','lastabtrag']:
                await go(t)
                if await pg.evaluate("/NaN|undefined|Infinity/.test(document.getElementById('main').innerHTML)"): bad.append((vp[0],t,'NaN'))
                if await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth+1"): bad.append((vp[0],t,'Überlauf'))
        check('Schnee, Wind, Lastweiterleitung Desktop + 390 px: keine NaN, kein Überlauf', not bad, bad)
        check('Keine JavaScript-Fehler', not errs, errs[:3])
        await br.close()

asyncio.run(main())
print('FEHLER:', fails); sys.exit(1 if fails else 0)
