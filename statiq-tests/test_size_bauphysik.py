# statiq·size v0.5.15 Bauphysik: U-Wert, Glaser, Schallschutz — gegen Python (Glaser unabhängig per scipy-Hülle)
# und gleiche Rechenkerne wie statiq·ref (Tabellen und Funktionen werden verglichen). Ohne Playwright: SKIP.
import os, sys, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
HTML='file://'+BASE+'/size.html'; REF='file://'+BASE+'/ref.html'
try:
    from playwright.async_api import async_playwright
    from scipy.spatial import ConvexHull
except ImportError:
    print('SKIP Playwright/scipy nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
ps=lambda t: 610.5*math.exp(17.269*t/(237.3+t)) if t>=0 else 610.5*math.exp(21.875*t/(265.5+t))
def glaser_py(L):
    Rsi,Rse,ti,te=0.25,0.04,20,-5; R=[d/l for (d,l,mu) in L]; q=(ti-te)/(Rsi+sum(R)+Rse)
    xs=[0.0]; ts=[ti-q*Rsi]
    for (d,l,mu),r in zip(L,R):
        for j in range(1,201): xs.append(xs[-1]+mu*d/200); ts.append(ts[-1]-q*r/200)
    pi=0.5*ps(ti); pe=0.8*ps(te); S=xs[-1]
    P=np.array([[0,pi]]+[[x,ps(t)] for x,t in zip(xs,ts)]+[[S,pe]]); V=sorted(set(ConvexHull(P).vertices))
    low=sorted([i for i in V if P[i,1]<=pi+(pe-pi)*P[i,0]/S+1e-9 and 0<P[i,0]<S],key=lambda i:P[i,0])
    if not low: return 0.0
    a=P[low[0]]; b=P[low[-1]]; Z=1/(2e-10*3600); return max(((pi-a[1])/(Z*a[0])-(b[1]-pe)/(Z*(S-b[0])))*2160,0)

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('bauph'); setBpMode('uwert')")
        s=await pg.inner_text('#summary'); check('Standard U-Wert (KS + WDVS) erfüllt', 'Alle Nachweise erfüllt' in s, s)
        MAT=await pg.evaluate('BP_MAT'); idx={m[0]:i for i,m in enumerate(MAT)}
        # gleiche Rechenkerne wie ref
        rf=await br.new_page(); await rf.goto(REF); await rf.wait_for_timeout(200)
        js="[BP_MAT,BP_RS,BP_ANF,BP_SCHALL,GL,glaser.toString(),bpWaerme.toString(),bpTemperaturen.toString(),psat.toString(),rwMasse.toString(),lnEq.toString(),dLwEstrich.toString(),flankenR.toString(),kStoss.toString(),kTritt.toString()]"
        check('Tabellen und Rechenkerne identisch mit statiq·ref', await pg.evaluate(js)==await rf.evaluate(js))
        async def setl(spec):
            code=[]
            for i in range(1,7):
                if i<=len(spec):
                    n,d=spec[i-1][:2]; M=MAT[idx[n]]; lam=spec[i-1][2] if len(spec[i-1])>2 else M[1]
                    code.append(f"$('bl-m{i}').value='{idx[n]}'; $('bl-d{i}').value={d}; $('bl-l{i}').value={lam}; $('bl-u{i}').value={M[2]}; $('bl-r{i}').value={M[3]};")
                else: code.append(f"$('bl-m{i}').value='-'; $('bl-d{i}').value=0;")
            await pg.evaluate(''.join(code)+' run()')
        # ── U-Wert ──
        for name,art,Rsi,Rse,spec in [('Außenwand KS + WDVS','wand',0.13,0.04,[('Gipsputz',1.5),('Kalksandstein RDK 1,8',17.5),('Mineralwolle WLS 035',16),('Kalkzementputz',1)]),
                                      ('Steildach, λ der Dämmung überschrieben (0,030)','dach',0.10,0.04,[('Gipskartonplatte',1.25),('Mineralwolle WLS 035',22,0.030),('Holzfaserdämmung WLS 040',6)]),
                                      ('Bodenplatte gegen Erdreich','erd',0.13,0.0,[('Zementestrich',6),('EPS WLS 035',8),('Stahlbeton',25),('XPS WLS 035',10)]),
                                      ('ungedämmter Altbau (Mindestwärmeschutz verfehlt)','wand',0.13,0.04,[('Kalkzementputz',1.5),('Vollziegel RDK 1,8',24),('Kalkzementputz',2)])]:
            await pg.evaluate(f"setBpMode('uwert'); $('bp-art').value='{art}';"); await setl(spec)
            Rb=sum((s[2] if len(s)>2 else MAT[idx[s[0]]][1]) and (s[1]/100)/(s[2] if len(s)>2 else MAT[idx[s[0]]][1]) for s in spec); U=1/(Rsi+Rb+Rse)
            g=await pg.evaluate("[LAST.res.W.U, LAST.res.W.Rb, LAST.res.ok, LAST.res.C.find(c=>c.id==='bumin').ok]")
            check(f'U-Wert {name}: U = {U:.3f}', abs(g[0]-U)<1e-12 and abs(g[1]-Rb)<1e-12, g)
        check('Altbau: Mindestwärmeschutz nicht erfüllt', g[3] is False)
        # ── Glaser ──
        await pg.evaluate("setBpMode('glaser')")
        for name,spec in [('Innendämmung ohne Dampfbremse',[('Gipskartonplatte',1.25),('Mineralwolle WLS 035',6),('Kalksandstein RDK 1,8',17.5),('Kalkzementputz',2)]),
                          ('Holzrahmen mit Dampfbremse',[('Gipskartonplatte',1.25),('Dampfbremse 0,2 mm (s_d = 2 m)',0.02),('Mineralwolle WLS 035',20),('Holzfaserdämmung WLS 040',6)]),
                          ('Holzrahmen außen OSB, ohne Dampfbremse',[('Gipskartonplatte',1.25),('Mineralwolle WLS 035',20),('OSB-Platte',2.2)]),
                          ('Flachdach ohne Dampfsperre',[('Stahlbeton',20),('EPS WLS 035',16),('Bitumen-Dachbahn 4 mm (s_d ≈ 200 m)',0.4)])]:
            await setl(spec); L=[(d/100,MAT[idx[n]][1],MAT[idx[n]][2]) for n,d in spec]; mT=glaser_py(L)
            g=await pg.evaluate("[LAST.res.G.mT, LAST.res.G.tau, LAST.res.ok]")
            check(f'Glaser {name}: m_W,T = {mT:.3f} kg/m²', abs(g[0]-mT)<1e-6*max(1,mT) and g[1]==(mT>1e-9), g)
        # ── Schall ──
        await pg.evaluate("setBpMode('schall')"); await setl([('Gipsputz',1),('Kalksandstein RDK 2,0',24),('Gipsputz',1)])
        await pg.evaluate("$('bs-anf').value='0'; $('bs-kf').value=3; $('bs-up').value=2; $('bs-tr').checked=false; run()")
        m=12+480+12; Rw=30.9*math.log10(m)-22.2
        g=await pg.evaluate("[LAST.res.m, LAST.res.Rw, LAST.res.ok]")
        check(f'Wohnungstrennwand KS 24: m′ = {m:.0f}, R_w = {Rw:.1f} dB, R′_w − u = {Rw-5:.1f} ≥ 53', abs(g[0]-m)<1e-9 and abs(g[1]-Rw)<1e-9 and g[2]==(Rw-5>=53), g)
        # genauer Flankennachweis: size = ref
        await pg.evaluate("$('bs-fl').value='genau'; showMat(); $('bf-S').value=10.4; $('bf-d').value=4.5; $('bf-dR').value=0; run()")
        g=await pg.evaluate("[LAST.res.Rs, LAST.res.m, LAST.res.FR.W.length]")
        rr=await rf.evaluate(f"flankenR({{mD:{g[1]},S:10.4,d:4.5,RDdPlus:0,F:[{{m:432,lf:4,art:'kreuz'}},{{m:432,lf:4,art:'kreuz'}},{{m:331,lf:2.6,art:'T'}},{{m:254,lf:2.6,art:'T'}}]}}).Rs")
        check(f'genauer Nachweis: R′w = {rr:.2f} dB wie in ref, 13 Wege, R′w < R_w', abs(g[0]-rr)<1e-9 and g[2]==13 and g[0]<Rw, g)
        check('Felder: pauschaler Abschlag ausgeblendet, Flanken sichtbar', await pg.evaluate("$('bs-kf').closest('.field').offsetParent===null && $('bf-m1').offsetParent!==null"))
        await pg.evaluate("$('bs-fl').value='pauschal'; showMat(); run()")
        await setl([('Stahlbeton',18)]); await pg.evaluate("$('bs-anf').value='2'; $('bs-tr').checked=true; showMat(); $('bs-dE').value=5; $('bs-rE').value=2000; $('bs-s').value=15; $('bs-K').value=2; $('bs-zul').value=50; run()")
        Ln=164-35*math.log10(432); dL=13*math.log10(100)-14.2*math.log10(15)+20.8; L=Ln-dL+2
        g=await pg.evaluate("[LAST.res.T.L, LAST.res.C.find(c=>c.id==='bst').ok]")
        check(f'Trittschall Stahlbeton 18 + Estrich 5 cm, s′ = 15: L′_n,w = {L:.1f} dB', abs(g[0]-L)<1e-9 and g[1]==(L+2<=50), g)
        check('Trittschallfelder sichtbar, wenn angehakt', await pg.evaluate("document.querySelector('.bs-trrow').offsetParent!==null"))
        # ── Bericht, Speichern, Menü ──
        for mode,word in [('uwert','Wärmedurchgangskoeffizient'),('glaser','Tauperiode'),('schall','Massegesetz')]:
            await pg.evaluate(f"setBpMode('{mode}'); run(); showReport()"); rp=await pg.inner_text('#report')
            check(f'Bericht {mode}', word.lower() in rp.lower() and 'bauteilaufbau' in rp.lower())
        await pg.evaluate("setBpMode('glaser'); $('bl-d2').value=7; run(); save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden stellt Bauphysik wieder her', await pg.evaluate("MAT==='bauph' && BPMODE==='glaser' && $('bl-d2').value==='7' && LAST.mode==='glaser'"))
        check('Menü kennt die fünf Bauphysik-Nachweise (mit Gebäudeklasse und Sommer)', await pg.evaluate("[...document.querySelectorAll('#seg-bp button')].length")==5)
        await pg.set_viewport_size({'width':390,'height':844}); await pg.wait_for_timeout(100)
        check('Handy: kein Querscrollen', await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth+1"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
