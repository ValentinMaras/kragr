# Rechenblätter statt Projekte (calc v0.11.11 · size v0.7.9 · projekt v0.1.24): „Als Rechenblatt speichern“ unter den Ergebnissen
# in Schnittkräfte und Bemessung, Liste aller Rechenblätter in projekt.html (Bericht, Öffnen, Umbenennen, Löschen, Datei).
# Frühere Projekt-Daten (statiq_sdf_pos_*, zugeordnete Nachweise) werden nicht gezeigt (Entscheidung: verwerfen).
import os, sys, asyncio, re, json
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
src={p:open(os.path.join(BASE,p+'.html'),encoding='utf-8').read() for p in ['calc','size','projekt','index']}
check('Projektmodus entfernt (kein data-pm, keine Projektzeile)', not any(re.search(r'<(style|script) data-pm', s) or 'k-pmbar' in s for s in src.values()))
b={p:re.search(r'<script data-blatt>(.*?)</script>', src[p], re.S) for p in ['calc','size']}
check('gleicher Baustein <script data-blatt> in calc und size', all(b.values()) and b['calc'].group(1)==b['size'].group(1))
check('Menü heißt „Rechenblätter“ (4 Sprachen), Symbol Blatt', all(x in src['calc'] for x in ["proj:'Rechenblätter'","proj:'Calculation sheets'","proj:'Notes de calcul'","proj:'Memorias de cálculo'",'M6 3h8l4 4v14H6z']))
check('kein sichtbares „Projekte“ mehr im Menü-Baustein', "proj:'Projekte'" not in src['calc'] and "projS:'Schnittkräfte + Bemessung'" not in src['calc'])

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        r=await pg.evaluate("""()=>{const w=document.querySelector('#tab-beam .kbl'); return {par:w && w.parentNode.id, last:w===w.parentNode.lastElementChild, right:Math.round(innerWidth-w.querySelector('.kbl-btn').getBoundingClientRect().right), vis:!!(w && w.offsetParent), txt:w && w.querySelector('.kbl-btn').textContent,
            old:[...document.querySelectorAll('.col-out .save-btn')].some(e=>e.offsetParent)}}""")
        check('calc: Knopf „Als Rechenblatt speichern“ ganz unten im Bereich, rechts (v0.11.12)', r['par']=='tab-beam' and r['last'] and r['right']<=17 and r['vis'] and r['txt']=='Als Rechenblatt speichern', r)
        check('calc: alter Knopf „Berechnung speichern“ verborgen', not r['old'], r)
        # Einfeldträger, Startlasten F = 10 kN bei a = 2,5 m und q = 5 kN/m von 0 bis 5 m, jetzt L = 7 m:
        # A = 25·4,5/7 + 10·4,5/7 = 22,5 kN; Q = 22,5 − 5·2,5 = 10 → nach F genau 0, also max M unter F: 22,5·2,5 − 5·2,5²/2 = 40,625 kNm
        await pg.fill('#bL','7'); await pg.dispatch_event('#bL','input'); await pg.wait_for_timeout(500)
        await pg.click('#tab-beam .kbl-btn'); await pg.wait_for_timeout(100)
        d=await pg.input_value('#tab-beam .kbl-in')
        check('Vorschlag für den Namen aus dem System', d=='Einfeldträger L=7m', d)
        await pg.fill('#tab-beam .kbl-in','Pos. 2 Unterzug'); await pg.press('#tab-beam .kbl-in','Enter'); await pg.wait_for_timeout(250)
        m=await pg.text_content('#tab-beam .kbl-msg')
        check('Rückmeldung „Gespeichert“ mit Link zu den Rechenblättern', 'Gespeichert: „Pos. 2 Unterzug“' in m and await pg.get_attribute('#tab-beam .kbl-msg a','href')=='projekt.html', m)
        e=await pg.evaluate("""()=>{const k=Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_')); const o=JSON.parse(localStorage.getItem(k[0])); return {n:k.length, name:o.name, M:o.sdf.results.Mmax, draft:!!o.draft, L:o.draft&&o.draft.inputs.bL}}""")
        check('gespeichert: Name, M_max = 40,625 kNm und die Eingaben (L = 7)', e['n']==1 and e['name']=='Pos. 2 Unterzug' and abs(e['M']-40.625)<1e-6 and e['draft'] and e['L']=='7', e)
        # gleicher Name: erst nachfragen, dann überschreiben (kein zweiter Eintrag)
        await pg.click('#tab-beam .kbl-btn'); await pg.fill('#tab-beam .kbl-in','Pos. 2 Unterzug'); await pg.click('#tab-beam .kbl-ok')
        a=await pg.text_content('#tab-beam .kbl-ok'); await pg.click('#tab-beam .kbl-ok'); await pg.wait_for_timeout(200)
        n=await pg.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_')).length")
        check('gleicher Name: „Überschreiben?“, dann ersetzt (1 Eintrag)', a=='Überschreiben?' and n==1 and 'Überschrieben' in await pg.text_content('#tab-beam .kbl-msg'), (a,n))
        # Abbrechen mit Escape
        await pg.click('#tab-beam .kbl-btn'); await pg.press('#tab-beam .kbl-in','Escape')
        check('Escape schließt das Namensfeld', await pg.evaluate("document.querySelector('#tab-beam .kbl-form').hidden && !document.querySelector('#tab-beam .kbl-btn').hidden"))
        # Sprache in calc ohne Neuladen
        await pg.evaluate("setCalcLang('en')"); t=await pg.text_content('#tab-beam .kbl-btn'); await pg.evaluate("setCalcLang('de')")
        check('calc: Sprache wechselt den Knopftext mit (EN)', t=='Save as calculation sheet', t)
        # size
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(900)
        r=await pg.evaluate("()=>{const w=document.querySelector('.kbl'), b=w.querySelector('.kbl-btn').getBoundingClientRect(); return {vis:!!(w&&w.offsetParent), rep:w.parentNode.matches('main') && w===w.parentNode.lastElementChild, right:Math.round(innerWidth-b.right)}}")
        check('size: Knopf ganz unten auf der Seite, rechts', r['vis'] and r['rep'] and r['right']<=17, r)
        await pg.click('.kbl-btn'); await pg.fill('.kbl-in','Unterzug Beton'); await pg.click('.kbl-ok'); await pg.wait_for_timeout(400)
        e=await pg.evaluate("()=>{const L=JSON.parse(localStorage.getItem('statiq-size-positionen')||'[]'); return {n:L.length, name:L[0]&&L[0].name, rep:(localStorage.getItem('statiq-size-bericht:Unterzug Beton')||'').length}}")
        check('size: Nachweis und Bericht gespeichert', e['n']==1 and e['name']=='Unterzug Beton' and e['rep']>500, e)
        # Daten aus früheren Projekten: nicht zeigen
        await pg.evaluate("""()=>{ localStorage.setItem('statiq_sdf_pos_alt', JSON.stringify({name:'Projektsystem', sdf:{module:'calc', timestamp:'2026-10-01T10:00:00Z', system:{type:'beam'}, results:{Mmax:1,Qmax:1,Nmax:0}}}));
            localStorage.setItem('statiq-projekt', JSON.stringify({pos:[{id:'alt',nr:'1',title:'A'}], asg:{'s:Projektnachweis':'alt'}}));
            const L=JSON.parse(localStorage.getItem('statiq-size-positionen')); L.push({name:'Projektnachweis', typ:'balken', ok:true, date:'2026-10-01T10:00:00Z', data:{}}); localStorage.setItem('statiq-size-positionen', JSON.stringify(L)); }""")
        # Liste
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(600)
        L=await pg.evaluate("[...document.querySelectorAll('.bl')].map(b=>[b.querySelector('.bl-name').textContent, b.querySelector('.tag').textContent])")
        check('Liste: neueste oben, beide Module, Projekt-Daten verborgen', L==[['Unterzug Beton','Bemessung'],['Pos. 2 Unterzug','Schnittkräfte']], L)
        check('Kopf: „Rechenblätter“ · „2 Rechenblätter“, Seitentitel', await pg.text_content('h1.ptitle')=='Rechenblätter' and await pg.text_content('#sum')=='2 Rechenblätter' and await pg.title()=='Rechenblätter — kragr')
        res=await pg.evaluate("document.querySelectorAll('.bl')[1].querySelector('.bl-res').textContent")
        check('calc-Eintrag zeigt M_max = 40,63 kNm und Q_max = 22,50 kN', 'Mmax = 40,63 kNm' in res and 'Qmax = 22,50 kN' in res, res)
        await pg.click('#filt button[data-f="s"]'); f=await pg.evaluate("[...document.querySelectorAll('.bl-name')].map(e=>e.textContent)")
        await pg.reload(); await pg.wait_for_timeout(300); f2=await pg.evaluate("[...document.querySelectorAll('.bl-name')].map(e=>e.textContent)")
        check('Filter „Bemessung“, bleibt nach Neuladen', f==['Unterzug Beton'] and f2==f, (f,f2))
        await pg.click('#filt button[data-f="all"]')
        # Menü
        await pg.click('#k5-burger'); await pg.wait_for_selector('#k5-menu.open')
        mi=await pg.evaluate("()=>{const a=document.querySelector('#k5-menu [data-mod=projekt]'); return {t:a.querySelector('b').textContent, s:a.querySelector('.k5-mt > span').textContent, cur:a.getAttribute('aria-current')}}")
        check('Menü: „Rechenblätter“ · „Gespeichert · als PDF drucken“, aktuelle Seite', mi=={'t':'Rechenblätter','s':'Gespeichert · als PDF drucken','cur':'page'}, mi)
        await pg.keyboard.press('Escape')
        # size-Bericht in der Seite
        await pg.click('.bl:first-child button.p'); await pg.wait_for_timeout(200)
        r=await pg.evaluate("({on:document.body.classList.contains('show-report'), t:document.getElementById('rep-title').textContent, n:document.getElementById('report').innerHTML.length})")
        check('Bericht (Bemessung) in der Seite, mit Titel, Drucken möglich', r['on'] and r['t']=='Unterzug Beton' and r['n']>500, r)
        await pg.click('#report-view button:has-text("Zurück")')
        # calc-Bericht: über calc, Zurück führt hierher
        await pg.click('.bl:nth-child(2) button.p'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("({rv:getComputedStyle(document.getElementById('saved-report-view')).display, vis:!!document.getElementById('saved-report-view').offsetParent, t:document.getElementById('report-title-bar').textContent, txt:document.getElementById('report-content').textContent})")
        check('Bericht (Schnittkräfte) öffnet in calc, sichtbar, mit M = 40,63', r['vis'] and r['t']=='Pos. 2 Unterzug' and ('40,63' in r['txt'] or '40.63' in r['txt']), {k:v for k,v in r.items() if k!='txt'})
        await pg.click('#saved-report-view button[onclick="closeReport()"]'); await pg.wait_for_timeout(600)
        check('„←“ im calc-Bericht führt zurück zu den Rechenblättern', pg.url.endswith('projekt.html'), pg.url)
        # Öffnen (calc): Eingaben kommen zurück
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(500); await pg.fill('#bL','4'); await pg.dispatch_event('#bL','input'); await pg.wait_for_timeout(900)
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(400)
        await pg.click('.bl:nth-child(2) a.btn'); await pg.wait_for_timeout(1200)
        r=await pg.evaluate("({L:document.getElementById('bL').value, h:location.hash, m:document.querySelector('#tab-beam .kbl-msg').textContent})")
        check('Öffnen (Schnittkräfte): L = 7 m wieder da, Hinweis „geöffnet“', r['L']=='7' and r['h']=='' and 'geöffnet' in r['m'], r)
        # Öffnen (size)
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(500); await pg.evaluate("document.getElementById(nameField()).value='anders'")
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(400)
        await pg.click('.bl:first-child a.btn'); await pg.wait_for_timeout(1200)
        r=await pg.evaluate("({n:document.getElementById(nameField()).value, h:location.hash})")
        check('Öffnen (Bemessung): Nachweis geladen', r['n']=='Unterzug Beton' and r['h']=='', r)
        # Umbenennen, Löschen
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(400)
        await pg.click('.bl:first-child .more-b'); await pg.click('.bl:first-child .morem button:has-text("Umbenennen")')
        await pg.fill('.bl-name input','Unterzug Pos. 3'); await pg.press('.bl-name input','Enter'); await pg.wait_for_timeout(200)
        r=await pg.evaluate("({n:document.querySelector('.bl-name').textContent, rep:!!localStorage.getItem('statiq-size-bericht:Unterzug Pos. 3'), old:!!localStorage.getItem('statiq-size-bericht:Unterzug Beton')})")
        check('Umbenennen (Bemessung): Name und Bericht ziehen mit', r=={'n':'Unterzug Pos. 3','rep':True,'old':False}, r)
        await pg.click('.bl:nth-child(2) .more-b'); await pg.click('.bl:nth-child(2) .morem button:has-text("Umbenennen")')
        await pg.fill('.bl-name input','Unterzug Achse B'); await pg.press('.bl-name input','Escape'); await pg.wait_for_timeout(100)
        check('Umbenennen abbrechen mit Escape', await pg.evaluate("document.querySelectorAll('.bl-name')[1].textContent")=='Pos. 2 Unterzug')
        await pg.click('.bl:nth-child(2) .more-b'); d=pg.locator('.bl:nth-child(2) .morem .danger'); await d.click(); a=await d.text_content(); await d.click(); await pg.wait_for_timeout(200)
        r=await pg.evaluate("({n:document.querySelectorAll('.bl').length, k:Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_')&&!k.startsWith('statiq_sdf_pos_')).length, pos:!!localStorage.getItem('statiq_sdf_pos_alt')})")
        check('Löschen erst nach „Wirklich löschen?“; frühere Projekt-Daten bleiben unberührt', a=='Wirklich löschen?' and r=={'n':1,'k':0,'pos':True}, (a,r))
        # Datei: Export und Import
        async with pg.expect_download() as dl: await pg.click('button[data-t="export"]')
        f=await (await dl.value).path(); d=json.load(open(f,encoding='utf-8'))
        check('Datei: kragr-rechenblaetter, ohne Projekt-Daten', d.get('kragr')=='rechenblaetter' and [s['name'] for s in d['size']]==['Unterzug Pos. 3'] and not d['calc'] and 'Unterzug Pos. 3' in d['reports'], [s['name'] for s in d['size']])
        await pg.evaluate("localStorage.removeItem('statiq-size-positionen')"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.set_input_files('input[type=file]', f); await pg.wait_for_timeout(400)
        check('Datei laden stellt die Rechenblätter wieder her', await pg.evaluate("[...document.querySelectorAll('.bl-name')].map(e=>e.textContent)")==['Unterzug Pos. 3'])
        # leer
        await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(300)
        r=await pg.evaluate("({e:document.querySelector('.empty')&&document.querySelector('.empty').textContent, f:document.getElementById('filt').hidden, links:[...document.querySelectorAll('.empty a')].map(a=>a.getAttribute('href'))})")
        check('leer: Hinweis „Als Rechenblatt speichern“ und Links zu beiden Modulen', 'Als Rechenblatt speichern' in r['e'] and r['f'] and r['links']==['calc.html','size.html'], r)
        # Sprachen
        for l,h,btn in [('en','Calculation sheets','Save as calculation sheet'),('fr','Notes de calcul','Enregistrer comme note de calcul'),('es','Memorias de cálculo','Guardar como memoria de cálculo')]:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{l}')"); await pg.reload(); await pg.wait_for_timeout(300)
            a=await pg.text_content('h1.ptitle'); await pg.goto(B+'size.html'); await pg.wait_for_timeout(600); b2=await pg.text_content('.kbl-btn'); await pg.goto(B+'projekt.html')
            check(f'{l}: Seite „{h}“, Knopf „{btn}“', a==h and b2==btn, (a,b2))
        # Startseite
        await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.goto(B+'index.html'); await pg.wait_for_timeout(500)
        r=await pg.evaluate("({t:document.getElementById('saved-title').textContent, c:document.getElementById('saved-count').textContent})")
        check('Startseite: Kachel „Rechenblätter“', r['t']=='Rechenblätter', r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
