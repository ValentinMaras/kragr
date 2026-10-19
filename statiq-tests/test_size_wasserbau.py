# statiq·size: Wasserbau (Hydrostatik, Hydrodynamik) — unabhängig nachgerechnet. Ohne Playwright: SKIP.
import os, sys, math, asyncio
import numpy as np
from scipy.optimize import brentq
HERE=os.path.dirname(os.path.abspath(__file__)); HTML='file://'+os.path.abspath(os.path.join(HERE,'..','size.html'))
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('SKIP Playwright nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:66}', str(info)[:150])
g=9.81; r=math.radians
def wdruck(alpha,b,to,L,hu):
    # numerische Integration über die Flächenlänge
    s=math.sin(r(alpha)); a=np.linspace(0,L,200001); da=a[1]-a[0]
    po=g*(to+a*s); pu=g*np.maximum(0,hu-(L-a)*s)
    Fo=np.trapezoid(po,a)*b; Fu=np.trapezoid(pu,a)*b
    eo=np.trapezoid(po*a,a)*b/Fo; M=np.trapezoid((po-pu)*(L-a),a)*b
    return Fo, eo, Fu, M
def colebrook(Re,kD):
    if Re<2320: return 64/Re
    f=lambda x: 1/math.sqrt(x)+2*math.log10(2.51/(Re*math.sqrt(x))+kD/3.71)
    return brentq(f,1e-4,1)
