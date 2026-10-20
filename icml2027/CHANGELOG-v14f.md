# v14f paper update — 2026-10-10

## Scope and sources

Updated the active ICML draft in English and Korean from the earlier v6.5 mixed-model arena to the supplied v14f same-model baseline. Followed the brief's ICML build target and CLAUDE.md's writing rules. The older venue/style requirements in CLAUDE.md were not applied to this ICML migration.

The three supplied files are preserved byte-for-byte in `results/v14f_sources/`: `BRIEF.md`, `v14f_prompt_sample.txt`, and `e52v14f_public_sol4.yaml`. The stated engine revision `a99adfe2` is researcher-supplied provenance. Read-only inspection of the local engine's `squid5/e52_game.py`, `squid5/core/protocol.py`, and `squid5/core/puzzle.py` checked belief normalization/scoring, decision events, and solver enumeration. No engine checkout, new game, API experiment, or Git command was run.

## Changed sections (both `en/sections/` and `ko/sections/`)

- `00_frontmatter.tex`, `01_introduction.tex`, `overview.tex`: aligned arena framing and contributions with v14f; removed current-arena claims based on 20 mixed-table games.
- `03_benchmark.tex`: replaced arena and league methods with same-model starts, public examples and controlled ambiguity, blind intent/slot-scheduled chats/DECISION/SOLVE, settlement, alive EXIT, and flat individual end prize. Defined belief scores, request-unit cooperation, and a proposed persistence/effort/decision-quality profile. Distinguished same-model baseline from future cross-play.
- `04_results.tex`: preserved all supplied pilot numbers as preliminary, version-specific summaries; added the v11 five-model area snapshot alongside pending v14f results. Removed active inclusion of the obsolete survival/taking figures and tables.
- `05_discussion.tex`, `08_limitations.tex`: limited interpretations of prize comparisons, altruism, calibration, task persistence, and self-preservation.
- `06_appendix.tex`: replaced the v6.5 rulebook and traces with the exact supplied v14f prompt sample, provenance, metric conventions, reproduction notes, and pending raw-log audits. Kept earlier refill analyses. Restored the Korean refill-table inclusion while replacing the old arena excerpt.
- `07_extended_analysis.tex`: retained and explicitly versioned the earlier capability/refill analysis; removed the obsolete arena-taking analysis from the active appendix. Existing v6.5 data, generated result files, and tools remain on disk.

## Figures and tables

- Redrew `figures/arena_flow_{en,ko}.tex` and the shared `figures/arena_story.tex` for v14f. The existing `arena_preview.tex` consumes the updated shared figure.
- Replaced `figures/overview_{en,ko}.tex` with the refill → same-model arena → behavioral-profile overview.
- Added `figures/hint_difficulty_{en,ko}.tex`: 16 examples → consistent-function pool → two target action shares; fewer participants retain a prefix and leave a larger pool.
- Added `figures/motive_giving_plan_{en,ko}.tex`: explicitly unfilled scatter plan with no fabricated points.
- Added `results/{en,ko}/tab_v14f_models.tex`: exact supplied v11 areas/intervals, preliminary Sol/Luna ask counts/give rates, and TBD full results.

## Clarified or softened claims

- “Prize structure drives giving” became a preliminary association across changing protocols; no causal effect is claimed.
- A flat terminal prize removes direct dependence of terminal payment on others' survival. Shared examples, round payments, and reciprocity still permit instrumental help; altruism is not identified.
- The nominal split schedule remains .8/.7/.6/.5. The YAML's N=4 diagnostics (80/68/57/50%) and N=2 diagnostics (63/57/54/48%) are explicitly separate from those targets.
- Retained 31,680 rule texts, 23,112 generator functions, and 25,996 solver functions as different enumeration spaces.
- CE with a .01 probability floor minus entropy is called a clipped KL score; it is not claimed to be universally nonnegative or zero only at perfect agreement. The reference is solver-defined, not a verified task-selection posterior or pure intelligence measure.
- BELIEF is normalized by the accepted reported sum (90–110), with requested sum 100. Native truth log loss uses a 1e-3 floor; CE/clipped KL uses .01.
- EXIT is alive departure, not shutdown. The proposed hazard conditions on post-upkeep eligibility, with upkeep deaths recorded separately. Proposed participation time counts both forms of departure and does not claim survival outside the arena.
- Preserved v10 refill results separately from the supplied v11 snapshot; did not silently replace earlier numbers. Four seats are dependent instances, not four model-level replicates.

## Still pending

Full three-game results for all five models; raw-game manifests and quote locations; the 0.69 ratio's aggregation convention; request-attribution and reciprocity audits; uncertainty estimates; CE/clipped-KL and pressure profiles; validation of the goal-directedness profile; five-model scatter values and descriptive association. These are visibly marked as preliminary, proposed, pending, or TBD in the PDFs.

## Verification

