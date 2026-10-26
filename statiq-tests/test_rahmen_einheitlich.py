# Einheitlicher Rahmen (calc v0.9.4 · size v0.6.3 · ref v0.3.43 · projekt v0.1.13 · rechtliches v0.1.12): auf allen App-Seiten
# gleiche Kopfzeile (Höhe, Logo-Größe, Logo-Kante, Module, Projekte, Erscheinungsbild, Sprache) und gleiche Inhaltsbreite
# (Rahmen 1180 px, Rand 24 px bzw. 16 px am Handy). Logo und Inhalt beginnen an derselben Kante. Ohne Playwright: SKIP.
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
PAGES=['calc','size','ref','projekt','rechtliches']
FRAME={'calc':'#tab-beam','size':'main.main','ref':'.layout','projekt':'.wrap','rechtliches':'#content'}
src={p:open(os.path.join(BASE,p+'.html'),encoding='utf-8').read() for p in PAGES}
blk={p:re.search(r'<style data-frame>(.*?)</style>',src[p],re.S) for p in PAGES}
check('gleicher Rahmen-Baustein (data-frame) auf allen fünf Seiten', all(blk.values()) and len({b.group(1) for b in blk.values()})==1)
M="""(sel)=>{const h=document.querySelector('.app-header'), l=h.querySelector('.logo'), f=document.querySelector(sel), cs=getComputedStyle(f);
 const lb=l.getBoundingClientRect(), fb=f.getBoundingClientRect(); const mods=[...h.querySelectorAll('.header-links > a, .header-links > .module-name')].map(e=>e.textContent.trim()).join(' ');
 const tools=h.querySelector('.hdr-tools'), pj=tools&&tools.querySelector('.proj-btn'), th=document.getElementById('theme-btn'), lg=tools&&tools.querySelector('select');
 return {h:Math.round(h.getBoundingClientRect().height), lx:Math.round(lb.left), fs:getComputedStyle(l).fontSize, fx:Math.round(fb.left+parseFloat(cs.paddingLeft)), fr:Math.round(fb.right-parseFloat(cs.paddingRight)),
   tr:Math.round(document.getElementById('k5-burger').getBoundingClientRect().right), mods, pj:!!pj, th:!!th && tools.contains(th), lang:!!lg, sw:document.documentElement.scrollWidth}}"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for W,H,gut,hh in [(390,844,16,58),(1280,800,24,68),(1600,900,24,68)]:
            pg=await br.new_page(viewport={'width':W,'height':H}); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')")
            R={}
            for f in PAGES:
                await pg.goto(B+f+'.html'); await pg.wait_for_timeout(500); R[f]=await pg.evaluate(M, FRAME[f])
            edge=max(gut, (W-1180)//2+gut)
            check(f'{W} px: Kopfzeile überall {hh} px hoch, Logo 24 px', all(r['h']==hh and r['fs']=='24px' for r in R.values()), {k:(v['h'],v['fs']) for k,v in R.items()})
            check(f'{W} px: Logo überall an derselben Kante ({edge} px)', all(r['lx']==edge for r in R.values()), {k:v['lx'] for k,v in R.items()})
            check(f'{W} px: Inhalt beginnt an der Logo-Kante und endet an der ☰-Kante', all(r['fx']==edge and abs(r['fr']-r['tr'])<=1 for r in R.values()), {k:(v['fx'],v['fr'],v['tr']) for k,v in R.items()})
            check(f'{W} px: überall calc · size · ref, Projekte, Erscheinungsbild, Sprache (im DOM, vom Menü gesteuert)', all(r['mods']=='calc size ref' and r['pj'] and r['th'] and r['lang'] for r in R.values()), {k:(v['mods'],v['pj'],v['th'],v['lang']) for k,v in R.items()})
            check(f'{W} px: kein Querscrollen', all(r['sw']<=W for r in R.values()), {k:v['sw'] for k,v in R.items()})
            await pg.close()
        pg=await br.new_page(viewport={'width':1280,'height':800}); pg.on('pageerror', lambda e: errs.append(str(e)))
        for f in ['ref','rechtliches']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(400)
            r=await pg.evaluate("[document.querySelector('.proj-go').getAttribute('href'), document.querySelector('.proj-go .pb-tx').textContent]")
            check(f'{f}: „Meine Projekte“ führt zu projekt.html', r==['projekt.html','Meine Projekte'], r)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(400)
        check('EN: „My projects“', (await pg.text_content('.proj-go .pb-tx')).strip()=='My projects')
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(400)
        check('projekt: Projekte-Knopf als aktuelle Seite (dunkel)', await pg.evaluate("[document.querySelector('.app-header .proj-btn.cur').getAttribute('aria-current'), getComputedStyle(document.querySelector('.app-header .proj-btn.cur')).backgroundColor]")==['page','rgb(17, 17, 20)'])
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
