"""Writes the KO appendix figure on giving as one's own slack shrinks (figures/arena_risk.tex) from
results/arena_v33_risk.json.

Every TALK call of a seat is one opportunity to give, whether or not it gave (v33 cohort, five models x seeds
4101--4105). Own slack = the seat's tokens when the tick starts (call_start balances) / the round's per-agent charge
(24,000 / agents taking part at the round's start). Bins: <1 (cannot pay the charge), 1-2, 2-4, >=4.
Left panel: share of calls with at least one completed GIVE, 95% interval resampling games (2,000 draws, seed 1919).
Right panel: median share of the seat's tokens given in such a call (sum of its GIVEs / its tokens at the tick).

Usage: python3 arena_risk.py [/path/to/squid5-runs]   (with a path: re-extract the JSON first)
"""
import json
import pathlib
import random
import statistics
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parents[1]
DATA = HERE / "results/arena_v33_risk.json"
MODELS = {"fable": "Fable 5.1", "astra": "GPT-6 Astra", "sol": "GPT-6 Sol", "opus": "Opus 5.5", "luna": "GPT-6 Luna"}
COLOR = {"Fable 5.1": "sgfable", "GPT-6 Astra": "sgastra", "GPT-6 Sol": "sgsol", "Opus 5.5": "sgopus", "GPT-6 Luna": "sgluna"}
MARK = {"Fable 5.1": "*", "GPT-6 Astra": "square*", "GPT-6 Sol": "triangle*", "Opus 5.5": "diamond*", "GPT-6 Luna": "pentagon*"}
SEEDS = set(range(4101, 4106))
BINS = [(0, 1, "<1"), (1, 2, "1–2"), (2, 4, "2–4"), (4, float("inf"), "≥4")]
CHARGE_TOTAL, B, BSEED = 24000, 2000, 1919


def bin_of(x):
    return next(i for i, (lo, hi, _) in enumerate(BINS) if lo <= x < hi)


