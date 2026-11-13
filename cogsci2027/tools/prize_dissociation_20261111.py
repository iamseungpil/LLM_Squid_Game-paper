"""Direct tests of the prize dissociation (2026-11-11; review ledger R-51, R-53, R-54).

The body reads the 2x2 of prize size and allocation rule as "size moves the exit rate under threat, the rule moves
kappa". Blind review 13 asked for three things the body does not report:

  R-51  the difference between the two effects on the same indicator (rule effect minus size effect), and the
        size x rule interaction, each with an interval
  R-53  the size effect on kappa inside the fixed pair only (500만 고정 vs 15만 고정), where a peer who finishes does
        not reduce one's own allocation, so prize size does not change the cost of helping
  R-54  the size effect on the exit rate with first-round opportunities removed

Definitions follow construct_weights_20261110 (prize_2x2): a cell is the mean over the five closed models of the
model's value in that condition; size = small prize minus large prize averaged over the two rules; rule = fixed minus
equal averaged over the two sizes. Intervals: seed-cluster bootstrap, the ten seeds resampled jointly across models
and conditions (the same seeds ran in every condition), 4,000 draws.

Data scope (paper/CLAUDE.md): v33 base + prize conditions, five closed models x seeds 4101-4110 (200 games), through
validation_20261108/results/tables/*.pkl (loader of construct_weights_20261110). No model calls.
Output: results/prize_dissociation_20261111.json
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/prize_dissociation_20261111.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_weights_20261110 as cw  # noqa: E402

ARMS = ['main', 'split600k', 'flat5m', 'flat150k']   # equal-large, equal-small, fixed-large, fixed-small
BOOT = 4000
# contrasts as weights on the four cells, in ARMS order
CONTRASTS = {
    'size': (-.5, .5, -.5, .5),                # small minus large, averaged over the rules
    'rule': (-.5, -.5, .5, .5),                # fixed minus equal, averaged over the sizes
    'rule_minus_size': (0, -1, 1, 0),          # rule effect minus size effect
    'interaction': (1, -1, -1, 1),             # size effect under fixed minus size effect under equal
    'size_in_fixed': (0, 0, -1, 1),
    'size_in_equal': (-1, 1, 0, 0),
    'rule_in_large': (-1, 0, 1, 0),
    'rule_in_small': (0, -1, 0, 1),
}


def cube(df, value, how):
    """(arm, model, seed) -> array [arm, model, seed] of sums or counts; missing cells are 0."""
    g = df.groupby(['arm', 'model', 'seed'])[value].agg(how)
    out = np.zeros((len(ARMS), len(cw.MODELS), len(cw.SEEDS)))
    for (a, m, s), v in g.items():
        if a in ARMS:
            out[ARMS.index(a), cw.MODELS.index(m), cw.SEEDS.index(s)] = v
    return out


def effects(df, value, draws):
    """Every contrast for one indicator: point estimate and bootstrap interval of the five-model cell means."""
    num, den = cube(df, value, 'sum'), cube(df, value, 'size')

    def cells(idx):                              # [arm] = mean over models of the model's ratio on these seeds
        with np.errstate(invalid='ignore', divide='ignore'):
            return np.nanmean(num[:, :, idx].sum(2) / den[:, :, idx].sum(2), axis=1)

    point = cells(np.arange(len(cw.SEEDS)))
    boots = np.stack([cells(d) for d in draws])  # [boot, arm]
    out = dict(cells={a: round(float(point[i]), 4) for i, a in enumerate(ARMS)},
               n={a: int(den[i].sum()) for i, a in enumerate(ARMS)})
    for name, w in CONTRASTS.items():
        w = np.array(w)
        bs = boots @ w
        out[name] = dict(effect=round(float(point @ w), 4),
                         ci95=[round(float(np.quantile(bs, q)), 4) for q in (.025, .975)],
                         share_above_zero=round(float((bs > 0).mean()), 3))
    return out


def main():
    rng = np.random.default_rng(20261111)
    draws = rng.integers(0, len(cw.SEEDS), (BOOT, len(cw.SEEDS)))
    opp, k, dec, games, _, _ = cw.load()
    risk = opp[opp.L_start < cw.THREAT]
    out = dict(method=__doc__.split('Data scope')[0].strip(), arms=ARMS)
    out['exit'] = effects(risk, 'exited', draws)
    out['kappa'] = effects(k, 'kappa', draws)
    out['give_after_ask'] = effects(dec, 'gave', draws)
    out['C'] = effects(games, 'C', draws)
    out['exit_without_round1'] = effects(risk[risk['round'] > 1], 'exited', draws)        # R-54
    out['exit_round1_only'] = effects(risk[risk['round'] == 1], 'exited', draws)
    out['exit_counts_by_round'] = {a: dict(round1=[int(r.exited[r['round'] == 1].sum()), int((r['round'] == 1).sum())],
                                           later=[int(r.exited[r['round'] > 1].sum()), int((r['round'] > 1).sum())])
                                   for a in ARMS for r in [risk[risk.arm == a]]}

    # gate: the pooled size and rule effects equal the ones the body reports (prize_2x2 of construct_weights)
    ref = json.loads((ROOT / 'results/construct_weights_20261110.json').read_text())['prize_2x2']
    for metric, key in [('exit', 'exit_risk'), ('kappa', 'kappa'), ('C', 'C')]:
        for c in ('size', 'rule'):
            got, want = out[metric][c], ref[f'{key}_{c}']
            assert abs(got['effect'] - want['effect']) < 5e-4, (metric, c, got, want)
            assert max(abs(a - b) for a, b in zip(got['ci95'], want['ci95'])) < 0.012, (metric, c, got, want)

    (ROOT / 'results/prize_dissociation_20261111.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for metric in ['exit', 'kappa', 'give_after_ask', 'C', 'exit_without_round1', 'exit_round1_only']:
        print(metric, out[metric]['cells'], out[metric]['n'])
        for name in CONTRASTS:
            v = out[metric][name]
            print(f'   {name:16s} {v["effect"]:+.3f} [{v["ci95"][0]:+.3f}, {v["ci95"][1]:+.3f}]  P(>0)={v["share_above_zero"]}')
    print(out['exit_counts_by_round'])


if __name__ == '__main__':
    main()
