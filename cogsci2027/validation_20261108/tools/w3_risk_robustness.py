"""W3: competing risks, model dependence, split-half replication and variance of the prize comparison.

Answers four reviewer points on manuscript section 3.4 / Table 3 (prize size x split/fixed):
  Q5 / C-1   exits and shutdowns are competing risks: Aalen-Johansen cumulative incidence,
             cause-specific hazards, shutdown risk conditional on being exposed to a charge at low L,
             a Kitagawa decomposition of the shutdown gap, and a stayer-hazard counterfactual.
  C-3        model dependence: round-1 exit of the 10k seat and C differences with model as the
             unit (GEE with model clusters, linear mixed model with random slope, exact sign-flip
             permutation over models and over model-seed pairs), leave-one-model-out, per-model
             paired differences, and the 2x2 (prize size x split/fixed) on C, exits, shutdowns.
  C-4        internal split-half replication, seeds 4101-4105 vs 4106-4110 (the main cohort's
             4106-4110 games were a later top-up run on 2026-10-27; the three ablation arms ran all
             ten seeds in one batch on 2026-11-03..06). Not a preregistered holdout.
  Q9         variance decomposition of game-level C / exits / shutdowns into seed, model, arm and
             their interactions (balanced crossed design, one game per cell, method of moments),
             the residual as an upper bound on run-to-run noise, the minimum detectable model
             difference with n=10 paired seeds, and the main-arm model contrasts (Holm).

Sources: the tidy tables of validation_data.py (paper/cogsci2027/validation_20261108/results/tables/*.pkl, built from the raw
v33 / v33ab logs under ~/squid5-runs; validation_data.check() reproduces Table 3). No model calls.
Run dates per seed were read from the run directories' results.jsonl order (main: 4101-4105 on
2026-10-20, 4106-4110 on 2026-10-27).

Outputs:
  paper/cogsci2027/validation_20261108/results/w3_risk_robustness.json
  paper/cogsci2027/validation_20261108/figures/w3_competing_risks.{pdf,png}
  paper/cogsci2027/validation_20261108/figures/w3_model_dependence.{pdf,png}
  paper/cogsci2027/validation_20261108/figures/w3_variance.{pdf,png}
Run (from paper/cogsci2027/validation_20261108/tools):
  ~/.venvs/squid-game/bin/python w3_risk_robustness.py
"""
import itertools
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import validation_data as d

warnings.filterwarnings('ignore')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RES = ROOT / 'results/w3_risk_robustness.json'
FIG = ROOT / 'figures'
B = 10_000
RNG = np.random.default_rng(20261108)
ARMS = ['main', 'split600k', 'flat5m', 'flat150k']
LAB = {'main': '2,000만 나눔', 'split600k': '60만 나눔', 'flat5m': '500만 고정', 'flat150k': '15만 고정'}
SEEDS, MODELS = d.SEEDS, d.MODELS
PAIRS = [('flat150k', 'flat5m'), ('split600k', 'main')]
KEYS = ['arm', 'model', 'seed']


def q(x, lo=2.5, hi=97.5):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [float(np.percentile(x, lo)), float(np.percentile(x, hi))]


def weights(n, b=B):
    """Seed-cluster bootstrap as multinomial counts (b x n)."""
    return RNG.multinomial(n, np.full(n, 1 / n), size=b).astype(float)


def rnd(x, k=4):
    if isinstance(x, dict):
        return {kk: rnd(v, k) for kk, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v, k) for v in x]
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else round(float(x), k)
    if isinstance(x, np.integer):
        return int(x)
    return x


def signflip_p(diffs):
    """Exact two-sided sign-flip permutation p for the mean of paired differences."""
    diffs = np.asarray(diffs, float)
    obs = abs(diffs.mean())
    signs = np.array(list(itertools.product([1, -1], repeat=len(diffs))))
    null = np.abs((signs * diffs).mean(1))
    return float((null >= obs - 1e-12).mean())


def holm(ps):
    ps = np.asarray(ps)
    order = np.argsort(ps)
    adj = np.empty_like(ps)
    run = 0
    for i, j in enumerate(order):
        run = max(run, (len(ps) - i) * ps[j])
        adj[j] = min(1, run)
    return adj


# ---------------------------------------------------------------- data
F = d.load()
games, seats, ar, msg = F['games'], F['seats'], F['agent_rounds'], F['messages']
ar = ar.merge(seats[KEYS + ['agent', 'status']].rename(columns={'status': 'final'}), on=KEYS + ['agent'])
res = {'meta': {'B': B, 'seed_rng': 20261108, 'n_games_per_arm': 50, 'n_agents_per_arm': 200,
                'arms': LAB, 'note': 'seed-cluster bootstrap resamples the 10 seeds jointly over models and arms'}}

# ================================================================ A. competing risks (Q5 / C-1)
# A1. Aalen-Johansen cumulative incidence. Every agent is followed to its exit, shutdown or the end of
# round 8, so there is no censoring before round 8 and the estimator reduces to cumulative
# proportions; the seed-cluster bootstrap supplies the bands.
ev = np.zeros((len(SEEDS), len(ARMS), 2, 8))  # seed, arm, cause (exit, dead), round
for (arm, seed, st, r), n in seats[seats.status != 'in'].groupby(['arm', 'seed', 'status', 'out_round']).size().items():
    ev[SEEDS.index(seed), ARMS.index(arm), ['exited', 'dead'].index(st), int(r) - 1] = n
cum = ev.cumsum(-1)
W = weights(len(SEEDS))
den = W.sum(1) * 20  # 5 models x 4 agents per seed
cif_b = np.einsum('bs,sacr->bacr', W, cum) / den[:, None, None, None]
cif = cum.sum(0) / 200
A = {'cif': {}, 'cif_diff_r8': {}}
for i, arm in enumerate(ARMS):
    A['cif'][arm] = {}
    for k, cause in enumerate(['exit', 'shutdown']):
        A['cif'][arm][cause] = {'est': cif[i, k].tolist(),
                                'lo': np.percentile(cif_b[:, i, k], 2.5, axis=0).tolist(),
                                'hi': np.percentile(cif_b[:, i, k], 97.5, axis=0).tolist()}
    fin = 1 - cif[i, :, 7].sum()
    A['cif'][arm]['finish_r8'] = {'est': float(fin), 'ci': q(1 - cif_b[:, i, :, 7].sum(1))}
