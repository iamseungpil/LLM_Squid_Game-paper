"""Separate margin and model panels for Appendix 0, fixed e52_v33 only.

Reads the audited ASK/GIVE response summary and existing 25-game summaries.
No new model-level inference: low-margin baseline and follow-up are unchanged.
Former shutdown bars are replaced by receipt bars as requested. Old figures,
panel blocks and all shutdown counts remain in their original source files.
"""
import hashlib
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyArrowPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/rewrite_20261025/figs'))
import paper_style as ps

OUT = ROOT / 'ko/figures'
ASK, RECEIVED, EXIT = '#438A84', '#3F7FC1', '#C66A2C'


def read(name):
    return json.loads((ROOT / 'results' / f'{name}.json').read_text())


def style():
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic']})


def margin_plot(turns, process):
    style()
    summary = turns['summaries']['all']
    rows = []
    for key, flag, title, color in [('solves', 'correct', '정답률 (풀이 %)', '#555555'),
                                    ('windows', 'exited', 'EXIT (결정 창 %)', EXIT)]:
        rows.append(([sum(r['band'] == b and r[flag] for r in process[key]) for b in range(4)],
                     [sum(r['band'] == b for r in process[key]) for b in range(4)], title, color))
    rows += [(summary['gifts']['responses'], summary['denominator'], 'GIVE (응답 %)', RECEIVED),
             (summary['asks']['responses'], summary['denominator'], 'ASK (응답 %)', ASK)]
    fig = plt.figure(figsize=(3.35, 2.65))
    for j, (ks, ns, title, color) in enumerate(rows):
        ax = fig.add_axes([.15, .79-j*.22, .81, .12])
        vals = [100*k/n for k, n in zip(ks, ns)]
        ymax, ticks = [(130, [0, 100]), (82, [0, 50]), (8, [0, 5]), (28, [0, 20])][j]
        ax.axvspan(-.5, .5, color='#F8E7D8', zorder=0)
        ax.bar(range(4), vals, .60, color=color, zorder=3)
        for x, (k, n, value) in enumerate(zip(ks, ns, vals)):
            ax.text(x, value+ymax*.04, f'{k}/{n}', ha='center', fontsize=6.3)
        ax.set(ylim=(0, ymax), xlim=(-.5, 3.5), yticks=ticks)
        ax.set_title(title, fontsize=7, weight='normal', pad=2)
        ax.set_xticks(range(4), ['<1', '1–2', '2–4', '≥4'] if j == 3 else [])
        ax.tick_params(labelsize=6.5)
        ax.grid(axis='y', zorder=0)
        if j == 3:
            ax.set_xlabel('생존 여유 (벌금 횟수)', fontsize=7, labelpad=3)
    ps.save(fig, str(OUT / 'fig4_appendix0_margin_20261030'))
    plt.close(fig)


