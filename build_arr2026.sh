#!/usr/bin/env bash
# Build the ARR 2026 (ACL review style) version of the paper in both languages.
# Output: build/arr2026/<lang>_arr2026.pdf and dist/<lang>_arr2026_<DATE>.pdf.
# Needs XeLaTeX, BibTeX and latexmk (TeX Live); the Korean build uses kotex.
set -euo pipefail
cd "$(dirname "$0")"
DATE="${ARR_DATE:-2026-10-01}"
mkdir -p build/arr2026 dist
for lang in "${@:-en ko}"; do
  latexmk -xelatex -interaction=nonstopmode -halt-on-error \
    -outdir=build/arr2026 "${lang}_arr2026.tex"
  cp "build/arr2026/${lang}_arr2026.pdf" "dist/${lang}_arr2026_${DATE}.pdf"
  echo "built dist/${lang}_arr2026_${DATE}.pdf"
done
