# calc im Browser: Rahmen-Vorlagen und Theorie-Hilfe (Playwright, sonst SKIP)
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(os.path.join(HERE,'..','calc.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:58}', info)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto('file://'+HTML+'#frame')
        await pg.evaluate("""()=>{ document.getElementById('fB').value=5; document.getElementById('fH').value=4; syncFrameHeights('h');
          frameLoads.vert=[{id:1,enabled:true,values:{member:'rafter',qa:10,qb:10,a:0,b:5}}]; frameLoads.horiz=[]; renderFrameUI(); }""")
        # Dreigelenkrahmen über den Schalter
        await pg.click('#btn-preset-three')
        st = await pg.evaluate("[supportA, supportB, frameHinges.map(h=>h.member+'@'+h.pos).join(','), document.getElementById('frame-indet-info').textContent.trim(), document.getElementById('btn-preset-three').className]")
        check('Schalter Dreigelenkrahmen: Festlager/Festlager + Gelenk Mitte, n = 0', st[:3]==['pin','pin','rafter@2.5'] and 'determinate' in st[3] and 'active' in st[4], str(st))
        await pg.evaluate("calculateFrame()")
        rows = await pg.evaluate("[...document.querySelectorAll('#frame-reactions-body tr')].map(r=>[...r.children].map(c=>c.textContent))")
        H = 10*25/(8*4)
        okR = abs(float(rows[0][1])-H)<0.01 and abs(float(rows[0][2])-25)<0.01 and abs(float(rows[1][1])+H)<0.01
        check(f'Dreigelenkrahmen q=10, b=5, h=4: V = 25 kN, H = ±{H:.2f} kN', okR, str(rows))
        Mk = await pg.evaluate("lastCalc.frame.plot.fine.left.M.slice(-1)[0]")
        check('Eckmoment = −q·b²/8 = −31,25 kNm (Zug außen)', abs(Mk+31.25)<0.01, f'{Mk:.3f}')
        Mg = await pg.evaluate("(()=>{const f=lastCalc.frame.plot.fine.rafter; let m=1e9; f.t.forEach((t,i)=>{ if(Math.abs(t-0.5)<1e-6) m=Math.min(m,Math.abs(f.M[i])); }); return m;})()")
        check('Moment im Gelenk = 0', Mg<1e-6, f'{Mg:.2e}')
        # Zweigelenk / eingespannt
        await pg.click('#btn-preset-two')
        st = await pg.evaluate("[supportA, supportB, frameHinges.length, document.getElementById('frame-indet-info').textContent]")
        check('Schalter Zweigelenkrahmen: kein Gelenk, n = 1', st[:3]==['pin','pin',0] and 'degree 1' in st[3], str(st))
        await pg.click('#btn-preset-fixed')
        st = await pg.evaluate("[supportA, supportB, frameHinges.length, document.getElementById('frame-indet-info').textContent]")
        check('Schalter eingespannt: n = 3', st[:3]==['fixed','fixed',0] and 'degree 3' in st[3], str(st))
        # Hervorhebung bei Eingabe von Hand
        await pg.evaluate("setSupportA('pin'); setSupportB('pin')")
        act = await pg.evaluate("[...document.querySelectorAll('[id^=btn-preset-]')].filter(b=>b.classList.contains('active')).map(b=>b.id)")
        check('Lager von Hand auf Festlager/Festlager → Zweigelenkrahmen hervorgehoben', act==['btn-preset-two'], str(act))
        await pg.evaluate("setSupportA('roller')")
        act = await pg.evaluate("[...document.querySelectorAll('[id^=btn-preset-]')].filter(b=>b.classList.contains('active')).length")
        check('Anderes System → keine Vorlage hervorgehoben', act==0)
        # Hilfe auf Deutsch
        await pg.evaluate("calcLang='de'; applyCalcTranslations(); openModal('frame')")
        txt = await pg.evaluate("document.getElementById('modal-frame').innerText")
        check('Hilfe DE: Dreigelenkrahmen von Hand, Weggrößenverfahren', 'Dreigelenkrahmen von Hand' in txt and 'Weggrößenverfahren' in txt and 'Crown' not in txt)
        lbl = await pg.evaluate("document.getElementById('btn-preset-three').textContent")
        check('Schalter DE beschriftet', lbl=='Dreigelenkrahmen', lbl)
        await pg.evaluate("calcLang='fr'; applyCalcTranslations()")
        txt = await pg.evaluate("document.getElementById('mfs4p').textContent")
        check('Hilfe FR: Absatz auf Französisch (kein Deutsch, kein Englisch)', txt.startswith('calc utilise'), txt[:40])
        # fehlender Schlüssel fällt auf Englisch zurück
        fb = await pg.evaluate("delete calcTranslations.fr.mcSupH; tr('mcSupH')")
        check('Fehlender Schlüssel FR → Englisch', fb.startswith('Superposition (by hand)'), fb)
        check('Keine Laufzeitfehler', not errs, '; '.join(errs)[:120])
        await b.close()
asyncio.run(main())
print('FAILS:',fails)
