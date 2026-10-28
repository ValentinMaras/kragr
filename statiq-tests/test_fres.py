# Statiq FR/ES (size v0.5.23, ref v0.3.22), dazu EN mit derselben strengen Prüfung: Oberfläche, Rechenwege, Berichte (size) und alle 132 Themen (ref)
# auf Französisch und Spanisch ohne deutsche Reste; Wörterbücher vollständig; Deutsch/Englisch unverändert. Ohne Playwright: SKIP.
import os, sys, re, json, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
ALL={}
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:160])
GER=re.compile(r'\w*[äöüÄÖÜß]\w*|\b(und|der|die|mit|nicht|oder|für|ein|eine|bei|aus|nach|ist|sind|wird|zum|zur|vom|oben|unten|Nachweis|Nachweise|erfüllt|Schicht|Wand|Platte|Balken|Decke|Holz|Stahl|Beton|Naht|Last|Fundament|Setzung|Rohr|Wehr|Gerinne|Höhe|Breite|Dicke|Länge|Seite|Stäbe|Bügel|Stütze|Auflager|Schub|Druck|Zug|Biegung|Knicken|Sohle|Boden|Querschnitt|Bewehrung|Kraft|Feld|Bitte|Eingabe|Ergebnis|Bericht|Beispiel|Träger|Knoten|Stab)\b')
OK_WORDS=['Der Eisenbetonbau','Eisenbetonbau','Eisenbeton','Stahlbeton','Mörsch','Erdbaumechanik','EA-Pfähle','Länder','Müller-Breslau','Dünnformat','Strickler','Glaser','Sichardt','Dupuit','Thiem','Joukowsky','Michaud','Blum','Rankine','Terzaghi','Coulomb','Mohr','Marcus','Torricelli','Bernoulli','Darcy','Weisbach','Colebrook','Prandtl','Reynolds','Froude','Steiner','Euler','Gauß','Möller','Schütt']
def german(t):
    for w in OK_WORDS: t=t.replace(w,'')
    return any(len(m.group(0))>=2 and not re.search(r'gü[eiéí]',m.group(0)) for m in GER.finditer(t))   # span. „desagüe“, „bilingüe“
TEXTS=r"""(sel) => { const out=[]; document.querySelectorAll(sel).forEach(R=>{ const w=document.createTreeWalker(R, NodeFilter.SHOW_TEXT);
  while(w.nextNode()){ const n=w.currentNode, p=n.parentElement; if(!p || ['SCRIPT','STYLE','SUB','SUP'].includes(p.tagName.toUpperCase())) continue;
    if(p.closest('.pos-name')) continue;
    const t=n.textContent.trim(); if(t && /[A-Za-zÄÖÜäöüß]{3,}/.test(t)) out.push(t); }
  R.querySelectorAll('[placeholder],[title]').forEach(e=>{ if(e.placeholder) out.push(e.placeholder); if(e.title) out.push(e.title); }); }); return out; }"""
SET={'beton':'setTyp','stahl':'setStMode','holz':'setHoMode','mauer':'setMwMode','grund':'setGrMode','wasser':'setWbMode','bauph':'setBpMode'}
MODES=[('beton',['balken','unterzug','platte','stuetze','durchstanzen']),('stahl',['traeger','anschluss','fuss','schweiss']),
 ('holz',['bauteil','verbindung','ausklink','sattel','versatz']),('mauer',['druck','teil','keller','schub']),
 ('grund',['flach','setzung','wand','upl','gleit']),('wasser',['druck','schwimm','rohr','gerinne','wehr']),('bauph',['uwert','glaser','schall'])]
