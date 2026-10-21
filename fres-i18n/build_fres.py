# Baut TTX.fr/TTX.es (size + ref) und I18N.fr/es (size) aus pool.json, idmap.json und o*.json
# Aufruf: python3 build_fres.py <Ordner mit size.html und ref.html>
import json,glob,re,sys,os
D=os.path.dirname(os.path.abspath(__file__))+'/'; B=sys.argv[1].rstrip('/')+'/'
pool=json.load(open(D+'pool.json'))['pool']; idm=json.load(open(D+'idmap.json'))
O={}
for f in sorted(glob.glob(D+'o[0-9][0-9].json')): O.update(json.load(open(f)))
if os.path.exists(D+'fix.json'): O.update(json.load(open(D+'fix.json')))   # Nachbesserungen {id:{fr,es}}
TT={'fr':{},'es':{}}; UI={'fr':{},'es':{}}
for cid,pid in idm.items():
    for L in ('fr','es'):
        v=O[cid][L]
        if pid.startswith('I:'): UI[L][pid[2:]]=v
        else: TT[L][pid[2:]]=v
if os.path.exists(D+'extra_tri.json'):   # Nachträge {de:{en,fr,es}}
    for k,v in json.load(open(D+'extra_tri.json')).items():
        for L in ('fr','es'):
            if v.get(L) is not None: TT[L][k]=v[L]
if os.path.exists(D+'same_fix.json'):    # Einträge mit DE = EN, die in FR/ES doch übersetzt werden {pool-id:{fr,es}}
    for pid,v in json.load(open(D+'same_fix.json')).items():
        for L in ('fr','es'):
            if pid.startswith('I:'): UI[L][pid[2:]]=v[L]
            else: TT[L][pid[2:]]=v[L]
if os.path.exists(D+'extra_ui.json'):    # neue Oberflächen-Schlüssel in size (I18N) {key:{fr,es}}
    for k,v in json.load(open(D+'extra_ui.json')).items():
        for L in ('fr','es'): UI[L][k]=v[L]
for pid in json.load(open(D+'pool.json'))['same']:   # übrige DE = EN: unverändert übernehmen (UI-Schlüssel müssen vollständig sein)
    if pid.startswith('I:'):
        for L in ('fr','es'): UI[L].setdefault(pid[2:], pool[pid]['de'])
def ttx_en(s):
    a=s.index('const TTX = { en: ')+18; return json.JSONDecoder().raw_decode(s[a:])[0]
def block(keys):
    return {L:{k:TT[L][k] for k in keys if k in TT[L]} for L in ('fr','es')}
MK0,MK1='/*FRES*/','/*/FRES*/'
def put(s, anchor, code):
    if MK0 in s:
        a=s.index(MK0); b=s.index(MK1,a)+len(MK1); return s[:a]+code+s[b:]
    i=s.index(anchor); i=s.index('\n',i)+1; return s[:i]+code+'\n'+s[i:]
J=lambda o: json.dumps(o,ensure_ascii=False,separators=(',',':'))
NOTICE={'size':{'fr':"<b>statiq·size</b> en français : saisies, étapes de calcul et rapports. Les vérifications suivent l’Annexe nationale allemande (DIN EN … /NA) ; les renvois aux normes allemandes et à l’AN sont conservés.",
                'es':"<b>statiq·size</b> en español: datos, desarrollo del cálculo e informes. Las comprobaciones siguen el Anejo Nacional alemán (DIN EN … /NA); se mantienen las referencias a las normas alemanas y al AN."},
        'ref':{'en':"<b>statiq·ref</b> in English. Values follow the German National Annexes where applicable; references to German standards and the NA are kept.",
               'fr':"<b>statiq·ref</b> en français. Les valeurs suivent les Annexes nationales allemandes lorsqu’elles s’appliquent ; les renvois aux normes allemandes et à l’AN sont conservés.",
               'es':"<b>statiq·ref</b> en español. Los valores siguen los Anejos Nacionales alemanes cuando corresponde; se mantienen las referencias a las normas alemanas y al AN."}}
# ── size
p=B+'size.html'; s=open(p).read()
bl=block(ttx_en(s).keys())
TTR={'fr':"[[/^Baustoff Schicht (\\d+)$/,'Matériau, couche $1'],[/ der Schicht (\\d+)/,' de la couche $1'],[/Schicht (\\d+)/,'couche $1'],[/^Dicke /,'Épaisseur '],[/ \\(wegen γ′\\)/,' (en raison de γ′)']]",
     'es':"[[/^Baustoff Schicht (\\d+)$/,'Material, capa $1'],[/ der Schicht (\\d+)/,' de la capa $1'],[/Schicht (\\d+)/,'capa $1'],[/^Dicke /,'Espesor '],[/ \\(wegen γ′\\)/,' (debido a γ′)']]"}
code=f"{MK0}Object.assign(TTX,{{fr:{J(bl['fr'])},es:{J(bl['es'])}}}); TTR.fr={TTR['fr']}; TTR.es={TTR['es']};{MK1}"
s=put(s,'const TTR = { en:',code)
for L,nxt in (('fr','\n },\n "es": {'),('es','\n }\n};\nconst tx')):
    a=s.index(f'\n "{L}": {{\n')+len(f'\n "{L}": {{\n'); b=s.index(nxt,a)
    d={'langNotice':NOTICE['size'][L]}; d.update(UI[L])
    s=s[:a]+',\n'.join(f'  {json.dumps(k,ensure_ascii=False)}: {json.dumps(v,ensure_ascii=False)}' for k,v in d.items())+s[b:]
open(p,'w').write(s); print('size', len(bl['fr']), len(bl['es']), 'UI', len(UI['fr']))
# ── ref
p=B+'ref.html'; s=open(p).read()
bl=block(ttx_en(s).keys())
code=f"{MK0}Object.assign(TTX,{{fr:{J(bl['fr'])},es:{J(bl['es'])}}});{MK1}"
s=put(s,'const _L = (s, ...v) =>',code) if MK0 in s else None or s
if MK0 not in s:
    i=s.index('const REF_INL'); s=s[:i]+code+'\n'+s[i:]
open(p,'w').write(s); print('ref', len(bl['fr']), len(bl['es']))
