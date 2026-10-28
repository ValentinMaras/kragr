# „Auf dieser Seite“ (ref v0.3.55): die blaue Markierung folgt dem Lesen und steht ganz unten auf dem letzten Abschnitt,
# auch wenn dieser kurz ist und den oberen Rand nie erreicht. Vorher (IntersectionObserver) blieb sie beim vorletzten stehen.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
ON="(()=>{ const a=[...document.querySelectorAll('#toc a')]; return [a.findIndex(x=>x.classList.contains('on')), a.length, document.querySelectorAll('#toc a.on').length]; })()"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1580,'height':1000}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'ref.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')")
        for h in ['baustatik/allgemein/geschichte','stahlbau/nachweise/biegeknicken','stahlbeton/betontechnologie/hydratation']:
            await pg.goto(B+'ref.html#/'+h); await pg.reload(); await pg.wait_for_timeout(600)
            vis=await pg.evaluate("!!document.querySelector('#toc a') && getComputedStyle(document.getElementById('toc')).display!=='none'")
            r0=await pg.evaluate(ON)
            check(f'{h.split("/")[-1]}: oben ist der erste Abschnitt markiert', vis and r0[0]==0 and r0[2]==1, r0)
            await pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); await pg.wait_for_timeout(250)
            r=await pg.evaluate(ON)
            check(f'{h.split("/")[-1]}: ganz unten ist der letzte Abschnitt markiert', r[0]==r[1]-1 and r[2]==1, r)
            await pg.evaluate("document.querySelectorAll('#main .card')[1].scrollIntoView({block:'start'})"); await pg.wait_for_timeout(250)
            r=await pg.evaluate(ON); end=await pg.evaluate("Math.ceil(scrollY+innerHeight)>=document.documentElement.scrollHeight-4")
            check(f'{h.split("/")[-1]}: Abschnitt 2 oben → Abschnitt 2 markiert (kurze Seite am Ende: der letzte)', r[0]==(r[1]-1 if end else 1), (r, end))
        # Themenwechsel: keine doppelten Scroll-Beobachter, Markierung stimmt auf der neuen Seite
        await pg.evaluate("location.hash='#/baustatik/allgemein/geschichte'"); await pg.wait_for_timeout(400)
        await pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); await pg.wait_for_timeout(250)
        r=await pg.evaluate(ON)
        check('nach Themenwechsel: unten wieder der letzte Abschnitt', r[0]==r[1]-1 and r[2]==1, r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
