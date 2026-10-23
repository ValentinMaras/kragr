# „Position als roter Faden“ (calc v0.10.0 · size v0.7.0 · projekt v0.1.16): alles gehört zu einer Position; Kopfzeile zeigt sie,
# Leiste „System · Nachweise“ darunter; calc sichert das System automatisch in der Position, size jeden Nachweis der Position;
# „＋ Neue Position“ beginnt mit Startwerten; Wechsel der Position lädt deren System bzw. Nachweise; Karte „Nachweise dieser
# Position“ in size mit „In Pos. N aufnehmen“ und „＋ Nachweis aus dem System“; geändertes System → „neu rechnen“ mit einem Tipp;
# „Meine Projekte“ als Übersicht mit „① System“/„② Nachweise“ und Markierung der aktuellen Position. Ohne Playwright: SKIP.
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
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1800)
        r=await pg.evaluate(f"[{PJ}, document.getElementById('k-posbar').innerText.replace(/\\s+/g,' '), document.querySelector('#proj-btn .pb-tx').textContent, !!localStorage.getItem(mulyPos.sysKey(mulyPos.cur().id))]")
        check('Start: Pos. 1 entsteht von selbst, Titel aus dem System, System gesichert', len(r[0]['pos'])==1 and r[0]['pos'][0]['title']=='Einfeldträger L=5m' and r[3], r[0])
        check('Leiste „Pos. 1 · Titel · System · Nachweise 0“, Knopf „Pos. 1 · Titel“', r[1].startswith('Pos. 1 Einfeldträger L=5m') and 'System' in r[1] and 'Nachweise 0' in r[1] and r[2]=='Pos. 1 · Einfeldträger L=5m', r[1:3])
        check('kein „Speichern“, kein Punkt, keine Ansicht „Gespeichert“ im Menü', await pg.evaluate("getComputedStyle(document.querySelector('#proj-btn .pb-dot')).display==='none' && document.getElementById('proj-panel').hidden && ![...document.querySelectorAll('.pick-item')].some(i=>i.dataset.k==='saved' && i.offsetParent)"))
        # Änderung → Titel und System folgen
        await pg.evaluate("const e=document.getElementById('bL'); e.value='6'; e.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(1800)
        r=await pg.evaluate(f"[{PJ}.pos[0].title, JSON.parse(localStorage.getItem(mulyPos.sysKey(mulyPos.cur().id))).sdf.system.geometry]")
        check('Stützweite 6 m: automatisch gesichert, Titel „Einfeldträger L=6m“', r[0]=='Einfeldträger L=6m', r)
        # Nachweis in size → gehört zur Position
        await pg.click('#tab-beam .k-tosize'); await pg.click('#tab-beam .k-tsm-i[data-ziel="holz.bauteil"]'); await pg.wait_for_url('**/size.html*'); await pg.wait_for_timeout(1800)
        r=await pg.evaluate("[document.getElementById('k-posbar').innerText.replace(/\\s+/g,' '), document.getElementById('k-poscard').innerText, document.querySelector('#ci-banner .cib-s')?.innerText]")
        check('size: Nachweis in Pos. 1, Leiste „Nachweise 1“, Karte zeigt ihn', 'Nachweise 1' in r[0] and 'Einfeldträger L=6m — Holz · Träger / Stütze' in r[1] and 'Automatisch in Pos. 1 gespeichert' in (r[2] or ''), r)
        # Autosave in size
        await pg.fill('#ho-N','30'); await pg.dispatch_event('#ho-N','input'); await pg.wait_for_timeout(1600)
        r=await pg.evaluate("posRead().map(p=>[p.name, p.data['ho-N']])")
        check('size: Änderung wird ohne Knopf in den Nachweis gesichert', r==[['Einfeldträger L=6m — Holz · Träger / Stütze','30']], r)
        # anderer Nachweis: erst durchsehen, dann aufnehmen
        await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[posRead().length, document.querySelector('#k-poscard .kpc-take')?.innerText]")
        check('Durchsehen legt nichts an; Karte bietet „In Pos. 1 aufnehmen“', r==[1,'In Pos. 1 aufnehmen'], r)
        await pg.click('#k-poscard .kpc-take'); await pg.wait_for_timeout(600)
        r=await pg.evaluate("[posRead().map(p=>p.name), mulyPos.checks(mulyPos.cur().id).length]")
        check('aufgenommen: Name aus dem Nachweis statt „Pos. 1 — Balken“, zwei Nachweise', r[1]==2 and 'Stahlbeton · Balken' in r[0] and not any(n.startswith('Pos. ') for n in r[0]), r)
        # Nachweis aus dem System (Menü in der Karte)
        await pg.click('#k-poscard .kpc-add'); await pg.wait_for_timeout(200)
        zs=await pg.evaluate("[...document.querySelectorAll('#k-poscard .kpc-menu button')].map(b=>b.dataset.ziel)")
        check('„＋ Nachweis aus dem System“: nur passende Nachweise für den Einfeldträger', zs==['beton.balken','beton.unterzug','beton.platte','stahl.traeger','holz.bauteil'], zs)
        await pg.click('#k-poscard .kpc-menu button[data-ziel="stahl.traeger"]'); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[MAT, STMODE, mulyPos.checks(mulyPos.cur().id).length, +$('sn-M').value]")
        check('Stahlträger aus dem System: M übernommen, dritter Nachweis der Position', r[:3]==['stahl','traeger',3] and abs(r[3]-35.42)<0.05, r)
        # Nachweis der Position wieder öffnen
        await pg.click('#k-poscard [data-load^="Einfeldträger L=6m — Holz"]'); await pg.wait_for_timeout(600)
        check('Tipp auf einen Nachweis lädt ihn', await pg.evaluate("[MAT, $('ho-N').value]")==['holz','30'])
        # neue Position aus size
        await pg.click('#proj-btn'); await pg.wait_for_timeout(200); await pg.click('#pos-panel .kp-add'); await pg.wait_for_timeout(1800)
        r=await pg.evaluate(f"[mulyPos.cur().nr, MAT, $('ho-N').value, document.getElementById('k-poscard').innerText, {PJ}.pos.length]")
        check('size „＋ Neue Position“: Pos. 2, gleicher Nachweis mit Startwerten, noch leer', r[0]=='2' and r[1]=='holz' and r[2]!='30' and 'Noch kein Nachweis' in r[3] and r[4]==2, r)
        # Schritt ① System in Pos. 2: Startwerte, Rahmen
        await pg.click('#k-posbar a >> nth=0'); await pg.wait_for_url('**/calc.html*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[curTab(), document.getElementById('bL').value, mulyPos.cur().nr]")
        check('① System in Pos. 2: calc mit Startwerten', r==['beam','5','2'], r)
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(1800)
        r=await pg.evaluate(f"[{PJ}.pos.map(q=>q.title), JSON.parse(localStorage.getItem(mulyPos.sysKey({PJ}.pos[0].id))).sdf.system.type]")
        check('Pos. 2 wird Rahmen, Pos. 1 bleibt Einfeldträger', r[0][1].startswith('Rahmen') and r[0][0]=='Einfeldträger L=6m' and r[1]=='beam', r)
        # Wechsel zurück zu Pos. 1
        await pg.click('#proj-btn'); await pg.wait_for_timeout(200); await pg.click('#pos-panel [data-pos] >> nth=0'); await pg.wait_for_timeout(1800)
        r=await pg.evaluate("[mulyPos.cur().nr, curTab(), document.getElementById('bL').value, document.querySelector('#pos-panel .kp-st')?.textContent]")
        check('Wechsel zu Pos. 1: Einfeldträger mit L = 6 m wieder da', r[:3]==['1','beam','6'], r)
        # System ändern → neu rechnen
        await pg.evaluate("const e=document.getElementById('bL'); e.value='7'; e.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(1800)
        await pg.click('#proj-btn'); await pg.wait_for_timeout(200)
        st=await pg.inner_text('#pos-panel .kp-item.cur .kp-st')
        check('geändertes System: Position zeigt „neu rechnen“', st=='neu rechnen', st)
        await pg.keyboard.press('Escape'); await pg.click('#k-posbar a >> nth=1'); await pg.wait_for_url('**/size.html*'); await pg.wait_for_timeout(1500)
        n=await pg.evaluate("document.querySelectorAll('#k-poscard [data-stale]').length")
        await pg.click('#k-poscard [data-stale] >> nth=0'); await pg.wait_for_timeout(2000)
        r=await pg.evaluate("[document.querySelectorAll('#k-poscard [data-stale]').length, MAT, +$('ho-L').value]")
        check('size: die zwei Nachweise aus dem System sind markiert, ein Tipp rechnet mit L = 7 m neu', n==2 and r==[1,'holz',7], (n, r))
        # Meine Projekte
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(800)
        r=await pg.evaluate("[document.querySelector('.pos.cur')?.dataset.id===proj().cur, document.querySelectorAll('.pos-go a').length, document.querySelector('.pos.cur .tag.cur')?.textContent]")
        check('Meine Projekte: aktuelle Position markiert, je Position „① System“ und „② Nachweise“', r==[True,4,'aktuell'], r)
        await pg.click('.pos:not(.cur) .pos-go a >> nth=1'); await pg.wait_for_url('**/size.html*'); await pg.wait_for_timeout(1500)
        check('„② Nachweise“ einer anderen Position: size öffnet in dieser Position', await pg.evaluate("mulyPos.cur().nr")=='2')
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(600); await pg.click('.pos:not(.cur) .pos-go a >> nth=0'); await pg.wait_for_url('**/calc.html*'); await pg.wait_for_timeout(1500)
        check('„① System“: calc öffnet in dieser Position', await pg.evaluate("[mulyPos.cur().nr, curTab()]")==['1','beam'])
        # Sprache: Leiste und Karte übersetzt
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.goto(B+'size.html'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[document.getElementById('k-posbar').innerText.replace(/\\s+/g,' '), document.querySelector('#k-poscard .kpc-h').textContent]")
        check('EN: Leiste „System · Checks“, Karte „Checks of this item“', 'Checks' in r[0] and r[1]=='Checks of this item', r)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        # Handy 360: Leiste ohne Querscrollen
        m=await br.new_page(viewport={'width':360,'height':720}); m.on('pageerror', lambda e: errs.append(str(e)))
        for f in ['calc','size']:
            await m.goto(B+f+'.html'); await m.wait_for_timeout(1200)
            r=await m.evaluate("[document.documentElement.scrollWidth, Math.round(document.getElementById('k-posbar').getBoundingClientRect().height)]")
            check(f'{f} 360 px: Positionsleiste passt, kein Querscrollen', r[0]<=360 and r[1]<=110, r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
