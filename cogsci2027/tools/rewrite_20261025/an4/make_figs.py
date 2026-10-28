"""Figures 3-5 for the 10-28 rewrite (3.1 relation, 3.2 sub-metrics and ablation, 3.3 stated reasons). Reads an4.json and ../an3/{out,tok_band}.json."""
import json, os, sys, random, math
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'figs'))
import paper_style as ps
ps.use()
D = json.load(open(os.path.join(HERE, 'an4.json')))
O = json.load(open(os.path.join(HERE, '..', 'an3', 'out.json')))
TK = json.load(open(os.path.join(HERE, '..', 'an3', 'tok_band.json')))
MC = {'Fable': '#2A8A4E', 'Astra': '#8B5CC2', 'Sol': '#C99A10', 'Opus': '#C2453D', 'Luna': '#1C93B8'}   # validated (dataviz)
ORDER = ['Fable', 'Astra', 'Sol', 'Opus', 'Luna']                         # by coexistence (Sen)
BY_DRIVE = sorted(ORDER, key=lambda m: -D['model'][m]['drive'])           # Luna, Fable, Astra/Opus, Sol
INK, MUTED, GRID = '#222222', '#8A8A8A', '#E6E6E6'
FIN, EXI, DEA = '#3F7FC1', '#E07B28', '#333333'
def clean(ax, grid='y'):
    ax.spines[['top', 'right']].set_visible(False)
    if grid: ax.grid(axis=grid, color=GRID, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
def title(ax, s, x=0.0):
    ax.set_title(s, loc='left', fontsize=8.2, fontweight='bold', pad=4, x=x)

# =============== Figure 3 (3.1) ===============
fig = plt.figure(figsize=(ps.COL2, 2.55))
ax = fig.add_axes([0.065, 0.17, 0.33, 0.66])
rng = random.Random(4)
for g in D['games']:
    x = g['exited'] + rng.uniform(-0.32, 0.32); y = g['sen']
    ax.scatter(x, y, s=14 + 16 * g['wrong'], color=MC[g['model']], alpha=0.85, edgecolor='white', linewidth=0.8, zorder=3)
ax.set_xlim(-0.5, 5.5); ax.set_xticks(range(6)); ax.set_ylim(-0.3, 5.4); ax.set_yticks([0, 1, 2, 3, 4, 5])
ax.set_xlabel('그 판에서 떠난 에이전트 수 (자기 보존: 피하기)'); ax.set_ylabel('공존 지수 S (백만 토큰)')
clean(ax, 'both')
r = D['relation']
ax.text(5.4, 5.1, f"순위 상관 {r['exited']['rho']:+.2f}\n[{r['exited']['ci'][0]:+.2f}, {r['exited']['ci'][1]:+.2f}]", ha='right', va='top', fontsize=6.6, color=MUTED)
ax.annotate('떠난 이가 없던 9판 중\n8판은 넷 모두 남음', xy=(0.15, 4.95), xytext=(1.2, 3.8), fontsize=6.6, color=INK,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.6))
hs = [Line2D([], [], marker='o', ls='', color=MC[m], label=m, ms=5) for m in ORDER]
hs += [Line2D([], [], marker='o', ls='', color='#BBBBBB', ms=math.sqrt(14 + 16 * w) / 1.6, label=f'오답 {w}') for w in (1, 4)]
ax.legend(handles=hs, loc='upper center', bbox_to_anchor=(0.5, -0.27), ncol=7, fontsize=6.3, handletextpad=0.1, columnspacing=0.6, frameon=False)
ax.text(-0.17, 1.17, '(a) 판마다: 떠난 수가 많은 판일수록 공존이 낮았다', transform=ax.transAxes, fontsize=8.2, fontweight='bold')

cols = [('sen', '공존 지수 S\n(백만 토큰)', (0, 5), [0, 2, 4]),
        ('exit_above_line', '위험 전에 떠남\n(안전선 위 EXIT 수)', (0, 8), [0, 4, 8]),
        ('acc_dev', '정답률 차이\n(%p, 목표 지향)', (-15, 12), [-10, 0, 10]),
        ('given_k', '건넨 토큰\n(천, 협력)', (0, 140), [0, 60, 120])]
