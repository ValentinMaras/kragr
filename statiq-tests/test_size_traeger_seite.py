# statiq·size v0.5.24/0.5.25: Seitenansicht des Stahlträgers und des Holzbauteils, Längsansicht Holz-Beton-Verbund;
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
        async def case(mv, psi=0, llt=3, zg=1):
            await pg.evaluate(f"setMat('stahl'); setStMode('traeger'); $('sn-mv').value='{mv}'; $('sn-psi').value='{psi}'; $('sn-Llt').value='{llt}'; $('sn-zg').value='{zg}'; run()")
            await pg.wait_for_timeout(80)
            return await pg.evaluate(f"""(()=>{{ const s={SIDE}; if(!s) return null;
              const blue=[...s.querySelectorAll('rect[fill="'+C_IN+'"]')].map(r=>[+r.getAttribute('y'), +r.getAttribute('width')]);
              const txt=[...s.querySelectorAll('text')].map(t=>t.textContent);
              const arrows=[...s.querySelectorAll('line[stroke="'+C_EW+'"]')].length, arcs=[...s.querySelectorAll('path[d*=" A "]')].length;
              const dots=[...s.querySelectorAll('circle')].map(c=>+c.getAttribute('cx'));
              const heads=[...s.querySelectorAll('path[fill="'+C_EW+'"]')].map(h=>h.getAttribute('d'));
              return {{blue, txt, arrows, arcs, dots, heads, C1:mvWerte($('sn-mv').value, num('sn-psi')).C1, legend:s.nextElementSibling?.textContent||''}}; }})()""")
        r=await case('lin',-0.5)
        check('Seitenansicht vorhanden (linear)', r is not None)
        top=sum(w for y,w in r['blue'] if y<80); bot=sum(w for y,w in r['blue'] if y>80)
        check('linear ψ = −0,5: unten gedrückt auf 1/3 der Länge', abs(bot/(top+bot)-1/3)<0.03, round(bot/(top+bot),3))
        check('linear ψ = −0,5: Momentennullpunkt bei 2/3 der Länge', r['dots'] and abs(r['dots'][0]-(80+320*2/3))<1, r['dots'])
        check('linear: Endmomente als Drehpfeile M₁ und M₂', r['arcs']==2 and 'M = 0' in r['txt'], r['arcs'])
        check('linear: M₂ = ψ·M₁ = −45,0 kNm beschriftet', any('−45,0 kNm' in t or '-45,0 kNm' in t for t in r['txt']), [t for t in r['txt'] if 'M₂' in t])
        check('linear: C₁ wie im Nachweis (2,33)', any(t=='C₁ = 2,33' for t in r['txt']) and abs(r['C1']-2.33)<1e-9)
        check('linear: Erklärung „keine Querlast … Endmomente“', 'keine Querlast' in r['legend'])
        r=await case('lin',0.5)
        check('linear ψ = +0,5: ganz oben gedrückt, kein Nullpunkt', all(y<80 for y,w in r['blue']) and not r['dots'])
        r=await case('lin',0)
        check('linear ψ = 0: nur ein Drehpfeil, M₂ = 0', r['arcs']==1 and 'M₂ = 0' in r['txt'], r['arcs'])
        r=await case('c')
        check('konstant: zwei Endmomente, C₁ = 1,00', r['arcs']==2 and 'C₁ = 1,00' in r['txt'])
        r=await case('q',0,3,1)
        check('Gleichlast: 9 Lastpfeile, Lastangriff Obergurt', r['arrows']>=10 and any('Lastangriff: Obergurt' in t for t in r['txt']), r['arrows'])
        tips=[float(re.match(r'M ([\d.]+) ([\d.]+)',h).group(2)) for h in r['heads']]
        check('Gleichlast am Obergurt: Pfeilspitzen auf dem Obergurt (y = 71)', tips and all(abs(t-71)<0.5 for t in tips), tips[:3])
        r=await case('F',0,3,-1)
        tips=[float(re.match(r'M ([\d.]+) ([\d.]+)',h).group(2)) for h in r['heads']]
        check('Einzellast am Untergurt: Pfeilspitze am Untergurt (y = 98)', len(tips)==1 and abs(tips[0]-98)<0.5, tips)
        check('Einzellast: C₁ = 1,35, Hinweis zum Lastangriff', 'C₁ = 1,35' in r['txt'] and 'Untergurt stabilisierend' in r['legend'])
        r=await case('q',0,0,1)
        check('L_LT = 0: Druckgurt durchgehend gehalten, kein C₁', any('durchgehend gehalten' in t for t in r['txt']) and not any(t.startswith('C₁') for t in r['txt']) and 'kein Biegedrillknicken' in r['legend'])
        check('L_LT = 0: Maß zeigt Stützweite L', any(re.search(r'L = 6,00 m', t) for t in r['txt']), [t for t in r['txt'] if 'm' in t][-3:])
        await case('lin',-0.5)
        rep=await pg.evaluate("buildReport()")
        check('Bericht enthält die Seitenansicht', 'Seitenansicht' in rep and 'keine Querlast' in rep)
        for L,word,title in (('en','No transverse load','Side view'),('fr','Aucune charge transversale','Vue latérale'),('es','no actúa ninguna carga','Vista lateral')):
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{L}')"); await pg.reload(); await pg.wait_for_timeout(250)
            r=await case('lin',-0.5)
            t=' '.join(r['txt'])+' '+r['legend']
            g=re.findall(r'\b(Seitenansicht|Gabellager|Lastangriff|Halterungen|Querlast|gedrückter|Gurt)\b', t)
            check(f'{L}: Seitenansicht übersetzt', word in r['legend'] and title in t and not g, g[:4])
        await pg.evaluate("localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(250)
        # Holz-Bauteil (seit v0.5.25)
        async def holz(mv, llt, zg, M=None):
            setM = '' if M is None else "$('ho-M').value='"+str(M)+"';"
            await pg.evaluate(f"setMat('holz'); setHoMode('bauteil'); $('ho-mv').value='{mv}'; $('ho-Llt').value='{llt}'; $('ho-zg').value='{zg}'; {setM} run()")
            await pg.wait_for_timeout(80)
            return await pg.evaluate(f"""(()=>{{ const s={SIDE}; if(!s) return null; return {{ txt:[...s.querySelectorAll('text')].map(t=>t.textContent),
              heads:[...s.querySelectorAll('path[fill="'+C_EW+'"]')].map(h=>h.getAttribute('d')), legend:s.nextElementSibling?.textContent||'', h:+$('ho-h').value }}; }})()""")
        r=await holz('q','3','1')
        check('Holz: Seitenansicht vorhanden', r is not None)
        lef=0.9*3000+2*r['h']
        check('Holz q, oberer Rand: l_ef = 0,9·L_K + 2h wie im Kippnachweis', any(t.replace(' ','')==('lef='+f"{lef/1000:.2f}".replace('.',',')+'m') for t in r['txt']), [t for t in r['txt'] if 'ef' in t])
        tips=[float(re.match(r'M ([\d.]+) ([\d.]+)',h).group(2)) for h in r['heads']]
        check('Holz q, oberer Rand: Pfeilspitzen am oberen Rand', tips and all(abs(t-71)<0.5 for t in tips) and 'oberen Rand verlängert' in r['legend'], tips[:2])
        r=await holz('c','3','0')
        check('Holz konstant: l_ef = 1,0·L_K = 3,00 m', any(t.replace(' ','')=='lef=3,00m' for t in r['txt']) and 'ungünstigster Fall' in r['legend'])
        r=await holz('F','0','-1')
        check('Holz L_K = 0: Druckrand durchgehend gehalten, kein l_ef', any('Druckrand durchgehend' in t for t in r['txt']) and not any('ef' in t for t in r['txt']) and 'kein Kippen' in r['legend'])
        r=await holz('q','3','1','0')
        check('Holz ohne Biegemoment: keine Seitenansicht', r is None)
        await pg.evaluate("$('ho-M').value='9'; run()")
        rep=await pg.evaluate("$('ho-Llt').value='3'; run(); buildReport()")
        check('Holz: Bericht enthält die Seitenansicht', 'Seitenansicht' in rep and 'gedrückter Rand' in rep)
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
            r=await holz('q','3','1','9')
            t=' '.join(r['txt'])+' '+r['legend']+' '+t1
            g=re.findall(r'\b(Längsansicht|Seitenansicht|Gabellager|Lastangriff|Rand|Fuge|Verbinder|Druckrand|Kipplänge)\b', t)
            check(f'{L}: Holz-Seitenansicht und Verbund-Längsansicht übersetzt', w1 in t1 and w2 in t and not g, g[:4])
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs[:3])
        await br.close()
asyncio.run(main())
print('FAILS:', fails); sys.exit(1 if fails else 0)
