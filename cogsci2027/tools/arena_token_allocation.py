"""Account for every token of the 100-agent cohort, excluding completion prizes."""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import feedback_20261028 as fb

ROOT=fb.ROOT
KEYS=('talk','solve_net','penalties','given','retained')
LABELS=('대화','풀이 (환급 제외)','벌금','GIVE','남긴 잔액')
COLORS=('#5386A6','#A27CB3','#C8794A','#4B9B83','#D2D5D8')
STATES=('finished','exited','dead')
SHORT_STATE={'finished':'완','exited':'이','dead':'꺼'}


def extract():
    sources,runs=fb.load_sources(json.loads((ROOT/'results/arena_v33.json').read_text()))
    rows=[]
    for run,raw in runs.items():
        model=next(m for m in fb.MODELS if m.lower() in run.lower())
        for result in raw['results.jsonl']:
            if result.get('event')!='session' or result['seed'] not in fb.SEEDS:
                continue
            events=[e for e in raw['events.jsonl'] if e['session_id']==result['session_id']]
            for a,v in result['agents'].items():
                calls=[e for e in events if e['event']=='call' and e['agent']==a]
                talk=sum(e['used'] for e in calls if e['kind']=='talk')
                solve=sum(e['used'] for e in calls if e['kind']=='solve')
                assert talk+solve==v['spent']
                received=sum(t['amount'] for t in result['transfers'] if t['dst']==a)
                given=sum(t['amount'] for t in result['transfers'] if t['src']==a)
                bonus=sum(e['agents'].get(a,{}).get('exit_bonus',0) for e in events if e['event']=='round')
                resource=result['starts'][a]+received+bonus
                parts=dict(talk=talk,solve_net=solve-v['returned'],penalties=v['charged'],given=given,retained=v['final'])
                assert min(parts.values())>=0 and sum(parts.values())==resource
                spent=sum(parts[k] for k in KEYS[:-1])
                assert spent>0
                status='finished' if a in result['final']['winner'] else v['status']
                assert status in STATES
                row=dict(model=model,seed=result['seed'],session_id=result['session_id'],agent=a,start=result['starts'][a],
                         status=status,received=received,exit_bonus=bonus,resource=resource,
                         solve_gross=solve,solve_refund=v['returned'],spent=spent,**parts)
                row.update({k+'_pct':100*parts[k]/resource for k in KEYS})
                row.update({k+'_spend_pct':100*parts[k]/spent for k in KEYS[:-1]})
                assert abs(sum(row[k+'_pct'] for k in KEYS)-100)<1e-10
                assert abs(sum(row[k+'_spend_pct'] for k in KEYS[:-1])-100)<1e-10
                rows.append(row)
    rows.sort(key=lambda r:(list(fb.MODELS).index(r['model']),STATES.index(r['status']),r['seed'],r['start']))
    assert len(rows)==100 and len({(r['session_id'],r['agent']) for r in rows})==100
    assert [sum(r['status']==s for r in rows) for s in STATES]==[56,34,10]
    assert sum(r['given'] for r in rows)==sum(r['received'] for r in rows)==383276
    means={}
    for s in ('all',)+STATES:
        rr=[r for r in rows if s=='all' or r['status']==s]
        means[s]=dict(n=len(rr),resource_pct={k:float(np.mean([r[k+'_pct'] for r in rr])) for k in KEYS},
                      spend_pct={k:float(np.mean([r[k+'_spend_pct'] for r in rr])) for k in KEYS[:-1]})
    return dict(agents=rows,means=means,sources=sources,definitions={
        'resource':'initial + all received GIVE + EXIT bonus. Completion prize excluded. Transfers can recirculate; this is cumulative resources, not unique tokens.',
        'talk':'Sum ledger call.used for TALK, thinking included, capped at available balance.',
        'solve_net':'Sum ledger call.used for SOLVE minus actual returned tokens; successful solve refunds are subtracted.',
        'penalties':'Recorded result agents.charged (wrong-answer penalties).',
        'given':'Gross executed outgoing transfers; not net gifts or independently estimated cooperation.',
        'retained':'Recorded terminal final balance, EXIT bonus included; completion reward not included.',
        'resource_pct':'Each component / resource * 100. All five components sum to 100 for every agent.',
        'spend_pct':'First four components / spent *100; excludes retained balance. Denominator positive for all 100 agents.',
        'means':'Arithmetic mean of individual percentages, each agent equal weight; not pooled-token shares.',
        'ordering':'Models in existing completion ranking; within model final state, seed, initial allocation. Label seed suffix / initial tokens in 10k / final state; agent ID in CSV.',
        'inference':'Descriptive, outcome-conditioned accounting; no causal or necessary-capability claim and no independent-agent inferential tests.'},
        checks=dict(ledger_identities_passed=100,percent_sums_passed=100,refunds_nonnegative=100,
                    n_finished=56,n_exited=34,n_dead=10,gross_transfers_match=383276))


