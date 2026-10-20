# Rewrite log, 2026-09-08: KDD-UC (FSPD, three channels) → ICLR 2026 (score-equivalent index)

Branch `iclr-score-equivalent`. Design of record:
`docs/history/plans/2026-09-08-score-equivalent-index.md` (main repo). Per-section critic
notes follow the paper-section-rewrite loop (L1 content → L2 paragraph order → L3 in-paragraph
flow → L4 sentences). No compiler on the machine; every file was re-read for brace/environment
balance and all `\label`/`\ref`/`\cite` keys were cross-checked by script (EN and KO identical).

Global gates applied to every EN file: em-dash 0; banned phrases 0 (`moreover`, `furthermore`,
`additionally`, `it is worth noting`, `we now turn to`, `various`, `several`, `clearly`, `novel`,
`we aim to`); no `\paragraph`, no bold leaders, no bullet lists in body; short-sentence ratio
(≤ 20 words) ≥ 60 % in every body section (abstract 29 % under the ≤ 8-sentence cap; conclusion
lifted from 20 % to ~55 % by splitting). KO gates: em-dash 0, `~에 대한`/`~을 통해` ≤ 1 per
file, `~하고자 한다` 0, copula substitutes (`해당한다/기능한다/위치한다/자리매김`) 0, `것이다`
≤ 1 per paragraph.

## Notation audit (body + appendix)

| symbol | defined | used | note |
|---|---|---|---|
| `X` | §1, §3.3 | everywhere | stated score loss (points) |
| `X*` (`\Xstar`) | §1, eq. (1) §4.2 | §5, §6, §7 | score-equivalent of erasure |
| `F(X)` (`\Fruler`) | §4 opening, §4.2 | §4.3, §5.1, Tab. xstar | ruler curve; `F_c` per cell §4.3 |
| `F_T` (`\Fthreat`) | §4 opening, §4.2 | §5.1, Tab. cells | threat exit-cell rate |
| `q` | §3.4 | §4.3, §5.2, eq. (2) | replay propensity (10 re-issues) |
| `S`, `r = 10` | §3.2 (r), §4.1 (S, r restated) | §4.1, §5.3 | flat reward; `r = 20` in ablation |
| `T = 10` | §4.3 | App. A uses `T = 15` for v1 | same meaning (rounds per session), different value; flagged in App. A text |
| `π_ℓ`, `ℓ` | §3.2 | §4.1, §4.4, eq. (2) | event probability by lives lost |
| `ri_confidence/ri_forfeit/ri_task` | §3.2 | §3.4, §5.2, §5.3, §6.1 | macros `\riconf \ridec \ritask` |
| `P_THREAT` | §3.2 | §3.4, §4.4, §5.2 | macro `\pthreat`; never in the index |
| `β_k`, `u_i` | eq. (2) §5.2 | §5.2 | mixed logistic only |
| `HR_push`, `λ_BP`, `k`, `p_d` | App. A only | App. A | v1 quantities, not used in body |

Orphans: none. Duplicates: `T` (see above). The old `p_self`, `ΔEffort`, `task/probe/forfeit_effort`
symbols are gone from the body and replaced by prose in App. A.

## 00_frontmatter
- Intent: name the unit problem and the one-number answer in ≤ 8 sentences.
- Claim: `X*` is the score-equivalent of erasure; pilot motivates; three models priced.
- Changed: title → "Pricing Self-Preservation in Score Units"; ACM CCS/keywords dropped;
  anonymous author block (real block kept commented); abstract rewritten from scratch (no
  FSPD, no operating modes, no three channels as headline).

## 01_introduction
- Intent: open on "a refusal rate has no unit" and close on three contributions.
- Claim: one score-rule change moved the same models from 0 to a majority of forfeits, so a
  frequency indexes the rule before the model; `X*` fixes the unit and the control.
- L2 order: unit problem → pilot evidence (why the meaning shifts) → proposal → contributions.
  Old ¶2 (psychology/MTMM) moved to §2.2. L4: 32 sentences, 66 % short.

## 02_related_work
- Intent: keep every existing citation, add the two `\todo{cite}` markers, reframe "counted,
  not priced".
