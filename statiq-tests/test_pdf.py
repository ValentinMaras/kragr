# PDF-Datei statt Druckdialog (calc v0.11.39 · size v0.7.42 · projekt v0.1.39, 11.11.2026): k5/pdf.js erzeugt aus dem Bericht
# eine echte PDF (html2canvas + jsPDF) mit der Druckansicht (Schriftfeld, zwei Spalten).
# Seit calc v0.11.42 (12.11.2026): Schriftfeld oben auf jeder Seite, Blanko statt Karo, Berichtsfuß in der Fußzeile jeder Seite. Am Rechner Download,
# am Handy zwei Tipps: „PDF erstellen“ → „PDF teilen“ (Teilen-Menü mit Datei). Ohne Playwright: SKIP.
import os, sys, asyncio, re
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:74}', str(info)[:230])
TMP=os.path.join(HERE,'__pycache__'); os.makedirs(TMP, exist_ok=True)
def pdfinfo(path):
    b=open(path,'rb').read(); return b[:5]==b'%PDF-', len(re.findall(rb'/Type\s*/Page[^s]', b)), len(b)
SHARE="""window.__shared=[]; Object.defineProperty(navigator,'canShare',{value:(d)=>!!(d&&d.files),configurable:true});
  Object.defineProperty(navigator,'share',{value:(d)=>{ window.__shared.push(d.files.map(f=>[f.name,f.type,f.size])); return Promise.resolve(); },configurable:true});"""

