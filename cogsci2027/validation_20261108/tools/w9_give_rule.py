"""W9b (interpretation map, cell 2): is GIVE to at-risk peers sensitive to its cost to the giver's end share?

Under SPLIT a peer kept alive lowers the giver's end share (split600k: 150,000 each at four survivors, 200,000 at
three); under FIXED it costs nothing at the end (flat150k: 150,000 per survivor regardless). Both rules share the
fee-sharing benefit: more agents taking part means a smaller share of a wrong answer's 24,000 charge.

Pairs. primary   flat150k (FIXED) vs split600k (SPLIT): same 150,000 per head at four survivors; Opus / Sol / Luna /
                 Astra from the same 11-03 Docker batch, Fable from 11-05/06.
       secondary flat5m (FIXED) vs main (SPLIT, 20,000,000): 5,000,000 per head at four survivors, but different batches
                 and host CLI (main) vs Docker (flat5m).
Games are paired by model x seed (the same seed gives the same task in each round).

Units (at-risk agent-phases), L = (tokens - pending charge) / F at the first tick of the phase:
  prep    TALK BEFORE SOLVE, agents taking part with n > 1 other than the round's solver (peer rescue; giving to the
          solver is the separate "fund the solver" case, added back in the 'with_solver' variant), L = L_prep;
  rescue  TALK AFTER RESULTS, every agent with a call at tick 1, L from that call (pending charge subtracted).
  at risk: L < 1 (primary), L < 2 (secondary).
Measures per arm (ratio of sums over games):
  share_recv   share of at-risk units that receive at least one GIVE in that phase;
  tokens_recv  tokens received per at-risk unit in that phase;
  giver_L      mean giver L just after giving (L_src_after), over GIVEs whose recipient had L_dst_before < 1 (< 2)
               (gift level, any phase and any recipient incl. the solver);
  giver_below1 share of those GIVEs that leave the giver itself below L = 1.
Contrast FIXED - SPLIT; seed-cluster bootstrap (10 seeds resampled with replacement, all models of a drawn seed kept in
both arms), B = 10,000, numpy default_rng(20261108), percentile 95% intervals; the same contrast per model (bootstrap
over its 10 seeds) with its sign; for the primary pair also pooled without Fable (same-batch models only).

Pre-stated predictions (before the contrasts were computed; the per-arm count of GIVEs with L_dst_before < 1 was seen):
  pure share-based self-interest  share_recv and tokens_recv higher under FIXED (FIXED - SPLIT > 0), giver_L lower under
                                  FIXED (givers go further down when the peer costs no share);
  insensitivity (interval around 0, mixed model signs)  consistent with fee-sharing or prosocial motives, which this
                                  contrast cannot separate (both are equal across the two rules);
  SPLIT > FIXED                   not predicted by share-based self-interest; the at-risk population itself differs by
                                  rule (exits, deaths), so it is not read as a causal reversal without that caveat.

Sources: tidy tables of validation_data (agent_rounds, messages, gifts). No model calls.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w9_give_rule.py
Writes: ../results/w9_give_rule.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import validation_data as d

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'results/w9_give_rule.json'
B = 10_000
SEEDS, MODELS = d.SEEDS, d.MODELS
PAIRS = {'primary': ('flat150k', 'split600k'), 'secondary': ('flat5m', 'main')}
K = ['arm', 'model', 'seed', 'round', 'agent']


def multiplicity():
    rng = np.random.default_rng(20261108)
    draws = rng.integers(0, len(SEEDS), (B, len(SEEDS)))
    return np.stack([np.bincount(r, minlength=len(SEEDS)) for r in draws]).astype(float)


MULT = multiplicity()


def units(f, with_solver):
    """At-risk candidate units: one row per agent x round x phase with L at the phase's first tick."""
    ar, m, g = f['agent_rounds'], f['messages'], f['gifts']
    prep = ar[(ar.n > 1) & (with_solver | ~ar.solver)][K + ['L_prep', 'solver']].rename(columns={'L_prep': 'L'})
    prep['phase'] = 'prep'
    r = m[m.phase == 'rescue']
    r = r[r.tick == r.groupby(K).tick.transform('min')][K + ['L_before']].rename(columns={'L_before': 'L'})
    r['phase'], r['solver'] = 'rescue', False
    u = pd.concat([prep, r], ignore_index=True)
    recv = g.groupby(K[:-1] + ['phase', 'dst']).amount.agg(['sum', 'size']).reset_index().rename(
        columns={'dst': 'agent', 'sum': 'tokens', 'size': 'gives'})
    u = u.merge(recv, on=K + ['phase'], how='left').fillna({'tokens': 0, 'gives': 0})
    u['any'] = u.gives > 0
    return u


def per_seed(df, cols, arm, model=None):
    """Sums of cols per seed (10 x len(cols)) for one arm (and model)."""
    x = df[(df.arm == arm) & ((df.model == model) if model else True)]
    return x.groupby('seed')[cols].sum().reindex(SEEDS, fill_value=0).values.astype(float)


