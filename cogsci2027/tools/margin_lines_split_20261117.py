"""Appendix figure R.5 (2026-11-17, researcher): margin_lines_20261117 split into closed and open models, 2 x 2 panels
(rows: closed five, open four; columns: exit rate, retention ratio R). Same values (read from
results/margin_lines_20261117.json); each model's points are nudged sideways by a small fixed amount so that models
with the same value (e.g. three closed models at R = 0 in the L < 0 band) do not hide one another.

Output: ko/figures/construct_20261110/margin_lines_split_20261117.{pdf,png}
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python margin_lines_split_20261117.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import margin_lines_20261117 as ml  # noqa: E402

DODGE = .07                          # sideways step between models inside one band


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    out = json.loads((ml.ROOT / 'results/margin_lines_20261117.json').read_text())['models']
    mbp = ml.mbp
    groups = [('비공개 모델', mbp.CLOSED), ('공개 모델', list(mbp.OPEN))]
    names = {m: m for m in mbp.CLOSED} | mbp.OPEN
    style = {m: (mbp.cb.COLORS[m], mbp.cb.MARKERS[m], '-', mbp.cb.COLORS[m]) for m in mbp.CLOSED}
    style |= {m: (ml.OPEN_COLORS[m], ml.OPEN_MARKERS[m], '--', 'white') for m in mbp.OPEN}

    fig, axes = plt.subplots(2, 2, figsize=(6.6, 3.9), gridspec_kw=dict(width_ratios=[4, 5]))
    for row, (gname, models) in enumerate(groups):
        for col, (key, bands, title) in enumerate((('exit', ml.EXIT_BANDS, '이탈률'), ('R', ml.R_BANDS, '유보율 $R$'))):
            ax = axes[row, col]
            for j, m in enumerate(models):
                color, marker, ls, face = style[m]
                dx = (j - (len(models) - 1) / 2) * DODGE
                xs, ys, ns = [], [], []
                for i, (b, _, _) in enumerate(bands):
                    if key == 'exit':
                        k, n = out[m]['exit'][b]
                        y = k / n if n else None
                    else:
                        y, n = out[m]['R'][b]
                    if y is not None:
                        xs.append(i + dx), ys.append(y), ns.append(n)
                ax.plot(xs, ys, color=color, ls=ls, lw=1.0, zorder=2)
                for x, y, n in zip(xs, ys, ns):
                    size = 8 + 46 * np.sqrt(min(n, 400) / 400)
                    ax.scatter(x, y, s=size, marker=marker, color=face if n >= 5 else 'white', edgecolors=color, lw=.8, zorder=3)
            ax.set(xticks=range(len(bands)), xticklabels=[b for b, _, _ in bands], ylim=(-.04, 1.04), yticks=[0, .25, .5, .75, 1])
            ax.set_xlim(-.45, len(bands) - .55)
            ax.tick_params(labelsize=6.2, length=2, pad=1.5)
            ax.grid(axis='y', alpha=.4)
            ax.set_title(f'({"abcd"[2 * row + col]}) {gname}: {title}', loc='left', fontsize=7.4, pad=3)
            if row == 1:
                ax.set_xlabel('자기 여유 $L$', fontsize=6.8, labelpad=1)
            if col == 1:
                ax.set_yticklabels([])
        axes[row, 1].legend(handles=[Line2D([], [], color=style[m][0], ls=style[m][2], marker=style[m][1], ms=3.6, lw=1,
                                            markerfacecolor=style[m][3], markeredgewidth=.8, label=names[m]) for m in models],
                            loc='center left', bbox_to_anchor=(1.01, .5), fontsize=6.4, frameon=False, handlelength=2.2)
    fig.subplots_adjust(left=.06, right=.87, bottom=.1, top=.94, wspace=.06, hspace=.32)
    for ext in ('pdf', 'png'):
        fig.savefig(mbp.cb.DEST / f'margin_lines_split_20261117.{ext}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    main()