def langfile(app, l):   # Sprachdatei lang/<app>.<l>.js
    t=open(os.path.join(BASE,'lang',f'{app}.{l}.js'),encoding='utf-8').read(); return json.loads(t[t.index('{'):t.rindex('}')+1])

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        # ── size
        pg=await br.new_page(); pg.on('pageerror', lambda e: errs.append('size: '+str(e)))
        await pg.goto('file://'+BASE+'/size.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        de=await pg.evaluate('I18N.de'); EN=langfile('size','en')['ttx']; en_t=list(EN)
        pa=await pg.evaluate('Object.keys(PA)')
        modes=[(m,x) for m,xs in MODES for x in xs]+[tuple(k.split('/')) for k in pa]
        for L in ('fr','es'):
            LFL=langfile('size',L); ui=LFL['i18n']; tt=LFL['ttx']
            miss=[k for k in de if not str(ui.get(k,'')).strip()]
            check(f'size {L}: I18N.{L} hat alle {len(de)} Schlüssel', not miss, miss[:6])
            ph=[k for k in de if k in ui and sorted(re.findall(r'\{\d\}',de[k]))!=sorted(re.findall(r'\{\d\}',ui[k]))]
            check(f'size {L}: Platzhalter {{0}}… wie im Deutschen', not ph, ph[:5])
            m2=[k for k in en_t if k not in tt and re.search(r'[a-zäöü]{3}',re.sub(r'<[^>]+>','',k)) and EN[k]!=k]
            check(f'size {L}: TTX.{L} deckt TTX.en ab ({len(tt)})', not m2, m2[:4])
        for L,word,word2 in (('en','All checks','Calculation steps'),('fr','Toutes les vérifications','Étapes de calcul'),('es','Todas las comprobaciones','Desarrollo del cálculo')):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(250)
            n=await pg.evaluate("document.querySelector('.lang-notice')?.textContent||''")
            if L!='en': check(f'size {L}: kein Sprachhinweis mehr (seit v0.5.33)', n=='', n[:90])
            left={}
            for mat,m in modes:
                await pg.evaluate(f"setMat('{mat}'); {SET[mat]}('{m}')"); await pg.wait_for_timeout(30)
                await pg.evaluate("showReport()")
                for t in await pg.evaluate(TEXTS, '.col-in, .det-bar, header, .ux-pick, #page-title, #page-sub, #fig-title, #summary, #chk-table, #details, #fig, #report'):
                    if german(t): left.setdefault(t[:70], f'{mat}/{m}')
                await pg.evaluate("document.body.classList.remove('show-report')")
            ALL['size-'+L]=left; check(f'size {L}: {len(modes)} Nachweise ohne deutsche Reste (Oberfläche, Rechenweg, Bericht)', not left, list(left.items())[:5])
            await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.wait_for_timeout(60)
            s=await pg.inner_text('#summary'); check(f'size {L}: Zusammenfassung', s.startswith(word), s[:60])
            check(f'size {L}: Leiste Rechenschritte', word2 in await pg.inner_text('.det-bar'))
            det=await pg.inner_text('#details'); check(f'size {L}: Dezimalzeichen', (re.search(r'\d,\d', det) is None) if L=='en' else (re.search(r'\d,\d', det) is not None))
            await pg.fill('#in-l','0'); await pg.dispatch_event('#in-l','input'); await pg.wait_for_timeout(60)
            s=await pg.inner_text('#summary'); check(f'size {L}: Eingabefehler übersetzt', not german(s), s[:60])
            await pg.fill('#in-l','6'); await pg.dispatch_event('#in-l','input')
        # ── ref
        pg=await br.new_page(); pg.on('pageerror', lambda e: errs.append('ref: '+str(e)))
        await pg.goto('file://'+BASE+'/ref.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        for L in ('fr','es'):
            RE=langfile('ref','en')['ttx']; RL=langfile('ref',L)['ttx']; m2=[k for k in RE if RE[k]!=k and re.search(r'[a-zäöü]{3}',re.sub(r'<[^>]+>','',k)) and k not in RL]
            check(f'ref {L}: TTX.{L} deckt TTX.en ab', not m2, m2[:4])
        for L,home,srch,hit in (('en','Reference','snow','Snow'),('fr','Aide-mémoire','neige','Neige'),('es','Prontuario','nieve','Nieve')):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(250)
            await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(150)
            ph=(await pg.evaluate("document.getElementById('search').placeholder")).lower(); mt=await pg.inner_text('#main')
            check(f'ref {L}: Startseite übersetzt (Suchfeld, ohne Titel seit v0.3.25)', srch in ph and 'Nachschlagewerk' not in mt and 'Schnee' not in ph, ph[:60])
            nde=await pg.evaluate("document.querySelectorAll('.tree-de').length"); check(f'ref {L}: kein Hinweis „DE“', nde==0, nde)
            side=[x for x in await pg.evaluate(TEXTS,'#sidebar') if german(x)]
            check(f'ref {L}: Seitenleiste übersetzt', not side, side[:4])
            pages=await pg.evaluate("Object.entries(FAECHER).flatMap(([f,F])=>Object.entries(F.kapitel).flatMap(([k,K])=>Object.keys(K.themen).map(t=>f+'/'+k+'/'+t)))")
            left={}
            for key in pages:
                await pg.evaluate(f"location.hash='#/{key}'"); await pg.wait_for_timeout(110)
                for x in await pg.evaluate(TEXTS, '#main, #toc, #breadcrumb'):
                    if german(x): left.setdefault(x[:70], key)
                await pg.evaluate("""[...document.querySelectorAll('#main input[type=number]')].slice(0,10).forEach(e=>{ e.value=(+e.value||1)*1.37; e.dispatchEvent(new Event('input',{bubbles:true})); })""")
                await pg.evaluate("""[...document.querySelectorAll('#main select')].forEach(e=>{ e.selectedIndex=e.options.length-1; e.dispatchEvent(new Event('change',{bubbles:true})); })""")
                await pg.wait_for_timeout(50)
                for x in await pg.evaluate(TEXTS, '#main'):
                    if german(x): left.setdefault(x[:70], key+' (Eingabe)')
            ALL['ref-'+L]=left; check(f'ref {L}: {len(pages)} Themen ohne deutsche Reste (auch nach Eingaben)', not left, list(left.items())[:5])
            await pg.evaluate("location.hash='#/baustatik/balkentafeln/einfeld'"); await pg.wait_for_timeout(150)
            t=await pg.inner_text('#main'); check(f'ref {L}: Dezimalzeichen im Inhalt', ('31.25 kNm' if L=='en' else '31,25 kNm') in t)
            await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(100)
            await pg.fill('#search',srch); await pg.wait_for_timeout(200)
            r=await pg.inner_text('#search-results'); check(f'ref {L}: Suche findet „{srch}“', hit in r, r[:60])
        # DE und EN unverändert
        await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("location.hash='#/baustatik/balkentafeln/einfeld'"); await pg.wait_for_timeout(150)
        check('ref de: weiterhin deutsch', 'Einfeldträger' in await pg.inner_text('#main'))
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("location.hash='#/baustatik/balkentafeln/einfeld'"); await pg.wait_for_timeout(150)
        check('ref en: weiterhin englisch mit Dezimalpunkt', 'Simply supported' in await pg.inner_text('#main') and '31.25 kNm' in await pg.inner_text('#main'))
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
if os.environ.get('SHOWALL'): print(json.dumps(ALL,ensure_ascii=False,indent=0))
print('FAILS:', fails); sys.exit(1 if fails else 0)
