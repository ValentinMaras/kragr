# size v0.5.50: Listen mit „+“ — Bauteilaufbau (U-Wert, Tauwasser, Schall), Setzung (Bodenschichten), Pfahl (Mantelreibung).
# Schichten kompakt als Zeilen mit Kurzfassung, eine aufgeklappt, „+“ fügt hinzu, „×“ entfernt und rückt nach; Ergebnisse
# unverändert gegenüber den Feldern (unabhängig nachgerechnet). Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
VIS="k=>[...document.querySelectorAll('.ml[data-ml=\"'+k+'\"] .ml-it')].filter(e=>e.style.display!=='none').map(e=>e.querySelector('.ml-s').textContent)"
OPEN="k=>[...document.querySelectorAll('.ml[data-ml=\"'+k+'\"] .ml-it.open')].map(e=>+e.dataset.i)"
RT=lambda L: 0.13+sum(d/l for d,l in L)+0.04
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.evaluate("setMat('bauph'); setBpMode('uwert')"); await pg.wait_for_timeout(300)
        v=await pg.evaluate(VIS,'bp'); o=await pg.evaluate(OPEN,'bp')
        check('Bauteilaufbau: 4 Schichten als Zeilen, alle zu, leere Plätze ausgeblendet', v==['Gipsputz · 1,5 cm','Kalksandstein · 17,5 cm','Mineralwolle WLS 035 · 16 cm','Kalkzementputz · 1 cm'], v)
        check('… keine Schicht aufgeklappt, Kopfzeile der Spalten ausgeblendet', o==[] and await pg.evaluate("getComputedStyle(document.querySelector('#bp-lay-card .bp-head')).display")=='none', o)
        await pg.click('.ml[data-ml="bp"] .ml-it[data-i="2"] .ml-h'); await pg.click('.ml[data-ml="bp"] .ml-it[data-i="3"] .ml-h')
        check('Antippen klappt auf, nur eine Schicht offen', await pg.evaluate(OPEN,'bp')==[3] and await pg.is_visible('#bl-d3') and not await pg.is_visible('#bl-d2'))
        await pg.click('.ml[data-ml="bp"] .ml-add'); await pg.wait_for_timeout(200)
        v=await pg.evaluate(VIS,'bp')
        check('„+“: neue Schicht 5 offen, Auswahl fokussiert, „Baustoff wählen“', len(v)==5 and 'Baustoff wählen' in v[4] and await pg.evaluate(OPEN,'bp')==[5] and await pg.evaluate("document.activeElement.id")=='bl-m5', v[-1])
        await pg.evaluate("$('bl-m5').value=String(BP_MAT.findIndex(m=>m[0]==='Holzfaserdämmung WLS 040')); bpPick(5)"); await pg.wait_for_timeout(200)
        mat=await pg.evaluate("[$('bl-d5').value, $('bl-l5').value]")
        U5=await pg.evaluate("LAST.res.W.U"); L5=[(0.015,0.51),(0.175,0.99),(0.16,0.035),(0.01,1.0),(float(mat[0])/100,float(mat[1]))]
        check('… gewählter Baustoff rechnet mit (U = 1/R_T)', abs(U5-1/RT(L5))<1e-9, (U5, 1/RT(L5)))
        await pg.click('.ml[data-ml="bp"] .ml-it[data-i="3"] .ml-x'); await pg.wait_for_timeout(200)
        r=await pg.evaluate("[[1,2,3,4,5].map(i=>$('bl-m'+i).value==='-'?'-':BP_MAT[+$('bl-m'+i).value][0]), LAST.res.W.U]")
        L4=[L5[0],L5[1],L5[3],L5[4]]
        check('„×“ entfernt Schicht 3, die folgenden rücken nach, U neu', r[0][:4]==['Gipsputz','Kalksandstein RDK 1,8','Kalkzementputz','Holzfaserdämmung WLS 040'] and r[0][4]=='-' and abs(r[1]-1/RT(L4))<1e-9, r)
        for _ in range(3): await pg.click('.ml[data-ml="bp"] .ml-it[data-i="1"] .ml-x')
        check('mindestens eine Schicht bleibt (× ausgeblendet)', len(await pg.evaluate(VIS,'bp'))==1 and await pg.evaluate("getComputedStyle(document.querySelector('.ml[data-ml=bp] .ml-it .ml-x')).visibility")=='hidden')
        for _ in range(5): await pg.evaluate("mlAdd('bp')")
        check('höchstens 6 Schichten, dann kein „+“ mehr', len(await pg.evaluate(VIS,'bp'))==6 and not await pg.is_visible('.ml[data-ml="bp"] .ml-add'))
        # Speichern und Laden: Liste folgt den Daten
        await pg.goto(U); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
        await pg.evaluate("setMat('bauph'); setBpMode('uwert'); $('bp-name').value='Wand 2 Schichten'; for(let i=3;i<=6;i++){ $('bl-m'+i).value='-'; $('bl-d'+i).value='0'; } run(); savePos(); for(let i=3;i<=5;i++) mlAdd('bp'); loadPos(posRead().findIndex(p=>p.name==='Wand 2 Schichten'))"); await pg.wait_for_timeout(300)
        check('Position laden: Liste zeigt genau die gespeicherten 2 Schichten', len(await pg.evaluate(VIS,'bp'))==2)
        # Setzung
        await pg.evaluate("setMat('grund'); setGrMode('setzung')"); await pg.wait_for_timeout(300)
        v=await pg.evaluate(VIS,'gs'); s0=await pg.evaluate("LAST.res.s")
        check('Setzung: 3 Bodenschichten als Zeilen, Anzahl-Feld ausgeblendet', len(v)==3 and 'Sand, mitteldicht' in v[0] and '2 m' in v[0] and not await pg.is_visible('#gs-n'), v)
        await pg.click('.ml[data-ml="gs"] .ml-add'); await pg.wait_for_timeout(200)
        check('„+“: 4. Schicht, gs-n = 4, letzte Schicht ohne Dickenfeld', await pg.evaluate("$('gs-n').value")=='4' and len(await pg.evaluate(VIS,'gs'))==4 and not await pg.is_visible('#gs-h4'))
        await pg.click('.ml[data-ml="gs"] .ml-it[data-i="4"] .ml-x'); await pg.wait_for_timeout(200)
        check('„×“ auf die neue Schicht: zurück auf 3, gleiche Setzung', await pg.evaluate("$('gs-n').value")=='3' and abs(await pg.evaluate("LAST.res.s")-s0)<1e-12)
        await pg.click('.ml[data-ml="gs"] .ml-it[data-i="1"] .ml-x'); await pg.wait_for_timeout(200)
        r=await pg.evaluate("[$('gs-n').value, $('gs-b1').value, $('gs-E1').value, $('gs-h1').value]")
        check('„×“ auf Schicht 1: Ton rückt nach oben (Werte mitgenommen)', r==['2','ts','12','4.0'] or (r[0]=='2' and r[2]=='12' and r[3] in ('4','4.0')), r)
        # Pfahl
        await pg.evaluate("setGrMode('pfahl')"); await pg.wait_for_timeout(300)
        v=await pg.evaluate(VIS,'pf'); R0=await pg.evaluate("JSON.stringify(LAST.res.C.map(c=>c.eta))")
        check('Pfahl: 2 Schichten (dritte mit Dicke 0 ausgeblendet)', len(v)==2 and v[0].startswith('4 m') and '60 kN/m²' in v[0], v)
        await pg.evaluate("mlAdd('pf'); $('pf-t3').value='3'; $('pf-q3').value='120'; run()"); await pg.wait_for_timeout(200)
        check('„+“: dritte Schicht rechnet mit (höhere Mantelreibung → kleinere Ausnutzung)', len(await pg.evaluate(VIS,'pf'))==3 and await pg.evaluate("JSON.stringify(LAST.res.C.map(c=>c.eta))")!=R0)
        # Sprachen
        res={}
        for lang,w in [('en','Add layer'),('fr','Ajouter une couche'),('es','Añadir capa')]:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(400)
            await pg.evaluate("setMat('bauph'); setBpMode('uwert')"); await pg.wait_for_timeout(200)
            res[lang]=w in await pg.inner_text('.ml[data-ml="bp"] .ml-add')
        check('EN/FR/ES: „+ Schicht hinzufügen“ übersetzt', all(res.values()), res)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
