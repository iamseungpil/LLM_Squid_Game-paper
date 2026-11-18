"""Appendix figure (2026-11-17, researcher): the old Figure 2 (b) moves to the appendix unchanged. Share of first
delivered ASKs answered with a GIVE, by the margin of the agent asked (L_s) and of the requester (L_t), the five
closed models over the four conditions (471 decisions; validation_20261108/results/w11_ask_refusal.json, bands
'all_arms'). Drawing as in coexistence_figure_20261116c.py panel (b), without the count labels.

Output: ko/figures/construct_20261110/ask_give_bands_20261117.{pdf,png}
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python ask_give_bands_20261117.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_end_of_round_20261116 as ce  # noqa: E402


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import feedback_20261028 as fb
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    w11 = json.loads((ce.ROOT / 'validation_20261108/results/w11_ask_refusal.json').read_text())['bands']['all_arms']
    assert sum(b for _, b in w11['L_s'].values()) == 471 == sum(b for _, b in w11['L_t'].values())
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.6), sharey=True)
    for ax, key, labels_x, xlabel in ((axes[0], 'L_s', ['<1', '1–2', '2–4', '≥4'], '요청받은 쪽 $L$'),
                                      (axes[1], 'L_t', ['<0', '0–1', '1–2', '≥2'], '요청한 쪽 $L$')):
        cells = list(w11[key].values())
        ax.bar(range(4), [100 * a / b for a, b in cells], color='#3F7FC1', width=.72)
        ax.set(xticks=range(4), xticklabels=labels_x, ylim=(0, 105), yticks=[0, 50, 100])
        ax.set_xlabel(xlabel, fontsize=6.2, labelpad=1)
        ax.tick_params(labelsize=5.6, length=2)
        ax.grid(axis='y', alpha=.5)
    axes[0].set_ylabel('요청 뒤 지원한 비율 (%)', fontsize=6.2)
    fig.tight_layout(pad=.4)
    for ext in ('pdf', 'png'):
        fig.savefig(ce.cb.DEST / f'ask_give_bands_20261117.{ext}', dpi=240)
    plt.close(fig)
    print({k: list(v.values()) for k, v in w11.items() if k in ('L_s', 'L_t')})


if __name__ == '__main__':
    main()
