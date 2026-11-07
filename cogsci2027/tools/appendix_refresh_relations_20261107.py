"""Additional C--H plots for the same hash-verified public v33 cohort, 50 games.
Reuses appendix_refresh_c_h_20261107 data; no simulation/model calls.
Paired-seed bootstrap resamples all models together; no seat-level independence.
"""
import json
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import appendix_refresh_c_h_20261107 as base
from inequality import distribution
base.PAY=json.loads((base.ROOT/'results/appendix_refresh_c_h_20261107.json').read_text())
D=base.DATA;G=D['games'];P=base.PAY;models=base.MODELS;colors=base.COLORS
rng=np.random.default_rng(20261107)


def pearson(rows,x,y):
 a=np.asarray([[g[x],g[y]] for g in rows if g.get(x) is not None and g.get(y) is not None],float)
 return float(np.corrcoef(a.T)[0,1]) if len(a)>2 and np.ptp(a[:,0])>0 and np.ptp(a[:,1])>0 else None


def associations():
 rows=[]
 for m in models:
  for l in P['models'][m]['ledgers']:
   g=base.GAMES[m,l['seed']];rows.append(dict(g,clear=int(g['finishers']>0),all4=int(g['all4_completion']),S=l['historic_settled']['S']/1e6,G=l['historic_settled']['G'],mu=l['historic_settled']['mu']/1e6,given_k=g['given']/1000,goal_pct=100*g['goal']))
 blocks=[[g for g in rows if g['seed']==s] for s in D['seeds']]
 draws=rng.integers(0,10,(2000,10));stats={}
 def plot(name,x,ys,shape):
  fig,axes=plt.subplots(*shape,figsize=(10,3.3*shape[0]));axes=np.asarray(axes).flat
  for ax,(y,label) in zip(axes,ys):
   pairs=[g for g in rows if g.get(x) is not None and g.get(y) is not None];r=pearson(pairs,x,y)
   cis=base.fb.interval([pearson([g for i in draw for g in blocks[i]],x,y) for draw in draws]);stats[name+'_'+y]=dict(r=r,ci95=cis,n=len(pairs))
   for m,c in zip(models,colors):
    p=[g for g in pairs if g['model']==m];ax.scatter([g[x] for g in p],[g[y] for g in p],s=23,alpha=.7,c=c,label=m)
   if x=='rho':
    missing=[g for g in rows if g.get(x) is None and g.get(y) is not None];ax.axvspan(-3.5,-2.5,color='#eee')
    for i,g in enumerate(missing):ax.scatter(-3+(i%5-2)*.1,g[y],s=20,c=colors[models.index(g['model'])],alpha=.6)
    ax.axvline(-2.4,color='.7',lw=.7);ax.text(-3,.97,'No GIVE',transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=7);ax.set_xlabel(r'지원 후 여유 비율 $\rho$')
   else:ax.set_xlabel(x)
   ax.set_ylabel(label);ax.set_title(f'r={r:.2f} [{cis[0]:.2f}, {cis[1]:.2f}], n={len(pairs)}',fontsize=9);ax.grid(alpha=.15)
  fig.axes[0].legend(fontsize=7,ncol=2);fig.tight_layout();base.save(fig,name)
 plot('rho_associations_10games','rho',[('accuracy','정답률'),('goal_pct','잔류 응답률 (%)'),('given_k','총 이전량 (천 토큰)'),('S','정산 Sen (백만 토큰)'),('G','정산 Gini'),('mu','정산 평균 (백만 토큰)')],(2,3))
 plot('rho_completion_10games','rho',[('all4','네 명 완주 (0/1)'),('goal_pct','잔류 응답률 (%)'),('given_k','총 이전량 (천 토큰)')],(1,3))
 fig,axs=plt.subplots(1,3,figsize=(10,3.4))
 for ax,(key,label) in zip(axs,[('accuracy','정답률'),('given_per_agent_round','참여자·라운드당 이전 토큰'),('rho',r'지원 후 여유 비율 $\rho$')]):
  for j,yes in enumerate([False,True]):
   selected=[g for g in G if g['all4_completion']==yes and g[key] is not None]
   for i,g in enumerate(selected):ax.scatter(j+(i%9-4)*.025,g[key],c=colors[models.index(g['model'])],s=22,alpha=.65)
   ys=[g[key] for g in selected];ax.scatter(j,np.mean(ys),c='k',marker='D',s=42);ax.text(j,.99,f'n={len(ys)}',transform=ax.get_xaxis_transform(),ha='center',va='top')
  ax.set(xticks=[0,1],xticklabels=['전원 완주 못함','전원 완주'],ylabel=label,xlim=(-.4,1.4));ax.grid(axis='y',alpha=.15)
 fig.tight_layout();base.save(fig,'all4_profiles_10games')
 (base.ROOT/'results/appendix_refresh_relations_20261107.json').write_text(json.dumps({'cohort':'public_v33','n_games':50,'bootstrap':'2000 paired seed block percentile draws, seed20261107','associations':stats},ensure_ascii=False,indent=2))


