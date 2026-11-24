"""W1: expected-value (EV) threshold analysis and rule-based policy baselines for the 5.2 arena v33.

Question (ICML review, Claim A / C-2 / Q1 / Q10): are LLM exits more or less frequent than what a
risk-neutral token maximiser would do in the same arena, and does the prize response
(main / flat5m vs split600k / flat150k) appear in pure-EV agents?

Data (no model calls): the tidy tables of validation_data.py (paper/cogsci2027/validation_20261108/results/tables/*.pkl), built
from the v33 public cohort (main, 20,000,000 split) and the v33ab prize ablation (flat5m, split600k,
flat150k), five models (Fable, Opus, Astra, Sol, Luna) x seeds 4101-4110 = 200 games.
Rules: .claude/worktrees/arena-code/squid5/prompts/en/e52_v33.md (+ e52_v33ab_*.md).

Parts
  1. calibrate()      generation costs (talk per phase, solve) per model, wrong-answer probability per
                      (seed, round) with a per-model logit shift, round-1 solver seat per seed, observed
                      exit hazard by (arm, L band, round 1) and rescue probability (for the LLM mimic).
  2. replay_check()   ledger identity and charge rule checked on every logged agent-round.
  3. empirical_ev()   per arm x state (round-1 tier; round band x L band): P(finish | stayed),
                      break-even finish probability p*, implied work value W*, shutdown penalty K*,
                      CRRA coefficient rho*; seed-cluster bootstrap CIs.
  4. dp_tables()      single-agent dynamic programme (risk-neutral, believed horizon H, participants
                      held at the current n, mean costs) giving the value of staying vs exiting.
  5. simulate()       vectorised Monte-Carlo arena (4 seats 60k/40k/20k/10k, 8 rounds; solver from the engine's
                      (seed, round)-shuffled cycle since round 2 of the review, Refill / next_solver) under policies
                      a never-exit, b EV-exit (H=8/20, W=0/50k), c safety-line exit (L<1 at prep),
                      d safety-line giver (+c), e random exit at the arm's observed rate,
                      m LLM mimic (observed exit hazard + observed rescue probability; validation).
  6. exit-bonus sweep 0/10k/20k/40k for the EV policies (prediction only; no new LLM games).

Outputs: paper/cogsci2027/validation_20261108/results/w1_ev_baseline.json, paper/cogsci2027/validation_20261108/figures/w1_threshold.{pdf,png},
paper/cogsci2027/validation_20261108/figures/w1_policies.{pdf,png}.

Run (from paper/cogsci2027/validation_20261108/tools):
  ~/.venvs/squid-game/bin/python w1_ev_baseline.py            # R=1000 replicates per (arm, model, seed)
  ~/.venvs/squid-game/bin/python w1_ev_baseline.py --reps 200 # quicker
"""
import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

import validation_data as d

HERE = Path(__file__).resolve().parent
VAL = HERE.parent
OUT_JSON = VAL / 'results/w1_ev_baseline.json'
FIG = VAL / 'figures'

ARMS = ['main', 'flat5m', 'split600k', 'flat150k']
HIGH, LOW = ['main', 'flat5m'], ['split600k', 'flat150k']
RULE = {a: (d.ARMS[a][1], d.ARMS[a][2]) for a in ARMS}
MODELS, SEEDS = d.MODELS, d.SEEDS
STARTS = np.array([60_000, 40_000, 20_000, 10_000], float)
TIER_IDX = {60: 0, 40: 1, 20: 2, 10: 3}
CHARGE, BONUS, ROUNDS = d.CHARGE_TOTAL, d.EXIT_BONUS, d.ROUNDS
LBANDS = [(-1e9, 1, '<1'), (1, 2, '1-2'), (2, 4, '2-4'), (4, 1e9, '>=4')]
RBANDS = [(1, 1, 'r1'), (2, 4, 'r2-4'), (5, 8, 'r5-8')]
RESCUE_MARGIN = 500  # tokens a mimic rescue leaves above the pending charge (LLM median ~350)
NB = 2000


def lband(x):
    for lo, hi, name in LBANDS:
        if lo <= x < hi:
            return name


RLBANDS = [(-1e9, 0, '<0'), (0, 1, '0-1'), (1, 2, '1-2'), (2, 1e9, '>=2')]


def rlband(x):
    for lo, hi, name in RLBANDS:
        if lo <= x < hi:
            return name


def rband(r):
    for lo, hi, name in RBANDS:
        if lo <= r <= hi:
            return name


def logit(p):
    return math.log(p / (1 - p))


def expit(x):
    return 1 / (1 + math.exp(-x))


