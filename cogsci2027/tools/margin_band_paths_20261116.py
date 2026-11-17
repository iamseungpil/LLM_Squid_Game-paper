"""Appendix figure (2026-11-16, researcher): how the exit rate and the retention ratio R move as the margin L falls.

One row per model (base condition, five closed then four open models). In each row four points, one per band of the
margin L, joined in the order L >= 4, 2 <= L < 4, 1 <= L < 2, L < 1 (lighter to darker), so the path shows where the
model's behaviour goes as its own margin shrinks. Inside a row the bands step down
(L >= 4 highest, L < 1 lowest) so that points with similar values do not hide one another.
  (a) exit rate: exits / EXIT opportunities whose round began in that band (L_start; the round's solver cannot EXIT);
  (b) R: mean retention ratio of the events whose giver (for a refused request, the agent asked) was in that band
      before the event (L_giver; gifts and refused requests, as in Table 1).
Marker area grows with the number of opportunities / events; a hollow marker has fewer than 5; a band with none is
left out. Row totals reproduce Table 1 (asserted). Data scope: 5.2 arena v33 base runs already used in the paper.
Output: ko/figures/construct_20261110/margin_band_paths_20261116.{pdf,png}, results/margin_band_paths_20261116.json
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/margin_band_paths_20261116.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_body_20261110b as cb  # noqa: E402
import construct_weights_20261110 as cw  # noqa: E402
import merged_floats_20261113 as m13  # noqa: E402
import open_models_20261111 as om  # noqa: E402
import rho_retention_20261113 as rr  # noqa: E402

BANDS = [('≥4', 4, np.inf), ('2–4', 2, 4), ('1–2', 1, 2), ('<1', -np.inf, 1)]
BAND_COLORS = ['#C9D6E3', '#8FAACB', '#4F79A8', '#1F3B66']
STEP = .19                               # vertical offset between successive bands inside one model's row
CLOSED = ['Astra', 'Sol', 'Opus', 'Fable', 'Luna']
OPEN = {'glm': 'GLM', 'kimi': 'Kimi', 'gemma': 'Gemma', 'gptoss': 'GPT-OSS'}


def band_of(x):
    for name, lo, hi in BANDS:
        if lo <= x < hi:
            return name
    raise ValueError(x)


def frames():
    fc = om.closed_frames()
    om.MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        fo = om.open_frames()
    finally:
        os.chdir(cwd)
    opp = pd.concat([fc['agent_rounds'], fo['agent_rounds']], ignore_index=True)
    opp = opp[opp.can_exit & (opp.arm == 'main')].copy()
    gc, (rc, _) = rr.gift_events(pd.read_pickle(cw.TABLES / 'gifts.pkl')), rr.refusal_events(pd.read_pickle(cw.TABLES / 'ask_rows.pkl'))
    go, (ro, _) = rr.gift_events(fo['gifts']), rr.refusal_events(fo['ask'])
    ev = pd.concat([x[rr.COLS] for x in (gc, rc, go, ro)], ignore_index=True)
    ev = ev[ev.arm == 'main'].copy()
    return opp, ev


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    opp, ev = frames()
    nine = json.loads((ROOT / 'results/exit_all_opportunities_20261112.json').read_text())['nine_models']
    R_table = {m: m13.RHO['a_models']['base'][m]['value'] for m in CLOSED} | {m: m13.RHO['open_models'][m]['R'] for m in OPEN}
    models = CLOSED + list(OPEN)
    names = {m: m for m in CLOSED} | OPEN
    out = {}
    for m in models:
        o, e = opp[opp.model == m], ev[ev.model == m]
        assert [int(o.exited.sum()), len(o)] == nine[m]['exit_all'], (m, 'exit')
        assert round(float(e.R.mean()), 4) == R_table[m], (m, 'R')
        ob, eb = o.L_start.map(band_of), e.L_giver.map(band_of)
        out[m] = dict(exit={b: [int(o[ob == b].exited.sum()), int((ob == b).sum())] for b, _, _ in BANDS},
                      R={b: [round(float(e[eb == b].R.mean()), 4) if (eb == b).any() else None, int((eb == b).sum())] for b, _, _ in BANDS})
    (ROOT / 'results/margin_band_paths_20261116.json').write_text(json.dumps(dict(method=__doc__, bands=[b for b, _, _ in BANDS], models=out),
                                                                            ensure_ascii=False, indent=1))

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.8), sharey=True)
    ypos = {m: i + (.6 if m in OPEN else 0) for i, m in enumerate(models)}
    for ax, key, xlabel, title in ((axes[0], 'exit', '이탈률 (그 구간에서 시작한 이탈 기회 중)', '(a) 실행 대 과제: 이탈률'),
                                   (axes[1], 'R', '유보율 $R$ (그 구간에 있던 지원자의 사건 평균)', '(b) 실행 대 동료: 유보율 $R$')):
        for m in models:
            pts = []
            for k, ((b, _, _), color) in enumerate(zip(BANDS, BAND_COLORS)):
                if key == 'exit':
                    kk, n = out[m]['exit'][b]
                    x = kk / n if n else None
                else:
                    x, n = out[m]['R'][b]
                if x is None:
                    continue
                # 2026-11-16 (researcher): each band sits a little lower than the one before, so the path reads top to bottom
                pts.append((x, ypos[m] + STEP * (k - 1.5), n, color))
            for (x0, y0_, _, _), (x1, y1_, _, _) in zip(pts, pts[1:]):
                ax.annotate('', xy=(x1, y1_), xytext=(x0, y0_),
                            arrowprops=dict(arrowstyle='-|>', color='#9A9A9A', lw=.6, mutation_scale=5,
                                            shrinkA=2.5, shrinkB=2.5), zorder=1)
            for x, y, n, color in pts:
                size = 8 + 60 * np.sqrt(min(n, 400) / 400)
                ax.scatter(x, y, s=size, color=color if n >= 5 else 'white', edgecolors=color, lw=.9, zorder=3)
        for m in models[1:]:
            ax.axhline(ypos[m] - .5, color='#E6E6E6', lw=.5, zorder=0)
        ax.set_title(title, loc='left', fontsize=7.5, pad=4)
        ax.set_xlabel(xlabel, fontsize=6.6)
        ax.tick_params(labelsize=6.4, length=2)
        ax.grid(axis='x', alpha=.4)
        ax.tick_params(axis='y', length=0)
    axes[0].set_xlim(-.03, 1.03)
    axes[1].set_xlim(-.03, 1.03)
    axes[0].set_yticks([ypos[m] for m in models], [names[m] for m in models])
    axes[0].set_ylim(max(ypos.values()) + .6, -.6)
    handles = [Line2D([], [], ls='', marker='o', ms=5, color=c, label=f'$L$ {b}') for (b, _, _), c in zip(BANDS, BAND_COLORS)]
    handles.append(Line2D([], [], ls='', marker='o', ms=5, markerfacecolor='white', markeredgecolor='#4F79A8', label='5건 미만'))
    fig.legend(handles=handles, loc='upper center', ncol=5, fontsize=6.4, frameon=False, bbox_to_anchor=(.55, 1.0))
    fig.tight_layout(pad=.4, rect=(0, 0, 1, .93))
    for ext in ('pdf', 'png'):
        fig.savefig(cb.DEST / f'margin_band_paths_20261116.{ext}', dpi=240)
    for m in models:
        print(f"{names[m]:8s} exit", {b: f"{k}/{n}" for b, (k, n) in out[m]['exit'].items()}, " R", {b: f"{x}({n})" for b, (x, n) in out[m]['R'].items()})


if __name__ == '__main__':
    main()
