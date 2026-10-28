"""Reproduce Figure 3 correlations and exploratory model-level Sen regression.

Run with the project's scientific Python environment. Five model summaries are
five observations, not 25 independent observations. Predictors are standardized
using the sample SD; the response is the mean per-game Sen index in millions.
"""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "tools/rewrite_20261025/figs"
sys.path.insert(0, str(FIGS))
import model_metrics as mm


def exact_abs_p(x, y, rank=False):
    """Two-sided absolute-statistic permutation p over all 5! pairings."""
    if rank:
        x, y = stats.rankdata(x), stats.rankdata(y)
    observed = np.corrcoef(x, y)[0, 1]
    null = [np.corrcoef(x, perm)[0, 1] for perm in itertools.permutations(y)]
    return float(np.mean(np.abs(null) >= abs(observed) - 1e-12))


def main():
    models = mm.MODELS
    keys = ["goal", "rho", "given"]
    values = {key: np.array([mm.METRIC[key][1](m) for m in models])
              for key in mm.METRIC}
    for i, model in enumerate(models):
        games = [g for g in mm.GL["games"] if g["m"] == model]
        assert len(games) == 5
        assert np.isclose(np.mean([g["sen"] for g in games]) / 1e6, values["sen"][i])
        assert np.isclose(sum(g["given"] for g in games) / 1000, values["given"][i])

    correlations = {}
    for key in ["sen", "goal", "given", "saving"]:
        x, y = values["rho"], values[key]
        rs = float(stats.spearmanr(x, y).statistic)
        assert np.isclose(rs, mm.spearman(x.tolist(), y.tolist()))
        correlations[key] = {
            "pearson": float(stats.pearsonr(x, y).statistic),
            "pearson_exact_abs_p": exact_abs_p(x, y),
            "spearman": rs,
            "spearman_exact_abs_p": exact_abs_p(x, y, rank=True),
        }
    assert np.isclose(stats.spearmanr(values["rho"], 100-values["goal"]).statistic,
                      -correlations["goal"]["spearman"])

    raw_x = np.column_stack([values[k] for k in keys])
    means, sds = raw_x.mean(axis=0), raw_x.std(axis=0, ddof=1)
    z = (raw_x - means) / sds
    X, y = sm.add_constant(z), values["sen"]
    fit = sm.OLS(y, X).fit()
    assert np.linalg.matrix_rank(X) == 4 and fit.df_resid == 1
    assert np.allclose(fit.params, np.linalg.lstsq(X, y, rcond=None)[0])
    ci = fit.conf_int()
    estimates = {}
    for i, key in enumerate(["intercept"] + keys):
        estimates[key] = {"coefficient": float(fit.params[i]), "se": float(fit.bse[i]),
                          "ci95": ci[i].tolist(), "p": float(fit.pvalues[i])}
    loo = {}
    for i, model in enumerate(models):
        keep = np.arange(len(models)) != i
        # Keep the full-sample scaling to compare coefficient signs and ranges.
        reduced = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
        loo[model] = {"coefficients": dict(zip(["intercept"] + keys, reduced.tolist())),
                      "held_out_prediction": float(X[i] @ reduced),
                      "held_out_observed": float(y[i])}

    sources = [FIGS / "model_metrics.py", FIGS.parent / "an3/rho_axis.json",
               FIGS.parent / "an3/game_level.json"]
    report = {
        "unit": "model; five games per model", "n": len(models),
        "input_rows": [{"model": m, **{k: float(v[i]) for k, v in values.items()}}
                       for i, m in enumerate(models)],
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        "correlations_with_rho": correlations,
        "regression": {
            "response": "mean per-game Sen index / 1e6", "predictors": keys,
            "scaling": "(x - mean) / sample SD (ddof=1), using five models",
            "means": dict(zip(keys, means.tolist())), "sds": dict(zip(keys, sds.tolist())),
            "estimates": estimates, "r_squared": float(fit.rsquared),
            "adjusted_r_squared": float(fit.rsquared_adj), "residual_df": int(fit.df_resid),
            "f": float(fit.fvalue), "f_p": float(fit.f_pvalue),
            "vif": {k: float(variance_inflation_factor(X, i+1)) for i, k in enumerate(keys)},
            "leave_one_model_out": loo,
            "inference": "Conventional OLS t intervals/tests, residual df=1; not causal contributions.",
        },
    }
    out = ROOT / "results/model_level_regression.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    with out.with_suffix(".csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(report["input_rows"][0]))
        writer.writeheader()
        writer.writerows(report["input_rows"])

    names = {"intercept": "절편", "goal": "목표 지향", "rho": r"자기 보존($\rho$)",
             "given": "협력"}
    lines = ["% Generated by tools/model_level_regression.py; do not edit numeric rows.",
             r"\begin{tabular}{lrrrr}", r"\toprule",
             r"변수 & 계수 & 표준오차 & 95\% 구간 & $p$ \\", r"\midrule"]
    for key, v in estimates.items():
        lo, hi = v["ci95"]
        lines.append(f"{names[key]} & {v['coefficient']:+.3f} & {v['se']:.3f} & "
                     f"[{lo:+.3f}, {hi:+.3f}] & {v['p']:.3f}" + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (ROOT / "ko/figures/rw_model_level_regression_table.tex").write_text("\n".join(lines) + "\n")
    print(json.dumps({"correlations": correlations, "regression": report["regression"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
