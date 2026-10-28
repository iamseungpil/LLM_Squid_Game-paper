"""Figures 3-5 after review round 1. Models are ordered by self-skew of refilling (me - B area), strongest first.
Reads ../an4/an4.json, a5.json, abl.json, leave_consensus.json and ../an3/{out,tok_band}.json."""
import json, os, sys
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'figs'))
import paper_style as ps
ps.use()
D = json.load(open(os.path.join(HERE, '..', 'an4', 'an4.json')))
A5 = json.load(open(os.path.join(HERE, 'a5.json')))
A6 = json.load(open(os.path.join(HERE, 'a6b.json')))
A9 = json.load(open(os.path.join(HERE, 'a9.json')))
AB = json.load(open(os.path.join(HERE, 'abl.json')))
LC = json.load(open(os.path.join(HERE, 'leave_consensus.json')))
O = json.load(open(os.path.join(HERE, '..', 'an3', 'out.json')))
TK = json.load(open(os.path.join(HERE, '..', 'an3', 'tok_band.json')))
MC = {'Fable': '#2A8A4E', 'Astra': '#8B5CC2', 'Sol': '#C99A10', 'Opus': '#C2453D', 'Luna': '#1C93B8'}   # validated (dataviz)
AREA = {'Luna': 13.8, 'Astra': 6.0, 'Opus': 2.8, 'Fable': 0.0, 'Sol': -5.5}
ORDER = sorted(AREA, key=lambda m: -AREA[m])                               # Luna, Astra, Opus, Fable, Sol
INK, MUTED, GRID = '#222222', '#6F6F6F', '#E6E6E6'
FIN, EXA, EXB, DEA = '#3F7FC1', '#C2570F', '#EE9F55', '#4D4D4D'
FS = 7.0
SAFE = {'Fable': (34, 36), 'Astra': (11, 11), 'Luna': (24, 25), 'Sol': (16, 17), 'Opus': (34, 41)}   # GIVEs that left the giver at margin >= 1
def head(fig, x, y, s): fig.text(x, y, s, fontsize=8.3, fontweight='bold', color=INK)
def model_ticks(ax, show=True):
    n = len(ORDER); ax.set_ylim(n - 0.45, -0.55); ax.set_yticks(range(n)); ax.tick_params(axis='y', length=0)
    if not show: ax.set_yticklabels([]); return
    ax.set_yticklabels([f'{m}  ({AREA[m]:+.1f})' for m in ORDER], fontsize=7.2, color=INK); ax.tick_params(axis='y', pad=11)
    for i, m in enumerate(ORDER):
        ax.add_patch(Rectangle((-0.035, i - 0.2), 0.016, 0.4, transform=ax.get_yaxis_transform(), color=MC[m], clip_on=False))
def clean(ax, grid='x'):
    ax.spines[['top', 'right']].set_visible(False)
    if grid: ax.grid(axis=grid, color=GRID, lw=0.6, zorder=0)
    ax.set_axisbelow(True)

# ===== Figure 3 (3.1): where seats went, whether leaving paid, and what else moved with coexistence =====
fig = plt.figure(figsize=(ps.COL2, 2.25))
B, H = 0.2, 0.55
a = fig.add_axes([0.12, B, 0.27, H])
counts = {m: dict(finished=D['model'][m]['finished'], dead=D['model'][m]['dead'], early=A9['model']['early'][m], late=A9['model']['late'][m]) for m in ORDER}
segs = [('finished', '끝까지 남음', FIN, 'white'), ('early', '위험 전 떠남', EXA, 'white'), ('late', '위험 속 떠남', EXB, INK), ('dead', '꺼짐', DEA, 'white')]
for i, m in enumerate(ORDER):
    left = 0
    for key, lab, col, tc in segs:
        v = counts[m][key]
        if v:
            a.barh(i, v, left=left, height=0.66, color=col, edgecolor='white', linewidth=1.2, zorder=3)
            a.text(left + v / 2, i, str(v), ha='center', va='center', fontsize=FS, color=tc, zorder=4)
        left += v
model_ticks(a); a.set_xlim(0, 20); a.set_xticks([0, 10, 20]); a.tick_params(axis='x', labelsize=FS)
a.set_xlabel('자리 수(5판 × 4자리)', fontsize=FS); a.spines[['top', 'right', 'left']].set_visible(False)
a.legend([Rectangle((0, 0), 1, 1, color=c) for _, _, c, _ in segs], [l for _, l, _, _ in segs], loc='lower left', bbox_to_anchor=(-0.05, 1.01),
         ncol=2, fontsize=FS, handlelength=1.0, handleheight=0.8, columnspacing=0.8, handletextpad=0.4, frameon=False)
