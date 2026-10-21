# Projekt-Menü vereinheitlicht (calc v0.8.28, size v0.5.46, ref v0.3.36): gleicher schlanker Knopf mit Speicherstand
# (orange = nicht gespeichert, grün = gespeichert), gleiches Fenster (Aktuelle Berechnung · Gespeichert · Link), Kopfzeile
# überall calc · size · ref mit Sprachwahl, calc legt dieselbe Berechnung nicht doppelt ab. Ohne Playwright: SKIP.
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
PAN="[...document.querySelectorAll('#proj-panel .pp-h')].map(e=>e.textContent).slice(0,2).concat([document.getElementById('pp-foot').textContent, getComputedStyle(document.getElementById('proj-panel')).borderRadius])"
ORD="[...document.querySelectorAll('.app-header .header-links > a, .app-header .header-links > .module-name')].map(e=>e.textContent.trim()).join(' ')"
ST="document.getElementById('proj-btn').dataset.st"
NS="Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_')).length"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':800}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.mouse.move(5,700); sc=await pg.evaluate(STY); await pg.click('#proj-btn'); await pg.wait_for_timeout(200); pc=await pg.evaluate(PAN)
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(600)
        await pg.mouse.move(5,700); ss=await pg.evaluate(STY); await pg.click('#proj-btn'); await pg.wait_for_timeout(200); ps=await pg.evaluate(PAN)
        check('calc und size: Knopf gleich (Farbe, Höhe, Schrift, Rundung)', sc==ss and sc[1]==40, (sc, ss))
        check('calc und size: Fenster gleich aufgebaut (Aktuelle Berechnung · Gespeichert · Link)', pc==ps and pc[0]=='Aktuelle Berechnung' and pc[1]=='Gespeichert' and 'Meine Projekte' in pc[2], (pc, ps))
        o={}
        for f in ['calc','size','ref']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400); o[f]=(await pg.evaluate(ORD), await pg.evaluate("document.getElementById('lang-sel')?.value"))
        check('Kopfzeile überall calc · size · ref, Sprachwahl vorhanden', all(v==('calc size ref','de') for v in o.values()), o)
        # size: Speicherstand
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.removeItem('statiq-size-positionen')"); await pg.reload(); await pg.wait_for_timeout(600)
        s1=await pg.evaluate(ST); await pg.click('#proj-btn'); await pg.click('#proj-panel >> text=Speichern'); await pg.wait_for_timeout(300)
        s2=await pg.evaluate(ST); t2=await pg.inner_text('#pp-st')
        await pg.evaluate("$('in-M').value='250'; run()"); await pg.wait_for_timeout(1500)
        s3=await pg.evaluate(ST); m3=await pg.inner_text('#pos-msg')
        check('size: neu (orange) → gespeichert (grün, mit Uhrzeit) → geändert (orange)', [s1,s2,s3]==['new','saved','changed'] and t2.startswith('Gespeichert ·'), [s1,s2,t2,s3])
        check('size: Meldung „gespeichert“ verschwindet nach Änderung', m3=='', m3)
        await pg.evaluate('openProj()'); await pg.wait_for_timeout(100)
        await pg.click('.pos-item >> text=Laden'); await pg.wait_for_timeout(1500)
        check('size: gespeicherte Position laden → wieder grün', await pg.evaluate(ST)=='saved')
        # calc: Speicherstand und keine Doppel
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(500)
        c1=await pg.evaluate(ST); n0=await pg.evaluate(NS)
        await pg.click('#proj-btn'); await pg.click('#pp-save'); await pg.wait_for_timeout(200)
        c2=await pg.evaluate(ST); n1=await pg.evaluate(NS); msg=await pg.inner_text('#pp-msg')
        await pg.click('#pp-save'); await pg.wait_for_timeout(200); n2=await pg.evaluate(NS); msg2=await pg.inner_text('#pp-msg')
        await pg.evaluate("saveCalc('beam')"); n3=await pg.evaluate(NS)
        check('calc: neu → gespeichert; zweites Speichern legt keine Kopie an', [c1,c2]==['new','saved'] and n1==n0+1 and n2==n1 and n3==n1 and 'gespeichert' in msg and 'Schon gespeichert' in msg2, [c1,c2,n0,n1,n2,n3,msg2])
        href=await pg.evaluate("document.querySelector('#pp-list a.pp-btn').getAttribute('href')")
        check('calc: Liste mit „→ size“ zur Übernahme', href.startswith('size.html#calc=statiq_sdf_'), href)
        await pg.evaluate("document.getElementById('bL').value='6'; calculateBeam()"); await pg.wait_for_timeout(1500)
        check('calc: geänderte Stützweite → wieder „nicht gespeichert“', await pg.evaluate(ST)=='new' and 'L=6m' in await pg.inner_text('#pp-name'))
        await pg.evaluate("showTab('saved')"); await pg.wait_for_timeout(1500)
        check('calc „Gespeichert“-Ansicht: kein Punkt, Speichern gesperrt', await pg.evaluate(ST)=='none' and await pg.evaluate("document.getElementById('pp-save').disabled"))
        await pg.evaluate("showTab('beam'); setCalcLang('en')"); await pg.wait_for_timeout(300)
        check('calc EN: Knopf und Fenster übersetzt', await pg.inner_text('#proj-btn .pb-tx')=='My projects' and await pg.inner_text('#pp-h-cur')=='Current calculation')
        await pg.evaluate("setCalcLang('de')")
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
