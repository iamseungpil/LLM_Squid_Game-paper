# Independent audit: Section 3.2 metrics

- Reviewer: `/root/goal_audit`; analysis author: `/root`, prose author: `/root/juhyeon_writer`.
- Time: 2026-10-28T14:24:02.175414+00:00 UTC.
- Rubric: version 1.0, 2026-10-07. Scope: bounded G02/G03/G04 interpretation and G07/G08 reproducibility of Section 3.2. This is not an ARENA_VALIDATED or RELEASE_READY assessment; full-goal D/E scores remain unassessed.
- Only this audit record was written by the reviewer. Analysis, plot and manuscript files were not changed.

## Verdict

**PASS for the bounded Section 3.2 numerical/data/figure/prose audit. No unresolved Critical or material Warning remains.**

The initially identified bootstrap-description conflict was corrected and reread: Figures 3 and 4 now explicitly use 5,000 paired-seed draws, separately from legacy intervals. The final Gini-definition sentence was also reread: it describes final distribution equality as an auxiliary outcome, not cooperation behavior or a substitute for all-four completion. Final LaTeX build verification belongs to root and is not asserted here.

## Independent evidence

Read the stored raw event/result JSONL files directly, without invoking the production `load`, `game_metrics`, `distribution`, or `association` functions. Reconstructed all 25 games' attempted/correct solves, round-start exposure, eligible pre-solve TALK denominator and parsed EXIT count, successful GIVE totals, post-GIVE rho, and settled four-seat distributions. All matched generated JSON within numerical precision.

Cohort totals: 25 games, 192 actual solver attempts, 133 correct, 680 participating agent-rounds, 130 successful GIVE events and 383,276 transferred tokens. Eligible pre-solve TALK responses total 1,020; 990 are non-EXIT. These totals validate the underlying records; plotted points are equally weighted per-game ratios, not pooled-response points.

The goal denominator excludes the selected solver and rounds with only one participant, and requires a corresponding call-start balance. It is a repeated-response behavioral rate, not the count of independent agents or all 34 eventual EXITs. The denominator includes 30 parsed EXIT responses. Actual solver attempts, not eight scheduled rounds per game, define accuracy. GIVE is gross transferred amount, including repeated transfers, divided by round-start participant exposure; it does not measure effective help or eligible helping opportunities.

Seven no-GIVE games have undefined rho and are omitted, never set to zero. The 18 valid games have positive weighted giver and receiver margins, so the stated direction of rho is applicable. The seven exclusions are Fable 4105, Astra 4103, Sol 4101/4103, Opus 4105, Luna 4103/4104. Opus 4103 has all four settled balances zero: mu=S=0 stays in their analyses; only G is undefined and omitted, leaving n=17.

Independent sorted-vector Gini calculation used `[2 sum(i*z_sorted_i) - (n+1) sum(z)] / [(n-1) sum(z)]`, n=4. This matches the explicitly normalized body formula and reaches one for one-seat concentration. Sen equals mu*(1-G); all-zero Sen is zero. All four original seats remain, dead seats contribute zero, EXIT balances retain their bonus, and only finishers receive the final prize.

All six OLS slopes/intercepts and Pearson correlations were independently recomputed using NumPy polyfit/corrcoef. Bootstrap reconstruction sampled the five paired seed blocks 5,000 times with RNG seed 20261028, preserved all models within each chosen seed, and recomputed each statistic from the expanded rows. All six beta/r intervals and counts matched; all 5,000 draws were valid for each metric.

| Metric | n | Pearson r | Paired-seed 95% interval |
|---|---:|---:|---|
| accuracy | 18 | -0.285621 | [-0.488549, +0.234388] |
| goal | 18 | -0.279413 | [-0.669434, +0.172493] |
| given_per_agent_round | 18 | -0.186463 | [-0.656640, +0.123781] |
| mu | 18 | -0.244826 | [-0.655823, +0.233799] |
| G | 17 | +0.205988 | [+0.033410, +0.795319] |
| S | 18 | -0.287605 | [-0.655633, +0.051370] |

