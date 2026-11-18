# Erzeugt k5/katalog.js: die Auswahl (Bereiche und Themen) von Schnittkräfte, Bemessung und Wissen in vier Sprachen, damit das
# Burger-Menü jeder Seite auch die Themen der anderen Module aufklappen kann (18.11.2026). Nach Änderungen an der Auswahl einer Seite
# neu erzeugen:  python3 statiq-tests/katalog_bauen.py  — test_menue_baum.py prüft, dass die Datei zum Stand der Seiten passt.
import os, sys, json, asyncio
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,'..')); B='file://'+ROOT+'/'
LANGS=['de','en','fr','es']
READ="""(mod)=>{ buildPick(); const m=document.getElementById('pick-menu'); const out=[];
  m.querySelectorAll('.pick-group').forEach(g=>{ const n=(g.querySelector('.pick-hn')||{}).textContent.trim(), tag=(g.querySelector('.pick-tag')||{}).textContent||'';
    const it=[]; g.querySelectorAll('.pick-body > *').forEach(e=>{
      if(mod==='calc' && e.matches('.pick-item')) it.push([e.textContent.trim(), 'calc.html#'+e.dataset.k]);
      else if(mod==='size' && e.matches('.pick-item')) it.push([e.textContent.trim(), 'size.html#nw='+e.dataset.mat+'/'+e.dataset.i]);
      else if(mod==='ref' && e.matches('.pick-k')) it.push([(e.textContent||'').replace(/^\\s*[\\d.]+\\s*/,'').trim(), 'ref.html'+e.getAttribute('href')]);   // Wissen: aus anderen Modulen bis zum Kapitel
    });
    out.push({n: n.replace(/\\s*DE$/,'').trim(), i:it}); });
  return out; }"""
async def build():
    K={}
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900})
        for mod in ('calc','size','ref'):
            K[mod]={}
            for L in LANGS:
                await pg.goto(B+mod+'.html'); await pg.evaluate(f"localStorage.clear();localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(700)
                K[mod][L]=await pg.evaluate(READ, mod)
        await br.close()
    return K
def render(K):
    return ('// kragr · Katalog der Auswahl für das Burger-Menü (erzeugt von statiq-tests/katalog_bauen.py — nicht von Hand ändern)\n'
            '// je Modul und Sprache: Bereiche mit Themen [Text, Ziel]. Wissen aus anderen Modulen nur bis zum Kapitel.\n'
            'window.KRAGR_KATALOG='+json.dumps(K, ensure_ascii=False, separators=(',',':'))+';\n')
if __name__=='__main__':
    K=asyncio.run(build())
    open(os.path.join(ROOT,'k5','katalog.js'),'w').write(render(K))
    print('k5/katalog.js:', {m:{L:sum(len(g['i']) for g in K[m][L]) for L in K[m]} for m in K})
