"""W1c (review round 3, item (a)-EV): checks of the round-2 calibrated EV baseline (w1b_calibrated.py) on existing data.

Answers Astra round 2, row (a)-EV and A-1, C-2, Q1, Tier1-1, structure-1:

  1. leave-one-seed-out (LOSO) calibration by model x arm x L band (L<1, 1-2, >=2): for every logged decision where the
     LLM stayed, the model fitted without that seed simulates forward from the logged state (the focal agent stays now,
     then follows its model's calibrated hazard; H=8) and predicts support success (received support in the decision
     round and is in at the next round with L>=1), later exit, shutdown, finishing and settled tokens at H=8. The
     immediate EXIT hazard is checked on all decisions. Each cell reports observed and predicted means and a seed-cluster
     bootstrap 95% interval of observed - predicted (paired by decision); cells whose interval excludes 0 are flagged;
  2. convergence: B seed-bootstrap refits (default 200) with R simulations per decision (default 1,600, nested prefixes
     50..1,600 of the same paths) for the 279 LLM exits, and B_all refits x R_all for all 3,588 decisions; classification
     counts (anchor H=8 / calibrated support / W=0; the 12-assumption set H in {8, geo}; the 30-assumption grid) and H*
     medians as a function of B and R, Monte-Carlo SE from a bootstrap over refits; point fit with R_point paths;
  3. baseline sensitivity for the LLM exits: (i) the calibrated baseline, (ii-a) behaviour (EXIT / support logits) pooled
     across models, (ii-b) shutdowns recalibrated to the observed count per arm (a simulated shutdown is cancelled with a
     per-arm probability, the agent keeps the observed post-rescue surplus; the probability is tuned on in-sample game
     simulations), (iii) an information-restricted baseline: peers' exact balances replaced by logged balances from other
     games of the same arm, round and headcount that respect the agent's rank order, future solver order unknown,
     horizon unknown (geometric anchor);
  4. C-2: stayers' realised settled tokens (seed bootstrap) and their LOSO prediction, separated from exiters' realised
     exit value and their model counterfactual EV(stay) (fit bootstrap), by arm x L band;
  5. H*: point-fit vs bootstrap medians as R grows (first-crossing statistics are biased down by Monte-Carlo noise);
     K* (shutdown penalty) for the 5M fixed arm, finite-only and including infinite values.

Data (no model calls): validation_data.py tidy tables (v33 public cohort + v33ab prize ablation, 200 games), as in w1b.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w1c_ev_check.py [--boot 200 --reps 1600 --boot-all 40
    --reps-all 100 --boot-alt 60 --reps-alt 400 --reps-point 800 --reps-point-all 400 --workers 10]
(stages: --stage calib | exits | alldec | alt | summary; 'all' runs them in order; ~1 h on 10 cores)
Writes results/w1c_ev_check.json, results/w1c_calib_cells.csv, results/w1c_c2_table.csv, results/w1c_decisions.csv,
figures/w1_ev_convergence.*, figures/w1_ev_calib_cells.*, figures/w1_ev_sensitivity.*, and redraws the round-2
figures/w1_ev_decisions.* with the converged classes (w1_validation / w1_ev_cells are redrawn unchanged). Intermediate
results/w1c_calib_{pred,hazard}.csv, w1c_calib_paths.npz, w1c_gamecheck.json and result/2026-11-08/icml_appendix/cache/w1c_arrays.npz
(~60 MB, outside paper/ so it stays out of the Overleaf mirror).
"""
import argparse
import json
import multiprocessing as mp
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')

import validation_data as d  # noqa: E402
import w1_ev_baseline as w1  # noqa: E402
import w1b_calibrated as c  # noqa: E402

VAL = c.VAL
OUT = VAL / 'results/w1c_ev_check.json'
NPZ = VAL.parents[2] / 'result/2026-11-08/icml_appendix/cache/w1c_arrays.npz'  # ~60 MB, kept out of paper/
FIG = c.FIG
ARMS, MODELS, SEEDS = c.ARMS, c.MODELS, c.SEEDS
ASSUME, ANCHOR, GRIDS = c.ASSUME, c.ANCHOR, c.GRIDS
GEO_ANCHOR = ASSUME.index(('geo', 'calib', 0.0))
SETS = {'anchor': [ANCHOR], 'geo_anchor': [GEO_ANCHOR]} | {k: v for k, v in GRIDS.items() if k != 'anchor'}
LB3 = ['<1', '1-2', '>=2']


def lb3(L):
    return np.where(L < 1, '<1', np.where(L < 2, '1-2', '>=2'))


