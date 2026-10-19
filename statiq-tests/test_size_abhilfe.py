# statiq·size v0.5.19 Abhilfe: Bei nicht erfüllten Nachweisen nennt size die Ursache und rechnet Stellschrauben durch
# („So wird der Nachweis erfüllt“). Geprüft: Vorschläge stimmen mit unabhängiger Handrechnung, „Übernehmen“ erfüllt den Nachweis,
# Eingaben und Ergebnis bleiben nach der Suche unverändert, Bericht und Englisch. Ohne Playwright: SKIP.
import os, sys, re, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
HTML='file://'+BASE+'/size.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
CASES=[  # Modus, geänderte Eingaben, Nachweis, Stellschraube
 ("setMat('holz'); setHoMode('bauteil')", {'ho-M':'20'}, 'biegung', ['ho-h','ho-b','ho-kl']),
 ("setMat('stahl'); setStMode('traeger')", {'sn-M':'200'}, 'qs', ['sn-prof']),
 ("setMat('beton'); setTyp('platte')", {'in-l':'8'}, 'schlank', ['in-h']),
 ("setMat('grund'); setGrMode('flach')", {'gf-VG':'2500'}, 'gfgb', ['gf-b','gf-a','gf-d']),
 ("setMat('mauer'); setMwMode('druck')", {'md-N':'600'}, 'mdn', ['mw-fb']),
 ("setMat('bauph'); setBpMode('uwert')", {'bl-d3':'4'}, 'bugeg', ['bl-d3']),
 ("setMat('wasser'); setWbMode('rohr')", {'wr-Q':'120'}, 'wrhv', ['wr-D']),
 ("setMat('stahl'); setStMode('anschluss')", {'an-V':'400'}, 'scher', ['an-n1']),
]
async def wait_fix(pg):
    await pg.wait_for_function("document.querySelector('.fixbox') || !document.querySelector('#chk-table .tag.bad')", timeout=15000)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1400,'height':1000}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(250)
        check('erfüllte Nachweise: keine Abhilfe-Kästen', await pg.evaluate("!document.querySelector('.fixbox')"))
        for go,vals,cid,levers in CASES:
            await pg.evaluate(go); await pg.wait_for_timeout(60)
            for k,v in vals.items(): await pg.evaluate(f"$('{k}').value='{v}'; run()")
            before=await pg.evaluate("[document.getElementById('summary').innerText, [...document.querySelectorAll('.col-in input, .col-in select')].map(e=>e.id+'='+e.value+e.checked+e.disabled).join('|'), LAST && LAST.res ? LAST.res.C.length : 0]")
            t0=await pg.evaluate("performance.now()"); await wait_fix(pg); dt=await pg.evaluate("performance.now()")-t0
            after=await pg.evaluate("[document.getElementById('summary').innerText, [...document.querySelectorAll('.col-in input, .col-in select')].map(e=>e.id+'='+e.value+e.checked+e.disabled).join('|'), LAST && LAST.res ? LAST.res.C.length : 0]")
            tag=go.split(';')[1].strip()
            check(f'{tag}: Eingaben und Ergebnis nach der Suche unverändert', before==after)
            box=await pg.evaluate(f"(document.querySelector('#n-{cid} .fixbox')||{{}}).innerText||''")
            check(f'{tag}: Kasten bei „{cid}“ mit Ursache', 'Warum nicht erfüllt?' in box and 'Ausnutzung η' in box, box[:80])
            got=await pg.evaluate(f"[...document.querySelectorAll('#n-{cid} .fixbox button[data-fix]')].map(b=>b.dataset.fix)")
            check(f'{tag}: Stellschrauben {levers}', all(l in got for l in levers), got)
            check(f'{tag}: Suche schnell (< 3 s)', dt<3000, f'{dt:.0f} ms')
            fx=await pg.evaluate(f"LAST.res.C.find(c=>c.id==='{cid}').fix")
            if go.startswith("setMat('holz')"):
                # unabhängig: C24, NKL 1, KLED mittel → f_m,d = 0,8·24/1,3; σ = 6M/(b h²)
                fmd=0.8*24/1.3; M=20e6
                hreq=math.sqrt(6*M/(100*fmd)); breq=6*M/(220**2*fmd)
                fh=next(f for f in fx if f['id']=='ho-h'); fb=next(f for f in fx if f['id']=='ho-b')
                check('Holz: h = nächste 10 mm über √(6M/(b·f_m,d))', fh['v']==math.ceil(hreq/10)*10, (fh['v'], round(hreq,1)))
                check('Holz: b = nächste 10 mm über 6M/(h²·f_m,d)', fb['v']==math.ceil(breq/10)*10, (fb['v'], round(breq,1)))
            if go.startswith("setMat('stahl'); setStMode('traeger')"):
                f=next(f for f in fx if f['id']=='sn-prof')
                # W_pl,y IPE 330 = 804 cm³, IPE 360 = 1019 cm³ (S235, γM0 = 1): M_pl = 189 bzw. 239 kNm
                check('Stahl: kleinstes ausreichendes Profil IPE 360 (M_pl 239 ≥ 200 > 189 kNm)', f['v']=='IPE 360', f['v'])
            # „Übernehmen“ erfüllt den Nachweis
            lv=levers[0]
            await pg.evaluate(f"document.querySelector('#n-{cid} .fixbox button[data-fix=\"{lv}\"]').click()"); await pg.wait_for_timeout(120)
            ok=await pg.evaluate(f"LAST.res.C.find(c=>c.id==='{cid}').ok")
            check(f'{tag}: „Übernehmen“ ({lv}) erfüllt den Nachweis', ok)
            await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        # Bericht
        await pg.evaluate("setMat('holz'); setHoMode('bauteil'); $('ho-M').value='20'; run()"); await wait_fix(pg)
        rep=await pg.evaluate("buildReport()")
        check('Bericht nennt die Abhilfe', 'So wird der Nachweis erfüllt' in rep and 'statt' in rep)
        # nicht erreichbar mit einer Eingabe
        await pg.evaluate("setMat('holz'); setHoMode('bauteil'); $('ho-M').value='2000'; run()"); await wait_fix(pg)
        box=await pg.evaluate("(document.querySelector('#n-biegung .fixbox')||{}).innerText||''")
        check('Unerreichbar: Hinweis auf mehrere Größen', 'mehrere Größen' in box or 'Höhe' in box, box[-100:])
        # Englisch
        await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(250)
        await pg.evaluate("setMat('holz'); setHoMode('bauteil'); $('ho-M').value='20'; run()"); await wait_fix(pg)
        box=await pg.evaluate("(document.querySelector('#n-biegung .fixbox')||{}).innerText||''")
        check('EN: Kasten englisch', 'Why is it not satisfied?' in box and 'instead of' in box and 'bending stress' in box and not re.search('[äöüß]', box), box[:120])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
