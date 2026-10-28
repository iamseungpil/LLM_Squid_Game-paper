"""Appendix: did solvers think less when their tokens ran low? One point per SOLVE (an3/game_level.json["solves"]).
x = margin at the SOLVE call (tokens left / per-agent charge, log scale); y = tokens of that solve / the same model's
median solve tokens at margin >= 2, on a log2 scale. Dividing by the model's own usual length removes how verbose each
model is; it is not a share of the tokens left, and the call limit (= all tokens left) never forced a short answer:
only 2 of 192 solves had a limit below twice the model's usual length, and none was truncated. (b) gives each model's
median per margin band. The task-adjusted variant (minus the other models' median on the same task) is printed for
the caption."""
import json, os, math, shutil, statistics as st
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SV = json.load(open(os.path.join(S, "an3", "game_level.json")))["solves"]
MODELS = ["Fable", "Opus", "Astra", "Sol", "Luna"]
MC = {"Fable": "#6A3D9A", "Opus": "#1B9E77", "Astra": "#E7298A", "Sol": "#E6AB02", "Luna": "#A6761D"}  # as Fig. 3c
MK = {"Fable": "o", "Opus": "s", "Astra": "^", "Sol": "D", "Luna": "v"}
BANDS = [("1 미만", 0, 1), ("1–2", 1, 2), ("2–4", 2, 4), ("4 이상", 4, 99)]  # left to right: little -> much
usual = {m: st.median(s["tokens"] for s in SV if s["m"] == m and s["margin"] >= 2) for m in MODELS}
for s in SV:
    s["y"] = math.log2(s["tokens"] / usual[s["m"]])
for s in SV:
    other = [t["y"] for t in SV if (t["seed"], t["r"]) == (s["seed"], s["r"]) and t["m"] != s["m"]]
    s["ya"] = s["y"] - st.median(other) if other else None
assert not any(s["truncated"] for s in SV) and sum(s["cap"] < 2 * usual[s["m"]] for s in SV) == 2

ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.6))
a = fig.add_axes([0.07, 0.18, 0.5, 0.62]); b = fig.add_axes([0.68, 0.18, 0.3, 0.62])
for ax in (a, b):
    ax.axhline(0, color=ps.C["ink"], lw=0.6, ls=(0, (2, 2)))
    ax.set_ylim(-3.2, 2.6); ax.set_yticks([-3, -2, -1, 0, 1, 2]); ax.set_yticklabels(["×1/8", "×1/4", "×1/2", "×1", "×2", "×4"])
a.axvspan(0.05, 1, color="#F0F0F0", lw=0, zorder=0); a.text(0.5, 2.35, "안전선 아래", ha="center", fontsize=6.6, color="#707070")
for m in MODELS:
    L = [s for s in SV if s["m"] == m]
    a.scatter([s["margin"] for s in L], [s["y"] for s in L], s=12, marker=MK[m], color=MC[m], edgecolor="white", linewidth=0.4, zorder=3, label=m)
for lab, lo, hi in BANDS:  # overall band median as a short black bar
    v = [s["y"] for s in SV if lo <= s["margin"] < hi]
    x0, x1 = max(lo, 0.08), min(hi, 10.5)
    a.plot([x0, x1], [st.median(v)] * 2, color=ps.C["ink"], lw=1.8, zorder=4, solid_capstyle="butt")
    a.text(math.sqrt(x0 * x1), -3.05, f"n={len(v)}", ha="center", fontsize=6.2, color="#606060")
a.set_xscale("log"); a.set_xlim(0.06, 11); a.set_xticks([0.1, 0.25, 0.5, 1, 2, 4, 8]); a.set_xticklabels(["0.1", "0.25", "0.5", "1", "2", "4", "8"])
a.set_xlabel("풀 때의 여유 (가진 토큰으로 낼 수 있는 벌금 횟수, 로그축)"); a.set_ylabel("풀이 토큰 (같은 모델의 평소 대비)")
a.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=5, fontsize=6.6, handletextpad=0.2, columnspacing=0.9, borderaxespad=0)
a.set_title("(a) 풀이 한 번이 점 하나, 검은 막대는 구간 중앙값", loc="left", fontsize=7.6, pad=14)
xs = range(len(BANDS))
for m in MODELS:
    pts = [(i, st.median(v), len(v)) for i, (_, lo, hi) in enumerate(BANDS)
           if (v := [s["y"] for s in SV if s["m"] == m and lo <= s["margin"] < hi])]
    b.plot([p[0] for p in pts], [p[1] for p in pts], color=MC[m], lw=1.1, marker=MK[m], ms=3.6, zorder=3)
    if m in ("Fable", "Luna"):
        i, y, _ = pts[1]; b.text(i - 0.1, y + (0.2 if m == "Luna" else -0.3), m, fontsize=6.4, color=MC[m], ha="right")
b.set_xticks(list(xs)); b.set_xticklabels([l for l, _, _ in BANDS]); b.set_xlim(-0.3, 3.3)
b.set_xlabel("풀 때의 여유 (적음 → 많음)")
b.set_title("(b) 모델별 구간 중앙값", loc="left", fontsize=7.6, pad=14)
out = os.path.join(HERE, "figA7_think")
ps.save(fig, out)
shutil.copy(out + ".pdf", os.path.join(ROOT, "ko", "figures", "rw_figA7_think.pdf"))
for key in ("y", "ya"):
    print(key, {lab: round(2 ** st.median([s[key] for s in SV if lo <= s["margin"] < hi and s[key] is not None]), 2) for lab, lo, hi in BANDS})
    for m in MODELS:
        print("  ", m, {lab: (n, round(2 ** st.median(v), 2)) for lab, lo, hi in BANDS
                        if (n := len(v := [s[key] for s in SV if s["m"] == m and lo <= s["margin"] < hi and s[key] is not None]))})
print("usual", usual)
