# Knoten und Stabendkräfte (calc v0.11.0 · size v0.7.2 · projekt v0.1.18): Knoten von links nach rechts nummeriert (Rahmen: A = 1,
# Ecke links = 2 …), Gelenke als eigene Knoten, Doppelindex M_ik (Moment im Stab i–k am Knoten i), Vorzeichen wie die Verläufe
# (M > 0 Zug unten/innen). Sollwerte unabhängig von Hand: Einfeldträger, Kragarm, Zweifeldträger; Rahmen über die Knotenproben (stetige
# Eckmomente, Q-Sprung = q·b, N = Auflagerkraft). Dazu Knotennummern in der Skizze, Übergabe Stabende → size (Schweißnaht, Stützenfuß). Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
near=lambda a,b,t=0.01: abs(a-b)<=t
def end(K, i, k):
    for b in K['bars']:
        if b['i']==i and b['k']==k: return b['ik']
        if b['k']==i and b['i']==k: return b['ki']
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de');localStorage.setItem('statiq-rw-closed','');localStorage.setItem('kragr-k5-acc',JSON.stringify({'calc:knoten':false,'size:scope':false}))"); await pg.reload(); await pg.wait_for_timeout(900)
        # Einfeldträger L = 5 m, q = 5 kN/m, F = 10 kN in der Mitte: A = qL/2 + F/2 = 17,5 kN
        K=await pg.evaluate("lastCalc.beam.knoten")
        check('Einfeldträger: Knoten 1 = A, 2 = B; Q12 = 17,5 kN, Q21 = −17,5 kN, M12 = M21 = 0', [n['lab'] for n in K['nodes']]==['A','B'] and near(end(K,1,2)['Q'],17.5) and near(end(K,2,1)['Q'],-17.5) and end(K,1,2)['M']==0 and end(K,2,1)['M']==0, K['bars'])
        r=await pg.evaluate("document.querySelectorAll('#beam-svg .k-knr').length")
        check('Einfeldträger: zwei Knotennummern in der Skizze', r==2, r)
        # Kragarm L = 3 m, q = 5, F = 10 bei 1,5 m: M12 = −(5·3²/2 + 10·1,5) = −37,5 kNm (Zug oben)
        await pg.evaluate("showTab('cantilever')"); await pg.wait_for_timeout(500)
        K=await pg.evaluate("lastCalc.cant.knoten"); t=await pg.inner_text('#cant-results .k-knoten')
        check('Kragarm: M12 = −37,5 kNm (Einspannmoment), Q12 = 25 kN, freies Ende M21 = Q21 = 0', near(end(K,1,2)['M'],-37.5) and near(end(K,1,2)['Q'],25) and end(K,2,1)['M']==0 and end(K,2,1)['Q']==0 and 'Einspannmoment' in t and 'freies Ende' in t, K['bars'])
        # Zweifeldträger 2 × 5 m, q = 5: M_B = −qL²/8 = −15,625; Q12 = 3qL/8 = 9,375; Q21 = −5qL/8
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(500)
        K=await pg.evaluate("lastCalc.cont.knoten"); t=await pg.inner_text('#cont-results .k-knoten')
        check('Zweifeldträger: M21 = M23 = −15,63 kNm, Q12 = 9,38, Q21 = −15,63, Q23 = 15,63 kN', near(end(K,2,1)['M'],-15.625) and near(end(K,2,3)['M'],-15.625) and near(end(K,1,2)['Q'],9.375) and near(end(K,2,1)['Q'],-15.625) and near(end(K,2,3)['Q'],15.625), K['bars'])
        check('Zweifeldträger: Probe „M21 = M23 = -15,63 kNm ✓“, Stäbe heißen „Feld 1“, „Feld 2“', 'M21 = M23 = -15,63 kNm' in t.replace('\n','') and 'Stab 1–2 · Feld 1' in t and 'Stab 2–3 · Feld 2' in t, t[:300])
        await pg.evaluate("addContHinge(); liveCalc(true)"); await pg.wait_for_timeout(500)
        K=await pg.evaluate("lastCalc.cont.knoten")
        check('Zweifeldträger mit Gelenk: Gelenk wird Knoten 3, M32 = M34 = 0', [n['kind'] for n in K['nodes']]==['sup','sup','gelenk','sup'] and end(K,3,2)['M']==0 and end(K,3,4)['M']==0, [n['kind'] for n in K['nodes']])
        # Rahmen (Voreinstellung: A eingespannt, B gelenkig, q = 10 auf dem Riegel, F = 5 kN an der linken Stütze)
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(600)
        K=await pg.evaluate("lastCalc.frame.knoten"); t=await pg.inner_text('#frame-results .k-knoten')
        check('Rahmen: Knoten 1 A · 2 Ecke links · 3 Ecke rechts · 4 B', [(n['nr'],n['kind'],n['lab']) for n in K['nodes']]==[(1,'sup','A'),(2,'ecke','L'),(3,'ecke','R'),(4,'sup','B')], K['nodes'])
        check('Rahmen: Momente an den Ecken stetig (M21 = M23, M32 = M34)', near(end(K,2,1)['M'],end(K,2,3)['M'],0.002) and near(end(K,3,2)['M'],end(K,3,4)['M'],0.002), (end(K,2,1),end(K,2,3)))
        check('Rahmen: Riegel Q23 − Q32 = q·b = 50 kN, Stütze rechts N34 = −B_V = −25 kN', near(end(K,2,3)['Q']-end(K,3,2)['Q'],50,0.01) and near(end(K,3,4)['N'],-25.002,0.01), (end(K,2,3), end(K,3,2), end(K,3,4)))
        check('Rahmen: wie bisher M = 13,81 kNm an der rechten Ecke (Schweißnaht-Test), Ecke „schließend (Zug außen)“', near(end(K,3,2)['M'],-13.81,0.01) and t.count('schließend (Zug außen)')==2, end(K,3,2))
        check('Rahmen: M12 = Einspannmoment 10,01 kNm, M43 = 0', near(end(K,1,2)['M'],10.01,0.01) and end(K,4,3)['M']==0 and 'M12 = 10,01 kNm' in t.replace('\n',''), end(K,1,2))
        r=await pg.evaluate("[document.querySelectorAll('#frame-svg .k-knr').length, document.querySelectorAll('#frame-svg .k-faser line').length]")
        check('Rahmen-Skizze: vier Knotennummern und die gestrichelte Faser innen', r==[4,3], r)
        # Dreigelenkrahmen: Mittelgelenk wird Knoten 3
        await pg.evaluate("applyFramePreset('three'); liveCalc(true)"); await pg.wait_for_timeout(600)
        K=await pg.evaluate("lastCalc.frame.knoten"); g=await pg.evaluate("[parseFloat(fB.value), parseFloat(fHA.value)]")
        check('Dreigelenkrahmen: fünf Knoten, Gelenk = Knoten 3 mit M32 = M34 = 0', len(K['nodes'])==5 and K['nodes'][2]['kind']=='gelenk' and end(K,3,2)['M']==0 and end(K,3,4)['M']==0, [n['kind'] for n in K['nodes']])
        check('Dreigelenkrahmen: Ecke links stetig, Fußpunkte gelenkig (M12 = M54 = 0)', near(end(K,2,1)['M'],end(K,2,3)['M'],0.002) and end(K,1,2)['M']==0 and end(K,5,4)['M']==0, (end(K,2,1), end(K,2,3)))
        # Übungsmodus versteckt die Karte
        await pg.evaluate("localStorage.setItem('muly-uebung','1')"); await pg.reload(); await pg.wait_for_timeout(900); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(500)
        check('Übungsmodus: Knotenkräfte verborgen (verraten die Lösung)', await pg.evaluate("!document.querySelector('#frame-results .k-knoten') || getComputedStyle(document.querySelector('#frame-results .k-knoten')).display==='none'"))
        await pg.evaluate("localStorage.setItem('muly-uebung','0')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("setCalcLang('en'); showTab('frame')"); await pg.wait_for_timeout(500)
        t=await pg.inner_text('#frame-results .k-knoten')
        check('EN: „Nodes and member end forces“, „Left corner“, „closing (tension outside)“', 'Nodes and member end forces' in t and 'Left corner' in t and 'closing (tension outside)' in t, t[:200])
        await pg.evaluate("setCalcLang('de')")
        # Projekt: Knoten im Menü, Übergabe an size
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(300); pid=await pg.evaluate("addPos()")
        await pg.goto(B+f'calc.html?pos={pid}'); await pg.wait_for_timeout(900); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(600)
        await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(400)
        r=await pg.evaluate(f"JSON.parse(localStorage.getItem('statiq_sdf_pos_{pid}')).sdf.results.knoten.nodes.length")
        check('System der Position enthält die Knoten (SDF results.knoten)', r==4, r)
        m=await pg.evaluate("[...document.querySelectorAll('.pos .addm a')].map(a=>new URLSearchParams(a.getAttribute('href').split('?')[1])).map(q=>(q.get('ziel')||'')+'|'+(q.get('ende')||''))")
        check('„＋ Nachweis“: Knoten-Gruppe mit Schweißnähten an 2–1, 2–3, 3–2, 3–4 und Stützenfuß 4–3 (nicht am eingespannten A)', [x for x in m if x.split('|')[1]]==['stahl.schweiss|2-1','stahl.schweiss|2-3','stahl.schweiss|3-2','stahl.schweiss|3-4','stahl.fuss|4-3'] and not any(x.startswith('stahl.schweiss|') and not x.split('|')[1] for x in m), m)
        await pg.goto(B+f'size.html?pos={pid}&ziel=stahl.schweiss&part=stiel&ende=2-1'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[STMODE, $('sw-fall').value, +$('sw-M').value, +$('sw-V').value, +$('sw-N').value, $('sw-name').value, $('ci-banner').innerText]")
        check('size: Schweißnaht am Stabende 2–1: M = 13,80, V = 3,45, N = −25,0 kN, Name „… · Stab 2–1“', r[:2]==['schweiss','stirn'] and near(r[2],13.799,0.002) and near(r[3],3.453,0.002) and near(r[4],-24.998,0.002) and r[5].endswith('Stab 2–1') and 'Stabende 2–1' in r[6] and 'M21' in r[6], r)
        await pg.click('#k-pmbar [data-pm=ok]'); await pg.wait_for_url('**/projekt.html*'); await pg.wait_for_timeout(300)
        check('Quelle merkt sich das Stabende (für „neu rechnen“)', await pg.evaluate("JSON.parse(localStorage.getItem('statiq-size-positionen'))[0].src.ende")=='2-1')
        await pg.goto(B+f'size.html?pos={pid}&ziel=stahl.fuss&part=stiel&ende=4-3'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[STMODE, +$('fp-N').value, +$('fp-V').value]")
        check('size: Stützenfuß am Stabende 4–3: N = 25,0 kN (Druck), V = 3,45 kN', r[0]=='fuss' and near(r[1],25.002,0.002) and near(r[2],3.453,0.002), r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
