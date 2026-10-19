# calc v0.9: Durchlaufträger mit Einspannung, Kragarmen, Gelenken, EI je Feld und Einzelmomenten —
# gegen eine unabhängige Balken-FEM (eigene Freiheitsgrade für Gelenke) und Handformeln.
import json, subprocess, numpy as np, sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
HTML=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else os.path.join(HERE,'..','calc.html')
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:58}', str(info)[:150])
def app(cfg):
    o=subprocess.run(['node',os.path.join(HERE,'harness_beam.js'),HTML,json.dumps(cfg)],capture_output=True,text=True)
    return json.loads(o.stdout)

def fem(segs, supports, hinges, points, dists, EI0, nseg=600):
    """segs: [(x0,L,k)], supports [(x,type)], hinges [x], points [(x,Fy↓,Me↻)], dists [(a,b,qa,qb)]"""
    Lt=segs[-1][0]+segs[-1][1]
    st=set(np.linspace(0,Lt,nseg+1).round(10))
    for x,_ in supports: st.add(round(x,10))
    for x in hinges: st.add(round(x,10))
    for p in points: st.add(round(p[0],10))
    for a,b,_,_ in dists: st.add(round(a,10)); st.add(round(b,10))
    for x0,L,k in segs: st.add(round(x0,10)); st.add(round(x0+L,10))
    xs=sorted(st); n=len(xs)
    # Freiheitsgrade: je Knoten v, φ; an Gelenken zweites φ (rechts)
    dof=[]; nd=0
    for x in xs:
        v=nd; nd+=1; phL=nd; nd+=1
        phR=phL
        if any(abs(x-h)<1e-9 for h in hinges): phR=nd; nd+=1
        dof.append((v,phL,phR))
    K=np.zeros((nd,nd)); F=np.zeros(nd); els=[]
    def EIat(x):
        for x0,L,k in segs:
            if x0-1e-9<=x<=x0+L+1e-9: return EI0*k
    def q(x):
        return sum(qa+(qb-qa)*(x-a)/(b-a) for a,b,qa,qb in dists if b-a>1e-12 and a-1e-12<=x<=b+1e-12)
    gp,gw=np.polynomial.legendre.leggauss(6)
    for i in range(n-1):
        l=xs[i+1]-xs[i]; EI=EIat((xs[i]+xs[i+1])/2)
        k=EI/l**3*np.array([[12,6*l,-12,6*l],[6*l,4*l*l,-6*l,2*l*l],[-12,-6*l,12,-6*l],[6*l,2*l*l,-6*l,4*l*l]])
        fe=np.zeros(4)
        for g,w in zip(gp,gw):
            t=(g+1)/2; py=-q(xs[i]+t*l)*w*l/2
            fe+=py*np.array([1-3*t*t+2*t**3,l*(t-2*t*t+t**3),3*t*t-2*t**3,l*(-t*t+t**3)])
        d=[dof[i][0],dof[i][2],dof[i+1][0],dof[i+1][1]]
        K[np.ix_(d,d)]+=k; F[d]+=fe; els.append((k,fe,d))
    idx={round(x,10):i for i,x in enumerate(xs)}
    for x,Fy,Me in points:
        i=idx[round(x,10)]; F[dof[i][0]]-=Fy; F[dof[i][1]]-=Me
    fixed=[]
    for x,t in supports:
        i=idx[round(x,10)]; fixed.append(dof[i][0])
        if t=='fixed': fixed+= [dof[i][1], dof[i][2]]
    free=[j for j in range(nd) if j not in fixed]
    u=np.zeros(nd); u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free]); R=K@u-F
    X=[];M=[];Q=[];W=[]
    for i,(k,fe,d) in enumerate(els):          # beide Stabenden → Sprünge bleiben scharf
        f=k@u[d]-fe
        X+= [xs[i], xs[i+1]]; M+=[-f[1], f[3]]; Q+=[f[0], -f[2]]; W+=[u[d[0]], u[d[2]]]
    reac=[R[dof[idx[round(x,10)]][0]] for x,_ in supports]
    return np.array(X),np.array(M),np.array(Q),np.array(W)*1000,reac

def ref(cfg):
    c=cfg.get('cont',{}); oL=c.get('ovL',{}).get('L',0); oR=c.get('ovR',{}).get('L',0)
    segs=[]; x=0
    if oL: segs.append((0,oL,1)); x=oL
    starts=[]
    for sp in cfg['spans']: starts.append(x); segs.append((x,sp['L'],sp.get('k',1))); x+=sp['L']
    xsup=starts+[x]
    if oR: segs.append((x,oR,1))
    n=len(cfg['spans'])
    sup=[(xx, c.get('supL','pin') if i==0 else c.get('supR','roller') if i==n else 'roller') for i,xx in enumerate(xsup)]
    hin=[starts[g['span']]+g['a'] for g in c.get('hinges',[])]
    pts=[]; ds=[]
    allsegs=([('L',c['ovL'],0)] if oL else [])+[(k,sp,starts[k]) for k,sp in enumerate(cfg['spans'])]+([('R',c['ovR'],x)] if oR else [])
    for _,sp,x0 in allsegs:
        pts+=[(x0+p['a'],p['F'],0) for p in sp.get('points',[])]
        pts+=[(x0+m['a'],0,m['M']) for m in sp.get('moms',[])]
        ds+=[(x0+d['a'],x0+d['b'],d['qa'],d['qb']) for d in sp.get('dists',[])]
    return fem(segs,sup,hin,pts,ds,21000), segs[-1][0]+segs[-1][1], sup

