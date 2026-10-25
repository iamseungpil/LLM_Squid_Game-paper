import pickle, collections
import os
SP=os.path.dirname(os.path.abspath(__file__))+'/'
G=pickle.load(open(SP+'G.pkl','rb'))
S=[]; task=collections.defaultdict(set)
for g in G.values():
    for r,rr in g['rounds'].items():
        res=rr['res']
        if not res['tried']: continue
        a=res['tried'][0]; n=len(rr['part']); F=24000/n
        pub=rr.get('public') 
        S.append(dict(m=g['m'],seed=g['seed'],r=r,n=n,marg=rr['bal0'][a]/F,ok=bool(res['solved'])))
print('solves',len(S))
# model accuracy
acc=collections.defaultdict(list)
for s in S: acc[s['m']].append(s['ok'])
print({m:'%d/%d=%.0f%%'%(sum(v),len(v),100*sum(v)/len(v)) for m,v in acc.items()})
def band(lo,hi):
    rows=[s for s in S if lo<=s['marg']<hi]
    pairs=[]; perrow=[]
    for s in rows:
        b=[t['ok'] for t in S if t['seed']==s['seed'] and t['r']==s['r'] and t['m']!=s['m'] and t['marg']>=2]
        if b: pairs+=b; perrow.append(sum(b)/len(b))
    nb=sum(1 for s in rows if any(t['seed']==s['seed'] and t['r']==s['r'] and t['m']!=s['m'] and t['marg']>=2 for t in S))
    return len(rows),sum(s['ok'] for s in rows),('pooled %.1f%% (%d)'%(100*sum(pairs)/len(pairs),len(pairs)) if pairs else None),('per-row mean %.1f%% over %d rows'%(100*sum(perrow)/len(perrow),len(perrow)) if perrow else None)
for lo,hi in [(0,1),(1,2),(2,4),(4,99),(2,99)]: print(lo,hi,band(lo,hi))
# with eff from the start balance including prep receipts? skip
for lo,hi in [(0,1),(1,2)]:
    rows=[s for s in S if lo<=s['marg']<hi]
    wb=[s for s in rows if any(t['seed']==s['seed'] and t['r']==s['r'] and t['m']!=s['m'] and t['marg']>=2 for t in S)]
    print('band',lo,hi,'rows with baseline',len(wb),'acc',sum(s['ok'] for s in wb))