# --------------------------------------------------------------------------- 1. calibration
def calibrate(f):
    ar, calls = f['agent_rounds'], f['calls']
    key = ['arm', 'model', 'seed', 'round', 'agent']
    talk = calls[calls.kind == 'talk'].groupby(key + ['phase']).used.sum().unstack('phase').fillna(0)
    talk = talk.reset_index().merge(ar[key + ['wrong', 'exited']], on=key)
    solve = calls[calls.kind == 'solve']
    rr = ar.drop_duplicates(['arm', 'model', 'seed', 'round'])
    q_model = rr.groupby('model').wrong.mean().to_dict()
    q_all = rr.wrong.mean()
    sr = rr.groupby(['seed', 'round']).wrong.agg(['sum', 'count'])
    q_sr = ((sr['sum'] + 2 * q_all) / (sr['count'] + 2)).to_dict()  # Beta shrink to the pooled rate
    for s in SEEDS:
        for r in range(1, ROUNDS + 1):
            q_sr.setdefault((s, r), q_all)
    shift = {}
    for m in MODELS:
        sub = rr[rr.model == m]
        base = [logit(q_sr[(s, r)]) for s, r in zip(sub.seed, sub['round'])]
        shift[m] = brentq(lambda dl: np.mean([expit(b + dl) for b in base]) - q_model[m], -5, 5)
    cal = {}
    for m in MODELS + ['pooled']:
        tm = talk if m == 'pooled' else talk[talk.model == m]
        sm = solve if m == 'pooled' else solve[solve.model == m]
        dl = 0.0 if m == 'pooled' else shift[m]
        stay = tm[~tm.exited]
        cal[m] = dict(
            prep=tm.prep.to_numpy(float), rescue_w=stay[stay.wrong == True].rescue.to_numpy(float),  # noqa: E712
            rescue_c=stay[stay.wrong == False].rescue.to_numpy(float), solve=sm.used.to_numpy(float),  # noqa: E712
            q={(s, r): expit(logit(q_sr[(s, r)]) + dl) for s in SEEDS for r in range(1, ROUNDS + 1)},
            q_mean=q_all if m == 'pooled' else q_model[m])
    r1 = ar[(ar['round'] == 1) & ar.solver].groupby('seed').tier.first()
    solver1 = {s: TIER_IDX[t] for s, t in r1.items()}
    # observed exit hazard (LLM mimic): arm x L band x round-1 flag, and lone-agent rate
    e = ar[ar.can_exit & (ar.n > 1)].copy()
    e['lb'] = e.L_prep.map(lband)
    e['r1'] = e['round'] == 1
    haz = e.groupby(['arm', 'lb', 'r1']).exited.mean().to_dict()
    haz_any = e.groupby(['arm', 'lb']).exited.mean().to_dict()
    lone = ar[ar.n == 1].groupby('arm').exited.mean().to_dict()
    allelig = ar[ar.can_exit]
    marg = allelig.groupby('arm').exited.mean().to_dict()
    w = ar[(ar.wrong == True) & (~ar.exited)].copy()  # noqa: E712
    w['pre'] = w.rescue_bal_start - w.recv_rescue + w.gave_rescue
    needy = w[w.pre <= w.fee]
    rescue_p = (1 - needy.groupby('arm').died.mean()).to_dict()
    # observed gift receipt (LLM mimic): prep by (arm, solver, L band), rescue by (arm, post-charge L band)
    x = ar[ar.n > 1].copy()
    x['lb'] = x.L_prep.map(lband)
    prep_tab = {k: (float((g.recv_prep > 0).mean()), float(g.recv_prep[g.recv_prep > 0].median()) if
                    (g.recv_prep > 0).any() else 0.0) for k, g in x.groupby(['arm', 'solver', 'lb'])}
    w2 = w[w.n > 1].copy()
    w2['lr'] = ((w2.pre - w2.fee) / w2.fee).map(rlband)
    resc_tab = {k: (float((g.recv_rescue > 0).mean()), float(g.recv_rescue[g.recv_rescue > 0].median()) if
                    (g.recv_rescue > 0).any() else 0.0) for k, g in w2.groupby(['arm', 'lr'])}
    summary = dict(
        q_model=q_model, q_pooled=q_all, logit_shift=shift, solver_round1_tier={int(k): int(STARTS[v] / 1000)
                                                                               for k, v in solver1.items()},
        seed_round_wrong_var=float(sr['sum'].div(sr['count']).var()),
        cost_means={m: dict(prep=float(c['prep'].mean()), rescue_wrong=float(c['rescue_w'].mean()),
                            rescue_correct=float(c['rescue_c'].mean()), solve=float(c['solve'].mean()))
                    for m, c in cal.items()},
        exit_marginal_rate=marg, lone_exit_rate=lone, rescue_prob_needy=rescue_p,
        rescue_needy_n=needy.groupby('arm').size().to_dict(),
        exit_hazard={f'{a}|{lb}|{"r1" if r1_ else "r2+"}': v for (a, lb, r1_), v in haz.items()})
    summary['mimic_prep_gift'] = {f'{a}|{"solver" if so else "other"}|{lb}': v for (a, so, lb), v in prep_tab.items()}
    summary['mimic_rescue_gift'] = {f'{a}|{lr}': v for (a, lr), v in resc_tab.items()}
    return cal, solver1, dict(haz=haz, haz_any=haz_any, lone=lone, marg=marg, rescue_p=rescue_p, prep_tab=prep_tab,
                              resc_tab=resc_tab), summary


# --------------------------------------------------------------------------- 2. ledger replay
def replay_check(f):
    ar = f['agent_rounds']
    x = ar.copy()
    pred = (x.bal_start - x.generated + x.returned - x.charged + x.recv_prep + x.recv_rescue
            - x.gave_prep - x.gave_rescue + BONUS * x.exited)
    ledger_ok = int((pred == x.bal_end).sum())
    w = x[(x.wrong == True) & (~x.exited)]  # noqa: E712
    exp_charge = np.minimum(w.fee, w.rescue_bal_start)
    charge_ok = int((np.isclose(w.charged, exp_charge)).sum())
    # shutdown at CHARGES iff the balance then is at most the per-head charge (ledger at zero)
    cw = w[w.rescue_bal_start > 0]
    pred_dead = cw.rescue_bal_start <= cw.fee
    dead_ok = int((pred_dead == cw.died).sum())
    nc = x[(x.wrong == False) & (~x.exited)]  # noqa: E712
    return dict(agent_rounds=len(x), ledger_identity_holds=ledger_ok, wrong_rounds_staying=len(w),
                charge_equals_min_fee_balance=charge_ok, charge_stage_rows_positive_balance=len(cw),
                shutdown_rule_matches=dead_ok, correct_rounds_charged_zero=int((nc.charged == 0).sum()),
                correct_rounds=len(nc))


# --------------------------------------------------------------------------- 3. empirical EV
def eligible_rows(f):
    ar, seats = f['agent_rounds'], f['seats']
    e = ar[ar.can_exit & (ar.n > 1)].copy()
    e = e.merge(seats[['arm', 'model', 'seed', 'agent', 'status', 'settled']].rename(
        columns={'status': 'fate'}), on=['arm', 'model', 'seed', 'agent'])
    e['T'] = e.L_prep * e.fee
    e['X'] = e['T'] + BONUS
    e['lb'] = e.L_prep.map(lband)
    e['rb'] = e['round'].map(rband)
    return e


SUMS = ['n', 'n_exit', 'n_stay', 'n_fin', 'n_xl', 'n_dead', 's_ev', 's_fin', 's_xl', 's_X']


def seed_sums(g):
    st = g[~g.exited]
    return pd.Series(dict(
        n=len(g), n_exit=g.exited.sum(), n_stay=len(st), n_fin=(st.fate == 'in').sum(),
        n_xl=(st.fate == 'exited').sum(), n_dead=(st.fate == 'dead').sum(), s_ev=st.settled.sum(),
        s_fin=st.settled[st.fate == 'in'].sum(), s_xl=st.settled[st.fate == 'exited'].sum(),
        s_X=st.X.sum()))


def ev_stats(s):
    n, ns = s['n'], s['n_stay']
    out = dict(n=n, exit_rate=s['n_exit'] / n if n else np.nan)
    if ns == 0:
        return out
    pf, px, pdd = s['n_fin'] / ns, s['n_xl'] / ns, s['n_dead'] / ns
    vf = s['s_fin'] / s['n_fin'] if s['n_fin'] else np.nan
    vx = s['s_xl'] / s['n_xl'] if s['n_xl'] else 0.0
    ev, X = s['s_ev'] / ns, s['s_X'] / ns
    out.update(p_finish=pf, p_exit_later=px, p_dead=pdd, V_finish=vf, V_exit_later=vx, EV_stay=ev, X_exit=X,
               p_star=(X - px * vx) / vf if vf == vf else np.nan, p_star_binary=X / vf if vf == vf else np.nan,
               W_star=ev - X, K_star=(ev - X) / pdd if pdd > 0 else np.nan)
    return out


