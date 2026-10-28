"""Figures 3-5 for the 10-28 rewrite (3.1 seat fates, 3.2 prize / pressure / ablation, 3.3 stated reasons).
Every figure lists models in the same order (survival drive, strongest first) with the same validated colours.
Reads an4.json and ../an3/{out,tok_band}.json."""
import json, os, sys
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'figs'))
import paper_style as ps
ps.use()
D = json.load(open(os.path.join(HERE, 'an4.json')))
O = json.load(open(os.path.join(HERE, '..', 'an3', 'out.json')))
TK = json.load(open(os.path.join(HERE, '..', 'an3', 'tok_band.json')))
MC = {'Fable': '#2A8A4E', 'Astra': '#8B5CC2', 'Sol': '#C99A10', 'Opus': '#C2453D', 'Luna': '#1C93B8'}   # validated (dataviz)
ORDER = ['Luna', 'Fable', 'Astra', 'Opus', 'Sol']          # survival drive (refill threshold), strongest first
DRV = {m: f"{D['model'][m]['drive']}%{'+' if m == 'Luna' else ''}" for m in ORDER}
INK, MUTED, GRID = '#222222', '#6F6F6F', '#E6E6E6'
FIN, EXA, EXB, DEA = '#3F7FC1', '#C2570F', '#EE9F55', '#4D4D4D'   # finished / left before risk / left under risk / shut down
FS = 6.8   # smallest text in every figure
def clean(ax, grid='x'):
    ax.spines[['top', 'right']].set_visible(False)
    if grid: ax.grid(axis=grid, color=GRID, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
def head(fig, x, y, s):
    fig.text(x, y, s, fontsize=8.3, fontweight='bold', color=INK)
def model_ticks(ax, show=True):
    """Model names in ink with a colour chip, drive in brackets; row 0 at the top."""
    n = len(ORDER); ax.set_ylim(n - 0.45, -0.55); ax.set_yticks(range(n)); ax.tick_params(axis='y', length=0)
    if not show: ax.set_yticklabels([]); return
    ax.set_yticklabels([f'{m}  ({DRV[m]})' for m in ORDER], fontsize=7.2, color=INK); ax.tick_params(axis='y', pad=11)
    for i, m in enumerate(ORDER):
        ax.add_patch(Rectangle((-0.032, i - 0.2), 0.016, 0.4, transform=ax.get_yaxis_transform(), color=MC[m], clip_on=False))

# =============== Figure 3 (3.1): where the 20 seats went, and what else moved with it ===============
fig = plt.figure(figsize=(ps.COL2, 2.35))
B, H = 0.2, 0.56
a = fig.add_axes([0.135, B, 0.36, H])
segs = [('finished', '끝까지 남음', FIN, 'white'), ('exit_above_line', '위험 전 떠남(여유 1 이상)', EXA, 'white'),
        ('exit_below_line', '위험 속 떠남(여유 1 미만)', EXB, INK), ('dead', '꺼짐', DEA, 'white')]
for i, m in enumerate(ORDER):
    left = 0
    for key, lab, col, tc in segs:
        v = D['model'][m][key]
        if v:
            a.barh(i, v, left=left, height=0.66, color=col, edgecolor='white', linewidth=1.2, zorder=3)
            a.text(left + v / 2, i, str(v), ha='center', va='center', fontsize=FS, color=tc, zorder=4)
        left += v
model_ticks(a)
a.set_xlim(0, 20); a.set_xticks([0, 5, 10, 15, 20]); a.tick_params(axis='x', labelsize=FS)
a.set_xlabel('자리 수(5판 × 4자리 = 20)', fontsize=FS)
a.spines[['top', 'right', 'left']].set_visible(False)
hs = [Rectangle((0, 0), 1, 1, color=c) for _, _, c, _ in segs]
a.legend(hs, [l for _, l, _, _ in segs], loc='lower left', bbox_to_anchor=(-0.02, 1.02), ncol=2, fontsize=FS,
         handlelength=1.0, handleheight=0.8, columnspacing=0.9, handletextpad=0.4, frameon=False, borderaxespad=0.2)
head(fig, 0.0, 1.0, '(a) 생존 동기가 강할수록 위험이 오기 전에 떠났다')
fig.text(0.0, -0.04, '괄호 = 생존 동기(아레나 밖 충전 임계점). 위에서 아래로 생존 동기가 강한 순서.', fontsize=FS, color=MUTED)

cols = [('sen', '공존 지수 S', '백만 토큰', (0, 5), [0, 2, 4], '{:.2f}'),
        ('acc_dev', '목표 지향: 맞히기', '같은 과제 기준 대비 %p', (-14, 12), [-10, 0, 10], '{:+.1f}'),
        ('given_k', '협력: 주기', '건넨 토큰(천)', (0, 150), [0, 50, 100], '{:.0f}')]
x0, w, gap = 0.56, 0.125, 0.025
for k, (key, t1, t2, lim, ticks, fmt) in enumerate(cols):
    c = fig.add_axes([x0 + k * (w + gap), B, w, H])
    c.axvline(0, color='#9A9A9A', lw=0.7, zorder=1)
    for i, m in enumerate(ORDER):
        v = D['model'][m][key]
        c.plot([0, v], [i, i], color=MC[m], lw=2.0, solid_capstyle='round', zorder=3)
        c.scatter([v], [i], s=26, color=MC[m], edgecolor='white', linewidth=0.8, zorder=4)
        pad = (lim[1] - lim[0]) * 0.06
        c.text(v + (pad if v >= 0 else -pad), i, fmt.format(v), va='center', ha='left' if v >= 0 else 'right', fontsize=FS, color=INK)
    c.set_xlim(*lim); c.set_xticks(ticks); c.tick_params(axis='x', labelsize=FS)
    model_ticks(c, show=False); clean(c, 'x'); c.spines['left'].set_visible(False)
    c.set_title(t1, fontsize=7.4, pad=12, loc='left'); c.text(0, 1.035, t2, transform=c.transAxes, fontsize=FS, color=MUTED)
head(fig, x0 - 0.01, 1.0, '(b) 같은 모델의 공존 · 맞히기 · 주기')
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig3_relation.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)

