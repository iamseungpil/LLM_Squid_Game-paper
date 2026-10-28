"""Figure 4: game-level rho versus behavior and settled resource distribution."""
import json
import sys
from pathlib import Path
import numpy as np
import fig3_completion_20261028 as source
from completion_life_buffer import association
from inequality import distribution

ROOT = source.ROOT
KEYS = ('accuracy', 'goal', 'given_per_agent_round', 'mu', 'G', 'S')

def main():
    games, _, _, sources, _ = source.load()
    for g in games:
        values = [v['settled'] for v in g['seats'].values()]
        d = distribution(values)
        assert d == g['historic_settled']
        g.update(d)
        if d['G'] is not None:
            assert np.isclose(d['S'], d['mu'] * (1-d['G']))
    fits = {k: association(games, 'rho', k) for k in KEYS}
    sensitivity = {}
    for k in ('mu','G','S'):
        rows = [dict(g, **{k:g['pre_prize'][k]}) for g in games]
        sensitivity[k] = association(rows, 'rho', k)
    leave_model_out = {k:{m:association([g for g in games if g['model'] != m], 'rho', k)['pearson_r']
                         for m in source.MODELS} for k in KEYS}
    data = dict(definitions=dict(unit='One game, equal weight; same 25-game cohort.',
        rho='Amount-weighted post-GIVE giver margin / receiver margin; seven no-GIVE games undefined.',
        goal='Non-EXIT / eligible pre-solve TALK responses (non-solver, at least two participants); not an inner motive.',
        resources='Four original seats; shutdown=0; EXIT includes 20000 bonus; finish includes allocated prize. Normalized Gini. All-zero: G undefined, mu=S=0.',
        uncertainty='5000 paired-seed percentile bootstrap, only five seed blocks; exploratory, unadjusted for multiple comparisons.',
        sensitivity='Remove final winner prize only; retain EXIT bonuses; descriptive alternative, not a treatment effect.'),
        analysis_inputs=[dict(path=str(p), sha256=source.fb.sha(p.read_bytes())) for p in
            (Path(__file__), Path(source.__file__), ROOT/'tools/feedback_20261028.py',
             ROOT/'tools/completion_life_buffer.py', ROOT/'tools/inequality.py')],
        sources=sources, games=games, associations=fits, pre_prize_sensitivity=sensitivity,
        leave_model_out=leave_model_out)
    (ROOT/'results/section32_metrics.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    sys.path.insert(0,str(source.fb.OLD/'figs'))
    import paper_style as ps
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    ps.use()
    fig, axes = plt.subplots(2,3,figsize=(7,4.5))
    fig.subplots_adjust(left=.075,right=.985,bottom=.19,top=.93,wspace=.44,hspace=.85)
    titles = ['(a) 추론: 정답률','(b) 목표 지속: 비이탈 응답','(c) 협력: 이전량',r'(d) 평균 토큰: $\mu$',r'(e) 불균등: Gini $G$',r'(f) 자원 분포: Sen $S$']
    labels = ['정답 / 실제 풀이 (%)','비이탈 / 이탈 가능 응답 (%)','GIVE / 참여\n에이전트·라운드','평균 정산 토큰 (백만)','Gini (0–1)','Sen (백만 토큰)']
    scales = [100,100,1,1e-6,1,1e-6]
    for ax,key,title,ylabel,scale in zip(axes.flat,KEYS,titles,labels,scales):
        for mi,m in enumerate(source.MODELS):
            rows=[g for g in games if g['model']==m and g['rho'] is not None and g[key] is not None]
            ax.scatter([g['rho'] for g in rows],[g[key]*scale for g in rows],s=20,
                color=source.COLORS[mi],marker=source.MARKERS[mi],alpha=.8,edgecolors='white',linewidths=.3,zorder=3)
        fit=fits[key]; x=np.array([min(g['rho'] for g in games if g['rho'] is not None),max(g['rho'] for g in games if g['rho'] is not None)])
        ax.plot(x,(fit['intercept']+fit['beta']*x)*scale,'--',color='#777777',lw=.9)
        ax.set(xlim=(0,11),xticks=[0,2,4,6,8,10],ylabel=ylabel)
        ax.set_title(title,fontsize=8)
        if key in ('accuracy','goal'): ax.set_ylim(0,105); ax.set_yticks([0,50,100])
        elif key=='G':ax.set_ylim(-.03,1.05);ax.set_yticks([0,.5,1])
        else:ax.set_ylim(bottom=-.15 if key in ('mu','S') else 0)
        lo,hi=fit['ci95']['pearson_r']
        ax.text(.5,-.25,rf"$r$={fit['pearson_r']:+.2f} [{lo:+.2f}, {hi:+.2f}] · n={fit['n']}",transform=ax.transAxes,ha='center',fontsize=6.2)
        ax.grid(axis='y',alpha=.6)
    fig.text(.53,.09,r'판별 자기 보존 행동 $\rho$ (준 쪽 / 받은 쪽의 가중 평균 여유)',ha='center',fontsize=8)
    handles=[Line2D([],[],color=c,marker=m,ls='',label=n,markersize=4) for n,c,m in zip(source.MODELS,source.COLORS,source.MARKERS)]
    fig.legend(handles=handles,loc='lower center',ncol=5,fontsize=7)
    ps.save(fig,str(ROOT/'ko/figures/fig4_section32_metrics'))
    for k,f in fits.items():print(k,f['n'],round(f['pearson_r'],4),f['ci95']['pearson_r'])
    print('sensitivity', {k:round(f['pearson_r'],4) for k,f in sensitivity.items()})
    print('leave model out',leave_model_out)

if __name__=='__main__':main()