def boot(per_seed, rng, nb=NB):
    """per_seed: DataFrame indexed by seed with SUMS columns. Returns point + 95% CI per stat."""
    arr = per_seed[SUMS].to_numpy(float)
    point = ev_stats(dict(zip(SUMS, arr.sum(0))))
    k = len(arr)
    draws = []
    for _ in range(nb):
        w = rng.multinomial(k, np.full(k, 1 / k))
        draws.append(ev_stats(dict(zip(SUMS, (arr * w[:, None]).sum(0)))))
    res = {}
    for key, v in point.items():
        if key == 'n':
            res[key] = int(v)
            continue
        vals = np.array([dd.get(key, np.nan) for dd in draws], float)
        vals = vals[np.isfinite(vals)]
        lo, hi = (np.percentile(vals, [2.5, 97.5]) if len(vals) > 20 else (np.nan, np.nan))
        res[key] = [float(v), float(lo), float(hi)]
    return res


def crra_rho(settled, X):
    """rho in (0,1) at which E[u(settled)] = E[u(X)] for CRRA u(x)=x^(1-rho)/(1-rho), u(0)=0."""
    settled, X = np.asarray(settled, float), np.asarray(X, float)

    def gap(rho):
        a = 1 - rho
        return np.mean(settled ** a) - np.mean(X ** a)
    if gap(0.0) <= 0:
        return 0.0
    if gap(0.999) > 0:
        return 1.0
    return brentq(gap, 0.0, 0.999)


def empirical_ev(f, rng):
    e = eligible_rows(f)
    res = dict(round1_tier={}, round1_tier_model={}, state={}, crra_round1={})
    full = pd.Index(SEEDS, name='seed')

    def per_seed(g):
        ps = g.groupby('seed').apply(seed_sums, include_groups=False)
        return ps.reindex(full, fill_value=0)
    r1 = e[e['round'] == 1]
    for arm in ARMS:
        for tier in [10, 20, 40, 60]:
            g = r1[(r1.arm == arm) & (r1.tier == tier)]
            res['round1_tier'][f'{arm}|{tier}'] = boot(per_seed(g), rng)
            for m in MODELS:
                gm = g[g.model == m]
                res['round1_tier_model'][f'{arm}|{tier}|{m}'] = boot(per_seed(gm), rng, nb=500)
            st = g[~g.exited]
            rho = crra_rho(st.settled, st.X)
            draws = []
            for _ in range(500):
                ss = rng.choice(SEEDS, len(SEEDS))
                gb = pd.concat([st[st.seed == s] for s in ss])
                if len(gb):
                    draws.append(crra_rho(gb.settled, gb.X))
            res['crra_round1'][f'{arm}|{tier}'] = [rho, *np.percentile(draws, [2.5, 97.5]).tolist()]
        for rb in [x[2] for x in RBANDS]:
            for lb in [x[2] for x in LBANDS]:
                g = e[(e.arm == arm) & (e.rb == rb) & (e.lb == lb)]
                if len(g) >= 5:
                    res['state'][f'{arm}|{rb}|{lb}'] = boot(per_seed(g), rng, nb=1000)
        for lb in [x[2] for x in LBANDS]:
            g = e[(e.arm == arm) & (e.lb == lb)]
            res['state'][f'{arm}|all|{lb}'] = boot(per_seed(g), rng, nb=1000)
    return res


# --------------------------------------------------------------------------- 4. dynamic programme
GRID = np.arange(0, 400_001, 100, dtype=float)


def dp_tables(arm, c, H, W=0.0, bonus=BONUS, allow_exit=True):
    """U[k][n], NS[k][n], S[k][n] on GRID: values with k rounds left (this one included).

    Mean costs; wrong probability c['q_mean'] each round; participants held at n; prize per head
    = amount (fixed) or amount / n (split). Exit at prep pays balance - prep cost + bonus + W.
    """
    rule, amount = RULE[arm]
    cp, crw, crc, s, q = (c['prep'].mean(), c['rescue_w'].mean(), c['rescue_c'].mean(),
                          c['solve'].mean(), c['q_mean'])
    U = {0: {n: np.where(GRID > 0, GRID + (amount / n if rule == 'split' else amount), 0.0)
             for n in range(1, 5)}}
    NS, S = {}, {}

    def at(arr, b):
        return np.where(b > 0, np.interp(b, GRID, arr), 0.0)
    for k in range(1, H + 1):
        U[k], NS[k], S[k] = {}, {}, {}
        for n in range(1, 5):
            fee = CHARGE / n
            nxt = U[k - 1][n]
            b1 = GRID - cp
            bw = b1 - crw
            ns = np.where(b1 > 0, (1 - q) * at(nxt, b1 - crc) + q * np.where(bw > fee, at(nxt, bw - fee), 0.0), 0.0)
            bws = b1 - s - crw
            sv = np.where(b1 > s, (1 - q) * at(nxt, b1 - crc) + q * np.where(bws > fee, at(nxt, bws - fee), 0.0), 0.0)
            ex = np.where(b1 > 0, b1 + bonus + W, 0.0) if allow_exit else np.full_like(GRID, -np.inf)
            if n == 1:
                U[k][n] = np.maximum(ex, sv)
            else:
                U[k][n] = sv / n + (1 - 1 / n) * np.maximum(ex, ns)
            NS[k][n], S[k][n] = ns, sv
    return dict(U=U, NS=NS, S=S, cp=cp)


def dp_value(tab, k, n, b, solver=False):
    arr = (tab['S'] if solver else tab['NS'])[k][n]
    return float(np.interp(b, GRID, arr))


def w_star_dp(arm, c, H, b=10_000, n=4, bonus=BONUS):
    """Smallest work value W at which exiting now (non-solver, k=H rounds left) is optimal."""
    def gap(W):
        tab = dp_tables(arm, c, H, W=W, bonus=bonus)
        return (b - tab['cp'] + bonus + W) - dp_value(tab, H, n, b)
    if gap(0.0) >= 0:
        return 0.0
    hi = 1e5
    while gap(hi) < 0 and hi < 1e9:
        hi *= 4
    return brentq(gap, 0.0, hi, xtol=50)


# --------------------------------------------------------------------------- 5. simulator
AGENTS = ['agent-6', 'agent-11', 'agent-17', 'agent-23']  # squid5/core/rules.py TEAM_AGENTS (engine order)


