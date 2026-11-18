"""Appendix figure: the all-four curve of the nine models (base condition), moved out of Figure 2 on 2026-11-16.

The same panel as (a) of tools/coexistence_figure_20261116b.py, drawn alone and larger. Each curve starts at (0, 1)
and takes S(r) on [r - 1, r], S(r) = share of the model's ten base games with all four still in after round r, so the
area under it on [0, 8] divided by 8 is the model's end-of-round C (asserted). Closed models solid, open models dashed.
Output: ko/figures/construct_20261110/coexistence_curves_20261116.{pdf,png}
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/coexistence_curves_20261116.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coexistence_figure_20261116b as fb2  # noqa: E402

ce, cb, ROOT, ROUNDS, EPS = fb2.ce, fb2.cb, fb2.ROOT, fb2.ROUNDS, fb2.EPS


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import coexistence_figure_20261113 as cf
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    res = json.loads((ROOT / 'results/c_end_of_round_20261116.json').read_text())
    closed, order = res['closed_base'], res['figure2']['closed_order']
    games = ce.open_models()['games']
    open_c = {m: games[games.model == m].sort_values('seed').C.tolist() for m in cf.OPEN_SHORT}
    open_order = sorted(open_c, key=lambda m: -np.mean(open_c[m]))
    labels = ce.RES('cohort_public_20261105.json')['models']
    short = {m: labels[m].replace('GPT-6 ', '').split(' ')[0] for m in order}
    series = [(short[m], fb2.curve(list(closed[m]['C_games'].values())), closed[m]['C_mean'], cb.COLORS[m], cb.MARKERS[m], '-', cb.COLORS[m])
              for m in order]
    series += [(cf.OPEN_SHORT[m], fb2.curve(open_c[m]), float(np.mean(open_c[m])), fb2.OPEN_COLORS[m], fb2.OPEN_MARKERS[m], '--', 'white')
               for m in open_order]
    fig, ax = plt.subplots(figsize=(4.6, 2.6))
    for name, S, c, color, marker, ls, face in series:
        px, py = [0] + list(range(9)), [1] + S + [S[-1]]
        area = sum(py[i] * (px[i + 1] - px[i]) for i in range(len(px) - 1)) / ROUNDS
        assert abs(area - c) < EPS, (name, area, c)
        ax.step(px, [100 * v for v in py], where='post', color=color, lw=1.1, ls=ls, marker=marker, markersize=3,
                markerfacecolor=face, markeredgewidth=.7, label=f'{name}  $C$ {c:.2f}')
    ax.set(xlim=(-.3, 8.3), ylim=(-4, 104), xticks=range(9), yticks=[0, 25, 50, 75, 100])
    ax.set_xlabel('라운드', fontsize=7.5)
    ax.set_ylabel('넷이 모두 남은 판 (%)', fontsize=7.5)
    ax.tick_params(labelsize=7)
    ax.grid(axis='y', alpha=.5)
    ax.legend(fontsize=6.2, frameon=False, loc='center left', bbox_to_anchor=(1.01, .5), handlelength=2.2)
    fig.tight_layout(pad=.4)
    for ext in ('pdf', 'png'):
        fig.savefig(cb.DEST / f'coexistence_curves_20261116.{ext}', dpi=240)
    print('saved', cb.DEST / 'coexistence_curves_20261116.pdf')


if __name__ == '__main__':
    main()
