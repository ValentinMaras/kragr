# Wissen, Mauerwerk-Paket (ref v0.3.68): neue Seite Ausfachungswand, Skizzen für Teilflächenpressung, Kellerwand und Schubwand.
# Sollwerte von Hand (DIN EN 1996-3/NA, Tab. NA.C.1, vierseitig gehalten):
#   t = 175 mm, bis 8 m, h = 2,75, l = 5,0: A = 13,75 m², ε = 1,818 → A_zul = 20 − 6 · 0,818 = 15,09 m², η = 0,911
#   t = 150 mm, Klasse ≥ 12: 12·4/3 = 16,0 und 8·4/3 = 10,67 → A_zul = 16 − 5,333 · 0,818 = 11,64 m², η = 1,182
#   t = 115 mm, 8 … 20 m: nicht zulässig
#   Kellerwand (Seitenvorgabe): b_c = 4, h = 2,5 → β = 60 − 32 = 28,00; n_erf = 19 · 2,5 · 4 / (28 · 0,3) = 22,6 kN/m
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/ref.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:220])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        async def page(k, out):
            await pg.evaluate(f"location.hash='#/{k}'"); await pg.wait_for_timeout(500)
            return (await pg.evaluate(f"document.getElementById('{out}').textContent")).replace(' = ','= ')
        async def txt(out): return (await pg.evaluate(f"document.getElementById('{out}').textContent")).replace(' = ','= ')
        t=await page('mauerwerk/bemessung/ausfach','afr-out')
        check('Ausfachung: A = 13,75 m², ε = 1,82', '13,75 m²' in t and '= 1,82' in t, t[:200])
        check('Ausfachung: A_zul = 15,09 m², η = 0,911', '15,09 m²' in t and '0,911' in t, t[-200:])
        await pg.evaluate("document.getElementById('afr-t').value='150'; document.getElementById('afr-sfk').value='12'; updateAusfach()")
        t=await txt('afr-out')
        check('Ausfachung 150 mm, Klasse 12: +1/3 → A_zul = 11,64 m², η = 1,182, Abhilfe', 'um 1/3' in t and '11,64' in t and '1,182' in t and 'Zu groß' in t, t[-260:])
        await pg.evaluate("document.getElementById('afr-t').value='115'; document.getElementById('afr-z').value='20'; updateAusfach()")
        check('Ausfachung 115 mm über 8 m: nicht zulässig', 'nur bis 8 m' in await txt('afr-out'), '')
        n=await pg.evaluate("document.querySelectorAll('#main .skfig svg').length")
        check('Ausfachung: Skizze vorhanden', n>=1, n)
        for k in ['teilflaeche','keller','schub']:
            await pg.evaluate(f"location.hash='#/mauerwerk/bemessung/{k}'"); await pg.wait_for_timeout(400)
            n=await pg.evaluate("document.querySelectorAll('#main .skfig svg').length"); a=await pg.evaluate("document.querySelectorAll('#main a.applink').length")
            check(f'{k}: Skizze und Link zur Bemessung', n>=1 and a>=1, (n,a))
        t=await page('mauerwerk/bemessung/keller','mwk-out')
        check('Kellerwand unverändert: β = 28,00, n_erf = 22,6 kN/m', '28,00' in t and '22,6 kN/m' in t, t[:200])
        await pg.evaluate("location.hash='#/mauerwerk/bemessung/ausfach'"); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.setItem('statiq-lang','fr')"); await pg.reload(); await pg.wait_for_timeout(700)
        t=await txt('afr-out'); h=await pg.evaluate("document.getElementById('main').textContent")
        check('FR Ausfachung: Rechenweg und Seite französisch', 'Remplissage' in t and 'Surface admissible' in t and 'Ausfachung' not in h, t[:120])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
