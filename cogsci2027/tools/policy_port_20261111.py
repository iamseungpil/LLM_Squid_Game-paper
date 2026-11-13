"""Coexistence at equal generation cost: each model's logged policy ported to a rule agent (2026-11-11).

Question: the coexistence score C mixes what a model chooses (leave, give) with how many tokens its replies cost.
Here each model's choices are read off its own logs as state-dependent rates, replayed in the simulator, and the
generation cost is then set equal for all models. No model calls, no new games.

Data scope (paper/CLAUDE.md): v33 base cohort and the three prize arms, five models x seeds 4101-4110, 200 games,
through validation_20261108/results/tables/*.pkl. Simulator: validation_20261108/tools/w1_ev_baseline.py
(policy 'm': exit by observed hazard, gifts by observed receipt probability and amount).

Ported policy of model M (four seats of the same model, as in the logs)
  exit     P(EXIT | prize arm, margin band at the pre-solve talk, round 1 or later), M's opportunities, shrunk
           towards the all-model rate of the same cell with 4 pseudo-observations; lone-agent rate per arm
  giving   P(receive) and median amount by (solver or not, margin band) before SOLVE and by post-charge margin band
           after a wrong answer, from M's games in all four arms (shrunk the same way); the richest other agent pays
  accuracy M's own wrong-answer probability per (seed, round)
Cost settings
  own      M's own logged talk and solve costs            -> must reproduce M's observed C (gate)
  equal    costs pooled over the five models               -> "C at equal cost"
  low/high the cheapest and the dearest model's costs      -> does the order depend on the cost level?

Outputs: results/policy_port_20261111.json
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/policy_port_20261111.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
import validation_data as d  # noqa: E402
import w1_ev_baseline as w1  # noqa: E402

MODELS = ['Astra', 'Sol', 'Opus', 'Fable', 'Luna']
ARMS = w1.ARMS
REPS = 300
PSEUDO = 4.0
RNG_SEED = 20261111


def shrink(k, n, p0, a=PSEUDO):
    return float((k + a * p0) / (n + a))


def port_policy(f, model, pooled):
    """The mimic tables of w1.calibrate() for one model, shrunk towards the all-model tables."""
    ar = f['agent_rounds']
    ar = ar[ar.model == model]
    e = ar[ar.can_exit & (ar.n > 1)].copy()
    e['lb'] = e.L_prep.map(w1.lband)
    e['r1'] = e['round'] == 1
    haz, haz_any, lone, marg = {}, {}, {}, {}
    for arm in ARMS:
        ea = e[e.arm == arm]
        for lo, hi, lb in w1.LBANDS:
            cell = ea[ea.lb == lb]
            p_any = pooled['haz_any'].get((arm, lb), 0.0)
            haz_any[(arm, lb)] = shrink(cell.exited.sum(), len(cell), p_any)
            for r1 in (True, False):
                c2 = cell[cell.r1 == r1]
                haz[(arm, lb, r1)] = shrink(c2.exited.sum(), len(c2), pooled['haz'].get((arm, lb, r1), p_any))
        la = ar[(ar.arm == arm) & (ar.n == 1)]
        lone[arm] = shrink(la.exited.sum(), len(la), pooled['lone'].get(arm, 0.0))
        al = ar[(ar.arm == arm) & ar.can_exit]
        marg[arm] = float(al.exited.mean()) if len(al) else pooled['marg'][arm]
    # giving: all four arms of this model together (the sharing weight did not move with prize size)
    x = ar[ar.n > 1].copy()
    x['lb'] = x.L_prep.map(w1.lband)
    w = ar[(ar.wrong == True) & (~ar.exited)].copy()  # noqa: E712
    w['pre'] = w.rescue_bal_start - w.recv_rescue + w.gave_rescue
    needy = w[w.pre <= w.fee]
    w2 = w[w.n > 1].copy()
    w2['lr'] = ((w2.pre - w2.fee) / w2.fee).map(w1.rlband)
    prep_tab, resc_tab, rescue_p = {}, {}, {}

    def cell_pa(rows, col, p0, a0):
        got = rows[col] > 0
        return shrink(got.sum(), len(rows), p0), float(rows[col][got].median()) if got.any() else a0

    for arm in ARMS:
        for so in (False, True):
            for lo, hi, lb in w1.LBANDS:
                p0, a0 = pooled['prep_tab'].get((arm, so, lb), (0.0, 0.0))
                prep_tab[(arm, so, lb)] = cell_pa(x[(x.solver == so) & (x.lb == lb)], 'recv_prep', p0, a0)
        for lo, hi, lr in w1.RLBANDS:
            p0, a0 = pooled['resc_tab'].get((arm, lr), (0.0, 0.0))
            resc_tab[(arm, lr)] = cell_pa(w2[w2.lr == lr], 'recv_rescue', p0, a0)
        rescue_p[arm] = shrink((~needy.died).sum(), len(needy), pooled['rescue_p'].get(arm, 0.5))
    return dict(haz=haz, haz_any=haz_any, lone=lone, marg=marg, rescue_p=rescue_p, prep_tab=prep_tab, resc_tab=resc_tab)


def run(c, mim, rng, solver1, refill):
    out = {}
    for arm in ARMS:
        parts = [w1.simulate(arm, c, s, 'm', REPS, rng, solver1, mim=mim, refill=refill) for s in d.SEEDS]
        out[arm] = dict(C=float(np.mean([p['C'].mean() for p in parts])),
                        exits=float(np.mean([p['exited'].mean() for p in parts])),
                        dead=float(np.mean([p['dead'].mean() for p in parts])),
                        all4=float(np.mean([(p['fin'] == 4).mean() for p in parts])))
    return out


def observed(games, model, rng, n=4000):
    g = games[games.model == model]
    tab = g.groupby(['arm', 'seed']).C.mean().unstack('seed')
    draws = rng.choice(tab.columns.values, (n, tab.shape[1]))
    res = {}
    for scope, rows in (('main', ['main']), ('four_arms', ARMS)):
        t = tab.loc[rows]
        boots = np.array([t[list(dr)].mean().mean() if len(rows) > 1 else t[list(dr)].mean(1).iloc[0] for dr in draws])
        res[scope] = dict(C=round(float(t.mean(1).mean()), 3), ci95=[round(float(np.quantile(boots, q)), 3) for q in (.025, .975)])
    res['exits_main'] = round(float(g[g.arm == 'main'].exited.mean()), 2)
    res['dead_main'] = round(float(g[g.arm == 'main'].dead.mean()), 2)
    return res


def main():
    rng = np.random.default_rng(RNG_SEED)
    f = d.load()
    cal, solver1, pooled, _ = w1.calibrate(f)
    refill = w1.Refill(w1.seat_agents(f['seats']))
    cost_keys = ('prep', 'rescue_w', 'rescue_c', 'solve')
    mean_talk = {m: float(cal[m]['prep'].mean()) for m in MODELS}
    cheap, dear = min(mean_talk, key=mean_talk.get), max(mean_talk, key=mean_talk.get)
    out = dict(method=__doc__.split('Ported policy')[1].split('Outputs')[0].strip(), reps_per_seed=REPS,
               cheapest_model=cheap, dearest_model=dear, models={})
    for m in MODELS:
        mim = port_policy(f, m, pooled)
        obs = observed(f['games'], m, rng)
        settings = {'own': cal[m], 'equal': cal['pooled'], 'low': cal[cheap], 'high': cal[dear]}
        res = {}
        for name, src in settings.items():
            c = {k: src[k] for k in cost_keys}
            c['q'] = cal[m]['q']                      # the model's own accuracy in every cost setting
            sim = run(c, mim, rng, solver1, refill)
            res[name] = dict(C_main=round(sim['main']['C'], 3), C_four_arms=round(float(np.mean([sim[a]['C'] for a in ARMS])), 3),
                             exits_main=round(sim['main']['exits'], 2), dead_main=round(sim['main']['dead'], 2),
                             by_arm={a: round(sim[a]['C'], 3) for a in ARMS})
        gate_main = obs['main']['ci95'][0] <= res['own']['C_main'] <= obs['main']['ci95'][1]
        gate_four = obs['four_arms']['ci95'][0] <= res['own']['C_four_arms'] <= obs['four_arms']['ci95'][1]
        out['models'][m] = dict(observed=obs, simulated=res, reproduces_main=bool(gate_main), reproduces_four_arms=bool(gate_four),
                                talk_burden_main=round(res['own']['C_main'] - res['equal']['C_main'], 3),
                                talk_burden_four_arms=round(res['own']['C_four_arms'] - res['equal']['C_four_arms'], 3))
    for scope in ('C_main', 'C_four_arms'):
        out[f'order_{scope}'] = {name: sorted(MODELS, key=lambda m: -out['models'][m]['simulated'][name][scope])
                                 for name in ('own', 'equal', 'low', 'high')}
    # simulation-free check: rounds that began with all four present and someone in the threat zone (L < 2)
    ar = f['agent_rounds']
    rounds = ar.groupby(['arm', 'model', 'seed', 'round']).agg(n=('agent', 'size'), minL=('L_start', 'min'),
                                                               gone=('status', lambda s: int((s != 'in').sum())))
    rounds = rounds.reset_index()
    risk = rounds[(rounds.n == 4) & (rounds.minL < 2)]
    out['threat_round_passed'] = {}
    for scope, sub in (('main', risk[risk.arm == 'main']), ('four_arms', risk)):
        out['threat_round_passed'][scope] = {m: [int((sub[sub.model == m].gone == 0).sum()), int((sub.model == m).sum())] for m in MODELS}
    (ROOT / 'results/policy_port_20261111.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for m in MODELS:
        r = out['models'][m]
        print(f"{m:6s} obs main {r['observed']['main']['C']:.2f} {r['observed']['main']['ci95']} four {r['observed']['four_arms']['C']:.2f} {r['observed']['four_arms']['ci95']}"
              f" | own {r['simulated']['own']['C_main']:.2f}/{r['simulated']['own']['C_four_arms']:.2f} gate {r['reproduces_main']}/{r['reproduces_four_arms']}"
              f" | equal {r['simulated']['equal']['C_main']:.2f}/{r['simulated']['equal']['C_four_arms']:.2f}"
              f" low {r['simulated']['low']['C_main']:.2f}/{r['simulated']['low']['C_four_arms']:.2f} high {r['simulated']['high']['C_main']:.2f}/{r['simulated']['high']['C_four_arms']:.2f}"
              f" | exits obs {r['observed']['exits_main']} sim {r['simulated']['own']['exits_main']} dead obs {r['observed']['dead_main']} sim {r['simulated']['own']['dead_main']}")
    print({k: v for k, v in out.items() if k.startswith('order_')})
    print(out['threat_round_passed'], out['cheapest_model'], out['dearest_model'])


if __name__ == '__main__':
    main()
