#!/usr/bin/env bash
# Build the Nature Machine Intelligence version of the paper in both languages.
# Output: build/natmi/<lang>_natmi.pdf and dist/<lang>_natmi_<DATE>.pdf.
# Needs TeX Live with latexmk and BibTeX (sn-nature.bst through natbib, as in the
# official Springer Nature template). English builds with pdfLaTeX like the
# template; Korean builds with XeLaTeX (kotex).
# Only natmi/style is put on the search paths (TEXINPUTS for sn-jnl.cls,
# BSTINPUTS for sn-nature.bst); natmi/official keeps the untouched upstream kit.
set -euo pipefail
cd "$(dirname "$0")"
DATE="${NATMI_DATE:-$(date +%F)}"
export TEXINPUTS="$PWD/natmi/style/:${TEXINPUTS:-}"
export BSTINPUTS="$PWD/natmi/style/:${BSTINPUTS:-}"
mkdir -p build/natmi dist
for lang in ${@:-en ko}; do
  if [ "$lang" = ko ]; then engine=-xelatex; else engine=-pdf; fi
  latexmk "$engine" -bibtex -interaction=nonstopmode -halt-on-error \
    -outdir=build/natmi "${lang}_natmi.tex"
  cp "build/natmi/${lang}_natmi.pdf" "dist/${lang}_natmi_${DATE}.pdf"
  echo "built dist/${lang}_natmi_${DATE}.pdf"
done
