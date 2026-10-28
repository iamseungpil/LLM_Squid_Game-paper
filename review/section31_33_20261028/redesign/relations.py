"""Same-task comparison and exact wallet accounting; no fitted causal model."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
HERE=Path(__file__).resolve().parent
A=json.loads((HERE.parent/'analysis.json').read_text())
RAW=json.loads((HERE.parent/'raw_case_index.json').read_text())
MODELS=['Fable','Astra','Sol','Opus','Luna']
font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
plt.rcParams.update({'font.family':'NanumGothic','font.size':10,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
shared=set.intersection(*[{(s['seed'],s['round']) for s in A['solves'] if s['model']==m} for m in MODELS])
prefix={(s,r) for s in range(4101,4106) for r in range(1,7)}
assert len(shared)==36 and prefix<=shared
rows=[]
for g in A['games']:
    m,seed=g['model'],g['seed']
    raw=next(x for x in RAW if (x['model'],x['seed'])==(m,seed))
    events=[e for _,e in raw['events']]
    talk=sum(e['used'] for e in events if e['event']=='call' and e['kind']=='talk')
    solve=sum(e['used'] for e in events if e['event']=='call' and e['kind']=='solve')
    refund=sum(sum(e['returned'].values()) for e in events if e['event']=='results')
    fines=sum(sum(e['taken'].values()) for e in events if e['event']=='charges')
    final=sum(a['final'] for a in raw['result']['agents'].values())
    bonus=20000*g['exited']
    assert sum(raw['result']['starts'].values())+bonus-talk-(solve-refund)-fines==final
    ss=[s for s in A['solves'] if (s['model'],s['seed'])==(m,seed)]
    common=[s for s in ss if (seed,s['round']) in shared]
    pre=[s for s in ss if (seed,s['round']) in prefix]
    rows.append(dict(model=m,seed=seed,common_correct=sum(s['correct'] for s in common),common_n=len(common),common_map=sum(s['map_correct'] for s in common),prefix_correct=sum(s['correct'] for s in pre),prefix_n=len(pre),prefix_map=sum(s['map_correct'] for s in pre),early_talk=g['early_talk_total'],talk=talk,net_solve=solve-refund,fines=fines,exit_bonus=bonus,retained=final,sen=g['historic_settled']['S'],finishers=g['finishers'],exited=g['exited'],dead=g['dead']))
# Match the task inputs independently, not merely seed/round IDs.
for seed,r in shared:
    tasks=[]
    for m in MODELS:
        raw=next(g for g in RAW if (g['model'],g['seed'])==(m,seed))
        e=next(e for _,e in raw['events'] if e['event']=='round_start' and e['round']==r)
        tasks.append(e['public'])
    assert all(t==tasks[0] for t in tasks)
summary={m:{k:sum(g[k] for g in rows if g['model']==m) for k in ['common_correct','common_n','common_map','prefix_correct','prefix_n','prefix_map','talk','net_solve','fines','exit_bonus','retained','finishers','exited','dead']} for m in MODELS}
for m in MODELS:
    summary[m]['mean_sen']=np.mean([g['sen'] for g in rows if g['model']==m])
    summary[m]['early_cost_pct']=np.mean([g['early_talk'] for g in rows if g['model']==m])/130000*100
    summary[m]['rho_manuscript']=1/A['models'][m]['rho']
(HERE/'relations.json').write_text(json.dumps({'games':rows,'models':summary,'common_tasks':sorted(shared),'definitions':{'common':'Primary: fixed R1-6 prefix30 permodel. Sensitivity: intersection of observed SOLVE seed-rounds36 permodel. Identical public task inputs verified.', 'cost':'Actual used tokens; SOLVE net of recorded refunds; fine=actual taken, not scheduled charge. Full-game totals depend on duration.', 'rho':'Current live manuscript equation giver/taker; preserved, obtained as reciprocal of historical analysis.json taker/giver. No manuscript rho edits.', 'sen':'Historical pergame settled four-seat mean times (1-Gini), then average games; end-pool prize retained. Different from preprize appendix wallets.', 'inference':'Descriptive profiles; shared-window selection is affected by termination. No necessary/sufficient/causal claims. Early cost % is just rescaling by common initial130k.'},'checks':{'all25_wallet_identities':True,'all36_task_inputs_equal':True}},ensure_ascii=False,indent=2))

def save(fig,name):
    for ext in ['png','pdf']:fig.savefig(HERE/f'{name}.{ext}',dpi=200,bbox_inches='tight')
    plt.close(fig)

def plot(blind=False):
    labels=['A','B','C','D','E'] if blind else MODELS
    fig,axs=plt.subplots(1,4,figsize=(13,6.6),sharey=True)
    fig.subplots_adjust(left=.10,right=.98,top=.72,bottom=.36,wspace=.38)
    titles=['(a) 같은 문제의 정답 수','(b) 초반 대화 비용','(c) GIVE 총량 · 비율은 주석','(d) 최종 상태 (20명)']
    for ax,title in zip(axs,titles):ax.set_title(title,loc='left',fontsize=11,pad=14);ax.grid(axis='x',alpha=.15);ax.set_ylim(4.6,-.6)
    for i,m in enumerate(MODELS):
        d=summary[m];gs=[g for g in rows if g['model']==m]
        axs[0].scatter(d['prefix_correct'],i,c='#417c97',s=65,zorder=3)
        axs[0].text(d['prefix_correct']+.28,i,f"{d['prefix_correct']}/30",va='center',fontsize=9)
        for ax,key,scale in [(axs[1],'early_talk',100/130000)]:
            vals=[g[key]*scale for g in gs]
            ax.scatter(vals,np.array([i]*5)+np.linspace(-.12,.12,5),s=18,color='#89aabc',alpha=.85,zorder=3)
            ax.scatter(np.mean(vals),i,color='#202020',marker='D',s=32,zorder=4)
        given=[g['given']/1000 for g in A['games'] if g['model']==m]
        axs[2].scatter(given,np.array([i]*5)+np.linspace(-.12,.12,5),s=18,color='#89aabc',alpha=.85,zorder=3)
        axs[2].scatter(np.mean(given),i,color='#202020',marker='D',s=32,zorder=4)
        axs[2].text(.98,i-.27,f"$\\rho$ {d['rho_manuscript']:.2f} · GIVE {A['models'][m]['gifts']}건",transform=axs[2].get_yaxis_transform(),ha='right',fontsize=8.5)
        left=0
        for key,c in [('finishers','#357c8d'),('exited','#d7a448'),('dead','#b95c53')]:
            v=d[key];axs[3].barh(i,v,left=left,color=c,height=.55,zorder=2)
            if v:axs[3].text(left+v/2,i,str(v),ha='center',va='center',color='white' if key!='exited' else '#222',fontsize=10)
            left+=v
    axs[0].axvline(22,color='#777',ls='--',lw=1);axs[0].set(xlim=(0,32),xticks=[0,10,20,30],xlabel='대표 solver 정답 / 30번 풀이')
    axs[0].set_yticks(range(5),labels)
    axs[0].text(22,-.7,'MAP 22',ha='center',fontsize=9,color='#666')
    axs[1].set(xlim=(-.5,17),xticks=[0,5,10,15],xlabel='4명 합산 R1–2 비용 / 초기합계 130k (%)')
    axs[2].set(xlim=(-2,60),xticks=[0,20,40,60],xlabel='판당 GIVE 총량 (천 토큰)')
    axs[3].set(xlim=(0,20),xticks=[0,10,20],xlabel='고정 20명 (5판 × 4명)')
    from matplotlib.patches import Patch
    axs[3].legend(handles=[Patch(color=c,label=l) for c,l in [('#357c8d','완주'),('#d7a448','EXIT'),('#b95c53','꺼짐')]],loc='upper center',bbox_to_anchor=(.5,1.08),ncol=3,fontsize=7.5,frameon=False,handlelength=.9,columnspacing=.7)
    axs[3].set_title('(d) 최종 상태 (20명)',loc='left',fontsize=11,pad=32)
    fig.suptitle('같은 문제의 풀이, 초기 지출, 이전 행동과 완주 결과',fontsize=15,y=.99)
    fig.text(.10,.87,'고정 R1–6 × 5판. solver는 시드로 섞은 순환 순서로 배정(중도 이탈자 제외). 라운드당 한 명만 풀이.',fontsize=10)

    fig.text(.10,.25, '작은 점 = 판 (각 5판), 검정 마름모 = 평균. 20자리는 5판에 중첩되며 독립 관측이 아님. GIVE 건수는 기회당 협력률이 아님.',fontsize=10)
    fig.text(.10,.10, '관찰된 공통 36문제까지 늘린 민감도 비교: '+ ' · '.join(f'{l} {summary[m]["common_correct"]}' for l,m in zip(labels,MODELS))+' (MAP 27). 종료 시점에 따른 선택은 남음.',fontsize=9)
    fig.text(.10,.05, '전원 완주: '+ ' · '.join(f'{l} {A["models"][m]["all4"]}/5판' for l,m in zip(labels,MODELS))+' (합계 8/25판). Sen은 상금 때문에 완주 인원에 지배되어 보조 표로 분리.',fontsize=9)
    fig.text(.10,.82,'예산·대화 상태가 달라 순수 능력 시험은 아님. 행은 완주 인원 순. 초반 대화 비용은 생각 토큰도 포함.',fontsize=10)
    fig.text(.10,.20,r'$\rho = (\sum_k g_k m_{giver,k})/(\sum_k g_k m_{receiver,k})$: 모델별 5판 전체에서 이전량 g로 가중한 두 여유 합의 비. 개별 비율의 평균이 아님.',fontsize=9)
    fig.text(.10,.15,'여유 m = (이전 직후 잔액 - 예정 벌금) / 라운드 1인당 벌금. 음수·0도 유지. 분모 0이면 미정. 여기서는 두 합 모두 양수, ρ>1은 준 쪽 여유가 더 큼.'.replace('ρ', 'rho'),fontsize=9)
    save(fig,'blind_relations' if blind else 'fig31_profiles')
    if blind:return
    fig,ax=plt.subplots(figsize=(9,4.5));fig.subplots_adjust(left=.13,right=.97,top=.82,bottom=.29)
    colors=['#d7a448','#738fa4','#b95c53','#4c9186'];keys=['talk','net_solve','fines','retained'];names=['대화 지출','풀이 순지출 (환급 차감)','실제 납부 벌금','최종 보유 (상금 제외)']
    for i,m in enumerate(MODELS):
        left=0
        for key,c,name in zip(keys,colors,names):
            v=summary[m][key]/5000;ax.barh(i,v,left=left,color=c,label=name if i==0 else None,height=.62)
            if v>4:ax.text(left+v/2,i,f'{v:.1f}',ha='center',va='center',fontsize=9,color='white' if key in ['fines','retained'] else '#222')
            left+=v
        ax.text(left+1,i,f'130 + {summary[m]["exit_bonus"]/5000:.0f}',va='center',fontsize=10)
    ax.set(yticks=range(5),yticklabels=MODELS,ylim=(4.6,-.6),xlim=(0,195),xlabel='판당 평균 토큰 (천)');ax.set_title('자원 장부: 초기 130k + EXIT 보너스 = 지출 + 최종 보유',loc='left',fontsize=13)
    ax.legend(ncol=2,loc='upper left',bbox_to_anchor=(0,-.22),frameon=False,fontsize=9)
    fig.text(.13,.02,'25판 모두 장부 일치. GIVE는 집단 내 이전이므로 합계에서 상쇄됨. 총비용은 플레이 길이에도 좌우된다.',fontsize=9)
    save(fig,'fig31_budget')
plot();plot(True)
print(json.dumps(summary,indent=2))
