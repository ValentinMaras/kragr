# calc v0.8.29: Bericht als Rechenblatt — Schriftfeld (Position, Datum, Version), Rechenweg aus der Speicherung mit doppelt
# unterstrichenen Ergebnissen, Kennwerte mit Dezimalkomma je Sprache, Schnittgrößen schwarz-weiß und schraffiert
# (Stiele quer zur Stabachse), alte Speicherungen ohne Rechenweg weiter lesbar. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','calc.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
OPEN="(()=>{ const ks=Object.keys(localStorage).filter(x=>x.startsWith('statiq_sdf_')).sort(); showTab('saved'); renderSavedTab(); openReport(ks[ks.length-1]); return ks.length; })()"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':900,'height':1200}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.evaluate("saveCalc('beam')"); await pg.evaluate(OPEN); await pg.wait_for_timeout(400)
        sf=await pg.evaluate("[...document.querySelectorAll('.rb-sf b')].map(b=>b.textContent)")
        v=await pg.evaluate("STATIQ_VERSION")
        check('Schriftfeld: Position, Datum, Version', len(sf)==3 and sf[0].startswith('Einfeldträger') and sf[2]==f'Schnittkräfte v{v}' and sf[1].count('.')==2, sf)
        rw=await pg.evaluate("(()=>{ const s=document.querySelector('.rb-grid .steps'); if(!s) return null; const b=[...s.querySelectorAll('b')].map(x=>x.textContent); return [s.querySelectorAll('.st').length, b, getComputedStyle(s.querySelector('b')).borderBottomStyle]; })()")
        check('Rechenweg im Bericht (6 Schritte), B_V = 17,50 kN, doppelt unterstrichen', rw and rw[0]==6 and '17,50 kN' in rw[1] and rw[2]=='double', rw)
        t=await pg.evaluate("document.querySelector('.rb').innerText")
        check('Kennwerte und Lasten mit Dezimalkomma (DE)', '28,13 kNm' in t and 'x = 2,5 m' in t and '17,50' in await pg.evaluate("document.querySelector('.rb-tab').innerText"), t[t.find('MAXIMALE'):][:80])
        d=await pg.evaluate("""(()=>{ const s=[...document.querySelectorAll('#report-diagrams svg')]; const col=new Set(['#0f6e56','#185fa5','#8b3a1e','#7c3aed']);
           return [s.length, s.filter(x=>x.querySelector('[fill^="url(#rbh"]')).length, s.reduce((n,x)=>n+[...x.querySelectorAll('[stroke],[fill]')].filter(e=>col.has((e.getAttribute('stroke')||'').toLowerCase())||col.has((e.getAttribute('fill')||'').toLowerCase())).length,0),
             s.reduce((n,x)=>n+x.querySelectorAll('[fill^="url(#grid"],[fill^="url(#wgrid"],[fill="#f8fdf8"]').length,0)]; })()""")
        check('Schnittgrößen: schraffiert, keine Farben, kein Raster', d[0]>=3 and d[1]==d[0] and d[2]==0 and d[3]==0, d)
        # Rahmen: Stiele quer schraffiert
        await pg.evaluate("showTab('frame'); calculateFrame(); saveFrameCalc()"); await pg.evaluate(OPEN); await pg.wait_for_timeout(400)
        h=await pg.evaluate("(()=>{ const s=document.getElementById('report-svg-N'); return [s.querySelectorAll('[fill$=\"h)\"]').length, s.querySelectorAll('[fill$=\"v)\"]').length]; })()")
        n=await pg.evaluate("document.querySelectorAll('.rb-grid .st').length")
        check('Rahmen: Stiele waagerecht, Riegel senkrecht schraffiert; Rechenweg mit Kraftgrößenverfahren (calc v0.11.13: mind. 10 Schritte)', h[0]>=1 and h[1]>=1 and n>=10, (h, n))
        # EN: Punkt als Dezimaltrenner, Überschriften englisch
        await pg.evaluate("setCalcLang('en')"); await pg.evaluate(OPEN); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('.rb').innerText")
        check('EN: Dezimalpunkt, englische Abschnitte', 'Item' in t and 'STEP BY STEP' in t.upper() and ',' not in t[t.upper().find('MAXIMUM'):][:60], t[t.upper().find('MAXIMUM'):][:60])
        await pg.evaluate("setCalcLang('de')")
        # alte Speicherung ohne Rechenweg
        await pg.evaluate("""(()=>{ localStorage.clear(); const sdf={statiq_version:'0.8.10', timestamp:new Date().toISOString(), module:'calc', system:{type:'beam', geometry:{L:5}, supports:{A:'pin',B:'roller'}, loads:{point:[],dist:[],horiz:[]}, svgSnapshot:''},
            results:{Mmax:31.25,Qmax:25,Nmax:0,reactions:[],members:{member_0:{M:[0,-20,-31.25,-20,0],Q:[-25,-12.5,0,12.5,25],N:[0,0,0,0,0]}}}};
            localStorage.setItem('statiq_sdf_1', JSON.stringify({name:'Alt', sdf})); })()""")
        await pg.evaluate(OPEN); await pg.wait_for_timeout(300)
        check('alte Speicherung: Bericht ohne Rechenweg, ohne Fehler', not await pg.evaluate("!!document.querySelector('.rb-grid')") and '31,25 kNm' in await pg.evaluate("document.querySelector('.rb').innerText") and not errs, errs[:1])
        # PDF
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(400)
        await pg.evaluate("saveCalc('beam')"); await pg.evaluate(OPEN); await pg.wait_for_timeout(400)
        await pg.emulate_media(media='print'); pdf=await pg.pdf(format='A4')
        check('Druck als PDF möglich (A4)', len(pdf)>20000, len(pdf))
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