Pre-prize mu/G/S distributions and all three sensitivity correlation intervals were also independently verified. Their r values are -0.082231, +0.367870, -0.202672; G's interval is [-0.042900, +0.690888]. Thus the settled G interval above zero is sensitive to prize treatment. The latest subsection explicitly reports this and does not treat mu/G/S as independent corroborating evidence.

## Interpretation and artifact checks

- G02: prose interprets rho as relative retained resource margin and non-EXIT as observed goal persistence. It explicitly rejects direct inner-motive measurement and causal conclusions.
- G03: the actual-attempt denominator is explicit. No pure-ability claim is made from the Section 3.2 correlation.
- G04: GIVE is an exposure-normalized transfer quantity. Gini concerns final inequality; it is not an independent effective-cooperation measure. The final writer clarification explicitly states this distinction.
- G07/G08: one game is the point/OLS weight; repeated seats/TALK turns are not treated as independent correlation observations. Uncertainty uses paired seed blocks. Only five blocks and six unadjusted comparisons limit interpretation; the caption calls the comparison exploratory.
- All section values and exclusion counts match JSON. The subsection uses body equation `eq:rw-sen` and its own body figure; no appendix reference or appendix-only evidentiary dependency was found. Prize sensitivity is stated in the body itself.
- Inspected final Figure 4 PNG and existing rendered-page preview. Six panels, units, valid n, model colors, OLS lines and interval labels are consistent with JSON. Zero mu/S observations remain visible after the negative bottom margin. No material clipping or label collision found. Rendered-page preview predates the last two wording fixes, so it is not certification of the final PDF.
- Generated JSON input-code hashes match current analysis source files. No new experiments or external data were used.

Bounded cautions are already compatible with the manuscript: rho is conditional on observed GIVE, goal rates are near ceiling, model mixture is not removed by resampling seeds, and prize-driven distributions are highly non-Gaussian. Leave-one-model-out correlations range -0.463 to -0.188 for accuracy, -0.518 to -0.195 for goal, -0.251 to +0.123 for GIVE exposure, -0.528 to -0.001 for mu, +0.021 to +0.527 for G, and -0.373 to -0.168 for S. These do not justify a stable causal or model-general claim; none is made here.

## Artifact SHA-256 snapshot

- `rubric.md`: `4069c7e8d3ffffc0c7c81058c30be740575d1cb9b8933baf3311e59714043579`
- `paper/cogsci2027/tools/section32_metrics.py`: `fd92f5ae207fe1ac15ccbb9fd07123ff7ae25f3f20d1fd219fb16d0dfdd95520`
- `paper/cogsci2027/tools/fig3_completion_20261028.py`: `d93e4a00f3c7583403c8894b05dadf551dc6e84aa19df4102e6d4e4daa916c97`
- `paper/cogsci2027/tools/feedback_20261028.py`: `1dfae116c0822802f3af4108554ab05c2df6f4d5fa836e4904b97ae37df699a7`
- `paper/cogsci2027/tools/completion_life_buffer.py`: `c68c1f1a8641b8874d1d8219988c68679d4fb8cafee86c08991499065f6bfe25`
- `paper/cogsci2027/tools/inequality.py`: `6f63c3ce8c38089b526f6d4b6aff771b317b69211b363913d6af196baa67d071`
- `paper/cogsci2027/results/section32_metrics.json`: `9edaef85444c89e568458152029c427ddecb73182104b4a89906dfb6ad0bc3af`
- `paper/cogsci2027/ko/figures/fig4_section32_metrics.png`: `c946333c69ec6b13978506aeb74bab0e1917ea13432fef9f801fbde5f875cdf6`
- `paper/cogsci2027/ko/figures/fig4_section32_metrics.pdf`: `d64b916aed3c1cb55cba8aed8fc6d7a5879794011f51798b0c9226c7a035be6a`
- `paper/cogsci2027/ko/sections/02_arena.tex`: `3c1b297138d4e298ba6d34d93424e44d7610c1aab96bdedb590cbac2d3a2ddf3`
- `paper/cogsci2027/ko/sections/03_analysis.tex`: `1b5e601fa7be8786608d75bf0827d92eae7919465e0213b3ab6e161e4ec98a1f`