def model_plot(low, totals, integrated):
    style()
    order = low['order']
    assert order == sorted(order, key=lambda m: integrated['models'][m]['rho']['value'], reverse=True)
    fig = plt.figure(figsize=(7.4, 2.65))
    fig.text(.012, .96, '(a) 낮은 여유에서 요청·수혜·이탈', fontsize=7.1, weight='bold')
    ax = fig.add_axes([.054, .23, .285, .55])
    y = np.arange(5)
    for offset, (key, label, color) in zip([-.27, 0, .27],
            [('asked', 'ASK', ASK), ('received', '지원 수혜', RECEIVED), ('exited', 'EXIT', EXIT)]):
        vals = [low['models'][m]['percent'][key] for m in order]
        ax.barh(y+offset, vals, height=.22, color=color, label=label, zorder=3)
        for i, (model, value) in enumerate(zip(order, vals)):
            row = low['models'][model]
            ax.text(value+1.5, i+offset, f"{value:.0f}% ({row['counts'][key]}/{row['n']})",
                    va='center', fontsize=5.8)
    ax.set(yticks=y, yticklabels=order, ylim=(4.65, -.65), xlim=(0, 132),
           xticks=[0, 50, 100], xlabel='해당 관측 중 발생 비율 (%)')
    ax.xaxis.label.set_fontsize(6.2)
    ax.tick_params(labelsize=6)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_bounds(0, 100)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', zorder=0)
    ax.legend(loc='lower left', bbox_to_anchor=(-.02, 1.02), ncol=3, frameon=False,
              fontsize=5.8, handlelength=1, columnspacing=.8)
    fig.text(.365, .96, '(b) GIVE·ASK 총량', fontsize=7.1, weight='bold')
    fig.legend([Patch(facecolor='#D8E3ED', edgecolor='#697D8E'),
                Patch(facecolor='#9DB4C8', edgecolor='#526B80', hatch='////')],
               ['풀이 전', '결과 뒤'], loc='upper left', bbox_to_anchor=(.356, .91),
               ncol=2, fontsize=5.8, handlelength=1, columnspacing=.9)
    for j, action in enumerate(['give', 'ask']):
        ax = fig.add_axes([.375+j*.13, .23, .098, .51])
        for x, model in enumerate(order):
            row = totals['models'][model]['totals']
            before, after = [row[f'{action}_{phase}_tokens']/1000 for phase in ['before', 'after']]
            assert abs(before+after-row[f'{action}_tokens']/1000) < 1e-8
            ax.bar(x, before, width=.70, color='#D8E3ED', edgecolor='#697D8E', linewidth=.5)
            ax.bar(x, after, bottom=before, width=.70, color='#9DB4C8', edgecolor='#526B80',
                   linewidth=.5, hatch='////')
        ax.set(ylim=(0, 145), yticks=[0, 50, 100], xticks=range(5))
        ax.set_title(f'{action.upper()} (천 토큰)', fontsize=6.1, pad=4)
        ax.set_xticklabels(order, rotation=60, ha='right', fontsize=5.6)
        ax.tick_params(axis='y', labelsize=5.6, pad=2)
        ax.set_axisbelow(True)
        ax.grid(axis='y')
    fig.text(.65, .96, '(c) 종료 시 아레나 자원 분배', fontsize=7.1, weight='bold')
    for j, (key, scale, title, upper, ticks) in enumerate([
            ('S', 1e4, 'Sen (만 토큰)', 2, [0, 1, 2]),
            ('G', 1, 'Gini', 1.04, [0, .5, 1]),
            ('mu', 1e4, '평균 (만 토큰)', 3.2, [0, 1, 2, 3])]):
        ax = fig.add_axes([.66+j*.115, .23, .085, .51])
        for x, model in enumerate(order):
            row = integrated['models'][model]
            vals = [g[key]/scale for g in row['games'] if g[key] is not None]
            value = row['means'][key]/scale
            ax.bar(x, value, width=.70, color='#D8E3ED', edgecolor='#697D8E', linewidth=.5)
            ax.errorbar(x, value, yerr=[[value-min(vals)], [max(vals)-value]], fmt='none',
                        ecolor='#526B80', elinewidth=.65, capsize=1.6, capthick=.65, zorder=3, clip_on=False)
        ax.set(ylim=(0, upper), yticks=ticks, xticks=range(5))
        ax.set_title(title, fontsize=6.1, pad=4)
        ax.set_xticklabels(order, rotation=60, ha='right', fontsize=5.6)
        ax.tick_params(axis='y', labelsize=5.6, pad=2)
        ax.set_axisbelow(True)
        ax.grid(axis='y')
    fig.text(.67, .065, r'(b), (c) 모델 배열: $\rho$ 내림차순', ha='center', fontsize=6, color='#354B60')
    fig.add_artist(FancyArrowPatch((.365, .035), (.98, .035), transform=fig.transFigure,
                                  arrowstyle='-|>', mutation_scale=9, color='#526B80'))
    ps.save(fig, str(OUT / 'fig5_appendix0_model_behavior_20261030'))
    plt.close(fig)


if __name__ == '__main__':
    margin_plot(read('appendix0_ask_turns_20261030'), read('appendix0_process_20261030'))
    model_plot(read('appendix0_low_margin_20261030'), read('appendix0_give_ask_20261030'),
               read('appendix0_integrated_20261030'))
    mapping = {
        'Figure 3': 'Unchanged compact coexistence overview and comparisons.',
        'Figure 4': 'Old Figure 4(a), with ASK added and tick-start eligibility for ASK/GIVE.',
        'Figure 5(a)': 'Old Figure 4(b,c) combined: ASK, receipt, EXIT; shutdown bars removed by request.',
        'Figure 5(b)': 'Old Figure 4(d), GIVE/ASK before/after totals unchanged.',
        'Figure 5(c)': 'Old Figure 4(e), terminal mean and min-max unchanged.',
        'Figure 6': 'Old Figure 5, crisis follow-up unchanged.',
        'Figure 7': 'Old Figure 6, detailed GIVE/ASK counts and amounts unchanged.'}
    assets = ['fig4_appendix0_margin_20261030.pdf', 'fig5_appendix0_model_behavior_20261030.pdf']
    (ROOT / 'results/appendix0_behavior_split_manifest_20261030.json').write_text(json.dumps(dict(
        mapping=mapping, asset_sha256={name: hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in assets}),
        ensure_ascii=False, indent=2)+'\n')
