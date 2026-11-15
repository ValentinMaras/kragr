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
                check(f'{tag} {t}: „Weiter“ in Abmessungen und Lager, Kurzfassung rechts', r['next'][:2]==['sup','loads'] and all(a=='right' for a in r['sumRight']), (r['next'], r['sumRight']))
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
