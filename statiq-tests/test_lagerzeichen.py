# Einheitliche Systemdarstellung (calc v0.11.7): Lagerzeichen nach Lehrbuch (Einspannung mit Schraffur direkt am Stab,
# Festlager mit Schraffur unter dem Dreieck, Loslager mit Gleitlinie parallel zur Unterseite, Wegfeder als Zickzack,
# Drehfeder als Spirale), Dreiecke als Kontur, Skizzen und Verläufe nur grau/schwarz.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
OLD=['#d85a30','#185fa5','#d97706','#7c3aed','#0f6e56','#8b3a1e','#5468ad','#b42318','#d0e8d0','#a8d4a8','#2d6a4f','#45589a','#92400e']
COLORS="sel=>{ const s=new Set(); document.querySelectorAll(sel).forEach(svg=>svg.querySelectorAll('*').forEach(e=>['fill','stroke'].forEach(a=>{ const v=(e.getAttribute(a)||'').toLowerCase(); if(v.startsWith('#')) s.add(v); }))); return [...s]; }"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        r=await pg.evaluate("""(()=>{ const svg=document.getElementById('beam-svg'), pol=[...svg.querySelectorAll('polygon')].filter(p=>p.getAttribute('fill')==='#fff');
          return [pol.length, [...svg.querySelectorAll('circle')].filter(c=>c.getAttribute('fill')==='#fff' && +c.getAttribute('r')<3).length]; })()""")
        check('Einfeldträger: zwei Dreiecke als Kontur (weiß gefüllt) mit Gelenkkreis', r==[2,2], r)
        r=await pg.evaluate("""(()=>{ const svg=document.getElementById('beam-svg'), L=[...svg.querySelectorAll('line')].map(l=>[+l.getAttribute('x1'),+l.getAttribute('y1'),+l.getAttribute('x2'),+l.getAttribute('y2'),l.getAttribute('stroke')]);
          const hor=x=>L.filter(l=>Math.abs(l[1]-l[3])<0.01 && l[0]<x && l[2]>x && l[1]>78 && l[4]==='#111114').length; return [hor(30), hor(290)]; })()""")
        check('Festlager: eine Grundlinie mit Schraffur, Loslager: Gleitlinie + Grundlinie', r==[1,2], r)
        await pg.evaluate("showTab('cantilever')"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("""(()=>{ const svg=document.getElementById('cant-svg'), L=[...svg.querySelectorAll('line')]; const wall=L.find(l=>+l.getAttribute('x1')===50 && +l.getAttribute('x2')===50);
          return [!!wall, L.filter(l=>+l.getAttribute('x1')===50 && +l.getAttribute('x2')<50).length, svg.querySelectorAll('rect[fill="#e0dfd8"]').length]; })()""")
        check('Kragarm: Einspannung als Wand direkt am Stabende (x = 50) mit Schraffur, kein grauer Block mehr', r[0] and r[1]>=4 and r[2]==0, r)
        await pg.evaluate("SUPX.cantilever={on:true, A:{cr:5000}}; drawCantilever()")
        r=await pg.evaluate("document.querySelectorAll('#cant-svg path').length>0 && [...document.querySelectorAll('#cant-svg path')].some(p=>(p.getAttribute('d')||'').split('L').length>40)")
        check('Drehfeder: Spirale statt Wand', r)
        await pg.evaluate("showTab('frame'); SUPX.frame={on:true, B:{cv:2000}}; drawFrame()"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('#frame-svg path')].filter(p=>(p.getAttribute('d')||'').split('L').length===9).length")
        check('Wegfeder: Zickzack unter dem Lager B', r>=1, r)
        await pg.evaluate("SUPX.frame={on:true, B:{ch:500}}; drawFrame()")
        r=await pg.evaluate("[...document.querySelectorAll('#frame-svg path')].filter(p=>(p.getAttribute('d')||'').split('L').length===9).length")
        check('Waagerechte Feder am Festlager: Zickzack zur Seite', r>=1, r)
        await pg.evaluate("SUPX.frame={}; drawFrame(); liveCalc(true)"); await pg.wait_for_timeout(400)
        bad=[]
        for t in ['beam','cantilever','cont','frame']:
            await pg.evaluate(f"showTab('{t}')"); await pg.wait_for_timeout(300)
            for m in ['M','Q','N','W']:
                await pg.evaluate(f"setDiagMode('{({'cantilever':'cant'}).get(t,t)}','{m}')")
                c=await pg.evaluate(COLORS, f"#tab-{t} svg")
                bad+= [(t,m,x) for x in c if x in OLD]
        check('Skizzen und Verläufe aller Systeme ohne die alten Farben (Rot, Blau, Orange, Violett, Grün, Braun)', not bad, bad[:6])
        r=await pg.evaluate("[diagColors.M, diagColors.Q, diagColors.N, CLR.F, CLR.q]")
        check('Farbtabellen grau/schwarz', all(x in ('#111114','#2b2d33','#3d3f45','#5c5e66') for x in r), r)
        await pg.close()
        pm=await br.new_page(viewport={'width':360,'height':780}); pm.on('pageerror', lambda e: errs.append(str(e)))
        await pm.goto(B+'calc.html'); await pm.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pm.reload(); await pm.wait_for_timeout(900)
        w=[]
        for t in ['beam','cantilever','cont','frame']:
            await pm.evaluate(f"showTab('{t}')"); await pm.wait_for_timeout(300); w.append(await pm.evaluate("document.documentElement.scrollWidth"))
        check('Handy 360 px: kein seitliches Scrollen', all(x<=360 for x in w), w)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print(f"\n{'ALLE OK' if not fails else str(fails)+' FEHLER'}"); sys.exit(1 if fails else 0)
