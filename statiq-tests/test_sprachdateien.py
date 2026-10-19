# Ladezeit (size v0.5.42, ref v0.3.33): EN/FR/ES liegen in lang/<app>.<sprache>.js und werden nur bei Bedarf geladen.
# Prüft: Deutsch lädt keine Sprachdatei, jede Sprache lädt genau ihre Datei, Seiten deutlich kleiner, Offline-Speicher kennt
# die Dateien, Sprachdateien sind gültig und vollständig. Ohne Playwright: SKIP.
import os, sys, json, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
def lf(app,l):
    t=open(os.path.join(BASE,'lang',f'{app}.{l}.js'),encoding='utf-8').read(); return json.loads(t[t.index('{'):t.rindex('}')+1])

for app,limit in [('size',1_300_000),('ref',1_000_000)]:
    sz=os.path.getsize(os.path.join(BASE,app+'.html'))
    check(f'{app}.html ohne Übersetzungen kleiner als {limit//1000} kB', sz<limit, sz)
    src=open(os.path.join(BASE,app+'.html'),encoding='utf-8').read()
    check(f'{app}.html: kein FR/ES-Wörterbuch mehr in der Seite', '/*FRES*/' not in src and 'const TTX = {};' in src)
    L={l:lf(app,l) for l in ['en','fr','es']}
    en=set(L['en']['ttx']); miss={l:len(set(L[l]['ttx'])-en) for l in ['fr','es']}
    check(f'lang/{app}.*.js gültig; FR/ES ohne Schlüssel, die EN nicht kennt', all(L[l]['ttx'] for l in L) and not any(miss.values()), {l:len(L[l]['ttx']) for l in L})
sw=open(os.path.join(BASE,'sw.js'),encoding='utf-8').read()
check('Offline-Speicher (sw.js) enthält alle sechs Sprachdateien', all(f'lang/{a}.{l}.js' in sw for a in ['size','ref'] for l in ['en','fr','es']))

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for app in ['size','ref']:
            for lang in ['de','en','fr','es']:
                pg=await br.new_page(); pg.on('pageerror', lambda e: errs.append(str(e))); req=[]
                pg.on('request', lambda r: req.append(r.url))
                await pg.goto(U+app+'.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); req.clear(); await pg.reload(); await pg.wait_for_timeout(400)
                got=[r.split('/lang/')[1] for r in req if '/lang/' in r]
                exp=[] if lang=='de' else [f'{app}.{lang}.js']
                n=await pg.evaluate("Object.keys(TTX[LANG]||{}).length")
                check(f'{app} {lang.upper()}: lädt {exp or "keine Sprachdatei"}, Wörterbuch {"leer" if lang=="de" else "gefüllt"}', got==exp and ((n==0)==(lang=='de')), (got, n))
                await pg.close()
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
