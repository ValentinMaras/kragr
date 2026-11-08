# Wissen, Holz-Paket (ref v0.3.68): Ausklinkung, Durchbruch, Satteldachträger, Querzug bei Anschlüssen.
# Sollwerte von Hand (k_mod 0,8 bzw. 0,9, γ_M = 1,3):
#   Ausklinkung C24, 120/240, h_ef = 180, x = 60, V = 8 kN: α = 0,75, k_v = 5/(√240·(0,433 + 0,8·0,25·0,878)) = 0,530,
#     τ = 1,5·8000/(0,5·120·180) = 1,111 → η = 1,111/(0,530·2,462) = 0,851
#   Durchbruch GL24h 140/600, h_d = 80, h_ro = 260, V = 40, M = 30: F_t,V = 40·80/2400·(3 − 80²/600²) = 3,98, F_t,M = 0,008·30000/260 = 0,92,
#     F_t,90 = 4,90 kN; l_t,90 = 0,5·(80 + 600) = 340, k_t,90 = (450/600)^0,5 = 0,866 → F_Rd = 0,5·340·140·0,866·0,308 = 6,34 kN, η = 0,773
#   Satteldach L = 15, h0 = 700, hap = 1200, q = 12: tan α = 0,0667, M_ap = 337,5 kNm, k_l = 1,117 → η First 0,665; Rand η 0,753; Querzug k_vol 0,536, η 0,508
#   Querzug GL24h kurz (k_mod 0,9), h = 400, a = 200, t_ef = 100, F = 10: F90,Rd = (6,5 + 4,5)·40000^0,8·0,346 = 18,29 kN, η 0,547
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
        t=await page('holzbau/details/ausklinkung','akl-out')
        check('Ausklinkung: α = 0,750, k_v = 0,530', '= 0,750' in t and '= 0,530' in t, t[:200])
        check('Ausklinkung: τ_d = 1,111, η = 0,851', '1,111 N/mm²' in t and '= 0,851' in t, '')
        await pg.evaluate("document.getElementById('akl-hef').value=100; updateAusklink()")
        check('Ausklinkung: α < 0,5 → Hinweis Verstärkung', 'Verstärkung' in await txt('akl-out'), '')
        t=await page('holzbau/details/durchbruch','dbr-out')
        check('Durchbruch: F_t,V = 3,98, F_t,90 = 4,90 kN', '3,98 kN' in t and '4,90 kN' in t, t[:300])
        check('Durchbruch: F_t,90,Rd = 6,34 kN, η = 0,773', '6,34 kN' in t and '= 0,773' in t, '')
        await pg.evaluate("document.getElementById('dbr-hd').value=120; updateDurchbruch()")
        check('Durchbruch: h_d > 0,15 h → nur mit Verstärkung', 'nur mit Verstärkung' in await txt('dbr-out'), '')
        t=await page('holzbau/details/sattel','sdt-out')
        check('Satteldach: tan α = 0,0667, Rand σ = 10,64, k_m,α = 0,956, η 0,753', '0,0667' in t and '10,64' in t and '0,956' in t and '0,753' in t, t[:300])
        check('Satteldach: First k_l = 1,117, η 0,665; Querzug k_vol 0,536, η 0,508', '1,117' in t and '0,665' in t and '0,536' in t and '0,508' in t, '')
        t=await page('holzbau/details/querzug','qzg-out')
        check('Querzug: α = 0,500, F90,Rd = 18,29 kN, η = 0,547', '= 0,500' in t and '18,29 kN' in t and '= 0,547' in t, t[:300])
        await pg.evaluate("document.getElementById('qzg-a').value=320; updateQuerzug()")
        check('Querzug: α = 0,8 → kein Nachweis erforderlich', 'kein Querzugnachweis erforderlich' in await txt('qzg-out'), '')
        await pg.evaluate("location.hash='#/holzbau/details/sattel'"); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(700)
        t=await txt('sdt-out')
        check('EN Satteldachträger: Rechenweg englisch', 'Double-tapered' in t and 'Satteldach' not in t, t[:120])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
