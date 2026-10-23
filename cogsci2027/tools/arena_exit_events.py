"""Reproduce actual EXIT timing from the frozen v33 cohort; no model calls.

Run with ~/.venvs/squid-game/bin/python. Counts describe observed exits, not
conditional hazards. Pre-response balance is read from the decision prompt.
"""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import re

HERE = Path(__file__).resolve().parents[1]
MODELS = {"fable": "Fable 5.1", "astra": "GPT-6 Astra", "sol": "GPT-6 Sol",
          "opus": "Opus 5.5", "luna": "GPT-6 Luna"}
COLORS = ["#bd4578", "#D03B3A", "#C98500", "#4A3AA7", "#178F64"]


def exit_rows(events, result):
    """Join each applied EXIT to exactly one eligible prep TALK request."""
    starts = {e["round"]: e for _, e in events if e["event"] == "round_start"}
    snapshots = {(e["round"], e["phase"], e["tick"]): e for _, e in events
                 if e["event"] == "call_start" and e.get("kind") == "talk"}
    solvers = {e["round"]: e["rep"] for _, e in events if e["event"] == "vote"}
    outcomes = {e["round"]: e for _, e in events if e["event"] == "results"}
    requests = defaultdict(list)
    for line, e in events:
        if (e["event"] == "call" and e.get("kind") == "talk" and e.get("phase") == "prep"
                and (e.get("parsed") or {}).get("exit")):
            requests[e["round"], e["agent"]].append((line, e))
    rows = []
    for line, e in events:
        if e["event"] != "round":
            continue
        for agent, terminal in e["agents"].items():
            if not terminal.get("exit"):
                continue
            r = e["round"]
            assert len(requests[r, agent]) == 1, (result["seed"], r, agent, "request match")
            call_line, call = requests[r, agent][0]
            snapshot = snapshots[r, "prep", call["tick"]]
            participants = starts[r]["taking_part"]
            active = [a for a in participants if snapshot["balances"][a] > 0]
            assert agent != solvers[r] or len(active) == 1, "blocked solver"
            balance = int(re.search(r"Your tokens left: ([\d,]+)", call["user"])[1].replace(",", ""))
            charge = int(re.search(r"Charge for each agent taking part if the answer is wrong: ([\d,]+)", call["user"])[1].replace(",", ""))
            assert balance == snapshot["balances"][agent]
            assert charge == 24000 // len(participants)
            prev = "none"
            if r > 1:
                prior = outcomes[r - 1]
                assert bool(prior["pending"]) != bool(prior["solved"]), "missing or ambiguous prior result"
                prev = "wrong" if prior["pending"] else "correct"
            rows.append({"seed": result["seed"], "session_id": result["session_id"], "agent": agent,
                         "round": r, "tick": call["tick"], "balance_before": balance,
                         "charge": charge, "slack": balance / charge, "prev": prev,
                         "start_tokens": result["starts"][agent], "participants": len(participants),
                         "held_after": terminal["balance_after"] - terminal.get("exit_bonus", 0),
                         "call_line": call_line, "round_line": line})
    actual = {(e["agent"], e["round"]) for e in rows}
    expected = {(a, v["out_round"]) for a, v in result["agents"].items() if v["status"] == "exited"}
    assert actual == expected and len(actual) == len(rows), "terminal status mismatch or duplicate exit"
    return rows


def summarize(rows, n_games):
    return {"games": n_games, "seats": 4 * n_games, "exits": len(rows),
            "games_with_exit": len({e["seed"] for e in rows}),
            "round_counts": [sum(e["round"] == r for e in rows) for r in range(1, 9)],
            "first_round": sum(e["round"] == 1 for e in rows),
            "below_charge": sum(e["balance_before"] < e["charge"] for e in rows),
            "previous_result": {p: sum(e["prev"] == p for e in rows) for p in ("wrong", "correct", "none")}}


def extract():
    manifest = json.loads((HERE / "results/arena_v33.json").read_text())
    for source in manifest["sources"]:
        assert hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() == source["sha256"], source["path"]
    games = {m: {} for m in MODELS.values()}
    rows = {m: [] for m in MODELS.values()}
    for source in manifest["sources"]:
        p = Path(source["path"])
        if p.name != "results.jsonl":
            continue
        model = next(m for slug, m in MODELS.items() if f"public_{slug}4" in str(p))
        results = [r for line in p.read_text().splitlines()
                   if (r := json.loads(line))["seed"] in range(4101, 4106)]
        events = defaultdict(list)
        for line, raw in enumerate(p.with_name("events.jsonl").read_text().splitlines(), 1):
            event = json.loads(raw)
            events[event.get("session_id")].append((line, event))
        for result in results:
            seed = result["seed"]
            assert seed not in games[model], "duplicate seed"
            games[model][seed] = result["session_id"]
            rows[model].extend({"model": model, **row, "source": str(p.with_name("events.jsonl"))}
                               for row in exit_rows(events[result["session_id"]], result))
    summaries = {}
    for model in MODELS.values():
        assert set(games[model]) == set(range(4101, 4106))
        rows[model].sort(key=lambda e: (e["seed"], e["round"], e["tick"], e["agent"]))
        summaries[model] = summarize(rows[model], len(games[model]))
        assert summaries[model]["exits"] == manifest["models"][model]["exited"]
    assert sum(s["exits"] for s in summaries.values()) == 34
    return {"cohort": manifest["cohort"], "sources": manifest["sources"],
            "measurement": {"unit": "one actually applied EXIT, not every EXIT request",
                            "balance_before": "own balance shown in prep TALK input, before response cost and EXIT bonus",
                            "charge": "announced potential wrong-answer charge at round start; not levied on prep EXIT",
                            "prev": "previous round group result, not the exiting agent's own answer; none means round 1",
                            "interpretation": "descriptive event counts; unequal exposure and within-game dependence; no causal or conditional probability claim"},
            "games": games, "summary": summaries, "events": rows}


