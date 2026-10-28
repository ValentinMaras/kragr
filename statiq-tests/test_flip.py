# Karten klappen weich (calc v0.11.12, vorher v0.11.10 mit Verschieben per transform): GSAP 3.13, selbst gehostet (k5/gsap.min.js).
# Die Höhe der geklappten Karte gleitet, alles darunter folgt über das Layout → nur die eigene Spalte bewegt sich (zwei Spalten am
# Rechner), am Seitenende kein Sprung. Zuklappen: Inhalt bleibt sichtbar (k5-closing) und blendet aus. Handy: Kopf bleibt stehen.
# Ohne GSAP: gleiche Höhenbewegung über die Web Animations API; im ruhigen Modus (Tests, „Bewegung reduzieren“) keine Bewegung.
import os, sys, asyncio, re, json
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
PAGES=['index','calc','size','ref','projekt','rechtliches']
gp=os.path.join(BASE,'k5','gsap.min.js')
check('GSAP selbst gehostet (k5/gsap.min.js, 3.13.0, Lizenzkopf)', os.path.exists(gp) and 'GSAP 3.13.0' in open(gp,encoding='utf-8').read(400) and 'standard-license' in open(gp,encoding='utf-8').read(600))
src={p:open(os.path.join(BASE,p+'.html'),encoding='utf-8').read() for p in PAGES}
check('alle sechs Seiten laden GSAP mit defer, vor dem k5-Baustein', all(re.search(r'<script data-k5-gsap src="k5/gsap\.min\.js" defer></script>\n<script data-k5>', s) for s in src.values()))
check('kein GSAP aus dem Netz (CDN)', not any('cdnjs' in s or 'jsdelivr' in s or 'unpkg' in s for s in src.values()))
sw=open(os.path.join(BASE,'sw.js'),encoding='utf-8').read(); files=json.loads(re.search(r'const FILES = (\[.*?\]);',sw).group(1))
check('Service Worker speichert GSAP für offline', 'k5/gsap.min.js' in files)

# Klick auf den Kopf und Messung über die Dauer der Bewegung (je Bild ein Messpunkt)
SAMPLE="""async([sel, watch])=>{ const c=document.querySelector(sel), h=c.querySelector(':scope > .k5-head, :scope > .k-head') || c;
  const w=watch ? document.querySelector(watch) : null, out=[]; h.click();
  const t0=performance.now(); await new Promise(res=>{ (function f(){ const b=c.querySelector(':scope > .k5-body');
    out.push({t:performance.now()-t0, head:h.getBoundingClientRect().top, sy:scrollY, ih:c.style.height, cl:c.classList.contains('k5-closing'),
      body:b ? getComputedStyle(b).display : null, w:w ? w.getBoundingClientRect().top : null, tr:[...document.querySelectorAll('body *')].some(e=>e.style.transform && /translate|matrix/.test(e.style.transform) && !e.classList.contains('k5-pill'))});
    if(performance.now()-t0<900) requestAnimationFrame(f); else res(); })(); });
  return {s:out, open:!c.classList.contains('k5-closed') && !c.classList.contains('closed') && !c.classList.contains('k-closed'), end:c.style.height, endCl:c.classList.contains('k5-closing')}; }"""
