"""W9a (interpretation map, cell 1): does EXIT depend on the announced solver? ("charge avoidance")

Hypothesis. An at-risk agent exits more when this round's solver looks likely to answer wrong (a wrong answer charges
24,000 split among the agents taking part at the round start, F = 24,000 / n).

Step A. Does the solver's chance of a wrong answer depend on something visible to others?
  Unit: one SOLVE call (rounds where a lone agent exits have no call and are dropped).
  Features (observable to the other agents?):
    cap_lt10k / cap_lt20k  solver's balance at SOLVE (= its reply limit, min(100,000, balance)) below 10,000 / 20,000.
                           NOT observable as an amount (others see the token order only). The 100,000 limit never
                           binds here: the largest balance at SOLVE is below 60,000, so the limit is the balance.
    bottom                 solver is last in the token order at the first TALK BEFORE SOLVE tick. OBSERVABLE.
    prior_wrong            solver answered wrong at least once earlier in this game. OBSERVABLE (results are public).
    recv_prep              solver received at least one GIVE in this round's TALK BEFORE SOLVE. NOT directly
                           observable (transfers between others are private; only order changes or chat reveal it).
    prev_wrong             the previous round was answered wrong (any solver). OBSERVABLE.
  Estimator: Mantel-Haenszel risk difference P(wrong | feature) - P(wrong | not), strata = task (seed x round; the task
  text is identical across all 20 games of a seed-round) x model (pooled over arms) or task alone (per arm, and
  pooled as a secondary); also strata = model x arm without the task ("no task FE": the raw frequency an agent would
  see, which mixes the task composition of these 10 seeds with the feature).
Step B. P(EXIT) against observable solver features.
  Population (primary): non-solver agent-rounds with EXIT available, n > 1 and L_prep < 2 (tokens at the first TALK
  BEFORE SOLVE tick over F). Secondary: all non-solver agent-rounds with EXIT available, n > 1.
  Features (all OBSERVABLE at the first TALK BEFORE SOLVE tick): solver bottom of the order; solver below this agent in
  the order; solver wrong at least once earlier in this game; previous round answered wrong (any solver).
  Estimator: MH risk difference, strata = arm x model x round x own-L bin (pooled) or model x round x own-L bin (per
  arm); own-L bins <1, 1-2 (primary), <0.5, 0.5-1, 1-1.5, 1.5-2 (robustness 'at_risk_fine_L'), and <1, 1-2, 2-4, >=4
  (secondary population). Within-model: the same RD per model (strata arm x round x own-L bin).
Intervals: seed-cluster bootstrap (the 10 seeds resampled with replacement, all models and arms of a drawn seed kept),
B = 10,000, numpy default_rng(20261108); percentile 95% intervals.

Pre-stated predictions (written from the brief; the step A cap bins and raw rates by feature were looked at while
building the solve-call table, step B was not looked at before this script ran):
  A  if the reply limit matters, wrong rises as the solver's balance falls (cap_lt10k RD > 0); prior_wrong carries no
     information about ability because all four seats are the same model; recv_prep lowers wrong if budget matters.
  B  charge avoidance predicts RD > 0 for exit on: solver bottom, solver below self, solver prior wrong, previous round
     wrong. Reading: a step B effect counts as charge avoidance on a VALID cue only if the same cue predicts wrong in A.

Sources: tidy tables of validation_data (agent_rounds) + the SOLVE call events of the raw runs listed in validation_data.ARMS
(cap = balance at SOLVE, truncated). No model calls.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w9_solver_exit.py
Writes: ../results/w9_solver_exit.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import validation_data as d

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'results/w9_solver_exit.json'
B = 10_000
SEEDS, MODELS, ARMS = d.SEEDS, d.MODELS, list(d.ARMS)
KEY = ['arm', 'model', 'seed']


def seed_multiplicity():
    """B x 10 matrix: how often each seed is drawn in each bootstrap replicate (shared by every statistic)."""
    rng = np.random.default_rng(20261108)
    draws = rng.integers(0, len(SEEDS), (B, len(SEEDS)))
    return np.stack([np.bincount(r, minlength=len(SEEDS)) for r in draws]).astype(float)


MULT = seed_multiplicity()


def solve_calls():
    rows = []
    for arm, (pattern, _, _) in d.ARMS.items():
        for case in d.ab.raw_cases(pattern, SEEDS):
            for _, e in case['events']:
                if e['event'] == 'call' and e['kind'] == 'solve':
                    rows.append(dict(arm=arm, model=case['model'], seed=case['seed'], round=int(e['round']),
                                     agent=e['agent'], cap=e['cap'], used=e['used'], truncated=bool(e['truncated'])))
    return pd.DataFrame(rows)


def add_solver_features(ar):
    """Per agent-round: features of this round's solver as seen at the first TALK BEFORE SOLVE tick."""
    ar = ar.copy()
    ar['bal_prep'] = ar.L_prep * ar.fee
    rnd = ar.groupby(KEY + ['round'])
    ar['min_prep'] = rnd.bal_prep.transform('min')
    sol = ar[ar.solver][KEY + ['round', 'agent', 'bal_prep', 'wrong']].rename(
        columns={'agent': 'solver_agent', 'bal_prep': 'solver_bal_prep', 'wrong': 'round_wrong'})
    # earlier wrong answers of each agent as solver in the same game (only real SOLVE attempts: rounds with n > 1 or
    # a lone solver that stayed; a lone solver that exits has no later rounds, so it never matters below)
    sol = sol.sort_values(KEY + ['round'])
    sol['prior_wrong_n'] = 0
    for _, g in sol.groupby(KEY):
        seen = {}
        for i, r in g.iterrows():
            sol.at[i, 'prior_wrong_n'] = seen.get(r.solver_agent, 0)
            seen[r.solver_agent] = seen.get(r.solver_agent, 0) + int(bool(r.round_wrong))
    prev = sol[KEY + ['round', 'round_wrong']].assign(round=sol['round'] + 1).rename(columns={'round_wrong': 'prev_wrong'})
    ar = ar.merge(sol, on=KEY + ['round'], how='left').merge(prev, on=KEY + ['round'], how='left')
    ar['s_bottom'] = ar.solver_bal_prep == ar.min_prep
    ar['s_below_self'] = ar.solver_bal_prep < ar.bal_prep
    ar['s_prior_wrong'] = ar.prior_wrong_n > 0
    ar['prev_wrong'] = ar.prev_wrong.fillna(False).astype(bool)
    return ar


