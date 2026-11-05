"""Render Figure 6 with shorter, wider cells from frozen 2026-11-04 counts.

Data: public v33, seeds 4101--4110, 64 EXIT responses, independent Fable/Opus coding.
The figure keeps all cell values, colours, labels, and font sizes. No recoding.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from update_exit_reasons_20261104 import CATEGORIES, ORDER

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = json.loads((ROOT / 'results/exit_reasons_20261104.json').read_text())
    summaries = report['models']
    plt.rcParams.update({'font.family': 'Apple SD Gothic Neo', 'font.size': 7.2,
                         'pdf.fonttype': 3, 'axes.unicode_minus': False})
    width, old_height, height = 241.2, 141.15682983398438, 119.0
    fig, ax = plt.subplots(figsize=(width / 72, height / 72))
    values = np.array([[summaries[m]['counts'][c] for c in CATEGORIES] + [summaries[m]['no_reason']]
                       for m in ORDER])
    den = np.array([summaries[m]['n'] for m in ORDER])
    ax.imshow(values / den[:, None], cmap='Oranges', vmin=0, vmax=1, aspect='auto')
    for i, n in enumerate(den):
        if n < 10:
            ax.add_patch(plt.Rectangle((-.5, i-.5), 6, 1, color='white', alpha=.55, lw=0))
        for j, value in enumerate(values[i]):
            ax.text(j, i, f'{value}/{n}', ha='center', va='center', fontsize=6.3,
                    color='white' if value/n > .65 and n >= 10 else '#222222')
    ax.set_xticks(range(6), ['상금\n몫', '벌금·\n실행\n종료', '보너스·\n정규 업무', '동료', '과제', '이유\n없음'])
    ax.xaxis.tick_top()
    ax.set_yticks(range(5), ORDER)
    ax.tick_params(length=0, pad=4)
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1)
    ax.tick_params(which='minor', length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Preserve header/footer space in points while reducing only the cell height.
    fig.subplots_adjust(left=.24, right=.99, bottom=.025 * old_height / height,
                        top=1 - .24 * old_height / height)
    out = ROOT / 'ko/figures/cohorts_20261105/exit_reasons_compact'
    fig.savefig(out.with_suffix('.pdf'))
    fig.savefig(out.with_suffix('.png'), dpi=240)
    plt.close(fig)
    print(f'Width {width:.1f} pt; height {old_height:.2f} -> {height:.1f} pt; {100*(1-height/old_height):.1f}% shorter')


if __name__ == '__main__':
    main()
