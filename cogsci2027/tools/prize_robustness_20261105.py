"""Compare v33 prize rules using complete, matched ten-seed cohorts only.

Sources: ~/squid5-runs/e52_v33ab (flat5m: five models; split600k: five
models, including the Fable top-up) and the hash-verified public and
flat150k cohorts frozen on 2026-11-05. Fable has no flat150k run.
The historical public runs are a descriptive reference: execution dates
and CLI versions are recorded separately from the matched game settings.
No model calls, manuscript prose writes, or incomplete-cohort estimates.
"""
import argparse
from functools import partial
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import yaml

import update_cohorts_20261104 as old

ROOT, ab, cx, fb = old.ROOT, old.ab, old.cx, old.fb
MODELS = old.PUBLIC
SEEDS = old.SEEDS
PATTERNS = {arm: str(Path.home() / 'squid5-runs/e52_v33ab' / f'squid5_e52v33ab_{arm}_docker_*4/*')
            for arm in ['flat5m', 'split600k']}


def ready():
    complete = True
    for arm, pattern in PATTERNS.items():
        cases = ab.raw_cases(pattern, SEEDS)
        counts = {m: sum(c['model'] == m for c in cases) for m in MODELS}
        print(arm, counts, flush=True)
        complete &= {(c['model'], c['seed']) for c in cases} == {(m, s) for m in MODELS for s in SEEDS}
    return complete


def frozen(name):
    data = json.loads((ROOT / f'results/cohort_{name}_20261105.json').read_text())
    for source in data['sources']:
        assert hashlib.sha256(fb.read_bytes(Path(source['path']))).hexdigest() == source['sha256_decompressed']
    return data


def estimate(games, metric):
    if metric == 'rho':
        return fb.revised_rho([gift for g in games for gift in g['gifts']])['rho']
    return ab.mean([g[metric] for g in games])


