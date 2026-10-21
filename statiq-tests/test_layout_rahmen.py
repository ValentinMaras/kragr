# calc v0.8.20 / size v0.5.34: gleicher Darstellungsrahmen (Breite, Spalten, Lage oben); ref v0.3.26 ohne Pfadleiste.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
JS="""(()=>{ const r=s=>{const e=document.querySelector(s); const b=e.getBoundingClientRect(); return [Math.round(b.left),Math.round(b.top),Math.round(b.width)]};
  return {head:Math.round(document.querySelector('.app-header').getBoundingClientRect().height), pick:r('#pick'), cin:r('.col-in'), cout:r('.col-out'), ctop:Math.round([...document.querySelectorAll('.col-out')].find(e=>e.offsetParent).getBoundingClientRect().top)} })()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for w in [1440,1920,1100]:
            pg=await br.new_page(viewport={'width':w,'height':900}); m={}
            for f in ['calc.html','size.html']:
                await pg.goto(U+f); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
                m[f]=await pg.evaluate(JS)
            c,s=m['calc.html'],m['size.html']
            check(f'{w} px: Kopfzeile gleich hoch ({c["head"]} / {s["head"]})', c['head']==s['head'])
            check(f'{w} px: Auswahl gleich gesetzt und gleich breit (wie size in der Eingabespalte)', c['pick']==s['pick'] and c['pick'][2]==c['cin'][2], (c['pick'], s['pick'], c['cin']))
            check(f'{w} px: Ergebnisspalte beginnt auf gleicher Höhe', abs(c['ctop']-s['ctop'])<=1, (c['ctop'], s['ctop']))
            check(f'{w} px: Eingabe- und Ergebnisspalte gleich breit und gleich gesetzt', c['cin'][0]==s['cin'][0] and c['cin'][2]==s['cin'][2] and c['cout'][0]==s['cout'][0] and c['cout'][2]==s['cout'][2], (c['cin'],s['cin'],c['cout'],s['cout']))
            await pg.close()
        pg=await br.new_page(viewport={'width':1440,'height':900})
        for r in ['','#/holzbau/baustoffe/vollholz']:
            await pg.goto(U+'ref.html'+r); await pg.wait_for_timeout(300)
            check(f'ref {r or "Startseite"}: keine Pfadleiste', await pg.evaluate("getComputedStyle(document.getElementById('breadcrumb')).display")=='none')
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
