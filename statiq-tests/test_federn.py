# Federn, Setzungen, Temperatur (calc v0.11.6). Sollwerte von Hand (EI = 21 000 kNm², α_T = 1,2·10⁻⁵/K):
#   Einfeldträger L = 5 m, q = 5, F = 10: Lagerfedern c = 5000 kN/m → zusätzliche Durchbiegung 17,5/5000 = 3,5 mm (w = 3,18 + 3,5 = 6,68 mm)
#   Kragarm L = 3 m (M_A = 37,5 kNm): Drehfeder c_φ = 10 000 kNm/rad → φ = 3,75 mrad → Spitze + 3·3,75 = 11,25 mm (w = 3,75 + 11,25 = 15 mm)
#   Zweifeldträger 2 × 5 m, q = 5, Setzung des Mittellagers 10 mm: M_B = −qL²/8 + 3·EI·s/L² = −15,625 + 25,2 = 9,575 kNm
#   Einfeldträger mit ΔT_M = 20 K, h = 30 cm: κ = α·ΔT/h = 8·10⁻⁴ 1/m → w = κL²/8 = 2,5 mm nach unten, M = 0 (statisch bestimmt)
#   Zweifeldträger an beiden Enden waagerecht gehalten, ΔT = 20 K, A = 50 cm²: N = −E·A·α·ΔT = −252 kN
#   Zweigelenkrahmen b = 5, h = 4, ΔT = 30 K im Riegel: Δ = α·ΔT·b = 1,8 mm, δ₁₁ = 2h³/(3EI) + h²b/EI → H = 0,308 kN, M_Ecke = H·h = 1,233 kNm
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
near=lambda a,b,t=0.01: a is not None and abs(a-b)<=t
OPEN="localStorage.setItem('statiq-stufen',JSON.stringify({frame:{dims:true,sup:true,loads:true,adv:true},cont:{dims:true,sup:true,loads:true,adv:true},beam:{loads:true,adv:true},cantilever:{loads:true,adv:true}}))"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de');"+OPEN); await pg.reload(); await pg.wait_for_timeout(1000)
        # Einfeldträger: Federn über die Eingabe
        r=await pg.evaluate("[!!document.querySelector('#tab-beam [data-st=adv] .k-supx'), document.querySelector('#tab-beam .k-supx .sx-body').hidden]")
        check('Einfeldträger: „Federn und Setzungen“ unter Erweitert, zunächst aus', r==[True,True], r)
        await pg.click('#tab-beam .k-supx .sx-on'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('#tab-beam .sx-sup')].map(s=>s.dataset.lab+':'+[...s.querySelectorAll('input')].map(i=>i.dataset.sx).join(','))")
        check('Lager A und B mit Feder c_V und Setzung s (Einfeldträger ohne waagerechte Felder)', r==['A:cv,sv','B:cv,sv'], r)
        for lab in 'AB': await pg.fill(f'#tab-beam .sx-sup[data-lab={lab}] input[data-sx=cv]','5000')
        await pg.wait_for_timeout(700)
        r=await pg.evaluate("[lastCalc.beam.maxima.w, lastCalc.beam.maxima.Mmax, document.getElementById('b-res-A').textContent]")
        check('Federn c = 5000 kN/m: w = 6,68 mm, Schnittgrößen unverändert (statisch bestimmt)', near(r[0],-6.6777,0.002) and near(r[1],28.125) and r[2]=='17.50', r)
        r=await pg.evaluate("[...document.querySelectorAll('#beam-svg .k-sxsvg text')].map(t=>t.textContent)")
        check('Skizze: c = 5000 an beiden Lagern', r.count('c=5000')==2, r)
        r=await pg.evaluate("document.querySelector('#tab-beam [data-st=adv] > .k-head .k-sum').textContent")
        check('Erweitert meldet „Federn/Setzungen“', 'Federn/Setzungen' in r, r)
        # Temperatur
        await pg.evaluate("SUPX.beam={}; loads.beam.point=[]; loads.beam.dist=[]; renderLoads('beam','point'); renderLoads('beam','dist'); addLoad('beam','temp'); liveCalc(true)"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[lastCalc.beam.maxima.w, lastCalc.beam.maxima.Mmax, loads.beam.temp[0].values]")
        check('Temperatur ΔT_M = 20 K: w = 2,5 mm nach unten, M = 0 (Hand)', near(r[0],-2.5,0.002) and near(r[1],0,1e-6), r)
        r=await pg.evaluate("[document.querySelector('#beam-temp-list .load-sum').textContent, [...document.querySelectorAll('#tab-beam .k-chip')].map(c=>c.textContent), [...document.querySelectorAll('#beam-svg .k-sxsvg text')].map(t=>t.textContent)]")
        check('Lastzeile, Chip und Skizze zeigen die Temperatur', r[0]=='ΔTₘ = 20 K · LF T' or r[0].startswith('ΔTₘ = 20 K'), r)
        check('Menü „Last hinzufügen“ bietet „Temperatur“', await pg.evaluate("[...document.querySelectorAll('#tab-beam .k-menu .add-load-btn')].some(b=>b.textContent.includes('Temperatur'))"))
        # Kragarm mit Drehfeder
        await pg.evaluate("showTab('cantilever')"); await pg.wait_for_timeout(300)
        await pg.evaluate("SUPX.cantilever={on:true, A:{cr:10000}}; liveCalc(true)"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[lastCalc.cant.maxima.w, lastCalc.cant.reactions[0].M]")
        check('Kragarm mit Drehfeder c_φ = 10 000 kNm/rad: w = 15 mm (Hand), M_A bleibt 37,5', near(r[0],-15,0.002) and r[1]=='37.50', r)
        # Zweifeldträger: Setzung
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(300)
        await pg.click('#tab-cont .k-supx .sx-on'); await pg.wait_for_timeout(300)
        await pg.fill('#tab-cont .sx-sup[data-lab=B] input[data-sx=sv]','10'); await pg.wait_for_timeout(700)
        r=await pg.evaluate("[lastCalc.cont.supportMoments, document.querySelector('#tab-cont [data-st=sup] > .k-head .k-sum').textContent]")
        check('Zweifeldträger, Setzung Mittellager 10 mm: M_B = 9,575 kNm (Hand), Stufe ② meldet es', near(r[0][0]['M'],9.575,0.002) and 'Federn/Setzungen' in r[1], r)
        r=await pg.evaluate("rwCont().S.join(' ')")
        check('Rechenweg: Hinweis statt Dreimomentengleichung', 'Dreimomentengleichung gilt hier nicht' in r, r[-160:])
        await pg.evaluate("saveCalc('cont',{key:'statiq_sdf_sx', quiet:true}); showTab('saved'); openReport('statiq_sdf_sx')"); await pg.wait_for_timeout(500)
        t=await pg.inner_text('#report-content')
        check('Bericht: „Lager B: s = 10 mm ↓“', 'Lager B: s = 10 mm ↓' in t, '')
        # Temperatur mit Fläche: Normalkraft
        await pg.evaluate("showTab('cont'); SUPX.cont={}; contCfg.supR='pin'; spanData.forEach((s,k)=>{ s.dist=[]; s.temp=[{id:990+k,enabled:true,values:{dTN:20,dTM:0,h:30,alpha:1.2,A:50}}]; }); renderContUI(); liveCalc(true)"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[Math.min(...lastCalc.cont.plot.N), Math.max(...lastCalc.cont.plot.N)]")
        check('Beide Enden waagerecht gehalten, ΔT = 20 K, A = 50 cm²: N = −252 kN (Hand)', near(r[0],-252,0.05) and near(r[1],-252,0.05), r)
        # Rahmen: Temperatur im Riegel
        await pg.evaluate("showTab('frame'); applyFramePreset('two'); frameLoads.vert=[]; frameLoads.horiz=[]; frameLoads.temp=[{id:991,enabled:true,values:{member:'rafter',dTN:30,dTM:0,h:30,alpha:1.2,A:0}}]; renderFrameUI(); liveCalc(true)"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[lastCalc.frame.knoten.bars[0].ki.M, lastCalc.frame.knoten.bars[0].ki.Q]")
        check('Zweigelenkrahmen, ΔT = 30 K im Riegel: H = 0,308 kN, Eckmoment 1,233 kNm (Hand)', near(abs(r[0]),1.2326,0.002) and near(abs(r[1]),0.30815,0.001), r)
        await pg.evaluate("SUPX.frame={on:true, A:{sv:10}}; liveCalc(true)"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[[...document.querySelectorAll('#tab-frame .sx-sup')].map(s=>s.dataset.lab+':'+[...s.querySelectorAll('input')].map(i=>i.dataset.sx).join(',')), JSON.stringify(lastCalc.frame.supx)]")
        check('Rahmen (Festlager): c_V, s, c_H, u je Lager; Stand im Schnappschuss', r[0]==['A:cv,sv,ch,sh','B:cv,sv,ch,sh'] and r[1]=='{"A":{"sv":10}}', r)
        # Lastfälle: Temperatur ist eigener Lastfall T, Setzungen gehören zu G
        await pg.evaluate("frameLoads.vert=[{id:992,enabled:true,values:{member:'rafter',qa:10,qb:10,a:0,b:5,rdir:'v',lf:'G'}}]; frameLoads.temp[0].values.lf='T'; document.getElementById('lf-on-frame').checked=true; lfCfg('frame')"); await pg.wait_for_timeout(800)
        lf=await pg.evaluate("lastCalc.frame.lf")
        cs={c['T']:c for c in lf['cases']}
        check('Lastfälle: T mit ψ = 0,6 / 0,5 / 0, Setzungen beim Lastfall G', 'T' in cs and cs['T']['psi']==[0.6,0.5,0] and 'Setzungen' in cs['G']['loads'], lf['cases'])
        # Speichern im Entwurf
        await pg.evaluate("k4Save(true)"); await pg.reload(); await pg.wait_for_timeout(1100); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[JSON.stringify(SUPX.frame), frameLoads.temp.length, document.querySelector('#tab-frame .k-supx .sx-on').checked]")
        check('Neu laden: Federn/Setzungen und Temperatur bleiben erhalten', r[0]=='{"on":true,"A":{"sv":10}}' and r[1]==1 and r[2], r)
        await pg.evaluate("setCalcLang('en')"); await pg.wait_for_timeout(300)
        t=await pg.inner_text('#tab-frame')
        m=await pg.evaluate("[...document.querySelectorAll('#tab-frame .k-menu .add-load-btn')].map(b=>b.textContent).join('|')")
        check('Englisch: „Springs and settlements“, Menü „＋ Temperature“', 'Springs and settlements' in t and 'Temperature' in m, (t[:0], m))
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print(f"\n{'ALLE OK' if not fails else str(fails)+' FEHLER'}"); sys.exit(1 if fails else 0)
