"""Reproduce round Sen, transfer timing and EXIT plots from the frozen v33 manifest.

No model calls. Run with the research Python environment. Four original seats
remain in every vector; EXIT holdings include their recorded bonus, shutdowns
are zero. Early-ended games retain their terminal vector through round eight.
"""
import hashlib
import json
import pathlib
import re
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = pathlib.Path(__file__).resolve().parents[1]
COLORS = {"Fable 5.1": "#bd4578", "GPT-6 Astra": "#D03B3A", "GPT-6 Sol": "#C98500",
          "Opus 5.5": "#4A3AA7", "GPT-6 Luna": "#178F64"}
SLUGS = {"fable": "Fable 5.1", "astra": "GPT-6 Astra", "sol": "GPT-6 Sol",
         "opus": "Opus 5.5", "luna": "GPT-6 Luna"}
FIG = HERE / "ko/figures"


def sen(values):
    assert len(values) == 4 and min(values) >= 0
    return sum(values) / 4 - sum(abs(a - b) for a in values for b in values) / 32


def extract():
    manifest = json.loads((HERE / "results/arena_v33.json").read_text())
    sources = manifest["sources"]
    for src in sources:
        assert hashlib.sha256(pathlib.Path(src["path"]).read_bytes()).hexdigest() == src["sha256"], src["path"]
    games = defaultdict(dict)
    for src in sources:
        p = pathlib.Path(src["path"])
        if p.name != "results.jsonl":
            continue
        model = next(m for slug, m in SLUGS.items() if f"public_{slug}4" in str(p))
        results = {r["session_id"]: r for line in p.read_text().splitlines()
                   if (r := json.loads(line))["seed"] in range(4101, 4106)}
        events = defaultdict(list)
        for line_no, line in enumerate(p.with_name("events.jsonl").read_text().splitlines(), 1):
            e = json.loads(line)
            if e.get("session_id") in results:
                events[e["session_id"]].append((line_no, e))
        for sid, result in results.items():
            assert result["seed"] not in games[model], "duplicate completed seed"
            seats = list(result["starts"])
            balances = dict(result["starts"])
            rounds = [{"round": 0, "tokens": list(balances.values()), "sen": sen(list(balances.values())), "observed": True}]
            gifts, exits, opportunities, prior = [], [], [], set()
            starts = {e["round"]: e for _, e in events[sid] if e["event"] == "round_start"}
            call_starts = {(e["round"], e["phase"], e["tick"]): e for _, e in events[sid]
                           if e["event"] == "call_start" and e.get("kind") == "talk"}
            solver = {}
            for line_no, e in events[sid]:
                if e["event"] == "vote":
                    solver[e["round"]] = e["rep"]
                if e["event"] == "call" and e.get("kind") == "talk" and e.get("phase") == "prep":
                    snapshot = call_starts[e["round"], "prep", e["tick"]]
                    active = [a for a in starts[e["round"]]["taking_part"] if snapshot["balances"][a] > 0]
                    # Pending EXITs are applied only after TALK; they still constrain the solver.
                    eligible = e["agent"] != solver[e["round"]] or len(active) == 1
                    balance = snapshot["balances"][e["agent"]]
                    shown = int(re.search(r"Your tokens left: ([\d,]+)", e["user"]).group(1).replace(",", ""))
                    charge = 24000 // len(starts[e["round"]]["taking_part"])
                    shown_charge = int(re.search(r"Charge for each agent taking part if the answer is wrong: ([\d,]+)", e["user"]).group(1).replace(",", ""))
                    assert shown == balance and charge == shown_charge
                    if eligible:
                        assert "EXIT — not available" not in e["user"].rsplit("TALK BEFORE SOLVE,", 1)[1]
                        opportunities.append({"round": e["round"], "tick": e["tick"], "agent": e["agent"],
                                              "balance": balance, "charge": charge, "bin": balance // charge,
                                              "requested_exit": bool((e.get("parsed") or {}).get("exit")), "line": line_no})
                if e["event"] == "gift" and e.get("status") == "done":
                    gifts.append({"round": e["round"], "phase": e["phase"], "amount": e["amount"],
                                  "src": e["src"], "dst": e["dst"], "return_direction": (e["dst"], e["src"]) in prior,
                                  "line": line_no})
                    prior.add((e["src"], e["dst"]))
                elif e["event"] == "round":
                    balances.update(e["end"])
                    vector = [balances[a] for a in seats]
                    assert all(v["status"] != "dead" or balances[a] == 0 for a, v in e["agents"].items())
                    rounds.append({"round": e["round"], "tokens": vector, "sen": sen(vector), "observed": True})
                    for a, v in e["agents"].items():
                        if v.get("exit"):
                            charge = 24000 // len(starts[e["round"]]["taking_part"])
                            held = v["balance_after"] - v.get("exit_bonus", 0)
                            exits.append({"round": e["round"], "seed": result["seed"], "agent": a,
                                          "held": held, "charge": charge, "slack": held / charge,
                                          "reason": v.get("exit_reason"), "line": line_no})
            actual_exits = {(e["round"], e["agent"]) for e in exits}
            for opportunity in opportunities:
                opportunity["exit"] = opportunity["requested_exit"] and (opportunity["round"], opportunity["agent"]) in actual_exits
            assert sum(o["exit"] for o in opportunities) == len(exits)
            assert len({(o["round"], o["agent"]) for o in opportunities if o["exit"]}) == len(exits)
            assert [r["round"] for r in rounds] == list(range(result["rounds_played"] + 1))
            for a, v in result["agents"].items():
                assert balances[a] == v["final"], (model, result["seed"], a)
            # Carry forward an absorbing terminal state, never omit a failed game.
            while len(rounds) < 9:
                rounds.append({**rounds[-1], "round": len(rounds), "observed": False})
            paid = [balances[a] + (result["final"]["prize_each"] if a in result["final"]["winner"] else 0) for a in seats]
            expected = next(g["sen"] for g in manifest["models"][model]["per_game"] if g["seed"] == result["seed"])
            assert abs(sen(paid) - expected) < 1e-8
            games[model][result["seed"]] = {"seed": result["seed"], "session_id": sid, "file": str(p.with_name("events.jsonl")),
                                          "rounds": rounds, "settled_tokens": paid, "settled_sen": sen(paid),
                                          "gifts": gifts, "exits": exits, "exit_opportunities": opportunities}
    data = {}
    penalties = [6000, 8000, 12000, 24000]
    token_edges = list(range(0, 45001, 5000))
    for model in sorted(games, key=lambda m: -manifest["models"][m]["sen_index"]):
        assert set(games[model]) == set(range(4101, 4106))
        gs = list(games[model].values())
        gifts = [g for game in gs for g in game["gifts"]]
        assert sum(g["amount"] for g in gifts) == manifest["models"][model]["given"]
        exits = [e for game in gs for e in game["exits"]]
        assert len(exits) == manifest["models"][model]["exited"]
        penalty_counts = [sum(e["charge"] == charge for e in exits) for charge in penalties]
        token_counts = [sum(lo <= e["held"] < hi for e in exits)
                        for lo, hi in zip(token_edges, token_edges[1:])]
        assert sum(penalty_counts) == sum(token_counts) == len(exits)
        opportunities = [o for game in gs for o in game["exit_opportunities"]]
        exit_rate = []
        for interval in range(max(o["bin"] for o in opportunities) + 1):
            encountered = [o for o in opportunities if o["bin"] == interval]
            numerator = sum(o["exit"] for o in encountered)
            exit_rate.append({"bin": interval, "opportunities": len(encountered), "exits": numerator,
                              "rate": numerator / len(encountered) if encountered else None})
        assert sum(b["exits"] for b in exit_rate) == len(exits)
        curve = [statistics.mean(g["rounds"][r]["sen"] for g in gs) for r in range(9)]
        settled_curve = curve[:-1] + [statistics.mean(g["settled_sen"] for g in gs)]
        data[model] = {"games": gs, "sen_before_prize": curve, "sen_with_settlement": settled_curve,
                       "exit_rate": exit_rate, "exits": exits, "exit_penalty_counts": penalty_counts, "exit_token_counts": token_counts, "exit_below_charge": sum(e["slack"] < 1 for e in exits),
                       "exit_median_tokens": statistics.median(e["held"] for e in exits),
                       "transfer": {ph: {"tokens": sum(g["amount"] for g in gifts if g["phase"] == ph),
                                         "count": sum(g["phase"] == ph for g in gifts),
                                         "return_tokens": sum(g["amount"] for g in gifts if g["phase"] == ph and g["return_direction"])}
                                    for ph in ("prep", "rescue")}}
    payload = {"cohort": manifest["cohort"], "sources": sources, "n_seats": 4,
               "intermediate": "end-of-round holdings; recorded EXIT bonus included; completion prize excluded",
               "settled": "same as intermediate until round 7; round 8 includes recorded completion prizes",
               "early_end": "terminal four-seat vector carried forward; fixed denominator of five games",
               "return_direction": "recipient previously gave to sender; not proof of a loan or exact repayment",
               "exit_penalty_categories": penalties, "exit_token_bin_edges": token_edges,
               "exit_measurement": "actual EXITs / eligible prep TALK decision calls in each floor(balance / announced per-agent penalty) bin; pre-response balance shown to the agent; blocked solvers and rescue TALK excluded; repeated calls count separately; empty bins null, not zero",
               "legacy_exit_counts": "historical event histograms retained in JSON only; held tokens are after EXIT response cost, before bonus",
               "models": data}
    (HERE / "results/arena_v33_round_dynamics.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    return data


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight", pad_inches=.03)
    fig.savefig(FIG / f"{name}.png", dpi=180, bbox_inches="tight", pad_inches=.03)
    plt.close(fig)


def plot(data):
    plt.rcParams.update({"font.family": "AppleGothic", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42, "axes.unicode_minus": False})
    for name, key, logarithmic in (("arena_sen_rounds", "sen_before_prize", False),
                                    ("arena_sen_settled", "sen_with_settlement", True)):
        fig, ax = plt.subplots(figsize=(6.9, 2.7))
        for i, (model, v) in enumerate(data.items()):
            ax.plot(range(9), v[key], color=COLORS[model], marker=["o", "s", "^", "D", "v"][i],
                    lw=1.5, ms=4, label=model)
        if logarithmic:
            ax.set_yscale("log")
            ax.set_yticks([10000, 100000, 1000000, 5000000], ["1만", "10만", "100만", "500만"])
        else:
            ax.set_ylim(bottom=0)
            ax.set_yticks([0, 5000, 10000, 15000, 20000, 25000], ["0", "5천", "1만", "1.5만", "2만", "2.5만"])
        ax.set_xticks(range(9), ["시작"] + [str(r) for r in range(1, 9)])
        ax.set_xlabel("라운드 (벌금 처리 뒤)" + (" · 8은 완주 상금 정산 포함" if logarithmic else ""))
        ax.set_ylabel("평균 Sen 지수 (토큰)" + (" · 로그축" if logarithmic else " · 상금 전"))
        ax.grid(axis="y", alpha=.18)
        ax.legend(ncol=3, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(.5, 1.27))
        save(fig, name)

    fig, ax = plt.subplots(figsize=(3.4, 2.35))
    for i, (model, v) in enumerate(data.items()):
        bins = v["exit_rate"]
        ax.plot([b["bin"] for b in bins], [100 * b["rate"] if b["rate"] is not None else float("nan") for b in bins],
                color=COLORS[model], marker=["o", "s", "^", "D", "v"][i], ms=3.5, lw=1,
                label=model.replace("GPT-6 ", ""), alpha=.85)
    ax.set_xticks(range(11)); ax.set_xlim(-.2, 10.2); ax.set_ylim(bottom=-1)
    ax.set_xlabel("잔여 토큰 / 오답 시 1인당 벌금 (정수 구간)", fontsize=8)
    ax.set_ylabel("EXIT 비율 (%)", fontsize=8)
    ax.tick_params(labelsize=7); ax.grid(axis="y", alpha=.18)
    ax.legend(ncol=3, frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(-.05, 1.01),
              handlelength=1.4, columnspacing=.8, borderaxespad=0)
    save(fig, "arena_exit_timing")

    fig, ax = plt.subplots(figsize=(6.9, 3.0))
    positions, labels = [], []
    for i, (model, v) in enumerate(data.items()):
        for j, phase in enumerate(("prep", "rescue")):
            y = 3 * i + j; x = v["transfer"][phase]
            base = (x["tokens"] - x["return_tokens"]) / 1000
            ax.barh(y, base, color=COLORS[model], height=.75)
            ax.barh(y, x["return_tokens"] / 1000, left=base, color=COLORS[model],
                    edgecolor="white", hatch="////", height=.75)
            ax.text(x["tokens"] / 1000 + 1, y, f"{x['tokens']:,} ({x['count']}회)", va="center", fontsize=8)
            positions.append(y); labels.append(model + (" · 전" if j == 0 else " · 뒤"))
    ax.set_yticks(positions, labels); ax.invert_yaxis(); ax.set_xlim(0, 122)
    ax.set_xlabel("5판의 총 GIVE 토큰 (천) · 전 = SOLVE 전, 뒤 = SOLVE 뒤")
    ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
    ax.legend(handles=[Patch(facecolor="#888888", edgecolor="white", hatch="////",
                             label="앞서 자기에게 준 상대에게 되돌려 준 방향의 이전")],
              frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0, 1.01))
    save(fig, "arena_transfer_timing")


if __name__ == "__main__":
    data = extract()
    plot(data)
    print(json.dumps({m: {k: v[k] for k in ("exit_below_charge", "exit_median_tokens", "transfer")}
                      for m, v in data.items()}, ensure_ascii=False, indent=1))
