# Marke kragr (Oktober 2026, vorher Muly/Statiq): kein sichtbares „Statiq“ oder „Muly“ mehr in allen Seiten und Sprachen, Logo „krag“ +
# Kragarm-r (blau, Last an der Spitze), Manifest und App-Symbole (weiß, schwarzes Kragarm-r mit Pfeil), alte Daten bleiben lesbar.
import os, sys, re, json, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])

ALT=re.compile(r'statiq(?!u)|muly', re.I)   # „statique“ (franz.) ist erlaubt
PAGES=['index.html','calc.html','size.html','ref.html','projekt.html','rechtliches.html']

m=json.load(open(os.path.join(BASE,'manifest.json'),encoding='utf-8'))
check('Manifest: Name und Kurzname kragr', m['short_name']=='kragr' and m['name'].startswith('kragr'), (m['name'],m['short_name']))
sw=open(os.path.join(BASE,'sw.js'),encoding='utf-8').read()
check('Service Worker: neue Version, alte Speicher werden weiter aufgeräumt', "VERSION = 'statiq-2026-10-15-2'" not in sw and "k.startsWith('statiq-')" in sw)
src={p:open(os.path.join(BASE,p),encoding='utf-8').read() for p in PAGES}
for p in PAGES:
    check(f'{p}: Startbildschirm-Name kragr', '<meta name="apple-mobile-web-app-title" content="kragr" />' in src[p])
check('calc Bericht: Marke kragr im Schriftfeld und in der Fußzeile', "const REP_BRAND = 'kragr';" in src['calc.html'] and '${REP_BRAND} · ${kmod(\'calc\')} · ' in src['calc.html'])
check('size Bericht: Kopf „kragr · Bemessung“', 'kragr · ${kmod(\'size\')} v${SIZE_VERSION}' in src['size.html'])
check('projekt: Export als .kragr.json, alte .muly- und .statiq-Dateien weiter ladbar', "'.kragr.json'" in src['projekt.html'] and '.statiq,.muly,.kragr' in src['projekt.html'] and "d.statiq!=='projekt'" in src['projekt.html'])
check('Spracheinstellung bleibt unter dem alten Schlüssel (keine Daten verloren)', all("'statiq-lang'" in src[p] for p in ['index.html','projekt.html']))

try:
    from PIL import Image
    i512=Image.open(os.path.join(BASE,'icons/icon-512.png')).convert('RGBA'); mk=Image.open(os.path.join(BASE,'icons/icon-maskable-512.png')).convert('RGBA')
    ap=Image.open(os.path.join(BASE,'icons/apple-touch-icon.png')).convert('RGBA')
    white=lambda c: c[0]>250 and c[1]>250 and c[2]>250 and c[3]==255
    black=lambda c: c[0]<20 and c[1]<20 and c[2]<20 and c[3]==255
    check('App-Symbol: weiß, Ecken rund (transparent), schwarzes Kragarm-r in der Mitte', white(i512.getpixel((40,256))) and i512.getpixel((2,2))[3]==0 and black(i512.getpixel((170,330))) and black(i512.getpixel((330,240))))
    check('App-Symbol maskable und Apple: vollflächig weiß, Zeichen in der sicheren Zone', white(mk.getpixel((3,3))) and white(ap.getpixel((2,2)))
          and not any(black(mk.getpixel((x,y))) for x in range(0,512,4) for y in range(0,512,4) if (x-256)**2+(y-256)**2>205**2))
    check('App-Symbole in den richtigen Größen', i512.size==(512,512) and mk.size==(512,512) and ap.size==(180,180) and Image.open(os.path.join(BASE,'icons/favicon-32.png')).size==(32,32))
except ImportError:
    print('SKIP Pillow fehlt')

try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); print('fertig'); sys.exit(1 if fails else 0)

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        bad=[]
        for lang in ['de','en','fr','es']:
            for pgf in PAGES:
                await pg.goto(U+pgf); await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(250)
                t=await pg.title()+' '+await pg.evaluate("document.body.innerText")
                if pgf=='ref.html':
                    await pg.goto(U+'ref.html#/baustatik/querschnitte/euler'); await pg.reload(); await pg.wait_for_timeout(150)
                    t+=' '+await pg.title()+' '+await pg.evaluate("document.body.innerText")
                h=ALT.findall(t)
                if h: bad.append(f'{lang}/{pgf}: '+', '.join(h[:3]))
        check('kein sichtbares „Statiq“ in 6 Seiten × 4 Sprachen (Titel und Text)', not bad, bad[:4])
        await pg.goto(U+'index.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(300)
        R="(sel)=>{const l=document.querySelector(sel), s=l&&l.querySelector('svg.logo-r'); if(!l||!s) return null; const r=s.getBoundingClientRect(), fs=parseFloat(getComputedStyle(l).fontSize); return [l.textContent.trim(), s.querySelectorAll('rect').length, s.querySelector('rect').getAttribute('fill'), +(r.height/fs).toFixed(2), l.getAttribute('href')]}"
        r=await pg.evaluate(R, '#headline')
        check('Startseite: Schriftzug „krag“ + blaues Kragarm-r mit Last', r and r[0]=='krag' and r[1]==2 and r[2]=='#5468ad' and 0.9<r[3]<1.2, r)
        xh=await pg.evaluate("""(()=>{ const h=document.getElementById('headline'), cs=getComputedStyle(h), c=document.createElement('canvas').getContext('2d'); c.font=cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;
          const fs=parseFloat(cs.fontSize), st=h.querySelector('svg rect').getBoundingClientRect(); return [+(c.measureText('g').actualBoundingBoxAscent/fs).toFixed(3), +((st.bottom-st.top)/fs).toFixed(3)]; })()""")
        check('Kragarm-r endet auf der Oberkante des g, nur der Pfeil ragt darüber', 0<=xh[0]-xh[1]<0.01, xh)
        fb=await pg.evaluate("""(()=>{ const h=document.getElementById('headline'); h.style.fontFamily='Arial'; const cs=getComputedStyle(h), c=document.createElement('canvas').getContext('2d'); c.font=cs.fontWeight+' '+cs.fontSize+' Arial';
          const fs=parseFloat(cs.fontSize), st=h.querySelector('svg rect').getBoundingClientRect(), r=[+(c.measureText('g').actualBoundingBoxAscent/fs).toFixed(3), +((st.bottom-st.top)/fs).toFixed(3)]; h.style.fontFamily=''; return r; })()""")
        check('auch mit Ersatzschrift (Arial): Kragarm nicht höher als das g', 0<=fb[0]-fb[1]<0.015, fb)
        for pgf in ['calc.html','size.html','ref.html','projekt.html','rechtliches.html']:
            await pg.goto(U+pgf); await pg.wait_for_timeout(200)
            r=await pg.evaluate(R, '.logo')
            check(f'{pgf}: Logo „krag“ + Kragarm-r, führt zur Startseite', r and r[0]=='krag' and r[1]==2 and r[4]=='index.html', r)
        await pg.goto(U+'calc.html'); await pg.wait_for_timeout(300)
        v=await pg.evaluate("[document.querySelector('.version').textContent, STATIQ_VERSION]")
        check('calc: Versionsanzeige im Kopf passt zur Programmversion', v[0]=='v'+v[1], v)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
