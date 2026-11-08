# Wissen, Grundbau-Paket (ref v0.3.67): Auftrieb (UPL), Winkelstützwand, Spundwand nach Blum, axial belasteter Pfahl.
# Sollwerte unabhängig nachgerechnet (Python, eigene Formeln):
#   Auftrieb Wanne 12 × 10 m, t_s 0,5, Wände 3 m × 0,3 m, Decke 0,25 m, h_w = 2,0 m: G = 1500 + 25·(120 − 11,4·9,4)·3 + 750 = 3213,0 kN;
#     A = 10·2·120 = 2400 kN → 1,05·2400 = 2520,0 ≤ 0,95·3213 = 3052,4 kN, η = 0,826
#   Stützwand H 4, B 2,8, b_v 0,5, t_W 0,3, t_s 0,4, φ′ 32,5°, γ 19, q 10, δ = 2/3·φ′: K_a = 0,2697, K_ah = 0,2506, E_ah,G = 38,1, E_ah,Q = 10,0 kN/m,
#     V_G = 206,9 kN/m, e_G = −0,024 m, e = 0,046 m, Gleiten η = 0,555
#   Blum h 3, φ′ 32,5°, γ 19, q 10, BS-P: K_a = 0,3010, K_p = 3,3225, t_0 = 4,425 m, t_erf = 5,31 m, M_max,d = 164,9 kNm/m, C = 195,1 kN/m
#   Pfahl D 0,9, q_b 2500, Schichten 4 m × 50 und 6 m × 90 kN/m², G 1200, Q 500: R_b = 1590,4, R_s = 2092,3, R_c,k = 3682,7, R_c,d = 2630,5, E_c,d = 2370,0 kN, η = 0,901
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
        t=await page('grundbau/flach/auftrieb','upl-out')
        check('Auftrieb: G_stb,k = 3213,0 kN, A_k = 2400,0 kN', 'Gstb,k= 3213,0 kN' in t and '= 2400,0 kN' in t, t[:200])
        check('Auftrieb: 1,05·2400 = 2520,0 ≤ 0,95·3213 = 3052,4 kN, η = 0,826', '= 2520,0 kN≤' in t.replace(' ≤','≤') and '= 3052,4 kN' in t and 'η= 0,826' in t, t[-260:])
        t=await page('grundbau/stuetz/stuetzwand','swk-out')
        check('Stützwand: K_a = 0,2697, K_ah = 0,2506, E_ah,G = 38,1, E_ah,Q = 10,0', 'Ka= 0,2697' in t and '0,2506' in t and '38,1 kN/m' in t and '10,0 kN/m' in t, t[:260])
        check('Stützwand: V_G = 206,9 kN/m, e_G = −0,024 m, e = 0,046 m', 'VG= 206,9 kN/m' in t and '-0,024 m' in t and '0,046 m' in t, t[300:600])
        check('Stützwand: Gleiten H_d/R_t,d = 0,555', '= 0,555' in t, t[-200:])
        t=await page('grundbau/stuetz/spundwand','blu-out')
        check('Blum: K_a = 0,3010, K_p = 3,3225, t_0 = 4,425 m, t_erf = 5,31 m', 'Ka= 0,3010' in t and 'Kp= 3,3225' in t and 't0= 4,425 m' in t and '5,31 m' in t, t[:400])
        check('Blum: M_max,d = 164,9 kNm/m, C = 195,1 kN/m', '164,9 kNm/m' in t and '195,1 kN/m' in t, t[-300:])
        t=await page('grundbau/pfahl/axial','pfa-out')
        check('Pfahl: R_b,k = 1590,4, R_s,k = 2092,3, R_c,k = 3682,7 kN', '1590,4 kN' in t and '2092,3 kN' in t and '3682,7 kN' in t, t[:300])
        check('Pfahl: R_c,d = 2630,5 kN, E_c,d = 2370,0 kN, η = 0,901', '2630,5 kN' in t and '2370,0 kN' in t and '= 0,901' in t, t[-300:])
        await pg.evaluate("document.getElementById('pfa-Q').value=800; updatePfahl()")
        t=(await pg.evaluate("document.getElementById('pfa-out').textContent"))
        check('Pfahl: Q = 800 kN → E_c,d = 2820,0 kN > R_c,d (nicht erfüllt)', '2820,0 kN' in t and 'nicht erfüllt' in t, '')
        r=await pg.evaluate("[...document.querySelectorAll('#pick-menu, .pick')].length>=0 && Object.keys(FAECHER.grundbau.kapitel)")
        check('Grundbau: Kapitel Stützbauwerke und Pfahlgründungen hinter Böschungen (Nummern bleiben)', r[-3:]==['boeschung','stuetz','pfahl'], r)
        # Englisch ohne deutsche Reste in den Rechnern
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(500)
        t=await page('grundbau/pfahl/axial','pfa-out')
        check('EN Pfahl: Rechenweg englisch („Characteristic resistance“)', 'Characteristic resistance' in t and 'Widerstand' not in t, t[:160])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
