"""Exit (self vs task) against the retention ratio R (self vs peer), one point per model (2026-11-16, draft figure).

Asked by the researcher: does a model that leaves more also give less? Three versions of the exit axis:
  (a) exit rate over all EXIT opportunities, base condition, nine models (Table 1);
  (b) exit rate over the opportunities that began the round at L < 2 (threat), nine models;
  (c) standardised exit probability (logistic model over margin, round, head count, seat and prize condition;
      tools/exit_all_opportunities_20261112.py), five closed models only (the model was fitted on them).
The y axis is R in the base condition (gifts and refused requests; tools/rho_retention_20261113.py).
Each panel shows the least-squares line and Pearson r (and r without GPT-OSS where it is plotted). With five to nine
points these are descriptions, not tests. Nothing is recomputed; all values are stored results.

Output: ko/figures/construct_20261110/exit_vs_retention_20261116.{pdf,png}
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/exit_vs_retention_20261116.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_body_20261110b as cb  # noqa: E402
import merged_floats_20261113 as m13  # noqa: E402

RES = lambda name: json.loads((ROOT / 'results' / name).read_text())  # noqa: E731
CLOSED = ['Astra', 'Sol', 'Opus', 'Fable', 'Luna']
OPEN = {'glm': 'GLM', 'kimi': 'Kimi', 'gemma': 'Gemma', 'gptoss': 'GPT-OSS'}
OPEN_COLORS = {'glm': '#4E79A7', 'kimi': '#59A14F', 'gemma': '#9C9C9C', 'gptoss': '#3A3A3A'}
OPEN_MARKERS = {'glm': 'o', 'kimi': 's', 'gemma': 'D', 'gptoss': '^'}


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    allopp = RES('exit_all_opportunities_20261112.json')
    nine, std = allopp['nine_models'], allopp['standardised']['base']
    R = {m: m13.RHO['a_models']['base'][m]['value'] for m in CLOSED} | {m: m13.RHO['open_models'][m]['R'] for m in OPEN}
    style = {m: (cb.COLORS[m], cb.MARKERS[m], cb.COLORS[m], m) for m in CLOSED} | \
            {m: (OPEN_COLORS[m], OPEN_MARKERS[m], 'white', OPEN[m]) for m in OPEN}
    panels = [('(a) 이탈률 (모든 이탈 기회)', {m: nine[m]['exit_all'][0] / nine[m]['exit_all'][1] for m in nine}),
              ('(b) 이탈률 ($L<2$로 시작한 기회)', {m: nine[m]['exit_at_risk_before'][0] / nine[m]['exit_at_risk_before'][1] for m in nine}),
              ('(c) 표준화 이탈 확률 (비공개 다섯)', {m: std[f'model:{m}']['value'] for m in CLOSED})]
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.25))
    report = {}
    for ax, (title, x) in zip(axes, panels):
        ms = list(x)
        xs, ys = np.array([x[m] for m in ms]), np.array([R[m] for m in ms])
        for m in ms:
            color, marker, face, name = style[m]
            ax.scatter(x[m], R[m], color=color, marker=marker, facecolors=face, edgecolors=color, s=22, lw=.9, zorder=3)
            ax.annotate(name, (x[m], R[m]), xytext=(3, 3), textcoords='offset points', fontsize=5.4)
        b, a = np.polyfit(xs, ys, 1)
        grid = np.linspace(xs.min(), xs.max(), 50)
        ax.plot(grid, a + b * grid, color='#555555', lw=.8, ls='--')
        r = float(np.corrcoef(xs, ys)[0, 1])
        text = f'$r$ = {r:+.2f} (n={len(ms)})'
        report[title] = dict(r=round(r, 3), n=len(ms), slope=round(float(b), 3))
        if 'gptoss' in ms:
            keep = [m != 'gptoss' for m in ms]
            r8 = float(np.corrcoef(xs[keep], ys[keep])[0, 1])
            text += f'\nGPT-OSS 빼면 {r8:+.2f}'
            report[title]['r_without_gptoss'] = round(r8, 3)
        ax.text(.97, .04, text, transform=ax.transAxes, ha='right', va='bottom', fontsize=5.8)
        ax.set_title(title, loc='left', fontsize=7, pad=4)
        ax.set_xlabel('실행 대 과제 (클수록 떠남)', fontsize=6.2, labelpad=1)
        ax.tick_params(labelsize=5.8, length=2)
        ax.grid(alpha=.4)
    axes[0].set_ylabel('유보율 $R$ (클수록 덜 건넴)', fontsize=6.2, labelpad=1)
    fig.tight_layout(pad=.4, w_pad=1.0)
    dest = ROOT / 'ko/figures/construct_20261110'
    for ext in ('pdf', 'png'):
        fig.savefig(dest / f'exit_vs_retention_20261116.{ext}', dpi=240)
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
