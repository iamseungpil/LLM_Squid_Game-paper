"""Second figure design, incorporating blind review and independent raw audit."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.gridspec import GridSpecFromSubplotSpec

OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'analysis.json').read_text())
RAW=json.loads((OUT/'raw_case_index.json').read_text())
MODELS=['Astra','Fable','Luna','Opus','Sol']
COLORS={'Fable':'#256b8c','Astra':'#478c57','Sol':'#a27822','Opus':'#b05a71','Luna':'#7263a3'}
MARKERS={'Fable':'o','Astra':'s','Sol':'^','Opus':'D','Luna':'v'}
ALIASES={'Fable':'C','Astra':'A','Sol':'E','Opus':'B','Luna':'D'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})


def save(fig,name,blind):
    folder=OUT/('blind_r2' if blind else 'final')
    folder.mkdir(exist_ok=True)
    for ext in ['png','pdf']:
        fig.savefig(folder/f'{name}.{ext}',dpi=210,bbox_inches='tight',facecolor='white')
    plt.close(fig)


def legend(fig,label,y):
    fig.legend(handles=[Line2D([],[],color=COLORS[m],marker=MARKERS[m],ls='',label=label(m)) for m in MODELS],
               loc='upper center',bbox_to_anchor=(.5,y),ncol=5,frameon=False)


def relation(blind=False):
    label=lambda m:ALIASES[m] if blind else m
    fig=plt.figure(figsize=(13.6,8.6))
    grid=fig.add_gridspec(2,3,left=.06,right=.985,bottom=.22,top=.84,hspace=.62,wspace=.4)
    ax=fig.add_subplot(grid[0,0])
    outcome_colors=['#303030','#b3b3b3','#ffffff']
    hatches=['','','////']
    for i,m in enumerate(MODELS):
        v=D['models'][m];left=0
        for j,k in enumerate(['finishers','exited','dead']):
            ax.barh(i,v[k],left=left,color=outcome_colors[j],hatch=hatches[j],edgecolor='#444',linewidth=.5,height=.6)
            if v[k]:ax.text(left+v[k]/2,i,str(v[k]),ha='center',va='center',color='white' if j==0 else 'black',fontsize=9)
            left+=v[k]
    ax.set(yticks=range(5),yticklabels=[label(m) for m in MODELS],xlim=(0,20),xticks=[0,5,10,15,20],xlabel='Observed seats: 20 per model in 5 games')
    ax.invert_yaxis();ax.set_title('(a) Distinct end states',loc='left',fontsize=11)
    ax.legend(handles=[Patch(facecolor=c,edgecolor='#444',hatch=h,label=l) for c,h,l in zip(outcome_colors,hatches,['Finished','EXIT (alive)','Dead'])],
              loc='upper center',bbox_to_anchor=(.5,-.26),ncol=3,fontsize=8,frameon=False,handlelength=1)
    specs=[('accuracy','(b) Observed SOLVE accuracy','Correct / attempted SOLVE (%)',100),
           ('early_talk_per_response','(c) Early TALK cost','Tokens per TALK response, rounds 1-2',1),
           ('rho','(d) Post-GIVE margin ratio',r'$\rho=\Sigma w\,m_{receiver}\,/\,\Sigma w\,m_{giver}$',1),
           ('given','(e) Gross transfers','Transferred tokens (thousands)',.001),
           ('giving_rate','(f) Giving-response frequency','TALK responses with GIVE / all TALK (%)',100)]
    for index,(key,title,xlab,scale) in enumerate(specs,1):
        slot=grid[index//3,index%3]
        if key=='rho':
            sub=GridSpecFromSubplotSpec(1,2,subplot_spec=slot,width_ratios=[4,1],wspace=.16)
            ax=fig.add_subplot(sub[0]);na=fig.add_subplot(sub[1],sharey=ax)
            na.set_facecolor('#f2f2f2');na.set(xticks=[],xlabel='No GIVE\n7 games',xlim=(-.2,4.2),yticks=range(5));na.tick_params(labelleft=False)
        else:ax=fig.add_subplot(slot)
        for mi,m in enumerate(MODELS):
            for g in [g for g in D['games'] if g['model']==m]:
                y=g['finishers']+(mi-2)*.035+(g['seed']-4103)*.018
                target=na if key=='rho' and g[key] is None else ax
                x=mi if g[key] is None else g[key]*scale
                target.scatter(x,y,color=COLORS[m],marker=MARKERS[m],s=43,edgecolor='white',linewidth=.3,zorder=3)
        a=next(a for a in D['associations'] if a['metric']==key);lo,hi=a['ci95']
        ax.set_title(f'{title}\nPooled r_s={a["spearman"]:+.2f} [{lo:+.2f}, {hi:+.2f}], n={a["n"]}',loc='left',fontsize=10,pad=10)
        ax.set(xlabel=xlab,ylabel='Finishers at round 8 (0-4)',yticks=range(5),ylim=(-.22,4.22))
        ax.grid(alpha=.16)
        if key=='rho':
            ax.text(0,-.32,'Lower rho = donor retains more relative margin',transform=ax.transAxes,fontsize=8)
    fig.suptitle('Observed success, communication cost, and giving',y=.98,fontsize=15)
    legend(fig,label,.945)
    fig.text(.06,.115,'Each point is one game; small vertical offsets reveal overlaps. Brackets: 95% paired-seed bootstrap intervals (only 5 seed clusters).',fontsize=9)
    fig.text(.06,.088,'Correlations pool models and can mix between-model and within-model patterns; they do not identify causal effects or pure abilities.',fontsize=9)
    fig.text(.06,.061,'Finished = still participating at the end of round 8. EXIT = voluntary departure while alive; dead = balance depleted. EXIT is not death.',fontsize=9)
    fig.text(.06,.034,'Rho uses transfer-amount-weighted post-GIVE margins (negative values retained). No-GIVE is undefined, not zero. Model order is fixed.',fontsize=9)
    save(fig,'fig31_relations',blind)


def case_data(seed):
    g=next(g for g in D['gifts'] if g['model']=='Opus' and g['seed']==seed and g['giver_after']==0)
    game=next(v for v in RAW if v['model']=='Opus' and v['seed']==seed)
    r=g['round'];es=game['events'];resline,res=next((line,e) for line,e in es if e['event']=='results' and e['round']==r)
    chline,ch=next((line,e) for line,e in es if e['event']=='charges' and e['round']==r)
    source=g['source']
    vals={role:[res['balances'][g[who]],g[role+'_before'],g[role+'_after'],ch['balances_before'][g[who]],ch['balances'][g[who]]]
          for role,who in [('giver','src'),('taker','dst')]}
    return g,vals,{'model':'Opus','seed':seed,'round':r,'source':source,'result_line':resline,'gift_line':g['line'],'charges_line':chline,
        'giver':g['src'],'receiver':g['dst'],'values':vals,'pending_fine':g['due'],
        'stages':['Results announced','Before GIVE (after responses)','Immediately after GIVE','Before fine (after later responses)','After fine']}


def behavior(blind=False):
    label=lambda m:ALIASES[m] if blind else m
    fig=plt.figure(figsize=(13.2,9.4))
    grid=fig.add_gridspec(2,2,left=.07,right=.98,bottom=.18,top=.88,wspace=.28,hspace=.62,height_ratios=[1,1.15])
    ax=fig.add_subplot(grid[0,0])
    for i,m in enumerate(MODELS):
        v=D['models'][m];n=v['gifts'];k=v['prep_gifts']
        ax.barh(i,k/n*100,color=COLORS[m],height=.55,alpha=.7)
        ax.text(115,i,f'{k}/{n}',va='center',ha='right',fontsize=9)
        for g in D['games']:
            if g['model']==m and g['n_give']:
                ax.scatter(g['prep_gifts']/g['n_give']*100,i+(g['seed']-4103)*.055,s=26,facecolors='white',edgecolors=COLORS[m],zorder=4)
    ax.set(yticks=range(5),yticklabels=[label(m) for m in MODELS],xlim=(-2,118),xlabel='Completed GIVE before SOLVE result (%)')
    ax.invert_yaxis();ax.set_title('(a) Before-result and after-result giving differ',loc='left',fontsize=11)
    ax.text(0,-.27,'Bar + k/n: pooled events. Open points: games with GIVE.\nNo-GIVE games excluded here: '+', '.join(f'{label(m)} {sum(g["n_give"]==0 for g in D["games"] if g["model"]==m)}' for m in MODELS),transform=ax.transAxes,fontsize=8)
    ax=fig.add_subplot(grid[0,1]);matrix=[];labels=[]
    for m in MODELS:
        ts=[t for t in D['talks'] if t['model']==m and t['exit_eligible']];row=[];labs=[]
        for lo,hi in [(0,1),(1,2),(2,1e10)]:
            rr=[t for t in ts if lo<=t['slack']<hi];k=sum(t['exit'] for t in rr);n=len(rr)
            row.append(k/n*100 if n else np.nan);labs.append(f'{k}/{n}\n{100*k/n:.1f}%' if n else 'NA')
        matrix.append(row);labels.append(labs)
    ax.imshow(matrix,vmin=0,vmax=100,cmap='Blues',aspect='auto')
    for i in range(5):
        for j in range(3):ax.text(j,i,labels[i][j],ha='center',va='center',fontsize=9,color='white' if matrix[i][j]>55 else '#172b3a')
    ax.set(yticks=range(5),yticklabels=[label(m) for m in MODELS],xticks=range(3),xticklabels=['Below 1','1 to <2','2 or more'],xlabel='Balance / per-agent fine at response start')
    ax.set_title('(b) EXIT requests are more frequent below one fine',loc='left',fontsize=11)
    ax.text(0,-.27,'Cells: requests / non-solver prep responses, round-start n > 1.\nRepeated responses, not independent agents. The 100% cell is 3/3.',transform=ax.transAxes,fontsize=8)
    case_payload=[]
    for ix,seed in enumerate([4102,4103]):
        ax=fig.add_subplot(grid[1,ix]);g,vals,case=case_data(seed);case_payload.append(case)
        x=np.arange(5)
        for role,color,marker,shown in [('giver','#ad4e6b','o','Donor'),('taker','#206a8e','s','Receiver')]:
            y=vals[role];ax.plot(x,y,marker=marker,color=color,lw=1.8,ms=5,label=shown)
            for j,v in enumerate(y):
                offset=10 if role=='taker' else -16
                if seed==4103 and role=='giver' and j==0:offset=13
                if seed==4103 and role=='taker' and j==2:offset=-18
                if v==0:offset=8 if role=='taker' else -16
                ax.annotate(f'{v:,}',(j,v),xytext=(0,offset),textcoords='offset points',ha='center',fontsize=8)
        ax.axhline(g['due'],color='#666',ls='--',lw=1)
        ax.text(2.5,g['due']+(700 if seed==4102 else 1300),f'Fine per agent = {int(g["due"]):,}',fontsize=8,ha='center')
        ax.set(xticks=x,xticklabels=['Results','Before\nGIVE','After\nGIVE','Before\nfine','After\nfine'],xlim=(-.3,4.3),
               ylim=(-2200,23000 if seed==4102 else 19000),ylabel='Token balance')
        if seed==4102:
            title=f'(c) {label("Opus")} seed 4102, round 8: no fine-threshold crossing'
            sub='Receiver was already above the fine; final balance 10,603.'
        else:
            title=f'(d) {label("Opus")} seed 4103, round 7: TALK cost precedes GIVE'
            sub='Before GIVE, two replies spend 664; joint balance 12,193 -> 11,529.'
        ax.set_title(title+'\n'+sub,loc='left',fontsize=9.5,pad=15)
        ax.legend(frameon=False,fontsize=8,loc='upper right' if seed==4102 else 'lower left',ncol=2)
        if seed==4103:
            ax.text(.04,.96,'Immediately after GIVE: receiver is 471 short.\nLater response costs 539; both end at zero.',transform=ax.transAxes,fontsize=8,va='top')
    fig.suptitle('Behavioral timing and two complete transfer sequences',fontsize=15,y=.98)
    fig.text(.07,.112,'Cases (c,d) include every full-balance GIVE in the 130-transfer cohort (2/130); both belong to the same model, in different games.',fontsize=9)
    fig.text(.07,.085,'GIVE changes neither agent\'s position above/below the pending fine in either case. These records do not show that giving caused death.',fontsize=9)
    fig.text(.07,.058,'EXIT is voluntary departure while alive; it is unavailable after SOLVE. The case panels occur after SOLVE; death follows balance depletion.',fontsize=9)
    fig.text(.07,.031,'Timing is descriptive, not proof of benefit. Fine in (b) is a potential round-start share; in (c,d) it is already due after an incorrect answer.',fontsize=9)
    save(fig,'fig33_behavior',blind)
    if not blind:(OUT/'cases.json').write_text(json.dumps(case_payload,indent=2))


def outcomes(blind=False):
    label=lambda m:ALIASES[m] if blind else m
    fig,(ax,table)=plt.subplots(1,2,figsize=(12,4.5),gridspec_kw={'width_ratios':[1.15,1]})
    fig.subplots_adjust(left=.075,right=.98,bottom=.23,top=.78,wspace=.25)
    data=[[next(g['finishers'] for g in D['games'] if g['model']==m and g['seed']==s) for s in range(4101,4106)] for m in MODELS]
    ax.imshow(data,cmap='Blues',vmin=0,vmax=4,aspect='auto')
    for i,row in enumerate(data):
        for j,v in enumerate(row):ax.text(j,i,str(v),ha='center',va='center',color='white' if v>=3 else '#172b3a',fontsize=13)
    ax.set(yticks=range(5),yticklabels=[label(m) for m in MODELS],xticks=range(5),xticklabels=range(4101,4106),xlabel='Seed (same five IDs for each model)')
    ax.set_title('Finishers in every game (0-4)',fontsize=11)
    table.axis('off')
    rows=[[label(m),f'{D["models"][m]["clear"]}/5',f'{D["models"][m]["all4"]}/5',f'{D["models"][m]["finishers"]}/20'] for m in MODELS]
    t=table.table(cellText=rows,colLabels=['Model','>=1 finishes','All 4 finish','Finished seats'],loc='center',cellLoc='center',colWidths=[.19,.27,.27,.3])
    t.auto_set_font_size(False);t.set_fontsize(10);t.scale(1,1.8)
    for (i,j),cell in t.get_celld().items():
        cell.set_edgecolor('#ddd')
        if i==0:cell.set_facecolor('#e8ecf0')
    fig.suptitle('Reaching the end is different from everyone reaching the end',fontsize=14,y=.97)
    fig.text(.075,.115,'All 25 games: at least one finisher 19/25; all four finishers 8/25; finished seats 56/100.',fontsize=10)
    fig.text(.075,.06,'Completion means reaching the end of round 8, not eight correct answers. EXIT is alive but does not count as finishing.',fontsize=9)
    save(fig,'table31_outcomes',blind)


if __name__=='__main__':
    for blind in [False,True]:
        relation(blind);behavior(blind);outcomes(blind)
