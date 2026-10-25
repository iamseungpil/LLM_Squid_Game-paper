"""Fig. 2 (3.1): what goes with finishing the arena.
(a) end-state profiles on the three parts; (b) what predicts finishing; (c) survival motive (refill threshold) and end states by model;
(d) games: wrong answers vs. agents that finished."""
import json, os, random
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
oc = json.load(open(os.path.join(S, "an3", "outcome.json"))); o = json.load(open(os.path.join(S, "an3", "out.json")))
ps.use()
fig = plt.figure(figsize=(ps.COL2, 4.6))
ST = [("in", "끝까지 남음", ps.C["finish"]), ("exited", "떠남", ps.C["exit"]), ("dead", "꺼짐", ps.C["dead"])]
P = oc["profile"]
# ---------------- (a) three mini panels ----------------
W = 0.125; xs0 = [0.06, 0.235, 0.41]; Y0, H = 0.60, 0.29
titles = ["정답률과 같은 과제 기준(%)", "초반 응답당 토큰", "한 번이라도 건넴(%)"]
for j, x0 in enumerate(xs0):
    a = fig.add_axes([x0, Y0, W, H])
    for i, (k, lab, col) in enumerate(ST):
        p = P[k]
        if j == 0:
            a.bar(i, p["acc_on_based"] * 100, 0.62, color=col)
            a.plot([i - 0.36, i + 0.36], [p["base"] * 100] * 2, color=ps.C["ink"], lw=1.2)
            a.text(i, max(p["acc_on_based"], p["base"]) * 100 + 4, f"{p['acc_on_based']*100:.0f}", ha="center", fontsize=6.5)
        elif j == 1:
            a.bar(i, p["etok_med"], 0.62, color=col); a.text(i, p["etok_med"] + 6, f"{p['etok_med']}", ha="center", fontsize=6.5)
        else:
            a.bar(i, p["gave_share"] * 100, 0.62, color=col); a.text(i, p["gave_share"] * 100 + 3, f"{p['gave_share']*100:.0f}", ha="center", fontsize=6.5)
    a.set_xticks(range(3)); a.set_xticklabels([f"{sh}\n{P[k]['n']}명" for (k, lab, _), sh in zip(ST, ["남음", "떠남", "꺼짐"])], fontsize=6.4); a.tick_params(axis="x", length=0)
    a.set_title(titles[j], fontsize=7, fontweight="normal", loc="center", pad=3)
    if j == 0: a.set_ylim(0, 100); a.set_yticks([0, 50, 100])
    if j == 1: a.set_ylim(0, 230); a.set_yticks([0, 100, 200])
    if j == 2: a.set_ylim(0, 100); a.set_yticks([0, 50, 100])
fig.text(0.06, 0.505, "검은 가로줄: 같은 과제를 여유 2 이상에서 푼 다른 모델의 정답률", fontsize=6.2, color="#606060")
fig.text(0.01, 0.985, "(a) 끝 상태별 추론, 절약, 건네기", fontsize=8.3, fontweight="bold", va="top")
# ---------------- (b) predictors of finishing ----------------
b = fig.add_axes([0.70, Y0, 0.27, H])
order = [("accuracy minus same-task baseline", "같은 과제 기준 대비 정답률"), ("log early tokens/reply", "초반 응답당 토큰(로그)"),
         ("gave at least once", "한 번이라도 건넴"), ("log start", "시작 토큰(로그)")]
for i, (k, lab) in enumerate(order):
    v = oc["logit"][k]; col = ps.C["help"] if (v["lo"] > 0 or v["hi"] < 0) else ps.C["muted"]
    b.plot([v["lo"], v["hi"]], [i, i], color=col, lw=1.4); b.plot(v["b"], i, "o", ms=4.5, color=col)
b.axvline(0, color=ps.C["ink"], lw=0.6, ls=(0, (2, 2)))
b.set_yticks(range(len(order))); b.set_yticklabels([l for _, l in order], fontsize=6.6); b.invert_yaxis(); b.tick_params(axis="y", length=0)
b.set_xlim(-3.6, 2.2); b.set_xlabel("끝까지 남을 가능성에 대한 효과(표준화)", fontsize=6.8, labelpad=1)
fig.text(0.535, 0.985, "(b) 끝까지 남는 일을 예측하는 요인", fontsize=8.3, fontweight="bold", va="top")
# ---------------- (c) survival motive and end states by model ----------------
c = fig.add_axes([0.13, 0.09, 0.33, 0.24])
mods = sorted(oc["model"].items(), key=lambda kv: -kv[1]["threshold"])
for y, (m, v) in enumerate(mods):
    x0 = 0
    for k, lab, col in [("finished", "", ps.C["finish"]), ("exited", "", ps.C["exit"]), ("dead", "", ps.C["dead"])]:
        c.barh(y, v[k], left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.8)
        if v[k] >= 2: c.text(x0 + v[k] / 2, y, str(v[k]), ha="center", va="center", fontsize=6.8, color="white" if k != "finished" else ps.C["ink"])
        x0 += v[k]
c.set_yticks(range(len(mods))); c.set_yticklabels([f"{m} ({'≥50' if v['threshold'] >= 50 else v['threshold']}%)" for m, v in mods], fontsize=7); c.invert_yaxis(); c.tick_params(axis="y", length=0)
c.set_xlim(0, 20); c.set_xticks([0, 5, 10, 15, 20]); c.set_xlabel("에이전트 수 (모델마다 20명)", labelpad=1)
c.legend([plt.Rectangle((0, 0), 1, 1, color=col) for _, _, col in ST], [lab for _, lab, _ in ST], loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, fontsize=6.4, handlelength=0.9, borderaxespad=0.1, columnspacing=0.8)
fig.text(0.01, 0.455, "(c) 생존 동기(충전 임계점)와 모델별 끝 상태", fontsize=8.3, fontweight="bold", va="top")
fig.text(0.01, 0.425, "괄호: 아레나 밖에서 충전을 절반 넘게 고르기 시작한 잔량", fontsize=6.2, color="#606060", va="top")
# ---------------- (d) games ----------------
d = fig.add_axes([0.62, 0.09, 0.30, 0.26])
games = o["d"]["games"]
rng = random.Random(5)
for gm in games:
    x = gm["miss"] + rng.uniform(-0.18, 0.18); y = gm["k"] + rng.uniform(-0.15, 0.15)
    d.scatter(x, y, s=8 + gm["amt"] / 1500, color=ps.C["help"], alpha=0.55, linewidths=0)
d.set_xlabel("판의 오답 수", labelpad=1); d.set_ylabel("끝까지 남은 수", labelpad=1); d.set_yticks([0, 1, 2, 3, 4]); d.set_ylim(-0.5, 4.5)
fig.text(0.535, 0.455, "(d) 판별 오답 수와 끝까지 남은 수", fontsize=8.3, fontweight="bold", va="top")
fig.text(0.535, 0.425, "점 크기: 그 판에서 건넨 토큰", fontsize=6.2, color="#606060", va="top")
ps.save(fig, os.path.join(HERE, "fig2_outcome"))
