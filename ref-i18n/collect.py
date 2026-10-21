# Sammelt für ein Fach: statische Blattblöcke (DE, aus CONTENT) und fehlende Code-Texte (EN, beim Rendern mit AFTER und beim Durchschalten der Eingaben)
import asyncio, json, sys
from playwright.async_api import async_playwright
FACH=sys.argv[1]
STATIC=r"""(f) => { const out=[]; for(const [k,b] of Object.entries(CONTENT)){ if(!k.startsWith(f+'/')) continue;
  const div=document.createElement('div'); div.innerHTML=b();
  [div, ...div.querySelectorAll('*')].forEach(el=>{ const tn=el.nodeName.toUpperCase(); if(['SCRIPT','STYLE','INPUT','TEXTAREA'].includes(tn)) return;
    if(!refBlockOf(el)) return; if(el!==div && el.parentElement && refBlockOf(el.parentElement)) return; out.push(refNorm(el.innerHTML)); });
  div.querySelectorAll('[placeholder],[title],[aria-label]').forEach(e=>['placeholder','title','aria-label'].forEach(a=>{ const v=e.getAttribute(a); if(v && /[A-Za-zÄÖÜäöüß]{3}/.test(v)) out.push(v); }));
  } return [...new Set(out)]; }"""
RENDERED=r"""() => { const root=document.getElementById('main'); const out=refUnits(root).map(u=>u.key);
  root.querySelectorAll('[placeholder],[title],[aria-label]').forEach(e=>['placeholder','title','aria-label'].forEach(a=>{ const v=e.getAttribute(a); if(v && /[A-Za-zÄÖÜäöüß]{3}/.test(v)) out.push(v); }));
  return out; }"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+__import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'../../ref.html'))); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        stat=set()
        pages0=await pg.evaluate(f"Object.entries(FAECHER['{FACH}'].kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>'{FACH}/'+k+'/'+t))")
        for key in pages0:
            await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(150)
            stat |= set(await pg.evaluate(RENDERED))
        stat=sorted(stat)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("window.__trMiss=new Set()")
        pages=await pg.evaluate(f"Object.entries(FAECHER['{FACH}'].kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>'{FACH}/'+k+'/'+t))")
        for key in pages:
            await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(150)
            ids=await pg.evaluate("[...document.querySelectorAll('#main select, #main input[type=checkbox]')].map(e=>e.id).filter(Boolean)")
            for sid in ids:
                n=await pg.evaluate(f"(()=>{{const e=document.getElementById('{sid}'); return e.tagName==='SELECT'?e.options.length:2}})()")
                for k in range(min(n,10)):
                    await pg.evaluate(f"""(()=>{{const e=document.getElementById('{sid}'); if(!e) return; if(e.tagName==='SELECT') e.selectedIndex={k}; else e.checked=!e.checked; e.dispatchEvent(new Event('input',{{bubbles:true}})); e.dispatchEvent(new Event('change',{{bubbles:true}}));}})()""")
                await pg.evaluate(f"location.hash='#/'"); await pg.wait_for_timeout(50); await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(80)
        miss=await pg.evaluate("[...window.__trMiss]")
        json.dump({'static':stat,'dyn':miss},open(f'col_{FACH}.json','w'),ensure_ascii=False)
        print(FACH,'static',len(stat),sum(map(len,stat)),'dyn',len(miss),sum(map(len,miss)),'errs',errs[:3])
        await b.close()
asyncio.run(main())
