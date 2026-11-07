"""Refresh appendix I--Q from existing v33 public seeds 4101--4110 only.

Sources: hash-verified cohort_public_20261105.json manifests under
~/squid5-runs/e52_v33/squid5_e52v33_public_*4. No experiments or corpus edits.
Current O/P/Q inputs are independently checked against existing raw records.
Writes new dated JSON/PDF/PNG and staging fragments, never live manuscript files.
"""
import json, sys, math, hashlib
from pathlib import Path
from collections import Counter
import statistics as st
import numpy as np
from scipy.stats import spearmanr
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import feedback_20261028 as fb
import ablation_prize_20261103 as ab
import arena_v33 as av
import fig3_completion_20261028 as fc
ROOT=fb.ROOT
OUT=ROOT/'ko/figures/appendix_refresh_20261107'
RES=ROOT/'results/appendix_refresh_20261107'
STAGE=ROOT.parent/'review/appendix_consolidation_20261107/staging'
SEEDS=list(range(4101,4111)); MODELS=list(fb.MODELS)
STATES=('finished','exited','dead'); SL=('완주','EXIT','꺼짐')
COLORS=dict(zip(MODELS,['#7155A1','#CE5184','#B58B18','#278D7A','#98633B']))
MARKERS=dict(zip(MODELS,['o','^','D','s','v']))
KEYS=('talk','solve_net','penalties','given','retained')
KL=('대화','풀이 (환급 제외)','벌금','GIVE','남긴 잔액')
KC=('#5386A6','#A27CB3','#C8794A','#4B9B83','#D2D5D8')
ps,plt=ab.style()
plt.rcParams.update({'mathtext.fontset':'dejavusans','mathtext.default':'it'})

def avg(x):
    x=[v for v in x if v is not None];return float(np.mean(x)) if x else None

def save(fig,name):
    ps.save(fig,str(OUT/name));plt.close(fig)

def verify_manifest(d):
    for s in d['sources']:
        assert fb.sha(fb.read_bytes(Path(s['path'])))==s['sha256_decompressed'],s['path']