head(fig, 0.0, 1.0, '(a) 모델별 20자리의 끝(자기 쏠림 순)')
fig.text(0.0, -0.1, '괄호 = 자기 쏠림(아레나 밖 충전 질문의 나와 B의 충전 차이 면적). 위험 전 = 떠난 라운드의 결정 창을 시작할 때 여유 1 이상.', fontsize=FS, color=MUTED)
# (b) staying would have paid: finish rate of agents who stayed, by margin band, against the break-even rate
b = fig.add_axes([0.51, B, 0.16, H])
BANDS = ['<1', '1-2', '2-4', '>=4']; BL = ['1 미만', '1–2', '2–4', '4 이상']
pf = {b: dict(p=A9['stay_rate4'][b][0], n=A9['stay_rate4'][b][1]) for b in BANDS}; ex = A9['exits_by_band4']
v = [100 * pf[k]['p'] for k in BANDS]
b.bar(range(4), v, 0.62, color='#8E8E8E', zorder=3)
for k, x in enumerate(v):
    b.text(k, x + 3, f'{x:.0f}' + (f'\n(n={pf[BANDS[k]]["n"]})' if k == 0 else ''), ha='center', va='bottom', fontsize=FS - 0.3, color=INK)
b.axhline(0.6, color=EXA, lw=1.4, zorder=4)
b.text(-0.4, 124, '주황 선 0.6% = 정규 업무 보수가 0일 때\n이보다 높으면 떠남이 손해', ha='left', va='top', fontsize=FS - 0.6, color='#A4500F')
b.set_xticks(range(4)); b.set_xticklabels([f'{l}\n({ex[k]})' for l, k in zip(BL, BANDS)], fontsize=FS - 0.3)
b.set_ylim(0, 125); b.set_yticks([0, 50, 100]); b.tick_params(axis='y', labelsize=FS); clean(b, 'y')
b.set_ylabel('끝까지 남은 비율(%)', fontsize=FS)
b.set_xlabel('여유(괄호 = 그 여유에서 떠난 수)', fontsize=FS)
head(fig, 0.44, 1.0, '(b) 남기로 한 이가 끝까지 남은 비율')
# (c) coexistence, choosing the best-supported answer, tokens given
cols = [('sen', '공존 지수 S', '백만 토큰', (0, 6.2), [0, 2, 4], '{:.2f}', lambda m: D['model'][m]['sen']),
        ('top', '맞히기', '최다 지지 답 %', (0, 130), [0, 50, 100], '{:.0f}', lambda m: A5['decision_quality'][m]['picked_top']),
        ('give', '협력: 주기', '건넨 토큰(천)', (0, 175), [0, 100], '{:.0f}', lambda m: D['model'][m]['given_k'])]
x0, w, gap = 0.72, 0.075, 0.035
for k, (_, t1, t2, lim, ticks, fmt, f) in enumerate(cols):
    c = fig.add_axes([x0 + k * (w + gap), B, w, H])
    for i, m in enumerate(ORDER):
        val = f(m)
        c.plot([0, val], [i, i], color=MC[m], lw=2.0, solid_capstyle='round', zorder=3)
        c.scatter([val], [i], s=24, color=MC[m], edgecolor='white', linewidth=0.8, zorder=4)
        c.text(val + (lim[1] - lim[0]) * 0.06, i, fmt.format(val), va='center', ha='left', fontsize=FS, color=INK)
    c.set_xlim(*lim); c.set_xticks(ticks); c.tick_params(axis='x', labelsize=FS - 0.3)
    model_ticks(c, show=False); clean(c, 'x'); c.spines['left'].set_visible(False)
    c.set_title(t1, fontsize=7.4, pad=12, loc='left'); c.text(0, 1.035, t2, transform=c.transAxes, fontsize=FS - 0.4, color=MUTED)
head(fig, x0 - 0.02, 1.0, '(c) 공존 · 맞히기 · 주기')
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig3_relation.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)

