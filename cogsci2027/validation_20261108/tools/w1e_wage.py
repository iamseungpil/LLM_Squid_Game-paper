"""W1e (review round 5: Astra round 4 rows A-1 and Q1): the value of regular work as a per-round wage.

Round 4 paid regular work after EXIT as a constant W. The rulebook (squid5/prompts/en/e52_v33.md) says only that each
completed task is paid in tokens, with no amount, so no single wage is assumed here. Instead the wage w is paid for every
remaining round of the believed game from the round of exit on: an exit at the TALK before SOLVE of round t earns
w x (H - t + 1) under the anchor H = 8, and w x sum_H g_H (H - t + 1) under the geometric horizon (continue with
probability 7/8 after each round; g_H = w1b_calibrated.geo_weights, mean remaining rounds 8). The same wage is paid to a
later exit on a stay path (focal agent's continuation rules), so a high wage also raises EV(stay).

Paths. The out-of-seed fits and random numbers of w1d_out_of_seed are reused exactly (same fold weights, B = 100 refits
per held-out seed, same rng seeds, calibrated support): for every LLM exit (279, R = 1,600 paths) and every LLM stay
(3,309, R = 200, H = 8) the simulation is rerun to record, per continuation rule p, the mean settled value A_p and the
mean wage rounds earned by a later exit Y_p = E[1{t_x <= H} (H - t_x + 1)]. With the exit value V_x (w1b exit_value,
calibrated support) and the probability that the exit is paid pok, for every wage

    Delta(w) = max_p (A_p + w Y_p) - (V_x + w pok K),   K = H - t + 1 (or its geometric mean),

which is convex and piecewise linear in w, so the break-even wage w* (Delta(w*) = 0) is exact per fit:
w* = max over rules with Y_p < pok K of (A_p - V_x) / (pok K - Y_p) (inf if a rule with Y_p >= pok K has A_p > V_x).
Delta(0) reproduces w1d's anchor and geometric deltas (checked). Classes at each wage use w1d's rule (2.5 / 97.5
percentiles over the fold's refits); counts get w1d's joint interval (refits resampled within fold x games resampled
within arm, 1,000 replicates); group medians of w* get the same joint interval (one refit per fold x game weights).

Comparison scale (no wage is picked): s = EV(stay at w = 0) / K, the arena's expected settled tokens per remaining
believed round for that decision, and its realized counterpart for LLM stayers (settled tokens / remaining rounds).

Data (no model calls): validation_data.py tidy tables (v33 public cohort + v33ab prize ablation, 200 games), as in w1b-w1d.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w1e_wage.py [--stage sim | summary] [--workers 10]
Writes result/2026-11-08/icml_appendix/cache/w1e_wage_arrays.npz, results/w1e_wage.json, results/w1e_wage_exits.csv,
figures/w1_wage.{pdf,png}.
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

import w1b_calibrated as c  # noqa: E402
import w1c_ev_check as x  # noqa: E402
import w1d_out_of_seed as dd  # noqa: E402

VAL = c.VAL
NPZ = dd.CACHE / 'w1e_wage_arrays.npz'
OUT = VAL / 'results/w1e_wage.json'
ARMS, MODELS, SEEDS = c.ARMS, c.MODELS, c.SEEDS
WAGES = [0.0, 1_000.0, 2_000.0, 5_000.0, 10_000.0, 20_000.0, 50_000.0, 100_000.0]
H8 = 8


# --------------------------------------------------------------------------- simulation (w1d paths, wage rounds kept)
def wage_rounds(o, hmax):
    Hs = np.arange(hmax + 1)
    t = o['ex_rd'][:, None]
    return np.where(t <= Hs[None, :], Hs[None, :] - t + 1, 0).astype(np.float32)


def job(spec):
    g = x.setup()
    E, init, refill = g['E'], g['init'], g['refill']
    s, b = spec['s'], spec['b']
    P = c.fit(g['T'], g['MR'], spec['w'], g['lam'])
    ix = np.flatnonzero(((E.seed == s) & E.exited).to_numpy())
    iy = np.flatnonzero(((E.seed == s) & ~E.exited).to_numpy())
    seed = [77, s, b]
    out = dict(ix=ix, iy=iy)
    # exits: as w1d sim_exits, calibrated support, HMAX = 30
    Ex, ii = E.iloc[ix].reset_index(drop=True), x.sub_init(init, ix)
    D, R = len(Ex), spec['R_ex']
    ex, pok = c.exit_value(P, Ex, 'calib')
    gw = c.geo_weights(ii['r0'])
    a8, y8, ag, yg = (np.zeros((D, 4), np.float32) for _ in range(4))
    for k, pol in enumerate(c.POLICIES):
        o = x.simulate_x(P, ii, R, np.random.default_rng(seed), 'calib', pol, c.HMAX, refill)
        val = x.path_values(o, c.HMAX)[0].reshape(D, R, -1).mean(1)
        yr = wage_rounds(o, c.HMAX).reshape(D, R, -1).mean(1)
        del o
        a8[:, k], y8[:, k] = val[:, H8], yr[:, H8]
        ag[:, k], yg[:, k] = (val * gw).sum(1), (yr * gw).sum(1)
    out['ex'] = dict(a8=a8, y8=y8, ag=ag, yg=yg, exitv=ex.astype(np.float32), pok=pok.astype(np.float32))
    # stays: as w1d sim_stays (H = 8, R = 200)
    Ey, iy_ = E.iloc[iy].reset_index(drop=True), x.sub_init(init, iy)
    D, R = len(Ey), spec['R_st']
    ex, pok = c.exit_value(P, Ey, 'calib')
    a8, y8 = np.zeros((D, 4), np.float32), np.zeros((D, 4), np.float32)
    for k, pol in enumerate(c.POLICIES):
        o = x.simulate_x(P, iy_, R, np.random.default_rng(seed), 'calib', pol, H8, refill)
        a8[:, k] = x.path_values(o, H8)[0][:, H8].reshape(D, R).mean(1)
        y8[:, k] = wage_rounds(o, H8)[:, H8].reshape(D, R).mean(1)
        del o
    out['st'] = dict(a8=a8, y8=y8, exitv=ex.astype(np.float32), pok=pok.astype(np.float32))
    return s, b, out


def run_sim(args):
    t0 = time.time()
    g = x.setup()
    E = g['E']
    B = args.boot
    specs = [dict(s=s, b=b, w=w, R_ex=args.reps_ex, R_st=args.reps_st)
             for s in SEEDS for b, w in enumerate(dd.fold_weights(s, B))]
    ex_all, st_all = np.flatnonzero(E.exited.to_numpy()), np.flatnonzero(~E.exited.to_numpy())
    pe, ps = np.full(len(E), -1), np.full(len(E), -1)
    pe[ex_all], ps[st_all] = np.arange(len(ex_all)), np.arange(len(st_all))
    A = {f'ex_{k}': np.zeros((B + 1, len(ex_all), 4), np.float32) for k in ['a8', 'y8', 'ag', 'yg']}
    A |= {f'st_{k}': np.zeros((B + 1, len(st_all), 4), np.float32) for k in ['a8', 'y8']}
    for k in ['ex_exitv', 'ex_pok']:
        A[k] = np.zeros((B + 1, len(ex_all)), np.float32)
    for k in ['st_exitv', 'st_pok']:
        A[k] = np.zeros((B + 1, len(st_all)), np.float32)
    done = 0
    with mp.get_context('spawn').Pool(args.workers, initializer=x.setup) as pool:
        for s, b, o in pool.imap_unordered(job, specs):
            for pre, pos, idx in [('ex', pe, o['ix']), ('st', ps, o['iy'])]:
                for k, v in o[pre].items():
                    A[f'{pre}_{k}'][b, pos[idx]] = v
            done += 1
            if done % 50 == 0:
                print('  done', done, '/', len(specs), round(time.time() - t0), flush=True)
    dd.CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ, **A)
    print('sim done', round(time.time() - t0), flush=True)


# --------------------------------------------------------------------------- wage algebra
def delta_w(a, y, ev, pok, K, w):
    """a, y: ... x 4 rules; ev, pok, K broadcast to ...; Delta(w) = max_p (a + w y) - (ev + w pok K)."""
    w = np.asarray(w, float)
    return (a + w[..., None] * y).max(-1) - (ev + w * pok * K)


def wstar(a, y, ev, pok, K):
    """Exact break-even wage of max_p (a_p + w y_p) - (ev + w pok K) (may be < 0: exit better already at w = 0)."""
    slope = pok[..., None] * K[..., None] - y
    icpt = a - ev[..., None]
    neg = slope > 1e-9
    root = np.where(neg, icpt / np.where(neg, slope, 1.0), -np.inf)
    never = (~neg & (icpt > 0)).any(-1)
    return np.where(never, np.inf, root.max(-1))


def wmedian(J, vals, mask, q=50):
    """Group median (or quantile q) of vals ((B+1) x D): point = row 0, joint interval as w1d Joint.mean."""
    mask = mask.astype(bool)
    if not mask.any():
        return None

    def wq(v, w):
        o = np.argsort(v)
        cw = np.cumsum(w[o])
        return float(v[o][np.searchsorted(cw, cw[-1] * q / 100)])
    pt = float(np.percentile(vals[0, mask], q))
    dr = []
    for r in range(J.nrep):
        v = vals[J.rone[r][J.fold], np.arange(J.n)]
        w = J.w[r] * mask
        if w.sum() > 0:
            dr.append(wq(v, w))
    return [pt, float(np.percentile(dr, 2.5)), float(np.percentile(dr, 97.5))]


# --------------------------------------------------------------------------- summary
def summarize(args):
    t0 = time.time()
    A = dict(np.load(NPZ))
    W1D = dict(np.load(dd.NPZ))
    B = A['ex_a8'].shape[0] - 1
    E = dd.frame()
    X = E[E.exited].reset_index(drop=True)
    S = E[~E.exited].reset_index(drop=True)
    r0 = X['round'].to_numpy()
    K8 = (H8 - r0 + 1).astype(float)
    Kg = (c.geo_weights(r0) * np.maximum(np.arange(c.HMAX + 1)[None, :] - r0[:, None] + 1, 0)).sum(1)
    ev, pok = A['ex_exitv'], A['ex_pok']
    hz = {'anchor': (A['ex_a8'], A['ex_y8'], K8), 'geo': (A['ex_ag'], A['ex_yg'], Kg)}
    # check: Delta(0) = w1d deltas
    chk = {'anchor': float(np.abs(delta_w(A['ex_a8'], A['ex_y8'], ev, pok, K8, 0) - W1D['rn'][:, :, c.ANCHOR]).max()),
           'geo': float(np.abs(delta_w(A['ex_ag'], A['ex_yg'], ev, pok, Kg, 0) - W1D['rn'][:, :, dd.GEO_ANCHOR]).max()),
           'stay_anchor': float(np.abs(delta_w(A['st_a8'], A['st_y8'], A['st_exitv'], A['st_pok'],
                                               (H8 - S['round'].to_numpy() + 1.0), 0)
                                       - W1D['anchor_all'][:, ~E.exited.to_numpy()]).max())}
    print('check', chk, flush=True)
    ws = {h: wstar(a, y, ev, pok, K) for h, (a, y, K) in hz.items()}
    J = dd.Joint(X, B, nrep=args.nrep)
    r110 = ((X['round'] == 1) & (X.tier == 10)).to_numpy()
    masks = {'all': np.ones(len(X), bool), 'big': X.big.to_numpy(), 'small': ~X.big.to_numpy(), 'r1_10k': r110,
             'r1_10k_big': r110 & X.big.to_numpy(), 'r1_10k_small': r110 & ~X.big.to_numpy()}
    masks |= {f'arm|{a}': (X.arm == a).to_numpy() for a in ARMS}
    masks |= {f'model|{m}': (X.model == m).to_numpy() for m in MODELS}
    masks |= {f'L|{l}': (X.L3 == l).to_numpy() for l in ['<1', '1-2', '>=2']}
    masks |= {f'r1_10k|{a}': r110 & (X.arm == a).to_numpy() for a in ARMS}
    masks |= {f'r1_10k|{m}': r110 & (X.model == m).to_numpy() for m in MODELS}
    out = dict(meta=dict(boot_per_fold=B, nrep=args.nrep, wages=WAGES, H=H8, geo=c.GEO,
                         note='wage w per remaining believed round from the exit round on (H - t + 1 rounds); '
                              'out-of-seed paths of w1d; calibrated support; risk neutral',
                         check_delta0_maxabs=chk, Kgeo_mean=float(Kg.mean()), K8_mean=float(K8.mean())))
    # (1) w* by group
    sc = {}
    for h in hz:
        a, y, K = hz[h]
        s_stay = a.max(-1) / K  # EV(stay, w=0) per remaining round (rule chosen at w=0)
        sc[h] = s_stay
        wlo, whi = np.percentile(ws[h][1:], 2.5, 0), np.percentile(ws[h][1:], 97.5, 0)
        rat = ws[h] / s_stay
        grp = {}
        for m, mk in masks.items():
            if not mk.any():
                continue
            grp[m] = dict(n=int(mk.sum()), median=wmedian(J, ws[h], mk), q25=float(np.percentile(ws[h][0, mk], 25)),
                          q75=float(np.percentile(ws[h][0, mk], 75)), min=float(ws[h][0, mk].min()),
                          max=float(ws[h][0, mk].max()), n_le0=int((ws[h][0, mk] <= 0).sum()),
                          n_inf=int(np.isinf(ws[h][0, mk]).sum()),
                          lo_median=float(np.median(wlo[mk])), hi_median=float(np.median(whi[mk])),
                          per_round_stay=wmedian(J, s_stay, mk), ratio=wmedian(J, rat, mk),
                          ratio_q25=float(np.percentile(rat[0, mk], 25)), ratio_q75=float(np.percentile(rat[0, mk], 75)))
        out[f'wstar_{h}'] = grp
        print('wstar', h, round(time.time() - t0), flush=True)
    # (2) losing / consistent counts on the wage grid
    cnt = {}
    cm = {k: masks[k].astype(float) for k in ['all', 'big', 'small', 'r1_10k', 'r1_10k_big', 'r1_10k_small']
          + [f'arm|{a}' for a in ARMS] + [f'r1_10k|{a}' for a in ARMS]}
    for w in WAGES:
        bdw = np.stack([delta_w(a[1:], y[1:], ev[1:], pok[1:], K, w) for a, y, K in hz.values()], -1)
        row = {}
        for sname, cols in [('anchor', [0]), ('geo', [1]), ('both', [0, 1])]:
            pc = dd.bounds(bdw, cols)
            r_ = J.count(bdw, cols, cm, pc)
            row[sname] = r_
        cnt[str(int(w))] = row
        print('count w', w, round(time.time() - t0), flush=True)
    out['counts'] = cnt
    # stays at the same wages (anchor): how many LLM stays the wage would call exit-better
    rs = S['round'].to_numpy()
    Ks = (H8 - rs + 1).astype(float)
    sbig = S.big.to_numpy()
    st = {}
    for w in WAGES:
        bdw = delta_w(A['st_a8'][1:], A['st_y8'][1:], A['st_exitv'][1:], A['st_pok'][1:], Ks, w)[..., None]
        cl = dd.bounds(bdw, [0])
        st[str(int(w))] = {k: dict(n=int(mk.sum()), losing=int((cl[mk] == 'losing').sum()),
                                   consistent=int((cl[mk] == 'consistent').sum()))
                           for k, mk in [('all', np.ones(len(S), bool)), ('big', sbig), ('small', ~sbig),
                                         ('r1_10k', ((S['round'] == 1) & (S.tier == 10)).to_numpy())]}
    wst = wstar(A['st_a8'], A['st_y8'], A['st_exitv'], A['st_pok'], Ks)
    out['stays'] = dict(counts=st, wstar_median={k: float(np.median(wst[0, mk])) for k, mk in
                                                 [('all', np.ones(len(S), bool)), ('big', sbig), ('small', ~sbig)]},
                        wstar_by_arm={a: float(np.median(wst[0, (S.arm == a).to_numpy()])) for a in ARMS},
                        wstar_q25_by_arm={a: float(np.percentile(wst[0, (S.arm == a).to_numpy()], 25)) for a in ARMS},
                        wstar_r1_10k_by_arm={a: float(np.median(wst[0, ((S.arm == a) & (S['round'] == 1) & (S.tier == 10))
                                                                .to_numpy()])) for a in ARMS})
    # realized per-round settled value of LLM stayers (data, not the model)
    S['per_round_real'] = S.settled / Ks
    out['realized_stay_per_round'] = {a: dict(median=float(S[S.arm == a].per_round_real.median()),
                                              mean=float(S[S.arm == a].per_round_real.mean()))
                                      for a in ARMS}
    out['realized_stay_per_round_r1_10k'] = {a: dict(median=float(g.per_round_real.median()), mean=float(g.per_round_real.mean()),
                                                      n=len(g))
                                             for a in ARMS for g in [S[(S.arm == a) & (S['round'] == 1) & (S.tier == 10)]]}
    # per-exit table
    Xo = X[['arm', 'model', 'seed', 'round', 'agent', 'tier', 'L3', 'T', 'big']].copy()
    for h in hz:
        Xo[f'wstar_{h}'] = ws[h][0]
        Xo[f'wstar_{h}_lo'] = np.percentile(ws[h][1:], 2.5, 0)
        Xo[f'wstar_{h}_hi'] = np.percentile(ws[h][1:], 97.5, 0)
        Xo[f'stay_per_round_{h}'] = sc[h][0]
    Xo['K8'], Xo['Kgeo'], Xo['pok'] = K8, Kg, pok[0]
    Xo.to_csv(VAL / 'results/w1e_wage_exits.csv', index=False)
    OUT.write_text(json.dumps(c.clean(out), ensure_ascii=False, indent=1))
    figure(Xo, cnt)
    print('wrote', OUT, round(time.time() - t0))


def figure(Xo, cnt):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'AppleGothic', 'axes.unicode_minus': False, 'font.size': 8,
                         'mathtext.fontset': 'dejavusans'})
    lab = {'main': '2천만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    ax = axes[0]
    xs = np.array(WAGES)
    xp = np.maximum(xs, 300)
    for (h, ls), (grp, col, gl) in [((h, ls), g) for h, ls in [('anchor', '-'), ('geo', '--')]
                                     for g in [('big', '#1f4e9c', '큰 상금 (110)'), ('small', '#c0392b', '작은 상금 (169)')]]:
        k = np.array([cnt[str(int(w))][h][grp]['losing'] for w in WAGES])
        lo = np.array([cnt[str(int(w))][h][grp]['count_lo'] for w in WAGES])
        hi = np.array([cnt[str(int(w))][h][grp]['count_hi'] for w in WAGES])
        ax.plot(xp, k, ls, color=col, marker='o', ms=3,
                label=f'{gl}, {"H=8" if h == "anchor" else "기하 기간"}')
        ax.fill_between(xp, lo, hi, color=col, alpha=.12, lw=0)
    ax.set_xscale('log')
    ax.set_xticks(xp)
    ax.set_xticklabels([c.tok(w) for w in WAGES])
    ax.set_xlabel('남은 믿음 라운드마다의 일반 작업 보수 w (토큰)')
    ax.set_ylabel('견고한 손실 이탈 수')
    ax.legend(fontsize=6.5, frameon=False, handlelength=3.5)
    ax.set_title('(a) 보수에 따른 손실 판정 수 (띠 = 95% 구간)', fontsize=8)
    ax = axes[1]
    data = [np.clip(Xo[Xo.arm == a].wstar_anchor.to_numpy(), 1e2, 1e8) for a in ARMS]
    ax.boxplot(data, positions=range(4), widths=.5, showfliers=False)
    rng = np.random.default_rng(0)
    for i, (a, d_) in enumerate(zip(ARMS, data)):
        xa = Xo[Xo.arm == a]
        r1 = ((xa['round'] == 1) & (xa.tier == 10)).to_numpy()
        ax.scatter(i + rng.uniform(-.18, .18, len(d_)), d_, s=5, c=np.where(r1, '#c0392b', '#888'), alpha=.7, lw=0)
    ax.set_yscale('log')
    ax.set_xticks(range(4))
    ax.set_xticklabels([lab[a] for a in ARMS])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(c.tok))
    ax.set_ylabel('손익분기 보수 w* (토큰/라운드, H=8)')
    ax.set_title('(b) 이탈별 w* (빨강 = 1라운드 1만 자리, 원 적합, 100 이하는 100에 표시)', fontsize=8)
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(c.FIG / f'w1_wage.{ext}', dpi=200, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--boot', type=int, default=100)
    ap.add_argument('--reps-ex', type=int, default=1600)
    ap.add_argument('--reps-st', type=int, default=200)
    ap.add_argument('--workers', type=int, default=10)
    ap.add_argument('--nrep', type=int, default=1000)
    ap.add_argument('--stage', default='all')
    args = ap.parse_args()
    if args.stage in ('all', 'sim'):
        run_sim(args)
    if args.stage in ('all', 'summary'):
        summarize(args)
