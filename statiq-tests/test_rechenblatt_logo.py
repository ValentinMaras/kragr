# Rechenblatt (PDF) mit der Wortmarke kragr oben links (calc v0.11.15, size v0.7.11): „krag“ + das r als Kragarm mit Last,
# darunter bzw. daneben das Modul. Vorher in calc ein Symbol mit „kragr · Schnittkräfte“, in size gar keine Marke.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
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
        pg=await br.new_page(viewport={'width':1100,'height':1400}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("localStorage.setItem('statiq_sdf_1', JSON.stringify({name:'Pos. 1', sdf:buildSDF()})); showTab('saved'); openReport('statiq_sdf_1')"); await pg.wait_for_timeout(700)
        await pg.emulate_media(media='print')
        r=await pg.evaluate("""(()=>{ const l=document.querySelector('#report-content .rb-logo'), sf=document.querySelector('#report-content .rb-sf'); if(!l) return null; const m=l.querySelector('.rb-mark'), b=m.getBoundingClientRect(), s=sf.getBoundingClientRect();
          return {txt:m.textContent, r:!!m.querySelector('svg.logo-r'), mod:l.querySelector('.rb-mod').textContent, left:b.left-s.left, top:b.top-s.top, first:sf.firstElementChild===l, vis:b.width>30 && b.height>12} })()""")
        check('calc: Wortmarke „krag“ + r als Kragarm im Schriftfeld', r and r['txt']=='krag' and r['r'] and r['vis'], r)
        check('calc: oben links (erste Zelle des Schriftfelds)', r and r['first'] and r['left']<20 and r['top']<20, r)
        check('calc: Modul „Schnittkräfte“ unter der Marke', r and r['mod']=='Schnittkräfte', r and r['mod'])
        check('calc: altes Symbol entfernt', await pg.evaluate("!document.querySelector('#report-content .rb-logo svg:not(.logo-r)')"))
        s=await br.new_page(viewport={'width':1100,'height':1400}); s.on('pageerror', lambda e: errs.append(str(e)))
        await s.goto(B+'size.html'); await s.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await s.reload(); await s.wait_for_timeout(900)
        await s.evaluate("showReport()"); await s.wait_for_timeout(400); await s.emulate_media(media='print')
        r=await s.evaluate("""(()=>{ const rep=document.getElementById('report'), m=rep.firstElementChild; const b=m.getBoundingClientRect(), R=rep.getBoundingClientRect();
          return {cls:m.className, txt:m.querySelector('.rep-mark-w').textContent, r:!!m.querySelector('svg.logo-r'), mod:m.querySelector('.rep-mark-m').textContent, left:b.left-R.left, vis:getComputedStyle(m).display!=='none' && b.height>15} })()""")
        check('size: Wortmarke als erstes Element des Rechenblatts, links', r['cls']=='rep-mark' and r['txt']=='krag' and r['r'] and r['left']<5 and r['vis'], r)
        check('size: Modul „Bemessung“ neben der Marke', r['mod']=='Bemessung', r['mod'])
        await s.emulate_media(media='screen'); await s.evaluate("localStorage.setItem('statiq-lang','en')"); await s.reload(); await s.wait_for_timeout(800); await s.evaluate("showReport()"); await s.wait_for_timeout(300)
        m=await s.evaluate("document.querySelector('#report .rep-mark-m').textContent")
        check('size EN: Modulname übersetzt', m!='Bemessung' and m, m)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