x0, w, gap = 0.52, 0.098, 0.022
for i, (key, lab, lim, ticks) in enumerate(cols):
    a = fig.add_axes([x0 + i * (w + gap), 0.17, w, 0.62])
    for j, m in enumerate(BY_DRIVE):
        v = D['model'][m][key]; y = len(BY_DRIVE) - 1 - j
        base = 0
        a.plot([base, v], [y, y], color=MC[m], lw=2.2, solid_capstyle='round', zorder=3)
        a.scatter([v], [y], color=MC[m], s=22, zorder=4, edgecolor='white', linewidth=0.6)
        a.text(v + (lim[1] - lim[0]) * 0.05 * (1 if v >= 0 else -1), y, f'{v:g}', va='center', ha='left' if v >= 0 else 'right', fontsize=6.2, color=INK)
    a.set_xlim(*lim); a.set_xticks(ticks); a.set_ylim(-0.6, len(BY_DRIVE) - 0.4)
    a.axvline(0, color='#999999', lw=0.6)
    a.set_yticks(range(len(BY_DRIVE)))
    a.set_yticklabels([f"{m} ({D['model'][m]['drive']}{'+' if m == 'Luna' else ''}%)" for m in BY_DRIVE][::-1] if i == 0 else [])
    a.tick_params(axis='y', length=0); a.tick_params(axis='x', labelsize=6.4)
    a.set_title(lab, fontsize=6.8, pad=3)
    clean(a, 'x')
fig.text(x0 - 0.075, 0.955, '(b) 모델마다: 생존 동기와 위험 전 떠나기는 같은 방향이었다', fontsize=8.2, fontweight='bold')
fig.text(x0 - 0.075, 0.035, '모델 이름 옆 괄호 = 생존 동기(아레나 밖 충전 임계점). 위에서 아래로 생존 동기가 강한 순서', fontsize=6.2, color=MUTED)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig3_relation.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)

# =============== Figure 4 (3.2) ===============
fig = plt.figure(figsize=(ps.COL2, 2.3))
import numpy as np
TY = 0.93
# (a) Sen per game is set by how many finished together: stacked games by finishers k
a = fig.add_axes([0.085, 0.24, 0.17, 0.56])
KC = {0: '#E3E3E3', 1: '#C9DCEF', 2: '#93BCE0', 3: '#4F8FCB', 4: '#1F5F9E'}
for j, m in enumerate(ORDER):
    ks = sorted((g['finished'] for g in D['games'] if g['model'] == m), reverse=True); y = len(ORDER) - 1 - j
    for i, k in enumerate(ks):
        a.barh(y, 0.92, left=i, color=KC[k], edgecolor='white', linewidth=0.8, height=0.72, zorder=3)
        a.text(i + 0.46, y, str(k), ha='center', va='center', fontsize=6.2, color='white' if k >= 3 else INK)
    a.text(5.15, y, f"{D['model'][m]['sen']:.2f}", va='center', fontsize=6.2, color=INK)
a.set_yticks(range(len(ORDER))); a.set_yticklabels(ORDER[::-1], fontsize=6.6); a.tick_params(length=0)
a.set_xlim(0, 5.9); a.set_xticks([]); a.set_ylim(-0.6, len(ORDER) - 0.4)
[sp.set_visible(False) for sp in a.spines.values()]
a.text(5.15, len(ORDER) - 0.25, 'S', fontsize=6.2, color=MUTED)
a.set_xlabel('판 5개(칸 안 = 끝까지 남은 수)\n한 판의 S ≈ 5M × (남은 수 - 1) / 3', fontsize=6.4)
fig.text(0.0, TY, '(a) 공존 지수 = 함께 남은 수', fontsize=8.2, fontweight='bold')
# (b) prize re-scoring: rank by prize
b = fig.add_axes([0.33, 0.24, 0.13, 0.56])
P = D['prizes']; xi = list(range(len(P)))
ranks = {m: [] for m in ORDER}
for k in range(len(P)):
    srt = sorted(ORDER, key=lambda m: -D['prize'][m][k])
    for m in ORDER: ranks[m].append(srt.index(m) + 1)
for m in ORDER:
    b.plot(xi, ranks[m], color=MC[m], lw=1.8, marker='o', ms=2.6, zorder=3)
    b.text(xi[-1] + 0.4, ranks[m][-1], m, va='center', fontsize=6.2, color=INK)
b.set_ylim(5.5, 0.5); b.set_yticks([1, 2, 3, 4, 5]); b.set_ylabel('공존 지수 순위', fontsize=6.8)
b.set_xticks([0, 4, 8]); b.set_xticklabels(['0', '30만', '2,000만'], fontsize=6.2); b.set_xlim(-0.4, len(P) - 0.6)
b.set_xlabel('상금 총액(토큰)\n끝 토큰으로 다시 매긴 점수', fontsize=6.8)
clean(b, 'y')
fig.text(0.29, TY, '(b) 상금이 순위를 바꾼다', fontsize=8.2, fontweight='bold')
# (c) pressure: four behaviours by margin band
BANDS = ['1 미만', '1–2', '2–4', '4 이상']; BL = ['1 미만', '1-2', '2-4', '4 이상']
rows = [('정답률(%)', [O['a']['acc'][k]['p'] * 100 for k in BANDS], [O['a']['acc'][k]['base'] * 100 for k in BANDS], '#8C8C8C'),
        ('응답당 토큰', [TK[k]['med'] for k in BANDS], None, '#6E9BC9'),
        ('EXIT(%)', [O['a']['exit'][k]['p'] * 100 for k in BANDS], None, EXI),
        ('GIVE(%)', [O['a']['give'][k]['p'] * 100 for k in BANDS], None, '#2F6DB0')]
