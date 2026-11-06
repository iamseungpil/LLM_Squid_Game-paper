"""Reflow Appendix 0 Figure 3 using the audited, cached e52_v33 results.

Keep the 533 pt canvas width and the widths of the comparison axes.
Only artist positions and typography change; no statistics are recomputed.
"""
import json

import fitz
import matplotlib.pyplot as plt
from matplotlib.text import Text

import appendix0_recompose_20261030 as blocks

ROOT = blocks.ROOT
OUT = blocks.OUT
WORK = OUT / 'fig3_appendix0_layout_blocks_20261030'
WORK.mkdir(exist_ok=True)
SIZE = (533, 182)


def read(name):
    return json.loads((ROOT / f'results/{name}.json').read_text())


def main():
    cached = read('fig3_completion_20261028')
    comparison = blocks.capture(lambda: blocks.f3.plot_primary(cached['games'], cached['summary']))
    comparison.set_size_inches(SIZE[0] / 72, SIZE[1] / 72)
    comparison.axes[0].set_visible(False)
    # The prior 126.72 pt blocks were placed in 115 pt slots.
    scale = 115 / 126.72
    width = 7.1 * 72 * .155 * .92 * scale
    height = 128
    titles = ['(b) 추론: 정답률', '(c) 협력: 이전량', r'(d) 자기 보존 $\rho$']
    for ax, x, title in zip(comparison.axes[1:], [265.21128, 370.21128, 464.21128], titles):
        ax.set_position([x / SIZE[0], (SIZE[1] - 14 - height) / SIZE[1],
                         width / SIZE[0], height / SIZE[1]])
        ax.set_title(title, fontsize=7.2, pad=6 * scale)
        for text in ax.findobj(Text):
            text.set_fontsize(text.get_fontsize() * scale * 1.2)
        for text in ax.texts:
            if text.get_text().startswith('$r$='):
                text.set_bbox(None)
                text.set_color('#44515C')
        ax.tick_params(pad=2 * scale)
        ax.yaxis.labelpad = 1
        for line in ax.lines:
            line.set_markersize(line.get_markersize() * scale)
            line.set_linewidth(line.get_linewidth() * scale)
        for collection in ax.collections:
            collection.set_sizes(collection.get_sizes() * scale**2)
    legend = comparison.legends[0]
    handles, labels = legend.legend_handles, [t.get_text() for t in legend.get_texts()]
    legend.remove()
    comparison.legend(handles, labels, loc='lower right', bbox_to_anchor=(.997, 1.5 / SIZE[1]),
                      ncol=6, fontsize=7.2, borderaxespad=0, handletextpad=.35,
                      handlelength=1.1, columnspacing=.9)

    integrated = read('appendix0_integrated_20261030')['models']
    order = sorted(integrated, key=lambda m: integrated[m]['rho']['value'], reverse=True)
    outcomes = blocks.capture(lambda: blocks.combined_outcomes(
        read('appendix0_completion_counts_20261030'),
        read('section32_behavior_20261029')['end_states'], order))
    outcomes.set_size_inches(SIZE[0] / 72, SIZE[1] / 72)
    # Grow both bar axes and place each legend in one column on its right.
    for ax, top, height in zip(outcomes.axes, [14, 99], [59 * 1.1, 51 * 1.1]):
        ax.set_position([33.44 / SIZE[0], (SIZE[1] - top - height) / SIZE[1],
                         133.76 * 1.15 / SIZE[0], height / SIZE[1]])
        ax.xaxis.labelpad = 2
        for text in ax.texts:
            text.set_fontsize(text.get_fontsize() * 1.1)
    for text in outcomes.findobj(Text):
        text.set_fontsize(text.get_fontsize() * (176 / 180) * 1.1)
    upper = outcomes.axes[0]
    upper.set_xticks([0, 100])
    upper.set_xlabel('')
    upper.annotate('완주 인원별 판 구성 (%)', xy=(.5, 0), xycoords='axes fraction',
                   xytext=(0, -4.5), textcoords='offset points', ha='center', va='top',
                   fontsize=upper.get_xticklabels()[0].get_fontsize())
    outcomes.texts[0].set_position((3.52 / SIZE[0], (SIZE[1] - 7.2) / SIZE[1]))
    for legend, top in zip(list(outcomes.legends), [14 + 59 * 1.1 / 2, 99 + 51 * 1.1 / 2]):
        handles, labels = legend.legend_handles, [t.get_text() for t in legend.get_texts()]
        legend.remove()
        outcomes.legend(handles, labels, loc='center left',
                        bbox_to_anchor=(193 / SIZE[0], (SIZE[1] - top) / SIZE[1]), ncol=1,
                        fontsize=5.7 * (176 / 180) * 1.1, handlelength=.8,
                        columnspacing=.65, handletextpad=.4, borderaxespad=0)

    doc = fitz.open()
    page = doc.new_page(width=SIZE[0], height=SIZE[1])
    for name, fig in [('comparison', comparison), ('outcomes', outcomes)]:
        path = WORK / f'{name}.pdf'
        fig.savefig(path, transparent=True)
        with fitz.open(path) as source:
            page.show_pdf_page(page.rect, source, 0)
        plt.close(fig)
    stem = OUT / 'fig3_appendix0_layout_20261030'
    doc.save(stem.with_suffix('.pdf'), garbage=4, deflate=True)
    page.get_pixmap(matrix=fitz.Matrix(3, 3)).save(stem.with_suffix('.png'))
    doc.close()


if __name__ == '__main__':
    main()