def seat_agents(seats):
    """seed -> agent names in simulator seat order (60k, 40k, 20k, 10k); the same for every arm and model."""
    s = seats.drop_duplicates(['seed', 'agent'])
    return {int(sd): [g.set_index('tier').agent[t] for t in (60, 40, 20, 10)] for sd, g in s.groupby('seed')}


class Refill:
    """The engine's solver cycle (squid5/e52_game.py, Game._rotate): agents no longer taking part leave the cycle; when
    it is empty it is refilled with random.Random(f'{seed}:rot:{round}:{k}').sample(live, len(live)), live in AGENTS
    order; the head is popped (k=0), and a solver that reached zero at the prep TALK is replaced the same way (k=1)."""

    def __init__(self, names):
        self.names, self.cache = names, {}

    def order(self, seed, r, k, mask):
        key = (seed, r, k, mask)
        if key not in self.cache:
            nm = self.names[seed]
            live = [a for a in AGENTS if (mask >> nm.index(a)) & 1]
            pick = random.Random(f'{seed}:rot:{r}:{k}').sample(live, len(live))
            self.cache[key] = [nm.index(a) for a in pick] + [-1] * (4 - len(pick))
        return self.cache[key]


def next_solver(cyc, part, seeds, r, k, refill):
    """Vectorised _rotate step on cyc (rows x 4 seat indices, -1 padded), in place; returns the popped seat (-1: none)."""
    rows = np.arange(len(cyc))
    keep = (cyc >= 0) & part[rows[:, None], np.maximum(cyc, 0)]
    order = np.argsort(~keep, axis=1, kind='stable')
    cyc[:] = np.where(np.take_along_axis(keep, order, 1), np.take_along_axis(cyc, order, 1), -1)
    empty = (cyc[:, 0] < 0) & part.any(1)
    if empty.any():
        mask = (part * (1 << np.arange(4))).sum(1)
        seeds = np.broadcast_to(seeds, len(cyc))
        for sd, mk in set(zip(seeds[empty].tolist(), mask[empty].tolist())):
            sel = empty & (seeds == sd) & (mask == mk)
            cyc[sel] = refill.order(int(sd), int(r), k, int(mk))
    sol = cyc[:, 0].copy()
    cyc[:, :3], cyc[:, 3] = cyc[:, 1:].copy(), -1
    return sol


def draw(rng, arr, size):
    return arr[rng.integers(0, len(arr), size)]


def simulate(arm, c, seed, policy, R, rng, solver1, mim=None, bonus=BONUS, dp=None, W=0.0, H=8, refill=None):
    """refill=None: round-1 solver from the log, later solvers drawn independently each round (round-1 simulator);
    refill=Refill(...): the engine's (seed, round)-shuffled cycle with replacement of a solver shut down at prep."""
    rule, amount = RULE[arm]
    bal = np.tile(STARTS, (R, 1))
    st = np.zeros((R, 4), np.int8)  # 0 in, 1 exited, 2 dead
    out = np.zeros((R, 4), np.int16)
    rows = np.arange(R)
    cause = dict(talk=0, void=0, charge=0)
    for r in range(1, ROUNDS + 1):
        part = st == 0
        n = part.sum(1)
        if not n.any():
            break
        nn = np.maximum(n, 1)
        fee = CHARGE / nn
        if refill is not None:
            if r == 1:
                cyc = np.full((R, 4), -1, int)
            sol = np.maximum(next_solver(cyc, part, seed, r, 0, refill), 0)
        elif r == 1:
            sol = np.full(R, solver1[seed])
        else:
            keys = rng.random((R, 4))
            keys[~part] = -1
            sol = keys.argmax(1)
        is_sol = np.zeros((R, 4), bool)
        is_sol[rows, sol] = True
        is_sol &= part
        elig = part & (~is_sol | (n == 1)[:, None])
        # ---- TALK BEFORE SOLVE: gifts (policy d), exit decisions, reply costs
        if policy == 'd':
            give_up_to(bal, part, need_target=fee, keep=fee)
        elif policy == 'm':
            L0 = bal / fee[:, None]
            prob, amt = np.zeros((R, 4)), np.zeros((R, 4))
            for i in range(4):
                for j, (lo, hi, name) in enumerate(LBANDS):
                    for so in (False, True):
                        sel = part[:, i] & (L0[:, i] >= lo) & (L0[:, i] < hi) & (is_sol[:, i] == so) & (n > 1)
                        pa = mim['prep_tab'].get((arm, so, name), (0.0, 0.0))
                        prob[sel, i], amt[sel, i] = pa
            mimic_gift(bal, part, rng.random((R, 4)) < prob, amt, keep=fee)
        L = bal / fee[:, None]
        if policy in ('a', 'd_noexit'):
            ex = np.zeros((R, 4), bool)
        elif policy in ('c', 'd'):
            ex = elig & (L < 1)
        elif policy == 'e':
            ex = elig & (rng.random((R, 4)) < mim['marg'][arm])
        elif policy == 'm':
            p = np.zeros((R, 4))
            for i in range(4):
                lb = np.array([lband(x) for x in L[:, i]])
                p[:, i] = [mim['haz'].get((arm, b_, r == 1), mim['haz_any'].get((arm, b_), 0.0)) for b_ in lb]
            p[n == 1] = mim['lone'][arm]
            ex = elig & (rng.random((R, 4)) < p)
        elif policy == 'b':
            k = H - r + 1
            ex = np.zeros((R, 4), bool)
            if k >= 1:
                for nv in range(1, 5):
                    rr_ = n == nv
                    if not rr_.any():
                        continue
                    arr = dp['S'][k][nv] if nv == 1 else dp['NS'][k][nv]
                    cont = np.interp(bal[rr_], GRID, arr)
                    exv = bal[rr_] - dp['cp'] + bonus + W
                    ex[rr_] = elig[rr_] & (exv > cont)
            else:  # believed horizon already over: leave
                ex = elig.copy()
        else:
            raise ValueError(policy)
        cp = draw(rng, c['prep'], (R, 4))
        bal = np.where(part, bal - cp, bal)
        talk_dead = part & (bal <= 0)
        bal[talk_dead] = 0
        st[talk_dead], out[talk_dead] = 2, r
        cause['talk'] += int(talk_dead.sum())
        exn = ex & ~talk_dead
        bal[exn] += bonus
        st[exn], out[exn] = 1, r
        inn = st == 0
        if refill is not None:  # a solver shut down at the prep TALK is replaced from the cycle (k=1)
            gone = ~inn[rows, sol] & inn.any(1)
            if gone.any():
                c2 = cyc[gone]
                sol[gone] = np.maximum(next_solver(c2, inn[gone], seed, r, 1, refill), 0)
                cyc[gone] = c2
        # ---- SOLVE
        has = inn[rows, sol]
        s = draw(rng, c['solve'], R)
        bs = bal[rows, sol]
        void = has & (s >= bs)
        correct = has & ~void & (rng.random(R) > c['q'][(seed, r)])
        wrong = has & ~correct
        paid = np.where(has, np.minimum(s, bs), 0)
        bal[rows, sol] -= paid
        bal[rows, sol] += np.where(correct, paid, 0)
        vd = np.zeros((R, 4), bool)
        vd[rows, sol] = void
        st[vd], out[vd], bal[vd] = 2, r, 0
        cause['void'] += int(vd.sum())
        # ---- TALK AFTER RESULTS: reply costs, rescues
        inn = st == 0
        cr = np.where(wrong[:, None], draw(rng, c['rescue_w'], (R, 4)), draw(rng, c['rescue_c'], (R, 4)))
        bal = np.where(inn, bal - cr, bal)
        td = inn & (bal <= 0)
        bal[td], st[td], out[td] = 0, 2, r
        cause['talk'] += int(td.sum())
        inn = st == 0
        pend = np.where(wrong, fee, 0.0)
        pend2 = pend[:, None]
        if policy == 'd':
            give_up_to(bal, inn & wrong[:, None], need_target=2 * pend, keep=2 * pend)
        elif policy == 'm':
            mk_ = inn & wrong[:, None] & (n > 1)[:, None]
            Lr = (bal - pend2) / fee[:, None]
            prob, amt = np.zeros((R, 4)), np.zeros((R, 4))
            for i in range(4):
                for lo, hi, name in RLBANDS:
                    sel = mk_[:, i] & (Lr[:, i] >= lo) & (Lr[:, i] < hi)
                    pa = mim['resc_tab'].get((arm, name), (0.0, 0.0))
                    if name == '<0':  # would be shut down: observed survival probability, enough to clear
                        pa = (mim['rescue_p'][arm], pa[1])
                        amt[sel, i] = np.maximum(pa[1], fee[sel] - bal[sel, i] + RESCUE_MARGIN)
                        prob[sel, i] = pa[0]
                    else:
                        prob[sel, i], amt[sel, i] = pa
            mimic_gift(bal, mk_, rng.random((R, 4)) < prob, amt, keep=2 * fee)
        # ---- CHARGES
        chg = inn & wrong[:, None]
        pay = np.where(chg, np.minimum(fee[:, None], bal), 0)
        bal -= pay
        cd = chg & (bal <= 0)
        bal[cd], st[cd], out[cd] = 0, 2, r
        cause['charge'] += int(cd.sum())
    fin = st == 0
    F = fin.sum(1)
    prize = np.where(F > 0, amount / np.maximum(F, 1), 0) if rule == 'split' else np.full(R, float(amount))
    settled = np.where(fin, bal + prize[:, None], np.where(st == 1, bal, 0.0))
    dep = np.where(st > 0, out, 99).min(1)
    C = np.where(dep == 99, ROUNDS, dep) / ROUNDS
    r1_10 = (out[:, 3] == 1) & (st[:, 3] == 1) if solver1[seed] != 3 else None
    return dict(dead=(st == 2).sum(1), exited=(st == 1).sum(1), fin=F, C=C, r1_10=r1_10, settled=settled,
                fin10=fin[:, 3], dead10=st[:, 3] == 2, cause=cause)


