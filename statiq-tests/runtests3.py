# v0.7-Tests: exakte Spitzen, exakte Verschiebungen, Stützen-Streckenlasten, Sprünge
import json, numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runtests import app
from fem import solve
def fem_interp(res,m,key,t):
    pts=np.array(res[m]['pts']); v=np.array(res[m][key])
    s=np.hypot(pts[:,0]-pts[0,0],pts[:,1]-pts[0,1]); s/=s[-1]
    return np.interp(t,s,v), s, v
def jump_near(s,v,t,tol=2e-3):
    # FEM-Wert springt in der Nähe von t → Vergleich dort überspringen
    i=np.searchsorted(s,t)
    for j in range(max(i-2,1),min(i+2,len(s))):
        if abs(s[j]-t)<tol and abs(v[j]-v[j-1])>0.05: return True
    return False
Q10={'member':'rafter','qa':10,'qb':10,'a':0,'b':5}
cases=[
 ('pin/pin F Riegel x=1.73 (nicht auf Raster)',dict(A='pin',B='pin',q=[],F=[{'member':'rafter','F':20,'z':1.73}])),
 ('fix/fix q + F Riegel x=3.37',dict(A='fixed',B='fixed',q=[Q10],F=[{'member':'rafter','F':15,'z':3.37}])),
 ('fix/fix F li. Stütze z=2.63',dict(A='fixed',B='fixed',q=[],F=[{'member':'left','F':8,'z':2.63}])),
 ('fix/pin q+F+F',dict(A='fixed',B='pin',q=[Q10],F=[{'member':'left','F':5,'z':2},{'member':'right','F':5,'z':2}])),
 ('pin/pin 3-Gelenk q+F',dict(A='pin',B='pin',q=[Q10],F=[{'member':'left','F':5,'z':3}],hinges=[{'member':'rafter','pos':2.5}])),
 ('fix/roller + Kopfhalt. links',dict(A='fixed',B='roller',q=[Q10],F=[],head='left',headType='roller')),
 ('fix/fix hA≠hB Trapez',dict(A='fixed',B='fixed',hB=3,q=[{'member':'rafter','qa':4,'qb':12,'a':1,'b':4}],F=[{'member':'left','F':5,'z':2}])),
 ('fix/fix EI Riegel 3x + Stützengelenk',dict(A='fixed',B='fixed',IR=30,q=[Q10],F=[],hinges=[{'member':'right','pos':1.5}])),
 ('fix/fix Wind q→ li. Stütze',dict(A='fixed',B='fixed',q=[{'member':'left','qa':3,'qb':3,'a':0,'b':4,'dir':'h'}],F=[])),
 ('pin/pin Wind Druck+Sog',dict(A='pin',B='pin',q=[Q10,{'member':'left','qa':2,'qb':2,'a':0,'b':4,'dir':'h'},{'member':'right','qa':1,'qb':1,'a':0,'b':4,'dir':'h'}],F=[])),
 ('fix/pin Trapez-Wind Teilbereich re.',dict(A='fixed',B='pin',q=[{'member':'right','qa':1,'qb':4,'a':0.5,'b':3.2,'dir':'h'}],F=[])),
 ('fix/fix axial q li. Stütze',dict(A='fixed',B='fixed',q=[Q10,{'member':'left','qa':2,'qb':2,'a':0,'b':4,'dir':'ax'}],F=[])),
 ('fix/fix Wind hA≠hB',dict(A='fixed',B='fixed',hA=4,hB=3,q=[{'member':'left','qa':3,'qb':3,'a':0,'b':4,'dir':'h'},{'member':'right','qa':-1.5,'qb':-1.5,'a':0,'b':3,'dir':'h'}],F=[])),
]
fails=0
for name,c in cases:
    cfg={**dict(b=5,hA=4,hB=4,hinges=[]),**c}; a=app(cfg); f=solve(cfg)
    if a['err'] or not a['r'] or 'fine' not in a['r']:
        print('FAIL',name,a['err']); fails+=1; continue
    fine=a['r']['fine']; worst={}
    for key in ['M','Q','N','ux','uy']:
        w=0
        for m in ['L','R','Rr']:
            t=np.array(fine[m]['t']); got=np.array(fine[m][key])
            ref,s,v=fem_interp(f,m,key,t)
            if key in ('ux','uy'): got=got*1000; ref=ref*1000   # mm
            d=np.abs(ref-got)
            if key in 'QN': d=np.array([0 if jump_near(s,v,ti) else x for ti,x in zip(t,d)])
            w=max(w,d.max())
        worst[key]=w
    # Spitzenwerte: App-max gegen FEM-max (FEM hat Stützstellen an allen Lastpunkten)
    fm=max(abs(x) for m in ['L','R','Rr'] for x in f[m]['M'])
    dmax=abs(a['r']['max']['M']-fm)
    ok=worst['M']<0.01 and worst['Q']<0.01 and worst['N']<0.01 and worst['ux']<0.005 and worst['uy']<0.005 and dmax<0.01
    fails+=not ok
    print('OK  ' if ok else 'FAIL',f'{name:40}','ΔM=%.4f ΔQ=%.4f ΔN=%.4f Δux=%.4fmm Δuy=%.4fmm Δmax|M|=%.4f (max %.2f)'%(worst['M'],worst['Q'],worst['N'],worst['ux'],worst['uy'],dmax,fm))
# Spitze unter Einzellast: feines Array enthält exakt den Lastpunkt, Q springt dort um F
a=app(dict(A='pin',B='pin',b=5,hA=4,hB=4,hinges=[],q=[],F=[{'member':'rafter','F':20,'z':1.73}]))
R=a['r']['fine']['R']; t=np.array(R['t']); i=[k for k in range(1,len(t)) if abs(t[k]-t[k-1])<1e-9]
ok=len(i)==1 and abs(t[i[0]]-1.73/5)<1e-9 and abs(abs(R['Q'][i[0]]-R['Q'][i[0]-1])-20)<1e-6
fails+=not ok
print('OK  ' if ok else 'FAIL','Sprung Q=20 genau bei x=1.73 (doppelte Stützstelle)', i and (t[i[0]]*5, R['Q'][i[0]-1], R['Q'][i[0]]))
# Uniformes Raster verpasst die Spitze, feines nicht
uni=max(abs(x) for x in a['r']['M']['R'])
fr=solve(dict(A='pin',B='pin',b=5,hA=4,hB=4,hinges=[],q=[],F=[{'member':'rafter','F':20,'z':1.73}]))
print('INFO','max M uniform %.3f  fein %.3f  FEM %.3f'%(uni,a['r']['max']['M'],max(abs(x) for m in ['L','R','Rr'] for x in fr[m]['M'])))
print('FAILS:',fails)
