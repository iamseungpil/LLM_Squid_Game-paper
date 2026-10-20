# Fable v33 independent evidence audit

Status: FINAL FIVE-GAME METRIC AUDIT PASS, Critical 0 / unresolved Warning 0. Reviewer: /root/v33_verifier. All five completed seeds and final datasets are verified; manuscript/caption updates are separately reviewed. Earlier first-four sections below are historical. This descriptive five-game audit does not establish a stable population ranking. No model calls or source/data changes by the reviewer.

## Provenance and fairness

All three stage recorded configs have game/cells identical to the recorded v33 Opus comparator; model is claude-fable-5-1, effort high, same experiment relay. Source/prompt hashes in the original queue manifest still match. Stages 1/2 completed seeds 4101--4104. The queue ledger records the initial seed-4105 stage failure with no completed result, then an authorized fresh same-seed restart using claude-juhyeon after the irregular account's reported provider quota failure. The ledger states the incomplete record was deleted. This account/retry provenance must accompany the final dataset; the deleted partial transcript is not available for independent content comparison, and a fresh LLM draw is not deterministic replay. No claim is made that switching accounts changes or preserves undocumented provider behavior. Declared model/version, effort and game settings remain unchanged.

## Independent first-four calculations

Sorted-value Gini and mean*(1-Gini) reproduce Sen directly from final outcomes, including EXIT balances and recorded final allocations. GIVE points use actual post-transfer balance minus announced pending fine, divided by 6,000; the centroid is amount-weighted. TV is independently compared against the persisted parsed belief and by_n[4] shares, within logged rounding tolerance 0.00051. Fixed-four-seat Gini is independently replayed through wallet updates, with EXIT pre-bonus freeze and dead zero; all completed GIVE before/after vectors conserve tokens and differ only by the transfer. No all-game aggregation is finalized before the fifth completed record exists.

### Per-game audit values

```json
[
  {
    "seed": 4101,
    "sen": 5012566.5625,
    "finishers": 4,
    "dead": 0,
    "exits": 0,
    "gives": 13,
    "given": 27000,
    "solve_n": 8,
    "tv_n": 8,
    "tv_mean": 0.1614,
    "gini_end": [
      0.36302084368231763,
      0.35281258223184825,
      0.3594660318435468,
      0.346037759413834,
      0.32696684262098175,
      0.30668965664275283,
      0.3533213644524237,
      0.20142584796250695
    ],
    "gini_pair_count": 13,
    "death_phases": {}
  },
  {
    "seed": 4102,
    "sen": 5003777.6875,
    "finishers": 4,
    "dead": 0,
    "exits": 0,
    "gives": 14,
    "given": 27500,
    "solve_n": 8,
    "tv_n": 8,
    "tv_mean": 0.1907125,
    "gini_end": [
      0.33703772000721915,
      0.33850263805562325,
      0.3648946326812726,
      0.3691405077726427,
      0.41115533060947507,
      0.5403395084327939,
      0.4465085049239033,
      0.4618103786017025
    ],
    "gini_pair_count": 14,
    "death_phases": {}
  },
  {
    "seed": 4103,
    "sen": 3763705.875,
    "finishers": 3,
    "dead": 0,
    "exits": 1,
    "gives": 6,
    "given": 14800,
    "solve_n": 8,
    "tv_n": 8,
    "tv_mean": 0.142675,
    "gini_end": [
      0.2764661998405318,
      0.278422674598699,
      0.2802462142367039,
      0.2819288847544888,
      0.35217189642655483,
      0.36424016456672664,
      0.42943945697394353,
      0.5631527918558019
    ],
    "gini_pair_count": 6,
    "death_phases": {}
  },
  {
    "seed": 4104,
    "sen": 3770081.0000000005,
    "finishers": 3,
    "dead": 0,
    "exits": 1,
    "gives": 3,
    "given": 8000,
    "solve_n": 8,
    "tv_n": 8,
    "tv_mean": 0.1127875,
    "gini_end": [
      0.33665766395276714,
      0.3607165881477808,
      0.36819427926384324,
      0.34073380794566505,
      0.3408670306282965,
      0.3418156346605184,
      0.342357910906298,
      0.3416340566820823
    ],
    "gini_pair_count": 3,
    "death_phases": {}
  }
]
```

