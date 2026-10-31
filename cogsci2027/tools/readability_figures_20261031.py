"""Refresh main-text labels using the audited, cached e52_v33 figures.

Only wording changes; original appendix figures and numerical data are retained.
"""
from pathlib import Path
from unittest.mock import patch

import fitz
from matplotlib.figure import Figure
from matplotlib.text import Text

import fig3_appendix0_layout_20261030 as completion
import fig4_behavior_compact_20261030 as behavior

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ko/figures/readability_20261031'
OUT.mkdir(exist_ok=True)
REPLACEMENTS = {
    '그 외': '미완주',
    '4인 완주': '전원 완주',
    '(c) 협력: 이전량': '(c) 협력: 지원량',
    'GIVE / 참여\n에이전트·라운드 (토큰)': '참여 인원당\n지원량 (토큰)',
    '준 쪽 / 받은 쪽': '지원자 / 수혜자',
    '집단 평균·95% 구간': '판 평균·95% 구간',
    '꺼짐': '실행 종료',
    'EXIT (결정 창 %)': '이탈 (기회 %)',
    'EXIT': '이탈',
    'Gini': '지니',
}


def labels(fig):
    for ax in fig.axes:
        for axis in [ax.xaxis, ax.yaxis]:
            old_labels = [text.get_text() for text in axis.get_ticklabels()]
            new_labels = old_labels.copy()
            for old, new in REPLACEMENTS.items():
                new_labels = [value.replace(old, new) for value in new_labels]
            if new_labels != old_labels:
                axis.set_ticklabels(new_labels, fontfamily='Apple SD Gothic Neo')
    for text in fig.findobj(Text):
        text.set_fontfamily('Apple SD Gothic Neo')
        value = text.get_text()
        for old, new in REPLACEMENTS.items():
            value = value.replace(old, new)
        text.set_text(value)


def main():
    completion.OUT = OUT
    completion.WORK = OUT / 'completion_blocks'
    completion.WORK.mkdir(exist_ok=True)
    behavior.APPENDIX = True
    behavior.BLOCKS = OUT / 'behavior_blocks'
    behavior.BLOCKS.mkdir(exist_ok=True)
    behavior.blocks.OUT = OUT

    original_save = Figure.savefig
    original_export = behavior.blocks.export

    def save(fig, *args, **kwargs):
        labels(fig)
        return original_save(fig, *args, **kwargs)

    def export(fig, *args, **kwargs):
        labels(fig)
        return original_export(fig, *args, **kwargs)

    with patch.object(Figure, 'savefig', save), patch.object(behavior.blocks, 'export', export):
        completion.main()
        behavior.main()

    # This existing panel is a cropped vector PDF; replace its one legacy label.
    source = ROOT / 'ko/figures/happy_2a3afa6/rw_fig5_reasons.pdf'
    original = fitz.open(source)
    full = original[0]
    clip = fitz.Rect(234.7, 11.35, 452, 137)
    # Remove off-panel text before cropping so PDF readers cannot extract it.
    for outside in [fitz.Rect(0, 0, full.rect.width, clip.y0),
                    fitz.Rect(0, clip.y1, full.rect.width, full.rect.height),
                    fitz.Rect(0, clip.y0, clip.x0, clip.y1),
                    fitz.Rect(clip.x1, clip.y0, full.rect.width, clip.y1)]:
        full.add_redact_annot(outside, fill=None)
    full.apply_redactions(images=0, graphics=0)
    doc = fitz.open()
    width, padding = 3.35 * 72, 2
    scale = (width - 2 * padding) / clip.width
    page = doc.new_page(width=width, height=clip.height * scale + 2 * padding)
    page.show_pdf_page(fitz.Rect(padding, padding, width-padding, page.rect.height-padding),
                       original, 0, clip=clip)
    hits = page.search_for('꺼짐')
    assert len(hits) == 1
    rect = hits[0]
    heading = page.search_for('벌금·')
    assert len(heading) == 1
    page.add_redact_annot(heading[0], fill=(1, 1, 1))
    page.add_redact_annot(rect, fill=(1, 1, 1))
    page.apply_redactions(images=0, graphics=0)
    for word, baseline in [('벌금·', 6.1), ('실행', 12.1), ('종료', 18.1)]:
        width = fitz.get_text_length(word, fontname='korea', fontsize=5.9)
        page.insert_text(((rect.x0 + rect.x1 - width) / 2, baseline),
                         word, fontname='korea', fontsize=5.9)
    stem = OUT / 'fig_appendix0_exit_reasons_single_20261030'
    doc.save(stem.with_suffix('.pdf'), garbage=4, deflate=True)
    page.get_pixmap(matrix=fitz.Matrix(3, 3)).save(stem.with_suffix('.png'))
    doc.close()
    original.close()


if __name__ == '__main__':
    main()
