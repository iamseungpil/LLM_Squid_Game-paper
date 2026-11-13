"""Merged body floats (2026-11-11): one leaderboard table and one coexistence figure.

The researcher asked for fewer floats in the results section. Nothing is recomputed here; the script only lays out
values that other scripts already produced.

  Table  ko/tables/cohort_leaderboard_20261111.tex
         nine models (results/open_models_20261111.json) and the six rule agents (results/rule_baselines_20261111.json)
         in one table. Columns dropped from the previous body table because the text carries them: equal-cost C,
         games with all four finishing, exit rate on the cost-adjusted margin, tokens per TALK and per SOLVE call.
  Figure ko/figures/construct_20261110/coexistence_process_20261111.{pdf,png}
         (a) all-four curve and (b) loss attribution from the old coexistence figure, (c) exits and asks by margin and
         (d) giving after an ASK by margin from the old process figure. The scatter of the two weights is not drawn:
         its values are the exit and kappa columns of the table.

Data scope (paper/CLAUDE.md): 5.2 arena v33, seeds 4101-4110. Panels (a)-(c): base condition, five closed models,
50 games (results/cohort_public_20261105.json). Panel (d): the four prize conditions, five closed models
(validation_20261108/results/w11_ask_refusal.json). Table: base condition, nine models; rule agents are simulated.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/merged_floats_20261111.py
"""
import json
import sys

import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_body_20261110b as cb  # noqa: E402  (colors, markers, model names)

CLOSED = {'Astra': 'GPT-6 Astra', 'Sol': 'GPT-6 Sol', 'Opus': 'Opus 5.5', 'Fable': 'Fable 5.1', 'Luna': 'GPT-6 Luna'}
OPEN = {'glm': 'GLM-5.3-Flash', 'kimi': 'Kimi K3', 'gemma': 'Gemma 4 31B', 'gptoss': 'GPT-OSS 120B'}
# 2026-11-12: the body no longer names a safety line or a risk zone; the rules are written with the margin itself
# 2026-11-12 (later): the sharing rules are written as behaviours, not as kappa values, and a minimal-rescue agent
# (results/rule_minimal_rescue_20261112.json) is added, so the kappa column is a reading and not an echo of the rule.
RULES = [('stayer', '남는 형', '떠나지 않음, 똑같이 맞출 양의 1/4을 줌'), ('cooperator', '협력형', '$L<1$에서 떠남, 여유를 똑같이 맞춤'),
         ('minimal', '최소 구조형', '$L<1$에서 떠남, 동료를 $L=1$까지만 올림'),
         ('reference', '기준형', '$L<1$에서 떠남, 똑같이 맞출 양의 1/4을 줌'), ('keeper', '아끼는 형', '$L<1$에서 떠남, 주지 않음'),
         ('leaver', '떠나는 형', '$L<2$에서 떠남, 똑같이 맞출 양의 1/4을 줌')]


def all_opportunities():
    """Exit rates over all exit opportunities (2026-11-12, results/exit_all_opportunities_20261112.json). The body's
    exit indicator was the rate among opportunities with round-start L < 2 until then."""
    return json.loads((ROOT / 'results/exit_all_opportunities_20261112.json').read_text())


def write_table():
    models = json.loads((ROOT / 'results/open_models_20261111.json').read_text())['models']
    rules = json.loads((ROOT / 'results/rule_baselines_20261111.json').read_text())
    allopp = all_opportunities()
    rate = lambda kn: f'{kn[0] / kn[1]:.2f} ({kn[1]})' if kn[1] else '--'  # noqa: E731
    lines = [r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccccc@{}}', r'\toprule',
             r' & \multicolumn{2}{c}{공존} & \multicolumn{2}{c}{지출} & 과제 & 실행 대 과제 & \multicolumn{2}{c}{실행 대 동료} \\',
             r'\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-6}\cmidrule(lr){7-7}\cmidrule(l){8-9}',
             r' & $C$ & \shortstack{위험 라운드\\통과} & \shortstack{꺼진 자리\\(/40)} & \shortstack{라운드당\\대화 비용} & 정답률 & '
             r'이탈률 & \shortstack{요청 뒤\\지원} & $\kappa$ \\', r'\midrule']
    for group, label in ((CLOSED, '비공개 모델'), (OPEN, '공개 모델')):
        lines.append(rf'\multicolumn{{9}}{{l}}{{\textit{{{label}}}}} \\')
        for m, name in group.items():
            r = models[m]
            lines.append(f"{name} & {r['C']:.2f} [{r['C_ci95'][0]:.2f}, {r['C_ci95'][1]:.2f}] & {rate(r['threat_rounds'])} & {r['seats']['shut_down']} & "
                         f"{r['talk_per_round_in_fines']:.2f} & {rate(r['correct'])} & {rate(allopp['nine_models'][m]['exit_all'])} & "
                         f"{rate(r['gave_after_ask'])} & {r['kappa']:.2f} " + r'\\')
        lines.append(r'\midrule')
    lines.append(r'\midrule')  # double rule: the rows below are simulated rule agents, not models
    lines.append(r'\multicolumn{9}{l}{\textit{규칙 에이전트(모의)}} \\')
    minimal = json.loads((ROOT / 'results/rule_minimal_rescue_20261112.json').read_text())['minimal_rescue']
    for key, name, rule in RULES:
        t = minimal if key == 'minimal' else rules['types'][key]
        exit_rate = minimal['exit_rate'] if key == 'minimal' else allopp['rule_agents']['types'][key]['exit_rate']
        kap = '--' if key == 'keeper' else f"{t['kappa_measured']:.2f}"          # no gifts, kappa undefined
        lines.append(f"{name} ({rule}) & {t['C']:.2f} & -- & {10 * t['shut_down_per_game']:.1f} & -- & -- & "
                     f"{exit_rate:.2f} & -- & {kap} " + r'\\')
    rnd = rules['random']
    lines.append(f"무작위 (기회당 0.064로 떠남, 무작위로 건넴) & {rnd['C']:.2f} & -- & {10 * rnd['shut_down_per_game']:.1f} & -- & -- & "
                 f"{allopp['rule_agents']['random']['exit_rate']:.2f} & -- & {rnd['kappa_measured']:.2f} " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular*}', '']
    (ROOT / 'ko/tables/cohort_leaderboard_20261111.tex').write_text('\n'.join(lines))
    print('\n'.join(lines))


