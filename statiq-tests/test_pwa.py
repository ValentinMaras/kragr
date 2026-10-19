# Statiq als installierbare Web-App: Manifest, Symbole, Service Worker, Offline-Betrieb, Installationshinweis.
import os, sys, json, re, asyncio, threading, functools, http.server, socketserver, struct
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
def png_size(p):
    with open(p,'rb') as f: h=f.read(24)
    return struct.unpack('>II', h[16:24]) if h[:8]==b'\x89PNG\r\n\x1a\n' else None
def serve(folder):
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv=socketserver.TCPServer(('127.0.0.1',0), functools.partial(Q, directory=folder)); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv
PAGES=['index.html','calc.html','size.html','ref.html','projekt.html','rechtliches.html']

async def main():
    m=json.load(open(os.path.join(BASE,'manifest.json'),encoding='utf-8'))
    check('Manifest: Name, start_url, scope, display standalone', m['short_name']=='Muly' and m['start_url']=='./index.html' and m['scope']=='./' and m['display']=='standalone')
    sizes={i['src']:(png_size(os.path.join(BASE,i['src'])), i.get('purpose','any')) for i in m['icons']}
    check('Symbole 192 und 512 px vorhanden, dazu maskable', sizes.get('icons/icon-192.png',[None])[0]==(192,192) and sizes.get('icons/icon-512.png',[None])[0]==(512,512) and ((512,512),'maskable') in sizes.values(), sizes)
    check('apple-touch-icon 180 px und favicon 32 px', png_size(os.path.join(BASE,'icons/apple-touch-icon.png'))==(180,180) and png_size(os.path.join(BASE,'icons/favicon-32.png'))==(32,32))
    src={p:open(os.path.join(BASE,p),encoding='utf-8').read() for p in PAGES}
    miss=[p for p,t in src.items() if not all(x in t for x in ['rel="manifest" href="manifest.json"','rel="apple-touch-icon"','serviceWorker.register(\'sw.js\')'])]
    check('alle sechs Seiten: Manifest, Apple-Symbol, Service-Worker-Registrierung', not miss, miss)
    sw=open(os.path.join(BASE,'sw.js'),encoding='utf-8').read(); files=json.loads(re.search(r'const FILES = (\[.*?\]);',sw).group(1))
    gone=[f for f in files if f!='./' and not os.path.exists(os.path.join(BASE,f))]
    fonts=[f for f in os.listdir(os.path.join(BASE,'fonts')) if f.endswith('.woff2')]
    check(f'Service Worker: alle {len(files)} Dateien im Offline-Speicher existieren, alle Schriften dabei', not gone and all('fonts/'+f in files for f in fonts) and all(p in files for p in PAGES), gone)
    srv=serve(BASE); U=f'http://127.0.0.1:{srv.server_address[1]}/'
    async with async_playwright() as p:
        br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1280,'height':900}); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U+'index.html'); await pg.wait_for_timeout(300)
        ok=await pg.evaluate("navigator.serviceWorker.ready.then(r=>!!r.active).catch(()=>false)")
        check('Service Worker wird registriert und aktiv', ok)
        await pg.wait_for_timeout(800)
        cached=await pg.evaluate("caches.keys().then(ks=>Promise.all(ks.map(k=>caches.open(k).then(c=>c.keys())))).then(a=>a.flat().map(r=>new URL(r.url).pathname))")
        need=['/index.html','/calc.html','/size.html','/ref.html','/projekt.html','/rechtliches.html','/fonts/fonts.css','/manifest.json']
        check('Offline-Speicher enthält Seiten, Schriften und Manifest', all(n in cached for n in need), [n for n in need if n not in cached])
        cdp=await ctx.new_cdp_session(pg)
        try:
            ie=await cdp.send('Page.getInstallabilityErrors'); errs_i=[e.get('errorId') for e in ie.get('installabilityErrors',[])]
            check('Chrome: keine Installations-Hindernisse', not errs_i, errs_i)
        except Exception as e:
            check('Chrome: Installationsprüfung verfügbar', False, str(e)[:80])
        # Offline: alle Seiten laden aus dem Speicher, Rechner funktionieren
        await ctx.set_offline(True)
        bad=[]
        for page in PAGES:
            try:
                await pg.goto(U+page); await pg.wait_for_timeout(300)
                if len(await pg.evaluate("document.body.innerText"))<200: bad.append(page)
            except Exception as e: bad.append(page+': '+str(e)[:40])
        check('offline: alle sechs Seiten öffnen sich', not bad, bad)
        await pg.goto(U+'calc.html'); await pg.wait_for_timeout(400)
        t=await pg.evaluate("document.body.innerText")
        check('offline: calc rechnet (Auflagerkraft 17,50 kN)', '17.50' in t or '17,50' in t)
        await pg.goto(U+'size.html'); await pg.wait_for_timeout(400)
        check('offline: size rechnet und zeigt das Ergebnis', 'Nachweise' in await pg.evaluate("document.getElementById('summary').innerText"))
        fam=await pg.evaluate("document.fonts.ready.then(()=>[...document.fonts].some(f=>f.family.replace(/\"/g,'')==='Inter' && f.status==='loaded'))")
        check('offline: Schrift Inter aus dem Speicher geladen', fam)
        await ctx.set_offline(False)
        # Installationshinweis: Desktop ohne Angebot verborgen, iPhone mit Anleitung
        await pg.goto(U+'index.html'); await pg.wait_for_timeout(300)
        check('Startseite: Installationskarte ohne Installationsangebot verborgen', await pg.evaluate("document.getElementById('install').hidden"))
        await pg.evaluate("window.dispatchEvent(Object.assign(new Event('beforeinstallprompt'),{prompt(){window.__prompted=true}, userChoice:Promise.resolve({outcome:'accepted'})}))")
        vis=await pg.evaluate("[document.getElementById('install').hidden, document.getElementById('install-btn').hidden]")
        await pg.click('#install-btn'); await pg.wait_for_timeout(100)
        check('Chrome/Android: Karte mit Knopf „Installieren“, Klick öffnet den Dialog', vis==[False,False] and await pg.evaluate("window.__prompted===true"), vis)
        ios=await br.new_context(user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1', viewport={'width':390,'height':844})
        ip=await ios.new_page(); await ip.goto(U+'index.html'); await ip.evaluate("localStorage.setItem('statiq-lang','de')"); await ip.reload(); await ip.wait_for_timeout(300)
        r=await ip.evaluate("[document.getElementById('install').hidden, document.getElementById('install-btn').hidden, document.getElementById('install-sub').textContent]")
        check('iPhone: Karte mit Anleitung „Zum Home-Bildschirm“, ohne Knopf', r[0]==False and r[1]==True and 'Home-Bildschirm' in r[2], r)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
    srv.shutdown()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
