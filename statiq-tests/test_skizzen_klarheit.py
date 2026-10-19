# Skizzen nachvollziehbar: keine Beschriftung ragt aus der Skizze, fachliche Korrekturen der Skizzen-Durchsicht (Oktober 2026).
import os, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); U='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])

# Text, der über den Rand der eigenen Skizze hinausragt (in Pixeln des Bildschirms, 1,5 px Toleranz)
OVER = """(root)=>{ const out=[]; root.querySelectorAll('svg').forEach(svg=>{ const b=svg.getBoundingClientRect(); if(b.width<60||b.height<40) return;
  if(svg.closest('.modal-overlay')) return;
  svg.querySelectorAll('text').forEach(t=>{ const r=t.getBoundingClientRect(); if(!r.width||!(t.textContent||'').trim()) return;
    if(r.left<b.left-1.5||r.right>b.right+1.5||r.top<b.top-1.5||r.bottom>b.bottom+1.5) out.push((t.textContent||'').trim().slice(0,30)); }); }); return out; }"""

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U+'ref.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload()
        routes=await pg.evaluate("Object.entries(FAECHER).flatMap(([f,F])=>Object.entries(F.kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>f+'/'+k+'/'+t)))")
        bad=[]; n=0
        for r in routes:
            await pg.goto(U+'ref.html#/'+r); await pg.reload(); await pg.wait_for_timeout(60)
            o=await pg.evaluate(OVER, await pg.query_selector('#main')) if await pg.query_selector('#main') else []
            n+=await pg.evaluate("document.querySelectorAll('#main svg').length")
            if o: bad.append(r+': '+', '.join(o[:3]))
        check(f'ref: in {len(routes)} Themen ({n} SVG) ragt keine Beschriftung aus der Skizze', not bad, bad[:4])
        # Euler Fall 3: unten eingespannt (Linie startet senkrecht), oben gelenkig
        await pg.goto(U+'ref.html#/baustatik/querschnitte/euler'); await pg.reload(); await pg.wait_for_timeout(80)
        src=open(os.path.join(BASE,'ref.html'),encoding='utf-8').read()
        check('ref Euler Fall 3: Knickfigur unten eingespannt (x = s), Lager oben verschieblich', "const raw3=s=>{ const x=s;" in src and 'rotate(-90)">${supRoll(0,0)}' in src)
        check('ref Biegung: Randstauchung ε_cu2 (nicht ε_c2) = 3,5 ‰', "'ε_cu2 = 3,5 ‰'" in src and "'ε_c2 = 3,5 ‰'" not in src)
        await pg.goto(U+'ref.html#/mathematik/geometrie/trigonometrie'); await pg.reload(); await pg.wait_for_timeout(80)
        t=await pg.evaluate("document.getElementById('main').innerText")
        check('ref Trigonometrie: a gegenüber α wie bei Pythagoras (sin α = a / c)', 'sin α = a / c' in t and 'c² = a² + b²' in t)

        # calc: Längenangaben sichtbar, Momente mit baustatischem Vorzeichen, Feldmomente am Durchlaufträger
        await pg.goto(U+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(400)
        res={}
        for tab in ['beam','cantilever','cont','frame']:
            await pg.evaluate(f"showTab('{tab}')"); await pg.wait_for_timeout(450)
            res[tab]=await pg.evaluate(OVER, await pg.query_selector('#tab-'+tab))
        check('calc: keine Beschriftung ragt aus System- oder Schnittgrößenskizze (alle vier Systeme)', not any(res.values()), res)
        await pg.evaluate("showTab('beam')"); await pg.wait_for_timeout(400)
        lb=await pg.evaluate("[...document.querySelectorAll('#diag-svg-beam text')].map(t=>t.textContent)")
        await pg.evaluate("showTab('cantilever')"); await pg.wait_for_timeout(400)
        lc=await pg.evaluate("[...document.querySelectorAll('#diag-svg-cant text')].map(t=>t.textContent)")
        await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(400)
        ld=await pg.evaluate("[...document.querySelectorAll('#diag-svg-cont text')].map(t=>t.textContent)")
        check('calc Einfeldträger: Feldmoment positiv (28.1), Einheit M [kNm]', '28.1' in lb and '-28.1' not in lb and 'M [kNm]' in lb, lb)
        check('calc Kragarm: Einspannmoment negativ (-37.5)', '-37.5' in lc, lc)
        check('calc Durchlaufträger: Stützmoment -15.6 und beide Feldmomente 8.8 beschriftet', '-15.6' in ld and ld.count('8.8')>=2, ld)

        # size: alle Modi, keine Beschriftung außerhalb, fachliche Stichproben
        await pg.goto(U+'size.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(300)
        SM={'beton':'seg-typ','stahl':'seg-st','holz':'seg-ho','grund':'seg-gr','mauer':'seg-mw','wasser':'seg-wb','bauph':'seg-bp'}
        bad=[]; n=0
        for m,sid in SM.items():
            k=await pg.evaluate(f"document.querySelectorAll('#{sid} button').length")
            for i in range(k):
                await pg.evaluate(f"setMat('{m}'); document.querySelectorAll('#{sid} button')[{i}].click()"); await pg.wait_for_timeout(200)
                await pg.evaluate("document.querySelectorAll('#details .card.closed').forEach(c=>c.classList.remove('closed'))"); await pg.wait_for_timeout(40)
                o=await pg.evaluate(OVER, await pg.query_selector('main')); n+=1
                if o: bad.append(f'{m}/{i}: '+', '.join(o[:3]))
        check(f'size: in {n} Modi ragt keine Beschriftung aus einer Skizze', not bad, bad[:4])
        ssrc=open(os.path.join(BASE,'size.html'),encoding='utf-8').read()
        check('size Zugstab: Nettoquerschnitt an der lastnahen Lochreihe', 'const xn=hx(I.n1-1);' in ssrc)
        check('size Kellerwand: Druckbogen wölbt sich zur Erdseite', 'const xr=cx+tw/2-4, xa=cx-tw/2+4, xq=2*xa-xr;' in ssrc)
        check('size Böschung: z als lotrechte Tiefe', 'const nx=0, ny=zz;' in ssrc)
        check('size Wasserdruck: Gegendruck aus der Tiefe unter dem Unterwasserspiegel', 'WB.gw*Math.max(0, I.hu-(I.L-a)*s)' in ssrc)
        await pg.evaluate("setMat('beton'); setTyp('torsion')"); await pg.wait_for_timeout(250)
        t=await pg.evaluate("[...document.querySelectorAll('main svg text')].map(t=>t.textContent).join(' | ')")
        check('size Torsion: Höhe in cm wie die Eingabe', re.search(r'h = \d+ cm', t), t[:120])
        await pg.evaluate("setMat('stahl'); setStMode('traeger')"); await pg.wait_for_timeout(250)
        t=await pg.evaluate("[...document.querySelectorAll('main svg text')].map(t=>t.innerHTML).join(' | ')")
        check('size Skizzen: Indizes tiefgestellt statt Unterstrich (t_f)', 't<tspan' in t and 't_f' not in t, t[:120])
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
