# Bemessungsgrundlage (calc v0.11.20 · size v0.7.22 · ref v0.3.58 · projekt v0.1.27): Auswahl im Menü (bisher nur DE aktiv),
# Marke „NA DE“ an Größen aus dem nationalen Anhang im Rechenweg, Hinweis oben in den Ergebnissen, nicht im Bericht und nicht im Druck.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
MARKS="[...document.querySelectorAll('#details .steps .na-t')].map(b=>b.dataset.sy)"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':390,'height':844}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        # Menü
        await pg.click('#k5-burger'); await pg.wait_for_selector('#k5-menu.open'); await pg.wait_for_timeout(200)
        r=await pg.evaluate("""(()=>{const g=document.getElementById('k5-na'); const bs=[...g.querySelectorAll('button')];
          return {codes:bs.map(b=>b.textContent), on:bs.filter(b=>!b.disabled).map(b=>b.dataset.v), pressed:bs.filter(b=>b.getAttribute('aria-pressed')==='true').map(b=>b.dataset.v),
            sub:g.closest('.k5-row').querySelector('.k5-rt').textContent, soon:bs[1].title, order:[...document.querySelectorAll('#k5-menu .k5-rt')].map(e=>e.firstChild.textContent)}})()""")
        check('Menü: Bemessungsgrundlage DE AT CH FR ES UK, nur DE wählbar und gewählt', r['codes']==['DE','AT','CH','FR','ES','UK'] and r['on']==['de'] and r['pressed']==['de'], r)
        check('Menü: Untertitel „Nationaler Anhang: Deutschland“, AT „in Vorbereitung“', 'Nationaler Anhang: Deutschland' in r['sub'] and r['soon']=='Österreich – in Vorbereitung', (r['sub'], r['soon']))
        check('Menü: Reihenfolge Übungsmodus, Erscheinungsbild, Bemessungsgrundlage, Sprache', r['order'][-3:]==['Erscheinungsbild','Bemessungsgrundlage','Sprache'], r['order'])
        await pg.click('#k5-na button[data-v="at"]', force=True); await pg.wait_for_timeout(100)
        check('Klick auf AT ändert nichts (deaktiviert)', await pg.evaluate("kragrNA()")=='de' and await pg.evaluate("localStorage.getItem('kragr-na')") in (None,'de'))
        await pg.evaluate("localStorage.setItem('kragr-na','uk')"); check('gespeichertes, noch nicht verfügbares Land fällt auf DE zurück', await pg.evaluate("kragrNA()")=='de')
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        # Marken im Rechenweg
        await pg.evaluate("setMat('beton')"); await pg.wait_for_timeout(500)
        m=await pg.evaluate(MARKS)
        check('Stahlbeton: γc, γs, αcc markiert', any('γc' in x for x in m) and any('γs' in x for x in m) and any('αcc' in x for x in m), m)
        check('keine falsche Marke in Wörtern („Fachwerkmodell“ ≠ kmod)', not any('kmod' in x for x in m), m)
        t=await pg.evaluate("document.querySelector('#details .steps .na-t').textContent")
        check('Marke lautet „NA DE“', t=='NA DE', t)
        h=await pg.evaluate("[!!document.querySelector('#details > .na-hint, #details .na-hint'), (document.querySelector('#details .na-hint')||{}).textContent]")
        check('Hinweis oben in den Ergebnissen erklärt die Marke', h[0] and 'nationale Anhang' in h[1] and 'Bemessungsgrundlage' in h[1], h)
        for mat,sym in [('stahl','γM0'),('holz','kmod'),('mauer','γM'),('grund','γR,v')]:
            await pg.evaluate(f"setMat('{mat}')"); await pg.wait_for_timeout(500); m=await pg.evaluate(MARKS)
            check(f'{mat}: {sym} markiert, jede Größe je Rechenweg nur einmal', any(sym in x.split(', ') for x in m) and all(len(set(x.split(', ')))==len(x.split(', ')) for x in m), m)
        await pg.evaluate("setMat('beton')"); await pg.wait_for_timeout(500)
        await pg.evaluate("showReport()"); await pg.wait_for_timeout(500)
        check('Bericht ohne Marken', await pg.evaluate("document.querySelectorAll('#report .na-t').length")==0)
        await pg.evaluate("hideReport && hideReport()"); await pg.wait_for_timeout(200)
        await pg.emulate_media(media='print'); d=await pg.evaluate("getComputedStyle(document.querySelector('#details .na-t')).display"); await pg.emulate_media(media='screen')
        check('im Druck ausgeblendet', d=='none', d)
        # Sprachen
        for L,abbr,word in [('en','NA DE','National Annex'),('fr','AN DE','annexe nationale'),('es','AN DE','anejo nacional')]:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(800)
            r=await pg.evaluate("[document.querySelector('#details .steps .na-t').textContent, document.querySelector('#details .na-hint').textContent]")
            check(f'{L}: Marke „{abbr}“, Hinweis übersetzt', r[0]==abbr and word in r[1], r)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        # ref: Rechenweg im Wissen
        await pg.goto(B+'ref.html#/stahlbeton/bemessung/biegung'); await pg.wait_for_timeout(800)
        m=await pg.evaluate("[...document.querySelectorAll('#main .steps .na-t')].map(b=>b.dataset.sy)")
        check('Wissen: Rechenweg Biegung markiert αcc und γc', any('αcc' in x and 'γc' in x for x in m), m)
        # projekt: Menü auch dort
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(500); await pg.click('#k5-burger'); await pg.wait_for_timeout(300)
        check('Rechenblätter: Bemessungsgrundlage im Menü', await pg.evaluate("!!document.getElementById('k5-na')"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
