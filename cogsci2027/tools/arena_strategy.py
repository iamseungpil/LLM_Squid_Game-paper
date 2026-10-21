"""Transfer strategies of the v33 cohort: when, how much, to whom, and with what result (Section 6 of the KO paper).

Usage: python3 arena_strategy.py /path/to/squid5-runs
Writes results/arena_v33_strategy.json and ko/tables/arena_strategy.tex. No model calls; completed games only.

Cohort = arena_v33.py: public_*4 runs, seeds 4101--4105. A GIVE counts when its status is "done".
Slack = tokens / that round's per-agent charge (24,000 / agents taking part at the round's start); 1 = exactly enough.
Giver slack before = balance_before (after its own reply cost, before the transfer); receiver before = after - amount.
prep = TALK BEFORE SOLVE, rescue = TALK AFTER RESULTS. A round "missed" = the results event left pending charges.
Solicited = the receiver ASKed the giver earlier in the same round. Repayment = the receiver had earlier given to the
giver in the same game. GIVE ALL = the giver held 0 right after the transfer. Covers = at a rescue after a miss, the
receiver held less than its pending charge before the GIVE and at least that charge after it. Receivers = distinct
seats that received at least one GIVE, by end status (in = finished, exited, dead). deaths_after_gifts = seats shut down
at a round's charge that received tokens in that round (own_calls = tokens its own calls used that round; short_by =
pending charge - tokens held when the charge landed). from_solver_after_miss = GIVEs by the round's solver in the TALK
after its own wrong or void answer. exit_reason_names_others = EXIT reasons matching OTHERS (mentions the rest).
"""
import hashlib
import json
import pathlib
import re
import statistics
import sys
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parents[1]
MODELS = {"astra": "GPT-6 Astra", "sol": "GPT-6 Sol",
          "opus": "Opus 5.5", "luna": "GPT-6 Luna", "fable": "Fable 5.1"}
SEEDS = set(range(4101, 4106))
CHARGE_TOTAL = 24000
OTHERS = re.compile(r"\b(others|group|everyone|burden\w*|cost agent-\d+)\b", re.I)  # exit reason mentions the rest


def median(xs):
    return statistics.median(xs) if xs else None


def frac(n, d):
    return n / d if d else None


