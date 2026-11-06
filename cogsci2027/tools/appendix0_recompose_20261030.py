"""Recompose all existing Appendix 0 panels as reusable vector blocks.

Source: the previously audited fixed 25-game e52_v33 JSONs and plot generators.
Capture their Matplotlib artists without writing over any original figure.
No metrics or uncertainty intervals are recomputed. Only the new completion
overview combines the existing 25-game aggregate and five model distributions.
"""
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys
from unittest.mock import patch

import fitz
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyArrowPatch
from matplotlib.transforms import Bbox
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools/rewrite_20261025/figs'))
import paper_style as ps
import fig3_completion_20261028 as f3
import appendix0_give_ask_20261030 as f5
import appendix0_low_margin_20261030 as f6

OUT = ROOT / 'ko/figures'
BLOCKS = OUT / 'appendix0_blocks_20261030'
BLOCKS.mkdir(exist_ok=True)


def capture(draw):
    figures = []
    with patch.object(ps, 'save', side_effect=lambda fig, _: figures.append(fig)), patch.object(plt, 'close'):
        draw()
    assert len(figures) == 1
    return figures[0]


def export(fig, name, axes=(), texts=(), legends=(), label=None, destination=None):
    for i, artist in enumerate(fig.axes):
        artist.set_visible(i in axes)
    for i, artist in enumerate(fig.texts):
        artist.set_visible(i in texts)
    for i, artist in enumerate(fig.legends):
        artist.set_visible(i in legends)
    for artist in fig.artists:
        artist.set_visible(False)
    heading = None
    if label:
        candidates = [fig.texts[i] for i in texts]
        candidates += [t for i in axes for t in [fig.axes[i].title, fig.axes[i]._left_title]]
        heading = next(t for t in candidates if re.match(r'^\([a-g]\)', t.get_text()))
        old = heading.get_text()
        heading.set_text(re.sub(r'^\([a-g]\)', f'({label})', old))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [fig.axes[i].get_tightbbox(renderer) for i in axes]
    boxes += [fig.texts[i].get_window_extent(renderer) for i in texts]
    boxes += [fig.legends[i].get_window_extent(renderer) for i in legends]
    box = Bbox.union(boxes).transformed(fig.dpi_scale_trans.inverted()).padded(.025)
    if name in ['old3_b', 'old3_c', 'old3_d']:
        # Equal panel widths keep the three comparison axes at the same scale.
        box = Bbox.from_bounds(box.x1-1.76, box.y0, 1.76, box.height)
    stem = BLOCKS / name
    fig.savefig(stem.with_suffix('.pdf'), bbox_inches=box)
    fig.savefig(stem.with_suffix('.png'), bbox_inches=box, dpi=220)
    text = ' '.join(fig.axes[i].get_title() for i in axes)
    if heading:
        heading.set_text(old)
    return dict(block=name, destination=destination, axes=list(axes), texts=list(texts),
                legends=list(legends), label=label, source_title=text,
                pdf=str(stem.with_suffix('.pdf').relative_to(ROOT)))


