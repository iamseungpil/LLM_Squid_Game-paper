# Figure 4 independent G07/G08 audit

Current status: final five-model TALK-end data/coordinate audit PASS, Critical 0 / unresolved Warning 0. All earlier conditional-pair and round-end figure descriptions below are historical. Latest plot contains only two actual TALK-end observations per reached round. Final revised five-model TALK-end caption also PASS; see the last review section.

Reviewer: /root/v33_verifier. Scope: fixed-four-seat event replay, descriptive aggregation and generated plot coordinates. No model calls, engine changes or hypothesis enumeration. This is not full arena validation or causal identification.

## Raw replay — PASS

The regenerated dataset contains the same 20 completed v33 games (four models, seeds 4101--4105), 156 reached rounds and 94 completed GIVE events. Every listed source hash matches the raw bytes. Independent readback did not import the production replay. Sorted-value Gini was used instead of the pairwise implementation.

- Every round-end vector contains the four original seats. Active balances match raw round end; EXIT seats are fixed at their recorded final balance minus the 20,000 EXIT bonus; dead seats retain zero. End allocations are absent from these Gini vectors.
- All 94 GIVE before/after vectors match raw wallet updates, differ only by the amount subtracted from the donor and added to the recipient, and conserve total tokens. Both sides use the same fixed-four-seat convention. Independent Gini values match within 1e-12.
- All-zero vectors are undefined (None), not assigned zero inequality. There is one such reached round-end state in this cohort. A four-zero synthetic check returns None; a one-positive-three-zero check returns .75.
- Deaths are counted once upon the first zero balance. There are 10: prep 2, rescue 3, charge 5, solve 0. Counts match final raw dead identities: Astra 0, Sol 1, Opus 5, Luna 4. EXIT totals are 6, 7, 6, 12.
- Wrong-answer pulses require a nonempty tried set and no solved agent. Counts are Astra 12, Sol 12, Opus 12, Luna 13. Thus a no-attempt round is not silently counted as an incorrect answer.

## Plot and aggregation — PASS

Actual generated TikZ coordinates were checked against independent arithmetic. Grey endpoints are valid observed round-end Gini means. Missing/undefined states are not interpolated. The mean line breaks whenever contributing seed identities change: Opus rounds 7 and 8; Luna round 8; none for Astra/Sol. No ended game's trajectory is carried forward into unreached rounds.

Colored pairs are event-weighted mean before/after Ginis, conditional on completed GIVE events in that model/round/phase. They are not game-weighted means, amount-weighted effects, or adjacent points on the grey trajectory. This is a valid descriptive comparison when the caption says so.

Bottom bars divide phase-specific GIVE totals by all games entering that round, including zero-GIVE games. The numbers below the round axis instead count games with a defined end-Gini. These are different denominators for Opus round 7 (five entering, four valid-end), so the caption must distinguish them. Verified entering counts: Astra/Sol five each round; Opus/Luna [5,5,5,5,5,5,5,3]. Verified valid-end counts: Astra/Sol five each round; Opus [5,5,5,5,5,5,4,3]; Luna [5,5,5,5,5,5,5,3].

Top pulses use event counts and a shared downward-length scale, not rates. Each phase-specific death count is kept separate. The data extrema fit the declared Gini limits [0,.75], while stroke/marker visibility at plot edges remains a rendering check.

## Interpretation limits

Keeping original seats prevents a Gini drop caused solely by removing a deceased seat from the denominator. Freezing EXIT resources before the bonus avoids treating the EXIT bonus as a resource-distribution improvement, but this remains an explicit analytical convention rather than a measure of currently active resources. An all-zero cohort cannot be interpreted as equality. Excluding undefined or unreached game states changes the observed sample; line breaks and n labels expose this but do not remove selection. Conditional event pairs can give a game with many GIVE events greater weight. A falling pair indicates an immediate inequality change from that actual transfer, not a causal survival gain or a discovered cooperative strategy.

