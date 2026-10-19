# statiq·ref v0.3.9 Stahlbau: Profiltabellen (I, U, L, Hohlprofile) und Rechner mit Rechenweg.
# Unabhängig nachgerechnet: Querschnittswerte per shapely-Geometrie + eigener Flächenintegration (numpy),
# Stichproben gegen veröffentlichte Tabellenwerte, Nachweisformeln EN 1993-1-1/-1-8 in Python.
import os, sys, math, asyncio, re
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(HERE,'..','ref.html'))
try:
    from playwright.async_api import async_playwright
    from shapely.geometry import box, Point, Polygon
    from shapely.ops import unary_union
except ImportError:
    print('SKIP Playwright/shapely nicht installiert'); sys.exit(0)
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:72}', str(info)[:170])
def rel(a,b): return abs(a-b)/max(abs(b),1e-9)

# ── unabhängige Geometrie (mm) ─────────────────────────────
def spandrel(cx, cy, r, qx, qy):
    """Ausrundungszwickel an der Ecke (cx,cy); (qx,qy) = Richtung in den freien Raum (±1)"""
    sq = box(min(cx, cx+qx*r), min(cy, cy+qy*r), max(cx, cx+qx*r), max(cy, cy+qy*r))
    return sq.difference(Point(cx+qx*r, cy+qy*r).buffer(r, quad_segs=256))
def i_shape(h,b,tw,tf,r):
    parts=[box(-b/2,-h/2,b/2,-h/2+tf), box(-b/2,h/2-tf,b/2,h/2), box(-tw/2,-h/2,tw/2,h/2)]
    for sx in (-1,1):
        for sy in (-1,1):
            parts.append(spandrel(sx*tw/2, sy*(h/2-tf), r, sx, -sy))
    return unary_union(parts)
def rrect(B,H,r):
    return box(-B/2+r,-H/2+r,B/2-r,H/2-r).buffer(r, quad_segs=256) if r>0 else box(-B/2,-H/2,B/2,H/2)
def ring_int(xy):
    x,y=np.asarray(xy).T; x1,y1=np.roll(x,-1),np.roll(y,-1); c=x*y1-x1*y
    return np.array([c.sum()/2, ((x+x1)*c).sum()/6, ((y+y1)*c).sum()/6, ((x*x+x*x1+x1*x1)*c).sum()/12, ((y*y+y*y1+y1*y1)*c).sum()/12, ((x*y1+2*x*y+2*x1*y1+x1*y)*c).sum()/24])
def integ(g):
    polys = [g] if g.geom_type=='Polygon' else list(g.geoms)
    t=np.zeros(6)
    for P in polys:
        e=ring_int(P.exterior.coords[:-1]); t+=e*np.sign(e[0])
        for hole in P.interiors:
            k=ring_int(hole.coords[:-1]); t-=k*np.sign(k[0])
    return t  # A, Sy(∫x), Sx(∫y), Iyy(∫x²), Ixx(∫y²), Ixy
def props(g):
    A,Sx_,Sy_,Ixx_,Iyy_,Ixy=integ(g); xs,ys=Sx_/A,Sy_/A
    Iy=Iyy_-A*ys*ys; Iz=Ixx_-A*xs*xs; Iyz=Ixy-A*xs*ys
    return A,xs,ys,Iy,Iz,Iyz
def wpl_h(g):
    """plastisches Widerstandsmoment um eine waagerechte Achse"""
    x0,y0,x1,y1=g.bounds; A=g.area; lo,hi=y0,y1
    for _ in range(60):
        m=(lo+hi)/2
        if g.intersection(box(x0-1,m,x1+1,y1+1)).area>A/2: lo=m
        else: hi=m
    c=(lo+hi)/2; up=g.intersection(box(x0-1,c,x1+1,y1+1)); dn=g.intersection(box(x0-1,y0-1,x1+1,c))
    return up.area*(up.centroid.y-c)+dn.area*(c-dn.centroid.y)
def swap(g):
    from shapely.affinity import affine_transform
    return affine_transform(g,[0,1,1,0,0,0])

