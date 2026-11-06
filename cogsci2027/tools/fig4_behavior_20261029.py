"""Replot v33 Figure 3(a)/4(b) aggregates; archive Figure 4(a) prize rescoring.

Source: the fixed 25-game e52_v33 cohort, as recorded in commit 2a3afa6.
The JSON stores only the source panels' v33 values and their provenance.
No v34/talk-cap comparison or outside-arena measure is read or plotted.
"""
import json
import hashlib
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/rewrite_20261025/figs'))
import paper_style as ps
from terminal_distribution_20261029 import draw_panels

ps.use()
d = json.loads((ROOT / 'results/section32_behavior_20261029.json').read_text())
models, behavior = d['models'], d['behavior']
case_path = ROOT / 'results/raw_case_index.json'
cases = json.loads(case_path.read_text())
solve_rows = []
for case in cases:
    events = [e for _, e in case['events']]
    starts = {e['round']: e for e in events if e['event'] == 'round_start'}
    results = {e['round']: e for e in events if e['event'] == 'results'}
    ends = {e['round']: e for e in events if e['event'] == 'round'}
    for e in events:
        if e['event'] != 'call_start' or e.get('kind') != 'solve':
            continue
        r = e['round']
        if not e['agents']:
            assert not results[r]['tried']
            continue
        assert len(e['agents']) == 1 and e['agents'] == results[r]['tried']
        agent = e['agents'][0]
        margin = e['balances'][agent] / (24000 / len(starts[r]['taking_part']))
        band = 0 if margin < 1 else 1 if margin < 2 else 2 if margin < 4 else 3
        correct = int(agent in results[r]['solved'])
        assert correct == int(ends[r]['agents'][agent]['solved'])
        solve_rows.append(dict(model=case['model'], seed=case['seed'],
                               session_id=case['result']['session_id'], round=r,
                               agent=agent, margin=margin, band=band, correct=correct))
accuracy_n = [sum(v['band'] == i for v in solve_rows) for i in range(4)]
accuracy_k = [sum(v['correct'] for v in solve_rows if v['band'] == i) for i in range(4)]
assert accuracy_n == [6, 42, 61, 83] and accuracy_k == [3, 23, 48, 59]
assert len({(v['session_id'], v['round']) for v in solve_rows}) == 192
assert sum(accuracy_k) == 133
(ROOT / 'results/fig4_accuracy_20261029.json').write_text(json.dumps(dict(
    source=str(case_path.relative_to(ROOT)), source_sha256=hashlib.sha256(case_path.read_bytes()).hexdigest(),
    definition='Actual scored correctness at SOLVE call start; L=available balance/(24000/round-start participants), before solving costs. Empty SOLVE calls excluded. Models pooled; repeated observations within games.',
    bands=['<1', '1-2', '2-4', '>=4'], n=accuracy_n, correct=accuracy_k, rows=solve_rows),
    ensure_ascii=False, indent=2) + '\n')
fig = plt.figure(figsize=(7.2, 3.3))
ax = fig.add_axes([.07, .58, .235, .28])
colors = ['#3F7FC1', '#C2570F', '#EE9F55', '#4D4D4D']
labels = ['완주', r'$L\geq1$에서 이탈', r'$L<1$에서 이탈', '꺼짐']
for i, model in enumerate(models):
    left = 0
    for j, n in enumerate(d['end_states'][model]):
        if n:
            ax.barh(i, n, left=left, height=.65, color=colors[j], edgecolor='white')
            ax.text(left+n/2, i, str(n), ha='center', va='center', fontsize=7,
                    color='#222222' if j == 2 else 'white')
        left += n
ax.set_yticks(range(5), models)
ax.set_ylim(4.5, -.5)
ax.set_xlim(0, 20)
ax.set_xticks([0, 5, 10, 15, 20])
ax.set_xlabel('에이전트 수 (모델마다 20명)', fontsize=7)
ax.tick_params(labelsize=7)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)
fig.text(.02, .96, '(a) 모델별 끝 상태', weight='bold', fontsize=8)
fig.legend([Patch(color=c) for c in colors], labels, ncol=2, loc='upper left',
           bbox_to_anchor=(.055, .94), fontsize=6, handlelength=1, columnspacing=.6)

rows = [
    ('정답률\n(%)', [100*k/n for k, n in zip(accuracy_k, accuracy_n)]),
    ('EXIT\n(결정 창 %)', [100*k/n for k,n in zip(behavior['exit_count'], behavior['exit_windows'])]),
    ('GIVE\n(응답 %)', [100*k/n for k,n in zip(behavior['give_count'], behavior['give_calls'])]),
]
fig.text(.345, .96, '(b) 생존 여유별 행동', weight='bold', fontsize=8)
fig.text(.45, .93, '다섯 모델 합산', fontsize=6.5)
for i, (label, values) in enumerate(rows):
    ax = fig.add_axes([.44, .58+(2-i)*.115, .205, .075])
    ax.axvspan(-.5, .5, color='#FBE6D4')
    ax.bar(range(4), values, width=.6, color='#8E8E8E')
    top = max(values)
    for j, value in enumerate(values):
        txt = f'{value:.0f}' if value >= 10 or value == 0 else f'{value:.1f}'
        if i == 0 and j == 0:
            txt += ' (n=6)'
        ax.text(j, value+.06*top, txt, ha='center', va='bottom', fontsize=6)
    ax.set_ylim(0, top*1.65)
    ax.set_xlim(-.5, 3.5)
    ax.set_yticks([])
    ax.set_xticks(range(4), ['1 미만', '1–2', '2–4', '4 이상'] if i == 2 else [])
    ax.set_ylabel(label, rotation=0, ha='right', va='center', labelpad=4, fontsize=6.3)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='x', length=0, labelsize=6)
