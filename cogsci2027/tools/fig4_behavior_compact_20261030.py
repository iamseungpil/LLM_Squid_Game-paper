"""Compact main-text Figure 4 from audited e52_v33 Appendix 0 panels.

Capture existing artists, change geometry only, and compose vector blocks.
Left: four margin rows. Middle: low-margin requests, receipts and EXIT.
Right: transfer/request totals above terminal resource distribution.
Height is exactly 110% of the prior 7.4 by 2.65 inch model figure.
"""
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

import appendix0_behavior_split_20261030 as plots
import appendix0_recompose_20261030 as blocks

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ko/figures'
BLOCKS = OUT / 'fig4_compact_blocks_20261030'
BLOCKS.mkdir(exist_ok=True)


def main():
    margin = blocks.capture(lambda: plots.margin_plot(plots.read('appendix0_ask_turns_20261030'),
                                                     plots.read('appendix0_process_20261030')))
    model = blocks.capture(lambda: plots.model_plot(plots.read('appendix0_low_margin_20261030'),
                              plots.read('appendix0_give_ask_20261030'), plots.read('appendix0_integrated_20261030')))
    blocks.BLOCKS = BLOCKS
    margin.set_size_inches(1.65, 2.915)
    margin.text(.015, .965, '(a) 생존 여유별 행동', fontsize=7, weight='bold')
    for ax in margin.axes:
        _, y, _, height = ax.get_position().bounds
        ax.set_position([.17, y*.90+.01, .81, height*.90])
        ax._left_title.set_fontsize(6.2)
        ax.xaxis.label.set_fontsize(6)
        ax.tick_params(labelsize=5.7, pad=2)
        for text in ax.texts:
            text.set_fontsize(5.4)
    manifest = [blocks.export(margin, 'a_margin', range(4), [0], destination='Figure 4(a)')]

    ax = model.axes[0]
    x, _, width, _ = ax.get_position().bounds
    ax.set_position([x, .13, width, .70])
    for text in ax.texts:
        text.set_fontsize(6.2)
    model.texts[0].set_text('(b) 낮은 여유의 요청·수혜·이탈')
    manifest.append(blocks.export(model, 'b_low_margin', [0], [0], destination='Figure 4(b)'))

    model.texts[1].set_text('(c) GIVE·ASK 총량')
    model.texts[1].set_position((.365, .94))
    model.legends[0].set_bbox_to_anchor((.356, .915), transform=model.transFigure)
    for j, ax in enumerate(model.axes[1:3]):
        ax.set_position([.375+j*.215, .63, .15, .16])
    manifest.append(blocks.export(model, 'c_totals', [1, 2], [1], [0], destination='Figure 4(c)'))

    model.texts[2].set_text('(d) 종료 시 아레나 자원 분배')
    model.texts[2].set_position((.39, .90))
    for j, ax in enumerate(model.axes[3:6]):
        ax.set_position([.40+j*.15, .60, .12, .17])
    manifest.append(blocks.export(model, 'd_resources', [3, 4, 5], [2], destination='Figure 4(d)'))
    plt.close(margin)
    plt.close(model)

    cue = plt.figure(figsize=(3.0, .20))
    cue.text(.5, .48, r'(c), (d) 모델 배열: $\rho$ 내림차순', ha='center', fontsize=5.8, color='#354B60')
    cue.add_artist(FancyArrowPatch((.01, .15), (.99, .15), transform=cue.transFigure,
                                  arrowstyle='-|>', mutation_scale=7, linewidth=.7, color='#526B80'))
    plots.ps.save(cue, str(BLOCKS / 'rho_order'))
    plt.close(cue)
    size = (7.4*72, 2.65*72*1.10)
    blocks.compose('fig4_behavior_compact_20261030', size, [
        ('a_margin', (0, 0, 117, 209.88)),
        ('b_low_margin', (121, 0, 306, 209.88)),
        ('c_totals', (312, 0, 532.8, 96)),
        ('d_resources', (312, 98, 532.8, 194)),
        ('rho_order', (312, 195, 532.8, 209.88))])
    for item in manifest:
        item['sha256'] = hashlib.sha256((ROOT / item['pdf']).read_bytes()).hexdigest()
    (BLOCKS / 'manifest.json').write_text(json.dumps(dict(
        source='Audited fixed e52_v33 summaries; no recomputation of metrics.',
        previous_height_pt=190.8, height_pt=size[1], height_ratio=1.10,
        arrangement='Margin | low-margin behavior | totals above resources', panels=manifest),
        ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
