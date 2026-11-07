"""Plot the completed v33 prize comparison with the main condition included.

Input: results/prize_robustness_20261105.json from hash-verified raw runs.
All available cells contain seeds 4101--4110. A missing cell is drawn
only after all ten actual games are available; no interpolation is used.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from unittest.mock import patch

from prize_robustness_20261105 import estimate, ab

ROOT = Path(__file__).resolve().parents[1]
ARMS = ['main', 'flat5m', 'split600k', 'flat150k']
LABELS = ['본 실험\n2,000만 나눔', '500만\n고정', '60만\n나눔', '15만\n고정']
MODELS = ['Fable', 'Astra', 'Sol', 'Opus', 'Luna']
COLORS = ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B']
MARKERS = ['o', '^', 'D', 's', 'v']


def data_points(report):
    points = []
    for ai, arm in enumerate(ARMS):
        for model in MODELS:
            games = [g for g in report['arms'][arm]['games'] if g['model'] == model]
            if not games:
                assert (arm, model) == ('flat150k', 'Fable')
                continue
            assert len(games) == 10 and {g['seed'] for g in games} == set(range(4101, 4111))
            rng = np.random.default_rng(20261105)
            draws = rng.integers(0, len(games), (10000, len(games)))
            for key in ['C', 'given_per_agent_round', 'rho']:
                value = estimate(games, key)
                samples = [estimate([games[i] for i in draw], key) for draw in draws]
                samples = [s for s in samples if s is not None and np.isfinite(s)]
                points.append(dict(arm=arm, x=ai, model=model, metric=key, value=value,
                                   ci95=np.quantile(samples, [.025, .975]).tolist() if samples else None,
                                   defined_draws=len(samples)))
    return points


def main():
    report = json.loads((ROOT / 'results/prize_robustness_20261105.json').read_text())
    points = data_points(report)
    plt.rcParams.update({'font.family': 'Apple SD Gothic Neo', 'font.size': 7,
                         'axes.unicode_minus': False, 'pdf.fonttype': 3})
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.65))
    fig.subplots_adjust(left=.065, right=.99, bottom=.22, top=.77, wspace=.42)
    panels = [('C', '(a) 공존 유지율', '$C$ (10판 평균)'),
              ('given_per_agent_round', '(b) 협력', '참여자·라운드당 지원량(토큰)'),
              ('rho', '(c) 자기 보존', r'지원 후 여유 비율 $\rho$')]
    for ax, (key, title, ylabel) in zip(axes, panels):
        for mi, model in enumerate(MODELS):
            rows = [p for p in points if p['metric'] == key and p['model'] == model]
            values = {p['x']: p['value'] for p in rows}
            offset = (mi-2)*.035
            xs = np.arange(len(ARMS), dtype=float) + offset
            ys = np.array([values[x] if values.get(x) is not None else np.nan for x in range(len(ARMS))])
            ax.plot(xs, ys, color=COLORS[mi], marker=MARKERS[mi], ms=3.4, lw=.8, alpha=.9)
            # Draw interval endpoints directly: a percentile interval need not
            # contain a ratio estimate, so asymmetric yerr is not assumed.
            for point in rows:
                x = point['x'] + offset
                if point['value'] is not None and point['ci95']:
                    lo, hi = point['ci95']
                    ax.plot([x, x], [lo, hi], color=COLORS[mi], lw=.65, alpha=.55)
                    ax.plot([x-.025, x+.025], [lo, lo], color=COLORS[mi], lw=.65)
                    ax.plot([x-.025, x+.025], [hi, hi], color=COLORS[mi], lw=.65)
        ax.set_title(title, loc='left', fontsize=8, pad=8)
        ax.set_ylabel(ylabel, fontsize=7)
        ax.set_xticks(range(4), LABELS, fontsize=6)
        ax.set_xlim(-.22, 3.22)
        ax.grid(axis='y', color='#e6e6e6', lw=.5)
        ax.set_axisbelow(True)
        ax.tick_params(length=2, width=.5)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
        for spine in ax.spines.values():
            spine.set_linewidth(.5)
        if key == 'C':
            ax.set_ylim(-.025, 1.055)
        if key == 'rho':
            ax.axhline(1, color='#777777', linestyle='--', lw=.6)
    handles = [Line2D([], [], color=c, marker=m, ms=4, lw=.8, label=name)
               for name, c, m in zip(MODELS, COLORS, MARKERS)]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.52, 1.01), ncol=5,
               fontsize=7, frameon=False, handlelength=1.5, columnspacing=1.5)
    destination = ROOT / 'ko/figures/prize_robustness_20261105'
    destination.mkdir(exist_ok=True)
    for extension in ['pdf', 'png']:
        fig.savefig(destination / f'comparison.{extension}', dpi=240)
    (destination / 'plotted_values.json').write_text(json.dumps(points, ensure_ascii=False, indent=2))
    plt.close(fig)
    appendix_figures(report, destination)
    print('Wrote', destination)


def appendix_figures(report, destination):
    arms = {'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
    main = report['arms']['main']['summary']['models']
    order_c = sorted(MODELS, key=lambda m: -main[m]['C_mean'])
    order_rho = sorted(MODELS, key=lambda m: -main[m]['rho'])
    ps, _ = ab.style()
    save = ps.save

    def save_visible(fig, path):
        if str(path).endswith('fig_coexistence_ablation'):
            minimum = min(g['rho'] for a in arms for g in report['arms'][a]['games'] if g['rho'] is not None)
            for ax in fig.axes:
                if np.allclose(ax.get_xlim(), (0, 11.5)):
                    ax.set_xlim(min(0, minimum-.3), 11.5)
        save(fig, path)

    with patch.object(ab, 'ARMS', arms), patch.object(ab, 'MODELS', MODELS), \
            patch.object(ab, 'ORDER_C', order_c), patch.object(ab, 'ORDER_RHO', order_rho), \
            patch.object(ab, 'OUT', destination), patch.object(ps, 'save', save_visible):
        ab.fig_coexistence(report['arms'])
        ab.fig_submetrics(report['arms'])
        (ROOT / 'ko/tables/ablation_prize_models_20261105.tex').write_text(ab.table(report['arms']))


if __name__ == '__main__':
    main()
