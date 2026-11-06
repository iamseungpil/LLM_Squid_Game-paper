# Low-margin non-solver figure independent evidence review

Status: **PASS** for analysis, JSON, plot, and writer draft. No factual blocker identified. Final manuscript PDF build verification remains with the orchestrator. Only this report was written.

## Data and selection verification

- Verified the SHA-256 of the raw case index and all **14** original event/results files listed in the analysis provenance.
- Independently reconstructed the cohort from raw-index events: each round's earliest prep TALK `call_start`, round-start participant count greater than one, participant present in that call, non-solver, and `balance / (24000 / n) < 1`.
- Reproduced exactly **28 agent-rounds**, involving **25 agents in 14 games**. The first-prep low-margin pool has 39 observations: four singleton observations and seven solver observations are excluded. Model denominators are Sol/Fable/Luna/Astra/Opus = **9/5/5/3/6**.
- Verified every row's baseline line, round-end line, margin, ASK flag, received-GIVE flag, end status, event-line lists, and amount sums. Follow-up includes only events after the baseline and through that round's closing `round` event. No later-round outcomes are substituted.
- Checked **102** referenced baseline, round-end, ASK, and receipt source lines against the original jsonl/xz content. All matched. ASK and receipt count successful registered requests and completed transfers respectively; all relevant amounts are positive.

## Independent counts and plotted percentages

| Model | N | ASK | EXIT | Shutdown | Received GIVE |
|---|---:|---:|---:|---:|---:|
| Sol | 9 | 3 (33%) | 6 (67%) | 0 (0%) | 1 (11%) |
| Fable | 5 | 4 (80%) | 1 (20%) | 0 (0%) | 3 (60%) |
| Luna | 5 | 1 (20%) | 3 (60%) | 2 (40%) | 1 (20%) |
| Astra | 3 | 0 (0%) | 3 (100%) | 0 (0%) | 0 (0%) |
| Opus | 6 | 2 (33%) | 2 (33%) | 3 (50%) | 2 (33%) |

All unrounded JSON percentages equal count/N. The PNG's rounded percentages and k/N labels match every cell. Both panels use the same per-model cohort denominator. Model order is descending current pooled rho. Zero-event labels remain visible, and no label clipping or overlap was observed.

Events overlap: ASK+receipt occurs in seven observations, ASK+EXIT in one, ASK+shutdown in three, and receipt+shutdown in three. EXIT and shutdown are mutually exclusive terminal statuses within a round. The grouped bars correctly avoid presenting ASK/EXIT/shutdown as a partition summing to 100%.

## Writer draft review

Reviewed `review/appendix0_low_margin_20261030/appendix0.tex` after creation. Its added introduction specifies the 39-to-28 selection, first-prep baseline, non-solver restriction, contemporaneous fine definition, agent-round unit, and same-round follow-up. The caption accurately states denominators, one-or-more-event counting, actual receipt rather than request fulfillment, overlap, and shutdown as an outcome rather than a chosen action.

The interpretation paragraph matches all reported counts. It explicitly acknowledges 3–9 observations per model, repeated observations of the same agent, inclusion of events after margin recovery, and exclusion of solvers and other low-margin phases. No causal or general model-trait inference is added. It does not mislabel these values as behavior rates conditional on L<1 at the event time.

The analysis answers the deliberately narrower, common-opportunity question; it is not a census of all L<1 situations throughout the game. The draft makes that scope limitation explicit. No style impression score assigned.