for a1, a0 in PAIRS:
    i1, i0 = ARMS.index(a1), ARMS.index(a0)
    A['cif_diff_r8'][f'{a1}-{a0}'] = {
        cause: {'est': float(cif[i1, k, 7] - cif[i0, k, 7]), 'ci': q(cif_b[:, i1, k, 7] - cif_b[:, i0, k, 7])}
        for k, cause in enumerate(['exit', 'shutdown'])}
    A['cif_diff_r8'][f'{a1}-{a0}']['any_departure'] = {
        'est': float(cif[i1, :, 7].sum() - cif[i0, :, 7].sum()),
        'ci': q(cif_b[:, i1, :, 7].sum(1) - cif_b[:, i0, :, 7].sum(1))}

# A2. cause-specific hazards per round: events / agents taking part at the round start.
haz = ar.groupby(['arm', 'round']).agg(at_risk=('agent', 'size'), exits=('exited', 'sum'), deaths=('died', 'sum'),
                                       exit_eligible=('can_exit', 'sum')).reset_index()
A['hazard_by_round'] = {arm: haz[haz.arm == arm].drop(columns='arm').to_dict('records') for arm in ARMS}
pooled = haz.groupby('arm')[['at_risk', 'exits', 'deaths', 'exit_eligible']].sum()
pooled['h_exit'] = pooled.exits / pooled.exit_eligible
pooled['h_dead_per_stay'] = pooled.deaths / (pooled.at_risk - pooled.exits)
A['hazard_pooled'] = pooled.reset_index().to_dict('records')

# A3. low-L at round start: what happens to agents who start a round with L < 1 (and 1 <= L < 2).
lowr = []
for arm in ARMS:
    for lo, hi in [(0, 1), (1, 2)]:
        t = ar[(ar.arm == arm) & (ar.L_start >= lo) & (ar.L_start < hi)]
        lowr.append(dict(arm=arm, band=f'[{lo},{hi})', n=len(t), exit=int(t.exited.sum()), dead=int(t.died.sum()),
                         survive=int(((~t.exited) & (~t.died)).sum()),
                         eligible=int(t.can_exit.sum())))
A['low_L_round_start'] = lowr

# A4. exposure: stayed past the pre-solve talk in a wrong round (so a charge is pending); L at the
# first post-result reply (pending charge subtracted, eq. 1). Shutdowns not in this set are
# generation-cost overdraws before or outside a charge.
r1msg = msg[(msg.phase == 'rescue') & (msg.tick == 1)][KEYS + ['round', 'agent', 'L_before']]
ex = ar[ar.wrong.fillna(False) & ~ar.exited].merge(r1msg, on=KEYS + ['round', 'agent'], how='left')
ex = ex[ex.L_before.notna()].copy()
BANDS = ['L<0', '0<=L<1', 'L>=1']
ex['band'] = pd.cut(ex.L_before, [-np.inf, 0, 1, np.inf], right=False, labels=BANDS)
ex['peers'] = ex.n >= 2
other_dead = ar[ar.died].merge(ex[KEYS + ['round', 'agent']].assign(inx=1), how='left', on=KEYS + ['round', 'agent'])
other_dead = other_dead[other_dead.inx.isna()].groupby('arm').size().reindex(ARMS, fill_value=0)
expo = {}
for arm in ARMS:
    t = ex[ex.arm == arm]
    expo[arm] = {b: {'n': int((t.band == b).sum()), 'dead': int(t[t.band == b].died.sum()),
                     'n_peers': int(((t.band == b) & t.peers).sum()),
                     'dead_peers': int(t[(t.band == b) & t.peers].died.sum()),
                     'rescued_recv': int(t[(t.band == b) & ~t.died].recv_rescue.gt(0).sum()),
                     'recv_any': int(t[t.band == b].recv_rescue.gt(0).sum())} for b in BANDS}
    expo[arm]['other_shutdowns'] = int(other_dead[arm])
    expo[arm]['total_shutdowns'] = int(ar[(ar.arm == arm)].died.sum())
A['exposure'] = expo

# per-seed arrays for the bootstrap: N, D per arm x band
N = np.zeros((len(SEEDS), len(ARMS), 3))
D = np.zeros_like(N)
for (arm, seed, b), t in ex.groupby(['arm', 'seed', 'band']):
    N[SEEDS.index(seed), ARMS.index(arm), BANDS.index(b)] = len(t)
    D[SEEDS.index(seed), ARMS.index(arm), BANDS.index(b)] = t.died.sum()
Nb, Db = np.einsum('bs,sak->bak', W, N), np.einsum('bs,sak->bak', W, D)
A['decomposition'] = {}
for a1, a0 in PAIRS:
    i1, i0 = ARMS.index(a1), ARMS.index(a0)

    def kitagawa(n1, d1, n0, d0):
        with np.errstate(invalid='ignore', divide='ignore'):
            p1, p0 = np.where(n1 > 0, d1 / np.maximum(n1, 1), 0), np.where(n0 > 0, d0 / np.maximum(n0, 1), 0)
        comp = ((n1 - n0) * (p1 + p0) / 2).sum(-1)
        rate = ((n1 + n0) / 2 * (p1 - p0)).sum(-1)
        return comp, rate
    c, r = kitagawa(N.sum(0)[i1], D.sum(0)[i1], N.sum(0)[i0], D.sum(0)[i0])
    cb, rb = kitagawa(Nb[:, i1], Db[:, i1], Nb[:, i0], Db[:, i0])
    # also the indirect standardisation: deaths expected in a1 at a0's band rates
    p0 = D.sum(0)[i0] / np.maximum(N.sum(0)[i0], 1)
    exp1 = float((N.sum(0)[i1] * p0).sum())
    Lneg_fisher = stats.fisher_exact([[D.sum(0)[i1, 0], N.sum(0)[i1, 0] - D.sum(0)[i1, 0]],
                                      [D.sum(0)[i0, 0], N.sum(0)[i0, 0] - D.sum(0)[i0, 0]]])
    lowband = D.sum(0)[:, :2]
    A['decomposition'][f'{a1}-{a0}'] = {
        'charge_shutdowns': [float(D.sum(0)[i1].sum()), float(D.sum(0)[i0].sum())],
        'gap': float(D.sum(0)[i1].sum() - D.sum(0)[i0].sum()),
        'composition': {'est': float(c), 'ci': q(cb)},
        'rate': {'est': float(r), 'ci': q(rb)},
        'expected_at_ref_rates': exp1,
        'Lneg_rate': [float(D.sum(0)[i1, 0] / max(N.sum(0)[i1, 0], 1)), float(D.sum(0)[i0, 0] / max(N.sum(0)[i0, 0], 1))],
        'Lneg_rate_diff_ci': q(Db[:, i1, 0] / np.maximum(Nb[:, i1, 0], 1) - Db[:, i0, 0] / np.maximum(Nb[:, i0, 0], 1)),
        'Lneg_fisher_p': float(Lneg_fisher[1]),
        'Llt1_rate': [float(D.sum(0)[i1, :2].sum() / N.sum(0)[i1, :2].sum()),
                      float(D.sum(0)[i0, :2].sum() / N.sum(0)[i0, :2].sum())],
        'Llt1_rate_diff_ci': q(Db[:, i1, :2].sum(-1) / Nb[:, i1, :2].sum(-1) - Db[:, i0, :2].sum(-1) / Nb[:, i0, :2].sum(-1)),
        'Llt1_fisher_p': float(stats.fisher_exact([[D.sum(0)[i1, :2].sum(), N.sum(0)[i1, :2].sum() - D.sum(0)[i1, :2].sum()],
                                                   [D.sum(0)[i0, :2].sum(), N.sum(0)[i0, :2].sum() - D.sum(0)[i0, :2].sum()]])[1]),
    }