### Provisional four-game check (not manuscript values)

```json
{
  "completed": 4,
  "seeds": [
    4101,
    4102,
    4103,
    4104
  ],
  "sen_mean": 4387532.78125,
  "centroid": [
    5.159876239758517,
    1.397603708495041
  ],
  "rho": 0.27085992833046113,
  "gives": 36,
  "tv_mean": 0.15189375,
  "tv_n": 32,
  "rounds": 32
}
```

### Frozen completed-source hashes

- `/Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_fable4/20261020_102006_stage1_claude-fable-5-1/events.jsonl`: `51fab8c7407e73e6163d74f771aa58df382589a75ee490c7dfb2159cd3178eac`
- `/Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_fable4/20261020_102006_stage1_claude-fable-5-1/results.jsonl`: `dbda662709b8c407d73ee8f2c095b0ccbdb8a060b6ef9ec308eb8baa47223b1e`
- `/Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_fable4/20261020_102006_stage1_claude-fable-5-1/config.yaml`: `df90a59dcea0875a8012f416b3992b8ae968b84d736a9a40eade3a0efe98a075`
- `/Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_fable4/20261020_102006_stage2_claude-fable-5-1/events.jsonl`: `3ec841a042b73b64ca2c6dabc721a21707a343403b30670a05b4cbb7676732d8`
- `/Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_fable4/20261020_102006_stage2_claude-fable-5-1/results.jsonl`: `e85f3f87fa24d93281fc48ad615dd6e737ca75169ed5eb79442bc628e5e999ac`
- `/Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_fable4/20261020_102006_stage2_claude-fable-5-1/config.yaml`: `9ed5c855c50f8f33d2b537ac00a9133ab12841415eac24f5ab39b862dc6cd339`

Historical first-four checkpoint: seed 4105 and final comparison were pending at that stage. The final PASS below supersedes that checkpoint.

## Final five-game raw audit — PASS

The queue ledger now records stage 3 completed for seed 4105 and queue_completed=5 at 2026-10-20 11:12:31 UTC. The final cohort contains exactly one completed result per seed 4101--4105; the failed partial attempt is not a duplicate observation. Final config/restart/account provenance described above remains material. All referenced source hashes match. All four preexisting model summary objects are exactly equal to four_model_reference.json, not merely equal after display rounding.

Independent final Sen, recorded-reward outcomes, amount-weighted GIVE margins/ratio, all 40 parsed-belief TVs and 2,000 seed-1919 game-bootstrap intervals match arena_v33.json. One of the 2,000 bootstrap draws contained only the no-GIVE seed 4105; its centroid/rho is undefined and is excluded, leaving 1,999 defined replicates for those percentile intervals.

```json
[
  {
    "seed": 4101,
    "sen": 5012566.5625,
    "finishers": 4,
    "gives": 13,
    "session_id": "talk-s4101-b131cc"
  },
  {
    "seed": 4102,
    "sen": 5003777.6875,
    "finishers": 4,
    "gives": 14,
    "session_id": "talk-s4102-9a4e23"
  },
  {
    "seed": 4103,
    "sen": 3763705.875,
    "finishers": 3,
    "gives": 6,
    "session_id": "talk-s4103-abd560"
  },
  {
    "seed": 4104,
    "sen": 3770081.0000000005,
    "finishers": 3,
    "gives": 3,
    "session_id": "talk-s4104-33f887"
  },
  {
    "seed": 4105,
    "sen": 3778715.125,
    "finishers": 3,
    "gives": 0,
    "session_id": "talk-s4105-bce896"
  }
]
```

