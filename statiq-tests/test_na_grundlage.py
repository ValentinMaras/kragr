# Bemessungsgrundlage (calc v0.11.20 · size v0.7.22 · ref v0.3.58 · projekt v0.1.27; Österreich seit size v0.7.23): Auswahl im Menü (DE und AT aktiv),
# Marke „NA DE“ an Größen aus dem nationalen Anhang im Rechenweg, Hinweis oben in den Ergebnissen, nicht im Bericht und nicht im Druck.
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
MARKS="[...document.querySelectorAll('#details .steps .na-t')].map(b=>b.dataset.sy)"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':390,'height':844}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        # Menü
        await pg.click('#k5-burger'); await pg.wait_for_selector('#k5-menu.open'); await pg.wait_for_timeout(200)
        r=await pg.evaluate("""(()=>{const g=document.getElementById('k5-na'); const bs=[...g.querySelectorAll('button')];
          return {codes:bs.map(b=>b.textContent), on:bs.filter(b=>!b.disabled).map(b=>b.dataset.v), pressed:bs.filter(b=>b.getAttribute('aria-pressed')==='true').map(b=>b.dataset.v),
            sub:g.closest('.k5-row').querySelector('.k5-rt').textContent, soon:bs[1].title, order:[...document.querySelectorAll('#k5-menu .k5-rt')].map(e=>e.firstChild.textContent)}})()""")
        check('Menü: Bemessungsgrundlage DE AT CH FR ES UK, alle außer CH wählbar, DE gewählt', r['codes']==['DE','AT','CH','FR','ES','UK'] and r['on']==['de','at','fr','es','uk'] and r['pressed']==['de'], r)
        check('Menü: Untertitel „Nationaler Anhang: Deutschland“, CH „in Vorbereitung“', 'Nationaler Anhang: Deutschland' in r['sub'] and await pg.evaluate("document.querySelector('#k5-na button[data-v=ch]').title")=='Schweiz – in Vorbereitung', r['sub'])
        await pg.click('#k5-na button[data-v="ch"]', force=True); await pg.wait_for_timeout(100)
        check('Klick auf CH ändert nichts (deaktiviert)', await pg.evaluate("kragrNA()")=='de' and await pg.evaluate("localStorage.getItem('kragr-na')") in (None,'de'))
        await pg.evaluate("localStorage.setItem('kragr-na','ch')"); check('gespeichertes, noch nicht verfügbares Land (CH) fällt auf DE zurück', await pg.evaluate("kragrNA()")=='de')
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        # Marken im Rechenweg
        await pg.evaluate("setMat('beton')"); await pg.wait_for_timeout(500)
        m=await pg.evaluate(MARKS)
        check('Stahlbeton: γc, γs, αcc markiert', any('γc' in x for x in m) and any('γs' in x for x in m) and any('αcc' in x for x in m), m)
        check('keine falsche Marke in Wörtern („Fachwerkmodell“ ≠ kmod)', not any('kmod' in x for x in m), m)
        t=await pg.evaluate("document.querySelector('#details .steps .na-t').textContent")
        check('Marke lautet „NA DE“', t=='NA DE', t)
        h=await pg.evaluate("[!!document.querySelector('#details > .na-hint, #details .na-hint'), (document.querySelector('#details .na-hint')||{}).textContent]")
        check('Hinweis oben in den Ergebnissen erklärt die Marke', h[0] and 'nationale Anhang' in h[1] and 'Bemessungsgrundlage' in h[1], h)
        for mat,sym in [('stahl','γM0'),('holz','kmod'),('mauer','γM'),('grund','γR,v')]:
            await pg.evaluate(f"setMat('{mat}')"); await pg.wait_for_timeout(500); m=await pg.evaluate(MARKS)
            check(f'{mat}: {sym} markiert, jede Größe je Rechenweg nur einmal', any(sym in x.split(', ') for x in m) and all(len(set(x.split(', ')))==len(x.split(', ')) for x in m), m)
        await pg.evaluate("setMat('beton')"); await pg.wait_for_timeout(500)
        await pg.evaluate("showReport()"); await pg.wait_for_timeout(500)
        check('Bericht ohne Marken', await pg.evaluate("document.querySelectorAll('#report .na-t').length")==0)
        await pg.evaluate("hideReport && hideReport()"); await pg.wait_for_timeout(200)
        await pg.emulate_media(media='print'); d=await pg.evaluate("getComputedStyle(document.querySelector('#details .na-t')).display"); await pg.emulate_media(media='screen')
        check('im Druck ausgeblendet', d=='none', d)
        # Sprachen
        for L,abbr,word in [('en','NA DE','National Annex'),('fr','AN DE','annexe nationale'),('es','AN DE','anejo nacional')]:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(800)
            r=await pg.evaluate("[document.querySelector('#details .steps .na-t').textContent, document.querySelector('#details .na-hint').textContent]")
            check(f'{L}: Marke „{abbr}“, Hinweis übersetzt', r[0]==abbr and word in r[1], r)
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        # ref: Rechenweg im Wissen
        await pg.goto(B+'ref.html#/stahlbeton/bemessung/biegung'); await pg.wait_for_timeout(800)
        m=await pg.evaluate("[...document.querySelectorAll('#main .steps .na-t')].map(b=>b.dataset.sy)")
        check('Wissen: Rechenweg Biegung markiert αcc und γc', any('αcc' in x and 'γc' in x for x in m), m)
        # projekt: Menü auch dort
        await pg.goto(B+'projekt.html'); await pg.wait_for_timeout(500); await pg.click('#k5-burger'); await pg.wait_for_timeout(300)
        check('Rechenblätter: Bemessungsgrundlage im Menü', await pg.evaluate("!!document.getElementById('k5-na')"))
        # ── Österreich (size v0.7.23) — Sollwerte von Hand ──
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(800)
        await pg.click('#k5-burger'); await pg.wait_for_selector('#k5-menu.open'); await pg.click('#k5-na button[data-v="at"]'); await pg.wait_for_timeout(400)
        r=await pg.evaluate("[kragrNA(), localStorage.getItem('kragr-na'), document.querySelector('#k5-na').closest('.k5-row').querySelector('.k5-rt > span').textContent]")
        check('AT wählen: gespeichert, Untertitel „Nationaler Anhang: Österreich“', r==['at','at','Nationaler Anhang: Österreich'], r)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        # Standardbalken C30/37, XC1, b/h = 300/600, Bügel Ø8, 2 Ø 25: c_min,dur = 15, Δc_dev = 5 → c_nom Bügel 20, Längsstab 30 → c_v = 22, d = 600 − 22 − 8 − 12,5 = 557,5 mm
        # f_cd = 1,0·30/1,5 = 20 N/mm² (α_cc = 1,0), A_s,min = max(0,26·2,9/500; 0,0013)·300·557,5 = 0,001508·300·557,5 = 252,2 mm²
        r=await pg.evaluate("(()=>{ const t=document.querySelector('#n-biegung .steps').textContent, d=document.querySelector('#n-deckung .steps').textContent; return [t.includes('= 1,0 · 30 / 1,5= 20,00'), d.includes('= 600 − 22 − 8 − 12,5= 557,5'), t.includes('= 2,52 cm²'), t.includes('9.2.1.1'), d.includes('Δcdev = 5 mm')]; })()")
        check('AT Beton: α_cc = 1,0 → f_cd = 20,00; d = 557,5 mm (Δc_dev = 5); A_s,min = 2,52 cm² nach EN 9.2.1.1', all(r), r)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].map(c=>[c.id.slice(2), c.querySelector('.steps').textContent.startsWith('Für Österreich')])")
        check('AT Beton: Deckung, Biegung, Querkraft und Rissbreite gerechnet, übrige als Hinweis', all(h==(i not in ('deckung','biegung','querkraft','riss')) for i,h in r), r)
        t=await pg.evaluate("document.querySelector('#n-riss .steps').textContent")
        check('AT Rissbreite: s_r,max wie DE (k3 = 0), w_max nach Tab. 7.1N', 'Tab. 7.1N' in t and 'Tab. 7.1DE' not in t, t[-80:])
        await pg.evaluate("$('in-zwang').checked=true; run()"); await pg.wait_for_timeout(300)
        check('AT Rissbreite mit Zwang (Gl. 7.7.1DE nicht belegt): als Hinweis', await pg.evaluate("document.querySelector('#n-riss .steps').textContent.startsWith('Für Österreich')"))
        await pg.evaluate("$('in-zwang').checked=false; run()"); await pg.wait_for_timeout(200)
        # Querkraft V_Ed = 160 kN: k = 1 + √(200/557,5) = 1,599; ρ_l = 982/(300·557,5) = 0,587 %; v_Rd,c = 0,18/1,5·1,599·(100·0,00587·30)^(1/3) = 0,499;
        # v_min = 0,035·1,599^1,5·√30 = 0,388; V_Rd,c = 83,5 kN; z = 0,9·d = 501,8; ν1 = 0,6·(1 − 30/250) = 0,528; cot θ = 1,2:
        # V_Rd,max = 300·501,75·0,528·20/(1,2 + 1/1,2) = 781,7 kN; a_sw,erf = 160000/(501,75·434,78·1,2)·10 = 6,11 cm²/m; a_sw,min = 0,15·2,9/434,78·300·10 = 3,00; s_l,max = min(0,75·557,5; 250) = 250
        t=await pg.evaluate("document.querySelector('#n-querkraft .steps').textContent")
        check('AT Querkraft: v_Rd,c 0,499 · v_min 0,388 · V_Rd,c 83,5 · z 501,8 · ν1 0,528 · V_Rd,max 781,7 · a_sw 6,11 / min 3,00 · s_max 250', all(x in t for x in ['= 0,499 N/mm²','= 0,388 N/mm²','83,5 kN','= 501,8 mm','= 0,528','781,7 kN','= 6,11 cm²/m','3,00 cm²/m','= 250 mm']), t[:200])
        await pg.evaluate("$('in-cot').value=2.5; run()"); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#n-querkraft .steps').textContent")
        check('AT Querkraft: cot θ = 2,5 wird auf 1,67 begrenzt (θ ≥ 30,96°)', 'auf den in Österreich zulässigen Bereich' in t and 'cot θ= 1,67' in t.replace(' = ','= '), t[t.find('cot'):t.find('cot')+120])
        await pg.evaluate("$('in-cot').value=1.2; run()"); await pg.wait_for_timeout(200)
        h=await pg.evaluate("document.querySelector('#details .na-hint').textContent")
        check('AT: Hinweis oben nennt die Marke NA AT und die Teilabdeckung', 'NA AT' in h and 'Für Österreich rechnet kragr bisher nur' in h, h)
        m=await pg.evaluate(MARKS); check('AT: Marke im Rechenweg „NA AT“', await pg.evaluate("document.querySelector('#details .steps .na-t').textContent")=='NA AT', m)
        await pg.select_option('#in-expo', 'XS1') if await pg.evaluate("!!document.getElementById('in-expo')") else None
        if await pg.evaluate("!!document.getElementById('in-expo')"):
            await pg.wait_for_timeout(400)
            r=await pg.evaluate("['deckung','biegung'].map(i=>document.querySelector('#n-'+i+' .steps').textContent.startsWith('Für Österreich'))")
            check('AT XS1 (keine c_min,dur im NA hinterlegt): Deckung und Biegung nicht gerechnet', r==[True,True], r)
            await pg.select_option('#in-expo', 'XC1'); await pg.wait_for_timeout(300)
        # Holz BSH GL24h: γ_M = 1,25 (ÖNORM B 1995-1-1)
        await pg.evaluate("setMat('holz'); $('ho-art').value='bsh'; $('ho-art').dispatchEvent(new Event('change')); run()"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[document.querySelector('#n-bem .steps').textContent, document.querySelector('#n-biegung .steps').textContent.startsWith('Für Österreich'), document.querySelector('#n-schub .steps').textContent.startsWith('Für Österreich')]")
        check('AT Holz BSH: γ_M = 1,25 → f_m,d = 16,90; f_v,d = 0,8·2,5/1,25 = 1,60; Biegung und Schub gerechnet', 'γM = 1,25' in r[0] and '24/1,25= 16,90' in r[0] and 'fv,d = 1,60' in r[0] and not r[1] and not r[2], r[0][-160:])
        # Holz Schub (Vollholz C24 100/220, V = 8 kN): f_v,d = 0,8·2,3/1,3 = 1,42; τ_d = 1,5·8000/(100·220) = 0,55 N/mm²
        await pg.evaluate("$('ho-art').value='vh'; $('ho-art').dispatchEvent(new Event('change')); run()"); await pg.wait_for_timeout(400)
        t=await pg.evaluate("document.querySelector('#n-schub .steps').textContent")
        check('AT Holz Schub: f_v,k = 2,3 (k_cr = 1), f_v,d = 1,42, τ_d = 0,55 N/mm²', 'fv,k = 2,3' in t and '= 1,42 N/mm²' in t and '0,55 N/mm²' in t, t[:200])
        await pg.evaluate("$('ho-Llt').value=4; $('ho-art').value='vh'; run()"); await pg.wait_for_timeout(300)
        k1=await pg.evaluate("document.querySelector('#n-kipp .steps').textContent.startsWith('Für Österreich')")
        await pg.evaluate("$('ho-art').value='bsh'; run()"); await pg.wait_for_timeout(300)
        k2=await pg.evaluate("document.querySelector('#n-kipp .steps').textContent.startsWith('Für Österreich')")
        check('AT Holz Kippen: Vollholz gerechnet (EN-Formel), BSH als Hinweis (DE-Faktor 1,4 nicht belegt)', not k1 and k2, (k1,k2))
        await pg.evaluate("$('ho-Llt').value=0; $('ho-art').value='vh'; run()"); await pg.wait_for_timeout(200)
        # Stahl IPE 300, S235, M = 90 kNm, Kipplänge 3 m: M_b,Rd = χ_LT,mod·W·f_y/γ_M1 = 0,801·147,7/1,0 = 118,3 kNm (DE mit 1,1: 107,6)
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].map(c=>[c.id.slice(2), c.querySelector('.steps').textContent.startsWith('Für Österreich')])")
        check('AT Stahl: Querschnitt, Querkraft und Biegedrillknicken gerechnet, Durchbiegung als Hinweis', all(h==(i=='w') for i,h in r), r)
        t=await pg.evaluate("document.querySelector('#n-bdk .steps').textContent")
        check('AT Stahl: γ_M1 = 1,0 → M_b,Rd = 118,3 kNm', '= 118,3 kNm' in t, t[-160:])
        # zurück auf DE: Werte wie vorher
        await pg.evaluate("localStorage.setItem('kragr-na','de')"); await pg.reload(); await pg.wait_for_timeout(800); await pg.evaluate("setMat('beton')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("document.querySelector('#n-biegung .steps').textContent")
        check('DE wieder: f_cd = 0,85·30/1,5 = 17,00', '= 0,85 · 30 / 1,5= 17,00' in r, r[:160])
        # Wissen bei AT: Marke bleibt NA DE, Hinweis oben auf der Seite
        await pg.evaluate("localStorage.setItem('kragr-na','at')"); await pg.goto(B+'ref.html#/stahlbeton/bemessung/biegung'); await pg.wait_for_timeout(800)
        r=await pg.evaluate("[document.querySelector('#main .na-t').textContent, (document.querySelector('#main .na-ref')||{}).textContent||'']")
        check('Wissen bei AT: Marke „NA DE“, Hinweis „noch nicht hinterlegt“ für Österreich', r[0]=='NA DE' and 'Für Österreich' in r[1], r)
        await pg.evaluate("localStorage.setItem('kragr-na','de')")
        # ── UK (size v0.7.26 · calc v0.11.22) — Sollwerte von Hand ──
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de'); localStorage.setItem('kragr-na','uk')"); await pg.reload(); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[kragrNA(), getComputedStyle(document.querySelector('.na-in-cdur')).display, $('in-cmindur').value]")
        check('UK: Eingabe c_min,dur nach BS 8500 sichtbar (Vorgabe 15 mm)', r==['uk','block','15'], r)
        await pg.evaluate("$('in-auto') && ($('in-auto').checked=false); run()"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].map(c=>[c.id.slice(2), c.querySelector('.steps').textContent.startsWith('Für')])")
        check('UK Beton: Deckung, Biegung, Querkraft und Rissbreite gerechnet, übrige als Hinweis', all(h==(i not in ('deckung','biegung','querkraft','riss')) for i,h in r), r)
        # Rissbreite UK (EN 7.3.4(3)): c = c_v + Ø_w = 25 + 8 = 33 mm; s_r,max = 3,4·33 + 0,8·0,5·0,425·16/0,03269 = 112,2 + 83,2 = 195 mm; w_max = 0,3 mm
        t=await pg.evaluate("document.querySelector('#n-riss .steps').textContent")
        check('UK Rissbreite: s_r,max = 3,4·33 + 0,8·0,5·0,425·Ø/ρ = 195 mm, w_max = 0,3 mm', '= 3,4·33 + 0,8·0,5·0,425·16/0,0327= 195 mm' in t.replace(' = ','= ') and '0,3 mm (XC1, BS EN 1992-1-1/NA)' in t, t[t.find('sr,max'):t.find('sr,max')+120])
        # Bügel Ø8: c_nom = max(15; 8; 10) + Δc_dev 10 = 25 mm; f_cd = 0,85·30/1,5 = 17,00; Querkraft: α_cc = 1,0 → f_cd = 20,00 für die Druckstrebe; a_sw,min = 0,08·√30/500·300·10 = 2,63 cm²/m; s_l,max = 0,75·d
        t=await pg.evaluate("[document.querySelector('#n-deckung .steps').textContent, document.querySelector('#n-biegung .steps').textContent, document.querySelector('#n-querkraft .steps').textContent]")
        check('UK Deckung: c_nom Bügel = max(15; 8; 10) + 10 = 25 mm', '= max(15; 8; 10) + 10= 25 mm' in t[0], t[0][:120])
        check('UK Biegung: f_cd = 0,85·30/1,5 = 17,00, A_s,min nach EN 9.2.1.1', '= 0,85 · 30 / 1,5= 17,00' in t[1] and '9.2.1.1' in t[1], '')
        check('UK Querkraft: f_cd(Strebe) = 20,00 mit α_cc = 1,0; a_sw,min = 2,63 cm²/m; s_l,max = 0,75·d', 'αcc = 1,0: 20,00 N/mm²' in t[2] and '2,63 cm²/m' in t[2] and 'sl,max= 0,75·d=' in t[2].replace(' = ','= '), t[2][-240:])
        await pg.evaluate("$('in-cot').value=3; run()"); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#n-querkraft .steps').textContent")
        check('UK Querkraft: cot θ = 3 wird auf 2,5 begrenzt', 'auf den zulässigen Bereich 1,0 … 2,5 begrenzt' in t, '')
        await pg.evaluate("$('in-cot').value=1.2; $('in-cmindur').value=''; run()"); await pg.wait_for_timeout(300)
        check('UK ohne c_min,dur: Deckung und Biegung nicht gerechnet', await pg.evaluate("['deckung','biegung'].every(i=>document.querySelector('#n-'+i+' .steps').textContent.startsWith('Für'))"))
        await pg.evaluate("$('in-cmindur').value=15; run()")
        # Stahl IPE 300: γ_M1 = 1,0, Kurve b, f = 1 → M_b,Rd = 0,778·147,7/1,0 = 114,9 kNm (Anzeige 114,8 aus ungerundetem χ)
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(500)
        t=await pg.evaluate("document.querySelector('#n-bdk .steps').textContent")
        check('UK Stahl: f = 1 (NA.2.18 nicht angesetzt), χ_LT,mod = 0,778, M_b,Rd = 114,8 kNm', 'f = 1 (sichere Seite)' in t and '= 0,778' in t and '= 114,8 kNm' in t, t[-200:])
        # Schnittkräfte UK: Einfeldträger g = 5 kN/m (G), F = 10 kN Mitte (Q, Kat. A): 6.10a 1,35·15,625 + 1,5·0,7·12,5 = 34,22; 6.10b 0,925·1,35·15,625 + 1,5·12,5 = 38,26 kNm → maßgebend 6.10b
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("loads.beam.point[0].values.lf='Q'; document.getElementById('lf-on-beam').checked=true; lfCfg('beam')"); await pg.wait_for_timeout(700)
        lf=await pg.evaluate("lastCalc.beam.lf")
        check('UK Schnittkräfte: max M = ξ·1,35·G + 1,5·Q = 38,26 kNm (Gl. 6.10b)', abs(lf['gov']['maxM']['v']-38.26172)<0.002 and lf['gov']['maxM']['formula']=='1,249·G + 1,5·Q', lf['gov']['maxM'])
        rA=lf['reac'][0]
        check('UK Auflager A: V max = 0,925·1,35·12,5 + 1,5·5 = 23,11 kN', abs(rA['V'][0]-23.1094)<0.002, rA)
        t=await pg.evaluate("document.querySelector('#beam-results .k-lfres').textContent")
        check('UK Karte: Formel Gl. 6.10a/6.10b mit ξ = 0,925', '6.10a' in t and '0,925' in t, t[-200:])
        await pg.evaluate("localStorage.setItem('kragr-na','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("loads.beam.point[0].values.lf='Q'; document.getElementById('lf-on-beam').checked=true; lfCfg('beam')"); await pg.wait_for_timeout(700)
        check('DE wieder: max M = 39,84 kNm (Gl. 6.10)', abs(await pg.evaluate("lastCalc.beam.lf.gov.maxM.v")-39.84375)<0.002)
        # ── Frankreich (size v0.7.28 · calc v0.11.24) — Sollwerte von Hand ──
        # Schnittkräfte: NF EN 1990/NA Gl. 6.10, γ und ψ wie DE: max M = 1,35·15,625 + 1,5·12,5 = 39,84 kNm
        await pg.evaluate("localStorage.setItem('kragr-na','fr')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("loads.beam.point[0].values.lf='Q'; document.getElementById('lf-on-beam').checked=true; lfCfg('beam')"); await pg.wait_for_timeout(700)
        r=await pg.evaluate("[lastCalc.beam.lf.gov.maxM.v, document.querySelector('#beam-results .k-lfres').textContent]")
        check('FR Schnittkräfte: max M = 1,35·G + 1,5·Q = 39,84 kNm, Formel „NF EN 1990/NA (FR), Gl. 6.10“', abs(r[0]-39.84375)<0.002 and 'NF EN 1990/NA (FR), Gl. 6.10' in r[1], r[0])
        # Bemessung Stahlbeton (Vorgabe Balken 30/60, C30/37, XC1, 2 Ø 25, Bügel Ø8/15): c_min,dur = 15 (Tab. 4.4N, S4), Δc_dev = 10
        #   Bügel c_nom = max(15; 8; 10) + 10 = 25; Längsstab max(15; 25; 10) + 10 = 35 → über Bügel 27 → c_v = 27, d = 600 − 27 − 8 − 12,5 = 552,5 mm
        #   f_cd = 1,0·30/1,5 = 20,00; Rissbreite: h_c,ef = min(2,5·47,5; 300) = 118,8 mm; c = 27 + 8 = 35 > 25 → k3 = 3,4·(25/35)^(2/3) = 2,717;
        #   s_r,max = 2,717·35 + 0,8·0,5·0,425·25/0,02756 = 95,1 + 154,2 = 249 mm; w_max (XC1) = 0,4 mm
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de'); localStorage.setItem('kragr-na','fr')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("$('in-auto') && ($('in-auto').checked=false); run()"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].map(c=>[c.id.slice(2), c.querySelector('.steps').textContent.startsWith('Für')])")
        check('FR Beton: Deckung, Biegung, Querkraft und Rissbreite gerechnet, übrige als Hinweis', all(h==(i not in ('deckung','biegung','querkraft','riss')) for i,h in r), r)
        t=await pg.evaluate("['deckung','biegung','querkraft','riss'].map(i=>document.querySelector('#n-'+i+' .steps').textContent.replace(/ = /g,'= '))")
        check('FR Deckung: Bügel max(15; 8; 10) + 10 = 25, Längsstab 35, d = 552,5 mm', '= max(15; 8; 10) + 10= 25 mm' in t[0] and '= max(15; 25; 10) + 10= 35 mm' in t[0] and '= 552,5 mm' in t[0] and 'S4' in t[0], t[0][:160])
        check('FR Biegung: f_cd = 1,0·30/1,5 = 20,00, A_s,min nach EN 9.2.1.1', '= 1,0 · 30 / 1,5= 20,00' in t[1] and '9.2.1.1' in t[1], '')
        check('FR Querkraft: v_min = 0,035·k^1,5·√f_ck, a_sw,min = 2,63 cm²/m, s_l,max = 0,75·d = 414 mm', '0,035 · k1,5' in t[2] and '2,63 cm²/m' in t[2] and 'NF EN 1992-1-1/NA, 9.2.2):sl,max= 0,75·d= 414 mm' in t[2].replace(': ',':'), t[2][-200:])
        check('FR Rissbreite: h_c,ef = 118,8, k3 = 2,717, s_r,max = 249 mm, w_max = 0,4 mm', 'min(2,5·(h−d); h/2)= 118,8 mm' in t[3] and '(25/35)2/3= 2,717' in t[3] and '2,717·35 + 0,8·0,5·0,425·25/0,0276= 249 mm' in t[3] and '0,4 mm (XC1, NF EN 1992-1-1/NA)' in t[3], t[3][t.find('hc,ef') if False else 0:0])
        # XD1: c_min,dur = 35 → Bügel max(35; 8; 10) + 10 = 45; w_max = 0,2 mm
        await pg.evaluate("$('in-expo').value='XD1'; run()"); await pg.wait_for_timeout(300)
        t=await pg.evaluate("['deckung','riss'].map(i=>document.querySelector('#n-'+i+' .steps').textContent.replace(/ = /g,'= '))")
        check('FR XD1: Bügel c_nom = max(35; 8; 10) + 10 = 45 mm, w_max = 0,2 mm', '= max(35; 8; 10) + 10= 45 mm' in t[0] and '0,2 mm (XD1, NF EN 1992-1-1/NA)' in t[1], '')
        # Balken h = 25 cm: s_l,max = 0,9·d
        await pg.evaluate("$('in-expo').value='XC1'; $('in-h').value=25; run()"); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#n-querkraft .steps').textContent.replace(/ = /g,'= ')")
        check('FR Balken h = 250 mm: s_l,max = 0,9·d', 'h ≤ 250 mm):sl,max= 0,9·d=' in t.replace(': ',':'), t[-120:])
        # Stahl: γ_M0 = 1,0 (Querschnitt gerechnet), Biegedrillknicken nicht hinterlegt; Holz ganz als Hinweis
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("Object.fromEntries([...document.querySelectorAll('#details > .card[id^=n-]')].map(c=>[c.id.slice(2), c.querySelector('.steps').textContent.startsWith('Für')]))")
        check('FR Stahl: Querschnitt gerechnet, Biegedrillknicken als Hinweis', r.get('qs')==False and r.get('qv')==False and r.get('bdk')==True, r)
        t=await pg.evaluate("document.querySelector('#n-qs .steps').textContent")
        check('FR Stahl: γM0 = 1,0, M_c,Rd = 147,7 kNm', '(γM0 = 1,0)' in t and '147,7 kNm' in t, '')
        await pg.evaluate("setMat('holz')"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].every(c=>c.querySelector('.steps').textContent.startsWith('Für Frankreich'))")
        check('FR Holz: alle Nachweise als Hinweis (keine belegte Quelle)', r)
        # ── Spanien (size v0.7.29 · calc v0.11.25) — Anejos Nacionales des Ministerio de Transportes; Sollwerte von Hand ──
        #   Balken 30/60, C30/37, XC1, 2 Ø 25, Bügel Ø8/15: c_min,dur = 15 (Tab. AN/3, S4) → wie FR d = 552,5 mm; f_cd = 20,00
        #   A_s,min = W/(0,8·h)·f_ctm,fl/f_yd = 18,0·10⁶/480·2,90/434,8 = 2,50 cm²; v_min = 0,075/1,5·1,602^1,5·√30 = 0,555 → V_Rd,c = 92,0 kN
        #   a_sw,min = 2,9/(7,5·500)·300·10 = 2,32 cm²/m; V_Ed/V_Rd,max = 160/774,7 = 0,21 > 1/5 → s_l,max = 0,60·552,5 = 332 mm
        #   Rissbreite EN: s_r,max = 3,4·35 + 0,8·0,5·0,425·25/0,02756 = 273 mm, w_max (XC1) = 0,4 mm
        await pg.goto(B+'size.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de'); localStorage.setItem('kragr-na','es')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("$('in-auto') && ($('in-auto').checked=false); run()"); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[...document.querySelectorAll('#details > .card[id^=n-]')].map(c=>[c.id.slice(2), c.querySelector('.steps').textContent.startsWith('Für')])")
        check('ES Beton: Deckung, Biegung, Querkraft und Rissbreite gerechnet, übrige als Hinweis', all(h==(i not in ('deckung','biegung','querkraft','riss')) for i,h in r), r)
        t=await pg.evaluate("['deckung','biegung','querkraft','riss'].map(i=>document.querySelector('#n-'+i+' .steps').textContent.replace(/ = /g,'= '))")
        check('ES Deckung: Tab. AN/3 (S4), Bügel max(15; 8; 10) + 10 = 25 mm, d = 552,5 mm', '= max(15; 8; 10) + 10= 25 mm' in t[0] and '= 552,5 mm' in t[0] and 'AN/3' in t[0], '')
        check('ES Biegung: A_s,min = W/(0,8·h)·f_ctm,fl/f_yd = 2,50 cm²', '18,00·10⁶/(0,8·600)·2,90/434,8= 2,50 cm²' in t[1] and '= 1,0 · 30 / 1,5= 20,00' in t[1], t[1][t[1].find('As,min'):][:120])
        check('ES Querkraft: v_min = 0,555, V_Rd,c = 92,0 kN, a_sw,min = 2,32 cm²/m, s_l,max = 0,60·d = 332 mm', '= 0,555 N/mm²' in t[2] and '= 92,0 kN' in t[2] and '2,32 cm²/m' in t[2] and '0,60·d ≤ 450 mm= 332 mm' in t[2], t[2][-160:])
        check('ES Rissbreite: s_r,max = 3,4·35 + … = 273 mm, w_max = 0,4 mm (Tab. AN/9)', '3,4·35 + 0,8·0,5·0,425·25/0,0276= 273 mm' in t[3] and '0,4 mm (XC1, UNE-EN 1992-1-1/AN, Tab. AN/9)' in t[3], '')
        await pg.evaluate("$('in-cot').value=0.6; run()"); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.querySelector('#n-querkraft .steps').textContent")
        check('ES Querkraft: cot θ = 0,6 bleibt zulässig (0,5 … 2,0)', 'cot θ= 0,60' in t.replace(' = ','= ') and 'begrenzt' not in t, '')
        await pg.evaluate("$('in-cot').value=1.2; $('in-expo').value='XD1'; run()"); await pg.wait_for_timeout(300)
        check('ES XD1: Deckung und Biegung nicht gerechnet (c_min,dur je nach Zement)', await pg.evaluate("['deckung','biegung'].every(i=>document.querySelector('#n-'+i+' .steps').textContent.startsWith('Für'))"))
        await pg.evaluate("$('in-expo').value='XC1'; run()")
        # Stahl IPE 300, S235: γ_M0 = γ_M1 = 1,05 → N_pl,Rd = 53,8·23,5/1,05 = 1204 kN; M_b,Rd = 0,778·147,7/1,05 = 109,4 kNm (f = 1)
        await pg.evaluate("setMat('stahl')"); await pg.wait_for_timeout(500)
        t=await pg.evaluate("[document.querySelector('#n-qs .steps').textContent, document.querySelector('#n-bdk .steps').textContent]")
        check('ES Stahl: γM0 = 1,05, N_pl,Rd = 1204 kN', '(γM0 = 1,05)' in t[0] and '1204 kN' in t[0], t[0][:200])
        check('ES Stahl: f = 1 (k_c nach Tab. AN/6 nicht angesetzt), M_b,Rd = 109,4 kNm', 'Tab. AN/6' in t[1] and '109,4 kNm' in t[1], t[1][-160:])
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(900)
        await pg.evaluate("loads.beam.point[0].values.lf='Q'; document.getElementById('lf-on-beam').checked=true; lfCfg('beam')"); await pg.wait_for_timeout(700)
        r=await pg.evaluate("[lastCalc.beam.lf.gov.maxM.v, document.querySelector('#beam-results .k-lfres').textContent]")
        check('ES Schnittkräfte: EN-Empfehlung, max M = 39,84 kNm, Hinweis auf fehlenden Anhang A1', abs(r[0]-39.84375)<0.002 and 'Anhang A1' in r[1] and 'DIN' not in r[1], r[0])
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