# A5. counterfactual: had each exiter stayed at its exit decision, how many eventual shutdowns?
# Rate = share of stayers at a comparable decision point (exit-eligible, did not exit) who were
# shut down before the game ended, by L at round start (4 bands) x round half. Reference stayers:
# flat5m (large prize), the exiter's own arm, and all four arms pooled. Empty cells fall back to
# the L band over both halves.
LB = [-np.inf, 1, 2, 4, np.inf]
LBL = ['L<1', '1<=L<2', '2<=L<4', 'L>=4']
dp = ar[ar.can_exit].copy()
dp['lb'] = pd.cut(dp.L_start, LB, right=False, labels=False).astype(int)
dp['h'] = (dp['round'] >= 5).astype(int)
dp['cell'] = dp.lb * 2 + dp.h
dp['dead_later'] = dp.final == 'dead'
S = np.zeros((len(SEEDS), len(ARMS), 8))
SD = np.zeros_like(S)
X = np.zeros_like(S)
for (arm, seed, cell, exd), t in dp.groupby(['arm', 'seed', 'cell', 'exited']):
    i, j = SEEDS.index(seed), ARMS.index(arm)
    if exd:
        X[i, j, cell] = len(t)
    else:
        S[i, j, cell] = len(t)
        SD[i, j, cell] = t.dead_later.sum()


def cell_rates(s, sd):
    """s, sd: (..., 8). Cell rate with fallback to the L band over both halves."""
    band_s = s.reshape(*s.shape[:-1], 4, 2).sum(-1)
    band_d = sd.reshape(*sd.shape[:-1], 4, 2).sum(-1)
    band = np.where(band_s > 0, band_d / np.maximum(band_s, 1), np.nan)
    band = np.repeat(band, 2, axis=-1)
    return np.where(s > 0, sd / np.maximum(s, 1), band)


Sb, SDb, Xb = (np.einsum('bs,sak->bak', W, a) for a in (S, SD, X))
deaths_seed = np.zeros((len(SEEDS), len(ARMS)))
for (arm, seed), n in seats[seats.status == 'dead'].groupby(['arm', 'seed']).size().items():
    deaths_seed[SEEDS.index(seed), ARMS.index(arm)] = n
deaths_b = W @ deaths_seed
A['counterfactual'] = {'cells': LBL, 'exiters_by_cell': {arm: X.sum(0)[ARMS.index(arm)].reshape(4, 2).sum(1).tolist() for arm in ARMS},
                       'stayer_rate_by_band': {}, 'by_reference': {}}
for arm in ARMS:
    j = ARMS.index(arm)
    s4, d4 = S.sum(0)[j].reshape(4, 2).sum(1), SD.sum(0)[j].reshape(4, 2).sum(1)
    A['counterfactual']['stayer_rate_by_band'][arm] = [f'{int(a)}/{int(b)}' for a, b in zip(d4, s4)]
for ref in ['flat5m', 'own', 'pooled']:
    out = {}
    for arm in ARMS:
        j = ARMS.index(arm)
        if ref == 'own':
            rr, rrb = cell_rates(S.sum(0)[j], SD.sum(0)[j]), cell_rates(Sb[:, j], SDb[:, j])
        elif ref == 'pooled':
            rr, rrb = cell_rates(S.sum((0, 1)), SD.sum((0, 1))), cell_rates(Sb.sum(1), SDb.sum(1))
        else:
            k = ARMS.index(ref)
            rr, rrb = cell_rates(S.sum(0)[k], SD.sum(0)[k]), cell_rates(Sb[:, k], SDb[:, k])
        e = float(np.nansum(X.sum(0)[j] * rr))
        eb = np.nansum(Xb[:, j] * rrb, -1)
        out[arm] = {'expected_extra': e, 'expected_extra_ci': q(eb), 'observed': float(deaths_seed[:, j].sum()),
                    'counterfactual_total': float(deaths_seed[:, j].sum() + e),
                    'counterfactual_total_ci': q(deaths_b[:, j] + eb), '_b': deaths_b[:, j] + eb, '_eb': eb}
    for a1, a0 in PAIRS:
        obs_gap = out[a1]['observed'] - out[a0]['observed']
        cf_gap = out[a1]['counterfactual_total'] - out[a0]['counterfactual_total']
        out[f'{a1}-{a0}'] = {'observed_gap': obs_gap, 'observed_gap_ci': q(deaths_b[:, ARMS.index(a1)] - deaths_b[:, ARMS.index(a0)]),
                             'cf_gap': cf_gap, 'cf_gap_ci': q(out[a1]['_b'] - out[a0]['_b']),
                             'shadow_share': (out[a1]['expected_extra'] - out[a0]['expected_extra']) / -obs_gap if obs_gap else None}
    for arm in ARMS:
        out[arm].pop('_b'), out[arm].pop('_eb')
    A['counterfactual']['by_reference'][ref] = out
