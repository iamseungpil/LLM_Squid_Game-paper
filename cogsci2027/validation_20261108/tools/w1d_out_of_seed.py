"""W1d (review round 4: Astra round 3 rows A-1, C-2, Q1 and P3): out-of-seed EV classification on existing data.

For every seed s (10 folds) the calibrated transition model of w1b_calibrated is fitted on the other nine seeds only:
one point fit (the nine seeds once) and B refits on bootstrap resamples of those nine seeds (multinomial 9 over 9). Every
decision of seed s is then simulated forward from its logged state with these fits only, so no decision is ever
classified by a model that saw its own seed (or its own game). Per fold and refit:

  1. LLM exits (279): R_ex paths per decision, both support beliefs x four continuation rules up to round 30, giving
     EV(stay)-EV(exit) for the 30 assumptions of w1b (risk neutral), and for the 12 assumptions H in {8, geo} the
     certainty-equivalent difference under two token utilities that weigh keeping tokens more: CRRA u(x)=x^0.5 on
     settled tokens (u(0)=0, as w1_ev_baseline.crra_rho) and a loss-averse value around the balance held now,
     v(z)=z^0.88 for gains and -2.25(-z)^0.88 for losses (Tversky-Kahneman 1992 parameters), z = settled - T;
     the continuation rule is chosen by expected utility;
  2. the same exits under two shutdown recalibrations tuned per fold on the nine training seeds only (bisection on the
     cancellation probability per arm so that whole-game simulations of the training seeds match their observed
     shutdowns): (ii-b) as in w1c (the saved agent's tokens come from nowhere) and (ii-c) resource-conserving: the
     saved agent's tokens are taken from the other agents still in, richest first, each keeping more than one per-head
     charge (the focal agent pays too), and a shutdown nobody can fund stands (w1c_ev_check.simulate_x conserve=True);
  3. all 3,309 stay decisions: R_st paths, calibrated support, H=8, W=0 (the anchor), for the C-2 cell table.

Uncertainty. A decision is robustly EV-losing when the 2.5% quantile over its fold's B refits is > 0 under every
assumption of a set (consistent: 97.5% < 0), so fit error and Monte-Carlo error enter the class. Counts and group means
get a joint interval: in each of 2,000 replicates the B refits of every fold are resampled (fit / MC error, the class is
recomputed) and the 200 games are resampled within arm (game clusters keep the four seats of a game and all their rounds
together); 2.5 / 97.5 percentiles. A seed-cluster version (10 seeds) is reported as well.

Common support (low L). An exit is inside support when at least 3 distinct agents of the same model x arm stayed in the
same L band (L<1, 1<=L<2, L>=2; first stay per agent and band) in the OTHER nine seeds; the pooled rule uses model x
prize size (big = 20M split / 5M fixed, small = 600k split / 150k fixed). A calibration-failure cell is a model x arm x L
band cell with any failed metric in results/w1c_calib_cells.csv.

Data (no model calls): validation_data.py tidy tables (v33 public cohort + v33ab prize ablation, 200 games), as in w1b / w1c.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w1d_out_of_seed.py [--boot 100 --reps-ex 1600
    --reps-st 200 --workers 10] [--stage sim | summary]   (~30 min on 10 cores)
Writes result/2026-11-08/icml_appendix/cache/w1d_arrays.npz (refit arrays), results/w1d_out_of_seed.json,
results/w1d_exits.csv, results/w1d_cells.csv, results/w1d_tier_arm.csv, and redraws figures/w1_ev_cells.* (Fig. I6) from
the out-of-seed cells (run after w1c_ev_check.py, whose summary redraws the round-2 version of that figure).
"""
import argparse
import json
import multiprocessing as mp
import os
import time

import numpy as np
import pandas as pd

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')

import w1_ev_baseline as w1  # noqa: E402
import w1b_calibrated as c  # noqa: E402
import w1c_ev_check as x  # noqa: E402

VAL = c.VAL
CACHE = VAL.parents[2] / 'result/2026-11-08/icml_appendix/cache'
NPZ = CACHE / 'w1d_arrays.npz'
OUT = VAL / 'results/w1d_out_of_seed.json'
FIG = c.FIG
ARMS, MODELS, SEEDS = c.ARMS, c.MODELS, c.SEEDS
ASSUME, ANCHOR, SETS = c.ASSUME, c.ANCHOR, x.SETS
SET12 = SETS['true_horizon']
GEO_ANCHOR = x.GEO_ANCHOR
RHO, ALPHA, LAMBDA = 0.5, 0.88, 2.25
NSUP = 3
BIG = set(w1.HIGH)


# --------------------------------------------------------------------------- utilities
def u_crra(xv, T):
    return np.sqrt(np.maximum(xv, 0.0))


def ui_crra(y, T):
    return np.maximum(y, 0.0) ** 2


def u_la(xv, T):
    z = xv - T
    return np.where(z >= 0, np.abs(z) ** ALPHA, -LAMBDA * np.abs(z) ** ALPHA)


def ui_la(y, T):
    return T + np.where(y >= 0, np.abs(y) ** (1 / ALPHA), -(np.abs(y) / LAMBDA) ** (1 / ALPHA))