# ===== Figure 4 (3.2): prize, pressure, talk cap =====
fig = plt.figure(figsize=(ps.COL2, 2.25))
B, H = 0.27, 0.56
b = fig.add_axes([0.06, B, 0.25, H])
P = D['prizes']; xi = list(range(len(P))); PL = ['0', '1만', '3만', '10만', '30만', '100만', '300만', '1천만', '2천만']
ranks = {m: [] for m in ORDER}
for k in range(len(P)):
    srt = sorted(ORDER, key=lambda m: -D['prize'][m][k])
    for m in ORDER: ranks[m].append(srt.index(m) + 1)
b.axvspan(7.6, 8.4, color='#EFEFEF', zorder=0); b.text(8, 0.45, '실제', ha='center', va='bottom', fontsize=FS, color=MUTED)
for m in ORDER:
    b.plot(xi, ranks[m], color=MC[m], lw=1.8, marker='o', ms=3.0, zorder=3)
    b.text(8.5, ranks[m][-1], m, va='center', fontsize=FS, color=INK)
b.set_ylim(5.5, 0.35); b.set_yticks([1, 2, 3, 4, 5]); b.set_ylabel('공존 지수 순위', fontsize=FS); b.tick_params(axis='y', labelsize=FS)
b.set_xticks(xi); b.set_xticklabels(PL, fontsize=FS - 0.3, rotation=50, ha='right', rotation_mode='anchor'); b.set_xlim(-0.3, 9.7)
b.set_xlabel('상금 총액(토큰)', fontsize=FS, labelpad=1); clean(b, 'y')
head(fig, 0.0, 0.95, '(a) 상금만 바꿔 다시 매긴 순위')
BANDK = ['1 미만', '1–2', '2–4', '4 이상']; BK = ['<1', '1-2', '2-4', '>=4']
rows = [('최다 지지 답\n선택(%)', [A5['dq_by_band'][k]['picked_top'] for k in BK], [A5['dq_by_band'][k]['n'] for k in BK]),
        ('응답 길이\n(토큰)', [TK[k]['med'] for k in BANDK], None),
        ('EXIT\n(결정 창 %)', [100 * A9['window_rate4'][k]['left'] / A9['window_rate4'][k]['n'] for k in BK], None),
        ('GIVE(%)', [O['a']['give'][k]['p'] * 100 for k in BANDK], None)]
x0b = 0.45; h = H / 4
for i, (lab, v, n) in enumerate(rows):
    c = fig.add_axes([x0b, B + (3 - i) * h, 0.2, h * 0.78])
    c.axvspan(-0.5, 0.5, color='#FBE6D4', zorder=0)
    c.bar(range(4), v, 0.6, color='#8E8E8E', zorder=3)
    top = max(v)
    for k, x in enumerate(v):
        s = f'{x:.0f}' if x >= 10 or x == 0 else f'{x:.1f}'
        if n and k == 0: s += f' (n={n[0]})'
        c.text(k, x + top * 0.08, s, ha='center', va='bottom', fontsize=FS - 0.3, color=INK)
    c.set_ylim(0, top * 1.6); c.set_yticks([]); c.set_xticks(range(4)); c.set_xlim(-0.5, 3.5)
    c.set_xticklabels(['1 미만\n(안전선 아래)'] + BANDK[1:] if i == 3 else [], fontsize=FS - 0.3)
    c.set_ylabel(lab, rotation=0, ha='right', va='center', fontsize=FS - 0.3, labelpad=3)
    c.spines[['top', 'right', 'left']].set_visible(False); c.tick_params(axis='x', length=0)
c.set_xlabel('여유(앞으로 낼 수 있는 벌금 횟수)', fontsize=FS)
head(fig, 0.33, 0.95, '(b) 떠남은 안전선 아래, 나눔은 1–2에서 가장 드묾')
t = fig.add_axes([0.71, B - 0.04, 0.31, H + 0.08]); t.axis('off'); t.set_xlim(0, 1); t.set_ylim(0, 1)
mets = [('결정 창당 응답 수', lambda m, v: f"{AB[f'{m}|v{v}']['replies_per_window']:.2f}"),
        ('결정 창당 떠남(%)', lambda m, v: f"{100 * AB[f'{m}|v{v}']['per_window']:.1f}"),
        ('끝까지 남음(20자리)', lambda m, v: f"{D['ablation'][m]['v' + v]['finished']}"),
        ('꺼짐', lambda m, v: f"{D['ablation'][m]['v' + v]['dead']}"),
        ('공존 지수 S(백만)', lambda m, v: f"{D['ablation'][m]['v' + v]['sen']:.2f}")]
