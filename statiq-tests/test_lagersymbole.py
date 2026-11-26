# kragr·calc v0.11.56 (26.11.2026): kleine Lagerzeichen in den Eingaben wie in den Skizzen (Festlager mit Gelenk und Schraffur,
# Loslager mit Gleitlinie, Einspannung als Wand bzw. Schraffur) statt der Schriftzeichen ⊞ △ ○.
# Text der Kurzfassungen bleibt gleich (⊞ △ ○ unsichtbar im Text, für Vergleiche und Kopieren); Bild mit Namen für Vorleseprogramme.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:160])

# je Zeichen: Anzahl Dreiecke (polygon), Kreise (Gelenk), Linien (Gleitlinie, Schraffur, Wand)
INFO = """(sel) => [...document.querySelectorAll(sel)].map(si => { const g=si.querySelector('svg'); const lines=[...g.querySelectorAll('line')];
  return { label: si.getAttribute('aria-label') || '', glyph: (si.querySelector('.k-vh')||{}).textContent || '',
    tri: g.querySelectorAll('polygon').length, circ: g.querySelectorAll('circle').length, lines: lines.length,
    vert: lines.filter(l=>Math.abs(+l.getAttribute('x1')-+l.getAttribute('x2'))<0.01 && Math.abs(+l.getAttribute('y1')-+l.getAttribute('y2'))>5).length,
    horiz: lines.filter(l=>Math.abs(+l.getAttribute('y1')-+l.getAttribute('y2'))<0.01).length,
    h: Math.round(g.getBoundingClientRect().height), color: getComputedStyle(si).color, stroke: (g.innerHTML.match(/stroke="([^"]+)"/)||[])[1] }; })"""

