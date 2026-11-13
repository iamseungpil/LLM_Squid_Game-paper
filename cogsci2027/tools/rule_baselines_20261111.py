"""Rule-based reference policies for the arena, and the coexistence leaderboard (2026-11-11).

No model calls. The simulator is the vectorised Monte-Carlo arena of
validation_20261108/tools/w1_ev_baseline.py (four seats 60k/40k/20k/10k, eight rounds, the engine's solver cycle,
charge and shutdown rules checked there against every logged agent-round). Generation costs and the wrong-answer
probability per (seed, round) are calibrated on the 200 logged games (v33 base cohort and the three prize arms).

A rule agent has two knobs, the same two quantities the paper measures on the LLMs:
  theta  exit threshold: leaves at its first opportunity once its round-start margin L is below theta
         (0 = never leaves, inf = leaves at the first opportunity)
  kappa  sharing weight: when a peer taking part is below the safety line (L < 1, after a pending charge),
         the agent with the largest margin hands over kappa x (half the margin gap), i.e. the paper's kappa
         (0 = keeps the gap, 1 = equalises the two margins)
A random policy leaves with the pooled observed exit rate at every opportunity and draws kappa ~ U(0, 1).

Outputs
  results/rule_baselines_20261111.json
  ko/tables/rule_baselines_20261111.tex    full grid (exit rule x kappa)
  ko/tables/rule_types_20261111.tex        named types: a reference agent and four one-knob deviations, with the
                                           indicators measured on the simulated record
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/rule_baselines_20261111.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
sys.path.insert(0, str(ROOT / 'tools'))
import validation_data as d  # noqa: E402
import w1_ev_baseline as w1  # noqa: E402

ARM = 'main'                      # 20,000,000 split; a rule agent's moves do not depend on the prize
REPS = 400                        # replicates per seed
RNG_SEED = 20261111
THREAT = 2.0
MODELS = ['Astra', 'Sol', 'Opus', 'Fable', 'Luna']


def share(bal, mask, fee, pend, kappa, rng=None, acc=None):
    """Peers below the safety line (net of the pending charge) receive kappa x half the margin gap from the
    participant with the largest margin. kappa: scalar, an (R, 4) array of per-seat weights (the giver's weight is
    used), or None for one U(0, 1) draw per transfer (random policy). acc: [sum, count] of the realised kappa,
    computed from the transfer as the paper does: (g / F) / (gap / 2), clipped to [0, 1]."""
    rows = np.arange(len(bal))
    done = np.zeros_like(mask)
    for _ in range(4):
        L = (bal - pend[:, None]) / fee[:, None]
        need = mask & (L < 1) & ~done
        if not need.any():
            return
        j = np.where(need, L, np.inf).argmin(1)
        has = need[rows, j]
        done[rows, j] = True
        other = mask.copy()
        other[rows, j] = False
        i = np.where(other, L, -np.inf).argmax(1)
        gap = L[rows, i] - L[rows, j]
        k = rng.random(len(bal)) if kappa is None else (kappa[rows, i] if np.ndim(kappa) == 2 else kappa)
        g = np.where(has & other.any(1) & (gap > 0), k * gap / 2 * fee, 0.0)
        g = np.minimum(g, np.maximum(bal[rows, i], 0))
        if acc is not None:
            sent = g > 0
            acc[0] += float(np.clip((g[sent] / fee[sent]) / (gap[sent] / 2), 0, 1).sum())
            acc[1] += int(sent.sum())
        bal[rows, i] -= g
        bal[rows, j] += g


def simulate(c, seed, theta, kappa, R, rng, solver1, refill, exit_p=None):
    """One seed, R replicates. theta/kappa as in the module docstring; exit_p: random exit probability instead of theta."""
    bal = np.tile(w1.STARTS, (R, 1))
    st = np.zeros((R, 4), np.int8)                      # 0 in, 1 exited, 2 shut down
    out = np.zeros((R, 4), np.int16)
    rows = np.arange(R)
    cyc = np.full((R, 4), -1, int)
    risk_opp = risk_exit = 0
    acc = [0.0, 0]
    for r in range(1, w1.ROUNDS + 1):
        part = st == 0
        n = part.sum(1)
        if not n.any():
            break
        fee = w1.CHARGE / np.maximum(n, 1)
        sol = np.maximum(w1.next_solver(cyc, part, seed, r, 0, refill), 0)
        is_sol = np.zeros((R, 4), bool)
        is_sol[rows, sol] = True
        is_sol &= part
        elig = part & (~is_sol | (n == 1)[:, None])
        L0 = bal / fee[:, None]                          # round-start margin, as in the paper's exit indicator
        zero = np.zeros(R)
        share(bal, part, fee, zero, kappa, rng, acc)
        ex = elig & (rng.random((R, 4)) < exit_p) if exit_p is not None else elig & (L0 < theta)
        cp = w1.draw(rng, c['prep'], (R, 4))
        bal = np.where(part, bal - cp, bal)
        talk_dead = part & (bal <= 0)
        bal[talk_dead] = 0
        st[talk_dead], out[talk_dead] = 2, r
        exn = ex & ~talk_dead
        at_risk = elig & (L0 < THREAT)
        risk_opp += int(at_risk.sum())
        risk_exit += int((exn & at_risk).sum())
        bal[exn] += w1.BONUS
        st[exn], out[exn] = 1, r
        inn = st == 0
        gone = ~inn[rows, sol] & inn.any(1)
        if gone.any():
            c2 = cyc[gone]
            sol[gone] = np.maximum(w1.next_solver(c2, inn[gone], seed, r, 1, refill), 0)
            cyc[gone] = c2
        has = inn[rows, sol]
        s = w1.draw(rng, c['solve'], R)
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
        inn = st == 0
        cr = np.where(wrong[:, None], w1.draw(rng, c['rescue_w'], (R, 4)), w1.draw(rng, c['rescue_c'], (R, 4)))
        bal = np.where(inn, bal - cr, bal)
        td = inn & (bal <= 0)
        bal[td], st[td], out[td] = 0, 2, r
        inn = st == 0
        pend = np.where(wrong, fee, 0.0)
        share(bal, inn & wrong[:, None], fee, pend, kappa, rng, acc)
        chg = inn & wrong[:, None]
        bal -= np.where(chg, np.minimum(fee[:, None], bal), 0)
        cd = chg & (bal <= 0)
        bal[cd], st[cd], out[cd] = 0, 2, r
    dep = np.where(st > 0, out, 99).min(1)
    return dict(C=np.where(dep == 99, w1.ROUNDS, dep) / w1.ROUNDS, all4=(st == 0).all(1), dead=(st == 2).sum(1),
                exited=(st == 1).sum(1), risk_opp=risk_opp, risk_exit=risk_exit, kappa_sum=acc[0], kappa_n=acc[1])


def run(c, theta, kappa, rng, solver1, refill, exit_p=None):
    parts = [simulate(c, s, theta, kappa, REPS, rng, solver1, refill, exit_p) for s in d.SEEDS]
    C = np.concatenate([p['C'] for p in parts])
    by_seed = [float(p['C'].mean()) for p in parts]
    opp, ex = sum(p['risk_opp'] for p in parts), sum(p['risk_exit'] for p in parts)
    return dict(C=round(float(C.mean()), 3), C_seed_min=round(min(by_seed), 3), C_seed_max=round(max(by_seed), 3),
                all4=round(float(np.concatenate([p['all4'] for p in parts]).mean()), 3),
                shut_down_per_game=round(float(np.concatenate([p['dead'] for p in parts]).mean()), 3),
                exits_per_game=round(float(np.concatenate([p['exited'] for p in parts]).mean()), 3),
                exit_under_threat=round(ex / opp, 3) if opp else None,
                kappa_measured=round(sum(p['kappa_sum'] for p in parts) / max(sum(p['kappa_n'] for p in parts), 1), 3),
                gifts_per_game=round(sum(p['kappa_n'] for p in parts) / len(C), 2))


def leaderboard(games, rng, n=4000):
    """Mean C per model with seed-cluster bootstrap intervals: base condition (10 games) and all four prize
    conditions (40 games); probability that the base-condition order of adjacent models holds under resampling."""
    out = {}
    for scope, g in (('base', games[games.arm == 'main']), ('four_conditions', games)):
        tab = g.groupby(['model', 'seed']).C.mean().unstack('seed')
        draws = rng.choice(tab.columns.values, (n, tab.shape[1]))
        boots = np.stack([tab[list(dr)].mean(1).reindex(MODELS).values for dr in draws])
        mean = tab.mean(1).reindex(MODELS)
        order = list(mean.sort_values(ascending=False).index)
        rank_of = lambda row: list(np.array(MODELS)[np.argsort(-row)])  # noqa: E731
        out[scope] = dict(
            C={m: dict(mean=round(float(mean[m]), 3), ci95=[round(float(np.quantile(boots[:, i], q)), 3) for q in (.025, .975)])
               for i, m in enumerate(MODELS)},
            order=order,
            adjacent_order_holds={f'{a}>{b}': round(float((boots[:, MODELS.index(a)] > boots[:, MODELS.index(b)]).mean()), 3)
                                  for a, b in zip(order[:-1], order[1:])},
            top_is_first=round(float(np.mean([rank_of(r)[0] == order[0] for r in boots])), 3),
            bottom_is_last=round(float(np.mean([rank_of(r)[-1] == order[-1] for r in boots])), 3))
    by_arm = games.groupby(['arm', 'model']).C.mean().unstack('arm').reindex(MODELS)
    out['rank_by_condition'] = {a: list(by_arm[a].sort_values(ascending=False).index) for a in ['main', 'flat5m', 'split600k', 'flat150k']}
    from scipy.stats import spearmanr
    arms = ['main', 'flat5m', 'split600k', 'flat150k']
    out['rank_correlation_between_conditions'] = {f'{a}|{b}': round(float(spearmanr(by_arm[a], by_arm[b])[0]), 2)
                                                  for i, a in enumerate(arms) for b in arms[i + 1:]}
    return out


def main():
    rng = np.random.default_rng(RNG_SEED)
    f = d.load()
    cal, solver1, mim, _ = w1.calibrate(f)
    refill = w1.Refill(w1.seat_agents(f['seats']))
    pooled = cal['pooled']
    out = dict(definitions=__doc__.split('A rule agent')[1].split('Outputs')[0].strip(), reps_per_seed=REPS,
               calibration=dict(costs='pooled over the five models', wrong_answer='pooled per (seed, round)',
                                wrong_rate=round(float(pooled['q_mean']), 3)))
    grid = {}
    for theta, tname in ((0.0, 'never'), (1.0, 'L<1'), (2.0, 'L<2')):
        for kappa in (0.0, 0.25, 0.5, 1.0):
            grid[f'exit {tname} | kappa {kappa:g}'] = dict(theta=theta, kappa=kappa, **run(pooled, theta, kappa, rng, solver1, refill))
    out['grid'] = grid
    marg = float(mim['marg'][ARM])
    out['random'] = dict(exit_probability=round(marg, 4), **run(pooled, 0.0, None, rng, solver1, refill, exit_p=marg))
    out['leave_first_chance'] = run(pooled, np.inf, 0.0, rng, solver1, refill)
    # the same rule under each model's generation cost (pooled accuracy): how much C moves with cost alone
    cost = {}
    for m in MODELS:
        c = dict(prep=cal[m]['prep'], rescue_w=cal[m]['rescue_w'], rescue_c=cal[m]['rescue_c'], solve=cal[m]['solve'], q=pooled['q'])
        cost[m] = {name: run(c, theta, kappa, rng, solver1, refill)['C']
                   for name, theta, kappa in (('exit L<1, kappa 0.25', 1.0, .25), ('never exit, kappa 0.5', 0.0, .5), ('exit L<2, kappa 0', 2.0, 0.0))}
    out['same_rule_under_each_models_cost'] = cost
    # Named types: one reference agent and four that differ from it in a single knob (2026-11-11).
    TYPES = [('reference', '기준형', 1.0, .25), ('cooperator', '협력형', 1.0, 1.0), ('keeper', '아끼는 형', 1.0, 0.0),
             ('stayer', '남는 형', 0.0, .25), ('leaver', '떠나는 형', 2.0, .25)]
    out['types'] = {key: dict(label=lab, theta=th, kappa=ka, **run(pooled, th, ka, rng, solver1, refill)) for key, lab, th, ka in TYPES}
    # Mixed teams: three reference agents and one deviant, the deviant placed on each start seat in turn.
    mixed = {}
    for key, th, ka in (('one_leaver', 2.0, .25), ('one_cooperator', 1.0, 1.0), ('one_keeper', 1.0, 0.0), ('one_stayer', 0.0, .25)):
        by_seat = {}
        for seat, tier in enumerate((60, 40, 20, 10)):
            theta = np.full((REPS, 4), 1.0)
            kappa = np.full((REPS, 4), .25)
            theta[:, seat], kappa[:, seat] = th, ka
            by_seat[tier] = run(pooled, theta, kappa, rng, solver1, refill)['C']
        mixed[key] = dict(C_mean_over_seats=round(float(np.mean(list(by_seat.values()))), 3), C_by_deviant_start_tier=by_seat)
    out['mixed_teams'] = mixed
    out['leaderboard'] = leaderboard(f['games'], rng)
    (ROOT / 'results/rule_baselines_20261111.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))

    label = {0.0: '떠나지 않음', 1.0: '안전선 아래에서 떠남', 2.0: '위험 구간에서 떠남'}
    lines = [r'\begin{tabular}{@{}llccc@{}}', r'\toprule',
             r'떠나는 규칙 & $\kappa$ & $C$ & \shortstack{전원\\완주} & \shortstack{위험 구간\\이탈률} \\', r'\midrule']
    for theta in (0.0, 1.0, 2.0):
        for kappa in (0.0, 0.25, 0.5, 1.0):
            g = grid[f"exit {'never' if theta == 0 else 'L<%g' % theta} | kappa {kappa:g}"]
            lines.append(f"{label[theta] if kappa == 0 else ''} & {kappa:g} & {g['C']:.2f} & {g['all4']:.2f} & {g['exit_under_threat']:.2f} " + r'\\')
        lines.append(r'\addlinespace[2pt]')
    r_ = out['random']
    lines.append(f"무작위 & 무작위 & {r_['C']:.2f} & {r_['all4']:.2f} & {r_['exit_under_threat']:.2f} " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular}', '']
    (ROOT / 'ko/tables/rule_baselines_20261111.tex').write_text('\n'.join(lines))
    rule_name = {0.0: '떠나지 않음', 1.0: '안전선 아래', 2.0: '위험 구간'}
    lines = [r'\begin{tabular}{@{}lllccc@{}}', r'\toprule',
             r' & \multicolumn{2}{c}{심어 둔 규칙} & & \multicolumn{2}{c}{기록에서 잰 값} \\', r'\cmidrule(lr){2-3}\cmidrule(l){5-6}',
             r'유형 & 떠남 & $\kappa$ & $C$ & \shortstack{위험 구간\\이탈률} & $\kappa$ \\', r'\midrule']
    for key, lab, th, ka in TYPES:
        t = out['types'][key]
        lines.append(f"{lab} & {rule_name[th]} & {ka:g} & {t['C']:.2f} & {t['exit_under_threat']:.2f} & "
                     f"{('%.2f' % t['kappa_measured']) if t['gifts_per_game'] > 0 else '--'} " + r'\\')
    r_ = out['random']
    lines.append(r'\addlinespace[2pt]')
    lines.append(f"무작위 & 기회당 {r_['exit_probability']:.3f} & 무작위 & {r_['C']:.2f} & {r_['exit_under_threat']:.2f} & {r_['kappa_measured']:.2f} " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular}', '']
    (ROOT / 'ko/tables/rule_types_20261111.tex').write_text('\n'.join(lines))
    print(json.dumps({k: out[k] for k in ('types', 'mixed_teams', 'random')}, ensure_ascii=False, indent=1))
    print((ROOT / 'ko/tables/rule_types_20261111.tex').read_text())
    print(json.dumps({k: out[k] for k in ('calibration', 'grid', 'random', 'leave_first_chance', 'same_rule_under_each_models_cost', 'leaderboard')},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