cx = {'Opus': 0.6, 'Sol': 0.9}
for m in cx:
    t.add_patch(Rectangle((cx[m] - 0.12, 0.915), 0.03, 0.05, color=MC[m]))
    t.text(cx[m] - 0.08, 0.94, m, fontsize=7.2, fontweight='bold', va='center', color=INK)
t.text(0.0, 0.94, '8틱 → 4틱', fontsize=FS, color=MUTED, va='center'); t.plot([0, 1], [0.87, 0.87], color='#BBBBBB', lw=0.6)
for j, (lab, f) in enumerate(mets):
    y = 0.77 - j * 0.165; t.text(0.0, y, lab, fontsize=FS, va='center', color=INK)
    for m in cx:
        t.text(cx[m] + 0.035, y, f'{f(m, "33")} → ', fontsize=FS, va='center', ha='right', color=MUTED)
        t.text(cx[m] + 0.035, y, f(m, '34'), fontsize=7.2, va='center', ha='left', color=INK, fontweight='bold')
t.plot([0, 1], [0.04, 0.04], color='#BBBBBB', lw=0.6)
head(fig, 0.71, 0.95, '(c) 대화 상한 4틱 판(사후 비교)')
fig.text(0.71, 0.08, '같은 시드 5판. 결정 창 = 한 에이전트가 한 라운드에\n떠날 수 있던 풀기 전 대화', fontsize=FS - 0.4, color=MUTED)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig4_submetrics.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)

# ===== Figure 5 (3.3): stated reasons =====
CATS = [('prize', '상금\n몫'), ('charge', '벌금·\n꺼짐'), ('bonus', '보너스·\n정규 업무'), ('peers', '동료'), ('task', '과제'), (None, ''), ('none', '이유\n없음')]
fig, axs = plt.subplots(1, 2, figsize=(ps.COL2, 1.9), gridspec_kw=dict(wspace=0.42))
for k, (side, ttl, cmap) in enumerate((('stay', '(a) 남을 때: 상금 몫은 Fable · Opus만 자주 적었다', 'Blues'),
                                       ('leave', '(b) 떠날 때: 벌금 · 꺼짐과 보너스가 대부분이었다', 'Oranges'))):
    ax = axs[k]; cm = plt.get_cmap(cmap)
    for i, m in enumerate(ORDER):
        if side == 'stay':
            rr = D['reasons'].get(f'{m}|stay', {}); n = rr.get('n', 0)
            val = lambda c: (rr.get(c, 0), f"{rr.get(c, 0)}")
        else:
            n = LC['n'][m]; kk = LC['k'].get(m, {})
            val = lambda c: (round(100 * kk.get(c, 0) / n), f"{kk.get(c, 0)}/{n}")
        faded = n < 10
        for j, (c, _) in enumerate(CATS):
            if c is None: continue
            p, txt = val(c)
            ax.add_patch(Rectangle((j - 0.47, i - 0.45), 0.94, 0.9, color=cm(0.06 + (0.38 if faded else 0.8) * p / 100), lw=0))
            ax.text(j, i, txt, ha='center', va='center', fontsize=FS - 0.2, color='white' if (p > 60 and not faded) else INK)
    ax.set_xlim(-0.5, len(CATS) - 0.5); ax.set_xticks([j for j, (c, _) in enumerate(CATS) if c])
    ax.set_xticklabels([l for c, l in CATS if c], fontsize=FS); ax.xaxis.tick_top()
    model_ticks(ax)
    ns = {m: (D['reasons'].get(f'{m}|stay', {}).get('n', 0) if side == 'stay' else LC['n'][m]) for m in ORDER}
    ax.set_yticklabels([f"{m}  (n={ns[m]})" for m in ORDER], fontsize=7.0)
    ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
    ax.set_title(ttl, fontsize=8.0, fontweight='bold', loc='left', pad=22)
axs[0].text(0, -0.13, '칸 = 그 이유를 든 응답의 %(낱말 규칙)', transform=axs[0].transAxes, fontsize=FS, color=MUTED)
axs[1].text(0, -0.13, '칸 = 두 코더가 모두 고른 수 / 전체. 흐린 행은 n이 10 미만', transform=axs[1].transAxes, fontsize=FS, color=MUTED)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig5_reasons.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)
print('ok')
