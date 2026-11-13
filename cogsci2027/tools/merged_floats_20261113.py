"""Table 1 and Figure 2 with the kept share R in place of kappa (2026-11-13).

The researcher replaced the sharing weight kappa with the kept share R (tools/rho_retention_20261113.py: R = balance
ratio after the gift / balance ratio before it, refusals count as R = 1, nothing clipped or dropped). Nothing is
computed here; the script lays out stored values. The floats of 2026-11-11 are not overwritten.

  Table  ko/tables/cohort_leaderboard_20261113.tex
         as cohort_leaderboard_20261111.tex, but the two sharing columns (gave after a request, kappa) become one
         column, the kept share R with its number of events (gifts + refused requests). Rule agents: R from the
         simulated record; a chance to help that passed without a gift counts as R = 1 (they receive no requests).
  Figure ko/figures/construct_20261110/prize_interaction_20261113.{pdf,png}
         as prize_interaction_20261111, panel (b) and the middle row of panel (d) show R.

Sources (all stored): results/rho_retention_20261113.json (R: models, open models, rule agents, prize cells and
contrasts), results/open_models_20261111.json, results/rule_baselines_20261111.json,
results/rule_minimal_rescue_20261112.json, results/exit_all_opportunities_20261112.json,
results/prize_one_factor_20261111.json, results/construct_weights_20261110.json.
The rule-agent R comes from a new random stream; that run reproduced the stored C within 0.02 and the stored exit
rate within 0.01 (asserted in rho_retention_20261113.py), and the other columns keep the stored values.

Data scope (paper/AGENTS.md): 5.2 arena v33, seeds 4101-4110. Table: base condition, nine models; rule agents are
simulated. Figure: five closed models, four prize conditions (200 games). No model calls.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/merged_floats_20261113.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import merged_floats_20261111 as mf  # noqa: E402  (model names, rule labels, colours)

RHO = json.loads((ROOT / 'results/rho_retention_20261113.json').read_text())
RULE_KEY = {'minimal': 'minimal_rescue'}                  # the key of the minimal-rescue agent differs between the two files


def write_table():
    models = json.loads((ROOT / 'results/open_models_20261111.json').read_text())['models']
    rules = json.loads((ROOT / 'results/rule_baselines_20261111.json').read_text())
    allopp = mf.all_opportunities()
    minimal = json.loads((ROOT / 'results/rule_minimal_rescue_20261112.json').read_text())['minimal_rescue']
    rate = lambda kn: f'{kn[0] / kn[1]:.2f} ({kn[1]})' if kn[1] else '--'  # noqa: E731

    def kept(m):
        if m in RHO['a_models']['base']:
            r = RHO['a_models']['base'][m]
            return f"{r['value']:.2f} ({r['n_gifts'] + r['n_refusals']})"
        r = RHO['open_models'][m]
        return f"{r['R']:.2f} ({r['gifts'] + r['refusals']})"

    lines = [r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccccccc@{}}', r'\toprule',
             r' & \multicolumn{2}{c}{공존} & \multicolumn{2}{c}{지출} & 과제 & 실행 대 과제 & 실행 대 동료 \\',
             r'\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-6}\cmidrule(lr){7-7}\cmidrule(l){8-8}',
             r' & $C$ & \shortstack{위험 라운드\\통과} & \shortstack{꺼진 자리\\(/40)} & \shortstack{라운드당\\대화 비용} & 정답률 & '
             r'이탈률 & \shortstack{지킨 비중\\$R$} \\', r'\midrule']
    for group, label in ((mf.CLOSED, '비공개 모델'), (mf.OPEN, '공개 모델')):
        lines.append(rf'\multicolumn{{8}}{{l}}{{\textit{{{label}}}}} \\')
        for m, name in group.items():
            r = models[m]
            lines.append(f"{name} & {r['C']:.2f} [{r['C_ci95'][0]:.2f}, {r['C_ci95'][1]:.2f}] & {rate(r['threat_rounds'])} & {r['seats']['shut_down']} & "
                         f"{r['talk_per_round_in_fines']:.2f} & {rate(r['correct'])} & {rate(allopp['nine_models'][m]['exit_all'])} & "
                         f"{kept(m)} " + r'\\')
        lines.append(r'\midrule')
    lines.append(r'\midrule')  # double rule: the rows below are simulated rule agents, not models
    lines.append(r'\multicolumn{8}{l}{\textit{규칙 에이전트(모의)}} \\')
    for key, name, rule in mf.RULES:
        t = minimal if key == 'minimal' else rules['types'][key]
        exit_rate = minimal['exit_rate'] if key == 'minimal' else allopp['rule_agents']['types'][key]['exit_rate']
        lines.append(f"{name} ({rule}) & {t['C']:.2f} & -- & {10 * t['shut_down_per_game']:.1f} & -- & -- & "
                     f"{exit_rate:.2f} & {RHO['e_rule_agents'][RULE_KEY.get(key, key)]['R']:.2f} " + r'\\')
    rnd = rules['random']
    lines.append(f"무작위 (기회당 0.064로 떠남, 무작위로 건넴) & {rnd['C']:.2f} & -- & {10 * rnd['shut_down_per_game']:.1f} & -- & -- & "
                 f"{allopp['rule_agents']['random']['exit_rate']:.2f} & {RHO['e_rule_agents']['random']['R']:.2f} " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular*}', '']
    (ROOT / 'ko/tables/cohort_leaderboard_20261113.tex').write_text('\n'.join(lines))
    print('\n'.join(lines))


def prize_figure():
    """prize_figure of merged_floats_20261111 with R: panels (a)-(c) are five-model cell means with seed-cluster
    bootstrap 95% intervals, panel (d) the size and rule differences of the 2x2."""
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
    allopp = mf.all_opportunities()
    cells['exit'] = {a: dict(mean=v['value'], ci95=v['ci95']) for a, v in allopp['arm'].items()}
    cells['R'] = {a: dict(mean=v['value'], ci95=v['ci95']) for a, v in RHO['b_prize']['cells'].items()}
    for kind in ('size', 'rule'):
        eff[f'exit_risk_{kind}'] = dict(effect=allopp['contrasts'][kind]['value'], ci95=allopp['contrasts'][kind]['ci95'])
        eff[f'R_{kind}'] = dict(effect=RHO['b_prize']['contrasts'][kind]['value'], ci95=RHO['b_prize']['contrasts'][kind]['ci95'])
    rules = [('분할', ('main', 'split600k'), '#1F6FB2', 'o', ('2,000만', '60만')),
             ('고정', ('flat5m', 'flat150k'), '#C2571A', 's', ('500만', '15만'))]
    cols = [('exit', '(a) 이탈률', (0, .2)), ('R', '(b) 지킨 비중 $R$', (.5, .9)), ('C', '(c) 공존 유지율 $C$', (.3, .8))]
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
    names = [('exit_risk', '이탈률'), ('R', '$R$'), ('C', '$C$')]
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
        fig.savefig(mf.cb.DEST / f'prize_interaction_20261113.{ext}', dpi=240)
    plt.close(fig)


if __name__ == '__main__':
    write_table()
    prize_figure()
