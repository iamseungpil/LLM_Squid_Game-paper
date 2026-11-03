"""C1 with the model held fixed: do all-four-completion games differ from the rest *within* a model?

Reviewer P0: the pooled C1 contrast (all-four games give more, solve more, keep a lower rho) is confounded with model
identity and accuracy. This script adds, for each game-level metric, (i) the pooled contrast the manuscript reports,
(ii) the within-model contrast per model, (iii) a model fixed-effects estimate (OLS, metric ~ all4 + model [+ seed]),
(iv) a within-model permutation p (labels shuffled inside each model; exact when small) and a model-stratified
bootstrap interval, and (v) a conditional logit (all4 ~ metric, strata = model) as the reverse-direction check.
Accuracy is also read against task difficulty: each solve minus the mean correctness of other models on the same
(seed, round) puzzle, whose puzzle and example order are fixed by seed and round (squid5/core/puzzle.py public_round).

Data (paper/CLAUDE.md scope): 5.2 arena v33 public runs only,
~/squid5-runs/e52_v33/squid5_e52v33_public_<model>4/*/{results,events}.jsonl[.xz]. Default seeds 4101-4105 are the
manuscript cohort (25 games); --seeds 4101-4110 adds the 2026-10-27 top-up. Only finished sessions are read, so a run
still writing is safe. No model calls. Writes results/c1_within_model_<seeds>.json.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/c1_within_model.py [--seeds 4101-4110] [--runs GLOB]
"""
import argparse
import glob
import itertools
import os
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import feedback_20261028 as fb

ROOT = fb.ROOT
RUNS = '~/squid5-runs/e52_v33/squid5_e52v33_public_*4/*'
METRICS = ('given_per_agent_round', 'accuracy', 'accuracy_vs_task', 'accuracy_vs_task_n', 'rho')
EXACT_MAX = 200_000
DRAWS = 20_000
BOOT = 10_000
RNG_SEED = 20261103


def read(run_dir, name):
    for path in (run_dir / name, run_dir / (name + '.xz')):
        if path.exists():
            return fb.records(fb.read_bytes(path))
    return []


def load(pattern, seeds):
    """One row per finished game: the manuscript's ledger metrics plus each solve with its solver's margin."""
    games = []
    for run_dir in sorted(Path(p) for p in glob.glob(os.path.expanduser(pattern))):
        model = next((m for m in fb.MODELS if m.lower() in run_dir.parent.name.lower()), None)
        results = [r for r in read(run_dir, 'results.jsonl') if r.get('event') == 'session' and r['seed'] in seeds]
        if model is None or not results:
            continue
        by_sid = defaultdict(list)
        for e in read(run_dir, 'events.jsonl'):
            by_sid[e.get('session_id')].append(e)
        for result in results:
            events = by_sid[result['session_id']]
            game = fb.game_metrics(events, result, model)
            agent_rounds, solves = 0, []
            for r in range(1, game['rounds_played'] + 1):
                ev = [e for e in events if e.get('round') == r]
                rs = next(e for e in ev if e['event'] == 'round_start')
                res = next(e for e in ev if e['event'] == 'results')
                n = len(rs['taking_part'])
                agent_rounds += n
                if res['tried']:
                    a, = res['tried']
                    solves.append(dict(round=r, n=n, correct=int(bool(res['solved'])),
                                       margin=rs['balances'][a] / (24000 / n)))
            game.update(run_dir=str(run_dir), agent_rounds=agent_rounds, solves=solves,
                        given_per_agent_round=game['given'] / agent_rounds,
                        accuracy=sum(s['correct'] for s in solves) / len(solves) if solves else None)
            games.append(game)
    keys = [(g['model'], g['seed']) for g in games]
    assert len(keys) == len(set(keys)), 'a (model, seed) game appears twice; pass a narrower --runs'
    add_task_reference(games)
    return games


