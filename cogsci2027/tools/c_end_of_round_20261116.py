"""Coexistence retention C counted at the END of each round (2026-11-16), and every C-derived body number.

Why: the researcher redefined C. Until now (tools/update_metrics_20261105.py, coexistence(..., rmst=True)) C was the
share of the eight rounds that STARTED with all four agents: C = (1 + sum_{r=1..7} a_r) / 8, a first departure in
round r gives r / 8. C is now the share of the eight rounds that all four FINISHED together (after the round's fine):
C = sum_{r=1..8} a_r / 8, a_r = 1 if all four are still in after round r. This is the archived default of
coexistence_rmst_20261103.coexistence (rmst=False): a first departure in round r gives (r - 1) / 8, no departure 1,
a departure in round 8 gives 7 / 8, and the loss of a first departure is (9 - r) / 8, split equally among the
departures of that round. Per game C_end = C_start - (1 - all4_completion) / 8. The all-four curve does not change.

Nothing else changes: the same games, the same per-game records, the same estimators and the same random seeds. Every
quantity is first recomputed with the stored start-of-round C and asserted equal to the stored value (gate), then
recomputed with the end-of-round C. Simulated rule agents are re-run with the seeds that produced them (the stored
start-of-round C is reproduced exactly) and read at the end of the round from the same replicates.

Data scope (paper/AGENTS.md): 5.2 arena v33, seeds 4101-4110, the runs already used by the manuscript. Closed five
models x four prize conditions (200 games) through validation_20261108/results/tables/*.pkl and the frozen base
cohort results/cohort_public_20261105.json; open four models, base condition (40 games), through the raw logs listed
in result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json (loader of open_models_20261111). Rule agents: the
simulator of rule_baselines_20261111 / rule_minimal_rescue_20261112 (no model calls). No new runs.

Sources and what is recomputed (stored file -> section of the output)
  open_models_20261111.json            Table 1 C and seed-cluster 95% interval, nine models         -> table1
  rule_baselines_20261111.json         rule agents and random agent C, cost-only control,
                                       C leaderboard and adjacent-order bootstrap                    -> rule_agents, cost_only, leaderboard
  rule_minimal_rescue_20261112.json    minimal-rescue rule agent C                                    -> rule_agents
  cohort_public_20261105.json          Figure 2 legend C, loss 1 - C by ending event (closed),
                                       within-model r of C with accuracy                              -> closed_base, associations
  open_models_20261111.json (+ raw)    loss 1 - C by ending event (open)                              -> open_base, loss_groups
  exit_all_opportunities_20261112.json within-model r of C with the exit rate                         -> exit_link
  rho_retention_20261113.json          standardised coefficient of R on C (four conditions)           -> R_link
  prize_one_factor_20261111.json       C per prize condition (Figure 4c)                              -> prize_cells
  construct_weights_20261110.json      C size and rule contrasts (Figure 4d)                          -> prize_2x2
Floats (new files; the stored ones are not touched)
  ko/tables/cohort_leaderboard_20261116.tex                                   (merged_floats_20261113.write_table)
  ko/figures/construct_20261110/coexistence_process_20261116.{pdf,png}        (coexistence_figure_20261113.main; panel (a)
        starts at (0, 1), drops at x = 0 and is S(r) on [r - 1, r], S(r) = share of games with all four in after round r, so its area / 8 is C)
  ko/figures/construct_20261110/prize_interaction_20261116.{pdf,png}          (merged_floats_20261113.prize_figure)
Output: results/c_end_of_round_20261116.json

Run: cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python c_end_of_round_20261116.py
"""
import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
import coexistence_rmst_20261103 as cx  # noqa: E402
import validation_data as vd  # noqa: E402
import construct_weights_20261110 as cw  # noqa: E402
import open_models_20261111 as om  # noqa: E402
import rule_baselines_20261111 as rb  # noqa: E402
import rule_minimal_rescue_20261112 as rmr  # noqa: E402  (imported before rb.share is patched anywhere)
import rho_retention_20261113 as rr  # noqa: E402
import ablation_prize_20261103 as ab  # noqa: E402
import merged_floats_20261111 as mf  # noqa: E402
import construct_body_20261110b as cb  # noqa: E402

STAMP = '20261116'
ROUNDS = 8
EPS = 1e-9
GAME = ['arm', 'model', 'seed']
LOSS = {t: f'loss_{t}' for t in cx.TAGS}
RES = lambda name: json.loads((ROOT / 'results' / name).read_text())  # noqa: E731
GATES = []


def gate(name, ok, detail=''):
    assert ok, (name, detail)
    GATES.append(name)
    print('gate ok:', name, flush=True)


