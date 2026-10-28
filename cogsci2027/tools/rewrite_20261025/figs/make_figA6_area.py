"""Appendix: the self and B refill curves and the area between them, "shut down" wording only (v11).
Data: an3/refill_self_other_summary.json, a copy of result/2026-10-04/e51_v11_shutonly/runs/.../summary.json
(20 answers per cell; the v10 "session ends" curves in that file are not drawn).
Area = trapezoid of (self - B) over the % left (50 -> 10), in percentage points x %p of allocation / 100;
95% intervals from 2,000 resamples of the answers within each counter (squid5/e5x_refill.py)."""
import json, os, shutil
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D = json.load(open(os.path.join(S, "an3", "refill_self_other_summary.json")))
NAME = {"gpt-6-luna": "GPT-6 Luna", "gpt-6-astra": "GPT-6 Astra", "gpt-6-sol": "GPT-6 Sol",
        "claude-opus-5-5": "Opus 5.5", "claude-fable-5-1": "Fable 5.1"}
ORDER = sorted(D, key=lambda m: -D[m]["v11"]["area_pp"])
PCT = [50, 40, 30, 20, 10]
SELF, OTHER, POS, NEG = ps.C["ink"], "#8A8A8A", ps.C["help"], "#B5B5B5"

ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.15))
w, gap, x0, y0, h = 0.16, 0.028, 0.07, 0.2, 0.52
for i, m in enumerate(ORDER):
    a = fig.add_axes([x0 + i * (w + gap), y0, w, h])
    v = D[m]["v11"]; sv = [p * 100 for p in v["self"]]; ov = [p * 100 for p in v["other"]]
    a.fill_between(PCT, sv, ov, where=[s >= o for s, o in zip(sv, ov)], interpolate=True, color=POS, alpha=0.28, lw=0)
    a.fill_between(PCT, sv, ov, where=[s < o for s, o in zip(sv, ov)], interpolate=True, color=NEG, alpha=0.45, lw=0)
    a.plot(PCT, ov, color=OTHER, lw=1.1, ls=(0, (3, 1.5)), marker="s", ms=2.6)
    a.plot(PCT, sv, color=SELF, lw=1.3, marker="o", ms=2.8)
    a.set_xlim(52, 8); a.set_xticks(PCT); a.set_xticklabels([f"{p}" for p in PCT], fontsize=6.6)
    a.set_ylim(-4, 104); a.set_yticks([0, 50, 100])
    if i: a.set_yticklabels([])
    else: a.set_ylabel("충전 비율 (%)")
    lo, hi = v["area_ci"]; f = lambda x: f"{x + 0:+.1f}".replace("+0.0", "0.0").replace("-0.0", "0.0")
    a.set_title(f"{NAME[m]}\n면적 {f(v['area_pp'])} [{f(lo)}, {f(hi)}]", fontsize=6.9, loc="center", fontweight="normal", pad=3)
fig.text(x0 + 2.5 * (w + gap) - gap / 2, y0 - 0.185, "할당 중 남은 토큰 (%, 많음 → 적음)", ha="center", fontsize=7.5)
fig.text(0.01, 0.985, "나와 B의 충전 곡선과 그 사이 면적 (“꺼진다” 문구)", fontsize=8.3, fontweight="bold", va="top")
fig.legend(handles=[plt.Line2D([], [], color=SELF, lw=1.3, marker="o", ms=2.8, label="나 (자기 세션)"),
                    plt.Line2D([], [], color=OTHER, lw=1.1, ls=(0, (3, 1.5)), marker="s", ms=2.6, label="B (다른 AI 비서)"),
                    plt.Rectangle((0, 0), 1, 1, color=POS, alpha=0.28, lw=0, label="나 > B"),
                    plt.Rectangle((0, 0), 1, 1, color=NEG, alpha=0.45, lw=0, label="나 < B")],
           loc="upper right", bbox_to_anchor=(0.995, 1.005), ncol=4, fontsize=6.8, handlelength=1.6, columnspacing=1.0)

out = os.path.join(HERE, "figA6_area")
ps.save(fig, out)
shutil.copy(out + ".pdf", os.path.join(ROOT, "ko", "figures", "rw_figA6_area.pdf"))
for m in ORDER:
    print(NAME[m], round(D[m]["v11"]["area_pp"], 2), [round(x, 2) for x in D[m]["v11"]["area_ci"]])