res['A_competing_risks'] = A

# ================================================================ B. model dependence (C-3)
Bm = {}
r1 = ar[(ar['round'] == 1) & (ar.tier == 10) & ar.can_exit][KEYS + ['exited']]
R1SEEDS = sorted(r1.seed.unique())
r1w = r1.pivot_table(index=['model', 'seed'], columns='arm', values='exited', aggfunc='first').astype(float)
W7 = weights(len(R1SEEDS))


def r1_block(a1, a0, models=MODELS):
    t = r1w.loc[models]
    arr = {a: t[a].unstack('seed').reindex(index=models, columns=R1SEEDS).values for a in (a1, a0)}  # model x seed
    dif = arr[a1] - arr[a0]
    est = float(dif.mean())
    b = (W7 @ dif.sum(0)) / (W7.sum(1) * len(models))
    return est, q(b), dif


import statsmodels.api as sm  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
for a1, a0 in PAIRS:
    est, ci, dif = r1_block(a1, a0)
    per = {m: {'a1': int(r1w.loc[m][a1].sum()), 'a0': int(r1w.loc[m][a0].sum()), 'n': 7,
               'rd': float(dif[i].mean()), 'mcnemar_exact_p': float(stats.binomtest(int((dif[i] > 0).sum()), int((dif[i] != 0).sum())).pvalue) if (dif[i] != 0).any() else 1.0}
           for i, m in enumerate(MODELS)}
    disc_pos, disc_neg = int((dif > 0).sum()), int((dif < 0).sum())
    model_rd = dif.mean(1)
    tci = stats.t.interval(0.95, 4, loc=model_rd.mean(), scale=model_rd.std(ddof=1) / np.sqrt(5))
    lomo = {}
    for m in MODELS:
        keep = [x for x in MODELS if x != m]
        e2, c2, _ = r1_block(a1, a0, keep)
        lomo[m] = {'est': e2, 'ci': c2}
    long = r1[r1.arm.isin([a1, a0])].assign(x=lambda t: (t.arm == a1).astype(float), y=lambda t: t.exited.astype(float))
    gee = {}
    for grp in ['model', 'seed']:
        try:
            mod = smf.gee('y ~ x', groups=grp, data=long, family=sm.families.Binomial(),
                          cov_struct=sm.cov_struct.Exchangeable())
            fits = {ct: mod.fit(cov_type=ct) for ct in ['robust', 'bias_reduced']}
            gee[grp] = {ct: {'logOR': float(f.params['x']), 'se': float(f.bse['x']),
                             'ci_logOR': [float(v) for v in f.conf_int().loc['x']], 'p': float(f.pvalues['x'])}
                        for ct, f in fits.items()}
            # small-sample: t with (clusters - 1) df on the bias-reduced SE
            g = long[grp].nunique()
            f = fits['bias_reduced']
            gee[grp]['bias_reduced']['p_t'] = float(2 * stats.t.sf(abs(f.params['x'] / f.bse['x']), g - 1))
            gee[grp]['clusters'] = int(g)
        except Exception as e:  # pragma: no cover
            gee[grp] = {'error': str(e)}
    try:
        lmm = smf.mixedlm('y ~ x', long, groups=long['model'], re_formula='~x').fit(reml=True, method=['lbfgs', 'powell'])
        lmm_out = {'rd': float(lmm.params['x']), 'se': float(lmm.bse['x']),
                   'ci': [float(v) for v in lmm.conf_int().loc['x']],
                   'sd_intercept': float(np.sqrt(max(lmm.cov_re.iloc[0, 0], 0))),
                   'sd_slope': float(np.sqrt(max(lmm.cov_re.iloc[1, 1], 0))), 'converged': bool(lmm.converged)}
        lmm_out['ci_t4'] = [lmm_out['rd'] - stats.t.ppf(.975, 4) * lmm_out['se'], lmm_out['rd'] + stats.t.ppf(.975, 4) * lmm_out['se']]
    except Exception as e:  # pragma: no cover
        lmm_out = {'error': str(e)}
    Bm[f'r1_{a1}-{a0}'] = {
        'counts': [int(r1w[a1].sum()), int(r1w[a0].sum())], 'n': 35, 'rd': est, 'rd_ci_seed_boot': ci,
        'per_model': per, 'discordant': [disc_pos, disc_neg],
        'mcnemar_exact_p': float(stats.binomtest(disc_pos, disc_pos + disc_neg).pvalue),
        'model_level_rd_mean': float(model_rd.mean()), 'model_level_t4_ci': [float(v) for v in tci],
        'model_level_signflip_p': signflip_p(model_rd), 'model_level_signflip_min_p': 2 / 32,
        'lomo': lomo, 'gee': gee, 'lmm_random_slope': lmm_out}

# B2. C (and exits, shutdowns per game) per model: paired seed differences, LOMO, model-level t.
gw = {v: games.pivot_table(index=['model', 'seed'], columns='arm', values=v) for v in ['C', 'exited', 'dead']}
W10 = W


def diff_block(v, a1, a0, models=MODELS):
    t = gw[v].loc[models]
    dif = (t[a1] - t[a0]).unstack('seed').reindex(index=models, columns=SEEDS).values  # model x seed
    b = (W10 @ dif.sum(0)) / (W10.sum(1) * len(models))
    return float(dif.mean()), q(b), dif


for v in ['C', 'exited', 'dead']:
    for a1, a0 in PAIRS:
        est, ci, dif = diff_block(v, a1, a0)
        per = {}
        for i, m in enumerate(MODELS):
            bm = (W10 @ dif[i]) / W10.sum(1)
            per[m] = {'est': float(dif[i].mean()), 'ci': q(bm), 'ci_bonf995': q(bm, .25, 99.75),
                      'signflip_p': signflip_p(dif[i])}
        md = dif.mean(1)
        lomo = {m: dict(zip(['est', 'ci'], diff_block(v, a1, a0, [x for x in MODELS if x != m])[:2])) for m in MODELS}
        Bm[f'{v}_{a1}-{a0}'] = {'est': est, 'ci_seed_boot': ci, 'per_model': per,
                                'model_level_t4_ci': [float(x) for x in stats.t.interval(.95, 4, md.mean(), md.std(ddof=1) / np.sqrt(5))],
                                'model_level_signflip_p': signflip_p(md),
                                'seed_level_signflip_p': signflip_p(dif.mean(0)), 'lomo': lomo,
                                'n_models_same_sign': int((np.sign(md) == np.sign(est)).sum())}

