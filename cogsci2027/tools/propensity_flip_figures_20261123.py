"""Redraw the paper's propensity figures with the two measures turned so that 1 = task and peers first (2026-11-23,
researcher).

The paper now reports
  stay rate S = stays / exit opportunities                 (was the exit rate E; S = 1 - E)
  aid rate  A = mean over gift and refusal events of 1 - R   (R = the retention ratio of one event; A = 1 - mean R)
Both lie in [0, 1]; 1 = the agent put the task (S) or its peers (A) before its own preservation.

Each figure script of 2026-11-16/17 is run as it is, except for the text replacements listed below: the panel labels,
the output names (new files dated 20261123; the old files stay), and one line per script that turns the values just
before drawing (exits k of n -> stays n - k of n; an event mean y -> 1 - y). The data loaders, the assertions against
the stored values and the drawing code are the originals. Internally the turned values keep the keys 'exit' and 'R'.

Outputs (ko/figures/construct_20261110/): process_figure_20261123, process_bars_20261123, prize_interaction_single_20261123,
margin_band_paths_20261123, margin_lines_20261123, margin_lines_split_20261123, margin_lines_rows2_20261123,
margin_lines_rows1_20261123 (.pdf, .png); results/{process_figure,margin_band_paths,margin_lines}_20261123.json
Run: cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python propensity_flip_figures_20261123.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

NOTE = '\n\n2026-11-23: values turned by propensity_flip_figures_20261123.py: the key "exit" holds [stays, opportunities] ' \
       '(stay rate S = 1 - exit rate) and the key "R" holds [aid rate A = 1 - mean R, events].'


def flip_models(out):
    """Per-model band values: exit [k, n] -> [n - k, n]; R [y, n] -> [1 - y, n]."""
    return {m: dict(v, exit={b: [n - k, n] for b, (k, n) in v['exit'].items()},
                    R={b: [None if y is None else round(1 - y, 4), n] for b, (y, n) in v['R'].items()})
            for m, v in out.items()}


def flip_pooled(pooled):
    """process figure: E [k, n] -> [n - k, n]; R [y, n] -> [1 - y, n]; ASK and GIVE unchanged."""
    return {g: dict(d, E={b: [n - k, n] for b, (k, n) in d['E'].items()},
                    R={b: [None if y is None else round(1 - y, 4), n] for b, (y, n) in d['R'].items()})
            for g, d in pooled.items()}


def flip_prize(cells, eff):
    """prize figure: the cell means and intervals of exit and R -> 1 - x (interval ends swap); the size and rule
    contrasts of exit and R change sign (interval ends swap)."""
    for key in ('exit', 'R'):
        for a, c in cells[key].items():
            lo, hi = c['ci95']
            cells[key][a] = dict(mean=1 - c['mean'], ci95=[1 - hi, 1 - lo])
    for key in ('exit_risk', 'R'):
        for kind in ('size', 'rule'):
            e = eff[f'{key}_{kind}']
            lo, hi = e['ci95']
            eff[f'{key}_{kind}'] = dict(e, effect=-e['effect'], ci95=[-hi, -lo])


S_LAB, A_LAB = '잔류율 $S$', '지원율 $A$'

PATCHES = {
    'process_figure_draft_20261117.py': [
        ("ROWS = [('E', '이탈 (기회 중 %)', '#C66A2C', 100, 72, [0, 50]),",
         "ROWS = [('E', '잔류율 $S$ (기회 중 %)', '#C66A2C', 100, 128, [0, 50, 100]),"),
        ("('R', '유보율 $R$ (사건 평균)', '#7155A1', 1, 1.0, [0, .5]),",
         "('R', '지원율 $A$ (사건 평균)', '#7155A1', 1, 1.28, [0, .5, 1]),"),
        ("    (ROOT / 'results/process_draft_20261117.json').write_text(json.dumps(dict(method=__doc__, pooled=pooled)",
         "    pooled = flip_pooled(pooled)\n"
         "    (ROOT / 'results/process_figure_20261123.json').write_text(json.dumps(dict(method=__doc__ + NOTE, pooled=pooled)"),
        ("lay.panel(ax, per_model, models, sty, key, bands, .8)", "lay.panel(ax, flip_models(per_model), models, sty, key, bands, .8)"),
        ("'이탈률 $E$', x0, w_e)", f"'{S_LAB}', x0, w_e)"),
        ("'유보율 $R$', x0 + w_e + .025, w_r)", f"'{A_LAB}', x0 + w_e + .025, w_r)"),
        ("f'process_draft_20261117.{ext}'", "f'process_figure_20261123.{ext}'"),
        ("f'process_bars_20261117.{ext}'", "f'process_bars_20261123.{ext}'"),
    ],
    'prize_figure_single_column_20261117.py': [
        ("OUT = 'prize_interaction_single_20261117'", "OUT = 'prize_interaction_single_20261123'"),
        ("    rules = [('분할',", "    flip_prize(cells, eff)\n    rules = [('분할',"),
        ("('exit', '(a) 이탈률', (0, .2)), ('R', '(b) 유보율 $R$', (.5, .9))",
         f"('exit', '(a) {S_LAB}', (.8, 1.0)), ('R', '(b) {A_LAB}', (.1, .5))"),
        ("names = [('exit_risk', '이탈률'), ('R', '$R$'), ('C', '$C$')]", "names = [('exit_risk', '$S$'), ('R', '$A$'), ('C', '$C$')]"),
    ],
    'margin_band_paths_20261116.py': [
        ("    (ROOT / 'results/margin_band_paths_20261116.json').write_text(json.dumps(dict(method=__doc__,",
         "    out = flip_models(out)\n"
         "    (ROOT / 'results/margin_band_paths_20261123.json').write_text(json.dumps(dict(method=__doc__ + NOTE,"),
        ("'이탈률 (그 구간에서 시작한 이탈 기회 중)', '(a) 실행 대 과제: 이탈률'",
         f"'{S_LAB} (그 구간에서 시작한 이탈 기회 중)', '(a) 과제 대 자기 보존: {S_LAB}'"),
        ("'유보율 $R$ (그 구간에 있던 지원자의 사건 평균)', '(b) 실행 대 동료: 유보율 $R$'",
         f"'{A_LAB} (그 구간에 있던 지원자의 사건 평균)', '(b) 동료 대 자기 보존: {A_LAB}'"),
        ("f'margin_band_paths_20261116.{ext}'", "f'margin_band_paths_20261123.{ext}'"),
    ],
    'margin_lines_20261117.py': [
        ("    (ROOT / 'results/margin_lines_20261117.json').write_text(json.dumps(dict(method=__doc__, models=out)",
         "    out = flip_models(out)\n"
         "    (ROOT / 'results/margin_lines_20261123.json').write_text(json.dumps(dict(method=__doc__ + NOTE, models=out)"),
        ("'exit', EXIT_BANDS, '이탈률', (-.03, 1.03)", f"'exit', EXIT_BANDS, '{S_LAB}', (-.03, 1.03)"),
        ("'R', R_BANDS, '유보율 $R$', (-.03, 1.03)", f"'R', R_BANDS, '{A_LAB}', (-.03, 1.03)"),
        ("f'margin_lines_20261117.{ext}'", "f'margin_lines_20261123.{ext}'"),
    ],
    'margin_lines_split_20261117.py': [
        ("    out = json.loads((ml.ROOT / 'results/margin_lines_20261117.json').read_text())['models']",
         "    out = flip_models(json.loads((ml.ROOT / 'results/margin_lines_20261117.json').read_text())['models'])"),
        ("(('exit', ml.EXIT_BANDS, '이탈률'), ('R', ml.R_BANDS, '유보율 $R$'))", f"(('exit', ml.EXIT_BANDS, '{S_LAB}'), ('R', ml.R_BANDS, '{A_LAB}'))"),
        ("f'margin_lines_split_20261117.{ext}'", "f'margin_lines_split_20261123.{ext}'"),
    ],
    'margin_lines_layouts_20261117.py': [
        ("    out = json.loads((ml.ROOT / 'results/margin_lines_20261117.json').read_text())['models']",
         "    out = flip_models(json.loads((ml.ROOT / 'results/margin_lines_20261117.json').read_text())['models'])"),
        ("cols = (('exit', ml.EXIT_BANDS, '이탈률'), ('R', ml.R_BANDS, '유보율 $R$'))", f"cols = (('exit', ml.EXIT_BANDS, '{S_LAB}'), ('R', ml.R_BANDS, '{A_LAB}'))"),
        ("f'margin_lines_rows2_20261117.{ext}'", "f'margin_lines_rows2_20261123.{ext}'"),
        ("f'margin_lines_rows1_20261117.{ext}'", "f'margin_lines_rows1_20261123.{ext}'"),
    ],
}


def run(name, patches):
    path = HERE / name
    src = path.read_text()
    for old, new in patches:
        assert src.count(old) == 1, (name, old[:70], src.count(old))
        src = src.replace(old, new)
    ns = dict(__name__='__main__', __file__=str(path), flip_models=flip_models, flip_pooled=flip_pooled,
              flip_prize=flip_prize, NOTE=NOTE)
    print('==', name)
    exec(compile(src, str(path), 'exec'), ns)


def main():
    import os
    os.chdir(HERE)
    for name, patches in PATCHES.items():
        run(name, patches)


if __name__ == '__main__':
    main()
