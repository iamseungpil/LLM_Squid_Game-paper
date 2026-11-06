"""Combine allocation and participation evidence for Appendix 0, e52_v33 only.

Source: fixed 25-game raw_case_index.json and its original v33 event/results
files, verified by appendix0_process_20261030.py. Terminal holdings retain four
original seats: finishers' pre-prize tokens; EXIT and shutdown are zero.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

from inequality import distribution

ROOT = Path(__file__).resolve().parents[1]
ORDER = ['Fable', 'Astra', 'Sol', 'Opus', 'Luna']


def analyze():
    source = ROOT / 'results/raw_case_index.json'
    process = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == process['source_sha256']
    for path, digest in process['raw_sources'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    cases = json.loads(source.read_text())
    assert len(cases) == 25
    round_n = {(c['result']['session_id'], e['round']): len(e['taking_part'])
               for c in cases for _, e in c['events'] if e['event'] == 'round_start'}
    eligible = [r for r in process['responses'] if round_n[r['session'], r['round']] > 1]
    give_behavior = dict(
        definition='Response-start margin; rounds starting with at least two participants; one or more completed transfers per response.',
        count=[sum(r['band'] == b and r['gave'] for r in eligible) for b in range(4)],
        denominator=[sum(r['band'] == b for r in eligible) for b in range(4)],
        excluded_singleton_responses=len(process['responses']) - len(eligible))
    original = json.loads((ROOT / 'results/section32_behavior_20261029.json').read_text())['behavior']
    assert give_behavior['count'] == original['give_count']
    assert give_behavior['denominator'] == original['give_calls']
    assert len(eligible) == 2898 and sum(give_behavior['count']) == 120
    models = {}
    for model in ORDER:
        subset = [c for c in cases if c['model'] == model]
        assert sorted(c['seed'] for c in subset) == list(range(4101, 4106))
        timing = {phase: dict(tokens=0, count=0, return_tokens=0)
                  for phase in ['prep', 'rescue']}
        states, games = Counter(), []
        for case in subset:
            prior = set()
            for _, event in case['events']:
                if event['event'] != 'gift' or event.get('status') != 'done':
                    continue
                row = timing[event['phase']]
                row['tokens'] += event['amount']
                row['count'] += 1
                if (event['dst'], event['src']) in prior:
                    row['return_tokens'] += event['amount']
                prior.add((event['src'], event['dst']))
            agents = case['result']['agents']
            states.update(v['status'] for v in agents.values())
            tokens = [v['final'] if v['status'] == 'in' else 0 for v in agents.values()]
            assert len(tokens) == 4
            games.append(dict(seed=case['seed'], tokens=tokens,
                              finishers=sum(v['status'] == 'in' for v in agents.values()),
                              **distribution(tokens)))
        means, defined = {}, {}
        for key in ['mu', 'G', 'S', 'finishers']:
            values = [g[key] for g in games if g[key] is not None]
            means[key], defined[key] = mean(values), len(values)
        gifts = [g for g in process['gifts'] if g['model'] == model]
        numerator = sum(g['amount'] * g['giver_after'] for g in gifts)
        denominator = sum(g['amount'] * g['receiver_after'] for g in gifts)
        models[model] = dict(timing=timing, states=dict(states), games=games,
                             means=means, n_defined=defined,
                             rho=dict(value=numerator / denominator,
                                      numerator=numerator, denominator=denominator,
                                      defined_games=len({g['session'] for g in gifts}),
                                      definition='Pooled transfer-weighted giver-after / receiver-after margin across five games; not mean of game ratios.'))
    previous = json.loads((ROOT / 'results/terminal_distribution_20261029.json').read_text())['models']
    for model, row in models.items():
        reference = next(v for k, v in previous.items() if model in k)
        for key, value in row['means'].items():
            assert abs(value - reference['means'][key]) < 1e-8
        assert row['n_defined'] == reference['n_defined']
    assert sum(v['tokens'] for m in models.values() for v in m['timing'].values()) == 383276
    assert sum(v['count'] for m in models.values() for v in m['timing'].values()) == 130
    out = dict(source=str(source.relative_to(ROOT)), source_sha256=process['source_sha256'],
               definition=__doc__, models=models, give_behavior=give_behavior,
               transfer_median=median(g['amount'] for g in process['gifts']))
    (ROOT / 'results/appendix0_integrated_20261030.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({m: {k: v for k, v in row.items() if k != 'games'}
                      for m, row in models.items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    analyze()