def combined_outcomes(completion, states, order):
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic']})
    fig = plt.figure(figsize=(2.5, 2.5))
    fig.text(.02, .96, '(a) 공존 결과', fontsize=7.2, weight='bold')
    left = fig.add_axes([.19, .565, .76, .285])
    right = fig.add_axes([.19, .125, .76, .245])
    colors = ['#2F6DB0', '#6C9FC7', '#A6C8E0', '#D5E0E8', '#6B6B6B']
    totals = [sum(completion['models'][m]['counts'][str(n)] for m in order) for n in range(4, -1, -1)]
    assert totals == [8, 4, 5, 2, 6]
    for y, model in enumerate(['전체'] + order):
        counts = totals if y == 0 else [completion['models'][model]['counts'][str(n)] for n in range(4, -1, -1)]
        assert sum(counts) == (25 if y == 0 else 5)
        start = 0
        for n, count, color in zip(range(4, -1, -1), counts, colors):
            width = 100*count/sum(counts)
            if count:
                left.barh(y, width, left=start, height=.70, color=color, edgecolor='white', linewidth=.6)
                left.text(start+width/2, y, f'{width:.0f}%' if y == 0 else str(count),
                          ha='center', va='center', fontsize=5.7,
                          color='white' if n in [4, 0] else '#222222')
            start += width
    left.set(yticks=range(6), yticklabels=['전체']+order, ylim=(5.6, -.6), xlim=(0, 100),
             xticks=[0, 50, 100], xlabel='완주 인원별 판 구성 (%)')
    left.axhline(.5, color='#AAAAAA', linewidth=.5)
    state_colors = ['#3F7FC1', '#C2570F', '#EE9F55', '#4D4D4D']
    for y, model in enumerate(order, start=1):
        start = 0
        assert sum(states[model]) == 20
        for j, count in enumerate(states[model]):
            if count:
                right.barh(y, count, left=start, height=.70, color=state_colors[j], edgecolor='white', linewidth=.6)
                right.text(start+count/2, y, str(count), ha='center', va='center', fontsize=5.7,
                           color='#222222' if j == 2 else 'white')
            start += count
    right.set(yticks=range(1, 6), yticklabels=order, ylim=(5.6, .4), xlim=(0, 20),
              xticks=[0, 5, 10, 15, 20], xlabel='개인의 끝 상태 (모델별 20명)')
    for ax in [left, right]:
        ax.spines['left'].set_visible(False)
        ax.tick_params(axis='y', length=0, labelsize=6.2)
        ax.tick_params(axis='x', labelsize=6.2)
        ax.xaxis.label.set_fontsize(6.2)
        ax.xaxis.labelpad = 2
        ax.tick_params(axis='x', pad=2)
    fig.legend([Patch(color=c) for c in colors], [f'{n}인' for n in range(4, -1, -1)],
               loc='upper left', bbox_to_anchor=(.16, .94), ncol=5, fontsize=5.7,
               handlelength=.8, columnspacing=.8)
    fig.legend([Patch(color=c) for c in state_colors],
               ['완주', r'$L\geq1$ EXIT', r'$L<1$ EXIT', '꺼짐'],
               loc='upper left', bbox_to_anchor=(.16, .475), ncol=2, fontsize=5.7,
               handlelength=.8, columnspacing=.7)
    ps.save(fig, str(BLOCKS / 'combined_outcomes'))
    plt.close(fig)


def compose(stem, size, placements):
    doc = fitz.open()
    page = doc.new_page(width=size[0], height=size[1])
    for name, rect in placements:
        source = fitz.open(BLOCKS / f'{name}.pdf')
        slot = fitz.Rect(rect)
        scale = min(slot.width/source[0].rect.width, slot.height/source[0].rect.height)
        width, height = source[0].rect.width*scale, source[0].rect.height*scale
        fitted = fitz.Rect(slot.x0+(slot.width-width)/2, slot.y0,
                           slot.x0+(slot.width+width)/2, slot.y0+height)
        page.show_pdf_page(fitted, source, 0, keep_proportion=True)
    doc.save(OUT / f'{stem}.pdf', garbage=4, deflate=True)
    page.get_pixmap(matrix=fitz.Matrix(3, 3)).save(OUT / f'{stem}.png')
    doc.close()


