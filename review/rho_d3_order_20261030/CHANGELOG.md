# D.3 rho and Figure4(f) order — 2026-10-30

User confirmed current pending-fine-adjusted giver/receiver ratio and requested D.3 update plus descending rho order in appendix0 Figure4(f).

- D.3 table (current Table D.2) now uses current pooled rho and newly calculated whole-game bootstrap95% intervals,2000 draws, seed1919. Undefined draws omitted, not zero-imputed. Other columns unchanged. Old formula reference replaced by current main equation; update explicitly marked.
- Table generation routed through table_d3_rho_20261030.py to prevent legacy generator restoring oldrho or omittedSen column.
- Figure4(f) only reordered Sol,Fable,Luna,Astra,Opus. Per-game values and marks unchanged; Gini sample counts reordered4/5/3/4/3. draw_panels default remains unchanged for otherfigures.
- Narrow Korean caption edits by ditto-writer juhyeon-ko-academic (gpt-6-astra high); no new causal claim or broad rewrite. Original snapshots retained locally.

Validation: independent raw bootstrap and plotting/source review PASS. Real Korean build62full/7body; only fullPDFpages8and27 changed. BodyPDFtext andpixels exactly unchanged. Final pages visually inspected: no clipping or overlap; no overfull/undefinedreference/duplicateanchor errors. Only two canonical dated delivery PDFs overwritten.

Interpretation: large rho means greater giver-relative margin after executed transfers, not proven latentdrive strength or causeofdeath. Sol dead1/20 versus Opus5/20 also does not support a monotonic model-leveldeath claim. Historicalappendixrecords elsewhere remain labeled legacy, not blanket-invalidated.
