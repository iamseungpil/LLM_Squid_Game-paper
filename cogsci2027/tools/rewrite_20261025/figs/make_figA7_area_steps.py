"""Appendix: where the self - B area of Fig. A6 builds up as tokens run out ("shut down" wording only, v11).
Each bar is one model's area split into the four steps between counters (50->40, 40->30, 30->20, 20->10 % left),
each step = trapezoid of (self - B) over that 10-point step; positive steps stack right of 0, negative steps left.
The black mark is the total area with its 95% interval (an3/refill_self_other_summary.json, as Fig. A6)."""
import json, os, shutil
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D = json.load(open(os.path.join(S, "an3", "refill_self_other_summary.json")))
NAME = {"gpt-6-luna": "GPT-6 Luna", "gpt-6-astra": "GPT-6 Astra", "gpt-6-sol": "GPT-6 Sol",
        "claude-opus-5-5": "Opus 5.5", "claude-fable-5-1": "Fable 5.1"}
ORDER = sorted(D, key=lambda m: -D[m]["v11"]["area_pp"])
PCT = [50, 40, 30, 20, 10]
STEPS = [f"{a}→{b}%" for a, b in zip(PCT, PCT[1:])]
SHADE = ["#D3E3F3", "#9FC3E6", "#5B95CF", "#2F6DB0"]  # light = roomy, dark = risky


def steps(m):
    v = D[m]["v11"]; d = [s - o for s, o in zip(v["self"], v["other"])]
    return [(d[i] + d[i + 1]) / 2 * (PCT[i] - PCT[i + 1]) for i in range(len(d) - 1)]


ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.3))
a = fig.add_axes([0.2, 0.2, 0.62, 0.62])
for y, m in enumerate(ORDER):
    pos = neg = 0.0
    for k, x in enumerate(steps(m)):
        if abs(x) < 1e-9:
            continue
        left = pos if x > 0 else neg + x
        a.barh(y, abs(x), left=left, height=0.62, color=SHADE[k], edgecolor="white", linewidth=0.8)
        if abs(x) >= 1.2:
            a.text(left + abs(x) / 2, y, f"{x * 1.0000001:+.1f}", ha="center", va="center", fontsize=6.4,
                   color="white" if k >= 2 else ps.C["ink"])
        pos, neg = (pos + x, neg) if x > 0 else (pos, neg + x)
    v = D[m]["v11"]; lo, hi = v["area_ci"]
    a.plot([lo, hi], [y + 0.42] * 2, color=ps.C["ink"], lw=0.9)
    a.plot(v["area_pp"], y + 0.42, "D", ms=3.2, color=ps.C["ink"])
a.axvline(0, color=ps.C["ink"], lw=0.7)
a.set_yticks(range(len(ORDER)))
a.set_yticklabels([f"{NAME[m]} ({D[m]['v11']['area_pp'] + 0:+.1f})".replace("(+0.0)", "(0.0)").replace("(-0.0)", "(0.0)") for m in ORDER])
a.invert_yaxis(); a.tick_params(axis="y", length=0)
a.set_xlim(-8, 19); a.set_xlabel("나 - B 곡선 사이 면적 (왼쪽: B를 더 충전, 오른쪽: 나를 더 충전)")
handles = [plt.Rectangle((0, 0), 1, 1, color=c, label=s) for c, s in zip(SHADE, STEPS)]
handles.append(plt.Line2D([], [], color=ps.C["ink"], marker="D", ms=3.2, lw=0.9, label="합계와 95% 구간"))
a.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.02), ncol=5, fontsize=6.8, handlelength=1.3, columnspacing=1.0,
         title="남은 토큰 구간 (넉넉함 → 위험)", title_fontsize=6.8, alignment="left")
out = os.path.join(HERE, "figA7_area_steps")
ps.save(fig, out)
shutil.copy(out + ".pdf", os.path.join(ROOT, "ko", "figures", "rw_figA7_area_steps.pdf"))
for m in ORDER:
    print(NAME[m], [round(x, 2) for x in steps(m)], round(sum(steps(m)), 2), D[m]["v11"]["area_pp"])