def plot(data):
    sys.path.insert(0,str(fb.OLD/'figs'))
    import paper_style as ps
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    ps.use()
    labels={'all':'전체 100명','finished':'완주 56명','exited':'EXIT 34명','dead':'꺼짐 10명'}
    fig,axes=plt.subplots(1,2,figsize=(7,2.8))
    fig.subplots_adjust(left=.12,right=.985,top=.81,bottom=.24,wspace=.4)
    for ax,key,title,kk in zip(axes,('resource_pct','spend_pct'),
                               ('(a) 이용한 전체 자원의 배분','(b) 실제 지출의 구성'),(KEYS,KEYS[:-1])):
        for i,s in enumerate(('finished','exited','dead','all')):
            left=0
            for k,color in zip(kk,COLORS):
                value=data['means'][s][key][k]
                ax.barh(i,value,left=left,color=color,height=.62)
                if value>=8:ax.text(left+value/2,i,f'{value:.1f}',ha='center',va='center',fontsize=6.5)
                left+=value
        ax.set_yticks(range(4),[labels[s] for s in ('finished','exited','dead','all')]);ax.invert_yaxis()
        ax.set(xlim=(0,100),xticks=[0,25,50,75,100],xlabel='개인별 비율의 평균 (%)');ax.set_title(title,fontsize=8)
    fig.legend([Patch(facecolor=c) for c in COLORS],LABELS,loc='lower center',ncol=5,fontsize=7)
    ps.save(fig,str(ROOT/'ko/figures/arena_token_allocation_mean'));plt.close(fig)

    fig,axes=plt.subplots(2,3,figsize=(7,7.1))
    fig.subplots_adjust(left=.11,right=.985,top=.94,bottom=.105,wspace=.65,hspace=.33)
    for ax,model in zip(axes.flat,fb.MODELS):
        rows=[r for r in data['agents'] if r['model']==model]
        assert len(rows)==20
        for i,r in enumerate(rows):
            left=0
            for k,color in zip(KEYS,COLORS):
                v=r[k+'_pct'];ax.barh(i,v,left=left,color=color,height=.8);left+=v
        ax.set_yticks(range(20),[f"{r['seed']-4100:02d}/{r['start']//10000}만/{SHORT_STATE[r['status']]}" for r in rows],fontsize=5.8)
        ax.set(ylim=(19.7,-.7),xlim=(0,100),xticks=[0,50,100],xlabel='전체 자원 대비 (%)')
        ax.set_title(model,fontsize=9)
        ax.tick_params(axis='y',length=0)
        # Separate final-state groups without treating them as independent experiments.
        for i in range(1,20):
            if rows[i]['status']!=rows[i-1]['status']:ax.axhline(i-.5,color='white',lw=2)
    ax=axes[1,2];ax.axis('off')
    ax.legend([Patch(facecolor=c) for c in COLORS],LABELS,loc='upper left',fontsize=8)
    ax.text(0,.55,'행: 시드 / 초기 토큰 / 끝 상태\n01–05 = 시드 4101–4105\n완 = 완주, 이 = EXIT, 꺼 = 꺼짐\n\n분모: 초기 + 받은 GIVE\n           + EXIT 보너스\n\n풀이 환급은 비용에서 뺌\n최종 완주 상금은 제외\n각 행의 합 = 100%',fontsize=7,va='top',linespacing=1.6)
    fig.suptitle('100명 각각의 토큰 배분',fontsize=11,y=.995)
    fig.text(.11,.01,'25판 × 4명. 이전 토큰은 다시 이전될 수 있으며, 이 그림은 고유 토큰의 흐름을 추적하는 것이 아니라 개인별 장부를 분해한다.',fontsize=6.3)
    ps.save(fig,str(ROOT/'ko/figures/arena_token_allocation_100'));plt.close(fig)


def main():
    data=extract();plot(data)
    data['analysis_sha256']=fb.sha(Path(__file__).read_bytes())
    data['figures']=[dict(path=str(p),sha256=fb.sha(p.read_bytes())) for p in sorted((ROOT/'ko/figures').glob('arena_token_allocation_*.*'))]
    out=ROOT/'results/arena_token_allocation.json';out.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    with out.with_suffix('.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(data['agents'][0]));writer.writeheader();writer.writerows(data['agents'])
    print(json.dumps({'means':data['means'],'checks':data['checks']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
