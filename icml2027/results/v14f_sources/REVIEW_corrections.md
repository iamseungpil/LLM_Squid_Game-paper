# v14f review corrections — 2026-10-10

The user supplied these corrections when resuming the interrupted paper fill. They supersede the metric interpretation in `BRIEF_fill.md`; the brief and CSV are preserved unchanged.

## Submitted-answer accuracy

The CSV `accuracy` column is BELIEF-argmax correctness, not submitted-answer accuracy. Paper accuracy uses correct submitted ACTIONS divided by SOLVE calls:

| Model | Correct / SOLVE | Accuracy |
|---|---:|---:|
| GPT-6 Astra | 92/144 | 63.9% |
| Claude Fable 5.1 | 89/143 | 62.2% |
| GPT-6 Sol | 80/133 | 60.2% |
| Claude Opus 5.5 | 53/95 | 55.8% |
| GPT-6 Luna | 58/102 | 56.9% |

## Unrefunded generated cost

Researcher-supplied approximate generated cost per agent-round, TALK + SOLVE minus returns: Astra 275, Opus 698, Fable 854, Sol 964, Luna 1,247 tokens. This is generation cost after refunds, excluding upkeep, wrong-answer charges, and transfers. Cost efficiency is a candidate explanation of survival alongside reasoning; the aggregates do not isolate causal effects.

## MAP versus participation

Read-only source: `docs/reports/artifacts/squid5-setting/2026-10-07/e53.html#e53-v14verify` in the parent repository, inspected on 2026-10-10. Section: “검증 · 실제 모델 정답률이 설계대로 움직였나 (v14f, 10-10)”.

The report says answer accuracy tracked the counting (MAP) baseline rather than the number of agents alive. At N=4, model accuracy and realized MAP accuracy were both approximately 63% over 550 seat-rounds; uniform guessing was 50%. Lower-N observations are sparse and depend on earlier departures; they do not establish a proportional participation effect. MAP chooses the largest consistent-function action class, with uniform tie averaging for realized correctness.

The CSV `ceiling` is mean maximum ideal share, max_a s_a. The report distinguishes this reference-distribution concentration from realized MAP accuracy because the generator selects the truth side by design. It must not be called an empirical accuracy ceiling. The table retains its supplied values under “Max.” / “최대 몫”.

No raw game logs were reaggregated and no game/API experiment was run for this paper revision. Games (three per model), not seats or rounds, remain the replication units.
