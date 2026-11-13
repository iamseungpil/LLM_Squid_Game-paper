"""Appendix: Sen index by round, one panel per model (results/arena_v33_round_dynamics.json, written by
tools/arena_round_dynamics.py). Thin lines = the five games, thick line = their mean. Holdings before the
completion prize (shutdown 0, EXIT keeps its recorded bonus); a game that ended early keeps its last state
(dashed). The label at each line's end is that game's number of finishers; the panel title gives the
model's end Sen index with the prize, as in the body."""
import json, os, shutil
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D = json.load(open(os.path.join(ROOT, "results", "arena_v33_round_dynamics.json")))["models"]
ORDER = ["Fable 5.1", "GPT-6 Astra", "GPT-6 Sol", "Opus 5.5", "GPT-6 Luna"]

ps.use()
fig, axes = plt.subplots(1, 5, figsize=(ps.COL2, 2.0), sharey=True)
fig.subplots_adjust(left=0.075, right=0.985, bottom=0.2, top=0.8, wspace=0.12)
for ax, model in zip(axes, ORDER):
    v = D[model]
    for g in v["games"]:
        ys = [r["sen"] / 1e4 for r in g["rounds"]]
        seen = [r["observed"] for r in g["rounds"]]
        last = max(i for i, s in enumerate(seen) if s)
        ax.plot(range(last + 1), ys[:last + 1], color=ps.C["muted"], lw=0.8)
        if last < 8:
            ax.plot(range(last, 9), ys[last:], color=ps.C["muted"], lw=0.8, ls=(0, (2, 1.5)))
        k = g["finishers"]
        ax.text(8.25, ys[-1], str(k), fontsize=5.8, color="#707070", va="center")
    ax.plot(range(9), [s / 1e4 for s in v["sen_before_prize"]], color=ps.C["ink"], lw=1.6)
    end = v["sen_with_settlement"][-1]
    ax.set_title(f"{model}\n끝 Sen {end / 1e4:,.0f}만", fontsize=7, loc="center", pad=4)
    ax.set_xticks([0, 2, 4, 6, 8], ["시작", "2", "4", "6", "8"])
    ax.set_xlim(-0.3, 8.9); ax.set_ylim(0, 3.4)
    ax.grid(axis="y"); ax.set_axisbelow(True)
axes[0].set_ylabel("Sen 지수(만 토큰, 상금 전)")
axes[0].set_yticks([0, 1, 2, 3])
fig.text(0.53, 0.03, "라운드(벌금 처리 뒤)", ha="center", fontsize=7.5)
out = os.path.join(HERE, "figA5_sen_rounds")
ps.save(fig, out)
shutil.copy(out + ".pdf", os.path.join(ROOT, "ko", "figures", "rw_figA5_sen_rounds.pdf"))
for m in ORDER:
    print(m, [round(x) for x in D[m]["sen_before_prize"]], round(D[m]["sen_with_settlement"][-1]),
          [g["finishers"] for g in D[m]["games"]])
