# Appendix 0 Figure 4(a,f,g) layout evidence review

Status: PASS. No factual or visual blocker identified. Only this review note was written; final PDF build verification remains with the orchestrator.

Reviewed the updated Figure 4 plotting script and PNG, referenced data, original main Figure 4 timing implementation, and writer draft `appendix0.tex`.

## Support timing (a)

Independently recomputed successful GIVE timing and same-game return-direction amounts from chronological raw events. All values match both `appendix0_integrated_20261030.json` and the `arena_v33_round_dynamics.json` transfer data used by main Figure 4(c).

| Model | Before SOLVE tokens | After result tokens | Return tokens before / after |
|---|---:|---:|---:|
| Sol | 5,100 | 43,600 | 0 / 3,000 |
| Fable | 53,800 | 23,500 | 0 / 0 |
| Luna | 9,000 | 51,818 | 0 / 7,000 |
| Astra | 10,000 | 61,000 | 0 / 0 |
| Opus | 41,500 | 83,958 | 3,000 / 43,158 |

The original model colors, light-before/dark-after distinction, horizontal scale of 0–100 thousand tokens, and return hatching semantics are preserved. The bars are reordered by current pooled rho, not recomputed with a different aggregation. Writer text that Fable gives more before SOLVE while the other four models give more after results is supported.

## Other panels

- (b), (c), and (d) calculation and drawing code is unchanged from the task backup; the only change in that code block moves the integrated JSON load earlier. Their populations, units, and counts remain unchanged.
- (e), (f), and (g), as well as (a), use descending rho order **Sol, Fable, Luna, Astra, Opus**. End-state data remain unchanged.
- (f) still calls the original terminal `draw_panels` with the same data, scale factors, limits, individual-game points, and missing-value handling. It removes mean values from tick labels, reduces point sizes, rotates model labels, and compresses axes. Sen and mean tokens remain in ten-thousand tokens; Gini counts remain **4/5/3/4/3**. Sen and mean tokens include all five games.
- (g) reads the already verified Figure 5 gross GIVE/ASK volumes. GIVE amounts are 48,700/77,300/60,818/71,000/125,458 tokens; ASK amounts are 63,500/83,000/54,000/20,000/50,300 tokens in plot order. Return hatching is 3,000/0/7,000/0/46,158, overlaid within the GIVE bar without extra height. There are no game dots in (g).
- Figure footnotes and writer caption correctly distinguish **per-game means with individual-game points in (f)** from **five-game totals in (a) and (g)**. ASK denotes requested amounts, includes repeated requests, and is not described as received support. Return-direction transfers are not claimed to be verified debt repayment.

## Prose and visual checks

The writer caption describes the new (a) timing panel, new (g) volume panels, model order, units, aggregation, and return hatching correctly. The body no longer describes the removed scatter as the figure's first comparison; the retained numerical safety-margin paragraph remains supported by the existing verified process data. No causal claim is introduced.

The inspected PNG shows all seven panels without observed label overlap or clipped data. Dense terminal axes remain legible at the inspected resolution; manuscript-scale PDF readability still needs the orchestrator's final build inspection.

Figure 5 PDF, PNG, and generating script are byte-identical to HEAD. Its standalone content is preserved. No style impression scoring performed.

## Additional Figure 6: game counts by number of finishers

Status: PASS. Independently checked `appendix0_completion_counts_20261030.py`, its results JSON, generated PNG, and `completion_snippet.tex`. Raw terminal status `in` determines completion. Every model/seed finisher count matches the JSON; weighted category totals also recover Figure 4(e)'s individual completion counts.

| Model, descending rho | 4 finishers | 3 | 2 | 1 | 0 |
|---|---:|---:|---:|---:|---:|
| Sol | 2 | 0 | 2 | 0 | 1 |
| Fable | 2 | 3 | 0 | 0 | 0 |
| Luna | 0 | 0 | 1 | 2 | 2 |
| Astra | 3 | 0 | 1 | 0 | 1 |
| Opus | 1 | 1 | 1 | 0 | 2 |

Each row totals five games. The figure's order, segment widths, numbers, and legend match this table, with no observed clipping or overlap. Its caption correctly distinguishes five games here from twenty individual end states in Figure 4(e).

Zero finishers does not mean all four agents died: Sol 4101, Astra 4101, Luna 4103, and Opus 4101 each have four EXITs; Luna 4101 has three EXITs and one shutdown; only Opus 4103 has four shutdowns. The caption explicitly avoids conflating these outcomes.
