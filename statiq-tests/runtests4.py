# v0.8.1: Gelenke an Lagern/Ecken, Positionsprüfung, abgeschnittene Streckenlasten, Kragarm M max
import json, subprocess, numpy as np, sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from runtests import app
HTML=os.path.join(HERE,'..','calc.html')
def bapp(cfg):
    o=subprocess.run(['node',os.path.join(HERE,'harness_beam.js'),HTML,json.dumps(cfg)],capture_output=True,text=True)
    return json.loads(o.stdout)
from fem import solve
Q10={'member':'rafter','qa':10,'qb':10,'a':0,'b':5}
base=dict(b=5,hA=4,hB=4,F=[])
fails=0
def check(name, ok, info=''):
    global fails; fails+=not ok; print('OK  ' if ok else 'FAIL', f'{name:52}', info)
def maxdiff(r1, r2):
    return max(abs(np.array(r1[k][m])-np.array(r2[k][m])).max() for k in 'MQN' for m in ['L','R','Rr'])

# 1) Gelenk am Fuß eines Festlagers ist wirkungslos: kein Mechanismus, gleiches Ergebnis wie ohne
a=app({**base,'A':'pin','B':'roller','q':[Q10],'hinges':[{'member':'left','pos':0}]})
b=app({**base,'A':'pin','B':'roller','q':[Q10],'hinges':[]})
check('Festlager + Gelenk am Fuß: rechnet, n=0', a['err'] is None and str(a['indet']).startswith('0'), f"err={a['err']} n={a['indet']}")
check('  … identisch mit System ohne Gelenk', a['r'] is not None and maxdiff(a['r'],b['r'])<1e-6)
# 2) Gelenk am Fuß einer Einspannung wirkt wie ein Festlager
a=app({**base,'A':'fixed','B':'fixed','q':[Q10],'F':[{'member':'left','F':5,'z':2}],'hinges':[{'member':'left','pos':0}]})
b=app({**base,'A':'pin','B':'fixed','q':[Q10],'F':[{'member':'left','F':5,'z':2}],'hinges':[]})
check('Einspannung + Gelenk am Fuß = Festlager, n=2', str(a['indet']).startswith('2') and maxdiff(a['r'],b['r'])<1e-3, f"n={a['indet']}")
# 3) Zwei Gelenke an derselben Ecke (Stütze oben + Riegel links) zählen einmal
a=app({**base,'A':'pin','B':'pin','q':[Q10],'hinges':[{'member':'left','pos':4},{'member':'rafter','pos':0}]})
f=solve({**base,'A':'pin','B':'pin','q':[Q10],'hinges':[{'member':'rafter','pos':0}]})
ok = a['err'] is None and str(a['indet']).startswith('0')
check('Eckgelenk doppelt (Stütze+Riegel): n=0, kein Mechanismus', ok, f"err={a['err']} n={a['indet']}")
# 4) Echter Mechanismus wird weiter erkannt
a=app({**base,'A':'pin','B':'roller','q':[Q10],'hinges':[{'member':'rafter','pos':2.5}]})
check('Mechanismus pin/roller + Riegelgelenk weiter erkannt', bool(a['err']) and 'mechanism' in a['err'])
# 5) Position außerhalb: Hinweis + auf Stabende gesetzt
a=app({**base,'A':'fixed','B':'fixed','q':[],'F':[{'member':'left','F':5,'z':6}]})
b=app({**base,'A':'fixed','B':'fixed','q':[],'F':[{'member':'left','F':5,'z':4}]})
check('Rahmen: P1 bei z=6 > h=4 → Hinweis, gleich wie z=4', any('posClamped P1 6' in w for w in a['warns']) and maxdiff(a['r'],b['r'])<1e-9, str(a['warns']))
# 6) Trapezlast über das Stabende: abgeschnitten, nicht gestaucht (0→10 auf 0…6 m, b=5 → 0→8.333 auf 0…5 m)
a=app({**base,'A':'fixed','B':'fixed','q':[{'member':'rafter','qa':0,'qb':10,'a':0,'b':6}]})
b=app({**base,'A':'fixed','B':'fixed','q':[{'member':'rafter','qa':0,'qb':10*5/6,'a':0,'b':5}]})
check('Rahmen: Trapez über Riegelende wird abgeschnitten', any('rangeClamped' in w for w in a['warns']) and maxdiff(a['r'],b['r'])<1e-6)
a=app({**base,'A':'fixed','B':'fixed','q':[{'member':'rafter','qa':10,'qb':10,'a':5.5,'b':7}]})
check('Rahmen: Streckenlast ganz außerhalb → ignoriert + Hinweis', any('rangeIgnored' in w for w in a['warns']), str(a['warns']))
# 7) Einfeldträger: gleiche Prüfung, Hinweis im Meldungsfeld
a=bapp({'sys':'beam','L':5,'points':[{'F':10,'a':7,'alpha':0}],'dists':[{'qa':0,'qb':12,'a':2,'b':8}]})
b=bapp({'sys':'beam','L':5,'points':[{'F':10,'a':5,'alpha':0}],'dists':[{'qa':0,'qb':6,'a':2,'b':5}]})
same = max(abs(np.array(a['out'][k])-np.array(b['out'][k])).max() for k in ['M','Q','w'])<1e-9
check('EFT: F1 bei 7 m und q1 bis 8 m → Hinweise, abgeschnitten', same and 'F1' in a['msgs'] and 'q1' in a['msgs'] and 'class="msg warn"' in a['msgs'])
a=bapp({'sys':'cont','spans':[{'L':4,'points':[{'F':10,'a':5}]},{'L':6}]})
check('DLT: Einzellast hinter dem Feldende → Hinweis L1·F1', 'L1·F1' in a['msgs'], a['msgs'][:80])
a=bapp({'sys':'beam','L':5,'points':[{'F':10,'a':2.5,'alpha':0}]})
check('EFT ohne Probleme: kein Hinweis', a['msgs']=='')
# 8) Kragarm: M max mit richtigem Vorzeichen
a=bapp({'sys':'cant','L':3,'points':[{'F':-10,'a':3,'alpha':0}]})
check('Kragarm, Last nach oben: M max = +30, Lagermoment M_A = −30 ↺', a['txt']['c-res-Mmax']=='30.00' and a['txt']['c-res-M']=='-30.00', f"Mmax={a['txt']['c-res-Mmax']} MA={a['txt']['c-res-M']}")
a=bapp({'sys':'cant','L':3,'points':[{'F':10,'a':3,'alpha':0}]})
check('Kragarm, Last nach unten: M max = −30', a['txt']['c-res-Mmax']=='-30.00')
# 9) Ungültige Eingabe: Fehlermeldung statt Pop-up
a=bapp({'sys':'beam','L':0})
check('EFT L=0: Fehlermeldung im Feld, kein Pop-up', a['err'] is None and 'class="msg error"' in a['msgs'])
print('FAILS:',fails)