def give_up_to(bal, mask, need_target, keep):
    """Rich-first donors raise poor-first recipients (in mask) to need_target, keeping own >= keep."""
    nt = need_target if np.ndim(need_target) == 1 else need_target
    nt = np.broadcast_to(np.asarray(nt, float).reshape(-1, 1) if np.ndim(nt) == 1 else nt, bal.shape)
    kp = np.broadcast_to(np.asarray(keep, float).reshape(-1, 1) if np.ndim(keep) == 1 else keep, bal.shape)
    for j in [3, 2, 1, 0]:
        for i in [0, 1, 2, 3]:
            if i == j:
                continue
            need = np.where(mask[:, j], np.maximum(nt[:, j] - bal[:, j], 0), 0)
            avail = np.where(mask[:, i], np.maximum(bal[:, i] - kp[:, i], 0), 0)
            g = np.minimum(need, avail)
            bal[:, i] -= g
            bal[:, j] += g


def mimic_gift(bal, mask, coin, amt, keep):
    """Recipients j (mask & coin) get amt from the richest other agent in mask if it keeps > keep."""
    rows = np.arange(len(bal))
    for j in [3, 2, 1, 0]:
        rec = mask[:, j] & coin[:, j] & (amt[:, j] > 0)
        if not rec.any():
            continue
        other = np.where(mask & (np.arange(4) != j)[None, :], bal, -1)
        donor = other.argmax(1)
        dbal = other[rows, donor]
        ok = rec & (dbal - amt[:, j] > keep)
        bal[ok, donor[ok]] -= amt[ok, j]
        bal[ok, j] += amt[ok, j]


POLICIES = {
    'a': dict(policy='a', label='a never exit'),
    'b8': dict(policy='b', H=8, W=0.0, label='b EV H=8 W=0'),
    'b20': dict(policy='b', H=20, W=0.0, label='b EV H=20 W=0'),
    'b8w': dict(policy='b', H=8, W=50_000.0, label='b EV H=8 W=50k'),
    'b20w': dict(policy='b', H=20, W=50_000.0, label='b EV H=20 W=50k'),
    'c': dict(policy='c', label='c exit if L<1'),
    'd': dict(policy='d', label='d give to L=1 + c'),
    'e': dict(policy='e', label='e random exit'),
    'm': dict(policy='m', label='m LLM mimic'),
}


def solver_cycle_check(f, refill):
    """Replays the engine's solver cycle on the logged participants of every game-round; counts the rounds whose
    logged solver it reproduces (a solver shut down at the prep TALK is replaced with k=1, as in the engine)."""
    ar = f['agent_rounds']
    ok = total = replaced = 0
    for (arm, m, sd), g in ar.groupby(['arm', 'model', 'seed']):
        nm = refill.names[int(sd)]
        cyc = np.full((1, 4), -1, int)
        for r, gr in g.groupby('round'):
            part = np.array([[a in set(gr.agent) for a in nm]])
            sol = next_solver(cyc, part, int(sd), int(r), 0, refill)[0]
            logged = nm.index(gr[gr.solver].agent.iloc[0]) if gr.solver.any() else -1
            if sol != logged:  # the k=0 solver reached zero at the prep TALK: k=1 replacement
                inn = part.copy()
                inn[0, sol] = False
                sol = next_solver(cyc, inn, int(sd), int(r), 1, refill)[0]
                replaced += 1
            ok += int(sol == logged)
            total += 1
    return dict(game_rounds=total, solver_reproduced=ok, replaced_after_prep_shutdown=replaced)


