"""Draft of the new Figure 2 (process figure), 2026-11-17 (researcher). Base condition.

Left column, four rows of bars sharing one axis of the margin L, the nine models pooled (researcher: bars, no
closed / open split; the pooled values of each group are kept in the json):
  E     exits / EXIT opportunities, by the margin at the start of the round (L_start)
  R     mean retention ratio of the events (gifts and refused requests) by the giver's margin just before the event
        (L_giver, net of a pending fine, so it can be below 0)
  ASK   share of agent-rounds (with at least one peer) in which the agent sent an ASK, by L_start
  GIVE  share of the same agent-rounds in which the agent handed over tokens (before or after the solve), by L_start
L_start is never below 0 (a round begins with no pending fine), so only R has a value in the < 0 slot.
Right block: the 2 x 2 of Figure R.5 (closed / open models x E / R, one line per model).

Values: E and R reproduce results/margin_lines_20261117.json per model (asserted); the pooled values are sums of
counts over the models of a group (R: mean over the group's events). Output (appendix draft only):
ko/figures/construct_20261110/process_draft_20261117.{pdf,png} and panel (a) alone as process_bars_20261117.{pdf,png}, results/process_draft_20261117.json
Run: cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python process_figure_draft_20261117.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import margin_lines_20261117 as ml  # noqa: E402
import margin_lines_layouts_20261117 as lay  # noqa: E402

mbp = ml.mbp
ROOT, REPO = mbp.ROOT, mbp.REPO
SLOTS = ['<0', '0–1', '1–2', '2–4', '≥4']
START_BANDS = ml.EXIT_BANDS                   # 0-1, 1-2, 2-4, >= 4


def band(x, bands):
    return ml.band(x, bands)


# rows: key, label written in the panel (as the earlier Figure 2 (c): "이탈 (기회 중 %)", "요청 (응답 중 %)"), colour,
# scale (percent for the shares as in (c); R is a ratio, so it keeps 0-1 with the same two ticks), y-limit, ticks
ROWS = [('E', '이탈 (기회 중 %)', '#C66A2C', 100, 72, [0, 50]),
        ('R', '유보율 $R$ (사건 평균)', '#7155A1', 1, 1.0, [0, .5]),
        ('ASK', '요청 (동료가 있던 라운드 중 %)', '#3E8A7E', 100, 72, [0, 50]),
        ('GIVE', '지원 (동료가 있던 라운드 중 %)', '#3F7FC1', 100, 72, [0, 50])]


def draw_bars(fig, cells, x, w, top, h, gap):
    """Panel (a) drawn exactly as the bars of the earlier Figure 2 (c) (coexistence_figure_20261117.py): the paper
    style of feedback_20261028 (paper_style.use: no top/right spines, thin dark axes), bars of width .72, the y grid
    of (c) (alpha .5), the row name inside at the top right, tick labels 5.6 pt. The style is applied only to these
    axes (rc_context), so the panels drawn after them keep theirs."""
    import matplotlib.pyplot as plt
    import feedback_20261028 as fb
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    axes = []
    with plt.rc_context():
        ps.use()
        plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
        for i, (key, title, color, scale, ymax, ticks) in enumerate(ROWS):
            ax = fig.add_axes([x, top - (i + 1) * h - i * gap, w, h])
            axes.append(ax)
            for j, b in enumerate(SLOTS):
                cell = cells[key].get(b)
                if cell is None:
                    continue
                y = cell[0] if key == 'R' else (cell[0] / cell[1] if cell[1] else None)
                if y is not None:
                    ax.bar(j, scale * y, color=color, width=.72)
            ax.set(xticks=range(5), xticklabels=SLOTS if i == len(ROWS) - 1 else [], ylim=(0, ymax), yticks=ticks)
            ax.set_xlim(-.6, 4.6)
            ax.text(.98, .93, title, transform=ax.transAxes, ha='right', va='top', fontsize=5.6)
            ax.tick_params(labelsize=5.6, length=2)
            ax.grid(axis='y', alpha=.5)
        axes[-1].set_xlabel('자기 여유 $L$', fontsize=6.2, labelpad=1)
    return axes

def agent_rounds():
    om = mbp.om
    fc = om.closed_frames()
    om.MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        fo = om.open_frames()
    finally:
        os.chdir(cwd)
    ar = pd.concat([fc['agent_rounds'], fo['agent_rounds']], ignore_index=True)
    return ar[ar.arm == 'main'].copy()


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})

    opp, ev = mbp.frames()
    ar = agent_rounds()
    assert (ar.L_start >= 0).all()
    per_model = json.loads((ROOT / 'results/margin_lines_20261117.json').read_text())['models']
    groups = {'closed': mbp.CLOSED, 'open': list(mbp.OPEN), 'all': mbp.CLOSED + list(mbp.OPEN)}
    pooled = {}
    for g, models in groups.items():
        o, e = opp[opp.model.isin(models)], ev[ev.model.isin(models)]
        a = ar[ar.model.isin(models) & (ar.n > 1)].copy()
        a['gave'] = (a.gave_prep + a.gave_rescue) > 0
        ob, eb, ab = (o.L_start.map(lambda x: band(x, START_BANDS)), e.L_giver.map(lambda x: band(x, ml.R_BANDS)),
                      a.L_start.map(lambda x: band(x, START_BANDS)))
        for m in models:                                      # the pooled counts are sums of the per-model counts
            for b, _, _ in START_BANDS:
                k, n = per_model[m]['exit'][b]
                assert (int(o[(o.model == m) & (ob == b)].exited.sum()), int(((o.model == m) & (ob == b)).sum())) == (k, n)
        pooled[g] = dict(
            E={b: [int(o[ob == b].exited.sum()), int((ob == b).sum())] for b, _, _ in START_BANDS},
            R={b: [round(float(e[eb == b].R.mean()), 4) if (eb == b).any() else None, int((eb == b).sum())] for b, _, _ in ml.R_BANDS},
            ASK={b: [int(a[ab == b].asked.sum()), int((ab == b).sum())] for b, _, _ in START_BANDS},
            GIVE={b: [int(a[ab == b].gave.sum()), int((ab == b).sum())] for b, _, _ in START_BANDS})
    (ROOT / 'results/process_draft_20261117.json').write_text(json.dumps(dict(method=__doc__, pooled=pooled), ensure_ascii=False, indent=1))

    fig = plt.figure(figsize=(7.1, 3.0))
    draw_bars(fig, pooled['all'], x=.065, w=.25, top=.9, h=.165, gap=.045)
    fig.text(.01, .955, '(a) 아홉 모델의 여유별 행동', fontsize=7, weight='bold')

    # right: the 2 x 2 of R.5
    names = {m: m for m in mbp.CLOSED} | mbp.OPEN
    sty = {m: (mbp.cb.COLORS[m], mbp.cb.MARKERS[m], '-', mbp.cb.COLORS[m]) for m in mbp.CLOSED}
    sty |= {m: (ml.OPEN_COLORS[m], ml.OPEN_MARKERS[m], '--', 'white') for m in mbp.OPEN}
    x0, w_e, w_r, hh = .385, .2, .25, .33
    for r, (gname, models) in enumerate((('비공개', mbp.CLOSED), ('공개', list(mbp.OPEN)))):
        y = .52 - r * .43
        for c, (key, bands, title, x, w) in enumerate((('exit', ml.EXIT_BANDS, '이탈률 $E$', x0, w_e), ('R', ml.R_BANDS, '유보율 $R$', x0 + w_e + .025, w_r))):
            ax = fig.add_axes([x, y, w, hh])
            lay.panel(ax, per_model, models, sty, key, bands, .8)
            ax.set_title(f'({"bcde"[2 * r + c]}) {gname} 모델: {title}', loc='left', fontsize=6.4, pad=2)
            if c == 1:
                ax.set_yticklabels([])
            if r == 0:
                ax.set_xticklabels([])
            else:
                ax.set_xlabel('자기 여유 $L$', fontsize=6.0, labelpad=1)
            if c == 1:
                ax.legend(handles=[Line2D([], [], color=sty[m][0], ls=sty[m][2], marker=sty[m][1], ms=3, lw=.9, markerfacecolor=sty[m][3],
                                          markeredgewidth=.7, label=names[m]) for m in models],
                          loc='center left', bbox_to_anchor=(1.02, .5), fontsize=5.4, frameon=False, handlelength=2.0, labelspacing=.25)
    for ext in ('pdf', 'png'):
        fig.savefig(mbp.cb.DEST / f'process_draft_20261117.{ext}', dpi=300)
    plt.close(fig)
    fig = plt.figure(figsize=(2.3, 3.0))                      # panel (a) alone
    draw_bars(fig, pooled['all'], x=.2, w=.76, top=.97, h=.185, gap=.04)
    for ext in ('pdf', 'png'):
        fig.savefig(mbp.cb.DEST / f'process_bars_20261117.{ext}', dpi=300)
    plt.close(fig)
    for g in pooled:
        print(g, {k: {b: v for b, v in d.items()} for k, d in pooled[g].items()})


if __name__ == '__main__':
    main()
