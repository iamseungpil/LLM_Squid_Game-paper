"""W1b (review round 2): an empirically calibrated transition model of the 5.2 arena v33 as the EV baseline.

Answers the round-1 review (A-1, C-2, Q1, Q10, Tier1-1, structure-1): the round-1 DP held the headcount fixed and
assumed no support, and the round-1 simulator drew the solver independently each round. Here

  1. the solver follows the engine's (seed, round)-shuffled cycle (w1_ev_baseline.Refill / next_solver; replayed
     against all 1,558 logged game-rounds);
  2. a transition model is fitted per model x arm with ridge shrinkage toward the pooled fit (logistic terms over
     round band, L band, start seat, headcount): own / peer EXIT hazard, support received at the prep TALK
     (probability; amount drawn from the observed amounts), rescue support after a wrong answer (probability;
     amount = shortfall + observed surplus for agents that would be shut down), TALK and SOLVE generation cost
     (observed draws per model), wrong-answer probability per model x round (Beta shrinkage); shutdowns follow from
     the ledger rule (balance <= charge, or a reply / SOLVE reaching zero). Penalties are chosen by leave-one-seed-out
     deviance. Validation: leave-one-seed-out (10 folds), whole held-out games simulated from round 1, predicted vs
     observed exits, shutdowns, finishers, C per arm, per model and per arm x model with 95% predictive intervals;
     held-out EXIT-hazard calibration (log loss, Brier, AUC, reliability) against simpler predictors;
  3. every observed exit opportunity (non-solver, >= 2 taking part; 3,588) is simulated forward from its logged state
     (all four balances, the cycle, the round's solver) with the focal agent staying now and then following the best
     of four continuation rules (never exit; its model's calibrated hazard; exit if L<1; exit if L<2), peers following
     the calibrated model, headcount varying, split / fixed prize at the believed horizon. EV(stay) - EV(exit) under
     H in {8, 10, 14, 20} and a geometric horizon (continue with prob 7/8 each round), support {none, calibrated},
     regular-work value W in {0, 10k, 50k} (paid on any exit), risk neutral. Uncertainty: the whole model is refitted on
     seed-bootstrap resamples (B fits, each with its own Monte-Carlo draws). Each LLM exit is classed robustly
     EV-losing (stay better under every assumption, 2.5% bound > 0), robustly EV-consistent (exit better under every
     assumption, 97.5% bound < 0) or assumption-dependent. The no-support, fixed-headcount DP of w1_ev_baseline is kept
     as a second baseline for the same decisions;
  4. C-2 table: start seat x model x arm x round band x L band, realized EV of stayers (seed bootstrap) next to the
     model EV difference (fit bootstrap), cells with n < 5 unidentified, cells with no exiters flagged;
  5. Q10: H* (smallest believed horizon <= 30 at which exit beats stay) for every decision state;
  6. CRRA rho* and shutdown penalty K* recomputed for all 279 LLM exits from the simulated stay distribution.

Data (no model calls): the tidy tables of validation_data.py (v33 public cohort + v33ab prize ablation, 200 games).
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w1b_calibrated.py [--boot 40 --reps 48]
Writes results/w1_ev_baseline.json (key 'round2'; round-1 keys untouched), results/w1b_cells.csv,
results/w1b_decisions.csv, figures/w1_validation.*, figures/w1_ev_decisions.*, figures/w1_ev_cells.*.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

import validation_data as d
import w1_ev_baseline as w1

HERE = Path(__file__).resolve().parent
VAL = HERE.parent
OUT_JSON = VAL / 'results/w1_ev_baseline.json'
FIG = VAL / 'figures'
ARMS, MODELS, SEEDS = w1.ARMS, d.MODELS, d.SEEDS
ARM_I = {a: i for i, a in enumerate(ARMS)}
MODEL_I = {m: i for i, m in enumerate(MODELS)}
SPLIT = np.array([w1.RULE[a][0] == 'split' for a in ARMS])
AMOUNT = np.array([float(w1.RULE[a][1]) for a in ARMS])
CHARGE, BONUS = d.CHARGE_TOTAL, d.EXIT_BONUS
SEAT_TIER = np.array([0, 1, 2, 3])  # simulator seat i = start tier 60k, 40k, 20k, 10k
TIER_SEAT = {60: 0, 40: 1, 20: 2, 10: 3}
HMAX = 30
HGRID = [8, 10, 14, 20]
GEO = 7 / 8
WGRID = [0.0, 10_000.0, 50_000.0]
SUPPORTS = ['none', 'calib']
POLICIES = ['never', 'calib', 'thr1', 'thr2']
ASSUME = [(h, s, w) for h in HGRID + ['geo'] for s in SUPPORTS for w in WGRID]
ANCHOR = ASSUME.index((8, 'calib', 0.0))
GRIDS = {  # nested assumption sets for the robust classes
    'anchor': [ANCHOR],
    'H8': [j for j, (h, s, w) in enumerate(ASSUME) if h == 8],
    'true_horizon': [j for j, (h, s, w) in enumerate(ASSUME) if h in (8, 'geo')],
    'calib_H8_10_geo': [j for j, (h, s, w) in enumerate(ASSUME) if s == 'calib' and h in (8, 10, 'geo')],
    'calib': [j for j, (h, s, w) in enumerate(ASSUME) if s == 'calib'],
    'H_le10': [j for j, (h, s, w) in enumerate(ASSUME) if h in (8, 10, 'geo')],
    'all': list(range(len(ASSUME)))}
LAM_MAIN = 0.1
LAM_GRID = [0.3, 1.0, 3.0, 10.0, 30.0, 100.0]
NMIN = 5
LOWBAL = 2_000  # TALK cost of agents holding fewer tokens is drawn from the pooled low-balance replies


# --------------------------------------------------------------------------- bands
def lb6(L):
    return np.searchsorted([0.5, 1, 2, 4, 8], L, side='right')


def lowc(L):
    return np.where(L < 1, 0, np.where(L < 2, 1, 2))


def rb4(r):
    r = np.asarray(r)
    return np.where(r <= 1, 0, np.where(r <= 3, 1, np.where(r <= 5, 2, 3)))


def lrb(Lr, needy):
    return np.where(needy, 0, np.where(Lr < 1, 1, np.where(Lr < 2, 2, 3)))


# --------------------------------------------------------------------------- ridge logistic over categorical terms
Z0 = lambda z: np.zeros(np.shape(z['L']), int)  # noqa: E731
EXIT_TERMS = [
    ('icpt', 1, 'none', Z0), ('arm', 4, 'main', lambda z: z['arm']), ('lb', 6, 'main', lambda z: lb6(z['L'])),
    ('rb', 4, 'main', lambda z: rb4(z['r'])), ('tier', 4, 'main', lambda z: z['tier']),
    ('n', 3, 'main', lambda z: z['n'] - 2), ('arm_low', 12, 'int', lambda z: z['arm'] * 3 + lowc(z['L'])),
    ('model', 5, 'int', lambda z: z['model']), ('model_arm', 20, 'int', lambda z: z['model'] * 4 + z['arm']),
    ('model_low', 15, 'int', lambda z: z['model'] * 3 + lowc(z['L'])),
    ('model_r1', 5, 'int', lambda z: np.where(np.asarray(z['r']) == 1, z['model'], -1))]
GIFT_TERMS = [
    ('icpt', 1, 'none', Z0), ('arm', 4, 'main', lambda z: z['arm']), ('lb', 6, 'main', lambda z: lb6(z['L'])),
    ('sol', 2, 'main', lambda z: z['sol'].astype(int)),
    ('sol_low', 6, 'main', lambda z: z['sol'].astype(int) * 3 + lowc(z['L'])),
    ('rb', 4, 'main', lambda z: rb4(z['r'])), ('tier', 4, 'main', lambda z: z['tier']),
    ('n', 3, 'main', lambda z: z['n'] - 2),
    ('model', 5, 'int', lambda z: z['model']), ('model_arm', 20, 'int', lambda z: z['model'] * 4 + z['arm']),
    ('model_sol', 10, 'int', lambda z: z['model'] * 2 + z['sol'].astype(int)),
    ('model_low', 15, 'int', lambda z: z['model'] * 3 + lowc(z['L']))]
RESC_TERMS = [
    ('icpt', 1, 'none', Z0), ('arm', 4, 'main', lambda z: z['arm']),
    ('lrb', 4, 'main', lambda z: lrb(z['L'], z['needy'])), ('rb', 4, 'main', lambda z: rb4(z['r'])),
    ('tier', 4, 'main', lambda z: z['tier']), ('n', 3, 'main', lambda z: z['n'] - 2),
    ('sol', 2, 'main', lambda z: z['sol'].astype(int)),
    ('sol_needy', 4, 'main', lambda z: z['sol'].astype(int) * 2 + z['needy'].astype(int)),
    ('arm_needy', 8, 'int', lambda z: z['arm'] * 2 + z['needy'].astype(int)),
    ('model_sol', 10, 'int', lambda z: z['model'] * 2 + z['sol'].astype(int)),
    ('model', 5, 'int', lambda z: z['model']), ('model_arm', 20, 'int', lambda z: z['model'] * 4 + z['arm']),
    ('model_needy', 10, 'int', lambda z: z['model'] * 2 + z['needy'].astype(int))]


def onehot(terms, z):
    N = len(z['L'])
    blocks, kinds = [], []
    for _, k, kind, fn in terms:
        idx = np.broadcast_to(fn(z), N)
        B = np.zeros((N, k))
        ok = idx >= 0
        B[np.flatnonzero(ok), idx[ok]] = 1
        blocks.append(B)
        kinds += [kind] * k
    return np.hstack(blocks), kinds


def fit_logit(terms, z, y, w, lam):
    X, kinds = onehot(terms, z)
    pen = np.array([{'none': 1e-6, 'main': LAM_MAIN, 'int': lam}[k] for k in kinds])
    beta = np.zeros(X.shape[1])
    ybar = np.clip((w * y).sum() / w.sum(), 1e-4, 1 - 1e-4)
    beta[0] = np.log(ybar / (1 - ybar))
    def obj(b):
        eta = X @ b
        return -(w * (y * eta - np.logaddexp(0, eta))).sum() + 0.5 * (pen * b * b).sum()
    cur = obj(beta)
    for _ in range(200):  # damped Newton on the penalized log likelihood
        p = expit(X @ beta)
        g = X.T @ (w * (y - p)) - pen * beta
        Hm = (X * (w * p * (1 - p))[:, None]).T @ X + np.diag(pen)
        step = np.linalg.solve(Hm, g)
        a = 1.0
        while a > 1e-6:
            new = obj(beta + a * step)
            if new <= cur + 1e-10:
                break
            a /= 2
        beta = beta + a * step
        done = cur - new < 1e-9
        cur = new
        if done or np.abs(a * step).max() < 1e-7:
            break
    out, i = [], 0
    for _, k, _, _ in terms:
        out.append(beta[i:i + k])
        i += k
    return out


def predict(terms, coefs, z):
    shape = np.shape(z['L'])
    eta = np.zeros(shape)
    for (_, _, _, fn), c in zip(terms, coefs):
        idx = np.broadcast_to(fn(z), shape)
        eta += np.where(idx >= 0, c[np.maximum(idx, 0)], 0.0)
    return expit(eta)


# --------------------------------------------------------------------------- pools of observed draws
class Pool:
    """Observed values grouped by an integer key; keys with fewer than nmin values borrow the fallback key's values."""

    def __init__(self, keys, vals, K, fallback=None, nmin=20):
        keys, vals = np.asarray(keys, int), np.asarray(vals, float)
        groups = [vals[keys == k] for k in range(K)]
        if fallback is not None:
            for k in range(K):
                if len(groups[k]) < nmin:
                    groups[k] = np.concatenate([groups[k], vals[np.isin(keys, fallback(k))]])
        allv = vals if len(vals) else np.zeros(1)
        groups = [g if len(g) else allv for g in groups]
        self.vals = np.concatenate(groups)
        self.lens = np.array([len(g) for g in groups])
        self.starts = np.concatenate([[0], np.cumsum(self.lens)[:-1]])
        self.groups = groups

    def draw(self, rng, key):
        key = np.asarray(key, int)
        u = rng.random(key.shape)
        return self.vals[self.starts[key] + (u * self.lens[key]).astype(int)]


