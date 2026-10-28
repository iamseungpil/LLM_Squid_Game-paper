"""All-four completion outcomes from the verified 25-game cohort; no model calls."""
import json
import sys
from pathlib import Path
import numpy as np
import fig3_completion_20261028 as base

ROOT = base.ROOT
MODELS = ['Astra', 'Fable', 'Sol', 'Opus', 'Luna']

def main():
    games, agents, solves, sources, med = base.load()
    rows = []
    for model in MODELS:
        gg = [g for g in games if g['model'] == model]
        counts = [g['finishers'] for g in gg]
        for g in gg:
            assert g['finishers'] == sum(a['status'] == 'finished' for a in g['seats'].values())
            assert g['all4_completion'] == (g['finishers'] == 4)
            assert not g['all4_completion'] or (g['rounds_played'] == 8 and g['exited'] == g['dead'] == 0)
        rows.append(dict(model=model, n=len(gg), by_seed={str(g['seed']):g['finishers'] for g in gg},
                         all_four=sum(k==4 for k in counts), clear=sum(k>=1 for k in counts),
                         completion_fraction=sum(counts)/(4*len(gg)),
                         pair_completion=np.mean([k*(k-1)/12 for k in counts]),
                         threshold_profile=[sum(k>=q for k in counts)/len(gg) for q in range(1,5)],
                         sen=np.mean([g['historic_settled']['S'] for g in gg])))
    assert [r['all_four'] for r in rows] == [3,2,2,1,0]
    assert sum(r['all_four'] for r in rows)==8
    groups={}
    for success in (True,False):
        gg=[g for g in games if g['all4_completion']==success]
        groups[str(success)]=dict(n=len(gg), accuracy=np.mean([g['accuracy'] for g in gg]),
            given=np.mean([g['given'] for g in gg]), goal=np.mean([g['goal'] for g in gg]),
            model_rho=np.mean([g['model_rho'] for g in gg]),
            no_give=sum(g['n_give']==0 for g in gg))
    out=ROOT/'results/all_four_completion.json'
    out.write_text(json.dumps(dict(models=rows,groups=groups,sources=sources,
        definition='All four original seats finish round 8; EXIT is not completion. Equal game weighting. Observed outcomes, not causal/necessary cooperation.',
        existing_evidence=['fb28:table: model all-four counts', 'fig:completion28-games: 0-4 finisher bins', 'fig:completion28-rho: per-game rho vs finishers']),ensure_ascii=False,indent=2)+'\n')
    tex=[]
    percent = chr(92) + '%'
    for r in rows:
        cells = [r['model'], f"{r['all_four']}/{r['n']}",
                 f"{100*r['all_four']/r['n']:.0f}" + percent,
                 f"{r['clear']}/{r['n']}", f"{100*r['completion_fraction']:.0f}" + percent,
                 f"{100*r['pair_completion']:.1f}" + percent, f"{r['sen']/1e6:.2f}"]
        tex.append(' & '.join(cells) + ' ' + chr(92)*2)
    (ROOT/'ko/tables/all_four_completion_rows.tex').write_text('\n'.join(tex)+'\n')
    (ROOT/'ko/tables/all_four_completion_summary.tex').write_text('\\begin{tabular}{@{}lrrrrrr@{}}\n\\toprule\n모델 & 네 명 완주 & 네 명 완주(\\%) & 한 명 이상 & 개인 완주(\\%) & 쌍 완주(\\%) & Sen \\\\\n\\midrule\n' + '\n'.join(tex)+'\n' + '\\bottomrule\n\\end{tabular}\n')
    sys.path.insert(0,str(base.fb.OLD/'figs'))
    import paper_style as ps
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    ps.use()
    fig,(ax,bx)=plt.subplots(1,2,figsize=(7,2.5),gridspec_kw={'width_ratios':[1.5,1]})
    fig.subplots_adjust(left=.09,right=.97,bottom=.2,top=.84,wspace=.45)
    matrix=np.array([[r['by_seed'][str(seed)] for seed in base.fb.SEEDS] for r in rows])
    colors=['#eeeeee','#d6e4ed','#a8c9db','#6b9eb9','#236782']
    ax.imshow(matrix,cmap=ListedColormap(colors),norm=BoundaryNorm(np.arange(-.5,5),5),aspect='auto')
    for i in range(5):
        for j in range(5):
            k=matrix[i,j]; ax.text(j,i,str(k),ha='center',va='center',color='white' if k==4 else '#222222',fontsize=10,fontweight='bold' if k==4 else 'normal')
    ax.set(xticks=range(5),xticklabels=base.fb.SEEDS,yticks=range(5),yticklabels=MODELS,xlabel='시드')
    ax.set_title('(a) 각 판의 완주자 수 (0–4명)')
    yy=np.arange(5); rates=[100*r['all_four']/r['n'] for r in rows]
    bx.barh(yy,rates,color='#236782',height=.6)
    bx.set(yticks=yy,yticklabels=MODELS,xlim=(0,100),xticks=[0,20,40,60,80,100],xlabel='네 명 완주율 (%)')
    bx.invert_yaxis(); bx.set_title('(b) 네 명 모두 완주한 판')
    for i,r in enumerate(rows):bx.text(rates[i]+2,i,f"{r['all_four']}/{r['n']}",va='center',fontsize=9)
    ps.save(fig,str(ROOT/'ko/figures/all_four_completion'));plt.close(fig)
    print(json.dumps(dict(models=rows,groups=groups),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
