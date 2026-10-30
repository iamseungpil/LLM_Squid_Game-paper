"""Integrated Appendix 0: allocation and participation in fixed 25-game e52_v33.

Sources: appendix0_process_20261030.json and appendix0_integrated_20261030.json,
verified against original v33 event/results logs by the corresponding scripts.
All displays are descriptive; repeated events are nested within the same games.
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

ps.use()
plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'],
                     'axes.labelsize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5})
d = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
a = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())
models = list(a['models'])
blue, orange, grey = '#3F7FC1', '#C66A2C', '#4D4D4D'
colors = ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B']
fig = plt.figure(figsize=(7.4, 4.2))

# Model-specific transfer amount and timing, five games per model.
fig.text(.035, .966, '(a) 모델별 지원 시점과 양', fontsize=8, weight='bold')
fig.text(.055, .925, '연함: 풀이 전 · 진함: 결과 뒤', fontsize=6.4)
ax = fig.add_axes([.085, .605, .215, .28])
for i, (model, color) in enumerate(zip(models, colors)):
    for j, phase in enumerate(['prep', 'rescue']):
        v = a['models'][model]['timing'][phase]
        ordinary = (v['tokens'] - v['return_tokens']) / 1000
        ax.barh(3*i+j, ordinary, height=.8, color=color, alpha=.4 if j == 0 else 1)
        ax.barh(3*i+j, v['return_tokens']/1000, left=ordinary, height=.8,
                color=color, alpha=.4 if j == 0 else 1, edgecolor='white', hatch='////')
ax.set(yticks=[3*i+.5 for i in range(5)], yticklabels=models, ylim=(13.8, -.8),
       xlim=(0, 90), xticks=[0, 40, 80], xlabel='이전 총량 (천 토큰)')
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.grid(axis='x', alpha=.5)
ax.set_axisbelow(True)

# Paired post-transfer margins, conditional on actual completed transfers.
fig.text(.37, .966, '(b) 지원 직후 양쪽의 여유', fontsize=8, weight='bold')
ax = fig.add_axes([.415, .605, .215, .28])
gifts = d['gifts']
lift = [g for g in gifts if g['receiver_before'] < 1 <= g['receiver_after'] and g['giver_after'] >= 1]
ax.axvspan(-2, 1, color='#F8E7D8', zorder=0)
ax.axhspan(-2, 1, color='#F8E7D8', alpha=.7, zorder=0)
ax.axvline(1, color=orange, ls='--', lw=.7)
ax.axhline(1, color=orange, ls='--', lw=.7)
ax.scatter([g['giver_after'] for g in gifts], [g['receiver_after'] for g in gifts],
           s=10, color='#9B9B9B', alpha=.55, edgecolors='none')
ax.scatter([g['giver_after'] for g in lift], [g['receiver_after'] for g in lift],
           s=16, facecolors='none', edgecolors=blue, linewidths=.8, zorder=4)
ax.set(xlim=(-2, 12), ylim=(-2, 10), xticks=[-1, 1, 6, 12], yticks=[-1, 1, 5, 10],
       xlabel='준 쪽의 여유', ylabel='받은 쪽의 여유')
fig.text(.397, .925, '자신의 안전선 유지 119/120건', fontsize=6.4)
ax.legend([Line2D([], [], marker='o', color='none', markeredgecolor=blue, markersize=3)],
          ['양쪽 안전선 확보 24건'], loc='upper right', fontsize=5.9,
          handletextpad=.2, borderaxespad=.2)

# Different denominators retained: EXIT windows versus scored solves.
fig.text(.70, .966, '(c) 여유별 이탈과 정답률', fontsize=8, weight='bold')
for j, (key, flag, label) in enumerate([
        ('windows', 'exited', 'EXIT / 결정 창'), ('solves', 'correct', '정답 / 풀이')]):
    ax = fig.add_axes([.75, .785-j*.18, .225, .105])
    rows = d[key]
    ns = [sum(x['band'] == b for x in rows) for b in range(4)]
    ks = [sum(x['band'] == b and x[flag] for x in rows) for b in range(4)]
    ax.axvspan(-.5, .5, color='#F8E7D8', zorder=0)
    ax.bar(range(4), [100*k/n for k, n in zip(ks, ns)], .6,
           color=orange if j == 0 else grey, zorder=3)
    for i, (k, n) in enumerate(zip(ks, ns)):
        ax.text(i, 100*k/n+5, f'{k}/{n}', ha='center', fontsize=5.8)
    ax.set(ylim=(0, 130), xlim=(-.5, 3.5), yticks=[0, 100], ylabel='%')
    ax.set_title(label, fontsize=6.6, weight='normal', pad=3)
    ax.set_xticks(range(4), ['<1', '1–2', '2–4', '≥4'] if j else [])
    ax.grid(axis='y', zorder=0)
    if j:
        ax.set_xlabel('생존 여유 (벌금 횟수)', labelpad=3)

# Person-level first crisis outcomes, including deaths during the crisis round.
fig.text(.035, .466, '(d) 첫 위기 이후 개인 완주', fontsize=8, weight='bold')
fig.text(.055, .427, '34명 · 19판 / 막대 안 숫자는 인원', fontsize=6.3)
ax = fig.add_axes([.13, .12, .175, .235])
for i, group in enumerate(['none', 'short', 'lifted']):
    row = d['summary']['groups'][group]
    left = 0
    for status, color in [('in', blue), ('exited', orange), ('dead', grey)]:
        width = 100*row[status]/row['n']
        ax.barh(i, width, left=left, height=.57, color=color, edgecolor='white')
        if row[status]:
            ax.text(left+width/2, i, str(row[status]), ha='center', va='center', fontsize=7, color='white')
        left += width
    ax.text(103, i, f"{row['n']}명", va='center', fontsize=6)
ax.set(yticks=range(3), yticklabels=['미지원', '지원 후\n안전선 미만', '지원 후\n안전선 도달'],
       xlim=(0, 100), xticks=[0, 50, 100], ylim=(2.55, -.55), xlabel='최종 상태 (%)')
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)
fig.legend([Patch(color=c) for c in [blue, orange, grey]], ['완주', 'EXIT', '꺼짐'],
           loc='center left', bbox_to_anchor=(.05, .387), ncol=3, fontsize=6.2,
           handlelength=.9, columnspacing=.65)

# Game-level exposure fixed at the first eligible crisis with four agents present.
fig.text(.37, .466, '(e) 첫 위기 이후 전원 완주', fontsize=8, weight='bold')
fig.text(.395, .427, '첫 위기 때 네 명이 남아 있던 16판', fontsize=6.3)
ax = fig.add_axes([.415, .12, .215, .255])
for i, group in enumerate(['all_lifted', 'gap']):
    rows = [g for g in d['games'] if g['coverage'] == group]
    for finished in range(5):
        subset = [g for g in rows if g['finished'] == finished]
        offsets = np.linspace(-.23, .23, len(subset)) if len(subset) > 1 else [0]*len(subset)
        ax.scatter([i+x for x in offsets], [finished]*len(subset), s=15,
                   color=blue if finished == 4 else '#888888', zorder=3)
    ax.text(i, 4.52, f"{sum(g['all_four'] for g in rows)}/{len(rows)}판", ha='center', fontsize=7, color=blue)
ax.axhline(4, color=blue, lw=.7, ls=':', zorder=0)
ax.set(xlim=(-.5, 1.5), ylim=(-.35, 4.9), yticks=[0, 1, 2, 3, 4], xticks=range(2),
       xticklabels=['위기 인원 모두\n지원 후 안전선 도달', '미지원·미달\n한 명 이상'], ylabel='판별 완주 인원')
ax.grid(axis='y', zorder=0)

# Compact numeric summary avoids mixing unlike scales or omitting Gini missingness.
fig.text(.70, .466, '(f) 종료 시 아레나 자원 분배', fontsize=8, weight='bold')
fig.text(.718, .427, '모델별 판 평균 · 상금·EXIT 보유분 제외', fontsize=6.2)
ax = fig.add_axes([.695, .125, .295, .26])
ax.axis('off')
rows = []
for model in models:
    m = a['models'][model]['means']
    rows.append([model, f"{m['mu']/1000:.2f}", f"{m['G']:.2f}",
                 f"{m['S']/1000:.2f}", f"{m['finishers']:.1f}"])
table = ax.table(cellText=rows, colLabels=['모델', '평균\n(천 토큰)', 'Gini', 'Sen\n(천 토큰)', '완주\n(명)'],
                 cellLoc='center', colWidths=[.21, .23, .15, .23, .18], bbox=[0, 0, 1, 1])
table.auto_set_font_size(False)
table.set_fontsize(6.4)
for (r, c), cell in table.get_celld().items():
    if r == 0:
        cell.set_height(cell.get_height()*1.5)
    cell.set_edgecolor('#D9D9D9')
    cell.set_linewidth(.3)
    cell.set_facecolor('#E8EFF5' if r == 0 else '#F5F5F5' if r % 2 else 'white')
fig.text(.71, .065, 'Gini 유효 판수: 5 / 4 / 4 / 3 / 3', fontsize=6.2)
fig.text(.71, .03, '평균·Sen·완주 인원: 모델마다 5판', fontsize=6.2)
ps.save(fig, str(ROOT / 'ko/figures/fig4_appendix0_process_20261030'))
plt.close(fig)
