# Zufallstest Einfeldträger, Kragarm, Durchlaufträger gegen unabhängige 1D-FEM
import json, random, sys, os, numpy as np, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from beamfem import solve
HTML=os.path.join(HERE,'..','calc.html')
def app(cfg):
    return json.loads(subprocess.run(['node',os.path.join(HERE,'harness_beam.js'),HTML,json.dumps(cfg)],capture_output=True,text=True).stdout)
rnd=random.Random(int(sys.argv[1]) if len(sys.argv)>1 else 1); N=int(sys.argv[2]) if len(sys.argv)>2 else 60
r1=lambda a,b: round(rnd.uniform(a,b),2); DEG=np.pi/180
ok=0; fails=[]
for k in range(N):
    sysn=rnd.choice(['beam','cant','cont'])
    if sysn=='cont':
        spans=[]
        for _ in range(rnd.randint(2,4)):
            L=r1(2,8); sp={'L':L,'points':[],'dists':[]}
            for _ in range(rnd.randint(0,2)): sp['points'].append({'F':r1(-10,30),'a':r1(0.1*L,0.9*L)})
            for _ in range(rnd.randint(0,2)):
                a=r1(0,0.5*L); sp['dists'].append({'qa':r1(-3,15),'qb':r1(-3,15),'a':a,'b':r1(a+0.2,L)})
            spans.append(sp)
        cfg={'sys':'cont','spans':spans}
        xs=np.cumsum([0]+[s['L'] for s in spans]); Lt=xs[-1]
        sup=[(xs[0],'pin')]+[(x,'roller') for x in xs[1:]]
        pts=[(xs[i]+p['a'],0,p['F'],0) for i,s in enumerate(spans) for p in s['points']]
        ds=[(xs[i]+d['a'],xs[i]+d['b'],d['qa'],d['qb']) for i,s in enumerate(spans) for d in s['dists']]
        sM,sQ=-1,-1
    else:
        Lt=r1(2,8); P=[]; D=[]; H=[]
        for _ in range(rnd.randint(0,3)): P.append({'F':r1(-10,30),'a':r1(0.05*Lt,0.95*Lt),'alpha':rnd.choice([0,0,r1(-45,45)])})
        for _ in range(rnd.randint(0,2)):
            a=r1(0,0.6*Lt); D.append({'qa':r1(-3,15),'qb':r1(-3,15),'a':a,'b':r1(a+0.2,Lt)})
        for _ in range(rnd.randint(0,1)): H.append({'H':r1(-10,10),'Me':r1(-15,15),'a':r1(0.05*Lt,0.95*Lt)})
        cfg={'sys':sysn,'L':Lt,'points':P,'dists':D,'horiz':H}
        sup=[(0,'pin'),(Lt,'roller')] if sysn=='beam' else [(0,'fixed')]
        pts=[(p['a'],p['F']*np.sin(p['alpha']*DEG),p['F']*np.cos(p['alpha']*DEG),0) for p in P]+[(h['a'],h['H'],0,h['Me']) for h in H]
        ds=[(d['a'],d['b'],d['qa'],d['qb']) for d in D]
        sM,sQ=(-1,-1) if sysn=='beam' else (1,-1)
    a=app(cfg); f=solve(Lt,sup,pts,ds,2100*10,nseg=400)
    if a['err'] or not a['out']: fails.append((k,sysn,'App-Fehler '+str(a['err']))); continue
    o=a['out']; t=np.array(o['ts']); x=t*Lt; worst=0
    for key,arr,sg,ref in [('M',o['M'],sM,f['M']),('Q',o['Q'],sQ,f['Q']),('N',o['N'],1,f['N']),('w',o['w'],1,f['v']*1000)]:
        got=np.array(arr,float)*sg; r=np.interp(x,f['x'],ref); d=np.abs(got-r)
        for i in range(len(x)):
            dup=(i>0 and abs(x[i]-x[i-1])<1e-9) or (i<len(x)-1 and abs(x[i+1]-x[i])<1e-9)
            j=np.searchsorted(f['x'],x[i]); near=any(abs(f['x'][jj]-x[i])<Lt/300 and abs(ref[jj]-ref[jj-1])>0.05 for jj in range(max(j-2,1),min(j+2,len(f['x']))))
            if dup or near: d[i]=0
        worst=max(worst, d.max()/max(1,np.abs(ref).max()))
    if worst<1e-2: ok+=1
    else: fails.append((k,sysn,f'rel {worst:.4f}',json.dumps(cfg)[:250]))
print({'ok':ok,'fail':len(fails)}); [print(f) for f in fails[:6]]