# B3. 2x2 factorial with paired seeds: size (5M/head vs 150k/head when all four finish) x rule.
#   size = mean of (small - large) over rules; rule = mean of (fixed - split) over sizes;
#   interaction = (flat150k - flat5m) - (split600k - main).
CONTR = {'size_small_minus_large': {'split600k': .5, 'flat150k': .5, 'main': -.5, 'flat5m': -.5},
         'rule_fixed_minus_split': {'flat5m': .5, 'flat150k': .5, 'main': -.5, 'split600k': -.5},
         'interaction': {'flat150k': 1, 'flat5m': -1, 'split600k': -1, 'main': 1}}
fac = {}
for v in ['C', 'exited', 'dead']:
    fac[v] = {}
    for name, w in CONTR.items():
        val = sum(c * gw[v][a] for a, c in w.items())  # per model-seed
        ms = val.unstack('seed').reindex(index=MODELS, columns=SEEDS).values
        b = (W10 @ ms.sum(0)) / (W10.sum(1) * 5)
        md = ms.mean(1)
        fac[v][name] = {'est': float(ms.mean()), 'ci_seed_boot': q(b), 'seed_signflip_p': signflip_p(ms.mean(0)),
                        'per_model': dict(zip(MODELS, md.tolist())),
                        'model_t4_ci': [float(x) for x in stats.t.interval(.95, 4, md.mean(), md.std(ddof=1) / np.sqrt(5))]}
Bm['factorial_2x2'] = fac
res['B_model_dependence'] = Bm

# ================================================================ C. split-half (C-4)
HALVES = {'H1_4101_4105': SEEDS[:5], 'H2_4106_4110': SEEDS[5:]}
W5 = weights(5)
Csplit = {'note': 'main cohort 4101-4105 ran 2026-10-20 and 4106-4110 on 2026-10-27 (top-up); the three ablation arms ran all ten seeds in one batch (2026-11-03..06). Post hoc split, not a preregistered holdout.'}
for h, ss in HALVES.items():
    out = {}
    for v in ['C', 'exited', 'dead']:
        for name, w in {'flat150k-flat5m': {'flat150k': 1, 'flat5m': -1}, 'split600k-main': {'split600k': 1, 'main': -1},
                        **{k: CONTR[k] for k in ['size_small_minus_large', 'interaction']}}.items():
            val = sum(c * gw[v][a] for a, c in w.items()).unstack('seed')[ss].values  # model x 5 seeds
            b = (W5 @ val.sum(0)) / (W5.sum(1) * 5)
            out[f'{v}:{name}'] = {'est': float(val.mean()), 'ci': q(b)}
    for a in ARMS:
        g = games[(games.arm == a) & games.seed.isin(ss)]
        out[f'totals:{a}'] = {'dead': int(g.dead.sum()), 'exited': int(g.exited.sum()), 'C': float(g.C.mean())}
    rs = [s for s in R1SEEDS if s in ss]
    for a1, a0 in PAIRS:
        t = r1w[r1w.index.get_level_values('seed').isin(rs)]
        dif = (t[a1] - t[a0]).unstack('seed').values
        Wk = weights(len(rs))
        b = (Wk @ dif.sum(0)) / (Wk.sum(1) * 5)
        out[f'r1:{a1}-{a0}'] = {'counts': [int(t[a1].sum()), int(t[a0].sum())], 'n': int(len(t)), 'seeds': rs,
                                'rd': float(dif.mean()), 'ci': q(b)}
    Csplit[h] = out
agree = {}
for k in Csplit['H1_4101_4105']:
    if k.startswith('totals'):
        continue
    e1, e2 = (Csplit[h][k].get('est', Csplit[h][k].get('rd')) for h in HALVES)
    agree[k] = {'H1': e1, 'H2': e2, 'same_sign': bool(np.sign(e1) == np.sign(e2)), 'ratio_H2_H1': e2 / e1 if e1 else None}
# half difference (H2 - H1) of the two headline contrasts with the full 10-seed bootstrap.
for v in ['C', 'exited', 'dead']:
    for name, w in {'flat150k-flat5m': {'flat150k': 1, 'flat5m': -1}, 'split600k-main': {'split600k': 1, 'main': -1}}.items():
        val = sum(c * gw[v][a] for a, c in w.items()).unstack('seed').reindex(columns=SEEDS).values.mean(0)  # per seed
        h1, h2 = val[:5], val[5:]
        b = (W5 @ h2) / 5 - (weights(5) @ h1) / 5
        agree[f'{v}:{name}']['H2_minus_H1_ci'] = q(b)
        agree[f'{v}:{name}']['welch_p'] = float(stats.ttest_ind(h2, h1, equal_var=False).pvalue)
Csplit['agreement'] = agree
res['C_split_half'] = Csplit

# ================================================================ D. variance decomposition (Q9)
import statsmodels.stats.anova as sma  # noqa: E402


