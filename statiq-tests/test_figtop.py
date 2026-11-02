# Bemessung am Handy (size v0.7.18): die Abbildungskarte (Querschnitt/Profil) steht direkt unter der Auswahl, vor den Eingaben —
# ohne Mitlaufen und Verkleinern (v0.7.17 wieder verworfen). Am Rechner bleibt sie rechts. Dazu: nach jedem Wechsel des Nachweises
# ist die erste Eingabekarte offen, alle anderen zu.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
POS="""(()=>{ const c=document.getElementById('fig').closest('.card'), col=document.querySelector('.col-in'), pick=col.querySelector('.pick-g').closest('.col-in > *');
  const folds=[...col.querySelectorAll('.card.fold')].filter(x=>x.offsetParent);
  return {inCol:col.contains(c), afterPick:pick.nextElementSibling && pick.nextElementSibling.contains(c), beforeInputs:folds.length>0 && (c.compareDocumentPosition(folds[0]) & Node.DOCUMENT_POSITION_FOLLOWING)>0,
    top:Math.round(c.getBoundingClientRect().top+scrollY), fixed:getComputedStyle(c).position, svg:!!c.querySelector('#fig svg')}; })()"""
FOLD="[...document.querySelectorAll('.col-in .card.fold')].filter(c=>c.offsetParent).map(c=>!c.classList.contains('closed'))"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        r=await pg.evaluate(POS)
        check('Handy: Abbildung direkt unter der Auswahl, vor den Eingaben', r['inCol'] and r['afterPick'] and r['beforeInputs'] and r['svg'] and r['top']<400, r)
        await pg.evaluate("scrollTo(0,600)"); await pg.wait_for_timeout(200)
        r2=await pg.evaluate("[document.getElementById('fig').closest('.card').getBoundingClientRect().top, !!document.getElementById('fd')]")
        check('kein Mitlaufen oder Verkleinern mehr (scrollt normal weg)', r2[0]<0 and not r2[1], r2)
        await pg.fill('#in-h','70'); await pg.wait_for_timeout(300)
        check('Eingabe ändert die Abbildung oben', '70 cm' in await pg.inner_text('#fig'))
        for m in ('stahl','holz','mauer','grund','wasser','bauph'):
            await pg.evaluate(f"setMat('{m}')"); await pg.wait_for_timeout(400)
            r=await pg.evaluate(POS); f=await pg.evaluate(FOLD)
            check(f'{m}: Abbildung oben; erste Eingabekarte offen, alle anderen zu', r['afterPick'] and r['beforeInputs'] and f and f[0] and not any(f[1:]), (r['afterPick'], f))
        await pg.evaluate("setMat('beton')"); await pg.wait_for_timeout(300)
        await pg.click('.col-in .card.fold:nth-of-type(3) > .card-title'); await pg.wait_for_timeout(400)
        for lab in ['Stütze','Torsion','Balken']:
            await pg.click('#pick'); await pg.wait_for_timeout(300); await pg.click(f'.pick-menu >> text={lab}'); await pg.wait_for_timeout(500)
            f=await pg.evaluate(FOLD)
            check(f'Auswahl „{lab}“: erste Eingabekarte offen, alle anderen zu', f and f[0] and not any(f[1:]), f)
        d=await br.new_page(viewport={'width':1280,'height':900}); d.on('pageerror', lambda e: errs.append(str(e)))
        await d.goto(B+'size.html'); await d.wait_for_timeout(800)
        r=await d.evaluate("[document.querySelector('.col-out').contains(document.getElementById('fig')), document.getElementById('fig').closest('.card').nextElementSibling?.id]")
        check('Rechner: Abbildung rechts über den Ergebnissen', r[0] and r[1]=='details', r)
        await d.set_viewport_size({'width':390,'height':844}); await d.wait_for_timeout(300)
        r=await d.evaluate(POS)
        check('Fenster schmal gezogen: Abbildung wandert nach oben', r['afterPick'], r)
        await d.set_viewport_size({'width':1280,'height':900}); await d.wait_for_timeout(300)
        check('wieder breit: zurück nach rechts', await d.evaluate("document.querySelector('.col-out').contains(document.getElementById('fig'))"))
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
