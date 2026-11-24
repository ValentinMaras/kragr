# Eingabe in Schnittkräfte einheitlich (calc v0.11.49, 15.11.2026): alle vier Systeme mit denselben Stufen
# System → Abmessungen → Lager und Gelenke → Lasten → Erweitert, „Weiter“-Knopf in Abmessungen und Lager, Kurzfassung rechts.
# Einfeld-/Kragträger: Länge in „Abmessungen“, Lager als Übersicht, Federn/Setzungen in „Lager und Gelenke“ (vorher „Erweitert“).
# Durchlaufträger: Lasten je Feld als schlichte Zwischenüberschrift statt Kasten im Kasten.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for w,h,mob in ((1280,900,False),(390,844,True)):
            pg=await br.new_page(viewport={'width':w,'height':h}, is_mobile=mob, has_touch=mob); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(1000)
            tag='Rechner' if not mob else 'Handy'
            for t in ['beam','cantilever','cont','frame']:
                await pg.evaluate(f"showTab('{t}')"); await pg.wait_for_timeout(400)
                r=await pg.evaluate(f"""(()=>{{ const c=document.querySelector('#tab-{t} .col-in'); const st=[...c.querySelectorAll(':scope > [data-st]')];
                  return {{order:st.map(e=>e.dataset.st), next:st.map(e=>e.querySelector(':scope .k-st-next')?.dataset.next||''), sumRight:st.map(e=>getComputedStyle(e.querySelector(':scope > .k-head .k-sum')).textAlign),
                    heads:st.map(e=>(e.querySelector(':scope > .k-head .k-h')||{{}}).textContent), supx:!!c.querySelector('[data-st=sup] .k-supx'), supxAdv:!!c.querySelector('[data-st=adv] .k-supx')}}; }})()""")
                check(f'{tag} {t}: Stufen Abmessungen → Lager und Gelenke → Lasten → Erweitert', r['order']==['dims','sup','loads','adv'] and r['heads']==['Abmessungen','Lager und Gelenke','Lasten','Erweitert'], (r['order'], r['heads']))
                check(f'{tag} {t}: kein „Weiter“-Knopf mehr (calc v0.11.52), Kurzfassung rechts', r['next']==['','','',''] and all(a=='right' for a in r['sumRight']), (r['next'], r['sumRight']))
                check(f'{tag} {t}: Federn und Setzungen in „Lager und Gelenke“', r['supx'] and not r['supxAdv'], r)
            # Einfeld-/Kragträger: Länge in Abmessungen, Lager-Übersicht, Federn wirken
            for t,L,info in (('beam','bL',['Lager A','Festlager','Lager B','Loslager']),('cantilever','cL',['Lager A','Einspannung','freies Ende'])):
                await pg.evaluate(f"showTab('{t}')"); await pg.wait_for_timeout(300)
                r=await pg.evaluate(f"[!!document.querySelector('#tab-{t} [data-st=dims] #{L}'), document.querySelector('#tab-{t} .k-supinfo').innerText, document.querySelector('#tab-{t} [data-st=dims] .k-sum').textContent]")
                check(f'{tag} {t}: Länge in „Abmessungen“ mit Kurzfassung, Lager als Übersicht', r[0] and all(x in r[1] for x in info) and r[2].startswith('L = '), r)
            await pg.evaluate("showTab('beam')"); await pg.evaluate("document.querySelectorAll('#tab-beam .k-st.k-closed > .k-head').forEach(h=>h.click())"); await pg.wait_for_timeout(200)
            await pg.evaluate("document.querySelector('#tab-beam [data-st=sup] .k-supx .sx-on').click()"); await pg.wait_for_timeout(300)
            await pg.fill('#tab-beam [data-st=sup] .sx-sup[data-lab=B] input[data-sx=sv]','10'); await pg.wait_for_timeout(600)
            r=await pg.evaluate("[SUPX.beam && SUPX.beam.on, SUPX.beam && SUPX.beam.B && SUPX.beam.B.sv, document.querySelector('#tab-beam [data-st=sup] .k-sum').textContent]")
            check(f'{tag} beam: Setzung in „Lager und Gelenke“ eingegeben, wirkt und steht in der Kurzfassung', r[0] and r[1]=='10' and 'Feder' in r[2] or 'Setz' in r[2], r)
            await pg.evaluate("document.querySelector('#tab-beam [data-st=sup] .k-supx .sx-on').click()"); await pg.wait_for_timeout(200)
            # Durchlaufträger: Felder ohne Kasten
            await pg.evaluate("showTab('cont')"); await pg.wait_for_timeout(300)
            r=await pg.evaluate("[...document.querySelectorAll('#span-load-cards > .card')].map(c=>{ const s=getComputedStyle(c); return [s.backgroundColor, s.boxShadow, (c.querySelector('.k-h')||{}).textContent]; })")
            check(f'{tag} cont: Lasten je Feld als Zwischenüberschrift (ohne eigenen Kasten)', len(r)>=2 and all(x[0] in ('rgba(0, 0, 0, 0)','transparent') and x[1]=='none' for x in r) and r[0][2].startswith('Feld 1'), r)
            await pg.close()
        # Beim Öffnen alle Eingabestufen zu (calc v0.11.52) und alle Eingabekarten in Bemessung zu (size v0.7.53) — echtes Verhalten mit ?k5zu
        for w,h,mob in ((390,844,True),(1280,900,False)):
            pg=await br.new_page(viewport={'width':w,'height':h}, is_mobile=mob, has_touch=mob); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(B+'calc.html?k5zu'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de');localStorage.setItem('statiq-stufen',JSON.stringify({beam:{dims:true,loads:true}}))"); await pg.reload(); await pg.wait_for_timeout(900)
            bad={}
            for t in ['beam','cantilever','cont','frame']:
                await pg.evaluate(f"showTab('{t}')"); await pg.wait_for_timeout(250)
                o=await pg.evaluate(f"[...document.querySelectorAll('#tab-{t} .col-in > [data-st]')].filter(c=>!c.classList.contains('k-closed')).map(c=>c.dataset.st)")
                if o: bad[t]=o
            if mob: check('Handy calc: beim Öffnen alle Stufen zu (auch mit altem Speicher)', not bad and await pg.evaluate("localStorage.getItem('statiq-stufen')") is None, bad)
            else:   # Rechner (calc v0.11.54): alle Stufen offen
                op={}
                for t in ['beam','cantilever','cont','frame']:
                    await pg.evaluate(f"showTab('{t}')"); await pg.wait_for_timeout(150)
                    op[t]=await pg.evaluate(f"[...document.querySelectorAll('#tab-{t} .col-in > [data-st]')].filter(c=>c.classList.contains('k-closed')).map(c=>c.dataset.st)")
                check('Rechner calc: beim Öffnen alle Stufen offen', all(v==[] for v in op.values()) and await pg.evaluate("localStorage.getItem('statiq-stufen')") is None, op)
            await pg.click('#tab-beam [data-st=dims] > .k-head') if await pg.evaluate("curTab()")=='beam' else None
            await pg.evaluate("showTab('beam')"); await pg.click('#tab-beam [data-st=dims] > .k-head'); await pg.wait_for_timeout(150)
            await pg.reload(); await pg.wait_for_timeout(800)
            check(f'{"Handy" if mob else "Rechner"} calc: nach Neuladen wieder der Anfangszustand', await pg.evaluate("document.querySelector('#tab-beam [data-st=dims]').classList.contains('k-closed')")==mob)
            await pg.goto(B+'size.html?k5zu'); await pg.wait_for_timeout(900)
            o=await pg.evaluate("[...document.querySelectorAll('.col-in .card.fold')].filter(c=>c.offsetParent && !c.classList.contains('closed')).map(c=>c.dataset.fold)")
            await pg.evaluate("setMat('holz')"); await pg.wait_for_timeout(300)
            o2=await pg.evaluate("[...document.querySelectorAll('.col-in .card.fold')].filter(c=>c.offsetParent && !c.classList.contains('closed')).map(c=>c.dataset.fold)")
            if mob: check('Handy size: beim Öffnen und nach dem Wechsel alle Eingabekarten zu', o==[] and o2==[], (o, o2))
            else:
                n=await pg.evaluate("[...document.querySelectorAll('.col-in .card.fold')].filter(c=>c.offsetParent).length")
                check('Rechner size: beim Öffnen und nach dem Wechsel alle Eingabekarten offen (size v0.7.55)', len(o2)==n and n>0 and len(o)>0, (o, o2, n))
            await pg.close()
        # Rechner: die Seite passt ins Fenster, nur die Spalten scrollen, Fußleiste schmal unten (calc v0.11.54 · size v0.7.55)
        pg=await br.new_page(viewport={'width':1280,'height':800})
        for f in ('calc','size'):
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(900)
            r=await pg.evaluate("""(()=>{ const H=document.documentElement, l=document.querySelector('.legal-bar').getBoundingClientRect(), V=s=>[...document.querySelectorAll(s)].find(e=>e.offsetParent);
              const a=V('.col-in').getBoundingClientRect(), b=V('.col-out').getBoundingClientRect();
              return {fit:H.scrollHeight<=H.clientHeight, foot:[Math.round(l.bottom), Math.round(l.height), parseFloat(getComputedStyle(document.querySelector('.legal-bar')).fontSize)], cols:[Math.round(a.top)===Math.round(b.top), a.bottom<=l.top+1, b.bottom<=l.top+1], own:[getComputedStyle(V('.col-in')).overflowY, getComputedStyle(V('.col-out')).overflowY]}; })()""")
            check(f'Rechner {f}: Seite ohne eigenes Scrollen, Spalten scrollen, Fußleiste (11 px, eine Zeile) unten im Bild', r['fit'] and r['foot'][0]==800 and r['foot'][1]<=36 and r['foot'][2]==11 and all(r['cols']) and r['own']==['auto','auto'], r)
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(800); await pg.evaluate("showTab('saved')"); await pg.wait_for_timeout(300)
        check('Rechner calc „Gespeichert“: normale Seite (scrollt, Fußleiste wie bisher)', await pg.evaluate("getComputedStyle(document.body).overflow!=='hidden'"))
        await pg.close()
        # Zahlenfelder ohne Pfeile des Browsers
        pg=await br.new_page(viewport={'width':1280,'height':900})
        for f in ('calc','size'):
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(700)
            r=await pg.evaluate("[getComputedStyle(document.querySelector('input[type=number]')).appearance, getComputedStyle(document.querySelector('.k-sb')).touchAction]")
            check(f'{f}: Zahlenfelder ohne Browser-Pfeile, − und + ohne Doppeltipp-Zoom', r[0]=='textfield' and r[1]=='manipulation', r)
        await pg.close()
        # Sprachen: neue Texte
        pg=await br.new_page(viewport={'width':1280,'height':900})
        for L,free in (('en','free end'),('fr','extrémité libre'),('es','extremo libre')):
            await pg.goto(B+'calc.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(800)
            await pg.evaluate("showTab('cantilever')"); await pg.wait_for_timeout(300)
            check(f'{L}: Kragträger „{free}“', free in await pg.evaluate("document.querySelector('#tab-cantilever .k-supinfo').innerText"))
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
    print('FAILS:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
