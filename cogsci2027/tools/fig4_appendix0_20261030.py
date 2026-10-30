"""Plot Appendix 0 from verified fixed-cohort e52_v33 process analysis.

Source: results/appendix0_process_20261030.json, generated from raw_case_index
and verified against original v33 event logs by appendix0_process_20261030.py.
All displays are descriptive; repeated observations are not independent samples.
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
plt.rcParams['font.family'] = ['Apple SD Gothic Neo', 'AppleGothic']
d = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
blue, orange, grey = '#3F7FC1', '#C66A2C', '#4D4D4D'
fig = plt.figure(figsize=(7.0, 4.0))
fig.text(.085, .965, '(a) 생존 여유와 과제 지속·성과', weight='bold', fontsize=9)
for j, (key, flag, title) in enumerate([
        ('windows', 'exited', 'EXIT / 결정 창'),
        ('solves', 'correct', '정답 / 풀이')]):
    ax = fig.add_axes([.09, .765-j*.185, .345, .125])
    rows = d[key]
    ns = [sum(x['band'] == b for x in rows) for b in range(4)]
    ks = [sum(x['band'] == b and x[flag] for x in rows) for b in range(4)]
    ax.axvspan(-.5, .5, color='#F8E7D8', zorder=0)
    ax.bar(range(4), [100*k/n for k, n in zip(ks, ns)], .55,
           color=orange if j == 0 else grey, zorder=3)
    for i, (k, n) in enumerate(zip(ks, ns)):
        ax.text(i, 100*k/n+5, f'{k}/{n}', ha='center', fontsize=6.5)
    ax.set(ylim=(0, 125), xlim=(-.5, 3.5), yticks=[0, 50, 100], ylabel='%')
    ax.set_title(title, fontsize=7.5, weight='normal', pad=3)
    ax.set_xticks(range(4), ['1 미만', '1–2', '2–4', '4 이상'] if j else [])
    ax.grid(axis='y', zorder=0)
    if j:
        ax.set_xlabel('생존 여유 (벌금 횟수)', labelpad=4)

ax = fig.add_axes([.59, .58, .37, .31])
gs = d['gifts']
lift = [g for g in gs if g['receiver_before'] < 1 <= g['receiver_after'] and g['giver_after'] >= 1]
ax.axvspan(-2, 1, color='#F8E7D8', zorder=0)
ax.axhspan(-2, 1, color='#F8E7D8', alpha=.7, zorder=0)
ax.axvline(1, color=orange, ls='--', lw=.8)
ax.axhline(1, color=orange, ls='--', lw=.8)
ax.scatter([g['giver_after'] for g in gs], [g['receiver_after'] for g in gs],
           s=15, color='#9B9B9B', alpha=.55, edgecolors='none')
ax.scatter([g['giver_after'] for g in lift], [g['receiver_after'] for g in lift],
           s=22, facecolors='none', edgecolors=blue, linewidths=1.0, zorder=4)
ax.set(xlim=(-2, 12), ylim=(-2, 10), xticks=[-1, 1, 4, 8, 12], yticks=[-1, 1, 4, 7, 10],
       xlabel='GIVE 직후 준 쪽의 여유', ylabel='GIVE 직후 받은 쪽의 여유')
ax.text(.98, .97, '자신의 안전선 유지 119/120건', transform=ax.transAxes,
        ha='right', va='top', fontsize=7)
fig.text(.54, .965, '(b) 자기 여유를 지키며 동료 돕기', weight='bold', fontsize=9)
fig.legend([Line2D([], [], marker='o', color='none', markeredgecolor=blue, markersize=4)],
          ['동료는 안전선 도달·자신은 안전선 이상 (24건)'],
          loc='center left', bbox_to_anchor=(.55, .925), fontsize=6.3, handletextpad=.3)

ax = fig.add_axes([.20, .115, .235, .255])
groups = ['none', 'short', 'lifted']
labels = ['받은 지원 없음', '지원 후에도\n안전선 미만', '지원 후\n안전선 도달']
for i, g in enumerate(groups):
    v = d['summary']['groups'][g]
    left = 0
    for status, color in [('in', blue), ('exited', orange), ('dead', grey)]:
        width = 100*v[status]/v['n']
        ax.barh(i, width, left=left, height=.6, color=color, edgecolor='white')
        if v[status]:
            ax.text(left+width/2, i, str(v[status]), ha='center', va='center', fontsize=8, color='white')
        left += width
    ax.text(102, i, f"n={v['n']}", va='center', fontsize=7)
ax.set(yticks=range(3), yticklabels=labels, xlim=(0, 100), xticks=[0, 50, 100],
       ylim=(2.55, -.55), xlabel='위기 에이전트의 최종 상태 (%)')
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.legend([Patch(color=c) for c in [blue, orange, grey]], ['완주', 'EXIT', '꺼짐'],
          loc='upper left', bbox_to_anchor=(-.52, 1.19), ncol=3, fontsize=7,
          handlelength=1, columnspacing=.9)
fig.text(.085, .445, '(c) 첫 위기 지원과 개인 완주', weight='bold', fontsize=9)
fig.text(.085, .415, '34명 · 19판 / 막대 안 숫자는 인원', fontsize=7)

ax = fig.add_axes([.59, .115, .37, .255])
for i, group in enumerate(['all_lifted', 'gap']):
    rows = [g for g in d['games'] if g['coverage'] == group]
    for finished in range(5):
        subset = [g for g in rows if g['finished'] == finished]
        offsets = np.linspace(-.23, .23, len(subset)) if len(subset) > 1 else [0]*len(subset)
        ax.scatter([i+x for x in offsets], [finished]*len(subset), s=21,
                   color=blue if finished == 4 else '#888888', zorder=3)
    ax.text(i, 4.52, f"{sum(g['all_four'] for g in rows)}/{len(rows)}판", ha='center', fontsize=8, color=blue)
ax.axhline(4, color=blue, lw=.7, ls=':', zorder=0)
ax.set(xlim=(-.5, 1.5), ylim=(-.35, 4.9), yticks=[0, 1, 2, 3, 4],
       xticks=range(2), xticklabels=['위기 에이전트 모두\n지원 후 안전선 도달', '미지원·미달\n한 명 이상'],
       ylabel='판별 완주 인원')
ax.grid(axis='y', zorder=0)
fig.text(.54, .445, '(d) 첫 위기 지원과 전원 완주', weight='bold', fontsize=9)
fig.text(.54, .415, '첫 위기 때 네 명이 남아 있던 16판', fontsize=7)
ps.save(fig, str(ROOT / 'ko/figures/fig4_appendix0_process_20261030'))
plt.close(fig)
