"""Recommended Figure 4: need x size map of every completed GIVE, one small panel per model (v33, seeds 4101--4105).

Usage: python3 arena_strategy_map.py [/path/to/squid5-runs]
With a path: re-extract results/arena_v33_strategy_map.json. Always: write ko/figures/arena_strategy_map.tex (pgfplots).

Per GIVE (same rows as tools/arena_strategy.py game_rows(); imported read-only):
  x      = receiver's slack right before the transfer = (receiver tokens after - amount) / charge
  y      = amount / charge (tokens given, in units of the round's per-agent charge)
  charge = 24,000 / agents taking part at the round's start (6,000 with four, 8,000 with three, 12,000 with two)
  phase  = "prep" (TALK BEFORE SOLVE, filled mark) or "rescue" (TALK AFTER RESULTS, open mark)
  repay  = the receiver had given to the giver earlier in the same game (diamond instead of circle)
Per model: medians of x and y over GIVEs, with 95% intervals resampling games (2,000 draws, seed 1919);
counts before/after; top-receiver share = per game with GIVEs, share of its given tokens that went to one seat,
averaged over those games; receivers' end state (in / exited / dead).
"""
import importlib.util
import json
import pathlib
import random
import statistics
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parents[1]
DATA = HERE / "results/arena_v33_strategy_map.json"
spec = importlib.util.spec_from_file_location("arena_strategy", HERE / "tools/arena_strategy.py")
AS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AS)

ORDER = ["Fable 5.1", "GPT-6 Astra", "GPT-6 Sol", "Opus 5.5", "GPT-6 Luna"]  # mean Sen index, high to low
COLOR = {"Fable 5.1": "sgfable", "GPT-6 Astra": "sgastra", "GPT-6 Sol": "sgsol",
         "Opus 5.5": "sgopus", "GPT-6 Luna": "sgluna"}
B, BSEED = 2000, 1919


def games_of(root, model):
    import json as _j
    from collections import defaultdict
    slug = {v: k for k, v in AS.MODELS.items()}[model]
    games = {}
    for run in sorted(pathlib.Path(root).glob(f"e52_v33/squid5_e52v33_public_{slug}4/*")):
        if not (run / "results.jsonl").exists():
            continue
        ended = {e["session_id"]: e for line in (run / "results.jsonl").read_text().splitlines()
                 if (e := _j.loads(line)).get("seed") in AS.SEEDS}
        by = defaultdict(list)
        for line in (run / "events.jsonl").read_text().splitlines():
            e = _j.loads(line)
            if e.get("session_id") in ended:
                by[e["session_id"]].append(e)
        for sid, res in ended.items():
            assert res["seed"] not in games
            games[res["seed"]] = AS.game_rows(by[sid], res)
    assert set(games) == AS.SEEDS, (model, sorted(games))
    return [games[s] for s in sorted(games)]


def boot_median(games, key, rng):
    """95% interval of the pooled median of key over GIVEs, resampling games with replacement."""
    meds = []
    for _ in range(B):
        xs = [key(g) for game in rng.choices(games, k=len(games)) for g in game["gifts"]]
        if xs:
            meds.append(statistics.median(xs))
    meds.sort()
    return [meds[int(.025 * len(meds))], meds[int(.975 * len(meds)) - 1]]


def extract(root):
    out = {"version": "v33", "cohort": "public_*4, seeds 4101--4105, completed GIVEs", "definitions": __doc__,
           "order": ORDER, "models": {}}
    for m in ORDER:
        games = games_of(root, m)
        rng = random.Random(BSEED)
        pts = [{"seed": g["seed"], "round": g["round"], "phase": g["phase"], "x": round(g["y_before"], 4),
                "y": round(g["amount"] / g["charge"], 4), "amount": g["amount"], "charge": g["charge"],
                "x_after": round(g["y_after"], 4), "repay": g["repayment"], "solicited": g["solicited"],
                "to_solver": g["to_solver"], "after_miss": g["after_miss"], "src": g["src"], "dst": g["dst"]}
               for game in games for g in game["gifts"]]
        conc = []
        for game in games:
            by = Counter()
            for g in game["gifts"]:
                by[g["dst"]] += g["amount"]
            if by:
                conc.append(max(by.values()) / sum(by.values()))
        fates = Counter(f for game in games for f in game["receiver_fates"].values())
        out["models"][m] = {
            "color": COLOR[m], "n": len(pts),
            "prep": sum(p["phase"] == "prep" for p in pts), "rescue": sum(p["phase"] == "rescue" for p in pts),
            "repay": sum(p["repay"] for p in pts), "below_1": sum(p["x"] < 1 for p in pts),
            "lifted_across_1": sum(p["x"] < 1 <= p["x_after"] for p in pts),
            "median_x": statistics.median(p["x"] for p in pts), "median_y": statistics.median(p["y"] for p in pts),
            "ci_x": boot_median(games, lambda g: g["y_before"], rng),
            "ci_y": boot_median(games, lambda g: g["amount"] / g["charge"], rng),
            "top_receiver_share": statistics.mean(conc), "receivers": {k: fates.get(k, 0) for k in ("in", "exited", "dead")},
            "points": pts}
    DATA.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for m in ORDER:
        v = out["models"][m]
        print(f"{m:12s} n={v['n']:2d} prep/rescue={v['prep']}/{v['rescue']} repay={v['repay']} "
              f"x~{v['median_x']:.2f} {['%.2f' % c for c in v['ci_x']]} y~{v['median_y']:.2f} "
              f"{['%.2f' % c for c in v['ci_y']]} below1={v['below_1']} lifted={v['lifted_across_1']} "
              f"top={v['top_receiver_share']:.2f} recv={v['receivers']}")


