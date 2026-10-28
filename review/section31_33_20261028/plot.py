"""Produce candidate figures; all values come from analysis.json."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'analysis.json').read_text())
MODELS=list(D['models'])
COLORS=dict(zip(MODELS,['#256b8c','#478c57','#a27822','#b05a71','#7263a3']))
MARKERS=dict(zip(MODELS,['o','s','^','D','v']))
ALIASES=dict(zip(MODELS,['C','A','E','B','D']))
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})

def save(fig,name,blind):
    directory=OUT/('blind_r1' if blind else 'draft_r1')
    directory.mkdir(exist_ok=True)
    for ext in ['png','pdf']:
        fig.savefig(directory/f'{name}.{ext}',dpi=190,bbox_inches='tight')
    plt.close(fig)

def relation(blind=False):
    label=lambda m:ALIASES[m] if blind else m
    fig,axs=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    ax=axs.flat[0]
    for i,m in enumerate(MODELS):
        v=D['models'][m];left=0
        for k,c in [('finishers','#397e91'),('exited','#d5af68'),('dead','#a9adb4')]:
            ax.barh(i,v[k],left=left,color=c,height=.64)
            if v[k]: ax.text(left+v[k]/2,i,str(v[k]),ha='center',va='center')
            left+=v[k]
    ax.set(yticks=range(5),yticklabels=[label(m) for m in MODELS],xlim=(0,20),xlabel='Seats (20 per model)')
    ax.invert_yaxis();ax.set_title('(a) Finished / EXIT / dead',loc='left')
    for ax,key,title,xlab in zip(axs.flat[1:],['rho','accuracy','early_talk_per_response','given','giving_rate'],
        ['Self-preservation','Observed task accuracy','Early TALK cost','Gross transfers','Giving responses'],
        ['Unchanged rho (receiver / giver)','Correct / attempted SOLVE (%)','Tokens per TALK response, rounds 1-2','Tokens transferred (thousands)','Responses with GIVE / TALK (%)']):
        scale=100 if key in ['accuracy','giving_rate'] else .001 if key=='given' else 1
        for mi,m in enumerate(MODELS):
            gs=[g for g in D['games'] if g['model']==m and g[key] is not None]
            jitter=(mi-2)*.035
            ax.scatter([g[key]*scale for g in gs],[g['finishers']+jitter for g in gs],color=COLORS[m],marker=MARKERS[m],s=45,label=label(m),alpha=.85)
        a=next(a for a in D['associations'] if a['metric']==key)
        lo,hi=a['ci95']
        ax.set_title(f'{title}\nr_s={a["spearman"]:+.2f} [{lo:+.2f}, {hi:+.2f}], n={a["n"]}',loc='left',fontsize=10)
        ax.set(xlabel=xlab,ylabel='Finishers at round 8',yticks=range(5),ylim=(-.25,4.3))
        ax.grid(alpha=.15)
    fig.legend(handles=[Line2D([],[],color=COLORS[m],marker=MARKERS[m],ls='',label=label(m)) for m in MODELS],loc='outside lower center',ncol=5,frameon=False)
    fig.suptitle('Coexistence outcomes and observed behavior | 25 games, five paired seeds',fontsize=13)
    fig.text(.5,-.025,'Small points = games; vertical offsets only for display. Brackets = paired-seed bootstrap 95% intervals.\nRho undefined in 7 no-GIVE games; omitted from its panel. Associations are exploratory, not causal.',ha='center',fontsize=8)
    save(fig,'candidate_P',blind)

def behavior(blind=False):
    label=lambda m:ALIASES[m] if blind else m
    fig,axs=plt.subplots(2,2,figsize=(11,7.3),layout='constrained')
    ax=axs[0,0]
    for i,m in enumerate(MODELS):
        v=D['models'][m];n=v['gifts'];k=v['prep_gifts']
        ax.barh(i,k/n*100,color=COLORS[m],height=.6)
        ax.text(k/n*100+2,i,f'{k}/{n}',va='center')
    ax.set(yticks=range(5),yticklabels=[label(m) for m in MODELS],xlim=(0,100),xlabel='Completed GIVE before result (%)')
    ax.invert_yaxis();ax.set_title('(a) Timing differs by model',loc='left')
    ax=axs[0,1]
    for mi,m in enumerate(MODELS):
        ts=[t for t in D['talks'] if t['model']==m and t['exit_eligible']]
        yy=[]
        for lo,hi in [(0,1),(1,2),(2,1e10)]:
            rr=[t for t in ts if lo<=t['slack']<hi];yy.append(sum(t['exit'] for t in rr)/len(rr)*100 if rr else np.nan)
        ax.plot(range(3),yy,marker=MARKERS[m],color=COLORS[m],label=label(m))
    ax.set(xticks=range(3),xticklabels=['<1','1-2','>=2'],ylabel='EXIT / eligible prep responses (%)',xlabel='Balance / per-agent fine before response')
    ax.set_title('(b) EXIT concentrates near the fine boundary',loc='left')
    for ax,seed in zip(axs[1], [4102,4103]):
        g=next(g for g in D['gifts'] if g['model']=='Opus' and g['seed']==seed and g['giver_after']==0)
        for i,role in enumerate(['giver','taker']):
            before=g[role+'_before'];after=g[role+'_after']
            ax.plot([0,1],[before,after],marker='o',lw=2,color=['#b05a71','#256b8c'][i],label=role)
            for x,y in [(0,before),(1,after)]: ax.annotate(f'{y:,}',(x,y),xytext=(6,5 if i else -14),textcoords='offset points',fontsize=9)
        ax.axhline(g['due'],color='#666',ls='--');ax.text(.03,g['due']+600,f'Pending fine {int(g["due"]):,}',fontsize=9)
        ax.set(xticks=[0,1],xticklabels=['Before GIVE','Immediately after'],xlim=(-.1,1.4),ylim=(-1000,22000),ylabel='Tokens')
        outcome='Recipient above fine; donor already below' if seed==4102 else 'Recipient still 471 below fine; both die'
        ax.set_title(f'{label("Opus")} · seed {seed} · round {g["round"]}\n{outcome}',loc='left',fontsize=10)
        ax.legend(frameon=False,fontsize=8)
    fig.suptitle('Similar acts can have different local consequences',fontsize=13)
    fig.text(.5,-.025,'Two cases are all observed full-balance GIVE events, selected by that rule. Immediate accounting is not a causal survival estimate.\nTiming uses transfer events; EXIT uses repeated eligible responses. Models each have only five games.',ha='center',fontsize=8)
    save(fig,'candidate_Q',blind)

if __name__=='__main__':
    for b in [False,True]:relation(b);behavior(b)
