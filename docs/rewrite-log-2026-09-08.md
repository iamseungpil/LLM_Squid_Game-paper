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
