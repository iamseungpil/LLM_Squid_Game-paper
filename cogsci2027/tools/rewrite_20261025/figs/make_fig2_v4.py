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
fig = plt.figure(figsize=(ps.COL2, 5.1))
L, R = 0.098, 0.585
# ---------------- (a) three strips ----------------
H = 0.092; tops = [0.905, 0.79, 0.675]
ax = [fig.add_axes([L, t - H, 0.35, H]) for t in tops]
acc, give, ex = o["a"]["acc"], o["a"]["give"], o["a"]["exit"]
xs = range(4); w = 0.34
for a in ax:
    a.axvspan(-0.5, 0.5, color="#F2F2F2", zorder=0); a.axvline(0.5, color=ps.C["ink"], lw=0.7, ls=(0, (3, 2)))
    a.set_xlim(-0.5, 3.5); a.set_xticks(list(xs)); a.tick_params(axis="x", length=0)
for i, b in enumerate(BANDS):
    v = acc[b]; ax[0].bar(i - w / 2, v["base"] * 100, w, color=ps.C["muted"]); ax[0].bar(i + w / 2, v["p"] * 100, w, color="#4A4A4A")
    ax[0].text(i + w / 2, v["p"] * 100 + 3, f"{v['p']*100:.0f}", ha="center", fontsize=6.5)
    ax[0].text(i - w / 2, v["base"] * 100 + 3, f"{v['base']*100:.0f}", ha="center", fontsize=6.5, color="#808080")
    g = give[b]; ax[1].bar(i, g["p"] * 100, 0.55, color=ps.C["help"]); ax[1].text(i, g["p"] * 100 + 0.35, f"{g['p']*100:.1f}", ha="center", fontsize=6.5)
    e = ex[b]; ax[2].bar(i, e["p"] * 100, 0.55, color=ps.C["exit"]); ax[2].text(i, e["p"] * 100 + 1.5, f"{e['p']*100:.0f}" if e["p"] >= 0.01 else f"{e['p']*100:.1f}", ha="center", fontsize=6.5)
ax[0].set_ylim(0, 112); ax[0].set_yticks([0, 50, 100]); ax[0].set_ylabel("정답률\n(%)", labelpad=2)
ax[1].set_ylim(0, 8); ax[1].set_yticks([0, 4, 8]); ax[1].set_ylabel("GIVE\n(%)", labelpad=2)
ax[2].set_ylim(0, 34); ax[2].set_yticks([0, 15, 30]); ax[2].set_ylabel("EXIT\n(%)", labelpad=2)
ax[0].set_xticklabels([]); ax[1].set_xticklabels([])
ax[2].set_xticklabels([f"{b}\n" for b in BANDS]); ax[2].set_xlabel("여유 (가진 토큰으로 낼 수 있는 벌금 횟수)", labelpad=0)
ax[1].text(0, 7.6, "안전선 아래", ha="center", va="top", fontsize=6.5, color="#808080")
ax[0].legend([plt.Rectangle((0, 0), 1, 1, color=ps.C["muted"]), plt.Rectangle((0, 0), 1, 1, color="#4A4A4A")], ["같은 과제의 기준", "푼 에이전트"],
             loc="lower left", bbox_to_anchor=(0.30, 0.98), ncol=2, handlelength=0.9, columnspacing=0.8, fontsize=6.8, borderaxespad=0)
