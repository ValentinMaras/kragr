# statiq·calc v0.8.15: Französisch und Spanisch ohne englische Reste (Oberfläche, Theorie-Fenster, Rechenweg aller Systeme, Rahmen-Voreinstellungen,
# Kopfhalterung, Durchlaufträger mit Gelenk/Kragarm, Speicherliste, Bericht); Wörterbücher vollständig. Ohne Playwright: SKIP.
import asyncio, re, json, sys
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:160])
import os
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/calc.html'
ENG=re.compile(r"\b(the|and|with|is|are|from|support|supports|load|loads|span|spans|left|right|reactions?|shear|check|beam|beams|frame|frames|column|columns|rafter|hinge|hinges|fixed|roller|please|calculate|calculation|saved?|deflection|step|steps|solution|sum|equilibrium|cantilever|continuous|member|node|nodes|stiffness|determinate|indeterminate|unknown|equation|equations|results?|delete|export|import|report|height|width|length|distributed|uniform|inside|outside|this|that|only|yes|add|remove|new|open|close|show|hide|print|value|values)\b",re.I)
OKW=['Clapeyron','statiq','Statiq','muly','Muly','kragr','calc','size','ref','SDF','kN','kNm','EI','Gerber','PDF','JSON']
TX=r"""() => { const out=[]; const w=document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while(w.nextNode()){ const n=w.currentNode, p=n.parentElement; if(!p || ['SCRIPT','STYLE'].includes(p.tagName)) continue; const t=n.textContent.trim(); if(t && /[A-Za-z]{3,}/.test(t)) out.push([t, p.closest('[id]')?.id||'']); }
  document.querySelectorAll('[placeholder],[title],[aria-label]').forEach(e=>['placeholder','title','aria-label'].forEach(a=>{ const v=e.getAttribute(a); if(v) out.push([v,'@'+a+':'+(e.id||'')]); }));
  return out; }"""
async def main():
    res={}
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1300,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        for L in ('fr','es'):
            miss=await pg.evaluate(f"[...Object.keys(RWT.en).filter(k=>!(k in RWT.{L})), ...Object.keys(MSG.en).filter(k=>!(k in MSG.{L})), ...Object.keys(calcTranslations.en).filter(k=>!(k in calcTranslations.{L}))]")
            check(f'{L}: Rechenweg, Meldungen und Oberfläche vollständig', not miss, miss[:6])
        await pg.evaluate("setCalcLang('de'); openModal('frame')"); await pg.wait_for_timeout(100)
        t=await pg.inner_text('#modal-frame'); check('DE: Theorie Rahmen ohne Englisch („linker Teil“, „Ecke“)', '(linker Teil)' in t and 'left part' not in t)
        await pg.evaluate("document.querySelectorAll('.modal.open').forEach(m=>m.classList.remove('open'))")
        for L in ('fr','es'):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(300)
            left={}
            async def grab(tag):
                for t,i in await pg.evaluate(TX):
                    s=t
                    for w in OKW: s=s.replace(w,'')
                    if ENG.search(s): left.setdefault(t[:90], tag+' #'+i)
            await grab('start')
            for tab,calc in (('beam','calculateBeam()'),('cantilever','calculateCantilever()'),('cont','calculateContinuous()'),('frame','calculateFrame()')):
                await pg.evaluate(f"showTab('{tab}')"); await pg.wait_for_timeout(100)
                await pg.evaluate(f"try{{ {calc} }}catch(e){{}}"); await pg.wait_for_timeout(150)
                await pg.evaluate("document.querySelectorAll('.rw.closed .rw-title, .closed > .rw-title').forEach(e=>e.click())"); await pg.wait_for_timeout(80)
                await grab(tab)
            # Durchlaufträger mit Gelenk und Kragarmen
            await pg.evaluate("showTab('cont'); contCfg.hinges=[{id:5,span:0,a:2}]; contCfg.ovL.L=1.5; contCfg.ovR.L=1; contCfg.supL='fixed'; renderContUI(); calculateContinuous()"); await pg.wait_for_timeout(150)
            await grab('cont-gelenk')
            await pg.evaluate("contCfg.hinges=[]; contCfg.ovL.L=0; contCfg.ovR.L=0; contCfg.supL='pin'; renderContUI(); calculateContinuous()"); await pg.wait_for_timeout(100)
            await grab('cont-kragarm')
            # Rahmen: alle Voreinstellungen, Kopfhalterung
            await pg.evaluate("showTab('frame')")
            ids=await pg.evaluate("[...document.querySelectorAll('[id^=btn-preset-]')].map(b=>b.id)")
            for b in ids:
                await pg.evaluate(f"document.getElementById('{b}').click(); try{{calculateFrame()}}catch(e){{}}"); await pg.wait_for_timeout(120)
                await grab('frame '+b)
            await pg.evaluate("supportHead='left'; supportHeadType='pin'; updateIndetInfo(); try{calculateFrame()}catch(e){}"); await pg.wait_for_timeout(120); await grab('frame head')
            await pg.evaluate("supportHead='none'; updateIndetInfo()")
            # Speichern und Bericht
            await pg.evaluate("showTab('beam'); calculateBeam()"); await pg.wait_for_timeout(100)
            await pg.evaluate("try{ const n=document.querySelector('#save-name-beam, [id^=save-name]'); if(n) n.value='Test'; }catch(e){}")
            await pg.evaluate("try{ (window.saveCalc||window.saveCurrent||(()=>{}))('beam') }catch(e){}")
            await pg.evaluate("showTab('saved')"); await pg.wait_for_timeout(150); await grab('saved')
            keys=await pg.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('statiq_sdf_'))")
            if keys:
                await pg.evaluate(f"openReport('{keys[0]}')"); await pg.wait_for_timeout(300); await grab('report')
                await pg.evaluate("closeReport()")
            check(f'{L}: alle Systeme, Rechenweg und Bericht ohne englische Reste', not left, list(left.items())[:5])
            await pg.evaluate("showTab('beam'); calculateBeam(); document.querySelectorAll('.rw.closed .rw-title').forEach(e=>e.click())"); await pg.wait_for_timeout(100)
            rw=await pg.inner_text('#rw-beam'); check(f'{L}: Rechenweg Einfeldträger übersetzt', ('pas à pas' if L=='fr' else 'paso a paso') in rw and re.search(r'\d,\d', rw), rw[:50])
            await pg.evaluate("showTab('cont'); calculateContinuous(); document.querySelectorAll('.rw.closed .rw-title').forEach(e=>e.click())"); await pg.wait_for_timeout(100)
            rw=await pg.inner_text('#rw-cont'); g=re.findall(r'\b(mit|und|bei|aus|links|rechts|Feld|Felder|Anteil)\b', rw)
            check(f'{L}: Rechenweg Durchlaufträger ohne deutsche Wörter', not g, g[:5])
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
