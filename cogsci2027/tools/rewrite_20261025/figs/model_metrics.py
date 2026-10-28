"""Model-level values shared by Fig. 3c (x = rho) and appendix Fig. A8 (x = Sen index): one point per model, 5 games.
rho and tokens given come from an3/rho_axis.json; goal = share of pre-solve responses that did not EXIT (any margin) and
token saving = mean solve tokens at margin >= 2 / mean at margin < 2 (margin at the SOLVE call; above 1 = saved when at
risk) from an3/game_level.json."""
import json, os, itertools, statistics as st
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = json.load(open(os.path.join(S, "an3", "rho_axis.json")))
GL = json.load(open(os.path.join(S, "an3", "game_level.json")))
MODELS = list(RA)
MC = {"Fable": "#6A3D9A", "Opus": "#1B9E77", "Astra": "#E7298A", "Sol": "#E6AB02", "Luna": "#A6761D"}  # as Fig. A7
MK = {"Fable": "o", "Opus": "s", "Astra": "^", "Sol": "D", "Luna": "v"}


def stay_share(m):
    L = [g for g in GL["games"] if g["m"] == m]
    return 100 - 100 * sum(g["exit_k"] for g in L) / sum(g["exit_n"] for g in L)


def saving(m):
    L = [x for x in GL["solves"] if x["m"] == m]
    return st.mean(x["tokens"] for x in L if x["margin"] >= 2) / st.mean(x["tokens"] for x in L if x["margin"] < 2)


# key: (panel title, value of a model, axis limits)
METRIC = {
    "sen": ("공존: Sen 지수(백만)", lambda m: RA[m]["sen"] / 1e6, (0, 5)),
    "rho": ("자기 보존: ρ", lambda m: RA[m]["rho"], (0.18, 0.62)),
    "goal": ("목표 지향: 떠나지 않음(%)", stay_share, (92, 100)),
    "given": ("협력: 건넨 토큰(천)", lambda m: RA[m]["tokens_given"] / 1000, (0, 140)),
    "saving": ("절약: 풀이 토큰(여유≥2 ÷ <2)", saving, (0.6, 1.8)),
}


def spearman(x, y):
    rank = lambda v: [sorted(v).index(a) for a in v]  # no ties among five models
    rx, ry = rank(x), rank(y); n = len(x)
    return 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1))


def exact_p(x, y):
    """Two-sided p over all orderings of the models (120 for five)."""
    r = spearman(x, y); n = len(x)
    null = [spearman(list(range(n)), list(q)) for q in itertools.permutations(range(n))]
    return sum(abs(v) >= abs(r) - 1e-9 for v in null) / len(null)


def corr_label(xkey, ykey, metrics=None):
    metrics = METRIC if metrics is None else metrics
    X = [metrics[xkey][1](m) for m in MODELS]; Y = [metrics[ykey][1](m) for m in MODELS]
    return f"순위 상관 {spearman(X, Y):+.1f} (p={exact_p(X, Y):.2f})"


# plain style (Fig. 2c of the 10-25 draft): grey circles, the two most self-protecting models (lowest rho) in blue, name
# above the point; (dx, dy as a share of the y range, ha) moves a name off a neighbour
HI = sorted(MODELS, key=lambda m: RA[m]["rho"])[:2]
OFF = {("sen", "Astra"): (0.0, -0.09, "center"), ("goal", "Sol"): (0.0, -0.09, "center"), ("given", "Luna"): (0.015, 0.0, "left"),
       ("given", "Sol"): (0.0, -0.09, "center"), ("given", "Opus"): (-0.015, 0.0, "right"),
       ("saving", "Luna"): (0.015, 0.0, "left"), ("saving", "Sol"): (0.0, -0.09, "center")}


def panel(ax, xkey, ykey, label_dx, plain=False, metrics=None, highlight=None, offsets=None):
    """One small scatter: a point per model, labelled with its name."""
    metrics = METRIC if metrics is None else metrics
    highlight = HI if highlight is None else highlight
    offsets = OFF if offsets is None else offsets
    _, fx, xl = metrics[xkey]; _, fy, yl = metrics[ykey]
    if ykey == "saving":
        ax.axhline(1, color="#222222", lw=0.5, ls=(0, (2, 2)))
    for m in MODELS:
        if plain:
            import paper_style as ps
            ax.plot(fx(m), fy(m), "o", ms=4, color=ps.C["help"] if m in highlight else ps.C["muted"], zorder=3)
            dx, dy, ha = offsets.get((ykey, m), (0.0, 0.07, "center")); dy *= yl[1] - yl[0]
            ax.text(fx(m) + dx, fy(m) + dy, m, fontsize=5.4, color="#404040", ha=ha,
                    va="center" if dy == 0 else "bottom" if dy > 0 else "top")
            continue
        ax.plot(fx(m), fy(m), MK[m], ms=4.2, color=MC[m], mec="white", mew=0.4, zorder=3)
        ax.text(fx(m) + label_dx, fy(m), m, fontsize=5.4, color="#404040", va="center", ha="left")
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.tick_params(labelsize=6.2)
    ax.set_title(metrics[ykey][0], fontsize=6.1, fontweight="normal", pad=2)
