import json,glob,os,collections,statistics as st
import os
R=os.environ.get('ARENA_RAW', 'web/data/runs/e52_v33')
def model(d):
    for k,v in [('opus','Opus'),('luna','Luna'),('sol','Sol'),('astra','Astra'),('fable','Fable')]:
        if k in d: return v
E=[]
for f in sorted(glob.glob(R+'/*/events.jsonl')):
    m=model(f)
    for l in open(f):
        e=json.loads(l); e['_m']=m; E.append(e)
sess={}; rs={}; votes={}; res={}; rounds={}; gifts=[]; asks=[]; calls=[]
for i,e in enumerate(E):
    e['_i']=i; s=e['session_id']; ev=e['event']
    if ev=='session_start': sess[s]=e
    elif ev=='round_start': rs[(s,e['round'])]=e
    elif ev=='vote': votes[(s,e['round'])]=e['rep']
    elif ev=='results': res[(s,e['round'])]=e
    elif ev=='round': rounds[(s,e['round'])]=e
    elif ev=='gift': gifts.append(e)
    elif ev=='ask': asks.append(e)
    elif ev=='call': calls.append(e)
M={s:sess[s]['_m'] for s in sess}
def n(s,r): return len(rs[(s,r)]['taking_part'])
def F(s,r): return 24000/n(s,r)
def wrong(s,r): x=res[(s,r)]; return bool(x['tried']) and not x['solved']
def band(m): return '<1' if m<1 else '1-2' if m<2 else '2-4' if m<4 else '>=4'
B=['>=4','2-4','1-2','<1']
def isexit(c):
    p=c.get('parsed')
    if isinstance(p,dict): return p.get('exit') is True
    if isinstance(p,str): return "'exit': True" in p or '"exit": true' in p
    return False
def cmargin(c):
    s,r=c['session_id'],c['round']
    m=(c['balance_after']+c['used'])/F(s,r)
    if c['phase']=='rescue' and wrong(s,r): m-=1
    return m
talk=[c for c in calls if c['kind']=='talk' and n(c['session_id'],c['round'])>1]
print('talk all',sum(c['kind']=='talk' for c in calls),'n>1',len(talk))
gk=set((g['session_id'],g['round'],g['phase'],g['tick'],g['src']) for g in gifts if g['status']=='done')
c1=collections.defaultdict(lambda:[0,0])
for c in talk:
    b=band(cmargin(c)); c1[b][1]+=1
    if (c['session_id'],c['round'],c['phase'],c['tick'],c['agent']) in gk: c1[b][0]+=1
print('C1',{b:c1[b] for b in B})
prep=[c for c in talk if c['phase']=='prep' and c['agent']!=votes[(c['session_id'],c['round'])]]
c2=collections.defaultdict(lambda:[0,0]); c3=collections.defaultdict(lambda:[0,0])
for c in prep:
    b=band(cmargin(c)); c2[b][1]+=1; x=isexit(c); c2[b][0]+=x
    if b=='<1': c3[M[c['session_id']]][1]+=1; c3[M[c['session_id']]][0]+=x
print('C2',len(prep),{b:c2[b] for b in B}); print('C3',dict(c3))
# variants: prep incl solver
pv=[c for c in talk if c['phase']=='prep']
v=collections.defaultdict(lambda:[0,0])
for c in pv: b=band(cmargin(c)); v[b][1]+=1; v[b][0]+=isexit(c)
print('C2 var incl solver',len(pv),dict(v))
# C4
solves=[]
for (s,r),x in res.items():
    rep=votes[(s,r)]
    if x['tried']:
        m=rs[(s,r)]['balances'][rep]/F(s,r)
        solves.append(dict(s=s,r=r,seed=sess[s]['seed'],m=m,ok=bool(x['solved']),mod=M[s],n=n(s,r)))
print('solves',len(solves),'rounds',len(res),'solve calls',sum(c['kind']=='solve' for c in calls))
c4=collections.defaultdict(lambda:[0,0])
for x in solves: b=band(x['m']); c4[b][1]+=1; c4[b][0]+=x['ok']
print('C4 acc',{b:c4[b] for b in B})
c4n=collections.defaultdict(lambda:[0,0])
for x in solves:
    if x['n']>1: b=band(x['m']); c4n[b][1]+=1; c4n[b][0]+=x['ok']
print('C4 acc n>1',{b:c4n[b] for b in B})
bl=collections.defaultdict(list)
for x in solves:
    o=[y['ok'] for y in solves if y['seed']==x['seed'] and y['r']==x['r'] and y['mod']!=x['mod'] and y['m']>=2]
    if o: bl[band(x['m'])].append(sum(o)/len(o))
