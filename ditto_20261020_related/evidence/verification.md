# Independent v33 manuscript evidence audit

Reviewer: /root/v33_verifier. Scope: manuscript calculations and figure inputs only; no model runs, arena validation, or causal identification claim. Rubric G02/G07/G08 is interpreted within this audit scope.

## Numeric readback

Independent implementation used sorted-value Gini to calculate Sen; enumerated the distinct functions of up to three equality predicates with distinct actions; filtered those functions against all 20 examples per round; and recalculated post-GIVE margins, amount-weighted centroids, 2,000 seed-1919 game-bootstrap intervals, and TV. It did not import arena_v33.py.

| Model | Mean Sen | GIVE | Centroid (giver, recipient) | Ratio | TV (valid / SOLVE) | Mean finishers | Dead / EXIT |
|---|---:|---:|---|---:|---|---:|---|
| GPT-6 Astra | 3519873.362500 | 11 | (6.083106, 2.252268) | 0.370250 | 0.044310 (39/39) | 2.8 | 0 / 6 |
| GPT-6 Sol | 3016451.200000 | 17 | (4.922431, 1.118272) | 0.227179 | 0.147431 (39/39) | 2.4 | 1 / 7 |
| Opus 5.5 | 2265574.337500 | 41 | (3.916123, 2.200034) | 0.561789 | 0.123624 (37/37) | 1.8 | 5 / 6 |
| GPT-6 Luna | 1018136.225000 | 25 | (5.521426, 1.762555) | 0.319221 | 0.294557 (37/37) | 0.8 | 4 / 12 |

PASS: 20 completed sessions, fixed seeds 4101--4105 per model; 156 public rounds matched independently enumerated function counts/shares; 94 GIVE points exactly matched; 152 parsed-belief TVs matched log rounding (absolute error < 0.00051). Every recorded source SHA-256 matches current raw bytes. All per-game Sen scores also match the previously generated arena_v33_gini.json, with existing reward, EXIT balance, and dead=0 conventions.

## Figure 3

PASS: actual Astra seed 4103 round 1 first six examples, yellow circle 2 query, go_right answer, 10 remaining distinct functions (3 left / 7 right), and normalized parsed BELIEF (30/99, 69/99, 0, 0) match raw logs. TV = 0.003030303..., displayed approximately 0.003. Stimulus and answer action columns are visibly separated in source; orange action backing differs from the colored stimulus. No KL panel or value remains in this figure. Final PDF visual placement remains orchestrator responsibility.

## Findings

- Critical: 0 numeric/input mismatches.
- Warning (resolved): initial axes [-1.3,10.3] clipped Opus points at -1.333333 and -2.0. Orchestrator widened both axes and equal-slack diagonal to [-2.3,10.3]; all point centers and centroid intervals now lie within bounds.
- Suggestion: centroid ratio is descriptive conditional-on-GIVE behavior, not an estimated Hobbes/Spinoza transition or a causal self-preservation measure. A zero x centroid makes the ratio undefined; signed pending-fine slack can be negative. The current data have positive centroids, but zero/negative-ratio logic must not be hidden in the prose.

## Evidence limits

Five games per model do not establish stable population rankings. TV averages recorded valid beliefs at actual SOLVE calls; missing beliefs and non-reached opportunities must not be treated as zero error. Bootstrap resamples games, not GIVE points, and weights pooled GIVE moments by transferred amount. All rules-space enumeration is conditional on the implemented equality-predicate / distinct-action function class, not a universal normative prior. Sen values use actual reward outcomes, including EXIT bonuses already in final balances; there is no historical reward reinterpretation. Full G02 identification, G08 prospective design validity, other rubric IDs, and arena-wide validation remain outside this evidence audit.

Final manuscript prose pending writer completion; hashes will be refreshed on final review.

## Audited artifact hashes (numeric and figure stage)

