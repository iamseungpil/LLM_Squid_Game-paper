# Compact Figure 4 main-text integration: bounded evidence audit

Status: **PASS; no factual or asset-level layout blocker identified.** Review covers the requested G02/G07/G08 measurement/interpretation boundaries, figure preservation, and source-edit scope. Final manuscript pagination, rendered-page readability and build references remain with the orchestrator. Only this report was written.

## Task and source boundary

The repository README describes script-generated figures and retention of full/body-only manuscripts and figure originals. This task remains a Korean main §3.2/Figure 4 integration with a corresponding Appendix 0 update; it does not change methods, Table 1, other main sections, or the historical data. Older README metric/build details were not treated as the authority for current numerical definitions.

Compared actual `03_analysis.tex` with this task's original backup:

- §3.1 and all preceding text are byte-for-byte unchanged.
- Table 1, including caption, headers, values and group structure, is byte-for-byte unchanged.
- Main Figure 5 and the subsequent §3.3 content are byte-for-byte unchanged.
- §3.2 contains no reference to Appendix 0 or another appendix. Its figure and table references are main-text labels and match the current content.
- The two removed 33-agent crisis paragraphs appear verbatim under the appendix heading `이전 기준의 위기 33명 분석`.

## Data and populations

The four previously independently audited caches—ASK/GIVE responses, low-margin agent-rounds, integrated terminal metrics, and GIVE/ASK totals—are byte-identical to HEAD. No raw-data recalculation or metric change occurs in the compact compositor.

Panel (a) retains 192 SOLVEs, 491 eligible EXIT windows, and **2,887** tick-start-peer-eligible prep/rescue responses. ASK counts are 52/19/0/0 out of 260/610/759/1258 responses, and GIVE counts are 9/5/36/70. These remain **71 ASK-containing responses with 90 requests** and **120 GIVE-containing responses with 130 transfers**. The main text defines one-or-more executed actions per response and correctly rounds the low-margin GIVE rate to 3.5%, while ASK is 3.1% at 1–2 and 20.0% below 1. Pending fines and phase inclusion are stated correctly.

Panel (b) retains **28 agent-round observations, 25 agents, 14 games**, selected at the first prep call with L<1, another participant, and no solver role. ASK/receipt/EXIT are followed until that round ends across both prep and rescue. Model denominators remain 9/5/5/3/6. Color and counts match: ASK green, actual receipt blue, EXIT orange. Overlap, repeated observations, 3–9 observations per model, and events after margin recovery are acknowledged. Shutdown bars are absent as requested, without altering stored data.

The populations are not conflated:

- Main Figure 4(b): 28 low-margin non-solver agent-rounds.
- Unchanged Table 1 crisis-receipt column: historical 33-agent post-result crisis cohort, with its 41−4−2−2 selection stated in the main text.
- Appendix crisis follow-up: revised 34-agent cohort, explicitly distinguished from the preserved historical 33-agent analysis.

## Preserved plots and compact geometry

The compositor captures existing artists, changes positions/fonts and panel letters, exports vector blocks, and reassembles them. All four manifest hashes match their PDFs. The canvas is **532.8 × 209.88 pt**, and 209.88 = 190.8 × 1.10 exactly.

Inspected the current compact PNG:

- Panel (a)'s four margin plots retain all numerator/denominator labels and bands.
- Panel (b) retains every percentage and k/N annotation, including zero values and Astra 100% EXIT.
- Panel (c)'s shared phase legend is readable and separated from both plot titles. Unhatched light segments mean prep; darker hatched segments mean rescue for both GIVE and ASK. Gross amounts, units, model order and stack sums remain unchanged.
- Panel (d) retains the audited terminal means and actual min–max whiskers, Gini missingness, units and descending-rho model order. No observed mark, label or whisker is clipped. The common order cue is correctly relabeled for (c,d).

No observed label overlap or missing original annotation in the compact asset. The vector asset remains available for manuscript-scale inspection.

## Main and appendix prose alignment

The main caption's (a–d) mapping matches the new figure. Nearby §3.2 prose supplies the otherwise shortened caption's measurement units, tick-start eligibility, pending-fine adjustment, agent-round follow-up, positive action definition, total-versus-mean aggregation, min–max interpretation, and Gini valid-game counts. The caption and text no longer describe hatching as return-direction transfers or terminal scatter points as individual games.

Main §3.2 remains self-contained: panel (c) means five-game gross GIVE/ASK totals, requests are not received support, and panel (d) means terminal in-arena balances with EXIT/shutdown set to zero, excluding prizes/EXIT bonuses. Min–max lines are explicitly not confidence intervals. The surviving old qualitative language about preserving one's margin is not newly strengthened into internal motivation or a causal explanation.

Appendix 0 includes the same compact figure with corresponding (a–d) references and preserves fuller counts and the historical crisis paragraphs. No mismatched old panel reference or newly introduced causal claim was found.

No correction required within this bounded review. No style impression score assigned.
