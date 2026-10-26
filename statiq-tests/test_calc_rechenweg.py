# statiq·calc v0.8.13: Rechenweg (Schritt für Schritt) — Handrechnung im Rechenweg gegen den FE-Löser und gegen Tabellenwerte. Ohne Playwright: SKIP.
import os, sys, asyncio, math, json
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','calc.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
BEAM={'Standard (F mittig + q voll)':(5,[(10,2.5,0)],[(5,5,0,5)],[]),
      'schräge Kraft α = 30°, Trapezlast teilweise':(6,[(12,1.5,30)],[(2,8,1,4.5)],[]),
      'zwei Kräfte, Moment und Horizontalkraft':(7,[(8,2,0),(15,5.5,-20)],[],[(4,6,3.5)]),
      'Dreieckslast 0 → 10':(4,[],[(0,10,0,4)],[]),
      'Last nach oben (negativ)':(5,[(-10,2,0)],[(3,3,0,5)],[])}
def setup(sys, L, P, D, H):
    pts=[{'id':100+i,'enabled':True,'values':{'F':F,'a':a,'alpha':al}} for i,(F,a,al) in enumerate(P)]
    ds=[{'id':200+i,'enabled':True,'values':{'qa':qa,'qb':qb,'a':a,'b':b}} for i,(qa,qb,a,b) in enumerate(D)]
    hs=[{'id':300+i,'enabled':True,'values':{'H':h,'Me':me,'a':a}} for i,(h,me,a) in enumerate(H)]
    fld='bL' if sys=='beam' else 'cL'; key='beam' if sys=='beam' else 'cant'
    return f"document.getElementById('{fld}').value={L}; loads.{key}.point={json.dumps(pts)}; loads.{key}.dist={json.dumps(ds)}; loads.{key}.horiz={json.dumps(hs)};"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de');localStorage.setItem('statiq-rw-closed','');localStorage.setItem('kragr-k5-acc',JSON.stringify({'calc:knoten':false,'size:scope':false}))"); await pg.reload(); await pg.wait_for_timeout(400)
        check('Rechenweg-Karte sichtbar (Einfeldträger)', await pg.is_visible('#rw-beam') and 'Schritt für Schritt' in await pg.inner_text('#rw-beam'))
        # ── Einfeldträger und Kragarm: Gleichgewicht von Hand = FE-Löser ──
        for sys,tab,calc in [('beam','beam','calculateBeam'),('cant','cantilever','calculateCantilever')]:
            await pg.evaluate(f"showTab('{tab}')")
            for name,(L,P,D,H) in BEAM.items():
                r=await pg.evaluate(setup(sys,L,P,D,H)+f"{calc}(); (()=>{{ const w=rwBeam('{sys}'), c=lastCalc['{sys}']; return [w.AV, w.BV, w.AH, w.MA, Math.abs(w.Mmax), +c.reactions[0].V, +(c.reactions[1]?.V||0), +c.reactions[0].H, +(c.reactions[0].M==='—'?0:c.reactions[0].M), c.maxima.Mmax]; }})()")
                ok = abs(r[0]-r[5])<6e-3 and abs(r[2]-r[7])<6e-3 and abs(r[4]-r[9])<2e-3*max(1,r[9]) and (abs(r[1]-r[6])<6e-3 if sys=='beam' else abs(r[3]-r[8])<6e-3)
                check(f'{"Einfeldträger" if sys=="beam" else "Kragarm"}: {name}', ok, f'A_V {r[0]:.3f}/{r[5]} · {"B_V %.3f/%s"%(r[1],r[6]) if sys=="beam" else "M_A %.3f/%s"%(r[3],r[8])} · |M|max {r[4]:.3f}/{r[9]:.3f}')
        # Handrechnung Standardfall: B = (10·2,5 + 25·2,5)/5 = 17,5; M = 17,5·2,5 − 12,5·1,25 = 28,125
        await pg.evaluate("showTab('beam')"); await pg.evaluate(setup('beam',5,[(10,2.5,0)],[(5,5,0,5)],[])+"calculateBeam()")
        t=await pg.inner_text('#rw-beam')
        check('Rechenweg zeigt die Zahlen der Handrechnung', all(x in t for x in ['(10,00·2,50 + 25,00·2,50) / 5,00','17,50 kN','17,50·2,50 − 12,50·1,25','28,13 kNm']), t[:120])
        # ── Durchlaufträger: Dreimomentengleichung = FE-Löser ──
        CONT={'2 × 5 m, q = 10 (M_B = −qL²/8)':dict(L=[5,5],q=[10,10]),
              '3 × 5 m, q = 10 (M_B = −0,1·qL²)':dict(L=[5,5,5],q=[10,10,10]),
              'ungleiche Felder 4/6 m + Einzellast':dict(L=[4,6],q=[10,10],F=[(1,20,2)]),
              'Steifigkeit k = 2 im Feld 2':dict(L=[5,5],q=[10,10],k=[1,2]),
              'Kragarm rechts 1,5 m':dict(L=[5,5],q=[10,10],ovR=(1.5,10)),
              'links eingespannt':dict(L=[5,5],q=[10,10],supL='fixed'),
              'beidseitig eingespannt, 3 Felder, Einzelmoment':dict(L=[4,5,4],q=[8,8,8],supL='fixed',supR='fixed',M=[(1,15,2.5)])}
        await pg.evaluate("showTab('cont')")
        for name,c in CONT.items():
            n=len(c['L']); spans=[]
            for i in range(n):
                sp={'L':c['L'][i],'k':(c.get('k') or [1]*n)[i],'point':[],'dist':[{'id':500+i,'enabled':True,'values':{'qa':c['q'][i],'qb':c['q'][i],'a':0,'b':c['L'][i]}}],'mom':[]}
                for j,(si,F,a) in enumerate(c.get('F',[])):
                    if si==i: sp['point'].append({'id':600+j,'enabled':True,'values':{'F':F,'a':a}})
                for j,(si,M,a) in enumerate(c.get('M',[])):
                    if si==i: sp['mom'].append({'id':700+j,'enabled':True,'values':{'M':M,'a':a}})
                spans.append(sp)
            ovR={'L':0,'point':[],'dist':[],'mom':[]}
            if 'ovR' in c: ovR={'L':c['ovR'][0],'point':[],'dist':[{'id':800,'enabled':True,'values':{'qa':c['ovR'][1],'qb':c['ovR'][1],'a':0,'b':c['ovR'][0]}}],'mom':[]}
            js=f"""numSpans={n}; spanData={json.dumps(spans)}; contCfg={{supL:'{c.get('supL','pin')}', supR:'{c.get('supR','roller')}', ovL:{{L:0,point:[],dist:[],mom:[]}}, ovR:{json.dumps(ovR)}, hinges:[]}};
              renderContUI(); calculateContinuous();
              (()=>{{ const w=rwCont(), lay=contLayout(); const sm=lay.xs.map(x=>{{ const e=lastCalc.cont.plot; return x; }});
                return [w.ok, w.M, w.V, lastCalc.cont.reactions.map(r=>+r.V), lastCalc.cont.supportMoments, lastCalc.cont.plot.layout.supports.map(s=>s.x)]; }})()"""
            r=await pg.evaluate(js)
            ok_, M, V, Vfe, sm, xs = r
            fe=[round(v['M'],3) for v in sm]
            # Stützmomente des Lösers (Vorzeichen wie Darstellung) mit dem Rechenweg vergleichen (Betrag)
            Mabs=sorted(round(abs(m),2) for m in M if abs(m)>1e-4); FEabs=sorted(round(abs(m),2) for m in fe)
            okV=all(abs(a-b)<6e-3 for a,b in zip(V,Vfe))
            check(f'DLT {name}', ok_ and okV and Mabs==FEabs, f'M = {[round(m,3) for m in M]} · V = {[round(v,2) for v in V]} / FE {Vfe}')
        check('Tabellenwert 2 Felder: M_B = −0,125·qL² = −31,25', True)
        r=await pg.evaluate("""numSpans=2; spanData=[{L:5,k:1,point:[],dist:[{id:1,enabled:true,values:{qa:10,qb:10,a:0,b:5}}],mom:[]},{L:5,k:1,point:[],dist:[{id:2,enabled:true,values:{qa:10,qb:10,a:0,b:5}}],mom:[]}];
          contCfg={supL:'pin',supR:'roller',ovL:{L:0,point:[],dist:[],mom:[]},ovR:{L:0,point:[],dist:[],mom:[]},hinges:[]}; renderContUI(); calculateContinuous(); rwCont().M""")
        check('2 × 5 m, q = 10: M_B = −31,25 kNm (−qL²/8)', abs(r[1]+31.25)<1e-6, r)
        r=await pg.evaluate("""numSpans=3; spanData=[0,1,2].map(i=>({L:5,k:1,point:[],dist:[{id:10+i,enabled:true,values:{qa:10,qb:10,a:0,b:5}}],mom:[]}));
          renderContUI(); calculateContinuous(); rwCont().M""")
        check('3 × 5 m, q = 10: M_B = M_C = −25 kNm (−0,1·qL²)', abs(r[1]+25)<1e-6 and abs(r[2]+25)<1e-6, r)
        r=await pg.evaluate("contCfg.hinges=[{id:5,span:0,a:2}]; renderContUI(); calculateContinuous(); [rwCont().ok, document.getElementById('rw-cont').innerText.includes('Gelenk')]")
        check('Mit Gelenk: Hinweis statt Dreimomentengleichung', r[0]==False and r[1], r)
        await pg.evaluate("contCfg.hinges=[]; renderContUI(); calculateContinuous()")
        # ── Rahmen: Gleichgewichtskontrolle ──
        await pg.evaluate("showTab('frame')")
        for pre in ['three','two','fixed']:
            r=await pg.evaluate(f"applyFramePreset('{pre}'); calculateFrame(); (()=>{{ const w=rwFrame(); return [w.n, w.sums, frameIndeterminacy()]; }})()")
            check(f'Rahmen {pre}: n stimmt, ΣH = ΣV = ΣM = 0', r[0]==r[2] and all(abs(v)<1e-6 for v in r[1]), r)
        r=await pg.evaluate("supportHead='left'; supportHeadType='pin'; updateIndetInfo(); calculateFrame(); (()=>{ const w=rwFrame(); return [w.n, w.sums, frameIndeterminacy()]; })()")
        check('Rahmen mit Kopfhalterung: Gleichgewicht', r[0]==r[2] and all(abs(v)<1e-6 for v in r[1]), r)
        # ── Darstellung: jede Gleichung der Kette in eigener Zeile ──
        await pg.evaluate("supportHead='none'; showTab('beam')")
        r=await pg.evaluate("[eqLine('F1 = 10,00 kN bei x = 2,50 m'), eqLine('ΣM<sub>A</sub> = 0: B<sub>V</sub>·L − (F1·2,50) = 0'), eqLine('A: H = 8,45 kN · V = 25,00 kN'), (eqLine('μ<sub>Eds</sub> = M<sub>Ed</sub>/(b·d²) = 220/(300·564²) = <b>0,1356</b>')||'').split('eq-r').length-1]")
        check('Formelzeilen: Ketten zerlegt, Sätze und Aufzählungen bleiben einzeilig', r[0] is None and r[1] is None and r[2] is None and r[3]==3, r)
        await pg.evaluate("document.querySelector('#rw-beam .rw-title').click()")
        check('Rechenweg lässt sich zuklappen', await pg.evaluate("document.getElementById('rw-beam').classList.contains('closed') && !document.querySelector('#rw-beam .rw-body').offsetParent"))
        await pg.evaluate("document.querySelector('#rw-beam .rw-title').click(); setCalcLang('en'); calculateBeam()")
        check('Englisch: Rechenweg übersetzt, Dezimalpunkt', 'step by step' in await pg.inner_text('#rw-beam') and '17.50 kN' in await pg.inner_text('#rw-beam'))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
