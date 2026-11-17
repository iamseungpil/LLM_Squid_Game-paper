"""Single-column outcome figure (2026-11-17, researcher): panel (a) of Figure 2 taken out on its own. One bar per
model from 0 to 1: the coexistence retention C on the left, then the lost coexistence 1 - C split by the event that
ended coexistence (shut-down, EXIT at L < 1, EXIT at L >= 1); last bar = the nine models' 90 base games pooled.
Same values and drawing as coexistence_figure_20261117.py panel (a) (no numbers on the bars), laid out for one column.

Output: ko/figures/construct_20261110/outcome_bars_20261117.{pdf,png}
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python outcome_bars_20261117.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_end_of_round_20261116 as ce  # noqa: E402

C_COLOR = '#7FA7C9'


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    import feedback_20261028 as fb
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})

    res = json.loads((ce.ROOT / 'results/c_end_of_round_20261116.json').read_text())
    order = res['figure2']['closed_order']
    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '$L<1$에서 이탈', 'exit_above': r'$L\geq1$에서 이탈'}
    rows = [(r['name'], r['loss'], 1 - r['lost']) for r in res['figure2']['rows']]
    assert len(rows) == 9
    pooled_loss = {t: float(np.mean([r[1][t] for r in rows])) for t in ce.cx.TAGS}     # ten games per model: equal weights
    pooled_c = float(np.mean([r[2] for r in rows]))
    assert abs(pooled_c + sum(pooled_loss.values()) - 1) < 1e-9
    rows.append(('전체', pooled_loss, pooled_c))
    ypos = [i + (.55 if i >= len(order) else 0) + (.55 if i >= 9 else 0) for i in range(len(rows))]

    fig, ax = plt.subplots(figsize=(3.3, 2.2))
    for y, (name, loss, c) in zip(ypos, rows):
        assert abs(c + sum(loss.values()) - 1) < 1e-9, name
        ax.barh(y, c, left=0, color=C_COLOR, edgecolor='white', linewidth=.4, height=.74)
        left = c
        for t in ce.cx.TAGS:
            ax.barh(y, loss[t], left=left, color=tag_colors[t], edgecolor='white', linewidth=.4, height=.74)
            left += loss[t]
    ax.set(yticks=ypos, yticklabels=[r[0] for r in rows], xlim=(0, 1), xticks=[0, .5, 1], ylim=(ypos[-1] + .6, -.6))
    ax.get_yticklabels()[-1].set_fontweight('bold')
    ax.set_xlabel('공존 $C$ (왼쪽)와 잃은 공존 $1-C$ (오른쪽)', fontsize=6.4, labelpad=1)
    ax.tick_params(axis='y', length=0, labelsize=6.2)
    ax.tick_params(axis='x', labelsize=6.0, length=2)
    fig.legend(handles=[Patch(color=C_COLOR, label='공존 $C$')] + [Patch(color=tag_colors[t], label=tag_labels[t]) for t in ce.cx.TAGS],
               loc='upper center', bbox_to_anchor=(.55, 1.0), ncol=4, fontsize=5.8, frameon=False, handlelength=.9,
               columnspacing=.8, handletextpad=.3)
    fig.subplots_adjust(left=.15, right=.97, bottom=.15, top=.9)
    for ext in ('pdf', 'png'):
        fig.savefig(ce.cb.DEST / f'outcome_bars_20261117.{ext}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    main()