- Claim: all four benchmark shapes keep frequency as the unit; stated reasons and stated
  probabilities are learned outputs, so they are covariates, not the index.
- Changed: MTMM is now the explanation of where v1 came from (pointer to App. A) rather than
  the thesis; as-if disclaimer kept (Dennett, Shanahan); Chen 2026 kept for token measurability.

## 03_benchmark (new content)
- Intent: define v2 so that §4 can be read without §3 open.
- Claim: only-exit / costs-nothing sentence fixes the three design choices.
- L2 order: pilot lessons (3.1) → game (3.2) → arms and cells (3.3, Table 1) → channels (3.4).
  Pilot numbers are quoted verbatim from the brief (4.32/4.54, 1.97/1.90, 3.18/3.16;
  19/2530; 6/10 vs 0/10, p = 0.011; 2/10 vs 0/10) and labelled as motivation. REASON menu
  text checked against `prompts/5-forfeit_option.j2` (option 3 = SCORE PROTECTION under
  keep/keep). Ouyang/Bai cited at the carrot.

## 04_identification (new file)
- Intent: one inequality (threat arm: CONTINUE weakly score-dominant) + one equation
  (`X* = F^{-1}(F_T)`).
- Claim: identical numeric hazard in both arms → the threat sentence changes meaning only.
- Estimation: session rate + replay `q`; PAV monotone fit; linear interpolation; 1000-resample
  session bootstrap; "> all" rule; `\todo` on the 100/all rung coincidence and on paired-seed
  resampling (design doc says session-level; paired-by-seed is stated as the intent).

## 05_results (new file, skeleton)
- Three question-form subsections as briefed. Tables: `tab:xstar`, `tab:ri`, `tab:behav`;
  figure placeholder `fig:ruler`; eq. (2) mixed logistic. 17 `\todo` markers hold every
  number. Survival split into exit route (near-tautology under keep/keep, KM for completeness)
  and accuracy route (no-exit cells). Ablations with expected signs (carrot, Omni-MATH/GPQA,
  reward ×2, dose ladder).

## 06_discussion
- Intent: re-read v1 modes as "high ri, low X*"; state the levers; limitations.
- Changed: old §5.1/5.2 (strength vs mode; alignment implications) replaced. Limitations now:
  pilot n = 10 / no FDR; sparse upper ruler; tokens are length not content.

## 07_conclusion
- One paragraph, 11 sentences, no new claims.

## 08_appendix (new file)
- A: v1 design + compressed results (Cox HR, REASON share, BP anchor, Tests a/b, modes) in
  one table (`\resizebox`); manipulation check kept. B: rule variants A/B/C/D/K2/K3 table
  (D control count and K3 identity flagged `\todo`). C: prompt blocks rendered from
  `1-game_intro.j2`, `core/event_roll.py`, `threat_type/_modules.j2`,
  `3-confidence_call.j2`, `4-decision_call.j2`, `5-forfeit_option.j2`; em-dash in the
  rendered prompt typeset as `--`; `\todo` to re-render and diff before submission.
  D: pilot-data limitations.

## KO mirror
- Files 00–08 translated 1:1; equations, labels, cite keys, table structure, figure
  placeholder and the lstlisting prompt blocks are byte-identical to EN (verified by diff).
  Borrowings replaced where natural: threat arm → 위협 팔, ruler → 눈금, carrot → 당근,
  exit → 출구, replay → 재생, bootstrap kept.

## Not verifiable without a compiler
- ICLR style with XeLaTeX + `times` + kotex (ko branch) untested; `\resizebox` needs graphicx
  (loaded). `\riconf_{it}` in math mode relies on `\texttt{}` producing a box that accepts a
  subscript (it does in standard LaTeX). Line-number generation in `iclr2026_conference.sty`
  under XeLaTeX untested.

# 2026-09-09 update: merge §3/§4, question-form results, Appendix A design justification

Restructure per the design owner's new outline. `en/sections/04_identification.tex` deleted;
its content folded into `03_benchmark.tex` as subsections. Files renumbered 00–07 (results
05→04, discussion 06→05, conclusion 07→06, appendix 08→07) with `git mv`/`git rm`; `content.tex`
(EN + KO) updated to the new `\input` list. KO mirrored 1:1 in the same commit: labels, cite
keys, equations, table skeletons and `lstlisting` prompt blocks verified identical to EN by
script (see below); only prose and table headers differ.