def extract():
    d=json.loads((ROOT/'results/cohort_public_20261105.json').read_text());verify_manifest(d)
    cases=ab.raw_cases(ab.V33,SEEDS)
    assert {(c['model'],c['seed']) for c in cases}=={(m,s) for m in MODELS for s in SEEDS}
    known={g['session_id']:g for g in d['games']};agents=[];solves=[];games=[]
    for c in cases:
        r=c['result'];ev=[e for _,e in c['events']];m=c['model'];sid=r['session_id']
        g=fb.game_metrics(ev,r,m,include_singleton=True);kg=known[sid]
        for k in ['finishers','exited','dead','given','n_give','rho','goal']:
            assert g[k]==kg[k],(sid,k,g[k],kg[k])
        starts={e['round']:e for e in ev if e['event']=='round_start'}
        ends={e['round']:e for e in ev if e['event']=='round'}
        sc={(e['round'],e['agent']):e for e in ev if e['event']=='call' and e.get('kind')=='solve'}
        sb={(e['round'],a):e['balances'][a] for e in ev if e['event']=='call_start' and e.get('kind')=='solve' for a in e['agents']}
        for a,v in r['agents'].items():
            calls=[e for e in ev if e['event']=='call' and e['agent']==a]
            talk=sum(e['used'] for e in calls if e['kind']=='talk');solve=sum(e['used'] for e in calls if e['kind']=='solve')
            assert talk+solve==v['spent']
            given=sum(t['amount'] for t in r['transfers'] if t['src']==a)
            received=sum(t['amount'] for t in r['transfers'] if t['dst']==a)
            bonus=sum(e['agents'].get(a,{}).get('exit_bonus',0) for e in ends.values())
            parts=dict(talk=talk,solve_net=solve-v['returned'],penalties=v['charged'],given=given,retained=v['final'])
            resource=r['starts'][a]+received+bonus;spent=resource-v['final']
            assert min(parts.values())>=0 and sum(parts.values())==resource and spent>0
            early=[e['used'] for e in calls if e['kind']=='talk' and e['round']<=2]
            ar=dict(model=m,seed=c['seed'],session_id=sid,agent=a,start=r['starts'][a],
                status=g['seats'][a]['status'],resource=resource,received=received,exit_bonus=bonus,spent=spent,
                solve_gross=solve,solve_refund=v['returned'],early_tokens=avg(early),early_tokens_sum=sum(early),early_calls=len(early),
                status_end2=next((ends[rr]['agents'][a]['status'] for rr in sorted(ends,reverse=True) if rr<=2 and a in ends[rr]['agents']),v['status']),
                active_rounds=sum(a in e['taking_part'] for e in starts.values()),**parts)
            ar.update({k+'_pct':100*parts[k]/resource for k in KEYS});ar.update({k+'_spend_pct':100*parts[k]/spent for k in KEYS[:-1]})
            ar['given_per_agent_round']=given/ar['active_rounds'];ar['solves']=[]
            for rr,end in ends.items():
                z=end['agents'].get(a,{})
                if not z.get('solve_call'):continue
                call=sc[rr,a];bal=sb[rr,a];fee=24000/len(starts[rr]['taking_part'])
                shares=starts[rr]['public']['task']['by_n']['4']['shares'];belief=z.get('belief')
                normalized_shares={k:v/sum(shares.values()) for k,v in shares.items()}
                js=av.js_distance(normalized_shares,belief) if belief else None
                if belief and z.get('tv_to_ideal') is not None:
                    tv=sum(abs(shares.get(k,0)-belief.get(k,0)) for k in set(shares)|set(belief))/2
                    assert abs(tv-z['tv_to_ideal'])<.0006
                sr=dict(model=m,seed=c['seed'],session_id=sid,agent=a,start=r['starts'][a],round=rr,
                    status=ar['status'],correct=int(bool(z.get('solved'))),picked_top=int(bool(z.get('picked_top'))),
                    margin=bal/fee,balance=bal,tokens=call['used'],cap=call['cap'],truncated=bool(call.get('truncated')),
                    js=js,shares=shares,belief=belief)
                ar['solves'].append(sr);solves.append(sr)
            ar.update(solve_n=len(ar['solves']),correct_n=sum(s['correct'] for s in ar['solves']))
            agents.append(ar)
        gg=dict(kg,model_rho=d['summary']['models'][m]['rho'])
        games.append(gg)
    assert len(agents)==200 and len(solves)==386
    assert sum(a['given'] for a in agents)==sum(a['received'] for a in agents)==sum(g['given'] for g in games)
    assert sum(s['correct'] for s in solves)==sum(g['correct_n'] for g in games)
    usual={m:st.median(s['tokens'] for s in solves if s['model']==m and s['margin']>=2) for m in MODELS}
    med={m:st.median(a['early_tokens'] for a in agents if a['model']==m and a['early_tokens'] is not None) for m in MODELS}
    for s in solves:
        s['relative_tokens']=s['tokens']/usual[s['model']]
        ref=[t for t in solves if t['seed']==s['seed'] and t['round']==s['round'] and t['model']!=s['model'] and t['margin']>=2]
        s['task_ref_top']=avg([t['picked_top'] for t in ref]);s['task_ref_correct']=avg([t['correct'] for t in ref])
        ref=[t for t in solves if t['seed']==s['seed'] and t['start']==s['start'] and t['model']!=s['model']]
        s['seat_ref_top']=avg([t['picked_top'] for t in ref])
    for a in agents:
        a['reasoning_deviation']=avg([s['picked_top']-s['seat_ref_top'] for s in a['solves'] if s['seat_ref_top'] is not None])
        a['early_relative']=a['early_tokens']/med[a['model']] if a['early_tokens'] is not None else None
        a['saving']=a['early_relative'] is not None and a['early_relative']<=1
        a['joint']='unobserved' if a['reasoning_deviation'] is None or a['early_relative'] is None else ('both' if a['saving'] else 'reasoning') if a['reasoning_deviation']>=0 else 'saving' if a['saving'] else 'neither'
    for g in games:
        aa=[a for a in agents if a['session_id']==g['session_id']]
        g['early_tokens']=sum(a['early_tokens_sum'] for a in aa)/sum(a['early_calls'] for a in aa)
    return d,cases,games,agents,solves,usual