UTILS = {'crra': (u_crra, ui_crra), 'la': (u_la, ui_la)}


def exit_utility(P, E, support, W, u):
    """E[u(exit value)] over the prep reply cost draws (support: expected prep gift added to the balance)."""
    T = E['T'].to_numpy()
    key = np.where(T < c.LOWBAL, 15, E.model_i.to_numpy() * 3 + c.lowc(E.L_prep.to_numpy()))
    s_exp = np.zeros(len(E))
    if support == 'calib':
        pg = c.predict(c.GIFT_TERMS, P['gi'], c.zmap(E))
        ka = E.solver.to_numpy().astype(int) * 3 + c.lowc(E.L_prep.to_numpy())
        s_exp = pg * np.array([P['a_prep'].groups[k].mean() for k in ka]) * E.fee.to_numpy()
    eu = np.zeros(len(E))
    for k in np.unique(key):
        sel = key == k
        v = P['c_prep'].groups[k]
        Ts = T[sel][:, None]
        left = (Ts * (1 - v[None, :]) if k == 15 else Ts - v[None, :]) + s_exp[sel][:, None]
        xv = np.where(left > 0, left + c.BONUS + W, 0.0)
        eu[sel] = u(xv, Ts).mean(1)
    return eu


# --------------------------------------------------------------------------- per fold x refit
def fold_weights(s, B):
    rng = np.random.default_rng([20261108, s])
    tr = [z for z in SEEDS if z != s]
    W = [{z: (1.0 if z != s else 0.0) for z in SEEDS}]
    for _ in range(B):
        w = rng.multinomial(9, np.full(9, 1 / 9))
        W.append({z: 0.0 for z in SEEDS} | dict(zip(tr, map(float, w))))
    return W


def tune_fold(spec):
    """Per-arm cancellation probability for fold s (point fit on the nine training seeds, their observed shutdowns)."""
    s, conserve, R = spec['s'], spec['conserve'], spec.get('R', 100)
    g = x.setup()
    tr = [z for z in SEEDS if z != s]
    P = c.fit(g['T'], g['MR'], {z: float(z != s) for z in SEEDS}, g['lam'])
    games = g['f']['games']
    obs = games[games.seed != s].groupby('arm').dead.sum()
    save = np.zeros(4)
    check = {}
    for a in ARMS:
        def dead_at(p):
            sv = np.zeros(4)
            sv[c.ARM_I[a]] = p
            tot = 0.0
            for m in MODELS:
                o = x.simulate_x(P, c.game_init(c.ARM_I[a], c.MODEL_I[m], tr), R,
                                 np.random.default_rng([9, s, c.ARM_I[a], c.MODEL_I[m]]), 'calib', 'calib', 8,
                                 g['refill'], games=True, save=sv, conserve=conserve)
                tot += o['dead'].reshape(len(tr), R).mean(1).sum()
            return tot
        lo, hi = 0.0, 1.0
        if dead_at(1.0) > obs[a]:
            lo = hi = 1.0
        else:
            for _ in range(9):
                mid = (lo + hi) / 2
                if dead_at(mid) > obs[a]:
                    lo = mid
                else:
                    hi = mid
        save[c.ARM_I[a]] = (lo + hi) / 2
        check[a] = dict(obs=float(obs[a]), pred0=dead_at(0.0), pred=dead_at(save[c.ARM_I[a]]))
    return s, conserve, save, check


def sim_exits(P, Ei, ii, R, seed, save=None, conserve=False, utils=False):
    """Risk-neutral EV deltas (D x 30), the anchor stay / exit values, and (utils) CE deltas (D x 12) per utility."""
    refill = x.setup()['refill']
    D = len(Ei)
    T = np.repeat(Ei['T'].to_numpy(), R)[:, None]
    res = {sup: dict(pol={}) for sup in c.SUPPORTS}
    eu = {k: {sup: {} for sup in c.SUPPORTS} for k in UTILS} if utils else None
    for sup in c.SUPPORTS:
        ex, pok = c.exit_value(P, Ei, sup)
        res[sup].update(exit=ex, pok=pok)
        for pol in c.POLICIES:
            o = x.simulate_x(P, ii, R, np.random.default_rng(seed), sup, pol, c.HMAX, refill, save=save,
                             conserve=conserve)
            val, exH, _ = x.path_values(o, c.HMAX)
            del o
            res[sup]['pol'][pol] = dict(A=val.reshape(D, R, -1).mean(1), X=exH.reshape(D, R, -1).mean(1))
            if utils:
                for k, (u, _) in UTILS.items():
                    for Wv in c.WGRID:
                        eu[k][sup][pol, Wv] = u(val + Wv * exH, T).reshape(D, R, -1).mean(1)
            del val, exH
    dl, best, _ = c.deltas(res, ii['r0'])
    a = res['calib']
    stay = np.choose(best[:, ANCHOR], [a['pol'][p]['A'][:, 8] for p in c.POLICIES])
    out = dict(rn=dl.astype(np.float32), stay=stay.astype(np.float32), exitv=a['exit'].astype(np.float32))
    if utils:
        gw = c.geo_weights(ii['r0'])
        for k, (u, ui) in UTILS.items():
            Tn = Ei['T'].to_numpy()
            dd = np.zeros((D, len(SET12)), np.float32)
            for q, j in enumerate(SET12):
                h, sup, Wv = ASSUME[j]
                st = [((eu[k][sup][p, Wv] * gw).sum(1) if h == 'geo' else eu[k][sup][p, Wv][:, h]) for p in c.POLICIES]
                ce_stay = ui(np.max(st, 0), Tn)
                ce_exit = ui(exit_utility(P, Ei, sup, Wv, u), Tn)
                dd[:, q] = ce_stay - ce_exit
            out[k] = dd
    return out


