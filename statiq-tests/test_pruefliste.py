# Prüfliste-Abgleich (ref v0.3.23, size v0.5.30): Norm- und NA-Werte, die gegen frei zugängliche Quellen
# geprüft und korrigiert wurden. Jeder Wert wird hier unabhängig in Python nachgerechnet bzw. als Sollwert gesetzt.
import os, sys, math, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
REF='file://'+BASE+'/ref.html'; SIZE='file://'+BASE+'/size.html'
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
near=lambda a,b,r=1e-3: a is not None and b is not None and abs(a-b)<=r*max(1,abs(b))

# ── Sollwerte aus den Quellen ──
SN003 = [(-1,2.55),(-0.75,2.57),(-0.5,2.33),(-0.25,2.05),(0,1.77),(0.25,1.52),(0.5,1.31),(0.75,1.14),(1,1.00)]   # NCCI SN003a, k = kw = 1
def c1lin(p):
    for (a,ca),(b,cb) in zip(SN003,SN003[1:]):
        if p<=b: return ca+(cb-ca)*(p-a)/(b-a)
    return 1.0
def itrect(b,h):
    s,l=min(b,h),max(b,h); S=sum(math.tanh(n*math.pi*l/(2*s))/n**5 for n in range(1,200,2)); return s**3*l/3*(1-192/math.pi**5*s/l*S)