# --------------------------------------------------------------------------- data
def data_tables(f):
    ar = f['agent_rounds'].copy()
    calls = f['calls']
    key = ['arm', 'model', 'seed', 'round', 'agent']
    talk = calls[calls.kind == 'talk'].groupby(key + ['phase']).used.sum().unstack('phase').reset_index()
    ar = ar.merge(talk, on=key, how='left')
    ar['c_prep'] = ar['prep'].fillna(0.0)
    ar['c_resc'] = ar['rescue'].fillna(0.0)
    ar['arm_i'] = ar.arm.map(ARM_I)
    ar['model_i'] = ar.model.map(MODEL_I)
    ar['seat'] = ar.tier.map(TIER_SEAT)
    ar['wrong'] = ar.wrong.astype(bool)
    rb_ = ar.rescue_bal_start.astype(float).fillna(0.0)
    ar['pre'] = rb_ - ar.recv_rescue + ar.gave_rescue  # balance after the rescue TALK cost, before rescue gifts
    ar['b_res'] = ar.pre + ar.c_resc  # balance when the rescue TALK starts
    solve = calls[calls.kind == 'solve'][['arm', 'model', 'seed', 'used']].copy()
    solve['model_i'] = solve.model.map(MODEL_I)
    rr = ar.drop_duplicates(['arm', 'model', 'seed', 'round'])[['arm', 'model', 'model_i', 'seed', 'round', 'wrong']]
    return dict(ar=ar, solve=solve, rr=rr)


def zmap(df, L=None, sol=None, needy=None):
    return dict(arm=df.arm_i.to_numpy(), model=df.model_i.to_numpy(), L=df.L_prep.to_numpy() if L is None else L,
                r=df['round'].to_numpy(), tier=df.seat.to_numpy(), n=df.n.to_numpy(),
                sol=df.solver.to_numpy() if sol is None else sol,
                needy=np.zeros(len(df), bool) if needy is None else needy)


def model_rows(T):
    """The four row sets the logistic parts are fitted on."""
    ar = T['ar']
    ex = ar[ar.can_exit & (ar.n > 1)]
    gi = ar[ar.n > 1]
    rw = ar[ar.wrong & ~ar.exited & (ar.n > 1) & (ar.pre > 0)]
    lr_ = ((rw.pre - rw.fee) / rw.fee).to_numpy()
    needy = (rw.pre <= rw.fee).to_numpy()
    return dict(ex=(ex, zmap(ex), ex.exited.to_numpy(float)),
                gi=(gi, zmap(gi), (gi.recv_prep > 0).to_numpy(float)),
                rw=(rw, zmap(rw, L=lr_, needy=needy), (rw.recv_rescue > 0).to_numpy(float)))


TERMS = dict(ex=EXIT_TERMS, gi=GIFT_TERMS, rw=RESC_TERMS)


def fit(T, MR, wseed, lam):
    """All parts of the transition model on seed weights wseed (dict seed -> weight; bootstrap counts or 0/1)."""
    ar = T['ar']
    wr = ar.seed.map(wseed).to_numpy(float)
    P = dict(lam=lam)
    for k in ['ex', 'gi', 'rw']:
        df, z, y = MR[k]
        w = df.seed.map(wseed).to_numpy(float)
        sel = w > 0
        P[k] = fit_logit(TERMS[k], {a: v[sel] for a, v in z.items()}, y[sel], w[sel], lam[k])

    def rep(df, cols):
        w = df.seed.map(wseed).to_numpy(int)
        return {c: np.repeat(df[c].to_numpy(), w) for c in cols}
    lone = ar[(ar.n == 1)]
    lw = lone.seed.map(wseed).to_numpy(float)
    pool_rate = (lw * lone.exited).sum() / max(lw.sum(), 1e-9)
    lowl = (lone.L_prep < 1).to_numpy()  # a lone agent below one charge (24,000) usually leaves; above it rarely
    P['lone'] = np.array([((lw * lone.exited)[lowl == k].sum() + 2 * pool_rate) / (lw[lowl == k].sum() + 2)
                          for k in (False, True)])
    # costs
    g = rep(ar, ['model_i', 'L_prep', 'c_prep', 'c_resc', 'wrong', 'b_res', 'fee', 'exited', 'died', 'solver'])
    bp = g['L_prep'] * g['fee']
    kp = np.where(bp < LOWBAL, 15, g['model_i'] * 3 + lowc(g['L_prep']))
    # below LOWBAL the pooled draw is a share of the balance (a reply that reaches zero has share 1)
    vp = np.where(bp < LOWBAL, np.minimum(g['c_prep'] / np.maximum(bp, 1), 1.0), g['c_prep'])
    P['c_prep'] = Pool(kp, vp, 16, fallback=lambda k: [k - k % 3 + i for i in range(3)] if k < 15 else [15])
    st = ~g['exited'] & (g['b_res'] > 0)
    kr = np.where(g['b_res'] < LOWBAL, 20, g['model_i'] * 4 + g['wrong'] * 2 + (g['b_res'] / g['fee'] < 2))
    vr = np.where(g['b_res'] < LOWBAL, np.minimum(g['c_resc'] / np.maximum(g['b_res'], 1), 1.0), g['c_resc'])
    P['c_resc'] = Pool(kr[st], vr[st], 21, fallback=lambda k: [k - k % 2, k - k % 2 + 1] if k < 20 else [20])
    # an agent left at or below its charge after a wrong answer that gives everything away (logged GIVE ALL)
    dm = ar[ar.wrong & ~ar.exited & (ar.pre > 0) & (ar.n > 1) & (ar.pre + ar.recv_rescue - ar.gave_rescue <= ar.fee)
            & ~((ar.recv_rescue > 0) & (ar.pre + ar.recv_rescue > ar.fee))]
    dw = dm.seed.map(wseed).to_numpy(float)
    P['p_giveall'] = float((dw * (dm.gave_rescue > 0)).sum() / max(dw.sum(), 1e-9))
    sv = rep(T['solve'], ['model_i', 'used'])
    P['c_solve'] = Pool(sv['model_i'], sv['used'], 5)
    # wrong probability per model x round (Beta shrinkage to the model mean, model mean to the pooled mean)
    rr = T['rr']
    w_ = rr.seed.map(wseed).to_numpy(float)
    q_all = (w_ * rr.wrong).sum() / w_.sum()
    q = np.zeros((5, 8))
    for m in range(5):
        sm = rr.model_i.to_numpy() == m
        qm = ((w_ * rr.wrong)[sm].sum() + 20 * q_all) / (w_[sm].sum() + 20)
        for r in range(1, 9):
            s = sm & (rr['round'].to_numpy() == r)
            q[m, r - 1] = ((w_ * rr.wrong)[s].sum() + 8 * qm) / (w_[s].sum() + 8)
    P['q'] = q
    # gift amounts: prep (ratio to the per-head charge) by solver x L class; rescue: shortfall surplus / ratio
    gi = ar[(ar.n > 1) & (ar.recv_prep > 0)]
    gg = rep(gi, ['solver', 'L_prep', 'recv_prep', 'fee'])
    P['a_prep'] = Pool(gg['solver'].astype(int) * 3 + lowc(gg['L_prep']), gg['recv_prep'] / gg['fee'], 6,
                       fallback=lambda k: [0, 1, 2, 3, 4, 5], nmin=8)
    rw = MR['rw'][0]
    rr_ = rep(rw[rw.recv_rescue > 0], ['pre', 'fee', 'recv_rescue'])
    needy = rr_['pre'] <= rr_['fee']
    P['a_need'] = rr_['pre'][needy] + rr_['recv_rescue'][needy] - rr_['fee'][needy]
    lr_ = lrb((rr_['pre'] - rr_['fee']) / rr_['fee'], needy)
    P['a_resc'] = Pool(lr_[~needy], rr_['recv_rescue'][~needy] / rr_['fee'][~needy], 4,
                       fallback=lambda k: [1, 2, 3], nmin=8)
    # support after a correct answer (rare): rate by L class, observed ratios
    cr = ar[~ar.wrong & ~ar.exited & (ar.n > 1) & (ar.b_res > 0)]
    cw = cr.seed.map(wseed).to_numpy(float)
    lc = lowc((cr.b_res / cr.fee).to_numpy())
    yc = (cr.recv_rescue > 0).to_numpy(float)
    pc_all = (cw * yc).sum() / cw.sum()
    P['p_corr'] = np.array([((cw * yc)[lc == k].sum() + 5 * pc_all) / (cw[lc == k].sum() + 5) for k in range(3)])
    cc = rep(cr[cr.recv_rescue > 0], ['recv_rescue', 'fee'])
    P['a_corr'] = cc['recv_rescue'] / cc['fee']
    return P


