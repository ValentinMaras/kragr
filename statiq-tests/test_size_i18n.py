# statiq·size v0.5.17/0.5.18 Sprachen: Englisch vollständig (Oberfläche, Rechenwege, Abbildungen, Bericht), Deutsch unverändert.
# Prüft Schlüssel (DE/EN vollständig, Platzhalter gleich), den deutschen Ausgangstext im HTML gegen I18N.de,
# alle Bereiche/Modi auf Englisch ohne deutsche Reste in der Oberfläche und dynamische Meldungen. Ohne Playwright: SKIP.
import os, json, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
HTML='file://'+BASE+'/size.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])

MODES=[('beton',None,['balken','unterzug','platte','stuetze','durchstanzen']),('stahl','setStMode',['traeger','anschluss','fuss','schweiss']),
 ('holz','setHoMode',['bauteil','verbindung','ausklink','sattel','versatz']),('mauer','setMwMode',['druck','teil','keller','schub']),
 ('grund','setGrMode',['flach','setzung','wand','upl','gleit']),('wasser','setWbMode',['druck','schwimm','rohr','gerinne','wehr']),('bauph','setBpMode',['uwert','glaser','schall'])]
UI='.col-in, .det-bar, #proj-panel, header, .ux-pick, #page-title, #page-sub, #fig-title, #summary, #mob-status'
GER=re.compile(r'[äöüÄÖÜß]|\b(und|der|die|das|mit|nicht|oder|für|ein|eine|bei|aus|nach|Bitte|Nachweis|Nachweise|erfüllt|Bezeichnung|Bericht|Eingabe|Rechenschritte|Themen|Wand|Platte|Balken|Decke|Holz|Stahl|Beton|Naht|Last|Fundament|Setzung|Rohr|Wehr|Gerinne|Alle|Ergebnis|Positionen|Höhe|Breite|Dicke|Länge|Schicht)\b')
TEXTS = r"""(sel) => { const out=[]; document.querySelectorAll(sel).forEach(R=>{ const w=document.createTreeWalker(R, NodeFilter.SHOW_TEXT);
  while(w.nextNode()){ const n=w.currentNode, p=n.parentElement; if(!p || ['SCRIPT','STYLE'].includes(p.tagName) || p.closest('svg')) continue;
    const t=n.textContent.trim(); if(!t || !/[A-Za-zÄÖÜäöüß]{3,}/.test(t)) continue; if(p.offsetParent===null && p.tagName!=='OPTION') continue; out.push(t); }
  R.querySelectorAll('[placeholder],[title]').forEach(e=>{ if(e.placeholder) out.push(e.placeholder); if(e.title) out.push(e.title); }); }); return out; }"""

GER2=re.compile(r'[äöüÄÖÜß]|\b(und|der|die|das|mit|nicht|oder|für|ein|eine|bei|aus|nach|ist|sind|wird|im|am|zum|zur|vom|oben|unten|gewählt|vorh|erf|zul|Nachweis|Nachweise|erfüllt|Schicht|Wand|Platte|Balken|Decke|Holz|Stahl|Beton|Naht|Last|Fundament|Setzung|Rohr|Wehr|Gerinne|Höhe|Breite|Dicke|Länge|Seite|Lage|Stäbe|Bügel|Stütze|Auflager|Schub|Druck|Zug|Biegung|Knicken|Kippen|Sohle|Boden|Erddruck|Grundwasser|Tauwasser|Flanke|Estrich|Querschnitt|Bewehrung|Kraft|Feld)\b')
TEXTS2 = r"""(sel) => { const out=[]; document.querySelectorAll(sel).forEach(R=>{ const w=document.createTreeWalker(R, NodeFilter.SHOW_TEXT);
  while(w.nextNode()){ const n=w.currentNode, p=n.parentElement; if(!p || ['SCRIPT','STYLE','SUB','SUP'].includes(p.tagName)) continue;
    const t=n.textContent.trim(); if(t && /[A-Za-zÄÖÜäöüß]{3,}/.test(t)) out.push(t); } }); return out; }"""