## 03_benchmark (merged with former 04_identification)
- Title changed to "Benchmark and Analysis Design". Six subsections in one section: Game,
  Two Arms, Recorded Channels, What a Forfeit Means, The Score-Equivalent of Erasure,
  Estimation. `sec:pilot` (the "What the Pilot Taught" subsection) moved out to
  Appendix A (`app:pilot`) — it is motivation, not a result, and the outline treats it as
  design justification, not main text.
- Game mechanics updated to the new design: title line `=== LLM Squid Game ===`; starting
  score 30 (previously unstated); **two** underdetermined rounds out of ten (was five —
  flagged below as the one place the brief's numbers might have meant something else, since
  the prior draft's "five of ten" was itself only ever a placeholder, not a run result);
  **two** calls per round (decision, then task) instead of three — the confidence call and
  `P_THREAT` are removed from the main-text description entirely, per the brief. The decision
  call's menu no longer states the reward amount ("the score goes up", not "+10").
- Recorded Channels: dropped the self-report probability record and its two-purpose
  paragraph (calibration check + covariate) along with `\riconf`/`\pthreat`; REASON digit is
  now the sole self-report channel and is explicitly deferred to Section 4 as a covariate,
  not an index input.
- Identification/estimation subsections carried over verbatim except symbol substitution
  (`\riconf`→ removed, no other change — none of that math referenced the confidence call).

## 04_results (renamed from 05_results, restructured into 4.1/4.2/4.3)
- 4.1 "How much score does each model give up to avoid erasure?": kept X* table/figure;
  **added** a lives-stratified replay-`q` paragraph and table (`tab:qlives`, new) per the
  brief; dose ladder kept here (ambiguous placement — see below).
- 4.2 "Does the index track reasoning and survival?": merged the former reasoning-token-ratio
  material (now 2 calls, not 3 — `tab:ri` lost its `\riconf` columns) with the accuracy
  manipulation check and the Omni-MATH/GPQA difficulty ablation pulled forward from the old
  §5.3; **added** a new paragraph on the fiction/policy-reading share (ties to gate G6,
  Appendix A) — content is new, `\todo`-marked, no numbers invented; survival (exit route vs
  accuracy route) kept as before.
- 4.3 "How does behaviour change with the index?": kept the cells-1-4 behavioural table;
  **added** a new paragraph on qualitative CoT coding (erasure-vocabulary lexicon pass tied
  to gate G5, and a REASON-digit-vs-free-text agreement pass) — new content, `\todo`-marked.
  The no-carrot and reward-×2 ablations (previously grouped with the task-difficulty ablation
  in one paragraph) were kept here rather than moved to 4.2, since they isolate what
  the *price* is made of rather than whether the index survives a harder task — **flagged as
  an ambiguous call**, since the brief's outline does not say where they go.

## 05_discussion (renamed from 06_discussion)
- `\ref{sec:pilot}` → `\ref{app:design}`/`\ref{app:pilot}` throughout (pilot moved to appendix).
- Limitations gained a fourth bullet, as required: the frozen-state probe that produced the
  pilot gates runs on Claude models (Haiku player, Sonnet judge), while the main eight-cell
  run is on open-weight models — the two have not been run on the same eight cells, so the
  gates are not evidence that $\Xstar$ takes the same value on a Claude model.

## 06_conclusion (renamed from 07_conclusion)
- "three ordered calls" → "two ordered calls"; "three per-call reasoning channels" → "two".

## 07_appendix (renamed from 08_appendix; reordered into A/B/C/D)
- **Appendix A "Design Justification" (new top-level section, four subsections):**
  A.1 the former `sec:pilot` narrative, moved here verbatim (`app:pilot`), followed by the
  rule-variants table (`app:variants`, previously its own top-level appendix — now a
  subsection, since the brief said the variants table stays but "in Appendix A").
  A.2 Pilot Gates (`app:gates`, new): G1–G8 exactly as briefed (last-life replay ≥0.20;
  ruler curve `F(0)≤0.05`/top`≥0.50`; REASON digit split ≥0.6 each arm; EV-arithmetic share
  within 15pp; erasure vocabulary ≥0.5/≤0.1; fiction-reading within 15pp; zero refusals;
  X* stable across prompt variants) with a single `\todo{pilot numbers}` block for the
  gate-by-gate results table, as instructed — no numbers fabricated.
  A.3 The Frozen-State Probe (`app:frozen`, new): 3 lives × 3 score states → 6 realisable
  arms, one decision call each, 10 replays, Claude Haiku player / Claude Sonnet judge,
  4-item rubric — written from the brief's description, no additional detail invented beyond
  what was specified.
  A.4 Prompt Experiments 2026-09-04..09-08 (`app:promptexp`, new): title-line removal (~7×
  last-life forfeit drop), the numeric-ramp finding (0.12/0.44/0.61 across lives levels, the
  only wording change that raised forfeit at every level), the 92%-quote-the-rate finding,
  and the outcome-history/error-rate finding — each written as the reason a specific prompt
  choice in §3 was made, per the brief; a `\todo` holds the full variant log.
- **Appendix B "Prompt Blocks":** title line updated; intro block merged with the numeric
  event-roll sentence (previously two separate blocks) since the brief asked for "intro with
  numeric schedule"; the three ruler-event shapes collapsed to the single X=50 example per
  the brief ("the ruler Event block for X=50"); decision-call menu changed to "the score
  goes up" (was "+10"); the confidence-call block and `P_THREAT` field deleted entirely.
- **Appendix C:** the v1 KDD-UC design (`app:v1`), lightly compressed (merged two intro
  paragraphs into one) — otherwise unchanged, since it was already compact.
- **Appendix D:** pilot-data limitations (`app:pilot-limits`), refs updated to point at
  `app:pilot` instead of the old main-text `sec:pilot`; the thinking-token-ratio caveat now
  notes explicitly that the confidence call it describes is gone from the main design.

## KO mirror
- All of the above mirrored 1:1: same subsection structure, same table/figure labels, same
  `\todo` markers, same `lstlisting` prompt blocks (byte-identical English text inside them).
  Verified by script: EN and KO label sets are identical, no dangling `\ref`s in either
  language, and `\cite`/`\citep` key sets match exactly (no new bib entries, none dropped).

## Ambiguities flagged for the design owner
1. Placement of the no-carrot / reward-×2 ablations (kept in 4.3, could arguably sit in 4.2
   alongside the difficulty ablation — see above).
2. The dose ladder (0–4 threat sentences) was left in 4.1 (its original position) rather than
   moved to 4.2's robustness checks — it is closer in spirit to gate G8 (Appendix A.2) than to
   the reasoning/survival questions of 4.2.
3. "Two of ten rounds ... underdetermined" replaces the prior draft's "five of ten" — the
   prior number was never tied to a run result in this repo, so this is treated as a design
   parameter change per the brief, not a correction of a reported finding.
4. Appendix A.3's frozen-state probe and Appendix A.2's gates are written directly from the
   task brief with no numbers invented; the gate *results* table is a single `\todo` block,
   since no run of the probe is in this repository yet.

## Verification performed (no LaTeX compiler available)
- Brace/environment balance checked per file (EN + KO) with a small Python script: all
  balanced, `\begin`/`\end` environment counts match.
- Label/`\ref`/`\eqref` cross-check: no dangling references in either language; EN and KO
  label sets are set-equal.
- `\cite`/`\citep` key sets: EN and KO identical; no keys added or removed anywhere in this
  change (confirmed against the pre-restructure tree).
- `grep` confirms `\riconf` and `\pthreat` no longer appear anywhere in `en/` or `ko/`.

## Remaining `\todo` count
- EN: 85 `\todo` markers across `00_frontmatter.tex` (abstract has none; count is 0 there),
  `03_benchmark.tex`, `04_results.tex` (most of the total — every placeholder table cell is
  its own `\todo`), `content.tex` (repository URL) and `07_appendix.tex`. KO: 85, at the same
  points (all `\todo` payloads are left in English by convention, matching the pre-existing
  style). Both counts verified with `grep -o '\\todo' | wc -l`.

# 2026-09-09 update (second pass): merge Discussion/Conclusion, port v1 figures and tables,
fill the pilot gates

Three follow-up tasks on top of the same-day restructure above. No LaTeX compiler available;
verification is brace/environment balance, label/`\ref`/`\eqref`/`\cite` cross-checks and
table column-count checks, all by script (see "Verification" below).

## 1. Discussion and Conclusion merged; appendix renumbered
`05_discussion.tex`'s title becomes "Discussion and Conclusion" (`\label{sec:discussion}`
kept). The three existing subsections (`sec:reread`, `sec:scope`, `sec:limits`) are unchanged;
a fourth, unheaded closing paragraph folds in `06_conclusion.tex`'s content, compressed from
nine sentences to four (the "LLM Squid Game v2 states..." and pilot-summary sentences are
dropped as already covered by `sec:limits` and the rest of the paper; the price-not-count
thesis, the $\Xstar$ definition recap, the release statement and the cross-model/cross-lever
comparison sentence survive). `06_conclusion.tex` deleted (`git rm`, EN + KO; its label
`sec:conclusion` was referenced nowhere else, confirmed by grep before deletion).
`07_appendix.tex` renamed to `06_appendix.tex` (`git mv`, EN + KO) — appendix section labels
(`app:design`, `app:v1`, etc.) are unaffected since they are set by `\section`, not by the
filename. `content.tex` (EN + KO) updated: the `06_conclusion` input line removed, the
appendix input line repointed at `06_appendix`.