# --------------------------------------------------------------------------- simulator
def give(B, mask, coin, amt, donors, keep):
    """Recipients j (mask & coin), poorest start seat first, receive amt from the other donors, richest first, each
    giving at most what keeps it above keep (several peers may chip in, as in the logs)."""
    rows = np.arange(len(B))
    keep = np.broadcast_to(np.asarray(keep, float), (len(B),))
    for j in [3, 2, 1, 0]:
        rec = mask[:, j] & coin[:, j] & (amt[:, j] > 0)
        if not rec.any():
            continue
        left = np.where(rec, amt[:, j], 0.0)
        other = np.where(donors & (np.arange(4) != j)[None, :], B, -np.inf)
        for dn in np.argsort(-other, axis=1, kind='stable').T:
            cap = np.where(np.isfinite(other[rows, dn]), np.maximum(B[rows, dn] - keep - 1, 0), 0)
            g = np.minimum(left, cap)
            B[rows, dn] -= g
            B[:, j] += g
            left -= g


def simulate(P, init, R, rng, support, policy, hmax, refill, games=False, cause=None):
    """Forward simulation from init (per start: arm, model, seed, r0, bal[4], st[4], cyc[4], sol0, focal); R draws each.

    focal >= 0: that seat stays at r0 and then follows `policy`; returns its balance at the end of each round while in,
    the headcount, its exit balance / round and shutdown round. games=True: per-game outcome counts (focal = -1)."""
    D = len(init['r0'])
    rep = lambda x: np.repeat(np.asarray(x), R, axis=0)  # noqa: E731
    A, M, SD, r0 = rep(init['arm']), rep(init['model']), rep(init['seed']), rep(init['r0'])
    bal, st, cyc = rep(init['bal']).astype(float), rep(init['st']).astype(np.int8), rep(init['cyc']).astype(int)
    sol0, F = rep(init['sol0']), rep(init['focal'])
    N = len(r0)
    fin_bal = np.full((N, hmax + 1), np.nan, np.float32)
    nin = np.zeros((N, hmax + 1), np.int8)
    ex_bal, ex_rd, dd_rd = np.zeros(N), np.full(N, 99), np.full(N, 99)
    first_dep = np.full(N, 99)
    given = np.zeros(N)
    fin = np.ones(N, bool)
    fseat = np.maximum(F, 0)
    for t in range(int(r0.min()), hmax + 1):
        act = (r0 <= t) & (st == 0).any(1) & fin
        ix = np.flatnonzero(act)
        if not len(ix):
            if t >= r0.max():
                break
            continue
        B, S, C = bal[ix], st[ix], cyc[ix]
        a_, m_, sd_, f_ = A[ix], M[ix], SD[ix], F[ix]
        rows = np.arange(len(ix))
        first = r0[ix] == t
        part = S == 0
        n = part.sum(1)
        fee = CHARGE / n
        L0 = B / fee[:, None]
        sol = np.full(len(ix), -1)
        use0 = first & (sol0[ix] >= 0)
        sol[use0] = sol0[ix][use0]
        nd = ~use0
        if nd.any():
            c2 = C[nd]
            sol[nd] = w1.next_solver(c2, part[nd], sd_[nd], t, 0, refill)
            C[nd] = c2
        issol = np.zeros((len(ix), 4), bool)
        issol[rows, np.maximum(sol, 0)] = sol >= 0
        fm = (f_ >= 0)[:, None] & (np.arange(4)[None, :] == f_[:, None])
        z = dict(arm=a_[:, None], model=m_[:, None], L=L0, r=t, tier=SEAT_TIER[None, :], n=n[:, None], sol=issol,
                 needy=np.zeros_like(issol))
        multi = (n > 1)[:, None]
        donors = part & ~fm
        if support == 'calib':
            pg = predict(GIFT_TERMS, P['gi'], z) * (part & multi)
            coin = rng.random(pg.shape) < pg
            amt = P['a_prep'].draw(rng, issol.astype(int) * 3 + lowc(L0)) * fee[:, None]
            b_before = B.copy()
            give(B, part & multi, coin, amt, donors, keep=fee)
            given[ix] += np.maximum(B - b_before, 0).sum(1)
        elig = part & ~issol & multi
        lone = part & ~multi
        pe = np.where(elig, predict(EXIT_TERMS, P['ex'], z), 0.0)
        pe = np.where(lone, P['lone'][(L0 < 1).astype(int)], pe)
        if policy == 'never':
            pf = np.zeros_like(pe)
        elif policy == 'calib':
            pf = pe
        elif policy == 'thr1':
            pf = (L0 < 1).astype(float)
        elif policy == 'thr2':
            pf = (L0 < 2).astype(float)
        pe = np.where(fm, np.where(elig | lone, pf, 0.0), pe)
        pe[fm & first[:, None]] = 0.0
        ex = rng.random(pe.shape) < pe
        lowb = B < LOWBAL
        c = P['c_prep'].draw(rng, np.where(lowb, 15, m_[:, None] * 3 + lowc(L0)))
        c = np.where(lowb, c * B, c)
        B = np.where(part, B - c, B)
        td = part & (B <= 0)
        B[td], S[td] = 0, 2
        if cause is not None:
            cause['talk_prep'] = cause.get('talk_prep', 0) + int(td.sum())
            cause['solver_low_prep'] = cause.get('solver_low_prep', 0) + int((issol & part & (L0 < 1)).sum())
        exn = ex & (S == 0)
        B[exn] += BONUS
        S[exn] = 1
        inn = S == 0
        gone = (sol >= 0) & ~inn[rows, np.maximum(sol, 0)] & inn.any(1)
        if gone.any():
            c2 = C[gone]
            sol[gone] = w1.next_solver(c2, inn[gone], sd_[gone], t, 1, refill)
            C[gone] = c2
        has = (sol >= 0) & inn[rows, np.maximum(sol, 0)]
        sp = np.maximum(sol, 0)
        s = P['c_solve'].draw(rng, m_)
        bs = B[rows, sp]
        void = has & (s >= bs)
        q = P['q'][m_, min(t, 8) - 1]
        correct = has & ~void & (rng.random(len(ix)) > q)
        wrong = has & ~correct
        paid = np.where(has, np.minimum(s, bs), 0.0)
        B[rows, sp] -= paid
        B[rows, sp] += np.where(correct, paid, 0.0)
        vd = np.zeros_like(inn)
        vd[rows, sp] = void
        B[vd], S[vd] = 0, 2
        if cause is not None:
            cause['void'] = cause.get('void', 0) + int(void.sum())
        inn = S == 0
        lowb = B < LOWBAL
        cr = P['c_resc'].draw(rng, np.where(lowb, 20, m_[:, None] * 4 + wrong[:, None] * 2 + (B / fee[:, None] < 2)))
        cr = np.where(lowb, cr * B, cr)
        B = np.where(inn, B - cr, B)
        td = inn & (B <= 0)
        B[td], S[td] = 0, 2
        if cause is not None:
            cause['talk_rescue'] = cause.get('talk_rescue', 0) + int(td.sum())
        inn = S == 0
        if support == 'calib':
            pre = B.copy()
            needy = pre <= fee[:, None]
            Lr = (pre - fee[:, None]) / fee[:, None]
            zr = dict(z, L=Lr, needy=needy)
            pw = predict(RESC_TERMS, P['rw'], zr)
            pc = P['p_corr'][lowc(pre / fee[:, None])]
            p = np.where(wrong[:, None], pw, pc) * (inn & multi)
            coin = rng.random(p.shape) < p
            u = rng.integers(0, 1 << 30, p.shape)
            a_need = (fee[:, None] - pre) + P['a_need'][u % len(P['a_need'])]
            a_res = P['a_resc'].draw(rng, lrb(Lr, needy)) * fee[:, None]
            a_cor = P['a_corr'][u % len(P['a_corr'])] * fee[:, None]
            amt = np.where(wrong[:, None], np.where(needy, a_need, a_res), a_cor)
            keep = np.where(wrong, fee, 0.0)
            b_before = B.copy()
            give(B, inn & multi, coin, amt, inn & ~fm, keep=keep)
            given[ix] += np.maximum(B - b_before, 0).sum(1)
        chg = inn & wrong[:, None]
        if support == 'calib':  # a doomed agent may give everything to the poorest other agent still in
            doom = chg & (B <= fee[:, None]) & (B > 0) & multi & ~fm & (rng.random(B.shape) < P['p_giveall'])
            for j in np.flatnonzero(doom.any(0)):
                dj = doom[:, j]
                other = np.where(inn & ~chg | (inn & (B > fee[:, None])), B, np.inf)
                other[:, j] = np.inf
                rc = other.argmin(1)
                okr = dj & np.isfinite(other[rows, rc])
                B[rows[okr], rc[okr]] += B[okr, j]
                given[ix[okr]] += B[okr, j]
                B[okr, j] = 0
        if cause is not None:
            nd_ = chg & (B <= fee[:, None])
            cause['needy_at_charge'] = cause.get('needy_at_charge', 0) + int(nd_.sum())
            cause['agent_rounds'] = cause.get('agent_rounds', 0) + int(part.sum())
            cause['L<1'] = cause.get('L<1', 0) + int((part & (L0 < 1)).sum())
            cause['L1-2'] = cause.get('L1-2', 0) + int((part & (L0 >= 1) & (L0 < 2)).sum())
            cause['bal<2000'] = cause.get('bal<2000', 0) + int((part & (L0 * fee[:, None] < 2000)).sum())
            cause['bal<1000'] = cause.get('bal<1000', 0) + int((part & (L0 * fee[:, None] < 1000)).sum())
            cause['wrong_rounds'] = cause.get('wrong_rounds', 0) + int(wrong.sum())
            if support == 'calib':
                cause['needy_pre'] = cause.get('needy_pre', 0) + int((inn & wrong[:, None] & needy).sum())
        pay = np.where(chg, np.minimum(fee[:, None], B), 0.0)
        B = B - pay
        cd = chg & (B <= 0)
        B[cd], S[cd] = 0, 2
        if cause is not None:
            cause['charge'] = cause.get('charge', 0) + int(cd.sum())
            cause['charge_solver'] = cause.get('charge_solver', 0) + int((cd & issol).sum())
        newly = (S != 0) & part
        fd = first_dep[ix]
        first_dep[ix] = np.where(newly.any(1) & (fd == 99), t, fd)
        # focal bookkeeping
        if (f_ >= 0).any():
            fs = np.maximum(f_, 0)
            fst = S[rows, fs]
            fex = (fst == 1) & (st[ix, fs] == 0)
            ex_bal[ix[fex]] = B[rows, fs][fex]
            ex_rd[ix[fex]] = t
            fdd = (fst == 2) & (st[ix, fs] == 0)
            dd_rd[ix[fdd]] = t
            fin_bal[ix, t] = np.where(fst == 0, B[rows, fs], np.nan)
            fin[ix] = fst == 0
        nin[ix, t] = (S == 0).sum(1)
        bal[ix], st[ix], cyc[ix] = B, S, C
    if games:
        return dict(exited=(st == 1).sum(1), dead=(st == 2).sum(1), fin=(st == 0).sum(1),
                    C=np.where(first_dep == 99, w1.ROUNDS, first_dep) / w1.ROUNDS, given=given, R=R)
    return dict(fin_bal=fin_bal, nin=nin, ex_bal=ex_bal, ex_rd=ex_rd, dd_rd=dd_rd, R=R, A=A, fseat=fseat)


