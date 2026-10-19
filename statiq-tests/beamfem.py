"""Unabhängige 1D-Balken-FEM (Euler-Bernoulli + Stab), Referenz für Einfeldträger,
Kragarm und Durchlaufträger. x nach rechts, y nach oben.
Eingabe: L, supports [(x,'pin'|'roller'|'fixed')], points [(x,Fx→,Fy↓,Me cw)],
dists [(a,b,qa,qb) ↓], EI.
Ausgabe an Stützstellen: M (Zug unten +), Q = dM/dx, N (Zug +), v (m, nach oben +)."""
import numpy as np
def solve(L, supports, points, dists, EI, nseg=400):
    st=set(np.linspace(0,L,nseg+1).round(10))
    for x,_ in supports: st.add(round(x,10))
    for p in points: st.add(round(p[0],10))
    for a,b,_,_ in dists: st.add(round(a,10)); st.add(round(min(b,L),10))
    xs=sorted(st); n=len(xs); nd=3*n; EA=1e6*EI
    K=np.zeros((nd,nd)); F=np.zeros(nd)
    def q(x):
        v=0
        for a,b,qa,qb in dists:
            b=min(b,L)
            if b-a>1e-12 and a-1e-12<=x<=b+1e-12: v+=qa+(qb-qa)*(x-a)/(b-a)
        return v
    gp,gw=np.polynomial.legendre.leggauss(6); els=[]
    for i in range(n-1):
        l=xs[i+1]-xs[i]
        k=np.array([[EA/l,0,0,-EA/l,0,0],[0,12*EI/l**3,6*EI/l**2,0,-12*EI/l**3,6*EI/l**2],
            [0,6*EI/l**2,4*EI/l,0,-6*EI/l**2,2*EI/l],[-EA/l,0,0,EA/l,0,0],
            [0,-12*EI/l**3,-6*EI/l**2,0,12*EI/l**3,-6*EI/l**2],[0,6*EI/l**2,2*EI/l,0,-6*EI/l**2,4*EI/l]])
        fe=np.zeros(6)
        for g,w in zip(gp,gw):
            t=(g+1)/2; py=-q(xs[i]+t*l)*w*l/2
            fe+=py*np.array([0,1-3*t*t+2*t**3,l*(t-2*t*t+t**3),0,3*t*t-2*t**3,l*(-t*t+t**3)])
        d=list(range(3*i,3*i+6)); K[np.ix_(d,d)]+=k; F[d]+=fe; els.append((k,fe,d))
    idx={round(x,10):i for i,x in enumerate(xs)}
    for x,Fx,Fy,Me in points:
        i=idx[round(x,10)]; F[3*i]+=Fx; F[3*i+1]-=Fy; F[3*i+2]-=Me
    fixed=[]
    for x,t in supports:
        i=idx[round(x,10)]; fixed+=[3*i+1]
        if t in('pin','fixed'): fixed+=[3*i]
        if t=='fixed': fixed+=[3*i+2]
    free=[j for j in range(nd) if j not in fixed]
    u=np.zeros(nd); u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free]); R=K@u-F
    X=[];M=[];Q=[];N=[];V=[]
    for i,(k,fe,d) in enumerate(els):
        f=k@u[d]-fe
        X.append(xs[i]);M.append(-f[2]);Q.append(f[1]);N.append(-f[0]);V.append(u[3*i+1])
    f=els[-1][0]@u[els[-1][2]]-els[-1][1]
    X.append(xs[-1]);M.append(f[5]);Q.append(-f[4]);N.append(f[3]);V.append(u[3*(n-1)+1])
    reac=[(R[3*idx[round(x,10)]],R[3*idx[round(x,10)]+1],R[3*idx[round(x,10)]+2]) for x,_ in supports]
    return dict(x=np.array(X),M=np.array(M),Q=np.array(Q),N=np.array(N),v=np.array(V),reac=reac)
