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
        FL="document.querySelector('.legal-bar .legal-ver a.fehler-link')"
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(300)
        await pg.evaluate(FL+".onclick()"); h=unquote(await pg.evaluate(FL+".href"))
        v=await pg.evaluate("STATIQ_VERSION")
        check('calc: „Fehler melden“ in der Fußleiste, E-Mail mit Version und System', f'calc v{v}' in h and 'frame' in h, h[:140])
        await pg.goto(U+'ref.html#/baustatik/querschnitte/euler'); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate(FL+".onclick()"); h=unquote(await pg.evaluate(FL+".href"))
        check('ref: Link in der Fußleiste, E-Mail mit Thema (#/…)', '#/baustatik/querschnitte/euler' in h and 'ref v' in h, h[:120])
        # gleiche Fußleiste in allen Apps: Hinweis, Impressum, Version mit „Fehler melden“, nichts danach
        bad=[]
        for f,mod in (('calc.html','Schnittkräfte'),('size.html','Bemessung'),('ref.html','Wissen'),('projekt.html','Rechenblätter')):
            await pg.goto(U+f); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
            r=await pg.evaluate("(()=>{ const l=document.querySelector('.legal-bar'); const after=[]; let e=l.nextElementSibling; while(e){ if(e.offsetHeight>0 && getComputedStyle(e).position!=='fixed') after.push(e.tagName+'.'+e.className); e=e.nextElementSibling; } return [l.children.length, l.querySelector('.legal-ver')?.textContent||'', after, !!document.querySelector('.footnote, #k-verfoot:not([style*=none])') && [...document.querySelectorAll('.footnote, #k-verfoot')].some(x=>x.offsetHeight>0)]; })()")
            ok=r[0]==3 and r[1].startswith('kragr · '+mod+' v') and r[1].endswith('Fehler gefunden? Bitte melden.') and not r[2] and not r[3]
            if not ok: bad.append((f,r))
        check('Fußleiste in Schnittkräfte, Bemessung, Wissen, Rechenblätter gleich (Hinweis · Impressum · Version mit „Fehler melden“), keine zweite Versionszeile', not bad, bad)
        # Startseite so breit wie die Apps: linke Kante der Karten = linke Kante der Auswahl, am Rechner und am Handy
        for w in (1280,390):
            await pg.set_viewport_size({'width':w,'height':844}); edges={}
            for f,sel in (('index.html','.module-card'),('calc.html','#pick'),('size.html','#pick'),('ref.html#/','#pick'),('projekt.html','#pick')):
                await pg.goto(U+f); await pg.wait_for_timeout(450); edges[f]=await pg.evaluate(f"Math.round(document.querySelector('{sel}').getBoundingClientRect().left)")
            check(f'{w} px: Startseite und Apps mit gleicher linker Kante', len(set(edges.values()))==1, edges)
        await pg.set_viewport_size({'width':1280,'height':720})
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
