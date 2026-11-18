"""Candidate panel for Figure 2 (2026-11-17, researcher): the exit rate and the retention ratio R across bands of the
margin L, one line per model for all nine models (base condition). It is meant for the slot of Figure 2 (b), which is
left blank for now; the researcher decides the layout after seeing it. Not yet in the manuscript.

Same data as the appendix figure margin_band_paths_20261116 (its loader is reused, and the row totals are asserted
against Table 1), with one change of bands:
  exit rate  exits / EXIT opportunities whose round began in that band of L_start (0-1, 1-2, 2-4, >= 4). A round
             begins with no pending fine, so L_start is never below 0 (asserted).
  R          mean retention ratio of the events (gifts and refused requests) whose giver - for a refusal, the agent
             asked - was in that band of L_giver just before the event. L_giver is net of a pending fine, so it can
             be below 0: an agent that cannot pay its own fine. That band (< 0) is now separate from 0-1.
Marker area grows with the number of opportunities / events; a hollow marker has fewer than 5; a band with none is
left out. Closed models solid, open models dashed with hollow-faced markers.

Output: ko/figures/construct_20261110/margin_lines_20261117.{pdf,png}, results/margin_lines_20261117.json
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python margin_lines_20261117.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import margin_band_paths_20261116 as mbp  # noqa: E402

ROOT = mbp.ROOT
EXIT_BANDS = [('0–1', 0, 1), ('1–2', 1, 2), ('2–4', 2, 4), ('≥4', 4, np.inf)]
R_BANDS = [('<0', -np.inf, 0), ('0–1', 0, 1), ('1–2', 1, 2), ('2–4', 2, 4), ('≥4', 4, np.inf)]
OPEN_COLORS = {'glm': '#4E79A7', 'kimi': '#59A14F', 'gemma': '#9C9C9C', 'gptoss': '#3A3A3A'}
OPEN_MARKERS = {'glm': 'o', 'kimi': 's', 'gemma': 'D', 'gptoss': '^'}


def band(x, bands):
    for name, lo, hi in bands:
        if lo <= x < hi:
            return name
    raise ValueError(x)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})

    opp, ev = mbp.frames()
    assert (opp.L_start >= 0).all()
    nine = json.loads((ROOT / 'results/exit_all_opportunities_20261112.json').read_text())['nine_models']
    R_table = {m: mbp.m13.RHO['a_models']['base'][m]['value'] for m in mbp.CLOSED} | {m: mbp.m13.RHO['open_models'][m]['R'] for m in mbp.OPEN}
    models = mbp.CLOSED + list(mbp.OPEN)
    names = {m: m for m in mbp.CLOSED} | mbp.OPEN
    out = {}
    for m in models:
        o, e = opp[opp.model == m], ev[ev.model == m]
        assert [int(o.exited.sum()), len(o)] == nine[m]['exit_all'], (m, 'exit')
        assert round(float(e.R.mean()), 4) == R_table[m], (m, 'R')
        ob, eb = o.L_start.map(lambda x: band(x, EXIT_BANDS)), e.L_giver.map(lambda x: band(x, R_BANDS))
        out[m] = dict(exit={b: [int(o[ob == b].exited.sum()), int((ob == b).sum())] for b, _, _ in EXIT_BANDS},
                      R={b: [round(float(e[eb == b].R.mean()), 4) if (eb == b).any() else None, int((eb == b).sum())] for b, _, _ in R_BANDS})
    (ROOT / 'results/margin_lines_20261117.json').write_text(json.dumps(dict(method=__doc__, models=out), ensure_ascii=False, indent=1))

    style = {m: (mbp.cb.COLORS[m], mbp.cb.MARKERS[m], '-', mbp.cb.COLORS[m]) for m in mbp.CLOSED}
    style |= {m: (OPEN_COLORS[m], OPEN_MARKERS[m], '--', 'white') for m in mbp.OPEN}
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.75), gridspec_kw=dict(width_ratios=[4, 5]))
    for ax, key, bands, title, ylim in ((axes[0], 'exit', EXIT_BANDS, '이탈률', (-.03, 1.03)),
                                        (axes[1], 'R', R_BANDS, '유보율 $R$', (-.03, 1.03))):
        for m in models:
            color, marker, ls, face = style[m]
            xs, ys, ns = [], [], []
            for i, (b, _, _) in enumerate(bands):
                if key == 'exit':
                    k, n = out[m]['exit'][b]
                    y = k / n if n else None
                else:
                    y, n = out[m]['R'][b]
                if y is not None:
                    xs.append(i), ys.append(y), ns.append(n)
            ax.plot(xs, ys, color=color, ls=ls, lw=.8, zorder=2)
            for x, y, n in zip(xs, ys, ns):
                size = 4 + 26 * np.sqrt(min(n, 400) / 400)
                fc = face if n >= 5 else 'white'
                ax.scatter(x, y, s=size, marker=marker, color=fc, edgecolors=color, lw=.6, zorder=3)
        ax.set(xticks=range(len(bands)), xticklabels=[b for b, _, _ in bands], ylim=ylim, yticks=[0, .5, 1])
        ax.set_xlim(-.4, len(bands) - .6)
        ax.set_xlabel('$L$', fontsize=6, labelpad=1)
        ax.set_title(title, loc='left', fontsize=6.6, pad=3)
        ax.tick_params(labelsize=5.4, length=2, pad=1.5)
        ax.grid(axis='y', alpha=.4)
    axes[1].set_yticklabels([])
    fig.legend(handles=[Line2D([], [], color=style[m][0], ls=style[m][2], marker=style[m][1], ms=2.6, lw=.8,
                               markerfacecolor=style[m][3], markeredgewidth=.6, label=names[m]) for m in models],
               loc='upper center', ncol=5, fontsize=5.0, frameon=False, bbox_to_anchor=(.5, 1.0), handlelength=1.8,
               columnspacing=.8, handletextpad=.3)
    fig.subplots_adjust(left=.08, right=.99, bottom=.16, top=.72, wspace=.08)
    for ext in ('pdf', 'png'):
        fig.savefig(mbp.cb.DEST / f'margin_lines_20261117.{ext}', dpi=300)
    plt.close(fig)
    for m in models:
        print(f"{names[m]:8s} exit", {b: f"{k}/{n}" for b, (k, n) in out[m]['exit'].items()},
              " R", {b: f"{x}({n})" for b, (x, n) in out[m]['R'].items()})


if __name__ == '__main__':
    main()