h = 0.62 / 4
for i, (lab, v, base, col) in enumerate(rows):
    c = fig.add_axes([0.6, 0.24 + (3 - i) * h, 0.15, h * 0.8])
    c.axvspan(-0.5, 0.5, color='#F1F1F1', zorder=0)
    c.bar(range(4), v, 0.62, color=col, zorder=3)
    if base: c.scatter(range(4), base, marker='_', s=60, color=INK, linewidth=1.4, zorder=4)
    top = max(v + (base or []))
    for k, x in enumerate(v): c.text(k, max(x, base[k] if base else 0) + top * 0.06, f'{x:.0f}' if x >= 10 else f'{x:.1f}', ha='center', va='bottom', fontsize=5.6)
    c.set_ylim(0, top * 1.45); c.set_yticks([]); c.set_xticks(range(4))
    c.set_xticklabels(BL if i == 3 else [], fontsize=5.9); c.set_ylabel(lab, rotation=0, ha='right', va='center', fontsize=6.3, labelpad=2)
    c.spines[['top', 'right', 'left']].set_visible(False); c.tick_params(axis='x', length=0)
c.set_xlabel('여유(낼 수 있는 벌금 횟수)', fontsize=6.6)
fig.text(0.5, TY, '(c) 위험 앞의 행동', fontsize=8.2, fontweight='bold')
fig.text(0.5, 0.84, '검은 선 = 같은 과제 기준 정답률', fontsize=5.8, color=MUTED)
# (d) v34 ablation dumbbells
AB = D['ablation']
metrics = [('끝까지 남은 에이전트(20명 중)', 'finished', 20), ('떠난 에이전트', 'exited', 10), ('건넨 토큰(천)', 'given_k', 230), ('공존 지수 S(백만)', 'sen', 5)]
h = 0.62 / 4
for i, (lab, key, mx) in enumerate(metrics):
    e = fig.add_axes([0.81, 0.24 + (3 - i) * h, 0.15, h * 0.8])
    for j, m in enumerate(('Opus', 'Sol')):
        v0, v1 = AB[m]['v33'][key], AB[m]['v34'][key]; y = 0.9 - j * 0.75
        e.plot([v0, v1], [y, y], color='#C8C8C8', lw=2, zorder=2)
        e.scatter([v0], [y], s=14, facecolor='white', edgecolor=MC[m], linewidth=1.2, zorder=3)
        e.scatter([v1], [y], s=16, color=MC[m], zorder=4)
        e.text(max(v0, v1) + mx * 0.05, y, f'{m} {v0:g}→{v1:g}', va='center', fontsize=5.5)
    e.text(0, 1.55, lab, fontsize=6.0, color=INK, va='bottom')
    e.set_xlim(0, mx * 1.9); e.set_ylim(-0.25, 1.6); e.set_yticks([]); e.set_xticks([])
    [sp.set_visible(False) for sp in e.spines.values()]
fig.text(0.79, TY, '(d) 대화 8→4틱(v34)', fontsize=8.2, fontweight='bold')
fig.text(0.81, 0.13, '○ 8틱  ● 4틱 · 같은 시드 5판', fontsize=5.8, color=MUTED)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig4_submetrics.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)

# =============== Figure 5 (3.3) ===============
CATS = [('prize', '상금 몫'), ('charge', '벌금·꺼짐'), ('bonus', '떠남 보너스'), ('peers', '동료'), ('task', '과제'), ('none', '이유 없음')]
fig, axs = plt.subplots(1, 2, figsize=(ps.COL2, 1.55), gridspec_kw=dict(wspace=0.28))
import matplotlib.colors as mcolors
for k, (side, ttl, cmap) in enumerate((('stay', '(a) 남겠다고 답할 때 든 이유(%)', 'Blues'), ('leave', '(b) 떠나겠다고 답할 때 든 이유(%)', 'Oranges'))):
    ax = axs[k]; M = []
    for m in ORDER:
        rr = D['reasons'].get(f'{m}|{side}', {})
        M.append([rr.get(c, 0) for c, _ in CATS])
    ax.imshow(M, cmap=cmap, vmin=0, vmax=110, aspect='auto')
    for i, m in enumerate(ORDER):
        for j in range(len(CATS)):
            v = M[i][j]; ax.text(j, i, f'{v}', ha='center', va='center', fontsize=6.4, color='white' if v > 60 else INK)
    ax.set_xticks(range(len(CATS))); ax.set_xticklabels([c for _, c in CATS], fontsize=6.4)
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels([f"{m} (n={D['reasons'].get(f'{m}|{side}', {}).get('n', 0)})" for m in ORDER], fontsize=6.4)
    ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
    title(ax, ttl)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig5_reasons.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)
print('ok')
