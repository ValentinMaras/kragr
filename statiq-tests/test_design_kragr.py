# kragr-Design, Stufe 1 (calc v0.9.0 · size v0.6.0): Farben, Schrift, Kopfzeile, Ergebnisleiste nach der Design-Übergabe
# vom 21.10.2026. Schrift Figtree + JetBrains Mono lokal, Akzent #5468ad, Kopfzeile Logo · calc size ref · Projekte, Theme,
# Sprache; Version im Projekt-Fenster. Ohne Playwright nur die Dateiprüfungen.
import os, sys, re, glob, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
pages=sorted(glob.glob(os.path.join(BASE,'*.html'))); src={os.path.basename(p):open(p,encoding='utf-8').read() for p in pages}
old=[(n,w) for n,s in src.items() for w in ['DM Sans','DM Mono','Bebas Neue',"'Inter'",'#2563eb','#1d4ed8','37,99,235','37, 99, 235'] if w in s]
check('keine alten Schriften (DM Sans/Mono, Bebas, Inter als Textschrift) und kein altes Blau mehr', not old, old)
check('keine Schrift von Google oder anderen Servern', not any('fonts.googleapis' in s or 'fonts.gstatic' in s for s in src.values()))
css=open(os.path.join(BASE,'fonts','fonts.css')).read(); fl=[f for f in os.listdir(os.path.join(BASE,'fonts')) if f.endswith('.woff2')]
check('fonts.css: Figtree und JetBrains Mono, jede Datei vorhanden', "font-family: 'Figtree'" in css and "font-family: 'JetBrains Mono'" in css and all(os.path.exists(os.path.join(BASE,'fonts',u)) for u in re.findall(r'url\(([^)]+)\)',css)))
sw=open(os.path.join(BASE,'sw.js')).read()
check('Offline-Speicher enthält genau die vorhandenen Schriftdateien', sorted(re.findall(r'"fonts/([^"]+\.woff2)"',sw))==sorted(fl), fl)
check('Lizenztexte Figtree und JetBrains Mono liegen bei', all(os.path.exists(os.path.join(BASE,'fonts',f'LICENSE-{n}.txt')) for n in ['Figtree','JetBrainsMono']))
check('calc und size: gleicher Design-Block', src['calc.html'].split('<style data-kragr>')[1].split('</style>')[0]==src['size.html'].split('<style data-kragr>')[1].split('</style>')[0])
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(1 if fails else 0)
HDR="""(()=>{const h=document.querySelector('.app-header'),k=[...h.children].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.id||e.className||e.tagName),b=document.getElementById('k5-burger').getBoundingClientRect(),
 v=getComputedStyle(document.querySelector('.app-header .version')).display, tools=h.querySelector('.hdr-tools');
 return {k, w:Math.round(b.width), hb:Math.round(b.height), ver:v, tools:tools?getComputedStyle(tools).display:'-', txt:document.getElementById('k5-burger').innerText.trim(),
  font:getComputedStyle(document.body).fontFamily, acc:getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(), h:Math.round(h.offsetHeight), sw:document.documentElement.scrollWidth}})()"""   # k5: Kopfzeile Logo · Menü
MENU="(()=>{ document.getElementById('k5-burger').click(); const m=document.getElementById('k5-menu'), r=[m.querySelectorAll('.k5-mod').length, !!m.querySelector('[data-mod=projekt]'), m.querySelectorAll('#k5-theme button').length, m.querySelectorAll('#k5-lang button').length]; document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'})); return r; })()"
FON="document.fonts.ready.then(()=>[...new Set([...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family.split(String.fromCharCode(34)).join('')))].sort())"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')")
        for f in ['calc','size']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(700); r=await pg.evaluate(HDR)
            check(f'{f} Handy: Kopfzeile eine Zeile Logo · Menü (58 px), alte Werkzeuge verborgen, kein Querscrollen', r['k'][0]=='logo' and r['k'][-1]=='k5-burger' and r['h']==58 and r['tools']=='none' and r['sw']<=390, r)
            mn=await pg.evaluate(MENU); await pg.wait_for_timeout(100)
            check(f'{f} Handy: Menüknopf 44 × 44; im Menü drei Module + Projekte, Erscheinungsbild, Sprache', r['w']==44 and r['hb']==44 and r['ver']=='none' and mn==[4,True,3,4], (r, mn))
            check(f'{f}: Schrift Figtree, Akzent #5468ad', r['font'].startswith('Figtree') and r['acc']=='#5468ad', r)
            fo=await pg.evaluate(FON); check(f'{f}: Figtree und JetBrains Mono geladen', 'Figtree' in fo and 'JetBrains Mono' in fo, fo)
            v=await pg.inner_text('#k-verfoot')
            want='kragr · Schnittkräfte v'+await pg.evaluate("typeof STATIQ_VERSION!=='undefined'?STATIQ_VERSION:''") if f=='calc' else 'kragr · Bemessung v'+await pg.evaluate("SIZE_VERSION")
            check(f'{f}: Version unten auf der Seite (Handy)', v==want and v.startswith(('kragr · Schnittkräfte v0.11.','kragr · Bemessung v0.7.')) and await pg.is_visible('#k-verfoot'), v)
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate("[localStorage.getItem('statiq-projekt'), document.getElementById('k-pmbar').hidden]"); check('calc Handy: als Rechner ohne Projektbezug (kein Projekt, keine Projektzeile)', r==[None,True], r)
        await pg.close()
        pg=await br.new_page(viewport={'width':1280,'height':800}); pg.on('pageerror', lambda e: errs.append(str(e)))
        for f in ['calc','size']:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(600); r=await pg.evaluate(HDR)
            check(f'{f} Rechner: Menüknopf mit Text „Menü“, Höhe 44', r['w']>80 and r['hb']==44 and r['txt'] in ('Menü','Menu'), r)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
