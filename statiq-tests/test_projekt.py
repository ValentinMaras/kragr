# statiq·projekt v0.1.0 (mit calc v0.8.16, size v0.5.28): Positionsliste — Einträge aus calc und size zuordnen, size folgt seiner
# calc-Quelle, „veraltet“ bei neuerer calc-Berechnung, „Neu rechnen“ über size.html#pos=…&calc=…, Gesamtbericht, Projektdatei,
# Sprung in calc (#report=) und size (#pos=), Startseite, Sprachen. Ohne Playwright: SKIP.
import os, sys, re, json, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:160])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1250,'height':1000}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'projekt.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(200)
        check('leeres Projekt: Hinweis, keine Positionen', 'Noch nichts gespeichert' in await pg.inner_text('#list') and (await pg.inner_text('#sum')).startswith('0 Positionen'))
        # seit calc v0.10.1: System einer Position über den Projektmodus (calc.html?pos=…, „Übernehmen und zurück“); saveFrameCalc() legt wie früher eine lose Berechnung ab
        pid0=await pg.evaluate("addPos()")
        await pg.goto(B+f'calc.html?pos={pid0}'); await pg.wait_for_timeout(1200); await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*')
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(600)
        await pg.evaluate("showTab('frame'); calculateFrame(); saveFrameCalc();"); await pg.wait_for_timeout(20)
        k0='statiq_sdf_pos_'+pid0
        keys=[k0]+await pg.evaluate(f"Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_') && k!=='{k0}')")
        check('calc: Ordner-Symbol führt zur Projektübersicht, System in Pos. 1, Rahmen lose', await pg.get_attribute('#proj-btn','onclick')=='toggleProj(event)' and len(keys)==2 and await pg.evaluate(f"!!localStorage.getItem('{k0}')"), keys)
        # size: aus calc übernehmen und speichern
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(500)
        await pg.evaluate(f"setMat('stahl'); setStMode('traeger'); renderCalcImport('{keys[0]}'); importCalc('{keys[0]}'); $('sn-name').value='Pos 3 Unterzug'; savePos()"); await pg.wait_for_timeout(150)
        e=await pg.evaluate("posRead().find(p=>p.name==='Pos 3 Unterzug')")
        check('size: Position merkt sich calc-Quelle, Ausnutzung, Bezeichnung', e['src']['key']==keys[0] and 0<e['eta']<5 and e['label'], (e.get('src'), e.get('eta')))
        check('size: Bericht für den Gesamtbericht gespeichert', await pg.evaluate("(localStorage.getItem('statiq-size-bericht:Pos 3 Unterzug')||'').includes('Pos 3 Unterzug')"))
        check('size: Ordner-Symbol zur Projektübersicht', await pg.evaluate("!!document.getElementById('proj-btn')"))
        await pg.evaluate("setMat('holz'); setHoMode('bauteil'); $('ho-name').value='Pfette P1'; savePos()"); await pg.wait_for_timeout(100)
        check('size: andere Nachweisart übernimmt die calc-Quelle nicht', await pg.evaluate("!posRead().find(p=>p.name==='Pfette P1').src"))
        # Projekt: alles ohne Position
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(600)
        L=await pg.inner_text('#loose')
        check('Projekt: Rahmen und Pfette ohne Position', all(x in L for x in ['Rahmen','Pfette P1']) and 'Pos 3 Unterzug' not in L, L[:80])
        # seit projekt v0.1.14: calc-Berechnung mit ihrem size-Nachweis wird automatisch eine Position
        P=await pg.evaluate("proj()"); pid=P['pos'][0]['id']
        check('automatisch: eine Position „Einfeldträger L=5m“ für die calc-Berechnung mit ihrem Nachweis', len(P['pos'])==1 and P['pos'][0]['title']=='Einfeldträger L=5m' and P['asg'].get('c:'+keys[0])==pid, P['pos'])
        t=await pg.inner_text(f".pos[data-id='{pid}']")
        check('Position aus calc, Nachweis folgt seiner calc-Quelle', 'Einfeldträger L=5m' in t and 'Pos 3 Unterzug' in t and 'Pos 3 Unterzug' not in await pg.inner_text('#loose'), t[:120])
        check('Status „alle erfüllt“ und Vorschau des Systems', 'alle erfüllt' in t and await pg.evaluate(f"!!document.querySelector(\".pos[data-id='{pid}'] .thumb svg\")"))
        await pg.evaluate(f"assign('s:Pfette P1','{pid}')"); await pg.wait_for_timeout(80)
        check('size-Eintrag von Hand zuordnen', 'Pfette P1' in await pg.inner_text(f".pos[data-id='{pid}']"))
        await pg.evaluate(f"setPos('{pid}','title','Unterzug Achse B'); setPos('{pid}','nr','3')"); await pg.wait_for_timeout(50)
        check('Nr. und Bezeichnung ändern', await pg.evaluate(f"proj().pos[0].title==='Unterzug Achse B' && proj().pos[0].nr==='3'"))
        # neuere calc-Berechnung → veraltet (mit geänderter Steifigkeit: dieselbe Berechnung legt calc seit v0.8.28 nicht doppelt ab)
        await pg.goto(B+f'calc.html?pos={pid}'); await pg.wait_for_timeout(1000)
        await pg.evaluate("const e=document.getElementById('beam-Iy'); e.value='20'; e.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(400)
        await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(250)
        k2=keys[0]
        t=await pg.inner_text(f".pos[data-id='{pid}']")
        check('System der Position geändert: Nachweis „veraltet“ (neu rechnen), Titel bleibt (von Hand vergeben)', 'System geändert — neu rechnen' in t and '1 veraltet' in await pg.inner_text('#sum') and await pg.evaluate("proj().pos[0].title")=='Unterzug Achse B', t[:200])
        href=await pg.evaluate("document.querySelector('a.warn')?.getAttribute('href')")
        check('„Neu rechnen“ öffnet size im Projektmodus mit dem Nachweis', href==f'size.html?pos={pid}&check=Pos%203%20Unterzug&neu=1', href)
        await pg.goto(B+href); await pg.wait_for_timeout(1200); await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(200)
        check('size rechnet neu und speichert', await pg.evaluate(f"(()=>{{ const p=JSON.parse(localStorage.getItem('statiq-size-positionen')).find(p=>p.name==='Pos 3 Unterzug'); return p.src.key==='{k2}' && p.src.ts===JSON.parse(localStorage.getItem('{k2}')).sdf.timestamp }})()"))
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(250)
        tp=await pg.inner_text(f".pos[data-id='{pid}']"); check('danach nicht mehr veraltet', 'neu rechnen' not in tp and '0 veraltet' in await pg.inner_text('#sum'), tp)
        # Gesamtbericht
        await pg.evaluate("showReport()"); await pg.wait_for_timeout(150)
        r=await pg.inner_text('#report')
        check('Gesamtbericht: Übersicht, Position, System, Nachweis-Bericht', 'Positionsübersicht' in r.upper().title() or 'POSITIONSÜBERSICHT' in r.upper() and 'Pos. 3 — Unterzug Achse B' in r and 'System aus „Schnittkräfte“' in r and 'BIEGEDRILLKNICKEN' in r.upper())
        check('Gesamtbericht: nur der aktuelle Stand des Systems', r.count('System aus „Schnittkräfte“')==1, r.count('System aus „Schnittkräfte“'))
        check('Gesamtbericht: Auflagerkräfte mit Dezimalkomma', re.search(r'V\s*A\s*= 17,50 kN', r) is not None, re.findall(r'V.{0,6}= [\d.,]+ kN', r)[:2])
        await pg.evaluate("hideReport()")
        # Projektdatei: sichern (Inhalt) und laden
        data=await pg.evaluate("(()=>{ const P=proj(), calc={}; calcItems().forEach(c=>calc[c.key]={name:c.name,sdf:c.sdf}); return {statiq:'projekt', version:PROJ_VERSION, project:P, calc, size:JSON.parse(localStorage.getItem('statiq-size-positionen')), reports:{}}; })()")
        await pg.evaluate("localStorage.clear(); render()"); await pg.wait_for_timeout(50)
        n=await pg.evaluate(f"importData({json.dumps(data)})")
        check('Projektdatei laden stellt Positionen und Einträge wieder her', n>=4 and await pg.evaluate(f"proj().pos.length===1 && document.querySelector(\".pos[data-id='{pid}']\").textContent.includes('Pos 3 Unterzug')"), n)
        check('fremde Datei wird abgelehnt', await pg.evaluate("importData({foo:1})")==0)
        # Sprünge
        await pg.goto(B+f'calc.html#report={keys[1]}'); await pg.wait_for_timeout(500)
        check('calc.html#report= öffnet den Bericht', await pg.evaluate("document.getElementById('saved-report-view').style.display!=='none' && !document.getElementById('tab-saved').classList.contains('hidden')"))
        await pg.goto(B+'size.html#pos=Pfette%20P1'); await pg.wait_for_timeout(700)
        check('size.html#pos= lädt die Position', await pg.input_value('#ho-name')=='Pfette P1' and 'Pfette P1' in await pg.inner_text('#pos-msg'))
        # Position löschen (zweimal klicken)
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(600)
        await pg.click(f".pos[data-id='{pid}'] .pos-h .more-b"); await pg.click(f".pos[data-id='{pid}'] [data-del]"); await pg.click(f".pos[data-id='{pid}'] [data-del]"); await pg.wait_for_timeout(80)
        check('Position löschen: Einträge wieder „ohne Position“', await pg.evaluate("proj().pos.length")==0 and 'Pos 3 Unterzug' in await pg.inner_text('#loose'))
        # Startseite
        await pg.evaluate(f"addPos('Test')"); await pg.goto(B+'index.html'); await pg.wait_for_timeout(250)
        check('Startseite: Kachel „Projekt“ → projekt.html mit Zählern', await pg.evaluate("document.getElementById('saved-card').getAttribute('href')")=='projekt.html' and re.search(r'^1 (Position|item) · \d+ (Einträge|entries)$', await pg.inner_text('#saved-count')), await pg.inner_text('#saved-count'))
        # Einheitlich „Meine Projekte“ (seit projekt v0.1.1)
        await pg.goto(B+'projekt.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Projektseite: Navigation und Titel „Projekte“', await pg.inner_text('.app-header .cur')=='Projekte' and await pg.title()=='kragr — Projekte')
        await pg.goto(B+'index.html'); await pg.wait_for_timeout(200)
        check('Startseite: „Projekte“', await pg.inner_text('#saved-title')=='Projekte')
        for f in ['size','calc']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(500); tx=await pg.inner_text('#proj-btn')
            await pg.click('#k5-burger'); await pg.click('#k5-menu [data-mod=projekt]'); await pg.wait_for_url('**/projekt.html')
            check(f'{f}: Knopf „Projekte“ führt zur Projektseite', tx=='Projekte', tx)
        # Sprachen
        for L,w in (('en','Projects'),('fr','Projets'),('es','Proyectos')):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(200)
            tx=await pg.inner_text('body')
            g=re.findall(r'\b(Position löschen|Öffnen|Zuordnen|Gesamtbericht|Datei laden|ohne Position|nicht erfüllt|veraltet)\b', tx)
            check(f'{L}: Projektseite übersetzt, Menüknopf nennt „{w}“', not g and w in (await pg.evaluate("document.getElementById('k5-burger').getAttribute('aria-label')")), g[:3])   # k5: Seite im Menüknopf genannt
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
