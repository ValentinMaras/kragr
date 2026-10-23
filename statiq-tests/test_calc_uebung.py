# calc v0.8.25 Übungsmodus: Ergebniswerte, Schnittgrößenbild und Rechenweg verdeckt; Auflagerkraft, M_max und
# Zwischenwerte prüfen; Schritt für Schritt aufdecken; alle vier Systeme; gleicher Schalter wie size. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        check('aus: Schalter da, Ergebnisse sichtbar, kein Übungsfeld', await pg.evaluate("document.getElementById('ueb-btn') && getComputedStyle(document.querySelector('#tab-beam .results-grid')).display!=='none' && !document.querySelector('.ueb-box')"))
        await pg.click('#ueb-btn'); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[getComputedStyle(document.querySelector('#tab-beam .results-grid')).display, getComputedStyle(document.querySelector('#tab-beam .diagram-svg-wrap')).display, document.querySelectorAll('#rw-beam .st').length, document.querySelectorAll('#rw-beam .st.ueb-hid').length]")
        check('an: Ergebniswerte, Schnittgrößenbild und alle Schritte verdeckt', r[0]=='none' and r[1]=='none' and r[2]==r[3]>0, r)
        va=await pg.evaluate("document.getElementById('b-res-A').textContent")
        await pg.fill('#rw-beam .ueb-in', va.replace('.',',')); await pg.click('#rw-beam .ueb-row button'); m=await pg.inner_text('#rw-beam .ueb-msg')
        check('Auflagerkraft V_A (mit Komma) erkannt', m.startswith('Richtig') and 'A' in m, m)
        mm=await pg.evaluate("document.getElementById('b-res-Mmax').textContent")
        await pg.fill('#rw-beam .ueb-in', str(round(float(mm),1))); await pg.click('#rw-beam .ueb-row button'); m=await pg.inner_text('#rw-beam .ueb-msg')
        check('M_max auf eine Stelle gerundet erkannt (Toleranz 1 %)', m.startswith('Richtig') and 'max' in m, m)
        await pg.fill('#rw-beam .ueb-in', '-'+va); await pg.click('#rw-beam .ueb-row button')
        check('Vorzeichen frei (Richtung je nach Konvention)', (await pg.inner_text('#rw-beam .ueb-msg')).startswith('Richtig'))
        await pg.fill('#rw-beam .ueb-in', '5'); await pg.click('#rw-beam .ueb-row button'); m=await pg.inner_text('#rw-beam .ueb-msg')
        check('Zwischenwert aus dem Rechenweg (L = 5 m) → Schritt 1', 'Schritt 1' in m, m)
        await pg.fill('#rw-beam .ueb-in', '999'); await pg.click('#rw-beam .ueb-row button')
        check('falscher Wert: Hinweis mit Tipp', (await pg.inner_text('#rw-beam .ueb-msg')).startswith('Stimmt mit keinem'))
        await pg.click('#rw-beam .ueb-next'); await pg.click('#rw-beam .ueb-next')
        check('„Nächster Schritt“ zeigt zwei Schritte', await pg.evaluate("document.querySelectorAll('#rw-beam .st:not(.ueb-hid)').length")==2)
        await pg.click('#rw-beam .ueb-row button:has-text("Lösung zeigen")')
        check('„Lösung zeigen“: alle Schritte sichtbar', await pg.evaluate("document.querySelectorAll('#rw-beam .st.ueb-hid').length")==0)
        await pg.click('#tab-beam .ueb-diabtn')
        check('Schnittgrößenbild lässt sich einblenden', await pg.evaluate("getComputedStyle(document.querySelector('#tab-beam .diagram-svg-wrap')).display!=='none'"))
        res={}
        for tab,sys in [('cantilever','cant'),('cont','cont'),('frame','frame')]:
            await pg.evaluate(f"showTab('{tab}')"); await pg.wait_for_timeout(500)
            res[tab]=await pg.evaluate(f"!!document.querySelector('#rw-{sys} .ueb-box') && document.querySelectorAll('#rw-{sys} .st.ueb-hid').length>0 && getComputedStyle(document.querySelector('#tab-{tab} .results-grid')).display==='none'")
        check('Kragarm, Durchlaufträger und Rahmen ebenfalls im Übungsmodus', all(res.values()), res)
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(400)
        check('gleicher Schalter: size startet ebenfalls im Übungsmodus', await pg.evaluate("document.body.classList.contains('uebung')"))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(400)   # seit v0.9.5 öffnet calc den zuletzt benutzten Bereich (Entwurf)
        t=await pg.evaluate("document.querySelector('#tab-beam .col-out').innerText+' '+document.getElementById('ueb-btn').title")
        check('EN: Übungsmodus übersetzt', 'numbers hidden' in t and 'Next step' in t and 'Übung' not in t, t[:80])
        await pg.click('#ueb-btn'); await pg.wait_for_timeout(400)
        check('ausschalten: alles wieder sichtbar', await pg.evaluate("!document.body.classList.contains('uebung') && !document.querySelector('.ueb-box') && document.querySelectorAll('#rw-beam .st.ueb-hid').length===0"))
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