def summary(rows,key,statistic='mean'):
    vals=[r[key] for r in rows if r[key] is not None];calc=np.median if statistic=='median' else np.mean
    if not vals:return dict(n=0,value=None,ci95=[None,None],valid_boot=0)
    blocks=[[r[key] for r in rows if r['seed']==s and r[key] is not None] for s in SEEDS]
    rng=np.random.default_rng(20261107);boots=[]
    for draw in rng.integers(0,10,(5000,10)):
        v=[x for i in draw for x in blocks[i]]
        if v:boots.append(float(calc(v)))
    ci=fb.interval(boots);clusters=sum(bool(x) for x in blocks)
    return dict(n=len(vals),value=float(calc(vals)),ci95=ci if clusters>=2 and ci[0]!=ci[1] else [None,None],
        bootstrap_ci95_raw=ci,seed_clusters=clusters,valid_boot=len(boots))

def reasoning_plots(solves,games,agents):
    bands=[(0,1),(1,2),(2,4),(4,float('inf'))];labs=['<1','1–2','2–4','≥4']
    fig,axs=plt.subplots(1,2,figsize=(7,2.6));fig.subplots_adjust(left=.08,right=.98,bottom=.24,top=.82,wspace=.35)
    counts=[]
    for lo,hi in bands:
        rr=[s for s in solves if lo<=s['margin']<hi];counts.append(len(rr))
    axs[0].bar(range(4),[100*avg([s['picked_top'] for s in solves if lo<=s['margin']<hi]) for lo,hi in bands],color='#5386A6')
    for i,(lo,hi) in enumerate(bands):
        rr=[s for s in solves if lo<=s['margin']<hi and s['task_ref_top'] is not None]
        ref=100*avg([s['task_ref_top'] for s in rr]);axs[0].plot([i-.35,i+.35],[ref]*2,color='black')
        axs[0].text(i,104,f'n={counts[i]}',ha='center',fontsize=6.5)
    axs[0].set(xticks=range(4),xticklabels=labs,ylim=(0,114),yticks=[0,50,100],xlabel='풀이 직전 생존 여유',ylabel='최다 행동 선택 (%)',title='(a) 최다 행동 선택과 같은 과제 기준')
    for m in MODELS:
        gifts=[x for g in games if g['model']==m for x in g['gifts']]
        axs[1].scatter([x['giver_margin'] for x in gifts],[x['taker_margin'] for x in gifts],s=12,color=COLORS[m],marker=MARKERS[m],alpha=.6,label=m)
    axs[1].axline((0,0),slope=1,color='gray',ls='--',lw=.6);axs[1].axhline(1,color='gray',lw=.5);axs[1].axvline(1,color='gray',lw=.5)
    axs[1].set(xlabel='지원 직후 지원자 여유',ylabel='지원 직후 수혜자 여유',title='(b) 미납 벌금을 반영한 지원 뒤 여유')
    axs[1].legend(fontsize=5.8,ncol=3,loc='upper left');save(fig,'reasoning_top')
    fig,axs=plt.subplots(1,2,figsize=(7,2.7));fig.subplots_adjust(left=.09,right=.98,bottom=.25,top=.82,wspace=.35)
    for m in MODELS:
        ss=[s for s in solves if s['model']==m]
        axs[0].scatter([s['margin'] for s in ss],[s['relative_tokens'] for s in ss],s=10,alpha=.6,color=COLORS[m],marker=MARKERS[m],label=m)
        vals=[np.median([s['relative_tokens'] for s in ss if lo<=s['margin']<hi]) if any(lo<=s['margin']<hi for s in ss) else np.nan for lo,hi in bands]
        axs[1].plot(range(4),vals,color=COLORS[m],marker=MARKERS[m],ms=3)
    axs[0].set(xscale='log',yscale='log',xlabel='풀이 직전 여유 (로그축)',ylabel='풀이 토큰 / 모델 기준 중앙값',title='(a) 386개 풀이')
    axs[1].set(yscale='log',xticks=range(4),xticklabels=labs,xlabel='풀이 직전 여유',title='(b) 모델별 구간 중앙값')
    for ax in axs:ax.axhline(1,color='gray',ls='--',lw=.6)
    from matplotlib.ticker import FuncFormatter, NullFormatter
    for ax in axs:
        ax.set_yticks([.125,.25,.5,1,2,4])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'))
        ax.yaxis.set_minor_formatter(NullFormatter())
    axs[0].xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'))
    axs[0].xaxis.set_minor_formatter(NullFormatter())
    axs[0].legend(fontsize=6,ncol=3);save(fig,'reasoning_tokens')
    for key,label in [('balance','풀이 시작 잔량 (천 토큰)'),('tokens','풀이 생성 토큰 (천 토큰)')]:
        fig,axs=plt.subplots(1,5,figsize=(7.2,2.2),sharey=True);fig.subplots_adjust(left=.08,right=.99,bottom=.29,top=.78,wspace=.3)
        for ax,m in zip(axs,MODELS):
            ss=[s for s in solves if s['model']==m and s['js'] is not None]
            for correct in (0,1):
                rows=[s for s in ss if s['correct']==correct]
                ax.scatter([s[key]/1000 for s in rows],[s['js'] for s in rows],s=13,facecolors=COLORS[m] if correct else 'none',edgecolors=COLORS[m],lw=.6)
            corr=spearmanr([s[key] for s in ss],[s['js'] for s in ss]).statistic
            ax.set_title(f'{m}\n$r_s$={corr:+.2f}, n={len(ss)}',fontsize=7);ax.set_xlabel(label,fontsize=6)
        axs[0].set_ylabel('JS 거리');save(fig,'js_'+key)

