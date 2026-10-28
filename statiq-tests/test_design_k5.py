# Design 5 (calc v0.11.2 · size v0.7.4 · ref v0.3.44 · projekt v0.1.20 · rechtliches v0.1.13 · Startseite): ein Aufbau für alle Seiten.
# Kopfzeile nur Logo + ☰, Menü mit Modulen, Projekten, Übungsmodus, Erscheinungsbild und Sprache; Karten als Akkordeon
# (Titel · Kurzfassung · Pfeil, immer nur eine offen); weiße Karten auf hellgrauem Grund; Bewegung (aus bei „Bewegung reduzieren“).
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..')); B='file://'+BASE+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:230])
PAGES=['index','calc','size','ref','projekt','rechtliches']
src={p:open(os.path.join(BASE,p+'.html'),encoding='utf-8').read() for p in PAGES}
for tag in ['style','script']:
    b={p:re.search(r'<%s data-k5>(.*?)</%s>'%(tag,tag),src[p],re.S) for p in PAGES}
    check(f'gleicher Baustein <{tag} data-k5> auf allen sechs Seiten', all(b.values()) and len({x.group(1) for x in b.values()})==1)
HDR="""()=>{const h=document.querySelector('.app-header.k-hdr, header.k5-idx'), bu=document.getElementById('k5-burger');
 const vis=e=>!!e && e.offsetParent!==null && getComputedStyle(e).display!=='none';
 const shown=[...h.querySelectorAll('a, button, select')].filter(vis).map(e=>e.id||e.className.split(' ')[0]);
 const r=bu.getBoundingClientRect();
 return {shown, w:Math.round(r.width), h:Math.round(r.height), right:Math.round(r.right), sw:document.documentElement.scrollWidth,
   bg:getComputedStyle(document.body).backgroundColor}}"""
