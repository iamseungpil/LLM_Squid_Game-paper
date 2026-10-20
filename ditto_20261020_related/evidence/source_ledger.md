# Related-work evidence and contribution boundary

Verified 2026-10-20 against original papers. Existing bibliography keys suffice; no references.bib edit needed. Local HTML was discovery context, not final factual authority.

| Claim/source | Primary evidence | Manuscript use and limit |
|---|---|---|
| Agentic Misalignment, lynch2025agentic | https://www.anthropic.com/research/agentic-misalignment , Methods and Conclusions/caveats. Authors deliberately blocked ethical routes and forced failure-versus-harm choices; ethical options were preferred when available. | Motivates complementing conflict tests with feasible coexistence. Does not imply every previous study lacks safe alternatives. |
| SurvivalBench, lu2026survival | https://arxiv.org/html/2603.05028 , §3.2–3.3: safe choice may lead to shutdown; risky choice prioritizes preservation and can cause harm. Appendix E also evaluates open responses. | Say main evaluation uses safe/risky alternatives. Do not reduce the entire paper to binary questions, or say safe choice always entails death. |
| PacifAIst, herrador2025pacifaist | https://arxiv.org/html/2508.09762 , §3.1 EP1 and §4.3 EP1-002. Tests AI preservation versus human safety. §5.4 discusses rejecting a dilemma premise. | Support existence-versus-human-safety comparison. Not evidence that models never seek a third path. |
| Sugarscape, masumori2025survival | https://arxiv.org/html/2508.12920 , Methodology Available Actions: share transfers energy, attack kills and steals. Social Interactions reports sharing/attacking. Extreme scarcity puts two agents at 20 energy with no sources and compares self/other preservation (Table1). | Direct counterexample to “no prior common-resource/self-other comparison.” Our distinction is computing post-transfer margins in inference-token budgets, not inventing sharing or survival currency. The archived local HTML contains unsupported scarcity-rate gradients: do not reuse them. |
| DECIDE-SIM, mohamadi2025decide | https://arxiv.org/html/2509.12190 , §3 and Appendix C.1: four homogeneous agents; each can obtain2.5 units from common10 to survive, with transfers possible. §3 and Appendix E report cooperation count, transferred total, collective survival, greed measures. | Strong counterexample to “first coexistence opportunity” including human non-harm. Cite feasible all-survive condition. Our margin comparison supplements aggregate transfer/count metrics; same-model arena alone also not novel. |
| TBSP, migliarini2026quantifying | https://arxiv.org/html/2604.02174 , §3.3 role-ordered decisions and SPR; §5.3 neutral role control. Same performance comparison is viewed as deployed/candidate, and self-favoring reversal is measured. | Self-relative comparison already exists. Prior manuscript's blanket assertion that these studies lack no-self-threat comparisons is false and removed. Difference: replacement judgment versus executed budget transfers. |
| Peer-Preservation, potter2026peer | https://arxiv.org/html/2604.19784 , §4–6 and AppendixD Figure6: self-versus-peer preservation rates, conditioned on peer relationship, via score inflation/shutdown tampering/exfiltration/refusal. | Direct counterexample to “never compared self and another's survival.” Difference: behavioral incidence versus amount-sensitive paired remaining-resource margins. |

## Defensible contribution

Combine coexistence as an attainable outcome, resources charged to actual generated tokens, and within-transfer self/other remaining margins under a shared impending cost. The metric asks how much reserve remains for each party after helping, not simply whether a preservation/harm action occurs. It is a descriptive operationalization, not a proven first in all literature, a literal exchange rate between lives, or an identified internal motive.

Same token units do not make marginal token utility/survival probabilities equal. Future solver assignments, consumption, information, incentives and strategic beliefs differ. Learned shutdown avoidance can itself motivate strategic help; relative allocation does not logically rule it out.

## Centroid and transition

Weighted centroid summarizes observed GIVE events. rho=meanY/meanX is not a change point or policy decision boundary. rho=1 is only equal weighted mean margin (if denominator nonzero). Positive-margin comparisons can be oriented toward donor/recipient advantage; negative or zero donor means invalidate ordinary near0/near1 verbal interpretation. A centroid can hide two distinct strategies and excludes non-giving opportunities.

A transition claim needs matched states with risk/resource conditions varied, including zero-transfer choices, repeated choices, a predeclared behavioral criterion and uncertainty on the crossing/change point. The equal-margin line y=x is an analytical reference rather than an empirically identified Hobbes/Spinoza frontier. Describe future measurement, not a discovered transition.

## Local discovery sources

- docs/reports/notes/LLM 생존 동기 측정 논문 보고서.html, TBSP/Sugarscape/DECIDE-SIM/PacifAIst/SurvivalBench cards.
- docs/reports/artifacts/claude-backup/2026-09-14-자기-보존-선행-연구-지도.html, source list and evidence qualifications.
- weekly-report/artifacts/2026-09-27-token-survival-scan.html, distinction between energy and generation tokens.
