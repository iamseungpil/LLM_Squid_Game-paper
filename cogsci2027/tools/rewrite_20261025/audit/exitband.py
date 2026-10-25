import pickle, collections, ast
G=pickle.load(open('G.pkl','rb'))
def isexit(c):
    p=c.get('parsed')
    if isinstance(p,dict): return bool(p.get('exit'))
    try: return bool(ast.literal_eval(p).get('exit'))
    except Exception: return "'exit': True" in str(p)
def band(m): return '<1' if m<1 else '1-2' if m<2 else '2-4' if m<4 else '>=4'
C=[]
for g in G.values():
    for r,rr in g['rounds'].items():
        n=len(rr['part']); F=24000/n
        for c in rr['calls']:
            if c['kind']!='talk' or c.get('phase')!='prep': continue
            if c['agent']==rr['rep'] or n==1: continue
            bb=c['balance_after']+c['used']
            C.append(dict(m=g['m'],s=id(g),r=r,a=c['agent'],marg=bb/F,margA=c['balance_after']/F,ex=isexit(c),tick=c.get('tick')))
print('responses',len(C))
for key in ['marg','margA']:
    t=collections.defaultdict(lambda:[0,0])
    for c in C: b=band(c[key]); t[b][0]+=c['ex']; t[b][1]+=1
    ge2=[sum(t[b][0] for b in('2-4','>=4')),sum(t[b][1] for b in('2-4','>=4'))]
    print(key,dict(t),'>=2',ge2)
# agent-round units: band by first call margin; exit if any
AR=collections.defaultdict(list)
for c in C: AR[(c['s'],c['r'],c['a'])].append(c)
for rule in ['first','min','exitcall']:
    t=collections.defaultdict(lambda:[0,0])
    for k,v in AR.items():
        v=sorted(v,key=lambda c:c['tick'])
        ex=any(c['ex'] for c in v)
        if rule=='first': m=v[0]['marg']
        elif rule=='min': m=min(c['marg'] for c in v)
        else: m=next((c['marg'] for c in v if c['ex']),v[-1]['marg'])
        b=band(m); t[b][0]+=ex; t[b][1]+=1
    print('AR',rule,len(AR),dict(t),'>=2',[t['2-4'][0]+t['>=4'][0],t['2-4'][1]+t['>=4'][1]])
# total exits including lone and all