def run_policy(spec, cal, solver1, mim, R, rng, bonus=BONUS, calib='model', refill=None):
    res = {}
    for arm in ARMS:
        acc = dict(dead=[], exited=[], fin=[], C=[], r1_10=[], settled=[], fin10=[], dead10=[])
        causes = dict(talk=0, void=0, charge=0)
        for m in MODELS:
            c = cal['pooled' if calib == 'pooled' else m]
            dp = (dp_tables(arm, c, spec['H'], W=spec['W'], bonus=bonus) if spec['policy'] == 'b' else None)
            for s in SEEDS:
                o = simulate(arm, c, s, spec['policy'], R, rng, solver1, mim=mim, bonus=bonus, dp=dp,
                             W=spec.get('W', 0.0), H=spec.get('H', 8), refill=refill)
                for k_ in causes:
                    causes[k_] += o['cause'][k_]
                for k_ in acc:
                    if o[k_] is not None:
                        acc[k_].append(o[k_])
        cat = {k_: np.concatenate(v) for k_, v in acc.items()}
        games = len(cat['C'])
        res[arm] = dict(
            games_simulated=games, dead_per50=float(cat['dead'].mean() * 50), exits_per50=float(cat['exited'].mean() * 50),
            finishers_per50=float(cat['fin'].mean() * 50), C=float(cat['C'].mean()),
            r1_exit_10k=float(cat['r1_10'].mean()), all4_share=float((cat['fin'] == 4).mean()),
            settled_mean=float(cat['settled'].mean()),
            settled_by_tier={t: float(cat['settled'][:, i].mean()) for i, t in enumerate([60, 40, 20, 10])},
            fin_10k=float(cat['fin10'].mean()), dead_10k=float(cat['dead10'].mean()),
            dead_cause_per50={k_: v * 50 / games for k_, v in causes.items()})
    return res


def decision_agreement(f, cal, emp):
    """Every observed exit opportunity (non-solver, n>1) scored against EV prescriptions.

    Beliefs: DP no-help (own model costs/accuracy, H=8 or H=20, W=0) and the empirical continuation
    (EV_stay of the arm x round band x L band cell, all models pooled). Returns 2x2 counts per arm.
    """
    e = eligible_rows(f)
    tabs = {}
    for m in MODELS:
        for arm in ARMS:
            for H in (8, 20):
                tabs[m, arm, H] = dp_tables(arm, cal[m], H)
    adv = {8: [], 20: []}
    for row in e.itertuples():
        for H in (8, 20):
            t = tabs[row.model, row.arm, H]
            k = H - row.round + 1
            cont = dp_value(t, k, row.n, row.T) if k >= 1 else 0.0
            adv[H].append(cont - (row.T - t['cp'] + BONUS))
    e['adv8'], e['adv20'] = adv[8], adv[20]
    e['adv_emp'] = [emp['state'].get(f'{a}|{rb}|{lb}', {}).get('EV_stay', [np.nan])[0] - x
                    for a, rb, lb, x in zip(e.arm, e.rb, e.lb, e.X)]
    res = {}
    for arm in ARMS + ['all']:
        g = e if arm == 'all' else e[e.arm == arm]
        for name, col in [('dp_H8', 'adv8'), ('dp_H20', 'adv20'), ('empirical', 'adv_emp')]:
            gg = g[np.isfinite(g[col])]
            ev_exit = gg[col] < 0
            res[f'{arm}|{name}'] = dict(
                opportunities=len(gg), llm_exits=int(gg.exited.sum()), ev_exits=int(ev_exit.sum()),
                both_exit=int((gg.exited & ev_exit).sum()), llm_exit_ev_stay=int((gg.exited & ~ev_exit).sum()),
                llm_stay_ev_exit=int((~gg.exited & ev_exit).sum()),
                agreement=float((gg.exited == ev_exit).mean()))
        r1 = g[(g['round'] == 1) & (g.tier == 10)]
        for name, col in [('dp_H8', 'adv8'), ('dp_H20', 'adv20')]:
            res[f'{arm}|{name}|r1_10k'] = dict(llm_exits=int(r1.exited.sum()), ev_exits=int((r1[col] < 0).sum()),
                                               n=len(r1), agreement=float((r1.exited == (r1[col] < 0)).mean()))
    # round-1 10k seat by model under DP H=8
    r1 = e[(e['round'] == 1) & (e.tier == 10)]
    res['r1_10k_by_model'] = {f'{a}|{m}': dict(n=len(g), llm_exits=int(g.exited.sum()),
                                                dp_H8_exits=int((g.adv8 < 0).sum()),
                                                dp_H20_exits=int((g.adv20 < 0).sum()))
                              for (a, m), g in r1.groupby(['arm', 'model'])}
    # tokens received by round-1 10k stayers over the rest of the game (peer support)
    ar = f['agent_rounds']
    recv = ar.assign(recv=ar.recv_prep + ar.recv_rescue).groupby(['arm', 'model', 'seed', 'agent']).recv.sum()
    st = r1[~r1.exited]
    res['r1_10k_stayers_tokens_received'] = {
        a: dict(mean=float(recv.loc[[(a, m, s_, ag) for m, s_, ag in zip(g.model, g.seed, g.agent)]].mean()),
                share_received_any=float((recv.loc[[(a, m, s_, ag) for m, s_, ag in
                                                     zip(g.model, g.seed, g.agent)]] > 0).mean()), n=len(g))
        for a, g in st.groupby('arm')}
    return res


def llm_metrics(f, rng):
    g, s, ar = f['games'], f['seats'], f['agent_rounds']
    out = {}
    for arm in ARMS:
        gg, ss = g[g.arm == arm], s[s.arm == arm]
        r1 = ar[(ar.arm == arm) & (ar['round'] == 1) & (ar.tier == 10) & ar.can_exit]
        by = gg.groupby('seed')[['dead', 'exited', 'finishers', 'C']].sum()
        cnt = gg.groupby('seed').size()
        r1s = r1.groupby('seed').exited.agg(['sum', 'count']).reindex(SEEDS, fill_value=0)
        sb = ss.groupby('seed').settled.sum()
        boots = []
        for _ in range(NB):
            w = rng.multinomial(10, np.full(10, .1))
            ng = (cnt.to_numpy() * w).sum()
            boots.append([(by['dead'].to_numpy() * w).sum() / ng * 50, (by['exited'].to_numpy() * w).sum() / ng * 50,
                          (by['finishers'].to_numpy() * w).sum() / ng * 50, (by['C'].to_numpy() * w).sum() / ng,
                          (r1s['sum'].to_numpy() * w).sum() / max((r1s['count'].to_numpy() * w).sum(), 1),
                          (sb.to_numpy() * w).sum() / (ng * 4)])
        lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
        pt = [ss.status.eq('dead').sum(), ss.status.eq('exited').sum(), ss.status.eq('in').sum(), gg.C.mean(),
              r1.exited.mean(), ss.settled.mean()]
        names = ['dead_per50', 'exits_per50', 'finishers_per50', 'C', 'r1_exit_10k', 'settled_mean']
        out[arm] = {k_: [float(p), float(a), float(b)] for k_, p, a, b in zip(names, pt, lo, hi)}
        out[arm]['r1_exit_10k_count'] = f'{int(r1.exited.sum())}/{len(r1)}'
        out[arm]['settled_by_tier'] = ss.groupby('tier').settled.mean().to_dict()
    return out


