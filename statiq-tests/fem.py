"""Independent 2D frame FEM reference (Euler-Bernoulli, EA large).
Geometry: A(0,0) - K2(0,hA) - K3(b,hB) - B(b,0).
Sign convention for output moments: positive = tension on the INNER face
(left col: right face, rafter: bottom face, right col: left face)."""
import numpy as np, json, sys

def solve(cfg, nseg=200):
    b,hA,hB = cfg['b'],cfg['hA'],cfg['hB']
    EI_S = 2100*cfg.get('IS',10); EI_R = 2100*cfg.get('IR',10)  # kNm² wie in der App (E·Iy·10)
    # --- member stations (param s in [0,1]) ---
    def stations(extra):
        s=set(np.linspace(0,1,nseg+1).round(12))
        for e in extra: s.add(round(min(max(e,0),1),12))
        return sorted(s)
    Fl=[f for f in cfg.get('F',[])]
    hinges=cfg.get('hinges',[])
    exL=[f['z']/hA for f in Fl if f.get('member','left')=='left']+[h['pos']/hA for h in hinges if h['member']=='left']
    exR=[f['z']/hB for f in Fl if f.get('member')=='right']+[h['pos']/hB for h in hinges if h['member']=='right']
    exT=[h['pos']/b for h in hinges if h['member']=='rafter']+[f['z']/b for f in Fl if f.get('member')=='rafter']
    for q in cfg.get('q',[]):
        mm=q.get('member','rafter')
        if mm=='rafter': exT += [q['a']/b, min(q['b'],b)/b]
        elif mm=='left': exL += [q['a']/hA, q['b']/hA]
        else: exR += [q['a']/hB, q['b']/hB]
    # members: list of node coordinates; left: A->K2, rafter K2->K3, right K3->B (head->foot)
    mem={'L':[(0,s*hA) for s in stations(exL)],
         'R':[(s*b,hA+(hB-hA)*s) for s in stations(exT)],
         'Rr':[(b,hB*(1-s)) for s in stations([1-e for e in exR])]}
    # node registry with DOF (ux,uy,rot); hinges -> separate rot DOF
    ndof=0; nodes=[]  # (x,y,dofs)
    def newdof():
        nonlocal ndof; ndof+=1; return ndof-1
    tr_dof={}  # coordinate -> (ux,uy)
    def trans(p):
        k=(round(p[0],9),round(p[1],9))
        if k not in tr_dof: tr_dof[k]=(newdof(),newdof())
        return tr_dof[k]
    rot_dof={}
    def rot(p,tag):
        k=(round(p[0],9),round(p[1],9),tag)
        if k not in rot_dof: rot_dof[k]=newdof()
        return rot_dof[k]
    hingepts={}
    for h in hinges:
        if h['member']=='left': hingepts[(0.0,round(h['pos'],9))]='L'
        if h['member']=='right': hingepts[(round(b,9),round(h['pos'],9))]='Rr'
        if h['member']=='rafter':
            x=h['pos']; hingepts[(round(x,9),round(hA+(hB-hA)*x/b,9))]='R'
    elems=[]
    for m,pts in mem.items():
        EI=EI_R if m=='R' else EI_S
        for i in range(len(pts)-1):
            p,q_=pts[i],pts[i+1]
            if np.hypot(q_[0]-p[0],q_[1]-p[1])<1e-12: continue
            def rd(pt,side):
                k=(round(pt[0],9),round(pt[1],9))
                return rot(pt,(m,i,side) if k in hingepts else 'rigid')
            elems.append(dict(m=m,i=i,p=p,q=q_,EI=EI,
                dofs=[*trans(p),rd(p,'a'),*trans(q_),rd(q_,'b')]))
    # fix duplicate hinge DOF: rd with (m,i,side) makes each element side separate -> true hinge
    K=np.zeros((ndof,ndof)); F=np.zeros(ndof)
    def loc(e):
        (x1,y1),(x2,y2)=e['p'],e['q']; L=np.hypot(x2-x1,y2-y1); c=(x2-x1)/L; s=(y2-y1)/L
        EI=e['EI']; EA=1e6*EI
        k=np.array([[EA/L,0,0,-EA/L,0,0],
            [0,12*EI/L**3,6*EI/L**2,0,-12*EI/L**3,6*EI/L**2],
            [0,6*EI/L**2,4*EI/L,0,-6*EI/L**2,2*EI/L],
            [-EA/L,0,0,EA/L,0,0],
            [0,-12*EI/L**3,-6*EI/L**2,0,12*EI/L**3,-6*EI/L**2],
            [0,6*EI/L**2,2*EI/L,0,-6*EI/L**2,4*EI/L]])
        T=np.zeros((6,6)); R=np.array([[c,s,0],[-s,c,0],[0,0,1]]); T[:3,:3]=R; T[3:,3:]=R
        return k,T,L
    # element fixed-end forces (global) for vertical load on rafter per horizontal length
    def qx(x, rd='v'):
        v=0
        for q in cfg.get('q',[]):
            if q.get('member','rafter')!='rafter' or q.get('rdir','v')!=rd: continue
            a,bb=q['a'],min(q['b'],b)
            if a-1e-12<=x<=bb+1e-12 and bb>a: v+=q['qa']+(q['qb']-q['qa'])*(x-a)/(bb-a)
        return v
    for e in elems:
        k,T,L=loc(e); e['k'],e['T'],e['L']=k,T,L
        fe=np.zeros(6)
        if e['m']=='R':
            # consistent loads via Gauss integration of downward load (per horizontal dx) in local coords
            dxh=e['q'][0]-e['p'][0]
            gp,gw=np.polynomial.legendre.leggauss(6)
            c,s=T[0,0],T[0,1]
            for xi,w in zip(gp,gw):
                t=(xi+1)/2; x=e['p'][0]+t*dxh; pv=-qx(x)*dxh*w/2  # global Fy increment
                # rechtwinklig zum Riegel (je m Stablänge, + = (sin, −cos)) und waagerecht (je m Höhe)
                dyh=e['q'][1]-e['p'][1]; qn=qx(x,'n')*L*w/2; qh=qx(x,'h')*abs(dyh)*w/2
                Gx=qn*s+qh; Gy=pv-qn*c
                pl=np.array([Gx*c+Gy*s,-Gx*s+Gy*c]); ss=t*L
                N=[1-3*t*t+2*t**3, L*(t-2*t*t+t**3), 3*t*t-2*t**3, L*(-t*t+t**3)]
                fe+=np.array([pl[0]*(1-t),pl[1]*N[0],pl[1]*N[1],pl[0]*t,pl[1]*N[2],pl[1]*N[3]])
        else:
            # Stützen-Streckenlast: z = Höhe über Fuß, global (gx,gy) je m
            mm='left' if e['m']=='L' else 'right'
            gp,gw=np.polynomial.legendre.leggauss(6)
            c,s=T[0,0],T[0,1]
            for xi,w in zip(gp,gw):
                t=(xi+1)/2; y=e['p'][1]+t*(e['q'][1]-e['p'][1]); gx=gy=0
                for q in cfg.get('q',[]):
                    if q.get('member','rafter')!=mm: continue
                    lo,hi=min(q['a'],q['b']),max(q['a'],q['b'])
                    if hi-lo<1e-12 or y<lo-1e-12 or y>hi+1e-12: continue
                    qq=q['qa']+(q['qb']-q['qa'])*(y-q['a'])/(q['b']-q['a'])
                    if q.get('dir')=='h': gx+=qq
                    else: gy-=qq
                W=w*L/2; pl=np.array([(gx*c+gy*s)*W,(-gx*s+gy*c)*W])
                N=[1-3*t*t+2*t**3, L*(t-2*t*t+t**3), 3*t*t-2*t**3, L*(-t*t+t**3)]
                fe+=np.array([pl[0]*(1-t),pl[1]*N[0],pl[1]*N[1],pl[0]*t,pl[1]*N[2],pl[1]*N[3]])
        e['fe_loc']=fe
        kg=T.T@k@T; d=e['dofs']
        K[np.ix_(d,d)]+=kg; F[d]+=T.T@fe
    for f in Fl:
        mm=f.get('member','left'); Fp=f.get('F',0); Hp=f.get('H',0)
        if mm=='left': d=tr_dof[(0.0,round(f['z'],9))]; F[d[0]]+=-Fp; F[d[1]]+=-Hp
        elif mm=='right': d=tr_dof[(round(b,9),round(f['z'],9))]; F[d[0]]+=Fp; F[d[1]]+=-Hp
        else:
            x=f['z']; d=tr_dof[(round(x,9),round(hA+(hB-hA)*x/b,9))]
            L=np.hypot(b,hB-hA); c=b/L; s=(hB-hA)/L
            F[d[0]]+=Fp*s+Hp*c; F[d[1]]+=-Fp*c+Hp*s
    # supports
    fixed=[]
    for pt,t,m in [((0,0),cfg['A'],'L'),((b,0),cfg['B'],'Rr')]:
        ux,uy=tr_dof[(round(pt[0],9),round(pt[1],9))]
        if t in('fixed','pin'): fixed+=[ux,uy]
        else: fixed+=[uy]
        if t=='fixed':
            fixed+=[e['dofs'][2 if e['p']==pt else 5] for e in elems if (e['p']==pt or e['q']==pt)]
    if cfg.get('head') in ('left','right'):
        pt=(0.0,round(hA,9)) if cfg['head']=='left' else (round(b,9),round(hB,9))
        ux,uy=tr_dof[pt]; fixed+=[ux]+([uy] if cfg.get('headType')=='pin' else [])
    free=[i for i in range(ndof) if i not in fixed]
    u=np.zeros(ndof)
    Kff=K[np.ix_(free,free)]
    # Mechanismus erkennen: kleinster/größter Eigenwert der (symmetrischen) Steifigkeitsmatrix
    # Diagonal skaliert, dann kleinster/größter Eigenwert: stabile Systeme ~1e-12…1e-13,
    # verschiebliche ≤ 1e-16 (geprüft an bekannten Fällen)
    dsc=1/np.sqrt(np.abs(np.diag(Kff))); ev=np.linalg.eigvalsh(Kff*dsc[:,None]*dsc[None,:])
    if ev[0] <= 1e-14*ev[-1]: raise ValueError('mechanism (FEM: singuläre Steifigkeitsmatrix)')
    u[free]=np.linalg.solve(Kff,F[free])
    Rf=K@u-F
    # internal moments per member, inner-tension positive (sagging wrt local y = left of direction)
    res={}
    for m in mem:
        es=[e for e in elems if e['m']==m]
        xs=[];Ms=[];Qs=[];Ns=[]
        for e in es:
            fl=e['k']@(e['T']@u[e['dofs']])-e['fe_loc']
            s0=e['i']
            xs.append(e['p']);Ms.append(-fl[2]);Qs.append(fl[1]);Ns.append(-fl[0])
        e=es[-1]; fl=e['k']@(e['T']@u[e['dofs']])-e['fe_loc']
        xs.append(e['q']);Ms.append(fl[5]);Qs.append(-fl[4]);Ns.append(fl[3])
        ux=[u[tr_dof[(round(p[0],9),round(p[1],9))][0]] for p in xs]
        uy=[u[tr_dof[(round(p[0],9),round(p[1],9))][1]] for p in xs]
        res[m]=dict(pts=xs,M=Ms,Q=Qs,N=Ns,ux=ux,uy=uy)
    def reac(pt):
        ux,uy=tr_dof[(round(pt[0],9),round(pt[1],9))]
        rd=[e['dofs'][2 if e['p']==pt else 5] for e in elems if (e['p']==pt or e['q']==pt)]
        return Rf[ux],Rf[uy],sum(Rf[r] for r in rd)
    res['reac']={'A':reac((0,0)),'B':reac((b,0))}
    return res

if __name__=='__main__':
    cfg=json.loads(sys.argv[1]); r=solve(cfg)
    L,R,Rr=r['L']['M'],r['R']['M'],r['Rr']['M']
    print('FussA %.3f KopfA %.3f Feldmax %.3f KopfB %.3f FussB %.3f'%(L[0],L[-1],max(R,key=abs) if False else R[len(R)//2],Rr[0],Rr[-1]))
    print('Reac',r['reac'])
