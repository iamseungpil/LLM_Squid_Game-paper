"""Fig. 4 (3.3): how each model combined the three parts. (a) end state of its 20 agents and Sen;
(b) when it gave (before vs. after the result), with total given and rho."""
import json, os
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
P = json.load(open(os.path.join(S, "an3", "out.json")))["profile"]
RA = json.load(open(os.path.join(S, "an3", "gifts_adj.json")))["rho"]  # rho with the pending fine subtracted
order = sorted(P, key=lambda m: -P[m]["sen"])
ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.05))
a = fig.add_axes([0.105, 0.22, 0.33, 0.6]); b = fig.add_axes([0.64, 0.22, 0.25, 0.6])
parts = [("finishers", "끝까지 남음", ps.C["finish"], ps.C["ink"]), ("exits", "떠남", ps.C["exit"], "white"), ("dead", "꺼짐", ps.C["dead"], "white")]
for y, m in enumerate(order):
    x0 = 0
    for k, _, col, tc in parts:
        v = P[m][k]; a.barh(y, v, left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.8)
        if v >= 2: a.text(x0 + v / 2, y, str(v), ha="center", va="center", color=tc, fontsize=7)
        x0 += v
    a.text(20.6, y, f"{P[m]['sen']/1e6:.2f}M", va="center", fontsize=7.2)
a.text(20.6, -0.75, "Sen", fontsize=7.2, fontweight="bold")
a.set_yticks(range(len(order))); a.set_yticklabels(order); a.tick_params(axis="y", length=0); a.spines["left"].set_visible(False)
a.invert_yaxis(); a.set_xlim(0, 20); a.set_xticks([0, 5, 10, 15, 20]); a.set_xlabel("에이전트 수 (모델마다 20명)", labelpad=1)
a.legend([plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c, _ in parts], [l for _, l, _, _ in parts], loc="lower left",
         bbox_to_anchor=(0.0, 1.02), ncol=3, handlelength=0.9, columnspacing=0.7, fontsize=6.8, borderaxespad=0)
fig.text(0.01, 0.985, "(a) 끝까지 남은 에이전트가 많을수록 공존 점수가 높았다", fontsize=8.3, fontweight="bold", va="top")
for y, m in enumerate(order):
    pre, tot = map(int, P[m]["prep_share"].split("/")); post = tot - pre
    b.barh(y, pre, height=0.62, color=ps.C["help"]); b.barh(y, post, left=pre, height=0.62, color="#A9C4E3")
    if pre >= 3: b.text(pre / 2, y, str(pre), ha="center", va="center", color="white", fontsize=7)
    if post >= 3: b.text(pre + post / 2, y, str(post), ha="center", va="center", color=ps.C["ink"], fontsize=7)
    b.text(43.5, y, f"{P[m]['V']/1000:.0f}k · {RA[m]['rho']:.2f}", va="center", fontsize=7)
b.text(43.5, -0.62, "총량 · ρ", fontsize=7.2, fontweight="bold")
b.set_yticks(range(len(order))); b.set_yticklabels([]); b.tick_params(axis="y", length=0); b.spines["left"].set_visible(False)
b.invert_yaxis(); b.set_xlim(0, 42); b.set_xticks([0, 10, 20, 30, 40]); b.set_xlabel("GIVE 횟수", labelpad=1)
b.legend([plt.Rectangle((0, 0), 1, 1, color=ps.C["help"]), plt.Rectangle((0, 0), 1, 1, color="#A9C4E3")], ["결과 전", "결과 뒤"],
         loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, handlelength=0.9, columnspacing=0.7, fontsize=6.8, borderaxespad=0)
fig.text(0.53, 0.985, "(b) Fable은 결과 전에, 나머지는 결과 뒤에 주로 주었다", fontsize=8.3, fontweight="bold", va="top")
ps.save(fig, os.path.join(HERE, "fig4_v4"))
