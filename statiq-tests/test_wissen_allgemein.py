# Wissen (ref v0.3.51): „Allgemeines“ (Geschichte, Werkstoff/Eigenschaften) in sieben Fachgebieten und das Kapitel
# Betontechnologie in Stahlbeton; erzeugt mit statiq-tools/wissen_allgemein.py. Dazu: keine Themen-Anzahl mehr in der Übersicht (v0.3.50).
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
FACH=['stahlbeton','stahlbau','holzbau','mauerwerk','grundbau','wasserbau','bauphysik']
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'ref.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(500)
        r=await pg.evaluate("FAECHER_KEYS=null, Object.fromEntries(%s.map(f=>[f, Object.keys(FAECHER[f].kapitel)]))" % FACH)
        check('„Allgemeines“ als erstes Kapitel in sieben Fachgebieten', all(r[f][0]=='allgemein' for f in FACH), {f:r[f][:2] for f in FACH})
        check('Stahlbeton: Betontechnologie direkt danach', r['stahlbeton'][:2]==['allgemein','betontechnologie'], r['stahlbeton'][:3])
        keys=await pg.evaluate("Object.keys(ALLG_DATA)")
        check('18 neue Themen mit Inhalt', len(keys)==18 and all(k.split('/')[1] in ('allgemein','betontechnologie') for k in keys), len(keys))
        th=await pg.evaluate("Object.keys(FAECHER.stahlbeton.kapitel.betontechnologie.themen)")
        check('Betontechnologie: Ausgangsstoffe, Hydratation, Frischbeton, Festbeton', th==['ausgangsstoffe','hydratation','frischbeton','festbeton'], th)
        # jede Seite: Inhalt, Links zeigen auf vorhandene Themen
        bad=[]; links=set()
        for k in keys:
            await pg.evaluate(f"location.hash='#/{k}'"); await pg.wait_for_timeout(120)
            t=await pg.inner_text('#main')
            if len(t)<400 or 'undefined' in t: bad.append(k)
            for h in await pg.evaluate("[...document.querySelectorAll('#main a.applink')].map(a=>a.getAttribute('href'))"): links.add(h)
        check('alle 18 Seiten mit Text (über 400 Zeichen, ohne undefined)', not bad, bad)
        miss=await pg.evaluate("(L)=>L.filter(h=>{ const [f,k,t]=h.replace('#/','').split('/'); return !(FAECHER[f] && FAECHER[f].kapitel[k] && FAECHER[f].kapitel[k].themen[t]); })", list(links))
        check('alle Verweise zeigen auf vorhandene Themen', not miss and len(links)>=10, (miss, len(links)))
        # Inhalte (Stichproben)
        await pg.evaluate("location.hash='#/stahlbeton/betontechnologie/hydratation'"); await pg.wait_for_timeout(150); t=await pg.inner_text('#main')
        check('w/z-Wert: Beispiel 176 / 320 = 0,55, Grenzwerte XC1 0,75 und XD3 0,45', '176 / 320 = 0,55' in t and '0,75 bei XC1' in t and '0,45 bei XD3' in t)
        await pg.evaluate("location.hash='#/stahlbeton/betontechnologie/festbeton'"); await pg.wait_for_timeout(150); t=await pg.inner_text('#main')
        # β_cc(7) = exp(0,25·(1 − √(28/7))) = exp(−0,25) = 0,779; f_cm(7) = 0,779 · 38 = 29,6 N/mm²
        check('Festigkeitsentwicklung: β_cc(7) = 0,78, f_cm(7) ≈ 29,6 N/mm²', '= 0,78' in t and '29,6 N/mm²' in t)
        await pg.evaluate("location.hash='#/stahlbeton/betontechnologie/frischbeton'"); await pg.wait_for_timeout(150); t=await pg.inner_text('#main')
        check('Konsistenzklassen F1 bis F6 (≤ 340 … ≥ 630 mm)', 'F1' in t and '≤ 340 mm' in t and 'F6' in t and '≥ 630 mm' in t)
        await pg.evaluate("location.hash='#/stahlbau/allgemein/eigenschaften'"); await pg.wait_for_timeout(150); t=await pg.inner_text('#main')
        check('Stahl: Duktilität erklärt', 'Duktilität' in t and 'fließt' in t)
        # Suche findet die neuen Themen
        await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(150)
        await pg.fill('#side-q', 'Hydratation'); await pg.wait_for_timeout(200)
        vis=await pg.evaluate("[...document.querySelectorAll('#sidebar a')].filter(a=>a.offsetParent).map(a=>a.textContent.trim())")
        check('Seitenleisten-Filter findet „Hydratation und w/z-Wert“', any('Hydratation' in v for v in vis), vis[:4])
        # keine Themen-Anzahl mehr
        await pg.fill('#side-q', ''); await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(200)
        subs=await pg.evaluate("[...document.querySelectorAll('.tile-sub')].map(e=>e.textContent)")
        check('Übersicht: keine „n Themen“ an den Fachgebieten', subs and not any(re.search(r'\d+ Themen', s) for s in subs), subs[:2])
        await pg.evaluate("location.hash='#/stahlbeton'"); await pg.wait_for_timeout(200)
        meta=await pg.evaluate("[...document.querySelectorAll('.nav-list-meta')].map(e=>e.textContent.trim())")
        check('Kapitelliste: nur der Pfeil, keine Anzahl', meta and all(m=='›' for m in meta), meta[:3])
        # Übersetzungen: jeder Text hat EN, FR, ES
        for l in ['en','fr','es']:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{l}')"); await pg.reload(); await pg.wait_for_timeout(300)
            miss=await pg.evaluate("""()=>{ const S=new Set(); const add=x=>{ if(typeof x==='string' && /[A-Za-zÄÖÜäöüß]{4,}/.test(x.replace(/<sub>.*?<[/]sub>/g,'').replace(/<[^>]+>/g,''))) S.add(x); };
              Object.values(ALLG_DATA).forEach(cs=>cs.forEach(c=>{ add(c.t); c.b.forEach(b=>{ if(b[0]==='p'||b[0]==='ex') add(b[1]); if(b[0]==='li') b[1].forEach(add);
                if(b[0]==='tl'){ b[1].forEach(r=>{ add(r[1]); if(!/^\\d+$/.test(r[0])) add(r[0]); }); add(b[2]); add(b[3]); }
                if(b[0]==='tab'){ b[1].forEach(add); b[2].forEach(r=>r.forEach(add)); } if(b[0]==='f'&&b[2]) add(b[2]); if(b[0]==='link') add(b[2]); }); }));
              return [...S].filter(s=>TTX[LANG][s]==null && !/^(CEM [IV]+|FM \\/ BV|LP|VZ \\/ BE)$/.test(s)); }""")
            check(f'{l}: alle Texte übersetzt', not miss, miss[:3])
            await pg.evaluate("location.hash='#/holzbau/allgemein/geschichte'"); await pg.wait_for_timeout(150)
            t=await pg.inner_text('#main')
            check(f'{l}: Holzbau-Geschichte ohne deutsche Sätze', 'Brettschichtholz' not in t and 'Otto Hetzer' in t, t[:80])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
