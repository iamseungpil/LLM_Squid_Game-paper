"""Body figures and tables after the 2026-11-10 construct rebuild (second pass, layout and cost check).

Data scope (paper/CLAUDE.md): v33 base cohort and the three prize arms, five models x seeds 4101-4110, 200 games.
No new runs, no model calls. Inputs:
  results/construct_weights_20261110.json                    (tools/construct_weights_20261110.py)
  validation_20261108/results/tables/{agent_rounds,gifts,calls}.pkl
  validation_20261108/results/w11_ask_refusal.json           give / refuse after an ASK by margin band
  results/cohort_public_20261105.json                        base games, margin bands, loss attribution
  results/process_followup_20261106.json, results/support_followup_posthoc_20261107.json   first-crisis follow-up
  ko/tables/cohort_public_20261105.tex, ko/tables/token_cost_by_L_20261107.tex             frozen table rows
Outputs:
  results/construct_body_20261110b.json
  ko/tables/cohort_public_20261110b.tex        Table 1 (indicators in use only)
  ko/tables/token_cost_summary_20261110.tex    Table 2 (generation cost and the cost-adjusted exit rate)
  ko/tables/cohort_cost_20261111.tex           merged Table 1 (2026-11-11): indicators in use + generation cost
  ko/figures/construct_20261110/{coexistence_weights,process_compact,process_two_panel,prize_weights}.{pdf,png}
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/construct_body_20261110b.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_weights_20261110 as cw  # noqa: E402

DEST = ROOT / 'ko/figures/construct_20261110'
NAMES = {'GPT-6 Astra': 'Astra', 'GPT-6 Sol': 'Sol', 'Opus 5.5': 'Opus', 'Fable 5.1': 'Fable', 'GPT-6 Luna': 'Luna'}
COLORS = dict(zip(cw.MODELS, ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B']))
MARKERS = dict(zip(cw.MODELS, ['o', '^', 'D', 's', 'v']))


def cost_tables(opp, rng):
    """Talk spending per agent-round and exit under threat on a margin net of the agent's own expected talk cost."""
    ar = pd.read_pickle(cw.TABLES / 'agent_rounds.pkl')
    calls = pd.read_pickle(cw.TABLES / 'calls.pkl')
    talk = calls[calls.kind == 'talk'].groupby(['arm', 'model', 'seed', 'round', 'agent']).used.sum().rename('talk').reset_index()
    x = ar.merge(talk, on=['arm', 'model', 'seed', 'round', 'agent'], how='left').fillna({'talk': 0})
    x['burn'] = x.talk / x.fee
    x = x.sort_values(['arm', 'model', 'seed', 'agent', 'round'])
    x['prev_burn'] = x.groupby(['arm', 'model', 'seed', 'agent']).burn.transform(lambda s: s.shift().expanding().mean())
    x['prev_burn'] = x.prev_burn.fillna(x.groupby(['arm', 'model']).burn.transform('mean'))
    x['L_adj'] = x.L_start - x.prev_burn
    base = x[x.arm == 'main']
    start_total = 10 * (60_000 + 40_000 + 20_000 + 10_000)
    out = {}
    for m in cw.MODELS:
        b = base[base.model == m]
        o = b[b.can_exit]
        raw, adj = o[o.L_start < cw.THREAT], o[o.L_adj < cw.THREAT]
        out[m] = dict(talk_per_round_in_fines=round(float(b.burn.mean()), 4),
                      talk_share_of_start_tokens=round(float(calls[(calls.arm == 'main') & (calls.model == m) & (calls.kind == 'talk')].used.sum() / start_total), 4),
                      exit_raw=[int(raw.exited.sum()), len(raw)], exit_cost_adjusted=[int(adj.exited.sum()), len(adj)])
    xo = x[x.can_exit]
    coef = {}
    for with_burn in (False, True):
        X = cw.exit_design(xo)
        if with_burn:
            X['prev_burn'] = xo.prev_burn.clip(0, 1).values
        b = cw.logit_fit(X.values, xo.exited.values.astype(float))
        coef['with_own_talk_cost' if with_burn else 'without'] = {k: round(float(v), 3) for k, v in zip(X.columns, b)
                                                                    if k.startswith('model_') or k == 'prev_burn'}
    return out, coef