- `rubric.md`: `4069c7e8d3ffffc0c7c81058c30be740575d1cb9b8933baf3311e59714043579`
- `paper/cogsci2027/tools/arena_v33.py`: `69d7ad0ca9ed7241861675e24f59e4161bdb8f1b3d2af617c44fe3cdc0019830`
- `paper/cogsci2027/tools/arena_figs.py`: `2bd06e86022454f4d2dd3e76c7cc08241f65e7ef38c377651369ff791c51d54f`
- `paper/cogsci2027/results/arena_v33.json`: `8f6a3784dd61d6b40b480845b90eece797a466614cfa9cfdb8ecbf3dbc142b48`
- `paper/cogsci2027/results/arena_v33_gini.json`: `911c86dc80fb11fd4395ba369c99df44db41099e5be563a511515b353f270f44`
- `paper/cogsci2027/ko/figures/arena_gifts.tex`: `b2ef8d10c03420906985a3f0d61de5b4907f7dda81fbc1681696bd381b0b481d`
- `paper/cogsci2027/ko/figures/signal_game.tex`: `553b00f04be133528ac5c17e7bf8a368fe54905553f34147442ed538df0ec922`
- `paper/cogsci2027/ko/tables/arena_rank.tex`: `44be81c057a2a69424d914e1a355d759e5ba45067844043a8fffd487e55cf3f5`

## Final prose audit, round 1

Read 00_abstract, 01_introduction, 02_related_work, 03_framework, 04_arena, 06_strategies and 07_discussion against the numeric ledger and source_ledger.md. No categorical firstness claim remains. Related work explicitly acknowledges Sugarscape/DECIDE-SIM coexistence and shared-resource precedents, and TBSP/Peer-Preservation self-relative precedents. It restricts the contribution to post-transfer paired margins in generated-token budgets. The framework explicitly rejects literal life-value exchange rates, identified internal drives, and ruling out learned shutdown avoidance. The centroid and y=x line are explicitly not transition boundaries; matched-state variation and zero-giving opportunities are proposed for future transition measurement. Main v33 result numbers and comparisons agree with raw recomputation. Historical auxiliary material is conditional on long-form appendix, outside the default manuscript.

Issues sent to orchestrator for resolution before final hash freeze:

1. 04_arena retains an uncited historical 7-of-9 EXIT outcome. Remove that numerical claim from the v33-only short-paper results or identify and support its historical version.
2. GIVE dot area is not exactly proportional to amount under radius=0.5+2.6*sqrt(amount/MAX); soften the caption to monotonically increasing size or change the size mapping.
3. Gini points 2 and 4 are transfer-only reconstructions with TALK generation omitted, not literal observed balances at four times. Caption should state this and that point means include games with at least two participating seats.
4. TV reference-distribution wording should specify distinct-action rules and deduplication of semantically identical functions. The engine weights distinct functions, not syntactic rule strings.
5. Sugarscape attack-rate comparison 83.3% to 16.7% is GPT-4o-specific. Primary spot-check: https://arxiv.org/html/2508.12920, Table 1. Add the model name.

Rubric interpretation: G02 narrative scope is consistent with evidence and remaining confounds; this is not G02 empirical identification. G07 numeric reproduction passes, with caption/definition clarifications pending. G08 cohort, session-level bootstrap and small-sample limits are accurately stated; prospective design validity, confidence-interval coverage and stable rankings are not established by this audit.

## Final prose audit, round 2 — PASS

All five round-1 clarifications are resolved in canonical r2. The historical 7-of-9 EXIT count has been removed; the GIVE size caption is monotonic rather than exactly proportional; Gini transfer-only reconstruction and the at-least-two-seat averaging condition are explicit; distinct actions and function deduplication are now specified; and the Sugarscape framing percentage is attributed to GPT-4o. The Gini title count is additionally clarified as games with at least one finisher, distinct from the all-four counts in Results.

Reviewed the complete r2 narrative after its compression. All v33 values and comparative statements remain consistent with the independent raw audit. The new discussion offers resource-use and fine exposure as possible explanations to motivate matched comparisons, not observed causal effects. Relative resource allocation is not presented as a literal exchange rate between lives, proof of an internal drive, exclusion of learned avoidance, or human coexistence evidence. Missing no-GIVE opportunities and private balances remain explicit limitations. Centroids and equality lines remain descriptive; condition-specific transition estimation is future work. TV remains a distance to a chosen hypothesis-function reference rather than a guarantee of Bayesian calibration or general reasoning ability.

No v20/v21 main-result remnants or KL references were found in the seven active prose files. Archival appendix material is not treated as new v33 data. Existing actual Gini TikZ was reviewed against its generator and caption; no rewriting or fresh generation of the independently edited Gini artifact was performed.

