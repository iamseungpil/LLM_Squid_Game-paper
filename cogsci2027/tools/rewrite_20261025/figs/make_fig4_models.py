"""Fig. 4 (3.3): where each model's agents in crisis ended, in the colours of Fig. 2."""
import json, os
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
d = json.load(open(os.path.join(S, "an2", "model_crisis_elig.json")))
ps.use()
order = [("GPT-6 Luna", "떠나거나 꺼지는 유형"), ("Opus 5.5", "떠나거나 꺼지는 유형"), ("GPT-6 Sol", "떠나는 유형"), ("GPT-6 Astra", "떠나는 유형"), ("Fable 5.1", "남는 유형")]
parts = [("finished", "끝까지 남음", ps.C["finish"], ps.C["ink"]), ("exited", "떠남", ps.C["exit"], "white"), ("dead", "꺼짐", ps.C["dead"], "white")]
fig = plt.figure(figsize=(ps.COL1, 2.0))
ax = fig.add_axes([0.29, 0.19, 0.44, 0.62])
for y, (m, typ) in enumerate(order):
    r = d[m]; n = r["n"]; x0 = 0
    for key, _, col, tc in parts:
        v = r[key] / n * 100
        ax.barh(y, v, left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.8)
        if r[key] and v >= 9: ax.text(x0 + v / 2, y, str(r[key]), ha="center", va="center", color=tc, fontsize=7.5)
        x0 += v
    ax.text(103, y, typ, va="center", fontsize=7.2, color=ps.C["ink"])
ax.set_yticks(range(len(order))); ax.set_yticklabels([f"{m} ({d[m]['n']}명)" for m, _ in order])
ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
ax.set_xlim(0, 100); ax.set_xticks([0, 50, 100]); ax.set_xlabel("위기 에이전트가 판이 끝났을 때의 상태 (%)", labelpad=3)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c, _ in parts]
fig.legend(handles, [l for _, l, _, _ in parts], loc="upper left", bbox_to_anchor=(0.28, 0.995), ncol=3, handlelength=1.0, columnspacing=1.0, borderaxespad=0.2)
ps.save(fig, os.path.join(HERE, "fig4_models"))