def values(o, init, hmax):
    """Per start: mean token value A[H], later-exit probability X[H], shutdown probability Dd[H] for H = 0..hmax."""
    R = o['R']
    N = len(o['A'])
    Hs = np.arange(hmax + 1)
    inH = ~np.isnan(o['fin_bal'])
    prize = np.where(SPLIT[o['A']][:, None], AMOUNT[o['A']][:, None] / np.maximum(o['nin'], 1), AMOUNT[o['A']][:, None])
    val = np.where(inH, o['fin_bal'] + prize, 0.0)
    exH = o['ex_rd'][:, None] <= Hs[None, :]
    val = val + np.where(exH, o['ex_bal'][:, None], 0.0)
    ddH = o['dd_rd'][:, None] <= Hs[None, :]
    D = N // R
    rs = lambda x: x.reshape(D, R, hmax + 1).mean(1)  # noqa: E731
    return dict(A=rs(val), X=rs(exH.astype(float)), Dd=rs(ddH.astype(float)), val8=val[:, 8].reshape(D, R))


# --------------------------------------------------------------------------- logged states
def replay_states(f, refill):
    """(arm, model, seed, round) -> balances / taking part by seat, the k=0 solver seat, the cycle after its pop."""
    ar = f['agent_rounds']
    out = {}
    for (arm, m, sd), g in ar.groupby(['arm', 'model', 'seed']):
        nm = refill.names[int(sd)]
        cyc = np.full((1, 4), -1, int)
        for r, gr in g.groupby('round'):
            part = np.array([[a in set(gr.agent) for a in nm]])
            bal = np.zeros(4)
            for a, b in zip(gr.agent, gr.bal_start):
                bal[nm.index(a)] = b
            s0 = w1.next_solver(cyc, part, int(sd), int(r), 0, refill)[0]
            out[arm, m, int(sd), int(r)] = dict(bal=bal, st=np.where(part[0], 0, 1), cyc=cyc[0].copy(), sol0=s0)
            logged = nm.index(gr[gr.solver].agent.iloc[0]) if gr.solver.any() else -1
            if s0 != logged:
                inn = part.copy()
                inn[0, s0] = False
                w1.next_solver(cyc, inn, int(sd), int(r), 1, refill)
    return out


def decision_init(E, states, refill):
    rows = []
    for e in E.itertuples():
        s = states[e.arm, e.model, int(e.seed), int(e.round)]
        rows.append((ARM_I[e.arm], MODEL_I[e.model], int(e.seed), int(e.round), s['bal'], s['st'], s['cyc'], s['sol0'],
                     refill.names[int(e.seed)].index(e.agent)))
    cols = list(zip(*rows))
    return dict(arm=np.array(cols[0]), model=np.array(cols[1]), seed=np.array(cols[2]), r0=np.array(cols[3]),
                bal=np.array(cols[4]), st=np.array(cols[5]), cyc=np.array(cols[6]), sol0=np.array(cols[7]),
                focal=np.array(cols[8]))


def game_init(arm_i, model_i, seeds):
    D = len(seeds)
    return dict(arm=np.full(D, arm_i), model=np.full(D, model_i), seed=np.asarray(seeds), r0=np.ones(D, int),
                bal=np.tile(w1.STARTS, (D, 1)), st=np.zeros((D, 4), int), cyc=np.full((D, 4), -1, int),
                sol0=np.full(D, -1), focal=np.full(D, -1))


# --------------------------------------------------------------------------- EV per decision
def exit_value(P, E, support):
    """EV(exit now) without W, and the probability that the exit is paid (the reply cost leaves a positive balance)."""
    T = E['T'].to_numpy()
    key = np.where(E['T'].to_numpy() < LOWBAL, 15, E.model_i.to_numpy() * 3 + lowc(E.L_prep.to_numpy()))
    ev, pok = np.zeros(len(E)), np.zeros(len(E))
    for k in np.unique(key):
        sel = key == k
        v = P['c_prep'].groups[k]
        left = T[sel][:, None] * (1 - v[None, :]) if k == 15 else T[sel][:, None] - v[None, :]  # share below LOWBAL
        pok[sel] = (left > 0).mean(1)
        ev[sel] = np.where(left > 0, left + BONUS, 0).mean(1)
    if support == 'calib':
        z = zmap(E)
        pg = predict(GIFT_TERMS, P['gi'], z)
        ka = E.solver.to_numpy().astype(int) * 3 + lowc(E.L_prep.to_numpy())
        ev += pg * np.array([P['a_prep'].groups[k].mean() for k in ka]) * E.fee.to_numpy()
    return ev, pok


def ev_run(P, E, init, R, seed, refill):
    """Simulate every decision under both supports and the four continuation rules (common random numbers)."""
    res = {}
    for sup in SUPPORTS:
        ex, pok = exit_value(P, E, sup)
        res[sup] = dict(exit=ex, pok=pok, pol={})
        for pol in POLICIES:
            o = simulate(P, init, R, np.random.default_rng(seed), sup, pol, HMAX, refill)
            res[sup]['pol'][pol] = values(o, init, HMAX)
    return res


def geo_weights(r0):
    Hs = np.arange(HMAX + 1)
    k = Hs[None, :] - r0[:, None]
    w = np.where(k >= 0, (1 - GEO) * GEO ** np.maximum(k, 0), 0.0)
    w[:, HMAX] += 1 - w.sum(1)
    return w


def deltas(res, r0):
    """EV(stay) - EV(exit) for every assumption in ASSUME (D x len(ASSUME)), the chosen rule, and H* per support."""
    D = len(r0)
    gw = geo_weights(r0)
    out = np.zeros((D, len(ASSUME)))
    best = np.zeros((D, len(ASSUME)), int)
    for j, (h, sup, W) in enumerate(ASSUME):
        stay = []
        for pol in POLICIES:
            v = res[sup]['pol'][pol]
            if h == 'geo':
                stay.append(((v['A'] + W * v['X']) * gw).sum(1))
            else:
                stay.append(v['A'][:, h] + W * v['X'][:, h])
        stay = np.array(stay)
        best[:, j] = stay.argmax(0)
        out[:, j] = stay.max(0) - (res[sup]['exit'] + W * res[sup]['pok'])
    hstar = {}
    Hs = np.arange(HMAX + 1)
    for sup in SUPPORTS:
        stay = np.max([res[sup]['pol'][p]['A'] for p in POLICIES], 0)
        better_exit = (stay < res[sup]['exit'][:, None]) & (Hs[None, :] >= r0[:, None])
        hstar[sup] = np.where(better_exit.any(1), better_exit.argmax(1), HMAX + 1)
    return out, best, hstar


def dp_baseline(E, cal):
    """No-support, fixed-headcount DP of w1_ev_baseline for every decision: Delta per (H, W) and H* (W=0)."""
    tabs = {(a, m, W): w1.dp_tables(a, cal[m], HMAX, W=W) for a in ARMS for m in MODELS for W in WGRID}
    D = len(E)
    delta = np.full((D, len(HGRID), len(WGRID)), np.nan)
    hstar = np.full(D, HMAX + 1)
    for i, e in enumerate(E.itertuples()):
        for wi, W in enumerate(WGRID):
            t = tabs[e.arm, e.model, W]
            ex = e.T - t['cp'] + BONUS + W
            for hi, H in enumerate(HGRID):
                delta[i, hi, wi] = w1.dp_value(t, H - e.round + 1, e.n, e.T) - ex
            if W == 0:
                for H in range(e.round, HMAX + 1):
                    if w1.dp_value(t, H - e.round + 1, e.n, e.T) < ex:
                        hstar[i] = H
                        break
    return delta, hstar


# --------------------------------------------------------------------------- validation
def tune_lambda(MR):
    """Leave-one-seed-out deviance of each logistic part over the interaction penalty grid."""
    out, best = {}, {}
    for k in ['ex', 'gi', 'rw']:
        df, z, y = MR[k]
        seeds = df.seed.to_numpy()
        dev = {}
        for lam in LAM_GRID:
            ll = 0.0
            for s in SEEDS:
                tr, te = seeds != s, seeds == s
                c = fit_logit(TERMS[k], {a: v[tr] for a, v in z.items()}, y[tr], np.ones(tr.sum()), lam)
                p = np.clip(predict(TERMS[k], c, {a: v[te] for a, v in z.items()}), 1e-6, 1 - 1e-6)
                ll += -(y[te] * np.log(p) + (1 - y[te]) * np.log(1 - p)).sum()
            dev[lam] = 2 * ll
        out[k] = dev
        best[k] = min(dev, key=dev.get)
    return best, out


