"""Appendix 0 layout: support timing, behavior, crisis follow-up, resources and GIVE/ASK totals.

Source: the fixed 25-game e52_v33 raw cohort, verified by appendix0_process and
appendix0_integrated analyses. End states and the three terminal panels reproduce
main Figure 4(a,d,e,f); same per-game data, missingness, scales and plot marks.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/rewrite_20261025/figs'))
import paper_style as ps
from terminal_distribution_20261029 import draw_panels

ps.use()
plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'],
                     'axes.labelsize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5})
d = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
original = json.loads((ROOT / 'results/section32_behavior_20261029.json').read_text())
terminal = json.loads((ROOT / 'results/terminal_distribution_20261029.json').read_text())['models']
integrated = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())
give_ask = json.loads((ROOT / 'results/appendix0_give_ask_20261030.json').read_text())
models = sorted(original['models'], key=lambda m: integrated['models'][m]['rho']['value'], reverse=True)
blue, orange, grey = '#3F7FC1', '#C66A2C', '#4D4D4D'
fig = plt.figure(figsize=(7.4, 4.3))

# (a) Main Figure 4(c): model-specific timing and return-direction transfers.
fig.text(.015, .965, '(a) 모델별 지원 시점', fontsize=7.6, weight='bold')
fig.text(.025, .925, '연함: 풀이 전 · 진함: 결과 뒤', fontsize=6.1)
fig.text(.025, .890, '빗금: 되돌려 준 방향의 이전', fontsize=6.1)
ax = fig.add_axes([.065, .615, .17, .235])
colors = dict(zip(original['models'], ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B']))
for i, model in enumerate(models):
    if i % 2 == 0:
        ax.axhspan(3*i-.5, 3*i+1.5, color='#f3f3f3', zorder=0)
    for j, phase in enumerate(['prep', 'rescue']):
        row = integrated['models'][model]['timing'][phase]
        ordinary = (row['tokens']-row['return_tokens'])/1000
        ax.barh(3*i+j, ordinary, height=.75, color=colors[model], alpha=.4 if j == 0 else 1)
        ax.barh(3*i+j, row['return_tokens']/1000, left=ordinary, height=.75,
                color=colors[model], alpha=.4 if j == 0 else 1, edgecolor='white', hatch='////')
ax.set(yticks=[3*i+.5 for i in range(5)], yticklabels=models, ylim=(13.8, -.8),
       xlim=(0, 100), xticks=[0, 50, 100], xlabel='총 이전량 (천 토큰)')
ax.tick_params(axis='y', length=0)
ax.spines['left'].set_visible(False)
ax.grid(axis='x', alpha=.4)
ax.set_axisbelow(True)

# (b) Keep distinct units: solves, eligible EXIT windows, and TALK responses.
fig.text(.27, .965, '(b) 생존 여유별 행동', fontsize=7.6, weight='bold')
behavior = integrated['give_behavior']
rows = []
for key, flag, label in [('solves', 'correct', '정답률 (풀이 %)'),
                          ('windows', 'exited', 'EXIT (결정 창 %)')]:
    ns = [sum(x['band'] == b for x in d[key]) for b in range(4)]
    ks = [sum(x['band'] == b and x[flag] for x in d[key]) for b in range(4)]
    rows.append((ks, ns, label))
rows.append((behavior['count'], behavior['denominator'], 'GIVE (응답 %)'))
for j, (ks, ns, label) in enumerate(rows):
    ax = fig.add_axes([.30, .825-j*.105, .18, .065])
    ax.axvspan(-.5, .5, color='#F8E7D8', zorder=0)
    vals = [100*k/n for k, n in zip(ks, ns)]
    ax.bar(range(4), vals, .6, color=[grey, orange, blue][j], zorder=3)
    ymax, ticks = [(130, [0, 100]), (90, [0, 50]), (8, [0, 5])][j]
    for i, (k, n, value) in enumerate(zip(ks, ns, vals)):
        ax.text(i, value+ymax*.035, f'{k}/{n}', ha='center', fontsize=5.7)
    ax.set(ylim=(0, ymax), xlim=(-.5, 3.5), yticks=ticks)
    ax.set_title(label, fontsize=6.3, weight='normal', pad=2)
    ax.set_xticks(range(4), ['<1', '1–2', '2–4', '≥4'] if j == 2 else [])
    ax.grid(axis='y', zorder=0)
    if j == 2:
        ax.set_xlabel('생존 여유 (벌금 횟수)', labelpad=3)

# (c) Agent follow-up; denominator is the first-crisis cohort, not all agents.
fig.text(.515, .965, '(c) 첫 위기 이후 개인 완주', fontsize=7.6, weight='bold')
fig.text(.53, .925, '34명 · 19판 / 숫자는 인원', fontsize=6.1)
fig.legend([Patch(color=c) for c in [blue, orange, grey]], ['완주', 'EXIT', '꺼짐'],
           loc='center left', bbox_to_anchor=(.515, .885), ncol=3, fontsize=5.9,
           handlelength=.8, columnspacing=.6)
ax = fig.add_axes([.58, .615, .135, .225])
for i, group in enumerate(['none', 'short', 'lifted']):
    row = d['summary']['groups'][group]
    left = 0
    for status, color in [('in', blue), ('exited', orange), ('dead', grey)]:
        width = 100*row[status]/row['n']
        ax.barh(i, width, left=left, height=.57, color=color, edgecolor='white')
        if row[status]:
            ax.text(left+width/2, i, str(row[status]), ha='center', va='center', fontsize=6.5, color='white')
        left += width
    ax.text(103, i, f"{row['n']}명", va='center', fontsize=5.9)
ax.set(yticks=range(3), yticklabels=['미지원', '지원 후\n안전선 미만', '지원 후\n안전선 도달'],
       xlim=(0, 100), xticks=[0, 50, 100], ylim=(2.55, -.55), xlabel='최종 상태 (%)')
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0, labelsize=6)

# (d) Game exposure fixed at the first eligible crisis with four agents present.
fig.text(.755, .965, '(d) 첫 위기 이후 전원 완주', fontsize=7.6, weight='bold')
fig.text(.775, .925, '첫 위기 때 네 명이 남은 16판', fontsize=6.1)
ax = fig.add_axes([.795, .615, .18, .265])
for i, group in enumerate(['all_lifted', 'gap']):
    games = [g for g in d['games'] if g['coverage'] == group]
    for finished in range(5):
        subset = [g for g in games if g['finished'] == finished]
        offsets = np.linspace(-.23, .23, len(subset)) if len(subset) > 1 else [0]*len(subset)
        ax.scatter([i+x for x in offsets], [finished]*len(subset), s=14,
                   color=blue if finished == 4 else '#888888', zorder=3)
    ax.text(i, 4.52, f"{sum(g['all_four'] for g in games)}/{len(games)}판", ha='center', fontsize=6.5, color=blue)
ax.axhline(4, color=blue, lw=.7, ls=':', zorder=0)
ax.set(xlim=(-.5, 1.5), ylim=(-.35, 4.9), yticks=[0, 1, 2, 3, 4], xticks=range(2),
       xticklabels=['위기 인원 모두\n지원 후 도달', '미지원·미달\n한 명 이상'], ylabel='판별 완주 인원')
ax.grid(axis='y', zorder=0)

# (e) Main Figure 4(a), including both EXIT margin categories.
fig.text(.025, .465, '(e) 모델별 끝 상태', fontsize=8, weight='bold')
state_colors = [blue, '#C2570F', '#EE9F55', grey]
state_labels = ['완주', r'$L\geq1$에서 이탈', r'$L<1$에서 이탈', '꺼짐']
fig.legend([Patch(color=c) for c in state_colors], state_labels, ncol=2,
           loc='center left', bbox_to_anchor=(.025, .405), fontsize=6,
           handlelength=.9, columnspacing=.6)
ax = fig.add_axes([.065, .145, .18, .210])
for i, model in enumerate(models):
    left = 0
    for j, n in enumerate(original['end_states'][model]):
        if n:
            ax.barh(i, n, left=left, height=.65, color=state_colors[j], edgecolor='white')
            ax.text(left+n/2, i, str(n), ha='center', va='center', fontsize=6.5,
                    color='#222222' if j == 2 else 'white')
        left += n
    assert left == 20
ax.set(yticks=range(5), yticklabels=models, ylim=(4.5, -.5), xlim=(0, 20),
       xticks=[0, 5, 10, 15, 20], xlabel='에이전트 수 (각 20명)')
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)

# (f) Original terminal panels, compact and rho-ordered; values/axes unchanged.
fig.text(.285, .465, '(f) 종료 시 아레나 자원 분배', fontsize=7.6, weight='bold')
axes = [fig.add_axes([.285 + i*.135, .145, .10, .210]) for i in range(3)]
terminal_order = [next(name for name in terminal if model in name) for model in models]
draw_panels(axes, terminal, order=terminal_order)
for ax, title in zip(axes, ['Sen (만 토큰)', 'Gini', '평균 (만 토큰)']):
    ax.set_title(title, fontsize=6.5)
    ax.set_ylabel('')
    ax.set_xticklabels(models, rotation=60, ha='right', fontsize=5.8)
    ax.tick_params(axis='y', labelsize=5.8)
    for points in ax.collections:
        points.set_sizes([7])
fig.text(.285, .025, '막대: 판별 평균 · 점: 한 판 / Gini n=4·5·3·4·3', fontsize=5.8)

# (g) Figure 5 volume panels: five-game totals, no points; return hatch within GIVE.
fig.text(.715, .465, '(g) GIVE·ASK 총량', fontsize=7.6, weight='bold')
for j, (key, title) in enumerate([('give_tokens', 'GIVE (천 토큰)'), ('ask_tokens', 'ASK (천 토큰)')]):
    ax = fig.add_axes([.725+j*.15, .145, .105, .210])
    for x, model in enumerate(models):
        row = give_ask['models'][model]['totals']
        total = row[key]/1000
        ax.bar(x, total, width=.7, color='#D8E3ED', edgecolor='#697D8E', linewidth=.6)
        if key == 'give_tokens' and row['return_tokens']:
            returned = row['return_tokens']/1000
            ax.bar(x, returned, bottom=total-returned, width=.7, color='none',
                   edgecolor='#697D8E', linewidth=.6, hatch='////')
    ax.set(title=title, ylim=(0, 145), yticks=[0, 50, 100], xticks=range(5))
    ax.set_xticklabels(models, rotation=60, ha='right', fontsize=5.8)
    ax.tick_params(axis='y', labelsize=5.8)
    ax.set_title(title, fontsize=6.5)
    ax.set_axisbelow(True)
    ax.grid(axis='y')
fig.text(.715, .025, '막대: 5판 합계 · 빗금: 되돌려 줌', fontsize=5.8)
ps.save(fig, str(ROOT / 'ko/figures/fig4_appendix0_process_20261030'))
plt.close(fig)