def add_task_reference(games):
    """Accuracy against the same puzzle: correct minus other models' mean on that (seed, round) when their solver had
    margin >= 2 (the manuscript's reference, fig3_completion_20261028.individual_outcomes). The _n variant also matches
    the number taking part, since one agent fewer shows fewer examples of the same puzzle."""
    pool = [(g['model'], g['seed'], s) for g in games for s in g['solves'] if s['margin'] >= 2]
    for g in games:
        for key, match_n in (('accuracy_vs_task', False), ('accuracy_vs_task_n', True)):
            diffs = []
            for s in g['solves']:
                ref = [t['correct'] for m, seed, t in pool if m != g['model'] and seed == g['seed']
                       and t['round'] == s['round'] and (not match_n or t['n'] == s['n'])]
                if ref:
                    diffs.append(s['correct'] - sum(ref) / len(ref))
            g[key] = sum(diffs) / len(diffs) if diffs else None
            g[key + '_solves'] = len(diffs)


def fe_beta(y, d, groups, extra=None):
    """OLS coefficient of the 0/1 indicator d with one dummy per group (and per extra factor level). Only groups in
    which d varies carry information about it; None if no group varies."""
    y, d = np.asarray(y, float), np.asarray(d, float)
    if not any(len(set(d[groups == k])) > 1 for k in set(groups)):
        return None
    cols = [d] + [(groups == k).astype(float) for k in sorted(set(groups))]
    if extra is not None:
        cols += [(extra == k).astype(float) for k in sorted(set(extra))[1:]]
    beta, *_ = np.linalg.lstsq(np.column_stack(cols), y, rcond=None)
    return float(beta[0])


def within_permutation(y, d, groups, rng):
    """Two-sided p for the FE coefficient with all4 labels permuted inside each model (counts per model kept)."""
    observed = fe_beta(y, d, groups)
    blocks = [np.flatnonzero(groups == k) for k in sorted(set(groups))]
    sizes = [math.comb(len(b), int(d[b].sum())) for b in blocks]
    exact = math.prod(sizes) <= EXACT_MAX

    def labels(choice):
        out = np.zeros(len(d))
        for b, pick in zip(blocks, choice):
            out[b[list(pick)]] = 1
        return out

    if exact:
        draws = (labels(c) for c in itertools.product(*[itertools.combinations(range(len(b)), int(d[b].sum()))
                                                         for b in blocks]))
    else:
        draws = (labels([rng.choice(len(b), int(d[b].sum()), replace=False) for b in blocks]) for _ in range(DRAWS))
    stats = np.array([fe_beta(y, p, groups) for p in draws])
    return dict(p=float(np.mean(np.abs(stats) >= abs(observed) - 1e-12)), exact=exact, n_labelings=len(stats))


def stratified_bootstrap(y, d, groups, rng):
    """Percentile 95% interval of the FE coefficient, resampling games with replacement inside each model."""
    blocks = [np.flatnonzero(groups == k) for k in sorted(set(groups))]
    stats = []
    for _ in range(BOOT):
        idx = np.concatenate([rng.choice(b, len(b)) for b in blocks])
        b = fe_beta(y[idx], d[idx], groups[idx])
        if b is not None:
            stats.append(b)
    return [float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))], len(stats)


def conditional_logit(y, d, groups):
    """all4 ~ standardized metric, strata = model: models without both outcomes drop out by construction."""
    from statsmodels.discrete.conditional_models import ConditionalLogit
    keep = np.array([len(set(d[groups == k])) > 1 for k in groups])
    if keep.sum() < 4:
        return dict(error='fewer than four games in models with both outcomes')
    z = (y - y[keep].mean()) / y[keep].std()
    try:
        fit = ConditionalLogit(d[keep], z[keep, None], groups=groups[keep]).fit(disp=False)
        lo, hi = fit.conf_int()[0]
        return dict(coef_per_sd=float(fit.params[0]), ci95=[float(lo), float(hi)], p=float(fit.pvalues[0]),
                    n_games=int(keep.sum()), n_models=len(set(groups[keep])))
    except Exception as exc:  # separation is likely at this sample size; record it rather than hide it
        return dict(error=f'{type(exc).__name__}: {exc}')