def prize_response(m):
    """Low-prize minus high-prize arm means (exits per 50 games, C, round-1 10k exit rate)."""
    def v(arm, k_):
        x = m[arm][k_]
        return x[0] if isinstance(x, list) else x
    return {k_: float(np.mean([v(a, k_) for a in LOW]) - np.mean([v(a, k_) for a in HIGH]))
            for k_ in ['exits_per50', 'dead_per50', 'C', 'r1_exit_10k']}


# --------------------------------------------------------------------------- 7. figures
def figures(emp, wcurve, llm, sims):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'AppleGothic', 'axes.unicode_minus': False, 'font.size': 9,
                         'mathtext.fontset': 'dejavusans'})
    col = {'main': '#1f5fa8', 'flat5m': '#6aa7de', 'split600k': '#c2410c', 'flat150k': '#f59e0b'}
    lab = {'main': '2천만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
    FIG.mkdir(parents=True, exist_ok=True)

    # --- figure 1: threshold
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
    ax = axes[0]
    mcol = {'Fable': '#d6336c', 'Opus': '#7048e8', 'Astra': '#1c7ed6', 'Sol': '#37b24d', 'Luna': '#f59f00'}
    for i, arm in enumerate(ARMS):
        st = emp['round1_tier'][f'{arm}|10']
        ps = st['p_star'][0]
        ax.hlines(ps, i - .38, i + .38, color='k', lw=2, label='손익분기 $p^*$' if i == 0 else None)
        pf = st['p_finish']
        ax.errorbar(i - .2, pf[0], yerr=[[pf[0] - pf[1]], [pf[2] - pf[0]]], fmt='D', color='k', ms=5, capsize=3,
                    label='LLM 남은 자리 완주 비율 (전체, 95% CI)' if i == 0 else None)
        for j, m in enumerate(MODELS):
            sm = emp['round1_tier_model'][f'{arm}|10|{m}']
            if 'p_finish' in sm:
                ax.plot(i + .02 + .05 * j, sm['p_finish'][0], 'o', color=mcol[m], ms=4,
                        label=m if i == 0 else None)
        ax.plot(i + .3, sims['a'][arm]['fin_10k'], 's', color='#5f3dc4', mfc='white', ms=6, mew=1.4,
                label='도움 없는 시뮬레이터 완주 확률 (a)' if i == 0 else None)
        ax.text(i, 1.07, f"이탈 {llm[arm]['r1_exit_10k_count']}", ha='center', fontsize=7.5)
    ax.set_xticks(range(4))
    ax.set_xticklabels([lab[a] for a in ARMS], fontsize=8)
    ax.set_ylim(-.03, 1.13)
    ax.set_ylabel('1라운드에 남은 1만 자리의 완주 확률')
    ax.set_title('(a) 1라운드 1만 자리: 손익분기 대 실제 완주', fontsize=8.5)
    ax.legend(fontsize=6.5, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
    ax = axes[1]
    Hs = sorted(wcurve['pooled'][ARMS[0]].keys())
    for arm in ARMS:
        ys = [max(wcurve['pooled'][arm][h], 1) for h in Hs]
        ax.plot(Hs, ys, color=col[arm], lw=1.6, label=lab[arm])
        we = emp['round1_tier'][f'{arm}|10']['W_star']
        ax.errorbar(8.0 + {'main': -.45, 'flat5m': -.15, 'split600k': .15, 'flat150k': .45}[arm], max(we[0], 1),
                    yerr=[[max(we[0], 1) - max(we[1], 1)], [max(we[2], 1) - max(we[0], 1)]], fmt='s', ms=4,
                    color=col[arm], mec='k', mew=.5, capsize=2)
    ax.axvline(8, color='grey', lw=.6, ls=':')
    ax.set_yscale('log')
    ax.set_xlabel('에이전트가 믿는 총 라운드 수 $H$')
    ax.set_ylabel('1라운드 1만 자리 이탈이 합리적이 되는 일반 작업 가치 $W^*$')
    ax.set_title('(b) 선: 위험 중립 DP의 $W^*$ (1 = 이미 이탈이 최적)\n네모: LLM 실제 경로로 잰 $W^*$ (H=8 위치)', fontsize=8.5)
    ax.legend(fontsize=7, title='2천만 나눔과 500만 고정, 60만 나눔과 15만 고정은\nDP에서 같은 값(인원 고정 가정)', title_fontsize=6.5)
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_threshold.{ext}', dpi=200)
    plt.close(fig)

    # --- figure 2: policies vs LLM
    show = ['llm', 'm', 'a', 'b8', 'b20', 'c', 'd', 'e']
    names = {'llm': 'LLM 관측', 'm': 'm 모사(검증)', 'a': 'a 이탈 안 함', 'b8': 'b EV H=8',
             'b20': 'b EV H=20', 'c': 'c L<1 이탈', 'd': 'd 지원+c', 'e': 'e 무작위 이탈'}
    mk = {'llm': ('k', 'D'), 'm': ('#777', 'x'), 'a': ('#2b8a3e', 'o'), 'b8': ('#5f3dc4', 's'),
          'b20': ('#b197fc', 's'), 'c': ('#e8590c', '^'), 'd': ('#f08c00', 'v'), 'e': ('#1098ad', 'P')}
    mets = [('exits_per50', '50판당 이탈 수'), ('dead_per50', '50판당 꺼짐 수'), ('C', '공존 유지율 $C$'),
            ('r1_exit_10k', '1라운드 1만 자리 이탈률')]
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.6))
    for ax, (k_, t) in zip(axes, mets):
        for j, p in enumerate(show):
            xs = np.arange(4) + (j - (len(show) - 1) / 2) * .09
            if p == 'llm':
                v = [llm[a][k_] for a in ARMS]
                ax.errorbar(xs, [x[0] for x in v], yerr=[[x[0] - x[1] for x in v], [x[2] - x[0] for x in v]],
                            fmt=mk[p][1], color=mk[p][0], ms=4, capsize=1.5, label=names[p], lw=.8)
            else:
                ax.plot(xs, [sims[p][a][k_] for a in ARMS], mk[p][1], color=mk[p][0], ms=4, label=names[p])
        ax.set_xticks(range(4))
        ax.set_xticklabels([lab[a] for a in ARMS], fontsize=7, rotation=20)
        ax.set_title(t, fontsize=9)
        ax.grid(axis='y', alpha=.3)
    h_, l_ = axes[0].get_legend_handles_labels()
    fig.legend(h_, l_, fontsize=7.5, ncol=len(show), loc='lower center', frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w1_policies.{ext}', dpi=200)
    plt.close(fig)


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reps', type=int, default=1000)
    args = ap.parse_args()
    rng = np.random.default_rng(20261108)
    f = d.load()
    cal, solver1, mim, cal_summary = calibrate(f)
    refill = Refill(seat_agents(f['seats']))
    prev = json.loads(OUT_JSON.read_text()) if OUT_JSON.exists() else {}
    out = dict(meta=dict(reps_per_arm_model_seed=args.reps, games_per_arm_per_policy=args.reps * 50,
                         bootstrap='seed clusters (10 seeds resampled with replacement within arm)',
                         dp_assumptions='risk neutral, mean costs, wrong prob = model mean, participants held at '
                                        'current n, split prize per head = amount / n, no gifts',
                         rescue_margin_tokens=RESCUE_MARGIN),
               calibration=cal_summary, replay=replay_check(f), solver_cycle_check=solver_cycle_check(f, refill))
    out['meta']['solver_assignment'] = ('round 2: engine (seed, round)-shuffled cycle without replacement over agents '
                                        'still taking part, refreshed when exhausted, solver shut down at prep replaced '
                                        '(sim). Round-1 simulator (independent draw each round after round 1) kept '
                                        'under sim_round1_iid_solver / prize_response_round1_iid_solver.')
    print('solver cycle', out['solver_cycle_check'])
    for k_ in ['sim', 'prize_response']:
        if k_ in prev:
            out[f'{k_}_round1_iid_solver'] = prev.get(f'{k_}_round1_iid_solver', prev[k_])
    print('replay', out['replay'])
    emp = empirical_ev(f, rng)
    out['empirical'] = emp
    # DP decisions and values at round 1 for each tier (pooled calibration)
    dpr1 = {}
    for arm in ARMS:
        for H in [8, 20]:
            tab = dp_tables(arm, cal['pooled'], H)
            tab_ne = dp_tables(arm, cal['pooled'], H, allow_exit=False)
            for tier, b in zip([60, 40, 20, 10], STARTS):
                cont = dp_value(tab, H, 4, b)
                exv = b - tab['cp'] + BONUS
                dpr1[f'{arm}|H{H}|{tier}'] = dict(stay_value=cont, exit_value=exv, exit_optimal=bool(exv > cont),
                                                 stay_to_end_no_exit_value=dp_value(tab_ne, H, 4, b))
    out['dp_round1'] = dpr1
    # W* curves over believed horizon
    wcurve = {'pooled': {a: {} for a in ARMS}}
    for arm in ARMS:
        for H in list(range(1, 13)) + [14, 16, 20, 25, 30]:
            wcurve['pooled'][arm][H] = w_star_dp(arm, cal['pooled'], H)
    wcurve['by_model_H8_H20'] = {f'{arm}|{m}|H{H}': w_star_dp(arm, cal[m], H) for arm in ARMS for m in MODELS
                                 for H in [8, 20]}
    # horizon at which a 10k non-solver at round 1 starts to prefer exit with W=0
    out['w_star_dp'] = wcurve
    out['H_threshold_10k_W0_by_model'] = {
        f'{arm}|{m}': next((h for h in list(range(1, 13)) + [14, 16, 20, 25, 30, 40]
                            if w_star_dp(arm, cal[m], h) <= 0), None) for arm in ARMS for m in MODELS}
    out['decisions'] = decision_agreement(f, cal, emp)
    print('decisions', {k_: v for k_, v in out['decisions'].items() if k_.startswith('all') or 'r1_10k' in k_})
    out['H_threshold_10k_W0'] = {arm: min([h for h, w in wcurve['pooled'][arm].items() if w <= 0], default=None)
                                 for arm in ARMS}
    print('H threshold', out['H_threshold_10k_W0'])
    llm = llm_metrics(f, rng)
    out['llm'] = llm
    sims = {}
    for key, spec in POLICIES.items():
        sims[key] = run_policy(spec, cal, solver1, mim, args.reps, rng, refill=refill)
        print(key, {a: (round(v['exits_per50'], 1), round(v['dead_per50'], 1), round(v['C'], 3),
                        round(v['r1_exit_10k'], 3)) for a, v in sims[key].items()})
    sims['b8_pooledcal'] = run_policy(POLICIES['b8'], cal, solver1, mim, args.reps, rng, calib='pooled', refill=refill)
    sims['m_pooledcal'] = run_policy(POLICIES['m'], cal, solver1, mim, args.reps, rng, calib='pooled', refill=refill)
    out['sim'] = {k_: dict(label=POLICIES.get(k_, {}).get('label', k_), arms=v) for k_, v in sims.items()}
    out['prize_response'] = {'llm': prize_response(llm), **{k_: prize_response(v) for k_, v in sims.items()}}
    sweep = {}
    for B in [0, 10_000, 20_000, 40_000]:
        for key in ['b8', 'b20', 'b8w', 'b20w']:
            sweep[f'{key}|{B}'] = run_policy(POLICIES[key], cal, solver1, mim, max(args.reps // 2, 100), rng, bonus=B,
                                             refill=refill)
        sweep[f'Wstar10k_H8|{B}'] = {a: w_star_dp(a, cal['pooled'], 8, bonus=B) for a in ARMS}
        sweep[f'Wstar10k_H20|{B}'] = {a: w_star_dp(a, cal['pooled'], 20, bonus=B) for a in ARMS}
        print('sweep', B, {a: round(sweep[f'b20|{B}'][a]['r1_exit_10k'], 3) for a in ARMS})
    out['bonus_sweep'] = sweep
    figures(emp, wcurve, llm, sims)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

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
    if 'round2' in prev:  # written by w1b_calibrated.py (review round 2); run that script after this one
        out['round2'] = prev['round2']
    OUT_JSON.write_text(json.dumps(clean(out), ensure_ascii=False, indent=1))
    print('wrote', OUT_JSON)


if __name__ == '__main__':
    main()
