import pickle, json, collections
G=pickle.load(open('G.pkl','rb')); EP=json.load(open('ep.json'))
nr=[e for e in EP if e['rec']==0]
print('no-receipt episodes',len(nr),'solo',sum(e['n']==1 for e in nr))
cnt=0; tot=0; fails=[]
for e in nr:
    if e['n']==1: continue
    rr=G[e['s']]['rounds'][e['r']]; res=rr['res']; F=e['F']
    peers=[p for p in res['pending'] if p!=e['a']]
    need=max(0,2*F-e['b'])
    ok=any(res['balances'][p]-need>=2*F for p in peers)
    tot+=1; cnt+=ok
    if not ok: fails.append((e['m'],e['seed'],e['r'],e['a'],len(peers),[res['balances'][p] for p in peers],e['b'],F))
print('capable',cnt,'/',tot); print(fails)
# variant: only peers active (not gone) -- also with alive peers count == 0
# ASK
ask=[e for e in EP if e['asked']]; noask=[e for e in EP if not e['asked']]
print('ASK eps',len(ask),'received',sum(e['rec']>0 for e in ask),'| no ASK',len(noask),'received',sum(e['rec']>0 for e in noask))
same=[e for e in ask if set(e['ask_ticks'])&set(e['give_ticks'])]
first_same=[e for e in ask if e['give_ticks'] and min(e['give_ticks'])<=min(e['ask_ticks'])]
print('ASK & GIVE same tick',len(same),'first GIVE at or before first ASK tick',len(first_same))
for e in ask: print(e['m'],e['seed'],e['r'],e['a'],'ask',e['ask_ticks'],'give',e['give_ticks'])
