# Ordner-Symbol „Meine Projekte“ (calc v0.10.1, size v0.7.1; früher Projekt- bzw. Positions-Menü): gleicher Knopf in calc und size,
# führt direkt zu „Meine Projekte“ (kein Fenster mehr, kein Speicherpunkt), Kopfzeile überall calc · size · ref mit Sprachwahl. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
STY="(()=>{const b=document.getElementById('k5-burger'),c=getComputedStyle(b); return [c.backgroundColor,Math.round(b.getBoundingClientRect().height),c.fontSize,c.fontWeight,c.borderRadius]})()"
TX="[document.querySelector('#proj-btn .pb-tx').textContent, getComputedStyle(document.querySelector('#proj-btn .pb-dot')).display, document.getElementById('proj-panel').hidden, document.getElementById('proj-btn').hasAttribute('aria-haspopup')]"
ORD="[...document.querySelectorAll('.app-header .header-links > a, .app-header .header-links > .module-name')].map(e=>e.textContent.trim()).join(' ')"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':800}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.mouse.move(5,700); sc=await pg.evaluate(STY); tc=await pg.evaluate(TX); await pg.click('#k5-burger'); await pg.click('#k5-menu [data-mod=projekt]'); await pg.wait_for_url('**/projekt.html'); uc=pg.url
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(600)
        await pg.mouse.move(5,700); ss=await pg.evaluate(STY); ts=await pg.evaluate(TX); await pg.click('#k5-burger'); await pg.click('#k5-menu [data-mod=projekt]'); await pg.wait_for_url('**/projekt.html'); us=pg.url
        check('calc und size: Menüknopf gleich (Farbe, Höhe 44, Schrift, Rundung)', sc==ss and sc[1]==44, (sc, ss))   # k5: Projekte im Menü
        check('calc und size: „Meine Projekte“ ohne Punkt und ohne Menü, führt zur Projektseite', tc==ts==['Projekte','none',True,False] and uc.endswith('projekt.html') and us.endswith('projekt.html'), (tc, ts))
        o={}
        for f in ['calc','size','ref']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400); o[f]=(await pg.evaluate(ORD), await pg.evaluate("document.getElementById('lang-sel')?.value"))
        check('Kopfzeile überall Schnittkräfte · Bemessung · Wissen, Sprachwahl vorhanden', all(v==('Schnittkräfte Bemessung Wissen','de') for v in o.values()), o)
        # Sprache
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(500); await pg.evaluate("setCalcLang('en')"); await pg.wait_for_timeout(300)
        r=await pg.evaluate(TX); check('calc EN: Knopf „My projects“', r[0]=='Projects', r)
        await pg.evaluate("setCalcLang('de')")
        # Sprachwahl in size und ref
        for f,c in [('size','Object.keys(TTX[LANG]||{}).length>0 && LANG'),('ref','LANG')]:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400)
            await pg.click('#k5-burger'); await pg.click('#k5-lang button[data-v=fr]'); await pg.wait_for_timeout(250); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(900)
            check(f'{f}: Sprachwahl in der Kopfzeile wechselt auf Französisch', await pg.evaluate(c)=='fr' and await pg.evaluate("document.getElementById('lang-sel').value")=='fr')
            await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        await pg.close()
        # Handy
        pg=await br.new_page(viewport={'width':360,'height':720}); pg.on('pageerror', lambda e: errs.append(str(e))); r={}
        for f in ['calc','size','ref']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(500)
            r[f]=await pg.evaluate("[document.documentElement.scrollWidth, Math.round(document.querySelector('.app-header').offsetHeight), Math.round(document.getElementById('k5-burger').getBoundingClientRect().width)]")
        check('Handy 360 px: Kopfzeile eine Zeile (58 px), Menüknopf nur Symbol (44 px), kein Querscrollen', all(v[0]<=360 and v[1]==58 and v[2]<=44 for v in r.values()), r)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