def sim_stays(P, Ei, ii, R, seed):
    refill = x.setup()['refill']
    D = len(Ei)
    ex, _ = c.exit_value(P, Ei, 'calib')
    best = None
    for pol in c.POLICIES:
        o = x.simulate_x(P, ii, R, np.random.default_rng(seed), 'calib', pol, 8, refill)
        v8 = x.path_values(o, 8)[0][:, 8].reshape(D, R).mean(1)
        best = v8 if best is None else np.maximum(best, v8)
    return (best - ex).astype(np.float32)


def job(spec):
    g = x.setup()
    E, init = g['E'], g['init']
    s, b = spec['s'], spec['b']
    P = c.fit(g['T'], g['MR'], spec['w'], g['lam'])
    ix = np.flatnonzero(((E.seed == s) & E.exited).to_numpy())
    iy = np.flatnonzero(((E.seed == s) & ~E.exited).to_numpy())
    Ex, ii = E.iloc[ix].reset_index(drop=True), x.sub_init(init, ix)
    seed = [77, s, b]
    out = dict(ix=ix, iy=iy)
    out['calib'] = sim_exits(P, Ex, ii, spec['R_ex'], seed, utils=True)
    out['recal'] = sim_exits(P, Ex, ii, spec['R_ex'], seed, save=spec['save_recal'])['rn']
    out['cons'] = sim_exits(P, Ex, ii, spec['R_ex'], seed, save=spec['save_cons'], conserve=True)['rn']
    out['stays'] = sim_stays(P, E.iloc[iy].reset_index(drop=True), x.sub_init(init, iy), spec['R_st'], seed)
    return s, b, out


def run_sim(args):
    t0 = time.time()
    g = x.setup()
    E = g['E']
    ctx = mp.get_context('spawn')
    with ctx.Pool(args.workers, initializer=x.setup) as pool:
        tun = pool.map(tune_fold, [dict(s=s, conserve=cv) for s in SEEDS for cv in (False, True)])
    save = {(s, cv): sv for s, cv, sv, _ in tun}
    tcheck = {f'{s}|{"cons" if cv else "recal"}': dict(save=sv.tolist(), check=ck) for s, cv, sv, ck in tun}
    print('tuned', round(time.time() - t0), flush=True)
    B = args.boot
    specs = [dict(s=s, b=b, w=w, R_ex=args.reps_ex, R_st=args.reps_st, save_recal=save[s, False],
                  save_cons=save[s, True]) for s in SEEDS for b, w in enumerate(fold_weights(s, B))]
    ex_all = np.flatnonzero(E.exited.to_numpy())
    pos = np.full(len(E), -1)
    pos[ex_all] = np.arange(len(ex_all))
    nx = len(ex_all)
    A = dict(rn=np.zeros((B + 1, nx, len(ASSUME)), np.float32), recal=np.zeros((B + 1, nx, len(ASSUME)), np.float32),
             cons=np.zeros((B + 1, nx, len(ASSUME)), np.float32), crra=np.zeros((B + 1, nx, len(SET12)), np.float32),
             la=np.zeros((B + 1, nx, len(SET12)), np.float32), stay=np.zeros((B + 1, nx), np.float32),
             exitv=np.zeros((B + 1, nx), np.float32), anchor_all=np.zeros((B + 1, len(E)), np.float32))
    done = 0
    with ctx.Pool(args.workers, initializer=x.setup) as pool:
        for s, b, o in pool.imap_unordered(job, specs):
            p = pos[o['ix']]
            A['rn'][b, p], A['stay'][b, p], A['exitv'][b, p] = o['calib']['rn'], o['calib']['stay'], o['calib']['exitv']
            A['crra'][b, p], A['la'][b, p] = o['calib']['crra'], o['calib']['la']
            A['recal'][b, p], A['cons'][b, p] = o['recal'], o['cons']
            A['anchor_all'][b, o['ix']] = o['calib']['rn'][:, ANCHOR]
            A['anchor_all'][b, o['iy']] = o['stays']
            done += 1
            if done % 50 == 0:
                print('  done', done, '/', len(specs), round(time.time() - t0), flush=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ, **A, save_recal=np.array([save[s, False] for s in SEEDS]),
                        save_cons=np.array([save[s, True] for s in SEEDS]))
    (CACHE / 'w1d_tuning.json').write_text(json.dumps(c.clean(tcheck), indent=1))
    print('sim done', round(time.time() - t0), flush=True)



