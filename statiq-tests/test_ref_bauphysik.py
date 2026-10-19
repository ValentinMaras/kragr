# statiq·ref v0.3.18 Bauphysik: U-Wert und Temperaturen, Magnus/Taupunkt gegen DIN-4108-3-Tabellenwerte,
# Glaser (Tangentenkonstruktion unabhängig per scipy-ConvexHull auf fein unterteiltem Bauteil), Schall, Gebäudeklassen.
import os, sys, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
    from scipy.spatial import ConvexHull
except ImportError:
    print('SKIP Playwright/scipy nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
de=lambda v,d=2: f'{v+(1e-9 if v>=0 else -1e-9):.{d}f}'.replace('.',',')
def has(t,v,d): t=t.replace('\n',' ').replace('−','-'); return de(v,d) in t or de(v,d) in t.replace('.','')
ps=lambda t: 610.5*math.exp(17.269*t/(237.3+t)) if t>=0 else 610.5*math.exp(21.875*t/(265.5+t))

def glaser_py(L, Rsi=0.25, Rse=0.04, ti=20, te=-5, phii=0.5, phie=0.8):
    # fein unterteilen: 200 Punkte je Schicht, Temperatur linear in x, s_d linear in x
    R=[d/l for (d,l,mu) in L]; RT=Rsi+sum(R)+Rse; q=(ti-te)/RT
    xs=[0.0]; ts=[ti-q*Rsi]
    for (d,l,mu),r in zip(L,R):
        for j in range(1,201): xs.append(xs[-1]+mu*d/200); ts.append(ts[-1]-q*r/200)
    pi=phii*ps(ti); pe=phie*ps(te); S=xs[-1]
    P=np.array([[0,pi]]+[[x,ps(t)] for x,t in zip(xs,ts)]+[[S,pe]])
    h=ConvexHull(P); V=sorted(set(h.vertices))
    # untere Hülle: Punkte unterhalb der Verbindungsgeraden der Endpunkte
    low=[i for i in V if P[i,1] <= pi+(pe-pi)*P[i,0]/S+1e-9]
    low=sorted(low,key=lambda i:P[i,0]); inner=[i for i in low if 0<P[i,0]<S and not (i==0 or i==len(P)-1)]
    if not inner: return 0.0, None
    a=P[inner[0]]; b=P[inner[-1]]
    Z=1/(2e-10*3600); gi=(pi-a[1])/(Z*a[0]); ge=(b[1]-pe)/(Z*(S-b[0]))   # δ₀ = 2·10⁻¹⁰ kg/(m·s·Pa)
    return max((gi-ge)*2160,0), (a[0],b[0])

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def go(t): await pg.goto(URL+'#/bauphysik/'+t); await pg.wait_for_timeout(200)
        async def setv(prefix, vals, fn):
            await pg.evaluate("([p,v,fn])=>{ for(const [k,x] of Object.entries(v)) document.getElementById(p+k).value=String(x); window[fn](); }", [prefix, vals, fn]); await pg.wait_for_timeout(40)
        async def out(id): return await pg.evaluate(f"document.getElementById('{id}').innerText")
        await go('waerme/uwert'); MAT=await pg.evaluate('BP_MAT'); idx={m[0]:i for i,m in enumerate(MAT)}
        def lay(spec): # [(Name, d_cm)] → Felder
            v={};
            for i in range(6):
                n,d=spec[i] if i<len(spec) else (None,0); v[f'm{i+1}']='-' if n is None else str(idx[n]); v[f'd{i+1}']=d
            return v

        # ── U-Wert ──
        okk=True; bad=[]
        for art,Rsi,Rse,spec in [('wand',0.13,0.04,[('Gipsputz',1.5),('Kalksandstein RDK 1,8',17.5),('Mineralwolle WLS 035',16),('Kalkzementputz',1)]),
                                 ('dach',0.10,0.04,[('Gipskartonplatte',1.25),('Dampfbremse 0,2 mm (s_d = 2 m)',0.02),('Mineralwolle WLS 032',24),('Holzfaserdämmung WLS 040',6)]),
                                 ('erd',0.13,0.0,[('Stahlbeton',25),('XPS WLS 035',12)]),('wand',0.13,0.04,[('Planziegel wärmedämmend (λ 0,09)',36.5),('Kalkzementputz',2)])]:
            v=lay(spec); v.update({'art':art,'ti':20,'te':-5}); await setv('uw-', v, 'updateUW'); o=await out('uw-out')
            L=[(d/100,MAT[idx[n]][1]) for n,d in spec]; Rb=sum(d/l for d,l in L); U=1/(Rsi+Rb+Rse); q=U*25; tsi=20-q*Rsi
            if not (has(o,U,3) and has(o,Rb,3) and has(o,tsi,2) and has(o,1-0.25*U,3)): okk=False; bad.append((art,round(U,4)))
        check('U-Wert: 4 Bauteile (Wand, Dach, gegen Erdreich, Monolith) mit R_si/R_se, θ_si, f_Rsi', okk, bad)
        T=await pg.evaluate("bpTemperaturen([{d:0.2,lam:2},{d:0.1,lam:0.04}],0.13,0.04,20,-5).T")
        RT=0.13+0.1+2.5+0.04; q=25/RT; check('Temperaturen an den Schichtgrenzen (Stahlbeton + Dämmung)', np.allclose(T,[20-q*0.13,20-q*0.23,20-q*2.73]), T)

        # ── Magnus / Taupunkt ──
        tab={20:2337,10:1227,0:611,-5:401,-10:260,12:1402}
        js=await pg.evaluate("[20,10,0,-5,-10,12].map(psat)")
        check('Sättigungsdampfdruck = DIN-4108-3-Tabelle (±1 Pa)', all(abs(a-tab[t])<=1 for a,t in zip(js,[20,10,0,-5,-10,12])), [round(x) for x in js])
        tp=await pg.evaluate("[taupunkt(0.5*psat(20)), taupunkt(0.8*psat(-5)), taupunkt(psat(7.3))]")
        check(f'Taupunkt 20 °C/50 % = 9,3 °C, Umkehrung p_s ↔ θ_s exakt', abs(tp[0]-9.26)<0.02 and abs(tp[2]-7.3)<1e-9 and tp[1]<-7, [round(x,3) for x in tp])
        await go('feuchte/luft'); await setv('tp-', {'t':20,'phi':60,'U':1.4,'te':-5}, 'updateTP'); o=await out('tp-out')
        pp=0.6*ps(20); x=math.log(pp/610.5); ts=237.3*x/(17.269-x); tsi=20-1.4*0.25*25
        check(f'Rechner: 20 °C/60 % → θ_s = {ts:.2f} °C, θ_si = {tsi:.2f} °C, f_Rsi = {(tsi+5)/25:.3f}', has(o,ts,2) and has(o,tsi,2) and has(o,(tsi+5)/25,3))

        # ── Glaser gegen unabhängige Hüllkonstruktion ──
        await go('feuchte/glaser'); okk=True; bad=[]; ntau=0
        cases=[[('Gipskartonplatte',1.25),('Mineralwolle WLS 035',6),('Kalksandstein RDK 1,8',17.5),('Kalkzementputz',2)],
               [('Gipskartonplatte',1.25),('Dampfbremse 0,2 mm (s_d = 2 m)',0.02),('Mineralwolle WLS 035',20),('Holzfaserdämmung WLS 040',6)],
               [('Gipskartonplatte',1.25),('Mineralwolle WLS 035',20),('OSB-Platte',2.2)],
               [('Gipsputz',1.5),('Kalksandstein RDK 1,8',17.5),('Mineralwolle WLS 035',14),('Kalkzementputz',1)],
               [('Stahlbeton',20),('EPS WLS 035',16),('Bitumen-Dachbahn 4 mm (s_d ≈ 200 m)',0.4)]]
        for spec in cases:
            v=lay(spec); await setv('gl-', v, 'updateGL'); o=await out('gl-out')
            L=[(d/100,MAT[idx[n]][1],MAT[idx[n]][2]) for n,d in spec]
            mT,zone=glaser_py(L)
            G=await pg.evaluate("glaser(bpLesen('gl-'))")
            ok_=abs(G['mT']-mT)<1e-6*max(1,mT) and (G['tau']==(mT>1e-9))
            if mT>1e-9: ntau+=1; ok_&=has(o,mT,3) and abs(G['xa']-zone[0])<1e-9
            else: ok_&='kein Tauwasser' in o
            if not ok_: okk=False; bad.append((spec[1][0],round(G['mT'],4),round(mT,4),zone))
        check(f'Glaser: 5 Aufbauten ({ntau} mit Tauwasser) = Hülle aus 200 Punkten je Schicht (scipy)', okk and ntau>=2, bad[:2])
        # Verdunstung unabhängig für Fall 1
        v=lay(cases[0]); await setv('gl-', v, 'updateGL'); G=await pg.evaluate("glaser(bpLesen('gl-'))")
        L=[(d/100,MAT[idx[n]][1],MAT[idx[n]][2]) for n,d in cases[0]]; R=[d/l for d,l,mu in L]; RT=0.25+sum(R)+0.04; q=8/RT
        tk=20-q*(0.25+sum(R[:G['ka']])); sdi=sum(mu*d for d,l,mu in L[:G['ka']]); sde=sum(mu*d for d,l,mu in L[G['ka']:])
        Z=1/(2e-10*3600); mV=((1700-1200)/(Z*sdi)+(1700-1200)/(Z*sde))*2160   # DIN 4108-3:2018: 1200 Pa innen/außen, 1700 Pa in der Tauwasserebene
        check(f'Verdunstungsperiode (1200 / 1700 Pa): m_W,V = {mV:.3f} kg/m²', abs(G['mV']-mV)<1e-9, G['mV'])

        # ── Schall ──
        await go('schall/luftschall')
        for spec,anf in [([('Gipsputz',1),('Kalksandstein RDK 2,0',24),('Gipsputz',1)],0),([('Stahlbeton',18)],2),([('Kalkzementputz',1.5),('Vollziegel RDK 1,8',24)],1)]:
            v={k:x for k,x in lay(spec).items() if int(k[1:])<=4}; v['anf']=anf; await setv('ls-', v, 'updateLS'); o=await out('ls-out')
            m=sum(MAT[idx[n]][3]*d/100 for n,d in spec); Rw=30.9*math.log10(m)-22.2
            check(f'Massegesetz m′ = {m:.1f} kg/m² → R_w = {Rw:.1f} dB', has(o,m,1) and has(o,Rw,1))
        await setv('ls-', {'sp':10,'ma':300,'mb':20}, 'updateLS'); o=await out('ls2-out'); f0=160*math.sqrt(10*(1/300+1/20))
        check(f'Vorsatzschale f₀ = {f0:.1f} Hz', has(o,f0,1))
        await go('schall/trittschall'); await setv('ts-', {'mD':440,'dE':5,'rE':2000,'s':20,'K':2,'zul':50,'mf':0}, 'updateTS'); o=await out('ts-out')
        Ln=164-35*math.log10(440); dL=13*math.log10(100)-14.2*math.log10(20)+20.8
        check(f'Trittschall: L_n,eq = {Ln:.1f}, ΔL_w = {dL:.1f}, L′_n,w = {Ln-dL+2:.1f} dB', has(o,Ln,1) and has(o,dL,1) and has(o,Ln-dL+2,1))

        # ── Flankenübertragung (DIN 4109-2) ──
        def flank_py(mD,S,d,F,dR=0):
            Rw=lambda m: 30.9*math.log10(m)-22.2; RDd=Rw(mD)+dR; paths=[RDd]
            for m,lf,art in F:
                M=math.log10(mD/m)   # DIN 4109-2:2018 / EN ISO 12354-1:2017
                if art=='kreuz': K13=9.6+11*M if M>0.182 else 8.7+17.1*M+5.7*M*M; K12=5.7+15.4*M*M
                else: K13=8+6.8*M if M>0.215 else 5.7+14.1*M+5.7*M*M; K12=4.7+5.7*M*M
                Sf=lf*d
                K13=max(K13,10*math.log10(lf*(2/Sf))); K12=max(K12,10*math.log10(lf*(1/S+1/Sf)))
                t=10*math.log10(S/lf); Rf=Rw(m)
                paths+= [Rf+K13+t, (RDd+Rf)/2+K12+t, (Rf+RDd)/2+K12+t]
            return -10*math.log10(sum(10**(-r/10) for r in paths)), RDd
        await go('schall/flanken'); okk=True; bad=[]
        cases=[(504,10.4,4.5,[(432,4,'kreuz'),(432,4,'kreuz'),(331,2.6,'T'),(254,2.6,'T')],0),
               (432,12,5,[(432,5,'kreuz'),(432,5,'kreuz'),(150,2.4,'T'),(150,2.4,'T')],0),
               (300,8,3,[(500,3.2,'T'),(500,3.2,'T'),(500,2.5,'kreuz'),(120,2.5,'T')],5)]
        for mD,S_,d_,F,dR in cases:
            v={'mD':mD,'S':S_,'d':d_,'dR':dR,'anf':0}
            for i,(m,lf,art) in enumerate(F,1): v.update({f'm{i}':m,f'l{i}':lf,f'a{i}':art})
            await setv('fl-', v, 'updateFL'); o=await out('fl-out'); R,RDd=flank_py(mD,S_,d_,F,dR)
            if not (has(o,R,1) and has(o,RDd,1)): okk=False; bad.append((mD,round(R,2)))
        check('Flankenübertragung: 3 Trennwände (Kreuz-/T-Stoß, leichte Flanken, ΔR) = Python', okk, bad)
        r=[await pg.evaluate(f"flankenR({{mD:400,S:10,d:4,F:[{{m:400,lf:4,art:'kreuz'}},{{m:400,lf:4,art:'kreuz'}},{{m:{mf},lf:2.5,art:'T'}},{{m:400,lf:2.5,art:'T'}}]}}).Rs") for mf in [100,200,400,800]]
        check('R′w steigt mit schwererer Flanke und bleibt unter R_Dd', all(r[i]<r[i+1] for i in range(3)) and r[-1]<30.9*math.log10(400)-22.2, [round(x,2) for x in r])
        await go('schall/trittschall'); await setv('ts-', {'mD':440,'dE':5,'rE':2000,'s':20,'K':2,'zul':50,'mf':250}, 'updateTS'); o=await out('ts-out')
        K=max(0,0.6+5.5*math.log10(440/250)); L=164-35*math.log10(440)-(13*2-14.2*math.log10(20)+20.8)+K
        check(f'Trittschall mit K = 0,6 + 5,5·lg(440/250) = {K:.2f} dB → L′_n,w = {L:.1f} dB', has(o,K,1) and has(o,L,1))
        # ── Gebäudeklassen ──
        await go('brand/gebaeudeklassen'); okk=True
        for h,n,a,fr,gk in [(4,1,180,1,1),(4,2,150,0,2),(6.5,4,85,1,3),(10,6,90,0,4),(12,2,450,0,5),(15,8,80,0,5),(7,2,250,1,3)]:
            await setv('gk-', {'h':h,'n':n,'a':a,'f':fr}, 'updateGK'); o=await out('gk-out'); okk&=f'Gebäudeklasse {gk}' in o
        check('Gebäudeklassen: 7 Fälle GK 1 … 5 (inkl. Fläche > 400 m², h > 13 m)', okk)

        # ── Seiten ──
        PAGES=['waerme/grundlagen','waerme/uwert','waerme/anforderungen','feuchte/luft','feuchte/glaser','schall/grundlagen','schall/luftschall','schall/flanken','schall/trittschall','brand/klassen','brand/gebaeudeklassen']
        bad=[]
        for vp in [(1440,900),(390,844)]:
            await pg.set_viewport_size({'width':vp[0],'height':vp[1]})
            for t in PAGES:
                await go(t)
                if await pg.evaluate("/NaN|undefined|Infinity/.test(document.getElementById('main').innerHTML)"): bad.append((vp[0],t,'NaN'))
                if await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth+1"): bad.append((vp[0],t,'Überlauf'))
        check(f'{len(PAGES)} Bauphysik-Seiten Desktop + 390 px: keine NaN, kein Seitenüberlauf', not bad, bad)
        check('Keine JavaScript-Fehler', not errs, errs[:3])
        await br.close()

asyncio.run(main())
print('FEHLER:', fails); sys.exit(1 if fails else 0)