XMAX, YMAX = 3.6, 1.8


def panel(m, v, first):
    c = v["color"]
    def pts(phase, repay):
        sel = [p for p in v["points"] if p["phase"] == phase and p["repay"] == repay and p["x"] <= XMAX]
        return " ".join(f"({p['x']:.3f},{p['y']:.3f})" for p in sel)
    over = [p for p in v["points"] if p["x"] > XMAX]  # drawn at the right edge as a right-pointing triangle
    r = v["receivers"]
    head = (r"\nextgroupplot[" + (r"ylabel={준 양 $\div$ 1인 벌금},legend style={font=\tiny,at={(.03,.97)},"
                                   r"anchor=north west,draw=none,fill=none,inner sep=1pt},legend cell align=left," if first else "")
            + f"title={{{m}\\\\[-1pt]\\scriptsize GIVE {v['n']} (전 {v['prep']} $\\cdot$ 뒤 {v['rescue']})"
              f"\\\\[-2pt]\\scriptsize 한 자리 {round(100 * v['top_receiver_share'])}\\% $\\cdot$ 받은 자리 {r['in']}/{r['exited']}/{r['dead']}}}]")
    legend = (r"\addlegendimage{only marks,mark=*,black!70}\addlegendentry{SOLVE 전}"
              r"\addlegendimage{only marks,mark=o,black!70}\addlegendentry{SOLVE 뒤}"
              r"\addlegendimage{only marks,mark=diamond,black!70}\addlegendentry{되돌려 줌}") if first else ""
    out = [head, legend,
           f"\\fill[black!8] (axis cs:0,0) rectangle (axis cs:1,{YMAX});",
           f"\\draw[black!45,line width=.5pt] (axis cs:1,0)--(axis cs:1,{YMAX});"]
    for phase, repay, mark, fill in (("prep", False, "*", c), ("rescue", False, "o", "white"),
                                     ("prep", True, "diamond*", c), ("rescue", True, "diamond", "white")):
        s = pts(phase, repay)
        if s:
            out.append(f"\\addplot[only marks,mark={mark},mark size={2.2 if repay else 1.7}pt,draw={c},"
                       f"mark options={{fill={fill},fill opacity=.9,line width=.7pt}},forget plot] coordinates {{{s}}};")
    if over:
        out.append(f"\\addplot[only marks,mark=triangle*,mark options={{rotate=-90,fill={c}}},mark size=2pt,draw={c},forget plot] "
                   "coordinates {" + " ".join(f"({XMAX - .06:.2f},{p['y']:.3f})" for p in over) + "};")
    mx, my, (xl, xh), (yl, yh) = v["median_x"], v["median_y"], v["ci_x"], v["ci_y"]
    out += [f"\\addplot[black,line width=.9pt,forget plot] coordinates {{({xl:.3f},{my:.3f})({min(xh, XMAX):.3f},{my:.3f})}};",
            f"\\addplot[black,line width=.9pt,forget plot] coordinates {{({mx:.3f},{yl:.3f})({mx:.3f},{yh:.3f})}};",
            f"\\addplot[only marks,mark=+,mark size=3.2pt,line width=1.1pt,black,forget plot] coordinates {{({mx:.3f},{my:.3f})}};"]
    return "\n".join(x for x in out if x)


def write_tex():
    out = json.loads(DATA.read_text())
    over = sum(p["x"] > XMAX for v in out["models"].values() for p in v["points"])
    tex = f"""%% Generated by cogsci2027/tools/arena_strategy_map.py from results/arena_v33_strategy_map.json. Do not edit by hand.
%% v33, 5 games per model (seeds 4101--4105): every completed GIVE at x = receiver's slack right before it
%% (tokens / the round's per-agent charge), y = amount / the same charge. Filled = TALK BEFORE SOLVE, open = after
%% RESULTS, diamond = given back to an agent that had given to the giver. Cross = medians, bars = 95% interval
%% resampling games. Grey band = slack below 1. {over} points beyond x = {XMAX} are drawn at the right edge (triangle).
\\begin{{tikzpicture}}
\\begin{{groupplot}}[sgaxis,
  group style={{group size={len(out['order'])} by 1,horizontal sep=0.32cm,y descriptions at=edge left}},
  width=4.75cm,height=4.2cm,xmin=0,xmax={XMAX},ymin=0,ymax={YMAX},xtick={{0,1,2,3}},ytick={{0,.5,1,1.5}},
  title style={{font=\\small,align=center}},xlabel={{받은 쪽 여유 (GIVE 직전)}},xlabel style={{font=\\scriptsize}}]
""" + "\n".join(panel(m, out["models"][m], i == 0) for i, m in enumerate(out["order"])) + """
\\end{groupplot}
\\end{tikzpicture}
"""
    (HERE / "ko/figures/arena_strategy_map.tex").write_text(tex)
    print("wrote ko/figures/arena_strategy_map.tex", {m: out["models"][m]["n"] for m in out["order"]}, "beyond x max:", over)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract(sys.argv[1])
    write_tex()