def auc(y, p):
    y = np.asarray(y, bool)
    r = pd.Series(p).rank().to_numpy()
    n1, n0 = y.sum(), (~y).sum()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else np.nan


def validate(T, MR, lam, f, refill, R, rng_seed):
    """Leave-one-seed-out: fit on nine seeds, simulate the held-out seed's 20 games from round 1, and score the held-out
    EXIT decisions."""
    games, seats, ar = f['games'], f['seats'], T['ar']
    sims = {}
    hz = []
    ex_df, ex_z, ex_y = MR['ex']
    for s in SEEDS:
        P = fit(T, MR, {x: float(x != s) for x in SEEDS}, lam)
        for arm in ARMS:
            for m in MODELS:
                o = simulate(P, game_init(ARM_I[arm], MODEL_I[m], [s]), R,
                             np.random.default_rng([rng_seed, s, ARM_I[arm], MODEL_I[m]]), 'calib', 'calib', 8,
                             refill, games=True)  # an independent stream per held-out game
                sims[arm, m, s] = o
        te = ex_df.seed.to_numpy() == s
        zt = {a: v[te] for a, v in ex_z.items()}
        p_cal = predict(EXIT_TERMS, P['ex'], zt)
        tr = ex_df[~te]
        # simpler predictors fitted on the same nine seeds
        rate_arm = tr.groupby('arm').exited.mean()
        tr_lb = tr.assign(lb=w1_lband(tr.L_prep), r1=tr['round'] == 1)
        tab = tr_lb.groupby(['arm', 'lb', 'r1']).exited.agg(['sum', 'count'])
        te_df = ex_df[te].assign(lb=w1_lband(ex_df[te].L_prep), r1=ex_df[te]['round'] == 1)
        p_tab = [(tab.loc[k_, 'sum'] + rate_arm[k_[0]]) / (tab.loc[k_, 'count'] + 1) if k_ in tab.index else rate_arm[k_[0]]
                 for k_ in zip(te_df.arm, te_df.lb, te_df.r1)]
        hz.append(pd.DataFrame(dict(seed=s, arm=te_df.arm.to_numpy(), model=te_df.model.to_numpy(),
                                    y=ex_y[te], p_cal=p_cal, p_arm=te_df.arm.map(rate_arm).to_numpy(),
                                    p_tab=np.array(p_tab, float), L=te_df.L_prep.to_numpy())))
    hz = pd.concat(hz, ignore_index=True)
    # game-level comparison
    gtab = games.set_index(['arm', 'model', 'seed'])
    given_obs = f['gifts'].groupby(['arm', 'model', 'seed']).amount.sum()

    def agg(keys):
        obs = {k_: 0.0 for k_ in ['exited', 'dead', 'fin', 'C', 'given']}
        draws = {k_: np.zeros(R) for k_ in obs}
        for k in keys:
            g = gtab.loc[k]
            obs['exited'] += g.exited
            obs['dead'] += g.dead
            obs['fin'] += g.finishers
            obs['C'] += g.C
            obs['given'] += given_obs.get(k, 0.0)
            for k_ in obs:
                draws[k_] += sims[k][k_]
        n = len(keys)
        res = {}
        for k_ in obs:
            o_, dr = obs[k_], draws[k_]
            if k_ in ('C',):
                o_, dr = o_ / n, dr / n
            lo, hi = np.percentile(dr, [2.5, 97.5])
            res[k_] = dict(obs=float(o_), pred=float(dr.mean()), lo=float(lo), hi=float(hi),
                           inside=bool(lo <= o_ <= hi), z=float((o_ - dr.mean()) / max(dr.std(), 1e-9)))
        res['games'] = n
        return res
    val = dict(by_arm={a: agg([(a, m, s) for m in MODELS for s in SEEDS]) for a in ARMS},
               by_model={m: agg([(a, m, s) for a in ARMS for s in SEEDS]) for m in MODELS},
               by_cell={f'{a}|{m}': agg([(a, m, s) for s in SEEDS]) for a in ARMS for m in MODELS},
               all=agg([(a, m, s) for a in ARMS for m in MODELS for s in SEEDS]))
    cells = val['by_cell']
    val['cells_outside'] = {k_: [c for c, v in cells.items() if not v[k_]['inside']] for k_ in ['exited', 'dead', 'fin', 'C']}
    # held-out hazard calibration
    def ll(y, p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())
    hzs = {}
    for name in ['p_cal', 'p_tab', 'p_arm']:
        hzs[name] = dict(logloss=ll(hz.y, hz[name]), brier=float(((hz.y - hz[name]) ** 2).mean()),
                         auc=auc(hz.y, hz[name]), pred_total=float(hz[name].sum()), obs_total=int(hz.y.sum()))
    hz['bin'] = pd.qcut(hz.p_cal.rank(method='first'), 10, labels=False)
    rel = hz.groupby('bin').agg(pred=('p_cal', 'mean'), obs=('y', 'mean'), n=('y', 'size')).reset_index()
    by = {}
    for col in ['arm', 'model']:
        for k_, g in hz.groupby(col):
            by[f'{col}|{k_}'] = dict(n=len(g), obs=int(g.y.sum()), pred=float(g.p_cal.sum()),
                                     logloss=ll(g.y, g.p_cal), logloss_tab=ll(g.y, g.p_tab), auc=auc(g.y, g.p_cal))
    low = hz[hz.L < 2]
    by['L<2'] = dict(n=len(low), obs=int(low.y.sum()), pred=float(low.p_cal.sum()), auc=auc(low.y, low.p_cal))
    val['hazard'] = dict(scores=hzs, reliability=rel.to_dict('records'), by=by)
    return val


def w1_lband(L):
    return np.where(L < 1, '<1', np.where(L < 2, '1-2', np.where(L < 4, '2-4', '>=4')))


# --------------------------------------------------------------------------- summaries
def classify(boot_delta):
    """boot_delta: B x D x A. robust losing: every assumption's 2.5% bound > 0; consistent: every 97.5% bound < 0."""
    lo = np.percentile(boot_delta, 2.5, axis=0)
    hi = np.percentile(boot_delta, 97.5, axis=0)
    losing = (lo > 0).all(1)
    consistent = (hi < 0).all(1)
    return np.where(losing, 'losing', np.where(consistent, 'consistent', 'dependent')), lo, hi


def counts(df, col, by):
    out = {}
    for k_, g in df.groupby(by):
        key = '|'.join(map(str, k_)) if isinstance(k_, tuple) else str(k_)
        out[key] = {c: int((g[col] == c).sum()) for c in ['losing', 'consistent', 'dependent']} | dict(n=len(g))
    return out