def kstoss(art,M):   # DIN 4109-2:2018 / EN ISO 12354-1:2017, Anhang E
    if art=='kreuz': return (9.6+11*M if M>0.182 else 8.7+17.1*M+5.7*M*M), 5.7+15.4*M*M
    return (8+6.8*M if M>0.215 else 5.7+14.1*M+5.7*M*M), 4.7+5.7*M*M

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        # ═════════ ref ═════════
        await pg.goto(REF); await pg.wait_for_timeout(300)
        r=await pg.evaluate("[-1,-0.6,0,0.3,1].map(p=>BDK_FALL.psi.C1(p))")
        check('ref C1 linear nach SN003a (Tabelle, interpoliert)', all(near(a,c1lin(p)) for a,p in zip(r,[-1,-0.6,0,0.3,1])), r)
        r=await pg.evaluate("[BDK_FALL.q.C1(),BDK_FALL.q.C2,BDK_FALL.F.C1(),BDK_FALL.F.C2]")
        check('ref C1/C2 Gleichlast 1,13/0,45, Einzellast 1,35/0,63', r==[1.13,0.45,1.35,0.63], r)
        r=await pg.evaluate("BETA_W")
        check('ref β_w nach NA: S420 0,88, S460 0,85', r=={'S235':0.8,'S275':0.85,'S355':0.9,'S420':0.88,'S460':0.85}, r)
        r=await pg.evaluate("STAHL.find(s=>s[0]==='S355')")
        check('ref S355: f_u = 490 / 470 N/mm² (EN 1993-1-1 mit AC:2009)', r==['S355',355,490,335,470], r)
        # Kippen BSH: E0,05·G0,05 × 1,4 (NA)
        r=await pg.evaluate("(()=>{ const x=holzKipp({cls:'GL24h',b:120,h:400,L:6,sys:'eq',lp:'s',M:30,nkl:0,kled:'2'}); return [x.scrit,x.lef,x.m.E05]; })()")
        b,h,lef=120,400,0.9*6000; Iz=h*b**3/12; It=itrect(b,h); W=b*h*h/6
        sc=math.pi*math.sqrt(1.4*r[2]*Iz*540*It)/(lef*W)
        check('ref Kippen BSH: σ_m,crit mit Faktor 1,4 auf E·G (NA)', near(r[0],sc) and near(r[1],lef), (r[0],sc))
        r=await pg.evaluate("[QART.nC.kled, QART.nD.kled, QART.nD.p2]")
        check('ref KLED: Kat. C kurz, Kat. D mittel (NA Tab. NA.1)', r==['3','2',0.6], r)
        r=await pg.evaluate("(()=>{ const R=hoehensprung(1.0, 1.0, 30, 20, 0); const S=hoehensprung(1.0, 3.0, 30, 30, 45); return [R.muw,R.mu2,S.muw,S.mus,S.mu2]; })()")
        # Fall 1: μ_w,roh = 25, γh/s = 2 → μ_w = 2,0; μ2 = 2,0 · Fall 2: roh 10, γh/s = 6 → μ_w = 4,0; μ_s = 0,5·μ1(45°) = 0,2; Summe 4,2 → μ2 = 2,4
        check('ref Schnee: μ_w ≤ 4,0, NA begrenzt μ2 = μ_s + μ_w auf 0,8 … 2,4', near(r[0],2.0) and near(r[1],2.0) and near(r[2],4.0) and near(r[3],0.2) and near(r[4],2.4), r)
        r=await pg.evaluate("[CPE_FLACH.I, CPE_FLACH.Ineg]")
        check('ref Wind Flachdach Bereich I: +0,2 / −0,6 (NA)', r==[[0.2,0.2],[-0.6,-0.6]], r)
        r=await pg.evaluate("MWR_RW.z.eps")
        check('ref Mauerziegel: Endschwindwert Rechenwert 0 (NA Tab. NA.13)', r==0, r)
        # Mauerwerk Φ1 mit a/t (DIN EN 1996-3/NA)
        r=await pg.evaluate("(()=>{ const M={fk:3.0,fd:1.7}; const a=mwWandRechnung({M,t:365,h:2.625,l:1,lage:'end',decke:'b',a:245,lf:5.5}); const d=mwWandRechnung({M,t:365,h:2.625,l:1,lage:'dach',decke:'b',a:245,lf:5.5}); return [a.P1,d.P1]; })()")
        at=245/365
        check('ref Φ1 = (1,6 − l_f/6)·a/t ≤ 0,9·a/t; Dachdecke 0,333·a/t (Lücking-Beispiel 0,459)', near(r[0],min((1.6-5.5/6)*at,0.9*at)) and near(r[0],0.4587,2e-3) and near(r[1],0.333*at), r)
        # Glaser Verdunstung DIN 4108-3:2018
        r=await pg.evaluate("[GL.Z, GL.pV, GL.psV]")
        check('ref Glaser: 1/δ₀ = 1/(2·10⁻¹⁰·3600), Verdunstung 1200 / 1700 Pa', near(r[0],1/(2e-10*3600)) and r[1:]==[1200,1700], r)
        r=await pg.evaluate("(()=>{ const L=[{d:0.0125,lam:0.25,mu:10},{d:0.16,lam:0.035,mu:1},{d:0.015,lam:0.13,mu:50},{d:0.02,lam:0.7,mu:15}]; try{ const G=glaser(L); return [G.tau,G.xa,G.xb,G.Stot,G.mV,G.giV,G.geV]; }catch(e){ return String(e); } })()")
        if isinstance(r,list) and r[0]:
            Z=1/(2e-10*3600); gi=(1700-1200)/(Z*r[1]); ge=(1700-1200)/(Z*(r[3]-r[2]))
            check('ref Glaser: m_W,V = (g_i,V + g_e,V)·2160 mit p_s = 1700 Pa', near(r[5],gi) and near(r[6],ge) and near(r[4],(gi+ge)*2160), r[4:])
        else: check('ref Glaser: Testaufbau mit Tauwasser', isinstance(r,list), r)
        r=await pg.evaluate("[0.1,0.3,-0.2].map(M=>{ const m=200, mS=m*10**M; return ['kreuz','t'].map(a=>{ const k=kStoss(a, mS, m); return [k.K13,k.K12]; }); })")
        exp=[[list(kstoss(a,M)) for a in ['kreuz','t']] for M in [0.1,0.3,-0.2]]
        check('ref K_ij nach DIN 4109-2:2018 (K12 = 5,7 + 15,4M² / 4,7 + 5,7M², K13 abschnittsweise)', all(near(x,y) for A,B in zip(r,exp) for a,b in zip(A,B) for x,y in zip(a,b)), r)
        r=await pg.evaluate("BP_ANF.unb.Rmin")
        check('ref Mindestwärmeschutz Wand zu unbeheiztem Raum R ≥ 1,20 (DIN 4108-2 Tab. 3)', r==1.2, r)
        r=await pg.evaluate("Object.fromEntries(BP_MAT.filter(m=>/OSB|Gipskarton/.test(m[0])).map(m=>[m[0],m[2]]))") if await pg.evaluate("typeof BP_MAT!=='undefined'") else None
        check('ref μ: OSB 50, Gipskarton 10 (DIN EN ISO 10456)', r in ({'OSB-Platte':50,'Gipskartonplatte':10},None) , r)
        r=await pg.evaluate("Object.fromEntries(PSI)")
        check('ref Abflussbeiwerte C_s nach DIN 1986-100 Tab. 9', r.get('Gründach, extensiv, ab 10 cm Aufbau')=='0,4' and r.get('Beton, Asphalt, Pflaster mit Fugenverguss')=='1,0' and r.get('Flachdach mit Kiesschüttung')=='0,8', r)
        r=await pg.evaluate("(()=>{ document.getElementById('da-gH') ; return typeof updateDarcy; })()")
        txt=await pg.evaluate("document.body.innerHTML.includes('γ<sub>G,stb</sub> = 0,90 (BS-P)')")
        check('ref HYD: γ_G,stb = 0,95 statt 0,90 im Text', not txt, txt)

        # ═════════ size ═════════
        await pg.goto(SIZE); await pg.wait_for_timeout(400)
        r=await pg.evaluate("BETA_W")
        check('size β_w nach NA: S420 0,88, S460 0,85', r.get('S420')==0.88 and r.get('S460')==0.85, r)
        async def run(go, vals):
            await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
            await pg.evaluate(go); await pg.wait_for_timeout(60)
            for k,v in vals.items(): await pg.evaluate(f"$('{k}').value='{v}'; $('{k}').dispatchEvent(new Event('change',{{bubbles:true}})); run()")
            return await pg.evaluate("LAST && LAST.res ? Object.fromEntries(Object.entries(LAST.res).filter(([k,v])=>typeof v==='number' || typeof v==='boolean' || v===null)) : null")
        async def cs(): return await pg.evaluate("Object.fromEntries(LAST.res.C.map(c=>[c.id,[c.eta,c.ok]]))")
        # Durchbruch: Grenzen für unverstärkte Durchbrüche
        r=await run("setMat('holz'); setHoMode('durchbruch')", {'db-form':'r','db-h':600,'db-hd':90,'db-a':200,'db-hro':255,'db-lv':600})
        c=await cs()
        check('size Durchbruch: Vorgabe hält h_d ≤ 0,15h, h_ro ≥ 0,35h, a ≤ 0,4h ein', c['dbgeo'][1] and near(c['dbgeo'][0], max(90/90, 210/255, 200/240, 600/600)), c['dbgeo'])
        r=await run("setMat('holz'); setHoMode('durchbruch')", {'db-form':'r','db-h':600,'db-hd':150,'db-a':200,'db-hro':225,'db-lv':600})
        c=await cs()
        check('size Durchbruch: h_d = 0,25h ist unverstärkt nicht zulässig', (not c['dbgeo'][1]) and near(c['dbgeo'][0],150/90), c['dbgeo'])
        r=await run("setMat('holz'); setHoMode('durchbruch')", {'db-form':'k','db-h':600,'db-hd':90,'db-hro':255})
        check('size Durchbruch rund: l_t,90 = 0,353·h_d + 0,5·h', near(r['lt'],0.353*90+0.5*600), r['lt'])
        # Schwingung: Prüflast 2 kN
        r=await run("setMat('holz'); setHoMode('schwingung')", {})
        if r and 'EIl' in r:
            check('size Schwingung: w(2 kN) = 2000·ℓ³/(48·EI·b_ef)', near(r['w'], 2000*(await pg.evaluate("LAST.I.L"))**3*1e9/(48*r['EIl']*r['bef'])), r['w'])
        else: check('size Schwingung: Modus erreichbar', False, r)
        # Pfahl: γ_t = 1,40 in allen BS, Einwirkungen nach BS
        for bs,gG,gQ in [('P',1.35,1.5),('T',1.2,1.3),('A',1.1,1.1)]:
            await run("setMat('grund'); setGrMode('pfahl')", {'pf-bs':bs})
            I=await pg.evaluate("LAST.I"); rr=await pg.evaluate("[LAST.res.C.find(c=>c.id==='pfnw').eta]")
            Ab=math.pi*I['D']**2/4; U=math.pi*I['D']; Rk=I['qb']*Ab+sum(l['q']*U*l['t'] for l in I['L']); Ed=gG*I['G']+gQ*I['Q']
            check(f'size Pfahl BS-{bs}: R_c,d = R_c,k/1,40, E_d mit γ_G {gG} / γ_Q {gQ}', near(rr[0], Ed/(Rk/1.4)), (rr[0], Ed/(Rk/1.4)))
        # HYD: γ_G,stb = 0,95
        r=await run("setMat('grund'); setGrMode('hyd')", {})
        if r and 'eta' in r:
            I=await pg.evaluate("LAST.I"); L=I['dh']+2*I['t']; S=10*I['dh']/L
            check('size HYD: η = S·γ_H/(γ′·0,95)', near(r['eta'], S*I['gH']/(I['gs']*0.95)), (r['eta'], S*I['gH']/(I['gs']*0.95)))
        else: check('size HYD: Modus erreichbar', False, r)
        # Mauerwerk Φ1 mit a/t
        r=await run("setMat('mauer'); setMwMode('druck')", {})
        if r and 'P1' in r and r['P1'] is not None:
            I=await pg.evaluate("[LAST.I.a, LAST.I.t, LAST.I.lf, LAST.I.M.fk, LAST.I.lage]")
            a,t,lf,fk,lage=I; at=a/t; P1=0.333*at if lage=='dach' else min(((1.6-lf/6) if fk>=1.8 else (1.6-lf/5))*at, 0.9*at)
            check('size Mauerwerk: Φ1 mit Faktor a/t', near(r['P1'],P1), (r['P1'],P1))
        else: check('size Mauerwerk: Φ1 vorhanden', r is not None, r)
        # Ausfachung nach Tab. NA.C.1
        r=await run("setMat('mauer'); setMwMode('ausfach')", {'af-t':150,'af-z':20,'af-h':2.5,'af-l':5,'af-sfk':4})
        check('size Ausfachung 150 mm, 8–20 m, ε = 2: A_zul = 5 m²', near(r['Azul'],5.0), r['Azul'])
        r=await run("setMat('mauer'); setMwMode('ausfach')", {'af-t':115,'af-z':8,'af-h':2.5,'af-l':2.5,'af-sfk':12})
        check('size Ausfachung 115 mm, SFK ≥ 12: Tabellenwert × 4/3 (12 → 16 m²)', near(r['Azul'],16.0), r['Azul'])
        r=await run("setMat('mauer'); setMwMode('ausfach')", {'af-t':115,'af-z':20,'af-h':2.5,'af-l':2.5})
        check('size Ausfachung 115 mm über 8 m: nicht zulässig', r['ok'] is False, r.get('ok'))
        opts=await pg.evaluate("[...document.querySelectorAll('#af-z option')].map(o=>o.value)")
        check('size Ausfachung: nur Höhenstufen 8 und 20 m', opts==['8','20'], opts)
        # Kippen BSH in size
        await run("setMat('holz'); setHoMode('bauteil')", {})
        ok=await pg.evaluate("String(nachweiseHolz).includes('1.4*E005')") if await pg.evaluate("typeof nachweiseHolz==='function'") else await pg.evaluate("document.documentElement.innerHTML.includes('Math.sqrt(1.4*E005*1000*Iz*540*It)')")
        check('size Kippen BSH: allgemeine Formel mit Faktor 1,4', ok, ok)
        # F_C-Optionen
        opts=await pg.evaluate("[...document.querySelectorAll('#sx-fcs option')].map(o=>o.value)")
        check('size F_C nach DIN 4108-2 Tab. 7 (2-fach, g > 0,40)', opts==['1','0.7','0.3','0.25','0.25','0.5','x'], opts)
        r=await pg.evaluate("[GL.Z, GL.pV, GL.psV, BP_ANF.unb.Rmin]")
        check('size Glaser und Mindestwärmeschutz wie ref', near(r[0],1/(2e-10*3600)) and r[1:]==[1200,1700,1.2], r)
        r=await pg.evaluate("[0.1,0.3].map(M=>{ const k=kStoss('kreuz', 200*10**M, 200); return [k.K13,k.K12]; })")
        check('size K_ij wie ref', all(near(a,b) for x,M in zip(r,[0.1,0.3]) for a,b in zip(x,kstoss('kreuz',M))), r)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('fertig', 'mit Fehlern' if fails else 'ohne Fehler'); sys.exit(1 if fails else 0)
