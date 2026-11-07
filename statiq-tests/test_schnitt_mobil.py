# „Schnitt führen“ direkt nach dem Laden und am Handy (calc v0.11.23).
# Fehler bis v0.11.22: Die erste Rechnung lief, bevor der Schnitt-Block die Rechenfunktionen umhüllte; ohne Eingabeänderung fehlte
#   das Modell, der Schnitt blieb leer (keine Linie, keine Werte). Jetzt wird das Modell beim Einschalten nachgeholt.
# Sollwerte von Hand (Grundeinstellung Einfeldträger L = 5 m, q = 5 kN/m, F = 10 kN in Feldmitte): A = B = 17,5 kN;
#   x = 2,5 m: M = 17,5·2,5 − 5·2,5²/2 = 28,13 kNm, Q = 5,00 | −5,00 kN.
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
RO="document.querySelector('.k-cutbar[data-sys=beam] .k-cutro').textContent"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        # Desktop, frisch geladen, ohne jede Eingabe
        pg=await br.new_page(viewport={'width':1280,'height':1000}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        await pg.click('.k-cutbar[data-sys="beam"] .k-cutbtn'); await pg.wait_for_timeout(150)
        r=await pg.evaluate(f"[!!document.querySelector('#diag-svg-beam .k-cut'), {RO}]")
        check('Desktop frisch geladen: Schnitt sichtbar, M = 28,13 kNm in Feldmitte', r[0] and 'M = 28,13 kNm' in r[1] and '5,00 | −5,00' in r[1], r)
        check('Desktop: Hinweis nennt die Pfeiltasten', 'Pfeiltasten' in r[1], r[1])
        r=await pg.evaluate("['cant','cont','frame'].map(s=>{ kragrMotion.cutToggle(s); const ok=!!document.querySelector('#diag-svg-'+s+' .k-cut') && /M = /.test(document.querySelector('.k-cutbar[data-sys='+s+'] .k-cutro').textContent); kragrMotion.cutToggle(s); return ok; })")
        check('Kragarm, Durchlaufträger, Rahmen frisch geladen: Schnitt mit Werten', r==[True]*3, r)
        await pg.close()
        # Handy 390 × 844, Touch
        ctx=await br.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True)
        pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        btn=pg.locator('.k-cutbar[data-sys="beam"] .k-cutbtn'); await btn.scroll_into_view_if_needed(); await pg.wait_for_timeout(200)
        y0=await pg.evaluate('scrollY'); await btn.tap(); await pg.wait_for_timeout(300)
        r=await pg.evaluate(f"[scrollY, {RO}]")
        check('Handy: Antippen zeigt den Schnitt, Seite springt nicht', r[0]==y0 and 'M = 28,13 kNm' in r[1], [y0]+r)
        check('Handy: Hinweis ohne Pfeiltasten', 'Finger' in r[1] and 'Pfeiltasten' not in r[1], r[1])
        sv=await pg.evaluate("(()=>{const r=document.getElementById('diag-svg-beam').getBoundingClientRect(); return [r.x,r.y,r.width,r.height]})()")
        m=await pg.evaluate("(()=>{ const s=document.getElementById('diag-svg-beam'), d=diagData.beam.members[0], M=s.getScreenCTM(); return [d.x0*M.a+M.e, d.x1*M.a+M.e]; })()")
        cdp=await ctx.new_cdp_session(pg); y=sv[1]+sv[3]*0.5; xa=m[0]+(m[1]-m[0])*0.2; xb=m[0]+(m[1]-m[0])*0.8
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':xa,'y':y}]})
        for i in range(1,13):
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':xa+(xb-xa)*i/12,'y':y+2*i}]}); await pg.wait_for_timeout(25)
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(250)
        r=await pg.evaluate(f"[kragrMotion.cut.beam.t, scrollY, {RO}]")
        # x = 4 m: M = 17,5·4 − 5·4²/2 − 10·1,5 = 15,00 kNm, Q = 17,5 − 20 − 10 = −12,50 kN
        check('Handy: Wischen zieht den Schnitt auf x = 4,00 m, Seite scrollt nicht', abs(r[0]-0.8)<0.02 and r[1]==y0, r[:2])
        check('Handy: Werte bei x = 4 m: M = 15,00 kNm, Q = −12,50 kN', 'x = 4,00 m' in r[2] and 'M = 15,00 kNm' in r[2] and 'Q = −12,50 kN' in r[2], r[2])
        r=await pg.evaluate("[document.documentElement.scrollWidth, (()=>{const b=document.querySelector('.k-cutbar[data-sys=beam]').getBoundingClientRect(); return Math.round(b.right);})()]")
        check('Handy: Ablesung bricht um, kein seitliches Scrollen', r[0]<=390 and r[1]<=390, r)
        await ctx.close()
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS', fails); sys.exit(1 if fails else 0)
