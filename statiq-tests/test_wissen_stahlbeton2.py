# Wissen, Stahlbeton-Paket (ref v0.3.68): Zugkraftdeckung und Staffelung, zweiachsige Biegung bei Stützen, zweiachsig gespannte Platten.
# Sollwerte von Hand:
#   Zugkraft: l = 6 m, q = 40 kN/m, d = 450 mm, cot θ = 1,2, 6 Ø16 (3 durchlaufend), C30/37: z = 405 mm, a_l = 243 mm, M = 180 kNm, F = 444,4 kN,
#     F_Rd = 6·201,06·434,78 = 524,5 kN (η 0,847); f_bd = 2,25·2,0/1,5 = 3,00, l_bd = 16/4·434,78/3 = 580 mm;
#     3 Stäbe 262,3 kN → M = 106,2 kNm bei ξ = 3 − √(9 − 5,311) = 1,079 m → x = ξ − a_l = 0,836 m; Staffelbeginn 0,836 − 0,580 = 0,26 m
#   Zweiachsig: N/N_Rd = 1500/4000 = 0,375 → a = 1 + 0,5·0,275/0,6 = 1,229; (50/150)^a + (80/200)^a = 0,259 + 0,324 = 0,583
#   Platte 5 × 6 m, q = 10: k_x = 1296/1921 = 0,6746, ν_x = 1 − 5/6·0,6944·0,6746 = 0,6096 → m_x = 12,85, m_y = 8,92 kNm/m
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
        t=await page('stahlbeton/bewehrung/zugkraft','zkd-out')
        check('Zugkraft: z = 405,0 mm, a_l = 243 mm', 'z= 0,9 · d= 0,9 · 450= 405,0 mm' in t and '243 mm' in t, t[:200])
        check('Zugkraft: M = 180,0 kNm, F_sd,max = 444,4 kN, F_Rd = 524,5 kN', '180,0 kNm' in t and '444,4 kN' in t and '524,5 kN' in t, '')
        check('Zugkraft: f_bd = 3,00, l_bd = 580 mm', '3,00 N/mm²' in t and 'lbd= 580 mm' in t, '')
        check('Zugkraft: Staffelung ab x = 0,836 m, Beginn 0,26 m, Ende 5,74 m', 'x= 0,836 m' in t and '0,26 m' in t and '5,74 m' in t, t[-300:])
        await pg.evaluate("document.getElementById('zkd-nd').value=6; updateZugkraft()")
        t=(await pg.evaluate("document.getElementById('zkd-out').textContent"))
        check('Zugkraft: alle 6 Stäbe durchlaufend → keine Staffelung nötig', 'decken die verschobene Zugkraftlinie überall' in t, '')
        t=await page('stahlbeton/stuetzen/zweiachsig','zwa-out')
        check('Zweiachsig: a = 1,229, Summe 0,583', 'a= 1,229' in t and '= 0,583' in t, t[:300])
        await pg.evaluate("document.getElementById('zwa-N').value=400; updateZweiachsig()")
        t=(await pg.evaluate("document.getElementById('zwa-out').textContent")).replace(' = ','= ')
        check('Zweiachsig: N/N_Rd = 0,1 → a = 1,000 (linear)', 'a= 1,000' in t, t[:160])
        t=await page('stahlbeton/bemessung/platte2','pl2-out')
        check('Platte: k_x = 0,6746, ν_x = 0,6096', '= 0,6746' in t and '= 0,6096' in t, t[:300])
        check('Platte: m_x = 12,85, m_y = 8,92 kNm/m', '12,85 kNm/m' in t and '8,92 kNm/m' in t, t[-300:])
        await pg.evaluate("location.hash='#/stahlbeton/bewehrung/zugkraft'"); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(700)
        t=(await pg.evaluate("document.getElementById('zkd-out').textContent"))
        check('EN Zugkraftdeckung: Rechenweg englisch', 'Curtailment' in t and 'Staffelung' not in t, t[:120])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