def compare(name, cfg, extra=None):
    a=app(cfg)
    if a['err'] or not a['out']: check(name, False, a['err'] or a['msgs']); return None
    (X,M,Q,W,reac),L,sup=ref(cfg)
    o=a['out']; ts=np.array(o['ts']); x=ts*L
    gM=-np.array(o['M']); gW=np.array(o['w'])
    # Momente nur abseits von Sprungstellen (Einzelmomente) vergleichen
    jumps=[xx for xx,_,me in [] ]
    mask=np.array([True]*len(x))
    dM=np.abs(gM-np.interp(x,X,M)); dW=np.abs(gW-np.interp(x,X,W))
    # an Stellen mit Doppelwerten (Sprung) nur den passenden Grenzwert akzeptieren
    for i in range(len(x)):
        if (i>0 and abs(x[i]-x[i-1])<1e-9) or (i<len(x)-1 and abs(x[i+1]-x[i])<1e-9):
            dM[i]=min(abs(gM[i]-np.interp(x[i]-1e-4,X,M)),abs(gM[i]-np.interp(x[i]+1e-4,X,M)), abs(gM[i]-M[np.argmin(abs(X-x[i]))]))
    # Auflagerkräfte aus der Tabelle
    V=[float(r.split('</td><td>')[1]) for r in a['table'].split('<tr>')[1:]]
    dR=max(abs(v-r) for v,r in zip(V,reac))
    ok=dM.max()<0.02 and dW.max()<0.02 and dR<0.02
    check(name, ok, f'ΔM={dM.max():.4f} Δw={dW.max():.4f}mm ΔV={dR:.4f}  (max|M| {abs(M).max():.2f}, V {", ".join(f"{r:.2f}" for r in reac)})')
    return a, (X,M,Q,W,reac)

q10=lambda L:{'qa':10,'qb':10,'a':0,'b':L}
# 1) Einspannung links, Loslager sonst: 2 Felder je 5 m, q = 10 → Handwert
r=compare('Einspannung links, 2×5 m, q = 10', dict(sys='cont',spans=[{'L':5,'dists':[q10(5)]},{'L':5,'dists':[q10(5)]}],cont={'supL':'fixed'}))
# 2) beidseitig eingespannt, ein Innenlager: entspricht zwei beidseitig eingespannten Feldern → M_Stütze = −qL²/12
r=compare('beidseitig eingespannt, 2×6 m, q = 10', dict(sys='cont',spans=[{'L':6,'dists':[q10(6)]},{'L':6,'dists':[q10(6)]}],cont={'supL':'fixed','supR':'fixed'}))
if r:
    X,M,_,_,_=r[1]; check('Handwert: Einspannmoment = −q·l²/12 = −30 kNm', abs(M[0]+30)<0.01 and abs(np.interp(6,X,M)+30)<0.01, f'{M[0]:.3f}')
# 3) Kragarme links und rechts mit Einzellasten
compare('Kragarme 1,5 m / 2 m + Einzellasten', dict(sys='cont',spans=[{'L':5,'dists':[q10(5)]},{'L':4,'dists':[q10(4)]}],
    cont={'ovL':{'L':1.5,'points':[{'F':15,'a':0}]},'ovR':{'L':2,'dists':[{'qa':10,'qb':10,'a':0,'b':2}],'points':[{'F':8,'a':2}]}}))
# 4) Gerberträger: 3 Felder, zwei Gelenke im Mittelfeld → statisch bestimmt
r=compare('Gerberträger 3 Felder, 2 Gelenke', dict(sys='cont',spans=[{'L':6,'dists':[q10(6)]},{'L':8,'dists':[q10(8)]},{'L':6,'dists':[q10(6)]}],
    cont={'hinges':[{'span':1,'a':1.5},{'span':1,'a':6.5}]}))
if r:
    X,M,_,_,_=r[1]
    # Einhängeträger 5 m: Gelenkkraft 25 kN; Stützmoment B = −25·1,5 − 10·1,5²/2 = −48,75 kNm
    check('Handwert Gerberträger: M_B = −48,75 kNm', abs(np.interp(6,X,M)+48.75)<0.01, f'{np.interp(6,X,M):.3f}')
    a=r[0]; gM=-np.array(a['out']['M']); ts=np.array(a['out']['ts'])*20
    check('Moment im Gelenk = 0', abs(np.interp(7.5,ts,gM))<0.02 and abs(np.interp(12.5,ts,gM))<0.02)
# 5) EI je Feld: Mittelfeld doppelt so steif
compare('EI je Feld (1 / 2 / 1)', dict(sys='cont',spans=[{'L':5,'dists':[q10(5)]},{'L':7,'k':2,'dists':[q10(7)]},{'L':5,'dists':[q10(5)]}]))
# 6) Einzelmomente
compare('Einzelmomente im Feld und auf dem Kragarm', dict(sys='cont',spans=[{'L':4,'moms':[{'M':20,'a':1.5}]},{'L':5,'dists':[q10(5)]}],
    cont={'ovR':{'L':1.5,'moms':[{'M':-12,'a':1.5}]}}))
# 7) Mechanismus: Gelenk im Feld neben einem Kragarm-Endfeld ohne weitere Stütze → Hinweis
a=app(dict(sys='cont',spans=[{'L':5,'dists':[q10(5)]},{'L':5,'dists':[q10(5)]}],cont={'hinges':[{'span':0,'a':2},{'span':1,'a':2}]}))
check('Zwei Gelenke im 2-Feld-Träger → Mechanismus-Hinweis', a['out'] is None and ('verschieblich' in a['msgs'] or 'mechanism' in a['msgs']), a['msgs'][:80])
# 8) alte Eingabe ohne neue Felder (Kompatibilität)
compare('Standard-DLT unverändert (2×5 m q)', dict(sys='cont',spans=[{'L':5,'dists':[q10(5)]},{'L':5,'dists':[q10(5)]}]))
print('FAILS:', fails)