def completion_plots(games,agents,sums):
    fig,ax=plt.subplots(figsize=(4,2.9));fig.subplots_adjust(left=.18,bottom=.28,right=.97,top=.89)
    for key,label,color in [('accuracy','정답률','#5386A6'),('given_per_agent_round','참여자·라운드당 지원량','#278D7A'),('rho','지원 후 여유 비율','#7155A1')]:
        v=[g[key] for g in games if g[key] is not None];mu,sd=np.mean(v),np.std(v)
        yy=[]
        for n in range(5):
            s=sums['by_finishers'][str(n)]['metrics'][key];yy.append((s['value']-mu)/sd if s['value'] is not None else np.nan)
            fc.estimate(ax,n,s,1/sd,color=color,offset=-mu/sd)
        ax.plot(range(5),yy,color=color,label=label)
    ax.set(xticks=range(5),xticklabels=[f"{n}\n({sums['by_finishers'][str(n)]['n_games']}판)" for n in range(5)],xlabel='완주자 수',ylabel='표준점수 평균');ax.axhline(0,color='gray',lw=.5)
    fig.legend(loc='lower center',fontsize=6.5,ncol=2);save(fig,'completion_overview')
    fig,axs=plt.subplots(2,2,figsize=(7,5.2));fig.subplots_adjust(left=.14,right=.98,bottom=.20,top=.89,hspace=.6,wspace=.4)
    for ax,key,title,scale in [(axs[0,0],'reasoning_deviation','같은 자리 대비 최다 행동 선택 (%p)',100),(axs[0,1],'early_relative','초반 응답당 토큰 / 모델 중앙값',1)]:
        for si,state in enumerate(STATES):
            for mi,m in enumerate(MODELS):
                rr=[a for a in agents if a['status']==state and a['model']==m and a[key] is not None]
                ax.scatter([si+(mi-2)*.055+(a['seed']-4105.5)*.006 for a in rr],[a[key]*scale for a in rr],s=10,color=COLORS[m],marker=MARKERS[m],alpha=.35)
            fc.estimate(ax,si,sums['agent_profiles'][state][key],scale)
        ax.set(xticks=range(3),xticklabels=SL,ylabel=title);ax.axhline(1 if key=='early_relative' else 0,color='gray',ls='--',lw=.5)
    ax=axs[1,0];keys=['both','reasoning','saving','neither','unobserved'];labs=['둘 다','수행만','절약만','둘 다 없음','미관측']
    for i,k in enumerate(keys):
        v=sums['joint'][k];left=0
        for state,color in zip(STATES,['#9CC0E0','#D9772B','#3C3C3C']):
            w=100*v['counts'][state]/v['n'] if v['n'] else 0;ax.barh(i,w,left=left,color=color);left+=w
        ax.text(50,i,f"{v['counts']['finished']}/{v['n']}",ha='center',va='center',fontsize=6.5)
    ax.set(yticks=range(5),yticklabels=labs,xlim=(0,100),xlabel='끝 상태 비율 (막대 안: 완주/전체)');ax.invert_yaxis()
    ax=axs[1,1]
    for i,start in enumerate([10000,20000,40000,60000]):
        for saving,off,color in [(True,-.12,'#5386A6'),(False,.12,'#D9772B')]:
            v=next(x for x in sums['landmark'] if x['start']==start and x['saving']==saving);fc.estimate(ax,i+off,v,100,color=color)
    ax.set(xticks=range(4),xticklabels=['1만','2만','4만','6만'],ylim=(-5,105),ylabel='이후 완주 (%)',xlabel='초기 토큰',title=f"2라운드 잔류자 {sums['landmark_n']}명")
    ax.text(.0,-.49,'파랑: 초반 사용 ≤ 모델 중앙값\n주황: 초반 사용 > 모델 중앙값',transform=ax.transAxes,fontsize=6.5)
    from matplotlib.lines import Line2D
    fig.legend([Line2D([],[],color=COLORS[m],marker=MARKERS[m],ls='') for m in MODELS],MODELS,loc='upper center',ncol=5,fontsize=6.5)
    fig.text(.13,.015,'끝 상태 색: 파랑=완주, 주황=EXIT, 검정=꺼짐. 큰 점=중앙값, 오차막대=시드 묶음 95% 구간.',fontsize=6)
    save(fig,'completion_agents')
    fig,axs=plt.subplots(1,3,figsize=(7,2.5));fig.subplots_adjust(left=.08,right=.98,bottom=.27,top=.83,wspace=.35)
    defined=[g['rho'] for g in games if g['rho'] is not None];left=min(defined)-2;edge=min(defined)-1
    for ax,key,label in zip(axs,['finishers','exited','dead'],SL):
        for mi,m in enumerate(MODELS):
            for g in games:
                if g['model']!=m:continue
                x=g['rho'] if g['rho'] is not None else left+(mi-2)*.08
                ax.scatter(x,g[key]+(mi-2)*.025,s=17,color=COLORS[m],marker=MARKERS[m])
        ax.axvspan(left-.5,edge,color='#eeeeee',zorder=0);ax.axvline(0,color='gray',lw=.5)
        ax.set(xlim=(left-.5,max(defined)+.5),ylim=(-.2,4.2),yticks=range(5),ylabel=f'{label} 인원',xlabel='지원 후 여유 비율 ρ')
        ax.text(left,4.05,'GIVE\n없음',ha='center',va='top',fontsize=6)
    fig.legend([Line2D([],[],color=COLORS[m],marker=MARKERS[m],ls='') for m in MODELS],MODELS,loc='upper center',ncol=5,fontsize=6.5)
    save(fig,'completion_rho')

