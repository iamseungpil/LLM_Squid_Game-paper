"""Export pages before the appendix, preserving the full PDF's typesetting."""

import re
import shutil
import sys
from pathlib import Path

import fitz


source, aux, target = map(Path, sys.argv[1:])
marker = re.search(
    r"\\newlabel\{paper:appendix-start\}\{\{[^}]*\}\{(\d+)\}",
    aux.read_text(),
)
if marker is None:
    # Manuscripts without an appendix still produce both requested filenames.
    shutil.copyfile(source, target)
else:
    with fitz.open(source) as document:
        first_appendix_page = int(marker.group(1)) - 1
        if not 0 < first_appendix_page < len(document):
            raise ValueError("Appendix boundary is outside the PDF page range")
        document.delete_pages(first_appendix_page, len(document) - 1)
        document.save(target, garbage=4, deflate=True)
