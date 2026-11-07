"""Audit common starts and compare existing pooled rho values without new games.

Source: the frozen public e52_v33 cohort, five models x seeds 4101--4110.
Raw session starts are checked against the cohort's decompressed source hashes.
Each bootstrap draw resamples the same ten seed indices for every model. All
actual GIVE events and their original amount weights are retained, including
negative giver margins. A no-GIVE game contributes zero to both sums; a draw
with zero denominator is undefined. No state matching or counterfactual policy.
"""
import hashlib
import itertools
import json
import lzma
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/cohort_public_20261105.json'
OUT = ROOT / 'results/rho_paired_models_20261107.json'
DRAWS, RNG_SEED = 20000, 20261107


def main():
    data = json.loads(SOURCE.read_text())
    models, seeds = list(data['models']), data['seeds']
    games = {g['session_id']: g for g in data['games']}
    assert len(games) == 50 and seeds == list(range(4101, 4111))
    starts, sources = {}, []
    for source in data['sources']:
        if 'events.jsonl' not in source['path']:
            continue
        path = Path(source['path'])
        assert 'e52_v33' in path.parts
        raw = path.read_bytes()
        if path.suffix == '.xz':
            raw = lzma.decompress(raw)
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == source['sha256_decompressed']
        sources.append(dict(path=str(path), sha256=digest))
        for line in raw.splitlines():
            event = json.loads(line)
            sid = event.get('session_id')
            if event['event'] == 'session_start' and sid in games:
                assert sid not in starts
                starts[sid] = event['starts']
    assert len(starts) == 50
    common_starts = {}
    for seed in seeds:
        selected = [g for g in games.values() if g['seed'] == seed]
        assert len(selected) == 5
        reference = starts[selected[0]['session_id']]
        assert sorted(reference.values()) == [10000, 20000, 40000, 60000]
        assert all(starts[g['session_id']] == reference for g in selected)
        common_starts[seed] = reference

    totals, estimates, nodonation = {}, {}, {}
    for model in models:
        selected = sorted((g for g in games.values() if g['model'] == model), key=lambda g: g['seed'])
        assert [g['seed'] for g in selected] == seeds
        values = np.array([[sum(t['amount'] * t[key] for t in g['gifts'])
                            for key in ['giver_margin', 'taker_margin']] for g in selected])
        numerator, denominator = values.sum(axis=0)
        estimates[model] = float(numerator / denominator)
        assert np.isclose(estimates[model], data['summary']['models'][model]['rho'])
        totals[model] = values
        nodonation[model] = sum(not g['gifts'] for g in selected)
    indices = np.random.default_rng(RNG_SEED).integers(0, len(seeds), (DRAWS, len(seeds)))
    samples = {}
    for model, values in totals.items():
        drawn = values[indices].sum(axis=1)
        samples[model] = np.divide(drawn[:, 0], drawn[:, 1],
                                   out=np.full(DRAWS, np.nan), where=drawn[:, 1] != 0)
    pairs = list(itertools.combinations(models, 2))
    alpha = .05 / len(pairs)
    results = []
    for a, b in pairs:
        difference = samples[a] - samples[b]
        defined = difference[np.isfinite(difference)]
        results.append(dict(a=a, b=b, difference=estimates[a]-estimates[b],
                            ci95_percentile=np.quantile(defined, [.025, .975]).tolist(),
                            ci995_bonferroni_percentile=np.quantile(defined, [alpha/2, 1-alpha/2]).tolist(),
                            defined_draws=int(len(defined))))
    report = dict(source=str(SOURCE.relative_to(ROOT)),
                  source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  scope='public v33, five models x ten paired seeds; descriptive post-hoc comparison',
                  source_checks=sources, common_starts_verified=common_starts,
                  rho_definition_unchanged=True, estimates=estimates, no_give_games=nodonation,
                  draws=DRAWS, rng_seed=RNG_SEED, n_comparisons=len(pairs),
                  interval_note='Ten 99.5% marginal percentile bootstrap intervals use Bonferroni alpha=.05/10; bootstrap coverage is approximate.',
                  pairs=results)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Verified 50 session starts and existing rho values; wrote', OUT)
    for row in results:
        print(row['a'], row['b'], round(row['difference'], 3),
              [round(v, 3) for v in row['ci995_bonferroni_percentile']])


if __name__ == '__main__':
    main()