def rohr(Q,D,L,k,zeta,nu):
    A=math.pi*D*D/4; v=Q/A; Re=v*D/nu; lam=colebrook(Re,k/D); return (lam*L/D+zeta)*v*v/(2*g), lam, v
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(HTML); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(200)
        await pg.evaluate("setMat('wasser'); setWbMode('druck')")
        s=await pg.inner_text('#summary'); check('Wasserdruck: nur Ergebnisse, keine Nachweise', 'Ergebnisse berechnet' in s, s)
        for name,(al,b,to,L,hu) in {'senkrechte Stauwand 4 m, Unterwasser 1,5 m':(90,1,0,4,1.5),'Schütz unter Wasser, geneigt 60°':(60,2,0.5,3,1),'flach geneigt 30°, trocken':(30,1,1,5,0),'senkrecht, Unterwasser höher als die Fläche':(90,1,1,2,4)}.items():
            await pg.evaluate(f"$('wd-alpha').value={al}; $('wd-b').value={b}; $('wd-to').value={to}; $('wd-L').value={L}; $('wd-hu').value={hu}; run()")
            Fo,eo,Fu,M=wdruck(al,b,to,L,hu); G=await pg.evaluate("[LAST.res.O.F, LAST.res.O.e, LAST.res.U.F, LAST.res.Mfuss]")
            ok=abs(G[0]-Fo)<1e-5*max(1,Fo) and abs(G[1]-eo)<1e-5 and abs(G[2]-Fu)<1e-5*max(1,Fu) and abs(G[3]-M)<1e-4*max(1,abs(M))
            check(f'Wasserdruck {name}', ok, f'F = {Fo:.2f} kN in e = {eo:.3f} m, F_u = {Fu:.2f} kN, M = {M:.2f} kNm')
        check('Hand: 4 m Wasser auf 1 m Wand → F = 9,81·4²/2 = 78,48 kN in 2/3·4', abs(wdruck(90,1,0,4,0)[0]-78.48)<1e-3 and abs(wdruck(90,1,0,4,0)[1]-8/3)<1e-4)
        # Schwimmkörper
        await pg.evaluate("setWbMode('schwimm')")
        for name,(L,B,H,G,zg,gw) in {'Standardponton':(12,5,1.5,450,1.6,9.81),'schmal und hoch beladen → instabil':(10,2,1.5,200,1.5,9.81),'Seewasser':(20,6,2,1500,1.8,10.05)}.items():
            await pg.evaluate(f"$('ws-L').value={L}; $('ws-B').value={B}; $('ws-H').value={H}; $('ws-G').value={G}; $('ws-zg').value={zg}; $('ws-w').value='{gw}'; run()")
            V=G/gw; T=V/(L*B); GM=T/2+B**2/(12*T)-zg
            R=await pg.evaluate("[LAST.res.T, LAST.res.GM, LAST.res.C.find(c=>c.id==='wsgm').ok]")
            check(f'Schwimmkörper {name}', abs(R[0]-T)<1e-12 and abs(R[1]-GM)<1e-12 and R[2]==(GM>0), f'T = {T:.3f} m, GM = {GM:.3f} m')
        # Rohrleitung
        await pg.evaluate("setWbMode('rohr')")
        for name,(Q,D,L,k,z,dh,nu) in {'DN 200 Guss, 45 l/s':(45,200,350,0.1,2.5,8,1.31e-6),'PE DN 110, 8 l/s, 20 °C':(8,110,500,0.007,4,6,1e-6),'laminar (sehr kleiner Durchfluss)':(0.05,100,50,0.1,1,1,1.31e-6),'Betonrohr DN 800, 1,2 m³/s':(1200,800,1200,0.4,3,5,1.31e-6)}.items():
            await pg.evaluate(f"$('wr-Q').value={Q}; $('wr-D').value={D}; $('wr-L').value={L}; $('wr-mat').value='x'; $('wr-k').value={k}; $('wr-zeta').value={z}; $('wr-dh').value={dh}; $('wr-nu').value='{'1.31e-6' if nu==1.31e-6 else '1.00e-6'}'; run()")
            hv,lam,v=rohr(Q/1000,D/1000,L,k/1000,z,nu)
            Qmax=brentq(lambda q: rohr(q,D/1000,L,k/1000,z,nu)[0]-dh, 1e-6, 50)
            R=await pg.evaluate("[LAST.res.hv, LAST.res.lam, LAST.res.Qmax]")
            check(f'Rohr {name}', abs(R[0]-hv)/hv<1e-9 and abs(R[1]-lam)/lam<1e-9 and abs(R[2]-Qmax)/Qmax<1e-7, f'λ = {lam:.5f}, h_v = {hv:.3f} m, Q_max = {Qmax*1000:.1f} l/s')
        # Haaland als grobe Plausibilität für λ
        lamH=(-1.8*math.log10(6.9/1e5+(0.0005/3.7)**1.11))**-2; lamC=colebrook(1e5,0.0005); check('Colebrook ≈ Haaland (±2 %)', abs(lamC-lamH)/lamC<0.02, f'{lamC:.5f} / {lamH:.5f}')
        # Gerinne
        await pg.evaluate("setWbMode('gerinne')")
        for name,(Q,I,b,m,k,H) in {'Trapez, Rasen':(2.5,1.5,2,1.5,35,1.5),'Rechteck Beton, steil (schießend)':(4,20,1.5,0,85,1.5),'breites Rechteck, flach':(10,0.5,8,0,30,2)}.items():
            await pg.evaluate(f"$('wg-Q').value={Q}; $('wg-I').value={I}; $('wg-b').value={b}; $('wg-m').value={m}; $('wg-mat').value='x'; $('wg-kst').value={k}; $('wg-H').value={H}; run()")
            A=lambda h:(b+m*h)*h; U=lambda h:b+2*h*math.sqrt(1+m*m); Bs=lambda h:b+2*m*h
            hn=brentq(lambda h:k*A(h)*(A(h)/U(h))**(2/3)*math.sqrt(I/1000)-Q,1e-6,50); hg=brentq(lambda h:Q*Q*Bs(h)/(g*A(h)**3)-1,1e-6,50)
            Fr=Q/A(hn)/math.sqrt(g*A(hn)/Bs(hn))
            R=await pg.evaluate("[LAST.res.hn, LAST.res.hg, LAST.res.Fr]")
            check(f'Gerinne {name}', abs(R[0]-hn)<1e-9 and abs(R[1]-hg)<1e-9 and abs(R[2]-Fr)<1e-8, f'h_n = {hn:.3f} m, h_gr = {hg:.3f} m, Fr = {Fr:.3f}')
        hg=await pg.evaluate("LAST.res.hg"); check('Rechteck: h_gr = (q²/g)^(1/3)', abs(hg-((10/8)**2/g)**(1/3))<1e-9, f'{hg:.4f} m')
        # Wehr
        await pg.evaluate("setWbMode('wehr')")
        for name,(Q,b,mu,w,hm) in {'rundkronig':(6,8,0.75,2,3),'scharfkantig, schmal':(3,2,0.64,1.5,2.5),'breitkronig, Hochwasser':(40,12,0.577,2.5,3.5)}.items():
            await pg.evaluate(f"$('ww-Q').value={Q}; $('ww-b').value={b}; $('ww-form').value='x'; $('ww-mu').value={mu}; $('ww-w').value={w}; $('ww-hmax').value={hm}; run()")
            hu=brentq(lambda h:2/3*mu*b*math.sqrt(2*g)*h**1.5-Q,1e-6,50); R=await pg.evaluate("[LAST.res.hu, LAST.res.C.find(c=>c.id==='wwow').ok]")
            check(f'Wehr {name}', abs(R[0]-hu)<1e-9 and R[1]==(w+hu<=hm), f'h_ü = {hu:.3f} m, OW = {w+hu:.3f} m')
        for m,word in [('druck','Druckmittelpunkt'),('schwimm','Metazentrum'),('rohr','Colebrook'),('gerinne','Froude'),('wehr','Poleni')]:
            await pg.evaluate(f"setWbMode('{m}'); run(); showReport()"); rp=await pg.inner_text('#report')
            check(f'Bericht {m}', word in rp)
        await pg.evaluate("setWbMode('gerinne'); $('wg-Q').value=3.3; run(); save()"); await pg.reload(); await pg.wait_for_timeout(200)
        check('Speichern/Laden stellt Wasserbau wieder her', await pg.evaluate("MAT==='wasser' && WBMODE==='gerinne' && $('wg-Q').value==='3.3' && LAST.mode==='gerinne'"))
        check('keine Skriptfehler', not errs, errs)
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
