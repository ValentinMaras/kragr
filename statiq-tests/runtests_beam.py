# Einfeldträger, Kragarm, Durchlaufträger gegen unabhängige FEM (beamfem.py)
import json, subprocess, numpy as np, sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); from beamfem import solve
HTML=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else os.path.join(HERE,'..','calc.html')
def app(cfg):
    o=subprocess.run(['node',os.path.join(HERE,'harness_beam.js'),HTML,json.dumps(cfg)],capture_output=True,text=True)
    return json.loads(o.stdout)
DEG=np.pi/180
def ref(cfg):
    EI=210*cfg.get('Iy',10)*10
    if cfg['sys']=='cont':
        xs=np.cumsum([0]+[s['L'] for s in cfg['spans']]); L=xs[-1]
        sup=[(xs[0],'pin')]+[(x,'roller') for x in xs[1:]]
        pts=[(xs[k]+p['a'],0,p['F'],0) for k,s in enumerate(cfg['spans']) for p in s.get('points',[])]
        ds=[(xs[k]+d['a'],xs[k]+min(d['b'],s['L']),d['qa'],d['qb']) for k,s in enumerate(cfg['spans']) for d in s.get('dists',[])]
    else:
        L=cfg['L']
        sup=[(0,'pin'),(L,'roller')] if cfg['sys']=='beam' else [(0,'fixed')]
        pts=[(p['a'],p['F']*np.sin(p.get('alpha',0)*DEG),p['F']*np.cos(p.get('alpha',0)*DEG),0) for p in cfg.get('points',[])]
        pts+=[(h['a'],h.get('H',0),0,h.get('Me',0)) for h in cfg.get('horiz',[])]
        ds=[(d['a'],d['b'],d['qa'],d['qb']) for d in cfg.get('dists',[])]
    return solve(L,sup,pts,ds,EI),L
def jump_near(x,v,xi,tol):
    i=np.searchsorted(x,xi)
    return any(abs(x[j]-xi)<tol and abs(v[j]-v[j-1])>0.05 for j in range(max(i-2,1),min(i+2,len(x))))
cases=[
 ('EFT q',dict(sys='beam',L=5,dists=[{'qa':10,'qb':10,'a':0,'b':5}])),
 ('EFT F x=1.73',dict(sys='beam',L=5,points=[{'F':20,'a':1.73,'alpha':0}])),
 ('EFT F schräg 30° + Trapez',dict(sys='beam',L=6,points=[{'F':12,'a':2.2,'alpha':30}],dists=[{'qa':2,'qb':8,'a':1,'b':5}])),
 ('EFT Me + H',dict(sys='beam',L=5,horiz=[{'H':5,'Me':10,'a':3.1}])),
 ('Kragarm q+F',dict(sys='cant',L=3,points=[{'F':10,'a':1.5,'alpha':0}],dists=[{'qa':5,'qb':5,'a':0,'b':3}])),
 ('Kragarm Me+F schräg',dict(sys='cant',L=3,points=[{'F':8,'a':2.37,'alpha':-20}],horiz=[{'H':0,'Me':6,'a':1.1}])),
 ('DLT 2×5 q',dict(sys='cont',spans=[{'L':5,'dists':[{'qa':10,'qb':10,'a':0,'b':5}]},{'L':5,'dists':[{'qa':10,'qb':10,'a':0,'b':5}]}])),
 ('DLT 4+6 q',dict(sys='cont',spans=[{'L':4,'dists':[{'qa':10,'qb':10,'a':0,'b':4}]},{'L':6,'dists':[{'qa':10,'qb':10,'a':0,'b':6}]}])),
 ('DLT 3 Felder F+Trapez',dict(sys='cont',spans=[{'L':4,'points':[{'F':20,'a':1.3}]},{'L':6,'dists':[{'qa':4,'qb':12,'a':1,'b':5}]},{'L':3.5,'points':[{'F':8,'a':2.9}]}])),
]
sign={'beam':(-1,-1),'cant':(1,-1),'cont':(-1,-1)}   # (M, Q) Vorzeichen App-Arrays
fails=0
for name,cfg in cases:
    a=app(cfg); f,L=ref(cfg)
    if a['err'] or not a['out']: print('FAIL',name,a['err']); fails+=1; continue
    o=a['out']; n=len(o['M'])-1
    ts=np.array(o['ts']) if o['ts'] else np.arange(n+1)/n    # so, wie der Renderer die Punkte setzt
    x=ts*L; sM,sQ=sign[cfg['sys']]
    res={}
    for key,arr,sg in [('M',o['M'],sM),('Q',o['Q'],sQ),('N',o['N'],1),('w',o['w'],1)]:
        got=np.array(arr,float)*sg
        rv={'M':f['M'],'Q':f['Q'],'N':f['N'],'w':f['v']*1000}[key]
        r=np.interp(x,f['x'],rv)
        d=np.abs(got-r)
        if o['ts']:
            # An Sprungstellen stehen beide Seitenwerte am selben x: gegen den
            # linken bzw. rechten Grenzwert der FEM prüfen. Schließpunkte (Q=0 am
            # Endauflager) sind Zeichenhilfen und werden übersprungen.
            eps=1e-7*L
            for i in range(len(x)):
                dup_prev = i>0 and abs(x[i]-x[i-1])<1e-9
                dup_next = i<len(x)-1 and abs(x[i+1]-x[i])<1e-9
                if not(dup_prev or dup_next): continue
                closing = key=='Q' and got[i]==0 and (i<=1 or i>=len(x)-2)
                if closing: d[i]=0; continue
                side = -1 if dup_next else 1       # erster Wert = links, zweiter = rechts
                xi = x[i]+side*eps
                j = np.searchsorted(f['x'],x[i])
                # FEM-Grenzwert: Wert des Elements links bzw. rechts vom Knoten
                if side<0: rr = np.interp(x[i]-L/400*0.5, f['x'], rv) if key!='M' else np.interp(x[i],f['x'],rv)
                else:      rr = np.interp(x[i]+L/400*0.5, f['x'], rv) if key!='M' else np.interp(x[i],f['x'],rv)
                d[i]=min(abs(got[i]-rr), abs(got[i]-np.interp(xi,f['x'],rv)))
        if key in 'QN': d=np.array([0 if jump_near(f['x'],rv,xi,L/350) else di for xi,di in zip(x,d)])
        if key=='M': d=np.array([0 if (o['ts'] and jump_near(f['x'],rv,xi,1e-6)) else di for xi,di in zip(x,d)])
        res[key]=d.max()
    mx=abs(max(np.abs(f['M'])))
    ok=res['M']<0.01 and res['Q']<0.01 and res['N']<0.01 and res['w']<0.01
    fails+=not ok
    print('OK  ' if ok else 'FAIL',f'{name:28}','ΔM=%.3f ΔQ=%.3f ΔN=%.3f Δw=%.3fmm   (max|M| FEM %.2f)'%(res['M'],res['Q'],res['N'],res['w'],mx))
