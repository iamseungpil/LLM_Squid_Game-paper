"""Writes the KO v33 Gini figure (figures/arena_gini.tex) from results/arena_v33_gini.json.

Rows (one column per model, shared rounds axis):
  1. Gini of the tokens held by the agents taking part, at four points of each round r:
     r+0    the round's start,
     r+.25  the start plus the GIVEs of TALK BEFORE SOLVE (transfers only: TALK generation left out),
     r+.5   the balances at RESULTS (after SOLVE, refunds, EXITs and shutdowns before SOLVE),
     r+.75  RESULTS plus the GIVEs of TALK AFTER RESULTS (transfers only).
     Solid coloured steps = GIVEs; grey dotted steps = everything else (SOLVE, charges, EXIT, shutdown).
     Thick line = mean over games with >= 2 agents taking part at that point; faint lines = single games.
  2. Tokens given per game in the round (TALK BEFORE SOLVE dark, TALK AFTER RESULTS light).
  3. Per round: wrong or void answers / rounds solved for; EXITs and shutdowns / agents taking part at the round's start.
Under the axis: the number of games still running at the round's start.

Usage: python3 arena_gini.py [/path/to/squid5-runs]   (with a path: re-extract the JSON from e52_v33 runs first)
"""
import json
import pathlib
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parents[1]
DATA = HERE / "results/arena_v33_gini.json"
MODELS = {"astra": "GPT-6 Astra", "sol": "GPT-6 Sol", "opus": "Opus 5.5", "luna": "GPT-6 Luna"}
COLOR = {"GPT-6 Astra": "sgastra", "GPT-6 Sol": "sgsol", "Opus 5.5": "sgopus", "GPT-6 Luna": "sgluna"}
ROUNDS = 8


def gini(xs):
    xs = [max(0, x) for x in xs]
    n, tot = len(xs), sum(xs)
    if n < 2 or not tot:
        return None
    return sum(abs(a - b) for a in xs for b in xs) / (2 * n * tot)


def sen(xs):
    n = len(xs)
    return sum(xs) / n - sum(abs(a - b) for a in xs for b in xs) / (2 * n * n)


def game(es, result):
    """One finished game: per round the four Gini points, the GIVEs, and the round's events."""
    rs, res, gifts, rows = {}, {}, defaultdict(list), {}
    for e in es:
        k = e["event"]
        if k == "round_start":
            rs[e["round"]] = e
        elif k == "results":
            res[e["round"]] = e
        elif k == "gift" and e.get("status") == "done":
            gifts[e["round"]].append(e)
        elif k == "round":
            rows[e["round"]] = e["agents"]
    out = []
    for r in sorted(rs):
        T, b0, row = rs[r]["taking_part"], rs[r]["balances"], rows.get(r, {})
        p1 = {a: b0[a] for a in T}
        for g in gifts[r]:
            if g.get("phase") == "prep":
                p1[g["src"]] = p1.get(g["src"], 0) - g["amount"]
                p1[g["dst"]] = p1.get(g["dst"], 0) + g["amount"]
        pts = [gini([b0[a] for a in T]), gini([p1[a] for a in T]), None, None]
        if r in res:
            b2 = res[r]["balances"]
            S = [a for a in T if not row.get(a, {}).get("exit") and b2.get(a, 0) > 0]
            p3 = {a: b2[a] for a in S}
            for g in gifts[r]:
                if g.get("phase") == "rescue" and g["src"] in p3 and g["dst"] in p3:
                    p3[g["src"]] -= g["amount"]
                    p3[g["dst"]] += g["amount"]
            pts[2:] = [gini([b2[a] for a in S]), gini(list(p3.values()))]
        out.append({"round": r, "n": len(T), "gini": pts,
                    "give_prep": sum(g["amount"] for g in gifts[r] if g.get("phase") == "prep"),
                    "give_rescue": sum(g["amount"] for g in gifts[r] if g.get("phase") == "rescue"),
                    "solve": r in res, "wrong": r in res and not res[r].get("solved"),
                    "exits": sum(bool(v.get("exit")) for v in row.values()),
                    "dead": sum(v.get("status") == "dead" for v in row.values())})
    agents = result["agents"]
    won, each = set(result["final"]["winner"]), result["final"]["prize_each"]
    end = [0 if v["status"] == "dead" else v["final"] + (each if a in won else 0) for a, v in agents.items()]
    return {"rounds": out, "sen": sen(end), "finishers": len(won)}


