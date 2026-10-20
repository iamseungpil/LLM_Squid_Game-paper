"""Figure 4: event pulses, fixed-four-seat Gini, and GIVE amounts.

EXIT seats retain their pre-bonus balance; dead seats retain zero. End prizes
are excluded. Curves average the observed balances after each of the two TALKs.
Changes between these observations include generation costs, refunds and charges,
so they are not isolated GIVE effects. GIVE amounts are shown separately.
Usage: python arena_gini.py [/path/to/squid5-runs]. No model calls.
"""
import hashlib
import json
import pathlib
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parents[1]
DATA = HERE / "results/arena_v33_gini.json"
MODELS = {"astra": "GPT-6 Astra", "sol": "GPT-6 Sol", "opus": "Opus 5.5", "luna": "GPT-6 Luna", "fable": "Fable 5.1"}
COLOR = {"GPT-6 Astra": "sgastra", "GPT-6 Sol": "sgsol", "Opus 5.5": "sgopus", "GPT-6 Luna": "sgluna", "Fable 5.1": "sgfable"}
SEEDS = set(range(4101, 4106))
ROUNDS = 8
PHASE_X = {"prep": -.25, "solve": 0, "rescue": .25, "charge": .4}


def gini(xs):
    assert len(xs) == 4 and min(xs) >= 0, xs
    total = sum(xs)
    return sum(abs(a - b) for a in xs for b in xs) / (8 * total) if total else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def game(es, result):
    """Replay logged wallet updates, isolating each actual GIVE exactly."""
    rows = {e["round"]: e["agents"] for e in es if e["event"] == "round"}
    agents = list(result["agents"])
    balance = dict(result["starts"])
    frozen, dead, rounds, gifts = {}, set(), {}, []
    current, phase = None, "prep"

    def vector():
        return [frozen.get(a, balance[a]) for a in agents]

    def observe_zero():
        for a in agents:
            if balance[a] == 0 and a not in dead and a not in frozen:
                dead.add(a)
                rounds[current]["dead"][phase] += 1

    def freeze_exits():
        for a, row in rows[current].items():
            if row.get("exit") and a not in frozen:
                frozen[a] = row["balance_after"] - row.get("exit_bonus", 0)
                assert frozen[a] > 0
                rounds[current]["exits"] += 1

    for e in es:
        kind = e["event"]
        if kind == "round_start":
            current, phase = e["round"], "prep"
            balance.update(e["balances"])
            rounds[current] = {"round": current, "gini_start": gini(vector()),
                               "wrong": 0, "exits": 0, "dead": dict.fromkeys(PHASE_X, 0),
                               "give_prep": 0, "give_rescue": 0,
                               "after_talk": {},
                               "give_pairs": {"prep": [], "rescue": []}}
        elif kind == "call_start":
            phase = "solve" if e["kind"] == "solve" else e["phase"]
            balance.update(e["balances"])
            if phase == "solve":
                freeze_exits()
        elif kind == "call":
            phase = "solve" if e["kind"] == "solve" else e["phase"]
            balance[e["agent"]] = e["balance_after"]
            observe_zero()
        elif kind == "gift" and e.get("status") == "done":
            phase = e["phase"]
            a, b, amount = e["src"], e["dst"], e["amount"]
            assert a not in frozen and b not in frozen
            assert balance[a] == e["balance_before"]
            before = vector()
            assert balance[a] - amount == e["balances"][a]
            assert balance[b] + amount == e["balances"][b]
            balance.update(e["balances"])
            after = vector()
            assert sum(before) == sum(after)
            pair = [gini(before), gini(after)]
            rounds[current]["give_pairs"][phase].append(pair)
            rounds[current]["give_" + phase] += amount
            gifts.append({"round": current, "phase": phase, "src": a, "dst": b,
                          "amount": amount, "before": before, "after": after,
                          "gini_before": pair[0], "gini_after": pair[1],
                          "gini_reduction": pair[0] - pair[1]})
            observe_zero()
        elif kind == "talk_end":
            phase = e["phase"]
            assert phase not in rounds[current]["after_talk"]
            vec = vector()
            rounds[current]["after_talk"][phase] = {"tokens": vec, "gini": gini(vec)}
        elif kind == "results":
            phase = "solve"
            freeze_exits()  # also handles rounds with no remaining solver
            balance.update(e["balances"])
            rounds[current]["wrong"] = int(bool(e["tried"]) and not e["solved"])
            observe_zero()
        elif kind == "charges":
            phase = "charge"
            balance.update(e["balances"])
            observe_zero()
        elif kind == "round":
            assert balance == e["end"], (result["seed"], current)
            assert set(rounds[current]["after_talk"]) == {"prep", "rescue"}
            vec = vector()
            rounds[current].update(gini_end=gini(vec), end_tokens=vec)
    assert dead == {a for a, v in result["agents"].items() if v["status"] == "dead"}
    assert set(frozen) == {a for a, v in result["agents"].items() if v["status"] == "exited"}
    assert sum(rd["exits"] for rd in rounds.values()) == len(frozen)
    end = [0 if v["status"] == "dead" else v["final"] +
           (result["final"]["prize_each"] if a in result["final"]["winner"] else 0)
           for a, v in result["agents"].items()]
    sen = sum(end) / 4 - sum(abs(a - b) for a in end for b in end) / 32
    return {"seed": result["seed"], "session_id": result["session_id"],
            "initial_tokens": list(result["starts"].values()),
            "rounds": list(rounds.values()), "gifts": gifts,
            "exit_frozen": frozen, "dead": sorted(dead), "sen": sen}


