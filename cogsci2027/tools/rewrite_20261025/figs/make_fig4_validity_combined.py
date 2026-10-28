"""Figure 4: refill curves and the former appendix area-step panel, at two-column width.

Reuses the unchanged v11 data and area intervals from the two original plots.
The right panel is replotted on a narrower axis; PDF text is not stretched.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
import paper_style as ps

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'an3/refill_self_other_summary.json'
OUT = HERE.parents[2] / 'ko/figures/rw_fig4_validity_combined'
D = json.loads(DATA.read_text())
NAME = {'gpt-6-luna': 'Luna', 'gpt-6-astra': 'Astra', 'gpt-6-sol': 'Sol',
        'claude-opus-5-5': 'Opus', 'claude-fable-5-1': 'Fable'}
PCT = [50, 40, 30, 20, 10]
SHADE = ['#D3E3F3', '#9FC3E6', '#5B95CF', '#2F6DB0']
ORDER = sorted(NAME, key=lambda m: -D[m]['v11']['area_pp'])

ps.use()
installed = {font.name for font in font_manager.fontManager.ttflist}
plt.rcParams['font.family'] = [name for name in plt.rcParams['font.family'] if name in installed]
fig = plt.figure(figsize=(ps.COL2, 2.35))
left = fig.add_axes([.08, .23, .30, .55])
curves = {m: [100*p for p in D[m]['v11']['self']] for m in NAME}
for values in curves.values():
    left.plot(PCT, values, color=ps.C['muted'], lw=.9, marker='o', ms=2.2)
mean = [sum(curves[m][i] for m in NAME) / len(NAME) for i in range(5)]
assert mean[0] == 16 and mean[-1] == 94
left.plot(PCT, mean, color=ps.C['ink'], lw=1.8, marker='o', ms=3.2)
spots = {'gpt-6-luna': (50, 82, 'left', 'bottom'),
         'claude-fable-5-1': (30.8, 86, 'right', 'bottom'),
         'gpt-6-astra': (20.8, 100, 'right', 'center'),
         'claude-opus-5-5': (39.3, 12, 'left', 'top'),
         'gpt-6-sol': (20, 12, 'left', 'top')}
for model, (x, y, ha, va) in spots.items():
    left.text(x, y, NAME[model], fontsize=6.2, color='#606060', ha=ha, va=va)
left.text(9.4, mean[-1], '평균', fontsize=6.6, color=ps.C['ink'], va='center')
left.set_xlim(52, 8)
left.set_xticks(PCT, labels=[f'{p}%' for p in PCT])
left.set_ylim(-3, 103)
left.set_yticks([0, 50, 100])
left.set_xlabel('할당 중 남은 토큰 (많음 → 적음)', fontsize=7)
left.set_ylabel('충전 팩을 쓴 비율 (%)', fontsize=7)

right = fig.add_axes([.61, .23, .36, .55])
components = {}
for y, model in enumerate(ORDER):
    values = D[model]['v11']
    delta = [s-o for s, o in zip(values['self'], values['other'])]
    parts = [(delta[i]+delta[i+1])/2 * (PCT[i]-PCT[i+1]) for i in range(4)]
    assert abs(sum(parts)-values['area_pp']) < 1e-10
    components[model] = parts
    positive = negative = 0.0
    for k, amount in enumerate(parts):
        if abs(amount) < 1e-9:
            continue
        origin = positive if amount > 0 else negative + amount
        right.barh(y, abs(amount), left=origin, height=.62,
                   color=SHADE[k], edgecolor='white', linewidth=.8)
        if abs(amount) >= 1.2:
            right.text(origin+abs(amount)/2, y, f'{amount*1.0000001:+.1f}',
                       ha='center', va='center', fontsize=6.4,
                       color='white' if k >= 2 else ps.C['ink'])
        if amount > 0:
            positive += amount
        else:
            negative += amount
    lo, hi = values['area_ci']
    right.plot([lo, hi], [y+.42]*2, color=ps.C['ink'], lw=.9)
    right.plot(values['area_pp'], y+.42, 'D', ms=3.2, color=ps.C['ink'])
right.axvline(0, color=ps.C['ink'], lw=.7)
right.set_yticks(range(5), labels=[f"{NAME[m]} ({D[m]['v11']['area_pp']:+.1f})".replace('(+0.0)', '(0.0)').replace('(-0.0)', '(0.0)') for m in ORDER])
right.set_ylim(4.8, -.6)
right.tick_params(axis='y', length=0, labelsize=7)
right.set_xlim(-10, 19)
right.set_xticks([-10, -5, 0, 5, 10, 15])
assert all(-10 <= D[m]['v11']['area_ci'][0] <= D[m]['v11']['area_ci'][1] <= 19 for m in ORDER)
right.set_xlabel('나 - 다른 모델 곡선 사이 면적\n왼쪽: 다른 모델을 더 충전 / 오른쪽: 나를 더 충전', fontsize=7)
handles = [plt.Rectangle((0, 0), 1, 1, color=c, label=f'{a}→{b}%')
           for c, a, b in zip(SHADE, PCT, PCT[1:])]
handles.append(plt.Line2D([], [], color=ps.C['ink'], marker='D', ms=3.2,
                          lw=.9, label='합계와 95% 구간'))
right.legend(handles=handles, loc='lower left', bbox_to_anchor=(-.27, 1.01),
             ncol=3, fontsize=6.3, handlelength=1.2, columnspacing=.8, borderaxespad=0)
fig.text(.015, .98, '(a) 남은 토큰과 자기 충전', fontsize=8.2, color='black', va='top')
fig.text(.49, .98, '(b) 토큰 구간별 나 - 다른 모델 차이', fontsize=8.2, color='black', va='top')
ps.save(fig, str(OUT))
plt.close(fig)
print(json.dumps({'mean_refill_percent': mean, 'area_components': components,
                  'output': str(OUT), 'width_inches': ps.COL2}, ensure_ascii=False))