# --------------------------------------------------------------------------- simulator with two hooks
def simulate_x(P, init, R, rng, support, policy, hmax, refill, games=False, save=None, track=False, conserve=False):
    """w1b_calibrated.simulate plus (a) save: per-arm probability that a simulated shutdown is cancelled (the agent keeps
    an observed post-rescue surplus, plus the per-head charge if it is cancelled before the charge), (b) track: support
    the focal agent receives in its first round. With save=None the paths equal w1b_calibrated.simulate exactly.
    conserve=True (round 4, w1d): a cancelled shutdown is funded by the other agents still in (richest first, each
    keeping more than one per-head charge, the focal agent included); if they cannot fund it, the shutdown stands."""
    CHARGE, BONUS, LOWBAL = c.CHARGE, c.BONUS, c.LOWBAL
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
    frecv = np.zeros(N)
    fin = np.ones(N, bool)
    surplus = P['a_need'] if len(P['a_need']) else np.array([500.0])

    def kill(B, S, mask, a_, fee, before_charge):
        if save is not None and mask.any():
            sv = mask & (rng.random(mask.shape) < save[a_][:, None])
            if sv.any():
                k = rng.integers(0, len(surplus), sv.sum())
                extra = np.broadcast_to(fee[:, None], mask.shape)[sv] if before_charge else 0.0
                if conserve:
                    tgt = np.zeros(mask.shape)
                    tgt[sv] = np.maximum(surplus[k], 1.0) + extra
                    rows_ = np.arange(len(B))
                    for j in range(4):
                        cand = sv[:, j]
                        if not cand.any():
                            continue
                        need = np.where(cand, tgt[:, j] - np.maximum(B[:, j], 0), 0.0)
                        don = (S == 0) & ~mask & (np.arange(4) != j)[None, :]
                        cap = np.where(don, np.maximum(B - fee[:, None] - 1, 0), 0.0)
                        ok = cand & (cap.sum(1) >= need)
                        left = np.where(ok, need, 0.0)
                        for dn in np.argsort(-np.where(don, B, -np.inf), axis=1, kind='stable').T:
                            g_ = np.minimum(left, cap[rows_, dn])
                            B[rows_, dn] -= g_
                            cap[rows_, dn] -= g_
                            left -= g_
                        B[ok, j] = tgt[ok, j]
                        sv[:, j] = ok
                else:
                    B[sv] = np.maximum(surplus[k], 1.0) + extra
                mask = mask & ~sv
        B[mask], S[mask] = 0, 2
        return mask

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
        fs = np.maximum(f_, 0)
        trk = track & first & (f_ >= 0)
        z = dict(arm=a_[:, None], model=m_[:, None], L=L0, r=t, tier=c.SEAT_TIER[None, :], n=n[:, None], sol=issol,
                 needy=np.zeros_like(issol))
        multi = (n > 1)[:, None]
        donors = part & ~fm
        if support == 'calib':
            pg = c.predict(c.GIFT_TERMS, P['gi'], z) * (part & multi)
            coin = rng.random(pg.shape) < pg
            amt = P['a_prep'].draw(rng, issol.astype(int) * 3 + c.lowc(L0)) * fee[:, None]
            b_before = B.copy()
            c.give(B, part & multi, coin, amt, donors, keep=fee)
            given[ix] += np.maximum(B - b_before, 0).sum(1)
            if track:
                frecv[ix] += np.where(trk, np.maximum(B - b_before, 0)[rows, fs], 0.0)
        elig = part & ~issol & multi
        lone = part & ~multi
        pe = np.where(elig, c.predict(c.EXIT_TERMS, P['ex'], z), 0.0)
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
        cc = P['c_prep'].draw(rng, np.where(lowb, 15, m_[:, None] * 3 + c.lowc(L0)))
        cc = np.where(lowb, cc * B, cc)
        B = np.where(part, B - cc, B)
        kill(B, S, part & (B <= 0), a_, fee, True)
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
        kill(B, S, vd, a_, fee, True)
        inn = S == 0
        lowb = B < LOWBAL
        cr = P['c_resc'].draw(rng, np.where(lowb, 20, m_[:, None] * 4 + wrong[:, None] * 2 + (B / fee[:, None] < 2)))
        cr = np.where(lowb, cr * B, cr)
        B = np.where(inn, B - cr, B)
        kill(B, S, inn & (B <= 0), a_, fee, True)
        inn = S == 0
        if support == 'calib':
            pre = B.copy()
            needy = pre <= fee[:, None]
            Lr = (pre - fee[:, None]) / fee[:, None]
            zr = dict(z, L=Lr, needy=needy)
            pw = c.predict(c.RESC_TERMS, P['rw'], zr)
            pc = P['p_corr'][c.lowc(pre / fee[:, None])]
            p = np.where(wrong[:, None], pw, pc) * (inn & multi)
            coin = rng.random(p.shape) < p
            u = rng.integers(0, 1 << 30, p.shape)
            a_need = (fee[:, None] - pre) + P['a_need'][u % len(P['a_need'])]
            a_res = P['a_resc'].draw(rng, c.lrb(Lr, needy)) * fee[:, None]
            a_cor = P['a_corr'][u % len(P['a_corr'])] * fee[:, None]
            amt = np.where(wrong[:, None], np.where(needy, a_need, a_res), a_cor)
            keep = np.where(wrong, fee, 0.0)
            b_before = B.copy()
            c.give(B, inn & multi, coin, amt, inn & ~fm, keep=keep)
            given[ix] += np.maximum(B - b_before, 0).sum(1)
            if track:
                frecv[ix] += np.where(trk, np.maximum(B - b_before, 0)[rows, fs], 0.0)
        chg = inn & wrong[:, None]
        if support == 'calib':
            doom = chg & (B <= fee[:, None]) & (B > 0) & multi & ~fm & (rng.random(B.shape) < P['p_giveall'])
            for j in np.flatnonzero(doom.any(0)):
                dj = doom[:, j]
                other = np.where(inn & ~chg | (inn & (B > fee[:, None])), B, np.inf)
                other[:, j] = np.inf
                rc = other.argmin(1)
                okr = dj & np.isfinite(other[rows, rc])
                if track:
                    frecv[ix[okr & trk & (rc == fs)]] += B[okr & trk & (rc == fs), j]
                B[rows[okr], rc[okr]] += B[okr, j]
                given[ix[okr]] += B[okr, j]
                B[okr, j] = 0
        pay = np.where(chg, np.minimum(fee[:, None], B), 0.0)
        B = B - pay
        kill(B, S, chg & (B <= 0), a_, fee, False)
        newly = (S != 0) & part
        fd = first_dep[ix]
        first_dep[ix] = np.where(newly.any(1) & (fd == 99), t, fd)
        if (f_ >= 0).any():
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
    return dict(fin_bal=fin_bal, nin=nin, ex_bal=ex_bal, ex_rd=ex_rd, dd_rd=dd_rd, R=R, A=A, frecv=frecv, r0=r0)


def path_values(o, hmax):
    """Per path: settled value val[H], later-exit indicator xH[H], shutdown indicator dH[H] (as w1b_calibrated.values)."""
    Hs = np.arange(hmax + 1)
    inH = ~np.isnan(o['fin_bal'])
    A = o['A']
    prize = np.where(c.SPLIT[A][:, None], c.AMOUNT[A][:, None] / np.maximum(o['nin'], 1), c.AMOUNT[A][:, None])
    val = np.where(inH, o['fin_bal'] + prize, 0.0)
    exH = o['ex_rd'][:, None] <= Hs[None, :]
    val = val + np.where(exH, o['ex_bal'][:, None], 0.0)
    ddH = o['dd_rd'][:, None] <= Hs[None, :]
    return val, exH, ddH


# --------------------------------------------------------------------------- worker state
G = {}


def setup():
    if G:
        return G
    f = d.load()
    refill = w1.Refill(w1.seat_agents(f['seats']))
    T = c.data_tables(f)
    MR = c.model_rows(T)
    lam = json.loads(c.OUT_JSON.read_text())['round2']['meta']['lam_int']
    lam = {k: float(v) for k, v in lam.items()}
    E = w1.eligible_rows(f).merge(T['ar'][['arm', 'model', 'seed', 'round', 'agent', 'arm_i', 'model_i', 'seat']],
                                  on=['arm', 'model', 'seed', 'round', 'agent'])
    states = c.replay_states(f, refill)
    init = c.decision_init(E, states, refill)
    G.update(f=f, refill=refill, T=T, MR=MR, lam=lam, E=E, states=states, init=init)
    return G


def sub_init(init, idx):
    return {k: v[idx] for k, v in init.items()}


def fit_variant(variant, wseed):
    g = setup()
    T, MR, lam = g['T'], g['MR'], g['lam']
    if variant == 'pooled':
        MR2 = {k: (df, dict(z, model=np.zeros_like(z['model'])), y) for k, (df, z, y) in MR.items()}
        P = c.fit(T, MR2, wseed, lam)
        for k in ['ex', 'gi', 'rw']:
            for (name, kk, _, _), coef in zip(c.TERMS[k], P[k]):
                if name.startswith('model'):
                    j = kk // 5
                    coef[:] = np.tile(coef[:j].copy(), 5)
        return P
    return c.fit(T, MR, wseed, lam)


