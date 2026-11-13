# Zwei Spalten scrollen für sich (calc v0.11.45 · size v0.7.47, 13.11.2026): am Rechner, Tablet quer und Handy quer sind Eingaben
# (links) und Ergebnisse (rechts) so hoch wie das Fenster unter der Kopfzeile; das Mausrad bzw. Wischen bewegt nur die Spalte darunter.
# Am Ende einer Spalte läuft (am Rechner) die Seite weiter bis zur Speichern- und Fußleiste.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
S="[Math.round(scrollY), document.querySelector('.col-in').scrollTop, document.querySelector('.col-out').scrollTop]"
GEO="""(()=>{ const a=document.querySelector('.col-in'), b=document.querySelector('.col-out'), h=document.querySelector('.app-header.k-hdr').getBoundingClientRect().bottom;
  const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect(); return {side: ra.right<=rb.left+1, top: Math.abs(ra.top-rb.top)<2 && ra.top>=h-2, fit: ra.bottom<=innerHeight+1 && rb.bottom<=innerHeight+1,
  own:[getComputedStyle(a).overflowY, getComputedStyle(b).overflowY], more: a.scrollHeight>a.clientHeight}; })()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for name,kw,page_too in (('Rechner',dict(viewport={'width':1280,'height':800}),True),('Tablet quer',dict(viewport={'width':1180,'height':820},is_mobile=True,has_touch=True),True),
                                 ('Handy quer',dict(viewport={'width':844,'height':390},is_mobile=True,has_touch=True),False)):
            pg=await br.new_page(**kw); pg.on('pageerror', lambda e: errs.append(str(e)))
            for f in ('size','calc'):
                await pg.goto(B+f+'.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
                g=await pg.evaluate(GEO)
                check(f'{name} {f}: zwei Spalten nebeneinander unter der Kopfzeile, beide passen in die Höhe und scrollen selbst', g['side'] and g['top'] and g['fit'] and g['own']==['auto','auto'] and g['more'], g)
                if name!='Handy quer':
                    sw=await pg.evaluate("[getComputedStyle(document.documentElement).scrollbarWidth, getComputedStyle(document.querySelector('.col-in')).scrollbarWidth, getComputedStyle(document.querySelector('.col-out')).scrollbarWidth]")
                    check(f'{name} {f}: Scrollleiste der Seite so schmal wie die der Spalten', sw==['thin','thin','thin'], sw)
                if name=='Handy quer': continue   # Mausrad gibt es dort nicht; Aufbau oben genügt (Wischen = gleiches Verhalten im Browser)
                W=kw['viewport']['width']
                await pg.mouse.move(W*0.25, 500); await pg.mouse.wheel(0, 400); await pg.wait_for_timeout(350); a=await pg.evaluate(S)
                check(f'{name} {f}: Mausrad links bewegt nur die Eingaben', a[0]==0 and a[1]>=100 and a[2]==0, a)
                await pg.mouse.move(W*0.75, 500); await pg.mouse.wheel(0, 200); await pg.wait_for_timeout(350); b=await pg.evaluate(S)
                check(f'{name} {f}: Mausrad rechts bewegt nur die Ergebnisse', b[0]==0 and b[1]==a[1] and b[2]>0, b)
                if page_too:
                    await pg.mouse.move(W*0.25, 500)
                    for _ in range(8): await pg.mouse.wheel(0, 800); await pg.wait_for_timeout(120)
                    c=await pg.evaluate(S); foot=await pg.evaluate("(()=>{ const l=document.querySelector('.legal-bar'); return !!l && l.getBoundingClientRect().top<innerHeight; })()")
                    check(f'{name} {f}: am Spaltenende läuft die Seite weiter bis zur Fußleiste', c[0]>0 and foot, (c, foot))
            await pg.close()
        # Menü am Handy quer (13.11.2026): Zeilen nicht zusammengeschoben, das Menü scrollt
        pg=await br.new_page(viewport={'width':844,'height':390}, is_mobile=True, has_touch=True)
        for f in ('calc','size','ref','projekt','index','rechtliches'):
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(700); await pg.click('#k5-burger'); await pg.wait_for_timeout(700)
            r=await pg.evaluate("""(()=>{ const m=document.getElementById('k5-menu'), k=[...m.children].filter(e=>e.offsetHeight>0); let bad=[];
              for(let i=1;i<k.length;i++){ const a=k[i-1].getBoundingClientRect(), b=k[i].getBoundingClientRect(); if(b.top<a.bottom-1) bad.push(k[i].className); }
              const sq=k.filter(e=>e.scrollHeight>e.clientHeight+2).map(e=>e.className); return {bad, sq, scroll:m.scrollHeight>m.clientHeight}; })()""")
            check(f'Handy quer {f}: Menüzeilen ohne Überlappung, Menü scrollt', not r['bad'] and not r['sq'] and r['scroll'], r)
        await pg.close()
        # Handy hochkant: unverändert eine Spalte, die Seite scrollt
        pg=await br.new_page(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True)
        for f in ('size','calc'):
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(800)
            r=await pg.evaluate("[getComputedStyle(document.querySelector('.col-in')).overflowY, getComputedStyle(document.querySelector('.col-in')).position]")
            check(f'Handy hochkant {f}: eine Spalte ohne eigenes Scrollen', r==['visible','static'], r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
    print('FAILS:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
