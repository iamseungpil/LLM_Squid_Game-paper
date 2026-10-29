"""Terminal in-arena distributions of the frozen e52_v33 cohort only.

Inputs: results/arena_v33_round_dynamics.json and results/raw_case_index.json
(five models, seeds 4101–4105). Keep the four original seats: finishers retain
their pre-prize balances; EXIT and shutdown are zero. EXIT bonuses and holdings
outside the arena are excluded, without reclassifying EXIT as death.
Bars average per-game metrics; points retain individual games. All-zero Gini is
undefined (excluded from its mean); its Sen and mean tokens remain zero.
"""
import hashlib
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

from inequality import distribution

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rewrite_20261025/figs"))
import paper_style as ps

SOURCE = ROOT / "results/arena_v33_round_dynamics.json"
CASES = ROOT / "results/raw_case_index.json"
ORDER = ["Fable 5.1", "GPT-6 Astra", "GPT-6 Sol", "Opus 5.5", "GPT-6 Luna"]
SHORT = ["Fable", "Astra", "Sol", "Opus", "Luna"]


def extract():
    data = json.loads(SOURCE.read_text())
    cases = {c["result"]["session_id"]: c["result"] for c in json.loads(CASES.read_text())}
    models = {}
    for model in ORDER:
        games = []
        for g in sorted(data["models"][model]["games"], key=lambda g: g["seed"]):
            terminal = g["rounds"][-1]
            observed = [r for r in g["rounds"] if r["observed"]][-1]
            assert terminal["round"] == 8 and terminal["tokens"] == observed["tokens"]
            result = cases[g["session_id"]]
            seats = list(result["starts"])
            assert [result["agents"][a]["final"] for a in seats] == terminal["tokens"]
            winners = set(result["final"]["winner"])
            assert len(winners) == g["finishers"]
            assert winners == {a for a in seats if result["agents"][a]["status"] == "in"}
            tokens = [result["agents"][a]["final"] if a in winners else 0 for a in seats]
            values = distribution(tokens)
            games.append(dict(seed=g["seed"], last_observed_round=observed["round"],
                              tokens=tokens, holdings_tokens=terminal["tokens"],
                              statuses=[result["agents"][a]["status"] for a in seats],
                              finishers=g["finishers"], **values))
        assert [g["seed"] for g in games] == list(range(4101, 4106))
        means, ns = {}, {}
        for metric in ["S", "G", "mu", "finishers"]:
            vals = [g[metric] for g in games if g[metric] is not None]
            means[metric], ns[metric] = float(np.mean(vals)), len(vals)
        models[model] = dict(games=games, means=means, n_defined=ns)
    payload = dict(source=str(SOURCE.relative_to(ROOT)),
                   source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                   status_source=str(CASES.relative_to(ROOT)),
                   status_source_sha256=hashlib.sha256(CASES.read_bytes()).hexdigest(),
                   definition=__doc__, models=models)
    (ROOT / "results/terminal_distribution_20261029.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2))
    return models


def draw_panels(axes, models, first_letter="a"):
    metrics = [("S", 1e4, "(a) Sen 지수", "만 토큰", 3.4),
               ("G", 1, "(b) Gini 계수", "Gini (0–1)", 1),
               ("mu", 1e4, "(c) 평균 토큰", "만 토큰", 4),
               ("finishers", 1, "(d) 평균 완주 인원", "명", 4.25)]
    for i, (ax, (key, scale, title, label, ymax)) in enumerate(zip(axes, metrics)):
        title = f"({chr(ord(first_letter) + i)})" + title[3:]
        means = [models[m]["means"][key] / scale for m in ORDER]
        ax.bar(range(5), means, width=.7, color="#D8E3ED", edgecolor="#697D8E", linewidth=.6)
        for x, model in enumerate(ORDER):
            for j, g in enumerate(models[model]["games"]):
                if g[key] is not None:
                    ax.scatter(x + (j - 2) * .11, g[key] / scale, color="#777777",
                               marker="o", s=12, linewidths=.4, zorder=3, clip_on=False)
        labels = [f"{short}\n({value:.2f})" if key == "G" else
                  f"{short}\n({value:.1f})" if key == "finishers" else f"{short}\n({value:.2f})"
                  for short, value in zip(SHORT, means)]
        ax.set(title=title, ylabel=label, ylim=(0, ymax), xticks=range(5), xticklabels=labels)
        ax.tick_params(axis="x", labelsize=6)
        ax.set_title(title, fontsize=8)
        ax.set_axisbelow(True)
        ax.grid(axis="y")
        if key == "G":
            ax.set_yticks([0, .25, .5, .75, 1])
        if key == "finishers":
            ax.set_yticks([0, 1, 2, 3, 4])


def plot(models):
    ps.use()
    fig, axes = plt.subplots(1, 4, figsize=(ps.COL2, 2.05))
    fig.subplots_adjust(left=.065, right=.985, bottom=.26, top=.85, wspace=.48)
    draw_panels(axes, models)
    ps.save(fig, str(ROOT / "ko/figures/figF1_terminal_distribution"))
    plt.close(fig)


if __name__ == "__main__":
    models = extract()
    plot(models)
    print(json.dumps({m: {"means": v["means"], "n": v["n_defined"]}
                      for m, v in models.items()}, ensure_ascii=False, indent=2))