def langfile(app, l):   # Sprachdatei lang/<app>.<l>.js (window.MULY_LANG = {...};)
    t=open(os.path.join(BASE,'lang',f'{app}.{l}.js'),encoding='utf-8').read(); return json.loads(t[t.index('{'):t.rindex('}')+1])

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        # 1) Schlüssel
        pg=await br.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        de=await pg.evaluate('I18N.de'); LF=langfile('size','en'); en=LF['i18n']
        miss=[k for k in de if not str(en.get(k,'')).strip()]
        check(f'I18N.en hat alle {len(de)} deutschen Schlüssel', not miss, miss[:8])
        extra=[k for k in en if k not in de and k!='langNotice']
        check('I18N.en ohne verwaiste Schlüssel', not extra, extra[:8])
        ph=[k for k in de if k in en and sorted(re.findall(r'\{\d\}',de[k]))!=sorted(re.findall(r'\{\d\}',en[k]))]
        check('Platzhalter {0}… in DE und EN gleich', not ph, ph[:8])
        used=await pg.evaluate("[...new Set([...document.querySelectorAll('[data-i18n]')].map(e=>e.dataset.i18n))]")
        check('jeder data-i18n-Schlüssel steht in I18N.de', all(k in de for k in used), [k for k in used if k not in de][:8])
        src=open(os.path.join(BASE,'size.html'),encoding='utf-8').read()
        i0=src.index('const TTX = {'); src=src[:i0]+src[src.index('const TTR',i0):]   # Wörterbuch selbst nicht mitzählen
        if '/*FRES*/' in src: f0=src.index('/*FRES*/'); src=src[:f0]+src[src.index('/*/FRES*/',f0):]   # FR/ES-Wörterbuch ebenso
        ttx=LF['ttx']; stale=[k for k in ttx if ("'"+k+"'") not in src and ('`'+k) not in src and ('"'+k+'"') not in src and ('>'+k+'<') not in src
               and not ('{}' in k and all(p in src for p in k.split('{}') if p.strip()))]   # Rechenwege: Textteile zwischen den Werten
        check(f'TTX.en: alle {len(ttx)} deutschen Texte kommen im Code vor', not stale, stale[:5])
        # 2) Deutsche Ausgangstexte im HTML = I18N.de (Deutsch bleibt unverändert)
        ctx=await br.new_context(java_script_enabled=False); raw=await ctx.new_page(); await raw.goto(HTML)
        pairs=await raw.evaluate("[...document.querySelectorAll('[data-i18n]')].map(e=>[e.dataset.i18n, e.innerHTML])")
        norm=lambda h: re.sub(r'\s+',' ',h.replace('&amp;','&').replace('&gt;','>').replace('&lt;','<').replace('&nbsp;',' ')).strip()
        bad=[k for k,h in pairs if norm(h)!=norm(de[k])]
        check(f'{len(pairs)} Elemente: HTML-Text = I18N.de', not bad, bad[:6]); await ctx.close()
        # DE-Oberfläche nach applyI18n
        s=await pg.inner_text('#summary'); check('DE: Zusammenfassung deutsch', s.startswith('Alle Nachweise erfüllt · größte Ausnutzung'), s)
        check('DE: Rechenschritte-Leiste deutsch', 'Rechenschritte' in await pg.inner_text('.det-bar'))
        check('DE: kein Sprachhinweis', await pg.evaluate("!document.querySelector('.lang-notice')"))
        # 3) Englisch: alle Modi
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(250)
        n=await pg.evaluate("document.querySelector('.lang-notice')?.textContent||''")
        check('EN: kein Sprachhinweis mehr (seit v0.5.33)', n=='', n)
        left={}
        for mat,fn,modes in MODES:
            for m in modes:
                await pg.evaluate(f"setMat('beton'); setTyp('{m}')" if mat=='beton' else f"setMat('{mat}'); {fn}('{m}')")
                await pg.wait_for_timeout(40)
                for t in await pg.evaluate(TEXTS, UI):
                    if GER.search(t): left.setdefault(t[:70], f'{mat}/{m}')
        check('EN: 31 Nachweise ohne deutsche Reste in der Oberfläche', not left, list(left.items())[:6])
        # Rechenwege, Ergebnis, Abbildungen und Bericht (seit v0.5.18)
        left2={}; RES='#summary, #chk-table, #details, #fig, #reinf-line'
        for mat,fn,modes in MODES:
            for m in modes:
                await pg.evaluate(f"setMat('beton'); setTyp('{m}')" if mat=='beton' else f"setMat('{mat}'); {fn}('{m}')")
                await pg.wait_for_timeout(40)
                await pg.evaluate("showReport()")
                for t in await pg.evaluate(TEXTS2, RES+', #report'):
                    if GER2.search(t): left2.setdefault(t[:70], f'{mat}/{m}')
                await pg.evaluate("document.body.classList.remove('show-report')")
        check('EN: Rechenwege, Abbildungen, Berichte ohne deutsche Reste', not left2, list(left2.items())[:6])
        await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.wait_for_timeout(60)
        det=await pg.inner_text('#details')
        check('EN: Dezimalpunkt in Rechenwegen', '0.9·d' in det and '1.15' in det and not re.search(r'\d,\d', det), re.findall(r'.{20}\d,\d.{10}', det)[:3])
        rep=await pg.evaluate("buildReport()")
        check('EN: Bericht englisch mit Datum en-GB', 'Learning tool' in rep and re.search(r'\d\d/\d\d/\d{4}', rep) is not None)
        await pg.evaluate("setMat('beton'); setTyp('balken')"); await pg.wait_for_timeout(60)
        s=await pg.inner_text('#summary'); check('EN: Zusammenfassung', s.startswith('All checks satisfied · max. utilisation'), s)
        check('EN: Seitentitel (ausgeblendet, Text übersetzt)', (await pg.evaluate("document.getElementById('page-title').textContent")).strip()=='Reinforced concrete — beams, slabs, columns, punching')
        check('EN: Kennzeichen „satisfied“', 'satisfied' in await pg.inner_text('#chk-table'))
        bar=await pg.inner_text('.det-bar'); check('EN: Leiste Rechenschritte', 'Calculation steps' in bar and 'Expand all' in bar, bar)
        await pg.click('.det-bar .det-all'); check('EN: Knopf „Collapse all“', 'Collapse all' in await pg.inner_text('.det-bar'))
        opt=await pg.evaluate("$('in-expo').options[2].text"); check('EN: Expositionsklasse übersetzt', opt=='XC3 — moderate humidity', opt)
        await pg.fill('#in-l','0'); await pg.dispatch_event('#in-l','input'); await pg.wait_for_timeout(60)
        s=await pg.inner_text('#summary'); check('EN: Eingabefehler englisch', s.startswith('Please check the input') and not GER.search(s), s)
        await pg.fill('#in-l','6'); await pg.dispatch_event('#in-l','input')
        await pg.fill('#in-name','Pos 1'); await pg.evaluate('savePos()')
        check('EN: Position gespeichert', await pg.inner_text('#pos-msg')=='“Pos 1” saved.', await pg.inner_text('#pos-msg'))
        meta=await pg.inner_text('#pos-list'); check('EN: Positionsliste englisch', 'Rectangular beam' in meta and 'all checks satisfied' in meta and re.search(r'\d\d/\d\d/\d{4}', meta), meta)
        await pg.evaluate("$('in-l').value=0; run()"); await pg.wait_for_timeout(40)
        ms=await pg.inner_text('#mob-status'); check('EN: Mobilstatus', ms=='Please check the input', ms)
        ci=await pg.inner_text('#ci-msg'); check('EN: calc-Import ohne Berechnung', ci.startswith('No calculation saved yet'), ci)
        await pg.evaluate("setMat('beton'); setTyp('stuetze')"); await pg.wait_for_timeout(40)
        check('EN: Stütze Label Dicke', 'Thickness h [cm] (in the plane of bending)' in await pg.inner_text('.col-in'))
        await pg.evaluate("$('ws-B') && 0; setMat('mauer'); setMwMode('druck'); $('md-t').value=-1; run()"); await pg.wait_for_timeout(40)
        s=await pg.inner_text('#summary'); check('EN: Fehler Mauerwerk ohne Deutsch', s.startswith('Please check the input') and not GER.search(s), s)
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