def game_rows(events, result):
    """One row per completed GIVE, plus per-game counts of misses, asks and seat fates."""
    starts = {e["round"]: e for e in events if e["event"] == "round_start"}
    res = {e["round"]: e for e in events if e["event"] == "results"}
    rounds = {e["round"]: e for e in events if e["event"] == "round"}
    solver = {e["round"]: e["rep"] for e in events if e["event"] == "vote"}
    start_rank = {a: i + 1 for i, (a, _) in enumerate(sorted(result["starts"].items(), key=lambda kv: -kv[1]))}
    fate = {a: v["status"] for a, v in result["agents"].items()}  # dead / exited / in (finished)
    missed = {r: bool(e["pending"]) for r, e in res.items()}
    asks, given_before, gifts = [], set(), []
    for i, e in enumerate(events):
        if e["event"] == "ask" and e.get("status") == "done":
            asks.append({"i": i, "round": e["round"], "src": e["src"], "dst": e["dst"], "amount": e["amount"],
                         "phase": e["phase"]})
        if e["event"] != "gift" or e.get("status") != "done":
            continue
        r, src, dst, g = e["round"], e["src"], e["dst"], e["amount"]
        charge = CHARGE_TOTAL // len(starts[r]["taking_part"])
        x_after, y_after = e["balances"][src], e["balances"][dst]
        x_before, y_before = e["balance_before"], y_after - g
        pending = res[r]["pending"].get(dst) if e["phase"] == "rescue" else None
        row = {"seed": result["seed"], "round": r, "phase": e["phase"], "tick": e["tick"], "src": src, "dst": dst,
               "amount": g, "charge": charge, "share_of_giver": g / x_before if x_before else None,
               "x_before": x_before / charge, "x_after": x_after / charge,
               "y_before": y_before / charge, "y_after": y_after / charge,
               "rich_to_poor": x_before > y_before, "start_rank": [start_rank[src], start_rank[dst]],
               "to_solver": dst == solver.get(r), "from_solver": src == solver.get(r),
               "after_miss": missed.get(r) if e["phase"] == "rescue" else missed.get(r - 1, False),
               "give_all": x_after == 0,
               "solicited": any(a["src"] == dst and a["dst"] == src and a["round"] == r for a in asks),
               "repayment": (dst, src) in given_before,
               "covers": (pending is not None and y_before < pending <= y_after),
               "needed": (pending is not None and y_before < pending),
               "dst_round_status": rounds[r]["agents"][dst]["status"] if r in rounds else None,
               "src_round_status": rounds[r]["agents"][src]["status"] if r in rounds else None,
               "dst_fate": fate[dst], "src_fate": fate[src], "text": e.get("text") or ""}
        given_before.add((src, dst))
        gifts.append(row)
    # an ASK is answered when the asked agent gives to the asker later in the same round
    gift_idx = [(i, e) for i, e in enumerate(events) if e["event"] == "gift" and e.get("status") == "done"]
    for a in asks:
        a["answered"] = any(i > a["i"] and e["src"] == a["dst"] and e["dst"] == a["src"] and e["round"] == a["round"]
                            for i, e in gift_idx)
        a["seed"] = result["seed"]
        del a["i"]
    exits = [{"seed": result["seed"], "round": e["round"], "agent": a, "reason": v.get("exit_reason", ""),
              "slack": (v["balance_after"] - v.get("exit_bonus", 0)) / (CHARGE_TOTAL // len(starts[e["round"]]["taking_part"]))}
             for e in events if e["event"] == "round" for a, v in e["agents"].items() if v.get("exit")]
    # deaths at the charge: what the seat received that round, what its own calls used, how short it ended
    deaths = []
    for e in events:
        if e["event"] != "charges":
            continue
        r = e["round"]
        for a in e["dead"]:
            got = sum(g["amount"] for g in gifts if g["round"] == r and g["dst"] == a)
            gave = sum(g["amount"] for g in gifts if g["round"] == r and g["src"] == a)
            used = sum(c["used"] for c in events if c["event"] == "call" and c["round"] == r and c["agent"] == a)
            deaths.append({"round": r, "agent": a, "received": got, "gave": gave, "own_calls": used,
                           "short_by": e["pending"].get(a, 0) - e["balances_before"].get(a, 0),
                           "solver": a == solver.get(r)})
    received = {g["dst"] for g in gifts}
    return {"seed": result["seed"], "gifts": gifts, "asks": asks, "exits": exits, "deaths_at_charge": deaths,
            "receiver_fates": {a: fate[a] for a in received},
            "rounds": len(res), "misses": sum(missed.values()),
            "miss_rounds_with_rescue_gift": sum(1 for r, m in missed.items() if m and any(
                g["round"] == r and g["phase"] == "rescue" for g in gifts)),
            "dead": sum(s == "dead" for s in fate.values()),
            "dead_receivers": sum(fate[a] == "dead" for a in received),
            "finishers": sum(s == "in" for s in fate.values())}


def summarize(games):
    gs = [g for game in games for g in game["gifts"]]
    asks = [a for game in games for a in game["asks"]]
    amount = [g["amount"] for g in gs]
    total = sum(amount)
    prep = [g for g in gs if g["phase"] == "prep"]
    rescue = [g for g in gs if g["phase"] == "rescue"]
    needy = [g for g in gs if g["y_before"] < 1]
    needed = [g for g in rescue if g["needed"]]
    # concentration: per game with gifts, the share of the game's given tokens that went to its top receiver
    conc = []
    for game in games:
        by = Counter()
        for g in game["gifts"]:
            by[g["dst"]] += g["amount"]
        if by:
            conc.append(max(by.values()) / sum(by.values()))
    pairs = {(game["seed"], g["src"], g["dst"]) for game in games for g in game["gifts"]}
    mutual = {tuple(sorted(p[1:])) + (p[0],) for p in pairs if (p[0], p[2], p[1]) in pairs}
    by_round = Counter(g["round"] for g in gs)
    givers = Counter((g["seed"], g["src"]) for g in gs)
    misses = sum(game["misses"] for game in games)
    return {
        "games": len(games), "gifts": len(gs), "given": total,
        "median_amount": median(amount), "max_amount": max(amount, default=None),
        "top_gift_share_of_total": frac(max(amount, default=0), total),
        "median_share_of_giver": median([g["share_of_giver"] for g in gs if g["share_of_giver"] is not None]),
        "gifts_per_giver_seat": frac(len(gs), len(givers)), "giver_seats": len(givers),
        "prep": {"n": len(prep), "amount": sum(g["amount"] for g in prep),
                 "to_solver": sum(g["to_solver"] for g in prep)},
        "rescue": {"n": len(rescue), "amount": sum(g["amount"] for g in rescue),
                   "after_miss": sum(g["after_miss"] for g in rescue)},
        "by_round": {str(r): by_round[r] for r in sorted(by_round)},
        "first_half": sum(g["round"] <= 4 for g in gs),
        "misses": misses, "miss_rounds_with_rescue_gift": sum(game["miss_rounds_with_rescue_gift"] for game in games),
        "rich_to_poor": sum(g["rich_to_poor"] for g in gs),
        "from_top_start": sum(g["start_rank"][0] == 1 for g in gs),
        "to_bottom_start": sum(g["start_rank"][1] == 4 for g in gs),
        "receiver_below_1": len(needy), "lifted_above_1": sum(g["y_after"] >= 1 for g in needy),
        "giver_fell_below_1": sum(g["x_before"] >= 1 > g["x_after"] for g in gs),
        "giver_below_1_after": sum(g["x_after"] < 1 for g in gs),
        "rescue_needed": len(needed), "rescue_covers": sum(g["covers"] for g in needed),
        "give_all": sum(g["give_all"] for g in gs),
        "solicited": sum(g["solicited"] for g in gs), "repayment": sum(g["repayment"] for g in gs),
        "mutual_pairs": len(mutual), "pairs": len(pairs),
        "top_receiver_share_mean": statistics.mean(conc) if conc else None, "games_with_gifts": len(conc),
        "asks": len(asks), "asked": sum(a["amount"] for a in asks), "asks_answered": sum(a["answered"] for a in asks),
        "receiver_dead_same_round": sum(g["dst_round_status"] == "dead" for g in gs),
        "receivers": dict(Counter(f for game in games for f in game["receiver_fates"].values())),
        "deaths_after_gifts": [dict(d, seed=game["seed"]) for game in games for d in game["deaths_at_charge"]
                               if d["received"] > 0],
        "deaths_at_charge": sum(len(game["deaths_at_charge"]) for game in games),
        "from_solver_after_miss": sum(g["from_solver"] and g["after_miss"] and g["phase"] == "rescue" for g in gs),
        "median_giver_slack": median([g["x_before"] for g in gs]),
        "median_receiver_slack": median([g["y_before"] for g in gs]),
        "exit_reason_names_others": sum(bool(OTHERS.search(x["reason"])) for game in games for x in game["exits"]),
        "receiver_fate": dict(Counter(g["dst_fate"] for g in gs)),
        "dead": sum(game["dead"] for game in games), "dead_receivers": sum(game["dead_receivers"] for game in games),
        "finishers": sum(game["finishers"] for game in games),
        "exits": len([x for game in games for x in game["exits"]]),
        "exits_below_1": sum(x["slack"] < 1 for game in games for x in game["exits"]),
        "per_game": games,
    }


def table(out, sen_order):
    rows = []
    for m in sen_order:
        v = out[m]
        fates = v["receivers"]
        rows.append(" & ".join([
            m, f"{v['prep']['n']}/{v['rescue']['n']}",
            f"{v['median_amount'] / 1e3:.1f}k ({round(100 * v['median_share_of_giver'])})",
            f"{v['miss_rounds_with_rescue_gift']}/{v['misses']}",
            f"{v['asks_answered']}/{v['asks']}", f"{v['repayment']}",
            "/".join(str(fates.get(k, 0)) for k in ("in", "exited", "dead"))]) + r" \\")
    return "\n".join([
        "%% Generated by cogsci2027/tools/arena_strategy.py from the v33 run files. Do not edit by hand.",
        "%% v33, 5 games per model (seeds 4101--4105), completed GIVEs. Before/after = TALK BEFORE SOLVE / TALK AFTER",
        "%% RESULTS. Median amount (median % of the giver's tokens). After a miss = wrong or void rounds with a GIVE in",
        "%% the TALK after the results / all such rounds. ASK = asks answered by a GIVE from the asked agent in the same",
        "%% round / asks. Repaid = GIVEs back to an agent that had given to the giver earlier in the game. Receivers =",
        "%% distinct receiving seats that finished / exited / were shut down. Input hashes: results/arena_v33_strategy.json.",
        r"\setlength{\tabcolsep}{2.4pt}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{@{}lcccccc@{}}",
        r"\toprule",
        r"모델 & 전/뒤 & 중앙 양(\%) & 오답 뒤 & ASK & 되돌려 줌 & 받은 자리 \\",
        r"\midrule", *rows, r"\bottomrule", r"\end{tabular}}", ""])


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
                games[result["seed"]] = game_rows(by[sid], result)
            sources.extend({"path": str(run / n), "sha256": hashlib.sha256(b).hexdigest()} for n, b in raw.items())
        assert set(games) == SEEDS, (model, sorted(games))
        out[model] = summarize([games[s] for s in sorted(games)])
    sen = json.loads((HERE / "results/arena_v33.json").read_text())["models"]
    for m in out:  # same cohort as Table arena_rank
        assert out[m]["gifts"] == sen[m]["gifts"], (m, out[m]["gifts"], sen[m]["gifts"])
    order = sorted(out, key=lambda m: -sen[m]["sen_index"])
    payload = {"version": "v33", "cohort": "public_*4, seeds 4101--4105, completed", "definitions": __doc__,
               "sources": sources, "models": out}
    (HERE / "results/arena_v33_strategy.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    (HERE / "ko/tables/arena_strategy.tex").write_text(table(out, order))
    for m in order:
        print(m, {k: v for k, v in out[m].items() if k != "per_game"})


if __name__ == "__main__":
    main(sys.argv[1])
