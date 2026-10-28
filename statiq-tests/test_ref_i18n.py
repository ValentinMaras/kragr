# statiq·ref v0.3.21 Sprachen: Navigation in Englisch, übersetzte Fächer ohne deutsche Reste (auch nach Eingaben),
# Deutsch unverändert, Suche auf Englisch, seit v0.3.21 alle 10 Fächer englisch (kein „DE“-Hinweis mehr). Ohne Playwright: SKIP.
import os, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
HTML='file://'+BASE+'/ref.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
GER=re.compile(r'\w*[äöüÄÖÜß]\w*|\b(und|der|die|das|mit|nicht|oder|für|ein|eine|bei|aus|nach|ist|sind|wird|im|am|zum|zur|vom|oben|unten|rechts|Feld|Felder|Last|Lager|Träger|Stütze|Wand|Platte|Balken|Querschnitt|Kraft|Knoten|Stab|Gurt|Pfosten|Riegel|Seite|Höhe|Breite|Dicke|Länge|Beispiel|Schnitt|Fall)\b')
OK_WORDS=['Der Eisenbetonbau','Eisenbetonbau','Eisenbeton','Stahlbeton','Mörsch','Erdbaumechanik','Müller-Breslau','Dünnformat']   # Eigennamen/Fachbegriffe ('links' = engl. Bügel, daher nicht im Muster)
TEXTS=r"""(sel) => { const out=[]; document.querySelectorAll(sel).forEach(R=>{ const w=document.createTreeWalker(R, NodeFilter.SHOW_TEXT);
  while(w.nextNode()){ const n=w.currentNode, p=n.parentElement; if(!p || ['SCRIPT','STYLE','SUB','SUP'].includes(p.tagName.toUpperCase())) continue;
    const t=n.textContent.trim(); if(t && /[A-Za-zÄÖÜäöüß]{3,}/.test(t)) out.push(t); }
  R.querySelectorAll('[placeholder],[title],[aria-label]').forEach(e=>['placeholder','title','aria-label'].forEach(a=>{ const v=e.getAttribute(a); if(v) out.push(v); })); }); return out; }"""
def german(t):
    for w in OK_WORDS: t=t.replace(w,'')
    return any(len(m.group(0))>=2 for m in GER.finditer(t))   # einzelnes ü/Ö als Formelzeichen ist erlaubt
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1300,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        # Deutsch unverändert
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(250)
        await pg.evaluate("location.hash='#/baustatik/balkentafeln/einfeld'"); await pg.wait_for_timeout(200)
        t=await pg.inner_text('#main')
        check('DE: Seite Einfeldträger deutsch', 'Einfeldträger' in t and 'Festlager' in t and 'Simply supported' not in t)
        check('DE: kein Hinweis „DE“ in der Seitenleiste', await pg.evaluate("!document.querySelector('.tree-de')"))
        check('DE: Wörterbuch wird nicht angewandt', await pg.evaluate("tt('Schnee')==='Schnee' && _L`Fall ${3}`==='Fall 3'"))
        # Englisch
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(250)
        await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(150)
        side=await pg.evaluate(TEXTS, '#sidebar')
        bad=[x for x in side if german(x) and x!='DE']
        check('EN: Seitenleiste (alle 132 Themen) englisch', not bad, bad[:5])
        check('EN: Startseite englisch', 'Reference' in await pg.inner_text('#main') and 'Open a subject' in await pg.inner_text('#main'))
        done=await pg.evaluate("REF_EN_DONE")
        nde=await pg.evaluate("document.querySelectorAll('.tree-de').length")
        check('EN: alle 10 Fächer übersetzt, kein Hinweis „DE“', len(done)==10 and nde==0, (len(done),nde))
        for fach in done:
            pages=await pg.evaluate(f"Object.entries(FAECHER['{fach}'].kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>'{fach}/'+k+'/'+t))")
            left={}
            for key in pages:
                await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(120)
                for x in await pg.evaluate(TEXTS, '#main, #toc, #breadcrumb'):
                    if german(x): left.setdefault(x[:70], key)
                # Eingaben ändern: Ergebnisse bleiben englisch
                await pg.evaluate("""[...document.querySelectorAll('#main input[type=number]')].slice(0,10).forEach(e=>{ e.value=(+e.value||1)*1.37; e.dispatchEvent(new Event('input',{bubbles:true})); })""")
                await pg.evaluate("""[...document.querySelectorAll('#main select')].forEach(e=>{ e.selectedIndex=e.options.length-1; e.dispatchEvent(new Event('change',{bubbles:true})); })""")
                await pg.wait_for_timeout(60)
                for x in await pg.evaluate(TEXTS, '#main'):
                    if german(x): left.setdefault(x[:70], key+' (Eingabe)')
            check(f'EN: {fach} — {len(pages)} Themen ohne deutsche Reste', not left, list(left.items())[:4])
        await pg.evaluate("location.hash='#/baustatik/balkentafeln/einfeld'"); await pg.wait_for_timeout(150)
        t=await pg.inner_text('#main')
        check('EN: Dezimalpunkt im Inhalt', '31.25 kNm' in t and not re.search(r'\d,\d\d kNm', t))
        await pg.evaluate("location.hash='#/lastannahmen/lasten/wind'"); await pg.wait_for_timeout(150)
        check('EN: Inhaltsverzeichnis englisch', 'On this page' in await pg.evaluate("document.getElementById('toc').textContent"))
        await pg.evaluate("location.hash='#/stahlbau/werkstoff/stahlsorten'"); await pg.wait_for_timeout(150)
        check('EN: Stahlbau ohne Hinweis „noch nicht übersetzt“', 'not been translated yet' not in await pg.inner_text('#main'))
        await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(150)
        await pg.fill('#search','snow'); await pg.wait_for_timeout(200)
        r=await pg.inner_text('#search-results')
        check('EN: Suche findet englische Inhalte („snow“)', 'Snow' in r, r[:80])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
