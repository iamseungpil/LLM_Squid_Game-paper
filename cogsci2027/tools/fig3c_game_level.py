"""Game-level version of main Figure3(c), retaining no-GIVE games explicitly."""
import json
import sys
from pathlib import Path
import numpy as np
import fig3_completion_20261028 as base
ROOT=base.ROOT

def main():
    games,agents,solves,sources,med=base.load()
    for g in games:g['all_four']=int(g['finishers']==4)
    metrics=[('all_four','전원 완주 여부',1),('goal','떠나지 않은 응답 (%)',100),('given','건넨 토큰 (천)',.001)]
    sums={m:{k:base.summary([g for g in games if g['model']==m],k) for k,_,_ in metrics} for m in base.MODELS}
    sys.path.insert(0,str(base.fb.OLD/'figs'))
    import paper_style as ps
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    ps.use()
    from matplotlib import font_manager
    font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
    plt.rcParams['font.family']='NanumGothic'
    fig,axes=plt.subplots(2,3,figsize=(7.2,5.5))
    fig.subplots_adjust(left=.09,right=.98,bottom=.14,top=.90,hspace=.75,wspace=.42)
    for j,(key,label,scale) in enumerate(metrics):
        ax=axes[0,j]
        ax.axvspan(-2,-.4,color='#eeeeee',zorder=0);ax.axvline(-.4,color='#aaaaaa',lw=.6)
        for mi,m in enumerate(base.MODELS):
            for g in [v for v in games if v['model']==m]:
                x=g['rho'] if g['rho'] is not None else -1.2+(mi-2)*.13+(g['seed']-4103)*.035
                y=g[key]*scale
                if key=='all_four':y+=(mi-2)*.012+(g['seed']-4103)*.003
                ax.scatter(x,y,color=base.COLORS[mi],marker=base.MARKERS[mi],s=22,alpha=.8,edgecolors='white',linewidths=.25,zorder=3)
        ax.set(xlim=(-2,11),xticks=[-1.2,2,6,10],xticklabels=['GIVE 없음','2','6','10'],xlabel='판별 ρ (왼쪽 띠는 미정)',ylabel=label)
        ax.set_title(f'({chr(97+j)}) 판별 {label}',fontsize=8)
        ax.tick_params(axis='x',labelsize=6)
        if key=='all_four':ax.set(ylim=(-.1,1.1),yticks=[0,1])
        else:ax.set_ylim(bottom=0)
        ax.grid(axis='y',alpha=.4)
        bx=axes[1,j]
        for mi,m in enumerate(base.MODELS):
            gg=[g for g in games if g['model']==m]
            bx.scatter([mi+(g['seed']-4103)*.055 for g in gg],[g[key]*scale for g in gg],s=14,alpha=.55,color=base.COLORS[mi],marker=base.MARKERS[mi])
            s=sums[m][key];val=s['value']*scale;ci=s['ci95']
            if ci[0] is not None:
                lo,hi=np.array(ci)*scale
                bx.plot([mi,mi],[lo,hi],color='#222',lw=1)
                bx.plot([mi-.06,mi+.06],[lo,lo],color='#222',lw=.8);bx.plot([mi-.06,mi+.06],[hi,hi],color='#222',lw=.8)
            bx.plot(mi,val,'D',ms=4,color='#222',mfc='#222' if ci[0] is not None else 'white',zorder=5)
        bx.set(xticks=range(5),xticklabels=base.MODELS,xlim=(-.5,4.5),ylabel=label,xlabel='모델별 5판 (GIVE 없는 판 포함)')
        bx.tick_params(axis='x',labelsize=6,rotation=25);bx.set_title(f'({chr(100+j)}) 모델별 평균·95% 구간',fontsize=8)
        if key=='all_four':bx.set(ylim=(-.07,1.07),yticks=[0,.5,1])
        else:bx.set_ylim(bottom=0)
        bx.grid(axis='y',alpha=.4)
    handles=[Line2D([],[],ls='',marker=mk,color=c,label=m,ms=4) for m,c,mk in zip(base.MODELS,base.COLORS,base.MARKERS)]
    fig.legend(handles=handles,loc='upper center',ncol=5,fontsize=7,frameon=False)
    ps.save(fig,str(ROOT/'ko/figures/fig3c_game_level'));plt.close(fig)
    payload=dict(n_games=len(games),rho_defined=sum(g['rho'] is not None for g in games),no_give=sum(g['rho'] is None for g in games),
        games=[{k:g[k] for k in ['model','seed','rho','all_four','goal','given']} for g in games],summary=sums,sources=sources,
        definitions=dict(upper='Every game once per panel; undefined rho in nonnumeric no-GIVE strip, never zero. All-four vertical jitter is display-only.',
          lower='Each model all5 games; arithmetic means,5000 paired-seed bootstrap as base.summary; hollow diamonds when percentile interval zero-width; no claim population certainty.',
          goal='Non-EXIT prep replies among recorded eligible non-solver replies with >=2 agents at round start; not independent of completion.' ))
    (ROOT/'results/fig3c_game_level.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    assert len(games)==25 and payload['rho_defined']==18 and payload['no_give']==7
    assert all(sums[m]['all_four']['n']==5 for m in base.MODELS)
    print('25 games each panel;18 defined rho +7 no-GIVE; five games per model mean.')
if __name__=='__main__':main()
