# python3 check.py NN  — prüft oNN.json gegen cNN.json
import json,re,sys
n=sys.argv[1]; C=json.load(open(f'c{n}.json'))
try: O=json.load(open(f'o{n}.json'))
except Exception as e: print('JSON-FEHLER',e); sys.exit(1)
tags=lambda s: sorted(re.findall(r'</?([a-zA-Z][a-zA-Z0-9]*)',s))
def ph(s):
    return re.findall(r'\{(\d*)\}',s)
err=[]
for c in C:
    i=c['id']; o=O.get(i)
    if not isinstance(o,dict) or not isinstance(o.get('fr'),str) or not isinstance(o.get('es'),str): err.append((i,'fehlt/Format')); continue
    n_de=c['de'].count('{}')
    num_de=sorted(re.findall(r'\{\d+\}',c['de']))
    for L in ('fr','es'):
        v=o[L]; p=ph(v)
        if not v.strip(): err.append((i,L,'leer'))
        if num_de:
            if sorted(re.findall(r'\{\d+\}',v))!=num_de: err.append((i,L,'nummerierte Platzhalter wie im Deutschen übernehmen'))
        elif all(x=='' for x in p):
            if len(p)!=n_de: err.append((i,L,f'Platzhalter {len(p)} statt {n_de}'))
        else:
            if any(x=='' for x in p) or sorted(set(int(x) for x in p))!=list(range(n_de)): err.append((i,L,'Platzhalter {0}… müssen 0..n-1 je einmal abdecken'))
        if tags(v)!=tags(c['de']) and tags(v)!=tags(c['en']): err.append((i,L,'HTML-Tags weichen ab',tags(c['de']),tags(v)))
        if c['de'][:1] in '!§' and v[:1]!=c['de'][:1]: err.append((i,L,'Anfangszeichen ! oder § fehlt'))
        if v==c['de'] and re.search(r'[a-zäöü]{4} [a-zäöü]{4}',re.sub(r'<[^>]+>','',v)): err.append((i,L,'unübersetzt?'))
extra=set(O)-{c['id'] for c in C}
if extra: err.append(('zusätzliche ids',sorted(extra)[:5]))
for e in err[:40]: print(*e)
print(f'{len(C)} Einträge, {len(err)} Probleme'); sys.exit(1 if err else 0)
