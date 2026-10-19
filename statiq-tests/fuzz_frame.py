# Zufallstest Rahmen: zufällige Lager, Gelenke, Lasten, Geometrie → App gegen unabhängige FEM
import json, random, sys, os, numpy as np, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from fem import solve
HTML=os.path.join(HERE,'..','calc.html')
def app(cfg):
    o=subprocess.run(['node',os.path.join(HERE,'harness.js'),HTML,json.dumps(cfg)],capture_output=True,text=True)
    return json.loads(o.stdout)
def interp(res,m,key,t):
    pts=np.array(res[m]['pts']); v=np.array(res[m][key]); s=np.hypot(pts[:,0]-pts[0,0],pts[:,1]-pts[0,1]); s/=s[-1]
    return np.interp(t,s,v), s, v
rnd=random.Random(int(sys.argv[1]) if len(sys.argv)>1 else 1); N=int(sys.argv[2]) if len(sys.argv)>2 else 150
r1=lambda a,b: round(rnd.uniform(a,b),2)
stats={'ok':0,'mech_both':0,'fail':0}; fails=[]
for k in range(N):
    b=r1(3,8); hA=r1(2.5,6); hB=rnd.choice([hA, r1(2.5,6)])
    A=rnd.choice(['fixed','pin','roller']); B=rnd.choice(['fixed','pin','roller'])
    hinges=[]
    for _ in range(rnd.choice([0,0,1,1,2])):
        m=rnd.choice(['rafter','left','right']); L={'rafter':b,'left':hA,'right':hB}[m]
        hinges.append({'member':m,'pos':r1(0.2*L,0.8*L)})
    q=[]; F=[]
    for _ in range(rnd.randint(0,3)):
        m=rnd.choice(['rafter','rafter','left','right']); L={'rafter':b,'left':hA,'right':hB}[m]
        a=r1(0,0.5*L); bb=r1(a+0.3,L)
        d={'member':m,'qa':r1(-5,15),'qb':r1(-5,15),'a':a,'b':bb}
        if m!='rafter': d['dir']=rnd.choice(['h','ax'])
        q.append(d)
    for _ in range(rnd.randint(0,3)):
        m=rnd.choice(['rafter','left','right']); L={'rafter':b,'left':hA,'right':hB}[m]
        F.append({'member':m,'F':r1(-20,20),'H':rnd.choice([0,0,r1(-10,10)]),'z':r1(0.1*L,0.9*L)})
    if not q and not F: q=[{'member':'rafter','qa':10,'qb':10,'a':0,'b':b}]
    head = rnd.choice(['none','none','left','right'])
    cfg=dict(A=A,B=B,b=b,hA=hA,hB=hB,hinges=hinges,q=q,F=F,head=head,headType=rnd.choice(['roller','pin']),IR=rnd.choice([10,20,30]),IS=rnd.choice([10,15]))
    a=app(cfg)
    try: f=solve(cfg, nseg=50); fem_ok=True
    except Exception as e: fem_ok=False
    app_mech = bool(a['err']) and 'mechanism' in a['err']
    if app_mech and not fem_ok: stats['mech_both']+=1; continue
    if app_mech or not fem_ok or a['err']:
        # FEM kann bei Mechanismen numerisch "lösen" (riesige Werte) → prüfen
        if app_mech and fem_ok and max(abs(np.array(f['L']['M'])).max(),abs(np.array(f['R']['M'])).max())>1e5: stats['mech_both']+=1; continue
        stats['fail']+=1; fails.append((k,'App:'+str(a['err'])[:60],'FEM ok' if fem_ok else 'FEM singulär',cfg)); continue
    worst=0
    for m in ['L','R','Rr']:
        fine=a['r']['fine'][m]; t=np.array(fine['t'])
        for key,scale in [('M',1),('Q',1),('N',1),('ux',1000),('uy',1000)]:
            got=np.array(fine[key])*scale; ref,s,v=interp(f,m,key,t); ref=ref*scale
            d=np.abs(got-ref)
            # Sprungstellen (doppelte t) und Nähe zu Sprüngen auslassen
            for i in range(len(t)):
                if (i>0 and abs(t[i]-t[i-1])<1e-9) or (i<len(t)-1 and abs(t[i+1]-t[i])<1e-9): d[i]=0
                j=np.searchsorted(s,t[i])
                if any(abs(s[jj]-t[i])<3e-3 and abs(v[jj]-v[jj-1])*scale>0.05 for jj in range(max(j-2,1),min(j+2,len(s)))): d[i]=0
            rel = d.max()/max(1, np.abs(ref).max())
            worst=max(worst, rel)
    if worst<1e-2: stats['ok']+=1
    else: stats['fail']+=1; fails.append((k,f'rel. Abw. {worst:.4f}','',cfg))
print(stats)
for f_ in fails[:8]: print(f_[0],f_[1],f_[2]); print('   ',json.dumps(f_[3])[:400])
