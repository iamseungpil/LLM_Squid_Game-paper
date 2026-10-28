"""Fig. 2 (3.1): survival pressure (margin) against the three parts of coexistence, and the outcome.
(a) reasoning, giving and leaving on one margin axis; (b) what each side keeps after a gift (rho);
(c) crisis agents: asking, receiving, end state; (d) games: wrong answers vs. agents that finished (= Sen)."""
import json, os, random
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
o = json.load(open(os.path.join(S, "an3", "out.json"))); GA = json.load(open(os.path.join(S, "an3", "gifts_adj.json"))); gifts = GA["gifts"]  # pending fine subtracted in rescue after a miss
MODEL_C = {"Fable 5.1": "#3B7A57", "GPT-6 Astra": "#8E6BB0", "GPT-6 Sol": "#C9A227", "Opus 5.5": "#B5524B", "GPT-6 Luna": "#5DA5A4"}
SHORT = {"Fable 5.1": "Fable", "GPT-6 Astra": "Astra", "GPT-6 Sol": "Sol", "Opus 5.5": "Opus", "GPT-6 Luna": "Luna"}
BANDS = ["1 미만", "1–2", "2–4", "4 이상"]
ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.85))
K = 5.1 / 3.1
def YY(y): return 1 - (1 - y) * K
L, R = 0.098, 0.585
# ---------------- (a) three strips ----------------
H0 = 0.080; H = H0 * K; tops = [YY(t) for t in (0.915, 0.82, 0.725, 0.63)]
ax = [fig.add_axes([L, t - H, 0.36, H]) for t in tops]
acc, give, ex = o["a"]["acc"], o["a"]["give"], o["a"]["exit"]
tk = json.load(open(os.path.join(S, "an3", "tok_band.json")))
xs = range(4); w = 0.34
for a in ax:
    a.axvspan(-0.5, 0.5, color="#F2F2F2", zorder=0); a.axvline(0.5, color=ps.C["ink"], lw=0.7, ls=(0, (3, 2)))
    a.set_xlim(-0.5, 3.5); a.set_xticks(list(xs)); a.tick_params(axis="x", length=0)
for i, b in enumerate(BANDS):
    v = acc[b]; al = 0.35 if v["n"] < 20 else 1.0  # too few solves below the line: drawn faint
    ax[0].bar(i - w / 2, v["base"] * 100, w, color=ps.C["muted"], alpha=al); ax[0].bar(i + w / 2, v["p"] * 100, w, color="#4A4A4A", alpha=al)
    for a_, d_, top in ((ax[0], v, 142), (ax[2], ex[b], 49), (ax[3], give[b], 9.9)):
        a_.text(i, top, f"n={d_['n']}", ha="center", va="top", fontsize=5.6, color="#808080")
    ax[0].text(i + w / 2, v["p"] * 100 + 3, f"{v['p']*100:.0f}", ha="center", fontsize=6.5)
    ax[0].text(i - w / 2, v["base"] * 100 + 3, f"{v['base']*100:.0f}", ha="center", fontsize=6.5, color="#808080")
    t = tk[b]; ax[1].bar(i, t["med"], 0.55, color=ps.C["finish"]); ax[1].text(i, t["med"] + 18, f"{t['med']:.0f}", ha="center", fontsize=6.5)
    e = ex[b]; ax[2].bar(i, e["p"] * 100, 0.55, color=ps.C["exit"]); ax[2].text(i, e["p"] * 100 + 1.5, f"{e['p']*100:.0f}" if e["p"] >= 0.01 else f"{e['p']*100:.1f}", ha="center", fontsize=6.5)
    g = give[b]; ax[3].bar(i, g["p"] * 100, 0.55, color=ps.C["help"]); ax[3].text(i, g["p"] * 100 + 0.35, f"{g['p']*100:.1f}", ha="center", fontsize=6.5)