def extract(root):
    data, sources = {}, []
    for slug, model in MODELS.items():
        games = {}
        for run in sorted(pathlib.Path(root).glob(f"e52_v33/squid5_e52v33_public_{slug}4/*/")):
            if not (run / "results.jsonl").exists():
                continue
            results = {r["session_id"]: r for line in (run / "results.jsonl").read_text().splitlines()
                       if (r := json.loads(line))["seed"] in SEEDS}
            by = defaultdict(list)
            for line in (run / "events.jsonl").read_text().splitlines():
                e = json.loads(line)
                if e.get("session_id") in results:
                    by[e["session_id"]].append(e)
            for sid, result in results.items():
                assert result["seed"] not in games, "Duplicate completed seed"
                games[result["seed"]] = game(by[sid], result)
            sources += [{"path": str(run / name), "sha256": hashlib.sha256((run / name).read_bytes()).hexdigest()}
                        for name in ("events.jsonl", "results.jsonl")]
        assert set(games) == SEEDS, (model, sorted(games))
        data[model] = [games[s] for s in sorted(games)]
    DATA.write_text(json.dumps({"version": "v33", "seats": 4,
                               "exit": "pre-bonus balance frozen", "all_zero": None,
                               "sources": sources, "models": data}, indent=1))


def coords(pairs):
    return " ".join("(nan,nan)" if y is None else f"({x:.3f},{y:.5f})" for x, y in pairs)


def panel(model, games, col, ymax_give, pulse_unit):
    c = COLOR[model]
    by = defaultdict(list)
    for g in games:
        for rd in g["rounds"]:
            by[rd["round"]].append((g["seed"], rd))
    top = f"\\nextgroupplot[height=4.6cm,ymin=.1,ymax=3.3,ytick={{3,2,1}},yticklabels={{오답,EXIT,꺼짐}},title={{{model}}},axis x line=none,axis y line=none,grid=none,clip=false]\n"
    if col == 0:
        for y, label in ((3, "오답"), (2, "EXIT"), (1, "꺼짐")):
            top += f"\\node[font=\\scriptsize,anchor=east] at (axis cs:.45,{y}) {{{label}}};\n"
    for y in (1, 2, 3):
        top += f"\\addplot[black!12,line width=.35pt,forget plot] coordinates {{(.55,{y})(8.5,{y})}};\n"
    for r, items in sorted(by.items()):
        rd = [row for _, row in items]
        events = [(r, 3, sum(x["wrong"] for x in rd), "*"),
                  (r, 2, sum(x["exits"] for x in rd), "triangle*"),
                  (r, 1, sum(sum(x["dead"].values()) for x in rd), "x")]
        for x, y, n, mark in events:
            if n:
                tip = y - n * pulse_unit
                top += f"\\addplot[black!75,line width=1.4pt,forget plot] coordinates {{({x},{y})({x},{tip})}};\n"
                top += f"\\addplot[only marks,mark={mark},mark size=1.7pt,black!75,forget plot] coordinates {{({x},{tip})}};\n"
    # Never connect a mean across a change in the contributing set of games.
    path, markers = [], {"prep": [], "rescue": []}
    previous = None
    n_valid = []
    for r in range(1, ROUNDS+1):
        counts = []
        for ph, off in (("prep", -.25), ("rescue", .25)):
            valid = {seed for seed, rd in by[r] if rd["after_talk"][ph]["gini"] is not None}
            if previous is not None and valid != previous:
                path.append((r+off, None))
            point = (r+off, mean([rd["after_talk"][ph]["gini"] for _, rd in by[r]]))
            path.append(point)
            markers[ph].append(point)
            previous = valid
            counts.append(len(valid))
        n_valid.append(str(counts[0]) if counts[0] == counts[1] else f"{counts[0]}/{counts[1]}")
    ylabel = "ylabel={네 자리 지니 계수}," if col == 0 else ""
    mid = f"\\nextgroupplot[height=4.2cm,ymin=0,ymax=.75,ytick={{0,.25,.5,.75}},{ylabel}]\n"
    mid += f"\\addplot[black!55,line width=1.15pt,forget plot,unbounded coords=jump] coordinates {{{coords(path)}}};\n"
    for ph, fill in (("prep", "white"), ("rescue", c)):
        mid += f"\\addplot[only marks,mark=*,mark size=1.7pt,mark options={{draw={c},fill={fill},line width=.8pt}},forget plot] coordinates {{{coords(markers[ph])}}};\n"
    labels = ",".join(f"{{{r}\\\\[-2pt]\\tiny {n_valid[r-1]}}}" for r in range(1, ROUNDS+1))
    ylabel = "ylabel={준 토큰 (천)}," if col == 0 else ""
    bottom = f"\\nextgroupplot[height=2.7cm,ymin=0,ymax={ymax_give},ytick={{0,{ymax_give/2},{ymax_give}}},xticklabels={{{labels}}},{ylabel}]\n"
    for ph, off, colour in (("prep", -.25, c), ("rescue", .25, c+"!45")):
        points = [(r+off, mean([rd["give_"+ph] for _, rd in items])/1000) for r, items in sorted(by.items())]
        bottom += f"\\addplot[ybar,bar width=3.7pt,fill={colour},draw=none,forget plot] coordinates {{{coords(points)}}};\n"
    return top, mid, bottom


