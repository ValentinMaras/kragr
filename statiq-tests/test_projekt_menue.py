# Positions-Menü (calc v0.10.0, size v0.7.0; früher Projekt-Menü seit calc v0.8.28): gleicher Knopf in calc und size, zeigt
# „Pos. N · Titel“, gleiches Fenster (Projektname · Positionen · „＋ Neue Position“ · Link „Meine Projekte“ · Version), kein
# Speicherpunkt mehr (alles wird automatisch gesichert), Kopfzeile überall calc · size · ref mit Sprachwahl. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
STY="(()=>{const b=document.getElementById('proj-btn'),c=getComputedStyle(b); return [c.backgroundColor,Math.round(b.getBoundingClientRect().height),c.fontSize,c.fontWeight,c.borderRadius]})()"
PAN="[document.querySelector('#pos-panel .kp-proj')?.textContent, document.querySelectorAll('#pos-panel .kp-item').length, document.querySelector('#pos-panel .kp-item.cur .kp-nr')?.textContent, document.querySelector('#pos-panel .kp-add')?.textContent, document.querySelector('#pos-panel .proj-link')?.textContent, getComputedStyle(document.getElementById('pos-panel')).borderRadius]"
ORD="[...document.querySelectorAll('.app-header .header-links > a, .app-header .header-links > .module-name')].map(e=>e.textContent.trim()).join(' ')"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':800}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.mouse.move(5,700); sc=await pg.evaluate(STY); await pg.click('#proj-btn'); await pg.wait_for_timeout(200); pc=await pg.evaluate(PAN)
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(600)
        await pg.mouse.move(5,700); ss=await pg.evaluate(STY); await pg.click('#proj-btn'); await pg.wait_for_timeout(200); ps=await pg.evaluate(PAN)
        check('calc und size: Knopf gleich (Farbe, Höhe, Schrift, Rundung)', sc==ss and sc[1]==40, (sc, ss))
        check('calc und size: Fenster gleich aufgebaut (Projekt · Positionen · Neue Position · Meine Projekte)', pc==ps and pc[0]=='Mein Projekt' and pc[1]==1 and pc[2]=='Pos. 1' and 'Neue Position' in pc[3] and 'Meine Projekte' in pc[4], (pc, ps))
        r=await pg.evaluate("[document.querySelector('#proj-btn .pb-tx').textContent, getComputedStyle(document.querySelector('#proj-btn .pb-dot')).display, document.getElementById('proj-panel').hidden]")
        check('Knopf zeigt „Pos. 1 · Titel“, kein Speicherpunkt, altes Fenster verborgen', r[0].startswith('Pos. 1 · ') and r[1]=='none' and r[2], r)
        o={}
        for f in ['calc','size','ref']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400); o[f]=(await pg.evaluate(ORD), await pg.evaluate("document.getElementById('lang-sel')?.value"))
        check('Kopfzeile überall calc · size · ref, Sprachwahl vorhanden', all(v==('calc size ref','de') for v in o.values()), o)
        # Sprache: Menü übersetzt
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(500); await pg.evaluate("setCalcLang('en')"); await pg.wait_for_timeout(300)
        await pg.click('#proj-btn'); await pg.wait_for_timeout(150)
        r=await pg.evaluate(PAN); check('calc EN: Positions-Menü übersetzt', r[0]=='My project' and 'New item' in r[3] and 'My projects' in r[4], r)
        await pg.keyboard.press('Escape'); await pg.evaluate("setCalcLang('de')")
        # Sprachwahl in size und ref
        for f,c in [('size','Object.keys(TTX[LANG]||{}).length>0 && LANG'),('ref','LANG')]:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400)
            await pg.select_option('#lang-sel','fr'); await pg.wait_for_timeout(900)
            check(f'{f}: Sprachwahl in der Kopfzeile wechselt auf Französisch', await pg.evaluate(c)=='fr' and await pg.evaluate("document.getElementById('lang-sel').value")=='fr')
            await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        await pg.close()
        # Handy
        pg=await br.new_page(viewport={'width':360,'height':720}); pg.on('pageerror', lambda e: errs.append(str(e))); r={}
        for f in ['calc','size','ref']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(500)
            r[f]=await pg.evaluate("[document.documentElement.scrollWidth, Math.round(document.querySelector('.app-header').offsetHeight), document.getElementById('proj-btn') ? Math.round(document.getElementById('proj-btn').getBoundingClientRect().width) : 0]")
        check('Handy 360 px: Kopfzeile einzeilig (58 px), Knopf nur Symbol, kein Querscrollen', all(v[0]<=360 and v[1]==58 and v[2]<=40 for v in r.values()), r)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
