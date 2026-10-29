#!/usr/bin/env bash
# Build the paper from the one entry point main.tex.
#   bash build.sh                 # CogSci 2027, Korean only (default)
#   bash build.sh cogsci ko       # language: 1/ko, 2/en, 3/both
#   bash build.sh cogsci both     # Korean and English
#   bash build.sh natmi en
# The venue and language are passed to main.tex as \paperVenue / \paperLang (latexmk -usepretex).
# Korean builds with XeLaTeX (kotex), English with pdfLaTeX, as the official templates do.
# CogSci uses biblatex + biber; NatMI uses BibTeX with sn-nature.bst. latexmkrc puts the venue
# style folders on TEXINPUTS / BSTINPUTS (so Overleaf finds them as well).
# Output: dist/<lang>_<venue folder>_<DATE>.pdf and the matching _no_appendix.pdf.
# (venue folder: cogsci2027 | natmi). DATE defaults to today; set PAPER_DATE to override.
# PDF export requires Python 3 with PyMuPDF (python3 -m pip install pymupdf).
set -euo pipefail
cd "$(dirname "$0")"
venue="${1:-cogsci}"; shift || true
case "$venue" in
  cogsci) dir=cogsci2027; bib=() ;;
  natmi)  dir=natmi;      bib=(-bibtex) ;;
  *) echo "usage: bash build.sh [cogsci|natmi] [1|ko|2|en|3|both]" >&2; exit 2 ;;
esac
# Default to Korean; validate all selections before starting a build.
langs=()
for selection in "${@:-ko}"; do
  case "$selection" in
    1|ko) langs+=(ko) ;;
    2|en) langs+=(en) ;;
    3|both) langs+=(ko en) ;;
    *) echo "language must be 1/ko, 2/en, or 3/both" >&2; exit 2 ;;
  esac
done
DATE="${PAPER_DATE:-$(date +%F)}"
mkdir -p "build/$dir" dist
for lang in "${langs[@]}"; do
  case "$lang" in ko) engine=-xelatex ;; en) engine=-pdf ;; *) echo "language must be ko or en" >&2; exit 2 ;; esac
  job="${lang}_${dir}"
  latexmk "$engine" ${bib[@]+"${bib[@]}"} -interaction=nonstopmode -halt-on-error -outdir="build/$dir" \
    -jobname="$job" -usepretex="\\def\\paperVenue{$venue}\\def\\paperLang{$lang}" main.tex
  cp "build/$dir/$job.pdf" "dist/${job}_${DATE}.pdf"
  echo "built dist/${job}_${DATE}.pdf"
  python3 tools/export_no_appendix.py "build/$dir/$job.pdf" "build/$dir/$job.aux" \
    "dist/${job}_${DATE}_no_appendix.pdf"
  echo "built dist/${job}_${DATE}_no_appendix.pdf"
done
