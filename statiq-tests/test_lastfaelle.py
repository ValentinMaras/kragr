# Lastfälle und Kombinationen nach EC 0 (calc v0.11.4 · size v0.7.6): Lasten den Lastfällen G, Q, S, W1, W2 zuordnen,
# Grundkombination 6.10 je Stelle (Umhüllende), Nutzlast feldweise beim Durchlaufträger, GZG charakteristisch für w.
# Sollwerte von Hand:
#   Einfeldträger L = 5 m, g = 5 kN/m (G), F = 10 kN in der Mitte (Q):
#     max M = 1,35·5·5²/8 + 1,5·10·5/4 = 39,84 kNm; V_A max = 1,35·12,5 + 1,5·5 = 24,38 kN, min = 1,0·12,5 = 12,5 kN
#     w (G + Q) = 5·5·5⁴/(384·EI) + 10·5³/(48·EI) mit EI = 21 000 kNm² → 3,18 mm
#   Zweifeldträger 2 × 5 m, g = 5 (G), q = 4 (Q, Kat. A): Stützmoment −(1,35·5 + 1,5·4)·5²/8 = −39,84 kNm,
#     Feldmoment mit Nutzlast nur im Feld 1: R = 1,35·5·3/8·5 + 1,5·4·7/16·5 = 25,78 kN, max M = R²/(2·12,75) = 26,06 kNm;
#     ohne feldweise Anordnung: R = 12,75·3/8·5 = 23,91 kN, max M = 22,41 kNm.
# Stufen (calc v0.11.5): Test öffnet alle Stufen und Ergebnis-Karten (Standardzustand prüft test_stufen.py)
import os, sys, asyncio, json
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
near=lambda a,b,t=0.01: a is not None and abs(a-b)<=t
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de');localStorage.setItem('statiq-rw-closed','0');localStorage.setItem('statiq-res-fold',JSON.stringify({knoten:false,lfres:false}));localStorage.setItem('statiq-stufen',JSON.stringify({frame:{dims:true,sup:true,loads:true,adv:true},cont:{dims:true,sup:true,loads:true,adv:true},beam:{loads:true,adv:true},cantilever:{loads:true,adv:true}}))"); await pg.reload(); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[!!document.getElementById('lf-on-beam'), document.getElementById('lf-on-beam').checked, !!document.querySelector('#beam-results .k-lfres'), !!lastCalc.beam.lf, document.querySelector('.k-lfcfg[data-lft=beam] .k-lfopt').hidden]")
        check('Voreinstellung: Lastfälle aus, keine Karte, Rechnung wie bisher', r==[True,False,False,False,True], r)
        await pg.evaluate("loads.beam.point[0].values.lf='Q'; document.getElementById('lf-on-beam').checked=true; lfCfg('beam')"); await pg.wait_for_timeout(600)
        lf=await pg.evaluate("lastCalc.beam.lf")
        check('Einfeldträger: max M = 1,35·g·L²/8 + 1,5·F·L/4 = 39,84 kNm (Hand)', near(lf['gov']['maxM']['v'],39.84375,0.002) and lf['gov']['maxM']['formula']=='1,35·G + 1,5·Q', lf['gov']['maxM'])
        rA=lf['reac'][0]
        check('Auflager A: V max = 24,38 kN (1,35·G + 1,5·Q), V min = 12,5 kN (1,0·G)', near(rA['V'][0],24.375) and near(rA['V'][1],12.5), rA)
        check('Durchbiegung charakteristisch G + Q: w = −3,18 mm (Hand)', near(lf['gov']['sls']['v'],-3.1777,0.002) and lf['gov']['sls']['formula']=='G + Q', lf['gov']['sls'])
        check('min M = 0 wird nicht aufgeführt (kein negatives Moment möglich)', lf['gov']['minM'] is None, lf['gov']['minM'])
        r=await pg.evaluate("[document.getElementById('b-res-Mmax').textContent, document.getElementById('b-res-A').textContent, lastCalc.beam.maxima.Mmax]")
        check('Kennwerte oben: M_max = 39,84, V_A der maßgebenden Kombination = 24,38', r[0]=='39.84' and r[1]=='24.38' and near(r[2],39.84375,0.002), r)
        r=await pg.evaluate("[lastCalc.beam.loads.point[0].F, lastCalc.beam.loads.point[0].lf, lastCalc.beam.loads.dist[0].qa, loads.beam.point[0].values.F]")
        check('Gespeichertes Lastbild bleibt charakteristisch (F = 10 kN, Lastfall Q)', r==[10,'Q',5,10], r)
        r=await pg.evaluate("[!!diagData.beam.members[0].alt, document.querySelectorAll('#diag-svg-beam path').length]")
        check('Diagramm: Umhüllende mit zwei Grenzlinien', r[0] and r[1]>=2, r)
        t=await pg.inner_text('#beam-results .k-lfres')
        check('Karte: Lastfälle G und Q, ψ₀ / ψ₁ / ψ₂ = 0,7 / 0,5 / 0,3, Formel Gl. 6.10', 'Nutzlast' in t and '0,7 / 0,5 / 0,3' in t and '6.10' in t, t[:200])
        r=await pg.evaluate("[document.querySelectorAll('.k-lfcfg[data-lft=beam] select option').length, document.querySelector('#beam-point-list .k-row .k-lfsub')!=null || document.querySelectorAll('#tab-beam .k-row [data-key=lf]').length>0]")
        check('Eingabe: sieben Nutzlast-Kategorien, Lastfall-Wahl in jeder Lastzeile', r==[7,True], r)
        r=await pg.evaluate("[...document.querySelectorAll('#tab-beam .k-row .load-sum')].map(e=>e.textContent)")
        check('Lastzeilen zeigen den Lastfall (LF Q, LF G)', any(x.endswith('LF Q') for x in r) and any(x.endswith('LF G') for x in r), r)
        # Ansicht: nur Lastfall Q
        await pg.evaluate("document.querySelector('#beam-results .k-lfchip[data-lfv=\"lf:Q\"]').click()"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[document.getElementById('b-res-A').textContent, lastCalc.beam.lf.view, !!diagData.beam.members[0].alt, lastCalc.beam.lf.viewLabel]")
        check('Ansicht Lastfall Q charakteristisch: V_A = 5,00 kN, einfache Linie', r[0]=='5.00' and r[1]=='lf:Q' and not r[2] and 'Q' in r[3], r)
        # Speichern mit Ansicht Q: Bemessung nimmt trotzdem die Grenzlinien
        await pg.evaluate("saveCalc('beam',{key:'statiq_sdf_lftest', quiet:true})")
        sdf=await pg.evaluate("JSON.parse(localStorage.getItem('statiq_sdf_lftest')).sdf")
        check('SDF: Lastfälle, Grenzlinien (plot.env) und Lastfall je Last gespeichert', sdf.get('lf') and sdf['plot'].get('env') and sdf['system']['loads']['point'][0]['lf']=='Q', list(sdf.keys()))
        await pg.evaluate("document.querySelector('#beam-results .k-lfchip[data-lfv=\"env\"]').click()"); await pg.wait_for_timeout(500)
        await pg.evaluate("saveCalc('beam',{key:'statiq_sdf_lfenv', quiet:true}); showTab('saved'); openReport('statiq_sdf_lfenv')"); await pg.wait_for_timeout(600)
        t=await pg.inner_text('#report-content')
        check('Bericht: Abschnitt Lastfälle, Lasten mit Lastfall, maßgebende Werte mit Kombination', 'LASTFÄLLE UND KOMBINATIONEN' in t.upper() and '· Q' in t and '1,35·G + 1,5·Q' in t and '39,84' in t, t[t.find('EINWIRK'):][:300])
        check('Bericht: Rechenweg mit den Bemessungswerten der angezeigten Kombination (B_V = 24,38 kN)', '= 24,38 kN' in t, '')
        r=await pg.evaluate("document.querySelectorAll('#report-svg-M path').length")
        check('Bericht: Momentenverlauf als Umhüllende (zwei Grenzlinien)', r>=2, r)
        # Durchlaufträger
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(400)
        await pg.evaluate("spanData.forEach((s,k)=>{ s.dist=[{id:900+k,enabled:true,values:{qa:5,qb:5,a:0,b:s.L,lf:'G'}},{id:910+k,enabled:true,values:{qa:4,qb:4,a:0,b:s.L,lf:'Q'}}]; s.point=[]; s.mom=[]; }); document.getElementById('lf-on-cont').checked=true; lfCfg('cont')"); await pg.wait_for_timeout(700)
        G=await pg.evaluate("lastCalc.cont.lf.gov")
        check('Zweifeldträger: Stützmoment −39,84 kNm mit 1,35·G + 1,5·Q', near(G['minM']['v'],-39.84375,0.002) and G['minM']['formula']=='1,35·G + 1,5·Q', G['minM'])
        check('Feldmoment feldweise: 26,06 kNm, Nutzlast nur im Feld 1 bzw. 2 (Hand)', near(G['maxM']['v'],26.064,0.02) and ('(Feld 1)' in G['maxM']['formula'] or '(Feld 2)' in G['maxM']['formula']), G['maxM'])
        await pg.evaluate("document.getElementById('lf-feld-cont').checked=false; lfCfg('cont')"); await pg.wait_for_timeout(600)
        G=await pg.evaluate("lastCalc.cont.lf.gov")
        check('Ohne feldweise Anordnung: Feldmoment nur 22,41 kNm', near(G['maxM']['v'],22.41,0.02) and 'Feld' not in G['maxM']['formula'], G['maxM'])
        await pg.evaluate("document.getElementById('lf-feld-cont').checked=true; lfCfg('cont')"); await pg.wait_for_timeout(500)
        # Kategorie E (ψ₀ = 1,0) ändert die Tabelle
        await pg.evaluate("document.getElementById('lf-cat-cont').value='E'; lfCfg('cont')"); await pg.wait_for_timeout(500)
        t=await pg.inner_text('#cont-results .k-lfres')
        check('Kategorie E Lager: ψ = 1 / 0,9 / 0,8', '1 / 0,9 / 0,8' in t, '')
        # Rahmen mit Schnee und Wind von beiden Seiten
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400)
        await pg.evaluate("frameLoads.vert=[{id:950,enabled:true,values:{member:'rafter',qa:10,qb:10,a:0,b:5,rdir:'v',lf:'G'}},{id:951,enabled:true,values:{member:'rafter',qa:3,qb:3,a:0,b:5,rdir:'v',lf:'S'}},{id:952,enabled:true,values:{member:'left',qa:2,qb:2,a:0,b:4,dir:'h',lf:'W1'}},{id:953,enabled:true,values:{member:'right',qa:-2,qb:-2,a:0,b:4,dir:'h',lf:'W2'}}]; frameLoads.horiz=[]; renderFrameLoads('vert'); renderFrameLoads('horiz'); document.getElementById('lf-on-frame').checked=true; lfCfg('frame')"); await pg.wait_for_timeout(800)
        lf=await pg.evaluate("lastCalc.frame.lf")
        fs=[v['formula'] for v in lf['gov'].values() if v]
        check('Rahmen: Wind 1 und Wind 2 nie gemeinsam in einer Kombination', all(not('W1' in f and 'W2' in f) for f in fs) and any('W' in f for f in fs), fs)
        check('Rahmen: Schnee begleitend mit 1,5·0,5 bzw. leitend mit 1,5', all(('S' not in f) or ('1,5·S' in f) or ('1,5·0,5·S' in f) or ('0,5·S' in f) for f in fs), fs)
        await pg.evaluate("document.querySelector('#frame-results .k-lfchip[data-lfv=\"lf:G\"]').click()"); await pg.wait_for_timeout(500)
        mG=await pg.evaluate("lastCalc.frame.knoten.bars[0].ki.M")
        await pg.evaluate("frameLoads.vert.forEach((l,i)=>{ if(i>0) l.enabled=false; }); document.getElementById('lf-on-frame').checked=false; lfCfg('frame')"); await pg.wait_for_timeout(500)
        m0=await pg.evaluate("lastCalc.frame.knoten.bars[0].ki.M")
        check('Ansicht Lastfall G = Rechnung nur mit den G-Lasten (Eckmoment)', near(mG,m0,0.002), (mG,m0))
        await pg.evaluate("frameLoads.vert.forEach(l=>{ l.enabled=true; }); document.getElementById('lf-on-frame').checked=true; lfCfg('frame')"); await pg.wait_for_timeout(600)
        await pg.evaluate("document.querySelector('#frame-results .k-lfchip[data-lfv=\"env\"]').click()"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[!!diagData.frame.members[1].alt, lastCalc.frame.lf.view, document.querySelectorAll('#diag-svg-frame path').length]")
        check('Rahmen: Umhüllende im Diagramm (Ansicht „Umhüllende“)', r[0] and r[1]=='env', r)
        # Bemessung: Grenzlinien statt der angezeigten Kombination
        pg2=await br.new_page(); pg2.on('pageerror', lambda e: errs.append('size: '+str(e)))
        await pg2.goto(B+'size.html'); await pg2.wait_for_timeout(700)
        r=await pg2.evaluate("(s=>{ const c=calcSchnitt(s); return [c.Mf, c.V]; })("+json.dumps(sdf)+")")
        check('Bemessung übernimmt die Grenzwerte (M = 39,84, V = 24,38) auch bei gespeicherter Ansicht „Q“', near(r[0],39.84,0.01) and near(r[1],24.375,0.01), r)
        await pg2.close()
        # Entwurf: Lastfälle bleiben nach dem Neuladen
        await pg.evaluate("k4Save(true)"); await pg.reload(); await pg.wait_for_timeout(1100); await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[document.getElementById('lf-on-frame').checked, frameLoads.vert.map(l=>l.values.lf), !!lastCalc.frame.lf, !!document.querySelector('#frame-results .k-lfres')]")
        check('Neu laden: Lastfälle eingeschaltet, Zuordnung je Last erhalten, Karte da', r[0] and r[1]==['G','S','W1','W2'] and r[2] and r[3], r)
        # Übungsmodus und Sprache
        await pg.evaluate("setCalcLang('en')"); await pg.wait_for_timeout(300)
        t=await pg.inner_text('#tab-frame')
        check('Englisch: „Load cases“ (unter „Advanced“), „Envelope“', 'Load cases' in t and 'Advanced' in t and 'Envelope' in t, '')
        await pg.evaluate("document.body.classList.add('uebung')")
        r=await pg.evaluate("getComputedStyle(document.querySelector('#frame-results .k-lfres .k-lftab')).display")
        check('Übungsmodus: Tabellen der Karte verborgen', r=='none', r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print(f"\n{'ALLE OK' if not fails else str(fails)+' FEHLER'}"); sys.exit(1 if fails else 0)
