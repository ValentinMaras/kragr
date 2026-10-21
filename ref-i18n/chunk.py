import json,re,sys
F=sys.argv[1]
FW=re.compile(r'\b(der|die|das|und|mit|für|von|zu|im|am|auf|aus|bei|nach|ist|sind|wird|werden|nicht|kein|keine|ein|eine|einer|den|dem|des|über|unter|oder|als|wie|nur|noch|je|bis|zum|zur|ab|vom|oben|unten|gewählt|vorh|erf|zul|bzw|ohne|gesamt|links|rechts|mitte|Seite)\b')
plain=lambda s: re.sub(r'&[a-z#0-9]+;',' ',re.sub(r'<[^>]+>',' ',s))
def isGer(s):
    p=plain(s)
    if not re.search(r'[A-Za-zÄÖÜäöüß]{3,}',p): return False
    return bool(re.search(r'[äöüÄÖÜß]',p) or FW.search(p) or re.search(r'(^|[\s(„-])[A-ZÄÖÜ][a-zäöüß]{3,}',p))
d=json.load(open(f'col_{F}.json'))
dyn=[x for x in d['dyn'] if len(x)<=400 and not re.search(r'<(div class="card"|table|section|svg)',x)]
import os
items=json.load(open(f'todo_{F}.json')) if os.path.exists(f'todo_{F}.json') else []; start=len(items); seen=set(items)
done=json.load(open('ttx_ref.json')) if __import__('os').path.exists('ttx_ref.json') else {}
for x in d['static']+dyn:
    if x in seen or x in done or not isGer(x): continue
    if re.search(r'nav-list-item|class="nx"|‹ zurück|weiter ›|search-hit',x): continue
    if re.match(r'^(Baustatik|Lastannahmen|Stahlbeton|Stahlbau|Holzbau|Mauerwerk|Grundbau|Wasserbau|Bauphysik|Mathematik) · ',x): continue
    seen.add(x); items.append(x)
json.dump(items,open(f'todo_{F}.json','w'),ensure_ascii=False)
ch=[];cur=[];n=0
for i,x in enumerate(items):
    if i<start: continue
    cur.append((i,x)); n+=len(x)
    if n>9000: ch.append(cur);cur=[];n=0
if cur: ch.append(cur)
import glob
j0=len(glob.glob(f'{F}_c*.txt'))
for j,c in enumerate(ch): open(f'{F}_c{j0+j}.txt','w').write('\n'.join(f'{i}\t{x}' for i,x in c))
print('new',len(items)-start,sum(map(len,items[start:])),len(ch))
