# Rechenweg mit dem Kraftgrößenverfahren und der Integraltafel (calc v0.11.13).
# Sollwerte von Hand:
#   Durchlaufträger, 2 Felder l = 5 m, q = 5 kN/m (Startwerte): Grundsystem mit Gelenk über B, X1 = M_B
#     EI·δ11 = l/3 + l/3 = 3,333 · EI·δ10 = 2 · l/3 · f mit f = q·l²/8 = 15,625 → 2 · 26,042 = 52,083
#     X1 = −52,083/3,333 = −15,625 kNm = −q·l²/8
#   Zweigelenkrahmen h = 4 m, l = 5 m, gleiches EI, nur q = 10 kN/m auf dem Riegel: X1 = H_B
#     M̄1 = h·(Lage) → EI·δ11 = 2·h³/3 + h²·l = 42,667 + 80 = 122,667
#     |EI·δ10| = h · 2/3 · (q·l²/8) · l = 4 · 2/3 · 31,25 · 5 = 416,667
#     |H_B| = q·l³ / (12·h·(2h/3 + l)) = 1250 / 368 = 3,397 kN
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
def txt(S): return re.sub(r'<[^>]+>','', '\n'.join(S))
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        # Durchlaufträger
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(700)
        t=txt(await pg.evaluate("rwCont().S"))
        check('DLT: Grundsystem mit Gelenken, X1 = M_B', 'Grundsystem' in t and 'X1 = MB' in t, t[:200])
        check('DLT: EI₀·δ11 = 5,00/3 + 5,00/3 = 3,333', 'EI₀·δ11 = 5,00/3 + 5,00/3 = 3,333' in t)
        check('DLT: Tafelzeile Parabel × Dreieck, l/3 · f = 26,042 je Feld', t.count('(Parabel × Dreieck): l/3 · f = 5,00/3 · 15,63 = 26,042')==2)
        check('DLT: EI₀·δ10 = 52,083', 'EI₀·δ10 = 52,083' in t)
        check('DLT: Gleichung 3,333·X1 + 52,083 = 0, Hinweis Dreimomentengleichung', '3,333·X1 + 52,083 = 0' in t and 'Dreimomentengleichung' in t)
        m=re.search(r'X1 = MB = (-?[\d,]+) kNm', t); v=float(m.group(1).replace(',','.')) if m else None
        check('DLT: M_B = −15,625 kNm (= −q·l²/8)', v is not None and abs(v+15.625)<0.006, v)
        check('DLT: Kontrolle gegen den Löser 0,000', 'Abweichung 0,000 kNm' in t)
        check('DLT: Link zur Integraltafel in Wissen', 'href="ref.html#/baustatik/arbeitssatz/koppeltafel"' in '\n'.join(await pg.evaluate("rwCont().S")))
        # Zweigelenkrahmen, nur q auf dem Riegel
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(600)
        await pg.evaluate("setSupportA('pin'); setSupportB('pin'); frameLoads.horiz.forEach(l=>l.enabled=false); calculateFrame()"); await pg.wait_for_timeout(600)
        r=await pg.evaluate("(()=>{ const r=rwFrame(); return {n:r.n, X:r.kgv&&r.kgv.X, rel:r.kgv&&r.kgv.rel.map(c=>c[1]+c[2]), dev:r.kgv&&r.kgv.dev, S:r.S} })()")
        t=txt(r['S'])
        check('Rahmen: n = 1, X1 = H_B', r['n']==1 and r['rel']==['HB'], r['rel'])
        check('Rahmen: EI₀·δ11 = 2h³/3 + h²·l = 122,667', 'EI₀·δ11 = 122,667' in t)
        m=re.search(r'EI₀·δ10 = (-?[\d,]+)', t); d10=float(m.group(1).replace(',','.')) if m else None
        check('Rahmen: |EI₀·δ10| = 416,667', d10 is not None and abs(abs(d10)-416.667)<0.002, d10)
        check('Rahmen: |H_B| = q·l³/(12·h·(2h/3 + l)) = 3,397 kN', r['X'] and abs(abs(r['X'][0])-1250/368)<0.002, r['X'])
        check('Rahmen: Riegel mit Parabelanteil l/3·f in der Tafelzeile', re.search(r'Riegel \(l = 5,00 m\): 5,00/6·\[.*\] \+ 5,00/3·\(?-?31,250', t) is not None)
        check('Rahmen: Kontrolle X und Momente gegen den Löser (< 0,001)', r['dev'] is not None and r['dev']<1e-3, r['dev'])
        # eingespannter Rahmen: n = 3
        await pg.evaluate("setSupportA('fixed'); setSupportB('fixed'); calculateFrame()"); await pg.wait_for_timeout(600)
        r=await pg.evaluate("(()=>{ const r=rwFrame(); return {n:r.n, rel:r.kgv&&r.kgv.rel.map(c=>c[1]+c[2]), dev:r.kgv&&r.kgv.dev, S:r.S.join(' ')} })()")
        check('Rahmen eingespannt: n = 3, X = M_B, H_B, V_B, Kontrolle < 0,001', r['n']==3 and r['rel']==['MB','HB','VB'] and r['dev']<1e-3, (r['rel'], r['dev']))
        check('Rahmen: 3×3-Gleichungssystem (δ33 vorhanden)', 'δ<sub>33</sub>' in r['S'])
        # Satteldach mit Gelenk
        await pg.evaluate("setSupportA('fixed'); setSupportB('pin'); document.getElementById('fGable').checked=true; document.getElementById('fF').value=1.5; addFrameHinge(); calculateFrame()"); await pg.wait_for_timeout(600)
        r=await pg.evaluate("(()=>{ const r=rwFrame(); return {n:r.n, dev:r.kgv&&r.kgv.dev} })()")
        check('Satteldach mit Gelenk: n = 1, Kontrolle < 0,001', r['n']==1 and r['dev'] is not None and r['dev']<1e-3, r)
        # Federn: Hinweis statt Kraftgrößenverfahren
        await pg.evaluate("frameHinges.length=0; document.getElementById('fGable').checked=false; setSupportA('pin'); setSupportB('pin'); SUPX.frame={on:true, B:{ch:5000}}; calculateFrame()"); await pg.wait_for_timeout(600)
        t=await pg.evaluate("rwFrame().S.join(' ')")
        check('mit Feder: Hinweis auf das Weggrößenverfahren', 'Federn, Setzungen oder Temperatur' in t, t[:120])
        await pg.evaluate("SUPX.frame={}; calculateFrame()")
        # Sprachen
        for l in ['en','fr','es']:
            await pg.evaluate(f"setCalcLang('{l}')"); await pg.wait_for_timeout(200)
            a=await pg.evaluate("rwFrame().S.join(' ')+rwCont().S.join(' ')")
            check(f'{l}: Rechenweg ohne Lücken (kein undefined) und ohne deutsche Schlüsselwörter', 'undefined' not in a and 'Grundsystem' not in a and 'Verträglichkeit' not in a, a[:120])
        await pg.evaluate("setCalcLang('de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
