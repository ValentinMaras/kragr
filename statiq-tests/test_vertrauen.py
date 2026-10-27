# Vertrauen und Seriosität (Oktober 2026): „Fehler melden“ in calc/size/ref, Prüfhinweis und aktuelle Versionen auf der
# Startseite, Impressum mit Name und markierten Platzhaltern, Normangabe in den Umfang-Karten von size. Ohne Playwright: SKIP.
import os, sys, re, asyncio
from urllib.parse import unquote
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(300)
        a=pg.locator('#scope-card .fehler-link'); await a.evaluate("e=>e.onclick()"); h=unquote(await a.get_attribute('href'))
        v=await pg.evaluate("SIZE_VERSION")
        check('size: „Fehler melden“ öffnet E-Mail mit Modul, Version und Eingaben', h.startswith('mailto:') and f'size v{v}' in h and 'stahl/traeger' in h and '"prof"' in h, h[:140])
        await pg.goto(U+'calc.html'); await pg.wait_for_timeout(300)
        n=await pg.evaluate("document.querySelectorAll('.footnote[data-foot] a.fehler-link').length")
        await pg.evaluate("document.querySelector('.footnote[data-foot] a').onclick()"); h=unquote(await pg.evaluate("document.querySelector('.footnote[data-foot] a').href"))
        v=await pg.evaluate("STATIQ_VERSION")
        check('calc: Link in allen vier Fußnoten, E-Mail mit Version', n==4 and f'calc v{v}' in h, (n, h[:100]))
        await pg.goto(U+'ref.html#/baustatik/querschnitte/euler'); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('.footnote a.fehler-link').onclick()"); h=unquote(await pg.evaluate("document.querySelector('.footnote a.fehler-link').href"))
        check('ref: Link in der Fußnote, E-Mail mit Thema (#/…)', '#/baustatik/querschnitte/euler' in h and 'ref v' in h, h[:120])
        # Startseite
        vers=[]
        for f,c in [('calc.html','STATIQ_VERSION'),('ref.html','REF_VERSION'),('size.html','SIZE_VERSION'),('projekt.html','PROJ_VERSION')]:
            await pg.goto(U+f); await pg.wait_for_timeout(200); vers.append(await pg.evaluate(c))
        await pg.goto(U+'index.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(800)
        meta=await pg.evaluate("document.querySelector('.footer-meta').innerText"); chk=await pg.evaluate("document.getElementById('footer-check').innerText")
        exp=f'Schnittkräfte v{vers[0]} · Bemessung v{vers[2]} · Wissen v{vers[1]} · Rechenblätter v{vers[3]}'
        check('Startseite: Versionen in der Fußzeile aktuell', exp in meta, (meta, exp))
        check('Startseite: Hinweis auf unabhängige Prüfungen', 'unabhängige Nachrechnungen' in chk, chk)
        # Impressum
        await pg.goto(U+'rechtliches.html'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.getElementById('content').innerText")
        ph=await pg.evaluate("[...document.querySelectorAll('.ph')].map(e=>e.textContent)")
        check('Impressum: Name eingetragen, offene Angaben als Platzhalter markiert', 'Valentin Maras' in t and all(x.startswith('[') for x in ph) and len(ph)>=3, ph[:4])
        check('Datenschutz: Hosting GitHub Pages mit Hinweis auf Übermittlung in die USA', 'GitHub' in t and 'USA' in t)
        # Normangaben
        await pg.goto(U+'size.html'); await pg.wait_for_timeout(300)
        res={}
        for js,key in [("setMat('beton'); setTyp('platte2')",'DIN EN 1992-1-1'),("setMat('mauer'); setMwMode('ausfach')",'DIN EN 1996-3'),("setMat('grund'); setGrMode('spundwand')",'DIN 4085'),("setMat('holz'); setHoMode('durchbruch')",'DIN EN 1995-1-1')]:
            try:
                await pg.evaluate(js); await pg.wait_for_timeout(250)
                res[key]=key in await pg.evaluate("document.getElementById('scope-card').textContent.replace(/\\s+/g,' ')")   # k5: Karte zugeklappt
            except Exception as e: res[key]=str(e)[:60]
        check('size: Umfang nennt die Norm (Platte zweiachsig, Ausfachung, Spundwand, Durchbruch)', all(v is True for v in res.values()), res)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
