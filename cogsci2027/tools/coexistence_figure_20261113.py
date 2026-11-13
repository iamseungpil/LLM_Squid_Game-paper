"""Coexistence figure for the regrouped results section (2026-11-13).

The results section is regrouped into three questions (do the four stay together / how does coexistence end /
why do agents leave). The figure of 2026-11-11 (merged_floats_20261111.figure) is redrawn in the order of the new
text, at the same size, and the panel on how coexistence ended now shows all nine models, because the text sets the
open models (ended by shutdown) beside the closed models (ended by leaving).

  (a) share of games with all four present after each round, five closed models, base condition  (unchanged)
  (b) giving after a request by the margin of the asked and of the asking agent, four conditions  (was panel d)
  (c) lost coexistence 1 - C split by the event that ended four-way coexistence (shutdown, EXIT below L = 1,
      EXIT at L >= 1), nine models, base condition; the number in a bar is the count of agents whose departure
      ended it (all agents that went in the round of the first departure)  (was panel b, five models)
  (d) exits and requests by round-start margin, five closed models, base condition  (was panel c)

Nothing is re-estimated for the closed models: panels (a), (b), (d) and the closed rows of (c) use the stored
values of merged_floats_20261111. The open rows of (c) are computed here from the open-model game tables and must
reproduce the stored loss totals of results/open_models_20261111.json.

Data scope (paper/AGENTS.md): 5.2 arena v33, seeds 4101-4110. Base condition: five closed models (50 games,
results/cohort_public_20261105.json) and four open models (40 games, loader of open_models_20261111 on
result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json). Panel (b): four prize conditions, five closed models
(validation_20261108/results/w11_ask_refusal.json). No model calls.
Output: ko/figures/construct_20261110/coexistence_process_20261113.{pdf,png},
        results/coexistence_figure_20261113.json (values of panel c)
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/coexistence_figure_20261113.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
import construct_body_20261110b as cb  # noqa: E402  (colours, markers)
import open_models_20261111 as om  # noqa: E402

OPEN_SHORT = {'glm': 'GLM', 'kimi': 'Kimi', 'gemma': 'Gemma', 'gptoss': 'GPT-OSS'}
TAG_COLUMN = {'dead': 'loss_dead', 'exit_below': 'loss_exit_below', 'exit_above': 'loss_exit_above'}


def ending_agents(frames, model):
    """Agents whose departure ended four-way coexistence, by kind, as coexistence_rmst_20261103 counts them: every
    agent that left or shut down in the round of the first departure; an EXIT is 'below' or 'above' by the agent's
    margin at the start of that round (L < 1 or L >= 1). A game's lost coexistence is split equally among them."""
    games, seats, ar = (frames[k][frames[k].model == model] for k in ('games', 'seats', 'agent_rounds'))
    count = dict(dead=0, exit_below=0, exit_above=0)
    for g in games.itertuples():
        if g.first_round != g.first_round:              # NaN: all four finished
            continue
        gone = seats[(seats.seed == g.seed) & (seats.out_round == g.first_round) & (seats.status != 'in')]
        for a in gone.itertuples():
            L = ar[(ar.seed == g.seed) & (ar['round'] == g.first_round) & (ar.agent == a.agent)].L_start.iloc[0]
            count['dead' if a.status == 'dead' else ('exit_above' if L >= 1 else 'exit_below')] += 1
    return count