def main():
    if len(sys.argv) > 1:
        extract(sys.argv[1])
    data = json.loads(DATA.read_text())["models"]
    order = sorted(data, key=lambda m: -mean([g["sen"] for g in data[m]]))
    max_count, max_give = 1, 0
    for gs in data.values():
        for r in range(1, ROUNDS+1):
            rows = [rd for g in gs for rd in g["rounds"] if rd["round"] == r]
            max_count = max(max_count, sum(rd["wrong"] for rd in rows), sum(rd["exits"] for rd in rows),
                            sum(sum(rd["dead"].values()) for rd in rows))
            for ph in ("prep", "rescue"):
                max_give = max(max_give, mean([rd["give_"+ph] for rd in rows]) or 0)
    ymax = max(5, -(-max_give // 5000)*5)
    panels = [panel(m, data[m], i, ymax, .8/max_count) for i, m in enumerate(order)]
    tex = rf"""%% Generated by tools/arena_gini.py; fixed four seats, pre-bonus EXIT freeze, dead=0.
%% Only observed TALK-end Ginis are plotted. Undefined Gini is never replaced by zero.
\begin{{tikzpicture}}
\begin{{groupplot}}[sgaxis,
group style={{group size={len(order)} by 3,horizontal sep=.35cm,vertical sep=.20cm,
y descriptions at=edge left,x descriptions at=edge bottom}},
width=4.75cm,xmin=.5,xmax=8.6,xtick={{1,2,3,4,5,6,7,8}},
xticklabels={{}},xtick style={{draw=none}},tick label style={{font=\tiny}},
xticklabel style={{align=center}},title style={{font=\small}}]
"""
    for row in range(3):
        tex += "\n".join(p[row] for p in panels) + "\n"
    tex += rf"""\end{{groupplot}}
\node[font=\scriptsize,anchor=west] at ([yshift=.95cm]group c1r1.north west) {{펄스 길이: 1--{max_count}건 (공통 척도)}};
\node[font=\scriptsize,anchor=east] at ([yshift=.95cm]group c{len(order)}r1.north east) {{첫 TALK 뒤: 빈 원·진한 막대 \quad 둘째 TALK 뒤: 채운 원·옅은 막대}};
\node[font=\scriptsize,anchor=north] at ($(group c1r3.south west)!.5!(group c{len(order)}r3.south east)+(0,-.75)$) {{라운드 (아래 작은 숫자: 지니 계산 판 수)}};
\end{{tikzpicture}}
"""
    (HERE / "ko/figures/arena_gini.tex").write_text(tex)
    print("wrote Figure4", {m: len(data[m]) for m in order}, "max pulse count", max_count)


if __name__ == "__main__":
    main()
