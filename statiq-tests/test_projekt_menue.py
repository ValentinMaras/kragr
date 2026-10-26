# „Meine Projekte“ (calc v0.10.1, size v0.7.1; seit Design 5 im Burgermenü): gleicher ☰ in calc und size, der Menüeintrag führt direkt zu
# „Meine Projekte“ (kein Fenster, kein Speicherpunkt), Module calc · size · ref und Sprachwahl im Menü. Ohne Playwright: SKIP.
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
TX="(()=>{const a=document.querySelector('#k5-menu [data-mod=projekt]'); return [a.querySelector('b').textContent, a.querySelector('.k5-badge') ? getComputedStyle(a.querySelector('.k5-badge')).display : 'none', document.getElementById('proj-panel').hidden || !document.getElementById('proj-panel').classList.contains('open'), a.getAttribute('href')]})()"
ORD="[...document.querySelectorAll('#k5-menu .k5-mod')].map(e=>e.dataset.mod).join(' ')"
async def menu(pg):
    await pg.click('#k5-burger'); await pg.wait_for_selector('#k5-menu.open')
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':800}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.mouse.move(5,700); sc=await pg.evaluate(STY); await menu(pg); tc=await pg.evaluate(TX); await pg.click('#k5-menu [data-mod=projekt]'); await pg.wait_for_url('**/projekt.html'); uc=pg.url
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(600)
        await pg.mouse.move(5,700); ss=await pg.evaluate(STY); await menu(pg); ts=await pg.evaluate(TX); await pg.click('#k5-menu [data-mod=projekt]'); await pg.wait_for_url('**/projekt.html'); us=pg.url
        check('calc und size: ☰ gleich (Farbe, Höhe, Schrift, Rundung)', sc==ss and sc[1]==44, (sc, ss))
        check('calc und size: „Meine Projekte“ im Menü ohne Punkt, kein Fenster, führt zur Projektseite', tc==ts==['Meine Projekte','none',True,'projekt.html'] and uc.endswith('projekt.html') and us.endswith('projekt.html'), (tc, ts))
        o={}
        for f in ['calc','size','ref']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400); await menu(pg); o[f]=(await pg.evaluate(ORD), await pg.evaluate("document.querySelector('#k5-lang button[aria-pressed=true]').dataset.v"))
        check('Menü überall calc · size · ref · Projekte, Sprachwahl vorhanden', all(v==('calc size ref projekt','de') for v in o.values()), o)
        # Sprache
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(500); await pg.evaluate("setCalcLang('en')"); await pg.wait_for_timeout(300)
        await menu(pg); r=await pg.evaluate(TX); check('calc EN: Menüeintrag „My projects“', r[0]=='My projects', r)
        await pg.keyboard.press('Escape'); await pg.evaluate("setCalcLang('de')")
        # Sprachwahl in size und ref
        for f,c in [('size','Object.keys(TTX[LANG]||{}).length>0 && LANG'),('ref','LANG')]:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400)
            await menu(pg); await pg.click('#k5-lang button[data-v=fr]'); await pg.wait_for_timeout(900)
            check(f'{f}: Sprachwahl im Menü wechselt auf Französisch', await pg.evaluate(c)=='fr' and await pg.evaluate("document.getElementById('lang-sel').value")=='fr')
            await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        await pg.close()
        # Handy
        pg=await br.new_page(viewport={'width':360,'height':720}); pg.on('pageerror', lambda e: errs.append(str(e))); r={}
        for f in ['calc','size','ref']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(500)
            r[f]=await pg.evaluate("[document.documentElement.scrollWidth, Math.round(document.querySelector('.app-header').offsetHeight), Math.round(document.getElementById('k5-burger').getBoundingClientRect().width)]")
        check('Handy 360 px: Kopfzeile einzeilig (58 px), ☰ nur Symbol (44 px), kein Querscrollen', all(v[0]<=360 and v[1]==58 and v[2]==44 for v in r.values()), r)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
