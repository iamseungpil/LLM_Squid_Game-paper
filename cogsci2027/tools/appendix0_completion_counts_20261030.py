"""Counts of games with 4/3/2/1/0 finishers in frozen e52_v33, seeds4101--4105.

Source: raw_case_index.json. Finishers have terminal status=in; EXIT is not
completion. Zero finishers does not imply four shutdowns. Each model has five
games. Plot these counts separately from Figure4(e)'s20individualendstates.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/rewrite_20261025/figs'))
import paper_style as ps


def main():
    source = ROOT / 'results/raw_case_index.json'
    process = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == process['source_sha256']
    cases = json.loads(source.read_text())
    integrated = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())['models']
    order = sorted(integrated, key=lambda m: integrated[m]['rho']['value'], reverse=True)
    models = {}
    for model in order:
        games = []
        for case in sorted((c for c in cases if c['model'] == model), key=lambda c: c['seed']):
            count = sum(a['status'] == 'in' for a in case['result']['agents'].values())
            reference = next(g for g in integrated[model]['games'] if g['seed'] == case['seed'])
            assert count == reference['finishers']
            games.append(dict(seed=case['seed'], finishers=count))
        assert [g['seed'] for g in games] == list(range(4101, 4106))
        counts = Counter(g['finishers'] for g in games)
        models[model] = dict(rho=integrated[model]['rho']['value'], counts={n: counts[n] for n in range(4, -1, -1)}, games=games)
        assert sum(counts.values()) == 5
    result = dict(definition=__doc__, source=str(source.relative_to(ROOT)), source_sha256=process['source_sha256'], order=order, models=models)
    (ROOT / 'results/appendix0_completion_counts_20261030.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'font.size': 8})
    fig, ax = plt.subplots(figsize=(5.8, 2.3))
    fig.subplots_adjust(left=.14, right=.98, top=.80, bottom=.20)
    colors = ['#2F6DB0', '#6C9FC7', '#A6C8E0', '#D5E0E8', '#6B6B6B']
    for y, model in enumerate(order):
        left = 0
        for n, color in zip(range(4, -1, -1), colors):
            width = models[model]['counts'][n]
            if width:
                ax.barh(y, width, left=left, height=.68, color=color, edgecolor='white', linewidth=.8)
                ax.text(left+width/2, y, str(width), va='center', ha='center', fontsize=9,
                        color='white' if n in [4, 0] else '#222222')
            left += width
    ax.set(yticks=range(5), yticklabels=order, ylim=(4.6, -.6), xlim=(0, 5), xticks=range(6), xlabel='판수 (모델별 5판)')
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.set_axisbelow(True)
    ax.grid(axis='x')
    fig.legend([Patch(color=c) for c in colors], [f'{n}인 완주' for n in range(4, -1, -1)],
               ncol=5, loc='upper center', bbox_to_anchor=(.54, .99), fontsize=7,
               handlelength=1, columnspacing=1.2)
    ps.save(fig, str(ROOT / 'ko/figures/fig_appendix0_completion_counts_20261030'))
    plt.close(fig)
    print(json.dumps({m:v['counts'] for m,v in models.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
