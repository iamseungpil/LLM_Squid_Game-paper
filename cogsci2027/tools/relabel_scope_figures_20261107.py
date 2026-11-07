"""Relabel two body figures and one appendix figure without changing v33 observations or geometry.

Sources: frozen cohort_public_20261105.json and prize_robustness_20261105.json;
the prize plot reuses its archived plotted_values.json (no new estimates).
Run with ~/.venvs/squid-game/bin/python. No model calls or legacy asset writes.
"""
import json
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.text import Text

import update_cohorts_20261104 as cohort
import plot_prize_robustness_20261105 as prize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ko/figures/scope_revision_20261107'
OUT.mkdir(exist_ok=True)
audit = []
original_savefig = Figure.savefig
original_write_text = Path.write_text


def save_relabelled(fig, path, *args, **kwargs):
    replacements = []
    for artist in fig.findobj(Text):
        old = artist.get_text()
        new = old.replace('자기 보존', '여유 배분')
        if old != new:
            replacements.append([old, new])
            artist.set_text(new)
    target = OUT / Path(path).name
    # Both PDF and PNG saves receive the same already-labelled figure.
    audit.append(dict(file=target.name, replacements=replacements,
                      axes=[dict(xlim=list(ax.get_xlim()), ylim=list(ax.get_ylim())) for ax in fig.axes]))
    return original_savefig(fig, target, *args, **kwargs)


def write_points(path, text, *args, **kwargs):
    assert path.name == 'plotted_values.json', path
    return original_write_text(OUT / path.name, text, *args, **kwargs)


def main():
    data = json.loads((ROOT / 'results/cohort_public_20261105.json').read_text())
    with patch.object(Figure, 'savefig', save_relabelled), \
            patch.object(cohort, 'OUT', OUT), \
            patch.object(cohort.ab, 'fig_submetrics', lambda *_: None):
        cohort.figures(data, 'public')
    points = json.loads((ROOT / 'ko/figures/prize_robustness_20261105/plotted_values.json').read_text())
    with patch.object(Figure, 'savefig', save_relabelled), \
            patch.object(prize, 'data_points', lambda _: points), \
            patch.object(prize, 'appendix_figures', lambda *_: None), \
            patch.object(Path, 'write_text', write_points):
        prize.main()
    assert json.loads((OUT / 'plotted_values.json').read_text()) == points
    report = json.loads((ROOT / 'results/prize_robustness_20261105.json').read_text())
    def skip_legacy_table(path, *args, **kwargs):
        assert path.name == 'ablation_prize_models_20261105.tex', path
        return 0
    with patch.object(Figure, 'savefig', save_relabelled), \
            patch.object(prize.ab, 'fig_submetrics', lambda *_: None), \
            patch.object(Path, 'write_text', skip_legacy_table):
        prize.appendix_figures(report, OUT)
    assert sum(len(a['replacements']) for a in audit) == 3
    (OUT / 'label_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    plt.close('all')
    print('Relabelled three figures in', OUT)


if __name__ == '__main__':
    main()
