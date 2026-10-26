# size v0.5.38 Stahlträger: eigene Karte „Querkraft“ — V_pl,z,Rd (EN 1993-1-1, 6.2.6) und Schubbeulen des Stegs
# (EN 1993-1-5, 5.1–5.3, η = 1,2, nur Auflagersteifen, verformbarer Endpfosten) mit Interaktion 7.1.
# Sollwerte unabhängig in Python aus den Profilmaßen. Ohne Playwright: SKIP.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); U='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:200])
close=lambda a,b,tol=0.002: abs(a-b)<=tol*max(1,abs(b))

def soll(P, fy, V, M=0, N=0):
    """Unabhängige Rechnung nach EN 1993-1-1 6.2.6 und EN 1993-1-5 Abschnitt 5 / 7.1."""
    hw=P['h']-2*P['tf']; tw=P['tw']; eps=math.sqrt(235/fy); eta=1.2
    Av=max(P['A']*100-2*P['b']*P['tf']+(tw+2*P['r'])*P['tf'], hw*tw)            # mm², η = 1,0 in der Schubfläche
    Vpl=Av*fy/math.sqrt(3)/1.0/1000
    r={'Vpl':Vpl, 'beul': hw/tw > 72*eps/eta, 'eta':V/Vpl}
    if r['beul']:
        lw=hw/(86.4*tw*eps)
        chi= eta if lw < 0.83/eta else 0.83/lw                                   # Tab. 5.1, verformbarer Endpfosten
        Vbw=chi*fy*hw*tw/(math.sqrt(3)*1.1)/1000
        Vb=min(Vbw, eta*fy*hw*tw/(math.sqrt(3)*1.1)/1000)
        r.update(lw=lw, chi=chi, Vb=Vb); r['eta']=max(r['eta'], V/Vb)
        e3=V/Vbw
        if e3>0.5 and M>0:
            Mpl=P['Wply']*fy/1000; Af=P['b']*P['tf']
            Mf=Af*(P['h']-P['tf'])*fy/1e6*max(0,1-abs(N)*1000/(2*Af*fy)); e1=M/Mpl
            if e1>=Mf/Mpl: r['mv']=e1+(1-Mf/Mpl)*(2*e3-1)**2; r['eta']=max(r['eta'], r['mv'])
    return r

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(U); await pg.evaluate("localStorage.clear();localStorage.setItem('statiq-lang','de');localStorage.setItem('statiq-rw-closed','');localStorage.setItem('kragr-k5-acc',JSON.stringify({'calc:knoten':false,'size:scope':false}))"); await pg.reload(); await pg.wait_for_timeout(400)
        await pg.evaluate("setMat('stahl'); setStMode('traeger')"); await pg.wait_for_timeout(300)
        async def run(prof, st, V, M, N=0):
            await pg.evaluate(f"$('sn-auto').checked=false; $('sn-prof').value='{prof}'; $('sn-stahl').value='{st}'; $('sn-V').value='{V}'; $('sn-M').value='{M}'; $('sn-N').value='{N}'; run()")
            await pg.wait_for_timeout(250)
            return await pg.evaluate("(()=>{ const C=LAST.res.C, q=C.find(c=>c.id==='qv'), s=C.find(c=>c.id==='qs'); return {q: q&&{eta:q.eta, ok:q.ok, ...q.qv}, qs: s&&s.eta, ids:C.map(c=>c.id), text: document.getElementById('n-qv')?.innerText||''}; })()")
        prof=lambda n: pg.evaluate(f"(()=>{{const P=profil('{n}'); return {{h:P.h,b:P.b,tf:P.tf,tw:P.tw,r:P.r,A:P.A,Wply:P.Wply}}; }})()")

        # 1) gedrungener Steg: nur V_pl,Rd, eigene Karte, Querschnittskarte enthält V nicht mehr
        P=await prof('IPE 300'); r=await run('IPE 300','S235',300,0); s=soll(P,235,300)
        check('IPE 300 S235: eigene Karte „Querkraft“ direkt nach der Querschnittstragfähigkeit', r['q'] is not None and r['ids'].index('qv')==r['ids'].index('qs')+1, r['ids'])
        check('IPE 300 S235: V_pl,z,Rd = A_v·f_y/(√3·γ_M0) unabhängig nachgerechnet', close(r['q']['Vpl'], s['Vpl']), (r['q']['Vpl'], s['Vpl']))
        check('IPE 300 S235: η = V_Ed/V_pl,Rd, kein Schubbeulen (h_w/t_w ≤ 60ε)', close(r['q']['eta'], s['eta']) and not r['q']['beul'] and not s['beul'], (r['q']['eta'], s['eta']))
        check('Querschnittskarte: Querkraft zählt nur noch in der eigenen Karte (η = 0 bei N = M = 0)', r['qs']==0, r['qs'])
        check('Rechenweg: Nachweiszeile V_Ed ≤ V_pl,z,Rd und Grenze 72·ε/η mit η = 1,2', 'Nachweis Querkraft' in r['text'] and '= 60,0' in r['text'] and 'η = 1,2' in r['text'], r['text'][:120])
        r=await run('IPE 300','S235',400,0)
        check('IPE 300 S235, V = 400 kN: nicht erfüllt, Zeichen „>“ im Rechenweg', not r['q']['ok'] and close(r['q']['eta'], 400/s['Vpl']) and '> Vpl,z,Rd' in r['text'].replace('\n',' '), r['q']['eta'])

        # 2) schlanker Steg: IPE 600 in S460 → h_w/t_w = 46,8 > 72·0,715/1,2 = 42,9
        P=await prof('IPE 600')
        r=await run('IPE 600','S460',1000,900); s=soll(P,460,1000,900)
        check('IPE 600 S460: Schubbeulen wird nachgewiesen (h_w/t_w > 72ε/η)', r['q']['beul'] and s['beul'], (r['q']['hwt'], r['q']['lim']))
        check('IPE 600 S460: λ̄_w = h_w/(86,4·t_w·ε) und χ_w nach Tab. 5.1', close(r['q']['lw'], s['lw']) and close(r['q']['chi'], s['chi']), (r['q']['lw'], s['lw'], r['q']['chi'], s['chi']))
        check('IPE 600 S460: V_b,Rd (ohne Gurtanteil) < V_pl,Rd, maßgebend', close(r['q']['Vb'], s['Vb']) and r['q']['Vb'] < r['q']['Vpl'], (r['q']['Vb'], s['Vb']))
        check('IPE 600 S460, M klein: η = V_Ed/V_b,Rd, Gurte tragen das Moment allein', close(r['q']['eta'], s['eta']) and 'mv' not in r['q'] and 'Gurte tragen das Moment allein' in r['text'], (r['q']['eta'], s['eta']))
        r=await run('IPE 600','S460',1500,1500); s=soll(P,460,1500,1500)
        check('IPE 600 S460, V und M groß: Interaktion 7.1 maßgebend und nicht erfüllt', 'mv' in s and close(r['q'].get('mv',0), s['mv']) and close(r['q']['eta'], s['eta']) and not r['q']['ok'], (r['q'].get('mv'), s.get('mv')))
        r=await run('IPE 600','S460',1500,1500,800); s=soll(P,460,1500,1500,800)
        check('IPE 600 S460 mit Normalkraft: M_f,Rd abgemindert, Interaktion unabhängig gleich', close(r['q']['eta'], s['eta']), (r['q']['eta'], s['eta']))
        r=await run('IPE 600','S355',600,300)
        check('IPE 600 S355: h_w/t_w = 46,8 ≤ 72·0,814/1,2 = 48,8 → kein Schubbeulen', not r['q']['beul'] and close(r['q']['lim'], 72*math.sqrt(235/355)/1.2), r['q']['lim'])

        # 3) Abhilfe, Umfang, Sprachen
        r=await run('IPE 300','S235',500,0); await pg.wait_for_timeout(300)
        t=await pg.evaluate("document.getElementById('n-qv').innerText")
        check('Abhilfe: Ursache „Schubtragfähigkeit des Stegs“ bei nicht erfülltem Querkraftnachweis', 'Schubtragfähigkeit des Stegs' in t, t[-200:])
        sc=await pg.evaluate("document.getElementById('scope-card').innerText")
        check('Umfang: unversteifter Steg enthalten, Zwischensteifen und Gurtanteil „nicht enthalten“', 'Schubbeulen mit Zwischensteifen' in sc and 'Plattenbeulen bei Schub' not in sc)
        for lang, word in [('en','Shear buckling'),('fr','Voilement'),('es','Abolladura')]:
            await pg.evaluate(f"localStorage.setItem('statiq-lang','{lang}')"); await pg.reload(); await pg.wait_for_timeout(300)
            await pg.evaluate("setMat('stahl'); setStMode('traeger')"); await pg.wait_for_timeout(200)
            r=await run('IPE 600','S460',1000,900)
            bad=[w for w in ['Schubbeulen','Nachweis','Schubfläche','Gurte','sichere Seite','Hinweis'] if w in r['text']]
            check(f'{lang.upper()}: Karte übersetzt ({word}), keine deutschen Reste', word in r['text'] and not bad, bad or r['text'][:80])
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
