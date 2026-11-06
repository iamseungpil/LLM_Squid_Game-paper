# Appendix 0 Figure 4 evidence review

Status: figure, analysis, and writer drafts PASS; no factual blocker identified. PDF build/layout verification remains the orchestrator's responsibility.

Scope: read-only review of `cogsci2027/tools/appendix0_integrated_20261030.py`, its results JSON, `fig4_appendix0_20261030.py`, and the generated PNG. No source, figure, or data edits made by this reviewer.

## Verified

- Requested layout is present: (a–d) in the first row, (e–f) in the second. The PNG has no observed label collisions or clipped data. Panel (f) retains the original three plots and only reduces their horizontal extent.
- Panel (a) contains all 130 completed transfers. Giver-after margins range from −1 to 9.5122 and recipient-after margins from −0.4529 to 8.5862, inside the plotted bounds. The 119/120 safety-maintenance count and 24 highlighted joint-safe lifts match the transfer records.
- Panel (b) uses actual correctness: 3/6, 23/42, 48/61, 59/83 (133/192 total). EXIT counts are 19/32, 14/108, 1/137, 0/214 (34/491 total). GIVE response counts are 9/262, 5/614, 36/764, 70/1258 (120/2898 total), in ascending margin bands.
- The GIVE denominator excludes exactly 11 responses in rounds starting with a sole participant, preserving `an3/analyze.py`'s existing definition. All 11 contain no completed GIVE and are not truncated. The count difference is not a token-cap or response-validity exclusion.
- A GIVE response means at least one completed transfer: 110 responses have one transfer and 10 have two, hence 120 responses contain 130 transfers. Before-response margins use `call_start` balances with pending fines removed in rescue. Independently checked 4,765 relevant original raw-event lines against `raw_case_index.json`; all matched. `call_start` balance equals `balance_after + used` for every TALK response.
- Panel (c) uses 34 first-crisis agents in 19 games: none 0/13/3, short 2/1/4, lifted 7/3/1 for completion/EXIT/shutdown. Panel (d) uses 16 games, with all-four completion 6/8 versus 0/8. Both reproduce the process summary.
- Panel (e)'s five end-state vectors match both the original Figure 4 data and an independent combination of raw final statuses with EXIT-window margin categories: Fable 17/2/1/0, Astra 14/2/4/0, Sol 12/0/7/1, Opus 9/3/3/5, Luna 4/8/4/4.
- All 25 terminal resource vectors and their per-game Sen/Gini/mean-token metrics match `terminal_distribution_20261029.json` when joined by model and seed. Panel (f) reuses `draw_panels` with the same scales, means, point data, and missingness. Gini valid-game counts are 5/4/4/3/3; Sen and mean tokens include all five games. Sen and mean-token axes are in ten-thousand tokens.
- Updated pooled giver/recipient rho matches independent calculation: Fable 3.677598, Astra 2.700880, Sol 4.237786, Opus 1.833345, Luna 3.171678. GIVE-present game counts are 4/4/3/4/3 out of five. These are ratios of pooled transfer-weighted margins, not arithmetic averages of per-game ratios. The historical `rho_axis.json` stores the opposite orientation; its rounded values were not inverted for this check.

## Caption requirements for final prose review

- Distinguish the coincidentally equal 120 denominators/numerators: (a) 120 transfer **events** beginning with giver margin at least 1; (b) 120 **responses** containing completed transfers.
- State GIVE's round-start two-or-more-participant eligibility and response-start measurement, alongside the separate SOLVE and EXIT-window denominators.
- Label panels in the new order; describe (f) only as Sen/Gini/mean tokens, in ten-thousand tokens. End-state counts are in (e).
- Table 1 must state pooled rho aggregation and the five-model valid-game counts; do not call its values mean per-game rho.

## Writer draft review

Reviewed `review/appendix0_layout_20261030/appendix0.tex` and `analysis.tex` after their creation. The appendix caption uses the new (a–f) ordering, correct units, separate response/window/solve denominators, and the revised 34-agent crisis cohort. Panel (d) now correctly describes points as per-game finisher counts and its fractions as all-four completion rates. All numerical statements checked against the figure/data are consistent. The body explicitly distinguishes 120 GIVE-containing responses from 130 transfer events and separately defines the 119/120 safety-maintenance subset.

Table 1 has the requested nine columns: individual end states removed, safety maintenance replaced by the correct pooled rho values. Its caption explicitly says the five games are pooled and excludes an arithmetic mean interpretation; seven no-GIVE games are described as undefined rather than zero. Optional precision improvement: report GIVE-present game counts of 4/4/3/4/3 (each out of five) in the caption. Optional standalone-figure improvement: define panel (a)'s 119/120 denominator in the caption as well as the body.

The main text's earlier 33-agent crisis analysis remains unchanged; only its Table 1 is revised in the draft. The appendix explicitly presents the revised 34-agent cohort and includes deaths in the crisis round, so the two populations should not be silently conflated during subsequent integration.

No factual blocker found in the updated figure, analysis, or writer drafts. No style impression score was assigned.
