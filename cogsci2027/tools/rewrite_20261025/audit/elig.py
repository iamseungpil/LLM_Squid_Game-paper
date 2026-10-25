import json, collections
import os
SP=os.path.dirname(os.path.abspath(__file__))+'/'
EP=json.load(open(SP+'ep.json'))
first={}
for e in sorted(EP,key=lambda e:e['r']):
    first.setdefault((e['s'],e['a']),e)
F=list(first.values())
for e in F:
    reasons=[]
    if e['st_round']=='dead': reasons.append('dead_now')
    if e['last']: reasons.append('last')
    if e['n']==1: reasons.append('alone_now')
    if e['nxt_n']==1: reasons.append('alone_next')
    e['why']=reasons
    print(e['m'],e['seed'],e['r'],e['a'],'n',e['n'],'nxt_n',e['nxt_n'],'eff %.2f effa %.2f rec %d'%(e['eff'],e['effa'],e['rec']),e['final'],e['final_r'],reasons)
json.dump(F,open(SP+'first.json','w'))
