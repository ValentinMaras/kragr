# Querschnitt mitlaufend (size v0.7.17): am Handy steht die Abbildung unter der Auswahl groß, bleibt beim Scrollen unter der
# Kopfzeile stehen und schrumpft gleichmäßig zur Leiste (Abbildung links, Angaben rechts). Am Rechner (zwei Spalten) nicht aktiv.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
ST="""(()=>{ const d=document.getElementById('fd'), r=d.getBoundingClientRect(), h=document.querySelector('.app-header.k-hdr').getBoundingClientRect(), f=d.querySelector('.fd-fig').getBoundingClientRect(), t=d.querySelector('.fd-tx').getBoundingClientRect();
  return {on:d.classList.contains('on') && getComputedStyle(d).display!=='none', top:Math.round(r.top), h:Math.round(r.height), hb:Math.round(h.bottom), p:+getComputedStyle(d).getPropertyValue('--p'),
    fw:Math.round(f.width), fx:Math.round(f.left-r.left), tx:Math.round(t.left-r.left), ty:Math.round(t.top-r.top), op:+getComputedStyle(d).opacity, svg:!!d.querySelector('.fd-fig svg'),
    t2:d.querySelector('.fd-t2').textContent, t3:d.querySelector('.fd-t3').textContent}; })()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        r0=await pg.evaluate(ST)
        check('Handy oben: Abbildung groß unter der Auswahl, Angaben darunter', r0['on'] and r0['svg'] and r0['h']>=220 and r0['p']==0 and r0['ty']>r0['h']*0.6 and r0['op']==1, r0)
        check('Angaben: Bewehrung und Gesamturteil wie im Ergebnis', 'Ø' in r0['t2'] and 'erfüllt' in r0['t3'], (r0['t2'], r0['t3']))
        seq=[]
        for y in range(0,420,30):
            await pg.evaluate(f"scrollTo(0,{y})"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(ST))
        hs=[x['h'] for x in seq]
        check('beim Scrollen schrumpft sie gleichmäßig (Höhe fällt monoton)', all(b<=a+0.5 for a,b in zip(hs,hs[1:])) and hs[-1]<hs[0]-100, hs)
        stuck=[x for x in seq if x['p']>0]
        check('sie bleibt direkt unter der Kopfzeile stehen', stuck and all(abs(x['top']-(x['hb']+6))<=1 for x in stuck), [(x['top'],x['hb']) for x in stuck][:3])
        r1=seq[-1]
        check('klein: Abbildung links schmal, Angaben rechts daneben', r1['p']==1 and r1['fw']<=120 and r1['tx']>r1['fw'] and r1['ty']<r1['h']/2 and r1['h']<=100, r1)
        # Eingabe ändern → Leiste folgt
        await pg.fill('#in-h','70'); await pg.wait_for_timeout(300)
        r=await pg.evaluate(ST)
        check('Eingabe geändert (h = 70 cm): Leiste aktualisiert', 'Ø' in r['t2'] and r['svg'], r['t2'])
        # unten bei den Ergebnissen ausgeblendet
        await pg.evaluate("document.getElementById('details').scrollIntoView()"); await pg.wait_for_timeout(250)
        r=await pg.evaluate(ST)
        check('bei den Ergebnissen ausgeblendet', r['op']<0.05, r['op'])
        # Antippen springt zur großen Abbildung
        await pg.evaluate("scrollTo(0,400)"); await pg.wait_for_timeout(200); await pg.click('#fd'); await pg.wait_for_timeout(900)
        t=await pg.evaluate("Math.round(document.getElementById('fig').closest('.card').getBoundingClientRect().top)")
        check('Antippen springt zur großen Abbildung', 0<=t<=160, t)
        # Stahl und Holz
        for m in ('stahl','holz','mauer'):
            await pg.evaluate(f"setMat('{m}'); scrollTo(0,0)"); await pg.wait_for_timeout(400); a=await pg.evaluate(ST)
            await pg.evaluate("scrollTo(0,500)"); await pg.wait_for_timeout(200); b=await pg.evaluate(ST)
            check(f'{m}: groß oben, klein beim Scrollen', a['on'] and a['svg'] and a['h']>=220 and b['h']<=100, (a['h'], b['h']))
        # Rechner: zwei Spalten → aus
        d=await br.new_page(viewport={'width':1280,'height':900}); d.on('pageerror', lambda e: errs.append(str(e)))
        await d.goto(B+'size.html'); await d.wait_for_timeout(800)
        r=await d.evaluate("[document.getElementById('fd').classList.contains('on'), getComputedStyle(document.getElementById('fd-ph')).display]")
        check('Rechner (zwei Spalten): keine mitlaufende Abbildung', r==[False,'none'], r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
