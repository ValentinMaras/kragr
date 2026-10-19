# size v0.5.40 / ref v0.3.31 Bauphysik: Baustoffe in Gruppen, neue Baustoffe, Luftschichten nach DIN EN ISO 6946
# (ruhend Tab. 8, schwach belüftet R_T = ½R_T,u + ½R_T,v, stark belüftet: außen entfällt, R_se = R_si) und Glaser mit
# hinterlüfteter Außenschale (R_se = 0,08). Sollwerte unabhängig in Python. Ohne Playwright: SKIP.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','size.html')); REF=U.replace('size.html','ref.html')
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
close=lambda a,b,tol=1e-4: abs(a-b)<=tol*max(1,abs(b))
D=[0,5,7,10,15,25,50,100,300]; TAB={'auf':[0,.11,.13,.15,.16,.16,.16,.16,.16],'hor':[0,.11,.13,.15,.17,.18,.18,.18,.18],'ab':[0,.11,.13,.15,.17,.19,.21,.22,.23]}
def rluft(dmm, r):
    import bisect
    R=TAB[r]
    for i in range(1,len(D)):
        if dmm<=D[i]: return R[i-1]+(R[i]-R[i-1])*(dmm-D[i-1])/(D[i]-D[i-1])
    return R[-1]
INNEN=[(0.015,0.51),(0.175,0.99),(0.12,0.035)]          # Gipsputz, KS, MW 035
KL=(0.115,0.96)                                          # Klinker
psat=lambda t: 610.5*math.exp(17.269*t/(237.3+t)) if t>=0 else 610.5*math.exp(21.875*t/(265.5+t))

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def fresh(lang='de', mode='uwert'):
            await pg.goto(U); await pg.evaluate(f"localStorage.clear();localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(300)
            await pg.evaluate(f"setMat('bauph'); setBpMode('{mode}')"); await pg.wait_for_timeout(250)
        async def setl(spec):
            js="(()=>{const ix=n=>String(BP_MAT.findIndex(m=>m[0]===n));"
            for i,(n,d) in enumerate(spec):
                js+=f"$('bl-m{i+1}').value={('ix('+repr(n)+')') if n else repr('-')}; $('bl-d{i+1}').value=''; " + (f"bpPick({i+1}); $('bl-d{i+1}').value={d};" if n else f"$('bl-d{i+1}').value=0;")
            await pg.evaluate(js+" run();})()"); await pg.wait_for_timeout(250)
        await fresh()
        # 1) Auswahl in Gruppen, alle Baustoffe genau einmal
        g=await pg.evaluate("[...document.querySelectorAll('#bl-m2 optgroup')].map(o=>[o.label,[...o.children].map(c=>+c.value)])")
        allv=sorted(sum([x[1] for x in g],[])); n=await pg.evaluate("BP_MAT.length")
        check('Auswahl: 8 Gruppen, jeder Baustoff genau einmal (65 inkl. Luftschichten)', len(g)==8 and allv==list(range(n)) and n==65, [x[0] for x in g])
        tab=await pg.evaluate("[bpLuftR(0,'hor'),bpLuftR(40,'hor'),bpLuftR(25,'auf'),bpLuftR(50,'ab'),bpLuftR(12,'hor'),bpLuftR(400,'ab')]")
        check('R ruhender Luftschichten nach Tab. 8 (interpoliert, > 300 mm gedeckelt)', all(close(a,b) for a,b in zip(tab,[0,rluft(40,'hor'),.16,.21,rluft(12,'hor'),.23])), tab)
        # 2) zweischalige Wand
        base=[('Gipsputz',1.5),('Kalksandstein RDK 1,8',17.5),('Mineralwolle WLS 035',12)]
        Rin=sum(d/l for d,l in INNEN)
        await setl(base+[('Luftschicht, ruhend',4),('Klinker (Vormauerschale)',11.5),(None,0)])
        r=await pg.evaluate("[LAST.res.W.U, $('bl-l4').disabled]"); RTu=0.13+Rin+0.18+KL[0]/KL[1]+0.04
        check('ruhende Luftschicht 40 mm, Wand: R = 0,18, U = 1/R_T, λ-Feld gesperrt', close(r[0],1/RTu) and r[1], (r, 1/RTu))
        await setl(base+[('Luftschicht, schwach belüftet',4),('Klinker (Vormauerschale)',11.5),(None,0)])
        r=await pg.evaluate("LAST.res.W.U"); RTv=0.13+Rin+0.13
        check('schwach belüftet: R_T = ½·R_T,u + ½·R_T,v (DIN EN ISO 6946, 6.9.3)', close(r,1/((RTu+RTv)/2)), (r, 1/((RTu+RTv)/2)))
        await setl(base+[('Luftschicht, stark belüftet',4),('Klinker (Vormauerschale)',11.5),(None,0)])
        r=await pg.evaluate("[LAST.res.W.U, LAST.res.W.Rse]")
        t=await pg.evaluate("document.getElementById('n-bu').innerText")
        check('stark belüftet: Vormauerschale entfällt, R_se = R_si = 0,13', close(r[0],1/RTv) and r[1]==0.13 and 'entfallen' in t, r)
        # Dach: Wärmestrom nach oben
        await pg.evaluate("$('bp-art').value='dach'; run()"); await pg.wait_for_timeout(250)
        await setl([('Gipskartonplatte',1.25),('Mineralwolle WLS 035',20),('Luftschicht, ruhend',2.5),('Nadelholz',2.4),(None,0),(None,0)])
        r=await pg.evaluate("LAST.res.W.U"); RT=0.10+0.0125/0.25+0.20/0.035+0.16+0.024/0.13+0.04
        check('Dach mit ruhender Luftschicht 25 mm: R = 0,16 (Wärmestrom nach oben)', close(r,1/RT), (r,1/RT))
        # 3) Glaser mit hinterlüfteter Außenschale
        await fresh(mode='glaser')
        await setl(base+[('Luftschicht, stark belüftet',4),('Klinker (Vormauerschale)',11.5),(None,0)])
        G=await pg.evaluate("[LAST.res.G.Stot, LAST.res.G.T[LAST.res.G.T.length-1], LAST.res.G.T[0]]")
        RT=0.25+Rin+0.08; q=25/RT; sd=0.015*10+0.175*15+0.12*1
        check('Glaser hinterlüftet: s_d nur innen, R_se = 0,08 (θ_se, θ_si unabhängig)', close(G[0],sd) and close(G[1],-5+q*0.08,1e-3) and close(G[2],20-q*0.25,1e-3), (G, sd))
        t=await pg.evaluate("document.getElementById('n-bgd').innerText")
        check('Glaser: Randbedingung zeigt R_se = 0,08 und den Hinweis', 'Rse = 0,08' in t.replace('\n',' ') and 'Hinterlüftete Außenschale' in t, t[:160])
        # 4) neue Baustoffe: übliche Dicken beim Wählen
        await fresh()
        ds={}
        for nme in ['Unterdeckbahn, diffusionsoffen','Dampfsperre mit Alu-Einlage','Klinker (Vormauerschale)','Luftschicht, ruhend','Fliesen (Keramik)','Schaumglas WLS 045']:
            await pg.evaluate(f"$('bl-d5').value=''; $('bl-m5').value=String(BP_MAT.findIndex(m=>m[0]==={nme!r})); bpPick(5)"); await pg.wait_for_timeout(120)
            ds[nme]=await pg.evaluate("$('bl-d5').value")
        check('übliche Dicken: Unterdeckbahn 0,05 · Alu 0,04 · Klinker 11,5 · Luft 4 · Fliesen 1 · Schaumglas 10 cm', list(ds.values())==['0.05','0.04','11.5','4','1','10'], ds)
        # 5) Sprachen: Gruppen und neue Namen übersetzt
        bad={}
        for lang,w in [('en','Air layers'),('fr','Lames d’air'),('es','Cámaras de aire')]:
            await fresh(lang)
            lab=await pg.evaluate("[...document.querySelectorAll('#bl-m2 optgroup')].map(o=>o.label).join('|')")
            txt=await pg.evaluate("[...document.querySelectorAll('#bl-m2 option')].map(o=>o.textContent).join('|')")
            if w not in lab or any(x in txt for x in ['Luftschicht','Klinker (Vormauer','Brettsperrholz','Dämmstofffüllung']) or 'Putze' in lab: bad[lang]=lab[:80]
        check('EN/FR/ES: Gruppen und neue Baustoffe übersetzt', not bad, bad)
        # 6) ref: gleiche Gruppen, Luftschicht im U-Wert-Rechner
        await pg.goto(REF+'#/bauphysik/waerme/uwert'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
        k=await pg.evaluate("document.querySelectorAll('#uw-m1 optgroup').length")
        await pg.evaluate("(()=>{const ix=n=>String(BP_MAT.findIndex(m=>m[0]===n)); const set=(i,n,d)=>{const e=document.getElementById('uw-m'+i); if(!e) return; e.value=n?ix(n):'-'; document.getElementById('uw-d'+i).value=d;}; set(1,'Gipsputz',1.5); set(2,'Kalksandstein RDK 1,8',17.5); set(3,'Mineralwolle WLS 035',12); set(4,'Luftschicht, ruhend',4); set(5,'Klinker (Vormauerschale)',11.5); set(6,null,0); updateUW(); })()")
        await pg.wait_for_timeout(250)
        t=await pg.evaluate("document.getElementById('uw-out').innerText")
        exp=f"{1/RTu:.3f}".replace('.',',')
        check('ref U-Wert: 8 Gruppen, ruhende Luftschicht mit R aus Tab. 8 → gleiches U', k==8 and exp in t and 'Tab. 8' in t, (k, exp))
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
