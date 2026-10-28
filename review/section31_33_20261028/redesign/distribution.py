"""Separate pre-final-prize mean and Gini graphs for the requested appendix."""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import font_manager

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DATA=json.loads((HERE.parent/'analysis.json').read_text())
MODELS=['Fable','Astra','Sol','Opus','Luna']
MARKERS=['o','s','^','D','v']
font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
plt.rcParams.update({'font.family':'NanumGothic','font.size':9,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
FIG=ROOT/'cogsci2027/ko/figures'
records={}
for key,name,title,unit in [('mu','appendix_preprize_mean','최종 상금 제외 평균 토큰','평균 토큰 (천)'),('G','appendix_preprize_gini','최종 상금 제외 지니 계수','지니 계수 (고정 네 자리)')]:
    fig,ax=plt.subplots(figsize=(6.5,3.7));fig.subplots_adjust(left=.14,right=.96,top=.87,bottom=.32)
    rng=np.random.default_rng(20261028);records[key]={}
    for i,m in enumerate(MODELS):
        gs=[g for g in DATA['games'] if g['model']==m]
        vals=[g['pre_prize'][key] for g in gs if g['pre_prize'][key] is not None]
        a=np.array(vals);boot=a[rng.integers(0,len(a),(10000,len(a)))].mean(axis=1)
        lo,hi=np.quantile(boot,[.025,.975]);mean=a.mean();scale=.001 if key=='mu' else 1
        records[key][m]={'n':len(a),'mean':float(mean),'ci95':[float(lo),float(hi)],'per_game':[{'seed':g['seed'],'value':g['pre_prize'][key]} for g in gs]}
        for g in gs:
            v=g['pre_prize'][key]
            if v is not None:ax.scatter(v*scale,i+(g['seed']-4103)*.07,marker=MARKERS[g['seed']-4101],color='#4f87a0',s=33,zorder=3)
        ax.errorbar(mean*scale,i,xerr=np.array([[mean-lo],[hi-mean]])*scale,fmt='o',color='#222',ms=5,capsize=3,lw=1.3,zorder=4)
        ax.text(.98,i,f'n={len(a)}',transform=ax.get_yaxis_transform(),ha='right',va='center',fontsize=8,color='#555')
    ax.set(yticks=range(5),yticklabels=MODELS,xlabel=unit,xlim=(-1,45) if key=='mu' else (-.02,.78))
    ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.set_title(title,loc='left',fontsize=12)
    handles=[Line2D([],[],ls='',marker=mk,color='#4f87a0',label=str(s)) for mk,s in zip(MARKERS,range(4101,4106))]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.11),ncol=5,fontsize=8,frameon=False)
    fig.text(.14,.025,'검정 점·선: 모델 평균과 판 재표집 95% 구간. EXIT 보너스 유지.',fontsize=8)
    if key=='G':fig.text(.14,.065,'Opus 4103: 네 자리 모두 0 → Gini 미정(평균에서 제외).',fontsize=8)
    for suffix in ['pdf','png']:
        fig.savefig(FIG/f'{name}.{suffix}',dpi=220,bbox_inches='tight')
        fig.savefig(HERE/f'{name}.{suffix}',dpi=220,bbox_inches='tight')
    plt.close(fig)
records['definitions']={'cohort':'25 frozen v33 games, seeds4101–4105','balance':'fixed four seats: dead0, EXIT raw final including20k exit bonus, finishers raw final before20m end-pool prize',
    'mean':'mean of four fixed seats, then arithmetic mean over all5 games; all-zero game retained',
    'Gini':'sum_ij abs(bi-bj)/(2*4*sum(b)), no n/(n-1) correction. All-zero = NA; Opus n4, others n5. Model mean of game Ginis, not pooled seats.',
    'CI':'within-model nonparametric game bootstrap10000 draws, percentile95; Gini conditional on defined games; five or four observed games only.'}
records['input_sha256']=hashlib.sha256((HERE.parent/'analysis.json').read_bytes()).hexdigest()
(HERE/'distribution.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(json.dumps({k:{m:records[k][m]['mean'] for m in MODELS} for k in ['mu','G']},indent=2))