def extract(root):
    data = {}
    for slug, model in MODELS.items():
        games = []
        for run in sorted(pathlib.Path(root).glob(f"e52_v33/squid5_e52v33_public_{slug}4/*/")):
            results = {json.loads(l)["session_id"]: json.loads(l) for l in open(run / "results.jsonl")}
            by = defaultdict(list)
            for line in open(run / "events.jsonl"):
                e = json.loads(line)
                if e.get("session_id") in results:
                    by[e["session_id"]].append(e)
            games += [dict(game(es, results[sid]), seed=sid.split("-")[1]) for sid, es in sorted(by.items())]
        data[model] = sorted(games, key=lambda g: g["seed"])
    DATA.write_text(json.dumps(data, indent=1))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def coords(pairs, gaps=()):
    return " ".join("(nan,nan)" if y is None or x in gaps else f"({x:.2f},{y:.4f})" for x, y in pairs)


def panel(model, games, col, ymax_give):
    c, first = COLOR[model], col == 0
    by = defaultdict(list)
    for g in games:
        for rd in g["rounds"]:
            by[rd["round"]].append(rd)
    xs = [(r + i / 4, i) for r in range(1, ROUNDS + 1) for i in range(4)]
    m = {r + i / 4: mean([rd["gini"][i] for rd in by[r]]) for r in range(1, ROUNDS + 1) for i in range(4)}
    allpath = coords([(x, m[x]) for x, _ in xs])
    gives = " ".join(f"({x:.2f},{m[x]:.4f}) ({x + .25:.2f},{m[x + .25]:.4f}) (nan,nan)"
                     for x, i in xs if i in (0, 2) and m[x] is not None and m[x + .25] is not None)
    faint = "\n".join(
        f"\\addplot[{c},opacity=.22,line width=.4pt,forget plot,unbounded coords=jump] coordinates {{"
        + coords([(rd["round"] + i / 4, rd["gini"][i]) for rd in g["rounds"] for i in range(4)]) + "};"
        for g in games)
    sen_mean = mean([g["sen"] for g in games])
    fin = sum(g["finishers"] > 0 for g in games)
    title = f"{model}\\\\[-1pt]\\scriptsize Sen {sen_mean / 1e6:.2f}M $\\cdot$ 끝까지 {fin}/{len(games)}판"
    top = (f"\\nextgroupplot[ymin=0,ymax=.75,ytick={{0,.25,.5,.75}},{'ylabel={지니 계수},' if first else ''}"
           f"title={{{title}}}]\n{faint}\n"
           f"\\addplot[black!45,densely dotted,line width=.7pt,forget plot,unbounded coords=jump] coordinates {{{allpath}}};\n"
           f"\\addplot[{c},line width=1.4pt,forget plot,unbounded coords=jump] coordinates {{{gives}}};")
    gp = {r: mean([rd["give_prep"] for rd in by[r]]) for r in range(1, ROUNDS + 1)}
    gr = {r: mean([rd["give_rescue"] for rd in by[r]]) for r in range(1, ROUNDS + 1)}
    mid = (f"\\nextgroupplot[ybar stacked,bar width=5pt,ymin=0,ymax={ymax_give},ytick={{0,{ymax_give // 2},{ymax_give}}},"
           f"{'ylabel={준 토큰 (천)},' if first else ''}]\n"
           f"\\addplot[fill={c},draw=none] coordinates {{{coords([(r + .5, (gp[r] or 0) / 1e3) for r in by])}}};\n"
           f"\\addplot[fill={c}!35,draw=none] coordinates {{{coords([(r + .5, (gr[r] or 0) / 1e3) for r in by])}}};")
    def rate(f, d):
        return [(r + .5, (sum(f(x) for x in by[r]) / s) if (s := sum(d(x) for x in by[r])) else None) for r in by]
    wrong = [(x - .18, y) for x, y in rate(lambda x: x["wrong"], lambda x: x["solve"])]
    ex = [(x, y or None) for x, y in rate(lambda x: x["exits"], lambda x: x["n"])]  # 0 left out (caption: blank = none)
    dead = [(x + .18, y or None) for x, y in rate(lambda x: x["dead"], lambda x: x["n"])]
    labels = ",".join(f"{{{r}\\\\[-2pt]\\tiny {len(by[r])}}}" for r in range(1, ROUNDS + 1))
    bot = (f"\\nextgroupplot[ymin=-.05,ymax=1.05,ytick={{0,.5,1}},xticklabels={{{labels}}},"
           f"xlabel={{라운드 (아래: 진행 중 판 수)}},{'ylabel={비율},' if first else ''}]\n"
           f"\\addplot[only marks,mark=*,mark size=1.4pt,black!70] coordinates {{{coords(wrong)}}};\n"
           f"\\addplot[only marks,mark=triangle,mark size=2.2pt,black!70,thick] coordinates {{{coords(ex)}}};\n"
           f"\\addplot[only marks,mark=x,mark size=2.2pt,black!70,thick] coordinates {{{coords(dead)}}};")
    return top, mid, bot