def audit_cases(arm, cases, baseline):
    """Check settings, puzzles, allocations and analysis inputs without cohort estimates."""
    amount = 5000000 if arm == 'flat5m' else 150000
    flat = arm != 'split600k'
    puzzles = {}
    for reference in baseline.values():
        for _, event in reference['events']:
            if event['event'] == 'round_start':
                key = reference['seed'], event['round']
                assert key not in puzzles or puzzles[key] == event['public'], key
                puzzles[key] = event['public']
    rows = []
    for case in cases:
        reference = baseline[case['model'], case['seed']]
        events = [e for _, e in case['events']]
        start = next(e for e in events if e['event'] == 'session_start')
        base_start = next(e for _, e in reference['events'] if e['event'] == 'session_start')
        assert start['seed'] == case['seed'] == case['result']['seed']
        assert start['session_id'] == case['result']['session_id']
        assert start['starts'] == base_start['starts']
        shared = lambda s: {k: v for k, v in s.items() if k not in ['end_flat', 'survivor_prize']}
        assert shared(start['settings']) == shared(base_start['settings'])
        assert start['settings']['survivor_prize'] == amount
        assert bool(start['settings'].get('end_flat')) == flat
        cfg = yaml.safe_load(fb.read_bytes(Path(case['source']) / 'config.yaml'))
        base_path = Path(reference['source']) / 'config.yaml'
        if not base_path.exists():
            base_path = base_path.with_suffix('.yaml.xz')
        base_cfg = yaml.safe_load(fb.read_bytes(base_path))
        assert shared(cfg['game']) == shared(base_cfg['game'])
        assert cfg['cells'] == base_cfg['cells'] and cfg['mode'] == base_cfg['mode']
        assert cfg['model']['model'] == base_cfg['model']['model']
        assert cfg['model']['think'] == base_cfg['model']['think'] == 'high'
        round_starts = [e for e in events if e['event'] == 'round_start']
        for event in round_starts:
            assert event['public'] == puzzles[case['seed'], event['round']], (arm, case['model'], case['seed'], event['round'])
        result = case['result']
        winners = result['final']['winner']
        assert set(winners) == {a for a, state in result['agents'].items() if state['status'] == 'in'}
        assert not winners or result['rounds_played'] == 8
        prize = (amount if flat else 4 * amount // len(winners)) if winners else 0
        assert result['final']['prize_each'] == prize
        gifts = [e for e in events if e['event'] == 'gift' and e.get('status') == 'done']
        participant_rounds = sum(len(e['taking_part']) for e in events if e['event'] == 'round_start')
        first_departure = min((e['round'] for e in events if e['event'] == 'round'
                              and any(s['status'] != 'in' for s in e['agents'].values())), default=8)
        rows.append(dict(model=case['model'], seed=case['seed'], session_id=result['session_id'],
                         C=first_departure / 8, given=sum(e['amount'] for e in gifts), n_give=len(gifts),
                         matched_puzzle_rounds=len(round_starts),
                         participant_rounds=participant_rounds, prize_each=prize,
                         exited=sum(s['status'] == 'exited' for s in result['agents'].values()),
                         dead=sum(s['status'] == 'dead' for s in result['agents'].values())))
    return rows


def contrast(left, right):
    """Right minus left, resampling matched game seeds; rho pools the sampled gifts."""
    out = {}
    for model in MODELS:
        a = {g['seed']: g for g in left['games'] if g['model'] == model}
        b = {g['seed']: g for g in right['games'] if g['model'] == model}
        if not a or not b:
            continue
        assert set(a) == set(b) == set(SEEDS)
        rng = np.random.default_rng(20261105)
        draws = rng.integers(0, len(SEEDS), (10000, len(SEEDS)))
        out[model] = {}
        for key in ['C', 'given_per_agent_round', 'exited', 'dead', 'rho']:
            av, bv = estimate(list(a.values()), key), estimate(list(b.values()), key)
            if av is None or bv is None:
                out[model][key] = None
                continue
            if key == 'rho':
                bootstrap = []
                for draw in draws:
                    x = estimate([a[SEEDS[i]] for i in draw], key)
                    y = estimate([b[SEEDS[i]] for i in draw], key)
                    if x is not None and y is not None:
                        bootstrap.append(y-x)
            else:
                delta = np.array([b[s][key] - a[s][key] for s in SEEDS])
                bootstrap = delta[draws].mean(axis=1)
            out[model][key] = dict(left=av, right=bv, difference=bv-av,
                                   ci95=fb.interval(bootstrap), defined_bootstrap_draws=len(bootstrap))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if not ready():
        raise SystemExit('Incomplete cohorts: no estimates or manuscript assets written.')
    if args.check_only:
        return
    arms = {'main': frozen('public'), 'flat150k': frozen('flat150k')}
    baseline = {(c['model'], c['seed']): c for c in ab.raw_cases(ab.V33, SEEDS)}
    assert set(baseline) == {(m, s) for m in MODELS for s in SEEDS}
    raw_audit = {}
    for arm, pattern in PATTERNS.items():
        print('Computing', arm, flush=True)
        with patch.object(cx, 'coexistence', partial(cx.coexistence, rmst=True)), \
                patch.object(fb, 'game_metrics', partial(fb.game_metrics, include_singleton=True)):
            arms[arm] = old.compute(arm, pattern, MODELS)
        for game in arms[arm]['games']:
            assert game['C'] == min((d['round'] for d in game['departures']), default=8) / 8
        arms[arm]['metric_definitions'] = arms['main']['metric_definitions'] | {
            'legacy_source': None,
            'cooperation': 'Mean per-game GIVE total / sum of round-start participant counts',
        }
    for arm in ['flat5m', 'split600k', 'flat150k']:
        pattern = str(Path.home() / f'squid5-runs/e52_v33ab/squid5_e52v33ab_{arm}_docker_*4/*')
        raw_audit[arm] = audit_cases(arm, ab.raw_cases(pattern, SEEDS), baseline)
        calculated = {(g['model'], g['seed']): g for g in arms[arm]['games']}
        for row in raw_audit[arm]:
            game = calculated[row['model'], row['seed']]
            for key in ['session_id', 'C', 'given', 'n_give', 'prize_each', 'exited', 'dead']:
                assert row[key] == game[key], (arm, row['model'], row['seed'], key)
            assert abs(row['given'] / row['participant_rounds'] - game['given_per_agent_round']) < 1e-9
    comparisons = {f'{right}_minus_{left}': contrast(arms[left], arms[right]) for left, right in [
        ('main', 'flat5m'), ('main', 'split600k'), ('flat5m', 'flat150k'), ('split600k', 'flat150k')]}
    for data in arms.values():
        for model, row in data['summary']['models'].items():
            row['cooperation_mean'] = estimate([g for g in data['games'] if g['model'] == model], 'given_per_agent_round')
    result = dict(seeds=SEEDS, models=MODELS, arms=arms, comparisons=comparisons,
                  raw_audit=raw_audit,
                  missing_cells=[dict(arm='flat150k', model='Fable', reason='Not part of the requested top-up')],
                  uncertainty='10,000 paired seed bootstrap draws; rho pooled by GIVE amount in each draw')
    path = ROOT / 'results/prize_robustness_20261105.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print('Wrote', path)


if __name__ == '__main__':
    main()