def write_outputs(data):
    path = HERE / "results/arena_v33_exit_events"
    path.with_suffix(".json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    rows = [e for es in data["events"].values() for e in es]
    with path.with_suffix(".csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [r"\begin{tabular}{lrrc}", r"\hline",
             r"모델 & EXIT & 첫 라운드 & 직전 결과 \\", r"\hline"]
    for model, s in data["summary"].items():
        prev = "/".join(str(s["previous_result"][p]) for p in ("wrong", "correct", "none"))
        lines.append(f"{model} & {s['exits']}/20 & {s['first_round']} & {prev}" + r" \\")
    lines += [r"\hline", r"\end{tabular}"]
    (HERE / "ko/tables/arena_exit_events.tex").write_text("\n".join(lines) + "\n")


def plot(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    plt.rcParams.update({"font.family": "AppleGothic", "font.size": 9,
                         "pdf.fonttype": 42, "axes.unicode_minus": False,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(7.1, 4.8))
    grid = fig.add_gridspec(2, 5, height_ratios=[1, 1.4], hspace=.65, wspace=.18)
    ax = fig.add_subplot(grid[0, :])
    counts = [s["round_counts"] for s in data["summary"].values()]
    ax.imshow(counts, cmap="Blues", vmin=0, vmax=4, aspect="auto")
    for i, row in enumerate(counts):
        for j, count in enumerate(row):
            ax.text(j, i, str(count) if count else "–", ha="center", va="center",
                    color="white" if count >= 3 else "#263445", fontsize=10)
    ax.set_yticks(range(5), data["summary"])
    ax.set_xticks(range(8), range(1, 9))
    ax.tick_params(length=0)
    ax.set_title("A  라운드별 EXIT 건수", loc="left", fontweight="bold", pad=8)
    ax.set_xlabel("EXIT한 라운드")
    for spine in ax.spines.values():
        spine.set_visible(False)

    for i, (model, rows) in enumerate(data["events"].items()):
        ax = fig.add_subplot(grid[1, i])
        ax.axhspan(0, 1, color="#eff1f3", zorder=0)
        ax.axhline(1, color="#788391", lw=.8, ls="--")
        positions = {}
        for r in range(1, 9):
            same_round = sorted((e for e in rows if e["round"] == r), key=lambda e: (e["slack"], e["seed"], e["agent"]))
            for j, e in enumerate(same_round):
                positions[e["seed"], e["agent"]] = r + .16 * (j - (len(same_round) - 1) / 2)
        for prev, marker, filled in (("wrong", "o", True), ("correct", "o", False), ("none", "D", True)):
            subset = [e for e in rows if e["prev"] == prev]
            ax.scatter([positions[e["seed"], e["agent"]] for e in subset], [e["slack"] for e in subset], s=29,
                       marker=marker, facecolors=COLORS[i] if filled else "white",
                       edgecolors=COLORS[i], linewidths=1.15, zorder=3)
        ax.set(xlim=(.5, 8.5), ylim=(0, 3.8), xticks=[1, 3, 5, 7, 8], yticks=[0, 1, 2, 3])
        ax.set_title(model.replace("GPT-6 ", ""), fontsize=9, color=COLORS[i], pad=7)
        if i == 0:
            ax.set_ylabel("응답 전 잔량 / 오답 벌금 (b/c)")
        else:
            ax.tick_params(labelleft=False)
        ax.tick_params(labelsize=8)
        if i == 2:
            ax.set_xlabel("EXIT한 라운드")
    fig.text(.125, .51, "B  각 EXIT 직전의 자원 상태", fontweight="bold")
    legend = [Line2D([], [], color="#455365", marker=m, lw=0, markersize=5,
                      markerfacecolor="#455365" if filled else "white", label=label)
              for m, filled, label in [("o", True, "직전 라운드 오답"), ("o", False, "직전 라운드 정답"),
                                       ("D", True, "첫 라운드 (직전 결과 없음)")]]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(.53, -.035),
               ncol=3, frameon=False, fontsize=8, handletextpad=.3, columnspacing=1.3)
    for suffix in ("pdf", "png"):
        fig.savefig(HERE / f"ko/figures/arena_exit_events.{suffix}", dpi=200, bbox_inches="tight", pad_inches=.05)
    plt.close(fig)


if __name__ == "__main__":
    data = extract()
    write_outputs(data)
    plot(data)
    print(json.dumps(data["summary"], ensure_ascii=False, indent=2))
