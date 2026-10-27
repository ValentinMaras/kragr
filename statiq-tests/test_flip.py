# Karten klappen weich auf (calc v0.11.10): FLIP mit GSAP 3.13, selbst gehostet als k5/gsap.min.js.
# Animiert werden nur transform (Nachfolgendes gleitet) und clip-path (wachsende Karte wird aufgedeckt), nie die Höhe.
# Ohne GSAP bleibt die alte Höhen-Animation; im ruhigen Modus (Tests, „Bewegung reduzieren“) keine Bewegung.
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
check('alle sechs Seiten laden GSAP mit defer, vor dem k5-Baustein',
      all(re.search(r'<script data-k5-gsap src="k5/gsap\.min\.js" defer></script>\n<script data-k5>', s) for s in src.values()))
check('kein GSAP aus dem Netz (CDN)', not any('cdnjs' in s or 'jsdelivr' in s or 'unpkg' in s for s in src.values()))
sw=open(os.path.join(BASE,'sw.js'),encoding='utf-8').read(); files=json.loads(re.search(r'const FILES = (\[.*?\]);',sw).group(1))
check('Service Worker speichert GSAP für offline', 'k5/gsap.min.js' in files)

MOVING="""()=>[...document.querySelectorAll('body *')].filter(e=>!e.classList.contains('k5-pill') && ((e.style.transform && /translate|matrix/.test(e.style.transform)) || e.style.clipPath)).length"""
OPEN1="""async(wait)=>{let c=[...document.querySelectorAll('.k5-acc.k5-closed')].find(c=>c.offsetParent);
  if(!c){ c=[...document.querySelectorAll('.k5-acc')].find(c=>c.offsetParent); kragrK5.setClosed(c,true,true); }
  c.scrollIntoView({block:'start'}); await new Promise(r=>setTimeout(r,80));
  c.querySelector(':scope > .k5-head').click(); await new Promise(r=>setTimeout(r,wait));
  const tr=[...document.querySelectorAll('body *')].filter(e=>!e.classList.contains('k5-pill') && e.style.transform && /translate|matrix/.test(e.style.transform)).length;
  return {clip:c.style.clipPath, tr, height:c.getAnimations().filter(a=>a.effect && a.effect.getKeyframes().some(k=>'height' in k)).length, open:!c.classList.contains('k5-closed'),
          aria:c.querySelector(':scope > .k5-head').getAttribute('aria-expanded'), id:c.querySelector('.k5-head').textContent.trim().slice(0,20)}}"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')")
        for page in PAGES:
            await pg.goto(B+page+'.html?k5motion'); await pg.wait_for_timeout(300)
            v=await pg.evaluate("window.gsap && gsap.version")
            check(f'{page}: GSAP geladen', v=='3.13.0', v)
        # Mit Bewegung: Karte aufklappen
        await pg.goto(B+'calc.html?k5motion'); await pg.wait_for_timeout(700)
        r=await pg.evaluate(OPEN1, 90)
        check('mitten in der Bewegung: Karte wird per clip-path aufgedeckt', r['clip'].startswith('inset(') and 'round' in r['clip'], r)
        check('mitten in der Bewegung: Nachfolgendes gleitet per transform', r['tr']>=1, r)
        check('keine Höhen-Animation an der Karte (nur transform und clip-path)', r['height']==0, r)
        check('Zustand sofort richtig: offen, aria-expanded=true', r['open'] and r['aria']=='true', r)
        await pg.wait_for_timeout(700)
        n=await pg.evaluate(MOVING)
        check('nach der Bewegung: keine Reste (transform, clip-path) im Inline-Stil', n==0, n)
        # Unterbrechen: zweimal schnell hintereinander
        st=await pg.evaluate("""async()=>{const c=[...document.querySelectorAll('.k5-acc')].find(c=>c.offsetParent && !c.classList.contains('k5-closed'));
          const h=c.querySelector(':scope > .k5-head'); h.click(); await new Promise(r=>setTimeout(r,60)); h.click(); await new Promise(r=>setTimeout(r,60)); h.click();
          await new Promise(r=>setTimeout(r,800)); return c.classList.contains('k5-closed')}""")
        n=await pg.evaluate(MOVING)
        check('dreimal schnell getippt: Endzustand zu, keine Reste', st and n==0, (st,n))
        # Lage stimmt nach der Bewegung mit der Lage ohne Bewegung überein (alle Blöcke unter der Karte)
        pos=await pg.evaluate("""async()=>{const c=[...document.querySelectorAll('.k5-acc.k5-closed')].find(c=>c.offsetParent); const h=c.querySelector(':scope > .k5-head');
          const flow=[]; for(let n=c; n && n!==document.body; n=n.parentElement) for(let s=n.nextElementSibling; s; s=s.nextElementSibling) if(s.getClientRects().length) flow.push(s);
          h.click(); await new Promise(r=>setTimeout(r,800)); const a=flow.map(e=>Math.round(e.getBoundingClientRect().top));
          flow.forEach(e=>e.style.transform='none'); const b=flow.map(e=>Math.round(e.getBoundingClientRect().top)); flow.forEach(e=>e.style.transform='');
          return {n:flow.length, same:a.every((v,i)=>v===b[i])}}""")
        check('nach der Bewegung sitzt alles an seiner Layout-Stelle', pos['n']>=1 and pos['same'], pos)
        # Fremde Klapp-Mechanik (size: Faltkarte)
        await pg.goto(B+'size.html?k5motion'); await pg.wait_for_timeout(700)
        r=await pg.evaluate("""async()=>{const t=[...document.querySelectorAll('.fold > .card-title, .dfold > .card-title, .k-loads > .k-head, .k-row > button:first-child')].find(e=>e.offsetParent);
          if(!t) return null; t.scrollIntoView({block:'center'}); await new Promise(r=>setTimeout(r,80)); t.click(); await new Promise(r=>setTimeout(r,120));
          const a=[...document.querySelectorAll('body *')].filter(e=>!e.classList.contains('k5-pill') && (e.style.transform||e.style.clipPath)).length;
          await new Promise(r=>setTimeout(r,700));
          const b=[...document.querySelectorAll('body *')].filter(e=>!e.classList.contains('k5-pill') && (e.style.transform||e.style.clipPath)).length;
          return {a,b}}""")
        check('size: fremde Faltkarte gleitet ebenfalls und räumt auf', r is None or (r['a']>=1 and r['b']==0), r)
        # Ruhiger Modus (automatisierter Browser ohne ?k5motion): keine Bewegung
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(500)
        r=await pg.evaluate(OPEN1, 60)
        check('ruhiger Modus: weder clip-path noch transform', not r['clip'] and r['tr']==0 and r['open'], r)
        # Rückfall ohne GSAP: alte Höhen-Animation, keine Fehler
        await pg.goto(B+'calc.html?k5motion'); await pg.wait_for_timeout(700)
        await pg.evaluate("delete window.gsap")
        r=await pg.evaluate(OPEN1, 60)
        check('ohne GSAP: Höhen-Animation wie bisher, kein clip-path', r['height']>=1 and not r['clip'], r)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
