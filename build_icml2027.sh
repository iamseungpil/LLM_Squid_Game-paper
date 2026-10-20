#!/usr/bin/env bash
# Build the ICML 2027 version of the paper in both languages.
# Output: build/icml2027/<lang>_icml2027.pdf and dist/<lang>_icml2027_<DATE>.pdf.
# Needs XeLaTeX, BibTeX and latexmk (TeX Live); the Korean build uses kotex.
# Style files (icml2027.sty stand-in, icml2027.bst, ICML's fancyhdr) live in
# icml2027/style and are searched before the paper root.
set -euo pipefail
cd "$(dirname "$0")"
DATE="${ICML_DATE:-$(date +%F)}"
export TEXINPUTS="$PWD/icml2027/style//:${TEXINPUTS:-}"
export BSTINPUTS="$PWD/icml2027/style//:${BSTINPUTS:-}"
mkdir -p build/icml2027 dist
for lang in ${@:-en ko}; do
  latexmk -xelatex -interaction=nonstopmode -halt-on-error \
    -outdir=build/icml2027 "${lang}_icml2027.tex"
  cp "build/icml2027/${lang}_icml2027.pdf" "dist/${lang}_icml2027_${DATE}.pdf"
  echo "built dist/${lang}_icml2027_${DATE}.pdf"
done