def ev_values(P, E, init, R, seed, rs, save=None, K=1):
    """For every decision: EV(stay)-EV(exit) under the 30 assumptions and H* for each nested prefix r in rs (paths per
    decision; with K information draws per decision the rows of init are D*K and r counts paths per decision)."""
    refill = setup()['refill']
    D = len(E)
    out = {r: {sup: dict(pol={}) for sup in c.SUPPORTS} for r in rs}
    dd = {r: {} for r in rs}
    for sup in c.SUPPORTS:
        ex, pok = c.exit_value(P, E, sup)
        for pol in c.POLICIES:
            o = simulate_x(P, init, R // K, np.random.default_rng(seed), sup, pol, c.HMAX, refill, save=save)
            val, exH, ddH = path_values(o, c.HMAX)
            del o
            val, exH = val.reshape(D, R, c.HMAX + 1), exH.reshape(D, R, c.HMAX + 1)
            d8 = ddH[:, 8].reshape(D, R)
            for r in rs:
                out[r][sup]['pol'][pol] = dict(A=val[:, :r].mean(1), X=exH[:, :r].mean(1))
                dd[r][sup, pol] = d8[:, :r].mean(1)
            del val, exH, ddH
        for r in rs:
            out[r][sup].update(exit=ex, pok=pok)
    res = {}
    for r in rs:
        dl, best, hs = c.deltas(out[r], init['r0'][::K])
        a = out[r]['calib']
        bp = best[:, ANCHOR]
        stay_anchor = np.choose(bp, [a['pol'][p]['A'][:, 8] for p in c.POLICIES])
        dd8 = np.choose(bp, [dd[r]['calib', p] for p in c.POLICIES])
        res[r] = dict(delta=dl.astype(np.float32), hstar=np.array([hs['none'], hs['calib']], np.int16),
                      stay=stay_anchor.astype(np.float32), exitv=a['exit'].astype(np.float32),
                      pdead=dd8.astype(np.float32))
    return res


# --------------------------------------------------------------------------- information-restricted states
def info_pool():
    """(arm, round, n) -> participant balance vectors sorted descending, over all logged states."""
    g = setup()
    pool = {}
    for (arm, m, sd, r), s in g['states'].items():
        b = s['bal'][s['st'] == 0]
        pool.setdefault((arm, r, len(b)), []).append(np.sort(b)[::-1])
    return {k: np.array(v) for k, v in pool.items()}


def info_init(E, init, rng, K):
    """K information draws per decision: peers' balances replaced by a logged vector (same arm, round, headcount) that
    keeps the focal agent's rank (peers above stay above its balance, below stay below), assigned to the actual peers in
    their actual rank order; the future solver order is reshuffled with a random seed (current solver kept)."""
    pool = info_pool()
    D = len(E)
    rows = np.repeat(np.arange(D), K)
    new = {k: np.repeat(v, K, axis=0).copy() for k, v in init.items()}
    fallback = 0
    for i in range(D):
        bal, st, fs = init['bal'][i], init['st'][i], init['focal'][i]
        part = np.flatnonzero(st == 0)
        peers = part[part != fs]
        T = bal[fs]
        above = int((bal[peers] > T).sum())
        n = len(part)
        arm, r = E.arm.iloc[i], int(E['round'].iloc[i])
        ok = None
        for rr in [r, r - 1, r + 1, r - 2, r + 2]:
            V = pool.get((arm, rr, n))
            if V is None:
                continue
            hi = V[:, :above].min(1) if above else np.full(len(V), np.inf)
            lo = V[:, above + 1:].max(1) if above + 1 < n else np.full(len(V), -np.inf)
            sel = (hi >= T) & (lo <= T)
            if sel.sum() >= 3:
                ok = np.delete(V[sel], above, axis=1)
                break
        order = peers[np.argsort(-bal[peers], kind='stable')]
        for k in range(K):
            j = i * K + k
            if ok is None:
                fallback += 1
                continue
            v = ok[rng.integers(len(ok))]
            new['bal'][j, order] = v
            new['seed'][j] = SEEDS[rng.integers(len(SEEDS))]
            new['cyc'][j] = -1
    assert (rows == np.arange(D * K) // K).all()
    return new, fallback


# --------------------------------------------------------------------------- jobs
def job(spec):
    g = setup()
    E, init = g['E'], g['init']
    idx = spec['idx']
    Ei = E.iloc[idx].reset_index(drop=True)
    ii = sub_init(init, idx)
    P = fit_variant(spec['variant'], spec['wseed'])
    K = spec.get('K', 1)
    if K > 1:
        ii, _ = info_init(Ei, ii, np.random.default_rng(spec['seed'] + 7), K)
    res = ev_values(P, Ei, ii, spec['R'], spec['seed'], spec['rs'], save=spec.get('save'), K=K)
    return spec['tag'], res


def calib_job(s):
    """LOSO: fit without seed s; simulate every decision of seed s where the LLM stayed (focal stays, then follows its
    model's calibrated hazard, H=8) and return per-decision predictions; also the held-out EXIT hazard."""
    g = setup()
    E, init, T, MR, lam, refill = g['E'], g['init'], g['T'], g['MR'], g['lam'], g['refill']
    P = c.fit(T, MR, {x: float(x != s) for x in SEEDS}, lam)
    sel = np.flatnonzero(((E.seed == s) & ~E.exited).to_numpy())
    ii = sub_init(init, sel)
    R = 400
    o = simulate_x(P, ii, R, np.random.default_rng([31, s]), 'calib', 'calib', 8, refill, track=True)
    val, exH, ddH = path_values(o, 8)
    D = len(sel)
    r0 = ii['r0']
    rr = np.repeat(r0, R)
    rowsN = np.arange(len(rr))
    rnext = np.minimum(rr, 8)
    fb = o['fin_bal'][rowsN, rnext]
    nn = o['nin'][rowsN, rnext].astype(float)
    Lnext = np.where(np.isnan(fb), -1.0, fb / (c.CHARGE / np.maximum(nn, 1)))
    recv = o['frecv'] > 0
    sup_ok = recv & (Lnext >= 1)
    inn8 = ~np.isnan(o['fin_bal'][:, 8])
    paths = dict(recv=recv, support=sup_ok, next_L1=Lnext >= 1, exit_later=exH[:, 8], dead=ddH[:, 8], fin=inn8,
                 v8=val[:, 8].astype(np.float32))
    paths = {k: v.reshape(D, R) for k, v in paths.items()}
    pred = pd.DataFrame(dict(
        i=sel, p_recv=paths['recv'].mean(1), p_support=paths['support'].mean(1),
        p_next_L1=paths['next_L1'].mean(1), p_exit=paths['exit_later'].mean(1),
        p_dead=paths['dead'].mean(1), p_fin=paths['fin'].mean(1), v8=paths['v8'].mean(1)))
    ex_df, ex_z, _ = MR['ex']
    te = (ex_df.seed == s).to_numpy()
    zt = {a: v[te] for a, v in ex_z.items()}
    hz = pd.DataFrame(dict(key=ex_df[te][['arm', 'model', 'seed', 'round', 'agent']].astype(str).agg('|'.join, axis=1).to_numpy(),
                           p_cal=c.predict(c.EXIT_TERMS, P['ex'], zt)))
    return s, pred, hz, paths


def game_check(variant, save, R=200):
    """In-sample game simulations (full fit) from round 1: exits, shutdowns, finishers per arm."""
    g = setup()
    P = fit_variant(variant, {s: 1.0 for s in SEEDS})
    out = {}
    for a in ARMS:
        tot = dict(exited=0.0, dead=0.0, fin=0.0)
        for m in MODELS:
            o = simulate_x(P, c.game_init(c.ARM_I[a], c.MODEL_I[m], SEEDS), R,
                           np.random.default_rng([5, c.ARM_I[a], c.MODEL_I[m]]), 'calib', 'calib', 8, g['refill'],
                           games=True, save=save)
            for k in tot:
                tot[k] += o[k].reshape(len(SEEDS), R).mean(1).sum()
        out[a] = tot
    return out


def tune_save(R=100):
    """Per-arm cancellation probability that matches the observed shutdowns per arm (bisection, in-sample)."""
    g = setup()
    obs = g['f']['games'].groupby('arm').dead.sum()
    P = fit_variant('calib', {s: 1.0 for s in SEEDS})
    save = np.zeros(4)
    for a in ARMS:
        lo, hi = 0.0, 1.0
        for _ in range(9):
            mid = (lo + hi) / 2
            sv = np.zeros(4)
            sv[c.ARM_I[a]] = mid
            dead = 0.0
            for m in MODELS:
                o = simulate_x(P, c.game_init(c.ARM_I[a], c.MODEL_I[m], SEEDS), R,
                               np.random.default_rng([9, c.ARM_I[a], c.MODEL_I[m]]), 'calib', 'calib', 8,
                               g['refill'], games=True, save=sv)
                dead += o['dead'].reshape(len(SEEDS), R).mean(1).sum()
            if dead > obs[a]:
                lo = mid
            else:
                hi = mid
        save[c.ARM_I[a]] = (lo + hi) / 2
    return save, obs.to_dict()


# --------------------------------------------------------------------------- summaries
def classify(boot_delta, cols):
    """boot_delta: B x D x A -> class per decision for assumption set cols (2.5 / 97.5 percentiles over refits)."""
    lo = np.percentile(boot_delta[:, :, cols], 2.5, axis=0)
    hi = np.percentile(boot_delta[:, :, cols], 97.5, axis=0)
    los, con = (lo > 0).all(1), (hi < 0).all(1)
    return np.where(los, 'losing', np.where(con, 'consistent', 'dependent'))


def count_sets(bd, mask=None):
    out = {}
    for name, cols in SETS.items():
        cl = classify(bd, cols)
        if mask is not None:
            cl = cl[mask]
        out[name] = {k: int((cl == k).sum()) for k in ['losing', 'dependent', 'consistent']}
    return out


def mc_se(bd, rng, nb=200, masks=None):
    """Bootstrap over refits: SE and 95% range of every count."""
    B = bd.shape[0]
    draws = []
    for _ in range(nb):
        ix = rng.integers(0, B, B)
        sub = bd[ix]
        row = {}
        for sname, cols in SETS.items():
            cl = classify(sub, cols)
            for mname, m in (masks or {'all': None}).items():
                cm = cl if m is None else cl[m]
                for k in ['losing', 'dependent', 'consistent']:
                    row[f'{mname}|{sname}|{k}'] = int((cm == k).sum())
        draws.append(row)
    df = pd.DataFrame(draws)
    return {k: dict(se=float(df[k].std()), lo=float(df[k].quantile(.025)), hi=float(df[k].quantile(.975)))
            for k in df.columns}


def hstar_summary(hb, sel):
    """Per-refit median of H* over the selected decisions -> [2.5, 50, 97.5] across refits."""
    med = np.median(hb[:, sel], 1)
    return [float(x) for x in np.percentile(med, [2.5, 50, 97.5])]


# --------------------------------------------------------------------------- main
def run_pool(specs, workers):
    ctx = mp.get_context('spawn')
    out = {}
    with ctx.Pool(workers, initializer=setup) as pool:
        for k, (tag, res) in enumerate(pool.imap_unordered(job, specs)):
            out[tag] = res
            if k % 10 == 0:
                print('  done', k + 1, '/', len(specs), time.strftime('%H:%M:%S'), flush=True)
    return out


def boot_weights(B):
    rng = np.random.default_rng(20261108)  # the round-2 sequence: the first 40 refits reuse its seed weights
    return [dict(zip(SEEDS, map(float, rng.multinomial(10, np.full(10, .1))))) for _ in range(B)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--boot', type=int, default=200)
    ap.add_argument('--reps', type=int, default=1600)
    ap.add_argument('--boot-all', type=int, default=40)
    ap.add_argument('--reps-all', type=int, default=100)
    ap.add_argument('--boot-alt', type=int, default=60)
    ap.add_argument('--reps-alt', type=int, default=400)
    ap.add_argument('--reps-point', type=int, default=800)
    ap.add_argument('--reps-point-all', type=int, default=400)
    ap.add_argument('--workers', type=int, default=10)
    ap.add_argument('--stage', default='all')
    args = ap.parse_args()
    t0 = time.time()
    g = setup()
    E = g['E']
    exits = np.flatnonzero(E.exited.to_numpy())
    alld = np.arange(len(E))
    stage = args.stage
    arrays = dict(np.load(NPZ)) if NPZ.exists() and stage != 'all' else {}
    W = boot_weights(max(args.boot, args.boot_all, args.boot_alt))
    full = {s: 1.0 for s in SEEDS}
    rsA = [r for r in [50, 100, 200, 400, 800, 1600] if r <= args.reps]
    if stage in ('all', 'calib'):
        print('LOSO calibration', time.strftime('%H:%M:%S'), flush=True)
        ctx = mp.get_context('spawn')
        with ctx.Pool(min(args.workers, 10), initializer=setup) as pool:
            cal = pool.map(calib_job, SEEDS)
        pred = pd.concat([p for _, p, _, _ in cal], ignore_index=True)
        hz = pd.concat([h for _, _, h, _ in cal], ignore_index=True)
        pred.to_csv(VAL / 'results/w1c_calib_pred.csv', index=False)
        hz.to_csv(VAL / 'results/w1c_calib_hazard.csv', index=False)
        np.savez_compressed(VAL / 'results/w1c_calib_paths.npz', i=pred.i.to_numpy(),
                            **{k: np.concatenate([q[k] for _, _, _, q in cal]) for k in cal[0][3]})
    if stage in ('all', 'exits'):
        print('exits: point + bootstrap', time.strftime('%H:%M:%S'), flush=True)
        specs = [dict(tag=('pt', 0), idx=exits, variant='calib', wseed=full, R=args.reps, seed=1, rs=rsA)]
        specs += [dict(tag=('b', b), idx=exits, variant='calib', wseed=W[b], R=args.reps, seed=100 + b, rs=rsA)
                  for b in range(args.boot)]
        res = run_pool(specs, args.workers)
        for r in rsA:
            arrays[f'ex_delta_{r}'] = np.array([res[('b', b)][r]['delta'] for b in range(args.boot)])
            arrays[f'ex_hstar_{r}'] = np.array([res[('b', b)][r]['hstar'] for b in range(args.boot)])
        arrays['ex_stay'] = np.array([res[('b', b)][rsA[-1]]['stay'] for b in range(args.boot)])
        for r, v in res[('pt', 0)].items():
            for k_ in ['delta', 'hstar', 'stay', 'exitv', 'pdead']:
                arrays[f'ex_pt_{k_}_{r}'] = v[k_]
        np.savez_compressed(NPZ, **arrays)
        print('exits done', round(time.time() - t0), flush=True)
    if stage in ('all', 'alldec'):
        print('all decisions', time.strftime('%H:%M:%S'), flush=True)
        chunks = np.array_split(alld, args.workers)
        rsB = [r for r in [50, 100, 200] if r <= args.reps_all]  # nested prefixes
        specs = [dict(tag=('pt', k), idx=ch, variant='calib', wseed=full, R=args.reps_point_all, seed=1,
                      rs=[100, args.reps_point_all]) for k, ch in enumerate(chunks)]
        specs += [dict(tag=('b', b), idx=alld, variant='calib', wseed=W[b], R=args.reps_all, seed=100 + b, rs=rsB)
                  for b in range(args.boot_all)]
        res = run_pool(specs, args.workers)
        for r in rsB:
            arrays[f'all_delta_{r}'] = np.array([res[('b', b)][r]['delta'] for b in range(args.boot_all)])
            arrays[f'all_hstar_{r}'] = np.array([res[('b', b)][r]['hstar'] for b in range(args.boot_all)])
        for r in [100, args.reps_point_all]:
            for k_ in ['delta', 'hstar']:
                arrays[f'all_pt_{k_}_{r}'] = np.concatenate([res[('pt', k)][r][k_] for k in range(len(chunks))],
                                                            axis=-1 if k_ == 'hstar' else 0)
        np.savez_compressed(NPZ, **arrays)
        print('all decisions done', round(time.time() - t0), flush=True)
    if stage in ('all', 'alt'):
        print('alternatives', time.strftime('%H:%M:%S'), flush=True)
        save, obs_dead = tune_save()
        arrays['save'] = save
        print('save', save, obs_dead, flush=True)
        specs = []
        for var, extra in [('pooled', {}), ('recal', dict(save=save)), ('info', dict(K=8))]:
            v = 'pooled' if var == 'pooled' else 'calib'
            specs += [dict(tag=(var, b), idx=exits, variant=v, wseed=W[b], R=args.reps_alt, seed=100 + b,
                           rs=[args.reps_alt], **extra) for b in range(args.boot_alt)]
            specs += [dict(tag=(var, 'pt'), idx=exits, variant=v, wseed=full, R=args.reps_point, seed=1,
                           rs=[args.reps_point], **extra)]
        res = run_pool(specs, args.workers)
        for var in ['pooled', 'recal', 'info']:
            arrays[f'alt_{var}_delta'] = np.array([res[(var, b)][args.reps_alt]['delta'] for b in range(args.boot_alt)])
            arrays[f'alt_{var}_hstar'] = np.array([res[(var, b)][args.reps_alt]['hstar'] for b in range(args.boot_alt)])
            arrays[f'alt_{var}_pt_delta'] = res[(var, 'pt')][args.reps_point]['delta']
        np.savez_compressed(NPZ, **arrays)
        gc = {'calib': game_check('calib', None), 'pooled': game_check('pooled', None),
              'recal': game_check('calib', save)}
        (VAL / 'results/w1c_gamecheck.json').write_text(json.dumps(dict(gc=gc, save=save.tolist(), obs_dead=obs_dead),
                                                                    indent=1))
        print('alternatives done', round(time.time() - t0), flush=True)
    if stage in ('all', 'summary'):
        summarize(args)
    print('total', round(time.time() - t0))


# --------------------------------------------------------------------------- summary
def calib_tables(E, rng, ndraw=4000):
    """Observed vs LOSO-predicted outcomes of stayers (and the immediate EXIT hazard) by model x arm x L band.

    Stayers enter once per agent and L band (its first stay decision in that band), so an agent's single fate is not
    counted several times. The 95% predictive interval of the cell mean draws one simulated path per agent-decision
    (LOSO fit, simulation variance only; agents of the same game are simulated independently, so the interval is
    somewhat too narrow). A cell fails when the observed mean lies outside it. The observed mean also gets a seed
    bootstrap interval. The EXIT hazard uses every decision (a Bernoulli draw per decision from its held-out
    probability)."""
    ar = setup()['f']['agent_rounds']
    pred = pd.read_csv(VAL / 'results/w1c_calib_pred.csv')
    pz = dict(np.load(VAL / 'results/w1c_calib_paths.npz'))
    pred['j'] = np.arange(len(pred))
    S = E[~E.exited].copy()
    S = S.join(pred.set_index('i'), how='inner')
    nxt = ar[['arm', 'model', 'seed', 'agent', 'round', 'L_prep']].copy()
    nxt['round'] -= 1
    S = S.merge(nxt.rename(columns={'L_prep': 'L_next'}), on=['arm', 'model', 'seed', 'agent', 'round'], how='left')
    S['o_recv'] = ((S.recv_prep + S.recv_rescue) > 0).astype(float)
    S['o_next_L1'] = (S.L_next >= 1).astype(float)
    S['o_support'] = S.o_recv * S.o_next_L1
    S['o_exit_later'] = (S.fate == 'exited').astype(float)
    S['o_dead'] = (S.fate == 'dead').astype(float)
    S['o_fin'] = (S.fate == 'in').astype(float)
    S['o_v8'] = S.settled.astype(float)
    S['L3'] = lb3(S.L_prep.to_numpy())
    hz = pd.read_csv(VAL / 'results/w1c_calib_hazard.csv')
    Ek = E.assign(key=E[['arm', 'model', 'seed', 'round', 'agent']].astype(str).agg('|'.join, axis=1))
    H = Ek.merge(hz, on='key')
    H['o_exit_now'] = H.exited.astype(float)
    H['L3'] = lb3(H.L_prep.to_numpy())
    mets = ['support', 'recv', 'next_L1', 'exit_later', 'dead', 'fin', 'v8']
    first = S.sort_values('round').drop_duplicates(['arm', 'model', 'seed', 'agent', 'L3'])
    first7 = S[S['round'] <= 7].sort_values('round').drop_duplicates(['arm', 'model', 'seed', 'agent', 'L3'])
    rows = []
    groupings = [('model|arm|L', ['model', 'arm', 'L3']), ('arm|L', ['arm', 'L3']), ('model|L', ['model', 'L3']),
                 ('L', ['L3'])]

    def seed_ci(g, col):
        per = g.groupby('seed')[col].agg(['sum', 'count']).reindex(SEEDS, fill_value=0).to_numpy(float)
        Wb = rng.multinomial(10, np.full(10, .1), size=1000).astype(float)
        den = Wb @ per[:, 1]
        ok = den > 0
        v = (Wb @ per[:, 0])[ok] / den[ok]
        return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))

    for gname, keys in groupings:
        for m in mets:
            base = first7 if m in ('support', 'recv', 'next_L1') else first
            for k_, g in base.groupby(keys):
                k_ = k_ if isinstance(k_, tuple) else (k_,)
                pth = pz[m][g.j.to_numpy()]
                draw = pth[np.arange(len(g))[None, :], rng.integers(0, pth.shape[1], (ndraw, len(g)))].mean(1)
                lo, hi = np.percentile(draw, [2.5, 97.5])
                obs = float(g[f'o_{m}'].mean())
                olo, ohi = seed_ci(g, f'o_{m}')
                rows.append(dict(level=gname, key='|'.join(map(str, k_)), metric=m, n=len(g),
                                 seeds=int(g.seed.nunique()), obs=obs, obs_lo=olo, obs_hi=ohi,
                                 pred=float(pth.mean()), pred_lo=float(lo), pred_hi=float(hi),
                                 fail=bool(obs < lo or obs > hi)))
        for k_, g in H.groupby(keys):
            k_ = k_ if isinstance(k_, tuple) else (k_,)
            p = g.p_cal.to_numpy()
            draw = (rng.random((ndraw, len(g))) < p[None, :]).mean(1)
            lo, hi = np.percentile(draw, [2.5, 97.5])
            obs = float(g.o_exit_now.mean())
            olo, ohi = seed_ci(g, 'o_exit_now')
            rows.append(dict(level=gname, key='|'.join(map(str, k_)), metric='exit_now', n=len(g),
                             seeds=int(g.seed.nunique()), obs=obs, obs_lo=olo, obs_hi=ohi, pred=float(p.mean()),
                             pred_lo=float(lo), pred_hi=float(hi), fail=bool(obs < lo or obs > hi)))
    cal = pd.DataFrame(rows)
    cal.to_csv(VAL / 'results/w1c_calib_cells.csv', index=False)
    return cal, S


def summarize(args):
    rng = np.random.default_rng(11)
    g = setup()
    E = g['E']
    A = dict(np.load(NPZ))
    X = E[E.exited].reset_index(drop=True)
    big = X.arm.isin(w1.HIGH).to_numpy()
    out = dict(meta=dict(boot=args.boot, reps=args.reps, boot_all=args.boot_all, reps_all=args.reps_all,
                         boot_alt=args.boot_alt, reps_alt=args.reps_alt, reps_point=args.reps_point,
                         sets={k: [f'{ASSUME[j][0]}|{ASSUME[j][1]}|{int(ASSUME[j][2])}' for j in v] for k, v in SETS.items()},
                         note='counts are LLM exits classed by the 2.5 / 97.5 percentiles of EV(stay)-EV(exit) over '
                              'seed-bootstrap refits, every assumption of the set; MC SE = SD over 200 bootstrap '
                              'resamples of the refits'))
    # 1. calibration
    cal, S = calib_tables(E, rng)
    low = cal[(cal.level == 'model|arm|L')]
    out['calibration'] = dict(
        by_L=cal[cal.level == 'L'].to_dict('records'), by_arm_L=cal[cal.level == 'arm|L'].to_dict('records'),
        by_model_L=cal[cal.level == 'model|L'].to_dict('records'),
        cells_fail={m: low[(low.metric == m) & low.fail].key.tolist() for m in low.metric.unique()},
        cells_n={m: int((low.metric == m).sum()) for m in low.metric.unique()},
        cells_fail_n={m: int(((low.metric == m) & low.fail).sum()) for m in low.metric.unique()},
        cells_fail_L={m: {L: int(((low.metric == m) & low.fail & low.key.str.endswith('|' + L)).sum()) for L in LB3}
                      for m in low.metric.unique()},
        cells_n_L={m: {L: int(((low.metric == m) & low.key.str.endswith('|' + L)).sum()) for L in LB3}
                   for m in low.metric.unique()},
        n_stays=len(S))
    # 2. convergence for the exits
    rs = sorted(int(k.split('_')[-1]) for k in A if k.startswith('ex_delta_'))
    conv = dict(by_R={}, by_B={}, hstar={}, mcse={})
    masks = {'all': None, 'big': big, 'small': ~big}
    for r in rs:
        bd = A[f'ex_delta_{r}']
        conv['by_R'][r] = {m: count_sets(bd, mk) for m, mk in masks.items()}
        hb = A[f'ex_hstar_{r}'][:, 1, :]
        hp = A[f'ex_pt_hstar_{r}'][1]
        conv['hstar'][r] = {k_: dict(boot=hstar_summary(hb, sel), point=float(np.median(hp[sel])),
                                     le8_boot=[float(x) for x in np.percentile((hb[:, sel] <= 8).mean(1), [2.5, 50, 97.5])],
                                     le8_point=float((hp[sel] <= 8).mean()),
                                     le10_boot=[float(x) for x in np.percentile((hb[:, sel] <= 10).mean(1), [2.5, 50, 97.5])],
                                     le10_point=float((hp[sel] <= 10).mean()))
                            for k_, sel in [('exits', np.ones(len(X), bool)), ('big', big), ('small', ~big)]}
        hbn = A[f'ex_hstar_{r}'][:, 0, :]
        hpn = A[f'ex_pt_hstar_{r}'][0]
        conv['hstar'][r]['none_exits'] = dict(boot=hstar_summary(hbn, np.ones(len(X), bool)), point=float(np.median(hpn)),
                                              le8_point=float((hpn <= 8).mean()))
        conv['hstar'][r]['point_stay_better_anchor'] = int((A[f'ex_pt_delta_{r}'][:, ANCHOR] > 0).sum())
    rmax = rs[-1]
    Bmax = A[f'ex_delta_{rmax}'].shape[0]
    for B in [10, 20, 40, 80, 120, 160, 200]:
        if B <= Bmax:
            conv['by_B'][B] = {f'R{r}': count_sets(A[f'ex_delta_{r}'][:B]) for r in (rs[0], rmax)}
    conv['mcse'][f'B{Bmax}_R{rmax}'] = mc_se(A[f'ex_delta_{rmax}'], rng, masks=masks)
    conv['mcse']['B40_R50'] = mc_se(A['ex_delta_50'][:40], rng, masks=masks)
    conv['mcse'][f'B{Bmax}_R50'] = mc_se(A['ex_delta_50'], rng, masks=masks)
    # split halves
    h1, h2 = A[f'ex_delta_{rmax}'][:Bmax // 2], A[f'ex_delta_{rmax}'][Bmax // 2:]
    conv['halves'] = [count_sets(h1), count_sets(h2)]
    # agreement of the anchor class with round 2
    D2 = pd.read_csv(VAL / 'results/w1b_decisions.csv')
    D2x = D2[D2.exited].reset_index(drop=True)
    cl_new = classify(A[f'ex_delta_{rmax}'], [ANCHOR])
    conv['anchor_vs_round2'] = pd.crosstab(D2x.anchor_cls, cl_new).to_dict()
    # percentile spread (2.5% bound) of the anchor delta as R grows
    conv['lo_anchor_median'] = {r: float(np.median(np.percentile(A[f'ex_delta_{r}'][:, :, ANCHOR], 2.5, 0))) for r in rs}
    out['convergence_exits'] = conv
    # all decisions
    rsB = sorted(int(k.split('_')[-1]) for k in A if k.startswith('all_delta_'))
    stays = ~E.exited.to_numpy()
    ex_all = E.exited.to_numpy()
    bigE = E.arm.isin(w1.HIGH).to_numpy()
    allc = dict(by_R={}, hstar={})
    for r in rsB:
        bd = A[f'all_delta_{r}']
        allc['by_R'][r] = dict(stays=count_sets(bd, stays), exits=count_sets(bd, ex_all))
        hb = A[f'all_hstar_{r}'][:, 1, :]
        allc['hstar'][r] = {k_: dict(boot=hstar_summary(hb, sel)) for k_, sel in
                            [('all', np.ones(len(E), bool)), ('exits', ex_all), ('stays', stays),
                             ('exits_big', ex_all & bigE), ('exits_small', ex_all & ~bigE)]}
    for r in sorted(int(k.split('_')[-1]) for k in A if k.startswith('all_pt_hstar_')):
        hp = A[f'all_pt_hstar_{r}'][1]
        allc['hstar'][f'point_{r}'] = {k_: float(np.median(hp[sel])) for k_, sel in
                                       [('all', np.ones(len(E), bool)), ('exits', ex_all), ('stays', stays),
                                        ('exits_big', ex_all & bigE), ('exits_small', ex_all & ~bigE)]}
        allc['hstar'][f'point_{r}_models'] = {m: float(np.median(hp[(E.model == m).to_numpy()])) for m in MODELS}
        allc['hstar'][f'point_{r}_astra_gt30'] = float((hp[(E.model == 'Astra').to_numpy()] > c.HMAX).mean())
    if rsB:
        allc['mcse_stays'] = mc_se(A[f'all_delta_{rsB[-1]}'], rng, nb=100, masks={'stays': stays})
    out['convergence_all'] = allc
    # 3. sensitivity
    sens = {}
    variants = [('calib', A.get(f'ex_delta_{args.reps_alt}'), A.get(f'ex_pt_delta_{args.reps_alt}'))]
    for var in ['pooled', 'recal', 'info']:
        if f'alt_{var}_delta' in A:
            variants.append((var, A[f'alt_{var}_delta'], A[f'alt_{var}_pt_delta']))
    cls_store = {}
    for var, bd, pt in variants:
        if bd is None:
            continue
        bd = bd[:args.boot_alt]
        sens[var] = dict(counts={m: count_sets(bd, mk) for m, mk in masks.items()},
                         mcse=mc_se(bd, rng, nb=200, masks={'all': None}),
                         point_stay_better={f'{h}|{s_}|{int(w)}': int((pt[:, j] > 0).sum())
                                            for j, (h, s_, w) in enumerate(ASSUME)},
                         median_delta_anchor=float(np.median(pt[:, ANCHOR])),
                         median_delta_geo=float(np.median(pt[:, GEO_ANCHOR])),
                         by_arm_anchor={a: {k: int(v) for k, v in pd.Series(classify(bd, [ANCHOR])[(X.arm == a).to_numpy()])
                                            .value_counts().items()} for a in ARMS},
                         by_arm_geo={a: {k: int(v) for k, v in pd.Series(classify(bd, [GEO_ANCHOR])[(X.arm == a).to_numpy()])
                                         .value_counts().items()} for a in ARMS})
        cls_store[var] = classify(bd, [ANCHOR])
        if var != 'calib':
            hb = A[f'alt_{var}_hstar'][:, 1, :]
            sens[var]['hstar_exits'] = dict(boot=hstar_summary(hb, np.ones(len(X), bool)),
                                            big=hstar_summary(hb, big), small=hstar_summary(hb, ~big))
    if 'calib' in cls_store:
        for var in cls_store:
            sens[var]['agree_anchor_with_calib'] = int((cls_store[var] == cls_store['calib']).sum())
            sens[var]['losing_in_both'] = int(((cls_store[var] == 'losing') & (cls_store['calib'] == 'losing')).sum())
        allv = np.array([cls_store[v] for v in cls_store])
        sens['losing_in_all_baselines_anchor'] = int((allv == 'losing').all(0).sum())
        sens['losing_in_all_baselines_anchor_big'] = int(((allv == 'losing').all(0) & big).sum())
    gcp = VAL / 'results/w1c_gamecheck.json'
    if gcp.exists():
        sens['gamecheck'] = json.loads(gcp.read_text())
    out['sensitivity'] = sens
    # 4. C-2: stayers' realised vs exiters' counterfactual, by arm x L band
    c2 = []
    stay_cf = A[f'ex_stay'] if 'ex_stay' in A else None
    exitv = A[f'ex_pt_exitv_{rmax}']
    stay_pt = A[f'ex_pt_stay_{rmax}']
    X['L3'] = lb3(X.L_prep.to_numpy())
    for (arm, L), gS in list(S.groupby(['arm', 'L3'])) + [((a, 'all'), S[S.arm == a]) for a in ARMS]:
        sel = ((X.arm == arm) & ((X.L3 == L) if L != 'all' else True)).to_numpy()
        per = gS.groupby('seed').agg(s=('o_v8', 'sum'), p=('v8', 'sum'), n=('o_v8', 'size')).reindex(SEEDS, fill_value=0)
        Wb = rng.multinomial(10, np.full(10, .1), size=1000).astype(float)
        den = Wb @ per.n.to_numpy(float)
        okb = den > 0
        rb = (Wb @ per.s.to_numpy(float))[okb] / den[okb]
        row = dict(arm=arm, L=L, n_stay=len(gS), stay_realised=float(gS.o_v8.mean()) if len(gS) else None,
                   stay_realised_lo=float(np.percentile(rb, 2.5)) if len(gS) else None,
                   stay_realised_hi=float(np.percentile(rb, 97.5)) if len(gS) else None,
                   stay_loso_pred=float(gS.v8.mean()) if len(gS) else None, n_exit=int(sel.sum()))
        if sel.sum():
            cf = stay_cf[:, sel].mean(1)
            row.update(exit_realised=float(X[sel].settled.mean()), exit_model=float(exitv[sel].mean()),
                       exit_cf_stay=float(stay_pt[sel].mean()), exit_cf_lo=float(np.percentile(cf, 2.5)),
                       exit_cf_hi=float(np.percentile(cf, 97.5)))
        c2.append(row)
    c2 = pd.DataFrame(c2)
    c2.to_csv(VAL / 'results/w1c_c2_table.csv', index=False)
    out['c2'] = c2.to_dict('records')
    # 5. K* for the exits (point fit, R max)
    dl, pdd = A[f'ex_pt_delta_{rmax}'][:, ANCHOR], A[f'ex_pt_pdead_{rmax}']
    kst = np.where((pdd > 0) & (dl > 0), dl / np.maximum(pdd, 1e-12), np.where(dl <= 0, 0.0, np.inf))
    ks = {}
    for k_, sel in [('all', np.ones(len(X), bool)), ('big', big), ('small', ~big)] + [(a, (X.arm == a).to_numpy())
                                                                                       for a in ARMS]:
        kk = kst[sel]
        fk = kk[np.isfinite(kk) & (kk > 0)]
        ks[k_] = dict(n=int(sel.sum()), finite_median=float(np.median(fk)) if len(fk) else None,
                      with_inf_median=float(np.median(kk[kk > 0])) if (kk > 0).any() else None,
                      n_inf=int(np.isinf(kk).sum()), n_zero=int((kk == 0).sum()))
    out['K_star'] = ks
    # breakdowns of the converged classes (B max, R max)
    bdm = A[f'ex_delta_{rmax}']
    lo_m, hi_m = np.percentile(bdm, 2.5, 0), np.percentile(bdm, 97.5, 0)
    Xb = X.assign(lb=X.L_prep.map(w1.lband), rb=X['round'].map(w1.rband), cls=classify(bdm, [ANCHOR]),
                  llm91=D2x.llm_only_dp8.to_numpy(), r1_10k=((X['round'] == 1) & (X.tier == 10)).to_numpy())
    brk = {}
    for col in ['arm', 'model', 'lb', 'rb']:
        brk[col] = {str(k_): {c_: int((g_.cls == c_).sum()) for c_ in ['losing', 'dependent', 'consistent']} | dict(n=len(g_))
                    for k_, g_ in Xb.groupby(col)}
    brk['r1_10k'] = {c_: int((Xb[Xb.r1_10k].cls == c_).sum()) for c_ in ['losing', 'dependent', 'consistent']}
    brk['r1_10k_by_arm'] = {a: {c_: int((Xb[Xb.r1_10k & (Xb.arm == a)].cls == c_).sum())
                                for c_ in ['losing', 'dependent', 'consistent']} for a in ARMS}
    brk['llm91'] = {sname: int((classify(bdm, cols)[Xb.llm91] == 'losing').sum()) for sname, cols in SETS.items()}
    brk['sets_by_arm'] = {sname: {a: int((classify(bdm, cols)[(X.arm == a).to_numpy()] == 'losing').sum()) for a in ARMS}
                          for sname, cols in SETS.items()}
    brk['per_assumption'] = {f'{h}|{s_}|{int(w)}': dict(lo_pos=int((lo_m[:, j] > 0).sum()), hi_neg=int((hi_m[:, j] < 0).sum()),
                                                       lo_pos_big=int((lo_m[big, j] > 0).sum()),
                                                       point_pos=int((A[f'ex_pt_delta_{rmax}'][:, j] > 0).sum()))
                             for j, (h, s_, w) in enumerate(ASSUME)}
    dpt = A[f'ex_pt_delta_{rmax}'][:, ANCHOR]
    brk['delta_median_by_arm'] = {a: [float(np.median(dpt[(X.arm == a).to_numpy()])),
                                      float(np.percentile(dpt[(X.arm == a).to_numpy()], 25)),
                                      float(np.percentile(dpt[(X.arm == a).to_numpy()], 75))] for a in ARMS}
    out['breakdown_exits'] = brk
    X2 = X.assign(cls_anchor=classify(A[f'ex_delta_{rmax}'], [ANCHOR]),
                  cls_12=classify(A[f'ex_delta_{rmax}'], SETS['true_horizon']),
                  cls_30=classify(A[f'ex_delta_{rmax}'], SETS['all']),
                  delta_anchor_pt=A[f'ex_pt_delta_{rmax}'][:, ANCHOR], hstar_pt=A[f'ex_pt_hstar_{rmax}'][1],
                  K_star=kst, **{f'cls_anchor_{v}': cls_store[v] for v in cls_store})
    X2[['arm', 'model', 'seed', 'round', 'agent', 'tier', 'n', 'L_prep', 'T', 'X', 'settled', 'cls_anchor', 'cls_12', 'cls_30',
        'delta_anchor_pt', 'hstar_pt', 'K_star'] + [f'cls_anchor_{v}' for v in cls_store]].to_csv(
        VAL / 'results/w1c_decisions.csv', index=False)
    OUT.write_text(json.dumps(c.clean(out), ensure_ascii=False, indent=1))
    print('wrote', OUT)
    figures3(out, cal)
    # redraw the round-2 decision figure with the converged classes (exits: B max x R max; H*: point fit, all decisions)
    E2 = D2.copy()
    ex_ix = np.flatnonzero(E2.exited.to_numpy())
    assert (E2.agent.to_numpy()[ex_ix] == X.agent.to_numpy()).all()
    E2.loc[ex_ix, 'anchor_cls'] = classify(bdm, [ANCHOR])
    E2.loc[ex_ix, 'delta_anchor'] = A[f'ex_pt_delta_{rmax}'][:, ANCHOR]
    for gname in ['anchor', 'true_horizon', 'H_le10', 'all']:
        E2.loc[ex_ix, f'cls_{gname}'] = classify(bdm, SETS[gname])
    hk = sorted(k for k in A if k.startswith('all_pt_hstar_'))
    if hk:
        E2['hstar_calib'] = A[max(hk, key=lambda k: int(k.split('_')[-1]))][1]
    c.figures(E2, json.loads(c.OUT_JSON.read_text())['round2']['validation'], pd.read_csv(VAL / 'results/w1b_cells.csv'))


def figures3(out, cal):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'AppleGothic', 'axes.unicode_minus': False, 'font.size': 8,
                         'mathtext.fontset': 'dejavusans'})
    lab = {'main': '2천만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
    conv = out['convergence_exits']
    rs = sorted(int(r) for r in conv['by_R'])
    mc = conv['mcse']
    Bk = [k for k in mc if k.endswith(f'_R{rs[-1]}')][0]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    ax = axes[0]
    for sname, cl, col, lb in [('anchor', 'losing', '#c92a2a', '기준 가정: 손실'), ('anchor', 'dependent', '#868e96', '기준 가정: 의존'),
                               ('true_horizon', 'losing', '#e8590c', '12개 가정: 손실'), ('all', 'losing', '#1971c2', '30개 가정: 손실')]:
        y = [conv['by_R'][r]['all'][sname][cl] for r in rs]
        ax.plot(rs, y, 'o-', color=col, label=lb, ms=3)
        se = mc[Bk][f'all|{sname}|{cl}']['se']
        ax.errorbar(rs[-1], y[-1], yerr=1.96 * se, color=col, capsize=2)
    ax.set_xscale('log')
    ax.set_xticks(rs)
    ax.set_xticklabels([str(r) for r in rs])
    ax.set_xlabel('결정당 시뮬레이션 수 R (재적합 200회)')
    ax.set_ylabel('LLM 이탈 수 (279건 중)')
    ax.legend(fontsize=6.5)
    ax.set_title('(a) 분류 수와 R (끝점 막대: 몬테카를로 95%)', fontsize=8)
    ax = axes[1]
    Bs = sorted(int(b) for b in conv['by_B'])
    for key, ls in [(f'R{rs[-1]}', '-'), (f'R{rs[0]}', ':')]:
        for sname, cl, col in [('anchor', 'losing', '#c92a2a'), ('true_horizon', 'losing', '#e8590c'), ('all', 'losing', '#1971c2')]:
            ax.plot(Bs, [conv['by_B'][b][key][sname][cl] for b in Bs], ls, marker='o', ms=3, color=col)
    ax.set_xlabel('재적합 수 B (실선 R=%d, 점선 R=%d)' % (rs[-1], rs[0]))
    ax.set_ylabel('견고한 손실 이탈 수')
    ax.set_title('(b) 분류 수와 B (빨강 기준, 주황 12개, 파랑 30개)', fontsize=8)
    ax = axes[2]
    for k_, col, lb in [('exits', 'k', '이탈 전체'), ('big', '#1f5fa8', '큰 상금 이탈'), ('small', '#c2410c', '작은 상금 이탈')]:
        bm = [conv['hstar'][r][k_]['boot'] for r in rs]
        pt = [conv['hstar'][r][k_]['point'] for r in rs]
        ax.errorbar(rs, [b[1] for b in bm], yerr=[[b[1] - b[0] for b in bm], [b[2] - b[1] for b in bm]], fmt='o-', ms=3,
                    color=col, capsize=2, label=lb + ' (재적합 중앙값)')
        ax.plot(rs, pt, 's--', ms=3, color=col, mfc='w', label=lb + ' (원 적합)')
    ax.set_xscale('log')
    ax.set_xticks(rs)
    ax.set_xticklabels([str(r) for r in rs])
    ax.set_xlabel('결정당 시뮬레이션 수 R')
    ax.set_ylabel('$H^*$ 중앙값')
    ax.legend(fontsize=6)
    ax.set_title('(c) 기간 문턱 중앙값과 R', fontsize=8)
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_ev_convergence.{ext}', dpi=200)
    plt.close(fig)
    # calibration cells
    cells = cal[cal.level == 'model|arm|L']
    mets = [('exit_now', '즉시 이탈'), ('support', '지원 성공'), ('exit_later', '이후 이탈'), ('dead', '꺼짐'),
            ('v8', '정산 토큰')]
    keys = [f'{m}|{a}' for m in MODELS for a in ARMS]
    fig, axes = plt.subplots(len(mets), 3, figsize=(12, 9), sharex=True)
    for i, (mt, mlab) in enumerate(mets):
        for j, L in enumerate(LB3):
            ax = axes[i, j]
            for x_, k_ in enumerate(keys):
                r_ = cells[(cells.metric == mt) & (cells.key == f'{k_}|{L}')]
                if not len(r_):
                    continue
                r_ = r_.iloc[0]
                sc = 1e6 if mt == 'v8' else 1.0
                colr = '#c92a2a' if r_.fail else '#2b8a3e'
                ax.vlines(x_, r_.pred_lo / sc, r_.pred_hi / sc, color='#999', lw=2.5, alpha=.7)
                ax.plot(x_, r_.pred / sc, '_', color='k', ms=6)
                ax.plot(x_, r_.obs / sc, 'o', color=colr, ms=2.5)
            for b in range(1, 5):
                ax.axvline(b * 4 - .5, color='#ccc', lw=.5)
            if i == 0:
                ax.set_title({'<1': '$L<1$', '1-2': '$1\\leq L<2$', '>=2': '$L\\geq 2$'}[L], fontsize=8)
            if j == 0:
                ax.set_ylabel(mlab + (' (백만)' if mt == 'v8' else ''), fontsize=7)
    for ax in axes[-1]:
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels([f"{k.split('|')[0]} {lab[k.split('|')[1]]}" for k in keys], rotation=90, fontsize=5.5)
    fig.suptitle('시드 제외 보정(모델 x 조건 칸, 열 = 여유 구간 L): 회색 막대 = 예측 95% 구간, 가로선 = 예측 평균, 점 = 관측(빨강: 구간 밖). '
                 '잔류 결정은 에이전트당 구간별 첫 결정만 쓴다', fontsize=8)
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_ev_calib_cells.{ext}', dpi=200)
    plt.close(fig)
    # sensitivity
    sens = out['sensitivity']
    vars_ = [v for v in ['calib', 'pooled', 'recal', 'info'] if v in sens]
    vl = {'calib': '(i) 보정', 'pooled': '(ii-a) 모델 합침', 'recal': '(ii-b) 꺼짐 재보정', 'info': '(iii) 정보 제한'}
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2), sharey=True)
    for ax, (sname, t) in zip(axes, [('anchor', '$H=8$, 보정 지원, $W=0$'), ('geo_anchor', '기하 기간, 보정 지원, $W=0$'),
                                     ('true_horizon', '$H\\in\\{8,$기하$\\}$ 12개 가정')]):
        bottom = np.zeros(len(vars_))
        for cl, col in [('losing', '#c92a2a'), ('dependent', '#adb5bd'), ('consistent', '#1971c2')]:
            v = np.array([sens[x]['counts']['all'][sname][cl] for x in vars_])
            ax.bar(range(len(vars_)), v, .7, bottom=bottom, color=col,
                   label={'losing': '견고한 손실', 'dependent': '가정 의존', 'consistent': '견고한 일치'}[cl])
            for k_, (vv, bb) in enumerate(zip(v, bottom)):
                if vv >= 12:
                    ax.text(k_, bb + vv / 2, str(vv), ha='center', va='center', fontsize=6.5, color='w')
            bottom += v
        ax.set_xticks(range(len(vars_)))
        ax.set_xticklabels([vl[x] for x in vars_], fontsize=6.5, rotation=20)
        ax.set_title(t, fontsize=8)
    axes[0].set_ylabel('LLM 이탈 수')
    axes[0].legend(fontsize=6.5, loc='lower left')
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_ev_sensitivity.{ext}', dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    main()
