# Bemessung (size v0.7.14): die Karte „Ergebnis“ (Balken je Nachweis) entfällt; die Leiste über den Nachweiskarten heißt jetzt
# „Ergebnisse“ und trägt das Gesamturteil und „Bericht ansehen“. Fehlerhafte Eingabe: Hinweis in derselben Leiste.
import os, sys, asyncio
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
        for W in (1280,390):
            pg=await br.new_page(viewport={'width':W,'height':1000}); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
            r=await pg.evaluate("""(()=>{ const res=document.getElementById('results'), bar=document.querySelector('#details > .det-bar');
              return { hidden:getComputedStyle(res).display==='none', title:bar.querySelector('.det-t').textContent, sum:(bar.querySelector('.det-sum')||{}).textContent||'',
                ok:bar.querySelector('.det-sum')?.classList.contains('ok'), rep:!!bar.querySelector('.det-rep'), all:!!bar.querySelector('.det-all'),
                cards:document.querySelectorAll('#details > .card[id^="n-"]').length, first:document.querySelector('.col-out').firstElementChild.id||'' }; })()""")
            check(f'{W} px: Karte „Ergebnis“ ausgeblendet', r['hidden'], r)
            check(f'{W} px: Leiste heißt „Ergebnisse“, mit Gesamturteil', r['title']=='Ergebnisse' and 'Alle Nachweise erfüllt' in r['sum'] and r['ok'], r)
            check(f'{W} px: Leiste mit „Alle aufklappen“ und „Bericht ansehen“, Nachweiskarten darunter', r['all'] and r['rep'] and r['cards']>=8, r)
            await pg.click('#details .det-rep'); await pg.wait_for_timeout(300)
            check(f'{W} px: „Bericht ansehen“ öffnet den Bericht', await pg.evaluate("document.body.classList.contains('show-report')"))
            await pg.evaluate("hideReport()"); await pg.wait_for_timeout(200)
            # nicht erfüllt: Urteil rot
            await pg.evaluate("document.getElementById('in-M').value='600'; document.getElementById('in-h').value='30'; run()"); await pg.wait_for_timeout(200)
            r=await pg.evaluate("[document.querySelector('#details .det-sum').className, document.querySelector('#details .det-sum').textContent]")
            check(f'{W} px: nicht erfüllt → Urteil rot', 'bad' in r[0] and 'nicht erfüllt' in r[1], r)
            # ungültige Eingabe
            await pg.evaluate("document.getElementById('in-h').value=''; run()"); await pg.wait_for_timeout(200)
            r=await pg.evaluate("document.querySelector('#details .det-bar')?.innerText||''")
            check(f'{W} px: ungültige Eingabe → Hinweis in der Leiste', 'Bitte Eingaben prüfen' in r, r)
            await pg.close()
        # Stahl und Holz: gleiche Leiste
        pg=await br.new_page(viewport={'width':1280,'height':1000}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(800)
        for m in ('stahl','holz','mauer','grund','wasser','bauph'):
            await pg.evaluate(f"setMat('{m}')"); await pg.wait_for_timeout(300)
            t=await pg.evaluate("[document.querySelector('#details .det-t')?.textContent, !!document.querySelector('#details .det-rep'), getComputedStyle(document.getElementById('results')).display]")
            check(f'{m}: Leiste „Ergebnisse“ mit Bericht-Knopf, keine Ergebnis-Karte', t==['Ergebnisse',True,'none'], t)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
