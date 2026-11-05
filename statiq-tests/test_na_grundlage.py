# Bemessungsgrundlage (calc v0.11.20 · size v0.7.22 · ref v0.3.58 · projekt v0.1.27; Österreich seit size v0.7.23): Auswahl im Menü (DE und AT aktiv),
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
        check('Menü: Bemessungsgrundlage DE AT CH FR ES UK, DE und AT wählbar, DE gewählt', r['codes']==['DE','AT','CH','FR','ES','UK'] and r['on']==['de','at'] and r['pressed']==['de'], r)
        check('Menü: Untertitel „Nationaler Anhang: Deutschland“, CH „in Vorbereitung“', 'Nationaler Anhang: Deutschland' in r['sub'] and await pg.evaluate("document.querySelector('#k5-na button[data-v=ch]').title")=='Schweiz – in Vorbereitung', r['sub'])
        await pg.click('#k5-na button[data-v="ch"]', force=True); await pg.wait_for_timeout(100)
        check('Klick auf CH ändert nichts (deaktiviert)', await pg.evaluate("kragrNA()")=='de' and await pg.evaluate("localStorage.getItem('kragr-na')") in (None,'de'))
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
        # ── Österreich (size v0.7.23) — Sollwerte von Hand ──
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(800)
        await pg.click('#k5-burger'); await pg.wait_for_selector('#k5-menu.open'); await pg.click('#k5-na button[data-v="at"]'); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[kragrNA(), localStorage.getItem('kragr-na'), document.querySelector('#k5-na').closest('.k5-row').querySelector('.k5-rt > span').textContent]")
        check('AT wählen: gespeichert, Untertitel „Nationaler Anhang: Österreich“', r==['at','at','Nationaler Anhang: Österreich'], r)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        # Standardbalken C30/37, XC1, b/h = 300/600, Bügel Ø8, 2 Ø 25: c_min,dur = 15, Δc_dev = 5 → c_nom Bügel 20, Längsstab 30 → c_v = 22, d = 600 − 22 − 8 − 12,5 = 557,5 mm
        # f_cd = 1,0·30/1,5 = 20 N/mm² (α_cc = 1,0), A_s,min = max(0,26·2,9/500; 0,0013)·300·557,5 = 0,001508·300·557,5 = 252,2 mm²
        r=await pg.evaluate("(()=>{ const t=document.querySelector('#n-biegung .steps').textContent, d=document.querySelector('#n-deckung .steps').textContent; return [t.includes('= 1,0 · 30 / 1,5= 20,00'), d.includes('= 600 − 22 − 8 − 12,5= 557,5'), t.includes('= 2,52 cm²'), t.includes('9.2.1.1'), d.includes('Δcdev = 5 mm')]; })()")
        check('AT Beton: α_cc = 1,0 → f_cd = 20,00; d = 557,5 mm (Δc_dev = 5); A_s,min = 2,52 cm² nach EN 9.2.1.1', all(r), r)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].map(c=>[c.id.slice(2), c.querySelector('.steps').textContent.startsWith('Für Österreich')])")
        check('AT Beton: nur Deckung und Biegung gerechnet, übrige Nachweise als Hinweis', all(h==(i not in ('deckung','biegung')) for i,h in r), r)
        h=await pg.evaluate("document.querySelector('#details .na-hint').textContent")
        check('AT: Hinweis oben nennt die Marke NA AT und die Teilabdeckung', 'NA AT' in h and 'Für Österreich rechnet kragr bisher nur' in h, h)
        m=await pg.evaluate(MARKS); check('AT: Marke im Rechenweg „NA AT“', await pg.evaluate("document.querySelector('#details .steps .na-t').textContent")=='NA AT', m)
        await pg.select_option('#in-expo', 'XS1') if await pg.evaluate("!!document.getElementById('in-expo')") else None
        if await pg.evaluate("!!document.getElementById('in-expo')"):
            await pg.wait_for_timeout(400)
            r=await pg.evaluate("['deckung','biegung'].map(i=>document.querySelector('#n-'+i+' .steps').textContent.startsWith('Für Österreich'))")
            check('AT XS1 (keine c_min,dur im NA hinterlegt): Deckung und Biegung nicht gerechnet', r==[True,True], r)
            await pg.select_option('#in-expo', 'XC1'); await pg.wait_for_timeout(300)
        # Holz BSH GL24h: γ_M = 1,25 (ÖNORM B 1995-1-1)
        await pg.evaluate("setMat('holz'); $('ho-art').value='bsh'; $('ho-art').dispatchEvent(new Event('change')); run()"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[document.querySelector('#n-bem .steps').textContent, document.querySelector('#n-biegung .steps').textContent.startsWith('Für Österreich'), document.querySelector('#n-schub .steps').textContent.startsWith('Für Österreich')]")
        check('AT Holz BSH: γ_M = 1,25 im Rechenweg, Biegung gerechnet, Schub als Hinweis', 'γM = 1,25' in r[0] and '24/1,25= 16,90' in r[0] and not r[1] and r[2], r[0][-160:])
        # Stahl: in AT noch nicht hinterlegt
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].every(c=>c.querySelector('.steps').textContent.startsWith('Für Österreich'))")
        check('AT Stahl: alle Nachweise als Hinweis (noch nicht hinterlegt)', r)
        # zurück auf DE: Werte wie vorher
        await pg.evaluate("localStorage.setItem('kragr-na','de')"); await pg.reload(); await pg.wait_for_timeout(800); await pg.evaluate("setMat('beton')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("document.querySelector('#n-biegung .steps').textContent")
        check('DE wieder: f_cd = 0,85·30/1,5 = 17,00', '= 0,85 · 30 / 1,5= 17,00' in r, r[:160])
        # Wissen bei AT: Marke bleibt NA DE, Hinweis oben auf der Seite
        await pg.evaluate("localStorage.setItem('kragr-na','at')"); await pg.goto(B+'ref.html#/stahlbeton/bemessung/biegung'); await pg.wait_for_timeout(800)
        r=await pg.evaluate("[document.querySelector('#main .na-t').textContent, (document.querySelector('#main .na-ref')||{}).textContent||'']")
        check('Wissen bei AT: Marke „NA DE“, Hinweis „noch nicht hinterlegt“ für Österreich', r[0]=='NA DE' and 'Für Österreich' in r[1], r)
        await pg.evaluate("localStorage.setItem('kragr-na','de')")
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
