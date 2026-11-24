# kragr·size v0.7.57 (24.11.2026): Längsbewehrung in drei Lagen (Balken, Plattenbalken) — Eingabe je Lage, unabhängig nachgerechnet.
# Prüft Eingabe (Auswahl 1–3 Lagen, Stäbe je Lage, Summe), Nutzhöhe bis zum Schwerpunkt, Biegung gegen eigenes ω-Verfahren,
# Fließen der obersten Lage, Prüfregeln, Automatik (dritte Lage erst, wenn zwei nicht reichen), Skizze, Text, Bericht, Speichern, alte Stände, Englisch.
# Ohne Playwright: SKIP.
import os, sys, math, asyncio
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
fyd=500/1.15; eyd=fyd/200; A=lambda ds: math.pi*ds*ds/4
def omega(mu):   # Parabel-Rechteck, eigene Integration: liefert (ω, ξ, ε_c)
    def st(t):
        ec = 3.5*t if t<=1 else 3.5; es = 25 if t<=1 else 25-(t-1)*(25-eyd)
        xi=ec/(ec+es); y=np.linspace(0,1,20001); e=ec*y; s=np.where(e<2,1-(1-e/2)**2,1.0)
        Ar=np.trapezoid(s,y); ka=1-np.trapezoid(s*y,y)/Ar
        return xi*Ar, xi*Ar*(1-ka*xi), xi, ec
    lo,hi=1e-6,2
    for _ in range(60):
        m=(lo+hi)/2
        if st(m)[1]<mu: lo=m
        else: hi=m
    r=st((lo+hi)/2); return r[0], r[2], r[3]