OPEN = "(t)=>{ const c=document.querySelector('#tab-'+t+' [data-st=sup]'); if(c.classList.contains('k-closed')||c.classList.contains('closed')) c.querySelector('.k-head').click(); }"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        # Einfeldträger: Kurzfassung und Übersicht
        await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(400); await pg.evaluate(OPEN, 'beam'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#tab-beam [data-st=sup] .k-sum').textContent")
        check('Einfeldträger: Text der Kurzfassung unverändert „A △ · B ○“', t=='A △ · B ○', t)
        s=await pg.evaluate(INFO, '#tab-beam [data-st=sup] .k-sum .k-si')
        check('Kurzfassung: zwei Bilder, Festlager und Loslager mit Namen', [x['label'] for x in s]==['Festlager','Loslager'] and [x['glyph'] for x in s]==['△','○'], s)
        check('Festlager: Dreieck, Gelenk, Schraffur ohne Gleitlinie', s[0]['tri']==1 and s[0]['circ']==1 and s[0]['horiz']==1, s[0])
        check('Loslager: Dreieck, Gelenk, Gleitlinie und Schraffurlinie (zwei waagerechte Striche)', s[1]['tri']==1 and s[1]['circ']==1 and s[1]['horiz']==2, s[1])
        check('Zeichen in Textfarbe (currentColor), etwa so hoch wie die Schrift', all(x['stroke']=='currentColor' and 12<=x['h']<=18 for x in s), [(x['stroke'],x['h']) for x in s])
        r=await pg.evaluate(INFO, '#tab-beam .k-supinfo .k-supi-s')
        check('Übersicht „Lager A/B“: dieselben Zeichen, blau, 24 px', [x['label'] for x in r]==['Festlager','Loslager'] and r[0]['tri']==1 and r[1]['horiz']==2 and all(x['h']==24 and x['color']=='rgb(84, 104, 173)' for x in r), r)
        check('Übersicht ohne Schriftzeichen ⊞ △ ○', await pg.evaluate("!/[⊞△○]/.test(document.querySelector('#tab-beam .k-supinfo').textContent)"))
        # Kragträger: Einspannung als Wand links mit Stab
        await pg.evaluate("showTab('cantilever')"); await pg.wait_for_timeout(400); await pg.evaluate(OPEN, 'cantilever'); await pg.wait_for_timeout(300)
        r=await pg.evaluate(INFO, '#tab-cantilever .k-supinfo .k-supi-s[role=img]')
        check('Kragträger: Einspannung als senkrechte Wand mit Schraffur und Stab', r[0]['label']=='Einspannung' and r[0]['tri']==0 and r[0]['vert']==1 and r[0]['lines']>=6, r[0])
        t=await pg.evaluate("document.querySelector('#tab-cantilever [data-st=sup] .k-sum').textContent")
        check('Kragträger: Text „A ⊞ · frei“', t=='A ⊞ · frei', t)
        # Rahmen: Kurzfassung und Lagerknöpfe
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400); await pg.evaluate(OPEN, 'frame'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#tab-frame [data-st=sup] .k-sum').textContent")
        check('Rahmen: Text „A ⊞ · B △ · n = 2“', t=='A ⊞ · B △ · n = 2', t)
        s=await pg.evaluate(INFO, '#tab-frame [data-st=sup] .k-sum .k-si')
        check('Rahmen: Einspannung am Fuß als Stab auf Schraffur (kein Dreieck), B Festlager', s[0]['label']=='Einspannung' and s[0]['tri']==0 and s[0]['vert']==1 and s[1]['tri']==1, s)
        b=await pg.evaluate("['btn-sA-fixed','btn-sA-pin','btn-sA-roller'].map(id=>{ const e=document.getElementById(id); return [e.textContent.trim(), !!e.querySelector('.k-si svg')]; })")
        check('Lagerknöpfe: Zeichen als Bild, Text gleich („Festlager △“)', b==[['Einspannung ⊞',True],['Festlager △',True],['Loslager ○',True]], b)
        await pg.click('#btn-sA-roller'); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#tab-frame [data-st=sup] .k-sum').textContent")
        check('Rahmen: Wechsel auf Loslager → Kurzfassung „A ○ · B △ …“ mit Loslager-Zeichen', t.startswith('A ○ · B △') and (await pg.evaluate(INFO, '#tab-frame [data-st=sup] .k-sum .k-si'))[0]['horiz']==2, t)
        # Durchlaufträger: Endlager links/rechts, Zwischenlager
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(400); await pg.evaluate(OPEN, 'cont'); await pg.wait_for_timeout(300)
        s=await pg.evaluate(INFO, '#tab-cont [data-st=sup] .k-sum .k-si')
        check('Durchlaufträger: ein Zeichen je Lager (△ ○ ○)', [x['glyph'] for x in s]==['△','○','○'] and s[0]['tri']==1 and s[1]['horiz']==2, [x['glyph'] for x in s])
        # Englisch: Namen übersetzt, Knöpfe nach dem Sprachwechsel wieder mit Bild
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(1000)
        await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(400); await pg.evaluate(OPEN, 'beam'); await pg.wait_for_timeout(300)
        s=await pg.evaluate(INFO, '#tab-beam [data-st=sup] .k-sum .k-si')
        check('Englisch: Namen „Pin“ und „Roller“', [x['label'] for x in s]==['Pin','Roller'], [x['label'] for x in s])
        await pg.evaluate("setCalcLang('de')"); await pg.wait_for_timeout(400); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400); await pg.evaluate(OPEN, 'frame'); await pg.wait_for_timeout(300)
        b=await pg.evaluate("[document.getElementById('btn-sB-pin').textContent.trim(), !!document.querySelector('#btn-sB-pin .k-si svg')]")
        check('Sprachwechsel ohne Neuladen: Knopf wieder mit Bild', b==['Festlager △', True], b)
        # dunkel: Zeichen folgen der Textfarbe
        await pg.emulate_media(color_scheme='dark'); await pg.evaluate("document.documentElement.setAttribute('data-theme','dark')"); await pg.wait_for_timeout(300)
        s=await pg.evaluate(INFO, '#tab-frame [data-st=sup] .k-sum .k-si')
        check('Dunkel: Zeichen in Textfarbe (keine feste Schwarzfarbe)', all(x['stroke']=='currentColor' for x in s), s)
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
