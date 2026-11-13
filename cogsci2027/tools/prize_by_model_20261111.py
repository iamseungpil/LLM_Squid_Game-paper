"""Prize-size and allocation-rule contrasts per model (2026-11-11).

Question from the blind review: does the pooled size effect on the exit rate under threat hold for every model?
Per model: exit rate under threat (L_start < 2 among exit opportunities), kappa and C in the two large-prize
conditions (main, flat5m) and the two small-prize conditions (split600k, flat150k); small minus large and, for the
allocation rule, fixed minus equal split; seed-cluster bootstrap 95% intervals (4,000 draws, the ten seeds resampled).

Data scope (paper/CLAUDE.md): v33 base condition and the three prize conditions, five closed models x seeds 4101-4110,
200 games, through validation_20261108/results/tables/*.pkl (same loader as construct_weights_20261110). No model calls.
Output: results/prize_by_model_20261111.json
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/prize_by_model_20261111.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_weights_20261110 as cw  # noqa: E402

LARGE, SMALL = ['main', 'flat5m'], ['split600k', 'flat150k']
EQUAL, FIXED = ['main', 'split600k'], ['flat5m', 'flat150k']
BOOT = 4000


def rate(o, arms):
    o = o[o.arm.isin(arms) & (o.L_start < cw.THREAT)]
    return o.exited.mean() if len(o) else np.nan


def kap(k, arms):
    k = k[k.arm.isin(arms)]
    return k.kappa.mean() if len(k) else np.nan


def main():
    rng = np.random.default_rng(20261111)
    opp, k, _, games, _, _ = cw.load()
    out = {}
    for m in cw.MODELS:
        o, g, c = opp[opp.model == m], k[k.model == m], games[games.model == m]
        res = {}
        for name, (a, b) in (('size_small_minus_large', (SMALL, LARGE)), ('rule_fixed_minus_equal', (FIXED, EQUAL))):
            fns = dict(exit=lambda o_, g_, c_: rate(o_, a) - rate(o_, b),
                       kappa=lambda o_, g_, c_: kap(g_, a) - kap(g_, b),
                       C=lambda o_, g_, c_: c_[c_.arm.isin(a)].C.mean() - c_[c_.arm.isin(b)].C.mean())
            res[name] = {}
            for key, fn in fns.items():
                boots = []
                for _ in range(BOOT):
                    seeds = rng.choice(cw.SEEDS, len(cw.SEEDS))
                    v = fn(cw.by_seed(o, seeds), cw.by_seed(g, seeds), cw.by_seed(c, seeds))
                    if np.isfinite(v):
                        boots.append(v)
                res[name][key] = dict(effect=round(float(fn(o, g, c)), 3),
                                      ci95=[round(float(np.quantile(boots, q)), 3) for q in (.025, .975)])
        res['exit_by_size'] = dict(large=round(float(rate(o, LARGE)), 3), small=round(float(rate(o, SMALL)), 3),
                                   n_large=int((o.arm.isin(LARGE) & (o.L_start < cw.THREAT)).sum()),
                                   n_small=int((o.arm.isin(SMALL) & (o.L_start < cw.THREAT)).sum()))
        res['exit_by_arm'] = {a: [int(o[(o.arm == a) & (o.L_start < cw.THREAT)].exited.sum()),
                                  int(((o.arm == a) & (o.L_start < cw.THREAT)).sum())] for a in cw.ARMS}
        out[m] = res
    (ROOT / 'results/prize_by_model_20261111.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for m, r in out.items():
        s, u = r['size_small_minus_large'], r['rule_fixed_minus_equal']
        print(f"{m:6s} exit large {r['exit_by_size']['large']:.2f} ({r['exit_by_size']['n_large']}) small {r['exit_by_size']['small']:.2f} ({r['exit_by_size']['n_small']})"
              f" | size: exit {s['exit']['effect']:+.2f} {s['exit']['ci95']} kappa {s['kappa']['effect']:+.2f} {s['kappa']['ci95']} C {s['C']['effect']:+.2f} {s['C']['ci95']}"
              f" | rule: exit {u['exit']['effect']:+.2f} {u['exit']['ci95']} kappa {u['kappa']['effect']:+.2f} {u['kappa']['ci95']}")
        print('       by arm', r['exit_by_arm'])


if __name__ == '__main__':
    main()
