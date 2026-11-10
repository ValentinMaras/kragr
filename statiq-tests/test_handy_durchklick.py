# Durchklicken am Handy (Prüfliste, Nov. 2026; calc v0.11.32 · ref v0.3.71): alle Bemessungs-Modi, alle Wissen-Themen,
# vier Schnittkräfte-Systeme, Startseite, Rechenblätter und Rechtliches in 360 px (DE) und 390 px (EN/FR/ES).
# Dazu je Bemessungs-Modus die Karte „Umfang und Grundlagen“. Geprüft: keine Seitenfehler, Seite nicht breiter als der Bildschirm, keine Beschriftung außerhalb einer Skizze,
# keine überlappenden Beschriftungen, keine Skizzenschrift unter 6,5 px (Bemessung mit Lupe: 4,5 px). Ohne Playwright: SKIP.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:260])
PROBE = r"""(root, minPx=6.5)=>{ const res={clip:[],ovl:[],small:[]};
 const vis=e=>{ const s=getComputedStyle(e); return s.visibility!=='hidden' && s.display!=='none' && +s.opacity!==0; };
 root.querySelectorAll('svg').forEach(svg=>{ const b=svg.getBoundingClientRect(); if(b.width<60||b.height<40) return;
  if(svg.closest('.modal-overlay')) return; let p=svg; while(p){ if(p.nodeType===1 && getComputedStyle(p).display==='none') return; p=p.parentElement; }
  const T=[...svg.querySelectorAll('text')].filter(t=>(t.textContent||'').trim() && vis(t)).map(t=>({r:t.getBoundingClientRect(), s:(t.textContent||'').trim().slice(0,28)})).filter(o=>o.r.width>0);
  T.forEach(o=>{ const r=o.r; if(r.left<b.left-1.5||r.right>b.right+1.5||r.top<b.top-1.5||r.bottom>b.bottom+1.5) res.clip.push(o.s);
    if(r.height<minPx) res.small.push(o.s+' ('+r.height.toFixed(1)+'px)'); });
  for(let i=0;i<T.length;i++) for(let j=i+1;j<T.length;j++){ const a=T[i].r, c=T[j].r;
    const w=Math.min(a.right,c.right)-Math.max(a.left,c.left), h=Math.min(a.bottom,c.bottom)-Math.max(a.top,c.top);
    if(w>1.5 && h>1.5 && w*h>0.25*Math.min(a.width*a.height, c.width*c.height)) res.ovl.push(T[i].s+' ⟂ '+T[j].s); }
 });
 res.overflow = document.documentElement.scrollWidth - document.documentElement.clientWidth; return res; }"""
MODES=[('beton',['balken','unterzug','platte','stuetze','durchstanzen']),('stahl',['traeger','anschluss','fuss','schweiss']),
 ('holz',['bauteil','verbindung','ausklink','sattel','versatz']),('mauer',['druck','teil','keller','schub']),
 ('grund',['flach','setzung','wand','upl','gleit']),('wasser',['druck','schwimm','rohr','gerinne','wehr']),('bauph',['uwert','glaser','schall'])]
SET={'beton':'setTyp','stahl':'setStMode','holz':'setHoMode','mauer':'setMwMode','grund':'setGrMode','wasser':'setWbMode','bauph':'setBpMode'}
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for L,w in (('de',360),('en',390),('fr',390),('es',390)):
            ctx=await br.new_context(viewport={'width':w,'height':800}, is_mobile=True, has_touch=True)
            pg=await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
            bad={'clip':[],'ovl':[],'small':[],'overflow':[]}; n=0; scope=[]
            def note(where,r):
                for k in ('clip','ovl','small'):
                    if r[k]: bad[k].append(where+': '+', '.join(sorted(set(r[k]))[:2]))
                if r['overflow']>2: bad['overflow'].append(f"{where} (+{r['overflow']} px)")
            await pg.goto(B+'size.html'); await pg.evaluate(f"localStorage.clear();localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(600)
            for k in [f'{a}/{x}' for a,xs in MODES for x in xs]+await pg.evaluate('Object.keys(PA)'):
                mat,m=k.split('/'); await pg.evaluate(f"setMat('{mat}'); {SET[mat]}('{m}')"); await pg.wait_for_timeout(100)
                await pg.evaluate("document.querySelectorAll('.card.closed').forEach(c=>c.classList.remove('closed'))"); await pg.wait_for_timeout(50)
                note('Bemessung '+k, await pg.evaluate(f'(()=>({PROBE})(document.body, 4.5))()')); n+=1   # Bemessung: Querschnittskizzen haben die Lupe (Ansichtsfenster), daher nur grobe Untergrenze
                if not await pg.evaluate("(()=>{ const c=[...document.querySelectorAll('.card')].find(e=>e.querySelector('.card-title, .det-h, summary') && /Umfang und Grundlagen|Scope|Portée|Alcance/.test(e.textContent)); return !!c; })()"): scope.append(k)
            await pg.goto(B+'ref.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(500)
            routes=await pg.evaluate("Object.entries(FAECHER).flatMap(([f,F])=>Object.entries(F.kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>f+'/'+k+'/'+t)))")
            for rt in ['']+routes:
                await pg.evaluate(f"location.hash='#/{rt}'"); await pg.wait_for_timeout(80)
                note('Wissen '+(rt or 'Start'), await pg.evaluate(PROBE, await pg.query_selector('body'))); n+=1
            await pg.goto(B+'calc.html'); await pg.evaluate(f"localStorage.clear();localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(800)
            for tab in ['beam','cantilever','cont','frame']:
                await pg.evaluate(f"showTab('{tab}')"); await pg.wait_for_timeout(450)
                note('Schnittkräfte '+tab, await pg.evaluate(PROBE, await pg.query_selector('body'))); n+=1
            narrow=[]
            for f in ['calc.html','size.html','ref.html','projekt.html']:   # Auswahl oben füllt die Breite (am iPhone war sie in Schnittkräfte nach der Fußleisten-Änderung schmal)
                await pg.goto(B+f); await pg.wait_for_timeout(500)
                pw=await pg.evaluate("(()=>{ const p=document.querySelector('#pick, .pick'); return p? p.getBoundingClientRect().width : null; })()")
                if pw is not None and pw < 0.8*w: narrow.append(f'{f}: {round(pw)} px')
            check(f'{L} {w} px: Auswahl oben mindestens 80 % der Breite', not narrow, narrow)
            for f in ['index.html','projekt.html','rechtliches.html']:
                await pg.goto(B+f); await pg.wait_for_timeout(450); note(f, await pg.evaluate(PROBE, await pg.query_selector('body'))); n+=1
            check(f'{L} {w} px: {n} Seiten ohne Seitenfehler', not errs, errs[:3])
            check(f'{L} {w} px: jeder Bemessungs-Modus hat die Karte „Umfang und Grundlagen“', not scope, scope[:5])
            check(f'{L} {w} px: keine Seite breiter als der Bildschirm', not bad['overflow'], bad['overflow'][:4])
            check(f'{L} {w} px: keine Beschriftung ragt aus einer Skizze', not bad['clip'], bad['clip'][:4])
            check(f'{L} {w} px: keine überlappenden Beschriftungen in Skizzen', not bad['ovl'], bad['ovl'][:4])
            check(f'{L} {w} px: Skizzenschrift nirgends unter 6,5 px (Bemessung 4,5 px)', not bad['small'], bad['small'][:4])
            await ctx.close()
        await br.close()
    print('FAILS:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
