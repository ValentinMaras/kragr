# statiq·ref v0.3.21: Jeder feste Text im Code (tt('…') und kurze _L`…`-Vorlagen) hat eine englische Übersetzung —
# auch Fehlermeldungen und Zweige, die mit Standardwerten nicht erscheinen. Dazu Stichproben DE/EN im Browser.
import os, sys, re, json, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
s=open(BASE+'/ref.html',encoding='utf-8').read()
lf=open(BASE+'/lang/ref.en.js',encoding='utf-8').read(); T=json.loads(lf[lf.index('{'):lf.rindex('}')+1])['ttx']   # Sprachdatei
code=s[s.index('const TTX = {}'):]
miss=[]
for m in re.finditer(r"\btt\('((?:[^'\\]|\\.)*)'\)",code):
    k=m.group(1).replace("\\'","'")
    if re.search('[A-Za-zÄÖÜäöüß]{3}',k) and k not in T: miss.append(k)
def tpl(i):  # _L`…` ab Index i → Schlüssel mit {} für Platzhalter
    p=i; parts=[]; cur=''
    while code[p]!='`':
        if code[p]=='\\': cur+=code[p:p+2]; p+=2; continue
        if code.startswith('${',p):
            d=1; p+=2
            while d:
                c=code[p]
                if c=='{': d+=1
                elif c=='}': d-=1
                elif c=='`':
                    q=p+1; dd=0
                    while not (code[q]=='`' and dd==0):
                        if code.startswith('${',q): dd+=1; q+=2; continue
                        if code[q]=='}' and dd: dd-=1
                        q+=1
                    p=q
                p+=1
            parts.append(cur); cur=''; continue
        cur+=code[p]; p+=1
    parts.append(cur); return '{}'.join(parts)
nL=0
for m in re.finditer(r'_L`',code):
    k=tpl(m.end())
    if '\n' in k or k.startswith(('<div class="data-table','<a href')) or not re.search('[A-Za-zÄÖÜäöüß]{3}',k): continue   # Seitenvorlagen werden im DOM übersetzt
    nL+=1
    if k not in T: miss.append(k)
check(f'Code: alle tt()-Texte und {nL} _L-Vorlagen übersetzt', not miss, miss[:5])
if os.environ.get('SHOWMISS'): print('\n'.join(miss))
bad=[k for k,v in T.items() if len(re.findall(r'\{\}',k))!=len(re.findall(r'\{\}',v)) and not re.findall(r'\{\d+\}',v) and '<!--{}-->' not in v]
check('Platzhalter {} in Schlüssel und Übersetzung gleich viele', not bad, bad[:3])
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Browser-Teil (Playwright fehlt)'); print('FAILS:', fails); sys.exit(1 if fails else 0)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+BASE+'/ref.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        async def run(hash, js):
            await pg.evaluate(f"location.hash='#/{hash}'"); await pg.wait_for_timeout(150)
            await pg.evaluate(js); await pg.wait_for_timeout(80); return await pg.inner_text('#main')
        GK="(()=>{const s=(i,v)=>{const e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event(e.tagName==='SELECT'?'change':'input',{bubbles:true}));}; s('gk-h','5'); s('gk-n','2'); s('gk-a','100'); s('gk-f','0');})()"
        t=await run('bauphysik/brand/gebaeudeklassen', GK)
        check('DE: Gebäudeklasse 2 Nutzungseinheiten, nicht freistehend', '2 Nutzungseinheiten' in t and 'nicht freistehend: GK 2' in t)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(250)
        t=await run('bauphysik/brand/gebaeudeklassen', GK)
        check('EN: building class 2 units, not detached', '2 units' in t and 'not detached: BC 2' in t, t[-200:])
        t=await run('bauphysik/brand/gebaeudeklassen', "(()=>{const e=document.getElementById('gk-n'); e.value='1'; e.dispatchEvent(new Event('input',{bubbles:true}));})()")
        check('EN: Einzahl „1 unit“', '1 unit ' in t, '')
        t=await run('holzbau/gzt/knicken', "")
        check('EN: Holz-Druckstab Material/Querschnitt englisch', 'Material C24, SC 1, load duration' in t and 'Cross-section' in t and 'Baustoff' not in t)
        t=await run('grundbau/boden/klassifikation', "(()=>{const e=[...document.querySelectorAll('#main input')][0]; e.value='-5'; e.dispatchEvent(new Event('input',{bubbles:true}));})()")
        check('EN: Fehlermeldung bei ungültiger Eingabe englisch', 'Bitte' not in t, '')
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