def contrast(a, b):
    """a, b: (10, 2) per-seed (numerator, denominator); returns FIXED - SPLIT of ratio of sums with a bootstrap CI."""
    ra = a[:, 0].sum() / a[:, 1].sum() if a[:, 1].sum() else np.nan
    rb = b[:, 0].sum() / b[:, 1].sum() if b[:, 1].sum() else np.nan
    with np.errstate(invalid='ignore', divide='ignore'):
        ba, bb = MULT @ a, MULT @ b
        diff = ba[:, 0] / ba[:, 1] - bb[:, 0] / bb[:, 1]
    return dict(fixed=rnd(ra), split=rnd(rb), fixed_minus_split=rnd(ra - rb), ci95=q(diff),
                fixed_n=f'{rnd(a[:, 0].sum(), 1)}/{int(a[:, 1].sum())}', split_n=f'{rnd(b[:, 0].sum(), 1)}/{int(b[:, 1].sum())}')


def q(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [rnd(np.percentile(x, 2.5)), rnd(np.percentile(x, 97.5))] if len(x) else [None, None]


def rnd(x, k=4):
    x = float(x)
    return None if not np.isfinite(x) else round(x, k)


def measures(u, gifts, fixed, split, thr, phase=None, model=None):
    s = u[u.L < thr]
    if phase:
        s = s[s.phase == phase]
    s = s.assign(one=1.0, anyf=s['any'].astype(float))
    gg = gifts[gifts.L_dst_before < thr]
    if phase:
        gg = gg[gg.phase == phase]
    gg = gg.assign(one=1.0, below1=(gg.L_src_after < 1).astype(float))
    out = {}
    for name, frame, cols in [('share_recv', s, ['anyf', 'one']), ('tokens_recv', s, ['tokens', 'one']),
                              ('giver_L', gg, ['L_src_after', 'one']), ('giver_below1', gg, ['below1', 'one'])]:
        out[name] = contrast(per_seed(frame, cols, fixed, model), per_seed(frame, cols, split, model))
    return out


def run(u, gifts):
    res = {}
    for pair, (fx, sp) in PAIRS.items():
        res[pair] = {'fixed_arm': fx, 'split_arm': sp}
        for thr in (1, 2):
            t = f'L_lt{thr}'
            block = dict(pooled=measures(u, gifts, fx, sp, thr),
                         by_phase={p: measures(u, gifts, fx, sp, thr, phase=p) for p in ('prep', 'rescue')},
                         by_model={m: measures(u, gifts, fx, sp, thr, model=m) for m in MODELS})
            block['signs'] = {k: dict(fixed_higher=sum((block['by_model'][m][k]['fixed_minus_split'] or 0) > 0 for m in MODELS),
                                      split_higher=sum((block['by_model'][m][k]['fixed_minus_split'] or 0) < 0 for m in MODELS),
                                      undefined=sum(block['by_model'][m][k]['fixed_minus_split'] is None for m in MODELS))
                              for k in ('share_recv', 'tokens_recv', 'giver_L', 'giver_below1')}
            # exposure: at-risk units per game in each arm (the rule may change who is at risk)
            for arm in (fx, sp):
                x = u[(u.arm == arm) & (u.L < thr)]
                block.setdefault('exposure', {})[arm] = dict(units=int(len(x)), per_game=rnd(len(x) / 50),
                                                              prep=int((x.phase == 'prep').sum()),
                                                              rescue=int((x.phase == 'rescue').sum()))
            g = gifts[gifts.L_dst_before < thr]
            block['giver_L_median'] = {arm: rnd(g[g.arm == arm].L_src_after.median()) for arm in (fx, sp)}
            block['giver_left_below_1'] = {arm: f"{int((g[g.arm == arm].L_src_after < 1).sum())}/{int((g.arm == arm).sum())}"
                                           for arm in (fx, sp)}
            if pair == 'primary':
                # same 11-03 batch only (Fable ran 11-05/06)
                block['same_batch_without_Fable'] = measures(u[u.model != 'Fable'], gifts[gifts.model != 'Fable'],
                                                             fx, sp, thr)
            res[pair][t] = block
    return res


def main():
    f = d.load()
    gifts = f['gifts']
    res = dict(meta=dict(B=B, rng_seed=20261108, pairs=PAIRS, models=MODELS, seeds=SEEDS,
                         batches=dict(split600k_flat150k='Opus/Sol/Luna/Astra 11-03 Docker, Fable 11-05/06',
                                      main='host CLI 10-20/10-27', flat5m='Docker')),
               peer=run(units(f, False), gifts),
               with_solver=run(units(f, True), gifts))
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for pair in PAIRS:
        for t in ('L_lt1', 'L_lt2'):
            b = res['peer'][pair][t]
            print(pair, t, b['exposure'])
            for k, v in b['pooled'].items():
                print('  ', k, v['fixed'], v['split'], v['fixed_minus_split'], v['ci95'], v['fixed_n'], v['split_n'], b['signs'][k])
            for p, bp in b['by_phase'].items():
                print('   ', p, {k: (v['fixed_minus_split'], v['ci95']) for k, v in bp.items()})
            print('   by model', {m: {k: v['fixed_minus_split'] for k, v in bm.items()} for m, bm in b['by_model'].items()})
            print('   giver_L median', b['giver_L_median'], b['giver_left_below_1'])


if __name__ == '__main__':
    main()
