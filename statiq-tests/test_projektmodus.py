# „Meine Projekte“ als eigenes Kapitel (calc v0.10.1 · size v0.7.1 · projekt v0.1.17): calc und size sind eigenständige Rechner
# ohne Projektbezug; erst aus „Meine Projekte“ geöffnet (?pos=<id>) arbeiten sie für eine Position, mit Projektzeile
# „Abbrechen“ / „Übernehmen und zurück“. Nur „Übernehmen“ schreibt in die Position. Schnittkräfte kommen nur über die Position
# nach size („＋ Nachweis“ mit passender Auswahl). Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
PJ="JSON.parse(localStorage.getItem('statiq-projekt')||'{}')"
SDF="Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_'))"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        # eigenständig
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("const e=document.getElementById('bL'); e.value='6'; e.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(1500)
        r=await pg.evaluate(f"[document.getElementById('k-pmbar').hidden, {SDF}.length, localStorage.getItem('statiq-projekt'), document.querySelectorAll('.k-tosize').length, document.getElementById('k-verfoot')?.textContent]")
        check('calc eigenständig: keine Projektzeile, nichts im Projekt, kein „Nachweis in size“', r[:4]==[True,0,None,0] and r[4]=='kragr·calc v0.10.1', r)
        await pg.reload(); await pg.wait_for_timeout(1200)
        check('calc eigenständig: Entwurf bleibt nach dem Neuladen (L = 6 m)', await pg.evaluate("document.getElementById('bL').value")=='6')
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(1200)
        r=await pg.evaluate("[document.getElementById('k-pmbar').hidden, document.querySelectorAll('.k-ci').length, !!document.getElementById('k-poscard')]")
        check('size eigenständig: keine Projektzeile, kein „Aus calc übernehmen“', r==[True,0,False], r)
        await pg.evaluate("setMat('holz')"); await pg.wait_for_timeout(500)
        await pg.click('#proj-btn'); await pg.wait_for_url('**/projekt.html'); await pg.wait_for_timeout(500)
        check('Ordner-Symbol führt direkt zu „Meine Projekte“', 'Noch nichts gespeichert' in await pg.inner_text('#list'))
        # Position anlegen, System in calc
        await pg.click('text=＋ Position'); await pg.wait_for_timeout(300)
        pid=await pg.evaluate(f"{PJ}.pos[0].id")
        await pg.click('.pos a.btn.p'); await pg.wait_for_url('**/calc.html?pos=*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[document.getElementById('k-pmbar').innerText.replace(/\\s+/g,' '), document.getElementById('bL').value]")
        check('„System in calc anlegen“: Projektzeile mit Pos. 1, Startwerte (nicht der Rechner-Entwurf)', 'Projekt · Pos. 1' in r[0] and 'Übernehmen und zurück' in r[0] and r[1]=='5', r)
        await pg.evaluate("const e=document.getElementById('bL'); e.value='7'; e.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(900)
        await pg.click('#k-pmbar [data-pm=x]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(500)
        check('„Abbrechen“ speichert nichts', await pg.evaluate(f"{SDF}.length")==0)
        await pg.click('.pos a.btn.p'); await pg.wait_for_url('**/calc.html?pos=*'); await pg.wait_for_timeout(1200)
        check('nach „Abbrechen“ wieder Startwerte', await pg.evaluate("document.getElementById('bL').value")=='5')
        await pg.evaluate("const e=document.getElementById('bL'); e.value='8'; e.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(900)
        await pg.reload(); await pg.wait_for_timeout(1200)
        check('Arbeitsstand im Projektmodus übersteht das Neuladen (L = 8 m)', await pg.evaluate("document.getElementById('bL').value")=='8')
        await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(600)
        r=await pg.evaluate(f"[{SDF}, {PJ}.pos[0].title, document.querySelector('.pos').innerText]")
        check('„Übernehmen“: System statiq_sdf_pos_<id>, Titel aus dem System', r[0]==['statiq_sdf_pos_'+pid] and r[1]=='Einfeldträger L=8m' and 'System bearbeiten' in r[2], r[:2])
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(1200)
        check('Rechner-Entwurf unberührt (L = 6 m)', await pg.evaluate("document.getElementById('bL').value")=='6')
        # Nachweis mit Schnittkräften
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(500)
        await pg.click('.pos .addc > button'); await pg.wait_for_timeout(200)
        zs=await pg.evaluate("[...document.querySelectorAll('.pos .addm a')].map(a=>new URLSearchParams(a.getAttribute('href').split('?')[1]).get('ziel')||'andere')")
        check('„＋ Nachweis“: nur passende Nachweise für den Einfeldträger und „Anderer Nachweis“', zs==['beton.balken','beton.unterzug','beton.platte','stahl.traeger','holz.bauteil','andere'], zs)
        await pg.click('.addm a[href*="holz.bauteil"]'); await pg.wait_for_url('**/size.html?*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[MAT, HOMODE, +$('ho-M').value, $('ho-name').value, document.getElementById('k-pmbar').innerText.replace(/\\s+/g,' ')]")
        check('size im Projektmodus: Holzträger mit M aus dem System (q·L²/8 + F·…)', r[:2]==['holz','bauteil'] and r[2]>40 and r[3]=='Holz · Träger / Stütze' and 'Nachweis: neuer Nachweis' in r[4], r)
        await pg.fill('#ho-name','Deckenbalken D1'); await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(600)
        r=await pg.evaluate(f"[JSON.parse(localStorage.getItem('statiq-size-positionen')).map(p=>[p.name, p.src&&p.src.key]), {PJ}.asg['s:Deckenbalken D1'], JSON.parse(localStorage.getItem('statiq-size-v1')||'{{}}').mat]")
        check('„Übernehmen“: Nachweis mit Quelle in der Position, Rechner-Stand von size unberührt (Holz bleibt)', r[0]==[['Deckenbalken D1','statiq_sdf_pos_'+pid]] and r[1]==pid and r[2]=='holz', r)
        # Nachweis öffnen, umbenennen
        await pg.click('.pos a[href*="check=Deckenbalken"]'); await pg.wait_for_url('**/size.html?*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[$('ho-name').value, document.getElementById('k-pmbar').innerText.replace(/\\s+/g,' ')]")
        check('„Öffnen“ lädt den Nachweis, Projektzeile nennt ihn', r[0]=='Deckenbalken D1' and 'Nachweis: Deckenbalken D1' in r[1], r)
        await pg.fill('#ho-name','Deckenbalken D2'); await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(600)
        r=await pg.evaluate(f"[JSON.parse(localStorage.getItem('statiq-size-positionen')).map(p=>p.name), Object.keys({PJ}.asg).filter(k=>k.startsWith('s:'))]")
        check('Umbenennen ersetzt den Nachweis, keine Kopie', r==[['Deckenbalken D2'],['s:Deckenbalken D2']], r)
        # System ändern → neu rechnen
        await pg.click('.pos a[href^="calc.html?pos="]'); await pg.wait_for_url('**/calc.html?pos=*'); await pg.wait_for_timeout(1200)
        check('„System bearbeiten“ lädt den übernommenen Stand (L = 8 m)', await pg.evaluate("document.getElementById('bL').value")=='8')
        await pg.evaluate("const e=document.getElementById('bL'); e.value='9'; e.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(600)
        await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(600)
        t=await pg.inner_text('.pos')
        check('geändertes System: Nachweis „calc geändert — neu rechnen“', 'calc geändert — neu rechnen' in t and 'Einfeldträger L=9m' in await pg.evaluate(f"{PJ}.pos[0].title"), t[:200])
        await pg.click('.pos a.warn'); await pg.wait_for_url('**/size.html?*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[+$('ho-L').value, $('ho-name').value]")
        check('„Neu rechnen“: size mit L = 9 m, Name bleibt', r==[9,'Deckenbalken D2'], r)
        await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(600)
        check('danach nicht mehr veraltet', 'neu rechnen' not in await pg.inner_text('.pos') and '0 veraltet' in await pg.inner_text('#sum'))
        # unveränderte Übernahme datiert nicht neu
        await pg.click('.pos a[href^="calc.html?pos="]'); await pg.wait_for_url('**/calc.html?pos=*'); await pg.wait_for_timeout(1200)
        await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(600)
        check('System unverändert übernommen: Nachweis bleibt aktuell', 'neu rechnen' not in await pg.inner_text('.pos'))
        # Rahmen: Stiel-Menü
        await pg.click('text=＋ Position'); await pg.wait_for_timeout(300)
        await pg.click('.pos >> nth=1 >> a.btn.p'); await pg.wait_for_url('**/calc.html?pos=*'); await pg.wait_for_timeout(1200)
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(600); await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(600)
        await pg.click('.pos >> nth=1 >> .addc > button'); await pg.wait_for_timeout(200)
        g=await pg.evaluate("[...document.querySelectorAll('.pos')[1].querySelectorAll('.addm-g')].map(e=>e.textContent)")
        check('Rahmen: Menü getrennt nach Riegel und Stiel', g==['Riegel','Stiel (der stärker gedrückte)'], g)
        await pg.click('.pos >> nth=1 >> .addm a[href*="beton.stuetze"]'); await pg.wait_for_url('**/size.html?*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[MAT, TYP, +$('su-N').value, 0, document.getElementById(nameField()).value]")
        check('Stiel als Stahlbetonstütze: N = 25 kN, Name „Stahlbeton · Stütze · Stiel“', r[:3]==['beton','stuetze',25] and r[4].endswith('· Stiel'), r)
        await pg.click('#k-pmbar [data-pm=x]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(500)
        check('„Abbrechen“ in size legt keinen Nachweis an', await pg.evaluate("JSON.parse(localStorage.getItem('statiq-size-positionen')).length")==1)
        # gelöschte Position
        await pg.goto(B+'calc.html?pos=gibtsnicht'); await pg.wait_for_timeout(1200)
        r=await pg.evaluate("[document.getElementById('k-pmbar').hidden, document.getElementById('k-pmbar').innerText]")
        check('unbekannte Position: Hinweis mit Link, kein Projektmodus', r[0]==False and 'gibt es nicht mehr' in r[1], r)
        # Sprache
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.goto(B+f'size.html?pos={pid}'); await pg.wait_for_timeout(1200)
        r=await pg.evaluate("document.getElementById('k-pmbar').innerText.replace(/\\s+/g,' ')")
        check('EN: Projektzeile übersetzt', 'Project · Pos. 1' in r and 'Apply and return' in r and 'Cancel' in r, r)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        # Handy 360
        m=await br.new_page(viewport={'width':360,'height':720}); m.on('pageerror', lambda e: errs.append(str(e)))
        for f in ['calc','size']:
            await m.goto(B+f+f'.html?pos={pid}'); await m.wait_for_timeout(1200)
            r=await m.evaluate("[document.documentElement.scrollWidth, Math.round(document.getElementById('k-pmbar').getBoundingClientRect().height)]")
            check(f'{f} 360 px: Projektzeile passt, kein Querscrollen', r[0]<=360 and r[1]<=140, r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