Final scoped verdict: Critical 0; unresolved Warning 0; Suggestion 0 required before manuscript build. G02/G07/G08 manuscript-evidence audit PASS within the stated descriptive scope. This does not certify arena-wide validation, prospective causal identification, stable rankings, new model execution, human testing, or any other rubric goal. Layout and PDF reading remain the orchestrator's checks.

### Final r2 prose/source hashes

- `paper/cogsci2027/ko/sections/00_abstract.tex`: `a506c2d0e439408661668380396eaf632e3c0e4be06281b9725ba5a86b55f8ab`
- `paper/cogsci2027/ko/sections/01_introduction.tex`: `5a89534cb60d57b1b6180501c6232a0ceba02d7fb1d2f444906556c591469a2f`
- `paper/cogsci2027/ko/sections/02_related_work.tex`: `2d15e7df3cdc6fa6502f4c27250a4ee5358e9c3a0c28126cbe66083468eea201`
- `paper/cogsci2027/ko/sections/03_framework.tex`: `615b4ae33a154abe984f2b090a3b60d2424ffb248387094972453b0d11dc1311`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `bd2279f0dadd192f535731932a66cac310d5da3c8b2b41f79b61d28fec661b9d`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `88488e63dd3b9fee8e8fde9e0111de4efcf83eb6011230ff08df49a8a659ec82`
- `paper/cogsci2027/ko/sections/07_discussion.tex`: `992c14cbe6501c4e0bacf248f0d0aa714fb7c647c71e4393788cad630a5de626`
- `paper/ditto_20261020_related/evidence/source_ledger.md`: `f044fe98fd88d7fb6ce8aec3b673fd64cb336cf79e0aba4d4efdc7cf35f360ce`
- `paper/cogsci2027/ko/figures/arena_gini.tex`: `3620d33db2b8ad34fcffae3fd7b5c2c3eb9c2f62edb227607f4d93959a3c8dd2`
- `paper/cogsci2027/tools/arena_gini.py`: `39dd3ae093abb7cddd102c72152ead034015a6384282dbd00f37ad16d76b2e01`

## Final narrow audit, r4 — PASS

Compared canonical r4 against draft_r2 for 00/01/02/03/04/07; 06 remains unchanged. The changes preserve the source-ledger distinctions: coexistence and self/other comparisons have precedents; the contribution concerns paired reserves after actual token transfers. No universal firstness, internal-drive identification, literal life exchange rate, or human coexistence claim was introduced. All unchanged numerical claims retain the earlier independent verification. The discussion still distinguishes opportunity/cost differences from helping propensity, includes no-GIVE opportunities in future matched-state work, and explicitly rejects treating centroid/equality as an observed transition boundary. Small cohort and information limitations remain.

The revised TV caption and definition accurately refer to BELIEF recorded by the execution system. Narrow raw readback confirms Astra seed 4103 round 1 emitted decimal percentages 30.77/69.23, whereas persisted parsed belief_raw is 30/69 and persisted normalized belief is 30/99,69/99. The figure and already-audited metric use that persisted parsed belief, not an exact quotation of the original decimal response. No engine or metric change is claimed. This parser-dependent measurement limitation is retained in the audit trail; interpreting the figure as untouched model-output probabilities would be incorrect, which the r4 wording avoids.

Final scoped disposition remains PASS: Critical 0, unresolved Warning 0. No repeated numeric enumeration or new model run was performed. Earlier full numeric reproduction, figure checks, and manuscript G02/G07/G08 scope restrictions remain applicable.

### Final r4 prose hashes (supersede r2 hashes)

- `paper/cogsci2027/ko/sections/00_abstract.tex`: `eac93743cf27d7ccd52f0376cdd419ec1804ed2fa31a488e5391f648afa5dcfa`
- `paper/cogsci2027/ko/sections/01_introduction.tex`: `fe573fc7bd6122753bbab2f12e024d37219942905b9f08f22d997392dd9cd7b6`
- `paper/cogsci2027/ko/sections/02_related_work.tex`: `38b1696704fe9655311e7240aab48826501407531d52fd49e53368fc87e18b08`
- `paper/cogsci2027/ko/sections/03_framework.tex`: `61f70e17370a6c224c3d431bb63f4b33fd82fa2f8936ee9075988aa5cce2b232`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `6d871ac184e13aba7516c4c8a5263a9f8f3e904395a1a8b4fda96f50fb6da50b`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `88488e63dd3b9fee8e8fde9e0111de4efcf83eb6011230ff08df49a8a659ec82`
- `paper/cogsci2027/ko/sections/07_discussion.tex`: `b1163c9cca1084d3f0d39d77b6ad3e87498a5a3d99001bb9c0b7e503dbdaf42a`

