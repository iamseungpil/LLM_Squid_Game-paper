#!/usr/bin/env bash
# Build the CogSci 2027 version of the paper in both languages.
# Output: build/cogsci2027/<lang>_cogsci2027.pdf and dist/<lang>_cogsci2027_<DATE>.pdf.
# Needs TeX Live with latexmk and biber (biblatex, style=apa). English builds with
# pdfLaTeX like the official template; Korean builds with XeLaTeX (kotex).
# Only cogsci2027/style is put on the search path; cogsci2027/official keeps the
# untouched upstream kit, including a second copy of cogsci.sty.
set -euo pipefail
cd "$(dirname "$0")"
DATE="${COGSCI_DATE:-$(date +%F)}"
export TEXINPUTS="$PWD/cogsci2027/style/:${TEXINPUTS:-}"
mkdir -p build/cogsci2027 dist
for lang in ${@:-en ko}; do
  if [ "$lang" = ko ]; then engine=-xelatex; else engine=-pdf; fi
  latexmk "$engine" -interaction=nonstopmode -halt-on-error \
    -outdir=build/cogsci2027 "${lang}_cogsci2027.tex"
  cp "build/cogsci2027/${lang}_cogsci2027.pdf" "dist/${lang}_cogsci2027_${DATE}.pdf"
  echo "built dist/${lang}_cogsci2027_${DATE}.pdf"
done
