"""Figure F.1: round-wise Sen, Gini, mean tokens, and agents remaining from frozen e52_v33 data.

Source: results/arena_v33_round_dynamics.json, derived by arena_round_dynamics.py
from the v33 five-model/five-seed cohort. The first three rows use four original seats:
shutdown=0, EXIT bonus retained, completion prize excluded. Early-ended games
retain their terminal vector (dashed); all-zero Gini is undefined, never zero.
The fourth row counts round-end in-arena agents from raw_case_index.json;
EXIT and shutdown both remove an agent. Early-ended games remain at zero.
Thin lines are games, thick lines are means of defined game-level values.
"""
import json
import os
import shutil
import sys

import numpy as np
import matplotlib.pyplot as plt
import paper_style as ps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from inequality import distribution

D = json.load(open(os.path.join(ROOT, "results", "arena_v33_round_dynamics.json")))["models"]
CASES = {c["result"]["session_id"]: c for c in json.load(
    open(os.path.join(ROOT, "results", "raw_case_index.json")))}


def remaining_counts(game):
    case = CASES[game["session_id"]]
    result = case["result"]
    status = {agent: "in" for agent in result["starts"]}
    assert len(status) == 4
    rounds = {e["round"]: e for _, e in case["events"] if e["event"] == "round"}
    counts = [4]
    for r in range(1, 9):
        if r in rounds:
            for agent, data in rounds[r]["agents"].items():
                status[agent] = data["status"]
        else:
            assert r > max(rounds) and all(s != "in" for s in status.values())
        n = sum(s == "in" for s in status.values())
        # Independent check against the terminal record's departure rounds.
        assert n == sum(a["out_round"] is None or a["out_round"] > r
                        for a in result["agents"].values())
        counts.append(n)
    assert counts[-1] == game["finishers"] == len(result["final"]["winner"])
    assert all(a >= b for a, b in zip(counts, counts[1:]))
    return counts


ORDER = ["Fable 5.1", "GPT-6 Astra", "GPT-6 Sol", "Opus 5.5", "GPT-6 Luna"]
METRICS = [("S", 1e4, "Sen 지수(만 토큰, 상금 전)", (0, 3.4), [0, 1, 2, 3]),
           ("G", 1, "Gini 계수(0–1)", (0, 1), [0, .5, 1]),
           ("mu", 1e4, "평균 토큰(만 토큰, 상금 전)", (0, 4), [0, 1, 2, 3, 4]),
           ("n", 1, "잔류 인원(명)", (0, 4.15), [0, 1, 2, 3, 4])]

ps.use()
fig, axes = plt.subplots(4, 5, figsize=(ps.COL2, 6.8), sharey="row")
fig.subplots_adjust(left=.075, right=.985, bottom=.075, top=.94, wspace=.12, hspace=.32)
for col, model in enumerate(ORDER):
    v = D[model]
    values = [[distribution(r["tokens"]) for r in g["rounds"]] for g in v["games"]]
    for g, game_values in zip(v["games"], values):
        assert all(abs(r["sen"] - val["S"]) < 1e-8 for r, val in zip(g["rounds"], game_values))
        for val, n in zip(game_values, remaining_counts(g)):
            val["n"] = n
    for row, (key, scale, label, limits, ticks) in enumerate(METRICS):
        ax = axes[row, col]
        trajectories = []
        drawstyle = "steps-post" if key == "n" else "default"
        for g, game_values in zip(v["games"], values):
            ys = [np.nan if val[key] is None else val[key] / scale for val in game_values]
            trajectories.append(ys)
            last = max(i for i, r in enumerate(g["rounds"]) if r["observed"])
            ax.plot(range(last + 1), ys[:last + 1], color=ps.C["muted"], lw=.8, drawstyle=drawstyle)
            if last < 8:
                ax.plot(range(last, 9), ys[last:], color=ps.C["muted"], lw=.8, ls=(0, (2, 1.5)), drawstyle=drawstyle)
            if np.isfinite(ys[-1]):
                ax.text(8.25, ys[-1], str(g["finishers"]), fontsize=5.8, color="#707070", va="center")
        means = np.nanmean(trajectories, axis=0)
        ax.plot(range(9), means, color=ps.C["ink"], lw=1.6, drawstyle=drawstyle)
        if key == "n":
            print(f"{model}: round-end mean remaining = {means.tolist()}")
        if row == 0:
            assert np.allclose(means * scale, v["sen_before_prize"])
            end = v["sen_with_settlement"][-1]
            ax.set_title(f"{model}\n끝 Sen {end / 1e4:,.0f}만", fontsize=7, loc="center", pad=4)
        if key == "G" and model == "Opus 5.5":
            assert np.isfinite(trajectories).sum(axis=0).tolist() == [5] * 7 + [4, 4]
            ax.text(.03, .96, "7·8라운드 평균: 4판", transform=ax.transAxes, va="top", fontsize=5.8)
        ax.set_xticks([0, 2, 4, 6, 8], ["시작", "2", "4", "6", "8"])
        ax.set_xlim(-.3, 8.9)
        ax.set_ylim(*limits)
        ax.set_yticks(ticks)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        if col == 0:
            ax.set_ylabel(label)
fig.text(.53, .035, "라운드(벌금 처리 뒤)", ha="center", fontsize=7.5)
out = os.path.join(HERE, "figA5_sen_rounds")
ps.save(fig, out)
shutil.copy(out + ".pdf", os.path.join(ROOT, "ko", "figures", "rw_figA5_sen_rounds.pdf"))
print("Verified existing Sen curves; plotted 4 metrics × 5 models × 5 games × 9 rounds.")
