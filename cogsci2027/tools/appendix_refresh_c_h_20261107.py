"""Refresh appendix C--H from the frozen public v33 ten-game/model cohort.
Sources: cohort_public_20261105.json and its SHA256-verified raw files under
~/squid5-runs/e52_v33. Five models x seeds4101--4110; no additional model calls.
Outputs are new assets/JSON/tables only. Original assets/manuscript untouched.
Current L=(balance-pending fine)/round-start charge, rho=weighted giver L / taker L.
Bootstrap: whole games within each model, 2000 draws, seed1919. All-zero Gini missing.
"""
import json, math, random
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import ablation_prize_20261103 as ab
import feedback_20261028 as fb
import arena_strategy as strategy
import arena_exit_events as ex
from inequality import distribution

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ko/figures/appendix_refresh_20261107'; OUT.mkdir(exist_ok=True)
TAB=ROOT/'ko/tables/appendix_refresh_20261107'; TAB.mkdir(exist_ok=True)
WORK=ROOT.parents[0]/'review/appendix_consolidation_20261107/staging'
MODELS=['Fable','Astra','Sol','Opus','Luna']
COLORS=['#7155A1','#CE5184','#B58B18','#278D7A','#98633B']
font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
plt.rcParams.update({'font.family':'NanumGothic','font.size':9,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
DATA=json.loads((ROOT/'results/cohort_public_20261105.json').read_text())
for s in DATA['sources']:
 assert fb.sha(fb.read_bytes(Path(s['path'])))==s['sha256_decompressed'],s['path']
CASES=ab.raw_cases(ab.V33,DATA['seeds']); assert len(CASES)==50
GAMES={(g['model'],g['seed']):g for g in DATA['games']}
assert set(GAMES)=={(m,s) for m in MODELS for s in range(4101,4111)}
PAY={'cohort':'public_v33','seeds':DATA['seeds'],'sources':DATA['sources'],'models':{},'checks':{'raw_sources_verified':len(DATA['sources']),'games':50}}

def save(fig,name):
 for ext in ['pdf','png']: fig.savefig(OUT/f'{name}.{ext}',dpi=200,bbox_inches='tight')
 plt.close(fig)

def tex_table(name,headers,rows):
 body='\n'.join([r'\begin{tabular}{@{}l'+'r'*(len(headers)-1)+r'@{}}',r'\toprule',' & '.join(headers)+r' \\',r'\midrule',*[' & '.join(map(str,row))+r' \\' for row in rows],r'\bottomrule',r'\end{tabular}'])+'\n'
 (TAB/f'{name}.tex').write_text(body)

def build():
 for m in MODELS:
  cases=sorted([c for c in CASES if c['model']==m],key=lambda c:c['seed'])
  games=[GAMES[m,c['seed']] for c in cases]
  asks=[]; gifts=[]; trajectories=[]; exits=[]; strategies=[]; ledgers=[]; risk=[]
  for c,g in zip(cases,games):
   ev=[e for _,e in c['events']]; assert c['result']['session_id']==g['session_id']
   ledger=fb.game_metrics(ev,c['result'],m,include_singleton=True)
   assert ledger['gifts']==g['gifts'] and ledger['given']==g['given'];ledgers.append(ledger)
   starts={e['round']:e for e in ev if e['event']=='round_start'}
   results={e['round']:e for e in ev if e['event']=='results'}
   snapshots={(e['round'],e['phase'],e['tick']):e for e in ev if e['event']=='call_start' and e.get('kind')=='talk'}
   for e in ev:
    if e['event']=='ask' and e.get('status')=='done' and e['amount']>0:
     fee=24000/len(starts[e['round']]['taking_part'])
     pend=results[e['round']]['pending'] if e['phase']=='rescue' else {}
     # ASK events store current balances after the response cost, at execution.
     balances=e.get('balances',snapshots[e['round'],e['phase'],e['tick']]['balances'])
     asks.append({'seed':c['seed'],'round':e['round'],'x':balances[e['dst']]/fee-pend.get(e['dst'],0)/fee,'y':balances[e['src']]/fee-pend.get(e['src'],0)/fee,'amount':e['amount']})
   gifts.extend(dict(x,seed=c['seed']) for x in g['gifts'])
   exits.extend(ex.exit_rows(c['events'],c['result']))
   strategies.append(strategy.game_rows(ev,c['result']))
   ends={e['round']:e for e in ev if e['event']=='round'}
   bal=dict(c['result']['starts']); statuses={a:'in' for a in bal}; rr=[]
   for r in range(9):
    if r in ends:
     bal.update(ends[r]['end']);statuses.update({a:v['status'] for a,v in ends[r]['agents'].items()})
    observed=r==0 or r in ends
    rr.append(dict(round=r,observed=observed,**distribution(list(bal.values())),remaining=sum(v=='in' for v in statuses.values()) if observed else 0,
      seat_balances={str(c['result']['starts'][a]):(None if statuses[a]=='exited' else bal[a]) for a in bal}))
   assert abs(rr[-1]['S']-ledger['pre_prize']['S'])<1e-8
   trajectories.append(dict(seed=c['seed'],rounds=rr))
   for row in g['responses']:
    risk.append(dict(row,seed=c['seed']))
  rng=random.Random(1919);boot=[]
  for _ in range(2000):
   v=fb.revised_rho([x for _ in games for x in rng.choice(games)['gifts']])
   if v['weighted_giver_margin'] is not None: boot.append([v['weighted_giver_margin'],v['weighted_taker_margin']])
  cur=fb.revised_rho(gifts)
  assert math.isclose(cur['rho'],DATA['summary']['models'][m]['rho'])
  PAY['models'][m]={'label':DATA['models'][m],'gifts':gifts,'asks':asks,'centroid':[cur['weighted_giver_margin'],cur['weighted_taker_margin']],'rho':cur['rho'],'centroid_ci95':np.quantile(boot,[.025,.975],axis=0).T.tolist(),'valid_boot':len(boot),'trajectories':trajectories,'exits':exits,'exit_summary':ex.summarize(exits,10),'strategy':strategy.summarize(strategies),'ledgers':ledgers,'risk':risk}


def scatter_gifts(only_c1=False):
 fig,grid=plt.subplots(2,3,figsize=(8.0,5.9),sharex=True,sharey=True)
 axs=list(grid.flat)[:5]
 allxy=[v for p in PAY['models'].values() for g in p['gifts'] for v in (g['giver_margin'],g['taker_margin'])]+[v for p in PAY['models'].values() for a in p['asks'] for v in (a['x'],a['y'])]
 low=min(-1.1,min(allxy)-.2);high=max(10.3,max(allxy)+.3)
 maxamount=max(g['amount'] for p in PAY['models'].values() for g in p['gifts']+p['asks'])
 for ax,m in zip(axs,MODELS):
  p=PAY['models'][m];ax.axvspan(low,1,color='#eeeeee');ax.axhspan(low,1,color='#eeeeee');ax.plot([low,high],[low,high],'--',color='.65',lw=.7)
  for rows,x,y,color,label in [(p['asks'],'x','y','#D03B3A','ASK'),(p['gifts'],'giver_margin','taker_margin','#2369A8','GIVE')]:
   ax.scatter([r[x] for r in rows],[r[y] for r in rows],s=[8+95*r['amount']/maxamount for r in rows],c=color,alpha=.38,linewidths=.4,label=label)
  (x,y),((xl,xh),(yl,yh))=p['centroid'],p['centroid_ci95'];ax.plot([xl,xh],[y,y],color='k');ax.plot([x,x],[yl,yh],color='k');ax.plot(x,y,'k+',ms=8)
  ax.set(title=f"{m} (10판)\n$\\rho$={p['rho']:.2f} · GIVE {len(p['gifts'])} · ASK {len(p['asks'])}",xlabel='지원자 / 요청받은 쪽 여유',xlim=(low,high),ylim=(low,high));ax.set_aspect('equal')
 axs[0].set_ylabel('수혜자 / 요청한 쪽 여유');axs[3].set_ylabel('수혜자 / 요청한 쪽 여유')
 keyax=grid.flat[5];keyax.axis('off')
 from matplotlib.lines import Line2D
 keyax.legend([Line2D([],[],marker='o',ls='',color='#2369A8',alpha=.55),Line2D([],[],marker='o',ls='',color='#D03B3A',alpha=.55),Line2D([],[],marker='+',ls='',color='black',ms=9)],["GIVE (300건)","ASK (250건)","GIVE 가중 평균과 95% 구간"],loc='center',frameon=False,fontsize=8)
 for ax in axs: ax.tick_params(labelbottom=True,labelleft=True,labelsize=8);ax.title.set_fontsize(8);ax.xaxis.label.set_fontsize(8);ax.yaxis.label.set_fontsize(8)
 fig.tight_layout(pad=1.0,h_pad=1.4,w_pad=1.1);save(fig,'arena_gifts_10games')
 if only_c1:return
 fig,ax=plt.subplots(figsize=(5.5,5.5));ax.axvspan(-1,1,color='#eee');ax.axhspan(-1,1,color='#eee');ax.plot([-1,8],[-1,8],'--',color='.6')
 for m,c in zip(MODELS,COLORS):
  p=PAY['models'][m];(x,y),((xl,xh),(yl,yh))=p['centroid'],p['centroid_ci95'];ax.plot([xl,xh],[y,y],color=c);ax.plot([x,x],[yl,yh],color=c);ax.plot(x,y,'o',color=c,label=f"{m} ($\\rho$={p['rho']:.2f})")
 ax.set(xlabel='지원자 가중 평균 여유',ylabel='수혜자 가중 평균 여유',xlim=(-1,8),ylim=(-1,8));ax.set_aspect('equal',adjustable='box');ax.legend(fontsize=8);save(fig,'arena_centroids_10games')


def completion():
 fig,axs=plt.subplots(1,2,figsize=(10,3.5),gridspec_kw={'width_ratios':[2,1]})
 matrix=[[GAMES[m,s]['finishers'] for s in range(4101,4111)] for m in MODELS]
 im=axs[0].imshow(matrix,vmin=0,vmax=4,cmap='Blues',aspect='auto')
 for i in range(5):
  for j in range(10):axs[0].text(j,i,str(matrix[i][j]),ha='center',va='center',color='white' if matrix[i][j]>=3 else 'black')
 axs[0].set(xticks=range(10),xticklabels=range(4101,4111),yticks=range(5),yticklabels=MODELS,title='(a) 판별 완주 인원',xlabel='시드');axs[0].tick_params(axis='x',rotation=45)
 counts=[sum(x==4 for x in r) for r in matrix];axs[1].barh(MODELS,counts,color=COLORS);axs[1].invert_yaxis();axs[1].set(xlim=(0,10),title='(b) 네 명 완주 판 수',xlabel='전체 10판')
 for i,n in enumerate(counts):axs[1].text(n+.1,i,f'{n}/10',va='center')
 fig.tight_layout();save(fig,'all_four_completion_10games')
 rows=[]
 for m in MODELS:
  gs=[GAMES[m,s] for s in DATA['seeds']];rows.append([m,f"{sum(g['all4_completion'] for g in gs)}/10",f"{sum(g['finishers'] for g in gs)/40:.3f}",f"{DATA['summary']['models'][m]['settled_S_mean']/1e6:.2f}"])
 tex_table('completion',['모델','네 명 완주','개인 완주 비율','정산 $S$ (백만)'],rows)


def distributions():
 fig,axs=plt.subplots(4,5,figsize=(13,8.5),sharex=True)
 for col,m in enumerate(MODELS):
  rows=PAY['models'][m]['trajectories']
  for j,(key,scale,label) in enumerate([('S',1e4,'Sen (만 토큰)'),('G',1,'Gini'),('mu',1e4,'평균 (만 토큰)'),('remaining',1,'잔류 인원')]):
   ax=axs[j,col];values=[]
   for g in rows:
    y=[np.nan if r[key] is None else r[key]/scale for r in g['rounds']];values.append(y)
    observed=[r['observed'] for r in g['rounds']];last=max(i for i,v in enumerate(observed) if v)
    ax.plot(range(last+1),y[:last+1],color=COLORS[col],alpha=.28,lw=.7)
    if last<8:ax.plot(range(last,9),y[last:],color=COLORS[col],alpha=.28,lw=.7,ls=':')
   ax.plot(range(9),np.nanmean(values,axis=0),color=COLORS[col],lw=2);ax.set(xticks=[0,2,4,6,8]);ax.grid(alpha=.15)
   if col==0:ax.set_ylabel(label)
   if j==0:ax.set_title(m+' (10판)')
   if j==3:ax.set_xlabel('라운드');ax.set_ylim(0,4.2)
 fig.tight_layout();save(fig,'resource_rounds_10games')
 fig,axs=plt.subplots(1,5,figsize=(14,3.5),sharey=True)
 for ax,m in zip(axs,MODELS):
  rows=PAY['models'][m]['trajectories']
  for balance,c in zip(['10000','20000','40000','60000'],['#845ec2','#008e9b','#d49000','#c34a36']):
   y=[np.mean([g['rounds'][r]['seat_balances'][balance] for g in rows if g['rounds'][r]['seat_balances'][balance] is not None])/1e4 if any(g['rounds'][r]['seat_balances'][balance] is not None for g in rows) else np.nan for r in range(9)]
   ax.plot(range(9),y,color=c,label=str(int(balance)//10000)+'만')
  total=[[v for g in rows for v in g['rounds'][r]['seat_balances'].values() if v is not None] for r in range(9)]
  ax.plot(range(9),[np.mean(v)/1e4 if v else np.nan for v in total],'k--',lw=1.8,label='전체 평균');ax.set(title=m,xticks=[0,2,4,6,8],xlabel='라운드');ax.grid(alpha=.15)
  ax.text(.02,-.32,'n: '+','.join(str(len(v)) for v in total),transform=ax.transAxes,fontsize=7)
 axs[0].set_ylabel('EXIT 제외 잔액 (만 토큰)');axs[-1].legend(fontsize=7);fig.tight_layout();save(fig,'preprize_trajectories_10games')
 rows=[]
 for m in MODELS:
  gs=PAY['models'][m]['ledgers']; valid=[g['pre_prize']['G'] for g in gs if g['pre_prize']['G'] is not None]
  rows.append([m,f"{sum(g['all4_completion'] for g in gs)}/10",f"{sum(g['finishers']>0 for g in gs)}/10",'/'.join(str(sum(g[k] for g in gs)) for k in ['finishers','exited','dead']),f"{np.mean([g['pre_prize']['mu'] for g in gs]):,.1f}",f'{np.mean(valid):.3f}',len(valid),f"{np.mean([g['pre_prize']['S'] for g in gs]):,.1f}",f"{np.mean([g['historic_settled']['S'] for g in gs]):,.1f}"])
 tex_table('preprize_distribution',['모델','네 명','한 명 이상','완주/EXIT/꺼짐',r'$\mu$',r'$G$',r'$n_G$',r'$S$',r'정산 $S$'],rows)


def exit_support():
 fig,axs=plt.subplots(2,5,figsize=(14,5.5),sharex=True)
 rows=[]
 for i,m in enumerate(MODELS):
  p=PAY['models'][m];es=p['exits'];s=p['exit_summary'];v=p['strategy'];axs[0,i].bar(range(1,9),s['round_counts'],color=COLORS[i]);axs[0,i].set(title=m,xticks=range(1,9))
  for j,e in enumerate(es):axs[1,i].scatter(e['round']+(j%5-2)*.045,e['slack'],marker='D' if e['prev']=='none' else 'o',facecolor='white' if e['prev']=='correct' else COLORS[i],edgecolor=COLORS[i],s=20)
  axs[1,i].axhspan(0,1,color='#eee');axs[1,i].axhline(1,color='.5',ls='--');axs[1,i].set(xlabel='EXIT 라운드',xticks=range(1,9))
  rows.append([m,f"{v['finishers']/10:.1f}",v['dead'],f"{len(es)}/40",'/'.join(str(v['receivers'].get(k,0)) for k in ['in','exited','dead']),s['first_round'],'/'.join(str(s['previous_result'][k]) for k in ['wrong','correct','none'])])
 axs[0,0].set_ylabel('EXIT 건수');axs[1,0].set_ylabel('응답 직전 잔액 / 벌금');fig.tight_layout();save(fig,'exit_timing_10games')
 tex_table('outcomes',['모델','판당 완주','꺼짐','EXIT','수혜자 끝 상태','첫 라운드','직전 오답/정답/없음'],rows)
 out={DATA['models'][m]:PAY['models'][m]['strategy'] for m in MODELS};order=list(out)
 (TAB/'cooperation.tex').write_text(strategy.cooperation_table(out,order));(TAB/'transfer_strategy.tex').write_text(strategy.table(out,order))
 fig,axs=plt.subplots(1,2,figsize=(10,3.5),sharey=True)
 for j,phase in enumerate(['prep','rescue']):
  amounts=[PAY['models'][m]['strategy'][phase]['amount']/1000 for m in MODELS]
  repayment=[sum(g['amount'] for g in PAY['models'][m]['strategy']['per_game'] for g in g['gifts'] if g['phase']==phase and g['repayment'])/1000 for m in MODELS]
  axs[j].barh(MODELS,amounts,color=COLORS,alpha=.7);axs[j].barh(MODELS,repayment,color='none',edgecolor='#333',hatch='///')
  for i,m in enumerate(MODELS):axs[j].text(amounts[i]+1,i,f"{amounts[i]:.1f} ({PAY['models'][m]['strategy'][phase]['n']}회)",va='center',fontsize=8)
  axs[j].set(title=['풀이 전','결과 뒤'][j],xlabel='총 이전량 (천 토큰)',xlim=(0,max(amounts)*1.3))
 axs[0].invert_yaxis();fig.tight_layout();save(fig,'transfer_timing_10games')


def sensitivity():
 prize=np.array([0,150000,300000,600000,1000000,5000000,20000000])
 fig,ax=plt.subplots(figsize=(8,3.7));values={}
 for m,c in zip(MODELS,COLORS):
  vv=[]
  for total in prize:
   vv.append(np.mean([distribution([v['pre_prize']+(total/g['finishers'] if v['status']=='finished' else 0) for v in g['seats'].values()])['S'] for g in PAY['models'][m]['ledgers']]))
  values[m]=vv;ax.plot(range(len(prize)),np.array(vv)/1e6,'o-',label=m,color=c)
 ax.set(xticks=range(len(prize)),xticklabels=['0','15만','30만','60만','100만','500만','2,000만'],xlabel='최종 상금 총액 (토큰)',ylabel='정산 Sen 지수 (백만 토큰)');ax.legend();ax.grid(alpha=.2);save(fig,'prize_sensitivity_10games');PAY['sensitivity']={'prize_total':prize.tolist(),'mean_settled_S':values}

if __name__=='__main__':
 build();scatter_gifts();completion();distributions();exit_support();sensitivity()
 (ROOT/'results/appendix_refresh_c_h_20261107.json').write_text(json.dumps(PAY,ensure_ascii=False,indent=1))
 print({m:{'give':len(p['gifts']),'ask':len(p['asks']),'rho':p['rho'],'exit':len(p['exits'])} for m,p in PAY['models'].items()})
