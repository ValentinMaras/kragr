import json, subprocess, numpy as np, re, itertools, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fem import solve
import os
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 and sys.argv[1].endswith('.html') else os.path.join(HERE,'..','calc.html')
def app(cfg):
    o=subprocess.run(['node',os.path.join(HERE,'harness.js'),HTML,json.dumps(cfg)],capture_output=True,text=True)
    return json.loads(o.stdout)
def fem_at(res,m,NP):
    pts=np.array(res[m]['pts']); M=np.array(res[m]['M'])
    s=np.hypot(pts[:,0]-pts[0,0],pts[:,1]-pts[0,1]); s/=s[-1]
    t=np.linspace(0,1,NP+1)
    # average duplicates
    return np.interp(t,s,M)
Q10={'member':'rafter','qa':10,'qb':10,'a':0,'b':5}
QTR={'member':'rafter','qa':4,'qb':12,'a':1,'b':4}
FL={'member':'left','F':5,'z':2}
FR={'member':'right','F':5,'z':2}
FLtop={'member':'left','F':5,'z':4}
loads={'q':[[Q10],[]],'qTrapez':[[QTR],[]],'F_links':[[],[FL]],'F_rechts':[[],[FR]],'F_links_Kopf':[[],[FLtop]],
       'q+F+F':[[Q10],[FL,FR]]}
supports=[('fixed','fixed'),('fixed','pin'),('pin','fixed'),('pin','pin'),('fixed','roller'),('roller','fixed'),('pin','roller'),('roller','pin')]
extra=[('pin','pin',[{'member':'rafter','pos':2.5}],'3-Gelenk')]
rows=[]
def check(A,B,hinges,lname,lq,lf,hA=4,hB=4,tag=''):
    cfg=dict(A=A,B=B,b=5,hA=hA,hB=hB,q=lq,F=lf,hinges=hinges)
    a=app(cfg)
    try: f=solve(cfg)
    except Exception as e: rows.append((A,B,tag,lname,'FEM-Fehler '+str(e),None)); return
    if a['err'] or not a['r']:
        rows.append((A,B,tag,lname,'APP-FEHLER: '+str(a['err']),None)); return
    NP=a['r']['NP']; worst=0; where=''
    for m in ['L','R','Rr']:
        ref=fem_at(f,m,NP); got=np.array(a['r']['M'][m])
        d=np.abs(ref-got); i=int(d.argmax())
        if d[i]>worst: worst=d[i]; where=f'{m}[{i}] app={got[i]:.2f} ref={ref[i]:.2f}'
    key=lambda m,i: (np.array(a['r']['M'][m])[i], fem_at(f,m,NP)[i])
    summ={'FussA':key('L',0),'KopfA':key('L',NP),'Mitte':key('R',NP//2),'KopfB':key('Rr',0),'FussB':key('Rr',NP)}
    rows.append((A,B,tag,lname,f'max|ΔM|={worst:.2f}  @ {where}',summ))
if __name__=='__main__':
    for (A,B) in supports:
        for ln,(lq,lf) in loads.items(): check(A,B,[],ln,lq,lf)
    for A,B,h,t in extra:
        for ln,(lq,lf) in loads.items(): check(A,B,h,ln,lq,lf,tag=t)
    for ln,(lq,lf) in {'q':loads['q'],'q+F+F':loads['q+F+F']}.items():
        for (A,B) in [('fixed','fixed'),('pin','pin'),('fixed','pin')]:
            check(A,B,[],ln,lq,lf,hA=4,hB=3,tag='hA≠hB')
    for r in rows:
        ok = r[4].startswith('max') and float(r[4].split('=')[1].split()[0])<0.1
        print(('OK  ' if ok else 'FAIL'),f'{r[0]:6}/{r[1]:6} {r[2]:9} {r[3]:13} {r[4]}')
    json.dump([[*r[:5],{k:list(map(float,v)) for k,v in (r[5] or {}).items()}] for r in rows],open('results.json','w'),indent=1)
    