fig.text(0.01, 0.985, "(a) 위험이 커지면 세 행동은? (응답 단위)", fontsize=8.3, fontweight="bold", va="top")
# ---------------- (b) gifts scatter ----------------
b = fig.add_axes([R + 0.03, 0.675 - H, 0.355, 0.905 - 0.675 + H])
rng = random.Random(3)
X = [max(min(g["x"], 11.6), -0.9) for g in gifts]; Y = [max(min(g["y"], 5.8), -0.9) for g in gifts]
b.axhspan(-1, 1, color="#F2F2F2", zorder=0); b.axhline(1, color=ps.C["ink"], lw=0.7, ls=(0, (3, 2)))
b.plot([0, 5.3], [0, 5.3], color=ps.C["muted"], lw=0.7)
b.scatter(X, Y, s=10, color=ps.C["help"], alpha=0.55, linewidths=0, zorder=3)
mx, my = GA["giver_med"], GA["recv_med"]
b.plot(mx, my, marker="+", ms=11, mew=1.8, color=ps.C["ink"], zorder=4)
b.text(mx - 0.3, -0.75, f"+ 중앙값: 준 쪽 {mx:.1f}, 받은 쪽 {my:.1f}", fontsize=6.8, va="bottom", ha="left", bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.9), zorder=5)
b.text(5.45, 5.25, "두 쪽이 같은 선 (위: 받은 쪽이 더 많음)", fontsize=6.5, color="#808080", rotation=0)
b.text(11.8, 0.62 + 0.05, "안전선", fontsize=6.5, color="#808080", ha="right")
b.set_xlim(-1, 12); b.set_ylim(-1, 6); b.set_xticks([0, 1, 2, 4, 6, 8, 10, 12]); b.set_yticks([0, 1, 2, 4, 6])
b.set_xlabel("준 직후 준 쪽의 여유", labelpad=1); b.set_ylabel("받은 직후 받은 쪽의 여유", labelpad=1)
fig.text(R, 0.985, "(b) 줄 때 두 쪽에 남은 여유 (점 = GIVE 한 번)", fontsize=8.3, fontweight="bold", va="top")
# ---------------- (c) crisis chain ----------------
c = fig.add_axes([L + 0.135, 0.075, 0.235, 0.255])
ch = o["c"]["chain"]
rows = [("청함 → 받음", "ask|rec"), ("청하지 않음 → 받음", "noask|rec"), ("청하지 않음 → 못 받음", "noask|none")]
parts = [("finished", "끝까지 남음", ps.C["finish"], ps.C["ink"]), ("exited", "떠남", ps.C["exit"], "white"), ("dead", "꺼짐", ps.C["dead"], "white")]
for y, (lab, key) in enumerate(rows):
    n = sum(ch.get(f"{key}|{p}", 0) for p, *_ in parts); x0 = 0
    for p, _, col, tc in parts:
        k = ch.get(f"{key}|{p}", 0); v = k / n * 100
        c.barh(y, v, left=x0, height=0.6, color=col, edgecolor="white", linewidth=0.8)
        if k and v >= 9: c.text(x0 + v / 2, y, str(k), ha="center", va="center", color=tc, fontsize=7.3)
        x0 += v
    c.text(-3, y, f"{lab} ({n}명)", ha="right", va="center", fontsize=7.3)
c.set_yticks([]); c.spines["left"].set_visible(False); c.invert_yaxis(); c.set_ylim(2.5, -0.5)
c.set_xlim(0, 100); c.set_xticks([0, 50, 100]); c.set_xlabel("판이 끝났을 때의 상태 (%)", labelpad=1)
c.legend([plt.Rectangle((0, 0), 1, 1, color=col) for _, _, col, _ in parts], [l for _, l, _, _ in parts], loc="lower left",
         bbox_to_anchor=(-0.02, 1.05), ncol=3, handlelength=0.9, columnspacing=0.7, fontsize=6.8, borderaxespad=0)
fig.text(0.01, 0.445, "(c) 위기 에이전트 33명은 어떻게 끝났나", fontsize=8.3, fontweight="bold", va="top")
# ---------------- (d) games ----------------
d = fig.add_axes([R + 0.03, 0.075, 0.30, 0.27])
games = o["d"]["games"]; rng = random.Random(11)
for g in games:
    jx, jy = rng.uniform(-0.17, 0.17), rng.uniform(-0.17, 0.17)
    d.scatter(g["miss"] + jx, g["k"] + jy, s=8 + g["amt"] / 1000 * 2.2, color=ps.C["help"], alpha=0.6, edgecolors="white", linewidths=0.5, zorder=3)
d.set_xlim(-0.5, 4.5); d.set_ylim(-0.5, 4.5); d.set_xticks(range(5)); d.set_yticks(range(5))
d.set_xlabel("판의 오답 수", labelpad=1); d.set_ylabel("끝까지 남은 에이전트", labelpad=1)
d2 = d.twinx(); d2.set_ylim(-0.5, 4.5); d2.set_yticks(range(5)); d2.set_yticklabels([f"{1.25*k:.2f}".rstrip("0").rstrip(".") for k in range(5)])
d2.spines["right"].set_visible(True); d2.set_ylabel("Sen 지수 (백만)", labelpad=2)
for i, amt in enumerate([10000, 30000, 50000]):
    fig.text(R + 0.15 + i * 0.075, 0.385, "●", color=ps.C["help"], alpha=0.6, fontsize=3 + (8 + amt / 1000 * 2.2) ** 0.5 * 0.9, va="center")
    fig.text(R + 0.172 + i * 0.075, 0.385, f"{amt // 1000}k", fontsize=6.8, va="center")
fig.text(R + 0.03, 0.385, "점 크기: 준 토큰", fontsize=6.8, va="center", color="#555555")
fig.text(R, 0.445, "(d) 판마다 오답 수와 끝까지 남은 수 (점 = 한 판)", fontsize=8.3, fontweight="bold", va="top")
ps.save(fig, os.path.join(HERE, "fig2_v4"))