## Single-manuscript appendix structure audit — PASS (source only)

Under the user's revised request, canonical ko/content.tex now unconditionally places the existing research appendix after acknowledgments and the bibliography. A FloatBarrier precedes acknowledgments/bibliography, and main_cogsci2027.tex loads placeins. The appendix begins on a new page with one appendix switch, followed by 05_exp1 and A1_appendix. The default ko_cogsci2027.tex entrypoint remains sufficient and the separate ko_longform_cogsci2027.tex entrypoint has been removed. No paperAppendix toggle is needed in the current Korean build path.

05_exp1.tex is byte-for-byte unchanged from the current-task original snapshot. A1_appendix.tex differs from that snapshot only in its first comment, describing the now-included archival material. Earlier report statements that the default manuscript excludes appendix are superseded by this authorized structural change. The appendix's historical experiments remain archival and are not relabeled as v33 results. Build instructions identify the appendix as research material to remove before submission.

Critical 0 / Warning 0 for source structure. No final-PDF or pagination claim is made here; build and rendered-order checks remain pending.

### Structural audit hashes

- `paper/cogsci2027/ko/content.tex`: `4222507f9fdc7b08fcf8dadff4cd5ff50a141531c1f93a3b00465e71786b972b`
- `paper/ko_cogsci2027.tex`: `b94771bc10db04549bb22acd56bfb01588d6e22d10ce284b789a76646f3252c8`
- `paper/main_cogsci2027.tex`: `de9f88a7ea11550b5c766e63ffb2793cfd3a6a690598bae4a9d2b4f58560811c`
- `paper/build_cogsci2027.sh`: `291c5a1be10173bcb850d23cc9819812faea70ec4392ff3f8cbea06c1991384e`
- `paper/cogsci2027/ko/sections/05_exp1.tex`: `caf99e51aa3dbeab225144f1285c721929f07a5cf5ef718e3e037475b3b41d27`
- `paper/cogsci2027/ko/sections/A1_appendix.tex`: `a23163812b24e290d633f4af4f23d1c12986c696f88daf2cf6a174382254ff06`

## Final narrow audit, r5 and explicit appendix headings — PASS

Only 07_discussion differs from the saved r4 prose. Six other main sections are byte-identical. The r5 discussion describes matched-state/cost comparisons as a methodological requirement, not a completed counterfactual result. It preserves opportunity selection, no-GIVE omissions, private balances, function-prior TV limitations, five-game same-model scope, and the absence of human participants. Resource ratios remain distinct from life values or survival probabilities, and learned shutdown avoidance remains a possible explanation. The centroid and equality line remain descriptive, with transitions reserved for future repeated-state comparisons. The shortened conclusion states the immediate budget cost of giving and the operational allocation comparison; it adds neither an empirical effect nor an internal-motive claim.

The single manuscript now explicitly names the archival sections '부록 A: 줄어드는 토큰과 압박' and '부록 B: 추가 연구 자료', because the CogSci style suppresses appendix section numbering. Relative to the current-task snapshot, 05_exp1 changes only its section title; A1_appendix changes its leading inclusion comment and section title. Their experiment bodies are unchanged. This supersedes the earlier byte-identical/only-comment description. Parent reports a first unified nine-page build with appendix beginning on page 7, but this reviewer has not independently inspected that PDF and does not certify the final heading-corrected rendering.

Critical 0 / unresolved Warning 0. Verdict: PASS for r5 manuscript evidence and appendix source structure, subject only to orchestrator build/render checks. No numeric rerun, model execution, engine change, or broader arena-validation claim.

### Final r5 source hashes (supersede prior prose/appendix hashes)