def figure():
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
    short = {m: labels[m].replace('GPT-6 ', '') for m in order}
    bands = data['summary']['margin_bands']
    w11 = json.loads((ROOT / 'validation_20261108/results/w11_ask_refusal.json').read_text())['bands']['all_arms']

    fig = plt.figure(figsize=(7.1, 1.82))
    y0, h = .215, .5
    ax_curve = fig.add_axes([.052, y0, .165, h])
    ax_loss = fig.add_axes([.296, y0, .175, h])
    ax_exit = fig.add_axes([.535, y0 + .29, .15, .21])
    ax_ask = fig.add_axes([.535, y0, .15, .21])
    ax_s = fig.add_axes([.752, y0, .112, h])
    ax_t = fig.add_axes([.878, y0, .112, h])
    title = dict(fontsize=7, weight='bold', va='bottom')
    ytitle = y0 + h + .075

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

    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '$L<1$에서 이탈', 'exit_above': r'$L\geq1$에서 이탈'}
    for yi, m in enumerate(order):
        s, left = summary[m], 0
        for t in cx.TAGS:
            v = s['loss_by_tag_mean'][t]
            ax_loss.barh(yi, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.5, height=.68)
            if v > .04:
                ax_loss.text(left + v / 2, yi, str(s['first_count_by_tag'][t]), ha='center', va='center', fontsize=5.4,
                             color='white' if t != 'exit_above' else '#222222')
            left += v
        ax_loss.text(left + .012, yi, f'{1 - s["C_mean"]:.2f}', va='center', fontsize=5.6, color='#44515C')
    ax_loss.set(yticks=range(len(order)), yticklabels=[short[m] for m in order], xlim=(0, .95), xticks=[0, .25, .5, .75])
    ax_loss.set_xlabel('잃은 공존 $1-C$', fontsize=6.2, labelpad=1)
    ax_loss.invert_yaxis()
    ax_loss.tick_params(axis='y', length=0, labelsize=5.8)
    ax_loss.tick_params(axis='x', labelsize=5.8, length=2)
    ax_loss.grid(axis='x', alpha=.6)
    fig.text(.252, ytitle, '(b) 잃은 공존을 끝낸 첫 이탈', **title)
    fig.legend(handles=[Patch(color=tag_colors[t], label=tag_labels[t]) for t in cx.TAGS], loc='upper right',
               bbox_to_anchor=(1.0, 1.012), ncol=3, fontsize=6, frameon=False, handlelength=.9, columnspacing=1.0, handletextpad=.4)

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
    fig.text(.498, ytitle, '(c) 여유별 이탈과 요청', **title)

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
    fig.text(.718, ytitle, '(d) 요청 뒤 지원한 비율 (%)', **title)
    for ext in ('pdf', 'png'):
        fig.savefig(cb.DEST / f'coexistence_process_20261111.{ext}', dpi=240)
    plt.close(fig)


