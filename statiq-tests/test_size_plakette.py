# size v0.5.46: Ergebnis am Handy als kleine Plakette unten mittig statt Balken über die ganze Breite unter der Kopfzeile.
# Kurzer Text (✓ max. 97 % / ✕ 3 nicht erfüllt), voller Text als Titel, Tipp springt zum Ergebnis, ausgeblendet solange
# das Ergebnis im Bild ist, nicht am Rechner, nicht im Bericht. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
ST="(()=>{const m=document.getElementById('mob-status'),b=m.getBoundingClientRect(),c=getComputedStyle(m); return {t:m.textContent,title:m.title,w:Math.round(b.width),l:Math.round(b.left),bot:Math.round(b.bottom),d:c.display,away:m.classList.contains('away'),cls:m.className,pos:c.position}})()"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':760}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(600)
        s=await pg.evaluate(ST)
        check('Handy: Plakette unten mittig, schmal (≤ 60 % der Breite), fest', s['pos']=='fixed' and s['w']<=234 and abs(s['l']+s['w']/2-195)<=2 and 700<=s['bot']<=760, s)
        check('kurzer Text „✓ max. 97 %“, voller Text als Titel', s['t'].startswith('✓') and 'max. 97 %' in s['t'] and s['title'].startswith('Alle Nachweise erfüllt · max. 97 %') and s['cls']=='ok', s)
        await pg.click('#mob-status'); await pg.wait_for_timeout(1000)
        s=await pg.evaluate(ST); top=await pg.evaluate("Math.round(document.getElementById('results').getBoundingClientRect().top)")
        check('Tipp: springt zum Ergebnis, Plakette blendet aus', s['away'] and top<400, (s['away'], top))
        await pg.evaluate("scrollTo(0,0)"); await pg.wait_for_timeout(500)
        check('zurück nach oben: Plakette wieder da', not (await pg.evaluate(ST))['away'])
        await pg.evaluate("$('in-h').value='25'; run()"); await pg.wait_for_timeout(300)
        s=await pg.evaluate(ST)
        check('nicht erfüllt: rot, „✕ 3 nicht erfüllt“', s['cls']=='bad' and s['t'].startswith('✕') and 'nicht erfüllt' in s['t'] and 'Nachweise nicht erfüllt' in s['title'], s)
        res={}
        for lang,w in [('en','not satisfied'),('fr','non satisfaite'),('es','no cumple')]:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(500)
            await pg.evaluate("$('in-h').value='25'; run()"); await pg.wait_for_timeout(200); res[lang]=w in (await pg.evaluate(ST))['t']
        check('EN/FR/ES übersetzt', all(res.values()), res)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        await pg.close()
        pg=await br.new_page(viewport={'width':1280,'height':800}); await pg.goto(U); await pg.wait_for_timeout(500)
        check('Rechner: keine Plakette', (await pg.evaluate(ST))['d']=='none')
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
