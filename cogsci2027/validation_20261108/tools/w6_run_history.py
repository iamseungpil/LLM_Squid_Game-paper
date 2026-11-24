"""Run-history sensitivity of the prize comparison (reviewer item "(a)-실행").

Marks every (arm, model, seed) whose game had an interrupted earlier attempt (a session_start
without a results line in the same run directory, or a deleted attempt recorded in the queue
manifest) or continued mid-game on another account, then recomputes the fixed-prize and
split-prize contrasts after dropping each affected model-seed pair from BOTH arms of the contrast.
Also reports same-batch contrasts (11-03 batch: split600k vs flat150k for Opus, Sol, Luna, Astra;
11-05/06 batch: Fable's flat5m, split600k, flat150k).
Sources: the raw run dirs in validation_data.ARMS, results/w5_manifest.json (Fable account switches,
Fable main 4105 deleted attempt). No model calls.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/validation_20261108/tools/w6_run_history.py
Writes: paper/cogsci2027/validation_20261108/results/w6_run_history.json
"""
import glob
import json
import lzma
import os
from pathlib import Path

import numpy as np

import validation_data as d

ROOT = Path(__file__).resolve().parents[1]
B = 10_000


def lines(path):
    p = Path(path)
    opener = lzma.open if p.suffix == '.xz' else open
    if not p.exists():
        p = p.with_suffix(p.suffix + '.xz')
        opener = lzma.open
    with opener(p, 'rt') as f:
        for line in f:
            yield json.loads(line)


def abandoned():
    out = set()
    for arm, (pattern, _, _) in d.ARMS.items():
        for run in glob.glob(os.path.expanduser(pattern)):
            model = next(m for m in d.MODELS if m.lower() in Path(run).parent.name.lower())
            done = {r['session_id'] for r in lines(Path(run) / 'results.jsonl') if r.get('event') == 'session'}
            for e in lines(Path(run) / 'events.jsonl'):
                if e['event'] == 'session_start' and e['session_id'] not in done and e['seed'] in d.SEEDS:
                    out.add((arm, model, e['seed']))
    return out


def affected():
    marks = {k: 'interrupted earlier attempt' for k in abandoned()}
    marks[('main', 'Fable', 4105)] = 'interrupted earlier attempt (deleted)'
    prov = json.loads((ROOT / 'results/w5_manifest.json').read_text())['provenance']
    for s in prov['fable_flat150k_account_switches']['continued_mid_game']:
        marks[('flat150k', 'Fable', s['seed'])] = f"continued on another account from round {s['round']}"
    return marks


def per_game(f):
    g, ar = f['games'], f['agent_rounds']
    r1 = ar[(ar['round'] == 1) & (ar.tier == 10) & ar.can_exit]
    out = {}
    for row in g.itertuples():
        x = r1[(r1.arm == row.arm) & (r1.model == row.model) & (r1.seed == row.seed)]
        out[row.arm, row.model, row.seed] = dict(C=row.C, exited=row.exited, dead=row.dead,
                                                  r1_n=len(x), r1_exit=int(x.exited.sum()))
    return out


def contrast(games, a, b, models, drop, rng):
    pairs = [(m, s) for m in models for s in d.SEEDS if (a, m, s) not in drop and (b, m, s) not in drop]
    diff = {k: np.array([games[b, m, s][k] - games[a, m, s][k] for m, s in pairs], float)
            for k in ['C', 'exited', 'dead']}
    seeds = sorted({s for _, s in pairs})
    idx = {s: [i for i, (_, t) in enumerate(pairs) if t == s] for s in seeds}
    res = dict(pairs=len(pairs), dropped=len(models) * len(d.SEEDS) - len(pairs))
    for k, v in diff.items():
        boots = [v[np.concatenate([idx[s] for s in rng.choice(seeds, len(seeds))])].mean() for _ in range(B)]
        res[k] = dict(mean=float(v.mean()), ci95=[float(x) for x in np.percentile(boots, [2.5, 97.5])])
    n_a = sum(games[a, m, s]['r1_n'] for m, s in pairs)
    res['r1_exit'] = dict(a=f"{sum(games[a, m, s]['r1_exit'] for m, s in pairs)}/{n_a}",
                          b=f"{sum(games[b, m, s]['r1_exit'] for m, s in pairs)}/{sum(games[b, m, s]['r1_n'] for m, s in pairs)}")
    return res


def main():
    f = d.load()
    games = per_game(f)
    marks = affected()
    rng = np.random.default_rng(20261108)
    nonfable = [m for m in d.MODELS if m != 'Fable']
    out = dict(affected={f'{a}|{m}|{s}': why for (a, m, s), why in sorted(marks.items())}, contrasts={})
    for name, a, b, models in [('flat150k-flat5m', 'flat5m', 'flat150k', d.MODELS),
                               ('split600k-main', 'main', 'split600k', d.MODELS),
                               ('flat150k-split600k', 'split600k', 'flat150k', d.MODELS)]:
        out['contrasts'][name] = dict(all=contrast(games, a, b, models, set(), rng),
                                      drop_affected=contrast(games, a, b, models, set(marks), rng),
                                      drop_fable=contrast(games, a, b, nonfable, set(), rng))
    out['same_batch'] = {
        '11-03 split600k->flat150k, Opus/Sol/Luna/Astra': contrast(games, 'split600k', 'flat150k', nonfable, set(marks), rng),
        '11-05/06 Fable flat5m->flat150k': contrast(games, 'flat5m', 'flat150k', ['Fable'], set(), rng),
        '11-05/06 Fable flat5m->flat150k, drop switched': contrast(games, 'flat5m', 'flat150k', ['Fable'], set(marks), rng),
        '11-05/06 Fable flat5m->split600k': contrast(games, 'flat5m', 'split600k', ['Fable'], set(marks), rng),
    }
    (ROOT / 'results/w6_run_history.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