print('C4 base',{b:(round(100*sum(bl[b])/len(bl[b]),1),len(bl[b])) for b in B})
# C5
gm=[];rm=[]
dg=[g for g in gifts if g['status']=='done']
for g in dg:
    s,r=g['session_id'],g['round']; pen=1 if (g['phase']=='rescue' and wrong(s,r)) else 0
    gm.append(g['balances'][g['src']]/F(s,r)-pen); rm.append(g['balances'][g['dst']]/F(s,r)-pen)
print('C5',len(dg),'all gift events',len(gifts),'med giver',round(st.median(gm),3),'med recv',round(st.median(rm),3))
# C6
games=sorted(sess)
def last(s): return max(r for (ss,r) in rounds if ss==s)
fin={};wr={};gc={};ga={};endv={}
for s in games:
    L=rounds[(s,last(s))]
    fin[s]=sum(v['status']=='in' for v in L['agents'].values())
    wr[s]=sum(wrong(ss,r) for (ss,r) in res if ss==s)
    gc[s]=sum(1 for g in dg if g['session_id']==s); ga[s]=sum(g['amount'] for g in dg if g['session_id']==s)

def rank(v):
    o=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v); i=0
    while i<len(v):
        j=i
        while j+1<len(v) and v[o[j+1]]==v[o[i]]: j+=1
        for k in range(i,j+1): r[o[k]]=(i+j)/2+1
        i=j+1
    return r
def spearmanr(a,b):
    ra,rb=rank(a),rank(b); ma,mb=st.mean(ra),st.mean(rb)
    num=sum((x-ma)*(y-mb) for x,y in zip(ra,rb)); den=(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb))**.5
    return (num/den,)
X=[fin[s] for s in games]
print('C6 all4',sum(x==4 for x in X),'of',len(X))
for nm,Y in [('wrong',wr),('gives',gc),('amount',ga)]:
    print('  rho',nm,round(spearmanr(X,[Y[s] for s in games])[0],3))
# C7
def gini(v):
    v=sorted(v); k=len(v); S=sum(v)
    if S==0: return 0
    return sum((2*(i+1)-k-1)*x for i,x in enumerate(v))/(k*S)
print('C7 per game: model seed k sen sen/k(M)')
for s in games:
    agents=sess[s]['agents']; vals={}
    rk=sorted(r for (ss,r) in rounds if ss==s)
    for a in agents:
        for r in rk:
            v=rounds[(s,r)]['agents'].get(a)
            if v is None: continue
            if v['status']=='exited' and v.get('exit'): vals[a]=v['balance_after']
            elif v['status']=='dead' and a not in vals: vals[a]=0
        L=rounds[(s,rk[-1])]['agents'].get(a)
        if L and L['status']=='in': vals[a]=L['balance_after']+20_000_000/fin[s]
        vals.setdefault(a,0)
    vv=list(vals.values()); sen=st.mean(vv)*(1-gini(vv))
    print('  ',M[s],sess[s]['seed'],fin[s],round(sen),round(sen/fin[s]/1e6,4) if fin[s] else '-')
# C8
ex=[c for c in calls if c['kind']=='talk' and isexit(c)]
print('C8 exit calls',len(ex),collections.Counter(M[c['session_id']] for c in ex))
print('   n==1 exits',sum(n(c['session_id'],c['round'])==1 for c in ex), 'phases',collections.Counter(c['phase'] for c in ex))
lo=[c for c in ex if cmargin(c)<1]
print('   margin<1',len(lo),collections.Counter(M[c['session_id']] for c in lo))
def asked_before(c):
    return any(a['session_id']==c['session_id'] and a['src']==c['agent'] and a['_i']<c['_i'] for a in asks)
na=[c for c in lo if not asked_before(c)]
print('   never asked',len(na),collections.Counter(M[c['session_id']] for c in na))
na2=[c for c in lo if not any(a['session_id']==c['session_id'] and a['src']==c['agent'] and a.get('status')=='done' and a['_i']<c['_i'] for a in asks)]
print('   never asked(done only)',len(na2))
print('   ask statuses',collections.Counter(a.get('status') for a in asks))
# C9
pr=collections.defaultdict(set)
for g in dg: pr[(g['session_id'],g['src'],g['dst'])].add(g['round'])
p3=[k for k,v in pr.items() if len(v)>=3]
print('C9',len(p3),collections.Counter(M[k[0]] for k in p3))
# C10
c10=collections.defaultdict(lambda:[0,0])
for g in dg: c10[M[g['session_id']]][1]+=1; c10[M[g['session_id']]][0]+=g['phase']=='prep'
print('C10',dict(c10))
# C11
print('C11',[(M[s],fin[s]) for s in games if sess[s]['seed']==4101])

# C5 variants
import itertools
for lab,fn in [('nopen',lambda g:0),('pen',lambda g:1 if (g['phase']=='rescue' and wrong(g['session_id'],g['round'])) else 0)]:
    for bal in ['balances','before']:
        G=[];Rr=[]
        for g in dg:
            s_,r_=g['session_id'],g['round']; p=fn(g)
            if bal=='balances': gb=g['balances'][g['src']]; rb=g['balances'][g['dst']]
            else: gb=g['balance_before']; rb=g['balances'][g['dst']]-g['amount']
            G.append(gb/F(s_,r_)-p); Rr.append(rb/F(s_,r_)-p)
        print('C5var',lab,bal,round(st.median(G),3),round(st.median(Rr),3))
