"""Transfer strategies of the v33 cohort: when, how much, to whom, and with what result (Section 6 of the KO paper).

Usage: python3 arena_strategy.py /path/to/squid5-runs
Writes results/arena_v33_strategy.json and ko/tables/arena_{strategy,cooperation,outcomes}.tex. No model calls; completed games only.

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
Correct-after uses solved results and the same round-level denominator as wrong/void-after.
Rounds with no participants and no task (after everyone exited) are excluded from both denominators.
F = TALK responses with >=1 completed GIVE / all observed TALK responses (both phases, zero-GIVE included).
A = gross transferred tokens / all observed TALK responses. Each response counts once even with multiple GIVEs.
These are descriptive response-normalized measures, not matched eligible-opportunity or preference estimates.
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


def cooperation_calls(events):
    """Observed TALK responses, including zero-GIVE responses; not hypothetical opportunities.

    A response may contain several transfers. Count it once for frequency, but sum
    all completed transfers for volume. Gross volume includes retransferred tokens.
    """
    def key(e, agent_field):
        return (e["round"], e["phase"], e["tick"], e[agent_field])

    calls = [e for e in events if e["event"] == "call" and e["kind"] == "talk"]
    keys = {key(e, "agent") for e in calls}
    assert len(keys) == len(calls), "Duplicate TALK response key"
    transfers = Counter()
    for e in events:
        if e["event"] == "gift" and e.get("status") == "done":
            k = key(e, "src")
            assert k in keys, "Completed GIVE without a TALK response"
            assert e["amount"] > 0
            transfers[k] += e["amount"]
    return {"talk_responses": len(calls), "giving_responses": len(transfers),
            "given": sum(transfers.values())}


def game_rows(events, result):
    """One row per completed GIVE, plus per-game counts of misses, asks and seat fates."""
    starts = {e["round"]: e for e in events if e["event"] == "round_start"}
    res = {e["round"]: e for e in events if e["event"] == "results"}
    rounds = {e["round"]: e for e in events if e["event"] == "round"}
    solver = {e["round"]: e["rep"] for e in events if e["event"] == "vote"}
    start_rank = {a: i + 1 for i, (a, _) in enumerate(sorted(result["starts"].items(), key=lambda kv: -kv[1]))}
    fate = {a: v["status"] for a, v in result["agents"].items()}  # dead / exited / in (finished)
    missed = {r: bool(e["pending"]) for r, e in res.items()}
    correct = {r: bool(e["solved"]) for r, e in res.items()}
    assert all(not (correct[r] and missed[r]) for r in res)
    skipped = sum(not correct[r] and not missed[r] for r in res)
    assert all(e["part"] == [] for r, e in res.items() if not correct[r] and not missed[r]), "Unclassified result"
    cooperation = cooperation_calls(events)
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
    assert cooperation["given"] == sum(g["amount"] for g in gifts)
    return {"seed": result["seed"], "gifts": gifts, "asks": asks, "exits": exits, "deaths_at_charge": deaths,
            "talk_responses": cooperation["talk_responses"], "giving_responses": cooperation["giving_responses"],
            "receiver_fates": {a: fate[a] for a in received},
            "rounds": len(res), "misses": sum(missed.values()),
            "corrects": sum(correct.values()), "skipped_rounds": skipped,
            "correct_rounds_with_rescue_gift": sum(1 for r, c in correct.items() if c and any(
                g["round"] == r and g["phase"] == "rescue" for g in gifts)),
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
    talk_responses = sum(game["talk_responses"] for game in games)
    giving_responses = sum(game["giving_responses"] for game in games)
    return {
        "games": len(games), "gifts": len(gs), "given": total,
        "talk_responses": talk_responses, "giving_responses": giving_responses,
        "giving_response_rate": frac(giving_responses, talk_responses),
        "tokens_per_talk_response": frac(total, talk_responses),
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
        "corrects": sum(game["corrects"] for game in games),
        "skipped_rounds": sum(game["skipped_rounds"] for game in games),
        "correct_rounds_with_rescue_gift": sum(game["correct_rounds_with_rescue_gift"] for game in games),
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


def render_table(headers, rows):
    return "\n".join([
        "%% Generated by cogsci2027/tools/arena_strategy.py; source hashes in arena_v33_strategy.json.",
        r"\setlength{\tabcolsep}{2.4pt}", r"\small",
        r"\begin{tabular}{@{}l" + "c" * (len(headers) - 1) + r"@{}}", r"\toprule",
        " & ".join(headers) + r" \\", r"\midrule",
        *[" & ".join(row) + r" \\" for row in rows],
        r"\bottomrule", r"\end{tabular}", ""])


def table(out, sen_order):
    rows = []
    for m in sen_order:
        v = out[m]
        rows.append([m, f"{v['prep']['n']}/{v['rescue']['n']}",
                     f"{v['correct_rounds_with_rescue_gift']}/{v['corrects']}",
                     f"{v['miss_rounds_with_rescue_gift']}/{v['misses']}"])
    return render_table(["모델", "전/뒤", "정답 뒤", "오답 뒤"], rows)


def cooperation_table(out, sen_order):
    rows = []
    for m in sen_order:
        v = out[m]
        rows.append([m,
                     f"{100 * v['giving_response_rate']:.1f} ({v['giving_responses']}/{v['talk_responses']})",
                     f"{v['tokens_per_talk_response']:.1f}",
                     f"{v['median_amount'] / 1e3:.1f}k ({100 * v['median_share_of_giver']:.0f})",
                     f"{v['asks_answered']}/{v['asks']}", str(v['repayment'])])
    return render_table(["모델", r"$F$ (\%)", r"$A$", r"중앙 양(\%)", "ASK", "되돌려 줌"], rows)


def outcomes_table(out, sen, order, exit_summary):
    rows = []
    for m in order:
        v, fates, e = sen[m], out[m]["receivers"], exit_summary[m]
        assert v['exited'] == e['exits'] and v['games'] == e['games']
        rows.append([m, f"{v['seats_left']:.1f}", str(v['dead']),
                     f"{e['exits']}/{e['seats']}",
                     "/".join(str(fates.get(k, 0)) for k in ("in", "exited", "dead")),
                     str(e['first_round']),
                     "/".join(str(e['previous_result'][k]) for k in ("wrong", "correct", "none"))])
    return render_table(["모델", r"\shortstack{판당\\완주}", "꺼짐", "EXIT",
                         r"\shortstack{받은\\자리}", r"\shortstack{첫\\라운드}",
                         r"\shortstack{직전\\결과}"], rows)


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
    (HERE / "ko/tables/arena_cooperation.tex").write_text(cooperation_table(out, order))
    exit_summary = json.loads((HERE / "results/arena_v33_exit_events.json").read_text())["summary"]
    (HERE / "ko/tables/arena_outcomes.tex").write_text(outcomes_table(out, sen, order, exit_summary))
    for m in order:
        print(m, {k: v for k, v in out[m].items() if k != "per_game"})


if __name__ == "__main__":
    main(sys.argv[1])
