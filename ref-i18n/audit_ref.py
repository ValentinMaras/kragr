import asyncio, json, sys, re
from playwright.async_api import async_playwright
FACH=sys.argv[1]; FULL=len(sys.argv)>2
GER=re.compile(r'[äöüÄÖÜß]|\b(und|der|die|das|mit|nicht|oder|für|ein|eine|bei|aus|nach|ist|sind|wird|im|am|zum|zur|vom|oben|unten|links|rechts|Feld|Felder|Last|Lager|Träger|Stütze|Wand|Platte|Balken|Querschnitt|Kraft|Knoten|Stab|Gurt|Pfosten|Riegel|Seite|Höhe|Breite|Dicke|Länge|Beispiel|Schnitt|Fall)\b')
JS=r"""(sel) => { const out=[]; document.querySelectorAll(sel).forEach(R=>{ const w=document.createTreeWalker(R, NodeFilter.SHOW_TEXT);
  while(w.nextNode()){ const n=w.currentNode, p=n.parentElement; if(!p || ['SCRIPT','STYLE','SUB','SUP'].includes(p.tagName.toUpperCase())) continue;
    const t=n.textContent.trim(); if(t && /[A-Za-zÄÖÜäöüß]{3,}/.test(t)) out.push(t); }
  R.querySelectorAll('[placeholder],[title],[aria-label]').forEach(e=>['placeholder','title','aria-label'].forEach(a=>{ const v=e.getAttribute(a); if(v) out.push('@'+v); })); }); return out; }"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file:///home/claude/work/v085/ref.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(300)
        pages=await pg.evaluate(f"Object.entries(FAECHER['{FACH}'].kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>'{FACH}/'+k+'/'+t))")
        left={}
        async def grab(tag):
            await pg.wait_for_timeout(30)
            for t in await pg.evaluate(JS, '#main, #sidebar, #toc, #breadcrumb'):
                if GER.search(t): left.setdefault(t[:130], tag)
        for key in pages:
            await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(150); await grab(key)
            if FULL:
                ids=await pg.evaluate("[...document.querySelectorAll('#main select, #main input[type=checkbox]')].map(e=>e.id).filter(Boolean)")
                for sid in ids:
                    n=await pg.evaluate(f"(()=>{{const e=document.getElementById('{sid}'); return e.tagName==='SELECT'?e.options.length:2}})()")
                    for k in range(min(n,10)):
                        await pg.evaluate(f"""(()=>{{const e=document.getElementById('{sid}'); if(!e) return; if(e.tagName==='SELECT') e.selectedIndex={k}; else e.checked=!e.checked; e.dispatchEvent(new Event('input',{{bubbles:true}})); e.dispatchEvent(new Event('change',{{bubbles:true}}));}})()""")
                        await grab(key+':'+sid)
                    await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(40); await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(100)
                # Zahlenfelder ändern
                nids=await pg.evaluate("[...document.querySelectorAll('#main input[type=number]')].map(e=>e.id).filter(Boolean)")
                for sid in nids[:12]:
                    await pg.evaluate(f"""(()=>{{const e=document.getElementById('{sid}'); e.value=(+e.value||1)*1.37; e.dispatchEvent(new Event('input',{{bubbles:true}})); e.dispatchEvent(new Event('change',{{bubbles:true}}));}})()""")
                await grab(key+':num')
        json.dump(left,open(f'left_{FACH}.json','w'),ensure_ascii=False,indent=0)
        for k,v in left.items(): print(repr(k),v)
        print(len(left),'errs',errs[:3])
        await b.close()
asyncio.run(main())
