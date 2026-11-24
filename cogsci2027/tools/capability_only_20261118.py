"""Capability-only control (2026-11-18, researcher): how much coexistence each model would keep if it had its own
capability (talk cost and accuracy) but the reference rule agent's propensity (leaves once its round-start margin
L < 1, hands over 0.25 x half the margin gap to a peer below L = 1).

It extends the cost-only control of rule_baselines_20261111 (same_rule_under_each_models_cost: the model's generation
costs, pooled accuracy, closed five models, costs from all four prize conditions) in three ways:
  * accuracy is the model's own as well: the pooled per (seed, round) wrong-answer rate of w1_ev_baseline.calibrate,
    logit-shifted to the model's wrong rate over its VALID answers (solve calls not truncated). Void answers and
    shut-downs before the solve are left out of that rate because the simulator produces them from the costs,
    (Table 1's 정답률 counts void answers as failures: GPT-OSS 9 right of 21 there, 9 of 14 valid answers here),
  * the four open models are added,
  * every model is calibrated on its base-condition games only (20,000,000 split, seeds 4101-4110), the games of Table 1.
Per model, three simulations of the reference rule (400 games on each of the ten seeds):
  cost      the model's talk and solve costs, pooled accuracy
  accuracy  pooled costs, the model's accuracy
  both      the model's costs and accuracy (= capability only)
C is read at the end of the round (c_end_of_round_20261116), with a seed-cluster bootstrap 95% interval as in
table1_rule_ci_20261117. Observed C is Table 1's (results/c_end_of_round_20261116.json, table1 end).
Reading: reference C - both = coexistence lost to capability; both - observed = lost to propensity (the model's
own leaving and giving, measured against the reference rule).

Gate: the closed models' cost-only C with all four conditions' costs (rule_baselines calibration) is recomputed
here with a fresh stream; it must lie within 0.02 of the stored start-of-round value (Monte-Carlo noise only).

Data scope (paper/AGENTS.md): 5.2 arena v33, seeds 4101-4110. Closed five models through validation_data
(validation_20261108/tools), open four models through open_models_20261111 (manifest
result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json). No model calls.
Output: results/capability_only_20261118.json
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python capability_only_20261118.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import margin_band_paths_20261116 as mbp  # noqa: E402
import rule_baselines_20261111 as rb  # noqa: E402

w1 = rb.w1
ROOT = rb.ROOT
RNG_SEED = 20261118
REF = (1.0, .25)                                          # reference rule (기준형): exit L < 1, kappa 0.25
KEY = ['arm', 'model', 'seed', 'round', 'agent']


def open_frames():
    om = mbp.om
    om.MANIFEST = mbp.REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'
    cwd = os.getcwd()
    os.chdir(mbp.REPO)
    try:
        return om.open_frames()
    finally:
        os.chdir(cwd)


def model_cal(ar, calls, q_sr):
    """Cost arrays and per (seed, round) wrong-answer probability of one model, as w1_ev_baseline.calibrate does."""
    talk = calls[calls.kind == 'talk'].groupby(KEY + ['phase']).used.sum().unstack('phase').fillna(0)
    for ph in ('prep', 'rescue'):
        if ph not in talk:
            talk[ph] = 0.0
    talk = talk.reset_index().merge(ar[KEY + ['wrong', 'exited']], on=KEY)
    stay = talk[~talk.exited]
    # accuracy over valid answers only: the simulator makes void answers (a solve call past the balance) and
    # shut-downs before the solve from the costs, so counting them as wrong here would count them twice
    sv = calls[(calls.kind == 'solve') & ~calls.truncated.astype(bool)].merge(ar[ar.solver.astype(bool)][KEY + ['wrong']], on=KEY)
    q = float(sv.wrong.astype(bool).mean())
    base = [w1.logit(q_sr[(s, r)]) for s, r in zip(sv.seed, sv['round'])]
    dl = brentq(lambda x: np.mean([w1.expit(b + x) for b in base]) - q, -8, 8)
    return dict(prep=talk.prep.to_numpy(float), rescue_w=stay[stay.wrong == True].rescue.to_numpy(float),  # noqa: E712
                rescue_c=stay[stay.wrong == False].rescue.to_numpy(float),  # noqa: E712
                solve=calls[calls.kind == 'solve'].used.to_numpy(float),
                q={k: w1.expit(w1.logit(v) + dl) for k, v in q_sr.items()}, wrong_rate=q)


def sim(c, rng, solver1, refill):
    parts = [rb.simulate(c, s, REF[0], REF[1], rb.REPS, rng, solver1, refill) for s in rb.d.SEEDS]
    end = [p['C'] - (~p['all4']) / w1.ROUNDS for p in parts]
    by_seed = np.array([float(e.mean()) for e in end])
    boots = by_seed[np.random.default_rng(rb.RNG_SEED).integers(0, len(by_seed), (4000, len(by_seed)))].mean(1)
    return dict(C=round(float(np.concatenate(end).mean()), 3),
                C_ci95=[round(float(np.quantile(boots, q)), 3) for q in (.025, .975)],
                C_start=round(float(np.concatenate([p['C'] for p in parts]).mean()), 3),
                shut_down_per_game=round(float(np.concatenate([p['dead'] for p in parts]).mean()), 3),
                exits_per_game=round(float(np.concatenate([p['exited'] for p in parts]).mean()), 3))


def write_table(rows, ref):
    """Appendix table ko/tables/capability_only_20261118.tex."""
    names = mbp.om.CLOSED | mbp.om.OPEN
    ci = lambda r: f"{r['C']:.2f} [{r['C_ci95'][0]:.2f}, {r['C_ci95'][1]:.2f}]"  # noqa: E731
    lines = [r'\begin{tabular}{@{}lccccccc@{}}', r'\toprule',
             r' & & \multicolumn{4}{c}{기준형 규칙의 모의} & \multicolumn{2}{c}{잃은 공존} \\',
             r'\cmidrule(lr){3-6}\cmidrule(l){7-8}',
             r' & \shortstack{유효 답\\정답률} & 비용만 & 정답률만 & 능력만 & 관측 $C$ & 능력 & 성향 \\', r'\midrule',
             f"기준형 (평균 능력) & -- & \\multicolumn{{3}}{{c}}{{{ci(ref)}}} & & & \\\\", r'\midrule']
    for g, label in (('closed', '비공개 모델'), ('open', '공개 모델')):
        lines.append(rf'\multicolumn{{8}}{{l}}{{\textit{{{label}}}}} \\')
        for m, r in rows.items():
            if r['group'] != g:
                continue
            lines.append(f"{names[m]} & {1 - r['wrong_rate']:.2f} & {r['cost']['C']:.2f} & {r['accuracy']['C']:.2f} & {ci(r['both'])} & "
                         f"{ci(r['observed'])} & ${r['lost_to_capability']:+.2f}$ & ${r['lost_to_propensity']:+.2f}$ " + r'\\')
    lines += [r'\bottomrule', r'\end{tabular}', '']
    (ROOT / 'ko/tables/capability_only_20261118.tex').write_text('\n'.join(lines))


def main():
    f = rb.d.load()
    cal, solver1, _, _ = w1.calibrate(f)
    refill = w1.Refill(w1.seat_agents(f['seats']))
    pooled = cal['pooled']
    q_sr = pooled['q']                                    # pooled per (seed, round) rate (logit shift 0)
    stored = json.loads((ROOT / 'results/rule_baselines_20261111.json').read_text())['same_rule_under_each_models_cost']
    observed = json.loads((ROOT / 'results/c_end_of_round_20261116.json').read_text())['table1']
    rng = np.random.default_rng(RNG_SEED)
    gates = {}
    for m in rb.MODELS:                                   # gate: the stored cost-only control
        c = dict(prep=cal[m]['prep'], rescue_w=cal[m]['rescue_w'], rescue_c=cal[m]['rescue_c'], solve=cal[m]['solve'], q=q_sr)
        got, want = sim(c, rng, solver1, refill)['C_start'], stored[m]['exit L<1, kappa 0.25']
        gates[m] = dict(recomputed=got, stored=want)
        assert abs(got - want) <= .02, (m, got, want)

    fo = open_frames()
    frames = {'closed': (f['agent_rounds'], f['calls']), 'open': (fo['agent_rounds'], fo['calls'])}
    models = [(m, 'closed') for m in mbp.CLOSED] + [(m, 'open') for m in mbp.OPEN]
    ref = sim(pooled, np.random.default_rng(RNG_SEED), solver1, refill)
    rows = {}
    for m, g in models:
        ar, calls = frames[g]
        ar, calls = ar[(ar.arm == 'main') & (ar.model == m)], calls[(calls.arm == 'main') & (calls.model == m)]
        assert ar.seed.nunique() == 10, (m, ar.seed.nunique())
        mc = model_cal(ar, calls, q_sr)
        costs = {k: mc[k] for k in ('prep', 'rescue_w', 'rescue_c', 'solve')}
        pcost = {k: pooled[k] for k in ('prep', 'rescue_w', 'rescue_c', 'solve')}
        runs = {name: sim(c, np.random.default_rng(RNG_SEED), solver1, refill) for name, c in
                (('cost', dict(costs, q=q_sr)), ('accuracy', dict(pcost, q=mc['q'])), ('both', dict(costs, q=mc['q'])))}
        obs = observed[m]['end']['C']
        rows[m] = dict(group=g, wrong_rate=round(mc['wrong_rate'], 3),
                       talk_per_round=round(float(mc['prep'].mean() + np.concatenate([mc['rescue_w'], mc['rescue_c']]).mean()), 0),
                       observed=dict(C=obs, C_ci95=observed[m]['end']['C_ci95']), **runs,
                       lost_to_capability=round(ref['C'] - runs['both']['C'], 3),
                       lost_to_propensity=round(runs['both']['C'] - obs, 3))
    out = dict(method=__doc__, reference_rule=dict(exit='L<1', kappa=.25, **ref), gate_cost_only_closed=gates,
               pooled_wrong_rate=round(float(pooled['q_mean']), 3), models=rows)
    (ROOT / 'results/capability_only_20261118.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    write_table(rows, ref)
    print('reference', ref)
    print(pd.DataFrame({m: dict(obs=r['observed']['C'], both=r['both']['C'], cost=r['cost']['C'], acc=r['accuracy']['C'],
                                wrong=r['wrong_rate'], cap_loss=r['lost_to_capability'], prop_loss=r['lost_to_propensity'],
                                dead_both=r['both']['shut_down_per_game'], exits_both=r['both']['exits_per_game'])
                        for m, r in rows.items()}).T.to_string())
    print('gate', gates)


if __name__ == '__main__':
    main()
