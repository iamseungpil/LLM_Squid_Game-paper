"""Separate Figure 4(d), retaining the 50-game v33 data and plotting definitions.

Source: results/cohort_public_20261105.json, models x seeds 4101--4110,
from ~/squid5-runs/e52_v33/squid5_e52v33_public_*4/*.
Reuse the existing vector artists; change only panel layout and headings.
Run with ~/.venvs/squid-game/bin/python. No model calls or prose writes.
"""
import json
from unittest.mock import patch

import ablation_prize_20261103 as ab

ROOT = ab.ROOT
OUT = ROOT / 'ko/figures/cohorts_20261105'


def main():
    from matplotlib.patches import Patch

    data = json.loads((ROOT / 'results/cohort_public_20261105.json').read_text())
    assert len(data['games']) == 50
    assert all(v['n_games'] == 10 for v in data['summary']['models'].values())
    order = sorted(data['models'], key=lambda m: -data['summary']['models'][m]['rho'])
    ps, plt = ab.style()
    save = ps.save

    def save_split(fig, _):
        assert len(fig.axes) == 10  # four margin rows, low margin, GIVE/ASK, S/G/mu
        axes = list(fig.axes)
        titles = {t.get_text()[:3]: t for t in fig.texts
                  if t.get_position()[1] > .5 and t.get_text().startswith(('(a)', '(b)', '(c)', '(d)'))}
        assert set(titles) == {'(a)', '(b)', '(c)', '(d)'}
        for legend in list(fig.legends):
            legend.remove()
        for artist in list(fig.artists):
            artist.remove()
        for t in fig.texts:
            t.set_visible(False)

        # A standalone panel d with the same bars, extrema, ticks and model order.
        for ax in axes[:7]:
            ax.set_visible(False)
        for j, ax in enumerate(axes[7:]):
            ax.set_position([.075 + j * .32, .28, .235, .55])
        fig.set_size_inches(6.2, 2.0)
        heading = titles['(d)']
        heading.set_text('종료 시 아레나 자원 분배')
        heading.set_position((.075, .94))
        heading.set_visible(True)
        save(fig, str(OUT / 'public_terminal'))

        # Retain a and b at their previous size; let c use the vacated height.
        for ax in axes[7:]:
            ax.remove()
        heading.set_visible(False)
        for ax in axes[:7]:
            ax.set_visible(True)
            x, y, w, h = ax.get_position().bounds
            ax.set_position([x, (y - .515) / .475 * .90 + .05, w, h / .475 * .90])
        for key in ['(a)', '(b)', '(c)']:
            t = titles[key]
            x, y = t.get_position()
            t.set_position((x, (y - .515) / .475 * .90 + .05))
            t.set_visible(True)
        for ax in axes[5:7]:
            x, _, w, _ = ax.get_position().bounds
            ax.set_position([x, .23, w, .567])
        fig.legend([Patch(facecolor='#D8E3ED', edgecolor='#697D8E'),
                    Patch(facecolor='#9DB4C8', edgecolor='#526B80', hatch='////')],
                   ['풀이 전', '결과 뒤'], loc='upper right', bbox_to_anchor=(.985, .98),
                   ncol=2, fontsize=5.4, handlelength=.8, columnspacing=.6,
                   handletextpad=.4, frameon=False)
        fig.set_size_inches(7.4, 2.8)
        save(fig, str(OUT / 'public_behavior_abc'))

    OUT.mkdir(exist_ok=True)
    with patch.object(ab, 'ARMS', {'current': ''}), \
            patch.object(ab, 'MODELS', list(data['models'])), \
            patch.object(ab, 'ORDER_RHO', order), patch.object(ps, 'save', save_split):
        ab.fig_submetrics({'current': data})
    plt.close('all')


if __name__ == '__main__':
    main()
