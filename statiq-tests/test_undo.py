# Rückgängig (calc v0.11.44 · size v0.7.46, 13.11.2026): Knopf links neben dem Menü-Knopf in Schnittkräfte und Bemessung
# (k5/undo.js). Ein Schritt = abgeschlossene Änderung; Reiter-/Nachweiswechsel ist kein Schritt, beim Zurücknehmen springt die Seite
# aber dorthin. „Wiederholen“ als gespiegelter Pfeil rechts daneben (seit calc v0.11.45 · size v0.7.47 statt eines Hinweises),
# Strg+Z / Strg+Umschalt+Z außerhalb von Feldern.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
DIS="document.getElementById('k5-undo').disabled"
SET={'beton':'setTyp','stahl':'setStMode','holz':'setHoMode','mauer':'setMwMode','grund':'setGrMode','wasser':'setWbMode','bauph':'setBpMode'}

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for w,h,mob in ((1280,900,False),(390,844,True)):
            tag='Rechner' if not mob else 'Handy'
            pg=await br.new_page(viewport={'width':w,'height':h}, is_mobile=mob, has_touch=mob); pg.on('pageerror', lambda e: errs.append(str(e)))
            # ── Bemessung ──
            await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
            r=await pg.evaluate("(()=>{ const u=document.getElementById('k5-undo'), w=document.getElementById('k5-redo'), b=document.getElementById('k5-burger'); if(!u||!w) return null; const a=u.getBoundingClientRect(), d=w.getBoundingClientRect(), c=b.getBoundingClientRect();"
                                " return [u.nextElementSibling===w && w.nextElementSibling===b, a.right<=d.left && d.right<=c.left, Math.abs(a.top-c.top)<2 && Math.abs(d.top-c.top)<2, Math.round(a.height), Math.round(c.height), u.disabled && w.disabled, u.getAttribute('aria-label'), w.getAttribute('aria-label'), getComputedStyle(w.querySelector('svg')).transform]; })()")
            check(f'{tag} Bemessung: Rückgängig und Wiederholen links neben dem Menü, gleiche Höhe, anfangs aus', r and r[0] and r[1] and r[2] and r[3]==r[4] and r[5] and r[6]=='Rückgängig' and r[7]=='Wiederholen', r)
            check(f'{tag} Bemessung: Wiederholen = derselbe Pfeil gespiegelt', r and r[8].startswith('matrix(-1'), r and r[8])
            await pg.mouse.click(5, 500); await pg.wait_for_timeout(300)
            check(f'{tag} Bemessung: Klick ins Leere ist kein Schritt', await pg.evaluate(DIS))
            await pg.fill('#in-h','70'); await pg.locator('#in-h').blur(); await pg.wait_for_timeout(250)
            await pg.fill('#in-M','300'); await pg.wait_for_timeout(100)   # noch im Feld: zählt beim Zurücknehmen als eigener Schritt
            check(f'{tag} Bemessung: nach einer Eingabe aktiv', not await pg.evaluate(DIS))
            await pg.click('#k5-undo'); await pg.wait_for_timeout(300)
            r=await pg.evaluate("[$('in-h').value, $('in-M').value, document.getElementById('k5-redo').disabled, !document.querySelector('.k5-undo-toast')]")
            check(f'{tag} Bemessung: erster Schritt zurück nimmt das zuletzt Getippte zurück, Wiederholen wird aktiv, kein Hinweis', r==['70','220',False,True], r)
            r=await pg.evaluate("[...document.querySelectorAll('.k5-undone')].some(f=>f.contains($('in-M')))")
            check(f'{tag} Bemessung: zurückgenommenes Feld kurz hinterlegt', r)
            await pg.click('#k5-undo'); await pg.wait_for_timeout(300)
            check(f'{tag} Bemessung: zweiter Schritt zurück, danach nichts mehr', await pg.evaluate("[$('in-h').value, $('in-M').value]")==['60','220'] and await pg.evaluate(DIS))
            await pg.click('#k5-redo'); await pg.wait_for_timeout(300)
            check(f'{tag} Bemessung: „Wiederholen“ stellt den Schritt wieder her', await pg.evaluate("$('in-h').value")=='70' and not await pg.evaluate(DIS))
            await pg.click('#k5-redo'); await pg.wait_for_timeout(300)
            check(f'{tag} Bemessung: zweimal Wiederholen, danach aus', await pg.evaluate("[$('in-h').value, $('in-M').value, document.getElementById('k5-redo').disabled]")==['70','300',True])
            await pg.click('#k5-undo'); await pg.wait_for_timeout(300)
            # Wechsel des Nachweises: kein Schritt, auch wo der Wechsel Vorgaben in Felder schreibt
            await pg.click('#k5-undo'); await pg.wait_for_timeout(300); await pg.mouse.click(5,500); await pg.wait_for_timeout(200)
            pa=await pg.evaluate('Object.keys(PA)'); bad=[]
            for k in pa:
                mat,m=k.split('/'); await pg.evaluate(f"setMat('{mat}'); {SET[mat]}('{m}')"); await pg.mouse.click(5,500); await pg.wait_for_timeout(80)
                if not await pg.evaluate(DIS): bad.append(k); break
            check(f'{tag} Bemessung: Wechsel durch alle Nachweise erzeugt keinen Schritt', not bad, bad)
            # Änderung in einem Nachweis, Wechsel, Zurücknehmen → springt zurück
            await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.mouse.click(5,500); await pg.fill('#in-b','35'); await pg.locator('#in-b').blur(); await pg.wait_for_timeout(200)
            await pg.evaluate("setMat('holz')"); await pg.mouse.click(5,500); await pg.wait_for_timeout(200)
            await pg.click('#k5-undo'); await pg.wait_for_timeout(400)
            check(f'{tag} Bemessung: Zurücknehmen springt in den Nachweis der Änderung', await pg.evaluate("[MAT, TYP, $('in-b').value]")==['beton','balken','30'], await pg.evaluate("[MAT, TYP, $('in-b').value]"))
            # Tastatur: im Feld Rückgängig des Browsers, außerhalb der Verlauf
            await pg.fill('#in-b','40'); await pg.locator('#in-b').blur(); await pg.wait_for_timeout(200)
            await pg.mouse.click(5,500); await pg.wait_for_timeout(200); await pg.keyboard.press('Control+z'); await pg.wait_for_timeout(300)
            check(f'{tag} Bemessung: Strg+Z außerhalb nimmt zurück', await pg.evaluate("$('in-b').value")=='30')
            await pg.keyboard.press('Control+Shift+Z'); await pg.wait_for_timeout(300)
            check(f'{tag} Bemessung: Strg+Umschalt+Z wiederholt', await pg.evaluate("$('in-b').value")=='40')
            await pg.keyboard.press('Control+z'); await pg.wait_for_timeout(300)   # b wieder 30, „Wiederholen“ möglich
            await pg.fill('#in-l','7'); await pg.locator('#in-l').blur(); await pg.mouse.click(5,500); await pg.wait_for_timeout(200)
            await pg.keyboard.press('Control+Shift+Z'); await pg.wait_for_timeout(300)
            check(f'{tag} Bemessung: neue Änderung verwirft „Wiederholen“', await pg.evaluate("[$('in-b').value, $('in-l').value]")==['30','7'], await pg.evaluate("[$('in-b').value, $('in-l').value]"))
            await pg.focus('#in-h'); f0=await pg.evaluate("kragrUndoInfo().back"); await pg.keyboard.press('Control+z'); await pg.wait_for_timeout(250)
            check(f'{tag} Bemessung: Strg+Z im Feld: Rückgängig des Browsers, nicht der Verlauf', await pg.evaluate("kragrUndoInfo()")=={'back':f0,'fwd':0,'armed':True}, await pg.evaluate("kragrUndoInfo()"))
            # ── Schnittkräfte ──
            await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
            check(f'{tag} Schnittkräfte: Knopf da, anfangs aus', await pg.evaluate("!!document.getElementById('k5-undo') && document.getElementById('k5-undo').disabled"))
            await pg.mouse.click(5, 500); await pg.wait_for_timeout(300)
            for t in ['cantilever','cont','frame','beam']:
                await pg.evaluate(f"showTab('{t}')"); await pg.mouse.click(5,500); await pg.wait_for_timeout(250)
            check(f'{tag} Schnittkräfte: Klick ins Leere und Reiterwechsel sind keine Schritte', await pg.evaluate(DIS))
            n0=await pg.evaluate("loads.beam.point.length")
            await pg.evaluate("document.querySelector('#tab-beam .add-load-btn[onclick*=\"point\"]').click()"); await pg.wait_for_timeout(300)
            await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(200)
            await pg.evaluate("document.getElementById('btn-sA-pin').click()"); await pg.wait_for_timeout(300)
            r=await pg.evaluate("[loads.beam.point.length, supportA]")
            check(f'{tag} Schnittkräfte: Last hinzu (Träger), Lager geändert (Rahmen)', r==[n0+1,'pin'], r)
            await pg.click('#k5-undo'); await pg.wait_for_timeout(400)
            check(f'{tag} Schnittkräfte: zurück → Lager wieder eingespannt', await pg.evaluate("supportA")=='fixed' and await pg.evaluate("document.getElementById('btn-sA-fixed').classList.contains('active')"))
            await pg.click('#k5-undo'); await pg.wait_for_timeout(400)
            r=await pg.evaluate("[curTab(), loads.beam.point.length, document.querySelectorAll('#tab-beam .k-chip[data-type=point]').length]")
            check(f'{tag} Schnittkräfte: zurück → springt zum Träger, Last wieder weg (auch in der Anzeige)', r[0]=='beam' and r[1]==n0 and r[2] in (n0, 0), r)
            await pg.click('#k5-redo'); await pg.wait_for_timeout(400)
            check(f'{tag} Schnittkräfte: „Wiederholen“ bringt die Last zurück', await pg.evaluate("loads.beam.point.length")==n0+1)
            # Hinweis „Last gelöscht · Rückgängig“ verschwindet beim Zurücknehmen über den Knopf
            await pg.evaluate("document.getElementById('k-undo') && document.getElementById('k-undo').classList.add('on')")
            await pg.click('#k5-undo'); await pg.wait_for_timeout(300)
            check(f'{tag} Schnittkräfte: alter Lösch-Hinweis geht weg', await pg.evaluate("!document.querySelector('#k-undo.on')"))
            # nicht in Wissen und Rechenblätter
            for pgn in ('ref.html','projekt.html','index.html'):
                await pg.goto(B+pgn); await pg.wait_for_timeout(400)
                check(f'{tag} {pgn}: kein Rückgängig-Knopf', await pg.evaluate("!document.getElementById('k5-undo')"))
            await pg.close()
        # Sprachen
        pg=await br.new_page(viewport={'width':1280,'height':900})
        for L,lab in (('en','Undo'),('fr','Annuler'),('es','Deshacer')):
            await pg.goto(B+'size.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(700)
            check(f'{L}: „{lab}“', await pg.evaluate("document.getElementById('k5-undo').getAttribute('aria-label')")==lab)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
    print('FAILS:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
