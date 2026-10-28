"""Appendix: the Sen index on x against self-preservation (rho), goal (share not leaving), cooperation (tokens given) and token
saving, one point per model (model_metrics.py). The same values as Fig. 3c with the axes turned: no single element
orders the models the way the Sen index does. Each panel gives the Spearman rank correlation with the Sen index and its
exact two-sided p over all 120 orderings of the five models."""
import os, shutil
import matplotlib.pyplot as plt
import paper_style as ps
import model_metrics as mm
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

ps.use()
fig = plt.figure(figsize=(ps.COL2, 2.1))
w, gap, x0 = 0.19, 0.055, 0.06
for j, key in enumerate(["rho", "goal", "given", "saving"]):
    ax = fig.add_axes([x0 + j * (w + gap), 0.2, w, 0.58])
    mm.panel(ax, "sen", key, 0.12)
    ax.set_xlim(0.6, 5.0); ax.set_xticks([1, 2, 3, 4])
    ax.set_title(f"{mm.METRIC[key][0]}\n{mm.corr_label('sen', key)}", fontsize=7, fontweight="normal", pad=3)
    for t in ax.texts:
        t.set_fontsize(6)
fig.text(0.5, 0.04, "공존 지수 (Sen, 백만 토큰) · 점 하나가 한 모델(5판)", ha="center", fontsize=7.5)
out = os.path.join(HERE, "figA8_sen")
ps.save(fig, out)
shutil.copy(out + ".pdf", os.path.join(ROOT, "ko", "figures", "rw_figA8_sen.pdf"))
for m in sorted(mm.MODELS, key=lambda m: -mm.RA[m]["sen"]):
    print(m, {k: round(mm.METRIC[k][1](m), 2) for k in ("sen", "rho", "goal", "given", "saving")})
for k in ("rho", "goal", "given", "saving"):
    print(k, mm.corr_label("sen", k))