# veröffentlichte Werte (Herstellertabellen / Schneider): A [cm²], I_y [cm⁴], (I_z [cm⁴])
PUB = {'IPE 300':(53.8,8356,604),'HEB 200':(78.1,5696,2003),'HEA 1000':(347,553800,14000),'HEB 1000':(400,644700,16280),
  'HEM 200':(131.3,10640,3651),'HEM 300':(303.1,59200,19400),'HEM 1000':(444.2,722300,18460),'HEA 550':(211.8,111900,10820),
  'UPN 100':(13.5,206,29.3),'UPN 200':(32.2,1910,148),'UPN 300':(58.8,8030,495),'UPN 320':(75.8,10870,597),'UPN 400':(91.5,20350,846),
  'UPE 200':(29.0,1910,None),'L 100×10':(19.2,177,None),'L 80×8':(12.3,72.2,None),
  'QRO 100×5':(18.7,279,None),'RO 168,3×8':(40.3,1297,None)}

async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); pg=await br.new_page(viewport={'width':1440,'height':900}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL+'#/stahlbau/profile/walzprofile'); await pg.wait_for_timeout(300)
        PROF=await pg.evaluate("PROF")
        # Anzahl je Reihe
        cnt={}
        for n,v in PROF.items(): cnt[v['reihe']]=cnt.get(v['reihe'],0)+1
        check('Reihen: IPE 18, HEA/HEB/HEM je 24, UPN 16, UPE 14, L 22, QRO 34, RRO 17, RO 17',
              cnt=={'IPE':18,'HEA':24,'HEB':24,'HEM':24,'UPE':14,'UPN':16,'L':22,'QRO':34,'RRO':17,'RO':17}, cnt)
        # I-Profile gegen shapely (alle 90)
        bad=[]
        for n,v in PROF.items():
            if v['typ']!='I': continue
            g=i_shape(v['h'],v['b'],v['tw'],v['tf'],v['r']); A,xs,ys,Iy,Iz,_=props(g)
            Wply=wpl_h(g); Wplz=wpl_h(swap(g))
            for k,ref in [('A',A/100),('Iy',Iy/1e4),('Iz',Iz/1e4),('Wply',Wply/1e3),('Wplz',Wplz/1e3)]:
                if rel(v[k],ref)>0.002: bad.append((n,k,v[k],ref))
        check('alle 90 I-Profile: A, I_y, I_z, W_pl,y, W_pl,z = Geometrie (±0,2 %)', not bad, bad[:3])
        # Hohlprofile gegen shapely
        bad=[]
        for n,v in PROF.items():
            if v['typ']=='RHS':
                t=v['t']; g=rrect(v['b'],v['h'],1.5*t).difference(rrect(v['b']-2*t,v['h']-2*t,t))
                A,_,_,Iy,Iz,_=props(g)
                for k,ref in [('A',A/100),('Iy',Iy/1e4),('Iz',Iz/1e4),('Wply',wpl_h(g)/1e3)]:
                    if rel(v[k],ref)>0.002: bad.append((n,k,v[k],ref))
            if v['typ']=='CHS':
                D,t=v['D'],v['t']; d=D-2*t
                for k,ref in [('A',math.pi*(D*D-d*d)/400),('I',math.pi*(D**4-d**4)/64e4),('Wpl',(D**3-d**3)/6e3)]:
                    if rel(v[k],ref)>0.001: bad.append((n,k,v[k],ref))
        check('alle Hohlprofile QRO/RRO/RO: A, I, W_pl = Geometrie', not bad, bad[:3])
        # Winkel gegen shapely (Ausrundung r1 innen, Kantenrundung r2 an den Schenkelspitzen)
        bad=[]
        for n,v in PROF.items():
            if v['typ']!='L': continue
            b,t,r1,r2=v['b'],v['t'],v['r1'],v['r2']
            g=unary_union([box(0,0,b,t), box(0,0,t,b), spandrel(t,t,r1,1,1)])
            g=g.difference(spandrel(b,t,r2,-1,-1)).difference(spandrel(t,b,r2,-1,-1))
            A,xs,ys,Iy,Iz,Iyz=props(g); m=(Iy+Iz)/2; d=math.hypot((Iy-Iz)/2,Iyz)
            for k,ref in [('A',A/100),('e',xs/10),('Iy',Iy/1e4),('Iu',(m+d)/1e4),('Iv',(m-d)/1e4)]:
                if rel(v[k],ref)>0.003: bad.append((n,k,v[k],ref))
        check('alle 22 Winkel: A, e, I_y, I_u, I_v = Geometrie (±0,3 %)', not bad, bad[:3])
        # veröffentlichte Werte
        bad=[]
        for n,(A,Iy,Iz) in PUB.items():
            v=PROF[n]; Iyv=v.get('Iy', v.get('I'))
            if rel(v['A'],A)>0.012 or rel(Iyv,Iy)>0.012 or (Iz and rel(v['Iz'],Iz)>0.012): bad.append((n,v['A'],Iyv,v.get('Iz')))
        check('Stichproben = veröffentlichte Tabellenwerte (±1,2 %)', not bad, bad)
        e=PROF['IPE 300']; f=PROF['HEB 200']
        check('Torsion/Wölbung: IPE 300 I_t = 20,12 / I_w = 125 900 · HEB 200 I_t = 59,28 / I_w = 171 100',
              rel(e['It'],20.12)<0.01 and rel(e['Iw'],125900)<0.01 and rel(f['It'],59.28)<0.01 and rel(f['Iw'],171100)<0.01, (e['It'],e['Iw'],f['It'],f['Iw']))
        check('Schubfläche IPE 300: A_vz = 25,68 cm²', rel(e['Avz'],25.68)<0.003, e['Avz'])
        # Tabellen auf den Seiten
        for f_,n_ in [('IPE',18),('HEA',24),('HEB',24),('HEM',24)]:
            await pg.click(f'.chip[data-f="{f_}"]')
            k=await pg.evaluate("document.querySelectorAll('#profile-table tbody tr').length")
            if k!=n_: check(f'Tabelle {f_}', False, k)
        check('I-Profil-Tabelle: Filter IPE/HEA/HEB/HEM', True)
        await pg.fill('.tbl-filter input','1000'); await pg.wait_for_timeout(100)
        vis=await pg.evaluate("[...document.querySelectorAll('#profile-tbl tbody tr')].filter(r=>r.style.display!=='none').map(r=>r.cells[0].textContent)")
        check('Filterfeld „1000“ zeigt HEM 1000', vis==['HEM 1000'], vis)

        async def out(id): return await pg.evaluate(f"document.getElementById('{id}').innerText")
        def has(txt, val, d):
            s=f'{val:.{d}f}'.replace('.',','); return s in txt.replace('.','').replace(' ','') or s in txt
        # Steckbrief IPE 300, S235
        o=await out('sb-out'); A=e['A'];
        check('Steckbrief IPE 300 S235: N_pl,Rd, M_pl,y,Rd = 147,7, V_pl,z,Rd',
              has(o,A*23.5,1) and '147,7' in o and has(o,e['Avz']*23.5/math.sqrt(3),1), o[-300:].replace('\n',' '))
        # Klassifizierung IPE 300, S355, N = 400, M = 120
        await pg.goto(URL+'#/stahlbau/nachweise/querschnitt'); await pg.wait_for_timeout(250)
        o=await out('qk-out'); eps=math.sqrt(235/355); c=300-2*10.7-2*15; tw=7.1
        al=min(1,0.5*(1+400/(c/10*tw/10*35.5))); g1=396*eps/(13*al-1) if al>0.5 else 36*eps/al; g2=456*eps/(13*al-1) if al>0.5 else 41.5*eps/al
        sN=400/e['A']; sM=12000/e['Iy']*(c/20); psi=(sN-sM)/(sN+sM); g3=42*eps/(0.67+0.33*psi) if psi>-1 else 62*eps*(1-psi)*math.sqrt(-psi)
        rw=c/tw; kl=1 if rw<=g1 else 2 if rw<=g2 else 3 if rw<=g3 else 4
        check(f'Klasse IPE 300 S355, N = 400 kN, M = 120 kNm: α = {al:.3f}, ψ = {psi:.3f} → Klasse {kl}',
              has(o,al,3) and has(o,psi,3) and f'Klasse {kl}' in o, o[-200:].replace('\n',' '))
        # Querschnittsnachweis IPE 300 S235, N = 250, M = 110, V = 190
        await pg.goto(URL+'#/stahlbau/nachweise/widerstand'); await pg.wait_for_timeout(250)
        o=await out('qn-out'); fy=23.5; Npl=e['A']*fy; Vpl=e['Avz']*fy/math.sqrt(3); Mpl=e['Wply']*fy/100
        rho=(2*190/Vpl-1)**2 if 190>0.5*Vpl else 0; Aw=e['hw']*e['tw']/100; Mv=min(Mpl,(e['Wply']-rho*Aw*Aw/(4*e['tw']/10))*fy/100)
        n=250/Npl; a=min(0.5,(e['A']*100-2*e['b']*e['tf'])/(e['A']*100))
        red = not (250<=0.25*Npl and 250<=0.5*e['hw']*e['tw']/100*fy)
        MN=min(Mv,Mv*(1-n)/(1-0.5*a)) if red else Mv
        check(f'Querschnitt IPE 300: V_pl = {Vpl:.1f}, ρ = {rho:.3f}, M_V = {Mv:.1f}, M_N = {MN:.1f}, η = {110/MN:.3f}',
              has(o,Vpl,1) and has(o,rho,3) and has(o,Mv,1) and has(o,MN,1) and has(o,110/MN,3), o[-260:].replace('\n',' '))
        ztxt=await pg.evaluate("[...document.querySelectorAll('.ablauf')].find(a=>a.innerText.includes('Flachstahl')).innerText")
        check('Zugstab 100 × 10, Loch 18: N_pl = 235,0, N_u = 0,9·820·360/1,25 = 212,5 kN', '235,0' in ztxt and '212,5' in ztxt, ztxt[-120:].replace('\n',' '))
        # Biegeknicken HEB 200 z, 4 m, N = 600
        await pg.goto(URL+'#/stahlbau/nachweise/biegeknicken'); await pg.wait_for_timeout(250)
        o=await out('kn-out'); lb=400/f['iz']/(math.pi*math.sqrt(210000/235)); Phi=0.5*(1+0.49*(lb-0.2)+lb*lb); chi=1/(Phi+math.sqrt(Phi*Phi-lb*lb)); Nb=chi*f['A']*23.5/1.1
        check(f'Biegeknicken HEB 200: λ̄ = {lb:.3f}, χ = {chi:.3f}, N_b,Rd = {Nb:.0f}, η = {600/Nb:.3f}', has(o,lb,3) and has(o,chi,3) and has(o,Nb,0) and has(o,600/Nb,3), o[-200:].replace('\n',' '))
        # S460, IPE: Knicklinie a0 (y)
        await pg.select_option('#kn-st','S460'); await pg.select_option('#kn-prof','IPE 300'); await pg.select_option('#kn-ax','y'); await pg.wait_for_timeout(150)
        check('Knicklinie IPE 300, S460, y–y = a0', 'Knicklinie a0' in await out('kn-out'))
        await pg.select_option('#kn-st','S235'); await pg.select_option('#kn-prof','HEM 1000'); await pg.wait_for_timeout(150)
        o=await out('kn-out').replace('\n',' ') if False else (await out('kn-out')).replace('\n',' ')
        check('HEM 1000: t_f = 40 mm → f_y = 235 N/mm², h/b > 1,2 → Knicklinie a (y)', '235 N/mm²' in o and 'Knicklinie a,' in o, o[:200])
        # Biegedrillknicken IPE 300, S235, L = 6, Gleichlast am Obergurt, M = 60
        await pg.goto(URL+'#/stahlbau/nachweise/biegedrillknicken'); await pg.wait_for_timeout(250)
        def mcr(v,L,C1,C2,zg):
            E,G=21000,8100; a=math.pi**2*E*v['Iz']/L**2
            return C1*a*(math.sqrt(v['Iw']/v['Iz']+L*L*G*v['It']/(math.pi**2*E*v['Iz'])+(C2*zg)**2)-C2*zg)
        def chiLT(v,lb,kc):
            al=0.34 if v['h']/v['b']<=2 else 0.49; Ph=0.5*(1+al*(lb-0.4)+0.75*lb*lb)
            c=1 if lb<=0.4 else min(1,1/(Ph+math.sqrt(Ph*Ph-0.75*lb*lb)),1/lb**2)
            fm=min(1,1-0.5*(1-kc)*(1-2*(lb-0.8)**2)); return c, min(1,c/fm,1/lb**2)
        M=mcr(e,600,1.13,0.45,15.0); lb=math.sqrt(e['Wply']*23.5/M); c,cm=chiLT(e,lb,0.94); Mb=cm*e['Wply']*23.5/1.1/100
        o=await out('bd-out')
        check(f'Kippen IPE 300, 6 m, q am OG: M_cr = {M/100:.1f} kNm, λ̄_LT = {lb:.3f}, χ_mod = {cm:.3f}, M_b,Rd = {Mb:.1f}',
              has(o,M/100,1) and has(o,lb,3) and has(o,cm,3) and has(o,Mb,1) and has(o,60/Mb,3), o[-200:].replace('\n',' '))
        # Plausibilität M_cr: konstantes Moment = klassische Formel (π/L)·√(E I_z G I_t)·√(1 + π² E I_w/(L² G I_t))
        await pg.select_option('#bd-fall','M'); await pg.wait_for_timeout(150); o=await out('bd-out')
        E,G=21000,8100; L=600; Mc=math.pi/L*math.sqrt(E*e['Iz']*G*e['It'])*math.sqrt(1+math.pi**2*E*e['Iw']/(L*L*G*e['It']))
        check(f'M_cr konstantes Moment = klassische Kippformel ({Mc/100:.1f} kNm)', has(o,Mc/100,1), o[:0])
        await pg.select_option('#bd-fall','psi'); await pg.fill('#bd-psi','-1'); await pg.wait_for_timeout(150); o=await out('bd-out')
        check('ψ = −1: C1 = 2,55 nach NCCI SN003a', '2,550' in o)
        # Biegung und Druck HEB 200, S235, L = 5/5, N = 500, M = 40, ψ = 0
        await pg.goto(URL+'#/stahlbau/nachweise/interaktion'); await pg.wait_for_timeout(250)
        v=f; fy=23.5; lam1=math.pi*math.sqrt(210000/235)
        NRk=v['A']*fy; MRk=v['Wply']*fy/100
        def chi_(lb,al):
            if lb<=0.2: return 1
            Ph=0.5*(1+al*(lb-0.2)+lb*lb); return min(1,1/(Ph+math.sqrt(Ph*Ph-lb*lb)))
        lby=500/v['iy']/lam1; lbz=500/v['iz']/lam1; cy=chi_(lby,0.34); cz=chi_(lbz,0.49)
        M_=mcr(v,500,1.77,0,0); lbLT=math.sqrt(MRk*100/M_); _,cLT=chiLT(v,lbLT,1/1.33)
        Cm=0.6; ny=500/(cy*NRk/1.1); nz=500/(cz*NRk/1.1)
        kyy=min(Cm*(1+(lby-0.2)*ny),Cm*(1+0.8*ny))
        kzy=max(1-0.1*lbz*nz/(Cm-0.25),1-0.1*nz/(Cm-0.25)) if lbz>=0.4 else min(0.6+lbz,1-0.1*lbz*nz/(Cm-0.25))
        MbR=cLT*MRk/1.1; e61=ny+kyy*40/MbR; e62=nz+kzy*40/MbR
        o=await out('in-out')
        check(f'Interaktion HEB 200: χy = {cy:.3f}, χz = {cz:.3f}, χLT = {cLT:.3f}, kyy = {kyy:.3f}, kzy = {kzy:.3f}',
              all(has(o,x,3) for x in (cy,cz,cLT,kyy,kzy)), o[-200:].replace('\n',' '))
        check(f'Interaktion HEB 200: (6.61) = {e61:.3f}, (6.62) = {e62:.3f}', has(o,e61,3) and has(o,e62,3))
        # Durchbiegung IPE 300, 6 m, q = 15
        await pg.goto(URL+'#/stahlbau/nachweise/gebrauch'); await pg.wait_for_timeout(250)
        w=5*0.15*600**4/(384*21000*e['Iy'])*10; o=await out('db-out')
        check(f'Durchbiegung IPE 300, 6 m, q = 15: w = {w:.1f} mm, L/300 = 20 mm', has(o,w,1) and '20,0' in o, o[-120:].replace('\n',' '))
        # Schrauben: 2 × 2 M20 8.8, Gewinde, einschnittig, t = 10, S235, e1 40, e2 35, p1 70, p2 70
        await pg.goto(URL+'#/stahlbau/verbindungen/schrauben'); await pg.wait_for_timeout(250)
        Fv=0.6*800*245/1.25/1000; d0=22; fu=360
        abE=min(40/(3*d0),800/fu,1); abI=min(70/(3*d0)-0.25,800/fu,1); k1=min(2.8*35/d0-1.7,1.4*70/d0-1.7,2.5)
        FbE=k1*abE*fu*20*10/1.25/1000; FbI=k1*abI*fu*20*10/1.25/1000
        FRd = 2*FbE+2*FbI if Fv>=max(FbE,FbI) else 4*min(Fv,FbE,FbI)
        o=await out('sr-out')
        check(f'Schrauben 2×2 M20 8.8: F_v,Rd = {Fv:.1f}, F_b,Rd = {FbE:.1f} / {FbI:.1f}, F_Rd = {FRd:.1f} kN',
              has(o,Fv,1) and has(o,FbE,1) and has(o,FbI,1) and has(o,FRd,1) and has(o,250/FRd,3), o[-200:].replace('\n',' '))
        await pg.select_option('#sr-m','2'); await pg.select_option('#sr-kl','4.6'); await pg.wait_for_timeout(150)
        Fv2=2*0.6*400*245/1.25/1000; ab2=min(40/(3*d0),400/fu,1); ab2i=min(70/(3*d0)-0.25,400/fu,1)
        Fb2=[k1*x*fu*20*10/1.25/1000 for x in (ab2,ab2,ab2i,ab2i)]
        F2 = sum(Fb2) if all(Fv2>=x for x in Fb2) else 4*min([Fv2]+Fb2)
        o=await out('sr-out'); check(f'zweischnittig 4.6: F_v,Rd = {Fv2:.1f}, F_Rd = {F2:.1f} kN', has(o,Fv2,1) and has(o,F2,1), o[-150:].replace('\n',' '))
        # Kehlnaht: S235, a = 4, l = 150, 2 Nähte, t 10/12, F = 200
        await pg.goto(URL+'#/stahlbau/verbindungen/schweissen'); await pg.wait_for_timeout(250)
        fvw=360/(math.sqrt(3)*0.8*1.25); FR=2*(150-8)*fvw*4/1000; o=await out('kw-out')
        check(f'Kehlnaht a = 4, 2 × 150 mm, S235: f_vw,d = {fvw:.1f} N/mm², F_Rd = {FR:.1f} kN', has(o,fvw,1) and has(o,FR,1) and has(o,200/FR,3), o[-150:].replace('\n',' '))
        # alle Stahlbau-Seiten: keine NaN, mobil ohne Querscrollen
        T=['werkstoff/stahlsorten','profile/walzprofile','profile/uprofile','profile/winkel','profile/hohlprofile','nachweise/querschnitt','nachweise/widerstand','nachweise/biegeknicken','nachweise/biegedrillknicken','nachweise/interaktion','nachweise/gebrauch','verbindungen/schrauben','verbindungen/schweissen']
        await pg.set_viewport_size({'width':390,'height':844}); badp=[]
        for t in T:
            await pg.goto(URL+'#/stahlbau/'+t); await pg.wait_for_timeout(200)
            r=await pg.evaluate("[document.documentElement.scrollWidth, /NaN|undefined|Infinity/.test(document.getElementById('main').innerText)]")
            if r[0]>390 or r[1]: badp.append((t,r))
        check('13 Stahlbau-Seiten: keine NaN, Handy ohne Querscrollen', not badp, badp)
        check('keine Skriptfehler', not errs, errs[:2])
        await br.close()
asyncio.run(main())
print('FAILS:', fails)
