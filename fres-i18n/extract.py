import json,re,subprocess
B='/home/claude/work/v085/'
def ttx(f):
    s=open(B+f).read(); a=s.index('const TTX = { en: ')+18
    return json.JSONDecoder().raw_decode(s[a:])[0]
i18n=json.loads(subprocess.check_output(['node','-e',"""
const fs=require('fs');const s=fs.readFileSync('%ssize.html','utf8');
const a=s.indexOf('const I18N = ');const b=s.indexOf('\\n};',a);const I=eval('('+s.slice(a+13,b+2)+')');
process.stdout.write(JSON.stringify({de:I.de,en:I.en}))"""%B]))
pool={}   # id -> {de,en,src}
order=[]
def add(id,de,en,src):
    if id in pool: return
    pool[id]={'de':de,'en':en,'src':src}; order.append(id)
for k,de in i18n['de'].items():
    if k=='langNotice': continue
    add('I:'+k,de,i18n['en'].get(k,''),'size-ui')
for src,f in [('size','size.html'),('ref','ref.html')]:
    for de,en in ttx(f).items(): add('T:'+de,de,en,src)
same=[i for i in order if pool[i]['de']==pool[i]['en'] or not re.search(r'[A-Za-zÄÖÜäöüß]{2}',re.sub(r'<[^>]+>','',pool[i]['de']))]
todo=[i for i in order if i not in set(same)]
print('gesamt',len(order),'gleich',len(same),'zu übersetzen',len(todo),'Zeichen',sum(len(pool[i]['de']) for i in todo))
json.dump({'pool':pool,'order':order,'same':same,'todo':todo},open('pool.json','w'),ensure_ascii=False)
# Pakete ~16k Zeichen
chunks=[];cur=[];n=0
for i in todo:
    L=len(pool[i]['de'])+len(pool[i]['en'])
    if cur and n+L>30000: chunks.append(cur);cur=[];n=0
    cur.append(i);n+=L
if cur: chunks.append(cur)
for ci,c in enumerate(chunks):
    json.dump([{'id':f'{ci:02d}-{j}','de':pool[i]['de'],'en':pool[i]['en']} for j,i in enumerate(c)],open(f'c{ci:02d}.json','w'),ensure_ascii=False,indent=1)
json.dump({f'{ci:02d}-{j}':i for ci,c in enumerate(chunks) for j,i in enumerate(c)},open('idmap.json','w'),ensure_ascii=False)
print('Pakete',len(chunks),[len(c) for c in chunks])
