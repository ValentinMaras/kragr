# statiq·ref v0.3.8: Seitenleiste mit Filter, „Auf dieser Seite“, Themen-Pager, Handy-Menü, Bausteine ablauf/eqLine/filterBox. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(400)
        g=await pg.evaluate("""(()=>{const s=document.getElementById('sidebar').getBoundingClientRect(), m=document.getElementById('main').getBoundingClientRect(), t=document.getElementById('toc').getBoundingClientRect();
          return [s.width>200, s.right<=m.left+1, getComputedStyle(document.getElementById('toc')).display]})()""")
        check('Desktop 1440: Seitenleiste links, Inhalt daneben', g[0] and g[1], g)
        g=await pg.evaluate("[getComputedStyle(document.querySelector('.home-tiles')).display, getComputedStyle(document.querySelector('.home-hint')).display, !!document.getElementById('search')]")
        check('Startseite Desktop: keine Kacheln, Hinweis und Suche sichtbar', g==['none','block',True], g)
        n=await pg.evaluate("document.querySelectorAll('#sidebar a').length")
        check('Seitenleiste enthält Themenlinks', n>20, n)
        await pg.fill('#side-q','Bernoulli'); await pg.wait_for_timeout(150)
        vis=await pg.evaluate("[...document.querySelectorAll('#sidebar a')].filter(a=>a.offsetParent).map(a=>a.textContent.trim())")
        check('Filter „Bernoulli“ zeigt nur passende Themen', 0<len(vis)<=3 and any('Bernoulli' in v for v in vis), vis)
        await pg.fill('#side-q',''); await pg.wait_for_timeout(100)
        link=pg.locator('#sidebar a', has_text='Bernoulli').first; await link.click(); await pg.wait_for_timeout(400)
        st=await pg.evaluate("[location.hash, document.querySelectorAll('#toc a').length, !!document.querySelector('.topic-pager'), document.querySelector('#sidebar a.active')?.textContent.trim()||'']")
        check('Klick in der Seitenleiste öffnet das Thema', 'bernoulli' in st[0], st)
        check('„Auf dieser Seite“ listet die Abschnitte', st[1]>=2, st[1])
        check('Themen-Pager vorhanden, aktives Thema markiert', st[2] and 'Bernoulli' in st[3], st)
        ok=await pg.evaluate("""(()=>{return [...document.querySelectorAll('#toc a')].every(a=>!!document.getElementById(a.dataset.id))})()""")
        check('Links in „Auf dieser Seite“ zeigen auf vorhandene Abschnitte', ok)
        # Bausteine
        h=await pg.evaluate("ablauf('Test',['§Schritt 1','!Hinweis','M = q · l² / 8 = 10 · 25 / 8 = 31,25 kNm'])")
        check('ablauf(): Überschrift, Hinweis, Formelkette zeilenweise', 'Schritt 1' in h and 'Hinweis' in h and h.count('class="eq-r')>=3, h)
        h=await pg.evaluate("eqLine('Beispiel: das ist ein Satz mit = Zeichen')")
        check('eqLine(): Fließtext wird nicht zerlegt', not h or 'eq-r' not in h, h)
        # Handy
        await pg.set_viewport_size({'width':390,'height':844}); await pg.wait_for_timeout(250)
        g=await pg.evaluate("[document.documentElement.scrollWidth, getComputedStyle(document.querySelector('#main .page-head'),'::after').content!=='none' ? 'pfeil' : 'none', getComputedStyle(document.getElementById('toc')).display]")   # k5: Seitenkopf mit Pfeil öffnet die Themenliste
        check('Handy: kein Querscrollen, Seitenkopf mit Pfeil (Themenliste), kein Inhaltsverzeichnis', g[0]<=390 and g[1]!='none' and g[2]=='none', g)
        await pg.goto(HTML+'#/'); await pg.wait_for_timeout(300)
        g=await pg.evaluate("[getComputedStyle(document.querySelector('.home-tiles')).display, getComputedStyle(document.querySelector('.home-hint')).display]")
        check('Startseite Handy: Kacheln bleiben (keine Seitenleiste)', g==['grid','none'], g)
        await pg.goto(HTML+'#/wasserbau/hydrodynamik/bernoulli'); await pg.wait_for_timeout(300)
        await pg.click('#main .page-head'); await pg.wait_for_timeout(200)
        check('Handy: Menüknopf öffnet die Themenliste', await pg.evaluate("document.getElementById('sidebar').classList.contains('open')"))
        await pg.locator('#sidebar a', has_text='Manning').first.click(); await pg.wait_for_timeout(300)
        check('Handy: Themenwahl schließt die Liste', not await pg.evaluate("document.getElementById('sidebar').classList.contains('open')"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
