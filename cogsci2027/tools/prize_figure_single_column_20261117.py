"""Single-column variant of Figure 4 (prize size and allocation rule), 2026-11-17 (researcher).

Same values as ko/figures/construct_20261110/prize_interaction_20261116.pdf (c_end_of_round_20261116.prize_figure):
panels (a)-(c) sit side by side in one narrow row, panel (d) runs below them, wide and short. The original
two-column figure is kept; this file only adds a new one. The C cells and the C contrasts are read from
results/c_end_of_round_20261116.json (end of round); the exit and R values come from the same loaders the
original figure uses.

Output: ko/figures/construct_20261110/prize_interaction_single_20261117.{pdf,png}
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python prize_figure_single_column_20261117.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_end_of_round_20261116 as ce  # noqa: E402

OUT = 'prize_interaction_single_20261117'


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import feedback_20261028 as fb
    import merged_floats_20261113 as m13
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})

    stored = ce.RES('c_end_of_round_20261116.json')
    cells_c = stored['prize_cells']['end']['cells']
    eff_c = {k: v for k, v in stored['prize_2x2']['end'].items() if k.startswith('C_')}
    RHO = m13.RHO
    cells = ce.RES('prize_one_factor_20261111.json')['cells']
    eff = ce.RES('construct_weights_20261110.json')['prize_2x2']
    allopp = ce.mf.all_opportunities()
    cells['exit'] = {a: dict(mean=v['value'], ci95=v['ci95']) for a, v in allopp['arm'].items()}
    cells['R'] = {a: dict(mean=v['value'], ci95=v['ci95']) for a, v in RHO['b_prize']['cells'].items()}
    cells['C'] = cells_c
    for kind in ('size', 'rule'):
        eff[f'exit_risk_{kind}'] = dict(effect=allopp['contrasts'][kind]['value'], ci95=allopp['contrasts'][kind]['ci95'])
        eff[f'R_{kind}'] = dict(effect=RHO['b_prize']['contrasts'][kind]['value'], ci95=RHO['b_prize']['contrasts'][kind]['ci95'])
        eff[f'C_{kind}'] = eff_c[f'C_{kind}']
    rules = [('분할', ('main', 'split600k'), '#1F6FB2', 'o', ('2,000만', '60만')),
             ('고정', ('flat5m', 'flat150k'), '#C2571A', 's', ('500만', '15만'))]
    c_axis = stored['figure4']['C_axis']                                    # same axes as the original figure
    cols = [('exit', '(a) 이탈률', (0, .2)), ('R', '(b) 유보율 $R$', (.5, .9)), ('C', '(c) 공존 유지율 $C$', tuple(c_axis))]

    W, H = 3.3, 2.75                                                       # one CogSci column is about 3.3 in
    fig = plt.figure(figsize=(W, H))
    for ci_, (key, title, ylim) in enumerate(cols):
        ax = fig.add_axes([.085 + .315 * ci_, .53, .25, .33])
        for ri, (name, arms, color, marker, amounts) in enumerate(rules):
            off = (ri - .5) * .12
            ys = [cells[key][a]['mean'] for a in arms]
            ax.plot([0 + off, 1 + off], ys, color=color, marker=marker, ms=3.2, lw=1.2)
            for xi, a in enumerate(arms):
                ax.plot([xi + off] * 2, cells[key][a]['ci95'], color=color, lw=.8, alpha=.75)
        ax.set(xlim=(-.5, 1.5), ylim=ylim)
        ax.set_yticks(np.arange(ylim[0], ylim[1] + .01, .1))
        ax.set_xticks([0, 1], ['큰\n상금', '작은\n상금'], fontsize=5.6)
        ax.tick_params(labelsize=5.4, length=2, pad=1.5)
        ax.grid(axis='y', alpha=.5)
        ax.set_title(title, loc='left', fontsize=6.6, pad=3)

    ax_eff = fig.add_axes([.12, .1, .85, .25])
    names = [('exit_risk', '이탈률'), ('R', '$R$'), ('C', '$C$')]
    lo_e = min(min(eff[f'{k}_{kind}']['ci95'][0] for kind in ('size', 'rule')) for k, _ in names)
    hi_e = max(max(eff[f'{k}_{kind}']['ci95'][1] for kind in ('size', 'rule')) for k, _ in names)
    ex = stored['figure4']['effect_axis']
    assert ex[0] <= lo_e and hi_e <= ex[1], (lo_e, hi_e)
    for yi, (key, _) in enumerate(names):
        for dy, kind, color in ((-.18, 'size', '#333333'), (.18, 'rule', '#9A9A9A')):
            e = eff[f'{key}_{kind}']
            ax_eff.plot(e['ci95'], [yi + dy] * 2, color=color, lw=1)
            ax_eff.scatter(e['effect'], yi + dy, color=color, s=10, zorder=3)
    ax_eff.axvline(0, color='#777777', lw=.6, ls='--')
    ax_eff.set(yticks=range(3), yticklabels=[n for _, n in names], ylim=(2.6, -.6), xlim=tuple(ex), xticks=[-.2, -.1, 0, .1, .2])
    ax_eff.set_xlabel('차이 (95% 구간)', fontsize=5.8, labelpad=1)
    ax_eff.tick_params(labelsize=5.4, length=2, pad=1.5)
    ax_eff.set_title('(d) 크기와 규칙의 차이', loc='left', fontsize=6.6, pad=3)
    ax_eff.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:+.1f}'.replace('+0.0', '0').replace('-0.0', '0')))
    ax_eff.grid(axis='x', alpha=.5)
    ax_eff.legend(handles=[Line2D([], [], color='#333333', marker='o', ms=2.6, lw=1, label='크기'),
                           Line2D([], [], color='#9A9A9A', marker='o', ms=2.6, lw=1, label='규칙')],
                  fontsize=5.2, loc='upper right', bbox_to_anchor=(1.0, 1.32), ncol=2, frameon=False, handlelength=1.3,
                  columnspacing=1.0, handletextpad=.4, borderaxespad=0)
    fig.legend(handles=[Line2D([], [], color=c, marker=mk, ms=3.2, lw=1.2, label=f'{n} 할당 ({am[0]} → {am[1]})') for n, _, c, mk, am in rules],
               loc='upper center', bbox_to_anchor=(.5, 1.0), ncol=2, fontsize=5.8, frameon=False, handlelength=1.6, columnspacing=1.4)
    for ext in ('pdf', 'png'):
        fig.savefig(ce.mf.cb.DEST / f'{OUT}.{ext}', dpi=300)
    plt.close(fig)
    print(ce.mf.cb.DEST / f'{OUT}.pdf')


if __name__ == '__main__':
    main()