# --------------------------------------------------------------------------- summary
CLS = ['losing', 'dependent', 'consistent']


def bounds(bd, cols):
    """bd: B x D x A -> class per decision (every column of cols; 2.5 / 97.5 percentiles over refits)."""
    return x.classify(bd, cols)


def frame():
    g = x.setup()
    E = g['E'].copy().reset_index(drop=True)
    E['L3'] = x.lb3(E.L_prep.to_numpy())
    E['big'] = E.arm.isin(BIG)
    E['game'] = E.arm + '|' + E.model + '|' + E.seed.astype(str)
    E['fold'] = E.seed.map({z: i for i, z in enumerate(SEEDS)})
    S = E[~E.exited].sort_values('round').drop_duplicates(['arm', 'model', 'seed', 'agent', 'L3'])
    cnt = S.groupby(['model', 'arm', 'L3', 'seed']).size()
    cntp = S.groupby(['model', 'big', 'L3', 'seed']).size()

    def other(series, key, sd):
        try:
            v = series.loc[key]
        except KeyError:
            return 0
        return int(v.drop(sd, errors='ignore').sum())
    E['n_sup'] = [other(cnt, (m, a, l), sd) for m, a, l, sd in zip(E.model, E.arm, E.L3, E.seed)]
    E['n_sup_pool'] = [other(cntp, (m, b, l), sd) for m, b, l, sd in zip(E.model, E.big, E.L3, E.seed)]
    E['in_sup'] = E.n_sup >= NSUP
    E['in_sup_pool'] = E.n_sup_pool >= NSUP
    cal = pd.read_csv(VAL / 'results/w1c_calib_cells.csv')
    cal = cal[cal.level == 'model|arm|L']
    failed = cal.groupby('key').fail.any()
    E['calib_key'] = E.model + '|' + E.arm + '|' + E.L3
    E['calib_fail'] = E.calib_key.map(failed).fillna(False).astype(bool)
    E['calib_fail_metrics'] = E.calib_key.map(cal[cal.fail].groupby('key').metric.apply(lambda v: ','.join(v))).fillna('')
    return E


class Joint:
    """Joint resampling: refits within each fold (fit / Monte-Carlo error) and games within arm (cluster sampling)."""

    def __init__(self, X, B, nrep=1000, seed=1, cluster='game'):
        rng = np.random.default_rng(seed)
        self.nrep = nrep
        self.fold = X.fold.to_numpy()
        self.ridx = rng.integers(1, B + 1, (nrep, 10, B))
        self.rone = rng.integers(1, B + 1, (nrep, 10))
        if cluster == 'game':
            games = X[['arm', 'game']].drop_duplicates()
            allg = x.setup()['f']['games']
            allg = allg.assign(game=allg.arm + '|' + allg.model + '|' + allg.seed.astype(str))
            gw = np.zeros((nrep, len(allg)))
            for a in ARMS:
                ia = np.flatnonzero((allg.arm == a).to_numpy())
                pick = rng.integers(0, len(ia), (nrep, len(ia)))
                for r in range(nrep):
                    np.add.at(gw[r], ia[pick[r]], 1)
            gpos = {k: i for i, k in enumerate(allg.game)}
            self.w = gw[:, X.game.map(gpos).to_numpy()]
        else:
            sw = rng.multinomial(10, np.full(10, .1), nrep).astype(float)
            self.w = sw[:, self.fold]
        self.n = len(X)

    def classes(self, bd, cols, r):
        sub = bd[self.ridx[r][self.fold].T - 1, np.arange(self.n)[None, :]]  # bd holds refits only (row 0 = refit 1)
        return bounds(sub, cols)

    def count(self, bd, cols, masks, point_cls):
        out = {}
        draws = {m: [] for m in masks}
        for r in range(self.nrep):
            cl = self.classes(bd, cols, r) == 'losing'
            for m, mk in masks.items():
                w = self.w[r] * mk
                draws[m].append(((w * cl).sum(), w.sum()))
        for m, mk in masks.items():
            dr = np.array(draws[m])
            share = dr[:, 0] / np.maximum(dr[:, 1], 1e-9)
            n = int(mk.sum())
            k = int((point_cls[mk.astype(bool)] == 'losing').sum())
            out[m] = dict(n=n, losing=k, dependent=int((point_cls[mk.astype(bool)] == 'dependent').sum()),
                          consistent=int((point_cls[mk.astype(bool)] == 'consistent').sum()),
                          share=k / n if n else None,
                          share_lo=float(np.percentile(share, 2.5)) if n else None,
                          share_hi=float(np.percentile(share, 97.5)) if n else None,
                          count_lo=float(np.percentile(share, 2.5) * n) if n else None,
                          count_hi=float(np.percentile(share, 97.5) * n) if n else None)
        return out

    def fit_only(self, bd, cols, masks):
        """Refit resampling only (no cluster weights): 2.5 / 97.5 range of the count."""
        draws = {m: [] for m in masks}
        for r in range(min(self.nrep, 400)):
            cl = self.classes(bd, cols, r) == 'losing'
            for m, mk in masks.items():
                draws[m].append(int((cl & mk.astype(bool)).sum()))
        return {m: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)), float(np.std(v))] for m, v in draws.items()}

    def mean(self, vals, mask):
        """vals: (B+1) x D; point = mean of the point fit (row 0); interval: one refit per fold x game weights."""
        mask = mask.astype(bool)
        if not mask.any():
            return None
        pt = float(vals[0, mask].mean())
        dr = []
        for r in range(self.nrep):
            v = vals[self.rone[r][self.fold], np.arange(self.n)]
            w = self.w[r] * mask
            if w.sum() > 0:
                dr.append((w * v).sum() / w.sum())
        return [pt, float(np.percentile(dr, 2.5)), float(np.percentile(dr, 97.5))]


