# Appendix 0 figure separation and preservation audit

Status: **PASS** for reviewed source, vector blocks, composed PNGs, writer draft, and bounded main-text diff. Final LaTeX PDF pagination and reference resolution remain with the orchestrator. Only this report was written.

## All source panels accounted for

Validated the manifest's 17 entries, unique original panel identities, nonempty destinations, existing block PDFs, and all recorded SHA-256 values. The compositor captures existing Matplotlib artists and places vector PDFs; it does not rerun the raw analysis or bootstrap calculations.

| Original panel(s) | New location |
|---|---|
| Old 3(a), overall completion distribution | New 3(a), overall row |
| Old 4(a), model completion game counts | New 3(a), model rows on left |
| Old 4(e), individual end states | New 3(a), right-hand bars |
| Old 3(b–d), accuracy/transfer/rho contrasts | New 3(b–d) |
| Old 4(b), margin-band behavior | New 4(a) |
| Old 6(a–b), low-margin behavior and receipt | New 4(b–c) |
| Old 4(f), GIVE/ASK volumes by timing | New 4(d) |
| Old 4(g), terminal Sen/Gini/mean resources | New 4(e) |
| Old 4(c–d), individual/game crisis follow-up | New 5(a–b) |
| Old 5(a–d), standalone GIVE/ASK counts/amounts | New 6(a–d), original figure reused |

No original plot's quantitative information is omitted. Source-block originals and original whole PDFs remain in the block directory. The former overall completion bracket's 8-versus-17 group counts remain explicit in the new contrast panels and accompanying text.

## New combined outcome panel

Independently summed the existing game records: 4/3/2/1/0 finishers occur in **8/4/5/2/6** of 25 games, giving **32/16/20/8/24%**. The overall row appears above Sol. Each model completion row contains five games and is normalized to the same 100% width, with integer game-count labels retained. The right-hand end-state rows retain their original twenty-person counts. Caption and axes explicitly distinguish these units.

Sol/Fable/Luna/Astra/Opus ordering matches descending current pooled rho. Completion and end-state legends retain their distinct meanings, including the two EXIT margin categories. No-zero-finisher-versus-all-shutdown conflation is introduced.

## Existing Figure 3(b–d) preserved

The compositor calls the original `plot_primary` with the cached games and summary, then exports its axes and shared model/estimate legend. Independently recomputed group means and point-biserial correlations from the cached game records:

| Metric | Other games | All-four completion | Correlation |
|---|---:|---:|---:|
| Accuracy | 0.64110644 (n=17) | 0.78125 (n=8) | +0.420028 |
| Transfer per agent-round | 447.122703 (n=17) | 754.296875 (n=8) | +0.289803 |
| Per-game rho | 4.51326896 (n=10) | 3.05505607 (n=8) | −0.338587 |

All match the cached summary and plotted labels/estimates. The 95% intervals are read unchanged from that summary: accuracy [0.53779762,0.76923077]/[0.7,0.828125]; transfer [309.313069,541.870022]/[556.25,866.964286]; rho [3.23452594,5.22812434]/[2.41266401,3.74770747]. No bootstrap rerun or estimator change occurs. The legend preserves model markers, group means, and interval meaning.

## New Figure 4/5 and prose alignment

Inspected all three newly composed PNGs. Margin-band denominators, low-margin 28-observation counts, phase-stacked GIVE/ASK totals, terminal mean/min-max marks, and both crisis panels remain visible with correct relabeled letters. The shared rho cue now applies to new 4(d,e). No observed clipping, missing annotation, or legend collision. Model colors/markers and different uncertainty meanings remain distinguishable.

The writer draft's four local figure labels are unique and all local references resolve within the draft. Its captions map to the actual new panels. Figure 3's 95% intervals remain distinct from Figure 4(e)'s descriptive minimum–maximum lines. Low-margin eligibility, repeated observations, possible event overlap, same-round follow-up and recovery caveats are retained. ASK remains requested, not received, volume. The crisis comparisons retain their descriptive/noncausal limitation. Standalone counts/amounts remain in new Figure 6.

## Main-text surgical-change audit

Compared `03_analysis.tex` with the task backup. Exactly the two requested bootstrap sentences move from the analysis introduction into §3.1, verbatim. Each occurs once before and after. After removing those sentences, the entire files are identical apart from whitespace. No other main-text content changed in the reviewed diff.

No factual correction required. No style impression scoring performed.