def main():
    cached = json.loads((ROOT / 'results/fig3_completion_20261028.json').read_text())
    first = capture(lambda: f3.plot_primary(cached['games'], cached['summary']))
    second = capture(lambda: runpy.run_path(str(ROOT / 'tools/fig4_appendix0_20261030.py')))
    fifth = capture(lambda: f5.plot(json.loads((ROOT / 'results/appendix0_give_ask_20261030.json').read_text())))
    sixth = capture(lambda: f6.plot(json.loads((ROOT / 'results/appendix0_low_margin_20261030.json').read_text())))
    # Narrow the comparison panels and fill their height without changing data or limits.
    for ax in first.axes[1:]:
        x, y, width, height = ax.get_position().bounds
        ax.set_position([x, y, width*.92, height*1.17])
        title = ax._left_title.get_text() or ax.get_title()
        title = title.replace('지원 후 생존 여유 비율: ', '지원 후 생존\n여유 비율: ') if title.startswith('(d)') else title.replace(': ', ':\n')
        ax.set_title(title, fontsize=7.2, pad=6)
    for indexes, anchor in [([10, 11], .285), ([7, 8, 9], .62)]:
        for i in indexes:
            x, y, width, height = second.axes[i].get_position().bounds
            second.axes[i].set_position([anchor+(x-anchor)*1.2, y, width*1.2, height])
    # Tighten vertical spacing within the low-margin panels.
    for ax in sixth.axes:
        x, y, width, height = ax.get_position().bounds
        ax.set_position([x, y, width, height*.72])
    # Data labels need to remain readable when these two blocks share the top row.
    for ax in sixth.axes:
        for text in ax.texts:
            text.set_fontsize(7)
    manifest = []
    for i, letter in enumerate('abcd'):
        manifest.append(export(first, f'old3_{letter}', [i], label=letter,
            destination='Figure 3(a) overall row' if i == 0 else f'Figure 3({letter})'))
    export(first, 'completion_legend', legends=[0])
    specs = [('a', [0], [0], [0], None, 'Figure 3(a) model completion rows'),
             ('b', [1, 2, 3], [1], [], 'a', 'Figure 4(a)'),
             ('c', [4], [2, 3], [1], 'a', 'Figure 5(a)'),
             ('d', [5], [4, 5], [], 'b', 'Figure 5(b)'),
             ('e', [6], [6], [2], None, 'Figure 3(a) individual end states'),
             ('f', [10, 11], [8], [3], 'd', 'Figure 4(d)'),
             ('g', [7, 8, 9], [7], [], 'e', 'Figure 4(e)')]
    for name, axes, texts, legends, label, destination in specs:
        manifest.append(export(second, f'old4_{name}', axes, texts, legends, label, destination))
    for i, letter in enumerate('abcd'):
        manifest.append(export(fifth, f'old5_{letter}', [i], destination=f'Figure 6({letter})'))
    for i, letter in enumerate('ab'):
        manifest.append(export(sixth, f'old6_{letter}', [i], label='bc'[i], destination=f'Figure 4({"bc"[i]})'))
    integrated = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())['models']
    order = sorted(integrated, key=lambda m: integrated[m]['rho']['value'], reverse=True)
    completion = json.loads((ROOT / 'results/appendix0_completion_counts_20261030.json').read_text())
    states = json.loads((ROOT / 'results/section32_behavior_20261029.json').read_text())['end_states']
    combined_outcomes(completion, states, order)
    # The shared ordering cue is retained for the two model-level bottom blocks.
    cue = plt.figure(figsize=(7.4, .32))
    cue.text(.5, .62, r'(d), (e) 각 그래프 공통: $\rho$ 내림차순 (Sol, Fable, Luna, Astra, Opus)',
             ha='center', fontsize=7, color='#354B60')
    cue.add_artist(FancyArrowPatch((.025, .22), (.98, .22), transform=cue.transFigure,
                                  arrowstyle='-|>', mutation_scale=10, color='#526B80'))
    ps.save(cue, str(BLOCKS / 'rho_order'))
    plt.close(cue)
    compose('fig3_appendix0_completion_20261030', (533, 180), [
        ('combined_outcomes', (0, 0, 176, 180)),
        ('old3_b', (179, 0, 294, 164)), ('old3_c', (298, 0, 413, 164)),
        ('old3_d', (417, 0, 532, 164)), ('completion_legend', (180, 165, 533, 180))])
    compose('fig4_appendix0_process_20261030', (533, 294), [
        ('old4_b', (0, 0, 136, 150)), ('old6_a', (142, 0, 377, 150)),
        ('old6_b', (382, 0, 533, 150)),
        ('old4_f', (0, 157, 233, 270)), ('old4_g', (238, 157, 533, 270)),
        ('rho_order', (0, 271, 533, 294))])
    compose('fig_appendix0_crisis_followup_20261030', (533, 155), [
        ('old4_c', (0, 0, 261, 155)), ('old4_d', (277, 0, 533, 155))])
    assert len(manifest) == 17 and all(row['destination'] for row in manifest)
    for row in manifest:
        row['sha256'] = hashlib.sha256((ROOT / row['pdf']).read_bytes()).hexdigest()
    (BLOCKS / 'manifest.json').write_text(json.dumps(dict(
        definition=__doc__, original_panel_count=17, panels=manifest,
        merged_overview=dict(counts=completion['models'], total_percent=[32, 16, 20, 8, 24]),
        model_order=order), ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