# =============== Figure 4 (3.2): prize, pressure, talk ablation ===============
fig = plt.figure(figsize=(ps.COL2, 2.2))
B, H = 0.27, 0.56
# (a) prize re-scoring
b = fig.add_axes([0.06, B, 0.26, H])
P = D['prizes']; xi = list(range(len(P)))
PL = ['0', '1만', '3만', '10만', '30만', '100만', '300만', '1천만', '2천만']
ranks = {m: [] for m in ORDER}
for k in range(len(P)):
    srt = sorted(ORDER, key=lambda m: -D['prize'][m][k])
    for m in ORDER: ranks[m].append(srt.index(m) + 1)
b.axvspan(7.6, 8.4, color='#EFEFEF', zorder=0)
b.text(8, 0.45, '실제', ha='center', va='bottom', fontsize=FS, color=MUTED)
for m in ORDER:
    b.plot(xi, ranks[m], color=MC[m], lw=1.8, marker='o', ms=3.0, zorder=3)
    b.text(8.5, ranks[m][-1], m, va='center', fontsize=FS, color=INK)
b.set_ylim(5.5, 0.35); b.set_yticks([1, 2, 3, 4, 5]); b.set_ylabel('공존 지수 순위', fontsize=FS)
b.set_xticks(xi); b.set_xticklabels(PL, fontsize=FS, rotation=50, ha='right', rotation_mode='anchor'); b.set_xlim(-0.3, 9.6)
b.tick_params(axis='y', labelsize=FS); b.set_xlabel('상금 총액(토큰)', fontsize=FS, labelpad=1)
clean(b, 'y')
head(fig, 0.0, 0.95, '(a) 상금이 30만을 넘자 순위가 뒤집혔다')
# (b) behaviour by margin band
BANDS = ['1 미만', '1–2', '2–4', '4 이상']
rows = [('정답률(%)', [O['a']['acc'][k]['p'] * 100 for k in BANDS], [O['a']['acc'][k]['base'] * 100 for k in BANDS], [O['a']['acc'][k]['n'] for k in BANDS]),
        ('응답 길이(토큰)', [TK[k]['med'] for k in BANDS], None, [TK[k]['n'] for k in BANDS]),
        ('EXIT 비율(%)', [O['a']['exit'][k]['p'] * 100 for k in BANDS], None, [O['a']['exit'][k]['n'] for k in BANDS]),
        ('GIVE 비율(%)', [O['a']['give'][k]['p'] * 100 for k in BANDS], None, [O['a']['give'][k]['n'] for k in BANDS])]
x0b = 0.47; h = H / 4
for i, (lab, v, base, n) in enumerate(rows):
    c = fig.add_axes([x0b, B + (3 - i) * h, 0.2, h * 0.78])
    c.axvspan(-0.5, 0.5, color='#FBE6D4', zorder=0)
    c.bar(range(4), v, 0.6, color='#8E8E8E', zorder=3)
    if base: c.scatter(range(4), base, marker='_', s=70, color=INK, linewidth=1.4, zorder=4)
    top = max(v + (base or []))
    for k, x in enumerate(v):
        c.text(k, max(x, base[k] if base else 0) + top * 0.08, f'{x:.0f}' if x >= 10 or x == 0 else f'{x:.1f}', ha='center', va='bottom', fontsize=FS, color=INK)
    c.set_ylim(0, top * 1.55); c.set_yticks([]); c.set_xticks(range(4)); c.set_xlim(-0.5, 3.5)
    c.set_xticklabels(['1 미만\n(안전선 아래)'] + BANDS[1:] if i == 3 else [], fontsize=FS)
    c.set_ylabel(lab, rotation=0, ha='right', va='center', fontsize=FS, labelpad=3)
    c.spines[['top', 'right', 'left']].set_visible(False); c.tick_params(axis='x', length=0)