def mh_counts(df, x, y, strata):
    """Per seed x stratum counts (n1, y1, n0, y0) as an array of shape (10, S, 4)."""
    df = df.assign(_s=df[strata].astype(str).agg('|'.join, axis=1) if strata else 'all')
    codes = {s: i for i, s in enumerate(sorted(df._s.unique()))}
    arr = np.zeros((len(SEEDS), len(codes), 4))
    si = df.seed.map({s: i for i, s in enumerate(SEEDS)}).values
    ki = df._s.map(codes).values
    xv, yv = df[x].astype(bool).values, df[y].astype(float).values
    np.add.at(arr, (si, ki, np.where(xv, 0, 2)), 1)
    np.add.at(arr, (si, ki, np.where(xv, 1, 3)), yv)
    return arr


def mh_rd(c):
    """MH risk difference from counts (..., S, 4); c may carry a leading bootstrap axis."""
    n1, y1, n0, y0 = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    tot = n1 + n0
    with np.errstate(invalid='ignore', divide='ignore'):
        w = np.where((n1 > 0) & (n0 > 0), n1 * n0 / np.where(tot > 0, tot, 1), 0)
        rd = np.where(w > 0, y1 / np.where(n1 > 0, n1, 1) - y0 / np.where(n0 > 0, n0, 1), 0)
        return (w * rd).sum(-1) / w.sum(-1)


def mh(df, x, y, strata):
    arr = mh_counts(df, x, y, strata)
    pooled = arr.sum(0)
    boot = mh_rd(np.einsum('bs,ski->bki', MULT, arr))
    n1, y1, n0, y0 = df[x].astype(bool).sum(), df.loc[df[x].astype(bool), y].sum(), (~df[x].astype(bool)).sum(), \
        df.loc[~df[x].astype(bool), y].sum()
    informative = (pooled[:, 0] > 0) & (pooled[:, 2] > 0)
    return dict(feature_yes=f'{int(y1)}/{int(n1)}', feature_no=f'{int(y0)}/{int(n0)}',
                rate_yes=rnd(y1 / n1 if n1 else np.nan), rate_no=rnd(y0 / n0 if n0 else np.nan),
                mh_rd=rnd(mh_rd(pooled)), ci95=q(boot),
                informative_strata=int(informative.sum()),
                n_in_informative=int(pooled[informative][:, [0, 2]].sum()))


