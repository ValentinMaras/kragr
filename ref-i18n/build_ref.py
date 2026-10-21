import json,re,sys,glob,runpy,os
D=os.path.dirname(os.path.abspath(__file__))+'/'
t=json.load(open(D+'ttx_ref.json'))
# Fach-Übersetzungen: <fach>_e*.py mit E = {index: en}, Index aus todo_<fach>.json
for f in sorted(glob.glob(D+'todo_*.json')):
    F=f.split('todo_')[1][:-5]; items=json.load(open(f))
    for e in sorted(glob.glob(D+f'{F}_e*.py')):
        for i,v in runpy.run_path(e)['E'].items():
            k=items[i]
            nk=len(re.findall(r'\{\}',k)); ph=re.findall(r'\{(\d*)\}',v)
            if (ph and all(p=='' for p in ph) and len(ph)!=nk) or (not ph and nk): print('PH',F,i,k[:60])
            t[k]=v
# Dezimalpunkt im Text (nicht in Tags)
def dec(v): return re.sub(r'(^|>)([^<]+)', lambda m: m.group(1)+re.sub(r'(\d),(\d)',r'\1.\2',m.group(2)), v)
t={k:dec(v) for k,v in t.items()}
p=sys.argv[1]; s=open(p).read()
a=s.index('const TTX = { en: ')+len('const TTX = { en: '); b=s.index(' };\nconst tt = ',a)
s=s[:a]+json.dumps(t,ensure_ascii=False,indent=0)+s[b:]
open(p,'w').write(s); print('TTX',len(t))