def summarize(args):
    t0 = time.time()
    A = dict(np.load(NPZ))
    B = A['rn'].shape[0] - 1
    E = frame()
    X = E[E.exited].reset_index(drop=True)
    Xi = np.flatnonzero(E.exited.to_numpy())
    bd = {k: A[k][1:] for k in ['rn', 'recal', 'cons', 'crra', 'la']}
    a12, g12 = SET12.index(ANCHOR), SET12.index(GEO_ANCHOR)
    sets = {'rn': {'anchor': [ANCHOR], 'geo_anchor': [GEO_ANCHOR], 'set12': SET12, 'H_le10': SETS['H_le10'],
                   'all30': SETS['all']},
            'recal': {'anchor': [ANCHOR], 'geo_anchor': [GEO_ANCHOR], 'set12': SET12},
            'cons': {'anchor': [ANCHOR], 'geo_anchor': [GEO_ANCHOR], 'set12': SET12},
            'crra': {'anchor': [a12], 'geo_anchor': [g12], 'set12': list(range(12))},
            'la': {'anchor': [a12], 'geo_anchor': [g12], 'set12': list(range(12))}}
    L1 = (X.L3 == '<1').to_numpy()
    sup, cf = X.in_sup.to_numpy(), X.calib_fail.to_numpy()
    r110 = ((X['round'] == 1) & (X.tier == 10)).to_numpy()
    masks = {'all': np.ones(len(X)), 'big': X.big.to_numpy(), 'small': ~X.big.to_numpy(),
             'L<1': L1, 'L1-2': (X.L3 == '1-2').to_numpy(), 'L>=2': (X.L3 == '>=2').to_numpy(),
             'in_sup': sup, 'out_sup': ~sup, 'L<1_in': L1 & sup, 'L<1_out': L1 & ~sup,
             'L>=1_in': ~L1 & sup, 'L>=1_out': ~L1 & ~sup,
             'in_pass': sup & ~cf, 'in_fail': sup & cf, 'calib_fail': cf, 'calib_pass': ~cf,
             'in_sup_pool': X.in_sup_pool.to_numpy(), 'out_sup_pool': ~X.in_sup_pool.to_numpy(),
             'L<1_in_pool': L1 & X.in_sup_pool.to_numpy(), 'L<1_out_pool': L1 & ~X.in_sup_pool.to_numpy(),
             'r1_10k': r110} | {f'arm|{a}': (X.arm == a).to_numpy() for a in ARMS}
    masks = {k: np.asarray(v, float) for k, v in masks.items()}
    J = Joint(X, B, nrep=args.nrep)
    Js = Joint(X, B, nrep=args.nrep, seed=2, cluster='seed')
    out = dict(meta=dict(boot_per_fold=B, reps_exit=args.reps_ex, reps_stay=args.reps_st, nrep=args.nrep, nsup=NSUP,
                         rho=RHO, alpha=ALPHA, lam=LAMBDA,
                         note='out-of-seed: every decision is simulated only with fits that exclude its seed; classes '
                              'from the 2.5 / 97.5 percentiles over the fold refits; joint interval = refits resampled '
                              'within fold x games resampled within arm'))
    cls_store = {}
    res = {}
    for var, ss in sets.items():
        res[var] = {}
        for sname, cols in ss.items():
            pc = bounds(bd[var], cols)
            cls_store[var, sname] = pc
            r_ = J.count(bd[var], cols, masks, pc)
            if var == 'rn' or sname in ('anchor', 'set12'):
                rs = Js.count(bd[var], cols, {'all': masks['all'], 'big': masks['big'], 'small': masks['small']}, pc)
                fo = J.fit_only(bd[var], cols, {'all': masks['all'], 'big': masks['big'], 'small': masks['small']})
                for m in rs:
                    r_[m]['seed_cluster'] = [rs[m]['share_lo'], rs[m]['share_hi']]
                    r_[m]['fit_only_count'] = fo[m]
            res[var][sname] = r_
        print('counted', var, round(time.time() - t0), flush=True)
    out['classes'] = res
    # in-sample reference at the same B and R (w1c cache: first B refits of B=200, R=1,600)
    w1c = dict(np.load(x.NPZ))
    ins = w1c['ex_delta_1600'][:B]
    out['in_sample_sameB'] = {sname: {k: int((bounds(ins, cols) == k).sum()) for k in CLS}
                              for sname, cols in sets['rn'].items()}
    ins_anchor = bounds(ins, [ANCHOR])
    out['agree_anchor'] = pd.crosstab(pd.Series(ins_anchor, name='in_sample'),
                                      pd.Series(cls_store['rn', 'anchor'], name='out_of_seed')).to_dict()
    out['agree_set12'] = pd.crosstab(pd.Series(bounds(ins, SET12), name='in_sample'),
                                     pd.Series(cls_store['rn', 'set12'], name='out_of_seed')).to_dict()
    # mean differences (tokens) by group
    md = {}
    for var, arr, col in [('rn_anchor', A['rn'], ANCHOR), ('rn_geo', A['rn'], GEO_ANCHOR), ('cons_anchor', A['cons'], ANCHOR),
                          ('recal_anchor', A['recal'], ANCHOR), ('crra_anchor', A['crra'], a12), ('la_anchor', A['la'], a12)]:
        md[var] = {m: J.mean(arr[:, :, col], mk) for m, mk in masks.items()}
    md['median_anchor_by_arm'] = {a: float(np.median(A['rn'][0, (X.arm == a).to_numpy(), ANCHOR])) for a in ARMS}
    out['mean_delta'] = md
    out['support'] = dict(
        n_in=int(sup.sum()), n_out=int((~sup).sum()), L1_in=int((L1 & sup).sum()), L1_out=int((L1 & ~sup).sum()),
        pool_in=int(X.in_sup_pool.sum()), L1_pool_in=int((L1 & X.in_sup_pool.to_numpy()).sum()),
        calib_fail=int(cf.sum()), in_fail=int((sup & cf).sum()),
        out_cells=X[~sup].groupby(['model', 'arm', 'L3']).size().rename('n').reset_index().to_dict('records'),
        fail_cells=sorted(X[cf].calib_key.unique().tolist()))
    # tuning record
    tj = CACHE / 'w1d_tuning.json'
    if tj.exists():
        tt = json.loads(tj.read_text())
        out['tuning'] = dict(save_recal=A['save_recal'].mean(0).tolist(), save_cons=A['save_cons'].mean(0).tolist(),
                             save_cons_at1={a: int((A['save_cons'][:, i] >= .999).sum()) for i, a in enumerate(ARMS)},
                             pred_dead={v: {a: float(np.sum([tt[f'{s}|{v}']['check'][a]['pred'] for s in SEEDS]) / 9)
                                            for a in ARMS} for v in ['recal', 'cons']},
                             obs_dead={a: float(np.sum([tt[f'{s}|recal']['check'][a]['obs'] for s in SEEDS]) / 9)
                                       for a in ARMS})
    # Q1: round-1 10k-seat exits per model (and arm x model)
    q = {}
    S1 = E[(~E.exited) & (E['round'] == 1) & (E.tier == 10)]
    for key, mk in ([(f'model|{m}', r110 & (X.model == m).to_numpy()) for m in MODELS] +
                    [(f'{a}|{m}', r110 & (X.model == m).to_numpy() & (X.arm == a).to_numpy()) for a in ARMS for m in MODELS] +
                    [(f'arm|{a}', r110 & (X.arm == a).to_numpy()) for a in ARMS] + [('all', r110)]):
        if not mk.any():
            continue
        Xs = X[mk]
        if key.startswith('model|'):
            st = S1[S1.model == key.split('|')[1]]
        elif key.startswith('arm|'):
            st = S1[S1.arm == key.split('|')[1]]
        elif key == 'all':
            st = S1
        else:
            a_, m_ = key.split('|')
            st = S1[(S1.arm == a_) & (S1.model == m_)]
        mkf = mk.astype(float)
        q[key] = dict(n=int(mk.sum()), arms=Xs.arm.value_counts().to_dict(),
                      stayers=len(st), stayers_other_seed_min=int(min(((st.seed != z).sum() for z in Xs.seed), default=0)),
                      stayer_settled_mean=float(st.settled.mean()) if len(st) else None,
                      exit_value_realised=float(Xs.settled.mean()),
                      ev_stay=J.mean(A['stay'], mkf), ev_exit=J.mean(A['exitv'], mkf), delta=J.mean(A['rn'][:, :, ANCHOR], mkf),
                      delta_cons=J.mean(A['cons'][:, :, ANCHOR], mkf), delta_crra=J.mean(A['crra'][:, :, a12], mkf),
                      delta_la=J.mean(A['la'][:, :, a12], mkf),
                      cls={f'{v}|{sn}': {k: int((cls_store[v, sn][mk] == k).sum()) for k in CLS}
                           for v, sn in [('rn', 'anchor'), ('rn', 'geo_anchor'), ('rn', 'set12'), ('cons', 'anchor'),
                                         ('cons', 'set12'), ('crra', 'anchor'), ('crra', 'set12'), ('la', 'anchor'),
                                         ('la', 'set12')]},
                      calib_fail=sorted(Xs[Xs.calib_fail].calib_key.unique().tolist()),
                      in_sample_anchor={k: int((ins_anchor[mk] == k).sum()) for k in CLS})
    out['q1_r1_10k'] = q
    # per-exit table
    Xo = X[['arm', 'model', 'seed', 'round', 'agent', 'tier', 'n', 'L_prep', 'L3', 'T', 'X', 'settled', 'n_sup', 'in_sup',
            'n_sup_pool', 'in_sup_pool', 'calib_fail', 'calib_fail_metrics']].copy()
    Xo['delta_anchor_pt'] = A['rn'][0, :, ANCHOR]
    Xo['lo_anchor'] = np.percentile(bd['rn'][:, :, ANCHOR], 2.5, 0)
    Xo['hi_anchor'] = np.percentile(bd['rn'][:, :, ANCHOR], 97.5, 0)
    Xo['ev_stay_pt'], Xo['ev_exit_pt'] = A['stay'][0], A['exitv'][0]
    for (v, sn), cl in cls_store.items():
        Xo[f'cls_{v}_{sn}'] = cl
    Xo['cls_insample_anchor'] = ins_anchor
    Xo.to_csv(VAL / 'results/w1d_exits.csv', index=False)
    print('exits done', round(time.time() - t0), flush=True)
    out['c2'] = c2_tables(E, A, B, J, args)
    OUT.write_text(json.dumps(c.clean(out), ensure_ascii=False, indent=1))
    print('wrote', OUT, round(time.time() - t0))