def calls_of(es):
    """(bin, gave, share) for every TALK call of a seat that still had tokens when its tick started."""
    n = {e["round"]: len(e["taking_part"]) for e in es if e["event"] == "round_start"}
    given = defaultdict(int)
    for e in es:
        if e["event"] == "gift" and e.get("status") == "done":
            given[(e["round"], e.get("phase"), e.get("tick"), e["src"])] += e["amount"]
    start = {(e["round"], e.get("phase"), e.get("turn", e.get("tick"))): e["balances"]
             for e in es if e["event"] == "call_start" and e.get("kind") == "talk"}
    out = []
    for e in es:
        if e["event"] != "call" or e.get("kind") != "talk":
            continue
        key = (e["round"], e.get("phase"), e.get("tick", e.get("turn")))
        bal = (start.get(key) or {}).get(e["agent"])
        if not bal or bal <= 0:
            continue
        g = given.get(key + (e["agent"],), 0)
        out.append([bin_of(bal / (CHARGE_TOTAL // n[e["round"]])), g > 0, round(g / bal, 4)])
    return out


def extract(root):
    data = {}
    for slug, model in MODELS.items():
        games = []
        for run in sorted(pathlib.Path(root).glob(f"e52_v33/squid5_e52v33_public_{slug}4/*/")):
            res = {json.loads(l)["session_id"]: json.loads(l) for l in open(run / "results.jsonl")}
            res = {k: v for k, v in res.items() if v["seed"] in SEEDS}
            by = defaultdict(list)
            for line in open(run / "events.jsonl"):
                e = json.loads(line)
                if e.get("session_id") in res:
                    by[e["session_id"]].append(e)
            games += [{"seed": res[s]["seed"], "calls": calls_of(es)} for s, es in sorted(by.items())]
        assert {g["seed"] for g in games} == SEEDS, model
        rng, per = random.Random(BSEED), []
        for i, (_, _, label) in enumerate(BINS):
            calls = [c for g in games for c in g["calls"] if c[0] == i]
            gave = [c for c in calls if c[1]]
            boots = []
            for _ in range(B):
                cs = [c for g in rng.choices(games, k=len(games)) for c in g["calls"] if c[0] == i]
                if cs:
                    boots.append(sum(c[1] for c in cs) / len(cs))
            boots.sort()
            per.append({"bin": label, "calls": len(calls), "gave": len(gave),
                        "p": len(gave) / len(calls) if calls else None,
                        "ci": [boots[int(.025 * len(boots))], boots[int(.975 * len(boots)) - 1]] if boots else None,
                        "share_median": statistics.median(c[2] for c in gave) if gave else None})
        data[model] = {"games": len(games), "bins": per}
    DATA.write_text(json.dumps({"version": "v33", "cohort": "public_*4, seeds 4101--4105", "definitions": __doc__,
                                "models": data}, ensure_ascii=False, indent=1))


def main():
    if len(sys.argv) > 1:
        extract(sys.argv[1])
    data = json.loads(DATA.read_text())["models"]
    order = list(MODELS.values())
    off = {m: (i - 2) * .09 for i, m in enumerate(order)}  # spread the models within a bin
    left, right = [], []
    for m in order:
        c, mk = COLOR[m], MARK[m]
        pts = [(i + 1 + off[m], b) for i, b in enumerate(data[m]["bins"]) if b["p"] is not None]
        left.append(f"\\addplot[{c},line width=.9pt,mark={mk},mark size=1.6pt,forget plot,"
                    "error bars/.cd,y dir=both,y explicit,error bar style={line width=.5pt}] coordinates {"
                    + " ".join(f"({x:.2f},{b['p']:.4f}) +- (0,0)" if not b["ci"] else
                               f"({x:.2f},{b['p']:.4f}) += (0,{b['ci'][1] - b['p']:.4f}) -= (0,{b['p'] - b['ci'][0]:.4f})"
                               for x, b in pts) + "};")
        sh = [(i + 1 + off[m], b["share_median"]) for i, b in enumerate(data[m]["bins"]) if b["share_median"] is not None]
        if sh:
            right.append(f"\\addplot[{c},only marks,mark={mk},mark size=1.9pt] coordinates {{"
                         + " ".join(f"({x:.2f},{y:.4f})" for x, y in sh) + "};\n\\addlegendentry{" + m + "}")
    labels = ",".join(f"{{{lab}}}" for _, _, lab in BINS)
    tex = rf"""%% Generated by cogsci2027/tools/arena_risk.py from results/arena_v33_risk.json. Do not edit by hand.
%% v33, 5 games per model: every TALK call is one opportunity to give. x = own slack (tokens / the round's per-agent
%% charge) when the tick starts. Left: share of calls with a GIVE (95% interval resampling games). Right: median share
%% of the seat's tokens given in such a call.
\begin{{tikzpicture}}
\begin{{groupplot}}[sgaxis,
  group style={{group size=2 by 1,horizontal sep=1.3cm}},
  width=6.4cm,height=4.4cm,xmin=.5,xmax=4.5,xtick={{1,2,3,4}},xticklabels={{{labels}}},
  xlabel={{자기 여유 (그 틱 시작 때)}},xlabel style={{font=\scriptsize}},title style={{font=\small}}]
\nextgroupplot[ymin=0,ymax=.2,ytick={{0,.05,.1,.15,.2}},yticklabel style={{/pgf/number format/fixed,/pgf/number format/precision=2}},
  ylabel={{GIVE한 호출의 비율}},title={{주는 확률}}]
\fill[black!8] (axis cs:.5,0) rectangle (axis cs:1.5,.2);
{chr(10).join(left)}
\nextgroupplot[ymin=0,ymax=.65,ytick={{0,.2,.4,.6}},ylabel={{준 몫 (잔량 대비, 중앙값)}},title={{줄 때 준 몫}},
  legend style={{font=\tiny,at={{(.98,.98)}},anchor=north east,draw=black!25,inner sep=1pt}},legend cell align=left]
\fill[black!8] (axis cs:.5,0) rectangle (axis cs:1.5,.65);
{chr(10).join(right)}
\end{{groupplot}}
\end{{tikzpicture}}
"""
    (HERE / "ko/figures/arena_risk.tex").write_text(tex)
    for m in order:
        print(m, [(b["bin"], b["gave"], b["calls"], None if b["p"] is None else round(b["p"], 3),
                   None if not b["ci"] else [round(x, 3) for x in b["ci"]], b["share_median"]) for b in data[m]["bins"]])


if __name__ == "__main__":
    main()
