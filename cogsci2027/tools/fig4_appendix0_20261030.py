"""Appendix 0 layout: paired margins, behavior, crisis follow-up and resources.

Source: the fixed 25-game e52_v33 raw cohort, verified by appendix0_process and
appendix0_integrated analyses. End states and the three terminal panels reproduce
main Figure 4(a,d,e,f); same per-game data, missingness, scales and plot marks.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
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
models = original['models']
blue, orange, grey = '#3F7FC1', '#C66A2C', '#4D4D4D'
fig = plt.figure(figsize=(7.4, 4.3))

# (a) GIVE events; shaded area is below the safety line.
fig.text(.015, .965, '(a) 지원 직후 양쪽의 여유', fontsize=7.6, weight='bold')
fig.text(.025, .925, '자신의 안전선 유지 119/120건', fontsize=6.1)
ax = fig.add_axes([.06, .615, .17, .265])
gifts = d['gifts']
lift = [g for g in gifts if g['receiver_before'] < 1 <= g['receiver_after'] and g['giver_after'] >= 1]
ax.axvspan(-2, 1, color='#F8E7D8', zorder=0)
ax.axhspan(-2, 1, color='#F8E7D8', alpha=.7, zorder=0)
ax.axvline(1, color=orange, ls='--', lw=.7)
ax.axhline(1, color=orange, ls='--', lw=.7)
ax.scatter([g['giver_after'] for g in gifts], [g['receiver_after'] for g in gifts],
           s=9, color='#9B9B9B', alpha=.55, edgecolors='none')
ax.scatter([g['giver_after'] for g in lift], [g['receiver_after'] for g in lift],
           s=15, facecolors='none', edgecolors=blue, linewidths=.8, zorder=4)
ax.set(xlim=(-2, 12), ylim=(-2, 10), xticks=[-1, 1, 6, 12], yticks=[-1, 1, 5, 10],
       xlabel='준 쪽의 여유', ylabel='받은 쪽의 여유')
ax.legend([Line2D([], [], marker='o', color='none', markeredgecolor=blue, markersize=3)],
          ['동료 안전선 도달\n양쪽 안전선 이상 (24건)'], loc='upper right', fontsize=5.9,
          handletextpad=.1, borderaxespad=.15)

# (b) Keep distinct units: solves, eligible EXIT windows, and TALK responses.
fig.text(.27, .965, '(b) 생존 여유별 행동', fontsize=7.6, weight='bold')
behavior = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())['give_behavior']
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
ax = fig.add_axes([.075, .105, .205, .255])
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
       xticks=[0, 5, 10, 15, 20], xlabel='에이전트 수 (모델마다 20명)')
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)

# (f) Reuse original plotting function for main Figure 4(d,e,f), narrower only.
fig.text(.345, .465, '(f) 종료 시 아레나 자원 분배', fontsize=8, weight='bold')
axes = [fig.add_axes([.355 + i*.22, .105, .17, .255]) for i in range(3)]
draw_panels(axes, terminal)
for ax, title in zip(axes, ['Sen 지수', 'Gini 계수', '평균 토큰']):
    ax.set_title(title, fontsize=7.6)
fig.text(.345, .025, '막대: 판별 값의 평균 · 점: 한 판 / Gini 유효 판수 5·4·4·3·3, Sen·평균 토큰은 각 5판', fontsize=6)
ps.save(fig, str(ROOT / 'ko/figures/fig4_appendix0_process_20261030'))
plt.close(fig)
