# Appendix 0 response/model figure split: bounded evidence audit

Status: **PASS; no factual blocker found.** Review is limited to the requested G02/G07/G08 measurement, denominator, analysis/interpretation scope and accompanying display/prose checks. This is not a complete manuscript or style review. Only this report was written. Final LaTeX build and page-level layout verification remain with the orchestrator.

## New ASK/GIVE response analysis

Independently reconstructed **all 2,909 response rows** from the raw case index and matched every response identifier, call/start line, round-start participant count, tick-start live count, eligibility, pending-fine-adjusted margin, band, and ASK/GIVE event count. Verified the raw-index hash and all **14 original event/results file hashes**.

Eligibility is another participating agent at tick start, using the union of called agents and DONE-waiting agents. The resulting **2,887** responses comprise **1,423 prep + 1,464 rescue** responses. The 22 singleton responses contain no successful ASK or GIVE. Eleven exclusions are additional to the older round-start-participant rule; the earlier 2,898-response cache remains unchanged.

| Response-start margin | Eligible responses | ASK-containing responses | ASK events | GIVE-containing responses | GIVE events |
|---|---:|---:|---:|---:|---:|
| <1 | 260 | 52 | 67 | 9 | 9 |
| 1–2 | 610 | 19 | 23 | 5 | 5 |
| 2–4 | 759 | 0 | 0 | 36 | 40 |
| ≥4 | 1,258 | 0 | 0 | 70 | 76 |
| Total | 2,887 | 71 | 90 | 120 | 130 |

All phase-specific summaries also match independent recomputation. Figure 4 correctly plots response occurrence, not number of action events: ASK 20.00/3.11/0/0%; GIVE 3.46/0.82/4.74/5.56%. Actual correctness and EXIT retain their separately identified solve/window units and previous values. The source and prose explicitly distinguish current tick-start eligibility from the old rule.

## Existing 28-observation model comparison

`appendix0_low_margin_20261030.json` is byte-identical to HEAD, preserving the independently audited 28 agent-rounds, first-prep L<1 non-solver selection, and same-round follow-up through both prep and rescue. Its denominators and three displayed outcomes are unchanged:

| Model | N | ASK | Receipt | EXIT |
|---|---:|---:|---:|---:|
| Sol | 9 | 3 | 1 | 6 |
| Fable | 5 | 4 | 3 | 1 |
| Luna | 5 | 1 | 1 | 3 |
| Astra | 3 | 0 | 0 | 3 |
| Opus | 6 | 2 | 2 | 2 |

New Figure 5(a) uses ASK green, actual support receipt blue, and EXIT orange. Its percentages and k/N annotations match the table. The shutdown bars are removed as requested; underlying shutdown records are retained unchanged. Grouped bars preserve possible overlap instead of implying an exhaustive partition. The previously separate receipt panel is absorbed without losing its values.

## Totals, terminal metrics and uncertainty

The integrated and GIVE/ASK-total JSONs are byte-identical to HEAD. New Figure 5(b) preserves every model's gross totals and before/after phase stacks, including repeated requests/retransfers. ASK remains requested tokens, not received support. Five-game sums are clearly separated from Figure 5(c)'s per-game means.

Figure 5(c) uses the same S/G/mu game values and means, with actual observed minimum–maximum whiskers and Gini `None` values omitted. Gini valid-game counts remain 4/5/3/4/3 in descending-rho order; S and mu use all five games. The display limits are tightened relative to the former layout (S to 2 ten-thousand tokens, G to 1.04, mu to 3.2 ten-thousand tokens) but still contain all data and whiskers. Numerical values and interval meaning are unchanged; the axes should not be described as identical to the old layout.

## Caption/prose and figure mapping

Actual `00_appendix0_section32.tex` has five unique figure labels in sequence 3–7, and all local references resolve. Figure 3 remains the compact coexistence overview; new Figure 4 contains margin bands including ASK; new Figure 5 contains model behavior/totals/resources; crisis follow-up and detailed action counts/amounts become Figures 6 and 7.

The three shorter captions retain their essential definitions in adjacent prose: response/solve/window units; 2,887 eligibility and comparison with the former 2,898 rule; pending fines; positive executed actions counted once per response; ASK versus receipt; first-prep baseline versus both-phase follow-up; repeated agent-round observations and small denominators; gross totals versus means; and minimum–maximum ranges versus confidence intervals/standard errors. Figure 3's original 95% interval explanation and seed-bootstrap method remain present.

Scope limitations are explicit: the response-band analysis pools nested repeated observations and is not a causal effect of margin or intrinsic reasoning/motivation; Figure 5(a) is limited to its common-opportunity baseline and includes later events after possible margin recovery. Receipt is not request fulfillment or inferred willingness to help. The L=1 reference is not claimed to guarantee subsequent survival. No missing definition requiring correction was found.

Inspected both new PNGs: counts, percentages, requested colors, legends, phases, labels, model order, and whisker endpoints agree with the source. No observed clipping or label collision. This is a source/asset review, not verification of the final compiled page.

## Edit boundary

`03_analysis.tex` and `05_appendix.tex` are byte-identical to HEAD. Main prose and M.1 therefore remain unchanged in this task. No new source edits were made by this reviewer, and no style impression score was assigned.