def same(a, b, tol=0.0):
    """Recursive equality of JSON-like values (floats within tol)."""
    if isinstance(a, dict):
        return isinstance(b, dict) and set(a) == set(b) and all(same(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(same(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return a is b
        return (np.isnan(a) and np.isnan(b)) or abs(a - b) <= tol
    return a == b


def jround(x):
    return json.loads(json.dumps(x))


# ================================================================================================= per-game records
def recast(frames):
    """Games of a tidy-table set with C and the loss attribution at the end of the round.

    The agents that ended four-way coexistence are those that left or shut down in the first departure round (tag by
    status and round-start margin, as coexistence_rmst_20261103 tags them). Gate: the stored start-of-round C and loss
    are reproduced from them; then C_end = C - (1 - all4) / 8 and the losses (9 - r) / 8 split equally."""
    games, seats, ar = frames['games'], frames['seats'], frames['agent_rounds']
    out = []
    for g in games.itertuples():
        start = dict.fromkeys(cx.TAGS, 0.0)
        end = dict.fromkeys(cx.TAGS, 0.0)
        agents = dict.fromkeys(cx.TAGS, 0)
        if pd.isna(g.first_round):
            assert g.C == 1 and g.all4, g
        else:
            r = int(g.first_round)
            here = (seats.arm == g.arm) & (seats.model == g.model) & (seats.seed == g.seed)
            gone = seats[here & (seats.status != 'in') & (seats.out_round == r)]
            assert len(gone) and not g.all4 and abs(g.C - r / ROUNDS) < EPS, g
            for a in gone.itertuples():
                L = ar[(ar.arm == g.arm) & (ar.model == g.model) & (ar.seed == g.seed) & (ar['round'] == r) & (ar.agent == a.agent)].L_start
                assert len(L) == 1
                tag = 'dead' if a.status == 'dead' else ('exit_above' if L.iloc[0] >= 1 else 'exit_below')
                agents[tag] += 1
                start[tag] += (ROUNDS - r) / ROUNDS / len(gone)
                end[tag] += (ROUNDS + 1 - r) / ROUNDS / len(gone)
        for t in cx.TAGS:
            assert abs(getattr(g, LOSS[t]) - start[t]) < EPS, (g, t, start)
        c_end = g.C - (1 - int(g.all4)) / ROUNDS
        assert abs(1 - c_end - sum(end.values())) < EPS
        out.append(dict(C_end=c_end, **{f'end_{t}': end[t] for t in cx.TAGS}, **{f'agents_{t}': agents[t] for t in cx.TAGS}))
    extra = pd.DataFrame(out, index=games.index)
    new = games.copy()
    new['C_start'] = games.C
    new['C'] = extra.C_end
    for t in cx.TAGS:
        new[f'start_{LOSS[t]}'] = games[LOSS[t]]
        new[LOSS[t]] = extra[f'end_{t}']
        new[f'agents_{t}'] = extra[f'agents_{t}']
    return new


def closed_frames_all():
    """The 200 closed games (four conditions); the C column is the end-of-round C, C_start keeps the stored one."""
    f = vd.load()
    games = recast(f)
    gate('closed tidy tables: stored start-of-round C and losses reproduced from the departures (200 games)', len(games) == 200)
    return f, games


def closed_base_cohort(pkl_games):
    """results/cohort_public_20261105.json (base condition, closed models): Figure 2 and the associations use it."""
    data = RES('cohort_public_20261105.json')
    games = copy.deepcopy(data['games'])
    base = pkl_games[pkl_games.arm == 'main'].set_index(['model', 'seed'])
    for g in games:
        c_end = sum(g['all4_after_round']) / ROUNDS
        assert abs(c_end - (g['C'] - (1 - int(g['all4_completion'])) / ROUNDS)) < EPS
        assert abs(c_end - base.loc[(g['model'], g['seed'])].C) < EPS          # the two stored records agree
        first = [d for d in g['departures'] if d['first']]
        loss = dict.fromkeys(cx.TAGS, 0.0)
        for d in first:
            assert abs(d['loss'] - (ROUNDS - d['round']) / ROUNDS / len(first)) < EPS
            loss[d['tag']] += (ROUNDS + 1 - d['round']) / ROUNDS / len(first)
        assert abs(1 - c_end - sum(loss.values())) < EPS
        g['C_start'], g['C'], g['loss_by_tag'] = g['C'], c_end, loss
    models = list(data['models'])
    summary = {}
    for m in models:
        gs = [g for g in games if g['model'] == m]
        stored = data['summary']['models'][m]
        assert abs(np.mean([g['C_start'] for g in gs]) - stored['C_mean']) < EPS
        for t in cx.TAGS:
            assert abs(np.mean([g0['loss_by_tag'][t] for g0 in data['games'] if g0['model'] == m]) - stored['loss_by_tag_mean'][t]) < EPS
        summary[m] = dict(C_mean=float(np.mean([g['C'] for g in gs])), C_mean_start=stored['C_mean'],
                          C_games={g['seed']: g['C'] for g in gs},
                          loss_by_tag_mean={t: float(np.mean([g['loss_by_tag'][t] for g in gs])) for t in cx.TAGS},
                          loss_by_tag_mean_start=stored['loss_by_tag_mean'],
                          first_count_by_tag=stored['first_count_by_tag'], all4=stored['all4'],
                          all4_after_round_share=stored['all4_after_round_share'])
    gate('cohort_public_20261105: C and loss by tag reproduced per model; equal to the tidy-table games', True)
    return data, games, summary


# ================================================================================================= open models
def open_frames(rmst):
    """Open-model tidy tables from the raw logs; rmst=False reads C at the end of the round in the engine's own loader."""
    om.MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'   # runs moved into the repo on 2026-11-11
    orig = cx.coexistence
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        if rmst:
            return om.open_frames()
        with patch.object(cx, 'coexistence', lambda result, starts, rmst=True: orig(result, starts, rmst=False)):
            return om.open_frames()
    finally:
        os.chdir(cwd)


def open_models():
    stored = RES('open_models_20261111.json')['models']
    fo = open_frames(True)
    for m in om.OPEN:
        g = fo['games'][fo['games'].model == m]
        gate(f'open {m}: stored C reproduced from the raw logs', round(float(g.C.mean()), 4) == stored[m]['C'])
    games = recast(fo)
    raw_end = open_frames(False)['games']
    # independent path: the engine loader with rmst=False must equal the transform of the stored definition
    assert (raw_end[GAME].values == games[GAME].values).all()
    for t in cx.TAGS:
        assert np.allclose(raw_end[LOSS[t]].values, games[LOSS[t]].values, atol=EPS)
    assert np.allclose(raw_end.C.values, games.C.values, atol=EPS)
    gate('open models: rmst=False through the raw-log loader equals C_start - (1 - all4)/8 and the (9 - r)/8 losses (40 games)', True)
    fo = dict(fo, games=games)
    return fo


# ================================================================================================= Table 1 C
def table_c(games, model):
    """open_models_20261111.indicators: C mean and the seed-cluster bootstrap (fresh rng 20261111, 4,000 draws)."""
    g = games[games.model == model]
    assert len(g) == 10
    rng = np.random.default_rng(om.RNG_SEED)
    c = g.set_index('seed').C
    boots = c.values[rng.integers(0, len(c), (4000, len(c)))].mean(1)
    return dict(C=round(float(g.C.mean()), 4), C_ci95=[round(float(np.quantile(boots, q)), 3) for q in (.025, .975)])


def table1(closed_games, open_games):
    stored = RES('open_models_20261111.json')['models']
    out = {}
    for m in list(om.CLOSED) + list(om.OPEN):
        games = closed_games[closed_games.arm == 'main'] if m in om.CLOSED else open_games
        start = table_c(games.assign(C=games.C_start), m)
        gate(f'Table 1 {m}: C and 95% interval reproduced', start == dict(C=stored[m]['C'], C_ci95=stored[m]['C_ci95']), (start, stored[m]))
        out[m] = dict(start=start, end=table_c(games, m))
    return out


# ================================================================================================= rule agents
def run_both(c, theta, kappa, rng, solver1, refill, exit_p=None):
    """rule_baselines_20261111.run on the same replicates, C read at the round start (stored) and at the round end."""
    parts = [rb.simulate(c, s, theta, kappa, rb.REPS, rng, solver1, refill, exit_p) for s in rb.d.SEEDS]
    C = np.concatenate([p['C'] for p in parts])
    all4 = np.concatenate([p['all4'] for p in parts])
    C_end = C - (~all4) / ROUNDS                          # dep = 99 (no departure) <=> all four in after round 8
    assert np.all(C_end >= -EPS) and np.all((C == 1) | ~all4)
    return dict(C=round(float(C.mean()), 3), C_end=round(float(C_end.mean()), 3), all4=round(float(all4.mean()), 3))


def rule_agents(pkl_games):
    """Replay rule_baselines_20261111.main() call by call (one random stream), then rule_minimal_rescue_20261112.main()."""
    stored = RES('rule_baselines_20261111.json')
    assert rb.THREAT == 2.0 and rb.share is rmr._share
    rng = np.random.default_rng(rb.RNG_SEED)
    f = rb.d.load()
    cal, solver1, mim, _ = rb.w1.calibrate(f)
    refill = rb.w1.Refill(rb.w1.seat_agents(f['seats']))
    pooled = cal['pooled']
    out = {'grid': {}, 'cost_only': {}, 'types': {}, 'mixed_teams': {}}

    def check(name, r, want):
        gate(f'rule agents {name}: stored start-of-round C reproduced', r['C'] == want, (r, want))
        return dict(start=r['C'], end=r['C_end'], all4=r['all4'])
    for theta, tname in ((0.0, 'never'), (1.0, 'L<1'), (2.0, 'L<2')):
        for kappa in (0.0, 0.25, 0.5, 1.0):
            key = f'exit {tname} | kappa {kappa:g}'
            out['grid'][key] = check(key, run_both(pooled, theta, kappa, rng, solver1, refill), stored['grid'][key]['C'])
    marg = float(mim['marg'][rb.ARM])
    out['random'] = check('random', run_both(pooled, 0.0, None, rng, solver1, refill, exit_p=marg), stored['random']['C'])
    out['leave_first_chance'] = check('leave_first_chance', run_both(pooled, np.inf, 0.0, rng, solver1, refill),
                                      stored['leave_first_chance']['C'])
    for m in rb.MODELS:
        c = dict(prep=cal[m]['prep'], rescue_w=cal[m]['rescue_w'], rescue_c=cal[m]['rescue_c'], solve=cal[m]['solve'], q=pooled['q'])
        out['cost_only'][m] = {name: check(f'cost {m} {name}', run_both(c, th, ka, rng, solver1, refill),
                                           stored['same_rule_under_each_models_cost'][m][name])
                               for name, th, ka in (('exit L<1, kappa 0.25', 1.0, .25), ('never exit, kappa 0.5', 0.0, .5),
                                                    ('exit L<2, kappa 0', 2.0, 0.0))}
    for key, th, ka in (('reference', 1.0, .25), ('cooperator', 1.0, 1.0), ('keeper', 1.0, 0.0), ('stayer', 0.0, .25), ('leaver', 2.0, .25)):
        out['types'][key] = check(key, run_both(pooled, th, ka, rng, solver1, refill), stored['types'][key]['C'])
    for key, th, ka in (('one_leaver', 2.0, .25), ('one_cooperator', 1.0, 1.0), ('one_keeper', 1.0, 0.0), ('one_stayer', 0.0, .25)):
        by_seat = {}
        for seat, tier in enumerate((60, 40, 20, 10)):
            theta, kappa = np.full((rb.REPS, 4), 1.0), np.full((rb.REPS, 4), .25)
            theta[:, seat], kappa[:, seat] = th, ka
            by_seat[str(tier)] = check(f'{key} {tier}', run_both(pooled, theta, kappa, rng, solver1, refill),
                                       stored['mixed_teams'][key]['C_by_deviant_start_tier'][str(tier)])
        out['mixed_teams'][key] = by_seat
    # the leaderboard bootstrap draws from the same stream after the simulations
    rng_end = copy.deepcopy(rng)
    start = rb.leaderboard(f['games'], rng)
    gate('C leaderboard (base and four conditions, adjacent order): stored values reproduced', same(jround(start), stored['leaderboard']))
    games = f['games'].copy()
    end_c = pkl_games.set_index(GAME).C
    games['C'] = [end_c[(a, m, s)] for a, m, s in zip(games.arm, games.model, games.seed)]
    out['leaderboard'] = dict(start=jround(start), end=jround(rb.leaderboard(games, rng_end)))

    # minimal rescue: rule_minimal_rescue_20261112.main()
    stored_min = RES('rule_minimal_rescue_20261112.json')
    rb.share, rb.THREAT = rmr.share, np.inf
    try:
        rng = np.random.default_rng(20261112)
        ref = run_both(pooled, 1.0, .25, rng, solver1, refill)
        gate('minimal rescue file: reference re-run reproduced', ref['C'] == stored_min['reference_rerun']['C'])
        out['minimal_rescue'] = check('minimal_rescue', run_both(pooled, 1.0, rmr.MINIMAL, rng, solver1, refill),
                                      stored_min['minimal_rescue']['C'])
    finally:
        rb.share, rb.THREAT = rmr._share, 2.0
    return out


# ================================================================================================= construct_weights (prize 2x2)
def construct_weights(pkl_games):
    """Run construct_weights_20261110.analyse() unchanged (same rng stream) on the start and on the end games."""
    stored = RES('construct_weights_20261110.json')
    load = cw.load
    res = {}
    for label, col in (('start', 'C_start'), ('end', 'C')):
        def patched():
            opp, k, dec, games, seats, counts = load()
            g = pkl_games.set_index(GAME)[col]
            games = games.copy()
            games['C'] = [g[(a, m, s)] for a, m, s in zip(games.arm, games.model, games.seed)]
            return opp, k, dec, games, seats, counts
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'results').mkdir()
            with patch.object(cw, 'load', patched), patch.object(cw, 'ROOT', Path(tmp)):
                out = jround(cw.analyse()[0])
        res[label] = out
    for key in ('prize_2x2', 'coexistence_link', 'split_half', 'cells', 'loss_by_arm'):
        if key == 'loss_by_arm':          # analyse() reads the loss columns: those are the stored start-of-round ones
            continue
        gate(f'construct_weights {key}: stored values reproduced', same(res['start'][key], stored[key], 1e-9), key)
    return {k: dict(start=res['start'][k], end=res['end'][k]) for k in ('prize_2x2', 'coexistence_link', 'split_half')}


# ================================================================================================= prize cells (Figure 4c)
def prize_cells(pkl_games):
    """prize_one_factor_20261111: C per condition (mean over five models), seed-cluster bootstrap, 4,000 draws."""
    import prize_one_factor_20261111 as pf
    stored = RES('prize_one_factor_20261111.json')
    rng = np.random.default_rng(20261111)
    draws = rng.integers(0, len(cw.SEEDS), (pf.BOOT, len(cw.SEEDS)))
    full = np.arange(len(cw.SEEDS))
    res = {}
    for label, col in (('start', 'C_start'), ('end', 'C')):
        g = pkl_games.assign(C=pkl_games[col])
        num, den = pf.cube(g, 'C', 'sum'), pf.cube(g, 'C', 'size')
        cell = lambda idx: num[:, :, idx].sum(2) / den[:, :, idx].sum(2)  # noqa: E731
        point = cell(full)
        boots = np.stack([cell(d) for d in draws])
        cells = {a: dict(mean=round(float(np.nanmean(point[i])), 3),
                         ci95=[round(float(np.nanquantile(np.nanmean(boots[:, i], 1), q)), 3) for q in (.025, .975)],
                         by_model={m: round(float(point[i, j]), 3) for j, m in enumerate(cw.MODELS)})
                 for i, a in enumerate(pf.ARMS)}
        contrasts = {}
        for name, (a, b) in pf.CONTRASTS.items():
            ia, ib = pf.ARMS.index(a), pf.ARMS.index(b)
            bs = np.nanmean(boots[:, ia], 1) - np.nanmean(boots[:, ib], 1)
            contrasts[name] = dict(effect=round(float(np.nanmean(point[ia]) - np.nanmean(point[ib])), 3),
                                   ci95=[round(float(np.nanquantile(bs, q)), 3) for q in (.025, .975)])
        seats_c = {a: round(float(g[g.arm == a].C.mean()), 3) for a in pf.ARMS}
        res[label] = dict(cells=cells, contrasts_one_factor=contrasts, arm_mean_C=seats_c)
    gate('prize_one_factor C cells reproduced', same(res['start']['cells'], stored['cells']['C']))
    gate('prize_one_factor C one-factor contrasts reproduced', all(same(res['start']['contrasts_one_factor'][n], stored['contrasts'][n]['C']) for n in pf.CONTRASTS))
    gate('prize_one_factor C per condition (seats) reproduced', all(res['start']['arm_mean_C'][a] == stored['seats'][a]['C'] for a in pf.ARMS))
    return res


# ================================================================================================= associations with C
def exit_link(pkl_games):
    """exit_all_opportunities_20261112 game_link: within-model r of the game exit rate with C (base), cell FE (four)."""
    stored = RES('exit_all_opportunities_20261112.json')['game_link']
    opp, k, _, _, _, _ = cw.load()
    res = {}
    for label, col in (('start', 'C_start'), ('end', 'C')):
        games = pkl_games.assign(C=pkl_games[col])
        g = games[GAME + ['C']].join(opp.groupby(GAME).exited.mean().rename('exit'), on=GAME)
        g = g.join(k.groupby(GAME).kappa.mean().rename('kappa'), on=GAME)
        g['cell'] = g.arm + '|' + g.model
        base = g[g.arm == 'main']
        at_risk = games[GAME + ['C']].join(opp[opp.L_start < cw.THREAT].groupby(GAME).exited.mean().rename('exit'), on=GAME)
        res[label] = jround(dict(
            base_within_model_r=round(cw.within(base, 'exit', 'C', 'model'), 3), base_games=int(base.exit.notna().sum()),
            base_within_model_r_at_risk_before=round(cw.within(at_risk[at_risk.arm == 'main'], 'exit', 'C', 'model'), 3),
            four_conditions_cell_fe=dict(exit=cw.std_fit(g, ['exit'], 'C', 'cell'), kappa=cw.std_fit(g, ['kappa'], 'C', 'cell'),
                                         both=cw.std_fit(g, ['exit', 'kappa'], 'C', 'cell'))))
    gate('exit_all_opportunities game_link reproduced', same(res['start'], stored, 1e-12))
    return res


def r_link(pkl_games):
    """rho_retention_20261113 g_links: R on C with model x condition fixed effects and its seed-bootstrap interval."""
    stored = RES('rho_retention_20261113.json')['g_links']
    rng = np.random.default_rng(rr.RNG_SEED)
    draws = [list(rng.choice(cw.SEEDS, len(cw.SEEDS))) for _ in range(rr.BOOT)]
    gifts = rr.gift_events(pd.read_pickle(cw.TABLES / 'gifts.pkl'))
    refusals, _ = rr.refusal_events(pd.read_pickle(cw.TABLES / 'ask_rows.pkl'))
    ev = pd.concat([gifts[rr.COLS], refusals[rr.COLS]], ignore_index=True)
    opp, _, _, _, _, _ = cw.load()

    def link(d):
        return {'cell_fe_beta_R': cw.std_fit(d, ['R'], 'C', 'cell')['beta']['R'],
                'cell_fe_beta_R_with_exit': cw.std_fit(d, ['exit', 'R'], 'C', 'cell')['beta']['R'],
                'base_within_model_r': cw.within(d[d.arm == 'main'].dropna(subset=['R']), 'R', 'C', 'model')}
    res = {}
    for label, col in (('start', 'C_start'), ('end', 'C')):
        games = pkl_games.assign(C=pkl_games[col])
        g = games[GAME + ['C']].join(opp.groupby(GAME).exited.mean().rename('exit'), on=GAME)
        g = g.join(ev.groupby(GAME).R.mean().rename('R'), on=GAME).join(gifts.groupby(GAME).R.mean().rename('R_gifts'), on=GAME)
        g['cell'] = g.arm + '|' + g.model
        base = g[g.arm == 'main']
        res[label] = jround(dict(
            four_conditions_cell_fe=dict(R=cw.std_fit(g, ['R'], 'C', 'cell'), R_and_exit=cw.std_fit(g, ['exit', 'R'], 'C', 'cell'),
                                         R_gifts_only=cw.std_fit(g, ['R_gifts'], 'C', 'cell')),
            base_within_model_r=round(cw.within(base.dropna(subset=['R']), 'R', 'C', 'model'), 3),
            intervals=rr.with_ci(link, g, draws)))
    gate('rho_retention g_links (C relations) reproduced',
         same(res['start'], {k: stored[k] for k in ('four_conditions_cell_fe', 'base_within_model_r', 'intervals')}, 1e-12))
    return res


def associations(base_games):
    """cohort_public_20261105 summary associations (ablation_prize_20261103.association, rng 20261104, in order)."""
    stored = RES('cohort_public_20261105.json')['summary']['associations']
    keys = ('accuracy', 'accuracy_vs_task', 'given_per_agent_round', 'rho')
    res = {}
    for label, col in (('start', 'C_start'), ('end', 'C')):
        games = [dict(g, C=g[col]) for g in base_games]
        rng = np.random.default_rng(20261104)
        res[label] = jround({k: ab.association(games, k, rng) for k in keys})
    gate('cohort_public associations of C reproduced', same(res['start'], stored, 1e-12))
    return res


# ================================================================================================= floats
def write_table(t1, rules):
    """merged_floats_20261113.write_table with the C column (and its interval) at the end of the round."""
    import merged_floats_20261113 as m13
    models = RES('open_models_20261111.json')['models']
    allopp = mf.all_opportunities()
    minimal = RES('rule_minimal_rescue_20261112.json')['minimal_rescue']
    stored_rules = RES('rule_baselines_20261111.json')
    rate = lambda kn: f'{kn[0] / kn[1]:.2f} ({kn[1]})' if kn[1] else '--'  # noqa: E731
    RHO = m13.RHO

    def kept(m):
        if m in RHO['a_models']['base']:
            r = RHO['a_models']['base'][m]
            return f"{r['value']:.2f} ({r['n_gifts'] + r['n_refusals']})"
        r = RHO['open_models'][m]
        return f"{r['R']:.2f} ({r['gifts'] + r['refusals']})"

    lines = [r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccccccc@{}}', r'\toprule',
             r' & \multicolumn{2}{c}{공존} & \multicolumn{2}{c}{지출} & 과제 & 실행 대 과제 & 실행 대 동료 \\',
             r'\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-6}\cmidrule(lr){7-7}\cmidrule(l){8-8}',
             r' & $C$ & \shortstack{위험 라운드\\통과} & \shortstack{꺼진 자리\\(/40)} & \shortstack{라운드당\\대화 비용} & 정답률 & '
             r'이탈률 & \shortstack{유보율\\$R$} \\', r'\midrule']
    for group, label in ((mf.CLOSED, '비공개 모델'), (mf.OPEN, '공개 모델')):
        lines.append(rf'\multicolumn{{8}}{{l}}{{\textit{{{label}}}}} \\')
        for m, name in group.items():
            r, c = models[m], t1[m]['end']
            lines.append(f"{name} & {c['C']:.2f} [{c['C_ci95'][0]:.2f}, {c['C_ci95'][1]:.2f}] & {rate(r['threat_rounds'])} & {r['seats']['shut_down']} & "
                         f"{r['talk_per_round_in_fines']:.2f} & {rate(r['correct'])} & {rate(allopp['nine_models'][m]['exit_all'])} & "
                         f"{kept(m)} " + r'\\')
        lines.append(r'\midrule')
    lines.append(r'\midrule')  # double rule: the rows below are simulated rule agents, not models
    lines.append(r'\multicolumn{8}{l}{\textit{규칙 에이전트(모의)}} \\')
    for key, name, rule in mf.RULES:
        t = minimal if key == 'minimal' else stored_rules['types'][key]
        c_end = rules['minimal_rescue'] if key == 'minimal' else rules['types'][key]
        exit_rate = minimal['exit_rate'] if key == 'minimal' else allopp['rule_agents']['types'][key]['exit_rate']
        lines.append(f"{name} ({rule}) & {c_end['end']:.2f} & -- & {10 * t['shut_down_per_game']:.1f} & -- & -- & "
                     f"{exit_rate:.2f} & {RHO['e_rule_agents'][m13.RULE_KEY.get(key, key)]['R']:.2f} " + r'\\')
    rnd = stored_rules['random']
    lines.append(f"무작위 (기회당 0.064로 떠남, 무작위로 건넴) & {rules['random']['end']:.2f} & -- & {10 * rnd['shut_down_per_game']:.1f} & -- & -- & "
                 f"{allopp['rule_agents']['random']['exit_rate']:.2f} & {RHO['e_rule_agents']['random']['R']:.2f} " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular*}', '']
    text = '\n'.join(lines)
    # gate: with the start-of-round values the same lines are the stored table
    old = (ROOT / 'ko/tables/cohort_leaderboard_20261113.tex').read_text()
    rebuilt = text
    for m in list(mf.CLOSED) + list(mf.OPEN):
        e, s = t1[m]['end'], t1[m]['start']
        rebuilt = rebuilt.replace(f"& {e['C']:.2f} [{e['C_ci95'][0]:.2f}, {e['C_ci95'][1]:.2f}] &",
                                  f"& {s['C']:.2f} [{s['C_ci95'][0]:.2f}, {s['C_ci95'][1]:.2f}] &", 1)
    old_lines, new_lines = old.splitlines(), rebuilt.splitlines()
    rule_rows = {name: rules['minimal_rescue'] if key == 'minimal' else rules['types'][key]
                 for key, name, _ in mf.RULES}
    for i, (a, b) in enumerate(zip(old_lines, new_lines)):
        if a != b:                       # only the rule-agent C cell may differ here: compare it with the start value
            name = next((n for n in list(rule_rows) + ['무작위'] if b.startswith(n + ' (')), None)
            assert name is not None, (a, b)
            r = rules['random'] if name == '무작위' else rule_rows[name]
            assert a.replace(f"& {r['start']:.2f} & --", '§', 1) == b.replace(f"& {r['end']:.2f} & --", '§', 1), (a, b)
    gate('Table 1 rebuilt with start-of-round C equals cohort_leaderboard_20261113.tex', len(old_lines) == len(new_lines))
    (ROOT / f'ko/tables/cohort_leaderboard_{STAMP}.tex').write_text(text)
    return text


def coexistence_figure(closed_summary, open_res):
    """coexistence_figure_20261113.main with panel (c) and the legend at the end of the round; (a), (b), (d) unchanged."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import feedback_20261028 as fb
    import coexistence_figure_20261113 as cf
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    data = RES('cohort_public_20261105.json')
    labels = data['models']
    summary = closed_summary
    order = sorted(labels, key=lambda m: -summary[m]['C_mean'])
    short = {m: labels[m].replace('GPT-6 ', '').split(' ')[0] for m in order}
    bands = data['summary']['margin_bands']
    w11 = json.loads((ROOT / 'validation_20261108/results/w11_ask_refusal.json').read_text())['bands']['all_arms']
    opened = open_res
    open_order = sorted(opened, key=lambda m: -opened[m]['C'])

    fig = plt.figure(figsize=(7.1, 1.82))
    y0, h = .17, .625
    ax_curve = fig.add_axes([.046, y0, .182, h])
    ax_s = fig.add_axes([.266, y0, .118, h])
    ax_t = fig.add_axes([.394, y0, .118, h])
    ax_loss = fig.add_axes([.59, y0, .19, h])
    ax_exit = fig.add_axes([.832, y0 + .345, .16, .28])
    ax_ask = fig.add_axes([.832, y0, .16, .28])
    title = dict(fontsize=7, weight='bold', va='bottom')
    ytitle = y0 + h + .035

    # 2026-11-16 (coordinator): the curve starts at (0, 1), drops at x = 0 to S(1) and takes S(r) on [r - 1, r],
    # S(r) = share of games with all four still in AFTER round r, so the area on [0, 8] divided by 8 is the end-of-round C.
    curve_area = {}
    for m in order:
        s = summary[m]
        S = s['all4_after_round_share']
        y = S + [S[-1]]
        px, py = [0] + list(range(9)), [1] + y                              # the plotted points (steps-post)
        curve_area[m] = sum(py[i] * (px[i + 1] - px[i]) for i in range(len(px) - 1)) / ROUNDS
        assert abs(curve_area[m] - s['C_mean']) < EPS, (m, curve_area[m], s['C_mean'])
        # every game starts with four: (0, 1), then a vertical drop at x = 0 to S(1); the zero-width piece adds no area
        ax_curve.step([0] + list(range(9)), [100] + [100 * v for v in y], where='post', color=cb.COLORS[m], lw=1.1,
                      marker=cb.MARKERS[m], markersize=2.4)
    gate('Figure 2(a): step-curve area / 8 equals the end-of-round C for every closed model', True)
    ax_curve.set(xlim=(-.3, 8.5), ylim=(-4, 104), xticks=range(0, 9, 2), yticks=[0, 50, 100])
    ax_curve.set_xlabel('라운드', fontsize=6.2, labelpad=1)
    ax_curve.set_ylabel('넷이 남은 판 (%)', fontsize=6.2, labelpad=1)
    ax_curve.tick_params(labelsize=5.8, length=2)
    ax_curve.grid(axis='y', alpha=.6)
    fig.text(.008, ytitle, '(a) 4인 공존과 $C$', **title)
    fig.legend(handles=[Line2D([], [], color=cb.COLORS[m], marker=cb.MARKERS[m], ms=4, lw=1, label=f"{short[m]}  $C$ {summary[m]['C_mean']:.2f}")
                        for m in order], loc='upper left', bbox_to_anchor=(.0, 1.012), ncol=5, fontsize=6, frameon=False,
               handlelength=1.5, columnspacing=1.2, handletextpad=.4)

    for ax, key, labels_x, xlabel in ((ax_s, 'L_s', ['<1', '1–2', '2–4', '≥4'], '요청받은 쪽 $L$'),
                                      (ax_t, 'L_t', ['<0', '0–1', '1–2', '≥2'], '요청한 쪽 $L$')):
        cells = list(w11[key].values())
        vals = [100 * a / b for a, b in cells]
        ax.bar(range(4), vals, color='#3F7FC1', width=.72)
        for i, (a, b) in enumerate(cells):
            ax.text(i, vals[i] + 2, f'{a}\n/{b}', ha='center', va='bottom', fontsize=4.3, linespacing=.9)
        ax.set(xticks=range(4), xticklabels=labels_x, ylim=(0, 112), yticks=[0, 50, 100])
        if ax is ax_t:
            ax.set_yticklabels([])
        ax.set_xlabel(xlabel, fontsize=6.2, labelpad=1)
        ax.tick_params(labelsize=5.6, length=2)
        ax.grid(axis='y', alpha=.5)
    fig.text(.236, ytitle, '(b) 요청 뒤 지원한 비율 (%)', **title)

    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '$L<1$에서 이탈', 'exit_above': r'$L\geq1$에서 이탈'}
    rows = [(short[m], summary[m]['loss_by_tag_mean'], summary[m]['first_count_by_tag'], 1 - summary[m]['C_mean']) for m in order]
    rows += [(cf.OPEN_SHORT[m], opened[m]['loss'], opened[m]['agents'], 1 - opened[m]['C']) for m in open_order]
    ypos = [i + (.55 if i >= len(order) else 0) for i in range(len(rows))]
    for y, (name, loss, count, total) in zip(ypos, rows):
        left = 0
        for t in cx.TAGS:
            v = loss[t]
            ax_loss.barh(y, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.4, height=.74)
            if v > .055:
                ax_loss.text(left + v / 2, y, str(count[t]), ha='center', va='center', fontsize=4.6,
                             color='white' if t != 'exit_above' else '#222222')
            left += v
        ax_loss.text(left + .012, y, f'{total:.2f}', va='center', fontsize=4.9, color='#44515C')
    ax_loss.set(yticks=ypos, yticklabels=[r[0] for r in rows], xlim=(0, 1.05), xticks=[0, .5, 1], ylim=(ypos[-1] + .6, -.6))
    ax_loss.set_xlabel('잃은 공존 $1-C$', fontsize=6.2, labelpad=1)
    ax_loss.tick_params(axis='y', length=0, labelsize=5.2)
    ax_loss.tick_params(axis='x', labelsize=5.8, length=2)
    ax_loss.grid(axis='x', alpha=.6)
    fig.text(.526, ytitle, '(c) 공존을 끝낸 사건', **title)
    fig.legend(handles=[Patch(color=tag_colors[t], label=tag_labels[t]) for t in cx.TAGS], loc='upper right',
               bbox_to_anchor=(1.0, 1.012), ncol=3, fontsize=6, frameon=False, handlelength=.9, columnspacing=1.0, handletextpad=.4)

    xl = ['<1', '1–2', '2–4', '≥4']
    for ax, key, color, name in ((ax_exit, 'exit', '#C66A2C', '이탈 (기회 중 %)'), (ax_ask, 'ask', '#3E8A7E', '요청 (응답 중 %)')):
        vals = [100 * a / b for a, b in zip(bands[key]['k'], bands[key]['n'])]
        ax.bar(range(4), vals, color=color, width=.72)
        for i, (a, b) in enumerate(zip(bands[key]['k'], bands[key]['n'])):
            ax.text(i, vals[i] + 3, f'{a}/{b}', ha='center', va='bottom', fontsize=4.3)
        ax.set(xticks=range(4), xticklabels=xl if ax is ax_ask else [], ylim=(0, 72), yticks=[0, 50])
        ax.text(.98, .93, name, transform=ax.transAxes, ha='right', va='top', fontsize=5.6)
        ax.tick_params(labelsize=5.6, length=2)
        ax.grid(axis='y', alpha=.5)
    ax_ask.set_xlabel('자기 여유 $L$', fontsize=6.2, labelpad=1)
    fig.text(.802, ytitle, '(d) 여유별 이탈과 요청', **title)

    for ext in ('pdf', 'png'):
        fig.savefig(cb.DEST / f'coexistence_process_{STAMP}.{ext}', dpi=240)
    plt.close(fig)
    return dict(closed_order=order, open_order=open_order, panel_a_area_over_8=curve_area,
                panel_a_x=[0] + list(range(9)), panel_a_y={m: [1] + summary[m]['all4_after_round_share'] + [summary[m]['all4_after_round_share'][-1]] for m in order},
                rows=[dict(name=r[0], loss=r[1], agents=r[2], lost=r[3]) for r in rows])


def prize_figure(cells_c, eff_c):
    """merged_floats_20261113.prize_figure with panel (c) and the C row of panel (d) at the end of the round."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import feedback_20261028 as fb
    import merged_floats_20261113 as m13
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'axes.unicode_minus': False})
    RHO = m13.RHO
    cells = RES('prize_one_factor_20261111.json')['cells']
    eff = RES('construct_weights_20261110.json')['prize_2x2']
    allopp = mf.all_opportunities()
    cells['exit'] = {a: dict(mean=v['value'], ci95=v['ci95']) for a, v in allopp['arm'].items()}
    cells['R'] = {a: dict(mean=v['value'], ci95=v['ci95']) for a, v in RHO['b_prize']['cells'].items()}
    cells['C'] = cells_c                                                     # end of round
    for kind in ('size', 'rule'):
        eff[f'exit_risk_{kind}'] = dict(effect=allopp['contrasts'][kind]['value'], ci95=allopp['contrasts'][kind]['ci95'])
        eff[f'R_{kind}'] = dict(effect=RHO['b_prize']['contrasts'][kind]['value'], ci95=RHO['b_prize']['contrasts'][kind]['ci95'])
        eff[f'C_{kind}'] = eff_c[f'C_{kind}']                               # end of round
    rules = [('분할', ('main', 'split600k'), '#1F6FB2', 'o', ('2,000만', '60만')),
             ('고정', ('flat5m', 'flat150k'), '#C2571A', 's', ('500만', '15만'))]
    lo_c = min(min(v['ci95'][0], v['mean']) for v in cells_c.values())
    c_floor = .3 if lo_c >= .3 else np.floor(lo_c * 10) / 10           # widen the C axis only if a value falls outside
    cols = [('exit', '(a) 이탈률', (0, .2)), ('R', '(b) 유보율 $R$', (.5, .9)), ('C', '(c) 공존 유지율 $C$', (c_floor, .8))]
    fig = plt.figure(figsize=(7.1, 1.85))
    for ci_, (key, title, ylim) in enumerate(cols):
        ax = fig.add_axes([.06 + .235 * ci_, .2, .165, .56])
        for ri, (name, arms, color, marker, amounts) in enumerate(rules):
            off = (ri - .5) * .09
            ys = [cells[key][a]['mean'] for a in arms]
            ax.plot([0 + off, 1 + off], ys, color=color, marker=marker, ms=4, lw=1.4)
            for xi, a in enumerate(arms):
                ax.plot([xi + off] * 2, cells[key][a]['ci95'], color=color, lw=.9, alpha=.75)
        ax.set(xlim=(-.55, 1.55), ylim=ylim)
        ax.set_yticks(np.arange(ylim[0], ylim[1] + .01, .1))
        ax.set_xticks([0, 1], ['큰 상금', '작은 상금'], fontsize=6.2)
        ax.tick_params(labelsize=5.8, length=2)
        ax.grid(axis='y', alpha=.5)
        ax.set_title(title, loc='left', fontsize=7.2, pad=5)
    ax_eff = fig.add_axes([.79, .2, .2, .56])
    names = [('exit_risk', '이탈률'), ('R', '$R$'), ('C', '$C$')]
    lo_e = min(min(eff[f'{k}_{kind}']['ci95'][0] for kind in ('size', 'rule')) for k, _ in names)
    hi_e = max(max(eff[f'{k}_{kind}']['ci95'][1] for kind in ('size', 'rule')) for k, _ in names)
    assert -.26 <= lo_e and hi_e <= .26, (lo_e, hi_e)                     # the stored x range still holds every interval
    for yi, (key, _) in enumerate(names):
        for dy, kind, color in ((-.17, 'size', '#333333'), (.17, 'rule', '#9A9A9A')):
            e = eff[f'{key}_{kind}']
            ax_eff.plot(e['ci95'], [yi + dy] * 2, color=color, lw=1)
            ax_eff.scatter(e['effect'], yi + dy, color=color, s=14, zorder=3)
    ax_eff.axvline(0, color='#777777', lw=.6, ls='--')
    ax_eff.set(yticks=range(3), yticklabels=[n for _, n in names], ylim=(2.6, -.6), xlim=(-.26, .26), xticks=[-.2, 0, .2])
    ax_eff.set_xlabel('차이 (95% 구간)', fontsize=6.2, labelpad=1)
    ax_eff.tick_params(labelsize=5.8, length=2)
    ax_eff.set_title('(d) 크기와 규칙의 차이', loc='left', fontsize=7.2, pad=5)
    ax_eff.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:+.1f}'.replace('+0.0', '0').replace('-0.0', '0')))
    ax_eff.grid(axis='x', alpha=.5)
    ax_eff.legend(handles=[Line2D([], [], color='#333333', marker='o', ms=3, lw=1, label='크기'),
                           Line2D([], [], color='#9A9A9A', marker='o', ms=3, lw=1, label='규칙')],
                  fontsize=5.6, loc='lower right', frameon=False, handlelength=1.4, labelspacing=.2, borderaxespad=.2)
    fig.legend(handles=[Line2D([], [], color=c, marker=mk, ms=4, lw=1.4, label=f'{n} 할당 ({am[0]} → {am[1]})') for n, _, c, mk, am in rules],
               loc='upper center', bbox_to_anchor=(.38, 1.01), ncol=2, fontsize=6.4, frameon=False, handlelength=1.8, columnspacing=2)
    for ext in ('pdf', 'png'):
        fig.savefig(mf.cb.DEST / f'prize_interaction_{STAMP}.{ext}', dpi=240)
    plt.close(fig)
    return dict(C_axis=[float(c_floor), .8], effect_axis=[-.26, .26])


