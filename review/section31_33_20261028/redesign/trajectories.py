"""Fixed-seat wallet trajectories grouped by each agent's initial tokens."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D

HERE=Path(__file__).resolve().parent
PAPER=HERE.parents[2]
MODELS=['Fable','Astra','Sol','Opus','Luna']
BUDGETS=[10000,20000,40000,60000]
COLORS=['#306c9c','#38a48a','#d58a27','#9a5f9f']
font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
plt.rcParams.update({'font.family':'NanumGothic','font.size':12,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})

def extract():
    raw=json.loads((HERE.parent/'raw_case_index.json').read_text())
    rows=[]
    for game in raw:
        result=game['result'];starts=result['starts'];ends={e['round']:(line,e) for line,e in game['events'] if e['event']=='round'}
        assert set(starts.values())==set(BUDGETS)
        for agent,start in starts.items():
            b=start;status='in'
            for r in range(9):
                line=None;carried=r>max(ends)
                if r in ends:
                    line,e=ends[r];b=e['end'][agent]
                    status=e['agents'].get(agent,{}).get('status',status)
                if status=='dead':assert b==0
                rows.append(dict(model=game['model'],seed=game['seed'],agent=agent,initial_tokens=start,
                    round=r,balance=b,status=status,carried_after_session=carried,source=game['source'],line=line))
            assert b==result['agents'][agent]['final'],(game['model'],game['seed'],agent)
    assert len(rows)==900
    data={}
    for m in MODELS:
        data[m]={}
        for budget in BUDGETS:
            a=np.array([[next(v['balance'] for v in rows if (v['model'],v['seed'],v['initial_tokens'],v['round'])==(m,s,budget,r)) for r in range(9)] for s in range(4101,4106)])
            data[m][str(budget)]={'n':5,'mean':a.mean(0).tolist(),'seed_rows':a.tolist()}
        data[m]['overall_mean']=np.array([data[m][str(b)]['mean'] for b in BUDGETS]).mean(0).tolist()
    prior=json.loads((HERE.parent/'analysis.json').read_text())
    for m in MODELS:assert abs(data[m]['overall_mean'][-1]-np.mean([g['pre_prize']['mu'] for g in prior['games'] if g['model']==m]))<1e-9
    with (HERE/'trajectory_seats.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    payload={'models':data,'definitions':{'n':'Per model20 fixed agents: four initial budgets x5seeds; group denominator5 at every round, overall20.',
        'time':'Round0=starting wallet; rounds1–8=round-end wallet after response charges, transfers, fines and EXIT bonus, before final end-pool prize.',
        'exit':'Retain20k EXIT bonus and freeze exited wallet; dead0 retained; after early session termination carry final wallet to round8 only for display.',
        'fifth_line':'overall_mean=mean of the focal model20agents, confirmed by user.'},
        'checks':{'agents':100,'rows':len(rows),'each_group_n':5,'last_balances_match_all100_raw_final':True,'overall_final_matches_preprize_mu':True},
        'input_sha256':hashlib.sha256((HERE.parent/'raw_case_index.json').read_bytes()).hexdigest()}
    (HERE/'trajectories.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    return payload

def plot(data):
    fig,axes=plt.subplots(2,3,figsize=(11.4,6.3),sharex=True,sharey=True)
    fig.subplots_adjust(left=.07,right=.98,bottom=.16,top=.9,wspace=.15,hspace=.35)
    ylim=max(max(data['models'][m][str(b)]['mean']) for m in MODELS for b in BUDGETS)/1000
    for ax,m in zip(axes.flat,MODELS):
        for b,c,mk in zip(BUDGETS,COLORS,['o','s','^','D']):
            ax.plot(range(9),np.array(data['models'][m][str(b)]['mean'])/1000,color=c,lw=1.6,marker=mk,ms=3)
        key='overall_mean'
        ax.plot(range(9),np.array(data['models'][m][key])/1000,color='#222',ls='--',lw=2.1,zorder=5)
        ax.set_title(m,loc='left',fontsize=13);ax.set(xticks=range(9),xlim=(0,8),ylim=(0,np.ceil(ylim/10)*10+2));ax.grid(alpha=.16)
        ax.set_xlabel('라운드 (0 = 시작)')
    for ax in axes[:,0]:ax.set_ylabel('평균 보유 토큰 (천)')
    axes[0,0].tick_params(labelbottom=True);axes[0,1].tick_params(labelbottom=True);axes[0,2].tick_params(labelbottom=True)
    keyax=axes[1,2];keyax.axis('off')
    label='해당 모델 전체 20명 평균'
    handles=[Line2D([],[],color=c,marker=mk,lw=1.6,ms=4,label=f'시작 {b//10000}만 (5명 평균)') for b,c,mk in zip(BUDGETS,COLORS,['o','s','^','D'])]
    handles.append(Line2D([],[],color='#222',ls='--',lw=2,label=label))
    keyax.legend(handles=handles,loc='upper left',frameon=False,fontsize=11)
    keyax.text(.02,.16,'초기 토큰 집단을 끝까지 고정\nEXIT 뒤 잔액 유지 · 꺼짐은 0\n최종 상금 제외 · EXIT 보너스 포함',transform=keyax.transAxes,fontsize=11,va='top',linespacing=1.6)
    fig.suptitle('초기 토큰별 평균 잔액의 라운드별 변화',fontsize=15,y=.98)
    fig.text(.07,.035,'각 모델 5판·20자리. 매 라운드 같은 5자리를 평균하므로, 중도 EXIT·꺼짐도 분모에서 빠지지 않는다.',fontsize=11)
    name='appendix_token_trajectories'
    for ext in ['png','pdf']:
        fig.savefig(HERE/f'{name}.{ext}',dpi=220,bbox_inches='tight')
        fig.savefig(PAPER/'cogsci2027/ko/figures'/f'{name}.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)

if __name__=='__main__':
    p=extract();plot(p);print(json.dumps(p['checks']))