async def menu(pg):
    await pg.click('#k5-burger'); await pg.wait_for_selector('#k5-menu.open')
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        pg=await br.new_page(viewport={'width':390,'height':844}); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')")
        # Kopfzeile und Menü auf allen Seiten
        for W in [390,1280]:
            await pg.set_viewport_size({'width':W,'height':844}); R={}
            for f in [x for x in PAGES if x!='index']:   # Startseite seit 28.10.2026 ohne Menü (eigene Prüfung unten)
                await pg.goto(B+f+'.html'); await pg.wait_for_timeout(300); R[f]=await pg.evaluate(HDR)
            check(f'{W} px: Kopfzeile zeigt nur Logo und ☰', all(set(r['shown'])<= {'logo','k5-burger'} and 'k5-burger' in r['shown'] for r in R.values()), {k:v['shown'] for k,v in R.items()})
            check(f'{W} px: ☰ mindestens 44 × 44 px', all(r['w']>=44 and r['h']>=44 for r in R.values()), {k:(v['w'],v['h']) for k,v in R.items()})
            edge=W-max(16 if W<=560 else 24, (W-1180)//2+24)
            check(f'{W} px: ☰ an der rechten Rahmenkante (App-Seiten)', all(abs(R[f]['right']-edge)<=1 for f in PAGES if f!='index'), {k:v['right'] for k,v in R.items()})
            check(f'{W} px: hellgrauer Seitengrund, kein Querscrollen', all(r['bg']=='rgb(242, 243, 246)' and r['sw']<=W for r in R.values()), {k:(v['bg'],v['sw']) for k,v in R.items()})
        await pg.set_viewport_size({'width':390,'height':844})
        # Startseite: kein Menü; Erscheinungsbild und Sprache oben rechts
        for W in [390,1280,360]:
            await pg.set_viewport_size({'width':W,'height':844}); await pg.goto(B+'index.html'); await pg.wait_for_timeout(300)
            r=await pg.evaluate("""(()=>{ const f=document.getElementById('k5-fset'), b=f&&f.getBoundingClientRect();
              return {burger:!!document.getElementById('k5-burger'), menu:!!document.getElementById('k5-menu'), theme:document.querySelectorAll('#k5-ftheme button').length, lang:document.querySelectorAll('#k5-flang button').length,
                inHdr:!!(f&&f.closest('header.k5-idx')), top:b?Math.round(b.top):null, h:b?Math.round(b.height):null, right:b?Math.round(b.right):null, sw:document.documentElement.scrollWidth}; })()""")
            check(f'Startseite {W} px: kein Menü, oben rechts Auto/Hell/Dunkel und DE/EN/FR/ES in einer Zeile', not r['burger'] and not r['menu'] and r['theme']==3 and r['lang']==4 and r['inHdr'] and r['top']>=0 and r['h']<=34 and r['right']<=W and r['sw']<=W, r)
        await pg.set_viewport_size({'width':390,'height':844}); await pg.goto(B+'index.html'); await pg.wait_for_timeout(300)
        await pg.click('#k5-ftheme button[data-v="dark"]'); await pg.wait_for_timeout(120)
        d=await pg.evaluate("[document.documentElement.classList.contains('dark'), localStorage.getItem('muly-theme')]")
        await pg.click('#k5-ftheme button[data-v="auto"]'); await pg.wait_for_timeout(120)
        check('Startseite: Erscheinungsbild „Dunkel“ und zurück auf „Auto“', d==[True,'dark'] and await pg.evaluate("localStorage.getItem('muly-theme')")=='auto', d)
        await pg.click('#k5-flang button[data-v="en"]'); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[localStorage.getItem('statiq-lang'), document.getElementById('footer-legal').textContent, document.querySelector('#k5-flang button[aria-pressed=true]').dataset.v]")
        check('Startseite: Sprache EN über die Umschalter', r[0]=='en' and 'Legal' in r[1] and r[2]=='en', r)
        await pg.click('#k5-flang button[data-v="de"]'); await pg.wait_for_timeout(500)
        for f,cur in [('calc','calc'),('size','size'),('ref','ref'),('projekt','projekt')]:
            await pg.goto(B+f+'.html'); await pg.wait_for_timeout(300); await menu(pg)
            r=await pg.evaluate("""()=>({mods:[...document.querySelectorAll('#k5-menu .k5-mod')].map(a=>a.dataset.mod+'>'+a.getAttribute('href').split('#')[0]),
              cur:(document.querySelector('#k5-menu .k5-mod[aria-current=page]')||{}).dataset?.mod||null, ueb:!!document.getElementById('k5-ueb'),
              theme:!!document.querySelector('#k5-theme'), lang:!!document.querySelector('#k5-lang'), exp:document.getElementById('k5-burger').getAttribute('aria-expanded'),
              foc:document.activeElement && document.activeElement.closest('#k5-menu')!==null, lock:document.body.classList.contains('k5-lock')})""")
            check(f'{f}: Menü mit calc, size, ref, Rechenblätter; aktuelle Seite markiert', r['mods']==['calc>calc.html','size>size.html','ref>ref.html','projekt>projekt.html'] and r['cur']==cur, r)
            check(f'{f}: Menü offen (aria-expanded, Fokus im Menü, Seite gesperrt), Erscheinungsbild und Sprache', r['exp']=='true' and r['foc'] and r['lock'] and r['theme'] and r['lang'], r)
            check(f'{f}: Übungsmodus nur in calc und size', r['ueb']==(f in ('calc','size')), r['ueb'])
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(100)
            check(f'{f}: Escape schließt das Menü', await pg.evaluate("!document.getElementById('k5-menu').classList.contains('open') && document.getElementById('k5-burger').getAttribute('aria-expanded')==='false' && !document.body.classList.contains('k5-lock')"))
        # Menü steuert Erscheinungsbild, Sprache, Übungsmodus
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(300); await menu(pg)
        await pg.click('#k5-theme button[data-v="dark"]'); await pg.wait_for_timeout(100)
        check('Erscheinungsbild „Dunkel“ über das Menü', await pg.evaluate("document.documentElement.classList.contains('dark') && localStorage.getItem('muly-theme')==='dark'"))
        await pg.click('#k5-theme button[data-v="light"]'); await pg.wait_for_timeout(100)
        check('Erscheinungsbild „Hell“ über das Menü', await pg.evaluate("!document.documentElement.classList.contains('dark') && localStorage.getItem('muly-theme')==='light'"))
        await pg.click('#k5-theme button[data-v="auto"]')
        await pg.click('#k5-lang button[data-v="en"]'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[localStorage.getItem('statiq-lang'), document.getElementById('lang-sel').value, document.querySelector('#k5-menu .k5-mlabel').textContent, document.querySelector('[data-i18n=system]').textContent]")
        check('Sprache EN über das Menü: Seite und Menü englisch', r==['en','en','Modules','System'], r)
        await pg.click('#k5-lang button[data-v="de"]'); await pg.wait_for_timeout(300)
        check('Sprache zurück auf DE', await pg.evaluate("localStorage.getItem('statiq-lang')")=='de')
        await pg.click('#k5-ueb'); await pg.wait_for_timeout(200)
        r=await pg.evaluate("[document.getElementById('ueb-btn').getAttribute('aria-pressed'), document.body.classList.contains('uebung'), document.getElementById('k5-menu').classList.contains('open')]")
        check('Übungsmodus über das Menü an (Menü schließt)', r==['true',True,False], r)
        await menu(pg)
        check('Schalter im Menü zeigt den Übungsmodus an', await pg.get_attribute('#k5-ueb','aria-checked')=='true')
        await pg.click('#k5-ueb'); await pg.wait_for_timeout(200)
        check('Übungsmodus über das Menü wieder aus', await pg.get_attribute('#ueb-btn','aria-pressed')=='false')
        # calc: Ergebnis-Details als Akkordeon
        await pg.goto(B+'calc.html'); await pg.wait_for_timeout(400)
        r=await pg.evaluate("""()=>{const k=document.querySelector('#tab-beam .k-knoten'), rw=document.getElementById('rw-beam');
          return {kc:k.classList.contains('k5-closed'), sum:k.querySelector('.k5-hsum').textContent, body:k.querySelector('.k5-body').offsetParent===null,
            rwc:rw.classList.contains('closed'), rws:rw.querySelector('.k5-hsum').textContent, tri:!!k.querySelector('.k5-tri') && !!rw.querySelector('.k5-tri')}}""")
        check('calc: Knotentabelle zugeklappt, Kurzfassung „2 Knoten · 1 Stab“', r['kc'] and r['body'] and r['sum']=='2 Knoten · 1 Stab' and r['tri'], r)
        check('calc: Lösungsweg zugeklappt, Kurzfassung „6 Schritte“', r['rwc'] and r['rws']=='6 Schritte', r)
        await pg.click('#tab-beam .k-knoten .k5-head'); await pg.wait_for_timeout(100)
        check('calc: Knotentabelle öffnet per Tipp', await pg.evaluate("!document.querySelector('#tab-beam .k-knoten').classList.contains('k5-closed') && document.querySelector('#tab-beam .k-knoten .k-kn-tab').offsetParent!==null"))
        await pg.click('#rw-beam .rw-title'); await pg.wait_for_timeout(100)
        check('calc: Lösungsweg öffnen schließt die Knotentabelle', await pg.evaluate("!document.getElementById('rw-beam').classList.contains('closed') && document.querySelector('#tab-beam .k-knoten').classList.contains('k5-closed')"))
        await pg.fill('#bL','6'); await pg.dispatch_event('#bL','input'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.querySelector('#tab-beam .k-knoten').classList.contains('k5-closed'), !!document.querySelector('#tab-beam .k-knoten > .k5-head .k5-tri'), document.getElementById('b-res-A').textContent]")
        check('calc: nach neuer Rechnung bleibt der Kopf, Zustand bleibt', r[0] and r[1] and r[2]!='—', r)
        await pg.reload(); await pg.wait_for_timeout(400)
        check('calc: Zustand nach Neuladen gemerkt (Lösungsweg offen)', await pg.evaluate("!document.getElementById('rw-beam').classList.contains('closed') && document.querySelector('#tab-beam .k-knoten').classList.contains('k5-closed')"))
        # calc Rahmen: seit calc v0.11.8 (k5 + Eingabe in Stufen) liegen Rahmentyp, Lager und Gelenke in Stufe ② „Lager und Gelenke“;
        # k5 baut dort keine eigenen Unterabschnitte mehr (sonst doppelte Kopfzeilen)
        await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("""()=>{ const st=document.querySelector('#tab-frame [data-st=sup]'); return [!!st, [...st.querySelectorAll('[data-i18n]')].map(e=>e.getAttribute('data-i18n')).filter(x=>['framePresets','supportA','supportB','internalHinges'].includes(x)), st.querySelectorAll('.k5-acc').length]; }""")
        check('calc Rahmen: Rahmentyp, Lager A/B und Gelenke in Stufe ②, ohne zweite k5-Faltung', r[0] and r[1]==['framePresets','supportA','supportB','internalHinges'] and r[2]==0, r)
        await pg.click('#tab-frame [data-st=sup] > .k-head'); await pg.wait_for_timeout(200)
        await pg.click('#btn-sA-pin'); await pg.wait_for_timeout(200)
        s=await pg.evaluate("document.querySelector('#tab-frame [data-st=sup] > .k-head .k-sum').textContent")
        check('calc Rahmen: Lagerwahl wirkt, Kurzfassung der Stufe („Zweigelenkrahmen · n = 1“)', await pg.evaluate("document.getElementById('btn-sA-pin').classList.contains('active')") and (s.startswith('A △') or s.startswith('Zweigelenkrahmen')), s)
        await pg.evaluate("showTab('beam')")
        # size: Eingabekarten als Akkordeon
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.removeItem('statiq-size-fold')"); await pg.reload(); await pg.wait_for_timeout(500)
        S="""()=>[...document.querySelectorAll('.col-in .card.fold')].filter(c=>c.offsetParent!==null).map(c=>[c.dataset.fold, !c.classList.contains('closed'), (c.querySelector('.card-title .k5-hsum')||{}).textContent||'', !!c.querySelector('.card-title .k5-tri')])"""
        r=await pg.evaluate(S)
        check('size: genau eine Eingabekarte offen', sum(x[1] for x in r)==1 and r[0][1], r)
        check('size: zugeklappte Karten zeigen eine Kurzfassung im Kopf', all(x[2] for x in r if not x[1]) and all(x[3] for x in r), r)
        await pg.click('.col-in .card.fold[data-fold="in-beton"] > .card-title'); await pg.wait_for_timeout(150)
        r=await pg.evaluate(S)
        check('size: andere Karte öffnen schließt die erste', [x[0] for x in r if x[1]]==['in-beton'], r)
        await pg.reload(); await pg.wait_for_timeout(500)
        check('size: Zustand nach Neuladen gemerkt', [x[0] for x in await pg.evaluate(S) if x[1]]==['in-beton'])
        r=await pg.evaluate("[document.getElementById('scope-card').classList.contains('k5-closed'), document.querySelectorAll('#details > .card.dfold .k5-tri').length>0]")
        check('size: „Umfang und Grundlagen“ zugeklappt, Rechenschritte mit gleichem Pfeil', r==[True,True], r)
        # projekt = „Rechenblätter“ (seit calc v0.11.11): flache Liste ohne Akkordeon, Karten im k5-Stil
        await pg.goto(B+'projekt.html'); await pg.evaluate("localStorage.setItem('statiq-size-positionen', JSON.stringify([{name:'A', typ:'balken', ok:true, date:'2026-10-27T10:00:00Z', data:{}},{name:'B', typ:'balken', ok:false, date:'2026-10-27T11:00:00Z', data:{}}]))"); await pg.reload(); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[document.querySelectorAll('.bl').length, document.querySelectorAll('.k5-acc').length, getComputedStyle(document.querySelector('.bl')).borderTopLeftRadius]")
        check('Rechenblätter: Karten ohne Akkordeon, Rundung wie k5 (20 px)', r==[2,0,'20px'], r)
        await pg.evaluate("localStorage.removeItem('statiq-size-positionen')")
        # ref: Seitenkopf als Karte
        await pg.goto(B+'ref.html#/stahlbeton/baustoffe/kriechen'); await pg.wait_for_timeout(500)
        # seit ref v0.3.53: der Seitenkopf sitzt im weißen Lehrbuchblatt (.lb-page)
        r=await pg.evaluate("(()=>{const h=document.querySelector('#main .page-head'), b=h.closest('.lb-page'); const cs=getComputedStyle(b); return [cs.backgroundColor, cs.borderRadius, getComputedStyle(h).flexDirection, h.querySelector('.page-sub').getBoundingClientRect().top < h.querySelector('.page-title').getBoundingClientRect().top]})()")
        check('ref: Seitenkopf im weißen Blatt, Fach · Kapitel als Oberzeile', r[0]=='rgb(255, 255, 255)' and r[1] in ('16px','20px') and r[2:]==['column-reverse',True], r)
        await pg.click('#main .page-head'); await pg.wait_for_timeout(200)
        check('ref (Handy): Tipp auf den Seitenkopf öffnet die Themenliste', await pg.evaluate("document.getElementById('sidebar').classList.contains('open')"))
        # rechtliches: Seitenkopf
        await pg.goto(B+'rechtliches.html'); await pg.wait_for_timeout(300)
        check('rechtliches: Titel, Einleitung und Sprungmarken in einer Kopfkarte', await pg.evaluate("(()=>{const k=document.querySelector('#content > .k5-phead'); return !!k && !!k.querySelector('h1') && !!k.querySelector('.lead')})()"))
        # Bewegung (?k5motion): Einblenden, Hochzählen ohne den echten Wert zu verändern
        ctx=await br.new_context(viewport={'width':390,'height':844}); mp=await ctx.new_page(); mp.on('pageerror', lambda e: errs.append(str(e)))
        await mp.goto(B+'calc.html?k5motion'); await mp.wait_for_timeout(120)
        r=await mp.evaluate("[document.documentElement.classList.contains('k5-still'), document.querySelectorAll('.k5-rv').length, !!document.querySelector('#b-res-A .k5-count'), document.getElementById('b-res-A').firstChild.textContent]")
        check('Bewegung: Karten blenden ein, Zahlen zählen hoch', r[0]==False and r[1]>0 and r[2], r)
        check('Bewegung: echter Wert bleibt während des Zählens im Element', r[3]=='17.50' or r[3]=='17,50', r[3])
        await mp.wait_for_timeout(1500)
        check('Bewegung: Zählebene danach entfernt', await mp.evaluate("!document.querySelector('.k5-count') && document.getElementById('b-res-A').textContent")=='17.50')
        await mp.click('#k5-burger'); await mp.wait_for_timeout(60)
        tf=await mp.evaluate("getComputedStyle(document.getElementById('k5-menu')).transform")
        check('Bewegung: Menü gleitet herein', tf not in ('none',''), tf)
        await ctx.close()
        ctx=await br.new_context(viewport={'width':390,'height':844}, reduced_motion='reduce'); mp=await ctx.new_page()
        await mp.goto(B+'calc.html?k5motion'); await mp.wait_for_timeout(120)
        check('„Bewegung reduzieren“: kein Einblenden, kein Hochzählen', await mp.evaluate("document.querySelectorAll('.k5-rv').length===0 && !document.querySelector('.k5-count')"))
        await ctx.close()
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
sys.exit(1 if fails else 0)
