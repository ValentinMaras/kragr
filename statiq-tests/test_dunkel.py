# Dunkles Erscheinungsbild (calc v0.8.26, size v0.5.44, ref v0.3.34, projekt v0.1.5, rechtliches v0.1.4):
# Schalter auf allen sechs Seiten, Reihenfolge Automatisch → Dunkel → Hell, Automatisch folgt der Systemeinstellung,
# Auswahl bleibt gespeichert, Bilder und Berichtsansicht werden zurückgedreht, Druck immer hell. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
PAGES=['index','calc','size','ref','projekt','rechtliches']
DARK="document.documentElement.classList.contains('dark')"

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for scheme in ['light','dark']:
            ctx=await br.new_context(color_scheme=scheme); pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            res={}
            for f in PAGES:
                await pg.goto(U+f+'.html'); await pg.evaluate("localStorage.removeItem('muly-theme')"); await pg.reload(); await pg.wait_for_timeout(250)
                res[f]=await pg.evaluate(DARK)
            check(f'Automatisch (ohne Auswahl): System {scheme} → Seiten {"dunkel" if scheme=="dark" else "hell"}', all(v==(scheme=='dark') for v in res.values()), res)
            await ctx.close()
        ctx=await br.new_context(color_scheme='light'); pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        bad={}
        for f in PAGES:
            await pg.goto(U+f+'.html'); await pg.evaluate("localStorage.setItem('muly-theme','auto')"); await pg.reload(); await pg.wait_for_timeout(250)
            vis=await pg.evaluate("(()=>{const b=document.getElementById('theme-btn'); return !!b && b.offsetParent!==null && !!b.getAttribute('aria-label')})()")
            seq=[]
            for _ in range(3):
                await pg.click('#theme-btn'); seq.append((await pg.evaluate("localStorage.getItem('muly-theme')"), await pg.evaluate(DARK)))
            if not vis or seq!=[('dark',True),('light',False),('auto',False)]: bad[f]=(vis,seq)
        check('Schalter auf allen sechs Seiten sichtbar, Folge Dunkel → Hell → Automatisch', not bad, bad)
        await pg.goto(U+'calc.html'); await pg.evaluate("localStorage.setItem('muly-theme','dark')")
        res={}
        for f in PAGES:
            await pg.goto(U+f+'.html'); await pg.wait_for_timeout(200); res[f]=await pg.evaluate(DARK)
        check('Auswahl „Dunkel“ gilt seitenübergreifend und nach Neuladen', all(res.values()), res)
        # Bilder und Berichtsansicht zurückgedreht, Hintergrund dunkel gerechnet
        await pg.goto(U+'size.html'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[getComputedStyle(document.documentElement).filter, getComputedStyle(document.getElementById('report-view')).filter]")
        check('size dunkel: Seite invertiert, Berichtsansicht zurückgedreht (bleibt papierweiß)', r[0].startswith('invert(0.92)') and r[1].startswith('invert(1)'), r)
        await pg.goto(U+'index.html'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('img')].map(i=>getComputedStyle(i).filter)")
        check('Startseite dunkel: Bilder zurückgedreht (Farben bleiben)', all(x.startswith('invert(1)') for x in r), r[:3])
        # Druck: immer hell, kein Schalter
        await pg.emulate_media(media='print')
        for f in ['size','calc']:
            await pg.goto(U+f+'.html'); await pg.wait_for_timeout(250)
            r=await pg.evaluate("[getComputedStyle(document.documentElement).filter, getComputedStyle(document.getElementById('theme-btn')).display]")
            check(f'{f} Druck bei „Dunkel“: kein Filter, Schalter ausgeblendet', r==['none','none'], r)
        await pg.emulate_media(media='screen')
        # Sprachen: Beschriftung übersetzt
        lab={}
        for lang in ['de','en','fr','es']:
            await pg.goto(U+'size.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(250)
            lab[lang]=await pg.evaluate("document.getElementById('theme-btn').getAttribute('aria-label')")
        check('Schalterbeschriftung in DE/EN/FR/ES verschieden', len(set(lab.values()))==4, lab)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        # Theme-Farbe für die Browserleiste
        for f in ['index','calc','projekt']:
            src=open(os.path.join(BASE,f+'.html'),encoding='utf-8').read()
            check(f'{f}: theme-color für hell und dunkel', 'name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)"' in src and '(prefers-color-scheme: dark)' in src)
        # Handy 390 px: Schalter passt in die Kopfzeile, kein Querscrollen
        mob=await br.new_page(viewport={'width':390,'height':800}); w={}
        for f in PAGES:
            await mob.goto(U+f+'.html'); await mob.wait_for_timeout(250)
            w[f]=await mob.evaluate("[document.documentElement.scrollWidth, Math.round(document.getElementById('theme-btn').getBoundingClientRect().right)]")
        check('Handy 390 px: Schalter sichtbar, keine Seite breiter als der Bildschirm', all(a<=390 and b<=390 for a,b in w.values()), w)
        await mob.close()
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