print('FAILS:',fails)
# Anzeige: Auflagerkräfte und max-Werte gegen FEM / Handrechnung
import re
def num(t): return float(t.split()[0])
chk=[]
a=app(cases[1][1]); f,_=ref(cases[1][1])      # EFT F=20 bei x=1.73
chk.append(('EFT A/B/Mmax', abs(num(a['txt']['b-res-A'])-f['reac'][0][1])+abs(num(a['txt']['b-res-B'])-f['reac'][1][1])+abs(num(a['txt']['b-res-Mmax'])-20*1.73*3.27/5)))
a=app(cases[4][1]); f,_=ref(cases[4][1])      # Kragarm: V=25 ↑, Lagermoment M_A = +37.5 ↺ (= FEM-Reaktion)
chk.append(('Kragarm V/M_A (Lagerkraft ↺)', abs(num(a['txt']['c-res-V'])-25)+abs(num(a['txt']['c-res-M'])-37.5)+abs(num(a['txt']['c-res-M'])-f['reac'][0][2])))
a=app(cases[3][1]); f,_=ref(cases[3][1])      # EFT H=5 → bei x=3.1: Festlager hält mit H_A = −5 (←), wie FEM
chk.append(('EFT H_A als Lagerkraft (→ +)', abs(num(a['txt']['b-res-HA'])+5)+abs(num(a['txt']['b-res-HA'])-f['reac'][0][0])))
a=app(cases[5][1]); f,_=ref(cases[5][1])      # Kragarm mit schräger Last: H_A, V_A, M_A gegen FEM
chk.append(('Kragarm H/V/M gegen FEM-Reaktionen', sum(abs(num(a['txt'][k])-f['reac'][0][j]) for k,j in [('c-res-HA',0),('c-res-V',1),('c-res-M',2)])))
a=app(cases[6][1])                            # DLT 2×5 q=10: 18.75 / 62.5 / 18.75, M_B = −31.25
rows=[re.findall(r'<td>(.*?)</td>',r) for r in re.findall(r'<tr>(.*?)</tr>',a['table'])]
chk.append(('DLT 2×5 Tabelle', abs(float(rows[0][1])-18.75)+abs(float(rows[1][1])-62.5)+abs(float(rows[2][1])-18.75)+abs(num(rows[1][2])+31.25)))
cfg=cases[8][1]; a=app(cfg); f,L=ref(cfg)     # DLT 3 Felder: Stützmomente gegen FEM
rows=[re.findall(r'<td>(.*?)</td>',r) for r in re.findall(r'<tr>(.*?)</tr>',a['table'])]
xs=np.cumsum([0]+[s['L'] for s in cfg['spans']])
dM=max(abs(num(rows[i][2])-np.interp(xs[i],f['x'],f['M'])) for i in (1,2))
dV=max(abs(float(rows[i][1])-f['reac'][i][1]) for i in range(4))
chk.append(('DLT 3 Felder Stützmomente+V', dM+dV))
for n,d in chk:
    ok=d<0.02; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{n:28} Abweichung {d:.4f}')
print('FAILS gesamt:',fails)
