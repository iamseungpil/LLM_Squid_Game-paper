"""Actual stay decision windows and final completion in public v33 50 games.
Source: hash-verified cohort_public_20261105 and raw v33 sessions. Repeated
agent-round observations are descriptive, not counterfactual EXIT outcomes.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
import appendix_refresh_c_h_20261107 as b
rows=[]
for c in b.CASES:
 g=b.GAMES[c['model'],c['seed']]
 for w in g['process']['windows']:
  rows.append(dict(w,model=c['model'],seed=c['seed'],final=c['result']['agents'][w['agent']]['status']))
by=[]
for band in range(4):
 selected=[r for r in rows if r['band']==band and not r['exited']]
 by.append(dict(band=band,n=len(selected),finished=sum(r['final']=='in' for r in selected),exited=sum(r['exited'] for r in rows if r['band']==band)))
fig,ax=plt.subplots(figsize=(6.3,3.6))
for i,v in enumerate(by):
 p=v['finished']/v['n'];ax.bar(i,100*p,color='#9CC0E0');ax.text(i,100*p+2,f"{v['finished']}/{v['n']}",ha='center',fontsize=9)
ax.set(xticks=range(4),xticklabels=[f"{lab}\n(EXIT {v['exited']})" for lab,v in zip(['<1','1–2','2–4','≥4'],by)],ylabel='남은 결정 창의 최종 완주 비율 (%)',xlabel='결정 창 시작의 생존 여유',ylim=(0,100));ax.grid(axis='y',alpha=.2);fig.tight_layout();b.save(fig,'stay_window_completion_10games')
(b.ROOT/'results/appendix_exit_followup_20261107.json').write_text(json.dumps({'n_windows':len(rows),'n_stay_windows':sum(v['n'] for v in by),'bands':by},indent=2))
print(by)
