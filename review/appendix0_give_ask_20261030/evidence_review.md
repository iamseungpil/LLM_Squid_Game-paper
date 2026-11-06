# Appendix 0 GIVE/ASK figure evidence review

Status: PASS. No factual or visual blocker identified. Final manuscript PDF build remains outside this read-only review.

Reviewed `cogsci2027/tools/appendix0_give_ask_20261030.py`, its results JSON, generated PNG, and `figure_snippet.tex`. Only this review note was written.

## Independent data validation

Re-read the original source jsonl/xz lines for all gift/ask events recorded in the 25-case raw index. All **221** lines matched exactly. Counted only status `done`; the sole excluded event is one refused GIVE. Independently reproduced every model/seed count and amount, including zero-valued games. All per-game JSON values and all historical `arena_v33.json` model-level counts/amounts match. The raw-index source hash also matches the output JSON.

| Model, descending current rho | GIVE events | GIVE tokens | ASK events | ASK requested tokens |
|---|---:|---:|---:|---:|
| Sol (4.24) | 17 | 48,700 | 20 | 63,500 |
| Fable (3.68) | 36 | 77,300 | 33 | 83,000 |
| Luna (3.17) | 25 | 60,818 | 16 | 54,000 |
| Astra (2.70) | 11 | 71,000 | 4 | 20,000 |
| Opus (1.83) | 41 | 125,458 | 17 | 50,300 |
| Total | 130 | 383,276 | 90 | 270,800 |

These are action events, not response counts. GIVE totals include retransfers; ASK totals include repeated requests. No normalization for opportunities, participants, or duration is applied.

## ASK semantics

Inspected `/Users/bagjuhyeon/wt/squid5-e52/squid5/e52_game.py`, `_move` at lines 283–303. ASK sets no refusal reason, logs an `ask` event with status `done`, and increments requested amount. Only GIVE invokes the wallet transfer. Thus `done` ASK means a registered request, not fulfillment; the caption's distinction is correct. This is a current engine-source semantic cross-check, alongside the exact frozen event validation above.

## Plot and caption

- All four panels use the correct descending rho order: Sol, Fable, Luna, Astra, Opus. Parenthesized rho values match the current pooled pending-fine-adjusted giver/recipient definition.
- Bars display each model's five-game **sum**, not a mean. Each model has five game points, including zeros; horizontal offsets preserve separate zero observations.
- Counts are in events; amounts and plotted amount labels are in thousands of tokens. Every bar height and annotation agrees with the table above. Axis limits contain all marks and annotations.
- The inspected PNG has no observed clipping or label overlap. Its footnote and the writer caption explicitly distinguish sum bars from single-game points, unlike the preceding resource-distribution figure's mean bars.
- The snippet states the correct total counts/amounts, request-registration semantics, repeated-event scope, and lack of normalization. No causal claim is added.

No corrections required. No style impression score assigned.