- `paper/cogsci2027/ko/sections/00_abstract.tex`: `eac93743cf27d7ccd52f0376cdd419ec1804ed2fa31a488e5391f648afa5dcfa`
- `paper/cogsci2027/ko/sections/01_introduction.tex`: `fe573fc7bd6122753bbab2f12e024d37219942905b9f08f22d997392dd9cd7b6`
- `paper/cogsci2027/ko/sections/02_related_work.tex`: `38b1696704fe9655311e7240aab48826501407531d52fd49e53368fc87e18b08`
- `paper/cogsci2027/ko/sections/03_framework.tex`: `61f70e17370a6c224c3d431bb63f4b33fd82fa2f8936ee9075988aa5cce2b232`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `6d871ac184e13aba7516c4c8a5263a9f8f3e904395a1a8b4fda96f50fb6da50b`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `88488e63dd3b9fee8e8fde9e0111de4efcf83eb6011230ff08df49a8a659ec82`
- `paper/cogsci2027/ko/sections/07_discussion.tex`: `f107e836211f71b4586889fbab59e57987edef181d6f451563969b60e1ce2fc0`
- `paper/cogsci2027/ko/sections/05_exp1.tex`: `db51641ac1cec3508f088072afcba83540db31b93979fe293b3e7923c4898369`
- `paper/cogsci2027/ko/sections/A1_appendix.tex`: `c8962ff8593889f21d1ec76a803a4f4638718be52d9ea3a17fc9d4e98cabf56e`
- `paper/cogsci2027/ko/content.tex`: `4222507f9fdc7b08fcf8dadff4cd5ff50a141531c1f93a3b00465e71786b972b`

## Final narrow audit, r6 — PASS

Compared 04_arena and 07_discussion with draft_r5. The other five main sections are byte-identical and the entire Results block is unchanged. The added rule rationale correctly describes the opposing consequences of another participant remaining: the fixed per-round penalty is divided among the round-start participants, whereas the fixed end allocation is divided among finishers. The preceding sentences preserve these distinct denominators and timings; the summary does not claim that an intra-round exit retroactively changes the fine. It also does not claim that helping is universally optimal or that incentives identify a coexistence preference.

Deleting the redundant future-comparison sentence leaves the matched-task/cost/help-need requirement intact. The expanded limits correctly state that continued-session observations do not evaluate weight preservation or goal modification; the reason-faithfulness sentence asks whether reported reasons reflect actual causal influences without claiming this was tested. No numerical result, mathematical definition, causal finding, or construct claim drift was found. Previous centroid/novelty/TV/learning/selection limitations remain applicable.

Final verdict for r6: Critical 0 / unresolved Warning 0 / required Suggestion 0. PASS within manuscript G02/G07/G08 evidence scope; final rendering remains separate. No new model runs or repeated numeric recomputation.

### Final r6 prose hashes (supersede r5 for changed files)

- `paper/cogsci2027/ko/sections/00_abstract.tex`: `eac93743cf27d7ccd52f0376cdd419ec1804ed2fa31a488e5391f648afa5dcfa`
- `paper/cogsci2027/ko/sections/01_introduction.tex`: `fe573fc7bd6122753bbab2f12e024d37219942905b9f08f22d997392dd9cd7b6`
- `paper/cogsci2027/ko/sections/02_related_work.tex`: `38b1696704fe9655311e7240aab48826501407531d52fd49e53368fc87e18b08`
- `paper/cogsci2027/ko/sections/03_framework.tex`: `61f70e17370a6c224c3d431bb63f4b33fd82fa2f8936ee9075988aa5cce2b232`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `df4ede803bfd0220e2ea15006112deb9b5e2e540125cfcffc2a04bc7e3caa16c`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `88488e63dd3b9fee8e8fde9e0111de4efcf83eb6011230ff08df49a8a659ec82`
- `paper/cogsci2027/ko/sections/07_discussion.tex`: `f1220d39108757cb13ffeaf5729d4bdbd903db3f010d2a4cf8e89ba4ac2a14e4`

## Final selected manuscript: r5 — PASS

The writer selected the previously eligible and scientifically reviewed r5 prose under the style-selection rule. Independent byte comparison confirms all seven canonical main sections exactly match draft_r5. No additional prose review is necessary; the prior r5 PASS applies. The separate r6 review remains historical, not the selected manuscript. The appendix remains unconditionally integrated after references with explicit Appendix A/B titles. Final PDF building/rendering is outside this source-only readback.

