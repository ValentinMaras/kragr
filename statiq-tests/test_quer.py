# Handy quer (calc v0.11.18 · size v0.7.20): Ansicht wie am Rechner — Eingaben links, Ergebnisse rechts, jede Spalte scrollt für sich,
# Spalten beginnen direkt unter der (flacheren) Kopfzeile; die Ergebnisleiste unten entfällt. Hochkant bleibt alles wie bisher.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
COL="""(()=>{ const ci=[...document.querySelectorAll('.col-in')].find(e=>e.offsetParent), co=ci.parentElement.querySelector(':scope > .col-out'), h=document.querySelector('.app-header.k-hdr').getBoundingClientRect();
  const a=ci.getBoundingClientRect(), b=co.getBoundingClientRect();
  return {side:b.left>=a.right-1 && Math.abs(a.top-b.top)<2, top:Math.round(a.top), hb:Math.round(h.bottom), hh:Math.round(h.height), ah:Math.round(a.height), ih:innerHeight,
    sIn:ci.scrollHeight>ci.clientHeight+20, sOut:co.scrollHeight>co.clientHeight+20, ov:getComputedStyle(ci).overflowY, sw:document.documentElement.scrollWidth}; })()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for W,Hh in ((844,390),(932,430),(667,375)):
            ctx=await br.new_context(viewport={'width':W,'height':Hh}, has_touch=True, is_mobile=True)
            pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            for f in ('size','calc'):
                await pg.goto(B+f+'.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
                r=await pg.evaluate(COL)
                check(f'{f} quer {W}×{Hh}: zwei Spalten nebeneinander, direkt unter der Kopfzeile', r['side'] and abs(r['top']-r['hb'])<=6 and r['hh']<=56 and r['sw']<=W, r)
                check(f'{f} quer {W}×{Hh}: jede Spalte scrollt für sich (Höhe = Bildschirm − Kopfzeile)', r['ov']=='auto' and abs(r['ah']-(r['ih']-r['hb']-6))<=4 and r['sIn'] and r['sOut'], r)
                # unabhängig scrollen
                m=await pg.evaluate("""(()=>{ const ci=[...document.querySelectorAll('.col-in')].find(e=>e.offsetParent), co=ci.parentElement.querySelector(':scope > .col-out'); ci.scrollTop=200; return [ci.scrollTop, co.scrollTop, scrollY]; })()""")
                check(f'{f} quer {W}×{Hh}: links scrollen bewegt rechts nicht', m[0]>=150 and m[1]==0 and m[2]==0, m)
                bar=await pg.evaluate("(()=>{ const b=document.getElementById('mob-status')||document.getElementById('k-bar'); return b ? getComputedStyle(b).display : 'none'; })()")
                check(f'{f} quer {W}×{Hh}: keine Ergebnisleiste unten', bar=='none', bar)
            await ctx.close()
        # Hochkant: unverändert untereinander
        ctx=await br.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True); pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        for f in ('size','calc'):
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(900)
            r=await pg.evaluate(COL)
            check(f'{f} hochkant: untereinander, Seite scrollt normal', not r['side'] and r['ov']!='auto', r)
        # Querformat an der Bemessung: Querschnitt rechts (nicht nach oben verschoben), Lupe geht
        ctx2=await br.new_context(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True); q=await ctx2.new_page(); q.on('pageerror', lambda e: errs.append(str(e)))
        await q.goto(B+'size.html'); await q.wait_for_timeout(1000)
        check('size quer: Abbildung in der rechten Spalte', await q.evaluate("document.querySelector('.col-out').contains(document.getElementById('fig'))"))
        await q.tap('.zv-open'); await q.wait_for_timeout(300)
        check('size quer: Ansichtsfenster öffnet', await q.evaluate("document.getElementById('zv').classList.contains('open')"))
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
