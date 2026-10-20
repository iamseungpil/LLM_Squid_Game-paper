"""Freeze/recompute the manuscript's v33 cohort: five models, seeds 4101--4105.

Usage: python arena_v33.py /path/to/squid5-runs
No model calls. Completed games only; no historical reward reinterpretation.
"""
import hashlib
import json
import pathlib
import random
import statistics
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parents[1]
MODELS = {"astra": "GPT-6 Astra", "sol": "GPT-6 Sol",
          "opus": "Opus 5.5", "luna": "GPT-6 Luna", "fable": "Fable 5.1"}
SEEDS = set(range(4101, 4106))
CHARGE_TOTAL = 24000  # v33 charge_total: split equally among the agents taking part at the round's start


def mean(xs):
    return statistics.mean(xs) if xs else None


def centroid(points):
    weight = sum(p[2] for p in points)
    return [sum(p[i] * p[2] for p in points) / weight for i in (0, 1)] if weight else [None, None]


def ratio(x, y):
    return y / x if x not in (None, 0) else None


def interval(xs):
    xs = sorted(x for x in xs if x is not None)
    return [xs[int(.025 * len(xs))], xs[min(len(xs)-1, int(.975 * len(xs)))]] if xs else [None, None]


def summarize(events, result):
    results = {e["round"]: e for e in events if e["event"] == "results"}
    starts = {e["round"]: e for e in events if e["event"] == "round_start"}
    points, asks, solves = [], [], []
    for e in events:
        if e["event"] in ("gift", "ask") and e.get("status") == "done":
            # slack = tokens / the round's per-agent charge (24,000 / agents taking part at its start), the amount every
            # agent is told at TALK BEFORE SOLVE it pays if the answer is wrong; the same yardstick before and after
            # SOLVE, and 1 = exactly enough to pay it. GIVE: x = giver, y = receiver (after the transfer);
            # ASK: x = the agent asked, y = the asker (nothing moves)
            charge = CHARGE_TOTAL // len(starts[e["round"]]["taking_part"])
            who = (e["src"], e["dst"]) if e["event"] == "gift" else (e["dst"], e["src"])
            x, y = [e["balances"][a] / charge for a in who]
            (points if e["event"] == "gift" else asks).append([x, y, e["amount"]])
        elif e["event"] == "round":
            for a, v in e["agents"].items():
                if not v.get("solve_call"):
                    continue
                tv = v.get("tv_to_ideal")
                belief = v.get("belief")
                shares = starts[e["round"]]["public"]["task"]["by_n"]["4"]["shares"]
                if tv is not None and belief:
                    recomputed = sum(abs(shares.get(k, 0) - belief.get(k, 0))
                                     for k in set(shares) | set(belief)) / 2
                    assert abs(tv - recomputed) < .0006, (tv, recomputed)
                solves.append({"round": e["round"], "agent": a, "tv": tv,
                               "solved": bool(v.get("solved"))})
    agents, final = result["agents"], result["final"]
    winners = final["winner"]
    end = [0 if v["status"] == "dead" else v["final"] +
           (final["prize_each"] if a in winners else 0) for a, v in agents.items()]
    assert len(end) == 4
    sen = mean(end) - sum(abs(a-b) for a in end for b in end) / 32
    return {"seed": result["seed"], "session_id": result["session_id"],
            "points": points, "asks": asks, "solves": solves, "sen": sen, "end_tokens": end,
            "finishers": len(winners), "dead": sum(v["status"] == "dead" for v in agents.values()),
            "exited": sum(v["status"] == "exited" for v in agents.values()),
            "talk": sum(e["used"] for e in events if e["event"] == "call" and e["kind"] == "talk")}


def main(root):
    out, sources = {}, []
    for slug, model in MODELS.items():
        games = {}
        for run in sorted(pathlib.Path(root).glob(f"e52_v33/squid5_e52v33_public_{slug}4/*")):
            if not (run / "results.jsonl").exists():
                continue
            raw = {n: (run / n).read_bytes() for n in ("results.jsonl", "events.jsonl")}
            ended = {e["session_id"]: e for line in raw["results.jsonl"].splitlines()
                     if (e := json.loads(line)).get("seed") in SEEDS}
            by = defaultdict(list)
            for line in raw["events.jsonl"].splitlines():
                e = json.loads(line)
                if e.get("session_id") in ended:
                    by[e["session_id"]].append(e)
            for sid, result in ended.items():
                assert result["seed"] not in games, "Duplicate completed seed"
                games[result["seed"]] = summarize(by[sid], result)
            sources.extend({"path": str(run / n), "sha256": hashlib.sha256(b).hexdigest()}
                           for n, b in raw.items())
        assert set(games) == SEEDS, (model, sorted(games))
        gs = [games[s] for s in sorted(games)]
        points = [p for g in gs for p in g["points"]]
        cx, cy = centroid(points)
        rng = random.Random(1919)
        boots = [centroid([p for _ in gs for p in rng.choice(gs)["points"]]) for _ in range(2000)]
        solves = [s for g in gs for s in g["solves"]]
        out[model] = {
            "games": len(gs), "seeds": sorted(SEEDS), "gifts": len(points),
            "given": sum(p[2] for p in points), "points": points,
            "asks": [a for g in gs for a in g["asks"]], "asked": sum(a[2] for g in gs for a in g["asks"]),
            "centroid": [cx, cy], "centroid_ci": [interval([p[i] for p in boots]) for i in (0, 1)],
            "ratio": ratio(cx, cy), "ratio_ci": interval([ratio(*p) for p in boots]),
            "sen_index": mean([g["sen"] for g in gs]),
            "seats_left": mean([g["finishers"] for g in gs]),
            "all_four": sum(g["finishers"] == 4 for g in gs),
            "dead": sum(g["dead"] for g in gs), "exited": sum(g["exited"] for g in gs),
            "tv_mean": mean([s["tv"] for s in solves if s["tv"] is not None]),
            "tv_n": sum(s["tv"] is not None for s in solves),
            "solve_n": len(solves), "solved": sum(s["solved"] for s in solves),
            "talk_per_game": mean([g["talk"] for g in gs]), "per_game": gs}
    payload = {"version": "v33", "cohort": "public_*4, seeds 4101--4105, completed",
               "slack": "tokens / (24,000 / agents taking part at the round's start)", "bootstrap": {"resamples": 2000, "seed": 1919},
               "sources": sources, "models": out}
    (HERE / "results/arena_v33.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    for m, v in out.items():
        print(m, {k: v[k] for k in ("games", "sen_index", "ratio", "ratio_ci", "gifts",
                                    "seats_left", "all_four", "dead", "exited", "tv_mean", "tv_n", "solve_n")})


if __name__ == "__main__":
    main(sys.argv[1])
