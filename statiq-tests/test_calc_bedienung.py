# Bedienung calc v0.9.5/v0.9.6 (seit v0.10.1 ohne „Nachweis in size“): (1) Schnittkräfte über eine Position in „Meine Projekte“
# mit passender Nachweis-Auswahl nach size, (2) Lasten in der Skizze antippen → Bearbeitung direkt unter der Skizze, auf den Träger
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
        # Seit v0.10.1 ist calc eigenständig: kein „Nachweis in size“. Schnittkräfte gehen über eine Position in „Meine Projekte“ nach size.
        check('kein Knopf „Nachweis in size“ mehr', await pg.evaluate("document.querySelectorAll('.k-tosize').length")==0)
        async def sys(tab):   # Position mit System anlegen (Startwerte des Bereichs)
            await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(300); pid=await pg.evaluate("addPos()")
            await pg.goto(B+f'calc.html?pos={pid}'); await pg.wait_for_timeout(900); await pg.evaluate(f"showTab('{tab}')"); await pg.wait_for_timeout(500)
            await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(300); return pid
        async def nw(pid, ziel, part=None):
            await pg.goto(B+f'size.html?pos={pid}&ziel={ziel}'+(f'&part={part}' if part else '')); await pg.wait_for_timeout(1500)
        pb=await sys('beam')
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(300)
        mi=await pg.evaluate(f"[...document.querySelectorAll('#pos-{pb} .addm a')].map(a=>new URLSearchParams(a.getAttribute('href').split('?')[1]).get('ziel')).filter(Boolean)")
        check('Menü Einfeldträger: nur Balken-Nachweise (Stahlbeton Balken/Unterzug/Platte, Stahl, Holz)', mi==['beton.balken','beton.unterzug','beton.platte','stahl.traeger','holz.bauteil'], mi)
        check('keine unpassenden Bereiche (Wasserbau, Grundbau, Mauerwerk, Bauphysik, Stütze)', not any(z.split('.')[0] in ('wasser','grund','mauer','bauph') or 'stuetze' in z for z in mi))
        await nw(pb, 'beton.balken'); r=await pg.evaluate("[MAT, TYP, document.getElementById('in-M')?.value]")
        check('„Stahlbeton · Balken“ öffnet size dort mit max M = 28,13 kNm', r[:2]==['beton','balken'] and r[2] in ('28.13','28.125'), r)
        await nw(pb, 'holz.bauteil'); r=await pg.evaluate("[MAT, HOMODE, $('ho-M').value]")
        check('„Holz · Träger“ öffnet den Holzträger mit M = 28,13 kNm', r[:2]==['holz','bauteil'] and r[2] in ('28.13','28.125'), r)
        pf=await sys('frame')
        mi=await pg.evaluate(f"[...document.querySelectorAll('#pos-{pf} .addm a')].map(a=>{{const q=new URLSearchParams(a.getAttribute('href').split('?')[1]); return q.get('ziel') ? q.get('ziel')+':'+(q.get('part')||'') : null}}).filter(Boolean)")
        check('Menü Rahmen: Riegel als Balken, Stiel als Stütze, Stützenfuß, je Schweißnaht', mi==['beton.balken:riegel','beton.unterzug:riegel','stahl.traeger:riegel','holz.bauteil:riegel','stahl.schweiss:riegel','beton.stuetze:stiel','stahl.traeger:stiel','holz.bauteil:stiel','stahl.fuss:stiel','stahl.schweiss:stiel'], mi)
        await nw(pf, 'stahl.traeger', 'stiel'); r=await pg.evaluate("[MAT, STMODE, $('ci-part').value, parseFloat($('sn-N').value)]")
        check('Rahmen → „Stahl · Stütze“: Stiel mit N = 25 kN übernommen', r==['stahl','traeger','stiel',25], r)
        await nw(pf, 'beton.stuetze', 'stiel'); r=await pg.evaluate("[MAT, TYP, parseFloat($('su-N').value), parseFloat($('su-l').value)]")
        check('Rahmen → „Stahlbeton · Stütze“: N = 25 kN, l = 4 m', r==['beton','stuetze',25,4], r)
        await nw(pf, 'stahl.fuss', 'stiel'); r=await pg.evaluate("[MAT, STMODE, parseFloat($('fp-N').value)]"); check('Rahmen → „Stahl · Stützenfuß“', r==['stahl','fuss',25], r)
        await nw(pf, 'stahl.schweiss', 'riegel'); r=await pg.evaluate("[MAT, STMODE, $('sw-fall').value, +$('sw-M').value, +$('sw-V').value, +$('sw-N').value]")
        check('Rahmen-Riegel → Schweißnaht: Stirnplatte, M = 13,81 kNm, V = 25 kN, N = −3,45 kN am Riegelende', r==['stahl','schweiss','stirn',13.81,25,-3.45], r)
        await nw(pf, 'stahl.schweiss', 'stiel'); r=await pg.evaluate("[+$('sw-M').value, +$('sw-V').value, +$('sw-N').value]")
        check('Rahmen-Stiel → Schweißnaht: M = 13,81 kNm, V = 3,45 kN, N = −25 kN (Druck)', r==[13.81,3.45,-25], r)
        pk=await sys('cantilever')
        mi=await pg.evaluate(f"[...document.querySelectorAll('#pos-{pk} .addm a')].map(a=>new URLSearchParams(a.getAttribute('href').split('?')[1]).get('ziel')).filter(Boolean)")
        check('Menü Kragarm: ohne Unterzug, mit Schweißnaht an der Einspannung', mi==['beton.balken','beton.platte','stahl.traeger','holz.bauteil','stahl.schweiss'], mi)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(300)
        r=await pg.evaluate(f"[...document.querySelectorAll('#pos-{pk} .addm a')].map(a=>a.textContent)")
        check('EN: „Timber · Beam“ im Menü', r[3]=='Timber · Beam', r)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        await nw(pk, 'stahl.schweiss')
        check('Kragarm → Schweißnaht an der Einspannung: M = 37,5 kNm, V = 25 kN', await pg.evaluate("[+$('sw-M').value, +$('sw-V').value, +$('sw-N').value]")==[37.5,25,0])
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
