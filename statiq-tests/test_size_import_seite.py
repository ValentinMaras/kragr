# statiq·size v0.5.26/0.5.27 (Seitenansicht seit v0.7.12 entfernt, geprüft wird der Momentenverlauf): Seitenansicht und Momentenverlauf (C₁) nach „Aus calc übernehmen“ — echtes System aus calc (Lager, Lasten, Momentenlinie,
# gedrückter Gurt nach Vorzeichen) für Stahlträger und Holzbauteil; nach Änderung von L oder M wieder schematisch. Ohne Playwright: SKIP.
import os, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:160])
SIDE="""(()=>{ const s=[...document.querySelectorAll('#fig svg')].find(x=>/Seitenansicht|Side view|Vue latérale|Vista lateral/.test(x.getAttribute('aria-label')||'')); if(!s) return null;
  const blue=[...s.querySelectorAll('rect[fill="'+C_IN+'"]')].map(r=>+r.getAttribute('y'));
  return { txt:[...s.querySelectorAll('text')].map(t=>t.textContent), blue, tri:s.querySelectorAll('path[d$="Z"][fill="#fff"]').length,
    hatch:[...s.querySelectorAll('line')].filter(l=>l.getAttribute('stroke-width')==='1.6' && l.getAttribute('stroke')==='#111').length, wood:!!s.querySelector('rect[fill="#f3ead9"]'),
    legend:s.nextElementSibling?.textContent||'', prof:document.querySelector('#fig .fig-legend')?.textContent||'' }; })()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1300,'height':1300}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("calculateBeam(); saveCalc('beam')"); await pg.wait_for_timeout(15)
        await pg.evaluate("showTab('cantilever'); calculateCantilever(); saveCalc('cantilever')"); await pg.wait_for_timeout(15)
        await pg.evaluate("showTab('cont'); calculateContinuous(); saveCalc('cont')"); await pg.wait_for_timeout(15)
        await pg.evaluate("showTab('frame'); calculateFrame(); saveFrameCalc();"); await pg.wait_for_timeout(15)
        keys=await pg.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_')).sort()")
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(500)
        async def imp(mat, k, part=None):
            await pg.evaluate(f"setMat('{mat}'); {'setStMode' if mat=='stahl' else 'setHoMode'}('{'traeger' if mat=='stahl' else 'bauteil'}'); renderCalcImport('{keys[k]}')")
            if part: await pg.evaluate(f"$('ci-part').value='{part}'")
            await pg.evaluate(f"importCalc('{keys[k]}')"); await pg.wait_for_timeout(120)
            return await pg.evaluate(SIDE)
        # seit size v0.7.12 keine Seitenansicht mehr — auch nicht nach dem Import aus calc
        for k,part in ((0,None),(1,None),(2,None),(3,'riegel'),(3,'stiel')):
            r=await imp('stahl',k,part)
            check(f'Import {k}{" "+part if part else ""}: keine Seitenansicht', r is None)
        await imp('stahl',0)
        check('Import setzt L_LT = Stützweite (mit Hinweis)', await pg.input_value('#sn-Llt')=='5' and 'Stützweite angenommen' in await pg.inner_text('#ci-msg'))
        await imp('stahl',1)
        check('Kragarm: Legende am Profil „Druck unten“', 'Druck unten' in await pg.evaluate("document.querySelector('#fig .fig-legend')?.textContent||''"))
        # Momentenverlauf aus calc (seit v0.5.27)
        mv=lambda: pg.evaluate("[$('sn-mv').value, +$('sn-psi').value, +$('sn-L').value, +$('sn-Llt').value]")
        await imp('stahl',0); v=await mv(); check('Verlauf: Einfeldträger → Gleichlast, L = L_LT = 5', v==['q',0,5,5], v)
        await imp('stahl',1); v=await mv(); check('Verlauf: Kragarm → konstant (sichere Seite)', v[0]=='c' and 'Kragarm: C₁' in await pg.inner_text('#ci-msg'), v)
        r=await imp('stahl',2); v=await mv(); t=await pg.inner_text('#ci-msg')
        check('Verlauf: Durchlaufträger (Stützmoment) → konstant, Feld 0…5 m', v[0]=='c' and v[2]==5 and 'Abschnitt 0,00 … 5,00 m' in t and 'als Gleichlast angesetzt' not in t, v)
        await imp('stahl',3,'riegel'); v=await mv(); check('Verlauf: Rahmenriegel mit Eckmomenten → konstant', v[0]=='c', v)
        await imp('stahl',3,'stiel'); v=await mv(); check('Verlauf: Rahmenstiel ohne Querlast → linear mit ψ', v[0]=='lin' and 'keine Querlast' in await pg.inner_text('#ci-msg'), v)
        R=await pg.evaluate("""[ciMomentVerlauf({typ:'cont',L:10,x:[0,5,10],M:[0,-20,10],sup:[{x:0},{x:5},{x:10}],loads:[{k:'q',a:0,b:5,qa:5,qb:5}]}),
                               ciMomentVerlauf({typ:'cont',L:12,x:[0,5,12],M:[0,-20,10],sup:[{x:0},{x:5},{x:12}],loads:[]}),
                               ciMomentVerlauf({typ:'beam',L:4,x:[0,2,4],M:[0,10,0],sup:[{x:0},{x:4}],loads:[{k:'F',a:2,F:20}]}, 'F')]""")
        check('Regel: Feld mit Last und Stützmoment → konstant', R[0]['mv']=='c' and R[0]['a']==0 and R[0]['b']==5, R[0])
        check('Regel: unbelastetes Feld (längeres Nachbarfeld) → linear, ψ = M_klein/M_groß', R[1]['mv']=='lin' and abs(R[1]['psi']-(-0.5))<1e-9 and R[1]['a']==5 and R[1]['b']==12, R[1])
        check('Regel: Feld ohne Endmomente → Verlauf aus den Lasten (Einzellast)', R[2]['mv']=='F', R[2])
        r=await imp('holz',1)
        check('Holz aus Kragarm: keine Seitenansicht, Verlauf konstant', r is None and await pg.input_value('#ho-mv')=='c')
        for L in ('en','fr','es'):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(300)
            await imp('stahl',2); t=await pg.inner_text('#ci-msg')
            g=re.findall(r'\b(Seitenansicht|Lager|Lasten|Momentenlinie|Rahmenecke|Druck|gedrückter|Gurt|Momentenverlauf|Abschnitt|Querlast|Endmomente)\b', t)
            check(f'{L}: Import-Hinweis übersetzt', t.strip() and not g, g[:4])
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