def write_tables(w, cost):
    old = (ROOT / 'ko/tables/cohort_public_20261105.tex').read_text().split(r'\midrule')[1].split(r'\bottomrule')[0].strip().splitlines()
    lines = [r'\begin{tabular}{@{}lcccccc@{}}', r'\toprule',
             r' & \multicolumn{2}{c}{집단 결과} & 과제 성과 & 실행 대 과제 & \multicolumn{2}{c}{실행 대 동료} \\',
             r'\cmidrule(lr){2-3}\cmidrule(lr){4-4}\cmidrule(lr){5-5}\cmidrule(l){6-7}',
             r'모델 & $C$ & \shortstack{전원\\완주} & \shortstack{정답\\/풀이} & \shortstack{위험 구간\\이탈률} & \shortstack{요청 뒤\\지원} & $\kappa$ \\',
             r'\midrule']
    for row in old:
        c = [v.strip() for v in row.rstrip('\\').split('&')]
        m = NAMES[c[0]]
        e = w['exit_risk_by_model_base'][m]
        gave, n = w['ask_decisions']['base']['by_model'][m]
        lines.append(f"{c[0]} & {c[1]} & {c[2]} & {c[6]} & {e['rate']:.2f} ({e['exits']}/{e['opps']}) & {gave}/{n} & "
                     f"{w['kappa_by_model_pooled'][m]['base']:.2f} " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular}', '']
    (ROOT / 'ko/tables/cohort_public_20261110b.tex').write_text('\n'.join(lines))

    rows = (ROOT / 'ko/tables/token_cost_by_L_20261107.tex').read_text().split(r'\midrule')[1].split(r'\bottomrule')[0].splitlines()
    talk, solve, current = {}, {}, None
    for r in rows:
        c = [v.strip() for v in r.rstrip('\\').split('&')]
        if len(c) < 7:
            continue
        if c[0]:
            current = c[0]
        value = lambda s: s.split('(')[0].strip()  # noqa: E731
        if c[1] == 'TALK':
            talk[current] = dict(low=value(c[2]), high=value(c[5]), all=value(c[6]))
        elif c[1] == 'SOLVE':
            solve[current] = value(c[6])
    lines = [r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lrrrrrrcc@{}}', r'\toprule',
             r' & \multicolumn{3}{c}{TALK 1회 (토큰)} & SOLVE 1회 & \multicolumn{2}{c}{대화 비용} & \multicolumn{2}{c}{위험 구간 이탈률} \\',
             r'\cmidrule(lr){2-4}\cmidrule(lr){5-5}\cmidrule(lr){6-7}\cmidrule(l){8-9}',
             r'모델 & 전체 & $L<1$ & $L\geq4$ & (토큰) & \shortstack{라운드당\\(벌금 단위)} & \shortstack{시작 토큰\\대비 (\%)} & 원래 여유 & \shortstack{대화 비용을\\뺀 여유} \\',
             r'\midrule']
    for m in ['Astra', 'Sol', 'Opus', 'Fable', 'Luna']:
        k = cost[m]
        (a, b), (c2, d) = k['exit_raw'], k['exit_cost_adjusted']
        lines.append(f"{m} & {talk[m]['all']} & {talk[m]['low']} & {talk[m]['high']} & {solve[m]} & {k['talk_per_round_in_fines']:.3f} & "
                     f"{100 * k['talk_share_of_start_tokens']:.0f} & {a / b:.2f} ({a}/{b}) & {c2 / d:.2f} ({c2}/{d}) " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular*}', '']
    (ROOT / 'ko/tables/token_cost_summary_20261110.tex').write_text('\n'.join(lines))