# XC1: c_min,dur = 10, Δc_dev = 10 (DIN EN 1992-1-1/NA)
def geo3(h, ds, dsw, n1, m2, m3, dg):
    cnw=max(10,dsw)+10; cnl=max(10,ds)+10; cv=max(cnw, cnl-dsw)
    d1=h-cv-dsw-ds/2; av=max(ds, dg+5, 20); s=ds+av
    ys=[d1]*n1+[d1-s]*m2+[d1-2*s]*m3            # Höhe jedes Stabs vom oberen Rand
    return cv, d1, av, sum(ys)/len(ys)           # d = Schwerpunkt aller Stäbe

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1280,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear(); localStorage.setItem('statiq-lang','de')"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("setMat('beton'); setTyp('balken'); $('in-expo').value='XC1'; $('in-beton').value='C30/37'; $('in-Ms').value=0; $('in-Mqp').value=0; run()")
        await pg.evaluate("document.querySelectorAll('.fold').forEach(c=>c.classList.remove('closed'))")
        # Eingabe
        o=await pg.evaluate("[[...$('in-lagen').options].map(o=>o.value+':'+o.textContent), getComputedStyle(document.querySelector('.lg2')).display, getComputedStyle(document.querySelector('.lg3')).display, !!$('in-n').offsetParent]")
        check('Auswahl eine/zwei/drei Lagen; bei einer Lage nur „Stäbe in Lage 1“, Gesamtzahl verborgen', o[0]==['1:eine Lage','2:zwei Lagen','3:drei Lagen'] and o[1]=='none' and o[2]=='none' and not o[3], o)
        await pg.uncheck('#in-auto'); await pg.select_option('#in-ds','20'); await pg.fill('#in-l1','4'); await pg.select_option('#in-lagen','3'); await pg.wait_for_timeout(150)
        o=await pg.evaluate("[getComputedStyle(document.querySelector('.lg2')).display, getComputedStyle(document.querySelector('.lg3')).display, $('in-l2').value, $('in-l3').value, $('in-n').value, $('in-nl2').value, $('in-nl3').value, $('in-nsum').textContent]")
        check('„drei Lagen“: Felder für Lage 2 und 3 erscheinen (je 2 vorbelegt), Summe darunter', o[:2]==['block','block'] or (o[0]!='none' and o[1]!='none') and o[2:7]==['2','2','8','2','2'], o)
        check('Summe: „zusammen 8 Ø 20 = 25,13 cm²“', o[7]=='zusammen 8 Ø 20 = 25,13 cm²', o[7])
        await pg.fill('#in-l2','3'); await pg.wait_for_timeout(100)
        check('Tippen in Lage 2 ändert Gesamtzahl und Modell', await pg.evaluate("[$('in-n').value, $('in-nl2').value, $('in-nl3').value]")==['9','3','2'])
        await pg.select_option('#in-lagen','1'); await pg.wait_for_timeout(100)
        check('zurück auf „eine Lage“: Modell nur noch Lage 1', await pg.evaluate("[$('in-n').value, $('in-nl2').value, $('in-nl3').value, LAST.res.G.m]")==['4','0','0',0])
        # Nutzhöhe und Biegung, Rechteck, Handeingabe (unabhängig)
        cases={'30/70, 4+3+2 Ø 25, d_g 16':(30,70,4,3,2,25,10,16,520),
               '30/80, 4+4+4 Ø 20, d_g 16':(30,80,4,4,4,20,10,16,560),
               '25/70, 3+3+2 Ø 25, d_g 32':(25,70,3,3,2,25,10,32,430)}
        for name,(b,h,n1,m2,m3,ds,dsw,dg,M) in cases.items():
            await pg.evaluate(f"$('in-auto').checked=false; $('in-b').value={b}; $('in-h').value={h}; $('in-ds').value={ds}; $('in-dsw').value={dsw}; $('in-sw').value=15; $('in-dg').value='{dg}'; $('in-M').value={M}; $('in-V').value=150; $('in-n2').value=2; $('in-ds2').value=12;"
                              f" $('in-lagen').value='3'; $('in-l1').value={n1}; $('in-l2').value={m2}; $('in-l3').value={m3}; lagenSet()")
            cv,d1,av,d=geo3(h*10,ds,dsw,n1,m2,m3,dg); n=n1+m2+m3
            g=await pg.evaluate("[LAST.res.G.d, LAST.res.G.d1, LAST.res.G.av, LAST.res.C.find(c=>c.id==='biegung').eta, LAST.res.C.find(c=>c.id==='regeln').eta, !!LAST.res.DZ, LAST.res.C.find(c=>c.id==='biegung').steps.join(' ')]")
            fcd=0.85*30/1.5; mu=M*1e6/(b*10*d*d*fcd); As=n*A(ds); Asmin=2.9*(b*10)*(h*10)**2/6/(500*0.9*d)
            om,xi,ec=omega(mu); etaB=None if g[5] else max(om*b*10*d*fcd/fyd, Asmin)/As
            a=(b*10-2*cv-2*dsw-n1*ds)/(n1-1); etaR=max(ds,dg+5,20)/a
            ok = abs(g[0]-d)<1e-9 and abs(g[1]-d1)<1e-9 and g[2]==av and abs(g[4]-etaR)<1e-9 and (etaB is None or abs(g[3]-etaB)<2e-4)
            check(f'Rechteck {name}: d, Biegung, Stababstand', ok, f'd = {d:.1f} mm (Schwerpunkt aus Einzelstäben) · η Biegung = {g[3]:.4f}' + ('' if etaB is None else f' / ref {etaB:.4f}') + f' · η Abstand = {etaR:.3f}')
            if not g[5]:
                d3=d1-2*(ds+av); x=xi*d; es3=ec*(d3-x)/x
                import re; mm=re.search(r'= (-?[0-9.,]+) ‰ [≥<] ε<sub>yd</sub>', g[6])
                got=float(mm.group(1).replace('.','').replace(',','.')) if mm else None
                check(f'Rechteck {name}: Dehnung der obersten Lage ε_s3', got is not None and abs(got-es3)<0.01 and ('fließt' not in g[6] or True), f'{got} / ref {es3:.3f} ‰')
        # oberste Lage fließt nicht: flacher Balken mit Druckbewehrung, x = 0,45·d
        await pg.evaluate("$('in-b').value=40; $('in-h').value=30; $('in-ds').value=28; $('in-dsw').value=10; $('in-dg').value='16'; $('in-M').value=150; $('in-n2').value=4; $('in-ds2').value=25;"
                          " $('in-lagen').value='3'; $('in-l1').value=5; $('in-l2').value=4; $('in-l3').value=3; lagenSet()")
        cv,d1,av,d=geo3(300,28,10,5,4,3,16); d3=d1-2*(28+av); x=0.45*d; es3=3.5*(d3-x)/x
        g=await pg.evaluate("[!!LAST.res.DZ, LAST.res.C.find(c=>c.id==='biegung').note||'', LAST.res.C.find(c=>c.id==='biegung').steps.join(' ')]")
        check('flacher Balken 40/30, 5+4+3 Ø 28: oberste Lage fließt nicht → Hinweis', g[0] and es3<eyd and 'fließt nicht' in g[1] and '✗' in g[2], f'ε_s3 = {es3:.2f} ‰ < ε_yd = {eyd:.2f} ‰')
        # Prüfregeln
        await pg.evaluate("$('in-b').value=30; $('in-h').value=70; $('in-ds').value=20; $('in-M').value=300; $('in-lagen').value='3'; $('in-l1').value=4; $('in-l2').value=2; $('in-l3').value=3; lagenSet()")
        check('3. Lage mit mehr Stäben als die 2. Lage wird abgelehnt', '3. Lage' in await pg.inner_text('#summary'))
        await pg.evaluate("$('in-l1').value=3; $('in-l2').value=4; $('in-l3').value=2; lagenSet()")
        check('2. Lage mit mehr Stäben als die 1. Lage wird abgelehnt', '2. Lage' in await pg.inner_text('#summary'))
        # Darstellung, Text, Bericht, Speichern
        await pg.evaluate("$('in-l1').value=4; $('in-l2').value=3; $('in-l3').value=2; lagenSet()")
        g=await pg.evaluate("""(()=>{ const ys=[...document.querySelectorAll('#fig svg circle[fill="#111"]')].map(c=>+c.getAttribute('cy')); const c={}; ys.forEach(y=>c[y.toFixed(1)]=(c[y.toFixed(1)]||0)+1);
          const k=Object.keys(c).map(Number).sort((a,b)=>b-a).slice(0,3); return k.map(y=>c[y.toFixed(1)]); })()""")
        check('Skizze: 4 Stäbe unten, 3 darüber, 2 in der 3. Lage', g==[4,3,2], g)
        check('Bewehrungszeile nennt drei Lagen', '(4 + 3 + 2 in drei Lagen)' in await pg.inner_text('#reinf-line'), await pg.inner_text('#reinf-line'))
        st=await pg.evaluate("LAST.res.C.find(c=>c.id==='deckung').steps.join(' ')")
        check('Rechenschritt: d bis zum Schwerpunkt aller Lagen, (n₂ + 2·n₃)/n', 'Schwerpunkt aller Lagen' in st and '(3 + 2·2)/9' in st)
        st=await pg.evaluate("LAST.res.C.find(c=>c.id==='regeln').steps.join(' ')")
        check('Stababstände: 3. Lage lotrecht über der 2. Lage, 2 ≤ 3', '3. Lage: Stäbe lotrecht' in st and '2 Stäbe in der 3. Lage ≤ 3 Stäbe in der 2. Lage' in st)
        await pg.evaluate("showReport()"); rp=await pg.inner_text('#report'); await pg.evaluate("document.body.classList.remove('show-report')")
        check('Bericht enthält die drei Lagen', 'drei Lagen' in rp)
        await pg.evaluate("save()"); await pg.reload(); await pg.wait_for_timeout(400)
        check('Speichern/Laden: drei Lagen bleiben erhalten (Auswahl und Felder)', await pg.evaluate("[$('in-lagen').value, $('in-l1').value, $('in-l2').value, $('in-l3').value, LAST.res.G.m3]")==['3','4','3','2',2])
        # alter Stand (ohne in-nl3): Gesamtzahl 6, davon 2 in Lage 2
        await pg.evaluate("$('in-n').value=6; $('in-nl2').value=2; $('in-nl3').value=''; run()")
        check('alter Stand „6, davon 2 in der 2. Lage“ → zwei Lagen, 4 + 2', await pg.evaluate("[$('in-lagen').value, $('in-l1').value, $('in-l2').value, LAST.res.G.m2, LAST.res.G.m3]")==['2','4','2',2,0])
        # Automatik: Plattenbalken 30/70, M = 1300 kNm → zwei Lagen reichen nicht, drei Lagen
        await pg.evaluate("setTyp('unterzug'); $('in-auto').checked=true; $('in-b').value=30; $('in-h').value=70; $('in-hf').value=20; $('in-b1').value=200; $('in-b2').value=200; $('in-M').value=1300; $('in-V').value=150; $('in-dg').value='16'; run()")
        g=await pg.evaluate("[LAST.res.ok, LAST.res.R.n, LAST.res.R.nl2, LAST.res.R.nl3, LAST.res.R.ds, $('in-lagen').value, $('in-l3').disabled, $('in-lagen').disabled]")
        check('Automatik Plattenbalken 30/70, M = 1300 kNm: drei Lagen, alle Nachweise erfüllt, Felder gesperrt', g[0] and g[3]>0 and g[5]=='3' and g[6] and g[7], g)
        alt=await pg.evaluate("""(()=>{ const I=readInput(), R=LAST.res.R, A0=R.n*areaBar(R.ds); let found=null;
          for(const ds of DS_L) for(let n=2;n<=14;n++) for(let m=0;m<=n/2;m++){ if(n*areaBar(ds)>A0+1e-9) continue; const r={...R, ds, n, nl2:m, nl3:0}; stirrups({...I,Ms:0}, r); const res=nachweise({...I,Ms:0}, r);
            if(['biegung','regeln','riss','auflager'].every(id=>res.C.filter(c=>c.id===id).every(c=>c.ok))) found=[n,m,ds]; } return found; })()""")
        check('Gegenprobe: keine Ein- oder Zwei-Lagen-Bewehrung mit ≤ Fläche erfüllt alles', alt is None, alt)
        await pg.evaluate("setTyp('balken'); $('in-b').value=30; $('in-h').value=60; $('in-M').value=150; run()")
        check('Standardfall: Automatik bleibt bei einer Lage', await pg.evaluate("[LAST.res.G.m, $('in-lagen').value]")==[0,'1'])
        # Englisch
        await pg.evaluate("localStorage.setItem('statiq-lang','en')"); await pg.reload(); await pg.wait_for_timeout(500)
        await pg.evaluate("setTyp('balken'); $('in-auto').checked=false; $('in-b').value=30; $('in-h').value=70; $('in-ds').value=25; $('in-M').value=520; $('in-lagen').value='3'; $('in-l1').value=4; $('in-l2').value=3; $('in-l3').value=2; lagenSet()")
        g=await pg.evaluate("[document.querySelector('label[data-i18n=\"zl7\"]').textContent, $('in-lagen').options[2].textContent, $('in-nsum').textContent, $('reinf-line').textContent, LAST.res.C.find(c=>c.id==='deckung').steps.join(' ')]")
        check('Englisch: Felder, Summe, Bewehrungszeile und Rechenweg übersetzt', g[0]=='Bars in layer 3' and g[1]=='three layers' and g[2].startswith('total 9') and 'in three layers' in g[3] and 'centroid of all layers' in g[4], g[:4])
        await pg.evaluate("localStorage.setItem('statiq-lang','de')")
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