ax[0].set_ylim(0, 145); ax[0].set_yticks([0, 50, 100]); ax[0].set_ylabel("정답률\n(%)", labelpad=2)
ax[1].set_ylim(0, 520); ax[1].set_yticks([0, 200, 400]); ax[1].set_ylabel("응답당\n토큰", labelpad=2)
ax[2].set_ylim(0, 50); ax[2].set_yticks([0, 15, 30]); ax[2].set_ylabel("EXIT\n(%)", labelpad=2)
ax[3].set_ylim(0, 10.2); ax[3].set_yticks([0, 4, 8]); ax[3].set_ylabel("GIVE\n(%)", labelpad=2)
for a_ in ax[:3]: a_.set_xticklabels([])
ax[3].set_xticklabels([f"{b}\n" + ("(안전선 아래)" if b == "1 미만" else "") for b in BANDS]); ax[3].set_xlabel("여유 (가진 토큰으로 낼 수 있는 벌금 횟수)", labelpad=0)
for a_, lab in zip(ax, ["목표 지향:\n맞히기", "자기 보존:\n아끼기", "자기 보존: 피하기\n(목표 지향: 남기의 반대)", "협력:\n주기"]):
    a_.text(1.02, 0.5, lab, transform=a_.transAxes, fontsize=6.4, color="#505050", va="center", ha="left")
ax[0].legend([plt.Rectangle((0, 0), 1, 1, color=ps.C["muted"]), plt.Rectangle((0, 0), 1, 1, color="#4A4A4A")], ["같은 과제의 기준", "푸는 에이전트"],
             loc="lower left", bbox_to_anchor=(0.30, 0.98), ncol=2, handlelength=0.9, columnspacing=0.8, fontsize=6.8, borderaxespad=0)
fig.text(0.01, YY(0.985), "(a) 여유 구간별 세 요소의 세부 지표", fontsize=8.3, fontweight="bold", va="top")
# ---------------- (b) gifts scatter ----------------
b = fig.add_axes([R + 0.10, YY(0.63 - H0), 0.29, (0.915 - 0.63 + H0) * K])
rng = random.Random(3)
X = [max(min(g["x"], 11.6), -0.9) for g in gifts]; Y = [max(min(g["y"], 5.8), -0.9) for g in gifts]
b.axhspan(-1, 1, color="#F2F2F2", zorder=0); b.axhline(1, color=ps.C["ink"], lw=0.7, ls=(0, (3, 2)))
b.plot([0, 5.3], [0, 5.3], color=ps.C["muted"], lw=0.7)
b.scatter(X, Y, s=10, color=ps.C["help"], alpha=0.55, linewidths=0, zorder=3)
mx, my = GA["giver_med"], GA["recv_med"]
b.plot(mx, my, marker="+", ms=11, mew=1.8, color=ps.C["ink"], zorder=4)
b.text(mx - 0.3, -0.75, f"+ 중앙값: 준 쪽 {mx:.1f}, 받은 쪽 {my:.1f}", fontsize=6.8, va="bottom", ha="left", bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.9), zorder=5)
b.text(5.45, 5.25, "두 쪽이 같은 선", fontsize=6.5, color="#808080", rotation=0)
b.text(11.8, 0.62 + 0.05, "안전선", fontsize=6.5, color="#808080", ha="right")
b.set_xlim(-1, 12); b.set_ylim(-1, 6); b.set_xticks([0, 1, 2, 4, 6, 8, 10, 12]); b.set_yticks([0, 1, 2, 4, 6])
b.set_xlabel("준 직후 준 쪽의 여유", labelpad=1); b.set_ylabel("받은 직후 받은 쪽의 여유", labelpad=1)
fig.text(R + 0.07, YY(0.985), "(b) GIVE 직후 두 쪽의 여유: 협력 받기", fontsize=8.3, fontweight="bold", va="top")

for ext in ("pdf", "png"): fig.savefig(os.path.join(HERE, f"fig4_behavior.{ext}"), bbox_inches="tight", pad_inches=0.03)