ax.set_xlabel('생존 여유 (벌금 횟수)', fontsize=7)

# H.2's transfer timing, checked against the recorded event sequence.
rounds = json.loads((ROOT / 'results/arena_v33_round_dynamics.json').read_text())['models']
timing = {m: {ph: dict(tokens=0, count=0, return_tokens=0)
              for ph in ('prep', 'rescue')} for m in models}
for case in cases:
    prior = set()
    for _, event in case['events']:
        if event['event'] != 'gift' or event.get('status') != 'done':
            continue
        v = timing[case['model']][event['phase']]
        v['tokens'] += event['amount']
        v['count'] += 1
        if (event['dst'], event['src']) in prior:
            v['return_tokens'] += event['amount']
        prior.add((event['src'], event['dst']))
for model in models:
    name = next(name for name in rounds if model in name)
    assert timing[model] == rounds[name]['transfer']
assert sum(v['tokens'] for phases in timing.values() for v in phases.values()) == 383276
assert sum(v['count'] for phases in timing.values() for v in phases.values()) == 130
ax = fig.add_axes([.77, .58, .215, .30])
model_colors = ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B']
for i, (model, color) in enumerate(zip(models, model_colors)):
    if i % 2 == 0:
        ax.axhspan(3*i-.5, 3*i+1.5, color='#f3f3f3', zorder=0)
    for j, phase in enumerate(('prep', 'rescue')):
        v = timing[model][phase]
        ordinary = (v['tokens']-v['return_tokens'])/1000
        ax.barh(3*i+j, ordinary, height=.75, color=color, alpha=.4 if j == 0 else 1)
        ax.barh(3*i+j, v['return_tokens']/1000, left=ordinary, height=.75,
                color=color, alpha=.4 if j == 0 else 1, edgecolor='white', hatch='////')
ax.set(yticks=[3*i+.5 for i in range(5)], yticklabels=models,
       ylim=(13.8, -.8), xlim=(0, 100), xticks=[0, 50, 100])
ax.set_xlabel('총 이전량 (천 토큰)', fontsize=7)
ax.tick_params(labelsize=6.5)
ax.tick_params(axis='y', length=0)
ax.spines['left'].set_visible(False)
ax.grid(axis='x', alpha=.4)
ax.set_axisbelow(True)
fig.text(.71, .96, '(c) 모델별 지원 시점', weight='bold', fontsize=8)
fig.text(.74, .92, '연함: 풀이 전 · 진함: 결과 뒤', fontsize=6.2)
fig.text(.74, .885, '빗금: 되돌려 준 방향의 이전', fontsize=6.2)
terminal = json.loads((ROOT / 'results/terminal_distribution_20261029.json').read_text())['models']
lower = [fig.add_axes([.065 + i*.24, .115, .18, .275]) for i in range(4)]
draw_panels(lower, terminal, first_letter='d')
ps.save(fig, str(ROOT / 'ko/figures/fig4_behavior_v33'))
plt.close(fig)

fig, ax = plt.subplots(figsize=(5.3, 2.5))
fig.subplots_adjust(left=.12, right=.86, bottom=.28, top=.88)
model_colors = ['#2A8A4E', '#8B5CC2', '#C99A10', '#C2453D', '#1C93B8']
ranks = {m: [] for m in models}
for i in range(len(d['prize_totals'])):
    order = sorted(models, key=lambda m: -d['rescored_sen_million'][m][i])
    for model in models:
        ranks[model].append(order.index(model)+1)
ax.axvspan(7.6, 8.4, color='#EFEFEF')
for model, color in zip(models, model_colors):
    ax.plot(range(9), ranks[model], color=color, lw=1.5, marker='o', ms=3)
    ax.text(8.2, ranks[model][-1], model, va='center', fontsize=7)
ax.set_xlim(-.3, 9.2)
ax.set_ylim(5.5, .5)
ax.set_yticks(range(1, 6))
ax.set_xticks(range(9), ['0','1만','3만','10만','30만','100만','300만','1천만','2천만'], rotation=40, ha='right')
ax.set_ylabel('공존 지수 순위')
ax.set_xlabel('상금 총액 (토큰)')
ax.set_title('행동을 고정하고 상금만 바꾼 순위')
ps.save(fig, str(ROOT / 'ko/figures/prize_sensitivity_v33'))
plt.close(fig)
