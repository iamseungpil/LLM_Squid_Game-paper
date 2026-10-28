# an5: review-loop analyses (10-28)

Scripts read the parsed v33 logs `../audit6/G.pkl` and `../audit6/elig.json` (kept outside the repo; `audit6/elig.json` is
also copied to `../audit/elig.json`), the paper's `results/arena_token_allocation.json`, and the code repo's
`web/data/runs/e52_v33`, `e52_v34`. Run in order: `a5.py`, `a6.py`, `a6b.py`, `a7.py`, `a8.py`, `a9.py`, `a10.py`,
`abl.py`, `kappa.py`, then `make_figs5.py`.

- `a9.json` holds the single margin definition the paper uses (margin at the start of the decision window).
- `kappa.json` compares two independent LLM coder sessions (`coder_A.json`, `coder_B.json`) on `code_items.json`.
