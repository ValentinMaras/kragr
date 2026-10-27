# Übungsmodus „Lernpfad“ (calc v0.8.34, size v0.5.51): Schritte bleiben sichtbar und zeigen Reihenfolge und Formeln,
# Zahlenwerte der Rechnung sind als „…“ ausgeblendet; Antippen eines Schritts deckt bis dorthin auf; Prüfen findet
# Zwischenwerte auch in noch verdeckten Schritten. Ohne Playwright: SKIP.
# Stufen (calc v0.11.5): Test öffnet alle Stufen und Ergebnis-Karten (Standardzustand prüft test_stufen.py)
import os, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); B='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
TXT="sel=>[...document.querySelectorAll(sel)].map(s=>s.innerText)"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':1000}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B+'calc.html'); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de');localStorage.setItem('statiq-rw-closed','0');localStorage.setItem('statiq-res-fold',JSON.stringify({knoten:false,lfres:false}));localStorage.setItem('statiq-stufen',JSON.stringify({frame:{dims:true,sup:true,loads:true,adv:true},cont:{dims:true,sup:true,loads:true,adv:true},beam:{loads:true,adv:true},cantilever:{loads:true,adv:true}}));localStorage.setItem('muly-uebung','1')"); await pg.reload(); await pg.wait_for_timeout(700)
        st=await pg.evaluate(TXT, '#rw-beam .rw-body > .st')
        heads=[s.split('\n')[0] for s in st]
        check('calc: alle 6 Schritte mit Überschrift sichtbar (Reihenfolge)', len(st)==6 and 'Momentengleichgewicht um A' in st[2] and 'Größtes Moment' in st[5] and all(await pg.evaluate("[...document.querySelectorAll('#rw-beam .rw-body > .st')].map(s=>s.offsetParent!==null)")), heads)
        check('calc: Formeln stehen da (x_R = (a + b)/2, A_V = ΣF_V + ΣR − B_V, M(x₀) = A_V·x₀ − …)', '= (a + b)/2' in st[1] and '= ΣFV + ΣR − BV' in st[3] and '= AV·x₀ − R' in st[5], st[3][:120])
        check('calc: keine Zahlenwerte, nur Lücken „…“ (Einheiten bleiben)', not any(re.search(r'\d+,\d', s) for s in st) and st[2].count('…')>=4 and 'kN' in st[2], st[2][:160])
        r=await pg.evaluate("[document.querySelector('#rw-beam .rw-body > .st .st-h').dataset.rev, getComputedStyle(document.querySelector('#rw-beam .rw-body > .st .st-h'),'::after').content]")
        check('calc: „Schritt zeigen“ an jedem verdeckten Schritt', r[0]=='Schritt zeigen' and 'Schritt zeigen' in r[1], r)
        await pg.fill('#rw-beam .ueb-in','28,13'); await pg.click('#rw-beam .ueb-box button'); m=await pg.inner_text('#rw-beam .ueb-msg')
        check('calc: Prüfen erkennt M_max, obwohl der Schritt verdeckt ist', 'Richtig' in m or 'Stimmt' in m, m)
        await pg.fill('#rw-beam .ueb-in','12,5'); await pg.click('#rw-beam .ueb-box button'); m=await pg.inner_text('#rw-beam .ueb-msg')
        check('calc: Prüfen erkennt Zwischenwert R′ = 12,50 kN aus verdecktem Schritt 6', 'Schritt 6' in m, m)
        await pg.wait_for_timeout(600)   # Live-Rechnung nach der Eingabe ins Prüffeld abwarten (zeichnet den Rechenweg neu)
        await pg.click('#rw-beam .rw-body > .st:nth-of-type(3) .st-h'); await pg.wait_for_timeout(200)
        st=await pg.evaluate(TXT, '#rw-beam .rw-body > .st'); hid=await pg.evaluate("[...document.querySelectorAll('#rw-beam .rw-body > .st')].map(s=>s.classList.contains('ueb-hid'))")
        check('calc: Antippen von Schritt 3 deckt 1–3 auf (mit Zahlen), 4–6 bleiben Lernpfad', hid==[False,False,False,True,True,True] and '17,50 kN' in st[2] and '…' not in st[2] and '…' in st[3], (hid, st[2][-40:]))
        await pg.click('#rw-beam .ueb-box button:has-text("Lösung zeigen")'); await pg.wait_for_timeout(150)
        check('calc: „Lösung zeigen“ stellt alle Zahlen wieder her', '28,13 kNm' in (await pg.evaluate(TXT, '#rw-beam .rw-body > .st'))[5])
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(600)
        st=await pg.evaluate(TXT, '#rw-beam .rw-body > .st')
        check('calc EN: Lernpfad mit Dezimalpunkt ebenfalls ohne Zahlen, „Show step“', not any(re.search(r'\d+\.\d', s) for s in st) and await pg.evaluate("document.querySelector('#rw-beam .st .st-h').dataset.rev")=='Show step', st[2][:100])
        # size
        await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.goto(B+'size.html'); await pg.wait_for_timeout(700)
        st=await pg.evaluate(TXT, '#n-biegung > .steps > .st')
        check('size Biegung: 6 Schritte, Formel μ_Eds = M_Ed / (b·d²·f_cd) sichtbar, Zahlen verdeckt', len(st)==6 and 'μEds=MEd/(b·d²·fcd)' in re.sub(r'\s','',st[1]) and not re.search(r'(^|[^\w.])\d+,\d', st[1]), st[1][:120])
        check('size: Zehnerpotenz 10⁶ bleibt stehen', '…·10⁶' in st[1], re.findall(r'.{0,12}⁶', st[1])[:1])
        await pg.fill('#n-biegung .ueb-in','0,135'); await pg.click('#n-biegung .ueb-box button'); m=await pg.inner_text('#n-biegung .ueb-msg')
        check('size: Prüfen erkennt μ_Eds = 0,135 im verdeckten Schritt 2', 'Schritt 2' in m, m)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
