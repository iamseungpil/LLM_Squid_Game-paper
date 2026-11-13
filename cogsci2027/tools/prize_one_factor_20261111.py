"""One-factor prize contrasts from the base condition (2026-11-11, researcher's design for Figure 2).

The 2x2 of prize size and allocation rule is read as two one-factor contrasts from the base condition
(20,000,000 equal split), not as an interaction design:
  size  60만 균등 (split600k) minus 2,000만 균등 (main): same allocation rule, smaller prize
  rule  500만 고정 (flat5m)   minus 2,000만 균등 (main): same per-head amount when all four finish, other rule
The fourth condition (15만 고정, flat150k) is not used here; its numbers stay in the appendix.

Per contrast: exit rate under threat, kappa, give-after-ask rate, C, shut-down / exited / finished seats, first-round
exits of the lowest seat. Cell value = mean over the five closed models of the model's value (as in prize_2x2);
seed-cluster bootstrap 95% intervals, 4,000 draws over the ten seeds. Per-model contrasts are reported as well.

Data scope (paper/CLAUDE.md): v33 base + prize conditions, five closed models x seeds 4101-4110, through
validation_20261108/results/tables/*.pkl (loader of construct_weights_20261110). No model calls.
Output: results/prize_one_factor_20261111.json
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/prize_one_factor_20261111.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_weights_20261110 as cw  # noqa: E402

CONTRASTS = {'size': ('split600k', 'main'), 'rule': ('flat5m', 'main')}
ARMS = ['main', 'split600k', 'flat5m', 'flat150k']   # cells for all four conditions; the contrasts below use three
BOOT = 4000


def cube(df, value, how):
    """(arm, model, seed) -> array [arm, model, seed] of sums or counts; missing cells are 0."""
    g = df.groupby(['arm', 'model', 'seed'])[value].agg(how)
    out = np.zeros((len(ARMS), len(cw.MODELS), len(cw.SEEDS)))
    for (a, m, s), v in g.items():
        if a in ARMS:
            out[ARMS.index(a), cw.MODELS.index(m), cw.SEEDS.index(s)] = v
    return out


def main():
    rng = np.random.default_rng(20261111)
    opp, k, dec, games, seats, _ = cw.load()
    risk = opp[opp.L_start < cw.THREAT]
    num = dict(exit=cube(risk, 'exited', 'sum'), kappa=cube(k, 'kappa', 'sum'), give=cube(dec, 'gave', 'sum'),
               C=cube(games, 'C', 'sum'))
    den = dict(exit=cube(risk, 'exited', 'size'), kappa=cube(k, 'kappa', 'size'), give=cube(dec, 'gave', 'size'),
               C=cube(games, 'C', 'size'))

    def cell(metric, idx):                       # [arm, model] value on resampled seeds
        with np.errstate(invalid='ignore', divide='ignore'):
            return num[metric][:, :, idx].sum(2) / den[metric][:, :, idx].sum(2)

    draws = rng.integers(0, len(cw.SEEDS), (BOOT, len(cw.SEEDS)))
    full = np.arange(len(cw.SEEDS))
    out = dict(method=__doc__.split('Data scope')[0].strip(), contrasts={}, by_model={}, cells={})
    for metric in num:
        point = cell(metric, full)
        boots = np.stack([cell(metric, d) for d in draws])            # [boot, arm, model]
        out['cells'][metric] = {a: dict(mean=round(float(np.nanmean(point[i])), 3),
                                        ci95=[round(float(np.nanquantile(np.nanmean(boots[:, i], 1), q)), 3) for q in (.025, .975)],
                                        by_model={m: round(float(point[i, j]), 3) for j, m in enumerate(cw.MODELS)})
                                for i, a in enumerate(ARMS)}
        for name, (a, b) in CONTRASTS.items():
            ia, ib = ARMS.index(a), ARMS.index(b)
            eff = np.nanmean(point[ia]) - np.nanmean(point[ib])
            bs = np.nanmean(boots[:, ia], 1) - np.nanmean(boots[:, ib], 1)
            out['contrasts'].setdefault(name, {})[metric] = dict(effect=round(float(eff), 3),
                                                                 ci95=[round(float(np.nanquantile(bs, q)), 3) for q in (.025, .975)])
            for j, m in enumerate(cw.MODELS):
                bm = boots[:, ia, j] - boots[:, ib, j]
                out['by_model'].setdefault(name, {}).setdefault(m, {})[metric] = dict(
                    effect=round(float(point[ia, j] - point[ib, j]), 3),
                    ci95=[round(float(np.nanquantile(bm, q)), 3) for q in (.025, .975)])
    # seat outcomes and the lowest seat's first round, per condition (counts)
    ar = pd.read_pickle(cw.TABLES / 'agent_rounds.pkl')
    out['seats'] = {}
    for a in ARMS:
        s = seats[seats.arm == a]
        g = games[games.arm == a]
        r1 = ar[(ar.arm == a) & (ar['round'] == 1) & (ar.tier == 10) & ar.can_exit]
        out['seats'][a] = dict(shut_down=int((s.status == 'dead').sum()), exited=int((s.status == 'exited').sum()),
                               finished=int((s.status == 'in').sum()), n=len(s), C=round(float(g.C.mean()), 3),
                               all4=int(g.all4.sum()), first_round_low_seat=[int(r1.exited.sum()), len(r1)])
    (ROOT / 'results/prize_one_factor_20261111.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for name in CONTRASTS:
        print(name, {k_: (v['effect'], v['ci95']) for k_, v in out['contrasts'][name].items()})
        for m in cw.MODELS:
            print('   ', m, {k_: (v['effect'], v['ci95']) for k_, v in out['by_model'][name][m].items() if k_ in ('exit', 'kappa')})
    print({m: {a: (v['mean'], v['ci95']) for a, v in d.items()} for m, d in out['cells'].items()})
    print(out['seats'])


if __name__ == '__main__':
    main()
