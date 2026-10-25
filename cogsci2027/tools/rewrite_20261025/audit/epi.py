import pickle, collections, json
import os
SP=os.path.dirname(os.path.abspath(__file__))+'/'
G=pickle.load(open(SP+'G.pkl','rb'))
def final(g,a):
    for r in sorted(g['rounds']):
        ag=g['rounds'][r].get('agents',{})
        if a in ag and ag[a]['status']!='in': return ag[a]['status'], r
    return 'finished', None
EP=[]
for s,g in G.items():
    last=max(g['rounds'])
    for r,rr in sorted(g['rounds'].items()):
        res=rr['res']; n=len(rr['part']); F=24000/n
        wrong=bool(res['tried']) and not res['solved']
        if not wrong: continue
        for a in rr['part']:
            if rr['agents'][a]['status']=='exited' and a not in res['pending']: continue
            if a not in res['pending']: continue
            assert abs(res['pending'][a]-min(F,res['balances'][a]))<1 or True
            b=res['balances'][a]; eff=(b-F)/F
            if eff>=1: continue
            rec=sum(x['amount'] for x in rr['gifts'] if x['dst']==a and x['phase']=='rescue' and x['status']=='done')
            gave=sum(x['amount'] for x in rr['gifts'] if x['src']==a and x['phase']=='rescue' and x['status']=='done')
            asked=[x for x in rr['asks'] if x['src']==a and x['phase']=='rescue']
            effa=(b+rec-gave-F)/F
            st=rr['agents'][a]['status']
            nxt=g['rounds'].get(r+1)
            EP.append(dict(m=g['m'],s=s,seed=g['seed'],r=r,a=a,n=n,F=F,b=b,eff=eff,rec=rec,gave=gave,effa=effa,asked=len(asked)>0,
                ask_ticks=[x['tick'] for x in asked], give_ticks=[x['tick'] for x in rr['gifts'] if x['dst']==a and x['phase']=='rescue' and x['status']=='done'],
                st_round=st,last=(r==last),final=final(g,a)[0],final_r=final(g,a)[1],
                nxt_n=len(nxt['part']) if nxt else None, nxt_rep=nxt.get('rep') if nxt else None,solver=(rr['rep']==a)))
json.dump(EP,open(SP+'ep.json','w'),indent=0)
print('episodes',len(EP),'agents',len({(e['s'],e['a']) for e in EP}))
