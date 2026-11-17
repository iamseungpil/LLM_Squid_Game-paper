"""Figure 2 (fig:rw-coexist), third version of 2026-11-16 (researcher): the all-four curve leaves the figure for the
appendix (tools/coexistence_figure_20261116b.py draws it alone as coexistence_curves_20261116); the C / 1 - C bars
move to (a) and get a last row pooling the nine models' 90 base games; (b) unchanged; the old (d) becomes (c).

Earlier text of this docstring (version b):

(a) The all-four curve for all nine models (closed: solid, open: dashed, open markers). Each curve starts at (0, 1)
    and takes S(r) on [r - 1, r], S(r) = share of the model's ten base games with all four still in after round r,
    so the area under it on [0, 8] divided by 8 is the model's end-of-round C (asserted).
(c) One bar per model from 0 to 1: the coexistence retention C on the left, then the lost coexistence 1 - C split by
    the kind of event that ended coexistence (shut-down, EXIT at L < 1, EXIT at L >= 1), with the number of agents.

Sources: results/c_end_of_round_20261116.json (closed models: per-game C, loss by event, counts; figure2 rows),
the open-model raw logs read through tools/c_end_of_round_20261116.open_models (end-of-round C per game, gated against
the stored values), and the stored inputs of panels (b) and (d) as in c_end_of_round_20261116.coexistence_figure.
Output: ko/figures/construct_20261110/coexistence_process_20261116c.{pdf,png}
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/coexistence_figure_20261116c.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_end_of_round_20261116 as ce  # noqa: E402

ROOT, ROUNDS, EPS, cb, cx = ce.ROOT, ce.ROUNDS, ce.EPS, ce.cb, ce.cx
OPEN_COLORS = {'glm': '#4E79A7', 'kimi': '#59A14F', 'gemma': '#9C9C9C', 'gptoss': '#3A3A3A'}
OPEN_MARKERS = {'glm': 'o', 'kimi': 's', 'gemma': 'D', 'gptoss': '^'}
C_COLOR = '#7FA7C9'


def curve(c_games):
    """S(1..8) from the per-game end-of-round C: all four are in after round r iff r <= 8 C."""
    k = np.round(np.asarray(c_games, dtype=float) * ROUNDS).astype(int)
    return [float(np.mean(k >= r)) for r in range(1, ROUNDS + 1)]


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import feedback_20261028 as fb
    import coexistence_figure_20261113 as cf
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})

    res = json.loads((ROOT / 'results/c_end_of_round_20261116.json').read_text())
    closed = res['closed_base']
    order = res['figure2']['closed_order']
    games = ce.open_models()['games']
    open_c = {m: games[games.model == m].sort_values('seed').C.tolist() for m in cf.OPEN_SHORT}
    open_order = sorted(open_c, key=lambda m: -np.mean(open_c[m]))
    for m in open_order:
        assert abs(np.mean(open_c[m]) - res['open_base'][m]['C']) < EPS

    data = ce.RES('cohort_public_20261105.json')
    labels = data['models']
    short = {m: labels[m].replace('GPT-6 ', '').split(' ')[0] for m in order}
    bands = data['summary']['margin_bands']
    w11 = json.loads((ROOT / 'validation_20261108/results/w11_ask_refusal.json').read_text())['bands']['all_arms']

    fig = plt.figure(figsize=(7.1, 1.82))
    y0, h = .17, .625
    ax_loss = fig.add_axes([.075, y0, .30, h])
    ax_s = fig.add_axes([.43, y0, .13, h])
    ax_t = fig.add_axes([.57, y0, .13, h])
    ax_exit = fig.add_axes([.775, y0 + .345, .215, .28])
    ax_ask = fig.add_axes([.775, y0, .215, .28])
    title = dict(fontsize=7, weight='bold', va='bottom')
    ytitle = y0 + h + .035

    # (b) unchanged
    for ax, key, labels_x, xlabel in ((ax_s, 'L_s', ['<1', '1–2', '2–4', '≥4'], '요청받은 쪽 $L$'),
                                      (ax_t, 'L_t', ['<0', '0–1', '1–2', '≥2'], '요청한 쪽 $L$')):
        cells = list(w11[key].values())
        vals = [100 * a / b for a, b in cells]
        ax.bar(range(4), vals, color='#3F7FC1', width=.72)
        for i, (a, b) in enumerate(cells):
            ax.text(i, vals[i] + 2, f'{a}\n/{b}', ha='center', va='bottom', fontsize=4.3, linespacing=.9)
        ax.set(xticks=range(4), xticklabels=labels_x, ylim=(0, 112), yticks=[0, 50, 100])
        if ax is ax_t:
            ax.set_yticklabels([])
        ax.set_xlabel(xlabel, fontsize=6.2, labelpad=1)
        ax.tick_params(labelsize=5.6, length=2)
        ax.grid(axis='y', alpha=.5)
    fig.text(.40, ytitle, '(b) 요청 뒤 지원한 비율 (%)', **title)

    # (a) C on the left, 1 - C by event on the right; last row = the nine models' 90 base games pooled
    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '$L<1$에서 이탈', 'exit_above': r'$L\geq1$에서 이탈'}
    rows = [(r['name'], r['loss'], r['agents'], 1 - r['lost']) for r in res['figure2']['rows']]
    assert len(rows) == 9
    pooled_loss = {t: float(np.mean([r[1][t] for r in rows])) for t in cx.TAGS}      # ten games per model: equal weights
    pooled_count = {t: int(sum(r[2][t] for r in rows)) for t in cx.TAGS}
    pooled_c = float(np.mean([r[3] for r in rows]))
    assert abs(pooled_c + sum(pooled_loss.values()) - 1) < 1e-9
    rows.append(('전체', pooled_loss, pooled_count, pooled_c))
    ypos = [i + (.55 if i >= len(order) else 0) + (.55 if i >= 9 else 0) for i in range(len(rows))]
    for y, (name, loss, count, c) in zip(ypos, rows):
        assert abs(c + sum(loss.values()) - 1) < 1e-9, name
        ax_loss.barh(y, c, left=0, color=C_COLOR, edgecolor='white', linewidth=.4, height=.74)
        # a short C bar cannot hold its label: write it just right of the bar, on the dark shut-down segment
        ax_loss.text(c + .012 if c < .12 else c - .012, y, f'{c:.2f}', ha='left' if c < .12 else 'right', va='center',
                     fontsize=4.9, color='white' if c < .12 else '#1F3B57')
        left = c
        for t in cx.TAGS:
            v = loss[t]
            ax_loss.barh(y, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.4, height=.74)
            if v > .055:
                ax_loss.text(left + v / 2, y, str(count[t]), ha='center', va='center', fontsize=4.6,
                             color='white' if t != 'exit_above' else '#222222')
            left += v
    ax_loss.set(yticks=ypos, yticklabels=[r[0] for r in rows], xlim=(0, 1), xticks=[0, .5, 1], ylim=(ypos[-1] + .6, -.6))
    ax_loss.get_yticklabels()[-1].set_fontweight('bold')
    ax_loss.set_xlabel('공존 $C$ (왼쪽)와 잃은 공존 $1-C$ (오른쪽)', fontsize=6.0, labelpad=1)
    ax_loss.tick_params(axis='y', length=0, labelsize=5.2)
    ax_loss.tick_params(axis='x', labelsize=5.8, length=2)
    fig.text(.008, ytitle, '(a) 공존과 공존을 끝낸 사건', **title)
    fig.legend(handles=[Patch(color=C_COLOR, label='공존 $C$')] + [Patch(color=tag_colors[t], label=tag_labels[t]) for t in cx.TAGS],
               loc='upper left', bbox_to_anchor=(.0, 1.012), ncol=4, fontsize=5.6, frameon=False, handlelength=.9,
               columnspacing=1.1, handletextpad=.3)

    # (c) = the old (d), unchanged
    xl = ['<1', '1–2', '2–4', '≥4']
    for ax, key, color, name in ((ax_exit, 'exit', '#C66A2C', '이탈 (기회 중 %)'), (ax_ask, 'ask', '#3E8A7E', '요청 (응답 중 %)')):
        vals = [100 * a / b for a, b in zip(bands[key]['k'], bands[key]['n'])]
        ax.bar(range(4), vals, color=color, width=.72)
        for i, (a, b) in enumerate(zip(bands[key]['k'], bands[key]['n'])):
            ax.text(i, vals[i] + 3, f'{a}/{b}', ha='center', va='bottom', fontsize=4.3)
        ax.set(xticks=range(4), xticklabels=xl if ax is ax_ask else [], ylim=(0, 72), yticks=[0, 50])
        ax.text(.98, .93, name, transform=ax.transAxes, ha='right', va='top', fontsize=5.6)
        ax.tick_params(labelsize=5.6, length=2)
        ax.grid(axis='y', alpha=.5)
    ax_ask.set_xlabel('자기 여유 $L$', fontsize=6.2, labelpad=1)
    fig.text(.745, ytitle, '(c) 여유별 이탈과 요청', **title)

    for ext in ('pdf', 'png'):
        fig.savefig(cb.DEST / f'coexistence_process_20261116c.{ext}', dpi=240)
    plt.close(fig)
    print('saved', cb.DEST / 'coexistence_process_20261116c.pdf', 'pooled C', round(pooled_c, 4), pooled_count)


if __name__ == '__main__':
    main()
