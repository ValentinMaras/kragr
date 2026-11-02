# Kopfzeile bleibt beim Scrollen vorne (calc v0.11.16): In Schnittkräfte lief am Handy die Systemauswahl (.nav.calc-top, z 30)
# über das Logo der mitlaufenden Kopfzeile (z 10). Geprüft auf allen App-Seiten: Logo und ☰ liegen nach dem Scrollen oben.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
TOP="""(()=>{ const h=document.querySelector('.app-header.k-hdr'); const hit=sel=>{ const e=document.querySelector(sel); if(!e) return null; const r=e.getBoundingClientRect();
  const t=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); return !!(t && h.contains(t)); };
  return { logo:hit('.k-hdr .logo'), burger:hit('#k5-burger') }; })()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for W in (390,1280):
            pg=await br.new_page(viewport={'width':W,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
            for f in ['calc','size','ref','projekt']:
                await pg.goto(B+f+'.html'); await pg.wait_for_timeout(700)
                res=[]
                for y in (20,40,80,160):
                    await pg.evaluate(f"scrollTo(0,{y})"); await pg.wait_for_timeout(120); res.append(await pg.evaluate(TOP))
                check(f'{f} {W} px: Logo und ☰ bleiben beim Scrollen vorne', all(r['logo'] and r['burger'] for r in res), res)
            await pg.goto(B+'calc.html'); await pg.wait_for_timeout(600)
            await pg.click('#pick'); await pg.wait_for_timeout(400)
            o=await pg.evaluate("(()=>{ const m=document.querySelector('.pick-menu'); if(!m) return null; const r=m.getBoundingClientRect(); const t=document.elementFromPoint(r.left+r.width/2, r.bottom-12); return !!(t && m.contains(t)); })()")
            check(f'calc {W} px: geöffnete Systemauswahl liegt über dem Inhalt', o, o)
            await pg.close()
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
