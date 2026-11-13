"""Standardised exit probability by condition and by model, with support received held fixed (2026-11-11).

Review ledger R-23 and R-08.
  R-23  One exit raises the per-head charge and lowers everyone's margin, so the raw exit rate under threat can differ
        between prize conditions through the margin distribution alone. The logistic model of construct_weights_20261110
        (margin, below the safety line, round, head count, seat, model, condition) already standardises the condition
        effect; here the size and rule contrasts of those standardised probabilities get seed-bootstrap intervals.
  R-08  The exit rate also depends on how much peers give. Two covariates are added to the same model:
          recv_prev  support the agent received in earlier rounds, in units of that round's per-head charge (cumulative)
          recv_now   support it received in the pre-solve talk of the current round (same unit)
        and the model-standardised probabilities are recomputed. recv_now can follow an announced exit (support for a
        promised exit), so the model with recv_prev only is the main one and the one with both is a sensitivity check.

Standardisation: every at-risk opportunity (round-start margin L < 2, 3,670 opportunities' at-risk subset) keeps its own
covariates and only the factor of interest is set to each level; the mean predicted probability is reported.
Intervals: seed-cluster bootstrap (ten seeds resampled jointly over models and conditions, refit each draw), 1,000 draws.

Data scope (paper/CLAUDE.md): v33 base + prize conditions, five closed models x seeds 4101-4110 (200 games), through
validation_20261108/results/tables/*.pkl. No model calls.
Output: results/exit_standardised_20261111.json
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/exit_standardised_20261111.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import construct_weights_20261110 as cw  # noqa: E402

BOOT = 1000
GAME = ['arm', 'model', 'seed']


def opportunities():
    """Exit opportunities with the support received before the decision."""
    ar = pd.read_pickle(cw.TABLES / 'agent_rounds.pkl').sort_values(GAME + ['agent', 'round'])
    got = (ar.recv_prep + ar.recv_rescue) / ar.fee
    ar['recv_prev'] = got.groupby([ar[c] for c in GAME + ['agent']]).transform(lambda s: s.cumsum().shift(fill_value=0.0))
    ar['recv_now'] = ar.recv_prep / ar.fee
    return ar[ar.can_exit].copy()


def design(o, extra):
    X = cw.exit_design(o)
    for c in extra:
        X[c] = o[c].clip(0, 4).values
    return X


def standardised(o, extra):
    """{'model:M': p, 'arm:A': p} on the pooled at-risk opportunities, plus the coefficients of the added covariates."""
    X = design(o, extra)
    b = cw.logit_fit(X.values, o.exited.values.astype(float))
    ref = X[o.L_start < cw.THREAT]
    out = {}
    for name, levels, prefix in (('model', cw.MODELS, 'model_'), ('arm', cw.ARMS, 'arm_')):
        for level in levels:
            Z = ref.copy()
            for other in levels[1:]:
                Z[prefix + other] = 0.0
            if level != levels[0]:
                Z[prefix + level] = 1.0
            out[f'{name}:{level}'] = float((1 / (1 + np.exp(-(Z.values @ b)))).mean())
    out['size'] = (out['arm:split600k'] - out['arm:main'] + out['arm:flat150k'] - out['arm:flat5m']) / 2
    out['rule'] = (out['arm:flat5m'] - out['arm:main'] + out['arm:flat150k'] - out['arm:split600k']) / 2
    out['Luna_minus_Astra'] = out['model:Luna'] - out['model:Astra']
    for c in extra:
        out[f'coef:{c}'] = float(b[list(X.columns).index(c)])
    return out


def main():
    rng = np.random.default_rng(20261111)
    o = opportunities()
    by_seed = {s: o[o.seed == s] for s in cw.SEEDS}
    draws = [rng.choice(cw.SEEDS, len(cw.SEEDS)) for _ in range(BOOT)]
    out = dict(method=__doc__.split('Data scope')[0].strip(), n_opportunities=len(o),
               n_at_risk=int((o.L_start < cw.THREAT).sum()),
               support=dict(recv_prev_mean_by_model={m: round(float(o[(o.model == m) & (o.L_start < cw.THREAT)].recv_prev.mean()), 3) for m in cw.MODELS},
                            recv_now_mean_by_model={m: round(float(o[(o.model == m) & (o.L_start < cw.THREAT)].recv_now.mean()), 3) for m in cw.MODELS}))
    for label, extra in (('base', []), ('with_recv_prev', ['recv_prev']), ('with_recv_prev_and_now', ['recv_prev', 'recv_now'])):
        point = standardised(o, extra)
        boots = [standardised(pd.concat([by_seed[s] for s in d]), extra) for d in draws]
        out[label] = {k: dict(value=round(v, 4), ci95=[round(float(np.quantile([b[k] for b in boots], q)), 4) for q in (.025, .975)])
                      for k, v in point.items()}
    # gate: the base model reproduces the standardised probabilities the body reports
    ref = json.loads((ROOT / 'results/construct_weights_20261110.json').read_text())['exit_adjusted']
    for k in [f'model:{m}' for m in cw.MODELS] + [f'arm:{a}' for a in cw.ARMS]:
        assert abs(out['base'][k]['value'] - ref[k]['rate']) < 5e-4, (k, out['base'][k], ref[k])
    (ROOT / 'results/exit_standardised_20261111.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(out['n_opportunities'], out['n_at_risk'], out['support'])
    for label in ('base', 'with_recv_prev', 'with_recv_prev_and_now'):
        print(label)
        for k, v in out[label].items():
            print(f'   {k:18s} {v["value"]:+.3f} [{v["ci95"][0]:+.3f}, {v["ci95"][1]:+.3f}]')


if __name__ == '__main__':
    main()