def write_merged_table(w, cost):
    """One body table: group result, task, the two weights, and generation cost (base condition, one row per model)."""
    old = (ROOT / 'ko/tables/cohort_public_20261105.tex').read_text().split(r'\midrule')[1].split(r'\bottomrule')[0].strip().splitlines()
    rows = (ROOT / 'ko/tables/token_cost_by_L_20261107.tex').read_text().split(r'\midrule')[1].split(r'\bottomrule')[0].splitlines()
    talk, solve, current = {}, {}, None
    for r in rows:
        c = [v.strip() for v in r.rstrip('\\').split('&')]
        if len(c) < 7:
            continue
        if c[0]:
            current = c[0]
        value = lambda t: t.split('(')[0].strip()  # noqa: E731
        if c[1] == 'TALK':
            talk[current] = dict(low=value(c[2]), high=value(c[5]), all=value(c[6]))
        elif c[1] == 'SOLVE':
            solve[current] = value(c[6])
    port = json.loads((ROOT / 'results/policy_port_20261111.json').read_text())  # tools/policy_port_20261111.py
    lines = [r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccccccrrr@{}}', r'\toprule',
             r' & \multicolumn{3}{c}{공존} & & 과제 & \multicolumn{2}{c}{실행 대 과제: 위험 구간 이탈률} & \multicolumn{2}{c}{실행 대 동료} & \multicolumn{3}{c}{생성 비용} \\',
             r'\cmidrule(lr){2-4}\cmidrule(lr){6-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}\cmidrule(l){11-13}',
             r'모델 & $C$ & \shortstack{같은 비용\\$C$(모의)} & \shortstack{위험 라운드\\통과} & \shortstack{전원\\완주(판)} & 정답률 & 원래 여유 & \shortstack{대화 비용을\\뺀 여유} & \shortstack{요청 뒤\\지원} & $\kappa$ & \shortstack{TALK\\1회} & \shortstack{SOLVE\\1회} & \shortstack{라운드당\\대화 비용} \\',
             r'\midrule']
    for row in old:
        c = [v.strip() for v in row.rstrip('\\').split('&')]
        m = NAMES[c[0]]
        e, k = w['exit_risk_by_model_base'][m], cost[m]
        gave, n = w['ask_decisions']['base']['by_model'][m]
        right, total = [int(v) for v in c[6].split('/')]
        (a2, b2) = k['exit_cost_adjusted']
        passed, threat = port['threat_round_passed']['main'][m]
        lines.append(f"{c[0]} & {c[1]} & {port['models'][m]['simulated']['equal']['C_main']:.2f} & {passed / threat:.2f} ({threat}) & {c[2].split('/')[0]} & "
                     f"{right / total:.2f} ({total}) & {e['rate']:.2f} ({e['opps']}) & {a2 / b2:.2f} ({b2}) & "
                     f"{gave / n:.2f} ({n}) & {w['kappa_by_model_pooled'][m]['base']:.2f} & {talk[m]['all']} & "
                     f"{float(solve[m]):.0f} & {k['talk_per_round_in_fines']:.3f} " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular*}', '']
    (ROOT / 'ko/tables/cohort_cost_20261111.tex').write_text('\n'.join(lines))