def allocation_plots(agents):
    means={}
    for state in ('all',)+STATES:
        rr=[a for a in agents if state=='all' or a['status']==state]
        means[state]=dict(n=len(rr),resource_pct={k:avg([a[k+'_pct'] for a in rr]) for k in KEYS},spend_pct={k:avg([a[k+'_spend_pct'] for a in rr]) for k in KEYS[:-1]})
    fig,axs=plt.subplots(1,2,figsize=(7,2.8));fig.subplots_adjust(left=.13,right=.98,bottom=.26,top=.85,wspace=.4)
    for ax,key,kk,title in zip(axs,['resource_pct','spend_pct'],[KEYS,KEYS[:-1]],['누적 이용 자원','실제 지출']):
        for i,state in enumerate(STATES+('all',)):
            left=0
            for k,color in zip(kk,KC):
                v=means[state][key][k];ax.barh(i,v,left=left,color=color,height=.65)
                if v>=7:ax.text(left+v/2,i,f'{v:.1f}',ha='center',va='center',fontsize=6)
                left+=v
        ax.set(yticks=range(4),yticklabels=[f'{l} {means[s]["n"]}명' for s,l in zip(STATES+('all',),SL+('전체',))],xlim=(0,100),xlabel='개인별 비율 평균 (%)',title=title);ax.invert_yaxis()
    from matplotlib.patches import Patch
    fig.legend([Patch(color=c) for c in KC],KL,loc='lower center',ncol=5,fontsize=6.5);save(fig,'allocation_mean')
    fig,axs=plt.subplots(1,5,figsize=(7.2,8));fig.subplots_adjust(left=.08,right=.99,bottom=.10,top=.94,wspace=.65)
    for ax,m in zip(axs,MODELS):
        rr=sorted([a for a in agents if a['model']==m],key=lambda a:(STATES.index(a['status']),a['seed'],a['start']))
        assert len(rr)==40
        for i,a in enumerate(rr):
            left=0
            for k,color in zip(KEYS,KC):v=a[k+'_pct'];ax.barh(i,v,left=left,color=color,height=.85);left+=v
        ax.set(yticks=range(40),yticklabels=[f"{a['seed']-4100:02d}/{a['start']//10000}/{dict(zip(STATES,['완','이','꺼']))[a['status']]}" for a in rr],ylim=(39.7,-.7),xlim=(0,100),xticks=[0,100],title=m)
        ax.tick_params(axis='y',labelsize=5,length=0);ax.tick_params(axis='x',labelsize=6)
    fig.legend([Patch(color=c) for c in KC],KL,loc='lower center',ncol=5,fontsize=6.5)
    fig.text(.08,.045,'50판 × 4명. 행: 시드 끝자리 / 초기 토큰(만) / 끝 상태. 상금 제외·EXIT 보너스 포함.',fontsize=6.5)
    save(fig,'allocation_200');return means

