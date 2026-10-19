# Marke Muly (Oktober 2026): kein sichtbares „Statiq“ mehr in allen Seiten und Sprachen, Logo „muly“ mit μ als Exponent,
# Manifest und App-Symbole, alte Daten (Spracheinstellung, Projektdateien) bleiben lesbar.
import os, sys, re, json, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])

ALT=re.compile(r'statiq(?!u)', re.I)   # „statique“ (franz.) ist erlaubt
PAGES=['index.html','calc.html','size.html','ref.html','projekt.html','rechtliches.html']

m=json.load(open(os.path.join(BASE,'manifest.json'),encoding='utf-8'))
check('Manifest: Name und Kurzname Muly', m['short_name']=='Muly' and m['name'].startswith('Muly'), (m['name'],m['short_name']))
sw=open(os.path.join(BASE,'sw.js'),encoding='utf-8').read()
check('Service Worker: neue Version, alte Speicher werden weiter aufgeräumt', "VERSION = 'statiq-2026-10-15-2'" not in sw and "k.startsWith('statiq-')" in sw)
src={p:open(os.path.join(BASE,p),encoding='utf-8').read() for p in PAGES}
for p in PAGES:
    check(f'{p}: Startbildschirm-Name Muly', '<meta name="apple-mobile-web-app-title" content="Muly" />' in src[p])
check('calc Bericht: Fußzeile muly·calc', 'muly·calc · ' in src['calc.html'] and 'statiq·calc' not in src['calc.html'])
check('size Bericht: Kopf Muly·size', 'Muly·size v${SIZE_VERSION}' in src['size.html'])
check('projekt: Export als .muly.json, alte .statiq-Dateien weiter ladbar', "'.muly.json'" in src['projekt.html'] and '.statiq,' in src['projekt.html'] and "d.statiq!=='projekt'" in src['projekt.html'])
check('Spracheinstellung bleibt unter dem alten Schlüssel (keine Daten verloren)', all("'statiq-lang'" in src[p] for p in ['index.html','projekt.html']))

try:
    from PIL import Image
    i512=Image.open(os.path.join(BASE,'icons/icon-512.png')).convert('RGBA'); mk=Image.open(os.path.join(BASE,'icons/icon-maskable-512.png')).convert('RGBA')
    ap=Image.open(os.path.join(BASE,'icons/apple-touch-icon.png')).convert('RGBA')
    blue=lambda c: abs(c[0]-0x25)<6 and abs(c[1]-0x63)<6 and abs(c[2]-0xeb)<6 and c[3]==255
    check('App-Symbol D: blaues Quadrat, Ecken rund (transparent)', blue(i512.getpixel((40,256))) and i512.getpixel((2,2))[3]==0)
    check('App-Symbol maskable und Apple: vollflächig blau, Schrift in der Mitte weiß',
          blue(mk.getpixel((3,3))) and blue(ap.getpixel((2,2))) and any(mk.getpixel((x,y))[0]>240 for x in range(150,360,4) for y in range(200,320,4)))
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
        r=await pg.evaluate("(()=>{const h=document.getElementById('headline'), s=h.querySelector('.iq'); const cs=getComputedStyle(s); return [h.textContent, cs.color, cs.verticalAlign, parseFloat(cs.fontSize)/parseFloat(getComputedStyle(h).fontSize)]})()")
        check('Startseite: Schriftzug „muly“ mit blauem μ als Exponent', r[0]=='mulyμ' and r[1]=='rgb(37, 99, 235)' and r[2]!='baseline' and 0.35<r[3]<0.55, r)
        for pgf in ['calc.html','size.html','ref.html','projekt.html','rechtliches.html']:
            await pg.goto(U+pgf); await pg.wait_for_timeout(200)
            r=await pg.evaluate("(()=>{const l=document.querySelector('.logo'), s=l&&l.querySelector('span'); return l? [l.textContent.trim(), getComputedStyle(s).verticalAlign, l.getAttribute('href')]:null})()")
            check(f'{pgf}: Logo „muly“ + μ hochgestellt, führt zur Startseite', r and r[0]=='mulyμ' and r[1]!='baseline' and r[2]=='index.html', r)
        await pg.goto(U+'calc.html'); await pg.wait_for_timeout(300)
        v=await pg.evaluate("[document.querySelector('.version').textContent, STATIQ_VERSION]")
        check('calc: Versionsanzeige im Kopf passt zur Programmversion', v[0]=='v'+v[1], v)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
