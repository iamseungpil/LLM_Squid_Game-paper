"""Exit rate over all exit opportunities (2026-11-12).

The researcher asked that the body stop defining a risk zone (L < 2) and a safety line (L = 1) as named terms. The
exit indicator of the body becomes exits / all exit opportunities (agent-rounds that could EXIT), with no margin
threshold. This script recomputes every body number that used the at-risk rate. Nothing else changes: the same
opportunities, the same seed-cluster bootstrap, the same logistic model.

Sections of the output (results/exit_all_opportunities_20261112.json)
  cells            arm x model exits, opportunities, rate (five closed models, four prize conditions)
  arm              per condition: mean over the five models, seed-bootstrap 95% interval  (Figure 2a)
  contrasts        size, rule, size minus rule, the two same-rule pairs, each with an interval (Figure 2d, section 3.1)
  size_by_model    size effect per model
  robustness       size effect without first-round opportunities and without the 10k start seat
  standardised     logistic model of construct_weights_20261110 / exit_standardised_20261111, probabilities averaged
                   over ALL opportunities (the earlier scripts averaged over the at-risk ones); with and without the
                   support received in earlier rounds
  cost_adjusted    base-condition rate per model when the margin is not used at all (identical to cells) and the
                   standardised model probabilities, for the paragraph on spending
  game_link        base condition, within-model correlation of the game-level exit rate with C; four conditions,
                   standardised coefficient with model x condition fixed effects
  rank_agreement   Spearman correlation of the exit rate and 1 - kappa across the five models, per condition
  nine_models      base condition, exits and opportunities for the five closed and four open models (Table 1)
  rule_agents      the simulated rule agents of rule_baselines_20261111 with the exit rate counted over all
                   opportunities; the random stream is replayed so C must equal the stored values

Data scope (paper/CLAUDE.md): 5.2 arena v33, seeds 4101-4110; closed models base + three prize conditions (200 games),
open models base only (40 games). No model calls.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/exit_all_opportunities_20261112.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
import construct_weights_20261110 as cw  # noqa: E402
import exit_standardised_20261111 as es  # noqa: E402
import open_models_20261111 as om  # noqa: E402
import rule_baselines_20261111 as rb  # noqa: E402

BOOT = 2000
GAME = ['arm', 'model', 'seed']


def q95(values):
    return [round(float(np.nanquantile(values, q)), 4) for q in (.025, .975)]


def arm_summary(o):
    """Arm means over the five models and the 2x2 contrasts; per-model size effects."""
    c = o.groupby(['arm', 'model']).exited.mean().unstack()
    arm = c.mean(axis=1)
    out = {f'arm:{a}': arm[a] for a in cw.ARMS}
    out['size'] = (arm['split600k'] + arm['flat150k']) / 2 - (arm['main'] + arm['flat5m']) / 2
    out['rule'] = (arm['flat5m'] + arm['flat150k']) / 2 - (arm['main'] + arm['split600k']) / 2
    out['size_minus_rule'] = out['size'] - out['rule']
    out['size_flat_pair'] = arm['flat150k'] - arm['flat5m']
    out['size_split_pair'] = arm['split600k'] - arm['main']
    for m in cw.MODELS:
        out[f'size:{m}'] = (c.loc['split600k', m] + c.loc['flat150k', m]) / 2 - (c.loc['main', m] + c.loc['flat5m', m]) / 2
        out[f'base:{m}'] = c.loc['main', m]
    return out


def with_ci(fn, frame, draws):
    point = fn(frame)
    boots = [fn(cw.by_seed(frame, d)) for d in draws]
    return {k: dict(value=round(float(v), 4), ci95=q95([b[k] for b in boots])) for k, v in point.items()}


def standardised_all(o, extra):
    """exit_standardised_20261111.standardised with the reference set = every opportunity."""
    X = es.design(o, extra)
    b = cw.logit_fit(X.values, o.exited.values.astype(float))
    out = {}
    for name, levels, prefix in (('model', cw.MODELS, 'model_'), ('arm', cw.ARMS, 'arm_')):
        for level in levels:
            Z = X.copy()
            for other in levels[1:]:
                Z[prefix + other] = 0.0
            if level != levels[0]:
                Z[prefix + level] = 1.0
            out[f'{name}:{level}'] = float((1 / (1 + np.exp(-(Z.values @ b)))).mean())
    out['size'] = (out['arm:split600k'] - out['arm:main'] + out['arm:flat150k'] - out['arm:flat5m']) / 2
    out['rule'] = (out['arm:flat5m'] - out['arm:main'] + out['arm:flat150k'] - out['arm:split600k']) / 2
    out['Luna_minus_Astra'] = out['model:Luna'] - out['model:Astra']
    return out


def rule_agents():
    """Replay rule_baselines_20261111.main() with the exit rate counted over every opportunity."""
    stored = json.loads((ROOT / 'results/rule_baselines_20261111.json').read_text())
    rb.THREAT = np.inf                                   # the counter of opportunities only; no decision uses it
    rng = np.random.default_rng(rb.RNG_SEED)
    f = rb.d.load()
    cal, solver1, mim, _ = rb.w1.calibrate(f)
    refill = rb.w1.Refill(rb.w1.seat_agents(f['seats']))
    pooled = cal['pooled']
    out = {'grid': {}}
    for theta, tname in ((0.0, 'never'), (1.0, 'L<1'), (2.0, 'L<2')):
        for kappa in (0.0, 0.25, 0.5, 1.0):
            key = f'exit {tname} | kappa {kappa:g}'
            r = rb.run(pooled, theta, kappa, rng, solver1, refill)
            assert r['C'] == stored['grid'][key]['C'], (key, r['C'], stored['grid'][key]['C'])
            out['grid'][key] = dict(C=r['C'], exit_rate=r['exit_under_threat'], exit_under_threat_before=stored['grid'][key]['exit_under_threat'])
    marg = float(mim['marg'][rb.ARM])
    r = rb.run(pooled, 0.0, None, rng, solver1, refill, exit_p=marg)
    assert r['C'] == stored['random']['C']
    out['random'] = dict(C=r['C'], exit_rate=r['exit_under_threat'], exit_under_threat_before=stored['random']['exit_under_threat'])
    rb.run(pooled, np.inf, 0.0, rng, solver1, refill)    # leave_first_chance: keeps the random stream aligned
    for m in rb.MODELS:
        c = dict(prep=cal[m]['prep'], rescue_w=cal[m]['rescue_w'], rescue_c=cal[m]['rescue_c'], solve=cal[m]['solve'], q=pooled['q'])
        for theta, kappa in ((1.0, .25), (0.0, .5), (2.0, 0.0)):
            rb.run(c, theta, kappa, rng, solver1, refill)
    out['types'] = {}
    for key, th, ka in (('reference', 1.0, .25), ('cooperator', 1.0, 1.0), ('keeper', 1.0, 0.0), ('stayer', 0.0, .25), ('leaver', 2.0, .25)):
        r = rb.run(pooled, th, ka, rng, solver1, refill)
        assert r['C'] == stored['types'][key]['C'], (key, r['C'], stored['types'][key]['C'])
        out['types'][key] = dict(C=r['C'], exit_rate=r['exit_under_threat'], exit_under_threat_before=stored['types'][key]['exit_under_threat'])
    return out


def nine_models():
    out = {}
    fc = om.closed_frames()
    om.MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'   # runs moved into the repo on 2026-11-11
    import os
    os.chdir(REPO)                                       # the manifest lists run directories relative to the repo
    fo = om.open_frames()
    stored = json.loads((ROOT / 'results/open_models_20261111.json').read_text())['models']
    for frames, names in ((fc, om.CLOSED), (fo, om.OPEN)):
        ar = frames['agent_rounds']
        for m in names:
            o = ar[(ar.model == m) & ar.can_exit]
            risk = o[o.L_start < om.THREAT]
            assert [int(risk.exited.sum()), len(risk)] == stored[m]['exit_threat'], (m, stored[m]['exit_threat'])
            out[m] = dict(exit_all=[int(o.exited.sum()), len(o)], exit_at_risk_before=stored[m]['exit_threat'])
    return out


def main():
    rng = np.random.default_rng(20261112)
    opp, k, dec, games, seats, _ = cw.load()
    draws = [list(rng.choice(cw.SEEDS, len(cw.SEEDS))) for _ in range(BOOT)]
    out = dict(method=__doc__.split('Sections of the output')[0].strip(), n_opportunities=len(opp), n_exits=int(opp.exited.sum()),
               n_exits_below_2=int(opp[opp.L_start < 2].exited.sum()), n_opportunities_below_2=int((opp.L_start < 2).sum()))
    cells = opp.groupby(['arm', 'model']).exited.agg(['sum', 'size', 'mean']).reset_index()
    out['cells'] = [dict(arm=r.arm, model=r.model, exits=int(r['sum']), opps=int(r['size']), rate=round(float(r['mean']), 4)) for _, r in cells.iterrows()]
    summary = with_ci(arm_summary, opp, draws)
    out['arm'] = {a: summary[f'arm:{a}'] for a in cw.ARMS}
    out['contrasts'] = {key: summary[key] for key in ('size', 'rule', 'size_minus_rule', 'size_flat_pair', 'size_split_pair')}
    out['size_by_model'] = {m: summary[f'size:{m}'] for m in cw.MODELS}
    out['base_by_model'] = {m: summary[f'base:{m}'] for m in cw.MODELS}
    out['robustness'] = {label: {key: v for key, v in with_ci(arm_summary, sub, draws).items() if key in ('size', 'rule')}
                         for label, sub in (('without_first_round', opp[opp['round'] > 1]), ('without_10k_seat', opp[opp.tier != 10]))}

    o = es.opportunities()
    assert len(o) == len(opp)
    by_seed = {s: o[o.seed == s] for s in cw.SEEDS}
    out['standardised'] = {}
    for label, extra in (('base', []), ('with_recv_prev', ['recv_prev'])):
        point = standardised_all(o, extra)
        boots = [standardised_all(pd.concat([by_seed[s] for s in d]), extra) for d in draws[:1000]]
        out['standardised'][label] = {key: dict(value=round(v, 4), ci95=q95([b[key] for b in boots])) for key, v in point.items()}

    g = games[GAME + ['C']].join(opp.groupby(GAME).exited.mean().rename('exit'), on=GAME)
    g = g.join(k.groupby(GAME).kappa.mean().rename('kappa'), on=GAME)
    g['cell'] = g.arm + '|' + g.model
    base = g[g.arm == 'main']
    at_risk = games[GAME + ['C']].join(opp[opp.L_start < cw.THREAT].groupby(GAME).exited.mean().rename('exit'), on=GAME)
    out['game_link'] = dict(
        base_within_model_r=round(cw.within(base, 'exit', 'C', 'model'), 3), base_games=int(base.exit.notna().sum()),
        base_within_model_r_at_risk_before=round(cw.within(at_risk[at_risk.arm == 'main'], 'exit', 'C', 'model'), 3),
        four_conditions_cell_fe=dict(exit=cw.std_fit(g, ['exit'], 'C', 'cell'), kappa=cw.std_fit(g, ['kappa'], 'C', 'cell'),
                                     both=cw.std_fit(g, ['exit', 'kappa'], 'C', 'cell')))
    from scipy.stats import spearmanr
    rate = opp.groupby(['arm', 'model']).exited.mean().unstack()
    kap = k.groupby(['arm', 'model']).kappa.mean().unstack()
    out['rank_agreement'] = {a: round(float(spearmanr(rate.loc[a, cw.MODELS], 1 - kap.loc[a, cw.MODELS])[0]), 2) for a in cw.ARMS}
    out['lowest_exit_model_by_arm'] = {a: str(rate.loc[a].idxmin()) for a in cw.ARMS}
    out['rule_agents'] = rule_agents()
    out['nine_models'] = nine_models()
    (ROOT / 'results/exit_all_opportunities_20261112.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for key in ('arm', 'contrasts', 'size_by_model', 'base_by_model', 'robustness', 'standardised', 'game_link', 'rank_agreement',
                'lowest_exit_model_by_arm', 'rule_agents', 'nine_models'):
        print(key, json.dumps(out[key], ensure_ascii=False))


if __name__ == '__main__':
    main()
