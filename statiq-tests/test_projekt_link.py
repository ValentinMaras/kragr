# Link „Meine Projekte“ auf einem Webserver: mit projekt.html → Navigation, ohne projekt.html → Hinweis statt 404 (index, calc, size).
import os, sys, shutil, tempfile, threading, asyncio, functools, http.server, socketserver
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])

def serve(folder):
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    H=functools.partial(Q, directory=folder)
    srv=socketserver.TCPServer(('127.0.0.1',0), H); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv

async def main():
    tmp=tempfile.mkdtemp(); full=os.path.join(tmp,'mit'); part=os.path.join(tmp,'ohne'); os.makedirs(full); os.makedirs(part)
    for f in ['index.html','calc.html','size.html','projekt.html']:
        shutil.copy(os.path.join(BASE,f), full)
        if f!='projekt.html': shutil.copy(os.path.join(BASE,f), part)
    s1=serve(full); s2=serve(part); u1=f'http://127.0.0.1:{s1.server_address[1]}/'; u2=f'http://127.0.0.1:{s2.server_address[1]}/'
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        for page,sel,prep in [('index.html','#saved-card',None),('calc.html','#sf-proj',None),('size.html','.proj-link',None)]:
            await pg.goto(u1+page); await pg.wait_for_timeout(300)
            await pg.evaluate(f"document.querySelector('{sel}').click()"); await pg.wait_for_timeout(700)
            check(f'{page}: mit projekt.html → Seite „Meine Projekte“', pg.url.endswith('projekt.html'), pg.url)
            await pg.goto(u2+page); await pg.wait_for_timeout(300)
            await pg.evaluate(f"document.querySelector('{sel}').click()"); await pg.wait_for_timeout(700)
            msg=await pg.evaluate("(document.getElementById('proj-missing')||{}).textContent||''")
            check(f'{page}: ohne projekt.html → Hinweis statt 404', pg.url.endswith(page) and 'projekt.html' in msg, msg[:80])
        await pg.goto(u2+'index.html'); await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('#saved-card').click()"); await pg.wait_for_timeout(700)
        msg=await pg.evaluate("(document.getElementById('proj-missing')||{}).textContent||''")
        check('Hinweis auf Englisch', msg.startswith('“Projects”'), msg[:60])
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
    s1.shutdown(); s2.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