def analyse(games, metric, rng):
    rows = [g for g in games if g[metric] is not None]
    y = np.array([g[metric] for g in rows], float)
    d = np.array([int(g['all4_completion']) for g in rows])
    groups = np.array([g['model'] for g in rows])
    seeds = np.array([g['seed'] for g in rows])
    per_model = {}
    for m in fb.MODELS:
        a, b = y[(groups == m) & (d == 1)], y[(groups == m) & (d == 0)]
        per_model[m] = dict(n_all4=len(a), n_rest=len(b), all4=float(a.mean()) if len(a) else None,
                            rest=float(b.mean()) if len(b) else None,
                            diff=float(a.mean() - b.mean()) if len(a) and len(b) else None)
    out = dict(n_games=len(rows), pooled=dict(all4=float(y[d == 1].mean()), rest=float(y[d == 0].mean()),
                                               n_all4=int(d.sum()), n_rest=int((1 - d).sum())),
               per_model=per_model,
               informative_models=[m for m, v in per_model.items() if v['diff'] is not None],
               models_same_sign_as_pooled=None, fe_model=fe_beta(y, d, groups),
               fe_model_seed=fe_beta(y, d, groups, extra=seeds))
    pooled_diff = out['pooled']['all4'] - out['pooled']['rest']
    diffs = [v['diff'] for v in per_model.values() if v['diff'] is not None]
    out['models_same_sign_as_pooled'] = f"{sum(np.sign(x) == np.sign(pooled_diff) for x in diffs)}/{len(diffs)}"
    if out['fe_model'] is not None:
        out['permutation'] = within_permutation(y, d, groups, rng)
        out['bootstrap_ci95'], out['bootstrap_draws'] = stratified_bootstrap(y, d, groups, rng)
        out['conditional_logit'] = conditional_logit(y, d, groups)
    return out


def seed_range(text):
    lo, _, hi = text.partition('-')
    return list(range(int(lo), int(hi or lo) + 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--seeds', default='4101-4105', help='inclusive range; 4101-4105 is the manuscript cohort')
    ap.add_argument('--runs', default=RUNS, help='glob of run directories (default: v33 public runs)')
    ap.add_argument('--out', type=Path, default=None)
    args = ap.parse_args()
    seeds = seed_range(args.seeds)
    games = load(args.runs, seeds)
    rng = np.random.default_rng(RNG_SEED)
    payload = dict(seeds=args.seeds, runs=args.runs, n_games=len(games),
                   games_per_model={m: sum(g['model'] == m for g in games) for m in fb.MODELS},
                   all4_per_model={m: sum(g['all4_completion'] for g in games if g['model'] == m) for m in fb.MODELS},
                   metrics={m: analyse(games, m, rng) for m in METRICS},
                   games=[{k: g[k] for k in ('model', 'seed', 'session_id', 'all4_completion', 'finishers',
                                             *METRICS, 'accuracy_vs_task_solves', 'run_dir')} for g in games])
    out = args.out or ROOT / f'results/c1_within_model_{args.seeds}.json'
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    print(f"{len(games)} games {payload['games_per_model']} all4 {payload['all4_per_model']}")
    for name, r in payload['metrics'].items():
        p = r['pooled']
        line = (f"{name:24s} pooled {p['all4']:.3f} vs {p['rest']:.3f} (n {p['n_all4']}/{p['n_rest']})"
                f" | same sign {r['models_same_sign_as_pooled']}")
        if r['fe_model'] is not None:
            lo, hi = r['bootstrap_ci95']
            line += (f" | FE {r['fe_model']:+.3f} [{lo:+.3f}, {hi:+.3f}] perm p {r['permutation']['p']:.3f}"
                     f" | FE+seed {r['fe_model_seed']:+.3f}")
        print(line)
    print('wrote', out)


if __name__ == '__main__':
    main()
