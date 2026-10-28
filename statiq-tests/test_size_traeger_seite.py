# statiq·size v0.5.24/0.5.25 (Seitenansicht seit v0.7.12 entfernt, Momentenverlauf im Stabilitätsteil): Seitenansicht des Stahlträgers und des Holzbauteils, Längsansicht Holz-Beton-Verbund;
# Stahlträger (Abschnitt zwischen den seitlichen Halterungen) — Belastung bzw. Endmomente,
# Lastangriff, gedrückter Gurt, Momentenlinie und C₁ passend zum gewählten Momentenverlauf; im Bericht; in EN/FR/ES übersetzt.
import os, sys, re, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:160])
SIDE="[...document.querySelectorAll('#fig svg')].find(s=>/Seitenansicht|Side view|Vue latérale|Vista lateral/.test(s.getAttribute('aria-label')||''))"
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1300,'height':1200}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+BASE+'/size.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        # seit size v0.7.12: keine Seitenansicht mehr (Valentin: der Querschnitt reicht); der Momentenverlauf steht im Stabilitäts-
        # bzw. Kipp-Teil, weil er nur C₁ / l_ef und die Biegelinie bestimmt, nicht M_Ed
        for mv,psi,C1 in (('lin',-0.5,2.33),('c',0,1.0),('q',0,1.127),('F',0,1.348)):
            await pg.evaluate(f"setMat('stahl'); setStMode('traeger'); $('sn-mv').value='{mv}'; $('sn-psi').value='{psi}'; $('sn-Llt').value='3'; run()"); await pg.wait_for_timeout(80)
            r=await pg.evaluate(f"[!!({SIDE}), mvWerte($('sn-mv').value, num('sn-psi')).C1]")
            check(f'Stahl {mv}: keine Seitenansicht, C₁ = {C1} wie bisher', not r[0] and abs(r[1]-C1)<0.005, r)
        r=await pg.evaluate("""[ $('sn-mv').closest('.card').querySelector('.card-title').textContent, $('sn-M').closest('.card').contains($('sn-mv')), $('sn-psi').closest('.card')===$('sn-mv').closest('.card'), document.querySelector('[data-i18n=mvHint]').textContent ]""")
        check('Stahl: Momentenverlauf im Teil Stabilität, nicht bei den Schnittgrößen', 'Stabilität' in r[0] and not r[1] and r[2], r[:3])
        check('Stahl: Hinweis „ändert M_y,Ed nicht“', 'ändert M' in r[3], r[3][:60])
        rep=await pg.evaluate("buildReport()")
        check('Stahl: Bericht ohne Seitenansicht', 'Seitenansicht' not in rep and 'Querschnitt' in rep or 'Profil' in rep)
        for mv in ('q','F','c'):
            await pg.evaluate(f"setMat('holz'); setHoMode('bauteil'); $('ho-mv').value='{mv}'; $('ho-Llt').value='3'; $('ho-M').value='9'; run()"); await pg.wait_for_timeout(80)
            r=await pg.evaluate(f"[!!({SIDE}), holzMV($('ho-mv').value).lef]")
            check(f'Holz {mv}: keine Seitenansicht, l_ef-Faktor {r[1]}', not r[0] and r[1]=={'q':0.9,'F':0.8,'c':1.0}[mv], r)
        r=await pg.evaluate("[ $('ho-mv').closest('.card').querySelector('.card-title').textContent, $('ho-M').closest('.card').contains($('ho-mv')) ]")
        check('Holz: Momentenverlauf im Teil Kippen und Knicken', 'Kippen' in r[0] and not r[1], r)
        rep=await pg.evaluate("buildReport()")
        check('Holz: Bericht ohne Seitenansicht', 'Seitenansicht' not in rep)
        # Holz-Beton-Verbund
        await pg.evaluate("setMat('holz'); setHoMode('verbund')"); await pg.wait_for_timeout(150)
        v=await pg.evaluate("""(()=>{ const s=[...document.querySelectorAll('#fig svg')].find(x=>/Längsansicht/.test(x.getAttribute('aria-label')||'')); if(!s) return null;
          const con=[...s.querySelectorAll('line')].filter(l=>l.getAttribute('y1')==='62' && l.getAttribute('y2')==='77');
          const I=PA['holz/verbund'].rd(), r=PA['holz/verbund'].na(I);
          return { n:con.length, orange:con.filter(l=>l.getAttribute('stroke')===C_EW).map(l=>+l.getAttribute('x1')), txt:[...s.querySelectorAll('text')].map(t=>t.textContent), F1:r.F1, L:I.L, s:I.s }; })()""")
        check('Verbund: Längsansicht vorhanden', v is not None)
        check('Verbund: Verbinder im Abstand s (höchstens 60 gezeichnet)', v['n']==max(2,min(60,round(v['L']*1000/v['s']))), (v['n'], v['L'], v['s']))
        check('Verbund: stark beanspruchte Verbinder nur in den Randvierteln', v['orange'] and all(x<70+340*0.25+1 or x>70+340*0.75-1 for x in v['orange']), len(v['orange']))
        check('Verbund: F₁ am Auflager wie im Nachweis', any(f"F₁ = {v['F1']/1000:.2f}".replace('.',',') in t for t in v['txt']), [t for t in v['txt'] if 'F₁' in t])
        rep=await pg.evaluate("buildReport()")
        check('Verbund: Bericht enthält die Längsansicht', 'Längsansicht' in rep)
        for L,w1,w2 in (('en','Longitudinal view','top edge'),('fr','Vue longitudinale','rive supérieure'),('es','Vista longitudinal','borde superior')):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(250)
            await pg.evaluate("setMat('holz'); setHoMode('verbund')"); await pg.wait_for_timeout(120)
            t1=await pg.inner_text('#fig')
            g=re.findall(r'\b(Längsansicht|Gabellager|Rand|Fuge|Verbinder)\b', t1)
            check(f'{L}: Verbund-Längsansicht übersetzt', w1 in t1 and not g, g[:4])
            await pg.evaluate("setMat('stahl'); setStMode('traeger')"); await pg.wait_for_timeout(120)
            h=await pg.evaluate("[document.querySelector('[data-i18n=mvKipp]').textContent, document.querySelector('[data-i18n=mvHint]').textContent]")
            check(f'{L}: Momentenverlauf-Beschriftung und Hinweis übersetzt', not re.search(r'Momentenverlauf|Kippen|ändert', ' '.join(h)), h[0])
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