def support():
 fig,axs=plt.subplots(1,4,figsize=(12,3.2))
 for ax,(key,label,scale) in zip(axs,[('give_count','GIVE 횟수',1),('give_tokens','GIVE 총량 (천 토큰)',1000),('ask_count','ASK 횟수',1),('ask_tokens','ASK 총량 (천 토큰)',1000)]):
  ax.bar(models,[sum(g['give_ask'][key] for g in G if g['model']==m)/scale for m in models],color=colors);ax.set(title=label);ax.tick_params(axis='x',rotation=30);ax.grid(axis='y',alpha=.2)
 fig.tight_layout();base.save(fig,'give_ask_10games')
 fig,axs=plt.subplots(1,5,figsize=(13,3.5),sharey=True)
 for ax,m,c in zip(axs,models,colors):
  rates=[];cis=[];ns=[]
  games=[g for g in G if g['model']==m]
  draws=np.random.default_rng(1919).integers(0,10,(2000,10))
  for band in range(4):
   rr=[r for g in games for r in g['responses'] if r['eligible'] and r['band']==band];ns.append(len(rr));rates.append(100*sum(r['gifts']>0 for r in rr)/len(rr) if rr else np.nan)
   bb=[]
   for draw in draws:
    r=[r for i in draw for r in games[i]['responses'] if r['eligible'] and r['band']==band]
    if r:bb.append(100*sum(t['gifts']>0 for t in r)/len(r))
   cis.append(base.fb.interval(bb))
  ax.bar(range(4),rates,color=c,alpha=.7)
  for i,(low,hi) in enumerate(cis):
   if low is not None:ax.plot([i,i],[low,hi],color='k',lw=1)
   ax.text(i,.97,f'n={ns[i]}',transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=7,rotation=90)
  ax.set(title=m,xticks=range(4),xticklabels=['<1','1–2','2–4','≥4'],xlabel='응답 시작 생존 여유');ax.grid(axis='y',alpha=.15)
 axs[0].set_ylabel('GIVE가 있었던 응답 (%)');fig.tight_layout();base.save(fig,'give_margin_10games')
 crises=[dict(c,model=g['model'],seed=g['seed']) for g in G for c in g['process']['crises'] if c['round']<8 and c['present']>1]
 groups=['none','short','lifted'];fates=['in','exited','dead'];fc=['#3d8b78','#d49538','#9c5e6b']
 fig,axs=plt.subplots(1,2,figsize=(10,3.6));counts={}
 for i,group in enumerate(groups):
  rr=[r for r in crises if r['group']==group];counts[group]={k:sum(r['status']==k for r in rr) for k in fates};bottom=0
  for fate,c in zip(fates,fc):
   n=counts[group][fate];axs[0].bar(i,n,bottom=bottom,color=c,label={'in':'완주','exited':'EXIT','dead':'꺼짐'}[fate] if i==0 else None)
   if n:axs[0].text(i,bottom+n/2,str(n),ha='center',va='center',color='white');bottom+=n
  axs[0].text(i,len(rr)+.4,f'n={len(rr)}',ha='center',fontsize=8)
 axs[0].set(xticks=range(3),xticklabels=['지원 없음','지원·여유 미회복','지원·여유 회복'],ylabel='첫 위기 에이전트 수');axs[0].legend(fontsize=8)
 first=[]
 for g in G:
  rr=[c for c in g['process']['crises'] if c['round']<8 and c['present']>1]
  if not rr:continue
  r=min(c['round'] for c in rr);rr=[c for c in rr if c['round']==r]
  if rr[0]['present']!=4:continue
  first.append(dict(model=g['model'],seed=g['seed'],recovered=all(c['received']>0 and c['after']>=1 for c in rr),finishers=g['finishers']))
 for j,yes in enumerate([False,True]):
  rows=[g for g in first if g['recovered']==yes]
  for i,g in enumerate(rows):axs[1].scatter(j+(i%9-4)*.025,g['finishers'],color=colors[models.index(g['model'])],s=26,alpha=.65)
  axs[1].text(j,4.35,f"전원 완주 {sum(g['finishers']==4 for g in rows)}/{len(rows)}",ha='center',fontsize=8)
 axs[1].set(xticks=[0,1],xticklabels=['위기 여유 미회복 포함','위기 모두 지원·여유 회복'],ylabel='판별 완주 인원',ylim=(-.2,4.65),yticks=range(5),xlim=(-.4,1.4));fig.tight_layout();base.save(fig,'crisis_followup_10games')
 (base.ROOT/'results/appendix_refresh_support_20261107.json').write_text(json.dumps({'n_crises':len(crises),'n_crisis_games':len({(r['model'],r['seed']) for r in crises}),'counts':counts,'first_crisis_four_present_games':first},ensure_ascii=False,indent=2))

if __name__=='__main__':associations();support()