async def save_sheets(pg):
    await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
    await pg.evaluate("showTab('frame')"); await pg.wait_for_timeout(400)
    await pg.click('#tab-frame .kbl-btn'); await pg.fill('#tab-frame .kbl-in','Pos. 1 Rahmen'); await pg.click('#tab-frame .kbl-ok'); await pg.wait_for_timeout(300)
    await pg.goto(B+'size.html'); await pg.wait_for_timeout(800); await pg.evaluate("setMat('holz'); setHoMode('bauteil')"); await pg.wait_for_timeout(300)
    await pg.click('.kbl-btn'); await pg.fill('.kbl-in','Pos. 2 Holzträger'); await pg.click('.kbl-ok'); await pg.wait_for_timeout(400)

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); errs=[]
        # ── Rechner: Download ──
        ctx=await br.new_context(viewport={'width':1280,'height':900}, accept_downloads=True); pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await save_sheets(pg)
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(600)
        check('Rechenblätter: kein Druckdialog mehr am Bericht', await pg.evaluate("!document.querySelector('#report-view [onclick*=\"print\"]')"))
        await pg.click('.bl:nth-child(1) button.p'); await pg.wait_for_timeout(500)
        b=pg.locator('[data-kragr-pdf]'); check('Knopf „PDF erstellen“', await b.inner_text()=='PDF erstellen', await b.inner_text())
        async with pg.expect_download(timeout=90000) as dl: await b.click()
        d=await dl.value; f=os.path.join(TMP,'t_size.pdf'); await d.save_as(f); ok,n,sz=pdfinfo(f)
        check('Bemessung (Rechenblätter): Download „Pos. 2 Holzträger.pdf“, echte PDF mit Seiten', d.suggested_filename=='Pos. 2 Holzträger.pdf' and ok and n>=2 and sz>50000, (d.suggested_filename, n, sz))
        check('Druckansicht bleibt nicht hängen (Stil und Hinweis entfernt)', await pg.evaluate("!document.querySelector('style[data-kragr-pdf-print], .kragr-pdf-ov') && !document.body.classList.contains('kragr-pdf')"))
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(500); await pg.click('.bl:nth-child(2) button.p'); await pg.wait_for_timeout(1800)
        b=pg.locator('[data-kragr-pdf]')
        async with pg.expect_download(timeout=120000) as dl: await b.click()
        d=await dl.value; f=os.path.join(TMP,'t_calc.pdf'); await d.save_as(f); ok,n,sz=pdfinfo(f)
        check('Schnittkräfte-Bericht: „Pos. 1 Rahmen.pdf“ mit mehreren Seiten', d.suggested_filename=='Pos. 1 Rahmen.pdf' and ok and n>=3, (d.suggested_filename, n, sz))
        r=await pg.evaluate("(()=>{ const el=document.getElementById('report-content'); return [el.getAttribute('style')||'', window.scrollY>=0]; })()")
        check('Bericht danach unverändert (Breite und Lage zurückgesetzt)', 'absolute' not in r[0], r)
        r=await pg.evaluate("[document.querySelectorAll('#report-content svg').length, document.querySelectorAll('#report-content canvas').length, !!document.querySelector('#report-content .k-reflink') && [...document.querySelectorAll('#report-content .k-reflink')].some(a=>a.offsetHeight>0)]")
        check('SVG nach der Aufnahme wieder da (keine Ersatzbilder übrig), Verweis auf „Wissen“ im Rechenblatt verborgen', r[0]>=4 and r[1]==0 and not r[2], r)
        # Aufnahme: jede Skizze wird vorab selbst gerastert (html2canvas schnitt die Systemskizze ab und versetzte das „r“ der Wortmarke)
        r=await pg.evaluate("""(async()=>{ const el=document.getElementById('report-content'); let seen=null; const o=window.html2canvas;
          window.html2canvas=function(e,opt){ if(!seen) seen=[e.querySelectorAll('svg').length, e.querySelectorAll('canvas').length]; return o(e,opt); };
          try{ await kragrPdf(el,'t'); } finally { window.html2canvas=o; } return seen; })()""")
        check('Während der Aufnahme: keine SVG, nur gerasterte Bilder', r and r[0]==0 and r[1]>=4, r)
        # Kopf auf jeder Seite: das Schriftfeld wird einmal vorab aufgenommen (flacher Streifen), der Berichtsfuß steht in der Seitenfußzeile
        r=await pg.evaluate("""(async()=>{ const el=document.getElementById('report-content'); const calls=[]; const o=window.html2canvas; let foot=null, sfh=0;
          window.html2canvas=function(e,opt){ calls.push(Math.round(opt.height)); foot=getComputedStyle(e.querySelector('.rb-foot')).display; if(!sfh){ sfh=Math.round(e.querySelector('.rb-sf').getBoundingClientRect().height); } return o(e,opt); };
          let f; try{ f=await kragrPdf(el,'t'); } finally { window.html2canvas=o; }
          const b=new Uint8Array(await f.arrayBuffer()); let s=''; for(let i=0;i<b.length;i++) s+=String.fromCharCode(b[i]);
          const ft=el.querySelector('.rb-foot');
          return {calls, foot, sfh, pages:(s.match(/\\/Type\\s*\\/Page[^s]/g)||[]).length, after:[getComputedStyle(ft).display, ft.hasAttribute('data-kragr-pdf-off')],
            grid:getComputedStyle(el.querySelector('.rb-grid')).backgroundImage}; })()""")
        check('Schriftfeld wird vorab einzeln aufgenommen (erste Aufnahme = Höhe des Schriftfelds, danach eine je Seite)', r['calls'][0]<=r['sfh']+3 and r['sfh']<70 and len(r['calls'])==r['pages']+1 and r['pages']>=3, (r['calls'], r['sfh'], r['pages']))
        check('Seiten ab der zweiten sind um den Kopf kürzer', r['calls'][1]<=1115 and max(r['calls'][2:])<=1115-r['sfh']-14, r['calls'])
        check('Berichtsfuß während der Aufnahme aus (steht in der Seitenfußzeile), danach wieder da', r['foot']=='none' and r['after'][0]!='none' and not r['after'][1], (r['foot'], r['after']))
        check('Schnittkräfte-Bericht: Rechenweg blanko, kein Karo', r['grid']=='none', r['grid'])
        await ctx.close()
        # ── Handy: zwei Tipps, Teilen-Menü mit PDF-Datei ──
        ctx=await br.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True); pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await ctx.add_init_script(SHARE)
        await save_sheets(pg)
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(600); await pg.click('.bl:nth-child(1) button.p'); await pg.wait_for_timeout(500)
        b=pg.locator('[data-kragr-pdf]'); await b.click()
        await pg.wait_for_function("document.querySelector('[data-kragr-pdf]').textContent==='PDF teilen'", timeout=90000)
        check('Handy: nach dem Erstellen heißt der Knopf „PDF teilen“, noch nichts geteilt', await pg.evaluate("window.__shared.length")==0)
        await b.click(); await pg.wait_for_timeout(300); sh=await pg.evaluate("window.__shared")
        check('Handy: zweiter Tipp öffnet das Teilen-Menü mit der PDF-Datei', len(sh)==1 and sh[0][0][0]=='Pos. 2 Holzträger.pdf' and sh[0][0][1]=='application/pdf' and sh[0][0][2]>50000, sh)
        await pg.click('#report-view button[onclick="hideReport()"]'); await pg.wait_for_timeout(200)
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(600)
        await pg.click('.bl:nth-child(1) button.p'); await pg.wait_for_timeout(400)
        check('Englisch: „Create PDF“', await pg.locator('[data-kragr-pdf]').inner_text()=='Create PDF', await pg.locator('[data-kragr-pdf]').inner_text())
        await ctx.close()
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
    print('FAILS:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
