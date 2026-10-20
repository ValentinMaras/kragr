# Bericht (v0.8.2): Speichern → Bericht öffnen für alle vier Systeme, im echten Browser.
# Braucht Playwright (pip install playwright; playwright install chromium). Ohne: SKIP.
import os, sys, asyncio, json
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(os.path.join(HERE,'..','calc.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)

SETUP = {
 'beam': """()=>{ showTab('beam'); document.getElementById('bL').value=5;
   loads.beam.point=[{id:1,enabled:true,values:{F:20,a:1.73,alpha:0}}];
   loads.beam.dist=[{id:2,enabled:true,values:{qa:5,qb:5,a:0,b:5}}]; loads.beam.horiz=[]; calculateBeam(); }""",
 'cantilever': """()=>{ showTab('cantilever'); document.getElementById('cL').value=3;
   loads.cant.point=[{id:3,enabled:true,values:{F:10,a:1.5,alpha:0}}];
   loads.cant.dist=[{id:4,enabled:true,values:{qa:5,qb:5,a:0,b:3}}]; loads.cant.horiz=[]; calculateCantilever(); }""",
 'cont': """()=>{ showTab('cont'); numSpans=2;
   spanData=[{L:4,point:[],dist:[{id:5,enabled:true,values:{qa:10,qb:10,a:0,b:4}}]},
             {L:6,point:[{id:7,enabled:true,values:{F:20,a:2}}],dist:[{id:6,enabled:true,values:{qa:10,qb:10,a:0,b:6}}]}];
   renderContUI(); calculateContinuous(); }""",
 'frame': """()=>{ showTab('frame'); setSupportA('fixed'); setSupportB('pin'); frameHinges=[{id:9,member:'rafter',pos:2}];
   frameLoads.vert=[{id:11,enabled:true,values:{member:'rafter',qa:10,qb:10,a:0,b:5}},{id:12,enabled:true,values:{member:'left',qa:3,qb:3,a:0,b:4,dir:'h'}}];
   frameLoads.horiz=[{id:13,enabled:true,values:{member:'rafter',F:20,H:0,z:1.7}}]; renderFrameUI(); calculateFrame(); }"""}
SAVE = {'beam':"saveCalc('beam')", 'cantilever':"saveCalc('cantilever')", 'cont':"saveCalc('cont')", 'frame':"saveFrameCalc()"}
# nach dem Berechnen etwas ändern — darf NICHT gespeichert werden
CHANGE = {'beam':"document.getElementById('bL').value=9; loads.beam.point[0].values.F=99",
          'cantilever':"document.getElementById('cL').value=9",
          'cont':"spanData[0].L=9",
          'frame':"document.getElementById('fB').value=9; frameLoads.horiz[0].values.F=99"}
EXPECT = {'beam':['Einfeldträger','L = 5 m','A: Festlager, B: Loslager','F1 = 20 kN, x = 1,73 m','q1 = 5 kN/m'],
          'cantilever':['Kragarm','L = 3 m','Einspannung','F1 = 10 kN'],
          'cont':['Durchlaufträger','L<sub>1</sub> = 4 m, L<sub>2</sub> = 6 m','Feld 2: F1 = 20 kN','Stützmomente'],
          'frame':['Rahmen','b = 5 m','A: Einspannung, B: Festlager','Gelenk 1: Riegel, x = 2 m','P1: F = 20 kN','Linker Stiel','horizontal']}
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:52}', info)

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto('file://'+HTML)
        await pg.evaluate("setCalcLang('de')")   # Inhalte werden auf Deutsch geprüft
        for sysn in ['beam','cantilever','cont','frame']:
            errs.clear()
            await pg.evaluate("localStorage.clear()")
            await pg.evaluate(SETUP[sysn])
            sid = 'cant' if sysn=='cantilever' else sysn
            w_calc = await pg.evaluate(f"lastCalc['{sid}'].maxima")
            APPF = {'beam':[('b-res-HA','H',0),('b-res-A','V',0),('b-res-B','V',1)],
                    'cantilever':[('c-res-HA','H',0),('c-res-V','V',0),('c-res-M','M',0)]}.get(sysn, [])
            app_vals = await pg.evaluate("ids=>ids.map(i=>document.getElementById(i).textContent)", [a for a,_,_ in APPF])
            await pg.evaluate(CHANGE[sysn]); await pg.evaluate(SAVE[sysn])
            r = await pg.evaluate("""()=>{ let k=null; for(let i=0;i<localStorage.length;i++){const x=localStorage.key(i); if(x.startsWith('statiq_sdf_')) k=x;}
              showTab('saved'); renderSavedTab(); openReport(k);
              const html=document.getElementById('report-content').innerHTML;
              const sdf=JSON.parse(localStorage.getItem(k)).sdf;
              return {html, sdf, toasts:document.querySelectorAll('.toast').length}; }""")
            await pg.wait_for_timeout(100)
            dia = await pg.evaluate("""()=>['M','Q','N','w'].map(k=>{const s=document.getElementById('report-svg-'+k); return s?[k, s.innerHTML.length, (s.innerHTML.match(/<line/g)||[]).length]:null}).filter(Boolean)""")
            html, sdf = r['html'], r['sdf']
            check(f'{sysn}: Bericht ohne Fehler', not errs and r['toasts']==0, '; '.join(errs)[:120])
            missing=[e for e in EXPECT[sysn] if e not in html]
            check(f'{sysn}: Inhalte (Geometrie, Lager, Lasten)', not missing, 'fehlt: '+str(missing) if missing else '')
            check(f'{sysn}: Diagramme am Tragwerk gezeichnet', all(n>500 and lines>=1 for _,n,lines in dia), str([(k,n) for k,n,_ in dia]))
            g = sdf['system']['geometry']
            stale = (g.get('L')==9) or (g.get('b')==9) or (g.get('spans',[0])[0]==9) or '99' in json.dumps(sdf['system'].get('loads',{}))
            check(f'{sysn}: gespeichert = Stand der Berechnung', not stale)
            key = 'u' if sysn=='frame' else 'w'
            check(f'{sysn}: Verformung im SDF = Berechnung', abs((sdf['results'].get(key) or 0) - w_calc[key])<1e-9 and w_calc[key]!=0, f"{key}={w_calc[key]:.3f} mm")
            if APPF:
                rx = sdf['results']['reactions']
                same = all(app_vals[k]==rx[j][key] for k,(_,key,j) in enumerate(APPF))
                check(f'{sysn}: Lagerkräfte App = Bericht', same, f"App {app_vals} / Bericht {[rx[j][key] for _,key,j in APPF]}")
            check(f'{sysn}: Systembild im Bericht, ids eindeutig', 'rep-sys-' in html or 'marker' not in sdf['system']['svgSnapshot'])
        # Alte Speicherung (ohne plot, ohne Lasten/Lager bei Balken, Version 0.5.5)
        errs.clear()
        await pg.evaluate("""()=>{ localStorage.clear();
          const sdf={statiq_version:'0.5.5', timestamp:new Date().toISOString(), module:'calc',
            system:{type:'beam', geometry:{L:5}, svgSnapshot:''},
            results:{Mmax:31.25,Qmax:25,Nmax:0,reactions:[],members:{member_0:{M:[0,-20,-31.25,-20,0],Q:[-25,-12.5,0,12.5,25],N:[0,0,0,0,0]}}}};
          localStorage.setItem('statiq_sdf_1', JSON.stringify({name:'Alt', sdf}));
          showTab('saved'); renderSavedTab(); openReport('statiq_sdf_1'); }""")
        await pg.wait_for_timeout(100)
        html = await pg.evaluate("document.getElementById('report-content').innerHTML")
        check('Alte Speicherung: öffnet, Hinweis, keine Ersatzkurve für w', not errs and 'Ältere Speicherung' in html and 'nicht enthalten' in html, '; '.join(errs)[:120])
        # derselbe Bericht auf Englisch, Französisch, Spanisch
        for lang, words in [('en',['Older saved calculation','Not included','A: pin, B: roller','MAXIMUM INTERNAL FORCES']),
                            ('fr',['Calcul enregistré ancien','A : appui fixe','EFFORTS MAXIMAUX']),
                            ('es',['Cálculo guardado antiguo','A: apoyo fijo','ESFUERZOS MÁXIMOS'])]:
            await pg.evaluate(f"setCalcLang('{lang}'); openReport('statiq_sdf_1')"); await pg.wait_for_timeout(80)
            html = await pg.evaluate("document.getElementById('report-content').innerHTML")
            miss=[w for w in words if w not in html]
            check(f'Bericht auf {lang.upper()}', not miss, miss)
        await b.close()
asyncio.run(main())
print('FAILS:',fails)
