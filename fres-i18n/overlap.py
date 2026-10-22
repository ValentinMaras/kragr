import asyncio, json, sys
from playwright.async_api import async_playwright
import os; B='file://'+os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))+'/'
JS=r"""() => { const res=[]; document.querySelectorAll('#main svg, main svg, #fig svg').forEach((sv,si)=>{ const R=sv.getBoundingClientRect(); if(!R.width) return;
  const T=[...sv.querySelectorAll('text')].map(t=>({t:t.textContent.trim(), r:t.getBoundingClientRect()})).filter(x=>x.t && x.r.width);
  for(const a of T){ if(a.r.left<R.left-2 || a.r.right>R.right+2) res.push('OUT '+si+': '+a.t.slice(0,50)); }
  for(let i=0;i<T.length;i++) for(let j=i+1;j<T.length;j++){ const a=T[i].r,b=T[j].r; const w=Math.min(a.right,b.right)-Math.max(a.left,b.left), h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
    if(w>2 && h>2 && w*h > 0.25*Math.min(a.width*a.height,b.width*b.height)) res.push('OVL '+si+': '+T[i].t.slice(0,40)+' | '+T[j].t.slice(0,40)); } }); return res; }"""
SET={'beton':'setTyp','stahl':'setStMode','holz':'setHoMode','mauer':'setMwMode','grund':'setGrMode','wasser':'setWbMode','bauph':'setBpMode'}
MODES=[('beton',['balken','unterzug','platte','stuetze','durchstanzen']),('stahl',['traeger','anschluss','fuss','schweiss']),('holz',['bauteil','verbindung','ausklink','sattel','versatz']),('mauer',['druck','teil','keller','schub']),('grund',['flach','setzung','wand','upl','gleit']),('wasser',['druck','schwimm','rohr','gerinne','wehr']),('bauph',['uwert','glaser','schall'])]
async def main():
    out={}
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1300,'height':900})
        await pg.goto(B+'ref.html'); await pg.wait_for_timeout(200)
        pages=await pg.evaluate("Object.entries(FAECHER).flatMap(([f,F])=>Object.entries(F.kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>f+'/'+k+'/'+t)))")
        for L in ('de','en','fr','es'):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(200)
            for key in pages:
                await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(100)
                for r in await pg.evaluate(JS): out.setdefault(('ref',key),{}).setdefault(L,[]).append(r)
        await pg.goto(B+'size.html'); await pg.wait_for_timeout(200)
        pa=await pg.evaluate('Object.keys(PA)'); modes=[(m,x) for m,xs in MODES for x in xs]+[tuple(k.split('/')) for k in pa]
        for L in ('de','en','fr','es'):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(250)
            for mat,m in modes:
                await pg.evaluate(f"setMat('{mat}'); {SET[mat]}('{m}')"); await pg.wait_for_timeout(60)
                for r in await pg.evaluate(JS): out.setdefault(('size',mat+'/'+m),{}).setdefault(L,[]).append(r)
        await br.close()
    n=0
    for k,v in out.items():
        de=len(v.get('de',[]))
        for L in ('en','fr','es'):
            if len(v.get(L,[]))>de:
                n+=1; print(k,L,'DE',de,'→',len(v[L]), v[L][:4])
    print('Stellen:',n)
asyncio.run(main())
