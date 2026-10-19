# Erweiterte Tests: Q, N, Reaktionen, Einzellast Riegel, Stützengelenk, Kopfhalterung, EI-Verhältnis, Superposition, Mechanismus
import json, numpy as np, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runtests import app, fem_at
from fem import solve
def samp(res,m,key,NP):
    pts=np.array(res[m]['pts']); v=np.array(res[m][key])
    s=np.hypot(pts[:,0]-pts[0,0],pts[:,1]-pts[0,1]); s/=s[-1]
    t=np.linspace(0,1,NP+1); return np.interp(t,s,v)
def table(a):
    rows=re.findall(r'<tr>(.*?)</tr>',a['table']); out={}
    for r in rows:
        c=re.findall(r'<td>(.*?)</td>',r); out[c[0]]=[float(x) if x not in('—',) else None for x in c[1:]]
    return out
Q10={'member':'rafter','qa':10,'qb':10,'a':0,'b':5}
cases=[
 ('fix/fix q',dict(A='fixed',B='fixed',q=[Q10],F=[])),
 ('fix/pin q+F+F',dict(A='fixed',B='pin',q=[Q10],F=[{'member':'left','F':5,'z':2},{'member':'right','F':5,'z':2}])),
 ('pin/pin F Riegel x=1.5',dict(A='pin',B='pin',q=[],F=[{'member':'rafter','F':20,'z':1.5}])),
 ('fix/fix F+H Riegel',dict(A='fixed',B='fixed',q=[],F=[{'member':'rafter','F':20,'H':8,'z':3.2}])),
 ('fix/fix Gelenk li. Stütze z=1',dict(A='fixed',B='fixed',q=[Q10],F=[{'member':'left','F':5,'z':3}],hinges=[{'member':'left','pos':1}])),
 ('pin/fix Gelenk re. Stütze z=2.5',dict(A='pin',B='fixed',q=[Q10],F=[],hinges=[{'member':'right','pos':2.5}])),
 ('pin/roller + Kopfhalt. rechts',dict(A='pin',B='roller',q=[Q10],F=[{'member':'left','F':5,'z':2}],head='right',headType='roller')),
 ('fix/fix EI Riegel 3x',dict(A='fixed',B='fixed',q=[Q10],F=[{'member':'left','F':5,'z':2}],IR=30)),
 ('fix/fix H axial Stütze',dict(A='fixed',B='fixed',q=[],F=[{'member':'left','F':0,'H':10,'z':2}])),
]
for name,c in cases:
    cfg={**dict(b=5,hA=4,hB=4,hinges=[]),**c}; a=app(cfg); f=solve(cfg)
    if a['err']: print('FAIL',name,a['err']); continue
    NP=a['r']['NP']; worst={}
    for key in 'MQN':
        w=0
        for m in ['L','R','Rr']:
            ref=samp(f,m,key,NP); got=np.array(a['r'][key][m])
            d=np.abs(ref-got)
            if key!='M': # Sprungstellen (Einzellasten) auslassen
                d=np.array([0 if (i>0 and abs(ref[i]-ref[i-1])>0.5) or (i<NP and abs(ref[i+1]-ref[i])>0.5) else x for i,x in enumerate(d)])
            w=max(w,d.max())
        worst[key]=w
    t=table(a); ra,rb=f['reac']['A'],f['reac']['B']
    dr=max(abs(t['A'][0]-ra[0]),abs(t['A'][1]-ra[1]),abs(t['B'][0]-rb[0]),abs(t['B'][1]-rb[1]),
           abs((t['A'][2] or 0)-(ra[2] if c['A']=='fixed' else 0)),abs((t['B'][2] or 0)-(rb[2] if c['B']=='fixed' else 0)))
    ok=all(v<0.02 for v in worst.values()) and dr<0.02
    print('OK  ' if ok else 'FAIL',f'{name:34}','ΔM=%.3f ΔQ=%.3f ΔN=%.3f ΔReak=%.3f'%(worst['M'],worst['Q'],worst['N'],dr))
# Superposition: app(q+F+F) == app(q)+app(F_L)+app(F_R)
for A,B in [('fixed','fixed'),('fixed','pin'),('pin','pin'),('fixed','roller')]:
    base=dict(A=A,B=B,b=5,hA=4,hB=3.5,hinges=[])
    parts=[dict(q=[Q10],F=[]),dict(q=[],F=[{'member':'left','F':5,'z':2}]),dict(q=[],F=[{'member':'rafter','F':12,'z':3}])]
    tot=app({**base,'q':[Q10],'F':parts[1]['F']+parts[2]['F']})['r']
    s=[app({**base,**p})['r'] for p in parts]
    d=max(abs(np.array(tot[k][m])-sum(np.array(x[k][m]) for x in s)).max() for k in 'MQN' for m in ['L','R','Rr'])
    print('OK  ' if d<0.01 else 'FAIL',f'Superposition {A}/{B:8} max Abweichung {d:.4f}')
# Mechanismus muss erkannt werden
for A,B,h in [('roller','roller',[]),('pin','roller',[{'member':'rafter','pos':2.5}])]:
    a=app(dict(A=A,B=B,b=5,hA=4,hB=4,q=[Q10],F=[],hinges=h))
    print('OK  ' if a['err'] and 'mechanism' in a['err'] else 'FAIL',f'Mechanismus {A}/{B} Gelenke={len(h)}:',a['err'])
