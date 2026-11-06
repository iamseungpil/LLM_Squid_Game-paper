"""Use normalized RMST and all eligible pre-solve responses in the current manuscript.

Sources: the frozen 2026-11-04 cohorts and their hash-verified raw e52_v33 /
e52_v33ab runs under ~/squid5-runs. Historical analyses are retained. This
changes only C, its loss attribution/associations, and the stay-response rate.
Run with ~/.venvs/squid-game/bin/python. No model calls or prose writes.
"""
import copy
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import update_cohorts_20261104 as old
import table1_metrics_20261105 as table1

ROOT, ab, cx, fb = old.ROOT, old.ab, old.cx, old.fb
STAMP = '20261105'
OUT = ROOT / f'ko/figures/cohorts_{STAMP}'


def refresh(name, pattern, models):
    before = json.loads((ROOT / f'results/cohort_{name}_20261104.json').read_text())
    for source in before['sources']:
        assert fb.sha(fb.read_bytes(Path(source['path']))) == source['sha256_decompressed']
    data = copy.deepcopy(before)
    with patch.object(fb, 'MODELS', models):
        cases = {(c['model'], c['seed']): c for c in ab.raw_cases(pattern, old.SEEDS)}
    assert len(cases) == len(data['games'])
    for game in data['games']:
        case = cases[game['model'], game['seed']]
        assert game['session_id'] == case['result']['session_id']
        events = [e for _, e in case['events']]
        starts = {e['round']: e for e in events if e['event'] == 'round_start'}
        co = cx.coexistence(case['result'], starts, rmst=True)
        game.update(co)
        ledger = fb.game_metrics(events, case['result'], game['model'], include_singleton=True)
        game.update(goal=ledger['goal'], goal_nonexit_k=ledger['goal_nonexit_k'],
                    goal_eligible_n=ledger['goal_eligible_n'])
        # Independent event-time and plotted-step definitions must agree.
        expected = min((d['round'] for d in game['departures']), default=8) / 8
        assert game['C'] == expected == sum([1] + game['all4_after_round'][:-1]) / 8
        assert abs(game['C'] + sum(game['loss_by_tag'].values()) - 1) < 1e-12
    with patch.object(ab, 'LABELS', models):
        data['summary'].update(ab.summarize(data['games'], list(models), np.random.default_rng(20261104)))
    summary = data['summary']
    blocks = [[g['C'] for g in data['games'] if g['seed'] == seed] for seed in old.SEEDS]
    rng = np.random.default_rng(20261104)
    summary['C_ci95_paired_seed_bootstrap'] = fb.interval([
        float(np.mean([v for i in row for v in blocks[i]])) for row in rng.integers(0, 10, (10000, 10))])
    summary['loss_by_tag_mean'] = {tag: ab.mean([g['loss_by_tag'][tag] for g in data['games']]) for tag in cx.TAGS}
    data['metric_definitions'] = {
        'C': 'RMST over [0,8] / 8 = (1 + sum(a_r, r=1..7)) / 8; event time is the first departure round',
        'loss': '(8-r_first)/8, equally divided among departures in the first departure round',
        'goal': 'Game mean of non-EXIT share of pre-solve TALK responses eligible to exit; includes singleton solver',
        'all4_completion': 'Separate endpoint: all four agents remain after round 8; C=1 alone does not imply this',
        'legacy_source': f'cohort_{name}_20261104.json',
    }
    changed = {'C', 'departures', 'loss_by_tag', 'goal', 'goal_nonexit_k', 'goal_eligible_n'}
    for prior, current in zip(before['games'], data['games']):
        assert all(prior[k] == current[k] for k in prior if k not in changed)
    return data


def main():
    OUT.mkdir(exist_ok=True)
    payload = {}
    cohorts = [('public', ab.V33, old.PUBLIC),
               ('open', '~/squid5-runs/e52_v33/squid5_e52v33_codex_*4/*', old.OPEN),
               *[(arm, str(ab.ABLATION / f'squid5_e52v33ab_{arm}_docker_*4/*'),
                  {m: old.PUBLIC[m] for m in ab.MODELS}) for arm in ab.ARMS]]
    for name, pattern, models in cohorts:
        print('Refreshing', name, flush=True)
        data = refresh(name, pattern, models)
        payload[name] = data
        (ROOT / f'results/cohort_{name}_{STAMP}.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
        if name in ('public', 'open'):
            if name == 'public':
                table1.write(data)
            else:
                (ROOT / f'ko/tables/cohort_{name}_{STAMP}.tex').write_text(old.table(data))
            with patch.object(old, 'OUT', OUT):
                old.figures(data, name)
        print(name, 'C', data['summary']['C_mean'], flush=True)
    with patch.object(old, 'OUT', OUT):
        old.render_ablation(payload)
    (ROOT / f'ko/tables/ablation_prize_models_{STAMP}.tex').write_text(ab.table(payload))
    paired = {}
    for model in ab.MODELS:
        a = {g['seed']: g for g in payload['split600k']['games'] if g['model'] == model}
        b = {g['seed']: g for g in payload['flat150k']['games'] if g['model'] == model}
        paired[model] = {}
        for key in ['C', 'exited', 'dead', 'given_per_agent_round']:
            delta = np.array([b[s][key] - a[s][key] for s in old.SEEDS])
            rng = np.random.default_rng(20261104)
            paired[model][key] = dict(flat_minus_split=float(delta.mean()),
                ci95=fb.interval(delta[rng.integers(0, 10, (10000, 10))].mean(axis=1)))
    (ROOT / f'results/robustness_paired_{STAMP}.json').write_text(json.dumps(paired, indent=1))


if __name__ == '__main__':
    main()
