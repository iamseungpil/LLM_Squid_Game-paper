"""Two layout drafts of Figure R.5 at the size of a two-column body figure (2026-11-17, researcher), for choosing the
new process figure of the body:
  rows2  the 2 x 2 of R.5 pressed down to about the height of the present Figure 2 (rows: closed, open models;
         columns: exit rate, retention ratio R)
  rows1  the four panels in one row (closed exit, closed R, open exit, open R)
Same values as R.5 (results/margin_lines_20261117.json), same per-model sideways nudge.

Output: ko/figures/construct_20261110/margin_lines_rows2_20261117.{pdf,png}, margin_lines_rows1_20261117.{pdf,png}
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python margin_lines_layouts_20261117.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import margin_lines_20261117 as ml  # noqa: E402

DODGE = .07


def panel(ax, out, models, style, key, bands, ms_scale):
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
        ax.plot(xs, ys, color=color, ls=ls, lw=.9, zorder=2)
        for x, y, n in zip(xs, ys, ns):
            size = ms_scale * (4 + 26 * np.sqrt(min(n, 400) / 400))
            ax.scatter(x, y, s=size, marker=marker, color=face if n >= 5 else 'white', edgecolors=color, lw=.7, zorder=3)
    ax.set(xticks=range(len(bands)), xticklabels=[b for b, _, _ in bands], ylim=(-.05, 1.05), yticks=[0, .5, 1])
    ax.set_xlim(-.45, len(bands) - .55)
    ax.tick_params(labelsize=5.6, length=2, pad=1.2)
    ax.grid(axis='y', alpha=.4)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    out = json.loads((ml.ROOT / 'results/margin_lines_20261117.json').read_text())['models']
    mbp = ml.mbp
    closed, opened = mbp.CLOSED, list(mbp.OPEN)
    names = {m: m for m in closed} | mbp.OPEN
    style = {m: (mbp.cb.COLORS[m], mbp.cb.MARKERS[m], '-', mbp.cb.COLORS[m]) for m in closed}
    style |= {m: (ml.OPEN_COLORS[m], ml.OPEN_MARKERS[m], '--', 'white') for m in opened}
    handle = lambda m: Line2D([], [], color=style[m][0], ls=style[m][2], marker=style[m][1], ms=3, lw=.9,  # noqa: E731
                              markerfacecolor=style[m][3], markeredgewidth=.7, label=names[m])
    cols = (('exit', ml.EXIT_BANDS, '이탈률'), ('R', ml.R_BANDS, '유보율 $R$'))

    # rows2: two rows, about the height of the present Figure 2
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 2.3), gridspec_kw=dict(width_ratios=[4, 5]))
    for r, (gname, models) in enumerate((('비공개', closed), ('공개', opened))):
        for c, (key, bands, title) in enumerate(cols):
            ax = axes[r, c]
            panel(ax, out, models, style, key, bands, .8)
            ax.set_title(f'({"abcd"[2 * r + c]}) {gname} 모델: {title}', loc='left', fontsize=6.6, pad=2)
            if c == 1:
                ax.set_yticklabels([])
            if r == 0:
                ax.set_xticklabels([])
        axes[r, 1].legend(handles=[handle(m) for m in models], loc='center left', bbox_to_anchor=(1.01, .5), fontsize=5.6,
                          frameon=False, handlelength=2.0, labelspacing=.25)
    axes[1, 0].set_xlabel('자기 여유 $L$', fontsize=6.2, labelpad=1)
    axes[1, 1].set_xlabel('자기 여유 $L$', fontsize=6.2, labelpad=1)
    fig.subplots_adjust(left=.05, right=.89, bottom=.12, top=.93, wspace=.05, hspace=.32)
    for ext in ('pdf', 'png'):
        fig.savefig(mbp.cb.DEST / f'margin_lines_rows2_20261117.{ext}', dpi=300)
    plt.close(fig)

    # rows1: one row of four panels
    fig, axes = plt.subplots(1, 4, figsize=(7.1, 1.75), gridspec_kw=dict(width_ratios=[4, 5, 4, 5]))
    for p, (gname, models, (key, bands, title)) in enumerate([('비공개', closed, cols[0]), ('비공개', closed, cols[1]),
                                                              ('공개', opened, cols[0]), ('공개', opened, cols[1])]):
        ax = axes[p]
        panel(ax, out, models, style, key, bands, .8)
        ax.set_title(f'({"abcd"[p]}) {gname}: {title}', loc='left', fontsize=6.6, pad=2)
        ax.set_xlabel('자기 여유 $L$', fontsize=6.0, labelpad=1)
        if p in (1, 3):
            ax.set_yticklabels([])
    fig.legend(handles=[handle(m) for m in closed + opened], loc='upper center', ncol=9, fontsize=5.6, frameon=False,
               bbox_to_anchor=(.5, 1.0), handlelength=2.0, columnspacing=.9, handletextpad=.3)
    fig.subplots_adjust(left=.04, right=.995, bottom=.2, top=.78, wspace=.12)
    for p in (1, 3):                                   # pair each exit panel with its R panel: less gap inside a pair
        pos = axes[p].get_position()
        axes[p].set_position([pos.x0 - .012, pos.y0, pos.width, pos.height])
    for ext in ('pdf', 'png'):
        fig.savefig(mbp.cb.DEST / f'margin_lines_rows1_20261117.{ext}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    main()
