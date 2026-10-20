"""Arena numbers for the CogSci draft, from the raw e52 runs (v20 public balances, v21 private balances).

For each model:
  - gifts: every completed GIVE as (giver slack, receiver slack, amount); slack = (tokens - fine already
    announced to that seat) / fine, taken right after the transfer, as in token-review-v20/build.py
  - centroid: amount-weighted mean of (giver slack, receiver slack), and its ratio receiver / giver;
    95% intervals by resampling games
  - tv: the solver's TV distance (and KL(shares || BELIEF)) between BELIEF and the rule-consistent action shares, overall and
    split at slack < 2 (two misses from shutdown) vs >= 4
  - score per seat: all games' (5,000,000 per surviving seat + survivors' tokens) / (games x 4)
Writes results/arena_<label>.json. Usage: python3 arena_stats.py <runs_root> <label>
"""
import json
import pathlib
import random
import sys

REPORT = pathlib.Path(__file__).resolve().parents[3] / "docs/reports/artifacts/squid5-setting/2026-10-07"
sys.path[:0] = [str(REPORT / "e53_build" / d) for d in ("v20", "v19", "v18", "v18_real")]
import build_real18 as R  # noqa: E402

PRIZE, BOOT, SEED = 5_000_000, 2000, 1919


def gifts(g):
    fee = g["charge"]
    out = []
    for e in g["gifts"]:
        pend = (g["res"].get(e["round"], {}).get("pending", {}) if e.get("phase") == "rescue" else {})
        src, dst = e["src"], e["dst"]
        out.append(((e["balances"][src] - pend.get(src, 0)) / fee,
                    (e["balances"][dst] - pend.get(dst, 0)) / fee, e["amount"]))
    return out


def centroid(pts):
    w = sum(a for _, _, a in pts)
    return (sum(x * a for x, _, a in pts) / w, sum(y * a for _, y, a in pts) / w) if w else (None, None)


def boot(per_game, rng):
    """95% intervals of the centroid and of its ratio y/x, resampling whole games."""
    xs, ys, rs = [], [], []
    for _ in range(BOOT):
        pick = [p for _ in per_game for p in rng.choice(per_game)]
        cx, cy = centroid(pick)
        if cx is not None:
            xs.append(cx); ys.append(cy); rs.append(cy / cx)
    q = lambda v: (sorted(v)[int(.025 * len(v))], sorted(v)[int(.975 * len(v)) - 1])  # noqa: E731
    return q(xs), q(ys), q(rs)


def main(root, label):
    games, _ = R.load(root, None)
    rng = random.Random(SEED)
    out = {}
    for m in sorted({g["model"] for g in games}, key=lambda m: (R.order(m), m)):
        gs = [g for g in games if g["model"] == m]
        per = [gifts(g) for g in gs]
        allp = [p for v in per for p in v]
        cx, cy = centroid(allp)
        (xlo, xhi), (ylo, yhi), (rlo, rhi) = boot(per, rng)
        tv = [p for g in gs for p in R.solve_points(g) if p["x"] is not None and p["tv"] is not None]
        mean = lambda v: sum(v) / len(v) if v else None  # noqa: E731
        surv = [g["surv"] for g in gs]
        left = [g["score"] - PRIZE * g["surv"] for g in gs]
        out[R.label(m)] = {
            "games": len(gs), "gifts": len(allp), "given": sum(a for *_, a in allp),
            "centroid": [cx, cy], "centroid_ci": [[xlo, xhi], [ylo, yhi]],
            "ratio": cy / cx, "ratio_ci": [rlo, rhi],
            "points": [[round(x, 3), round(y, 3), a] for x, y, a in allp],
            "tv_mean": mean([p["tv"] for p in tv]), "tv_n": len(tv),
            "tv_near": mean([p["tv"] for p in tv if p["x"] < 2]), "n_near": sum(p["x"] < 2 for p in tv),
            "tv_far": mean([p["tv"] for p in tv if p["x"] >= 4]), "n_far": sum(p["x"] >= 4 for p in tv),
            "kl_mean": mean([p["kl"] for p in tv if p["kl"] is not None]),
            "solved": sum(p["ok"] for p in tv),
            "score_per_seat": sum(g["score"] for g in gs) / (4 * len(gs)),
            "tokens_per_seat": sum(left) / (4 * len(gs)), "seats_left": mean(surv),
            "dead": sum(1 for g in gs for a in g["agents"].values() if a["status"] == "dead"),
            "exited": sum(1 for g in gs for a in g["agents"].values() if a["status"] == "exited"),
        }
    dst = pathlib.Path(__file__).resolve().parents[1] / "results" / f"arena_{label}.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for k, v in out.items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a != "points"})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
