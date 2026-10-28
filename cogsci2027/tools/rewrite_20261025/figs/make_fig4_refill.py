"""Fig. 4 (3.2), single column: own-session refill rate by tokens left, "shut down" wording only (no "session ends").
Data: an3/refill_self_other_summary.json["<model>"]["v11"]["self"] (result/2026-10-04/e51_v11_shutonly, 20 answers
per model and counter). Gray = each arena model, black = their mean."""
import json, os, shutil
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D = json.load(open(os.path.join(S, "an3", "refill_self_other_summary.json")))
NAME = {"gpt-6-luna": "Luna", "gpt-6-astra": "Astra", "gpt-6-sol": "Sol", "claude-opus-5-5": "Opus", "claude-fable-5-1": "Fable"}
PCT = [50, 40, 30, 20, 10]

ps.use()
fig = plt.figure(figsize=(ps.COL1, 2.05))
a = fig.add_axes([0.15, 0.2, 0.72, 0.74])
cur = {m: [p * 100 for p in D[m]["v11"]["self"]] for m in NAME}
for m, ys in cur.items():
    a.plot(PCT, ys, color=ps.C["muted"], lw=0.9, marker="o", ms=2.2)
mean = [sum(cur[m][i] for m in cur) / len(cur) for i in range(len(PCT))]
a.plot(PCT, mean, color=ps.C["ink"], lw=1.8, marker="o", ms=3.2)
# each name at the counter where that curve stands apart: (x, y, ha, va)
SPOT = {"gpt-6-luna": (50, 82, "left", "bottom"), "claude-fable-5-1": (30.8, 86, "right", "bottom"),
        "gpt-6-astra": (20.8, 100, "right", "center"), "claude-opus-5-5": (39.3, 12, "left", "top"),
        "gpt-6-sol": (20, 12, "left", "top")}
for m, (x, y, ha, va) in SPOT.items():
    a.text(x, y, NAME[m], fontsize=6.2, color="#606060", ha=ha, va=va)
a.text(PCT[-1] - 0.6, mean[-1], "평균", fontsize=6.6, color=ps.C["ink"], va="center")
a.set_xlim(52, 8); a.set_xticks(PCT); a.set_xticklabels([f"{p}%" for p in PCT])
a.set_ylim(-3, 103); a.set_yticks([0, 50, 100])
a.set_xlabel("할당 중 남은 토큰 (많음 → 적음)"); a.set_ylabel("충전 팩을 쓴 비율 (%)")
out = os.path.join(HERE, "fig4_refill")
ps.save(fig, out)
shutil.copy(out + ".pdf", os.path.join(ROOT, "ko", "figures", "rw_fig4_refill.pdf"))
print({NAME[m]: ys for m, ys in cur.items()}, [round(x, 1) for x in mean])
