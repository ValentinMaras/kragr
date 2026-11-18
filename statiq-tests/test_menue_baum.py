# Auswahl im Burger-Menü als Baum (18.11.2026, Vorschlag C): die Auswahlkarte oben ist eine schlichte Pfadzeile
# „Modul › Bereich › Thema“; ein Tipp darauf öffnet das Menü. Im Menü sind die Module die Hauptpunkte, das aktuelle Modul ist bis zum
# Thema aufgeklappt (die Liste der Seite, #pick-menu, wird dafür ausgeliehen), Einstellungen liegen auf einer Unterseite.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
OPEN="document.getElementById('k5-menu').classList.contains('open')"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        for w,h,mob in ((390,844,True),(1280,900,False)):
            tag='Handy' if mob else 'Rechner'
            pg=await br.new_page(viewport={'width':w,'height':h}, is_mobile=mob, has_touch=mob); pg.on('pageerror', lambda e: errs.append(str(e)))
            for f,crumb,act in (('size','Bemessung › Stahlbeton › Balken','Balken'),('calc','Schnittkräfte › Balken › Einfeldträger','Einfeldträger'),('ref','Wissen › Stahlbeton · Baustoffe › Kriechen und Schwinden','Kriechen und Schwinden')):
                await pg.goto(B+f+'.html'+('#/stahlbeton/baustoffe/kriechen' if f=='ref' else '')); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
                r=await pg.evaluate("""(()=>{ const b=document.getElementById('pick-btn'), cs=getComputedStyle(b), tx=b.querySelector('.pick-txt');
                  const before=getComputedStyle(tx,'::before').content, g=document.getElementById('pick-g').textContent, t=document.getElementById('pick-t').textContent;
                  return {bg:cs.backgroundColor, sh:cs.boxShadow, path:(before.replace(/^"|"$/g,'').replace(/\\\\203A|\\u203a/g,'›')+' '+g+' › '+t).replace(/\\s+/g,' ')}; })()""")
                check(f'{tag} {f}: Auswahl als schlichte Pfadzeile ohne Kasten „{crumb}“', r['bg'] in ('rgba(0, 0, 0, 0)','transparent') and r['sh']=='none' and r['path'].strip()==crumb, r)
                await pg.click('#pick-btn'); await pg.wait_for_timeout(300)
                r=await pg.evaluate(f"""[{OPEN}, !!document.querySelector('#k5-menu .k5-tree #pick-menu'), (document.querySelector('.k5-tree .pick-item.active')||{{}}).textContent, document.querySelectorAll('#pick-menu').length,
                  (document.querySelector('#k5-menu .k5-cur')||{{}}).dataset?.mod, [...document.querySelectorAll('#k5-menu a.k5-mod')].map(a=>a.dataset.mod)]""")
                check(f'{tag} {f}: Tipp öffnet das Menü; aktuelles Modul aufgeklappt bis zum Thema', r[0] and r[1] and (r[2] or '').strip()==act and r[3]==1 and r[4]==f and f not in r[5] and 'projekt' in r[5], r)
                await pg.click('#k5-menu .k5-cur'); await pg.wait_for_timeout(150)
                c=await pg.evaluate("[document.querySelector('.k5-tree').hidden, document.querySelector('#k5-menu .k5-cur').getAttribute('aria-expanded')]")
                await pg.click('#k5-menu .k5-cur'); await pg.wait_for_timeout(150)
                check(f'{tag} {f}: Modulzeile klappt den Baum zu und wieder auf', c==[True,'false'] and not await pg.evaluate("document.querySelector('.k5-tree').hidden"), c)
                await pg.keyboard.press('Escape'); await pg.wait_for_timeout(150)
                check(f'{tag} {f}: Escape schließt, Liste zurück an der Seite', await pg.evaluate(f"!{OPEN} && !!document.querySelector('#pick > #pick-menu') && document.querySelectorAll('#pick-menu').length===1"))
            # Auswahl treffen
            await pg.goto(B+'size.html'); await pg.wait_for_timeout(900); await pg.click('#pick-btn'); await pg.wait_for_timeout(200)
            await pg.click('.k5-tree .pick-item >> text=Stütze'); await pg.wait_for_timeout(500)
            r=await pg.evaluate(f"[TYP, {OPEN}, document.getElementById('pick-t').textContent, document.querySelectorAll('#pick-menu').length]")
            check(f'{tag} size: Thema wählen stellt um und schließt das Menü', r==['stuetze',False,'Stütze',1], r)
            await pg.goto(B+'calc.html'); await pg.wait_for_timeout(900); await pg.click('#pick-btn'); await pg.wait_for_timeout(200)
            await pg.click('.k5-tree .pick-item >> text=Durchlaufträger'); await pg.wait_for_timeout(500)
            r=await pg.evaluate(f"[curTab(), {OPEN}, document.getElementById('pick-t').textContent]")
            check(f'{tag} calc: System wählen stellt um und schließt das Menü', r==['cont',False,'Durchlaufträger'], r)
            await pg.evaluate("showTab('beam')")
            await pg.goto(B+'ref.html#/stahlbeton/baustoffe/kriechen'); await pg.wait_for_timeout(900); await pg.click('#pick-btn'); await pg.wait_for_timeout(200)
            await pg.fill('#pick-q','manning'); await pg.wait_for_timeout(200)
            vis=await pg.evaluate("[...document.querySelectorAll('.k5-tree .pick-item')].filter(a=>a.offsetParent).map(a=>a.textContent)")
            check(f'{tag} ref: Suche im Baum filtert die Themen', 0<len(vis)<6, vis)
            await pg.click('.k5-tree .pick-item:visible >> nth=0'); await pg.wait_for_timeout(600)
            r=await pg.evaluate(f"[location.hash, {OPEN}, document.querySelectorAll('#pick-menu').length, !!document.querySelector('#pick > #pick-menu')]")
            check(f'{tag} ref: Thema aus dem Baum öffnet die Seite, Menü zu, keine doppelte Liste', r[0]!='#/stahlbeton/baustoffe/kriechen' and not r[1] and r[2]==1 and r[3], r)
            # Einstellungen als Unterseite
            await pg.goto(B+'size.html'); await pg.wait_for_timeout(800); await pg.click('#k5-burger'); await pg.wait_for_timeout(200)
            r=await pg.evaluate("[!!document.querySelector('#k5-theme') && document.querySelector('#k5-theme').offsetParent===null, getComputedStyle(document.querySelector('.k5-setbtn')).display]")
            await pg.click('.k5-setbtn'); await pg.wait_for_timeout(200)
            r2=await pg.evaluate("[document.querySelector('#k5-theme').offsetParent!==null, document.querySelector('.k5-pm').offsetParent===null, document.querySelector('.k5-back').textContent]")
            await pg.click('.k5-back'); await pg.wait_for_timeout(150)
            r3=await pg.evaluate("[document.querySelector('.k5-pm').offsetParent!==null, document.querySelector('#k5-theme').offsetParent===null]")
            check(f'{tag}: Einstellungen als Unterseite (hin und zurück)', r[0] and r[1]!='none' and r2[0] and r2[1] and 'Einstellungen' in r2[2] and all(r3), (r, r2, r3))
            await pg.keyboard.press('Escape'); await pg.click('#k5-burger'); await pg.wait_for_timeout(200)
            check(f'{tag}: Menü öffnet wieder auf der Hauptseite', await pg.evaluate("document.querySelector('.k5-pm').offsetParent!==null"))
            await pg.keyboard.press('Escape')
            # Seiten ohne Auswahl: kein Baum
            for f in ('projekt','index','rechtliches'):
                await pg.goto(B+f+'.html'); await pg.wait_for_timeout(500); await pg.click('#k5-burger'); await pg.wait_for_timeout(200)
                check(f'{tag} {f}: Menü ohne Baum, Module als Verweise', await pg.evaluate("!document.querySelector('.k5-tree') && document.querySelectorAll('#k5-menu a.k5-mod').length===4"))
                await pg.keyboard.press('Escape')
            await pg.close()
        # Sprachen: Pfadzeile folgt
        pg=await br.new_page(viewport={'width':390,'height':844})
        for L,mod in (('en','Design'),('fr','Dimensionnement'),('es','Dimensionado')):
            await pg.goto(B+'size.html'); await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(700)
            v=await pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--k5-modname')")
            check(f'{L}: Modulname in der Pfadzeile', v.strip().strip('"')==await pg.evaluate("kmod('size')"), (v, mod))
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
    print('FAILS:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
