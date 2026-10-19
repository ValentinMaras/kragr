# statiq·calc v0.8.10: Streckenlast auf dem Riegel rechtwinklig zum Riegel (Wind auf die Dachfläche) und waagerecht.
# Vergleich mit dem unabhängigen FEM-Modell (fem.py) und Gleichgewichtskontrollen.
import os, sys, re, math, json, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from runtests import app, fem_at
from fem import solve
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:62}', info)
def worst(a,f):
    NP=a['r']['NP']; return max(np.abs(fem_at(f,m,NP)-np.array(a['r']['M'][m])).max() for m in ['L','R','Rr'])
def reac(a):
    rows=re.findall(r'<tr><td>(\w)</td><td>([-\d.,]+)</td><td>([-\d.,]+)</td>', a['table'])
    return {k:(float(h.replace(',','.')),float(v.replace(',','.'))) for k,h,v in rows}
CASES=[('Zweigelenk, Pultdach 4→6 m, ⊥ 2 kN/m', dict(A='pin',B='pin',b=5,hA=4,hB=6,q=[{'member':'rafter','qa':2,'qb':2,'a':0,'b':5,'rdir':'n'}])),
       ('eingespannt, Pultdach 6→4 m, ⊥ Sog −1,5 kN/m', dict(A='fixed',B='fixed',b=6,hA=6,hB=4,q=[{'member':'rafter','qa':-1.5,'qb':-1.5,'a':0,'b':6,'rdir':'n'}])),
       ('Festlager/Loslager, ⊥ Trapez 1→3 auf 1…4 m', dict(A='pin',B='roller',b=5,hA=3,hB=5,q=[{'member':'rafter','qa':1,'qb':3,'a':1,'b':4,'rdir':'n'}])),
       ('Dreigelenk, Pultdach, waagerecht 3 kN/m', dict(A='pin',B='pin',b=5,hA=4,hB=6,q=[{'member':'rafter','qa':3,'qb':3,'a':0,'b':5,'rdir':'h'}],hinges=[{'member':'rafter','pos':2.5}])),
       ('eingespannt, alle drei Richtungen gemischt', dict(A='fixed',B='pin',b=5,hA=4,hB=5.5,q=[{'member':'rafter','qa':4,'qb':4,'a':0,'b':5},{'member':'rafter','qa':1.2,'qb':1.2,'a':0,'b':5,'rdir':'n'},{'member':'rafter','qa':2,'qb':0,'a':0,'b':5,'rdir':'h'}]))]
for name,cfg in CASES:
    cfg={**{'F':[],'hinges':[]},**cfg}
    a=app(cfg); f=solve(cfg)
    w=worst(a,f) if a['r'] else 1e9
    check(f'{name}: M wie FEM', w<0.05, f'max|ΔM| = {w:.4f} kNm')
# Gleichgewicht: Summe der Lasten = − Summe der Auflagerkräfte
cfg=dict(A='pin',B='pin',b=5,hA=4,hB=6,F=[],hinges=[],q=[{'member':'rafter','qa':2,'qb':2,'a':0,'b':5,'rdir':'n'}])
R=reac(app(cfg)); L=math.hypot(5,2); s,c=2/L,5/L
check('⊥ 2 kN/m: ΣH = −q·L·sin α, ΣV = q·L·cos α', abs(R['A'][0]+R['B'][0]+2*L*s)<0.02 and abs(R['A'][1]+R['B'][1]-2*L*c)<0.02, R)
cfg['q'][0]['rdir']='h'; R=reac(app(cfg))
check('waagerecht 2 kN/m je m Höhe: ΣH = −q·Δh = −4 kN, ΣV = 0', abs(R['A'][0]+R['B'][0]+4)<0.02 and abs(R['A'][1]+R['B'][1])<0.02, R)
# Flacher Riegel: ⊥ entspricht der senkrechten Last, waagerecht ergibt nichts
base=dict(A='fixed',B='fixed',b=5,hA=4,hB=4,F=[],hinges=[])
a1=app({**base,'q':[{'member':'rafter','qa':5,'qb':5,'a':0,'b':5,'rdir':'n'}]}); a2=app({**base,'q':[{'member':'rafter','qa':5,'qb':5,'a':0,'b':5}]})
check('flacher Riegel: ⊥-Last = senkrechte Last', max(np.abs(np.array(a1['r']['M'][m])-np.array(a2['r']['M'][m])).max() for m in ['L','R','Rr'])<1e-9)
a3=app({**base,'q':[{'member':'rafter','qa':5,'qb':5,'a':0,'b':5,'rdir':'h'}]})
check('flacher Riegel: waagerechte Last je m Höhe = 0', max(np.abs(np.array(a3['r']['M'][m])).max() for m in ['L','R','Rr'])<1e-9)
print('FAILS:', fails)
