# Veröffentlichung: Rechtsseite (DE/EN/FR/ES), Haftungshinweis und Link auf allen Seiten, Hinweis im Bericht,
# Schriften lokal (keine Anfrage an fremde Server), Normtabellen in ref als gekennzeichneter Auszug.
import os, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
PAGES=['index.html','calc.html','size.html','ref.html','projekt.html','rechtliches.html']

async def main():
    # Schriften: Dateien vorhanden, CSS verweist nur auf vorhandene Dateien, keine Google-Links mehr
    css=open(os.path.join(BASE,'fonts','fonts.css'),encoding='utf-8').read()
    files=re.findall(r'url\(([^)]+)\)',css)
    check(f'fonts.css: {len(files)} Schriftdateien vorhanden', files and all(os.path.exists(os.path.join(BASE,'fonts',f)) for f in files), [f for f in files if not os.path.exists(os.path.join(BASE,'fonts',f))])
    check('Lizenztexte der Schriften (OFL) liegen bei', all(os.path.exists(os.path.join(BASE,'fonts',f'LICENSE-{n}.txt')) for n in ['Figtree','JetBrainsMono','Inter']))
    srcs={p:open(os.path.join(BASE,p),encoding='utf-8').read() for p in PAGES}
    check('kein Verweis auf fonts.googleapis.com / gstatic in allen Seiten', not any(('googleapis' in t or 'gstatic' in t) for t in srcs.values()), [p for p,t in srcs.items() if 'googleapis' in t])
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); ext=[]; errs=[]
        pg.on('request', lambda r: ext.append(r.url) if not r.url.startswith(('file:','data:','blob:','about:')) else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        for lang,disc,link in [('de','ersetzt keine geprüfte statische Berechnung','Impressum'),('en','does not replace a checked structural calculation','Legal notice'),
                               ('fr','ne remplace pas une note de calcul contrôlée','Mentions légales'),('es','no sustituye un cálculo estructural revisado','Aviso legal')]:
            await pg.goto(U+'index.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')")
            bad=[]
            for page in PAGES[:5]:
                await pg.goto(U+page); await pg.wait_for_timeout(350)
                t=await pg.evaluate("document.body.innerText"); h=await pg.evaluate("[...document.querySelectorAll('a[href=\"rechtliches.html\"]')].map(a=>a.innerText)")
                if disc not in t or not any(link in x for x in h): bad.append(page)
            check(f'{lang.upper()}: Haftungshinweis und Link zur Rechtsseite auf allen fünf Seiten', not bad, bad)
            await pg.goto(U+'rechtliches.html'); await pg.wait_for_timeout(200)
            ids=await pg.evaluate("['impressum','haftung','normen','datenschutz','lizenzen'].every(i=>document.getElementById(i))")
            ph=await pg.evaluate("document.querySelectorAll('.ph').length"); lg=await pg.evaluate("document.documentElement.lang")
            check(f'{lang.upper()}: Rechtsseite mit fünf Abschnitten und Platzhaltern', ids and ph>=6 and lg==lang, (ids, ph, lg))
        # Sprache auf der Rechtsseite umschalten
        await pg.click('#k5-burger'); await pg.click('#k5-lang button[data-v=de]'); await pg.wait_for_timeout(250); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(100)
        check('Rechtsseite: Umschalten auf DE', 'Angaben gemäß § 5 DDG' in await pg.evaluate("document.body.innerText"))
        # Fußleiste folgt dem Sprachwechsel in calc (ohne Neuladen)
        await pg.goto(U+'calc.html'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.documentElement.lang='fr'"); await pg.wait_for_timeout(100)
        check('Fußleiste folgt <html lang> ohne Neuladen', 'Outil d’apprentissage' in await pg.evaluate("document.querySelector('.legal-bar').innerText"))
        # Bericht in size und projekt mit Hinweis
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        await pg.goto(U+'size.html'); await pg.wait_for_timeout(400); await pg.evaluate("showReport()"); await pg.wait_for_timeout(200)
        check('size: Bericht endet mit Haftungshinweis', 'ersetzt keine geprüfte statische Berechnung' in await pg.evaluate("document.getElementById('report').innerText"))
        await pg.evaluate("localStorage.setItem('statiq-size-positionen', JSON.stringify([{name:'Test', typ:'balken', ok:true, date:'2026-10-27T10:00:00Z', data:{}}])); localStorage.setItem('statiq-size-bericht:Test', '<h3>Test</h3>')")
        await pg.goto(U+'projekt.html'); await pg.wait_for_timeout(300); await pg.evaluate("report('s:Test')"); await pg.wait_for_timeout(200)
        check('Rechenblätter: Bericht endet mit Haftungshinweis', 'ersetzt keine geprüfte statische Berechnung' in await pg.evaluate("document.getElementById('report').innerText"))
        # Druck: Fußleiste ausgeblendet
        await pg.emulate_media(media='print')
        check('Druckansicht ohne Fußleiste', await pg.evaluate("getComputedStyle(document.querySelector('.legal-bar')).display")=='none')
        await pg.emulate_media(media='screen')
        # ref: Normtabellen als Auszug
        await pg.goto(U+'ref.html#/holzbau/baustoffe/vollholz'); await pg.wait_for_timeout(250)
        n=await pg.evaluate("document.querySelectorAll('table.data')[0].querySelectorAll('tbody tr').length")
        check('ref EN 338: Auszug mit 5 Klassen, Rechner kennt alle 12', n==5 and await pg.evaluate("VOLLHOLZ_NADEL.rows.length")==12, n)
        await pg.goto(U+'ref.html#/grundbau/flach/sohlwiderstand'); await pg.wait_for_timeout(250)
        t=await pg.evaluate("document.getElementById('main').innerText")
        check('ref Sohlwiderstand: Tabellen gekürzt, Hinweis auf DIN 1054 Anhang A', 'DIN 1054, Anhang A' in t and 'b = 0,5 m\t1,0 m\t2,0 m' in t, '')
        cnt=0
        for r in ['stahlbeton/dauerhaftigkeit/deckung','stahlbau/nachweise/biegeknicken','lastannahmen/lasten/wind','holzbau/baustoffe/kmod']:
            await pg.goto(U+'ref.html#/'+r); await pg.wait_for_timeout(150)
            cnt+='Eigene, gekürzte Darstellung' in await pg.evaluate("document.getElementById('main').innerText")
        check('ref: Normtabellen tragen den Hinweis „eigene, gekürzte Darstellung“', cnt==4, cnt)
        # size v0.5.32: Beschreibung des Nachweises steht in der Abschlusskarte „Umfang und Grundlagen“
        for lang,title in [('de','Umfang und Grundlagen'),('en','Scope and basis')]:
            await pg.goto(U+'size.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(400)
            await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(300)
            r=await pg.evaluate("[getComputedStyle(document.querySelector('.page-head')).display, document.getElementById('scope-card').textContent.replace(/\\s+/g,' '), document.getElementById('page-sub').textContent.replace(/\\s+/g,' '), [...document.querySelectorAll('#details > .card')].pop().id]")
            check(f'size {lang.upper()}: Kopf (Titel, Beschreibung) ausgeblendet, Beschreibung unten in „{title}“ vor „Nicht enthalten“', r[0]=='none' and title in r[1] and r[2].strip()[:40] in r[1] and ('Schnittkräfte' in r[1] or 'Internal forces' in r[1]) and r[3]=='scope-card', r[1][:80])
        await pg.goto(U+'size.html'); await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(400)
        first=await pg.evaluate("(()=>{ const m=document.querySelector('main.main'); const vis=[...m.querySelectorAll('*')].find(e=>e.offsetParent!==null && e.getBoundingClientRect().height>0); return [!!document.querySelector('.lang-notice'), document.getElementById('pick-btn').getBoundingClientRect().top < 140]; })()")
        check('size EN: kein Sprachhinweis, Auswahl steht oben', first==[False, True], first)
        check('keine Anfragen an fremde Server beim Laden', not ext, ext[:3])
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