def mid(r): return [x for x in r['s'] if 60<x['t']<250]
def steps(r, k):   # größter Schritt je Bild; der erste Messpunkt direkt nach dem Klick (vor dem nächsten Bild) wird nicht gezeichnet
    v=[x[k] for x in r['s'] if x[k] is not None and x['t']>1]; return max([abs(b-a) for a,b in zip(v,v[1:])] or [0])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')")
        for page in PAGES:
            await pg.goto(B+page+'.html?k5motion'); await pg.wait_for_timeout(300)
            v=await pg.evaluate("window.gsap && gsap.version"); check(f'{page}: GSAP geladen', v=='3.13.0', v)
        # Handy: Karte auf- und zuklappen
        await pg.goto(B+'calc.html?k5motion'); await pg.wait_for_timeout(800)
        K='#tab-beam .k-knoten'
        await pg.evaluate(f"document.querySelector('{K}').scrollIntoView({{block:'center'}})"); await pg.wait_for_timeout(200)
        r=await pg.evaluate(SAMPLE, [K, None]); m=mid(r)
        check('Aufklappen: Höhe gleitet (Inline-Höhe während der Bewegung)', r['open'] and any(x['ih'] for x in m), m[:2])
        check('kein Verschieben per transform mehr', not any(x['tr'] for x in r['s']))
        check('danach aufgeräumt (keine Inline-Höhe)', r['end']=='' and not r['endCl'], r['end'])
        hs=[x['head'] for x in r['s']]
        check('Handy: Kopf der Karte bleibt stehen (± 2 px)', max(hs)-min(hs)<=2, (min(hs),max(hs)))
        r=await pg.evaluate(SAMPLE, [K, None]); m=mid(r)
        check('Zuklappen: Inhalt bleibt sichtbar und blendet aus, bis die Karte zu ist', not r['open'] and m and all(x['cl'] and x['body']=='block' for x in m), m[:2])
        check('Zuklappen: Höhe gleitet, danach aufgeräumt', any(x['ih'] for x in m) and r['end']=='' and not r['endCl'] and r['s'][-1]['body']=='none', r['s'][-1])
        # Seitenende: keine Sprünge beim Zuklappen ganz unten (Seite rückt allmählich nach)
        await pg.evaluate(f"(()=>{{const c=document.querySelector('{K}'); if(c.classList.contains('k5-closed')) kragrK5.setClosed(c,false,true); window.scrollTo(0, document.body.scrollHeight);}})()"); await pg.wait_for_timeout(300)
        r=await pg.evaluate(SAMPLE, [K, None])
        check('Seitenende: Seite rückt ohne Sprung nach (größter Schritt je Bild < 70 px)', steps(r,'sy')<70, steps(r,'sy'))
        # Dreimal schnell: Endzustand stimmt, nichts bleibt hängen
        st=await pg.evaluate(f"""async()=>{{const c=document.querySelector('{K}'), h=c.querySelector(':scope > .k5-head'); h.click(); await new Promise(r=>setTimeout(r,60)); h.click(); await new Promise(r=>setTimeout(r,60)); h.click();
          await new Promise(r=>setTimeout(r,900)); return [c.classList.contains('k5-closed'), c.style.height, c.classList.contains('k5-closing'), getComputedStyle(c.querySelector(':scope > .k5-body')).display]}}""")
        check('dreimal schnell getippt: Endzustand stimmt, nichts hängt', st[1]=='' and not st[2] and (st[3]=='none')==st[0], st)
        # Rechner, zwei Spalten: nur die eigene Spalte bewegt sich
        d=await br.new_page(viewport={'width':1280,'height':860}); d.on('pageerror', lambda e: errs.append(str(e)))
        await d.goto(B+'calc.html?k5motion'); await d.wait_for_timeout(900)
        await d.evaluate("window.scrollTo(0, 300)"); await d.wait_for_timeout(200)
        r=await d.evaluate(SAMPLE, ['#tab-beam .k-loads', '#tab-beam .col-out > *:first-child'])
        check('Rechner: Lasten zuklappen (linke Spalte) — rechte Spalte bleibt stehen', steps(r,'w')<=1 and steps(r,'sy')<=1, (steps(r,'w'), steps(r,'sy')))
        hs=[x['ih'] for x in mid(r)]
        check('Rechner: die Lasten-Karte gleitet in der Höhe', any(hs), hs[:3])
        mh=await d.evaluate("document.querySelector('#tab-beam .cols').style.minHeight")
        await d.evaluate("window.scrollTo(0,0)"); await d.wait_for_timeout(300)
        mh2=await d.evaluate("document.querySelector('#tab-beam .cols').style.minHeight")
        check('Rechner: Spaltenbehälter hält die Höhe, beim Hochscrollen wieder frei', mh!='' and mh2=='', (mh, mh2))
        await d.evaluate("window.scrollTo(0, 300)"); await d.wait_for_timeout(200)
        r=await d.evaluate(SAMPLE, ['#tab-beam .k-knoten', '#tab-beam .col-in > *:first-child'])
        check('Rechner: Karte rechts aufklappen — linke Spalte bleibt stehen', steps(r,'w')<=1 and steps(r,'sy')<=1, (steps(r,'w'), steps(r,'sy')))
        await d.close()
        # size: fremde Faltkarte gleitet ebenfalls
        await pg.goto(B+'size.html?k5motion'); await pg.wait_for_timeout(700)
        r=await pg.evaluate("""async()=>{const t=[...document.querySelectorAll('.fold > .card-title, .dfold > .card-title')].find(e=>e.offsetParent); if(!t) return null; const c=t.parentNode;
          t.scrollIntoView({block:'center'}); await new Promise(r=>setTimeout(r,80)); t.click(); await new Promise(r=>setTimeout(r,120)); const a=c.style.height; await new Promise(r=>setTimeout(r,800)); return {a, b:c.style.height}}""")
        check('size: Faltkarte gleitet in der Höhe und räumt auf', r is None or (r['a']!='' and r['b']==''), r)
        # Ruhiger Modus: keine Bewegung
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(500)
        r=await pg.evaluate(SAMPLE, [K, None])
        check('ruhiger Modus: keine Inline-Höhe, kein k5-closing', not any(x['ih'] or x['cl'] for x in r['s']))
        # Ohne GSAP: Web Animations API
        await pg.goto(B+'calc.html?k5motion'); await pg.wait_for_timeout(700); await pg.evaluate("delete window.gsap")
        r=await pg.evaluate(f"""async()=>{{const c=document.querySelector('{K}'); c.querySelector(':scope > .k5-head').click(); await new Promise(r=>setTimeout(r,60));
          const n=c.getAnimations().filter(a=>a.effect && a.effect.getKeyframes().some(k=>'height' in k)).length; await new Promise(r=>setTimeout(r,800)); return [n, c.style.height]}}""")
        check('ohne GSAP: Höhenbewegung über die Web Animations API, danach aufgeräumt', r[0]>=1 and r[1]=='', r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
