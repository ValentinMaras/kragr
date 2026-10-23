# calc → size: gespeicherte Berechnungen in size übernehmen (Einfeldträger, Kragarm, Durchlaufträger, Rahmen) — Browser. Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:62}', str(info)[:160])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        # Startwerte: EFT L = 5 m, q = 5, F = 10 mittig → M = 5·25/8 + 10·5/4 = 28,125; V = 17,5
        await pg.evaluate("calculateBeam(); saveCalc('beam')"); await pg.wait_for_timeout(15)
        # Kragarm L = 3, q = 5, F = 10 bei 1,5 → M = 22,5 + 15 = 37,5; V = 25
        await pg.evaluate("showTab('cantilever'); calculateCantilever(); saveCalc('cantilever')"); await pg.wait_for_timeout(15)
        # DLT 2 × 5 m, q = 5 → M_Feld = 0,07·q·l² = 8,79, M_B = −q·l²/8 = −15,63, V = 0,625·q·l = 15,63
        await pg.evaluate("showTab('cont'); calculateContinuous(); saveCalc('cont')"); await pg.wait_for_timeout(15)
        await pg.evaluate("showTab('frame'); calculateFrame(); saveFrameCalc();"); await pg.wait_for_timeout(15)
        await pg.evaluate("showTab('saved')"); await pg.wait_for_timeout(100)
        keys=await pg.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_')).sort()")
        check('calc: Knopf „In size bemessen“ an jeder Berechnung', await pg.locator('a[href^="size.html#calc="]').count()==4)
        await pg.click(f'a[href="size.html#calc={keys[0]}"]'); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(900)
        g=lambda i: pg.input_value('#'+i)
        check('Link öffnet size, Adresse ohne #calc', pg.url.endswith('size.html'), pg.url)
        v=[await g(i) for i in ['in-l','in-K','in-M','in-Ms','in-V']]
        check('EFT → Balken: l, K, M = 28,13, V = 17,5', v==['5','1.0','28.13','0','17.5'], v)
        check('Hinweis: M_qp von Hand', 'Mqp' in await pg.inner_text('#ci-msg'))
        await pg.evaluate("setTyp('unterzug')"); await pg.evaluate('mulyAltProj()'); await pg.select_option('#ci-sel', keys[2]); await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        v=[await g(i) for i in ['in-l','in-feld','in-K','in-M','in-Ms','in-V']]
        check('DLT → Unterzug: Endfeld, M = 8,79, |M_St| = 15,63', v==['5','0.85','1.3','8.79','15.63','15.63'], v)
        await pg.evaluate("setTyp('stuetze')"); await pg.evaluate('mulyAltProj()'); await pg.select_option('#ci-sel', keys[3]); await pg.evaluate('mulyAltProj()'); await pg.select_option('#ci-part','stiel'); await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        fr=await pg.evaluate(f"JSON.parse(localStorage.getItem('{keys[3]}')).sdf.plot.fine")
        cands=[]
        for m,h in [('left',4),('right',4)]:
            c=fr[m]; N=-min(c['N']); a,b=c['M'][0],c['M'][-1]; big,small=(a,b) if abs(a)>=abs(b) else (b,a)
            cands.append((N,h,abs(big),(1 if big*small>0 else -1)*abs(small)))
        N,h,M02,M01=max(cands)
        v=[float(await g(i)) for i in ['su-l','su-N','su-M02','su-M01']]
        check(f'Rahmen → Stütze: N = {N:.2f}, M02 = {M02:.2f}, M01 = {M01:.2f}', abs(v[0]-h)<1e-9 and abs(v[1]-N)<0.006 and abs(v[2]-M02)<0.006 and abs(v[3]-M01)<0.006, v)
        await pg.evaluate("setMat('stahl')"); await pg.evaluate('mulyAltProj()'); await pg.select_option('#ci-part','riegel'); await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        raf=fr['rafter']; v=[float(await g(i)) for i in ['sn-L','sn-M','sn-V','sn-N']]
        check('Rahmen → Stahl (Riegel): M = max|M|, V, N Druck', abs(v[1]-max(abs(x) for x in raf['M']))<0.006 and abs(v[2]-max(abs(x) for x in raf['Q']))<0.006 and abs(v[3]+min(raf['N']))<0.006, v)
        await pg.evaluate('mulyAltProj()'); await pg.select_option('#ci-part','stiel'); await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        check('Rahmen-Stiel → Stahl: linearer Verlauf mit ψ', await g('sn-mv')=='lin' and abs(float(await g('sn-psi'))-M01/M02)<0.01, await g('sn-psi'))
        await pg.evaluate("setMat('holz')"); await pg.evaluate('mulyAltProj()'); await pg.select_option('#ci-sel', keys[1]); await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        v=[await g(i) for i in ['ho-L','ho-M','ho-V','ho-F']]
        check('Kragarm → Holz: M = 37,5, V = 25, Auflagerkraft 25', v==['3','37.5','25','25'], v)
        await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        check('Kragarm → Beton: Betrag, K = 0,4, Hinweis Zug oben', [await g('in-M'), await g('in-K')]==['37.5','0.4'] and 'Zugseite oben' in await pg.inner_text('#ci-msg'))
        await pg.evaluate("setTyp('stuetze')"); await pg.evaluate('mulyAltProj()'); await pg.select_option('#ci-sel', keys[0]); await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        check('Einfeldträger → Stütze: Hinweis „nur Rahmen liefern N“', 'Normalkraft' in await pg.inner_text('#ci-msg'))
        await pg.evaluate("localStorage.setItem('statiq_sdf_1', JSON.stringify({name:'alt', sdf:{module:'calc', timestamp:new Date().toISOString(), system:{type:'beam'}, results:{}}})); renderCalcImport('statiq_sdf_1')")
        await pg.evaluate('mulyAltProj()'); await pg.click('#ci-form button')
        check('alte Speicherstände ohne Verläufe → Hinweis', 'älteren calc-Version' in await pg.inner_text('#ci-msg'))
        await pg.evaluate("localStorage.clear(); renderCalcImport()")
        check('ohne gespeicherte Berechnungen → Hinweis mit Link zu calc', 'kragr·calc' in await pg.inner_text('#calc-import') and not await pg.is_visible('#ci-form'))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
