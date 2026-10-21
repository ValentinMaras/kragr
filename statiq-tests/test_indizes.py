# Indizes wie im Lehrbuch (calc v0.8.35, size v0.5.52, ref v0.3.40, projekt v0.1.10, rechtliches v0.1.9): kein „f_yd“ mehr im
# angezeigten Text, sondern f<sub>yd</sub>; in Auswahllisten und Hinweisen ohne Unterstrich (s_d → sd); Skizzen und Eingaben bleiben unberührt.
import os, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
RX=re.compile(r'(?<![\w/\\.])[A-Za-zα-ωΑ-ΩΣΔ′]{1,4}_\{?[A-Za-z0-9,α-ω]+')
TXT="""(()=>{ const out=[]; const w=document.createTreeWalker(document.body,4); while(w.nextNode()){ const n=w.currentNode; if(n.parentElement && n.parentElement.closest('script,style')) continue; out.push(n.nodeValue);}
  document.querySelectorAll('[title],[placeholder],[aria-label]').forEach(e=>out.push((e.title||'')+' '+(e.placeholder||'')+' '+(e.getAttribute('aria-label')||''))); return out.join(' \\n '); })()"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        bad={}
        def add(t,w):
            h=RX.findall(t)
            if h: bad.setdefault(w,set()).update(h)
        for lang in ['de','en']:
            await pg.goto(B+'size.html'); await pg.evaluate(f"localStorage.clear();localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(500)
            n=await pg.evaluate("(buildPick(), document.querySelectorAll('#pick-menu .pick-item').length)")
            for i in range(n):
                await pg.evaluate(f"buildPick(); [...document.querySelectorAll('#pick-menu .pick-item')][{i}].click()"); await pg.wait_for_timeout(120)
                add(await pg.evaluate(TXT), 'size/'+lang)
            await pg.goto(B+'calc.html'); await pg.wait_for_timeout(400)
            for tab in ['beam','cantilever','cont','frame']:
                await pg.evaluate(f"showTab('{tab}')"); await pg.wait_for_timeout(200); add(await pg.evaluate(TXT),'calc/'+lang)
            await pg.goto(B+'ref.html'); await pg.wait_for_timeout(400)
            routes=await pg.evaluate("Object.entries(FAECHER).flatMap(([f,F])=>Object.entries(F.kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>f+'/'+k+'/'+t)))")
            for r in routes:
                await pg.evaluate(f"location.hash='#/{r}'"); await pg.wait_for_timeout(60); add(await pg.evaluate(TXT),'ref/'+lang)
        check('kein Unterstrich-Index in size (alle Modi), calc (alle Systeme), ref (alle Themen), DE und EN', not bad, {k:sorted(v)[:5] for k,v in bad.items()})
        await pg.goto(B+'ref.html#/stahlbeton/baustoffe/beton'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        h=await pg.evaluate("[...document.querySelectorAll('#main th')].map(t=>t.innerHTML).join('|')")
        check('ref Betontabelle: Kopf f<sub>ck</sub>, f<sub>ck,cube</sub>, E<sub>cm</sub>', 'f<sub>ck</sub>' in h and 'f<sub>ck,cube</sub>' in h and 'E<sub>cm</sub>' in h, h[:120])
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(400)
        h=await pg.evaluate("document.querySelector('.formula-box').innerHTML")
        check('calc Theorie: ΣF<sub>y</sub> und ΣM<sub>A</sub>', 'ΣF<sub>y</sub>' in h and 'ΣM<sub>A</sub>' in h, h[:80])
        s=await pg.evaluate("[...document.querySelectorAll('#tab-beam .load-sum')].map(e=>e.textContent)")
        check('calc: Kurzfassung der Streckenlast weiter richtig (q = 5 kN/m · 0 – 5 m)', any('q = 5 kN/m' in x for x in s), s)
        await pg.goto(B+'ref.html'); await pg.wait_for_timeout(400)
        o=await pg.evaluate("[...document.querySelectorAll('option')].map(o=>o.textContent).filter(t=>/PE|Dampfbremse/.test(t)).slice(0,2)")
        r=await pg.goto(B+'ref.html#/bauphysik/waerme/uwert'); await pg.reload(); await pg.wait_for_timeout(500)
        o=await pg.evaluate("[...document.querySelectorAll('option')].map(o=>o.textContent).filter(t=>/Dampfbremse 0,2/.test(t))")
        check('Auswahlliste: „Dampfbremse 0,2 mm (sd = 2 m)“ ohne Unterstrich', o and all('_' not in x and 'sd' in x for x in o), o[:1])
        svg=await pg.evaluate("[...document.querySelectorAll('svg sub')].length")
        check('Skizzen (SVG) unberührt', svg==0, svg)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
