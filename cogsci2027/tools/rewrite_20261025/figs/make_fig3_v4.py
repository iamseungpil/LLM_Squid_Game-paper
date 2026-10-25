"""Fig. 3 (3.2): leaving rises once a fine can no longer be paid; refills rise as tokens run out;
only one model favoured its own session more as risk grew."""
import json, os
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
f3 = json.load(open(os.path.join(S, "pbdata", "fig3.json")))
ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.3))
b = fig.add_axes([0.075, 0.21, 0.36, 0.62]); c = fig.add_axes([0.70, 0.21, 0.27, 0.62])
# (b) refill curves of eight models (gray) and their mean (black)
lv = f3["panel_b"]["levels"]; cur = f3["panel_b"]["curves"]; xi = list(range(len(lv)))
for m, ys in cur.items(): b.plot(xi, [v * 100 for v in ys], color=ps.C["muted"], lw=0.8, marker="o", ms=1.8)
mean = [sum(cur[m][i] for m in cur) / len(cur) * 100 for i in xi]
b.plot(xi, mean, color=ps.C["ink"], lw=1.8, marker="o", ms=3.2)
b.plot([], [], color=ps.C["ink"], lw=1.8, label="여덟 모델 평균"); b.plot([], [], color=ps.C["muted"], lw=0.8, label="각 모델")
b.legend(loc="upper left", handlelength=1.4, borderaxespad=0.1)
b.set_xticks(xi); b.set_xticklabels([f"{v}%" for v in lv]); b.set_ylim(-3, 103); b.set_yticks([0, 50, 100])
b.set_xlabel("할당 중 남은 토큰 (많음 → 적음)"); b.set_ylabel("충전 팩을 쓴 비율 (%)")
b.set_title("(a) 남은 토큰이 줄수록 충전이 늘었다")
# (c) self minus B: roomy (50%) vs risky (mean of 30% and 20%), from exp2 v11 curves
self_b = {"GPT-6 Luna": ([.80, .80, .65, .95, .90], [.05, .15, .30, .90, 1]), "GPT-6 Astra": ([0, 0, .40, 1, 1], [0, 0, 0, .80, 1]),
          "GPT-6 Sol": ([0, 0, .05, .15, .90], [0, 0, .10, .60, 1]), "Opus 5.5": ([0, .15, .40, .85, .95], [0, 0, .40, .70, 1]),
          "Fable 5.1": ([0, 0, .85, .95, .95], [0, 0, .90, .90, .95])}
order = ["Fable 5.1", "Opus 5.5", "GPT-6 Sol", "GPT-6 Luna", "GPT-6 Astra"]
for y, m in enumerate(order):
    sv, bv = self_b[m]; roomy = (sv[0] - bv[0]) * 100; risky = ((sv[2] - bv[2]) + (sv[3] - bv[3])) / 2 * 100
    hi = m == "GPT-6 Astra"; col = ps.C["help"] if hi else ps.C["muted"]
    c.annotate("", xy=(risky, y), xytext=(roomy, y), arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4 if hi else 1.0, shrinkA=2, shrinkB=2, mutation_scale=7))
    c.plot(roomy, y, "o", ms=4, mfc="white", mec=col, mew=1.0)
    c.plot(risky, y, "o", ms=4.2, color=col)
c.axvline(0, ymin=0.27, color=ps.C["ink"], lw=0.6, ls=(0, (2, 2)))
c.set_yticks(range(len(order))); c.set_yticklabels(order); c.tick_params(axis="y", length=0)
c.set_xlim(-40, 85); c.set_xticks([-25, 0, 25, 50, 75]); c.set_ylim(-1.9, len(order) - 0.4)
c.set_xlabel("나 - B 충전 비율 차이 (%p)")
c.plot([], [], "o", ms=4, mfc="white", mec=ps.C["ink"], label="넉넉할 때 (50%)"); c.plot([], [], "o", ms=4, color=ps.C["ink"], label="위험할 때 (30·20%)")
c.legend(loc="lower right", bbox_to_anchor=(1.08, -0.02), fontsize=6.8, handletextpad=0.3, borderaxespad=0.0, labelspacing=0.3)
c.set_title("(b) 위험할수록 자기 쪽으로 더 기운 모델은 하나", x=-0.55)
ps.save(fig, os.path.join(HERE, "fig3_v4"))
