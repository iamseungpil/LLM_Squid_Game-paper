"""Plot the existing model rho numerator/denominator centroids, GIVE only."""
import json
import math
import random
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import fig3_completion_20261028 as base

ROOT=base.ROOT

def main():
    games,agents,solves,sources,med=base.load()
    current=json.loads((ROOT/'results/feedback_20261028.json').read_text())
    rows=[]
    for model in base.MODELS:
        gg=sorted([g for g in games if g['model']==model],key=lambda g:g['seed'])
        v=current['models'][model]
        point=[v['weighted_giver_margin'],v['weighted_taker_margin']]
        gifts=[g for game in gg for g in game['gifts']]
        recomputed=base.fb.revised_rho(gifts)
        assert point==[recomputed['weighted_giver_margin'],recomputed['weighted_taker_margin']]
        assert math.isclose(point[0]/point[1],v['rho'])
        rng=random.Random(1919);boots=[]
        for _ in range(2000):
            pick=[gift for _ in gg for gift in rng.choice(gg)['gifts']]
            stats=base.fb.revised_rho(pick)
            if stats['weighted_giver_margin'] is not None:
                boots.append([stats['weighted_giver_margin'],stats['weighted_taker_margin']])
        ci=np.quantile(np.array(boots),[.025,.975],axis=0).T.tolist()
        rows.append(dict(model=model,centroid=point,rho=v['rho'],ci95=ci,n_give=len(gifts),valid_boot=len(boots)))
    assert sum(r['n_give'] for r in rows)==130
    font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
    plt.rcParams.update({'font.family':'NanumGothic','font.size':8,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(3.35,3.25));fig.subplots_adjust(left=.17,right=.97,bottom=.16,top=.97)
    lo=min(0,math.floor(min(v for r in rows for ci in r['ci95'] for v in ci)))
    hi=math.ceil(max(v for r in rows for ci in r['ci95'] for v in ci)+.4)
    ax.axvspan(lo,1,color='#eeeeee');ax.axhspan(lo,1,color='#eeeeee');ax.plot([lo,hi],[lo,hi],ls='--',color='#999999',lw=.7)
    for r,c,mk in zip(rows,base.COLORS,base.MARKERS):
        x,y=r['centroid'];(xl,xh),(yl,yh)=r['ci95']
        ax.plot([xl,xh],[y,y],color=c,lw=1.4,alpha=.8);ax.plot([x,x],[yl,yh],color=c,lw=1.4,alpha=.8)
        ax.plot(x,y,marker=mk,color=c,ms=5,ls='',mec='white',mew=.5,label=rf"{r['model']} ($\rho$={r['rho']:.2f})",zorder=4)
    ax.set(xlim=(lo,hi),ylim=(lo,4),xlabel='준 쪽의 가중 평균 생존 여유',ylabel='받은 쪽의 가중 평균 생존 여유')
    ax.set_aspect('equal',adjustable='box');ax.legend(loc='upper left',frameon=False,fontsize=6.8,handletextpad=.4)
    for ext in ['pdf','png']:fig.savefig(ROOT/f'ko/figures/arena_centroids_current.{ext}',dpi=240,bbox_inches='tight')
    plt.close(fig)
    (ROOT/'results/arena_centroids_current.json').write_text(json.dumps(dict(models=rows,sources=sources,
        definition='Existing model centroids from feedback_20261028, verified against current raw-derived completed GIVE only. x=amount-weighted giver L, y=amount-weighted taker L; rho=x/y. ASK excluded.',
        uncertainty='2000 whole-game bootstrap draws, seed1919, coordinatewise percentile95%; draws with no GIVE excluded; five games/model.'),ensure_ascii=False,indent=2)+'\n')
    print('130 completed GIVEs; all five existing model rho and centroids preserved exactly.')
if __name__=='__main__':main()
