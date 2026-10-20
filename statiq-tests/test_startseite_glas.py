# Startseite auf einem Bildschirm und Glasleiste (calc v0.8.27, size v0.5.45, ref v0.3.35, projekt v0.1.6, rechtliches v0.1.5):
# Startseite ohne Scrollen auf Handy, Tablet und Rechner (alle Sprachen, mit und ohne Hinweis „als App“), Hinweis
# ausblendbar, Kopfzeilen durchscheinend mit weichgezeichnetem Hintergrund und weichem Rand, im Druck ohne. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
VP=[(360,560),(375,548),(390,664),(430,740),(768,1024),(1024,600),(1280,720),(1440,900),(1920,1080)]

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        bad={}; gap={}
        for w,h in VP:
            pg=await br.new_page(viewport={'width':w,'height':h}); pg.on('pageerror', lambda e: errs.append(str(e)))
            for lang in ['de','en','fr','es']:
                for inst in [0,1]:
                    await pg.goto(U+'index.html'); await pg.evaluate(f"localStorage.clear();localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(500)
                    if inst: await pg.evaluate("document.getElementById('install').hidden=false; document.getElementById('install-btn').hidden=true; document.getElementById('install-sub').textContent=translations[currentLang].install_ios")
                    r=await pg.evaluate("[document.documentElement.scrollHeight, document.documentElement.scrollWidth]")
                    vis=await pg.evaluate("[...document.querySelectorAll('.module-card')].every(c=>{const b=c.getBoundingClientRect(); return b.top>=0 && b.bottom<=innerHeight})")
                    if r[0]>h or r[1]>w or not vis: bad[(w,h,lang,inst)]=r
                    if lang=='de' and not inst and w<=430:
                        gap[(w,h)]=await pg.evaluate("Math.round(document.querySelector('.headline').getBoundingClientRect().top)")
            await pg.close()
        check('Startseite passt ohne Scrollen: 9 Bildschirme × 4 Sprachen × mit/ohne App-Hinweis', not bad, list(bad.items())[:3])
        check('Handy: Logo „kragr“ beginnt höchstens 64 px unter dem oberen Rand (vorher ~110 px)', all(v<=64 for v in gap.values()), gap)
        pg=await br.new_page(viewport={'width':844,'height':340})
        await pg.goto(U+'index.html'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.documentElement.scrollHeight, getComputedStyle(document.querySelector('.card-title')).fontSize]")
        check('Handy quer (340 px hoch): normale Größen, Scrollen erlaubt', r[0]>340 and float(r[1][:-2])>=30, r)
        await pg.close()
        # Schalter rechts neben der Sprachwahl, Versionen auf dem Rechner sichtbar, auf dem Handy ausgeblendet
        pg=await br.new_page(viewport={'width':390,'height':664})
        await pg.goto(U+'index.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[Math.round(document.getElementById('theme-btn').getBoundingClientRect().right), Math.round(document.getElementById('langSwitcher').getBoundingClientRect().left), getComputedStyle(document.querySelector('.fm-ver')).display]")
        check('Handy: Hell/Dunkel-Schalter direkt links der Sprachwahl, Versionen ausgeblendet', 0<=r[1]-r[0]<=12 and r[2]=='none', r)
        # Hinweis „als App“ ausblenden, bleibt aus
        await pg.goto('about:blank'); await pg.goto(U+'index.html'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('install').hidden=false")
        await pg.click('#install-x'); h1=await pg.evaluate("document.getElementById('install').hidden")
        lab=await pg.evaluate("document.getElementById('install-x').getAttribute('aria-label')")
        check('Hinweis „als App“: × blendet aus, gespeichert, Beschriftung übersetzt', h1 and await pg.evaluate("localStorage.getItem('muly-install-aus')")=='1' and lab=='Ausblenden', lab)
        await pg.close()
        # Glasleiste auf allen sechs Seiten
        res={}
        pg=await br.new_page(viewport={'width':390,'height':700})
        for f in ['index','calc','size','ref','projekt','rechtliches']:
            await pg.goto(U+f+'.html'); await pg.wait_for_timeout(300)
            res[f]=await pg.evaluate("""(()=>{const e=document.querySelector('header.glass'); if(!e) return 'fehlt'; const c=getComputedStyle(e), b=getComputedStyle(e,'::before');
               return [c.position, c.backgroundColor, (b.backdropFilter||b.webkitBackdropFilter||'').includes('blur'), b.backgroundImage.includes('0.6') || b.backgroundColor.includes('0.72')]})()""")
        ok=all(v!='fehlt' and v[0]=='sticky' and v[1]=='rgba(0, 0, 0, 0)' and v[2] and v[3] for v in res.values())
        check('Kopfzeile auf allen Seiten: haftet oben, durchscheinend, Hintergrund weichgezeichnet', ok, res)
        await pg.goto(U+'size.html'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("(()=>{const e=document.querySelector('header.glass'), b=getComputedStyle(e,'::before'); return [Math.round(e.getBoundingClientRect().height), b.bottom, b.maskImage||b.webkitMaskImage]})()")
        check('weicher Rand: Glasfläche 16 px unter die Leiste, nach unten ausgeblendet', r[1]=='-16px' and 'gradient' in r[2], r)
        await pg.goto(U+'index.html'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("getComputedStyle(document.querySelector('header.glass'),'::before').bottom")
        check('Startseite: Leiste ohne Auslauf (Logo darunter bleibt scharf)', r=='0px', r)
        await pg.emulate_media(media='print'); await pg.goto(U+'calc.html'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("getComputedStyle(document.querySelector('header.glass'),'::before').display")
        check('Druck: keine Glasfläche', r=='none', r)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