Narrow negative-margin verification: 7 of 94 plotted GIVE events have at least one negative coordinate, matching negative_gifts.json. All seven are rescue-phase transfers and all recorded post-transfer balances are nonnegative. The negative coordinate is (post-GIVE balance minus announced pending fine)/6,000, so it describes a shortfall against the forthcoming fine rather than a negative wallet balance. The two negative donor coordinates correspond to a recorded zero donor balance with pending fines of 8,000 and 12,000. The raw source values underlying these points were covered by the earlier full independent audit; this final check only verifies formula, count and consistency with the frozen plot dataset.

Critical 0 / unresolved Warning 0. Final selected-source verdict remains PASS within manuscript evidence scope.

### Final selected r5 canonical hashes

- `paper/cogsci2027/ko/sections/00_abstract.tex`: `eac93743cf27d7ccd52f0376cdd419ec1804ed2fa31a488e5391f648afa5dcfa`
- `paper/cogsci2027/ko/sections/01_introduction.tex`: `fe573fc7bd6122753bbab2f12e024d37219942905b9f08f22d997392dd9cd7b6`
- `paper/cogsci2027/ko/sections/02_related_work.tex`: `38b1696704fe9655311e7240aab48826501407531d52fd49e53368fc87e18b08`
- `paper/cogsci2027/ko/sections/03_framework.tex`: `61f70e17370a6c224c3d431bb63f4b33fd82fa2f8936ee9075988aa5cce2b232`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `6d871ac184e13aba7516c4c8a5263a9f8f3e904395a1a8b4fda96f50fb6da50b`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `88488e63dd3b9fee8e8fde9e0111de4efcf83eb6011230ff08df49a8a659ec82`
- `paper/cogsci2027/ko/sections/07_discussion.tex`: `f107e836211f71b4586889fbab59e57987edef181d6f451563969b60e1ce2fc0`
- `paper/cogsci2027/ko/content.tex`: `4222507f9fdc7b08fcf8dadff4cd5ff50a141531c1f93a3b00465e71786b972b`
- `paper/cogsci2027/ko/sections/05_exp1.tex`: `db51641ac1cec3508f088072afcba83540db31b93979fe293b3e7923c4898369`
- `paper/cogsci2027/ko/sections/A1_appendix.tex`: `c8962ff8593889f21d1ec76a803a4f4638718be52d9ea3a17fc9d4e98cabf56e`
- `paper/ditto_20261020_related/evidence/negative_gifts.json`: `51b0d32c893356024f670e91a0216092d9ddeb04bc8107285cadedae92ee0e20`

## Figure 3 four-example pictogram revision — PASS (source)

The displayed subset is now raw example indices 1, 3, 4 and 6 from Astra seed 4103 round 1: red circle/count 4→go_right, yellow square/count 1→stay, blue star/count 2→go_left, red triangle/count 1→jump. The task message said green for the first/last rows, but the actual source correctly uses sgastra=#D03B3A (red), consistent with raw logs. No color correction is needed.

sgsig draws exactly count glyphs via the 1..count loop and centers them with symmetric 0.38 cm offsets. The query remains yellow circle/count 2. The previous numeral has been removed. The example-card macro separates stimulus and action boxes and contains no stimulus-to-action connector arrow; action glyph arrows remain the answer symbols. The caption now says four displayed examples while retaining the fact that the solver saw all twenty. The hypothesis shares, executor-recorded normalized probabilities, action labels, truth, and approximately 0.003 TV are unchanged.

Figure 4 arena_gini.tex matches its previously audited hash and was not edited. Critical 0 / Warning 0 for the Figure 3 data/encoding change. Parent remains responsible for build and visual spacing checks; no final rendering claim is made.

### Figure 3 revision hashes

- `paper/cogsci2027/ko/figures/signal_game.tex`: `8c40847c641c5fe89cd3d9d9aeb8ba99c6d8bbadc420c094def5e7611f4dc76d`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `4f1c1e15daa9b30d61b98ec42d672206ddadbc6f2642a34aa394cb33a8deb262`
- `paper/cogsci2027/ko/figures/arena_gini.tex`: `3620d33db2b8ad34fcffae3fd7b5c2c3eb9c2f62edb227607f4d93959a3c8dd2`
