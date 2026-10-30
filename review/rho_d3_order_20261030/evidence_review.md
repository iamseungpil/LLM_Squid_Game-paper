# D.3 rho and Appendix 0 Figure 4(f) review

Status: PASS. No factual or visual blocker found. Final manuscript PDF build verification is outside this read-only review.

Reviewed `tools/table_d3_rho_20261030.py`, `results/table_d3_rho_20261030.json`, `ko/tables/arena_rank.tex`, the plotting changes, the updated Figure 4 PNG, and writer drafts `appendix.tex` and `appendix0.tex` in this review directory. Only this review file was written.

## D.3 numerical verification

Independently reconstructed each completed GIVE's post-transfer giver and recipient margins from `raw_case_index.json`: round-start participant count determines the fine; rescue margins subtract each agent's pending fine. Negative margins remain unchanged. Computed five per-game numerator/denominator pairs for each model, including zero pairs for no-GIVE games. The point estimate pools the five pairs rather than averaging per-game ratios.

Independently reproduced 2,000 bootstrap draws of five whole games with replacement using seed 1919, reset for each model, and the documented legacy order-statistic percentile rule. Every point estimate, interval endpoint, and retained draw count matches the output JSON.

| Model | Pooled rho | 95% interval | Retained draws | Omitted no-GIVE draws |
|---|---:|---|---:|---:|
| Fable | 3.677598 | 3.133859–4.948224 | 1999 | 1 |
| Astra | 2.700880 | 2.242573–3.784678 | 2000 | 0 |
| Sol | 4.237786 | 3.062744–10.251096 | 1976 | 24 |
| Opus | 1.833345 | 1.356759–3.545770 | 1999 | 1 |
| Luna | 3.171678 | 2.130107–8.159209 | 1986 | 14 |

All omitted draws contain no GIVE; no sampled draw with GIVE had zero denominator. The process JSON source hash matches the report. The generated table rounds these values correctly. EXIT, transfer-volume/count, and JS columns retain their existing historical source values.

The D.3 writer caption identifies the current giver/recipient formula, pending-fine adjustment, pooling, five-game bootstrap, 2,000 draws, seed 1919, and omission of undefined draws. Its equation reference `eq:completion-rho` exists in `ko/sections/02_arena.tex`.

## Figure order and captions

- Descending current pooled rho is **Sol, Fable, Luna, Astra, Opus**. All three Figure 4(f) plots use this order in the source and inspected PNG.
- Corresponding Gini valid-game counts are **4/5/3/4/3**; Sen and mean tokens retain five games each. Plot footnote and writer caption agree.
- Only the order changes: resource values, individual-game points, scales, missingness, and aggregation remain unchanged. Figure 4(e) retains its existing model order as requested.
- `draw_panels(..., order=None)` uses the original `ORDER` by default. All means, individual-game points, and tick names use the same selected order; existing callers preserve their original output ordering.
- The PNG has no observed label collision or clipping. The writer's changes are confined to D.3's heading/caption and Figure 4(f)'s order/count descriptions. They introduce no claim that higher rho caused Sol's exits, shutdowns, or terminal resource distribution.

No correction required from this review. No style impression scoring performed.
