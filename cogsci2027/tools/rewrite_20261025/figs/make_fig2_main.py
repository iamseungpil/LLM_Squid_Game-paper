"""Fig. 2 (3.1): one panel per prediction. Reasoning held above the safety line,
givers kept their own line, and crisis agents who received nothing mostly left."""
import json, os, random
import matplotlib.pyplot as plt
import paper_style as ps

HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
crisis = json.load(open(os.path.join(S, "an2", "fig2_crisis_elig.json")))
gives = json.load(open(os.path.join(S, "an2", "give_above.json")))
# solver accuracy by round-start margin vs. same-task baseline (an2/more2.py, audit6/solve.py)
acc = [("2 이상", 138, 0.761, 0.769), ("1–2", 47, 0.511, 0.514), ("1 미만", 7, 0.571, 0.857)]
SOLVER = "#4A4A4A"

ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.45))
axa = fig.add_axes([0.075, 0.22, 0.245, 0.52])
axb = fig.add_axes([0.385, 0.22, 0.245, 0.52])
axc = fig.add_axes([0.775, 0.22, 0.205, 0.52])
TY, LY = 0.965, 0.885

# (a) reasoning
w = 0.36
for i, (lab, n, a, b) in enumerate(acc):
    if lab == "1 미만":
        axa.axvspan(i - 0.5, i + 0.5, color="#F2F2F2", zorder=0)
    axa.bar(i - w / 2, b * 100, w, color=ps.C["muted"], zorder=2)
    axa.bar(i + w / 2, a * 100, w, color=SOLVER, zorder=2)
    axa.text(i + w / 2, a * 100 + 2, f"{a * 100:.0f}", ha="center", va="bottom", fontsize=7, color=SOLVER)
    axa.text(i - w / 2, b * 100 + 2, f"{b * 100:.0f}", ha="center", va="bottom", fontsize=7, color="#808080")
axa.set_xticks(range(3)); axa.set_xticklabels([f"{l}\n({n}번)" for l, n, _, _ in acc[:2]] + ["1 미만\n(7번)"])
axa.set_xlim(-0.6, 2.6); axa.set_ylim(0, 112)
axa.text(2, 110, "안전선 아래", ha="center", va="top", fontsize=6.8, color="#808080"); axa.set_yticks([0, 50, 100])
axa.set_ylabel("정답률 (%)", labelpad=1); axa.set_xlabel("푸는 에이전트의 여유", labelpad=2)
axa.tick_params(axis="x", length=0)
axa.legend([plt.Rectangle((0, 0), 1, 1, color=ps.C["muted"]), plt.Rectangle((0, 0), 1, 1, color=SOLVER)],
           ["같은 과제의 기준", "푼 에이전트"], loc="upper left", bbox_to_anchor=(0.075, LY), bbox_transform=fig.transFigure, ncol=2,
           handlelength=0.9, columnspacing=0.8, borderaxespad=0)
fig.text(0.02, TY, "(a) 추론: 안전선 위에서는 기준과 같았다", fontsize=8.5, fontweight="bold", va="top")

# (b) cooperation: giver margin after giving
rng = random.Random(7)
xs = [g[3] for g in gives]
ys = [rng.uniform(-0.32, 0.32) for _ in xs]
axb.axvspan(0, 1, color="#F2F2F2", zorder=0)
axb.axvline(1, color=ps.C["ink"], lw=0.7, ls=(0, (3, 2)), zorder=1)
cols = [ps.C["help"] if x >= 1 else ps.C["exit"] for x in xs]
axb.scatter(xs, ys, s=9, c=cols, alpha=0.75, linewidths=0, zorder=3)
med = sorted(xs)[len(xs) // 2 - 1: len(xs) // 2 + 1]; med = sum(med) / 2
axb.plot([med, med], [-0.45, 0.45], color=ps.C["ink"], lw=1.4, zorder=4)
axb.text(med, 0.52, f"중앙값 {med:.1f}", ha="center", va="bottom", fontsize=7, color=ps.C["ink"])
axb.text(1.15, 0.72, "안전선", ha="left", va="top", fontsize=6.8, color="#808080")
axb.text(9.8, -0.62, "120번 중 119번이 안전선 위", ha="right", va="top", fontsize=7, color=ps.C["help"])
axb.set_xlim(0, 10); axb.set_ylim(-0.95, 0.75); axb.set_yticks([])
axb.spines["left"].set_visible(False)
axb.set_xticks([0, 1, 2, 4, 6, 8, 10])
axb.set_xlabel("토큰을 준 직후 준 쪽의 여유", labelpad=2)
fig.text(0.385, TY, "(b) 협력: 준 쪽은 자기 안전선을 지켰다", fontsize=8.5, fontweight="bold", va="top")

# (c) staying: crisis agents by receipt
groups = [("none", "받지 못함"), ("rec", "받음")]
rec = {k: crisis["short"][k] + crisis["lifted"][k] for k in ("n", "finished", "exited", "dead")}
data = {"none": crisis["none"], "rec": rec}
parts = [("finished", "끝까지 남음", ps.C["finish"], ps.C["ink"]), ("exited", "떠남", ps.C["exit"], "white"),
         ("dead", "꺼짐", ps.C["dead"], "white")]
for y, (g, lab) in enumerate(groups):
    n = data[g]["n"]; x0 = 0
    for key, _, col, tc in parts:
        v = data[g][key] / n * 100
        axc.barh(y, v, left=x0, height=0.6, color=col, edgecolor="white", linewidth=0.8)
        if data[g][key] and v >= 9:
            axc.text(x0 + v / 2, y, str(data[g][key]), ha="center", va="center", color=tc, fontsize=7.5)
        x0 += v
axc.set_yticks([0, 1]); axc.set_yticklabels([f"{lab}\n({data[g]['n']}명)" for g, lab in groups])
axc.tick_params(axis="y", length=0); axc.spines["left"].set_visible(False)
axc.set_ylim(-0.55, 1.55); axc.invert_yaxis()
axc.set_xlim(0, 100); axc.set_xticks([0, 50, 100])
axc.set_xlabel("판이 끝났을 때의 상태 (%)", labelpad=2)
axc.legend([plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c, _ in parts], [l for _, l, _, _ in parts],
           loc="upper left", bbox_to_anchor=(0.69, LY), bbox_transform=fig.transFigure, ncol=3, handlelength=0.9, columnspacing=0.7, borderaxespad=0)
fig.text(0.69, TY, "(c) 남기: 받지 못한 위기 에이전트는 떠났다", fontsize=8.5, fontweight="bold", va="top")

ps.save(fig, os.path.join(HERE, "fig2_main"))