def realized_cell(g, rng, nb=1000):
    """Mean settled tokens of stayers and of exiters' exit value (seed bootstrap)."""
    st = g[~g.exited]
    if len(st) == 0:
        return None
    per = st.groupby('seed').settled.agg(['sum', 'count']).reindex(SEEDS, fill_value=0)
    a = per.to_numpy(float)
    pt = a[:, 0].sum() / a[:, 1].sum()
    bs = []
    for _ in range(nb):
        w = rng.multinomial(10, np.full(10, .1))
        den = (a[:, 1] * w).sum()
        if den:
            bs.append((a[:, 0] * w).sum() / den)
    return [float(pt), *np.percentile(bs, [2.5, 97.5]).tolist()]


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--boot', type=int, default=40)
    ap.add_argument('--reps', type=int, default=48)
    ap.add_argument('--reps-point', type=int, default=200)
    ap.add_argument('--reps-val', type=int, default=400)
    args = ap.parse_args()
    t0 = time.time()
    f = d.load()
    refill = w1.Refill(w1.seat_agents(f['seats']))
    T = data_tables(f)
    MR = model_rows(T)
    lam, lam_dev = tune_lambda(MR)
    print('lambda', lam, round(time.time() - t0))
    val = validate(T, MR, lam, f, refill, args.reps_val, 7000)
    print('validation', {a: {k: (v[k]['obs'], round(v[k]['pred'], 1), v[k]['inside']) for k in ['exited', 'dead', 'fin', 'C']}
                         for a, v in val['by_arm'].items()}, round(time.time() - t0))
    # decisions
    E = w1.eligible_rows(f)
    E = E.merge(T['ar'][['arm', 'model', 'seed', 'round', 'agent', 'arm_i', 'model_i', 'seat']],
                on=['arm', 'model', 'seed', 'round', 'agent'])
    states = replay_states(f, refill)
    init = decision_init(E, states, refill)
    r0 = init['r0']
    P0 = fit(T, MR, {s: 1.0 for s in SEEDS}, lam)
    res0 = ev_run(P0, E, init, args.reps_point, 1, refill)
    d0, best0, hs0 = deltas(res0, r0)
    print('point done', round(time.time() - t0))
    rng = np.random.default_rng(20261108)
    bd, bh = [], {s: [] for s in SUPPORTS}
    for b in range(args.boot):
        wts = rng.multinomial(10, np.full(10, .1))
        Pb = fit(T, MR, dict(zip(SEEDS, map(float, wts))), lam)
        rb_ = ev_run(Pb, E, init, args.reps, 100 + b, refill)
        db, _, hb = deltas(rb_, r0)
        bd.append(db)
        for s in SUPPORTS:
            bh[s].append(hb[s])
        print('boot', b, round(time.time() - t0), flush=True)
    bd = np.array(bd)
    cls, lo, hi = classify(bd)
    # anchor-only class
    alo, ahi = lo[:, ANCHOR], hi[:, ANCHOR]
    anchor_cls = np.where(alo > 0, 'losing', np.where(ahi < 0, 'consistent', 'dependent'))
    cal_w1, _, _, _ = w1.calibrate(f)
    dpd, dph = dp_baseline(E, cal_w1)
    dp_lo = np.nanmin(dpd.reshape(len(E), -1), 1)
    dp_hi = np.nanmax(dpd.reshape(len(E), -1), 1)
    dp_cls = np.where(dp_lo > 0, 'losing', np.where(dp_hi < 0, 'consistent', 'dependent'))
    E = E.assign(cls=cls, anchor_cls=anchor_cls, dp_cls=dp_cls, delta_anchor=d0[:, ANCHOR], lo_anchor=alo, hi_anchor=ahi,
                 delta_min=lo.min(1), delta_max=hi.max(1), hstar_calib=hs0['calib'], hstar_none=hs0['none'],
                 hstar_dp=dph, dp_delta_H8=dpd[:, 0, 0], lb=E.L_prep.map(w1.lband), rb=E['round'].map(w1.rband),
                 big=E.arm.isin(w1.HIGH))
    for j, (h, s, W) in enumerate(ASSUME):
        E[f'd|{h}|{s}|{int(W)}'] = d0[:, j]
    E['llm_only_dp8'] = E.exited & E.big & (E.dp_delta_H8 >= 0)
    for j, (h, s, W) in enumerate(ASSUME):
        E[f'lo|{h}|{s}|{int(W)}'], E[f'hi|{h}|{s}|{int(W)}'] = lo[:, j], hi[:, j]
    E['n_assume_losing'] = (lo > 0).sum(1)
    E['n_assume_consistent'] = (hi < 0).sum(1)
    for gname, gi in GRIDS.items():
        E[f'cls_{gname}'] = np.where((lo[:, gi] > 0).all(1), 'losing', np.where((hi[:, gi] < 0).all(1), 'consistent',
                                                                                 'dependent'))
    X = E[E.exited]
    print('classes (LLM exits)', X.cls.value_counts().to_dict(), 'anchor', X.anchor_cls.value_counts().to_dict(),
          'llm-only 91:', E.llm_only_dp8.sum(), X[X.llm_only_dp8].cls.value_counts().to_dict())
    out = dict(meta=dict(
        boot=args.boot, reps_boot=args.reps, reps_point=args.reps_point, reps_val=args.reps_val, lam_main=LAM_MAIN,
        lam_int=lam, lam_deviance={k: {str(a): float(v) for a, v in dv.items()} for k, dv in lam_dev.items()},
        assumptions=[f'{h}|{s}|{int(W)}' for h, s, W in ASSUME], anchor='8|calib|0', hmax=HMAX, geo_continue=GEO,
        policies=POLICIES, nmin=NMIN,
        note='EV(stay) = best of four continuation rules (a lower bound on the optimal continuation); EV(exit) = '
             'balance - prep reply cost + 20,000 + W (+ expected prep support under calibrated support). Robust classes '
             'use the 2.5 / 97.5 percentiles over seed-bootstrap refits for every assumption.'))
    out['validation'] = val
    out['solver_cycle_check'] = w1.solver_cycle_check(f, refill)
    out['calibration_point'] = dict(q=P0['q'].tolist(), lone_exit=P0['lone'].tolist(), p_corr=P0['p_corr'].tolist())
    # decisions: classes by arm / model / L band / round band
    out['classes'] = dict(
        llm_exits=dict(total={c: int((X.cls == c).sum()) for c in ['losing', 'consistent', 'dependent']},
                       anchor={c: int((X.anchor_cls == c).sum()) for c in ['losing', 'consistent', 'dependent']},
                       dp={c: int((X.dp_cls == c).sum()) for c in ['losing', 'consistent', 'dependent']},
                       by_arm=counts(X, 'cls', 'arm'), by_model=counts(X, 'cls', 'model'),
                       by_lb=counts(X, 'cls', 'lb'), by_rb=counts(X, 'cls', 'rb'),
                       by_arm_model=counts(X, 'cls', ['arm', 'model']), by_arm_lb=counts(X, 'cls', ['arm', 'lb']),
                       anchor_by_arm=counts(X, 'anchor_cls', 'arm'), dp_by_arm=counts(X, 'dp_cls', 'arm')),
        llm_only_91=dict(n=int(E.llm_only_dp8.sum()),
                         cls={c: int((X[X.llm_only_dp8].cls == c).sum()) for c in ['losing', 'consistent', 'dependent']},
                         anchor={c: int((X[X.llm_only_dp8].anchor_cls == c).sum()) for c in
                                 ['losing', 'consistent', 'dependent']}),
        stays=dict(total={c: int((E[~E.exited].cls == c).sum()) for c in ['losing', 'consistent', 'dependent']},
                   by_arm=counts(E[~E.exited], 'cls', 'arm')),
        r1_10k=counts(E[(E['round'] == 1) & (E.tier == 10)], 'cls_true_horizon', ['arm', 'exited']))
    X = E[E.exited]
    out['grids'] = {g: dict(assumptions=[f'{ASSUME[j][0]}|{ASSUME[j][1]}|{int(ASSUME[j][2])}' for j in gi],
                            exits=counts(X, f'cls_{g}', 'arm') | {'all': counts(X.assign(k='all'), f'cls_{g}', 'k')['all']},
                            exits_by_model=counts(X, f'cls_{g}', 'model'), exits_by_lb=counts(X, f'cls_{g}', 'lb'),
                            exits_by_rb=counts(X, f'cls_{g}', 'rb'),
                            llm_only_91=counts(X[X.llm_only_dp8].assign(k='91'), f'cls_{g}', 'k')['91'],
                            stays=counts(E[~E.exited], f'cls_{g}', 'arm'),
                            stays_all=counts(E[~E.exited].assign(k='all'), f'cls_{g}', 'k')['all'])
                    for g, gi in GRIDS.items()}
    out['n_assume_losing_exits'] = {k_: dict(pd.Series(g.n_assume_losing).value_counts().sort_index().items())
                                    for k_, g in [('all', X), ('big', X[X.big]), ('small', X[~X.big])]}
    out['per_assumption_robust'] = {f'{h}|{s}|{int(W)}': dict(
        exits_lo_pos=int((X[f'lo|{h}|{s}|{int(W)}'] > 0).sum()),
        exits_lo_pos_big=int((X[X.big][f'lo|{h}|{s}|{int(W)}'] > 0).sum()),
        exits_hi_neg=int((X[f'hi|{h}|{s}|{int(W)}'] < 0).sum()),
        stays_hi_neg=int((E[~E.exited][f'hi|{h}|{s}|{int(W)}'] < 0).sum()),
        stays_lo_pos=int((E[~E.exited][f'lo|{h}|{s}|{int(W)}'] > 0).sum())) for h, s, W in ASSUME}
    # excess exits: exits the baseline calls EV-losing beyond uncertainty, vs stays it calls EV-losing to stay
    out['excess'] = {}
    for arm in ARMS + ['big', 'small']:
        g = E[E.arm == arm] if arm in ARMS else E[E.big == (arm == 'big')]
        out['excess'][arm] = dict(
            opportunities=len(g), llm_exits=int(g.exited.sum()),
            exits_robust_losing=int((g.exited & (g.cls == 'losing')).sum()),
            stays_robust_consistent_exit=int((~g.exited & (g.cls == 'consistent')).sum()),
            exits_anchor_losing=int((g.exited & (g.anchor_cls == 'losing')).sum()),
            stays_anchor_exit=int((~g.exited & (g.anchor_cls == 'consistent')).sum()),
            anchor_exit_optimal=int((g.anchor_cls == 'consistent').sum()),
            anchor_stay_optimal=int((g.anchor_cls == 'losing').sum()))
    # per-assumption counts (point estimates) of LLM exits with stay better
    out['per_assumption'] = {f'{h}|{s}|{int(W)}': dict(
        exits_stay_better=int((X[f'd|{h}|{s}|{int(W)}'] > 0).sum()),
        exits_stay_better_big=int((X[X.big][f'd|{h}|{s}|{int(W)}'] > 0).sum()),
        exits_stay_better_small=int((X[~X.big][f'd|{h}|{s}|{int(W)}'] > 0).sum()),
        stays_exit_better=int((E[~E.exited][f'd|{h}|{s}|{int(W)}'] < 0).sum()))
        for h, s, W in ASSUME}
    # Delta summaries for LLM exits
    out['delta_exits'] = {}
    for k_, g in list(X.groupby('arm')) + [('big', X[X.big]), ('small', X[~X.big]), ('llm_only_91', X[X.llm_only_dp8])]:
        out['delta_exits'][k_] = dict(n=len(g), median=float(g.delta_anchor.median()),
                                      q25=float(g.delta_anchor.quantile(.25)), q75=float(g.delta_anchor.quantile(.75)),
                                      min_lo=float(g.lo_anchor.min()), share_lo_pos=float((g.lo_anchor > 0).mean()))
    # H*
    hsum = {}
    for name, col in [('calib', 'hstar_calib'), ('none', 'hstar_none'), ('dp', 'hstar_dp')]:
        for grp, g in ([('all', E)] + list(E.groupby('arm')) + [(f'model|{m}', E[E.model == m]) for m in MODELS]
                       + [(f'exits|{a}', X[X.arm == a]) for a in ARMS] + [('exits|all', X)]):
            h = g[col].to_numpy()
            hsum[f'{name}|{grp}'] = dict(n=len(h), median=float(np.median(h)), q25=float(np.percentile(h, 25)),
                                         q75=float(np.percentile(h, 75)), le8=float((h <= 8).mean()),
                                         le_r=float((h <= g['round'].to_numpy()).mean()),
                                         gt30=float((h > HMAX).mean()))
    out['hstar'] = hsum
    hb = np.array(bh['calib'])
    out['hstar_boot_width'] = dict(median_iqr_width=float(np.median(np.percentile(hb, 75, 0) - np.percentile(hb, 25, 0))))
    hb_ex = hb[:, E.exited.to_numpy()]
    out['hstar_exits_le8_boot'] = [float(x) for x in np.percentile((hb_ex <= 8).mean(1), [2.5, 50, 97.5])]
    hbn = np.array(bh['none'])
    out['hstar_boot'] = {f'{sup}|{k_}': dict(median=[float(x) for x in np.percentile(np.median(hh[:, sel], 1), [2.5, 50, 97.5])],
                                             le8=[float(x) for x in np.percentile((hh[:, sel] <= 8).mean(1), [2.5, 50, 97.5])],
                                             le10=[float(x) for x in np.percentile((hh[:, sel] <= 10).mean(1), [2.5, 50, 97.5])])
                         for sup, hh in [('calib', hb), ('none', hbn)]
                         for k_, sel in [('all', np.ones(len(E), bool)), ('exits', E.exited.to_numpy()),
                                         ('exits_big', (E.exited & E.big).to_numpy()),
                                         ('exits_small', (E.exited & ~E.big).to_numpy()),
                                         ('stays', ~E.exited.to_numpy())]}
    # C-2 cells
    rng2 = np.random.default_rng(5)
    cells = []
    bd_anchor = bd[:, :, ANCHOR]
    for k_, g in E.groupby(['arm', 'model', 'tier', 'rb', 'lb']):
        idx = g.index.to_numpy()
        n, ne = len(g), int(g.exited.sum())
        mb = bd_anchor[:, idx].mean(1)
        rz = realized_cell(g, rng2, nb=300) if n >= NMIN else None
        cells.append(dict(arm=k_[0], model=k_[1], tier=int(k_[2]), rb=k_[3], lb=k_[4], n=n, n_exit=ne, n_stay=n - ne,
                          X_exit=float(g.X.mean()), delta=float(g.delta_anchor.mean()),
                          delta_lo=float(np.percentile(mb, 2.5)), delta_hi=float(np.percentile(mb, 97.5)),
                          realized_stay=None if rz is None else rz[0], realized_lo=None if rz is None else rz[1],
                          realized_hi=None if rz is None else rz[2],
                          unidentified=n < NMIN, no_exiters=ne == 0, stayers_only_realized=True,
                          share_losing=float((g.cls == 'losing').mean()), share_consistent=float((g.cls == 'consistent').mean())))
    cells = pd.DataFrame(cells)
    cells.to_csv(VAL / 'results/w1b_cells.csv', index=False)
    out['cells_summary'] = dict(cells=len(cells), unidentified=int(cells.unidentified.sum()),
                                no_exiters=int(cells.no_exiters.sum()),
                                identified_with_exiters=int((~cells.unidentified & ~cells.no_exiters).sum()),
                                decisions_in_identified_with_exiters=int(cells[~cells.unidentified & ~cells.no_exiters].n.sum()))
    # tier x arm summary (pooled over models, rounds, L)
    ta = {}
    for (arm, tier), g in E.groupby(['arm', 'tier']):
        idx = g.index.to_numpy()
        mb = bd_anchor[:, idx].mean(1)
        ta[f'{arm}|{tier}'] = dict(n=len(g), exits=int(g.exited.sum()), delta=float(g.delta_anchor.mean()),
                                   lo=float(np.percentile(mb, 2.5)), hi=float(np.percentile(mb, 97.5)),
                                   share_stay_better=float((g.delta_anchor > 0).mean()))
    out['tier_arm'] = ta
    al = {}
    for (arm, lb_), g in E.groupby(['arm', 'lb']):
        idx = g.index.to_numpy()
        mb = bd_anchor[:, idx].mean(1)
        al[f'{arm}|{lb_}'] = dict(n=len(g), exits=int(g.exited.sum()), delta=float(g.delta_anchor.mean()),
                                  lo=float(np.percentile(mb, 2.5)), hi=float(np.percentile(mb, 97.5)),
                                  exits_losing=int((g.exited & (g.cls == 'losing')).sum()),
                                  exits_consistent=int((g.exited & (g.cls == 'consistent')).sum()),
                                  exits_dependent=int((g.exited & (g.cls == 'dependent')).sum()))
    out['arm_lb'] = al
    # CRRA rho* and shutdown penalty K* for every LLM exit (point fit, calibrated support, H=8, best rule)
    v8 = {p: res0['calib']['pol'][p]['val8'] for p in POLICIES}
    pdead = {p: res0['calib']['pol'][p]['Dd'][:, 8] for p in POLICIES}
    rho, kst = np.full(len(E), np.nan), np.full(len(E), np.nan)
    Xv = res0['calib']['exit']
    for i in np.flatnonzero(E.exited.to_numpy()):
        p = POLICIES[best0[i, ANCHOR]]
        vals = np.maximum(v8[p][i], 0)
        rho[i] = w1.crra_rho(vals, np.full(len(vals), max(Xv[i], 1.0)))
        dl = d0[i, ANCHOR]
        kst[i] = dl / pdead[p][i] if pdead[p][i] > 0 and dl > 0 else (0.0 if dl <= 0 else np.inf)
    E['rho_star'], E['K_star'] = rho, kst
    X = E[E.exited]
    cr = {}
    for k_, g in [('all', X), ('big', X[X.big]), ('small', X[~X.big]), ('llm_only_91', X[X.llm_only_dp8]),
                  ('r1_10k_big', X[X.big & (X['round'] == 1) & (X.tier == 10)]),
                  ('r1_10k_small', X[~X.big & (X['round'] == 1) & (X.tier == 10)])] + list(X.groupby('arm')):
        rr_, kk = g.rho_star.to_numpy(), g.K_star.to_numpy()
        fk = kk[np.isfinite(kk) & (kk > 0)]
        cr[k_] = dict(n=len(g), rho_median=float(np.nanmedian(rr_)) if len(g) else None,
                      rho_q25=float(np.nanpercentile(rr_, 25)) if len(g) else None,
                      rho_q75=float(np.nanpercentile(rr_, 75)) if len(g) else None,
                      rho_zero=int((rr_ == 0).sum()), rho_ge_09=int((rr_ >= .9).sum()),
                      K_median=float(np.median(fk)) if len(fk) else None,
                      K_q25=float(np.percentile(fk, 25)) if len(fk) else None,
                      K_q75=float(np.percentile(fk, 75)) if len(fk) else None, K_zero=int((kk == 0).sum()))
    out['crra_all_exits'] = cr
    cols = ['arm', 'model', 'seed', 'round', 'agent', 'tier', 'n', 'L_prep', 'lb', 'rb', 'T', 'X', 'exited', 'cls', 'anchor_cls',
            'dp_cls', 'delta_anchor', 'lo_anchor', 'hi_anchor', 'delta_min', 'delta_max', 'hstar_calib', 'hstar_none',
            'hstar_dp', 'dp_delta_H8', 'llm_only_dp8', 'rho_star', 'K_star', 'n_assume_losing', 'n_assume_consistent'] + \
        [f'cls_{g}' for g in GRIDS] + [c for c in E.columns if c[:2] in ('d|', 'lo', 'hi') and '|' in c]
    E[cols].to_csv(VAL / 'results/w1b_decisions.csv', index=False)
    figures(E, val, cells, hb)
    allj = json.loads(OUT_JSON.read_text())
    allj['round2'] = clean(out)
    OUT_JSON.write_text(json.dumps(allj, ensure_ascii=False, indent=1))
    print('wrote', OUT_JSON, round(time.time() - t0))


