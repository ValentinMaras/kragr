# size v0.5.39 Bauphysik — Plausibilität: Eingaben ohne Einfluss ausgeblendet, ρ wirkt im U-Wert (leichte Bauteile R ≥ 1,75),
# Baustoffnamen ohne Rohdichte, Folien mit realistischer Dicke, Massegesetz nur für die massive Schale. Ohne Playwright: SKIP.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
close=lambda a,b,tol=1e-3: abs(a-b)<=tol*max(1,abs(b))
# Standardaufbau: Gipsputz 1,5 / KS 17,5 / MW 16 / KZ-Putz 1 cm
STD=[(0.015,0.51,1200),(0.175,0.99,1800),(0.16,0.035,30),(0.01,1.0,1800)]

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def fresh(lang='de', mode='uwert'):
            await pg.goto(U); await pg.evaluate(f"localStorage.clear();localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(300)
            await pg.evaluate(f"setMat('bauph'); setBpMode('{mode}')"); await pg.wait_for_timeout(250)
        vis=lambda: pg.evaluate("['d','l','u','r'].filter(c=>document.getElementById('bl-'+c+'2').offsetParent).join('')")
        await fresh()
        # 1) nur Eingaben, die in die Rechnung eingehen
        exp={'uwert':'dlr','glaser':'dlu','schall':'dr'}
        for mode,e in exp.items():
            await pg.evaluate(f"setBpMode('{mode}'); ML.bp.open=2; mlRefresh()"); await pg.wait_for_timeout(200); v=await vis()   # Schicht 2 aufgeklappt (seit v0.5.50 Liste)
            check(f'{mode}: sichtbar nur die wirksamen Spalten ({e})', v==e, v)
        # 2) ρ wirkt im U-Wert über m′ (DIN 4108-2, 5.1.2.2)
        await pg.evaluate("setBpMode('uwert')"); await pg.wait_for_timeout(200)
        R=sum(d/l for d,l,_ in STD); m=sum(d*r for d,_,r in STD)
        r=await pg.evaluate("(()=>{const c=LAST.res.C.find(x=>x.id==='bumin'); return [c.eta,c.Rmin,c.mF]})()")
        check('U-Wert Standard: m′ = Σρ·d ≥ 100 → R_min = 1,20, η = R_min/R', close(r[2],m) and r[1]==1.2 and close(r[0],1.2/R), (r, m, R))
        await pg.evaluate("$('bl-r2').value='300'; run()"); await pg.wait_for_timeout(250)
        m2=m-0.175*1800+0.175*300
        r=await pg.evaluate("(()=>{const c=LAST.res.C.find(x=>x.id==='bumin'); return [c.eta,c.Rmin,c.mF]})()")
        check('ρ der KS-Schicht 300 kg/m³ → m′ < 100: leichtes Bauteil, R_min = 1,75', close(r[2],m2) and m2<100 and r[1]==1.75 and close(r[0],1.75/R), (r, m2))
        t=await pg.evaluate("document.getElementById('n-bumin').innerText")
        check('Rechenweg nennt m′ und die Regel für leichte Bauteile (5.1.2.2)', 'leichtes Bauteil' in t and '5.1.2.2' in t, t[:120])
        # 3) Glaser: ρ ohne Einfluss (Spalte ausgeblendet)
        await pg.evaluate("setBpMode('glaser')"); await pg.wait_for_timeout(250)
        a=await pg.evaluate("JSON.stringify(LAST.res.C.map(c=>[c.id,c.eta]))")
        await pg.evaluate("$('bl-r2').value='2400'; run()"); await pg.wait_for_timeout(250)
        b=await pg.evaluate("JSON.stringify(LAST.res.C.map(c=>[c.id,c.eta]))")
        check('Tauwasser: Ergebnis unabhängig von ρ (darum ausgeblendet)', a==b)

        # 4) Baustoffnamen ohne Rohdichte und ohne Kennwerte, die in den Spalten stehen
        bad={}
        for lang in ['de','en','fr','es']:
            await fresh(lang)
            names=await pg.evaluate("[...document.querySelectorAll('#bl-m2 option')].filter(o=>!o.hidden).map(o=>o.textContent)")
            b_=[n for n in names if any(w in n for w in ['RDK','Rohdichte','density','(λ','s_d','0,2 mm','0.2 mm','4 mm'])]
            if b_ or len(set(names))!=len(names): bad[lang]=b_ or 'doppelt'
        check('Auswahl DE/EN/FR/ES: keine Rohdichte, kein λ/s_d im Namen, kein Name doppelt', not bad, bad)
        await fresh()
        await pg.evaluate("$('bl-m2').value='6'; bpPick(2)"); await pg.wait_for_timeout(200)
        r=await pg.evaluate("[$('bl-m2').value, $('bl-l2').value, $('bl-r2').value, $('bl-m2').selectedOptions[0].textContent]")
        check('alter Speicherstand „KS 2,0“ (Index 6) lädt weiter mit λ = 1,1 und ρ = 2000', r==['6','1.1','2000','Kalksandstein'], r)
        # 5) Folien: Dicke beim Wählen 0,2 mm → s_d = μ·d = 100 m
        await fresh(mode='glaser')
        await pg.evaluate("$('bl-d5').value=''; $('bl-m5').value=String(BP_MAT.findIndex(m=>m[0].startsWith('PE-Folie'))); bpPick(5)"); await pg.wait_for_timeout(250)
        d=await pg.evaluate("$('bl-d5').value"); t=await pg.evaluate("document.getElementById('details').innerText")
        sd=sum(dd*mu for dd,mu in [(0.015,10),(0.175,15),(0.16,1),(0.01,20)])+0.0002*500000
        check('PE-Folie: Dicke 0,02 cm → s_d = 100 m (vorher 10 cm → 50 000 m)', d=='0.02' and (f'{sd:.3f}'.replace('.',',') in t), (d, sd))
        # 6) Schallschutz: Massegesetz nur für die massive Schale
        await fresh(mode='schall')
        r=await pg.evaluate("[LAST.res.m, LAST.res.Rw]"); ms=0.015*1200+0.175*1800
        t=await pg.evaluate("document.getElementById('n-bsm').innerText")
        check('Schall Standard (KS mit WDVS): m′ nur Putz + KS = 333 kg/m², Dämmung und Außenputz nicht', close(r[0],ms) and close(r[1],30.9*math.log10(ms)-22.2) and 'Nicht angesetzt' in t and 'Kalkzementputz' in t, r)
        await pg.evaluate("$('bl-m3').value='-'; run()"); await pg.wait_for_timeout(250)
        r=await pg.evaluate("[LAST.res.m]"); m3=0.015*1200+0.175*1800+0.01*1800
        t=await pg.evaluate("document.getElementById('n-bsm').innerText")
        check('Schall ohne Dämmschicht: alle Schichten zählen, kein Hinweis', close(r[0],m3) and 'Nicht angesetzt' not in t, r)
        await fresh('en','schall')
        t=await pg.evaluate("document.getElementById('details').innerText")
        check('EN: Massegesetz-Karte ohne deutsche Reste', 'einschalig' not in t and 'Nicht angesetzt' not in t and 'Not included' in t)
        # 7) ref: Vorgaben der Rechner auch in EN/FR/ES (vorher leer: übersetzter Name fand keinen Baustoff)
        REF=U.replace('size.html','ref.html')
        res={}
        for lang in ['en','fr','es']:
            await pg.goto(REF+'#/bauphysik/waerme/uwert'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(400)
            a=await pg.evaluate("document.getElementById('uw-out').innerText")
            await pg.goto(REF+'#/bauphysik/feuchte/glaser'); await pg.reload(); await pg.wait_for_timeout(400)
            g=await pg.evaluate("document.getElementById('gl-out').innerText")
            res[lang]=('0.202' in a or '0,202' in a) and len(g)>200
        check('ref U-Wert und Glaser: Beispielaufbau auch in EN/FR/ES gerechnet', all(res.values()), res)
        await pg.goto(REF+'#/bauphysik/waerme/uwert'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
        a=await pg.evaluate("document.getElementById('uw-out').innerText")
        check('ref U-Wert: m′ und Regel für leichte Bauteile im Rechenweg', 'm′ = Σ' in a and '355,8 kg/m²' in a, a[-200:])
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