def main():
    d,cases,games,agents,solves,usual=extract()
    fc.summary=summary;fc.fb.SEEDS=SEEDS
    sums=fc.aggregate(games,agents)
    reasoning_plots(solves,games,agents);completion_plots(games,agents,sums);means=allocation_plots(agents)
    model_stats={}
    for m in MODELS:
        ss=[s for s in solves if s['model']==m];valid=[s for s in ss if s['task_ref_top'] is not None]
        model_stats[m]=dict(n=len(ss),correct=sum(s['correct'] for s in ss),picked_top=sum(s['picked_top'] for s in ss),
            top_minus_task_reference=avg([s['picked_top']-s['task_ref_top'] for s in valid]),
            accuracy_minus_task_reference=avg([s['correct']-s['task_ref_correct'] for s in valid]),reference_n=len(valid),
            usual_tokens=usual[m],js_n=sum(s['js'] is not None for s in ss),
            js_spearman={k:float(spearmanr([s[k] for s in ss if s['js'] is not None],[s['js'] for s in ss if s['js'] is not None]).statistic) for k in ['balance','tokens']})
    report=dict(scope=dict(version='v33',cohort='public',models=fb.MODELS,seeds=SEEDS,games=50,agents=200),
        sources=d['sources'],checks=dict(raw_games_match_cached_metrics=50,ledger_identities_passed=200,
        state_counts=dict(Counter(a['status'] for a in agents)),solves=len(solves),correct=sum(s['correct'] for s in solves),
        picked_top=sum(s['picked_top'] for s in solves),top_but_wrong=sum(s['picked_top'] and not s['correct'] for s in solves),
        not_top_but_correct=sum(not s['picked_top'] and s['correct'] for s in solves),
        truncated=sum(s['truncated'] for s in solves),cap_below_twice_usual=sum(s['cap']<2*usual[s['model']] for s in solves),
        no_give_games=sum(g['rho'] is None for g in games),negative_rho_games=sum(g['rho'] is not None and g['rho']<0 for g in games)),
        model_stats=model_stats,completion=sums,allocation_means=means,agents=agents,solves=solves,games=games,
        definitions=dict(rho='sum(g*L_giver)/sum(g*L_receiver); pending penalty deducted; negative values retained; no GIVE undefined',
        solve_margin='call-start balance / round-start per-agent penalty, no pending penalty before SOLVE',
        top='round record picked_top; valid and invalid responses retained in solve denominator',
        allocation='initial + received GIVE + EXIT bonus = TALK + net SOLVE + charged penalties + outgoing GIVE + terminal balance; completion prize excluded',
        inference='descriptive outcome-conditioned comparison; 5000 paired-seed bootstrap draws over ten seeds; no independent agent bootstrap',
        early='rounds 1-2 TALK mean tokens per agent, divided by same-model 40-agent median',
        seat_reference='other models at same seed and initial allocation, all observed solves; fixed observed reference'))
    RES.mkdir(exist_ok=True);(RES/'iq_analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    rows=['\\begin{tabular}{lrrrrr}','\\toprule','모델 & 풀이 & 정답 & 최다 행동 & 정답률−기준 & 최다 행동−기준 \\\\','\\midrule']
    for m,s in model_stats.items():rows.append(f"{fb.MODELS[m]} & {s['n']} & {s['correct']} & {s['picked_top']} & {100*s['accuracy_minus_task_reference']:+.1f} & {100*s['top_minus_task_reference']:+.1f} \\\\")
    rows+=['\\bottomrule','\\end{tabular}'];(STAGE/'iq_reasoning_table.tex').write_text('\n'.join(rows)+'\n')
    print(json.dumps(report['checks'],ensure_ascii=False));print('model_stats',model_stats)
if __name__=='__main__':main()
