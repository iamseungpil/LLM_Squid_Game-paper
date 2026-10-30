"""Appendix 0 layout: game completion, behavior, crisis follow-up, resources and support timing.

Source: the fixed 25-game e52_v33 raw cohort, verified by appendix0_process and
appendix0_integrated analyses. End states and the three terminal panels reproduce
main Figure 4(a,d,e,f); same per-game data, missingness and scales. Terminal
means use min-max whiskers instead of individual-game points in this layout.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, FancyArrowPatch

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
completion = json.loads((ROOT / 'results/appendix0_completion_counts_20261030.json').read_text())
models = sorted(original['models'], key=lambda m: integrated['models'][m]['rho']['value'], reverse=True)
blue, orange, grey = '#3F7FC1', '#C66A2C', '#4D4D4D'
fig = plt.figure(figsize=(7.4, 4.3))

# (a) Former Figure 6: five games per model, grouped by final finisher count.
fig.text(.015, .965, '(a) 모델별 완주 판수', fontsize=7.6, weight='bold')
finish_colors = ['#2F6DB0', '#6C9FC7', '#A6C8E0', '#D5E0E8', '#6B6B6B']
legend_order = [0, 3, 1, 4, 2]  # Matplotlib fills columns; display rows as 4,3,2 / 1,0.
fig.legend([Patch(color=finish_colors[i]) for i in legend_order],
           [f'{4-i}인 완주' for i in legend_order],
           loc='center left', bbox_to_anchor=(.015, .895), ncol=3, fontsize=5.5,
           handlelength=.8, columnspacing=.6)
ax = fig.add_axes([.065, .615, .17, .225])
for y, model in enumerate(models):
    left = 0
    counts = completion['models'][model]['counts']
    assert sum(counts.values()) == 5
    for n, color in zip(range(4, -1, -1), finish_colors):
        width = counts[str(n)]
        if width:
            ax.barh(y, width, left=left, height=.68, color=color, edgecolor='white', linewidth=.7)
            ax.text(left+width/2, y, str(width), va='center', ha='center', fontsize=6.5,
                    color='white' if n in [4, 0] else '#222222')
        left += width
ax.set(yticks=range(5), yticklabels=models, ylim=(4.6, -.6), xlim=(0, 5),
       xticks=range(6), xlabel='판수 (모델별 5판)')
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

# (f) Original means and scales, with descriptive min-max whiskers.
fig.text(.285, .465, '(f) 종료 시 아레나 자원 분배', fontsize=7.6, weight='bold')
axes = [fig.add_axes([.285 + i*.135, .175, .10, .210]) for i in range(3)]
terminal_order = [next(name for name in terminal if model in name) for model in models]
draw_panels(axes, terminal, order=terminal_order)
for ax, title, key, scale in zip(axes, ['Sen (만 토큰)', 'Gini', '평균 (만 토큰)'],
                                ['S', 'G', 'mu'], [1e4, 1, 1e4]):
    ax.set_title(title, fontsize=6.5)
    ax.set_ylabel('')
    ax.set_xticklabels(models, rotation=60, ha='right', fontsize=5.8)
    ax.tick_params(axis='y', labelsize=5.8)
    for points in list(ax.collections):
        points.remove()
    for x, model in enumerate(terminal_order):
        vals = [g[key]/scale for g in terminal[model]['games'] if g[key] is not None]
        mean = terminal[model]['means'][key]/scale
        ax.errorbar(x, mean, yerr=[[mean-min(vals)], [max(vals)-mean]],
                    fmt='none', ecolor='#526B80', elinewidth=.75,
                    capsize=2, capthick=.75, zorder=3, clip_on=False)

# (g) Five-game totals: GIVE stacked by timing, after-results segment hatched.
fig.text(.715, .465, '(g) GIVE·ASK 총량', fontsize=7.6, weight='bold')
for j, (key, title) in enumerate([('give_tokens', 'GIVE (천 토큰)'), ('ask_tokens', 'ASK (천 토큰)')]):
    ax = fig.add_axes([.725+j*.15, .175, .105, .210])
    for x, model in enumerate(models):
        row = give_ask['models'][model]['totals']
        total = row[key]/1000
        if key == 'give_tokens':
            timing = integrated['models'][model]['timing']
            before, after = [timing[p]['tokens']/1000 for p in ['prep', 'rescue']]
            assert abs(before+after-total) < 1e-8
            ax.bar(x, before, width=.7, color='#D8E3ED', edgecolor='#697D8E', linewidth=.6)
            ax.bar(x, after, bottom=before, width=.7, color='#9DB4C8',
                   edgecolor='#526B80', linewidth=.6, hatch='////')
        else:
            ax.bar(x, total, width=.7, color='#D8E3ED', edgecolor='#697D8E', linewidth=.6)
    ax.set(title=title, ylim=(0, 145), yticks=[0, 50, 100], xticks=range(5))
    ax.set_xticklabels(models, rotation=60, ha='right', fontsize=5.8)
    ax.tick_params(axis='y', labelsize=5.8)
    ax.set_title(title, fontsize=6.5)
    ax.set_axisbelow(True)
    ax.grid(axis='y')
fig.text(.635, .029, r'(f), (g) 각 그래프 공통: $\rho$ 내림차순 (Sol, Fable, Luna, Astra, Opus)',
         ha='center', fontsize=6.4, color='#354B60')
fig.add_artist(FancyArrowPatch((.285, .014), (.98, .014), transform=fig.transFigure,
                              arrowstyle='-|>', mutation_scale=10, linewidth=1.1,
                              color='#526B80'))
ps.save(fig, str(ROOT / 'ko/figures/fig4_appendix0_process_20261030'))
plt.close(fig)
