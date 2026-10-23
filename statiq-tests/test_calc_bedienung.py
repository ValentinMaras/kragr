# Bedienung calc v0.9.5: (1) „Nachweis in size“ unter den Ergebnissen (legt die Berechnung bei Bedarf in „Meine Projekte“,
# öffnet size mit den Schnittgrößen), (2) Lasten in der Skizze antippen → Bearbeitung direkt unter der Skizze, auf den Träger
# tippen setzt eine neue Einzellast, (3) Eingaben werden als Entwurf gesichert und beim nächsten Öffnen wiederhergestellt.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
NS="Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_')).length"
async def tap(pg, svgsel, x, y):   # Koordinaten im SVG (viewBox 320 breit)
    bb=await (await pg.query_selector(svgsel)).bounding_box(); s=bb['width']/320
    await pg.mouse.click(bb['x']+x*s, bb['y']+y*s); await pg.wait_for_timeout(700)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        ctx=await br.new_context(viewport={'width':390,'height':844}); pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        check('Hinweis unter der Skizze', 'auf den Träger für eine neue Einzellast' in await pg.inner_text('#tab-beam .k-taphint'))
        # (2) Träger antippen bei x = 1 m
        await tap(pg, '#beam-svg', 30+260*1/5, 74)
        r=await pg.evaluate("[loads.beam.point.map(l=>l.values.a), document.querySelector('#tab-beam .k-edit .load-item-label b')?.textContent, document.getElementById('b-res-A').textContent, !!document.querySelector('#beam-svg .k-selmark')]")
        check('Tipp auf den Träger bei 1 m: neue Einzellast F2 (a = 1 m), Bearbeitung unter der Skizze, Markierung', r[0]==[2.5,1] and r[1]=='F2' and r[2]=='25.50' and r[3], r)
        await pg.click('#tab-beam .k-edit .k-stpv .k-sb >> nth=1'); await pg.wait_for_timeout(600)
        r=await pg.evaluate("[loads.beam.point[1].values.F, document.querySelectorAll('#beam-point-list .load-sum')[1].textContent, [...document.querySelectorAll('#tab-beam .k-chip')].map(c=>c.textContent)[1]]")
        check('Stepper unter der Skizze: F2 = 11 kN, Liste und Chip ziehen mit', r==[11,'F = 11 kN · @ 1 m','F2 11 kN'], r)
        # Streckenlast in der Skizze antippen
        await tap(pg, '#beam-svg', 30+260*4/5, 50)
        r=await pg.evaluate("[document.querySelector('#tab-beam .k-edit .load-item-label b')?.textContent, document.querySelector('#tab-beam .k-chip.k-dist').getAttribute('aria-pressed')]")
        check('Tipp auf die Streckenlast wählt q1 (Chip gefüllt)', r==['q1','true'], r)
        await pg.click('#tab-beam .k-chip.k-dist'); await pg.wait_for_timeout(300)
        check('erneuter Tipp auf den Chip schließt die Bearbeitung', await pg.evaluate("document.querySelector('#tab-beam .k-edit').children.length")==0)
        await tap(pg, '#beam-svg', 30+260*2.5/5, 30)
        check('Tipp auf F1 in der Skizze wählt F1', await pg.evaluate("document.querySelector('#tab-beam .k-edit .load-item-label b')?.textContent")=='F1')
        await pg.click('#tab-beam .k-edit .load-item-header'); await pg.wait_for_timeout(300)
        check('Tipp auf die Kopfzeile (✕) schließt', await pg.evaluate("document.querySelector('#tab-beam .k-edit').children.length")==0)
        await pg.evaluate("showTab('cantilever')"); await pg.wait_for_timeout(500)
        await tap(pg, '#cant-svg', 50+240*2/3, 74)
        check('Kragarm: Tipp auf den Träger bei 2 m setzt F2', await pg.evaluate("loads.cant.point.map(l=>l.values.a)")==[1.5,2])
        await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(400)
        # (3) Entwurf
        await pg.wait_for_timeout(900); await pg.reload(); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[loads.beam.point.map(l=>[l.values.a,l.values.F]), loads.cant.point.length, document.getElementById('b-res-A').textContent, typeof uid==='number']")
        check('Entwurf: nach dem Neuladen sind die Lasten und das Ergebnis wieder da', r[0]==[[2.5,10],[1,11]] and r[1]==2 and r[2]=='26.30', r)
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(500); await pg.evaluate("document.getElementById('fB').value='6'; document.getElementById('fB').dispatchEvent(new Event('input',{bubbles:true})); setSupportA('pin')"); await pg.wait_for_timeout(900)
        await pg.reload(); await pg.wait_for_timeout(1000)
        r=await pg.evaluate("[curTab(), document.getElementById('fB').value, supportA]")
        check('Entwurf: Rahmen-Bereich, Breite 6 m und Lager A bleiben erhalten', r==['frame','6','pin'], r)
        await pg.evaluate("addLoad('beam','dist')"); await pg.wait_for_timeout(300)
        n=await pg.evaluate("(()=>{const ids=[...loads.beam.point,...loads.beam.dist,...loads.cant.point,...loads.cant.dist,...frameLoads.vert,...frameLoads.horiz].map(l=>l.id); return new Set(ids).size===ids.length})()")
        check('neue Lasten bekommen nach dem Wiederherstellen eindeutige Nummern', n)
        # Neu beginnen (im Projekt-Fenster, mit Rückfrage am Knopf)
        await pg.click('#proj-btn'); await pg.wait_for_timeout(200)
        t=await pg.inner_text('#pp-extra .k-draft')
        await pg.click('#pp-extra .k-draft button'); a1=await pg.inner_text('#pp-extra .k-draft button')
        await pg.click('#pp-extra .k-draft button'); await pg.wait_for_timeout(1200)
        r=await pg.evaluate("[curTab(), loads.beam.point.length, document.getElementById('fB').value, localStorage.getItem('muly-calc-entwurf')===null || JSON.parse(localStorage.getItem('muly-calc-entwurf')).loads.beam.point.length===1]")
        check('„Neu beginnen“: Hinweis, erst „Wirklich zurücksetzen?“, dann Startwerte', 'automatisch gesichert' in t and a1=='Wirklich zurücksetzen?' and r[:3]==['beam',1,'5'], (t,a1,r))
        # (1) Nachweis in size
        n0=await pg.evaluate(NS); b=await pg.inner_text('#tab-beam .k-tosize')
        check('Knopf „Nachweis in size“ unter den Ergebnissen', 'Nachweis in size' in b and 'übernimmt M, V und N' in b, b)
        await pg.click('#tab-beam .k-tosize'); await pg.wait_for_timeout(1800)
        r=await pg.evaluate("[location.pathname.endsWith('size.html'), document.getElementById('in-M')?.value, document.getElementById('ci-msg')?.innerText.slice(0,40)]")
        check('öffnet size mit max M = 28,13 kNm aus calc', r[0] and r[1] in ('28.13','28.125'), r)
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(900)
        n1=await pg.evaluate(NS); await pg.click('#tab-beam .k-tosize'); await pg.wait_for_timeout(1500); await pg.goto(B+'calc.html'); await pg.wait_for_timeout(700)
        n2=await pg.evaluate(NS)
        check('dabei einmal in „Meine Projekte“ gelegt, beim zweiten Mal keine Kopie', n1==n0+1 and n2==n1, (n0,n1,n2))
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(700); await pg.click('#tab-frame .k-tosize'); await pg.wait_for_timeout(1800)
        check('Rahmen: ebenfalls direkt nach size', await pg.evaluate("location.pathname.endsWith('size.html') && parseFloat(document.getElementById('in-M')?.value||0)>0"))
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(700)
        await pg.evaluate("localStorage.setItem('muly-uebung','1')"); await pg.reload(); await pg.wait_for_timeout(900)
        check('Übungsmodus: kein „Nachweis in size“ (Ergebnis bleibt verborgen)', await pg.evaluate("getComputedStyle(document.querySelector('#tab-beam .k-tosize')).display")=='none')
        await pg.evaluate("localStorage.setItem('muly-uebung','0')")
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