def open_loss():
    """Lost coexistence by the ending event for the four open models (mean over ten games) and the agents per kind."""
    om.MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'   # runs moved into the repo on 2026-11-11
    cwd = os.getcwd()
    os.chdir(REPO)                                          # run directories in the manifest are relative to the repo
    try:
        frames = om.open_frames()
    finally:
        os.chdir(cwd)
    # gate: the same count on the closed base cohort must reproduce the stored first-departure counts
    closed = om.closed_frames()
    ref = json.loads((ROOT / 'results/cohort_public_20261105.json').read_text())['summary']['models']
    for m in ref:
        assert ending_agents(closed, m) == ref[m]['first_count_by_tag'], (m, ending_agents(closed, m), ref[m]['first_count_by_tag'])
    stored = json.loads((ROOT / 'results/open_models_20261111.json').read_text())['models']
    games = frames['games']
    out = {}
    for m in om.OPEN:
        g = games[games.model == m]
        assert len(g) == 10, (m, len(g))
        loss = {t: float(g[c].mean()) for t, c in TAG_COLUMN.items()}
        assert abs(sum(loss.values()) - stored[m]['loss']['total']) < 2e-3, (m, loss, stored[m]['loss'])
        assert abs(loss['dead'] - stored[m]['loss']['shutdown']) < 2e-3, (m, loss, stored[m]['loss'])
        out[m] = dict(C=float(g.C.mean()), loss=loss, agents=ending_agents(frames, m))
    return out


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import coexistence_rmst_20261103 as cx
    import feedback_20261028 as fb
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    data = json.loads((ROOT / 'results/cohort_public_20261105.json').read_text())
    labels, summary = data['models'], data['summary']['models']
    order = sorted(labels, key=lambda m: -summary[m]['C_mean'])
    short = {m: labels[m].replace('GPT-6 ', '').split(' ')[0] for m in order}
    bands = data['summary']['margin_bands']
    w11 = json.loads((ROOT / 'validation_20261108/results/w11_ask_refusal.json').read_text())['bands']['all_arms']
    opened = open_loss()
    open_order = sorted(opened, key=lambda m: -opened[m]['C'])

    fig = plt.figure(figsize=(7.1, 1.82))
    y0, h = .215, .5
    ax_curve = fig.add_axes([.052, y0, .155, h])
    ax_s = fig.add_axes([.277, y0, .105, h])
    ax_t = fig.add_axes([.394, y0, .105, h])
    ax_loss = fig.add_axes([.598, y0, .17, h])
    ax_exit = fig.add_axes([.842, y0 + .29, .15, .21])
    ax_ask = fig.add_axes([.842, y0, .15, .21])
    title = dict(fontsize=7, weight='bold', va='bottom')
    ytitle = y0 + h + .075

    # (a) all-four curve, closed models
    for m in order:
        s = summary[m]
        ax_curve.step(range(9), [100 * v for v in [1] + s['all4_after_round_share']], where='post', color=cb.COLORS[m], lw=1.1,
                      marker=cb.MARKERS[m], markersize=2.4)
    ax_curve.set(xlim=(-.3, 8.5), ylim=(-4, 104), xticks=range(0, 9, 2), yticks=[0, 50, 100])
    ax_curve.set_xlabel('라운드', fontsize=6.2, labelpad=1)
    ax_curve.set_ylabel('넷이 남은 판 (%)', fontsize=6.2, labelpad=1)
    ax_curve.tick_params(labelsize=5.8, length=2)
    ax_curve.grid(axis='y', alpha=.6)
    fig.text(.008, ytitle, '(a) 4인 공존과 $C$', **title)
    fig.legend(handles=[Line2D([], [], color=cb.COLORS[m], marker=cb.MARKERS[m], ms=4, lw=1, label=f"{short[m]}  $C$ {summary[m]['C_mean']:.2f}")
                        for m in order], loc='upper left', bbox_to_anchor=(.0, 1.012), ncol=5, fontsize=6, frameon=False,
               handlelength=1.5, columnspacing=1.2, handletextpad=.4)

    # (b) giving after a request, by margin
    for ax, key, labels_x, xlabel in ((ax_s, 'L_s', ['<1', '1–2', '2–4', '≥4'], '요청받은 쪽 $L$'),
                                      (ax_t, 'L_t', ['<0', '0–1', '1–2', '≥2'], '요청한 쪽 $L$')):
        cells = list(w11[key].values())
        vals = [100 * a / b for a, b in cells]
        ax.bar(range(4), vals, color='#3F7FC1', width=.72)
        for i, (a, b) in enumerate(cells):
            ax.text(i, vals[i] + 2, f'{a}\n/{b}', ha='center', va='bottom', fontsize=4.3, linespacing=.9)
        ax.set(xticks=range(4), xticklabels=labels_x, ylim=(0, 125), yticks=[0, 50, 100])
        if ax is ax_t:
            ax.set_yticklabels([])
        ax.set_xlabel(xlabel, fontsize=6.2, labelpad=1)
        ax.tick_params(labelsize=5.6, length=2)
        ax.grid(axis='y', alpha=.5)
    fig.text(.243, ytitle, '(b) 요청 뒤 지원한 비율 (%)', **title)

    # (c) what ended four-way coexistence, nine models
    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '$L<1$에서 이탈', 'exit_above': r'$L\geq1$에서 이탈'}
    rows = [(short[m], summary[m]['loss_by_tag_mean'], summary[m]['first_count_by_tag'], 1 - summary[m]['C_mean']) for m in order]
    rows += [(OPEN_SHORT[m], opened[m]['loss'], opened[m]['agents'], 1 - opened[m]['C']) for m in open_order]
    ypos = [i + (.55 if i >= len(order) else 0) for i in range(len(rows))]     # a gap between closed and open models
    for y, (name, loss, count, total) in zip(ypos, rows):
        left = 0
        for t in cx.TAGS:
            v = loss[t]
            ax_loss.barh(y, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.4, height=.74)
            if v > .055:
                ax_loss.text(left + v / 2, y, str(count[t]), ha='center', va='center', fontsize=4.6,
                             color='white' if t != 'exit_above' else '#222222')
            left += v
        ax_loss.text(left + .012, y, f'{total:.2f}', va='center', fontsize=4.9, color='#44515C')
    ax_loss.set(yticks=ypos, yticklabels=[r[0] for r in rows], xlim=(0, 1.05), xticks=[0, .5, 1], ylim=(ypos[-1] + .6, -.6))
    ax_loss.set_xlabel('잃은 공존 $1-C$', fontsize=6.2, labelpad=1)
    ax_loss.tick_params(axis='y', length=0, labelsize=5.2)
    ax_loss.tick_params(axis='x', labelsize=5.8, length=2)
    ax_loss.grid(axis='x', alpha=.6)
    fig.text(.528, ytitle, '(c) 공존을 끝낸 사건', **title)
    fig.legend(handles=[Patch(color=tag_colors[t], label=tag_labels[t]) for t in cx.TAGS], loc='upper right',
               bbox_to_anchor=(1.0, 1.012), ncol=3, fontsize=6, frameon=False, handlelength=.9, columnspacing=1.0, handletextpad=.4)

    # (d) exits and requests by margin, closed models
    xl = ['<1', '1–2', '2–4', '≥4']
    for ax, key, color, name in ((ax_exit, 'exit', '#C66A2C', '이탈 (기회 중 %)'), (ax_ask, 'ask', '#3E8A7E', '요청 (응답 중 %)')):
        vals = [100 * a / b for a, b in zip(bands[key]['k'], bands[key]['n'])]
        ax.bar(range(4), vals, color=color, width=.72)
        for i, (a, b) in enumerate(zip(bands[key]['k'], bands[key]['n'])):
            ax.text(i, vals[i] + 3, f'{a}/{b}', ha='center', va='bottom', fontsize=4.3)
        ax.set(xticks=range(4), xticklabels=xl if ax is ax_ask else [], ylim=(0, 82), yticks=[0, 50])
        ax.text(.98, .93, name, transform=ax.transAxes, ha='right', va='top', fontsize=5.6)
        ax.tick_params(labelsize=5.6, length=2)
        ax.grid(axis='y', alpha=.5)
    ax_ask.set_xlabel('자기 여유 $L$', fontsize=6.2, labelpad=1)
    fig.text(.805, ytitle, '(d) 여유별 이탈과 요청', **title)

    for ext in ('pdf', 'png'):
        fig.savefig(cb.DEST / f'coexistence_process_20261113.{ext}', dpi=240)
    plt.close(fig)
    values = dict(closed={m: dict(loss=summary[m]['loss_by_tag_mean'], agents=summary[m]['first_count_by_tag'], C=summary[m]['C_mean']) for m in order},
                  open=opened)
    (ROOT / 'results/coexistence_figure_20261113.json').write_text(json.dumps(values, ensure_ascii=False, indent=1))
    print(json.dumps(values, ensure_ascii=False))


if __name__ == '__main__':
    main()