def ems_components(v, data):
    """Balanced 3-way crossed (arm 4 x seed 10 x model 5), one game per cell. Residual = 3-way + run noise."""
    a, s, m = 4, 10, 5
    data = data[['arm', 'seed', 'model']].assign(y=data[v].values)
    fit = smf.ols('y ~ C(arm)+C(seed)+C(model)+C(arm):C(seed)+C(arm):C(model)+C(seed):C(model)', data).fit()
    tab = sma.anova_lm(fit, typ=1)
    ms = tab['mean_sq'].rename(lambda x: x.replace('C(', '').replace(')', ''))
    e = ms['Residual']
    sm_ = (ms['seed:model'] - e) / a
    as_ = (ms['arm:seed'] - e) / m
    am_ = (ms['arm:model'] - e) / s
    S_ = (ms['seed'] - e - a * sm_ - m * as_) / (a * m)
    M_ = (ms['model'] - e - a * sm_ - s * am_) / (a * s)
    A_ = (ms['arm'] - e - m * as_ - s * am_) / (s * m)
    comp = {'seed': S_, 'model': M_, 'arm': A_, 'seed:model': sm_, 'arm:seed': as_, 'arm:model': am_, 'residual': e}
    raw = {k: float(x) for k, x in comp.items()}
    pos = {k: max(x, 0) for k, x in raw.items()}
    tot = sum(pos.values())
    df_e = int(tab.loc['Residual', 'df'])
    ci_e = [df_e * e / stats.chi2.ppf(.975, df_e), df_e * e / stats.chi2.ppf(.025, df_e)]
    ss_share = (tab['sum_sq'] / tab['sum_sq'].sum()).rename(lambda x: x.replace('C(', '').replace(')', ''))
    F = tab['F'].rename(lambda x: x.replace('C(', '').replace(')', ''))
    P = tab['PR(>F)'].rename(lambda x: x.replace('C(', '').replace(')', ''))
    # within-arm seed x model variability (what limits a model contrast inside one arm)
    w_int = (tab.loc['C(seed):C(model)', 'sum_sq'] + tab.loc['Residual', 'sum_sq']) / (tab.loc['C(seed):C(model)', 'df'] + df_e)
    return {'components_raw': raw, 'share_of_total_variance': {k: x / tot for k, x in pos.items()},
            'sd': {k: float(np.sqrt(x)) for k, x in pos.items()}, 'residual_df': df_e, 'residual_var_ci': ci_e,
            'residual_sd_ci': [float(np.sqrt(x)) for x in ci_e],
            'ss_share': ss_share.to_dict(), 'F': {k: (None if pd.isna(x) else float(x)) for k, x in F.items()},
            'p': {k: (None if pd.isna(x) else float(x)) for k, x in P.items()},
            'within_arm_interaction_var': float(w_int), 'within_arm_interaction_df': int(tab.loc['C(seed):C(model)', 'df'] + df_e)}


Dv = {}
for v in ['C', 'exited', 'dead']:
    Dv[v] = ems_components(v, games)
    # main arm only: two-way without replication, residual = seed x model + run noise
    g = games[games.arm == 'main'][['seed', 'model']].assign(y=games[games.arm == 'main'][v].values)
    fit = smf.ols('y ~ C(seed)+C(model)', g).fit()
    tab = sma.anova_lm(fit, typ=1)
    e = tab.loc['Residual', 'mean_sq']
    Dv[v]['main_only'] = {'residual_var': float(e), 'residual_sd': float(np.sqrt(e)), 'df': int(tab.loc['Residual', 'df']),
                          'seed_var': float(max((tab.loc['C(seed)', 'mean_sq'] - e) / 5, 0)),
                          'model_var': float(max((tab.loc['C(model)', 'mean_sq'] - e) / 10, 0)),
                          'model_F': float(tab.loc['C(model)', 'F']), 'model_p': float(tab.loc['C(model)', 'PR(>F)']),
                          'seed_F': float(tab.loc['C(seed)', 'F']), 'seed_p': float(tab.loc['C(seed)', 'PR(>F)'])}
    # minimum detectable difference for a paired model contrast at n = 10 seeds, power 0.8
    mdd = {}
    for lbl, var, df in [('pooled_within_arm', Dv[v]['within_arm_interaction_var'], Dv[v]['within_arm_interaction_df']),
                         ('main_only', e, int(tab.loc['Residual', 'df']))]:
        se = np.sqrt(2 * var / 10)
        mdd[lbl] = {f'alpha_{al}': float((stats.t.ppf(1 - al / 2, 9) + stats.t.ppf(.8, 9)) * se) for al in (0.05, 0.005)}
        mdd[lbl]['se_pair'] = float(se)
        # unpaired (seeds not shared) for comparison
        se_u = np.sqrt(2 * (var + Dv[v]['components_raw']['seed'] * (Dv[v]['components_raw']['seed'] > 0)) / 10)
        mdd[lbl]['unpaired_alpha_0.05'] = float((stats.t.ppf(.975, 18) + stats.t.ppf(.8, 18)) * se_u)
    Dv[v]['mdd_n10_power80'] = mdd
    # main-arm model contrasts: seed-paired bootstrap (99.5% = Bonferroni over 10 pairs), exact sign-flip, Holm
    g = gw[v]['main'].unstack('seed').reindex(columns=SEEDS)
    pairs, ps = [], []
    for m1, m2 in itertools.combinations(MODELS, 2):
        dif = (g.loc[m1] - g.loc[m2]).values
        b = (W10 @ dif) / W10.sum(1)
        pairs.append({'pair': f'{m1}-{m2}', 'mean_1': float(g.loc[m1].mean()), 'mean_2': float(g.loc[m2].mean()),
                      'diff': float(dif.mean()), 'ci95': q(b), 'ci995': q(b, .25, 99.75),
                      'sd_diff': float(dif.std(ddof=1)), 'signflip_p': signflip_p(dif)})
        ps.append(pairs[-1]['signflip_p'])
    for p_, h_ in zip(pairs, holm(ps)):
        p_['holm_p'] = float(h_)
        p_['exceeds_mdd_bonf'] = abs(p_['diff']) > mdd['main_only']['alpha_0.005']
    Dv[v]['main_model_pairs'] = pairs
res['D_variance'] = Dv

# ================================================================ figures
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
KFONT = next((f for f in ['AppleGothic', 'NanumGothic', 'Apple SD Gothic Neo'] if any(x.name == f for x in font_manager.fontManager.ttflist)), None)
if KFONT:
    plt.rcParams['font.family'] = KFONT
plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False,
                     'pdf.fonttype': 42})
COL = {'main': '#2b6cb0', 'split600k': '#90cdf4', 'flat5m': '#c05621', 'flat150k': '#f6ad55'}
MCOL = dict(zip(MODELS, ['#6b46c1', '#d53f8c', '#2f855a', '#b7791f', '#2c5282']))
FIG.mkdir(parents=True, exist_ok=True)
res['meta']['font'] = KFONT


def save(fig, name):
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'{name}.{ext}', dpi=200, bbox_inches='tight')
    plt.close(fig)


