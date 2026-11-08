# Wissen v0.3.69: Laschenstoß (Stahlbau → Verbindungen) — Rechner gegen dieselbe unabhängige Handrechnung wie test_size_lasche.py,
# Varianten, Skizze, Verweis auf „Bemessung“, Übersetzung. Ohne Playwright: SKIP.
import os, sys, asyncio, importlib.util
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/ref.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
src=open(os.path.join(HERE,'test_size_lasche.py'),encoding='utf-8').read()
ns={'math':__import__('math')}; exec(src[src.index('PR={'):src.index('async def res')], ns); hand=ns['hand']
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:220])
near=lambda a,b,r=2e-3: abs(a-b)<=r*max(1,abs(b))
K=['Mw','Ff','RgrF','NL','Nf','Ms','Fr','FS','Mel','Vpl','hs']
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.evaluate("location.hash='#/stahlbau/verbindungen/lasche'"); await pg.wait_for_timeout(500)
        async def calc(vals):
            await pg.evaluate("vals=>{ for(const [k,v] of Object.entries(vals)) document.getElementById(k).value=v; updateLasche(); }", vals)
            I=await pg.evaluate("""()=>{ const g=id=>document.getElementById(id).value; return {prof:g('lsr-prof'),st:g('lsr-st'),d:g('lsr-d'),kl:g('lsr-kl'),M:+g('lsr-M'),V:+g('lsr-V'),ga:g('lsr-ga'),ta:+g('lsr-ta'),ti:+g('lsr-ti'),n1:+g('lsr-n1'),e1:+g('lsr-e1'),p1:+g('lsr-p1'),w:+g('lsr-w'),ts:+g('lsr-ts'),nv:+g('lsr-nv'),nh:+g('lsr-nh'),pv:+g('lsr-pv'),ph:+g('lsr-ph'),es:+g('lsr-es'),e:+g('lsr-e')}; }""")
            return await pg.evaluate("I=>{ const R=lsrRechnung(I); return Object.fromEntries(Object.entries(R).filter(([k,v])=>typeof v==='number')); }", I)
        def cmp(r,e): return all(near(r[k],e[k]) for k in K), {k:(round(r[k],2),round(e[k],2)) for k in K if not near(r[k],e[k])}
        r=await calc({}); ok,info=cmp(r,hand()); check('Vorgabe IPE 300, M20 8.8 wie Handrechnung (M_w, F_f, Gurt- und Stegschrauben, Laschen)', ok, info)
        t=await pg.evaluate("document.getElementById('lsr-out').textContent")
        check('Rechenweg: M_w = 12,25 kNm, F_f = 234,2 kN, Steg F_Ed = 55,6 kN', '12,25 kNm' in t and '234,2 kN' in t and '55,6 kN' in t, t[:160])
        r=await calc({'lsr-ga':'ai'}); ok,info=cmp(r,hand(ga='ai')); check('außen und innen (zweischnittig)', ok, info)
        r=await calc({'lsr-ga':'a','lsr-n1':'6','lsr-p1':'80'}); ok,info=cmp(r,hand(n1=6,p1=80)); check('lange Verbindung (β_Lf)', ok and 'β' in await pg.evaluate("document.getElementById('lsr-out').textContent"), info)
        r=await calc({'lsr-n1':'2','lsr-p1':'70','lsr-V':'250','lsr-M':'40'}); ok,info=cmp(r,hand(V=250,M=40)); check('große Querkraft: Abminderung ρ', ok, info)
        await calc({'lsr-w':'20'}); check('ungültiger Querabstand: Hinweis', 'gültige Werte' in await pg.evaluate("document.getElementById('lsr-out').textContent"))
        n=await pg.evaluate("[document.querySelectorAll('#main .skfig svg').length, document.querySelectorAll('#main a.applink').length]")
        check('Skizze und Verweis auf „Bemessung“', n[0]>=1 and n[1]>=1, n)
        await pg.evaluate("localStorage.setItem('statiq-lang','es')"); await pg.reload(); await pg.wait_for_timeout(700)
        t=await pg.evaluate("document.getElementById('lsr-out').textContent"); h=await pg.evaluate("document.getElementById('main').textContent")
        check('ES: Seite und Rechenweg spanisch', 'Empalme' in t and 'Tornillos de ala' in t and 'Laschen' not in h, t[:120])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
