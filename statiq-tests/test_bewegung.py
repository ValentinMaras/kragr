# Bewegung mit Lernwert (calc v0.11.5, auf v0.11.8 mit Stufen, Federn und Lastfällen): gleitende Verläufe, Biegelinie in der Skizze, „Schnitt führen“.
# Sollwerte von Hand:
#   Einfeldträger L = 5 m, q = 5 kN/m, F = 10 kN in Feldmitte: A = B = 17,5 kN; x = 2,5 m: M = 17,5·2,5 − 5·2,5²/2 = 28,13 kNm,
#     Q links = 17,5 − 12,5 = 5,00, rechts −5,00 kN; x = 2,6 m: M = 17,5·2,6 − 5·2,6²/2 − 10·0,1 = 27,60 kNm, Q = 17,5 − 13 − 10 = −5,50 kN.
#   Zweifeldträger 2 × 5 m, q = 10 kN/m: Stützmoment −q·L²/8 = −31,25 kNm, Q links von B = −31,25, rechts +31,25 kN.
#   Rahmen eingespannt h = 4, b = 5, q = 10 (Referenz): Riegelmitte M = 16,37 kNm, N = −5,58 kN (= H); Stützenkopf links M = −14,88, N = −25 kN.
#   Kragarm L = 3 m, F = 10 kN am Ende: Einspannung M = −30 kNm, Q = 10 kN.
#   Zweifeldträger 2 × 5 m, q = 5 kN/m, Setzung Mittellager 10 mm (EI = 21 000 kNm²): M_B = −15,625 + 3·EI·s/L² = 9,575 kNm.
#   Zweifeldträger 2 × 5 m, g = q = 10 kN/m (Q Kat. A, feldweise), Umhüllende: M_B zwischen −2,85·31,25 = −89,06 und −1,0·31,25 = −31,25 kNm.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
async def ro(pg, s): return await pg.evaluate(f"document.querySelector('.k-cutbar[data-sys=\"{s}\"] .k-cutro').textContent")
BEAM="""loads.beam.point=[{id:801,enabled:true,values:{F:10,a:2.5,alpha:0}}]; loads.beam.dist=[{id:802,enabled:true,values:{a:0,b:5,qa:5,qb:5}}]; loads.beam.horiz=[];
  document.getElementById('bL').value=5; ['point','dist','horiz'].forEach(t=>renderLoads('beam',t)); drawBeam(); calculateBeam()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':1000}); pg.on('pageerror', lambda e: errs.append(str(e)))
        # Mit Bewegung (?k5motion schaltet die Bewegung im automatisierten Browser ein)
        await pg.goto(B+'calc.html?k5motion'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
        await pg.evaluate(BEAM); await pg.wait_for_timeout(500)
        await pg.evaluate("loads.beam.point[0].values.F=30; calculateBeam()"); await pg.wait_for_timeout(80)
        r=await pg.evaluate("[kragrMotion.shown.beam.__tw===true, document.querySelectorAll('#diag-svg-beam polyline, #diag-svg-beam polygon, #diag-svg-beam path').length>0]")
        check('A: nach Laständerung ein Zwischenbild (Verlauf gleitet), Diagramm gezeichnet', r==[True,True], r)
        await pg.wait_for_timeout(450)
        r=await pg.evaluate("kragrMotion.shown.beam===diagData.beam")
        check('A: nach 280 ms steht der echte Verlauf', r, r)
        r=await pg.evaluate("(()=>{ const d=document.querySelector('#beam-svg .k-bl').getAttribute('d').split(/[ML ]+/).filter(Boolean).map(Number); return [d[1], d[61], d[121]]; })()")
        check('A: Biegelinie in der Skizze: an den Lagern auf der Achse, Mitte 10 px darunter', r==[74,84,74], r)
        await pg.evaluate(BEAM.replace('F:10','F:10')); await pg.wait_for_timeout(450)
        # Schnitt
        r=await pg.evaluate("['beam','cant','cont','frame'].map(s=>!!document.querySelector('.k-cutbar[data-sys=\"'+s+'\"] .k-cutbtn'))")
        check('B: Knopf „Schnitt führen“ unter jedem Verlauf', r==[True]*4, r)
        await pg.click('.k-cutbar[data-sys="beam"] .k-cutbtn'); await pg.wait_for_timeout(150)
        t=await ro(pg,'beam')
        check('B: Schnitt in Feldmitte: M = 28,13 kNm, Q = 5,00 | −5,00 kN (Lastpunkt, Hand)', 'x = 2,50 m' in t and 'M = 28,13 kNm' in t and 'Q = 5,00 | −5,00 kN' in t and 'links | rechts' in t, t[:120])
        await pg.focus('#diag-svg-beam'); await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(80)
        t=await ro(pg,'beam')
        check('B: Pfeiltaste → x = 2,60 m: M = 27,60 kNm, Q = −5,50 kN (Hand)', 'x = 2,60 m' in t and 'M = 27,60 kNm' in t and 'Q = −5,50 kN' in t, t[:100])
        r=await pg.evaluate("(()=>{ const s=document.getElementById('diag-svg-beam'), m=diagData.beam.members[0], p=s.createSVGPoint(); p.x=m.x0+(m.x1-m.x0)*0.49; p.y=m.y0; const q=p.matrixTransform(s.getScreenCTM()); return [q.x,q.y]; })()")
        await pg.mouse.move(r[0], r[1]); await pg.mouse.down(); await pg.mouse.up(); await pg.wait_for_timeout(80)
        t=await ro(pg,'beam')
        check('B: Tippen kurz neben den Lastpunkt rastet bei x = 2,50 m ein', 'x = 2,50 m' in t, t[:40])
        r=await pg.evaluate("[!!document.querySelector('#diag-svg-beam .k-cut'), document.getElementById('diag-svg-beam').classList.contains('k-cutting')]")
        check('B: Schnittlinie und Freikörper im Verlauf, Ziehen aktiv', r==[True,True], r)
        await pg.evaluate("setDiagMode('beam','Q')"); await pg.wait_for_timeout(80)
        r=await pg.evaluate("!!document.querySelector('#diag-svg-beam .k-cut')")
        check('B: Schnitt bleibt beim Wechsel auf Q stehen', r, r)
        await pg.click('.k-cutbar[data-sys="beam"] .k-cutbtn'); await pg.wait_for_timeout(80)
        r=await pg.evaluate("[!!document.querySelector('#diag-svg-beam .k-cut'), document.querySelector('.k-cutbar[data-sys=beam] .k-cutro').textContent]")
        check('B: Ausschalten entfernt Schnitt und Werte', r==[False,''], r)
        # Kragarm
        await pg.evaluate("""showTab('cantilever'); loads.cant.point=[{id:811,enabled:true,values:{F:10,a:3,alpha:0}}]; loads.cant.dist=[]; loads.cant.horiz=[]; document.getElementById('cL').value=3;
          ['point','dist','horiz'].forEach(t=>renderLoads('cant',t)); drawCantilever(); calculateCantilever(); kragrMotion.cutToggle('cant'); kragrMotion.cut.cant.t=0; kragrMotion.cutDraw('cant')"""); await pg.wait_for_timeout(200)
        t=await ro(pg,'cant')
        check('B: Kragarm an der Einspannung: M = −30,00 kNm, Q = 10,00 kN (Hand)', 'M = −30,00 kNm' in t and 'Q = 10,00 kN' in t, t[:90])
        r=await pg.evaluate("(()=>{ const d=document.querySelector('#cant-svg .k-bl').getAttribute('d').split(/[ML ]+/).filter(Boolean).map(Number); return [d[1], d[121]]; })()")
        check('A: Biegelinie Kragarm: an der Einspannung auf der Achse, am Ende 10 px tiefer', abs(r[1]-r[0]-10)<0.01, r)
        # Durchlaufträger
        await pg.evaluate("""(()=>{ showTab('cont'); const sp=id=>({L:5,k:1,point:[],mom:[],dist:[{id:id,enabled:true,values:{a:0,b:5,qa:10,qb:10}}]});
          spanData=[sp(900),sp(910)]; numSpans=2; contCfg.ovL.L=0; contCfg.ovR.L=0; contCfg.hinges=[]; renderContUI(); calculateContinuous(); kragrMotion.cutToggle('cont'); kragrMotion.cut.cont.t=0.5; kragrMotion.cutDraw('cont'); })()"""); await pg.wait_for_timeout(200)
        t=await ro(pg,'cont')
        check('B: Zweifeldträger über B: M = −31,25 kNm, Q = −31,25 | 31,25 kN (Hand)', 'x = 5,00 m' in t and 'M = −31,25 kNm' in t and 'Q = −31,25 | 31,25 kN' in t, t[:110])
        r=await pg.evaluate("!!document.querySelector('#cont-svg .k-bl')")
        check('A: Biegelinie auch in der Skizze des Durchlaufträgers', r, r)
        # Federn/Setzungen (v0.11.6): Schnitt nimmt das gerechnete Modell
        await pg.evaluate("""(()=>{ const sp=id=>({L:5,k:1,point:[],mom:[],dist:[{id:id,enabled:true,values:{a:0,b:5,qa:5,qb:5}}]});
          spanData=[sp(920),sp(930)]; numSpans=2; renderContUI(); SUPX.cont={on:true, B:{sv:10}}; calculateContinuous(); kragrMotion.cut.cont.t=0.5; kragrMotion.cutDraw('cont'); })()"""); await pg.wait_for_timeout(200)
        t=await ro(pg,'cont')
        check('B: Setzung Mittellager 10 mm: Schnitt über B zeigt M = 9,58 kNm (Hand 9,575)', 'M = 9,58 kNm' in t, t[:80])
        # Lastfälle (v0.11.4 im Zip-Stand): Umhüllende → Spanne
        await pg.evaluate("""(()=>{ SUPX.cont={on:false}; const sp=id=>({L:5,k:1,point:[],mom:[],dist:[{id:id,enabled:true,values:{a:0,b:5,qa:10,qb:10}},{id:id+1,enabled:true,values:{a:0,b:5,qa:10,qb:10,lf:'Q'}}]});
          spanData=[sp(940),sp(950)]; numSpans=2; renderContUI(); document.getElementById('lf-on-cont').checked=true; lfCfg('cont'); calculateContinuous(); kragrMotion.cut.cont.t=0.5; kragrMotion.cutDraw('cont'); })()"""); await pg.wait_for_timeout(300)
        t=await ro(pg,'cont')
        check('B: Lastfälle, Umhüllende: über B M = −89,06 … −31,25 kNm (Hand)', 'M = −89,06 … −31,25 kNm' in t and 'Umhüllende' in t, t[:120])
        await pg.evaluate("document.getElementById('lf-on-cont').checked=false; lfCfg('cont')")
        # Rahmen
        await pg.evaluate("""showTab('frame'); fB.value=5; fH.value=4; if(window.fHA) fHA.value=4; if(window.fHB) fHB.value=4; if(typeof setRoof==='function') setRoof(false); setSupportA('fixed'); setSupportB('fixed'); setHeadSupport('pos','none'); frameHinges=[]; renderFrameHinges();
          frameLoads.vert=[{id:950,enabled:true,values:{member:'rafter',a:0,b:5,qa:10,qb:10}}]; frameLoads.horiz=[]; renderFrameLoads('vert'); renderFrameLoads('horiz'); calculateFrame();
          kragrMotion.cutToggle('frame'); kragrMotion.cut.frame.k=1; kragrMotion.cut.frame.t=0.5; kragrMotion.cutDraw('frame')"""); await pg.wait_for_timeout(200)
        t=await ro(pg,'frame')
        check('B: Rahmen, Riegelmitte: M = 16,37 kNm, N = −5,58 kN (Referenz)', 'Riegel, x = 2,50 m' in t and 'M = 16,37 kNm' in t and 'N = −5,58 kN' in t, t[:100])
        await pg.evaluate("kragrMotion.cut.frame.k=0; kragrMotion.cut.frame.t=1; kragrMotion.cutDraw('frame')")
        t=await ro(pg,'frame')
        check('B: Rahmen, Kopf der linken Stütze: M = −14,88 kNm, N = −25,00 kN', 'Stütze links, z = 4,00 m' in t and 'M = −14,88 kNm' in t and 'N = −25,00 kN' in t, t[:100])
        r=await pg.evaluate("(()=>{ const s=document.getElementById('diag-svg-frame'), m=diagData.frame.members[2], p=s.createSVGPoint(); p.x=m.x0+6; p.y=(m.y0+m.y1)/2; const q=p.matrixTransform(s.getScreenCTM()); return [q.x,q.y]; })()")
        await pg.mouse.click(r[0], r[1]); await pg.wait_for_timeout(80)
        t=await ro(pg,'frame')
        check('B: Tippen neben die rechte Stütze wählt den nächsten Stab', t.startswith('Stütze rechts'), t[:40])
        r=await pg.evaluate("document.querySelectorAll('#diag-svg-frame .k-cut polyline').length")
        check('B: Freikörper am Rahmen: Stütze links und Riegel ganz, Stütze rechts bis zum Schnitt', r==3, r)
        r=await pg.evaluate("(()=>{ document.body.classList.add('uebung'); const d=getComputedStyle(document.querySelector('.k-cutbar[data-sys=frame]')).display; document.body.classList.remove('uebung'); return d; })()")
        check('Übungsmodus: Schnittleiste verborgen', r=='none', r)
        await pg.evaluate("setCalcLang('en')"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.querySelector('.k-cutbar[data-sys=frame] .k-cutbtn').textContent, document.querySelector('.k-cutbar[data-sys=frame] .k-cutro').textContent]")
        check('Englisch: „Cut section“, „Right column“, Dezimalpunkt', r[0]=='Cut section' and r[1].startswith('Right column') and '.' in r[1][:30], r)
        # Ohne Bewegung (Standard im automatisierten Browser): kein Zwischenbild
        pg2=await br.new_page(viewport={'width':1280,'height':1000}); pg2.on('pageerror', lambda e: errs.append(str(e)))
        await pg2.goto(B+'calc.html'); await pg2.wait_for_timeout(900)
        await pg2.evaluate(BEAM); await pg2.wait_for_timeout(200)
        await pg2.evaluate("loads.beam.point[0].values.F=30; calculateBeam()")
        r=await pg2.evaluate("[document.documentElement.classList.contains('k5-still'), kragrMotion.shown.beam===diagData.beam]")
        check('Ohne Bewegung (k5-still / reduzierte Bewegung): Verlauf springt sofort', r==[True,True], r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
    print(f'\n{"ALLE OK" if not fails else str(fails)+" FEHLER"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