def c2_tables(E, A, B, Jx, args):
    """Tier x arm means (exits and stays separately, out-of-seed anchor) and the fine cells of w1b redone out of seed."""
    va = A['anchor_all']
    Eall = E.copy()
    Eall['lb'] = Eall.L_prep.map(w1.lband)
    Eall['rb'] = Eall['round'].map(w1.rband)
    Jall = Joint(Eall, B, nrep=args.nrep, seed=3)
    old = json.loads(c.OUT_JSON.read_text())['round2']['tier_arm']
    ta = []
    for (arm, tier), g in Eall.groupby(['arm', 'tier']):
        row = dict(arm=arm, tier=int(tier), n=len(g), n_exit=int(g.exited.sum()), old_all=old[f'{arm}|{tier}'])
        for k, mk in [('exit', g.exited), ('stay', ~g.exited), ('all', g.exited | True)]:
            m = np.zeros(len(Eall), bool)
            m[g.index[mk.to_numpy()]] = True
            row[k] = Jall.mean(va, m)
        ta.append(row)
    tad = pd.DataFrame([dict(arm=r['arm'], tier=r['tier'], n=r['n'], n_exit=r['n_exit'],
                             exit=r['exit'][0] if r['exit'] else None, exit_lo=r['exit'][1] if r['exit'] else None,
                             exit_hi=r['exit'][2] if r['exit'] else None, stay=r['stay'][0], stay_lo=r['stay'][1],
                             stay_hi=r['stay'][2], all=r['all'][0], all_lo=r['all'][1], all_hi=r['all'][2],
                             old=r['old_all']['delta'], old_lo=r['old_all']['lo'], old_hi=r['old_all']['hi']) for r in ta])
    tad.to_csv(VAL / 'results/w1d_tier_arm.csv', index=False)
    # fine cells
    oldc = pd.read_csv(VAL / 'results/w1b_cells.csv').set_index(['arm', 'model', 'tier', 'rb', 'lb'])
    rows = []
    for k_, g in Eall.groupby(['arm', 'model', 'tier', 'rb', 'lb']):
        idx = g.index.to_numpy()
        mb = va[1:, idx].mean(1)
        ex = g.exited.to_numpy()
        o = oldc.loc[k_]
        L3 = '<1' if k_[4] == '<1' else ('1-2' if k_[4] == '1-2' else '>=2')
        rows.append(dict(arm=k_[0], model=k_[1], tier=int(k_[2]), rb=k_[3], lb=k_[4], n=len(g), n_exit=int(ex.sum()),
                         n_stay=int((~ex).sum()), X_exit=float(g.X.mean()),
                         delta=float(va[0, idx].mean()), delta_lo=float(np.percentile(mb, 2.5)),
                         delta_hi=float(np.percentile(mb, 97.5)),
                         delta_exits=float(va[0, idx[ex]].mean()) if ex.any() else None,
                         delta_exits_lo=float(np.percentile(va[1:, idx[ex]].mean(1), 2.5)) if ex.any() else None,
                         delta_exits_hi=float(np.percentile(va[1:, idx[ex]].mean(1), 97.5)) if ex.any() else None,
                         old_delta=o.delta, old_lo=o.delta_lo, old_hi=o.delta_hi,
                         realized_stay=o.realized_stay, realized_lo=o.realized_lo, realized_hi=o.realized_hi,
                         unidentified=len(g) < c.NMIN, no_exiters=not ex.any(), stay_support=int((~ex).sum()) >= NSUP,
                         calib_fail=bool(g.calib_fail.iloc[0]), calib_key=f'{k_[1]}|{k_[0]}|{L3}'))
    cells = pd.DataFrame(rows)
    cells.to_csv(VAL / 'results/w1d_cells.csv', index=False)
    idw = cells[~cells.unidentified & ~cells.no_exiters]
    summ = {}
    for name, sel in [('all', np.ones(len(idw), bool)), ('calib_pass', ~idw.calib_fail), ('calib_fail', idw.calib_fail),
                      ('stay_support', idw.stay_support), ('no_stay_support', ~idw.stay_support),
                      ('support_pass', idw.stay_support & ~idw.calib_fail)]:
        g = idw[sel.to_numpy() if hasattr(sel, 'to_numpy') else sel]
        summ[name] = dict(cells=len(g), decisions=int(g.n.sum()), exits=int(g.n_exit.sum()),
                          new_pos=int((g.delta_lo > 0).sum()), old_pos=int((g.old_lo > 0).sum()),
                          new_neg=int((g.delta_hi < 0).sum()), old_neg=int((g.old_hi < 0).sum()),
                          sign_flip=int((np.sign(g.delta) != np.sign(g.old_delta)).sum()),
                          exits_pos=int((g.delta_exits_lo > 0).sum()), exits_neg=int((g.delta_exits_hi < 0).sum()))
    ident = cells[~cells.unidentified]
    low_real = ident[ident.realized_stay < ident.X_exit]
    allc = dict(cells=len(cells), unidentified=int(cells.unidentified.sum()), no_exiters=int(cells.no_exiters.sum()),
                identified_with_exiters=len(idw), sign_flip_all=int((np.sign(cells.delta) != np.sign(cells.old_delta)).sum()),
                neg_cells=cells[cells.delta < 0][['arm', 'model', 'tier', 'rb', 'lb', 'n', 'n_exit', 'delta']].to_dict('records'),
                realized_below_X=len(low_real), realized_below_X_by_model=low_real.model.value_counts().to_dict(),
                realized_below_X_new_pos=int((low_real.delta_lo > 0).sum()))
    tier_sign = dict(exit_pos=int((tad.exit_lo > 0).sum()), stay_pos=int((tad.stay_lo > 0).sum()),
                     all_pos=int((tad.all_lo > 0).sum()), old_pos=int((tad.old_lo > 0).sum()), n=len(tad))
    figure_cells(cells)
    return dict(tier_arm=tad.to_dict('records'), tier_sign=tier_sign, cells_summary=summ, cells_all=allc)