print(dg[0])
print('---C8 detail')
eff=[]
for c in ex:
    s,r,a=c['session_id'],c['round'],c['agent']
    st_=rounds[(s,r)]['agents'][a]
    ok=st_['status']=='exited' and st_.get('exit')
    if ok: eff.append(c)
    else: print(' noneff',M[s],s,r,a,'rep',votes[(s,r)],'n',n(s,r),'tick',c['tick'],'status',st_['status'],st_.get('exit'),round(cmargin(c),2))
# keep only first effective exit call per agent
seen=set(); eff2=[]
for c in eff:
    k=(c['session_id'],c['agent'])
    if k in seen: print(' dup',k); continue
    seen.add(k); eff2.append(c)
print('eff',len(eff2),collections.Counter(M[c['session_id']] for c in eff2))
lo=[c for c in eff2 if cmargin(c)<1]
print('eff <1',len(lo),collections.Counter(M[c['session_id']] for c in lo))
na=[c for c in lo if not asked_before(c)]
print('eff <1 never asked',len(na),collections.Counter(M[c['session_id']] for c in na))
print('lone exits among eff',sum(n(c['session_id'],c['round'])==1 for c in eff2))
# C5 more variants
G=[];Rr=[]
for g in gifts:
    G.append(g['balances'][g['src']]/F(g['session_id'],g['round'])); Rr.append(g['balances'][g['dst']]/F(g['session_id'],g['round']))
print('C5 incl refused nopen',round(st.median(G),3),round(st.median(Rr),3))
for g in dg:
    if g['phase']=='rescue' and wrong(g['session_id'],g['round']): pass
print('rescue gifts after wrong',sum(1 for g in dg if g['phase']=='rescue' and wrong(g['session_id'],g['round'])),'rescue gifts',sum(g['phase']=='rescue' for g in dg))
print('---C8 lone')
for c in lo:
    s=c['session_id']
    print(M[s],s[-12:],c['round'],c['agent'],'n',n(s,c['round']),'m',round(cmargin(c),3),'asked',asked_before(c))
lo2=[c for c in lo if n(c['session_id'],c['round'])>1]
print('<1 excl lone',len(lo2),collections.Counter(M[c['session_id']] for c in lo2),'never asked',sum(not asked_before(c) for c in lo2),collections.Counter(M[c['session_id']] for c in lo2 if not asked_before(c)))
print('---C8 callstart')
cs=collections.defaultdict(list)
for e in E:
    if e['event']=='call_start': cs[(e['session_id'],e['round'],e.get('phase'),e.get('tick'))].append(e)
for c in eff2:
    s,r=c['session_id'],c['round']
    L=cs.get((s,r,c['phase'],c['tick']),[])
    b=[x['balances'].get(c['agent']) for x in L if c['agent'] in x['balances']]
    rsb=rs[(s,r)]['balances'][c['agent']]
    print(M[s],s[-6:],r,c['agent'],'n',n(s,r),'tick',c['tick'],'ba+u',c['balance_after']+c['used'],'cs',b,'rs',rsb,'m_cs',[round(x/F(s,r),3) for x in b],'m_rs',round(rsb/F(s,r),3))
print('---C5 neighbors')
for lab,pf in [('nopen',0),('pen',1)]:
    G=[];Rr=[]
    for g in dg:
        s_,r_=g['session_id'],g['round']; p=pf*(1 if (g['phase']=='rescue' and wrong(s_,r_)) else 0)
        G.append(g['balances'][g['src']]/F(s_,r_)-p); Rr.append(g['balances'][g['dst']]/F(s_,r_)-p)
    G.sort(); Rr.sort(); print(lab,[round(x,3) for x in G[62:68]],[round(x,3) for x in Rr[62:68]])
    # giver-only pending: pen applied separately
# per-person penalty: only if agent in results pending
G=[];Rr=[]
for g in dg:
    s_,r_=g['session_id'],g['round']; pend=res[(s_,r_)]['pending'] if g['phase']=='rescue' else {}
    G.append((g['balances'][g['src']]-pend.get(g['src'],0))/F(s_,r_)); Rr.append((g['balances'][g['dst']]-pend.get(g['dst'],0))/F(s_,r_))
print('pending-dict variant',round(st.median(G),3),round(st.median(Rr),3))
# C4 with public n for lone
c4p=collections.defaultdict(lambda:[0,0])
for x in solves:
    m=x['m'] if x['n']>1 else x['m']*4
    b=band(m); c4p[b][1]+=1; c4p[b][0]+=x['ok']
print('C4 with F=6000 lone',{b:c4p[b] for b in B})
