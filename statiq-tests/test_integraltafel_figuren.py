# Integraltafel mit Figuren (ref v0.3.52, calc v0.11.14): Wissen zeigt die Koppeltafel als Matrix mit kleinen Figuren in Kopfzeile
# und Kopfspalte (Rechteck, Dreieck, Dreieck Mitte, Trapez, Parabel); der Rechenweg in Schnittkräfte setzt vor jede Tafelzeile
# die beiden Verläufe (M₀ bzw. M̄ als echte, abgetastete Form).
# Stichproben der Tafelwerte von Hand: ∫ Parabel·Parabel = 8/15·L·i·k; Dreieck Mitte × Dreieck Mitte = ⅓·L·i·k; Dreieck × Dreieck gegensinnig = ⅙·L·i·k.
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'ref.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
        await pg.evaluate("location.hash='#/baustatik/arbeitssatz/koppeltafel'"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("""(()=>{ const t=document.querySelector('.ktf-tab'); if(!t) return null;
          const tx=c=>{ const sp=c.querySelector('.ktf-h span'); return (sp||c).textContent.trim(); };
          return {head:[...t.querySelectorAll('thead th')].map(tx), rows:[...t.querySelectorAll('tbody tr')].map(tr=>[...tr.children].map(tx)),
            svgH:t.querySelectorAll('thead svg.ktf').length, svgR:t.querySelectorAll('tbody th svg.ktf').length, w:t.getBoundingClientRect().width, cw:t.parentNode.clientWidth}; })()""")
        check('Koppeltafel als Matrix: 5 Spalten, 6 Zeilen', r and len(r['head'])==6 and len(r['rows'])==6, r and (len(r['head']), len(r['rows'])))
        check('Figuren in Kopfzeile (5) und Kopfspalte (6)', r and r['svgH']==5 and r['svgR']==6, r and (r['svgH'], r['svgR']))
        check('Spalten: Rechteck, Dreieck, Dreieck Mitte, Trapez, Parabel', r and [h.split(' ')[0] for h in r['head'][1:]]==['Rechteck','Dreieck','Dreieck','Trapez','Parabel'], r and r['head'])
        R={row[0]:row[1:] for row in r['rows']} if r else {}
        check('Parabel × Parabel = 8/15·L·i·k', R.get('Parabel i',[None]*5)[4]=='8/15·L·i·k', R.get('Parabel i'))
        check('Dreieck Mitte × Dreieck Mitte = ⅓·L·i·k', R.get('Dreieck Mitte i',[None]*5)[2]=='⅓·L·i·k')
        check('Dreieck gegensinnig × Dreieck = ⅙·L·i·k', R.get('Dreieck i (gegensinnig)',[None]*5)[1]=='⅙·L·i·k')
        check('Rechner: Tafel passt ohne Scrollen in die Karte', r and r['w']<=r['cw']+1, r and (r['w'], r['cw']))
        # Beschriftung liegt über der Figur (nicht in der Fläche)
        ok=await pg.evaluate("""[...document.querySelectorAll('svg.ktf')].every(s=>{ const p=s.querySelector('path'); return [...s.querySelectorAll('text')].every(t=>{ const b=t.getBBox(), q=s.createSVGPoint(); q.x=b.x+b.width/2; q.y=b.y+b.height*0.6; return !p.isPointInFill(q); }); })""")
        check('Beschriftungen i, k über den Figuren', ok)
        # Handy: Tafel scrollt waagerecht in ihrem Rahmen, die Seite nicht
        m=await br.new_page(viewport={'width':390,'height':844}); m.on('pageerror', lambda e: errs.append(str(e)))
        await m.goto(B+'ref.html#/baustatik/arbeitssatz/koppeltafel'); await m.wait_for_timeout(500)
        sw=await m.evaluate("[document.documentElement.scrollWidth, document.querySelector('.ktf-wrap').scrollWidth>document.querySelector('.ktf-wrap').clientWidth]")
        check('Handy: Seite ohne Querscroll, Tafel scrollt im Rahmen', sw[0]<=390 and sw[1], sw)
        await m.close()
        for l in ['en','fr','es']:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{l}')"); await pg.reload(); await pg.wait_for_timeout(400)
            h=await pg.evaluate("[...document.querySelectorAll('.ktf-tab th')].map(e=>e.textContent.trim()).join(' | ')")
            check(f'{l}: Tafelköpfe übersetzt', not re.search(r'Rechteck|Dreieck|Parabel\b|Trapez\b|gleichsinnig|gegensinnig', h), h[:120])
        # Rechenweg in calc
        c=await br.new_page(viewport={'width':390,'height':844}); c.on('pageerror', lambda e: errs.append(str(e)))
        await c.goto(B+'calc.html'); await c.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await c.reload(); await c.wait_for_timeout(900)
        await c.evaluate("showTab('cont')"); await c.wait_for_timeout(600)
        S=await c.evaluate("rwCont().S")
        figs=[k for k,s in enumerate(S) if s.startswith('<div class=\"rw-figs\"')]
        check('DLT: Figurenpaar vor jeder Tafelzeile (δ11 und zwei Parabel-Zeilen)', len(figs)==3 and all('svg' in S[k] and S[k].count('<svg')==2 for k in figs), len(figs))
        check('DLT: Figurenpaar steht direkt vor der Formel', all(k+1<len(S) and ('δ' in S[k+1] or 'Parabel' in S[k+1]) for k in figs))
        n=await c.evaluate("(()=>{ const c=[...document.querySelectorAll('#tab-cont .rw-card')].find(e=>e.offsetParent); return c ? c.querySelectorAll('.st-f > .rw-figs svg.rw-fig').length : -1 })()")
        check('DLT: Figuren im Rechenweg gezeichnet (direkt im Schritt, nicht als Textzeile)', n>=6, n)
        await c.evaluate("showTab('frame')"); await c.wait_for_timeout(500)
        await c.evaluate("setSupportA('pin'); setSupportB('pin'); calculateFrame()"); await c.wait_for_timeout(600)
        S=await c.evaluate("rwFrame().S")
        figs=[k for k,s in enumerate(S) if s.startswith('<div class=\"rw-figs\"')]
        nT=len([s for s in S if re.match(r'^(Stiel|Riegel)[^<]*\(l = [\d,]+ m\)', s) and ('/6·[' in s or 'numerisch' in s)])
        check('Rahmen: je Tafelzeile ein Figurenpaar', len(figs)==nT and nT>=4, (len(figs), nT))
        # Figur gibt den Verlauf wieder: Parabel im Riegel (Lastzustand) hat in der Mitte den höchsten Punkt
        ok=await c.evaluate("""(()=>{ const d=document.createElement('div'); d.innerHTML=rwFig(t=>4*t*(1-t), null, null); const pts=d.querySelector('polygon').getAttribute('points').split(' ').slice(1,-1).map(p=>p.split(',').map(Number));
          const top=pts.reduce((a,b)=>b[1]<a[1]?b:a); return Math.abs(top[0]-39)<2 && top[1]<=7.01; })()""")
        check('rwFig: Parabel hat den Scheitel in der Mitte', ok)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
