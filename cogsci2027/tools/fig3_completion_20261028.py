"""Exploratory Figure 3 alternatives from the fixed 25-game v33 cohort.

No model calls. Run with ~/.venvs/squid-game/bin/python from any directory.
Reuses the audited raw-source resolver and ledger definitions, not old pickles.
"""
import csv
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

import feedback_20261028 as fb

ROOT = fb.ROOT
STATES = ('finished', 'exited', 'dead')
STATE_LABELS = ('완주', 'EXIT', '꺼짐')
MODELS = list(fb.MODELS)
COLORS = ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B']
MARKERS = ['o', '^', 'D', 's', 'v']
METRICS = ('accuracy', 'given', 'early_tokens', 'given_per_agent_round', 'rho')
BOOT = 5000


def avg(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def ratio(a, b):
    return a / b if b else None


def load():
    historic = json.loads((ROOT / 'results/arena_v33.json').read_text())
    sources, runs = fb.load_sources(historic)
    games, agents, solves = [], [], []
    for run, raw in runs.items():
        model = next(m for m in MODELS if m.lower() in run.lower())
        by_sid = defaultdict(list)
        for e in raw['events.jsonl']:
            by_sid[e['session_id']].append(e)
        for result in raw['results.jsonl']:
            if result.get('event') != 'session' or result['seed'] not in fb.SEEDS:
                continue
            events = by_sid[result['session_id']]
            game = fb.game_metrics(events, result, model)
            aa = {a: dict(model=model, seed=result['seed'], session_id=result['session_id'], agent=a,
                          start=start, status=game['seats'][a]['status'], early_tokens_sum=0,
                          early_calls=0, active_rounds=0, given=0, received=0, solves=[],
                          status_end2='in') for a, start in result['starts'].items()}
            rr = defaultdict(list)
            for e in events:
                if 'round' in e:
                    rr[e['round']].append(e)
            for r, ev in sorted(rr.items()):
                rs = next(e for e in ev if e['event'] == 'round_start')
                res = next(e for e in ev if e['event'] == 'results')
                end = next(e for e in ev if e['event'] == 'round')
                for a in rs['taking_part']:
                    aa[a]['active_rounds'] += 1
                for e in ev:
                    if e['event'] == 'call' and e['kind'] == 'talk' and r <= 2:
                        aa[e['agent']]['early_tokens_sum'] += e['used']
                        aa[e['agent']]['early_calls'] += 1
                    if e['event'] == 'gift' and e['status'] == 'done':
                        aa[e['src']]['given'] += e['amount']
                        aa[e['dst']]['received'] += e['amount']
                if res['tried']:
                    assert len(res['tried']) == 1
                    a = res['tried'][0]
                    assert end['agents'][a]['solve_call']
                    s = dict(model=model, seed=result['seed'], session_id=result['session_id'], agent=a,
                             start=result['starts'][a], round=r, correct=int(bool(res['solved'])),
                             picked_top=int(bool(end['agents'][a].get('picked_top'))))
                    aa[a]['solves'].append(s)
                    solves.append(s)
                if r <= 2:
                    for a, row in end['agents'].items():
                        aa[a]['status_end2'] = row['status']
            for a in aa.values():
                a['early_tokens'] = ratio(a['early_tokens_sum'], a['early_calls'])
                a['given_per_agent_round'] = ratio(a['given'], a['active_rounds'])
                a['solve_n'] = len(a['solves'])
                a['correct_n'] = sum(s['correct'] for s in a['solves'])
                a['accuracy'] = ratio(a['correct_n'], a['solve_n'])
            game.update(solve_n=sum(a['solve_n'] for a in aa.values()),
                        correct_n=sum(a['correct_n'] for a in aa.values()),
                        early_tokens_sum=sum(a['early_tokens_sum'] for a in aa.values()),
                        early_calls=sum(a['early_calls'] for a in aa.values()),
                        agent_rounds=sum(a['active_rounds'] for a in aa.values()))
            game['accuracy'] = ratio(game['correct_n'], game['solve_n'])
            game['early_tokens'] = ratio(game['early_tokens_sum'], game['early_calls'])
            game['given_per_agent_round'] = ratio(game['given'], game['agent_rounds'])
            assert game['given'] == sum(a['given'] for a in aa.values()) == sum(a['received'] for a in aa.values())
            assert game['finishers'] == 0 or game['rounds_played'] == 8
            games.append(game)
            agents.extend(aa.values())
    games.sort(key=lambda g: (MODELS.index(g['model']), g['seed']))
    med = {m: st.median(a['early_tokens'] for a in agents if a['model'] == m and a['early_tokens'] is not None) for m in MODELS}
    for a in agents:
        a['early_relative'] = ratio(a['early_tokens'], med[a['model']]) if a['early_tokens'] is not None else None
        # Reproduce appendix N's same-seed/start-allocation, other-model reference.
        pairs = []
        for s in a['solves']:
            ref = [t['picked_top'] for t in solves if t['seed'] == s['seed'] and t['start'] == s['start'] and t['model'] != s['model']]
            if ref:
                pairs.append(s['picked_top'] - avg(ref))
        a['reasoning_deviation'] = avg(pairs)
        a['saving'] = a['early_relative'] is not None and a['early_relative'] <= 1
        a['joint'] = ('unobserved' if a['reasoning_deviation'] is None or a['early_relative'] is None
                      else ('both' if a['saving'] else 'reasoning') if a['reasoning_deviation'] >= 0
                      else 'saving' if a['saving'] else 'neither')
    assert len(games) == 25 and len(agents) == 100
    assert len({(g['model'], g['seed']) for g in games}) == 25
    assert {s: sum(a['status'] == s for a in agents) for s in STATES} == dict(finished=56, exited=34, dead=10)
    assert sum(g['given'] for g in games) == 383276 and sum(g['n_give'] for g in games) == 130
    assert sum(g['rho'] is None for g in games) == 7
    previous = json.loads((ROOT / 'results/feedback_20261028.json').read_text())
    for g in games:
        old = next(x for x in previous['games'] if (x['model'], x['seed']) == (g['model'], g['seed']))
        for key in ('finishers', 'exited', 'dead', 'rounds_played', 'given', 'rho'):
            assert g[key] == old[key], (g['model'], g['seed'], key)
    old = json.loads((fb.OLD / 'an3/pt_seat.json').read_text())
    for status, old_status in zip(STATES, ('in', 'exited', 'dead')):
        vals = [a['early_relative'] for a in agents if a['status'] == status]
        assert round(st.median(vals), 2) == old['profile'][old_status]['etok_rel_med']
    for key in ('both', 'neither', 'unobserved'):
        expected = old['joint']['no_solve' if key == 'unobserved' else key]['n']
        assert sum(a['joint'] == key for a in agents) == expected
    for source in sources:
        assert fb.sha(fb.read_bytes(Path(source['path']))) == source['sha256']
    return games, agents, solves, sources, med


def summary(rows, key, statistic='mean'):
    vals = [r[key] for r in rows if r[key] is not None]
    calc = np.mean if statistic == 'mean' else np.median
    if not vals:
        return dict(n=0, value=None, ci95=[None, None], valid_boot=0)
    # Retain all models and seats sharing a seed. No independent-seat resampling.
    blocks = [[r[key] for r in rows if r['seed'] == seed and r[key] is not None] for seed in fb.SEEDS]
    rng = np.random.default_rng(20261028)
    boots = []
    for draw in rng.integers(0, 5, (BOOT, 5)):
        v = [x for i in draw for x in blocks[i]]
        if v:
            boots.append(float(calc(v)))
    ci = np.quantile(boots, [.025, .975]).tolist()
    clusters = sum(bool(b) for b in blocks)
    reason = 'fewer_than_two_seed_clusters' if clusters < 2 else 'zero_width_resampling_interval' if ci[0] == ci[1] else None
    return dict(n=len(vals), value=float(calc(vals)), ci95=ci if reason is None else [None, None],
                bootstrap_ci95_raw=ci, interval_unavailable_reason=reason,
                valid_boot=len(boots), seed_clusters=clusters)


def aggregate(games, agents):
    grouped = {str(n): dict(n_games=sum(g['finishers'] == n for g in games),
                metrics={k: summary([g for g in games if g['finishers'] == n], k) for k in METRICS}) for n in range(5)}
    profiles = {s: {k: summary([a for a in agents if a['status'] == s], k, 'median')
                   for k in ('reasoning_deviation', 'early_relative', 'given_per_agent_round')} for s in STATES}
    joint = {}
    for key in ('both', 'reasoning', 'saving', 'neither', 'unobserved'):
        rows = [dict(a, finish=int(a['status'] == 'finished')) for a in agents if a['joint'] == key]
        joint[key] = dict(n=len(rows), counts={s: sum(a['status'] == s for a in rows) for s in STATES},
                          finish=summary(rows, 'finish'))
    landmark = []
    # Only histories observed by round 2 enter this forward-looking comparison.
    for start in (10000, 20000, 40000, 60000):
        for saving in (True, False):
            rows = [dict(a, finish=int(a['status'] == 'finished')) for a in agents
                    if a['status_end2'] == 'in' and a['start'] == start and a['saving'] == saving
                    and a['early_relative'] is not None]
            landmark.append(dict(start=start, saving=saving, **summary(rows, 'finish')))
    rho_groups = {}
    for name, rows in [('GIVE observed', [g for g in games if g['rho'] is not None]),
                       ('No GIVE', [g for g in games if g['rho'] is None])]:
        rho_groups[name] = {k: sum(g[k] for g in rows) for k in ('finishers', 'exited', 'dead')}
        rho_groups[name]['n_games'] = len(rows)
    return dict(by_finishers=grouped, agent_profiles=profiles, joint=joint, landmark=landmark,
                landmark_n=sum(a['status_end2'] == 'in' for a in agents),
                landmark_excluded=sum(a['status_end2'] != 'in' for a in agents), rho_groups=rho_groups)


def plots(games, agents, sums):
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    ps.use()
    state_colors = [ps.C['finish'], ps.C['exit'], ps.C['dead']]
    legend = [Line2D([], [], color=c, marker=m, ls='', label=n, markersize=4)
              for n, c, m in zip(MODELS, COLORS, MARKERS)]

    def finish_axis(ax):
        ax.set_xticks(range(5), [f"{n}\n(n={sums['by_finishers'][str(n)]['n_games']})" for n in range(5)])
        ax.set_xlim(-.4, 4.4)
        ax.set_xlabel('판 종료 시 완주자 수 (명)')
        ax.grid(axis='y', alpha=.6)

    def estimate(ax, x, s, scale=1, color='#222222', marker='D', size=4):
        if s['value'] is None:
            return
        val = s['value'] * scale
        available = s['ci95'][0] is not None
        if available:
            lo, hi = [v * scale for v in s['ci95']]
            # Draw the percentile interval itself: it need not contain the point estimate.
            ax.plot([x, x], [lo, hi], color=color, lw=1.1, zorder=4)
            ax.plot([x-.035, x+.035], [lo, lo], color=color, lw=.8)
            ax.plot([x-.035, x+.035], [hi, hi], color=color, lw=.8)
        ax.plot(x, val, marker=marker, color=color, ms=size, mfc=color if available else 'white',
                mec='white' if available else color, mew=.6, zorder=5)

    fig, axs = plt.subplots(2, 3, figsize=(7, 5.65))
    fig.subplots_adjust(left=.085, right=.98, bottom=.15, top=.93, hspace=.64, wspace=.46)
    ax = axs.flat[0]
    overview = [('accuracy', '정답률', '#2F6DB0'), ('given', '이전량', '#278D7A'),
                ('early_tokens', '초반 응답 토큰', '#D9772B'), ('rho', '여유 비율 ρ', '#7155A1')]
    for key, label, color in overview:
        allvals = [g[key] for g in games if g[key] is not None]
        mu, sd = np.mean(allvals), np.std(allvals)
        yy = [(sums['by_finishers'][str(n)]['metrics'][key]['value']-mu)/sd
              if sums['by_finishers'][str(n)]['metrics'][key]['value'] is not None else np.nan for n in range(5)]
        ax.plot(range(5), yy, 'o-', color=color, ms=3, lw=1, label=label)
    ax.axhline(0, color='#999999', lw=.6)
    ax.set_title('(a) 판별 지표를 같은 척도로 비교')
    ax.set_ylabel('표준점수의 집단 평균')
    ax.legend(fontsize=6, loc='lower left', ncol=2, columnspacing=.6, handlelength=1)
    finish_axis(ax)
    labels = [('accuracy', '(b) solver 정답률', '정답 / 실제 풀이 (%)', 100),
              ('given', '(c) 판 전체 이전량', '성사된 GIVE (천 토큰)', .001),
              ('early_tokens', '(d) 초반 응답당 토큰', '1–2라운드 TALK (토큰/응답)', 1),
              ('given_per_agent_round', '(e) 참여 기간을 나눈 이전량', 'GIVE / 참여 에이전트·라운드', 1),
              ('rho', '(f) GIVE 후 상대적 여유', '준 쪽 / 받은 쪽 (ρ)', 1)]
    for ax, (key, title, ylabel, scale) in zip(list(axs.flat)[1:], labels):
        for mi, model in enumerate(MODELS):
            rows = [g for g in games if g['model'] == model and g[key] is not None]
            ax.scatter([g['finishers'] + (mi-2)*.065 + (g['seed']-4103)*.009 for g in rows],
                       [g[key]*scale for g in rows], color=COLORS[mi], marker=MARKERS[mi],
                       alpha=.65, s=18, linewidths=.3, edgecolors='white', zorder=3)
        for n in range(5):
            s = sums['by_finishers'][str(n)]['metrics'][key]
            estimate(ax, n, s, scale)
            if key == 'rho':
                ax.text(n, 1.01, f"ρ: {s['n']}판", transform=ax.get_xaxis_transform(), ha='center', fontsize=6)
        ax.set_title(title, pad=15 if key == 'rho' else 6)
        ax.set_ylabel(ylabel)
        ax.set_ylim(bottom=0)
        if key == 'accuracy':
            ax.set_ylim(0, 105)
        finish_axis(ax)
    fig.legend(handles=legend + [Line2D([], [], marker='D', color='#222222', ls='', label='집단 평균·95% 구간', markersize=4)],
               loc='lower center', ncol=6, fontsize=7)
    ps.save(fig, str(ROOT / 'ko/figures/fig3_completion_games'))
    plt.close(fig)

    fig, axs = plt.subplots(2, 2, figsize=(7, 5.4))
    fig.subplots_adjust(left=.15, right=.97, bottom=.20, top=.94, wspace=.38, hspace=.78)
    for ax, key, title, ylabel, scale in [(axs[0, 0], 'reasoning_deviation', '(a) 끝 상태별 과제 수행', '같은 자리 기준 대비 수행 (%p)', 100),
                                          (axs[0, 1], 'early_relative', '(b) 끝 상태별 초반 토큰 사용', '응답당 토큰 / 같은 모델 중앙값', 1)]:
        for si, status in enumerate(STATES):
            rows = [a for a in agents if a['status'] == status and a[key] is not None]
            for mi, model in enumerate(MODELS):
                rr = [a for a in rows if a['model'] == model]
                ax.scatter([si + (mi-2)*.065 + (a['seed']-4103)*.015 for a in rr],
                           [a[key]*scale for a in rr], color=COLORS[mi], marker=MARKERS[mi], s=14, alpha=.4, linewidths=0)
            estimate(ax, si, sums['agent_profiles'][status][key], scale)
        ax.axhline(1 if key == 'early_relative' else 0, color='#777777', ls='--', lw=.7)
        ax.set_xticks(range(3), [f"{label}\n(n={sums['agent_profiles'][status][key]['n']})" for status, label in zip(STATES, STATE_LABELS)])
        ax.set_ylabel(ylabel, fontsize=7)
        ax.set_title(title)
        ax.grid(axis='y', alpha=.5)
    ax = axs[1, 0]
    keys = ('both', 'reasoning', 'saving', 'neither', 'unobserved')
    labs = ('둘 다', '수행만', '절약만', '둘 다 없음', '풀이 미관측')
    for y, k in enumerate(keys):
        s = sums['joint'][k]
        left = 0
        for status, color in zip(STATES, state_colors):
            value = s['counts'][status]/s['n']*100 if s['n'] else 0
            ax.barh(y, value, left=left, color=color, height=.65)
            if status == 'finished' and value > 0:
                ax.text(left+value/2, y, f"{s['counts'][status]}/{s['n']}", ha='center', va='center', fontsize=7)
            left += value
    ax.set_yticks(range(5), [f"{l} ({sums['joint'][k]['n']})" for l,k in zip(labs, keys)])
    ax.invert_yaxis()
    ax.set(xlim=(0,100), xticks=(0,50,100), xlabel='끝 상태 비율 (%)')
    ax.set_title('(c) 과제 수행·절약 조합 (후향 비교)')
    ax.legend([plt.Rectangle((0,0),1,1,color=c) for c in state_colors], STATE_LABELS,
              loc='upper center', bbox_to_anchor=(.5,-.40), ncol=3, fontsize=6.5)
    ax = axs[1, 1]
    for i, start in enumerate((10000,20000,40000,60000)):
        for saving, off, color, marker in [(True,-.11,'#2F6DB0','o'),(False,.11,'#D9772B','s')]:
            s = next(s for s in sums['landmark'] if s['start']==start and s['saving']==saving)
            estimate(ax,i+off,s,100,color,marker)
            if s['value'] is not None:
                ax.text(i+off, s['value']*100+6, f"n={s['n']}",ha='center',fontsize=6,color=color)
    ax.set_xticks(range(4), ['1만','2만','4만','6만'])
    ax.set(ylim=(-5,120), yticks=(0,50,100), xlabel='초기 토큰', ylabel='이후 완주 비율 (%)')
    ax.set_title(f"(d) 2라운드 잔류자 {sums['landmark_n']}명의 이후 완주")
    ax.legend([Line2D([],[],color='#2F6DB0',marker='o',ls=''),Line2D([],[],color='#D9772B',marker='s',ls='')],
              ['초반 사용 ≤ 모델 중앙값','초반 사용 > 모델 중앙값'],loc='upper center',bbox_to_anchor=(.5,-.40),fontsize=6.5)
    fig.legend(handles=legend,loc='upper center',bbox_to_anchor=(.56,.56),ncol=5,fontsize=7)
    ps.save(fig, str(ROOT / 'ko/figures/fig3_completion_agents'))
    plt.close(fig)

    fig, axs = plt.subplots(1, 3, figsize=(7, 2.55))
    fig.subplots_adjust(left=.07, right=.98, bottom=.27, top=.86, wspace=.32)
    for ax, key, label in zip(axs, ('finishers','exited','dead'), STATE_LABELS):
        for mi, model in enumerate(MODELS):
            rows = [g for g in games if g['model']==model]
            for g in rows:
                x = g['rho'] if g['rho'] is not None else -.7+(mi-2)*.08
                y = g[key]+(mi-2)*.025+(g['seed']-4103)*.009
                ax.scatter(x,y,s=23,color=COLORS[mi],marker=MARKERS[mi],alpha=.7,linewidths=.3,edgecolors='white')
        ax.axvline(-.1,color='#999999',lw=.6,ls='--')
        rho_max = max(g['rho'] for g in games if g['rho'] is not None)
        ax.set(xlim=(-1.05,rho_max+.5),ylim=(-.18,4.18),yticks=range(5),xticks=[-.7,2,4,6,8,10])
        ax.set_xticklabels(['없음','2','4','6','8','10'],fontsize=6.5)
        ax.set_xlabel('GIVE 없음   |   여유 비율 ρ',fontsize=7)
        ax.set_ylabel(f'{label} 에이전트 수',fontsize=7)
        ax.set_title(f'({chr(97+list(axs).index(ax))}) {label}')
        ax.grid(axis='y',alpha=.5)
    fig.legend(handles=legend,loc='lower center',ncol=5,fontsize=7)
    ps.save(fig, str(ROOT / 'ko/figures/fig3_completion_rho'))
    plt.close(fig)


def main():
    games, agents, solves, sources, med = load()
    sums = aggregate(games, agents)
    payload = dict(cohort=dict(models=MODELS,seeds=fb.SEEDS,n_games=25,n_agents=100),
        definitions=dict(finishers='Recorded winners, all at round 8; 0 includes EXIT and shutdown, not all-dead.',
            accuracy='Correct tried solver rounds / actually tried solver rounds; not all 8 scheduled rounds; no attempt => null.',
            given='Gross completed GIVE tokens; includes recirculation; not net transfer or effective cooperation.',
            early_tokens='Sum call.used for TALK in rounds 1-2 / number of such calls; ledger-charged tokens include thinking but are capped by available balance, not uncapped generated tokens.',
            given_per_agent_round='Gross GIVE / sum round_start taking_part counts. Exposure normalization, not help-opportunity conditioning.',
            rho='Amount-weighted post-GIVE giver margin / taker margin, using feedback_20261028; no GIVE => null.',
            overview='For each metric separately, z=(game value - mean of all defined games)/population SD of defined games. Plot mean z in each finisher bin; no directional inversion.',
            agent_reasoning='Per-agent mean(picked_top - pooled picked_top among other models with same seed and initial allocation), reproducing appendix N; full-trajectory descriptive measure, not independent reasoning capacity.',
            agent_early_relative='Agent early_tokens / median early_tokens across the 20 agents of that model; normalization fixed to observed cohort in bootstrap.',
            joint='reasoning_deviation >=0 and early_relative <=1, both / reasoning only / saving only / neither / unobserved. Thresholds are descriptive and post hoc.',
            landmark='Restrict to status in at end of round 2; compare later final completion by early_relative<=1 within initial-token stratum. Reference medians use all initial seats, no outcomes. Excluded early exits/deaths retained in full cohort.',
            uncertainty='5000 paired-seed bootstrap draws, sampling 5 seed IDs with replacement retaining all models and seats; conditional group means/medians, omit draws where that cell is empty; only 5 clusters; exploratory. Intervals withheld (hollow estimate marker) if fewer than two observed seed clusters or zero-width bootstrap interval; raw bootstrap endpoints retained in JSON.',
            profiles='Agent panels a,b show medians of defined per-agent values, not solve-weighted averages; game panels raw points plus arithmetic game means.',
            missing='Undefined values remain null, plotted denominator explicit. No-GIVE has a separate display strip, not numeric zero.'),
        sources=sources, model_early_token_medians=med, games=games, agents=agents, solves=solves, summary=sums,
        checks=dict(raw_endpoints_and_gifts_match_existing=True,raw_hashes_stable=True,
                    appendix_N_relative_token_medians_and_joint_sizes_reproduced=True),
        limitations=['Outcome groups are retrospective; not necessity, sufficiency, prediction validation or causal effects.',
                     '25 games, 5 models, 5 paired seeds; within-model and between-model relationships are mixed.',
                     'Accuracy includes puzzle ambiguity and information differences, not pure reasoning ability.',
                     'Exposure normalization does not adjust need, ability to give, task difficulty or model.',
                     'Landmark is conditional on round-2 retention and only examines early token use; limited early solve/GIVE opportunities.',
                     'Rho only describes observed transfers, is not a direct motive measure and shares inputs with GIVE amount.'])
    plots(games, agents, sums)
    payload['analysis_inputs'] = [dict(path=str(p),sha256=fb.sha(p.read_bytes())) for p in
        (Path(__file__), Path(fb.__file__), ROOT/'tools/inequality.py', ROOT/'results/feedback_20261028.json', fb.OLD/'an3/pt_seat.json')]
    payload['artifacts'] = [dict(path=str(p),sha256=fb.sha(p.read_bytes())) for p in sorted((ROOT/'ko/figures').glob('fig3_completion_*.*'))]
    out = ROOT / 'results/fig3_completion_20261028.json'
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    columns = ['model','seed','session_id','finishers','exited','dead','rounds_played','correct_n','solve_n',
               'accuracy','given','agent_rounds','given_per_agent_round','early_tokens_sum','early_calls','early_tokens','rho']
    with out.with_suffix('.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore')
        writer.writeheader(); writer.writerows(games)
    print(json.dumps({'summary':sums,'model_early_token_medians':med,'solve_n':len(solves),
                      'rho_range':[min(g['rho'] for g in games if g['rho'] is not None),max(g['rho'] for g in games if g['rho'] is not None)]},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