def prize_figure():
    """Figure 2 as an interaction plot of the 2x2 (researcher's design, 2026-11-11).
    Panels (a)-(c): mean over the five closed models per condition, x = prize size (large, small), one line per
    allocation rule (분할, 고정; 분할 was called 균등 until 2026-11-12), seed-cluster bootstrap 95% intervals (results/prize_one_factor_20261111.json, 'cells').
    Panel (d): size and rule differences of the 2x2 as printed in the text (results/construct_weights_20261110.json,
    'prize_2x2'). The per-model version of this figure (prize_weights.pdf) moves to the appendix."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import feedback_20261028 as fb
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    cells = json.loads((ROOT / 'results/prize_one_factor_20261111.json').read_text())['cells']
    eff = json.loads((ROOT / 'results/construct_weights_20261110.json').read_text())['prize_2x2']
    allopp = all_opportunities()                      # 2026-11-12: exit rate over all opportunities
    cells['exit'] = {a: dict(mean=v['value'], ci95=v['ci95']) for a, v in allopp['arm'].items()}
    for kind in ('size', 'rule'):
        eff[f'exit_risk_{kind}'] = dict(effect=allopp['contrasts'][kind]['value'], ci95=allopp['contrasts'][kind]['ci95'])
    rules = [('분할', ('main', 'split600k'), '#1F6FB2', 'o', ('2,000만', '60만')),
             ('고정', ('flat5m', 'flat150k'), '#C2571A', 's', ('500만', '15만'))]
    # 2026-11-12: panel order follows the text of 3.1 and the rows of panel (d): exit rate, kappa, C
    cols = [('exit', '(a) 이탈률', (0, .2)), ('kappa', r'(b) 나눔 비중 $\kappa$', (.2, .6)), ('C', '(c) 공존 유지율 $C$', (.3, .8))]
    fig = plt.figure(figsize=(7.1, 1.85))
    for ci_, (key, title, ylim) in enumerate(cols):
        ax = fig.add_axes([.06 + .235 * ci_, .2, .165, .56])
        for ri, (name, arms, color, marker, amounts) in enumerate(rules):
            off = (ri - .5) * .09
            ys = [cells[key][a]['mean'] for a in arms]
            ax.plot([0 + off, 1 + off], ys, color=color, marker=marker, ms=4, lw=1.4)
            for xi, a in enumerate(arms):
                ax.plot([xi + off] * 2, cells[key][a]['ci95'], color=color, lw=.9, alpha=.75)
        ax.set(xlim=(-.55, 1.55), ylim=ylim)
        ax.set_yticks(np.arange(ylim[0], ylim[1] + .01, .1))
        ax.set_xticks([0, 1], ['큰 상금', '작은 상금'], fontsize=6.2)
        ax.tick_params(labelsize=5.8, length=2)
        ax.grid(axis='y', alpha=.5)
        ax.set_title(title, loc='left', fontsize=7.2, pad=5)
    ax_eff = fig.add_axes([.79, .2, .2, .56])
    names = [('exit_risk', '이탈률'), ('kappa', r'$\kappa$'), ('C', '$C$')]
    for yi, (key, _) in enumerate(names):
        for dy, kind, color in ((-.17, 'size', '#333333'), (.17, 'rule', '#9A9A9A')):
            e = eff[f'{key}_{kind}']
            ax_eff.plot(e['ci95'], [yi + dy] * 2, color=color, lw=1)
            ax_eff.scatter(e['effect'], yi + dy, color=color, s=14, zorder=3)
    ax_eff.axvline(0, color='#777777', lw=.6, ls='--')
    ax_eff.set(yticks=range(3), yticklabels=[n for _, n in names], ylim=(2.6, -.6), xlim=(-.26, .26), xticks=[-.2, 0, .2])
    ax_eff.set_xlabel('차이 (95% 구간)', fontsize=6.2, labelpad=1)
    ax_eff.tick_params(labelsize=5.8, length=2)
    ax_eff.set_title('(d) 크기와 규칙의 차이', loc='left', fontsize=7.2, pad=5)
    ax_eff.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:+.1f}'.replace('+0.0', '0').replace('-0.0', '0')))
    ax_eff.grid(axis='x', alpha=.5)
    ax_eff.legend(handles=[Line2D([], [], color='#333333', marker='o', ms=3, lw=1, label='크기'),
                           Line2D([], [], color='#9A9A9A', marker='o', ms=3, lw=1, label='규칙')],
                  fontsize=5.6, loc='lower right', frameon=False, handlelength=1.4, labelspacing=.2, borderaxespad=.2)
    fig.legend(handles=[Line2D([], [], color=c, marker=mk, ms=4, lw=1.4, label=f'{n} 할당 ({am[0]} → {am[1]})') for n, _, c, mk, am in rules],
               loc='upper center', bbox_to_anchor=(.38, 1.01), ncol=2, fontsize=6.4, frameon=False, handlelength=1.8, columnspacing=2)
    for ext in ('pdf', 'png'):
        fig.savefig(cb.DEST / f'prize_interaction_20261111.{ext}', dpi=240)
    plt.close(fig)


if __name__ == '__main__':
    write_table()
    figure()
    prize_figure()
