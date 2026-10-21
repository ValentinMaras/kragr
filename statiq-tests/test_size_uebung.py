# size v0.5.43 Übungsmodus: Ergebnis, Abbildung und Rechenweg verdeckt; η und Zwischenwerte prüfen; Schritt für Schritt
# aufdecken; neue Aufgabe setzt zurück; Schalter wird gemerkt; EN übersetzt. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
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
        await pg.goto(U); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(300)
        check('aus: kein Übungsfeld, Ergebnis sichtbar', await pg.evaluate("document.querySelectorAll('.ueb-box').length===0 && getComputedStyle($('summary')).display!=='none'"))
        await pg.click('.det-bar .ueb-tog'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("""[document.querySelectorAll('#details > .card[id^="n-"]').length, document.querySelectorAll('.ueb-box').length,
          getComputedStyle($('summary')).display, getComputedStyle($('chk-table')).display, getComputedStyle($('fig')).display,
          [...document.querySelectorAll('#details .card.ueb .st')].every(s=>{ const f=s.querySelector('.st-f'); if(!f) return s.classList.contains('ueb-hid'); const c=f.cloneNode(true); c.querySelectorAll('sub,sup').forEach(x=>x.remove()); return s.classList.contains('ueb-hid') && !/(^|[^\w.])\d+[.,]\d/.test(c.textContent); }),
          [...document.querySelectorAll('#details .card.ueb > .card-title .tag')].every(t=>getComputedStyle(t).display==='none')]""")
        check('an: jede Karte mit Übungsfeld; Ergebnis, Tabelle, Abbildung und η verdeckt, Schritte ohne Zahlenwerte', r[0]==r[1]>0 and r[2]==r[3]==r[4]=='none' and r[5] and r[6], r)
        eta=await pg.evaluate("UEB_C.find(c=>c.id==='qs').eta")
        await pg.fill('#n-qs .ueb-in', f"{eta:.2f}".replace('.',',')); await pg.click('#n-qs .ueb-row button')
        m=await pg.inner_text('#n-qs .ueb-msg'); shown=await pg.evaluate("getComputedStyle(document.querySelector('#n-qs > .card-title .tag')).display!=='none'")
        check('richtiges η (mit Komma): „Richtig“, η-Anzeige wird sichtbar', m.startswith('Richtig') and shown, m)
        await pg.fill('#n-qs .ueb-in', '61 %'); await pg.click('#n-qs .ueb-row button')
        check('η auch in Prozent', (await pg.inner_text('#n-qs .ueb-msg')).startswith('Richtig'))
        vpl=await pg.evaluate("UEB_C.find(c=>c.id==='qv').qv.Vpl")
        await pg.fill('#n-qv .ueb-in', f"{vpl:.1f}"); await pg.click('#n-qv .ueb-row button'); m=await pg.inner_text('#n-qv .ueb-msg')
        check('Zwischenwert V_pl,Rd wird im Rechenweg gefunden (Schritt 2)', 'Schritt 2' in m, m)
        await pg.fill('#n-qv .ueb-in', '9999'); await pg.click('#n-qv .ueb-row button'); m=await pg.inner_text('#n-qv .ueb-msg')
        check('falscher Wert: Hinweis mit Tipp', m.startswith('Stimmt nicht'), m)
        await pg.fill('#n-qv .ueb-in', 'abc'); await pg.click('#n-qv .ueb-row button')
        check('keine Zahl: Bitte eine Zahl eingeben', (await pg.inner_text('#n-qv .ueb-msg')).startswith('Bitte'))
        await pg.click('#n-klasse .ueb-next'); await pg.click('#n-klasse .ueb-next')
        r=await pg.evaluate("[document.querySelectorAll('#n-klasse .st:not(.ueb-hid)').length, document.querySelector('#n-klasse .ueb-cnt').textContent]")
        check('„Nächster Schritt“ deckt einen Schritt nach dem anderen auf', r[0]==2 and r[1].startswith('Schritt 2 von'), r)
        await pg.click('#n-klasse .ueb-row button:has-text("Lösung zeigen")')
        r=await pg.evaluate("[document.querySelectorAll('#n-klasse .st.ueb-hid').length, document.querySelector('#n-klasse').classList.contains('ueb-done'), document.querySelector('#n-klasse .ueb-next').disabled]")
        check('„Lösung zeigen“ deckt alles auf, Knopf „Nächster Schritt“ gesperrt', r==[0,True,True], r)
        await pg.click('#ueb-figbtn'); check('Abbildung lässt sich einblenden', await pg.evaluate("getComputedStyle($('fig')).display!=='none'"))
        await pg.evaluate("$('sn-M').value='120'; run()"); await pg.wait_for_timeout(300)
        check('neue Aufgabe (Eingabe geändert): Schritte wieder verdeckt', await pg.evaluate("document.querySelectorAll('#n-klasse .st:not(.ueb-hid)').length===0"))
        await pg.reload(); await pg.wait_for_timeout(300); await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(300)
        check('Schalter wird gemerkt (nach Neuladen weiter Übungsmodus)', await pg.evaluate("document.body.classList.contains('uebung') && document.querySelectorAll('.ueb-box').length>0"))
        await pg.evaluate("setMat('bauph'); setBpMode('uwert')"); await pg.wait_for_timeout(300)
        check('auch in anderen Fächern (Bauphysik)', await pg.evaluate("document.querySelectorAll('.ueb-box').length>0"))
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(400); await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.getElementById('details').innerText+' '+document.getElementById('ueb-hint').innerText")
        check('EN: Übungsmodus übersetzt', 'Practice mode' in t and 'Next step' in t and 'Übung' not in t and 'Nächster' not in t, t[:100])
        await pg.click('.det-bar .ueb-tog'); await pg.wait_for_timeout(300)
        check('ausschalten: alles wieder sichtbar', await pg.evaluate("!document.body.classList.contains('uebung') && document.querySelectorAll('.ueb-box').length===0"))
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
