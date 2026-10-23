# Weg calc → size → „Meine Projekte“ ohne Umwege (size v0.6.7 · projekt v0.1.14): nach „Nachweis in size“ kein Projekt-Fenster,
# sondern eine Hinweisleiste; der Nachweis wird gleich als Position gespeichert (Name aus calc und Nachweis); „Aus calc
# übernehmen“ zeigt die gespeicherten Berechnungen direkt unter dem Knopf; „→ size“ ohne Ziel wählt einen passenden Nachweis;
# „Meine Projekte“ bündelt calc-Berechnung und Nachweis automatisch zu einer Position. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
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
        ctx=await br.new_context(viewport={'width':390,'height':844}); pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.click('#tab-beam .k-tosize'); await pg.click('#tab-beam .k-tsm-i[data-ziel="stahl.traeger"]'); await pg.wait_for_url('**/size.html*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[$('proj-panel').classList.contains('open'), $('ci-banner')?.innerText||'', $('proj-btn').dataset.st, $('sn-name').value, posRead().map(p=>p.name)]")
        check('nach „Nachweis in size“: kein Projekt-Fenster, Hinweisleiste mit den übernommenen Werten', r[0]==False and 'Übernommen aus calc: Einfeldträger L=5m' in r[1] and 'My,Ed = 28,1 kNm' in r[1], r[:2])
        check('Nachweis gleich als Position gespeichert: „Einfeldträger L=5m — Stahl · Träger / Stütze“', r[2]=='saved' and r[3]=='Einfeldträger L=5m — Stahl · Träger / Stütze' and r[4]==[r[3]] and 'In „Meine Projekte“ gespeichert als' in r[1], r[2:])
        await pg.click('#ci-banner .cib-x'); check('Hinweisleiste lässt sich schließen', not await pg.evaluate("!!$('ci-banner')"))
        # derselbe Weg noch einmal: keine zweite Position
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(800); await pg.click('#tab-beam .k-tosize'); await pg.click('#tab-beam .k-tsm-i[data-ziel="stahl.traeger"]'); await pg.wait_for_url('**/size.html*'); await pg.wait_for_timeout(1200)
        check('gleiche Berechnung, gleicher Nachweis: Position wird aktualisiert, nicht verdoppelt', await pg.evaluate("posRead().length")==1)
        # Rahmen: Stiel als Holzstütze
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(800); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(700)
        await pg.click('#tab-frame .k-tosize'); await pg.click('#tab-frame .k-tsm-i[data-ziel="holz.bauteil"][data-part="stiel"]'); await pg.wait_for_url('**/size.html*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[$('ho-name').value, +$('ho-N').value, posRead().length]")
        check('Rahmen-Stiel als Holzstütze: Name mit „Stiel“, N = 25 kN, zweite Position', r[0].startswith('Rahmen') and ' · Stiel — Holz' in r[0] and r[1]==25 and r[2]==2, r)
        # „Aus calc übernehmen“ in der Karte: Liste direkt darunter
        await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.wait_for_timeout(500)
        await pg.evaluate("document.querySelector('.card:has(.card-title[data-i18n=\"z045\"]) .k-ci').scrollIntoView({block:'center'})")
        await pg.click('.card:has(.card-title[data-i18n="z045"]) .k-ci'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('.card:has(.card-title[data-i18n=\"z045\"]) .kci-i')].map(b=>b.innerText.replace(/\\s+/g,' '))")
        check('„Aus calc übernehmen“: Rahmen (Riegel, Stiel) und Einfeldträger als Liste unter dem Knopf', len(r)==3 and r[0].startswith('Rahmen') and 'Riegel' in r[0] and 'Stiel' in r[1] and r[2].startswith('Einfeldträger L=5m'), r)
        await pg.click('.card:has(.card-title[data-i18n="z045"]) .kci-i >> nth=2'); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[$('proj-panel').classList.contains('open'), +$('in-M').value, $('ci-banner')?.innerText.includes('Übernommen aus calc: Einfeldträger L=5m')]")
        check('ein Tipp übernimmt M = 28,13 kNm in den Stahlbetonbalken, Hinweisleiste statt Fenster', r==[False,28.13,True], r)
        # „→ size“ im Projekt-Fenster von calc, während size auf Wasserbau steht
        await pg.evaluate("setMat('wasser')"); await pg.wait_for_timeout(400)
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(800); await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(400)
        await pg.click('#proj-btn'); await pg.wait_for_timeout(200); await pg.click('#pp-list a.pp-btn >> nth=-1'); await pg.wait_for_url('**/size.html*'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[MAT, TYP, +$('in-M').value]")
        check('„→ size“ aus dem calc-Fenster bei Wasserbau: wechselt auf Stahlbeton Balken und übernimmt', r==['beton','balken',28.13], r)
        # Meine Projekte: automatisch gebündelt
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(800)
        r=await pg.evaluate("[proj().pos.map(q=>q.title), document.getElementById('loose').innerText]")
        check('Meine Projekte: je calc-Berechnung eine Position mit ihrem Nachweis, nichts „ohne Position“', sorted(r[0])==sorted(['Einfeldträger L=5m', [t for t in r[0] if t.startswith('Rahmen')][0] if any(t.startswith('Rahmen') for t in r[0]) else 'Rahmen']) and 'Alles ist zugeordnet' in r[1], r)
        t=await pg.inner_text('#list')
        check('Position zeigt calc-Berechnung und Nachweis zusammen', 'Einfeldträger L=5m — Stahl · Träger / Stütze' in t and 'Holz' in t, t[:160])
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
