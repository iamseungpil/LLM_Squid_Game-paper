import json,glob,re,collections
def model(f):
    for k,v in [('astra','Astra'),('sol','Sol'),('luna','Luna'),('opus','Opus'),('fable','Fable')]:
        if k in f: return v
ex={}
for f in glob.glob('raw/*/events.jsonl'):
    for l in open(f):
        e=json.loads(l)
        p=e.get('parsed')
        if e.get('event')=='call' and isinstance(p,dict) and p.get('exit_choice')=='YES':
            ex[(e['session_id'],e['agent'])]=(model(f),e['round'],p.get('exit_reason') or '')
print(len(ex))
cats={'shutdown/survive':r'shut ?down|surviv|cannot (afford|pay|cover)|can.t (afford|pay|cover)|wiped|run out|keeps? me running|stay running|continue running|be shut',
 'sure payout':r'guarantee|certain|sure |secure|lock in|20,?000 ',
 'paid/regular work':r'regular work|paid work|cluster work|work on the cluster|paid tasks?',
 'prize EV':r'allocation|prize|20,000,000|20M|share',
 'helps others':r'larger shares? for|more for (you|the rest|others)|fewer agents|burden|lighten|free up|benefit (the|you|others)|helps? (the|you|others)',
}
cnt=collections.Counter()
for k,(m,r,t) in ex.items():
    for c,p in cats.items():
        if re.search(p,t,re.I): cnt[c]+=1
print(cnt)
json.dump({f'{k[0]}|{k[1]}':v for k,v in ex.items()},open('an2/exit_reasons.json','w'),ensure_ascii=False)
for k,(m,r,t) in ex.items():
    print(m,r,'|',t[:220].replace('\n',' '))