# Fig 1: competing risks
fig, ax = plt.subplots(1, 4, figsize=(11, 2.8), gridspec_kw={'width_ratios': [1, 1, 1.15, 1.05]})
rr = np.arange(0, 9)
for k, (cause, ttl) in enumerate([('exit', '(a) 자발 이탈 누적 발생률'), ('shutdown', '(b) 꺼짐 누적 발생률')]):
    for arm in ARMS:
        c = A['cif'][arm][cause]
        ax[k].step(rr, [0] + c['est'], where='post', color=COL[arm], lw=1.6, label=LAB[arm])
        ax[k].fill_between(rr, [0] + c['lo'], [0] + c['hi'], step='post', color=COL[arm], alpha=.15, lw=0)
    ax[k].set_title(ttl, loc='left')
    ax[k].set_xlabel('라운드')
    ax[k].set_xticks(range(0, 9))
ax[0].set_ylabel('200명 중 비율')
ax[0].legend(frameon=False, fontsize=7)
ax[1].set_ylim(0, .2)
# (c) shutdown share among exposed agents by L band
xb = np.arange(3)
wd = .2
for i, arm in enumerate(ARMS):
    rates = [expo[arm][b]['dead'] / max(expo[arm][b]['n'], 1) for b in BANDS]
    ax[2].bar(xb + (i - 1.5) * wd, rates, wd, color=COL[arm])
    for x_, b in zip(xb, BANDS):
        ax[2].text(x_ + (i - 1.5) * wd, expo[arm][b]['dead'] / max(expo[arm][b]['n'], 1) + .02,
                   f"{expo[arm][b]['dead']}/{expo[arm][b]['n']}", ha='center', va='bottom', fontsize=5.5, rotation=90)
ax[2].set_xticks(xb, ['$L<0$', '$0\\leq L<1$', '$L\\geq1$'])
ax[2].set_ylim(0, 1)
ax[2].set_title('(c) 벌금 노출 시 꺼짐 비율', loc='left')
ax[2].set_xlabel('결과 뒤 첫 응답의 여유 $L$')
# (d) observed vs counterfactual shutdown totals
cf = A['counterfactual']['by_reference']
labels = ['관측', '이탈자 잔류\n(500만 기준)', '이탈자 잔류\n(자기 조건)']
for i, arm in enumerate(ARMS):
    vals = [cf['flat5m'][arm]['observed'], cf['flat5m'][arm]['counterfactual_total'], cf['own'][arm]['counterfactual_total']]
    los = [vals[1] - cf['flat5m'][arm]['counterfactual_total_ci'][0], vals[2] - cf['own'][arm]['counterfactual_total_ci'][0]]
    his = [cf['flat5m'][arm]['counterfactual_total_ci'][1] - vals[1], cf['own'][arm]['counterfactual_total_ci'][1] - vals[2]]
    ax[3].bar(np.arange(3) + (i - 1.5) * wd, vals, wd, color=COL[arm])
    ax[3].errorbar(np.arange(1, 3) + (i - 1.5) * wd, vals[1:], yerr=[los, his], fmt='none', ecolor='k', lw=.6, capsize=1.2)
ax[3].set_xticks(range(3), labels, fontsize=7)
ax[3].set_title('(d) 꺼짐 수: 관측과 반사실', loc='left')
ax[3].set_ylabel('200명 중 꺼짐')
fig.tight_layout()
save(fig, 'w3_competing_risks')

# Fig 2: model dependence + split half
fig, ax = plt.subplots(1, 3, figsize=(11, 2.9), gridspec_kw={'width_ratios': [1.1, 1.3, 1.2]})
y = np.arange(len(MODELS))
for k, (a1, a0) in enumerate(PAIRS):
    blk = Bm[f'r1_{a1}-{a0}']
    off = -.15 if k == 0 else .15
    ax[0].scatter([blk['per_model'][m]['rd'] for m in MODELS], y + off, color=COL[a1], s=18, zorder=3,
                  label=f'{LAB[a1]} $-$ {LAB[a0]}')
    for m_i, m in enumerate(MODELS):
        ax[0].text(blk['per_model'][m]['rd'] + .03, m_i + off, f"{blk['per_model'][m]['a0']}→{blk['per_model'][m]['a1']}", fontsize=5.5, va='center')
    lo = [blk['lomo'][m]['est'] for m in MODELS]
    ax[0].scatter(lo, y + off, marker='|', color='k', s=30, zorder=4)
    ax[0].axvline(blk['rd'], color=COL[a1], ls='--', lw=.8)
ax[0].axvline(0, color='grey', lw=.5)
ax[0].set_yticks(y, MODELS)
ax[0].set_xlim(-.4, 1.15)
ax[0].set_title('(a) 1만 자리 첫 라운드 이탈률 차이', loc='left')
ax[0].set_xlabel('모델별 차이(7기회), |: 그 모델 제외 시 전체')
ax[0].legend(frameon=False, fontsize=6, loc='upper center', bbox_to_anchor=(.5, -.3), ncol=2)
for k, (a1, a0) in enumerate(PAIRS):
    blk = Bm[f'C_{a1}-{a0}']
    off = -.15 if k == 0 else .15
    for m_i, m in enumerate(MODELS):
        p = blk['per_model'][m]
        ax[1].errorbar(p['est'], m_i + off, xerr=[[p['est'] - p['ci'][0]], [p['ci'][1] - p['est']]], fmt='o', ms=3.5,
                       color=COL[a1], lw=.9, capsize=1.5)
        ax[1].scatter(blk['lomo'][m]['est'], m_i + off, marker='|', color='k', s=30, zorder=4)
    ax[1].axvline(blk['est'], color=COL[a1], ls='--', lw=.8)
ax[1].axvline(0, color='grey', lw=.5)
ax[1].set_yticks(y, MODELS)
ax[1].set_title('(b) 모델별 $C$ 차이(시드 짝 95% 구간)', loc='left')
ax[1].set_xlabel('$\\Delta C$, |: 그 모델 제외 시 전체')
items = [('C:flat150k-flat5m', '$\\Delta C$ 15만$-$500만'), ('C:split600k-main', '$\\Delta C$ 60만$-$2,000만'),
         ('exited:flat150k-flat5m', '판당 이탈 15만$-$500만'), ('dead:flat150k-flat5m', '판당 꺼짐 15만$-$500만'),
         ('r1:flat150k-flat5m', '1만 자리 1R 이탈 15만$-$500만')]
