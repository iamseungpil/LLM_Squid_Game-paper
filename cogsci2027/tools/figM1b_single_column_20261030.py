"""Extract Figure M.1(b), the existing e52_v33 coded EXIT-reason panel.

Preserve the source PDF's cells, labels, colors and model order as vectors.
The standalone caption replaces the original panel heading and footnote.
"""
from pathlib import Path
from collections import Counter
import re

import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ko/figures/happy_2a3afa6/rw_fig5_reasons.pdf'
OUTPUT = ROOT / 'ko/figures/fig_appendix0_exit_reasons_single_20261030'


def main():
    source = fitz.open(SOURCE)
    clip = fitz.Rect(234.7, 11.35, 452, 137)
    width = 3.35 * 72
    padding = 2
    scale = (width - 2 * padding) / clip.width
    doc = fitz.open()
    page = doc.new_page(width=width, height=clip.height * scale + 2 * padding)
    target = fitz.Rect(padding, padding, width - padding, page.rect.height - padding)
    page.show_pdf_page(target, source, 0, clip=clip)
    expected = Counter(re.findall(r'\b\d+/\d+\b', source[0].get_text(clip=clip)))
    actual = Counter(re.findall(r'\b\d+/\d+\b', page.get_text()))
    assert sum(expected.values()) == 30 and actual == expected
    doc.save(OUTPUT.with_suffix('.pdf'), garbage=4, deflate=True)
    page.get_pixmap(matrix=fitz.Matrix(3, 3)).save(OUTPUT.with_suffix('.png'))
    doc.close()
    source.close()


if __name__ == '__main__':
    main()