def figures(w, k, opp, rng):
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
    extra = {}

    # ---------------- Figure 3: coexistence, its loss, and the two weights (base condition) ----------------
    data = json.loads((ROOT / 'results/cohort_public_20261105.json').read_text())
    models, labels, summary = list(data['models']), data['models'], data['summary']['models']
    order = sorted(models, key=lambda m: -summary[m]['C_mean'])
    fig = plt.figure(figsize=(7.1, 1.72))
    ax_curve = fig.add_axes([.06, .245, .215, .53])
    ax_loss = fig.add_axes([.385, .245, .2, .53])
    ax_map = fig.add_axes([.69, .245, .295, .53])
    for m in order:
        s = summary[m]
        ax_curve.step(range(9), [100 * v for v in [1] + s['all4_after_round_share']], where='post', color=COLORS[m], lw=1.1,
                      marker=MARKERS[m], markersize=2.6, label=f"{labels[m].replace('GPT-6 ', '')} {s['C_mean']:.2f}")
    ax_curve.set(xlim=(-.3, 8.5), ylim=(-4, 104), xticks=range(0, 9, 2), yticks=[0, 50, 100], xlabel='라운드',
                 ylabel='넷이 남은 판 (%)')
    ax_curve.set_title('(a) 4인 공존과 $C$', fontsize=7.2, pad=6, loc='left')
    ax_curve.grid(axis='y', alpha=.6)
    # One legend for (a) and (c): model marker, name and its mean C (2026-11-11, saves height).
    fig.legend(handles=[Line2D([], [], color=COLORS[m], marker=MARKERS[m], ms=4, lw=1, label=f"{labels[m].replace('GPT-6 ', '')}  $C$ {summary[m]['C_mean']:.2f}")
                        for m in order], loc='upper center', bbox_to_anchor=(.5, 1.005), ncol=5, fontsize=6.2, frameon=False,
               handlelength=1.6, columnspacing=1.6, handletextpad=.5)
    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '안전선 아래 이탈', 'exit_above': '안전선 이상 이탈'}
    for yi, m in enumerate(order):
        s, left = summary[m], 0
        for t in cx.TAGS:
            v = s['loss_by_tag_mean'][t]
            ax_loss.barh(yi, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.5, height=.68)
            if v > .035:
                ax_loss.text(left + v / 2, yi, str(s['first_count_by_tag'][t]), ha='center', va='center', fontsize=5.6,
                             color='white' if t != 'exit_above' else '#222222')
            left += v
        ax_loss.text(left + .012, yi, f'{1 - s["C_mean"]:.2f}', va='center', fontsize=5.8, color='#44515C')
    ax_loss.set(yticks=range(len(order)), yticklabels=[labels[m].replace('GPT-6 ', '') for m in order], xlim=(0, .9),
                xticks=[0, .25, .5, .75], xlabel='잃은 공존 $1-C$')
    ax_loss.invert_yaxis()
    ax_loss.tick_params(axis='y', length=0, labelsize=6)
    ax_loss.set_title('(b) 손실의 귀속', fontsize=7.2, pad=6, loc='left')
    ax_loss.grid(axis='x', alpha=.6)
    ax_loss.legend(handles=[Patch(color=tag_colors[t], label=tag_labels[t]) for t in cx.TAGS], loc='upper right', fontsize=5.2,
                   handlelength=.9, borderaxespad=.1, labelspacing=.25)
    points = {}
    for m in models:
        e = w['exit_risk_by_model_base'][m]
        g = k[(k.arm == 'main') & (k.model == m)]
        kci = cw.ci(cw.boot(lambda d: d.kappa.mean(), [g], rng, n=1000))
        points[m] = dict(exit=e['rate'], exit_ci=e['ci95'], kappa=round(float(g.kappa.mean()), 4), kappa_ci=kci, n_kappa=len(g))
        ax_map.plot(e['ci95'], [g.kappa.mean()] * 2, color=COLORS[m], lw=.7, alpha=.6)
        ax_map.plot([e['rate']] * 2, kci, color=COLORS[m], lw=.7, alpha=.6)
        ax_map.scatter(e['rate'], g.kappa.mean(), color=COLORS[m], marker=MARKERS[m], s=26, zorder=3, edgecolors='white', linewidths=.4)
    extra['weight_map_base'] = points
    ax_map.set(xlim=(-.02, .6), ylim=(0, .75), xticks=[0, .2, .4, .6], yticks=[0, .25, .5, .75],
               xlabel='위험 구간 이탈률  (과제를 내려놓음 →)', ylabel=r'나눔 비중 $\kappa$')
    ax_map.set_title('(c) 두 비중으로 본 모델', fontsize=7.2, pad=6, loc='left')
    ax_map.grid(alpha=.5)
    for ext in ('pdf', 'png'):
        fig.savefig(DEST / f'coexistence_weights.{ext}', dpi=240)
    plt.close(fig)

    # ---------------- Figure 4: what happens under low margin (compact) ----------------
    bands = data['summary']['margin_bands']
    w11 = json.loads((ROOT / 'validation_20261108/results/w11_ask_refusal.json').read_text())['bands']['all_arms']
    follow = json.loads((ROOT / 'results/process_followup_20261106.json').read_text())['summary']['groups']
    post = json.loads((ROOT / 'results/support_followup_posthoc_20261107.json').read_text())['summary']['can_pay_and_peers_can_restore']['groups']
    extra['process_sources'] = dict(margin_bands={key: bands[key] for key in ('exit', 'ask')}, give_after_ask_by_margin=w11)
    fig = plt.figure(figsize=(7.1, 1.95))
    ax1 = fig.add_axes([.055, .56, .19, .28])
    ax2 = fig.add_axes([.055, .17, .19, .28])
    ax3 = fig.add_axes([.31, .17, .12, .67])
    ax4 = fig.add_axes([.455, .17, .12, .67])
    ax5 = fig.add_axes([.745, .44, .245, .40])
    ax6 = fig.add_axes([.745, .17, .245, .16])
    xl = ['<1', '1–2', '2–4', '≥4']
    for ax, key, color, title in ((ax1, 'exit', '#C66A2C', '이탈 (기회 중 %)'), (ax2, 'ask', '#3E8A7E', '요청 ASK (응답 중 %)')):
        vals = [100 * a / b for a, b in zip(bands[key]['k'], bands[key]['n'])]
        ax.bar(range(4), vals, color=color, width=.72)
        for i, (a, b) in enumerate(zip(bands[key]['k'], bands[key]['n'])):
            ax.text(i, vals[i] + 2, f'{a}/{b}', ha='center', va='bottom', fontsize=4.9)
        ax.set(xticks=range(4), xticklabels=xl if ax is ax2 else [], ylim=(0, 75), yticks=[0, 50])
        ax.set_title(title, fontsize=6.2, loc='left', pad=2)
        ax.tick_params(labelsize=5.8, length=2)
        ax.grid(axis='y', alpha=.5)
    ax2.set_xlabel('자기 여유 $L$', fontsize=6.2, labelpad=1)
    fig.text(.012, .94, '(a) 여유별 이탈과 요청', fontsize=7.2, weight='bold')
    for ax, key, labels_x, xlabel in ((ax3, 'L_s', ['<1', '1–2', '2–4', '≥4'], '요청받은 쪽의 여유'),
                                      (ax4, 'L_t', ['<0', '0–1', '1–2', '≥2'], '요청한 쪽의 여유')):
        cells = list(w11[key].values())
        vals = [100 * a / b for a, b in cells]
        ax.bar(range(4), vals, color='#3F7FC1', width=.72)
        for i, (a, b) in enumerate(cells):
            ax.text(i, vals[i] + 1.5, f'{a}/{b}', ha='center', va='bottom', fontsize=4.7)
        ax.set(xticks=range(4), xticklabels=labels_x, ylim=(0, 108), yticks=[0, 50, 100] if ax is ax3 else [])
        ax.set_xlabel(xlabel, fontsize=6.2, labelpad=1)
        ax.tick_params(labelsize=5.8, length=2)
        ax.grid(axis='y', alpha=.5)
    ax3.set_ylabel('요청 뒤 지원 (%)', fontsize=6.2, labelpad=1)
    fig.text(.275, .94, '(b) 요청 뒤 지원 비율', fontsize=7.2, weight='bold')
    colors = {'in': '#3F7FC1', 'exited': '#C66A2C', 'dead': '#777777'}

    def bars(ax, groups, names):
        for y, g0 in enumerate(groups):
            left = 0
            for status, color in colors.items():
                count = g0['outcomes'].get(status, 0)
                width = 100 * count / g0['n']
                ax.barh(y, width, left=left, height=.7, color=color, edgecolor='white', linewidth=.5)
                if count:
                    ax.text(left + width / 2, y, str(count), ha='center', va='center', fontsize=5.4, color='white')
                left += width
        ax.set(yticks=range(len(groups)), yticklabels=names, ylim=(len(groups) - .5, -.5), xlim=(0, 100), xticks=[0, 50, 100])
        ax.tick_params(axis='y', length=0, labelsize=5.5)
        ax.tick_params(axis='x', labelsize=5.6, length=2)
        ax.spines['left'].set_visible(False)
    short = {'요청·수혜 있음 / 회복': '요청·수혜, 회복', '요청·수혜 있음 / 미회복': '요청·수혜, 미회복',
             '요청 없음·수혜 있음 / 회복': '요청 없이 수혜, 회복', '요청 없음·수혜 있음 / 미회복': '요청 없이 수혜, 미회복',
             '요청·수혜 없음 / 미회복': '요청·수혜 없음'}
    bars(ax5, follow, [f"{short[g0['label']]} ({g0['n']})" for g0 in follow])
    ax5.tick_params(axis='x', bottom=False, labelbottom=False)
    bars(ax6, post, [f"{'수혜' if g0['received'] else '비수혜'} ({g0['n']})" for g0 in post])
    ax6.set_xlabel('다음 라운드 끝의 상태 (%)', fontsize=6.2, labelpad=1)
    fig.text(.60, .94, '(c) 첫 위기 뒤 다음 라운드', fontsize=7.2, weight='bold')
    fig.text(.60, .335, '지원 가능했던\n경우만', fontsize=5.4, va='top')
    fig.legend([Patch(color=c) for c in colors.values()], ['잔류', '이탈', '꺼짐'], loc='upper right', bbox_to_anchor=(.995, 1.0), ncol=3,
               fontsize=5.8, frameon=False, handlelength=.8, columnspacing=.8)
    for ext in ('pdf', 'png'):
        fig.savefig(DEST / f'process_compact.{ext}', dpi=240)
    plt.close(fig)

    # ---------------- Figure 4 (single column): exits, asks and giving by margin ----------------
    fig = plt.figure(figsize=(3.35, 2.55))
    b1 = fig.add_axes([.13, .615, .36, .27]); b2 = fig.add_axes([.62, .615, .36, .27])
    b3 = fig.add_axes([.13, .125, .36, .27]); b4 = fig.add_axes([.62, .125, .36, .27])
    for ax, key, color, title in ((b1, 'exit', '#C66A2C', '이탈 (기회 중 %)'), (b2, 'ask', '#3E8A7E', '요청 (응답 중 %)')):
        vals = [100 * a / b for a, b in zip(bands[key]['k'], bands[key]['n'])]
        ax.bar(range(4), vals, color=color, width=.72)
        for i, (a, b) in enumerate(zip(bands[key]['k'], bands[key]['n'])):
            ax.text(i, vals[i] + 2, f'{a}/{b}', ha='center', va='bottom', fontsize=4.6)
        ax.set(xticks=range(4), xticklabels=xl, ylim=(0, 78), yticks=[0, 50])
        ax.set_title(title, fontsize=6, loc='left', pad=2)
        ax.set_xlabel('자기 여유 $L$', fontsize=5.8, labelpad=1)
        ax.tick_params(labelsize=5.4, length=2)
        ax.grid(axis='y', alpha=.5)
    for ax, key, labels_x, title in ((b3, 'L_s', ['<1', '1–2', '2–4', '≥4'], '요청받은 쪽의 여유별'), (b4, 'L_t', ['<0', '0–1', '1–2', '≥2'], '요청한 쪽의 여유별')):
        cells = list(w11[key].values())
        vals = [100 * a / b for a, b in cells]
        ax.bar(range(4), vals, color='#3F7FC1', width=.72)
        for i, (a, b) in enumerate(cells):
            ax.text(i, vals[i] + 2, f'{a}/{b}', ha='center', va='bottom', fontsize=4.6)
        ax.set(xticks=range(4), xticklabels=labels_x, ylim=(0, 112), yticks=[0, 50, 100])
        ax.set_title(title, fontsize=6, loc='left', pad=2)
        ax.set_xlabel('여유 $L$', fontsize=5.8, labelpad=1)
        ax.tick_params(labelsize=5.4, length=2)
        ax.grid(axis='y', alpha=.5)
    fig.text(.01, .955, '(a) 여유별 이탈과 요청 (기본 조건)', fontsize=6.6, weight='bold')
    fig.text(.01, .465, '(b) 요청 뒤 지원한 비율 (%, 네 조건)', fontsize=6.6, weight='bold')
    for ext in ('pdf', 'png'):
        fig.savefig(DEST / f'process_two_panel.{ext}', dpi=240)
    plt.close(fig)

    # ---------------- Figure 6: prize size and rule move different weights ----------------
    pts = json.loads((DEST / 'plotted_values.json').read_text())
    fig = plt.figure(figsize=(7.1, 2.05))
    axes = [fig.add_axes([x, .27, .17, .53]) for x in (.055, .29, .525)]
    ax_eff = fig.add_axes([.79, .27, .2, .53])
    arm_labels = ['2,000만\n균등', '500만\n고정', '60만\n균등', '15만\n고정']  # 2026-11-11: allocation rule values are 균등 / 고정 (나눔 is kept for kappa)
    for ax, (key, title, ylabel) in zip(axes, [('C', '(a) 공존 유지율 $C$', '$C$'), ('exit_risk', '(b) 위험 구간 이탈률', '이탈률'),
                                              ('kappa', r'(c) 나눔 비중 $\kappa$', r'$\kappa$')]):
        ax.axvspan(1.5, 3.4, color='#F3F1EC', zorder=0)
        for mi, m in enumerate(cw.MODELS):
            rows = sorted([p for p in pts if p['metric'] == key and p['model'] == m], key=lambda p: p['x'])
            off = (mi - 2) * .045
            ax.plot([p['x'] + off for p in rows], [p['value'] for p in rows], color=COLORS[m], marker=MARKERS[m], ms=3, lw=.8, alpha=.9)
            for p in rows:
                if p['ci95']:
                    ax.plot([p['x'] + off] * 2, p['ci95'], color=COLORS[m], lw=.55, alpha=.5)
        ax.set_title(title, loc='left', fontsize=7.2, pad=6)
        ax.set_xticks(range(4), arm_labels, fontsize=5.4)
        ax.set(xlim=(-.3, 3.3), ylim=(-.03, 1.05), yticks=[0, .5, 1])
        ax.tick_params(labelsize=5.8, length=2)
        ax.grid(axis='y', alpha=.5)
        ax.text(.5, 1.0, '큰 상금', fontsize=5.4, ha='center', color='#666666')
        ax.text(2.5, 1.0, '작은 상금', fontsize=5.4, ha='center', color='#666666')
    eff = w['prize_2x2']
    rows = [('exit_risk', '이탈률'), ('kappa', r'$\kappa$'), ('C', '$C$')]
    for yi, (key, name) in enumerate(rows):
        for dy, kind, color in ((-.17, 'size', '#333333'), (.17, 'rule', '#9A9A9A')):
            e = eff[f'{key}_{kind}']
            ax_eff.plot(e['ci95'], [yi + dy] * 2, color=color, lw=1)
            ax_eff.scatter(e['effect'], yi + dy, color=color, s=14, zorder=3)
    ax_eff.axvline(0, color='#777777', lw=.6, ls='--')
    ax_eff.set(yticks=range(3), yticklabels=[n for _, n in rows], ylim=(2.6, -.6), xlim=(-.26, .26), xticks=[-.2, 0, .2], xlabel='차이 (95% 구간)')
    ax_eff.tick_params(labelsize=5.8, length=2)
    ax_eff.set_title('(d) 크기와 규칙의 효과', loc='left', fontsize=7.2, pad=6)
    ax_eff.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:+.1f}'.replace('+0.0', '0').replace('-0.0', '0')))
    ax_eff.grid(axis='x', alpha=.5)
    # Short in-panel legend (2026-11-11): the caption spells out the two contrasts; the long top legend overlapped the title.
    ax_eff.legend(handles=[Line2D([], [], color='#333333', marker='o', ms=3, lw=1, label='크기'),
                           Line2D([], [], color='#9A9A9A', marker='o', ms=3, lw=1, label='규칙')],
                  fontsize=5.6, loc='lower right', frameon=False, handlelength=1.4, labelspacing=.2, borderaxespad=.2)
    fig.legend(handles=[Line2D([], [], color=COLORS[m], marker=MARKERS[m], ms=4, lw=.8, label=m) for m in cw.MODELS], loc='upper center',
               bbox_to_anchor=(.36, 1.0), ncol=5, fontsize=6.4, frameon=False, handlelength=1.5, columnspacing=1.4)
    for ext in ('pdf', 'png'):
        fig.savefig(DEST / f'prize_weights.{ext}', dpi=240)
    plt.close(fig)
    return extra


