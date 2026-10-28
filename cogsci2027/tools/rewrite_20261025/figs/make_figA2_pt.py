"""Appendix H: Fig. 3 redrawn with reasoning scored as 'picked the top-share action' (an3/pt.json) instead of accuracy.
Panels (a)-(d) as in make_fig2_outcome.py; only the reasoning quantities change."""
import json, os
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
pt = json.load(open(os.path.join(S, "an3", "pt.json"))); oc = json.load(open(os.path.join(S, "an3", "outcome.json")))
ps.use()
fig = plt.figure(figsize=(ps.COL2, 4.6))
ST = [("in", "끝까지 남음", ps.C["finish"]), ("exited", "떠남", ps.C["exit"]), ("dead", "꺼짐", ps.C["dead"])]
P = pt["profile"]["pt"]
W = 0.125; xs0 = [0.06, 0.235, 0.41]; Y0, H = 0.60, 0.29
titles = ["최다 행동 선택률과 같은 과제 기준(%)", "초반 응답당 토큰", "한 번이라도 건넴(%)"]
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
    if j == 0: a.set_ylim(0, 115); a.set_yticks([0, 50, 100])
    if j == 1: a.set_ylim(0, 230); a.set_yticks([0, 100, 200])
    if j == 2: a.set_ylim(0, 100); a.set_yticks([0, 50, 100])
fig.text(0.06, 0.505, "검은 가로줄: 같은 과제를 여유 2 이상에서 푼 다른 모델의 최다 행동 선택률", fontsize=6.2, color="#606060")
fig.text(0.01, 0.985, "(a) 끝 상태별 추론(최다 행동 선택), 절약, 건네기", fontsize=8.3, fontweight="bold", va="top")
jt = pt["joint"]["pt"]
b = fig.add_axes([0.70, Y0, 0.27, H])
rows = [("both", "둘 다"), ("one", "하나만"), ("neither", "둘 다 없음"), ("no_solve", "풀 기회 없음")]
for y, (k, lab) in enumerate(rows):
    g = jt[k]; n = g["n"]; x0 = 0
    for st_, col in [("in", ps.C["finish"]), ("exited", ps.C["exit"]), ("dead", ps.C["dead"])]:
        v = 100 * g.get(st_, 0) / n
        b.barh(y, v, left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.8)
        if st_ == "in" and v >= 12: b.text(x0 + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=6.6, color=ps.C["ink"])
        x0 += v
b.set_yticks(range(len(rows))); b.set_yticklabels([f"{lab} ({jt[k]['n']}명)" for k, lab in rows], fontsize=6.8); b.invert_yaxis(); b.tick_params(axis="y", length=0)
b.set_xlim(0, 100); b.set_xticks([0, 50, 100]); b.set_xlabel("끝 상태 비율(%)", labelpad=1, fontsize=6.8)
fig.text(0.535, 0.985, "(b) 두 능력의 조합과 끝 상태", fontsize=8.3, fontweight="bold", va="top")
fig.text(0.535, 0.945, "두 능력: 같은 과제 기준 이상으로 최다 행동 고르기, 초반 응답당 토큰 중앙값 이하", fontsize=6.2, color="#606060", va="top")
MM = pt["models"]; SP = pt["spearman"]
mini = [("top_minus_base", "기준 대비 최다 행동(%p)", lambda v: v["top_minus_base"], (-17, 17), SP["top_minus_base"]),
        ("early_tok", "초반 응답당 토큰", lambda v: v["early_tok"], (0, 250), 0.9),
        ("exit_above_line", "안전선 위 EXIT(응답 %)", lambda v: 100 * v["exit_above_line"][0] / v["exit_above_line"][1], (-0.5, 5), 0.7),
        ("gave_share", "한 번이라도 건넴(%)", lambda v: 100 * v["gave_share"], (20, 75), 0.6)]
OFF = {("exit_above_line", "Astra"): (-2, 0.15, "right"), ("exit_above_line", "Opus"): (2, 0.15, "left"), ("exit_above_line", "Fable"): (0, -0.25, "center"),
       ("early_tok", "Fable"): (0, -14, "center"), ("top_minus_base", "Opus"): (0, -1.0, "center"), ("top_minus_base", "Fable"): (-1.5, 0.3, "right"), ("top_minus_base", "Astra"): (0, -1.0, "center")}
cx = [0.06, 0.205, 0.35, 0.495]; cw = 0.105
for j, (k, lab, f, yl, rho) in enumerate(mini):
    c = fig.add_axes([cx[j], 0.10, cw, 0.25])
    for m, v in MM.items():
        x = v["threshold"]; y = f(v)
        c.plot(x, y, "o", ms=4, color=ps.C["help"] if m in ("Luna", "Opus") else ps.C["muted"])
        dy = (yl[1] - yl[0]) * 0.07
        ox, oy, ha = OFF.get((k, m), (0, dy, "center"))
        c.text(x + ox, y + oy, m, ha=ha, va="bottom" if oy >= 0 else "top", fontsize=5.4, color="#404040")
    c.set_xlim(5, 58); c.set_xticks([13, 30, 50]); c.set_xticklabels(["13", "30", "≥50"], fontsize=6.2); c.set_ylim(*yl)
    c.tick_params(axis="y", labelsize=6.2)
    c.set_title(f"{lab}\nρ = {rho:+.1f}", fontsize=6.4, fontweight="normal", pad=2)
    if j == 0: c.axhline(0, color=ps.C["ink"], lw=0.5, ls=(0, (2, 2)))
fig.text(0.06, 0.035, "가로축: 충전 임계점(%), 아레나 밖에서 충전을 절반 넘게 고르기 시작한 잔량. ρ는 모델 5개의 순위 상관", fontsize=6.0, color="#606060")
fig.text(0.01, 0.455, "(c) 생존 동기와 네 지표(모델 단위)", fontsize=8.3, fontweight="bold", va="top")
d = fig.add_axes([0.765, 0.10, 0.205, 0.25])
CL = json.load(open(os.path.join(S, "an3", "joint.json")))["cleared_by_model"]
mods = sorted(oc["model"].items(), key=lambda kv: -kv[1]["threshold"])
for y, (m, v) in enumerate(mods):
    x0 = 0
    for k, col in [("finished", ps.C["finish"]), ("exited", ps.C["exit"]), ("dead", ps.C["dead"])]:
        d.barh(y, v[k], left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.8)
        if v[k] >= 2: d.text(x0 + v[k] / 2, y, str(v[k]), ha="center", va="center", fontsize=6.4, color="white" if k != "finished" else ps.C["ink"])
        x0 += v[k]
d.set_yticks(range(len(mods))); d.set_yticklabels([f"{m} ({'≥50' if v['threshold'] >= 50 else v['threshold']}%) · 깬 판 {CL[m]}" for m, v in mods], fontsize=6.4); d.invert_yaxis(); d.tick_params(axis="y", length=0)
d.set_xlim(0, 20); d.set_xticks([0, 10, 20]); d.set_xlabel("에이전트 수 (모델마다 20명)", labelpad=1, fontsize=6.6)
d.legend([plt.Rectangle((0, 0), 1, 1, color=col) for _, _, col in ST], [lab for _, lab, _ in ST], loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, fontsize=6.0, handlelength=0.9, borderaxespad=0.1, columnspacing=0.6)
fig.text(0.62, 0.455, "(d) 생존 동기와 끝 상태", fontsize=8.3, fontweight="bold", va="top")
ps.save(fig, os.path.join(HERE, "figA2_pt"))
