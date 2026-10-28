# Wissen als Lehrbuchseite (ref v0.3.53): ein weißes Blatt je Thema statt Karten, Nummern Fach.Kapitel.Thema (Reihenfolge der
# Seitenleiste), Abschnitte 4.4.3.1 …, Tafeln „Tafel 4.4.3-n“ mit Rahmen, Formeln „(4.4.3-n)“ rechts, Bilder „Bild 4.4.3-n“;
# Fach- und Kapitelübersicht als Inhaltsverzeichnis. Schrift bleibt Figtree.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
PSEUDO="([sel,p])=>[...document.querySelectorAll(sel)].map(e=>getComputedStyle(e,p).content)"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'ref.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
        n=await pg.evaluate("[lbNum('stahlbau'), lbNum('stahlbau','nachweise'), lbNum('stahlbau','nachweise','biegeknicken'), Object.keys(FAECHER).indexOf('stahlbau')+1]")
        check('Nummer Biegeknicken = Fach.Kapitel.Thema', n[2]==f"{n[3]}.4.3" and n[1]==f"{n[3]}.4" and n[0]==str(n[3]), n)
        await pg.evaluate("location.hash='#/stahlbau/nachweise/biegeknicken'"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("""(()=>{ const a=document.querySelector('#main .lb-page'); const c=a.querySelector('.card'); return {art:!!a, num:a.querySelector('.page-title .lb-n').textContent,
          title:a.querySelector('.page-title').textContent, sub:a.querySelector('.page-sub').textContent, cardBg:getComputedStyle(c).backgroundColor, cardSh:getComputedStyle(c).boxShadow, bg:getComputedStyle(a).backgroundColor} })()""")
        N=n[2]
        check('Thema als ein weißes Blatt (article.lb-page)', r['art'] and r['bg']=='rgb(255, 255, 255)', r['bg'])
        check('Titel mit Nummer', r['num']==N and r['title']==N+'Biegeknicken', r['title'])
        check('Oberzeile: EC3 · Stahlbau · 4.4 Nachweise', r['sub']==f"EC3 · Stahlbau · {n[1]} Nachweise", r['sub'])
        check('Abschnitte ohne Kartenoptik (kein Hintergrund, kein Schatten)', r['cardBg'] in ('rgba(0, 0, 0, 0)','transparent') and r['cardSh']=='none', (r['cardBg'], r['cardSh']))
        h=await pg.evaluate(PSEUDO, ['#main .lb-page > .card > .card-title','::before'])
        check('Abschnittsnummern 4.4.3.1, 4.4.3.2, …', len(h)>=3 and all(x==f'"{N}." counter(lbsec)' for x in h), h[:3])
        # Zählerwerte über Text der Pseudoelemente lassen sich nicht direkt lesen: Anzahl und Form prüfen
        t=await pg.evaluate("[...document.querySelectorAll('#main .lb-page .data-table-wrap')].map(e=>[getComputedStyle(e,'::before').content, getComputedStyle(e).borderTopWidth, getComputedStyle(e).borderTopColor])")
        check('Tafeln mit Überschrift „Tafel …“ und schwarzem Rahmen', t and all('Tafel' in x[0] and x[1] in ('1.2px','1px') and x[2]=='rgb(17, 17, 17)' for x in t), t[:2])
        f=await pg.evaluate("[...document.querySelectorAll('#main .lb-page .figure + .figure-cap')].map(e=>getComputedStyle(e,'::before').content)")
        check('Bilder mit „Bild …“ vor der Unterschrift', f and all('Bild' in x for x in f), f[:2])
        await pg.evaluate("location.hash='#/stahlbeton/bemessung/biegung'"); await pg.wait_for_timeout(400)
        e=await pg.evaluate("[...document.querySelectorAll('#main .lb-page .formula-box')].map(e=>[getComputedStyle(e,'::after').content, getComputedStyle(e,'::after').position])")
        check('Formeln: Nummer rechts in Klammern', e and all(x[0].startswith('"(3.5.1-"') and x[0].endswith('")"') and x[1]=='absolute' for x in e), e[:2])
        # Übersichten als Inhaltsverzeichnis
        await pg.evaluate("location.hash='#/holzbau'"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.querySelector('#main .lb-toc .page-title').textContent, [...document.querySelectorAll('#main .lb-toc .nav-list-item .lb-n')].map(e=>e.textContent)]")
        fi=await pg.evaluate("Object.keys(FAECHER).indexOf('holzbau')+1")
        check('Fach-Übersicht: Inhaltsverzeichnis mit 5.1, 5.2 …', r[0]==f'{fi}Holzbau' and r[1][:2]==[f'{fi}.1',f'{fi}.2'], r)
        await pg.evaluate("location.hash='#/holzbau/baustoffe'"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('#main .lb-toc .nav-list-item .lb-n')].map(e=>e.textContent)")
        k=await pg.evaluate("lbNum('holzbau','baustoffe')")
        check('Kapitel-Übersicht: Themen mit Nummern', r and r[0]==k+'.1', r[:3])
        s=await pg.evaluate("[...document.querySelectorAll('#sidebar .tree-k .lb-tn')].length")
        check('Seitenleiste: Kapitel mit Nummern', s>=30, s)
        # Schrift bleibt
        ff=await pg.evaluate("getComputedStyle(document.querySelector('#main .lb-page .page-title')).fontFamily")
        check('Schrift bleibt Figtree', 'Figtree' in ff, ff)
        # Handy: kein Querscroll
        m=await br.new_page(viewport={'width':390,'height':844}); m.on('pageerror', lambda e: errs.append(str(e)))
        for h in ['stahlbau/nachweise/biegeknicken','stahlbeton/bemessung/biegung','baustatik/arbeitssatz/koppeltafel']:
            await m.goto(B+'ref.html#/'+h); await m.wait_for_timeout(400)
            w=await m.evaluate("document.documentElement.scrollWidth")
            check(f'Handy {h.split("/")[-1]}: Seite ohne Querscroll', w<=390, w)
        # Englisch: Nummern bleiben, Titel übersetzt
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.goto(B+'ref.html#/stahlbau/nachweise/biegeknicken'); await pg.reload(); await pg.wait_for_timeout(500)
        t=await pg.evaluate("document.querySelector('#main .page-title').textContent")
        check('EN: Nummer + übersetzter Titel', t.startswith(N) and 'Biegeknicken' not in t, t)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