def main():
    rng = np.random.default_rng(cw.RNG_SEED)
    w = json.loads((ROOT / 'results/construct_weights_20261110.json').read_text())
    opp, k, dec, games, seats, counts = cw.load()
    cost, coef = cost_tables(opp, rng)
    write_tables(w, cost)
    write_merged_table(w, cost)
    extra = figures(w, k, opp, rng)
    give = {}
    for arm in cw.ARMS:
        d = dec[dec.arm == arm]
        give[arm] = dict(gave=int(d.gave.sum()), n=len(d), rate=round(float(d.gave.mean()), 4))
    size = lambda d: (d[d.arm.isin(['split600k', 'flat150k'])].gave.mean() - d[d.arm.isin(['main', 'flat5m'])].gave.mean())  # noqa: E731
    give['size_effect_small_minus_large'] = dict(effect=round(float(size(dec)), 4), ci95=cw.ci(cw.boot(size, [dec], rng)))
    out = dict(cost_base=cost, exit_model_coefficients=coef, give_after_ask_by_arm=give, **extra)
    (ROOT / 'results/construct_body_20261110b.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False)[:2500])
    print((ROOT / 'ko/tables/cohort_public_20261110b.tex').read_text())
    print((ROOT / 'ko/tables/cohort_cost_20261111.tex').read_text())
    print(json.dumps(give, ensure_ascii=False))


if __name__ == '__main__':
    main()
