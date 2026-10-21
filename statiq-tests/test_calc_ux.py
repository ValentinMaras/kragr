# statiq·calc v0.8.12: Auswahlmenü, zwei Spalten, kompakte Lasten, Live-Berechnung, Beschriftungen ohne Überlappung. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','calc.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
OVERLAP="""(id)=>{ const T=[...document.querySelectorAll('#'+id+' text')].filter(t=>t.textContent.trim().length>1).map(t=>t.getBoundingClientRect()).filter(r=>r.width);
  let n=0; for(let i=0;i<T.length;i++) for(let j=0;j<i;j++){ const a=T[i], b=T[j]; if(a.left<b.right-1 && b.left<a.right-1 && a.top<b.bottom-1 && b.top<a.bottom-1) n++; } return n; }"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        # Live-Ergebnis direkt nach dem Laden
        check('Ergebnis sofort sichtbar (ohne Klick auf Berechnen)', await pg.is_visible('#beam-results') and await pg.inner_text('#b-res-Mmax')=='28.13', await pg.inner_text('#b-res-Mmax'))
        check('Berechnen-Knopf ausgeblendet, Hinweis „laufend berechnet“', not await pg.is_visible('#tab-beam .run-btn') and 'laufend' in await pg.inner_text('#tab-beam .live-note'))
        await pg.fill('#bL','6'); await pg.wait_for_timeout(450)
        m=float(await pg.inner_text('#b-res-Mmax'))
        # q = 5 auf 0…5 m, F = 10 bei 2,5 m, L = 6 m: max M unter F (Querkraft wechselt dort das Vorzeichen)
        RA=25*3.5/6+10*3.5/6; ref=RA*2.5-5*2.5**2/2
        check('Eingabe ändern → Ergebnis rechnet nach (L = 6 m)', abs(m-ref)<0.006, f'{m} / {ref}')
        # zwei Spalten
        g=await pg.evaluate("(()=>{const a=document.querySelector('#tab-beam .col-in').getBoundingClientRect(), b=document.querySelector('#tab-beam .col-out').getBoundingClientRect(); return [a.left,a.right,b.left,b.top, getComputedStyle(document.querySelector('#tab-beam .col-out')).position]})()")
        check('Rechner: Eingaben links, Ergebnis rechts (mitlaufend)', g[1]<=g[2] and g[4]=='sticky', g)
        check('Speichern-Knopf unter dem Ergebnis', await pg.evaluate("document.querySelector('#tab-beam .col-out').lastElementChild.classList.contains('save-btn')"))
        # Auswahlmenü
        check('Auswahlknopf zeigt Bereich und System', await pg.inner_text('#pick-g')=='Balken' and await pg.inner_text('#pick-t')=='Einfeldträger')
        await pg.click('#pick-btn')
        st=await pg.evaluate("[[...document.querySelectorAll('.pick-group')].map(g=>g.dataset.g), [...document.querySelectorAll('.pick-group.open')].map(g=>g.dataset.g), document.querySelectorAll('.pick-item').length]")
        check('Menü: Balken, Rahmen (Meine Projekte nur über den Knopf oben); nur der aktuelle Bereich offen', st==[['beams','frames'],['beams'],6], st)
        vis=await pg.evaluate("(()=>{const r=document.querySelector('.pick-group.open .pick-item').getBoundingClientRect(); const e=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2); return !!(e && e.closest('.pick-menu'))})()")
        check('Menü liegt über den Karten (nicht verdeckt)', vis)
        await pg.click('.pick-group[data-g="frames"] .pick-head'); await pg.click('.pick-item[data-k="frame:three"]'); await pg.wait_for_timeout(400)
        st=await pg.evaluate("[curTab(), framePresetNow(), document.getElementById('pick-t').textContent, document.getElementById('pick').classList.contains('open'), !document.getElementById('frame-results').classList.contains('hidden')]")
        check('Menü → Dreigelenkrahmen: Tab, Vorlage, Anzeige, Ergebnis', st==['frame','three','Dreigelenkrahmen',False,True], st)
        await pg.click('#pick-btn'); await pg.click('.pick-group[data-g="beams"] .pick-head'); await pg.click('.pick-item[data-k="cantilever"]'); await pg.wait_for_timeout(300)
        check('Menü → Kragarm', await pg.evaluate("curTab()==='cantilever' && document.getElementById('pick-t').textContent==='Kragarm' && !document.getElementById('cant-results').classList.contains('hidden')"))
        await pg.evaluate("saveCalc('cantilever')"); await pg.click('#proj-btn'); await pg.click('#proj-panel .pp-more'); await pg.wait_for_timeout(200)
        check('Meine Projekte → Alle Berechnungen: Ansicht „Gespeichert“, Auswahl zeigt sie an', await pg.evaluate("curTab()==='saved' && document.getElementById('pick-t').textContent==='Gespeichert'"))
        await pg.click('#pick-btn'); await pg.keyboard.press('Escape'); check('Escape schließt das Menü', not await pg.evaluate("document.getElementById('pick').classList.contains('open')"))
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(400)
        check('Durchlaufträger startet mit Gleichlast und Ergebnis', await pg.evaluate("parseFloat(document.getElementById('cont-Mmax').textContent)")>15)
        # kompakte Lasten
        await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(300)
        st=await pg.evaluate("[...document.querySelectorAll('#beam-point-list .load-item, #beam-dist-list .load-item')].map(i=>[i.classList.contains('cmp'), i.classList.contains('open'), i.querySelector('.load-sum').textContent])")
        check('Lasten zugeklappt mit Kurzfassung', st==[[True,False,'F = 10 kN · @ 2,5 m'],[True,False,'q = 5 kN/m · 0 – 6 m']] or st==[[True,False,'F = 10 kN · @ 2,5 m'],[True,False,'q = 5 kN/m · 0 – 5 m']], st)
        await pg.click('#beam-point-list .load-item-header .load-item-label')
        check('Klick auf die Kopfzeile klappt auf', await pg.is_visible('#beam-point-list .load-item-body input'))
        await pg.fill('#beam-point-list .load-item-body input >> nth=0','20'); await pg.wait_for_timeout(450)
        st=await pg.evaluate("[document.querySelector('#beam-point-list .load-sum').textContent, document.getElementById('b-res-A').textContent]")
        check('Eingabe in der Last: Kurzfassung und Ergebnis folgen', st[0].startswith('F = 20 kN') and abs(float(st[1])-(25*3.5/6+20*3.5/6))<0.006, st)
        await pg.evaluate("addLoad('beam','point')"); await pg.wait_for_timeout(100)
        st=await pg.evaluate("[...document.querySelectorAll('#beam-point-list .load-item')].map(i=>i.classList.contains('open'))")
        check('Neue Last ist aufgeklappt, offene bleibt offen', st==[True,True], st)
        await pg.click('#beam-point-list .load-item >> nth=0 >> .load-action-btn >> nth=0'); await pg.wait_for_timeout(100)
        check('Augen-Knopf klappt nicht um (nur Ein/Aus)', await pg.evaluate("document.querySelector('#beam-point-list .load-item').classList.contains('disabled') && document.querySelector('#beam-point-list .load-item').classList.contains('open')"))
        await pg.evaluate("toggleLoad('beam','point', loads.beam.point[0].id)")
        # Beschriftungen ohne Überlappung
        await pg.evaluate("loads.beam.point=[{id:901,enabled:true,values:{F:10,a:3,alpha:0}},{id:902,enabled:true,values:{F:15,a:3.3,alpha:0}}]; renderLoads('beam','point'); drawBeam()"); await pg.wait_for_timeout(100)
        check('Systemskizze: keine überlappenden Beschriftungen (zwei nahe Kräfte + q)', await pg.evaluate(f"({OVERLAP})('beam-svg')")==0)
        cross=await pg.evaluate("""(()=>{ const svg=document.getElementById('beam-svg'); const q=[...svg.querySelectorAll('text')].find(t=>t.textContent.startsWith('q1')).getBoundingClientRect();
          return [...svg.querySelectorAll('line')].filter(l=>(l.getAttribute('marker-end')||'').includes('red')).some(l=>{ const r=l.getBoundingClientRect(); return r.left>q.left && r.left<q.right && r.top<q.bottom && r.bottom>q.top; }); })()""")
        check('q-Beschriftung wird von keinem Lastpfeil durchgestrichen', not cross)
        for t,svg in [('cantilever','cant-svg'),('cont','cont-svg'),('frame','frame-svg')]:
            await pg.evaluate(f"showTab('{t}')"); await pg.wait_for_timeout(300)
            check(f'Skizze {t}: keine überlappenden Beschriftungen', await pg.evaluate(f"({OVERLAP})('{svg}')")==0)
        # Sprache
        await pg.evaluate("showTab('beam'); setCalcLang('en')"); await pg.wait_for_timeout(200)
        check('Sprache EN: Menü übersetzt', await pg.inner_text('#pick-g')=='Beams' and await pg.inner_text('#pick-t')=='Simply Supported' and 'automatically' in await pg.inner_text('#tab-beam .live-note'))
        await pg.evaluate("setCalcLang('de')")
        # keine Seitenleiste mehr: Module stehen oben, Sprache als Auswahl im Kopf
        check('Kein ☰-Menü und keine Seitenleiste', await pg.evaluate("!document.getElementById('nav-drawer') && !document.querySelector('.menu-btn')"))
        await pg.select_option('#lang-sel','fr'); await pg.wait_for_timeout(150)
        check('Sprachauswahl im Kopf: FR', await pg.evaluate("calcLang==='fr' && localStorage.getItem('statiq-lang')==='fr' && document.getElementById('lang-sel').value==='fr'"))
        await pg.evaluate("setCalcLang('de')")
        check('Auswahl folgt der Sprache', await pg.evaluate("document.getElementById('lang-sel').value")=='de')
        # Handy
        await pg.set_viewport_size({'width':390,'height':844}); await pg.wait_for_timeout(200)
        g=await pg.evaluate("[document.documentElement.scrollWidth, getComputedStyle(document.querySelector('#tab-beam .cols')).display, document.getElementById('lang-sel').getBoundingClientRect().right]")
        check('Handy: einspaltig, kein Querscrollen, Sprachauswahl sichtbar', g[0]<=390 and g[1]=='block' and g[2]<=390, g)
        await pg.click('#pick-btn'); r=await pg.evaluate("(()=>{const r=document.getElementById('pick-menu').getBoundingClientRect(); return [r.left, r.right]})()")
        check('Handy: Menü passt auf den Bildschirm', r[0]>=0 and r[1]<=390, r)
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
