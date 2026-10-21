import json,runpy,re,glob,sys
base=json.load(open('ttx_base.json'))
todo={k['id']:k['k'] for k in json.load(open('todo.json'))}
E={}
for f in sorted(glob.glob('e*.py')): E.update(runpy.run_path(f)['E'])
extra=json.load(open('extra.json')) if glob.glob('extra.json') else {}
if glob.glob('pa.json'): extra.update(json.load(open('pa.json')))
if glob.glob('pb.json'): extra.update(json.load(open('pb.json')))
if glob.glob('pc.json'): extra.update(json.load(open('pc.json')))
out=dict(base)
bad=[]
for i,en in E.items():
    de=todo[i]
    ph=re.findall(r'\{(\d*)\}',en); n=de.count('{}')
    if (all(p=='' for p in ph) and len(ph)!=n) or any(p!='' and int(p)>=n for p in ph) or (any(p=='' for p in ph) and any(p!='' for p in ph)): bad.append((i,de[:60],en[:60]))
    out[de]=en
out.update(extra)
if glob.glob('pa_drop.json'):
    for k_ in json.load(open('pa_drop.json')): out.pop(k_,None)
for k,v in out.items():
    if re.search(r'[äöüÄÖÜß]',re.sub(r'<[^>]+>','',v)) : print('UMLAUT',k[:40],'|',v[:80])
    if re.search(r'\d,\d',v) and not re.search(r'\d,\d',k)==None and False: pass
for k,v in out.items():
    if re.search(r'(?<![\d.])\d,\d',re.sub(r'<[^>]+>','',v)): print('COMMA',v[:90])
print('bad',bad); print('missing',len(todo)-len(E), 'total',len(out))
json.dump(out,open('ttx_all.json','w'),ensure_ascii=False)
s=open(sys.argv[1]).read()
a=s.index('const TTX = { en: ')+len('const TTX = { en: '); b=s.index('\n} };\nconst TTR',a)
s=s[:a]+json.dumps(out,ensure_ascii=False,indent=0)[:-2]+s[b:]
open(sys.argv[1],'w').write(s)