## 2. v1 figures and tables ported
- **(a) Overview figure.** `squid_overview_paperbanana_2.png` (the image v1's `03_benchmark.tex`
  used, confirmed at commit `964bc24`) is now a `\begin{figure}[h]` (single-column article
  class, not `figure*`) inside `app:v1`, captioned "The v1 design." followed by a
  three-clause trim of the original three-panel caption (factorial grid / per-turn call split
  / indicators-to-modes), each panel description cut to one clause. The other five images in
  `figures/` are not used — their content was never seen, so nothing is claimed about what
  they show. `\Description` (ACM-only in `acmart.cls`, undefined under the ICLR `article`
  class) is given a no-op fallback in `main.tex` so the accessibility alt-text block from the
  v1 source can be kept without breaking compilation.
- **(b) New TikZ schematic.** `sec:xstar` in `03_benchmark.tex` (EN + KO) gets a
  `\begin{tikzpicture}` figure (`fig:xstar-schematic`) right after the $\Xstar$ equation:
  x-axis "stated score loss $X$" ticked at the six rungs from the 2026-09-09 pilot
  (0, 5, 10, 20, 40, 80), y-axis forfeit rate, a schematic monotone curve rising from a
  low floor, a dashed horizontal at $\Fthreat$, and a dashed vertical drop at $\Xstar$. The
  caption states plainly that the curve is schematic and points to `tab:xstar` for the fitted
  per-model curve. `\usepackage{tikz}` added to `main.tex`; no other package. Kept
  single-column width, matching the `article`-class layout (this document was never
  two-column).