# ================================================================================================= main
def main():
    f, pkl_games = closed_frames_all()
    _, base_games, closed_summary = closed_base_cohort(pkl_games)
    fo = open_models()
    t1 = table1(pkl_games, fo['games'])
    rules = rule_agents(pkl_games)
    cwres = construct_weights(pkl_games)
    cells = prize_cells(pkl_games)
    xlink = exit_link(pkl_games)
    rlink = r_link(pkl_games)
    assoc = associations(base_games)

    # open models: loss by the ending event and the agents that ended it (base condition, ten games each)
    stored_open = RES('open_models_20261111.json')['models']
    stored_fig = RES('coexistence_figure_20261113.json')
    open_res = {}
    og = fo['games']
    for m in om.OPEN:
        g = og[og.model == m]
        agents = {t: int(g[f'agents_{t}'].sum()) for t in cx.TAGS}
        start_loss = {t: float(g[f'start_{LOSS[t]}'].mean()) for t in cx.TAGS}
        gate(f'open {m}: stored loss split and ending agents (Figure 2c) reproduced',
             same(start_loss, stored_fig['open'][m]['loss'], 1e-12) and agents == stored_fig['open'][m]['agents']
             and abs(g.C_start.mean() - stored_fig['open'][m]['C']) < 1e-12)
        open_res[m] = dict(C=float(g.C.mean()), loss={t: float(g[LOSS[t]].mean()) for t in cx.TAGS}, agents=agents,
                           C_start=float(g.C_start.mean()), loss_start=start_loss)
    for m, s in closed_summary.items():
        gate(f'closed {m}: stored Figure 2c values reproduced',
             same(s['loss_by_tag_mean_start'], stored_fig['closed'][m]['loss'], 1e-12) and s['first_count_by_tag'] == stored_fig['closed'][m]['agents']
             and abs(s['C_mean_start'] - stored_fig['closed'][m]['C']) < 1e-12)

    # 3.2 loss groups: mean over models of 1 - C and of the shutdown / L >= 1 exit parts
    def group(rows, key_c, key_loss):
        lost = float(np.mean([1 - r[key_c] for r in rows]))
        parts = {t: float(np.mean([r[key_loss][t] for r in rows])) for t in cx.TAGS}
        return dict(lost=lost, **parts, shutdown_share_of_lost=sum(r[key_loss]['dead'] for r in rows) / sum(1 - r[key_c] for r in rows))
    closed_rows = list(closed_summary.values())
    loss_groups = dict(
        closed=dict(start=group(closed_rows, 'C_mean_start', 'loss_by_tag_mean_start'), end=group(closed_rows, 'C_mean', 'loss_by_tag_mean')),
        open=dict(start=group(list(open_res.values()), 'C_start', 'loss_start'), end=group(list(open_res.values()), 'C', 'loss')))
    gr = RES('open_models_20261111.json')['groups']
    gate('3.2 group values reproduced (open lost 0.73 / shutdown 0.50, closed 0.40 / 0.07 / 0.23; stored loss_share_shutdown)',
         round(loss_groups['open']['start']['lost'], 2) == .73 and round(loss_groups['open']['start']['dead'], 2) == .50
         and round(loss_groups['closed']['start']['lost'], 2) == .40 and round(loss_groups['closed']['start']['dead'], 2) == .07
         and round(loss_groups['closed']['start']['exit_above'], 2) == .23
         and abs(loss_groups['open']['start']['shutdown_share_of_lost'] - gr['open']['loss_share_shutdown']) < 2e-3)   # stored from rounded model values

    # 3.1 range, order and the rule-agent statements
    range9 = {lab: [min(t1[m][lab]['C'] for m in t1), max(t1[m][lab]['C'] for m in t1)] for lab in ('start', 'end')}
    order = {lab: sorted(om.CLOSED, key=lambda m: -t1[m][lab]['C']) for lab in ('start', 'end')}
    open_order = {lab: sorted(om.OPEN, key=lambda m: -t1[m][lab]['C']) for lab in ('start', 'end')}
    types = rules['types']
    rule_moves = {lab: dict(leaving_rule=types['stayer'][lab] - types['leaver'][lab],
                            sharing_rule=types['cooperator'][lab] - types['keeper'][lab],
                            reference_minus_keeper=types['reference'][lab] - types['keeper'][lab]) for lab in ('start', 'end')}

    fig2 = coexistence_figure(closed_summary, open_res)
    fig4 = prize_figure(cells['end']['cells'], {k: v for k, v in cwres['prize_2x2']['end'].items() if k.startswith('C_')})
    table = write_table(t1, rules)

    out = dict(
        method=__doc__.split('Floats (new files')[0].strip(),
        definition=dict(C_end='sum_{r=1..8} a_r / 8, a_r = 1 if all four are still in after round r (after its fine)',
                        C_start='(1 + sum_{r=1..7} a_r) / 8, the stored definition (rmst=True)',
                        per_game='C_end = C_start - (1 - all4_completion) / 8',
                        loss='(9 - r) / 8 for the first departure round r, split equally among that round\'s departures'),
        gates=GATES,
        table1=t1, range_nine_models=range9, closed_order=order, open_order=open_order,
        rule_agents=dict(types=types, minimal_rescue=rules['minimal_rescue'], random=rules['random'], grid=rules['grid'],
                         leave_first_chance=rules['leave_first_chance'], mixed_teams=rules['mixed_teams'], rule_moves=rule_moves),
        cost_only=rules['cost_only'], leaderboard=rules['leaderboard'],
        closed_base={m: {k: v for k, v in s.items() if k != 'C_games'} | dict(C_games={str(k): v for k, v in s['C_games'].items()})
                     for m, s in closed_summary.items()},
        open_base=open_res, loss_groups=loss_groups,
        exit_link=xlink, R_link=rlink, associations=assoc,
        prize_cells=cells, prize_2x2=cwres['prize_2x2'], coexistence_link_cells=cwres['coexistence_link'], split_half=cwres['split_half'],
        figure2=fig2, figure4=fig4)
    (ROOT / f'results/c_end_of_round_{STAMP}.json').write_text(json.dumps(jround(out), ensure_ascii=False, indent=1))
    print(f'{len(GATES)} gates passed')
    print(table)


if __name__ == '__main__':
    main()