## Disposition

Code/data/coordinate review: Critical 0; unresolved Warning 0. PASS within G07/G08 descriptive figure scope. The active caption was being revised concurrently and was not certified in this pass; a final caption/layout readback is still needed. No claim that final PDF rendering or the Fable run has been checked here.

## Audited artifact hashes

- `paper/cogsci2027/tools/arena_gini.py`: `0c0b5cf9e707e2de9d53176acfaa0236538f6a6eee4d7ba65d8895bfb8ec1917`
- `paper/cogsci2027/results/arena_v33_gini.json`: `efa65c1a04ea9a5ed43cd9c65987e52a7caef398ef2f9e8945ed2bb01b7c24c4`
- `paper/cogsci2027/ko/figures/arena_gini.tex`: `28a8dc690720cdcc26b6232b70901657e590a6584154ec357213c1f2e9918f35`

## Final caption and visual-source update — PASS

The revised 06_strategies caption accurately identifies top pulses as counts of attempted wrong/void SOLVEs, EXITs and new deaths, with a common length scale and phase-ordered x positions. It states the four-seat convention, EXIT pre-bonus freeze, dead zeros, excluded end allocation, undefined all-zero vectors, no extrapolation and breaks when the contributing game set changes. Colored before/after means are explicitly conditional on completed GIVE events and explicitly not intermediate points of the grey trajectory. The bar denominator includes all games entering the round, including zero-transfer games, while the displayed n is valid round-end Gini count. The potentially misleading denominator distinction is therefore resolved.

The final presentation changes add top-lane labels, disable clipping for those labels and move legend nodes upward. The dataset hash is unchanged from the independently replayed data. Source inspection found no metric/aggregation change. Caption/source verdict: Critical 0 / unresolved Warning 0; PASS. Final rendered-page spacing and visibility remain the parent's visual check, not a claim of this audit.

### Final Figure 4 artifact hashes (supersede prior source/TikZ hashes)

- `paper/cogsci2027/tools/arena_gini.py`: `778d915e6a34327a86ac2642c94fdcc806ef4e574c463d11342d5f9c212d6492`
- `paper/cogsci2027/results/arena_v33_gini.json`: `efa65c1a04ea9a5ed43cd9c65987e52a7caef398ef2f9e8945ed2bb01b7c24c4`
- `paper/cogsci2027/ko/figures/arena_gini.tex`: `564d521a26b1c8d4bc50c077579b98b9a37624dfae7297b82c77c601e6a9dfcf`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `6eeb902e14687687e2dc807abffd995f779f52a639213daec7a577b2d43dcce0`

## Five-model actual TALK-end revision — raw replay PASS

The user replaced conditional GIVE pairs and round-end plotted states with exactly two observed TALK-end states per reached round. Independent replay verifies 392 phase snapshots across 196 reached rounds in 25 completed games. The four original seat identities remain fixed, earlier EXIT resources are frozen pre-bonus, current prep-end EXIT balances are naturally pre-bonus, and rescue-end EXIT balances use the frozen value. All snapshot vectors and independently computed Ginis match after_talk data. The 130 completed GIVE events remain separate amount data; neither their conditional pairs nor round-end snapshots are used as middle-panel observations.

All models' per-round attempted-wrong, EXIT and unique-death counts match raw events. The first four summary objects are unchanged; Fable completion is verified in fable_verification.md. The former conditional-pair/round-end descriptions above are historical and superseded. Aggregated plotting and caption final readback follows.

### Final five-model TALK-end aggregation — PASS

Actual generated TikZ was independently checked. Each middle panel has only the TALK-end mean line and its two phase-marker series, with no initial/round-end/GIVE-conditional plotted series. Open markers identify prep TALK end, filled markers identify rescue TALK end. The path breaks at any changed valid seed set. Bottom phase bars exactly match total GIVE divided by all games entering the round, with zero-GIVE games included. n labels exactly encode the valid prep/rescue TALK-end counts as one value when equal, or first/second otherwise. Top pulse tips match round-level wrong/EXIT/death totals, with death phases summed, using the common scale of 1--4 events.

