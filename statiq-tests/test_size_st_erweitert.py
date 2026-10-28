# Stahlträger (size v0.7.13): M_z, Torsion und Einzellast auf den Gurt nicht mehr als eigene Karte „Weitere Einwirkungen“,
# sondern als „Erweitert“ in der Karte Schnittgrößen (k5-Akkordeon, standardmäßig zu, Kurzfassung der gesetzten Werte).
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':1400}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("setMat('stahl'); setStMode('traeger')"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("""(()=>{ const a=document.getElementById('st-adv'), c=a.closest('.card');
          return { inCard: c.contains(document.getElementById('sn-M')), acc:a.classList.contains('k5-acc'), closed:a.classList.contains('k5-closed'),
            ids:['sn-Mz','sn-tors','sn-Tw','sn-F','sn-ss','sn-lage','sn-cE'].every(i=>a.contains(document.getElementById(i))),
            oldCard:[...document.querySelectorAll('#st-traeger .card > .card-title, #st-traeger .card > .k5-head .card-title')].some(t=>/Weitere Einwirkungen/.test(t.textContent)),
            title:a.querySelector('.card-title').textContent } })()""")
        check('„Erweitert“ in der Karte Schnittgrößen, mit allen Feldern', r['inCard'] and r['ids'], r)
        check('als Akkordeon, standardmäßig zu', r['acc'] and r['closed'], r)
        check('keine eigene Karte „Weitere Einwirkungen“ mehr', not r['oldCard'])
        check('Titel nennt Inhalt: Biegung um z, Torsion, Einzellast', 'Biegung um z' in r['title'] and 'Torsion' in r['title'] and 'Gurt' in r['title'], r['title'])
        await pg.click('#st-adv > .k5-head'); await pg.wait_for_timeout(300)
        o=await pg.evaluate("[!document.getElementById('st-adv').classList.contains('k5-closed'), document.getElementById('sn-Mz').offsetParent!==null]")
        check('Klick öffnet, Felder sichtbar', all(o), o)
        await pg.fill('#sn-Mz','8'); await pg.fill('#sn-F','40'); await pg.wait_for_timeout(200)
        t=await pg.inner_text('.col-out')
        check('Werte wirken auf die Rechnung (M_z im Nachweis)', 'M' in t and await pg.evaluate("LAST && LAST.I && LAST.I.Mz===8"), await pg.evaluate("LAST && LAST.I && LAST.I.Mz"))
        await pg.click('#st-adv > .k5-head'); await pg.wait_for_timeout(300)
        s=await pg.evaluate("document.querySelector('#st-adv > .k5-head .k5-hsum').textContent")
        check('zu: Kurzfassung zeigt M_z und F', 'Mz,Ed 8 kNm' in s and 'F 40 kN' in s, s)
        # Zustand bleibt nach dem Neuladen (gespeichert)
        await pg.reload(); await pg.wait_for_timeout(900); await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(300)
        check('nach Neuladen bleibt der zuletzt gewählte Zustand (zu)', await pg.evaluate("document.getElementById('st-adv').classList.contains('k5-closed')"))
        for L,w in (('en','Advanced'),('fr','Avancé'),('es','Avanzado')):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(800); await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(300)
            t=await pg.evaluate("document.querySelector('#st-adv .card-title').textContent")
            check(f'{L}: Titel übersetzt', t.startswith(w) and not re.search(r'Erweitert|Biegung|Einzellast', t), t)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