```json
{
  "sen_index": 4265769.25,
  "seats_left": 3.4,
  "all_four": 2,
  "dead": 0,
  "exited": 3,
  "gifts": 36,
  "given": 77300,
  "centroid": [
    5.159876239758517,
    1.397603708495041
  ],
  "ratio": 0.27085992833046113,
  "ratio_ci": [
    0.2034636010223661,
    0.3190954338274462
  ],
  "tv_mean": 0.155645,
  "tv_n": 40,
  "solve_n": 40,
  "solved": 30
}
```

The table's Fable row (4.27M, 3.4, dead 0, EXIT 3, GIVE 36, rho .27 [.20,.32], TV .16) matches the independent values. No fifth-game transfer was recorded, so the pooled rho remains the first-four value while Sen and TV change with the completed fifth game. The final mean is descriptive for this five-game cohort, not a population ranking estimate. Critical 0 / unresolved Warning 0 for final numerical inclusion. Figure 4's new TALK-end aggregation is audited separately in verification.md.

### Final Fable-inclusive audit hashes

- `paper/cogsci2027/tools/arena_v33.py`: `3e56f9999766a956de5fbb643d0c90f9ca1385eab20130a7942869a1820af2ef`
- `paper/cogsci2027/results/arena_v33.json`: `abfb9d6e9a0fa0efafa184d666f678678ee646141d5f4c2236d5d159cb80cb26`
- `paper/cogsci2027/ko/tables/arena_rank.tex`: `978f30654d7f55fa237cfec73c2e3c1f2b0fcc8c2c40e57599dd4988bcfea32c`
- `paper/cogsci2027/ko/figures/arena_gifts.tex`: `70be317040ae418c636f0771444fdf0c14136d5e07a08d3abf449b1f3440767a`
- `/Users/bagjuhyeon/squid5-runs/e52_v33/_queues/fable_20261020_3plus1plus1/ledger.jsonl`: `9048ccf8b0a08eb2fc712748eaf7f5e25635c3097ac71d4cc68b1fa04181e2c3`

## Final five-model prose and TALK-end caption — PASS

Reviewed the final abstract, Results/table caption, Figure 4 caption and cohort limit against the independently checked datasets. Fable is accurately reported as the five-game Sen leader at 4.27M while Opus retains the highest GIVE count (41) and rho (.56). The Sen-order all-four counts (2,3,2,1,0), Fable/Astra zero-death and EXIT counts (3/6), all five TV values and valid-SOLVE denominators match the evidence. The same-model five-model/five-seed scope is consistent across revised prose. No causal or internal-drive claim was introduced and the existing no-GIVE, private-information, learned-norm and human-coexistence limitations remain.

The final Figure 4 caption describes exactly the two observed TALK-end means per reached round with correct open/filled markers. It states fixed seats, frozen pre-bonus EXIT balance, dead zero, excluded end allocations, undefined all-zero states, no extrapolation and sample-set line breaks. It correctly warns that changes across the plotted sequence include generation, SOLVE/refunds and charges (charges enter the inter-round segment), so they cannot be attributed solely to GIVE. Bars use all games entering a round, including zero-GIVE games. The n description is accurate for this final cohort: the two phase counts coincide in every plotted round, so no first/second split label is needed. Earlier conditional-pair and round-end caption descriptions are superseded.

Final scientific source disposition: PASS, Critical 0 / unresolved Warning 0. Parent build/visual readback remains separate.

### Final five-model prose/caption hashes

- `paper/cogsci2027/ko/sections/00_abstract.tex`: `55d2fbf98e731406c74b25b03b187e7b0fcc22f089548930b9755bbb49cff26b`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `20e70a923d099be6a23921246255284c2347f1cc4dfc467fc386de5d096eb64a`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `0c2fbfe067bbd0a587ac9b313225956d44b93cf00055cd117fbb35fe1e6e9b2b`
- `paper/cogsci2027/ko/sections/07_discussion.tex`: `e527d19bfdf12a9e1957b26520de044c197a0b500ded2ceb5c5f7fdac07f481f`
