# Wissen › Querschnitte › Spannungen (ref v0.3.48): „Ausprobieren: Spannungsbild im Querschnitt“.
# σ(z) = N/A + M/I·z (z nach unten, Zug positiv), Farbe je Streifen, Nulllinie z0 = −N·I/(A·M). Sollwerte von Hand:
#   Rechteck 20/40 cm: A = 800 cm², I = 20·40³/12 = 106 667 cm⁴, W = 5333 cm³
#     M = 30 kNm, N = 0:     σ = ∓ 30e6/5,333e6 = ∓ 5,625 → −5,63 / 5,63 N/mm², Nulllinie in der Schwerachse
#     M = 30 kNm, N = +200:  N/A = 2,50 → σo = −3,125 → −3,13, σu = 8,125 → 8,13; z0 = 200e3·1,0667e9/(80 000·30e6) = 88,9 mm → 8,9 cm über S
#   IPE 240: I = 3892 cm⁴, h = 240 mm → M = 30 kNm: σ = 30e6·120/3,892e7 = 92,5 N/mm²
#     N = −600 kN: |z0| = 600e3·3,892e7/(3912·30e6) ≈ 199 mm > 120 mm → Nulllinie außerhalb, überall Druck
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
OUT="document.getElementById('spb-out').innerText.replace(/\\s+/g,' ')"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'ref.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        await pg.goto(B+'ref.html#/baustatik/querschnitte/spannungen'); await pg.wait_for_timeout(900)
        t=await pg.evaluate(OUT)
        check('Start: Rechteck 20/40, M = 30 kNm: A = 800 cm², I = 106667 cm⁴', 'A = 800,0 cm²' in t and 'Iy = 106667 cm⁴' in t, t)
        check('σ oben −5,63, σ unten 5,63 N/mm², Nulllinie in der Schwerachse', 'σoben = 0,00 − 5,63 = −5,63 N/mm²' in t and 'σunten = 0,00 + 5,63 = 5,63 N/mm²' in t and 'in der Schwerachse' in t, t)
        r=await pg.evaluate("()=>{const s=document.querySelector('#spb-fig svg'); const R=[...s.querySelectorAll('g[clip-path] rect')]; return {n:R.length, top:R[0].getAttribute('fill'), bot:R[R.length-1].getAttribute('fill'), mid:R[30].getAttribute('fill'), dash:!!s.querySelector('line[stroke-dasharray]')}}")
        def rgb(c): return [int(x) for x in re.findall(r'\d+', c)]
        tp,bt,md=rgb(r['top']),rgb(r['bot']),rgb(r['mid'])
        check('Farben: oben blau (Druck), unten rot (Zug), Mitte fast neutral', tp[2]>tp[0] and bt[0]>bt[2] and abs(md[0]-md[2])<20 and r['n']==60, r)
        check('Nulllinie gestrichelt im Bild', r['dash'], r)
        await pg.evaluate("document.getElementById('spb-N').value=200; updateSpBild()"); t=await pg.evaluate(OUT)
        check('N = +200 kN: σo = −3,13, σu = 8,13, Nulllinie 8,9 cm über S', '= −3,13 N/mm²' in t and '= 8,13 N/mm²' in t and 'z0 = 8,9 cm über der Schwerachse' in t, t)
        lab=await pg.evaluate("[document.getElementById('spb-Mo').textContent, document.getElementById('spb-No').textContent]")
        check('Anzeige an den Reglern: M = 30, N = +200', lab==[' = 30',' = +200'], lab)
        await pg.select_option('#spb-q','IPE 240'); await pg.evaluate("document.getElementById('spb-N').value=0; updateSpBild()"); t=await pg.evaluate(OUT)
        hid=await pg.evaluate("getComputedStyle(document.getElementById('spb-bh').closest('.calc-field')).display")
        check('IPE 240: A = 39,1 cm², I = 3892 cm⁴, σ = ∓ 92,51 N/mm²', 'A = 39,1 cm²' in t and 'Iy = 3892 cm⁴' in t and '= −92,51 N/mm²' in t and '= 92,51 N/mm²' in t, t)
        check('Profil gewählt: Felder b / h ausgeblendet', hid=='none', hid)
        await pg.evaluate("document.getElementById('spb-N').value=-600; updateSpBild()"); t=await pg.evaluate(OUT)
        check('N = −600 kN: Nulllinie außerhalb, überall Druck', 'außerhalb des Querschnitts' in t and t.count('−')>=4, t)
        await pg.evaluate("document.getElementById('spb-M').value=0; document.getElementById('spb-N').value=100; updateSpBild()"); t=await pg.evaluate(OUT)
        check('M = 0: keine Nulllinie, σ überall N/A', 'keine (M = 0' in t, t)
        await pg.select_option('#spb-q','r'); await pg.fill('#spb-b','0'); await pg.dispatch_event('#spb-b','input'); t=await pg.evaluate(OUT)
        check('b = 0: Hinweis statt Rechnung', 'Bitte b und h größer 0' in t, t)
        for l,h in [('en','Try it: stress distribution in the cross-section'),('fr','À essayer : contraintes dans la section'),('es','Pruébalo: tensiones en la sección')]:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{l}')"); await pg.goto('about:blank'); await pg.goto(B+'ref.html#/baustatik/querschnitte/spannungen'); await pg.wait_for_timeout(900)
            r=await pg.evaluate("[document.getElementById('spb-out').closest('.card').querySelector('.card-title').textContent, document.getElementById('spb-out').innerText]")
            check(f'{l}: Titel übersetzt, Ausgabe ohne deutsche Wörter', h in r[0] and 'Schwerachse' not in r[1] and 'Nulllinie' not in r[1] and 'oben' not in r[1] and 'unten' not in r[1], r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