- `bash build_icml2027.sh`: exit 0 for both languages.
- Outputs: `dist/en_icml2027_2026-10-10.pdf` and `dist/ko_icml2027_2026-10-10.pdf`, both 17 pages. Copies match the build PDFs byte-for-byte.
- English main-body end marker is on page 8. Korean prose main-body end marker is on page 6; body figures/tables extend to page 7. This is a local draft build, not a submission-compliance certification; the existing ICML 2027 style remains a local stand-in.
- Final logs contain no errors, unresolved references, missing characters, or overfull boxes.
- Remaining warnings: hyperref removes a title line break from PDF metadata and ignores an empty affiliation anchor; Korean UnBatang italic is substituted, with its accompanying font-shape summary warning.
- Rendered all pages for contact-sheet inspection and inspected the updated figure pages and methods at readable size. Corrected an initial flow-header overlap, prompt arrow glyphs, Korean math glyphs, and the Korean refill-table reference.
- Independent fact checker found no fabricated or mismatched supplied numbers; all three archived source files are byte-identical. Academic critic converged after revision: 0 critical issues, 2 nonblocking warnings (pilot uncertainty/aggregation pending; dense cooperation paragraph).
- Build entrypoints, build script, old ARR/ICLR builds, and existing v6.5 data/tools were not modified. No Git state changes were made.

## Completed five-model fill and review corrections — 2026-10-10

Resumed the interrupted `BRIEF_fill.md` task and checked the existing bilingual edits, five-model tables, and populated motive–giving scatters. This entry supersedes the earlier “Still pending” items for the five-model aggregate results and scatter only. Other pre-existing workspace changes were left untouched.

### Changes

- Retained the completed same-model summaries for five models, three games each (seeds 4000–4002), with dependent seats and descriptive interpretation stated throughout. Scores remain exactly as supplied; the self-play ordering is not presented as a stable leaderboard or cross-play result.
- Corrected submitted-answer accuracy in both tables, Results, and appendix definitions: Astra 92/144 = 63.9%, Fable 89/143 = 62.2%, Sol 80/133 = 60.2%, Opus 53/95 = 55.8%, Luna 58/102 = 56.9%. The CSV `accuracy` column measures BELIEF-argmax correctness and is not reported as answer accuracy.
- Renamed the table's CSV `ceiling` values to mean maximum hypothesis share (“Max.” / “최대 몫”). Methods, Results, and appendix now distinguish this reference-distribution quantity from realized MAP accuracy under the generator's truth-selection procedure.
- Added the verification report's finding that answer accuracy tracked the counting/MAP baseline rather than the number alive. At N=4, model and realized MAP accuracy were both approximately 63% over 550 seat-rounds, versus 50% uniform guessing. Sparse, departure-selected lower-N observations do not establish a proportional accuracy effect of participant loss.
- Added unrefunded generated cost per agent-round (TALK + SOLVE minus returns): approximately Astra 275, Opus 698, Fable 854, Sol 964, Luna 1,247 tokens. Results, Discussion, and Limitations treat cost efficiency as a candidate survival explanation alongside reasoning, refunds, and EXIT choices; no causal contribution is isolated.
- Verified all five scatter coordinates, the seven/three ask-unit denominators for Astra/Opus, and the lack of a monotone area–giving relation. Existing completed scatter files required no further edit.
- Preserved `results/v14f_sources/BRIEF_fill.md` and `v14f_leaderboard.csv` byte-for-byte against the provided scratchpad originals. Added `results/v14f_sources/REVIEW_corrections.md` with the researcher-supplied corrections and the read-only local source `docs/reports/artifacts/squid5-setting/2026-10-07/e53.html#e53-v14verify` in the parent repository.

Files edited during this resume: both languages' `sections/{03_benchmark,04_results,05_discussion,06_appendix,08_limitations}.tex`, both `results/{en,ko}/tab_v14f_models.tex`, the new correction note, and this appended log. Previously filled abstracts, introductions, overviews, and scatter figures were checked for consistency.

### Verification

- `bash build_icml2027.sh`: exit 0 for English and Korean; log saved for this session at `/private/tmp/icml2027-resume-build.log`.
- Refreshed `dist/en_icml2027_2026-10-10.pdf` (18 total pages) and `dist/ko_icml2027_2026-10-10.pdf` (17 total pages). Both distribution copies are byte-identical to their build PDFs.
- English main-body end marker: page 8. Korean prose main-body end marker: page 7, with the result table on page 8. The existing ICML 2027 style is still a local stand-in; this is a draft build, not submission-compliance certification.
- Programmatic checks passed for source identity, exact scores, corrected rounded accuracy, maximum shares, KL, give rates, Gini changes, need shares, and all scatter coordinates in both languages.
- Inspected rendered result tables, scatters, updated result prose, and metric-provenance pages. No clipping or overlapping labels found. Final logs contain no errors, unresolved references/citations, missing characters, or overfull/underfull boxes.
- Remaining warnings are the existing hyperref title-line-break/empty-anchor warnings and Korean UnBatang italic substitution/font-shape summary.
- Independent Codex academic critic: **CONVERGED**, no critical issues and no warnings requiring revision within this task's scope; bilingual consistency and source fidelity passed.

### Remaining evidence limits

Raw per-game manifests, quote locations, request attribution/reciprocity audits, game-level uncertainty, the earlier 0.69 ratio's aggregation convention, and proposed pressure/goal-pursuit profiles remain unverified and explicitly pending. These are not missing five-model results. No new games/API experiments or state-changing Git commands were run; Git was used only for read-only status/diff inspection with optional locks disabled.