def main():
    if len(sys.argv) > 1:
        extract(sys.argv[1])
    data = json.loads(DATA.read_text())
    order = sorted(data, key=lambda m: -mean([g["sen"] for g in data[m]]))
    top_give = max(sum(rd["give_prep"] + rd["give_rescue"] for rd in g["rounds"] if rd["round"] == r)
                   for gs in data.values() for g in gs for r in range(1, ROUNDS + 1))
    ymax = max(5, -(-max(mean([(rd["give_prep"] + rd["give_rescue"]) for g in gs for rd in g["rounds"] if rd["round"] == r]) or 0
                        for gs in data.values() for r in range(1, ROUNDS + 1)) // 5000) * 5)
    panels = [panel(m, data[m], i, ymax) for i, m in enumerate(order)]
    rows = [p[0] for p in panels] + [p[1] for p in panels] + [p[2] for p in panels]
    n = sum(len(v) for v in data.values()) // len(data)
    tex = f"""%% Generated by cogsci2027/tools/arena_gini.py from results/arena_v33_gini.json. Do not edit by hand.
%% v33, {n} games per model (seeds {', '.join(sorted({g['seed'] for gs in data.values() for g in gs}))}); largest single-round total given {top_give:,} tokens.
\\begin{{tikzpicture}}
\\begin{{groupplot}}[sgaxis,
  group style={{group size={len(order)} by 3,horizontal sep=0.35cm,vertical sep=0.28cm,
    y descriptions at=edge left,x descriptions at=edge bottom}},
  width=4.75cm,xmin=.9,xmax={ROUNDS + 1.1},xtick={{{','.join(str(r + .5) for r in range(1, ROUNDS + 1))}}},
  xticklabels={{}},xtick style={{draw=none}},tick label style={{font=\\tiny}},
  xticklabel style={{align=center}},title style={{font=\\small,align=center}}]
"""
    for i, body in enumerate(rows):
        h = "3.8cm" if i < len(order) else "2.5cm"
        tex += body.replace("\\nextgroupplot[", f"\\nextgroupplot[height={h},", 1) + "\n"
    tex += r"""\end{groupplot}
\end{tikzpicture}
"""
    (HERE / "ko/figures/arena_gini.tex").write_text(tex)
    print("wrote ko/figures/arena_gini.tex;", {m: len(data[m]) for m in order})


if __name__ == "__main__":
    main()