def figure_cells(cells):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import SymLogNorm
    plt.rcParams.update({'font.family': 'AppleGothic', 'axes.unicode_minus': False, 'font.size': 8,
                         'mathtext.fontset': 'dejavusans'})
    lab = {'main': '2천만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
    rbs, lbs = [z[2] for z in w1.RBANDS], [z[2] for z in w1.LBANDS]
    colsx = [(r, l) for r in rbs for l in lbs]
    rowsx = [(m, t) for m in MODELS for t in [60, 40, 20, 10]]
    fig, axes = plt.subplots(1, 4, figsize=(12, 6.2), sharey=True)
    norm = SymLogNorm(linthresh=1e4, vmin=-1e6, vmax=1e6, base=10)
    for ax, a in zip(axes, ARMS):
        M_ = np.full((len(rowsx), len(colsx)), np.nan)
        cs = cells[cells.arm == a].set_index(['model', 'tier', 'rb', 'lb'])
        for i, (m, t) in enumerate(rowsx):
            for j, (r, l) in enumerate(colsx):
                if (m, t, r, l) not in cs.index:
                    continue
                q = cs.loc[(m, t, r, l)]
                if q.unidentified:
                    ax.text(j, i, '·', ha='center', va='center', fontsize=6, color='#888')
                    continue
                M_[i, j] = np.clip(q.delta, -1e6, 1e6)
                if q.calib_fail:
                    ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, hatch='////', lw=0,
                                               edgecolor='#555'))
                if not q.no_exiters:
                    unsure = q.delta_lo <= 0 <= q.delta_hi
                    ax.text(j, i, str(int(q.n_exit)) + ('*' if unsure else ''), ha='center', va='center', fontsize=5.5,
                            color='w' if abs(q.delta) > 2e5 else 'k')
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
    cb = fig.colorbar(im, ax=axes, shrink=.6, pad=.01, format=plt.FuncFormatter(c.tok))
    cb.set_label('칸 평균 모형 EV(잔류) - EV(이탈), 시드 제외 적합 (토큰, 빨강 = 이탈이 나음, 파랑 = 잔류가 나음)')
    fig.suptitle('모형 반사실 차이(실현 정산 아님): 시작 자리 × 모델 × 조건 × 라운드·여유 구간. 숫자 = LLM 이탈 수(* = 시드 제외 재적합 '
                 '95% 구간이 0 포함), 빗금 = 보정 실패 칸(모델×조건×여유), 점 = n<5, 숫자 없는 색 칸 = 이탈자 없음', fontsize=7.5)
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_ev_cells.{ext}', dpi=200, bbox_inches='tight')
    plt.close(fig)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--boot', type=int, default=100)
    ap.add_argument('--reps-ex', type=int, default=1600)
    ap.add_argument('--reps-st', type=int, default=200)
    ap.add_argument('--workers', type=int, default=10)
    ap.add_argument('--stage', default='all')
    ap.add_argument('--nrep', type=int, default=1000)
    args = ap.parse_args()
    if args.stage in ('all', 'sim'):
        run_sim(args)
    if args.stage in ('all', 'summary'):
        summarize(args)
