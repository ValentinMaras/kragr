# kragr-Design Stufe 3 in size (v0.6.1, Profil-Knöpfe in v0.6.2 entfernt): Stepper − / + an den Zahlenfeldern (Schritt nach Wert: 220 → 10, 60 → 1, 6.0 → 0.1),
# „Aus calc übernehmen“ in den Schnittgrößen-Karten, Übungsmodus als Schalter.
# Rechnung unverändert. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:220])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        n=await pg.evaluate("[document.querySelectorAll('.col-in .k-stp').length, !!document.querySelector('.k-stp #in-M'), document.querySelector('.k-stp:has(#in-M) .k-sb').getAttribute('aria-label')]")
        check('Stepper an den Zahlenfeldern (M_Ed mit vorlesbarem Knopf)', n[0]>50 and n[1] and 'verringern' in n[2], n)
        e0=await pg.inner_text('#summary')
        await pg.click('.k-stp:has(#in-M) .k-sb >> nth=1'); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[$('in-M').value, $('summary').innerText]")
        check('M_Ed 220 + → 230 kNm (Schritt 10), Nachweis neu gerechnet', r[0]=='230' and r[1]!=e0, r)
        await pg.click('.k-stp:has(#in-M) .k-sb >> nth=0'); await pg.wait_for_timeout(900)
        check('− → wieder 220, gleiches Ergebnis wie vorher', await pg.evaluate("[$('in-M').value, $('summary').innerText]")==['220', e0])
        await pg.click('.k-stp:has(#in-l) .k-sb >> nth=1'); await pg.wait_for_timeout(500)
        await pg.click('.k-stp:has(#in-h) .k-sb >> nth=1'); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[$('in-l').value, $('in-h').value]")
        check('Stützweite 6.0 + → 6.1 (Schritt 0,1), Höhe 60 + → 61', r==['6.1','61'], r)
        await pg.evaluate("$('in-l').value='6.0'; $('in-h').value='60'; run()"); await pg.wait_for_timeout(500)
        check('kein „Aus calc übernehmen“ mehr in den Karten (seit v0.7.1 nur über „Meine Projekte“)', await pg.evaluate("document.querySelectorAll('.col-in .k-ci, .k-cimenu').length")==0)
        # Stahl: Profil-Knöpfe
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(900)
        s0=await pg.inner_text('#summary')
        check('Stahl: keine Profil-Knöpfe (Profil nur über die Auswahlliste, seit v0.6.2)', await pg.evaluate("document.querySelectorAll('.k-pills, .k-pill').length")==0)
        await pg.select_option('#sn-prof','IPE 270'); await pg.wait_for_timeout(800)
        check('Auswahlliste wählt das Profil, Nachweis neu', await pg.evaluate("$('sn-prof').value")=='IPE 270' and await pg.inner_text('#summary')!=s0)
        await pg.select_option('#sn-prof','IPE 300'); await pg.wait_for_timeout(600)
        # Übungsmodus-Schalter
        sw=await pg.evaluate("(()=>{const t=document.getElementById('ueb-btn'); return [t.closest('.hdr-tools')?1:0, t.getAttribute('aria-pressed'), t.title, !!document.querySelector('.det-bar .ueb-tog')]})()")
        check('Übungsmodus als Doktorhut-Knopf in der Kopfzeile (aus), kein Schalter mehr in der Rechenweg-Leiste', sw==[1,'false','Übungsmodus: Aus – vollständige Lösung',False], sw)
        await pg.click('#ueb-btn'); await pg.wait_for_timeout(600)
        sw=await pg.evaluate("(()=>{const t=document.getElementById('ueb-btn'); return [t.getAttribute('aria-pressed'), t.title, document.body.classList.contains('uebung')]})()")
        check('an: „Zahlen verborgen“, Übungsmodus aktiv', sw[0]=='true' and 'Zahlen verborgen' in sw[1] and sw[2], sw)
        await pg.click('#ueb-btn'); await pg.wait_for_timeout(500)
        # kein Querscrollen in allen Bereichen
        ov={}
        await pg.set_viewport_size({'width':360,'height':740})
        for m in ['beton','stahl','holz','mauer','grund','bauph','wasser']:
            await pg.evaluate(f"setMat('{m}')"); await pg.wait_for_timeout(700); ov[m]=await pg.evaluate("document.documentElement.scrollWidth")
        check('Handy 360 px: kein Querscrollen in allen Baustoffen', all(v<=360 for v in ov.values()), ov)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[document.getElementById('ueb-btn').title, document.querySelector('.k-sb').getAttribute('aria-label')]")
        check('EN: Practice mode · decrease', 'Practice mode' in r[0] and 'full solution' in r[0] and r[1].endswith('decrease'), r)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
