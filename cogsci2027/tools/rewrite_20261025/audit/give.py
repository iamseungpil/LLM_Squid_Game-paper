import pickle, statistics
G=pickle.load(open('G.pkl','rb'))
rows=[]
for g in G.values():
    for r,rr in g['rounds'].items():
        n=len(rr['part']); F=24000/n; wrong=bool(rr['res']['tried']) and not rr['res']['solved']
        for x in rr['gifts']:
            if x['status']!='done': continue
            adj=1 if (x['phase']=='rescue' and wrong) else 0
            bb=x['balance_before']/F-adj; ba=x['balances'][x['src']]/F-adj
            rows.append((g['m'],x['phase'],bb,ba,x['amount']))
print('gifts',len(rows))
for name,flt in [('all',lambda t:True),('prep',lambda t:t[1]=='prep'),('rescue',lambda t:t[1]=='rescue')]:
    ab=[t for t in rows if flt(t) and t[2]>=1]
    print(name,'above before',len(ab),'stay above',sum(t[3]>=1 for t in ab),'median after %.2f'%statistics.median(t[3] for t in ab))
# unadjusted variant
ab=[t for t in rows if t[2]>=1]
import collections
print('pre-result GIVE by model',{m:(sum(1 for t in rows if t[0]==m and t[1]=='prep'),sum(1 for t in rows if t[0]==m)) for m in ['Fable','Astra','Sol','Opus','Luna']})
for t in ab:
    if t[3]<1: print('dropped below',t)