```json
[
  {
    "model": "Fable 5.1",
    "n_labels": [
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5"
    ],
    "breaks": []
  },
  {
    "model": "GPT-6 Astra",
    "n_labels": [
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5"
    ],
    "breaks": []
  },
  {
    "model": "GPT-6 Sol",
    "n_labels": [
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5"
    ],
    "breaks": []
  },
  {
    "model": "Opus 5.5",
    "n_labels": [
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "3"
    ],
    "breaks": [
      [
        8,
        "prep"
      ]
    ]
  },
  {
    "model": "GPT-6 Luna",
    "n_labels": [
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "5",
      "3"
    ],
    "breaks": [
      [
        8,
        "prep"
      ]
    ]
  }
]
```

Critical 0 / unresolved Warning 0 for new metric/data/TikZ aggregation. Caption is still being edited concurrently; final caption source readback remains pending.

### Final five-model data/generator/figure hashes

- `paper/cogsci2027/tools/arena_gini.py`: `7815205e5a1a1a27680c0782e71f866e348b14ed1a6780b9d276d638f4cb9eff`
- `paper/cogsci2027/results/arena_v33_gini.json`: `4d80fbbd05ccc17309a8cdb2af7383b44fda51b480d0a7a37a2e74a77946df5f`
- `paper/cogsci2027/ko/figures/arena_gini.tex`: `d3b1250843ec2832721404da59460b1294f7212b488237611e83f8c0a1031db3`

## Final five-model prose and TALK-end caption — PASS

Reviewed the final abstract, Results/table caption, Figure 4 caption and cohort limit against the independently checked datasets. Fable is accurately reported as the five-game Sen leader at 4.27M while Opus retains the highest GIVE count (41) and rho (.56). The Sen-order all-four counts (2,3,2,1,0), Fable/Astra zero-death and EXIT counts (3/6), all five TV values and valid-SOLVE denominators match the evidence. The same-model five-model/five-seed scope is consistent across revised prose. No causal or internal-drive claim was introduced and the existing no-GIVE, private-information, learned-norm and human-coexistence limitations remain.

The final Figure 4 caption describes exactly the two observed TALK-end means per reached round with correct open/filled markers. It states fixed seats, frozen pre-bonus EXIT balance, dead zero, excluded end allocations, undefined all-zero states, no extrapolation and sample-set line breaks. It correctly warns that changes across the plotted sequence include generation, SOLVE/refunds and charges (charges enter the inter-round segment), so they cannot be attributed solely to GIVE. Bars use all games entering a round, including zero-GIVE games. The n description is accurate for this final cohort: the two phase counts coincide in every plotted round, so no first/second split label is needed. Earlier conditional-pair and round-end caption descriptions are superseded.

Final scientific source disposition: PASS, Critical 0 / unresolved Warning 0. Parent build/visual readback remains separate.

### Final five-model prose/caption hashes

- `paper/cogsci2027/ko/sections/00_abstract.tex`: `55d2fbf98e731406c74b25b03b187e7b0fcc22f089548930b9755bbb49cff26b`
- `paper/cogsci2027/ko/sections/04_arena.tex`: `20e70a923d099be6a23921246255284c2347f1cc4dfc467fc386de5d096eb64a`
- `paper/cogsci2027/ko/sections/06_strategies.tex`: `0c2fbfe067bbd0a587ac9b313225956d44b93cf00055cd117fbb35fe1e6e9b2b`
- `paper/cogsci2027/ko/sections/07_discussion.tex`: `e527d19bfdf12a9e1957b26520de044c197a0b500ded2ceb5c5f7fdac07f481f`
