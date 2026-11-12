# statiq·size: Bedienung — Auswahlmenü, Projekt-Menü, aufklappbare Karten und Nachweise. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
MODES={'beton':('TYP',['balken','unterzug','platte','stuetze','durchstanzen']),'stahl':('STMODE',['traeger','anschluss','fuss','schweiss']),'holz':('HOMODE',['bauteil','verbindung']),
       'mauer':('MWMODE',['druck','teil','keller','schub']),'grund':('GRMODE',['flach','setzung','wand','upl']),'wasser':('WBMODE',['druck','schwimm','rohr','gerinne','wehr'])}
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(300)
        check('Alte Leisten ausgeblendet, Auswahlknopf sichtbar', await pg.evaluate("getComputedStyle($('seg-mat')).display==='none' && getComputedStyle($('seg-typ')).display==='none'") and await pg.is_visible('#pick-btn'))
        n=await pg.evaluate("document.querySelectorAll('.pick-item').length"); await pg.click('#pick-btn')
        n=await pg.evaluate("document.querySelectorAll('.pick-item').length")
        check('Menü zeigt alle 59 Nachweise in 7 Bereichen (seit size v0.7.34 mit Laschenstoß)', n==59 and await pg.evaluate("document.querySelectorAll('.pick-group').length")==7, n)
        bad=[]
        for mat,(var,ms) in MODES.items():
            for i,m in enumerate(ms):
                if not await pg.is_visible('#pick-menu'): await pg.click('#pick-btn')
                if not await pg.is_visible(f'.pick-item[data-mat="{mat}"][data-i="{i}"]'): await pg.click(f'.pick-group[data-mat="{mat}"] .pick-head')
                await pg.click(f'.pick-item[data-mat="{mat}"][data-i="{i}"]'); await pg.wait_for_timeout(60)
                st=await pg.evaluate(f"[MAT, {var}, $('pick-t').textContent, document.querySelector('#summary').innerText, $('pick').classList.contains('open')]")
                if st[0]!=mat or st[1]!=m or not st[2] or not st[3] or st[4]: bad.append((mat,m,st))
        check('Jeder Menüpunkt stellt Bereich und Nachweis ein, Menü schließt', not bad, bad[:2])
        # Zu Beginn nur der aktuelle Bereich offen; weitere Bereiche bleiben aufgeklappt, bis man sie schließt
        await pg.evaluate("localStorage.removeItem('kragr-pick-open-size'); setMat('holz'); setHoMode('versatz')"); await pg.click('#pick-btn')
        st=await pg.evaluate("[[...document.querySelectorAll('.pick-group.open')].map(g=>g.dataset.mat), document.querySelectorAll('.pick-item').length - [...document.querySelectorAll('.pick-item')].filter(b=>b.offsetParent).length]")
        check('Anfangs nur der aktuelle Bereich (Holz) offen, übrige Listen zu', st[0]==['holz'] and st[1]==48, st)
        await pg.click('.pick-group[data-mat="grund"] .pick-head')
        st=await pg.evaluate("[[...document.querySelectorAll('.pick-group.open')].map(g=>g.dataset.mat), $('pick').classList.contains('open'), MAT]")
        check('Klick auf Bereichskopf klappt ihn auf, Holz bleibt offen, Menü offen, Auswahl unverändert', st==[['holz','grund'],True,'holz'], st)
        await pg.keyboard.press('Escape'); await pg.click('#pick-btn')
        check('Menü wieder öffnen: Grundbau bleibt aufgeklappt', await pg.evaluate("[...document.querySelectorAll('.pick-group.open')].map(g=>g.dataset.mat)")==['holz','grund'])
        await pg.click('.pick-group[data-mat="grund"] .pick-head')
        check('Erneuter Klick schließt nur diesen Bereich', await pg.evaluate("[...document.querySelectorAll('.pick-group.open')].map(g=>g.dataset.mat)")==['holz'])
        await pg.keyboard.press('Escape')
        await pg.click('#pick-btn'); await pg.mouse.click(1200,850); check('Klick daneben schließt das Menü', not await pg.evaluate("$('pick').classList.contains('open')"))
        await pg.click('#pick-btn'); await pg.keyboard.press('Escape'); check('Escape schließt das Menü', not await pg.evaluate("$('pick').classList.contains('open')"))
        # Projekt-Menü
        check('Kopfzeile: Ordner-Symbol ohne Menü, altes Projekt-Fenster verborgen', await pg.evaluate("$('proj-panel').hidden && !$('proj-btn').hasAttribute('aria-haspopup')"))
        await pg.click('#k5-burger'); await pg.click('#k5-menu [data-mod=projekt]'); await pg.wait_for_url('**/projekt.html'); check('Ordner-Symbol öffnet „Meine Projekte“', 'projekt.html' in pg.url); await pg.go_back(); await pg.wait_for_timeout(500)
        # Aufklappbare Karten
        await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.wait_for_timeout(100)
        st=await pg.evaluate("[...document.querySelectorAll('.fold')].filter(c=>c.offsetParent).map(c=>[c.dataset.fold, c.classList.contains('closed'), c.querySelector('.fold-sum').textContent])")
        d={k:(c,t) for k,c,t in st}
        # seit size v0.7.44: am Rechner (zweispaltig) sind alle Eingabekarten offen und schließen sich nicht gegenseitig
        check('Rechner: alle Eingabekarten offen', d and not any(c for c,_ in d.values()), st)
        OPEN="[...document.querySelectorAll('.col-in .card.fold')].filter(c=>c.offsetParent).map(c=>!c.classList.contains('closed'))"
        await pg.click('.fold[data-fold="in-beton"] > .card-title'); await pg.wait_for_timeout(150)
        o=await pg.evaluate(OPEN); bz=await pg.evaluate("document.querySelector('.fold[data-fold=\"in-beton\"]').classList.contains('closed')")
        check('Klick auf den Titel klappt nur diese Karte zu, die anderen bleiben offen', bz and sum(o)==len(o)-1, o)
        await pg.evaluate("$('in-beton').value='C35/45'; run()")
        check('Kurzfassung folgt den Eingaben', 'C35/45' in await pg.inner_text('.fold[data-fold="in-beton"] .fold-sum'))
        await pg.click('.fold[data-fold="in-beton"] > .card-title'); await pg.wait_for_timeout(150)
        check('erneuter Klick klappt wieder auf, nichts anderes schließt sich', all(await pg.evaluate(OPEN)))
        await pg.evaluate("setTyp('platte')"); await pg.wait_for_timeout(200); o=await pg.evaluate(OPEN)
        check('Wechsel des Nachweises: weiter alle offen', o and all(o), o)
        await pg.evaluate("setTyp('balken')"); await pg.reload(); await pg.wait_for_timeout(400); o=await pg.evaluate(OPEN)
        check('nach Neuladen: alle offen', o and all(o), o)
        # Handy (einspaltig): Akkordeon wie bisher — nach dem Laden nur die erste Karte offen, Öffnen einer anderen schließt die erste
        await pg.set_viewport_size({'width':390,'height':844}); await pg.reload(); await pg.wait_for_timeout(500); o=await pg.evaluate(OPEN)
        check('Handy: nach Neuladen nur die erste Karte offen', o and o[0] and not any(o[1:]), o)
        await pg.click('.fold[data-fold="in-beton"] > .card-title'); await pg.wait_for_timeout(200); o=await pg.evaluate(OPEN)
        check('Handy: andere Karte öffnen schließt die erste', sum(o)==1 and not o[0], o)
        await pg.set_viewport_size({'width':1280,'height':900}); await pg.reload(); await pg.wait_for_timeout(500)
        # Nachweisdetails
        await pg.evaluate("$('in-h').value=30; $('in-M').value=600; run()"); await pg.wait_for_timeout(100)
        st=await pg.evaluate("[...document.querySelectorAll('#details .dfold')].map(c=>[c.id, c.classList.contains('closed'), !!c.querySelector('.card-title .tag.bad')])")
        check('Nicht erfüllte Nachweise offen, erfüllte zu', all(cl==(not b) for _,cl,b in st) and any(b for *_,b in st), st[:3])
        await pg.click('.det-bar .det-all'); check('„Alle aufklappen“', await pg.evaluate("[...document.querySelectorAll('#details .dfold')].every(c=>!c.classList.contains('closed'))"))
        await pg.click('.det-bar .det-all'); await pg.evaluate("$('in-h').value=60; $('in-M').value=220; run()")
        await pg.click('#chk-table a[href="#n-quer"]') if await pg.evaluate("!!document.querySelector('#chk-table a[href=\"#n-quer\"]')") else None
        check('Klick in der Ergebnisliste öffnet den Nachweis', await pg.evaluate("!document.getElementById('n-quer') || !document.getElementById('n-quer').classList.contains('closed')"))
        await pg.evaluate("run()"); check('Geöffneter Nachweis bleibt bei neuer Rechnung offen', await pg.evaluate("!document.getElementById('n-quer') || !document.getElementById('n-quer').classList.contains('closed')"))
        await pg.evaluate("showReport()"); r=await pg.inner_text('#report')
        check('Bericht enthält weiter alle Rechenschritte', 'Querkraft' in r and 'Rissbreite' in r)
        # Handy
        m=await br.new_page(viewport={'width':390,'height':844}); await m.goto(HTML); await m.wait_for_timeout(300)
        w=await m.evaluate("document.documentElement.scrollWidth"); await m.click('#pick-btn')
        check('Handy: keine seitliche Überbreite, Menü einspaltig', w<=390 and await m.evaluate("getComputedStyle($('pick-menu')).gridTemplateColumns.split(' ').length")==1, w)
        bb=await m.evaluate("JSON.stringify($('proj-btn').getBoundingClientRect())")
        check('Handy: Ordner-Symbol passt auf den Bildschirm', await m.evaluate("$('proj-btn').getBoundingClientRect().right<=390"), bb)
        # Rechenschritte: Rechenketten in Einzelzeilen, „=“ untereinander
        await pg.set_viewport_size({'width':1280,'height':900}); await pg.evaluate("setMat('beton'); setTyp('balken')")
        g=await pg.evaluate("(()=>{ const c=document.getElementById('n-biegung'); const eq=[...c.querySelectorAll('.eq')].find(e=>e.textContent.startsWith('μ')); return eq ? [...eq.querySelectorAll('.eq-r')].map(r=>r.textContent.trim()[0]) : null; })()")
        check('Rechenschritte: μ-Kette in drei Zeilen, jede beginnt mit „=“', g is not None and len(g)>=3 and all(x=='=' for x in g[:3]), g)
        g=await pg.evaluate("[eqLine('F1 = 10 kN bei x = 2,5 m'), eqLine('f<sub>v,d</sub> = 2,15 · f<sub>c,0,d</sub> = 14,8 N/mm²')]")
        check('Sätze und Aufzählungen bleiben einzeilig', g==[None,None], g)
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