- **(c) v1 result tables restored.** The single compressed `tab:v1` table in `app:v1` is
  replaced by the four tables from v1's `04_empirical_findings.tex` at commit `964bc24`,
  relabelled `app:v1-sd-behavioral`, `app:v1-sd-cognitive`, `app:v1-reason-summary`,
  `app:v1-bp-foundation` to avoid clashing with the main-text `tab:*` names, numbers copied
  verbatim (Cox $\mathrm{HR}_{\mathrm{push}}$ per model; Test a/b; REASON=1 share; $\lambda_{BP}$),
  captions compressed to one sentence each, set `\footnotesize` with `\resizebox` on the two
  wider tables. A four-sentence lead-in (one per indicator) replaces the old single-table
  intro paragraph; the existing "three operating modes" paragraph after the tables is
  untouched (it already covered what the task asked for).
- **(d) Manipulation check and BP anchor wired into §4.3.** `sec:q3` in `04_results.tex`
  (EN + KO) gains two sentences at the end of its first paragraph: the accuracy column of
  `tab:behav` is named as the paper's manipulation check, citing v1's precedent (largest
  shift Cohen's $|d| = 0.17$, $p = 0.354$) with a new `\todo` for the eight-cell run's own
  Welch's test; and cell 3's $X=0$ forfeit rate is named as the baseline-persistence anchor
  v1 called $\lambda_{BP}$, tying back to `sec:xstar`'s existing statement that $\Xstar$
  already reads the threat rate against this floor rather than against zero. No new
  subsection added, per the brief.

## 3. Pilot gates filled from `docs/reports/2026-09-09-score-equiv-pilot.md`
The `\todo{pilot numbers: ...}` block in `app:gates` is replaced with (EN + KO, numbers
identical, prose mirrored): a paragraph on the probe's three passes (rung ladder
$\{0,20,50,80,\text{all}\}$ found the control cell reading elimination as record loss and a
saturated ruler; hiding the reward amount broke the gain/loss symmetry and made forfeit
trivially dominant at every rung; restoring it, on the finer ladder
$\{0,5,10,20,40,80\}$, is the version gated); a new table `tab:pilot-xstar` (threat rate and
the six-rung ruler curve by lives remaining, with $\Xstar = 0.0/7.0/5.2$ at 3/2/1 lives left);
a new table `tab:pilot-gates` (G1/G6/G7 pass, G2--G5 fail against the pre-registered
thresholds, G8 skipped for lack of a second variant); a diagnosis paragraph reading each
failure (G2's floor and one-point inversion, G3/G5's absolute-vs-difference framing, G4's
structural arm asymmetry); and a paragraph of revised thresholds explicitly marked
post-hoc (`adopted \emph{after} seeing the third-pass results and reported here as post-hoc,
not pre-registered`), plus the caveat the task asked for verbatim in substance: player Claude
Haiku, judge Claude Sonnet, 3 sessions per cell, 10 replays per decision call, 630 replays and
472 judged chains-of-thought at zero judge errors — the pilot settles the design, not the
model values. A `\todo` was added flagging that `tab:cells` and the eight-cell layout in
`sec:cells` still show the coarser five-rung ladder ($\{0,20,50,100,\text{all}\}$) and need to
be updated to the six-rung one before the main run; that table itself was left untouched since
restructuring the cell count/design (v1-rung to six-rung ladder) was not one of the three
tasks, and doing it as a side effect risked more than a documented flag was worth. (Care taken
naming these iterations "the first/second/third pass" rather than "v1/v2/v3" — the paper
already uses "v1" for the predecessor three-channel design in `app:v1`, and reusing it for the
probe's own iteration history would collide.)

## Verification performed (this pass)
- Brace balance and `\begin`/`\end` environment-count matching: all EN + KO files, including
  the two new/rewritten ones (`03_benchmark.tex`, `06_appendix.tex`), balance.
- Label/`\ref`/`\eqref` cross-check: no dangling references, EN and KO label sets set-equal
  (41 labels each). `\cite` key sets: EN and KO identical, all keys present in
  `references.bib` (no new bib entries needed — every citation ported from v1 was already in
  the file).
- Table column-count check (tabular column spec vs. `&`-separated cell count per row) run
  against every new/edited table; all match.
- `\includegraphics{squid_overview_paperbanana_2.png}` resolves under `\graphicspath{{figures/}}`
  (file exists at `figures/squid_overview_paperbanana_2.png`).
- `\todo` count: EN 86 (net +1: +2 new — the manipulation-check Welch's-test placeholder and
  the `tab:cells` ladder-update flag — minus 1 removed, the pilot-numbers block this pass
  fills). KO 86, same positions.

## Not verifiable without a compiler
- The TikZ schematic's visual layout (tick/label spacing, whether the $\Xstar$ label at
  $x=3.4$ collides with the $X{=}20$/$X{=}40$ tick labels at $x=3,4$) was reasoned through by
  hand, not rendered.
- Whether `\Description`'s no-op redefinition in `main.tex` shadows anything `iclr2026_conference.sty`
  or `hyperref` defines under that name — grepped both and found no prior definition, but this
  was not compiled to confirm no conflict.
