# Lastfälle und Kombinationen nach DIN EN 1990/NA (calc v0.11.4): Baukasten „+“ in der System-Karte, Kürzel je Last,
# Karte „Kombinationen“ mit GZT (6.10), charakteristisch, häufig, quasi-ständig; Nutzlast beim Durchlaufträger feldweise.
# Sollwerte unabhängig von Hand (ψ nach Tab. NA.A.1.1):
#   Einfeldträger L = 5 m, g = 5 kN/m (G), F = 10 kN in Feldmitte (Q, Kat. A: ψ 0,7/0,5/0,3):
#     M_G = 5·25/8 = 15,625, M_Q = 10·5/4 = 12,5 kNm → GZT 1,35·15,625 + 1,5·12,5 = 39,84; char 28,13; häufig 15,625 + 0,5·12,5 = 21,88;
#     quasi-ständig 15,625 + 0,3·12,5 = 19,38 kNm; V_A,max = 1,35·12,5 + 1,5·5 = 24,38, V_A,min = 12,50 kN.
#   dazu Schnee s = 2 kN/m (bis 1000 m: ψ 0,5/0,2/0): M_S = 6,25 kNm → Q führend 21,094 + 18,75 + 1,5·0,5·6,25 = 44,53 kNm
#     (S führend nur 21,094 + 1,05·12,5 + 9,375 = 43,59); char 15,625 + 12,5 + 0,5·6,25 = 31,25 kNm.
#   Wind als Sog w = −8 kN/m: M_W = −25 kNm → GZT min 1,0·15,625 + 1,5·(−25) = −21,88 kNm (G günstig), max 1,35·15,625 = 21,09 kNm.
#   Zweifeldträger 2 × 5 m, g = 10, q = 10 kN/m je Feld (Kat. A): M_B = −2,85·31,25 = −89,06 kNm; Feld 1 max mit Q nur in Feld 1:
#     A = 1,35·18,75 + 1,5·21,875 = 58,125 kN, q_d = 28,5 kN/m → x = 2,04 m, M = 58,125²/(2·28,5) = 59,27 kNm; V_A,min = 18,75 − 1,5·3,125 = 14,06 kN;
#     V_B,max = 2,85·62,5 = 178,13 kN.
#   Rahmen eingespannt h = 4, b = 5, q = 10 als G (Referenz Ecke −14,88, Feld 16,37) → GZT ×1,35: −20,09 / 22,10 kNm.
import os, sys, asyncio, json
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
near=lambda a,b,t=0.01: abs(a-b)<=t
def ext(sys_, mode, key): return f"lfDebug.data['{sys_}'].E['{mode}'].ext['{key}'].v"
BEAM="""loads.beam.point=[{id:801,enabled:true,values:{F:10,a:2.5,alpha:0%s}}];
  loads.beam.dist=[{id:802,enabled:true,values:{a:0,b:5,qa:5,qb:5}}%s]; loads.beam.horiz=[];
  document.getElementById('bL').value=5; ['point','dist','horiz'].forEach(t=>renderLoads('beam',t)); drawBeam(); liveCalc(true)"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':1000}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        r=await pg.evaluate("['beam','cantilever','cont','frame'].map(t=>document.querySelectorAll('#tab-'+t+' .card-title-row .k-plus').length)")
        check('Baukasten: ein „+“ in der System-Karte aller vier Systeme', r==[1,1,1,1], r)
        await pg.evaluate(BEAM % ('','')); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.querySelectorAll('#tab-beam .k-lft').length, document.querySelectorAll('#beam-results .k-lfc').length, document.getElementById('b-res-Mmax').textContent]")
        check('Aus (Standard): keine Kürzel, keine Kombinationskarte, Rechnung wie bisher (M_max 28,13)', r==[0,0,'28.13'], r)
        await pg.click('#tab-beam .k-plus'); await pg.wait_for_timeout(150)
        r=await pg.evaluate("[!document.querySelector('.k-plusm[data-lfsys=beam]').hidden, document.querySelectorAll('.k-plusm[data-lfsys=beam] .k-pm-it').length, document.querySelectorAll('.k-plusm[data-lfsys=beam] .k-pm-it:disabled').length]")
        check('„+“ öffnet die Erweiterungen: Lastfälle (Schalter), Federn/Setzungen und Temperatur als „bald“', r==[True,3,2], r)
        await pg.click('.k-plusm[data-lfsys=beam] [data-lfsw]'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.getElementById('lfOn-beam').checked, [...document.querySelectorAll('#tab-beam .k-lft')].map(e=>e.textContent), document.querySelectorAll('#beam-results .k-lfc').length, document.querySelector('.k-plusm[data-lfsys=beam]').hidden]")
        check('Einschalten: alle Lasten tragen „G“, Karte „Kombinationen“ erscheint, Menü schließt', r==[True,['G ▾','G ▾'],1,True], r)
        v=await pg.evaluate(ext('beam','gzt','Mmax'))
        check('nur G: M_Ed = 1,35·28,125 = 37,97 kNm', near(v,37.969), v)
        # F1 als Nutzlast Kat. A über das Kürzel
        await pg.locator('#tab-beam .k-row[data-type="point"] .k-lft').first.click(); await pg.wait_for_timeout(150)
        n=await pg.locator('#tab-beam .k-row[data-type="point"] .k-lfo').count()
        check('Kürzel öffnet die Auswahl: G, Q Kat. A–H, Schnee (2), Wind = 12 Einwirkungen', n==12, n)
        await pg.locator('#tab-beam .k-row[data-type="point"] .k-lfo[data-lfa="Q:A"]').click(); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[loads.beam.point[0].values.act, document.querySelector('#tab-beam .k-row[data-type=point] .k-lft').textContent, document.querySelectorAll('#tab-beam .k-row.open').length]")
        check('Auswahl Q Kat. A: gespeichert in values.act, Kürzel „Q A“, Zeile bleibt zu', r==['Q:A','Q A ▾',0], r)
        r=await pg.evaluate("['gzt','char','freq','qp'].map(m=>lfDebug.data.beam.E[m].ext.Mmax.v)")
        check('M: GZT 39,84 · char 28,13 · häufig 21,88 · quasi-ständig 19,38 kNm (Hand)', all(near(a,b) for a,b in zip(r,[39.84375,28.125,21.875,19.375])), r)
        r=await pg.evaluate("lfDebug.data.beam.E.gzt.reac.map(x=>[x.lab.join(''), +x.max.v.toFixed(3), +x.min.v.toFixed(3)])")
        check('Auflager A: V_max = 1,35·12,5 + 1,5·5 = 24,38, V_min = 1,0·12,5 = 12,50 kN', ['VA',24.375,12.5] in r, r)
        t=await pg.inner_text('#beam-results .k-lfc')
        check('Karte: maßgebende Kombination „1,35·G + 1,5·Q“ und Stelle x = 2,5 m', '1,35·G + 1,5·Q' in t and 'x = 2,5 m' in t, t[:200])
        check('Rechenweg: M_G = 15,63, M_Q = 12,50 → 1,35·15,63 + 1,5·12,50 = 39,84 kNm', '1,35·15,63 + 1,5·12,50 = 39,84 kNm' in t.replace('\n',' '), t[-260:])
        check('Hinweis: Kennwerte oben mit Faktor 1,0, H_A = 0 nicht in der Tabelle', 'Faktor 1,0' in t and 'HA' not in t.replace('\n',''), '')
        await pg.click('#beam-results .k-lfc [data-lfm="qp"]'); await pg.wait_for_timeout(150)
        t=await pg.inner_text('#beam-results .k-lfc [data-lfk="Mmax"]')
        check('Umschalter quasi-ständig: 19,38 kNm mit „1,0·G + 0,3·Q“', '19,38' in t and '1,0·G + 0,3·Q' in t, t.replace('\n',' | '))
        await pg.click('#beam-results .k-lfc [data-lfm="gzt"]')
        # Schnee dazu
        await pg.evaluate(BEAM % (",act:'Q:A'", ",{id:803,enabled:true,values:{a:0,b:5,qa:2,qb:2,act:'S'}}")); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[lfDebug.data.beam.E.gzt.ext.Mmax.v, lfDebug.data.beam.E.char.ext.Mmax.v, lfDebug.data.beam.E.qp.ext.Mmax.v]")
        check('mit Schnee: GZT 44,53 (Q führend), char 31,25, quasi-ständig 19,38 kNm (Hand)', near(r[0],21.09375+18.75+4.6875) and near(r[1],31.25) and near(r[2],19.375), r)
        t=await pg.inner_text('#beam-results .k-lfc [data-lfk="Mmax"]')
        check('Bezeichnung „1,35·G + 1,5·Q + 0,75·S“', '1,35·G + 1,5·Q + 0,75·S' in t, t.replace('\n',' | '))
        # Windsog: G günstig
        await pg.evaluate(BEAM % (",act:'Q:A'", ",{id:804,enabled:true,values:{a:0,b:5,qa:-8,qb:-8,act:'W'}}")); await pg.evaluate("loads.beam.point=[]; renderLoads('beam','point'); liveCalc(true)"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[lfDebug.data.beam.E.gzt.ext.Mmin.v, lfDebug.data.beam.E.gzt.ext.Mmax.v, lfDebug.data.beam.E.gzt.ext.Mmin.gG]")
        check('Windsog: M_min = 1,0·15,63 + 1,5·(−25) = −21,88 (G günstig), M_max = 21,09 kNm', near(r[0],-21.875) and near(r[1],21.09375) and r[2]==1.0, r)
        # Speichern, Neuladen, Bericht
        await pg.evaluate(BEAM % (",act:'Q:A'", "")); await pg.wait_for_timeout(300)
        await pg.evaluate("k4Save(true)")
        await pg.reload(); await pg.wait_for_timeout(1000)
        r=await pg.evaluate("[document.getElementById('lfOn-beam').checked, loads.beam.point[0].values.act, [...document.querySelectorAll('#tab-beam .k-lft')].map(e=>e.textContent), document.querySelectorAll('#beam-results .k-lfc').length]")
        check('Neu laden: Schalter, Einwirkungen und Karte bleiben (Entwurf)', r==[True,'Q:A',['Q A ▾','G ▾'],1], r)
        r=await pg.evaluate("(()=>{ saveCalc('beam',{key:'statiq_sdf_lftest',quiet:true}); const d=JSON.parse(localStorage.getItem('statiq_sdf_lftest')); return [d.sdf.results.combo.modes.gzt.ext.Mmax.v, d.sdf.results.combo.modes.gzt.ext.Mmax.comb, d.sdf.system.loads.point[0].act]; })()")
        check('Speichern: sdf.results.combo (GZT 39,84 mit Kombination), act im Lastschnappschuss', near(r[0],39.84375) and r[1]=='1,35·G + 1,5·Q' and r[2]=='Q:A', r)
        await pg.evaluate("openReport('statiq_sdf_lftest')"); await pg.wait_for_timeout(600)
        t=await pg.inner_text('#report-content')
        check('Bericht: Abschnitt „Kombinationen (DIN EN 1990/NA)“, Lastzeile mit [Q A], 39,84 kNm', 'Kombinationen (DIN EN 1990/NA)' in t and '[Q A]' in t and '39,84' in t, t[:120])
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(900)
        # Durchlaufträger, Nutzlast feldweise
        await pg.evaluate("""(()=>{ showTab('cont'); const sp=id=>({L:5,k:1,point:[],mom:[],dist:[{id:id,enabled:true,values:{a:0,b:5,qa:10,qb:10}},{id:id+1,enabled:true,values:{a:0,b:5,qa:10,qb:10,act:'Q:A'}}]});
          spanData=[sp(900),sp(910)]; numSpans=2; contCfg.ovL.L=0; contCfg.ovR.L=0; contCfg.hinges=[]; renderContUI(); lfSetOn('cont', true); })()"""); await pg.wait_for_timeout(400)
        r=await pg.evaluate("(()=>{ const e=lfDebug.data.cont.E.gzt.ext, C=lfDebug.data.cont.C; return [e.Mmax.v, e.Mmax.t*C.len.beam, e.Mmin.v, e.Mmin.t*C.len.beam]; })()")
        check('DLT: Feld max M = 59,27 kNm bei x = 2,04 m (Q nur in Feld 1), M_B = −89,06 kNm (Hand)', near(r[0],58.125**2/57) and near(r[1],58.125/28.5,0.005) and near(r[2],-89.0625) and near(r[3],5,1e-6), r)
        t=await pg.inner_text('#cont-results .k-lfc')
        check('DLT: Bezeichnung „1,35·G + 1,5·Q (Feld 1)“, Hinweis „feldweise“', '1,35·G + 1,5·Q (Feld 1)' in t and 'feldweise' in t, '')
        r=await pg.evaluate("lfDebug.data.cont.E.gzt.reac.map(x=>[x.lab.join(''), +x.max.v.toFixed(3), +x.min.v.toFixed(3)])")
        check('DLT: V_A,min = 14,06 (Q nur in Feld 2), V_B,max = 178,13 kN', r[0][0]=='VA' and near(r[0][2],14.0625) and r[1][0]=='VB' and near(r[1][1],178.125), r)
        r=await pg.evaluate("[...document.querySelectorAll('#tab-cont .k-lft')].map(e=>e.textContent)")
        check('DLT: Kürzel an allen Lasten der Felder', r.count('G ▾')==2 and r.count('Q A ▾')==2, r)
        # Rahmen: nur G → 1,35 × Referenz
        await pg.evaluate("""(()=>{ showTab('frame'); fB.value=5; fH.value=4; if(window.fHA) fHA.value=4; if(window.fHB) fHB.value=4; if(typeof setRoof==='function') setRoof(false);
          setSupportA('fixed'); setSupportB('fixed'); setHeadSupport('pos','none'); frameHinges=[]; renderFrameHinges();
          frameLoads.vert=[{id:950,enabled:true,values:{member:'rafter',a:0,b:5,qa:10,qb:10}}]; frameLoads.horiz=[]; renderFrameLoads('vert'); renderFrameLoads('horiz'); lfSetOn('frame', true); })()"""); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[lfDebug.data.frame.E.gzt.ext.Mmax.v, lfDebug.data.frame.E.gzt.ext.Mmin.v, lfDebug.data.frame.E.char.ext.Mmax.v]")
        check('Rahmen nur G: GZT 1,35·16,37 = 22,10 und 1,35·(−14,88) = −20,09, char 16,37 kNm', near(r[0],22.10,0.02) and near(r[1],-20.09,0.02) and near(r[2],16.37,0.01), r)
        # Übungsmodus, Ausschalten, Sprache
        r=await pg.evaluate("(()=>{ document.body.classList.add('uebung'); const d=getComputedStyle(document.querySelector('#frame-results .k-lfc')).display; document.body.classList.remove('uebung'); return d; })()")
        check('Übungsmodus: Kombinationskarte verborgen', r=='none', r)
        await pg.evaluate("lfSetOn('frame', false)"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.querySelectorAll('#frame-results .k-lfc').length, document.querySelectorAll('#tab-frame .k-lft').length, !!lastCalc.frame.combo]")
        check('Ausschalten: Karte und Kürzel weg, keine Kombinationen im Speicherstand', r==[0,0,False], r)
        await pg.evaluate("lfSetOn('frame', true); setCalcLang('en')"); await pg.wait_for_timeout(500)
        t=await pg.inner_text('#frame-results .k-lfc'); tp=await pg.evaluate("document.querySelector('#tab-frame .k-plus').getAttribute('aria-label')")
        check('Englisch: „Combinations“, „ULS“, „Extend the system“', 'Combinations' in t and 'ULS' in t and tp=='Extend the system', (t[:60], tp))
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
    print(f'\n{"ALLE OK" if not fails else str(fails)+" FEHLER"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