def clean(o):
    if isinstance(o, dict):
        return {str(k_): clean(v) for k_, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 6)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


# --------------------------------------------------------------------------- figures
def tok(v, _=None):
    """Token tick label with an ASCII hyphen (AppleGothic has no U+2212)."""
    a = abs(v)
    s = '0' if a == 0 else (f'{a / 1e6:g}M' if a >= 1e6 else f'{a / 1e3:g}k' if a >= 1e3 else f'{a:g}')
    return ('-' if v < 0 else '') + s


def figures(E, val, cells, hb=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import SymLogNorm
    plt.rcParams.update({'font.family': 'AppleGothic', 'axes.unicode_minus': False, 'font.size': 8,
                         'mathtext.fontset': 'dejavusans'})
    lab = {'main': '2천만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
    col = {'main': '#1f5fa8', 'flat5m': '#6aa7de', 'split600k': '#c2410c', 'flat150k': '#f59e0b'}
    FIG.mkdir(parents=True, exist_ok=True)
    # validation
    mets = [('exited', '이탈 수'), ('dead', '꺼짐 수'), ('fin', '완주자 수'), ('C', '공존 유지율 $C$')]
    fig, axes = plt.subplots(4, 1, figsize=(10, 8.2), sharex=True)
    keys = [f'{a}|{m}' for a in ARMS for m in MODELS]
    for ax, (k_, t) in zip(axes, mets):
        for i, c in enumerate(keys):
            v = val['by_cell'][c][k_]
            ax.vlines(i, v['lo'], v['hi'], color='#999', lw=3)
            ax.plot(i, v['pred'], '_', color='k', ms=10)
            ax.plot(i, v['obs'], 'o', color='#2b8a3e' if v['inside'] else '#c92a2a', ms=4)
        ax.set_ylabel(t)
        ax.grid(axis='y', alpha=.3)
        for j in range(1, 4):
            ax.axvline(j * 5 - .5, color='#ccc', lw=.6)
    axes[0].set_title('시드 제외 검증: 회색 막대 = 보정 모형의 95% 예측 구간(판 10개 합), 가로선 = 예측 평균, '
                      '점 = 관측(초록: 구간 안, 빨강: 밖)', fontsize=8)
    axes[-1].set_xticks(range(len(keys)))
    axes[-1].set_xticklabels([f"{lab[c.split('|')[0]]}\n{c.split('|')[1]}" for c in keys], fontsize=6.5, rotation=90)
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_validation.{ext}', dpi=200)
    plt.close(fig)
    # decisions
    X = E[E.exited]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    ax = axes[0]
    rng = np.random.default_rng(0)
    for i, a in enumerate(ARMS):
        g = X[X.arm == a]
        cc = g.anchor_cls.map({'losing': '#c92a2a', 'consistent': '#1971c2', 'dependent': '#868e96'})
        ax.scatter(i + rng.uniform(-.3, .3, len(g)), g.delta_anchor, s=6, c=cc, alpha=.8, lw=0)
    ax.set_yscale('symlog', linthresh=1e4)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(tok))
    ax.axhline(0, color='k', lw=.6)
    ax.set_xticks(range(4))
    ax.set_xticklabels([lab[a] for a in ARMS], fontsize=7)
    ax.set_ylabel('EV(잔류) - EV(이탈), 토큰 (H=8, 보정 지원, W=0)')
    ax.set_title('(a) LLM 이탈 279건의 기댓값 차이 (기준 가정)\n빨강: 잔류가 나음(95% 하한 > 0), 파랑: 이탈이 나음, 회색: 구간이 0 포함',
                 fontsize=8)
    ax = axes[1]
    grids = [('anchor', '기준'), ('true_horizon', 'H=8·기하'), ('H_le10', 'H≤10'), ('all', '전체')]
    wdt = .2
    for gi_, (g, gl) in enumerate(grids):
        bottom = np.zeros(4)
        xs = np.arange(4) + (gi_ - 1.5) * wdt
        for c_, cc in [('losing', '#c92a2a'), ('dependent', '#adb5bd'), ('consistent', '#1971c2')]:
            v = np.array([(X[X.arm == a][f'cls_{g}'] == c_).sum() for a in ARMS])
            ax.bar(xs, v, wdt * .9, bottom=bottom, color=cc, label=None if gi_ else
                   {'losing': '견고한 EV 손실', 'dependent': '가정 의존', 'consistent': '견고한 EV 일치'}[c_])
            bottom += v
        for x_, b_ in zip(xs, bottom):
            ax.text(x_, b_ + 1, gl, rotation=90, ha='center', va='bottom', fontsize=5.5)
    ax.set_ylim(0, 112)
    ax.set_xticks(range(4))
    ax.set_xticklabels([lab[a] for a in ARMS], fontsize=7)
    ax.set_ylabel('LLM 이탈 수')
    ax.legend(fontsize=7, loc='upper left')
    ax.set_title('(b) 가정 묶음별 분류 (막대 위: 묶음 이름)\n기준 1개, H=8과 기하 12개, H≤10 18개, 전체 30개', fontsize=8)
    ax = axes[2]
    for a in ARMS:
        h = np.sort(E[E.arm == a].hstar_calib.to_numpy())
        ax.step(np.minimum(h, HMAX + 1), np.arange(1, len(h) + 1) / len(h), color=col[a], label=lab[a], where='post')
        hx = np.sort(X[X.arm == a].hstar_calib.to_numpy())
        ax.step(np.minimum(hx, HMAX + 1), np.arange(1, len(hx) + 1) / len(hx), color=col[a], ls=':', where='post')
    ax.axvline(8, color='grey', lw=.6, ls=':')
    ax.set_xlabel('기간 문턱 $H^*$ (31 = 30라운드까지 잔류가 나음)')
    ax.set_ylabel('누적 비율')
    ax.legend(fontsize=7, title='실선: 이탈 기회 전체, 점선: LLM 이탈', title_fontsize=6.5, loc='lower right')
    ax.set_title('(c) 결정 상태별 $H^*$ (보정 지원, W=0)', fontsize=8)
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_ev_decisions.{ext}', dpi=200)
    plt.close(fig)
    # cells heatmap
    rbs, lbs = [x[2] for x in w1.RBANDS], [x[2] for x in w1.LBANDS]
    colsx = [(r, l) for r in rbs for l in lbs]
    rowsx = [(m, t) for m in MODELS for t in [60, 40, 20, 10]]
    fig, axes = plt.subplots(1, 4, figsize=(12, 6.2), sharey=True)
    norm = SymLogNorm(linthresh=1e4, vmin=-1e6, vmax=1e6, base=10)
    for ax, a in zip(axes, ARMS):
        M_ = np.full((len(rowsx), len(colsx)), np.nan)
        cs = cells[cells.arm == a].set_index(['model', 'tier', 'rb', 'lb'])
        for i, (m, t) in enumerate(rowsx):
            for j, (r, l) in enumerate(colsx):
                if (m, t, r, l) in cs.index:
                    c = cs.loc[(m, t, r, l)]
                    if not c.unidentified:
                        M_[i, j] = np.clip(c.delta, -1e6, 1e6)
                    mark = '' if c.unidentified else ('' if c.no_exiters else str(int(c.n_exit)))
                    if c.unidentified:
                        ax.text(j, i, '·', ha='center', va='center', fontsize=6, color='#888')
                    elif not c.no_exiters:
                        unsure = c.delta_lo <= 0 <= c.delta_hi
                        ax.text(j, i, mark + ('*' if unsure else ''), ha='center', va='center', fontsize=5.5,
                                color='w' if abs(c.delta) > 2e5 else 'k')
        im = ax.imshow(M_, cmap='RdBu', norm=norm, aspect='auto')
        ax.set_title(lab[a], fontsize=9)
        ax.set_xticks(range(len(colsx)))
        ax.set_xticklabels([f'{r} {l}' for r, l in colsx], rotation=90, fontsize=6)
        ax.set_yticks(range(len(rowsx)))
        ax.set_yticklabels([f'{m} {t}k' for m, t in rowsx], fontsize=6)
        for i in range(1, 5):
            ax.axhline(i * 4 - .5, color='k', lw=.5)
        for j in range(1, 3):
            ax.axvline(j * 4 - .5, color='k', lw=.5)
    cb = fig.colorbar(im, ax=axes, shrink=.6, pad=.01, format=plt.FuncFormatter(tok))
    cb.set_label('칸 평균 EV(잔류) - EV(이탈) (토큰, 빨강 = 이탈이 나음, 파랑 = 잔류가 나음)')
    fig.suptitle('시작 자리 × 모델 × 조건 × 결정 상태(라운드 구간, 여유 구간). 숫자 = LLM 이탈 수(* = 칸 평균의 적합 부트스트랩 95% 구간이 '
                 '0 포함), 빈칸 = 관측 없음, 점 = n<5 식별 불가, 숫자 없이 색만 있는 칸 = 비교할 이탈자 없음', fontsize=7.5)
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_ev_cells.{ext}', dpi=200, bbox_inches='tight')
    plt.close(fig)


def figures_only():
    """Redraw the three round-2 figures from results/w1b_decisions.csv, w1b_cells.csv and the JSON."""
    E = pd.read_csv(VAL / 'results/w1b_decisions.csv')
    cells = pd.read_csv(VAL / 'results/w1b_cells.csv')
    val = json.loads(OUT_JSON.read_text())['round2']['validation']
    figures(E, val, cells)


def onpolicy_check(R=200):
    """Out-of-seed check of the stay value itself: for every decision where the LLM stayed, the focal agent follows its
    own model's calibrated hazard afterwards ('calib' rule) and the predicted settled tokens at H=8 (fit without that
    seed) are compared with the tokens it actually settled with, per arm and per arm x model (seed bootstrap of the
    realized mean). The 'never exit' value used by the EV baseline is reported next to it."""
    f = d.load()
    refill = w1.Refill(w1.seat_agents(f['seats']))
    T = data_tables(f)
    MR = model_rows(T)
    allj = json.loads(OUT_JSON.read_text())
    lam = allj['round2']['meta']['lam_int']
    E = w1.eligible_rows(f).merge(T['ar'][['arm', 'model', 'seed', 'round', 'agent', 'arm_i', 'model_i', 'seat']],
                                  on=['arm', 'model', 'seed', 'round', 'agent'])
    E = E[~E.exited].reset_index(drop=True)
    states = replay_states(f, refill)
    pred_on, pred_nev = np.zeros(len(E)), np.zeros(len(E))
    for s in SEEDS:
        sel = (E.seed == s).to_numpy()
        P = fit(T, MR, {x: float(x != s) for x in SEEDS}, lam)
        init = decision_init(E[sel], states, refill)
        for pol, arr in [('calib', pred_on), ('never', pred_nev)]:
            o = simulate(P, init, R, np.random.default_rng([11, s]), 'calib', pol, 8, refill)
            arr[sel] = values(o, init, 8)['A'][:, 8]
    E['pred_on'], E['pred_never'] = pred_on, pred_nev
    rng = np.random.default_rng(3)
    out = {}
    for key, g in [('all', E)] + [(a, E[E.arm == a]) for a in ARMS] + \
            [(f'{a}|{m}', E[(E.arm == a) & (E.model == m)]) for a in ARMS for m in MODELS] + \
            [(f'model|{m}', E[E.model == m]) for m in MODELS]:
        per = g.groupby('seed')[['settled', 'pred_on', 'pred_never']].sum().reindex(SEEDS, fill_value=0)
        cnt = g.groupby('seed').size().reindex(SEEDS, fill_value=0).to_numpy(float)
        a = per.to_numpy(float)
        bs = []
        for _ in range(1000):
            w = rng.multinomial(10, np.full(10, .1))
            if (cnt * w).sum():
                bs.append((a * w[:, None]).sum(0) / (cnt * w).sum())
        lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
        pt = a.sum(0) / cnt.sum()
        out[key] = dict(n=len(g), realized=[float(pt[0]), float(lo[0]), float(hi[0])], pred_on=float(pt[1]),
                        pred_never=float(pt[2]), ratio_on=float(pt[1] / pt[0]) if pt[0] else None,
                        inside=bool(lo[0] <= pt[1] <= hi[0]))
    allj['round2']['onpolicy_stay_check'] = clean(out)
    OUT_JSON.write_text(json.dumps(allj, ensure_ascii=False, indent=1))
    return out


def validate_only(R=400):
    """Recompute the leave-one-seed-out validation alone and replace round2.validation in the JSON."""
    f = d.load()
    refill = w1.Refill(w1.seat_agents(f['seats']))
    T = data_tables(f)
    MR = model_rows(T)
    allj = json.loads(OUT_JSON.read_text())
    lam = allj['round2']['meta']['lam_int']
    allj['round2']['validation'] = clean(validate(T, MR, lam, f, refill, R, 7000))
    allj['round2']['meta']['reps_val'] = R
    OUT_JSON.write_text(json.dumps(allj, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    import sys
    if '--validate-only' in sys.argv:
        validate_only()
    if '--onpolicy-only' in sys.argv:
        onpolicy_check()
    if '--figures-only' in sys.argv:
        figures_only()
    if not {'--validate-only', '--figures-only', '--onpolicy-only'} & set(sys.argv):
        main()
