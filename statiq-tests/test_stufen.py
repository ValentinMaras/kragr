# Eingabe in Stufen (calc v0.11.5): Skizze oben, darunter ① Abmessungen ② Lager und Gelenke ③ Lasten (Rahmen, Durchlaufträger),
# „Erweitert“ (Riegelform, Kopfhalterung, Steifigkeit EI, Lastfälle); zugeklappte Stufen mit Zusammenfassung, „Weiter“ zur nächsten Stufe,
# Zustand gemerkt. Ergebnisse: Rechenweg, Knoten und Lastfälle zugeklappt mit Kopfzeile. Keine Eingabe geht verloren (gleiche ids).
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
ST="t=>[...document.querySelectorAll('#tab-'+t+' .col-in [data-st]')].map(c=>[c.dataset.st, !c.classList.contains('k-closed'), (c.querySelector(':scope > .k-head .k-sum')||{}).textContent])"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400)
        s=await pg.evaluate(ST, 'frame')
        check('Rahmen: Stufen Abmessungen · Lager · Lasten · Erweitert in dieser Reihenfolge', [x[0] for x in s]==['dims','sup','loads','adv'], s)
        check('Erster Besuch: ① offen, ② zu, ③ offen, Erweitert zu', [x[1] for x in s]==[True,False,True,False], s)
        check('Zusammenfassungen: „b = 5 m · h = 4 m“, „A ⊞ · B △ · n = 2“, „2 Lasten“, „Standard“', s[0][2]=='b = 5 m · h = 4 m' and s[1][2]=='A ⊞ · B △ · n = 2' and s[2][2]=='2 Lasten' and s[3][2]=='Standard', s)
        r=await pg.evaluate("""['fB','fHA','btn-preset-three','btn-sA-fixed','btn-sB-pin','frame-hinge-list','frame-indet-info','btn-roof-gable','btn-sH-left','frame-E-raf','frame-Iy-col','lf-on-frame']
          .map(id=>{ const e=document.getElementById(id); return e ? (e.closest('[data-st]')||{dataset:{}}).dataset.st || 'top' : null; })""")
        check('Alle Eingaben noch da und in der richtigen Stufe (Maße ①, Lager ②, Rest unter Erweitert)', r==['dims','dims','sup','sup','sup','sup','sup','adv','adv','adv','adv','adv'], r)
        check('Skizze bleibt oben sichtbar', await pg.is_visible('#frame-svg'))
        r=await pg.evaluate("[...document.querySelectorAll('#tab-frame .k-stn')].map(e=>e.textContent)")
        check('Nummern ① ② ③ an den Stufen', r==['1','2','3'], r)
        # Weiter
        await pg.click('#tab-frame [data-st=dims] .k-st-next'); await pg.wait_for_timeout(300)
        s=await pg.evaluate(ST, 'frame')
        check('„Weiter: Lager und Gelenke ›“ klappt ① zu und ② auf', [x[1] for x in s][:2]==[False,True], s)
        check('Lager-Schalter jetzt sichtbar und bedienbar', await pg.is_visible('#btn-preset-three'))
        await pg.click('#btn-preset-three'); await pg.wait_for_timeout(400)
        s=await pg.evaluate(ST, 'frame')
        check('Zusammenfassung folgt: „Dreigelenkrahmen · statisch bestimmt“', s[1][2]=='Dreigelenkrahmen · statisch bestimmt', s[1])
        await pg.evaluate("fB.value=6; fB.dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(300)
        s=await pg.evaluate(ST, 'frame')
        check('Zugeklappte Stufe ① zeigt die neue Breite (b = 6 m)', s[0][2].startswith('b = 6 m'), s[0])
        # Erweitert
        await pg.click('#tab-frame [data-st=adv] > .k-head'); await pg.wait_for_timeout(300)
        await pg.click('#btn-roof-gable'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('frame-E-raf').value=100; document.getElementById('frame-E-raf').dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(300)
        await pg.click('#lf-on-frame'); await pg.wait_for_timeout(600)
        s=await pg.evaluate(ST, 'frame')
        check('Erweitert meldet Abweichungen: „Satteldach · EI geändert · Lastfälle an“', s[3][2]=='Satteldach · EI geändert · Lastfälle an', s[3])
        check('Abmessungen nennen das Satteldach (b = 6 m · h = 4 m · Satteldach f = 1 m)', s[0][2]=='b = 6 m · h = 4 m · Satteldach f = 1 m', s[0])
        # Zustand bleibt
        await pg.evaluate("k4Save(true)"); await pg.reload(); await pg.wait_for_timeout(1000); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400)
        s=await pg.evaluate(ST, 'frame')
        check('Neu laden: offene und zugeklappte Stufen wie zuletzt', [x[1] for x in s]==[False,True,True,True], s)
        # EI-Hinweis im w-Diagramm
        await pg.evaluate("setDiagMode('frame','W')"); await pg.wait_for_timeout(200)
        r=await pg.evaluate("[getComputedStyle(document.getElementById('ei-hint-frame')).display, document.getElementById('ei-input-frame').closest('[data-st]').dataset.st]")
        check('w-Diagramm: Hinweis „EI ändern: Erweitert öffnen“ statt der Eingabe', r==['block','adv'] or (r[0]!='none' and r[1]=='adv'), r)
        await pg.click('#ei-hint-frame button'); await pg.wait_for_timeout(300)
        check('Hinweis öffnet „Erweitert“', await pg.evaluate("!document.querySelector('#tab-frame [data-st=adv]').classList.contains('k-closed')"))
        await pg.evaluate("setDiagMode('frame','M')")
        # Ergebnisse
        # Knotenkarte: mit der Design-Schicht k5 faltet k5 sie (eine Kopfzeile, calc v0.11.8)
        r=await pg.evaluate("[document.querySelector('#frame-results .k-knoten').classList.contains('k5-closed'), document.querySelector('#frame-results .k-knoten .k5-hsum').textContent, !!document.querySelector('#frame-results .k-knoten .k-kn-tab').offsetParent, document.getElementById('rw-frame').classList.contains('closed'), document.querySelectorAll('#frame-results .k-knoten .k-fsum').length]")
        check('Ergebnisse: Knoten zugeklappt mit „6 Knoten · 5 Stäbe“ (Gelenk + First), Rechenweg zugeklappt, nur eine Kopfzeile', r[0] and r[1]=='6 Knoten · 5 Stäbe' and not r[2] and r[3] and r[4]==0, r)
        await pg.click('#frame-results .k-knoten > .k5-head'); await pg.wait_for_timeout(300)
        check('Antippen der Kopfzeile öffnet die Knotentabelle', await pg.evaluate("!!document.querySelector('#frame-results .k-knoten .k-kn-tab').offsetParent"))
        r=await pg.evaluate("[document.querySelector('#frame-results .k-lfres').classList.contains('k-closed'), !!document.querySelector('#frame-results .k-lfres .k-lfchips').offsetParent, document.querySelector('#frame-results .k-lfres .k-fsum').textContent]")
        check('Lastfälle-Karte zugeklappt, Ansichts-Chips bleiben sichtbar, Kopfzeile nennt max M mit Kombination', r[0] and r[1] and r[2].startswith('max M = ') and ' kNm · ' in r[2] and '·G' in r[2], r)
        # Durchlaufträger
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("""[!!document.querySelector('#tab-cont [data-st=dims] #span-length-inputs input'), !!document.querySelector('#tab-cont [data-st=sup] #cont-sup-inputs select'),
           !!document.querySelector('#tab-cont [data-st=sup] #cont-hinge-list'), !!document.querySelector('#tab-cont [data-st=loads] #span-load-cards .k-loads'), !document.querySelector('#span-length-inputs select')]""")
        check('Durchlaufträger: Felder in ①, Endlager/Kragarme/Gelenke in ②, Lasten je Feld in ③', all(r), r)
        await pg.evaluate("addContHinge()")
        for _ in range(20):   # Kurzfassung baut sich verzögert neu (unter Last im Gesamtlauf langsamer)
            await pg.wait_for_timeout(150); s=await pg.evaluate(ST, 'cont')
            if s[1][2].endswith('1 Gelenk'): break
        check('Zusammenfassungen: „2 Felder · L = 5 / 5 m“, Lager mit „1 Gelenk“', s[0][2]=='2 Felder · L = 5 / 5 m' and s[1][2].endswith('1 Gelenk'), s)
        # Einfeldträger
        await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(300)
        s=await pg.evaluate(ST, 'beam')
        check('Einfeldträger: Länge bleibt an der Skizze, Stufen Lasten und Erweitert', [x[0] for x in s]==['loads','adv'] and await pg.is_visible('#bL'), s)
        # Englisch
        await pg.evaluate("setCalcLang('en'); showTab('frame')"); await pg.wait_for_timeout(300)
        t=await pg.inner_text('#tab-frame .col-in')
        check('Englisch: „Dimensions“, „Supports and hinges“, „Advanced“, „Next: …“', 'Dimensions' in t and 'Supports and hinges' in t and 'Advanced' in t and 'Next: Supports and hinges' in await pg.evaluate("document.querySelector('#tab-frame .k-st-next').textContent"), '')
        await pg.close()
        # Handy: kein seitliches Scrollen
        pm=await br.new_page(viewport={'width':360,'height':780}); pm.on('pageerror', lambda e: errs.append(str(e)))
        await pm.goto(B+'calc.html'); await pm.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','fr')"); await pm.reload(); await pm.wait_for_timeout(900)
        w=[]
        for t in ['beam','cantilever','cont','frame']:
            await pm.evaluate(f"showTab('{t}'); document.querySelectorAll('#tab-{t} .k-st.k-closed').forEach(c=>k11Set(c,true))"); await pm.wait_for_timeout(300)
            w.append(await pm.evaluate("document.documentElement.scrollWidth"))
        check('Handy 360 px (Französisch, alle Stufen offen): kein seitliches Scrollen', all(x<=360 for x in w), w)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print(f"\n{'ALLE OK' if not fails else str(fails)+' FEHLER'}"); sys.exit(1 if fails else 0)