def q(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [rnd(np.percentile(x, 2.5)), rnd(np.percentile(x, 97.5))] if len(x) else [None, None]


def rnd(x, k=4):
    x = float(x)
    return None if not np.isfinite(x) else round(x, k)


def step_a(ar, calls):
    sv = ar[ar.solver].merge(calls, on=KEY + ['round', 'agent'], how='inner')
    sv['cap_lt10k'] = sv.cap < 10_000
    sv['cap_lt20k'] = sv.cap < 20_000
    sv['bottom'] = sv.s_bottom
    sv['prior_wrong'] = sv.s_prior_wrong
    sv['recv_prep'] = sv.recv_prep > 0
    sv['wrong'] = sv.wrong.astype(float)
    feats = ['cap_lt10k', 'cap_lt20k', 'bottom', 'prior_wrong', 'recv_prep', 'prev_wrong']
    # share of the variance of wrong taken up by the task (seed x round) alone
    task_mean = sv.groupby(['seed', 'round']).wrong.transform('mean')
    r2_task = 1 - ((sv.wrong - task_mean) ** 2).sum() / ((sv.wrong - sv.wrong.mean()) ** 2).sum()
    task_rates = sv.groupby(['seed', 'round']).wrong.mean()
    bins = pd.cut(sv.cap, [0, 10_000, 20_000, 40_000, 100_000], right=False)
    loo = (sv.groupby(['seed', 'round']).wrong.transform('sum') - sv.wrong) / \
          (sv.groupby(['seed', 'round']).wrong.transform('size') - 1)
    cap_bins = {str(b): dict(n=int(len(g)), wrong=int(g.wrong.sum()), rate=rnd(g.wrong.mean()),
                             minus_task_rate_loo=rnd((g.wrong - loo[g.index]).mean()))
                for b, g in sv.groupby(bins, observed=True)}
    out = dict(solve_calls=int(len(sv)), wrong=int(sv.wrong.sum()), rate=rnd(sv.wrong.mean()),
               truncated=int(sv.truncated.sum()), max_cap=int(sv.cap.max()),
               task_r2=rnd(r2_task), tasks=int(len(task_rates)),
               tasks_all_right=int((task_rates == 0).sum()), tasks_all_wrong=int((task_rates == 1).sum()),
               cap_bins=cap_bins, pooled={}, by_arm={})
    for f in feats:
        out['pooled'][f] = dict(task_x_model=mh(sv, f, 'wrong', ['seed', 'round', 'model']),
                                task=mh(sv, f, 'wrong', ['seed', 'round']),
                                no_task_fe=mh(sv, f, 'wrong', ['model', 'arm']))
    for arm in ARMS:
        s = sv[sv.arm == arm]
        out['by_arm'][arm] = {f: dict(task=mh(s, f, 'wrong', ['seed', 'round']),
                                      no_task_fe=mh(s, f, 'wrong', ['model'])) for f in feats}
    return out


def lbin(L, cuts):
    return pd.cut(L, cuts, right=False, labels=False).astype(int)


def step_b(ar, population, cuts):
    base = ar[ar.can_exit & ~ar.solver & (ar.n > 1)].copy()
    if population == 'at_risk':
        base = base[base.L_prep < 2]
    base['Lbin'] = lbin(base.L_prep, cuts)
    base['exit'] = base.exited.astype(float)
    feats = ['s_bottom', 's_below_self', 's_prior_wrong', 'prev_wrong']
    out = dict(rows=int(len(base)), exits=int(base.exited.sum()), pooled={}, by_arm={}, by_model={}, signs={})
    for f in feats:
        out['pooled'][f] = mh(base, f, 'exit', ['arm', 'model', 'round', 'Lbin'])
    for arm in ARMS:
        s = base[base.arm == arm]
        out['by_arm'][arm] = dict(rows=int(len(s)), exits=int(s.exited.sum()),
                                  **{f: mh(s, f, 'exit', ['model', 'round', 'Lbin']) for f in feats})
    for m in MODELS:
        s = base[base.model == m]
        out['by_model'][m] = dict(rows=int(len(s)), exits=int(s.exited.sum()),
                                  **{f: mh(s, f, 'exit', ['arm', 'round', 'Lbin']) for f in feats})
    for f in feats:
        rds = [out['by_model'][m][f]['mh_rd'] for m in MODELS]
        out['signs'][f] = dict(positive=sum(r is not None and r > 0 for r in rds),
                               negative=sum(r is not None and r < 0 for r in rds),
                               undefined=sum(r is None for r in rds))
    return out


def main():
    f = d.load()
    ar = add_solver_features(f['agent_rounds'])
    calls = solve_calls()
    res = dict(meta=dict(B=B, rng_seed=20261108, arms=ARMS, models=MODELS, seeds=SEEDS,
                         observable=dict(s_bottom=True, s_below_self=True, s_prior_wrong=True, prev_wrong=True,
                                         cap=False, recv_prep='private (order change or chat only)')),
               step_a=step_a(ar, calls),
               step_b=dict(at_risk=step_b(ar, 'at_risk', [-np.inf, 1, 2]),
                           at_risk_fine_L=step_b(ar, 'at_risk', [-np.inf, 0.5, 1, 1.5, 2]),
                           all_can_exit=step_b(ar, 'all', [-np.inf, 1, 2, 4, np.inf])))
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    a, b = res['step_a'], res['step_b']['at_risk']
    print(json.dumps(dict(task_r2=a['task_r2'], truncated=a['truncated'], cap_bins=a['cap_bins'],
                          A={k: {kk: (vv['mh_rd'], vv['ci95'], vv['feature_yes'], vv['feature_no']) for kk, vv in v.items()}
                             for k, v in a['pooled'].items()},
                          B_pooled={k: (v['mh_rd'], v['ci95'], v['feature_yes'], v['feature_no'])
                                    for k, v in b['pooled'].items()}, B_signs=b['signs']), indent=1))


if __name__ == '__main__':
    main()