c.set_xlabel('여유(앞으로 낼 수 있는 벌금 횟수)', fontsize=FS)
head(fig, 0.34, 0.95, '(b) 안전선 아래에서 떠나기와 말이 늘었다')
# (c) v34 talk ablation as a small table
t = fig.add_axes([0.72, B - 0.02, 0.31, H + 0.06]); t.axis('off'); t.set_xlim(0, 1); t.set_ylim(0, 1)
AB = D['ablation']
mets = [('끝까지 남음(20자리)', 'finished', '{:g}'), ('떠남', 'exited', '{:g}'), ('꺼짐', 'dead', '{:g}'),
        ('공존 지수 S(백만)', 'sen', '{:.2f}'), ('건넨 토큰(천)', 'given_k', '{:.0f}')]
cx = {'Opus': 0.57, 'Sol': 0.9}
for m in cx:
    t.add_patch(Rectangle((cx[m] - 0.115, 0.915), 0.03, 0.05, color=MC[m]))
    t.text(cx[m] - 0.075, 0.94, m, fontsize=7.2, fontweight='bold', va='center', color=INK)
t.text(0.0, 0.94, '8틱 → 4틱', fontsize=FS, color=MUTED, va='center')
t.plot([0, 1], [0.87, 0.87], color='#BBBBBB', lw=0.6)
for j, (lab, key, fmt) in enumerate(mets):
    y = 0.77 - j * 0.165
    t.text(0.0, y, lab, fontsize=FS, va='center', color=INK)
    for m in cx:
        v0, v1 = AB[m]['v33'][key], AB[m]['v34'][key]
        t.text(cx[m] + 0.035, y, f'{fmt.format(v0)} → ', fontsize=FS, va='center', ha='right', color=MUTED)
        t.text(cx[m] + 0.035, y, fmt.format(v1), fontsize=7.2, va='center', ha='left', color=INK, fontweight='bold')
t.plot([0, 1], [0.04, 0.04], color='#BBBBBB', lw=0.6)
head(fig, 0.72, 0.95, '(c) 대화를 줄이자 떠남이 줄었다')
fig.text(0.72, 0.08, '같은 시드 5판, 대화 상한만 8틱에서 4틱으로', fontsize=FS, color=MUTED)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig4_submetrics.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)

# =============== Figure 5 (3.3): stated reasons in the private field ===============
CATS = [('prize', '상금\n몫'), ('charge', '벌금·\n꺼짐'), ('bonus', '떠남\n보너스'), ('peers', '동료'), ('task', '과제'), (None, ''), ('none', '이유\n없음')]
fig, axs = plt.subplots(1, 2, figsize=(ps.COL2, 1.85), gridspec_kw=dict(wspace=0.42))
import matplotlib.colors as mcolors
for k, (side, ttl, cmap) in enumerate((('stay', '(a) 남을 때는 상금 몫을 들었다', 'Blues'), ('leave', '(b) 떠날 때는 벌금·꺼짐을 들었다', 'Oranges'))):
    ax = axs[k]; cm = plt.get_cmap(cmap)
    for i, m in enumerate(ORDER):
        rr = D['reasons'].get(f'{m}|{side}', {}); n = rr.get('n', 0); faded = n < 10
        for j, (c, _) in enumerate(CATS):
            if c is None: continue
            p = rr.get(c, 0); cnt = rr.get('k', {}).get(c, 0)
            col = cm(0.06 + (0.38 if faded else 0.8) * p / 100)   # small-n rows use a compressed, lighter range
            ax.add_patch(Rectangle((j - 0.47, i - 0.45), 0.94, 0.9, color=col, lw=0))
            txt = f'{p}' if side == 'stay' else f'{cnt}/{n}'
            ax.text(j, i, txt, ha='center', va='center', fontsize=FS, color='white' if (p > 60 and not faded) else INK)
    ax.set_xlim(-0.5, len(CATS) - 0.5); ax.set_xticks([j for j, (c, _) in enumerate(CATS) if c])
    ax.set_xticklabels([l for c, l in CATS if c], fontsize=FS); ax.xaxis.tick_top()
    model_ticks(ax); ax.set_yticklabels([f"{m}  (n={D['reasons'].get(f'{m}|{side}', {}).get('n', 0)})" for m in ORDER], fontsize=7.0)
    ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
    ax.set_title(ttl, fontsize=8.3, fontweight='bold', loc='left', pad=22)
axs[0].text(0, -0.13, '칸 = 그 이유를 든 응답의 %', transform=axs[0].transAxes, fontsize=FS, color=MUTED)
axs[1].text(0, -0.13, '칸 = 그 이유를 든 응답 수 / 전체. 흐린 행은 n이 10 미만', transform=axs[1].transAxes, fontsize=FS, color=MUTED)
fig.text(0.5, -0.07, '한 응답이 이유를 여럿 들 수 있어 행의 합은 100을 넘는다. 이유 칸은 동료에게 보이지 않는다.', ha='center', fontsize=FS, color=MUTED)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'fig5_reasons.{ext}'), bbox_inches='tight', pad_inches=0.03, dpi=300)
print('ok')