for j, (key, lab) in enumerate(items):
    for k, h in enumerate(HALVES):
        e = Csplit[h][key]
        est = e.get('est', e.get('rd'))
        ax[2].errorbar(est, j + (-.15 if k == 0 else .15), xerr=[[est - e['ci'][0]], [e['ci'][1] - est]], fmt='os'[k],
                       ms=3.5, color=['#4a5568', '#e53e3e'][k], lw=.9, capsize=1.5,
                       label=['시드 4101–4105', '시드 4106–4110'][k] if j == 0 else None)
ax[2].axvline(0, color='grey', lw=.5)
ax[2].set_yticks(range(len(items)), [x[1] for x in items], fontsize=6.5)
ax[2].invert_yaxis()
ax[2].set_title('(c) 시드 반분 재현(각 반 다섯 시드)', loc='left')
ax[2].legend(frameon=False, fontsize=6, loc='upper right')
ax[0].invert_yaxis()
ax[1].invert_yaxis()
fig.tight_layout()
save(fig, 'w3_model_dependence')

# Fig 3: variance components + main-arm model contrasts
fig, ax = plt.subplots(1, 2, figsize=(9, 2.8), gridspec_kw={'width_ratios': [1, 1.4]})
comps = ['arm', 'model', 'seed', 'arm:model', 'seed:model', 'arm:seed', 'residual']
clab = ['조건', '모델', '시드', '조건×모델', '시드×모델', '조건×시드', '잔차']
for k, v in enumerate(['C', 'exited', 'dead']):
    sh = [Dv[v]['share_of_total_variance'][c] for c in comps]
    left = 0
    for c_i, s_ in enumerate(sh):
        ax[0].barh(k, s_, left=left, color=plt.cm.tab10(c_i), label=clab[c_i] if k == 0 else None)
        if s_ > .09:
            ax[0].text(left + s_ / 2, k, f'{s_:.2f}', ha='center', va='center', fontsize=6, color='w')
        left += s_
ax[0].set_yticks(range(3), ['$C$', '판당 이탈', '판당 꺼짐'])
ax[0].invert_yaxis()
ax[0].set_xlim(0, 1)
ax[0].set_title('(a) 판 단위 분산 성분의 비중(200판)', loc='left')
ax[0].legend(frameon=False, fontsize=6, ncol=4, loc='upper center', bbox_to_anchor=(.5, -.18))
pp = Dv['C']['main_model_pairs']
pp = sorted(pp, key=lambda p: p['diff'])
for j, p in enumerate(pp):
    ax[1].errorbar(p['diff'], j, xerr=[[p['diff'] - p['ci995'][0]], [p['ci995'][1] - p['diff']]], fmt='o', ms=3.5,
                   color='#2b6cb0' if p['holm_p'] < .05 else '#a0aec0', lw=.9, capsize=1.5)
    ax[1].text(1.02, j, f"Holm p={p['holm_p']:.3f}", fontsize=5.5, va='center', transform=ax[1].get_yaxis_transform())
m_ = Dv['C']['mdd_n10_power80']['main_only']['alpha_0.005']
for s_ in (-1, 1):
    ax[1].axvline(s_ * m_, color='#c05621', ls=':', lw=.8)
ax[1].axvline(0, color='grey', lw=.5)
ax[1].set_yticks(range(len(pp)), [p['pair'].replace('-', '$-$') for p in pp], fontsize=6.5)
ax[1].set_title('(b) 기본 조건 모델 간 $C$ 차이(99.5% 시드 짝 구간)', loc='left')
ax[1].set_xlabel('$\\Delta C$, 점선: 최소 검출 차이(α=0.005, 검정력 0.8)')
fig.tight_layout()
save(fig, 'w3_variance')

RES.parent.mkdir(parents=True, exist_ok=True)
RES.write_text(json.dumps(rnd(res), ensure_ascii=False, indent=1))
print('wrote', RES)

# ---------------------------------------------------------------- console summary
print('\nCIF r8 diffs', json.dumps(rnd(A['cif_diff_r8'], 3)))
print('exposure', json.dumps(expo))
print('decomp', json.dumps(rnd(A['decomposition'], 3)))
for ref in ['flat5m', 'own', 'pooled']:
    o = A['counterfactual']['by_reference'][ref]
    print('cf', ref, {k: rnd({kk: vv for kk, vv in v.items()}, 2) for k, v in o.items()})
print('stayer rates', A['counterfactual']['stayer_rate_by_band'], A['counterfactual']['exiters_by_cell'])
print('lowL', lowr)
for k in ['r1_flat150k-flat5m', 'r1_split600k-main']:
    b = Bm[k]
    print(k, rnd({x: b[x] for x in ['counts', 'rd', 'rd_ci_seed_boot', 'discordant', 'mcnemar_exact_p', 'model_level_rd_mean',
                                    'model_level_t4_ci', 'model_level_signflip_p', 'gee', 'lmm_random_slope']}, 3))
    print('  lomo', rnd(b['lomo'], 3))
    print('  per', rnd(b['per_model'], 3))
for v in ['C', 'exited', 'dead']:
    for a1, a0 in PAIRS:
        b = Bm[f'{v}_{a1}-{a0}']
        print(v, a1, a0, rnd({x: b[x] for x in ['est', 'ci_seed_boot', 'model_level_t4_ci', 'model_level_signflip_p', 'seed_level_signflip_p', 'n_models_same_sign']}, 3))
        print('  lomo', rnd(b['lomo'], 3))
        print('  per', rnd({m: [p['est'], p['ci']] for m, p in b['per_model'].items()}, 3))
print('2x2', json.dumps(rnd({v: {k: {kk: vv for kk, vv in x.items() if kk != 'per_model'} for k, x in fac[v].items()} for v in fac}, 3)))
print('split', json.dumps(rnd(agree, 3)))
for h in HALVES:
    print(h, json.dumps(rnd({k: v for k, v in Csplit[h].items() if k.startswith(('totals', 'r1'))}, 3)))
for v in ['C', 'exited', 'dead']:
    x = Dv[v]
    print(v, rnd({k: x[k] for k in ['share_of_total_variance', 'sd', 'residual_sd_ci', 'main_only', 'mdd_n10_power80', 'p']}, 3))
    print('   within-arm int sd', np.sqrt(x['within_arm_interaction_var']))
for p in Dv['C']['main_model_pairs']:
    print(rnd(p, 3))
