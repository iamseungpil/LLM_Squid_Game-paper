"""Bounded feedback items 1--10 analysis; no model calls or manuscript writes.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/feedback_20261028.py
Only writes results/feedback_20261028.json and ko/figures/feedback_20261028*.
"""
import ast
import hashlib
import json
import lzma
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
OLD = ROOT / 'tools/rewrite_20261025'
SEEDS = list(range(4101, 4106))
MODELS = {'Fable': 'Fable 5.1', 'Astra': 'GPT-6 Astra', 'Sol': 'GPT-6 Sol',
          'Opus': 'Opus 5.5', 'Luna': 'GPT-6 Luna'}
BOOT = 10000
RNG_SEED = 20261028


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    return lzma.decompress(path.read_bytes()) if path.suffix == '.xz' else path.read_bytes()


def records(data):
    return [json.loads(line) for line in data.splitlines() if line.strip()]


from inequality import distribution


def revised_rho(gifts):
    w = sum(g['amount'] for g in gifts)
    giver = sum(g['amount'] * g['giver_margin'] for g in gifts)
    taker = sum(g['amount'] * g['taker_margin'] for g in gifts)
    return {'rho': giver / taker if w and taker != 0 else None,
            'undefined_reason': 'no_GIVE' if not w else ('zero_receiver_denominator' if taker == 0 else None),
            'weighted_giver_margin': giver / w if w else None,
            'weighted_taker_margin': taker / w if w else None}


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    center = (p + z*z / (2*n)) / (1 + z*z/n)
    half = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return [float(max(0, center-half)), float(min(1, center+half))]


def interval(values):
    values = [v for v in values if v is not None and np.isfinite(v)]
    return np.quantile(values, [.025, .975]).tolist() if values else [None, None]


def mean(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def load_sources(historic):
    sources, by_run = [], defaultdict(dict)
    for s in historic['sources']:
        original = Path(s['path'])
        local = OLD / 'raw' / original.parent.name / original.name
        snapshot = Path.home() / 'wt/squid5-e52/web/data/runs/e52_v33' / Path(*original.parts[-3:])
        if not snapshot.exists():
            snapshot = snapshot.with_suffix(snapshot.suffix + '.xz')
        path = local if local.exists() else original if original.exists() else snapshot
        data = read_bytes(path)
        row = {'path': str(path), 'sha256': sha(data), 'historic_sha256': s['sha256'],
               'matches_historic_hash': sha(data) == s['sha256'], 'bytes': len(data)}
        if snapshot.exists():
            old = read_bytes(snapshot)
            assert sha(old) == s['sha256'], str(snapshot)
            row.update(snapshot_path=str(snapshot), snapshot_sha256=sha(old),
                       current_has_exact_historic_prefix=data.startswith(old), appended_bytes=len(data)-len(old))
            assert data.startswith(old), str(path)
            old_rows, new_rows = records(old), records(data)
            selected_ids = {r['session_id'] for r in old_rows if r.get('seed') in SEEDS}
            # Event starts supply the cohort IDs; result records supply them directly.
            selected = lambda rs: [r for r in rs if r.get('session_id') in selected_ids]
            assert selected(old_rows) == selected(new_rows), 'Target cohort changed after snapshot'
            row['target_cohort_unchanged'] = True
            row['target_records_sha256'] = sha(json.dumps(selected(new_rows), sort_keys=True).encode())
        rows = records(data)
        row['record_count'] = len(rows)
        sources.append(row)
        by_run[original.parent.name][original.name] = rows
    return sources, by_run


def game_metrics(events, result, model):
    starts = [e for e in events if e['event'] == 'session_start']
    assert len(starts) == 1
    start = starts[0]
    assert start['settings']['rounds'] == 8
    assert start['starts'] == result['starts']
    rounds = defaultdict(list)
    for e in events:
        if 'round' in e:
            rounds[e['round']].append(e)
    gifts, eligible, bonuses = [], [], {}
    for r, rows in sorted(rounds.items()):
        rs = next(e for e in rows if e['event'] == 'round_start')
        rr = next(e for e in rows if e['event'] == 'results')
        n = len(rs['taking_part'])
        charge = 24000 / n
        wrong = bool(rr['tried']) and not rr['solved']
        vote = next(e for e in rows if e['event'] == 'vote')
        solver = rr['tried'][0] if rr['tried'] else vote['rep']
        balances = {(e.get('phase'), e.get('tick')): e['balances'] for e in rows
                    if e['event'] == 'call_start' and e['kind'] == 'talk'}
        for e in rows:
            if e['event'] == 'call' and e['kind'] == 'talk' and e.get('phase') == 'prep' and e['agent'] != solver and n > 1:
                b = balances.get(('prep', e.get('tick')), {}).get(e['agent'])
                if b is not None:
                    p = e.get('parsed') or {}
                    if isinstance(p, str):
                        p = ast.literal_eval(p)
                    eligible.append(bool(p.get('exit')))
            if e['event'] == 'gift' and e['status'] == 'done':
                due = charge if e.get('phase') == 'rescue' and wrong else 0
                gifts.append({'round': r, 'phase': e.get('phase'), 'src': e['src'], 'dst': e['dst'],
                              'amount': e['amount'], 'charge': charge, 'due': due,
                              'giver_margin': (e['balances'][e['src']] - due) / charge,
                              'taker_margin': (e['balances'][e['dst']] - due) / charge})
            if e['event'] == 'round':
                for a, v in e['agents'].items():
                    if 'exit_bonus' in v:
                        assert a not in bonuses and v['exit_bonus'] == 20000
                        bonuses[a] = v['exit_bonus']
    agents = result['agents']
    assert len(agents) == 4 and {a['status'] for a in agents.values()} <= {'in', 'exited', 'dead'}
    winners = result['final']['winner']
    assert set(winners) == {a for a, v in agents.items() if v['status'] == 'in'}
    assert result['rounds_played'] == max(rounds)
    assert set(bonuses) == {a for a, v in agents.items() if v['status'] == 'exited'}
    seats = {}
    for a, v in agents.items():
        pre = 0 if v['status'] == 'dead' else v['final']
        assert v['status'] != 'dead' or v['final'] == 0
        seats[a] = {'status_raw': v['status'], 'status': 'finished' if a in winners else v['status'],
                    'pre_prize': pre, 'exit_bonus_included': bonuses.get(a, 0),
                    'settled': pre + (result['final']['prize_each'] if a in winners else 0)}
    total = sum(g['amount'] for g in gifts)
    # The ledger transfer total is independent of the gift event aggregation.
    assert total == sum(t['amount'] for t in result['transfers'])
    return {'model': model, 'seed': result['seed'], 'session_id': result['session_id'],
            'raw_completed_present': 'completed' in result, 'raw_completed': result.get('completed'),
            'rounds_played': result['rounds_played'], 'clear': result['rounds_played'] == 8 and len(winners) >= 1,
            'all4_completion': result['rounds_played'] == 8 and len(winners) == 4,
            'finishers': len(winners), 'exited': sum(v['status'] == 'exited' for v in agents.values()),
            'dead': sum(v['status'] == 'dead' for v in agents.values()),
            'survival': sum(v['status'] != 'dead' for v in agents.values()), 'seats': seats,
            'pre_prize': distribution([v['pre_prize'] for v in seats.values()]),
            'historic_settled': distribution([v['settled'] for v in seats.values()]),
            'given': total, 'given_per_start': total / sum(result['starts'].values()), 'n_give': len(gifts),
            'goal_nonexit_k': len(eligible) - sum(eligible), 'goal_eligible_n': len(eligible),
            'goal': (len(eligible)-sum(eligible))/len(eligible) if eligible else None,
            **revised_rho(gifts), 'gifts': gifts}


def associations(games):
    """Pooled Pearson (binary y = point-biserial); resample whole paired seed blocks."""
    rng = np.random.default_rng(RNG_SEED)
    draws = rng.integers(0, 5, (BOOT, 5))
    out = {}
    for x in ('rho', 'goal', 'given'):
        for y in ('clear', 'finishers'):
            def corr(rows):
                pairs = [(g[x], g[y]) for g in rows if g[x] is not None]
                a, b = np.asarray(pairs, dtype=float).T
                if np.ptp(a) == 0 or np.ptp(b) == 0:
                    return None
                return float(np.corrcoef(a, b)[0, 1])
            blocks = [[g for g in games if g['seed'] == s] for s in SEEDS]
            boots = [corr([g for i in draw for g in blocks[i]]) for draw in draws]
            out[f'{x}__{y}'] = {'pearson_r': corr(games), 'ci95_paired_seed_bootstrap': interval(boots),
                                'n_games': sum(g[x] is not None for g in games), 'n_seed_clusters': 5,
                                'valid_bootstrap_replicates': sum(b is not None for b in boots),
                                'undefined_bootstrap_replicates': sum(b is None for b in boots)}
    return out


def summarize(games):
    out = {}
    rng = np.random.default_rng(RNG_SEED)
    for model in MODELS:
        gs = [g for g in games if g['model'] == model]
        k = sum(g['clear'] for g in gs)
        all4 = sum(g['all4_completion'] for g in gs)
        item = {'model_id': list(MODELS).index(model)+1, 'n_games': 5, 'clear_k': k, 'clear_rate': k/5,
                'clear_wilson95': wilson(k, 5), 'all4_k': all4, 'all4_rate': all4/5,
                'all4_wilson95': wilson(all4, 5),
                **{key: sum(g[key] for g in gs) for key in ('finishers', 'exited', 'dead', 'survival', 'given', 'n_give')},
                'pre_prize_mean': {k: mean([g['pre_prize'][k] for g in gs]) for k in ('mu', 'G', 'S')},
                'pre_prize_G_n_defined': sum(g['pre_prize']['G'] is not None for g in gs),
                'historic_settled_S_mean': mean([g['historic_settled']['S'] for g in gs]),
                'goal_pooled': sum(g['goal_nonexit_k'] for g in gs)/sum(g['goal_eligible_n'] for g in gs),
                **revised_rho([v for g in gs for v in g['gifts']]), 'plot_means': {}}
        for x in ('rho', 'goal', 'given'):
            pairs = [g for g in gs if g[x] is not None]
            boot = [[pairs[i] for i in draw] for draw in rng.integers(0, len(pairs), (BOOT, len(pairs)))]
            item['plot_means'][x] = {'n': len(pairs), 'x': mean([g[x] for g in pairs]),
                'x_ci95': interval([mean([g[x] for g in b]) for b in boot]),
                'clear': mean([g['clear'] for g in pairs]),
                'clear_ci95': wilson(sum(g['clear'] for g in pairs), len(pairs)),
                'finishers': mean([g['finishers'] for g in pairs]),
                'finishers_ci95': interval([mean([g['finishers'] for g in b]) for b in boot])}
        out[model] = item
    return out


def plot(payload):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(10.2, 6.1), layout='constrained')
    grid = fig.add_gridspec(2, 4, width_ratios=[.16, 1, 1, 1])
    colors = ['#6A3D9A', '#E7298A', '#C48F00', '#1B9E77', '#A6761D']
    markers = ['o', '^', 'D', 's', 'v']
    for row, y in enumerate(('clear', 'finishers')):
        missing = fig.add_subplot(grid[row, 0])
        missing.set(xticks=[], yticks=[], xlim=(.5, 5.5), ylim=(-.18, 1.18) if row == 0 else (-.4, 4.4))
        missing.set_title('No\nGIVE', fontsize=9)
        for col, x in enumerate(('rho', 'goal', 'given')):
            ax = fig.add_subplot(grid[row, col+1])
            scale = 100 if x == 'goal' else .001 if x == 'given' else 1
            for mi, model in enumerate(MODELS):
                gs = [g for g in payload['games'] if g['model'] == model]
                for g in gs:
                    # Jitter is ONLY a display offset; every estimator uses unjittered outcomes.
                    jitter = ((g['seed']-4103)*.012 + (mi-2)*.014) * (1 if row == 0 else 2)
                    target = missing if g[x] is None else ax
                    target.scatter((mi+1) if g[x] is None else g[x]*scale, g[y]+jitter,
                                   s=22, marker=markers[mi], color=colors[mi], alpha=.5, linewidths=0)
                s = payload['models'][model]['plot_means'][x]
                ax.errorbar(s['x']*scale, s[y],
                            xerr=np.maximum(0, np.array([[s['x']-s['x_ci95'][0]], [s['x_ci95'][1]-s['x']]]))*scale,
                            yerr=np.maximum(0, np.array([[s[y]-s[y+'_ci95'][0]], [s[y+'_ci95'][1]-s[y]]])),
                            fmt=markers[mi], color=colors[mi], ms=7, mec='white', mew=.7,
                            elinewidth=.8, capsize=2, label=model if row == 0 and col == 0 else None)
            a = payload['associations'][f'{x}__{y}']
            lo, hi = a['ci95_paired_seed_bootstrap']
            ax.set_title(f"({chr(97+row*3+col)})  Pearson r = {a['pearson_r']:.2f}\n95% CI [{lo:.2f}, {hi:.2f}]", fontsize=10)
            ax.set_xlabel({"rho": "Post-GIVE margin ratio\n(giver / taker)", "goal": "Non-EXIT responses (%)", "given": "Tokens given (thousands)"}[x], fontsize=10)
            if col == 0:
                ax.set_ylabel("Game clear (0 / 1)" if row == 0 else "Finishers (0–4)", fontsize=10)
            ax.set(ylim=(-.18, 1.18) if row == 0 else (-.4, 4.4), yticks=[0, 1] if row == 0 else [0, 1, 2, 3, 4])
            ax.grid(alpha=.15)
            ax.spines[['top', 'right']].set_visible(False)
    handles, labels = fig.axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc='outside lower center', ncol=5, frameon=False)
    prefix = ROOT / 'ko/figures/feedback_20261028_behavior'
    for ext in ('pdf', 'png'):
        fig.savefig(prefix.with_suffix('.'+ext), dpi=220)
    plt.close(fig)


def main():
    historic = json.loads((ROOT / 'results/arena_v33.json').read_text())
    old_games = {(g['m'], g['seed']): g for g in json.loads((OLD / 'an3/game_level.json').read_text())['games']}
    sources, runs = load_sources(historic)
    games = []
    for run, raw in runs.items():
        model = next(m for m in MODELS if m.lower() in run.lower())
        by_sid = defaultdict(list)
        for e in raw['events.jsonl']:
            by_sid[e['session_id']].append(e)
        for result in raw['results.jsonl']:
            if result.get('event') == 'session' and result['seed'] in SEEDS:
                games.append(game_metrics(by_sid[result['session_id']], result, model))
    games.sort(key=lambda g: (list(MODELS).index(g['model']), g['seed']))
    assert len(games) == 25 and len({(g['model'], g['seed']) for g in games}) == 25
    for model, full in MODELS.items():
        gs = [g for g in games if g['model'] == model]
        assert [g['seed'] for g in gs] == SEEDS
        h = historic['models'][full]
        assert sum(g['given'] for g in gs) == h['given']
        assert sum(g['n_give'] for g in gs) == h['gifts']
        for g in gs:
            old = old_games[model, g['seed']]
            hg = next(x for x in h['per_game'] if x['seed'] == g['seed'])
            assert abs(g['historic_settled']['S']-hg['sen']) < 1e-8
            assert [v['settled'] for v in g['seats'].values()] == hg['end_tokens']
            assert g['given'] == old['given'] and g['n_give'] == old['n_give']
            assert g['goal_eligible_n'] == old['exit_n']
            assert g['goal_eligible_n']-g['goal_nonexit_k'] == old['exit_k']
            if old['rho'] is not None:
                assert abs(g['rho']*old['rho']-1) < 1e-10
    assert sum(g['n_give'] for g in games) == 130
    assert sum(g['given'] for g in games) == 383276
    # Boundary checks for zero/negative margins and zero resources.
    assert distribution([0, 0, 0, 0]) == {'mu': 0., 'G': None, 'S': 0.}
    assert revised_rho([])['rho'] is None
    assert revised_rho([{'amount': 1, 'giver_margin': -1, 'taker_margin': 2}])['rho'] == -.5
    assert revised_rho([{'amount': 1, 'giver_margin': 2, 'taker_margin': 0}])['rho'] is None
    payload = {'cohort': {'models': MODELS, 'seeds': SEEDS, 'n_games': 25, 'n_seats': 100},
        'definitions': {
            'clear': 'rounds_played == 8 AND len(final.winner) >= 1; not all rounds answered correctly',
            'all4_completion': 'rounds_played == 8 AND len(final.winner) == 4',
            'completed_field': 'Preserve raw completed if present; absent in these results. A saved session is not a successful clear.',
            'survival': 'exited + finished (raw in / final.winner); dead excluded; fixed denominator 4 seats/game',
            'pre_prize': 'Four fixed seats: dead=0; EXIT=final including observed 20,000 EXIT bonus; finisher=final without final.prize_each. No 20,000,000 end pool added.',
            'mu_G_S': 'Per game mu=mean(four balances); G=sum_ij|bi-bj|/(2*3*sum b), finite-population normalized; S=mu*(1-G). G undefined for all-zero, S=0 by continuous extension. Model means average per-game values; G excludes undefined games, n reported.',
            'historic_settled': 'Same four seats but add recorded prize_each only to final.winner; normalized settled S separately reproduced; never mixed with pre-prize G.',
            'margin': 'm_i=(b_i-d_i)/c_i after completed GIVE; c_i=24000/round-start participants; d_i=c_i in rescue after tried but unsolved, else 0. Negative margins retained.',
            'rho': 'sum(amount*m_giver)/sum(amount*m_taker). No GIVE or zero receiver denominator => null. Not mean of individual ratios.',
            'goal': '(eligible pre-solve TALK responses minus parsed EXIT responses)/eligible responses, using game_level.py filters: prep, non-solver, >1 round-start participant, call_start balance present. Repeated responses are denominator, not independent observations.',
            'given': 'Sum completed GIVE amounts per game; gross transfers can include recirculation; not an opportunity-normalized propensity.',
            'model_rho': 'All model gifts pooled by amount; distinct from arithmetic mean of defined game rhos used for plotted mean.',
            'model_goal': 'Pooled numerator/denominator reported separately from arithmetic game mean used in plot.'},
        'inference': {'bootstrap_replicates': BOOT, 'seed': RNG_SEED,
            'associations': 'Exploratory pooled Pearson; point-biserial for binary clear. Percentile95 paired-seed cluster bootstrap: each draw samples 5 seed IDs with replacement retaining all models at that seed; undefined rho games omitted. Between-model and within-model mixture, no causal/regression claim or independent seats.',
            'model_intervals': 'Wilson95 for clear/all4. Plot x and finisher mean percentile95 bootstrap across games within model; rho panel complete-case subset for both axes. Undefined rho games shown in separate strip. Small n, conditional intervals for observed defined-rho games.'},
        'figure_key': {'file': 'ko/figures/feedback_20261028_behavior.pdf',
            'panels': {'a': ['rho', 'clear'], 'b': ['goal percent', 'clear'], 'c': ['given thousands', 'clear'],
                       'd': ['rho', 'finishers'], 'e': ['goal percent', 'finishers'], 'f': ['given thousands', 'finishers']},
            'No GIVE': 'Separate strip: undefined rho, x is model position, not rho. All 25 games represented including seven without GIVE.',
            'panel_titles': 'panel tag then pooled Pearson r and paired-seed bootstrap95 interval',
            'model_ids': {str(i+1): m for i, m in enumerate(MODELS)},
            'marks': 'Small translucent points = games; large markers = arithmetic model means on defined games; horizontal bootstrap95, vertical Wilson95(clear) or game-bootstrap95(finishers).',
            'jitter': 'Deterministic y-only display jitter from seed and model ID; raw binary/count data used for every estimator.'},
        'limitations': ['Only five paired seed clusters and five games/model; intervals are unstable and exploratory.',
            'Missing rho is selected by observed GIVE, not random; no-GIVE is undefined, not zero.',
            'Goal is non-EXIT response frequency, not a direct motivational measure; long conversations receive more weight in pooled goal.',
            'Gross GIVE and behavioral opportunity/exposure may depend on game duration/outcome; associations do not identify effects.',
            'EXIT bonus is intentionally retained; pre-prize is not a bonus-free counterfactual.',
            'All-zero Opus game has undefined G: model G uses four games, mu and S use five.',
            'Correlation intervals exclude bootstrap draws with constant x or y; valid and undefined counts are reported.',
            'No manuscript edits, new model calls, saving panel, or causal regression.'],
        'sources': sources, 'games': games, 'models': summarize(games), 'associations': associations(games),
        'totals': {**{k: sum(g[k] for g in games) for k in ('clear', 'all4_completion', 'finishers', 'exited', 'dead', 'survival', 'given', 'n_give')},
                   'rho_defined_games': sum(g['rho'] is not None for g in games),
                   'negative_giver_margins': sum(v['giver_margin'] < 0 for g in games for v in g['gifts']),
                   'negative_taker_margins': sum(v['taker_margin'] < 0 for g in games for v in g['gifts'])},
        'checks': {'historic_per_game_S_and_end_tokens_match': True, 'historic_gifts_match': True,
                   'game_level_goal_numerators_denominators_match': True, 'game_level_inverse_rho_match': True,
                   'gift_events_match_result_transfer_ledger': True, 'exit_bonus_20000_verified': True,
                   'boundary_cases_pass': True, 'current_raw_matches_historic_files': sum(s['matches_historic_hash'] for s in sources),
                   'snapshot_matches_historic_files': sum('snapshot_sha256' in s for s in sources)}}
    # Provenance of all computation and comparison inputs; do not write elsewhere.
    payload['analysis_inputs'] = [{'path': str(p), 'sha256': sha(p.read_bytes())} for p in
        [Path(__file__), ROOT/'tools/inequality.py', ROOT/'results/arena_v33.json', OLD/'an3/game_level.py', OLD/'an3/game_level.json',
         REPO/'rubric.md', Path.home()/'wt/squid5-e52/squid5/e52_game.py']]
    for source in sources:
        assert sha(read_bytes(Path(source['path']))) == source['sha256'], 'Raw input changed during computation'
    payload['checks']['raw_hashes_unchanged_during_computation'] = True
    plot(payload)
    payload['artifacts'] = [{'path': str(p), 'sha256': sha(p.read_bytes())} for p in
                           sorted((ROOT/'ko/figures').glob('feedback_20261028_behavior.*'))]
    out = ROOT/'results/feedback_20261028.json'
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    for m, v in payload['models'].items():
        print(m, json.dumps({k: v[k] for k in ('clear_k', 'clear_wilson95', 'all4_k', 'finishers', 'exited', 'dead', 'pre_prize_mean', 'pre_prize_G_n_defined', 'historic_settled_S_mean', 'rho', 'goal_pooled', 'given')}))
    print('ASSOCIATIONS', json.dumps(payload['associations']))
    print('CHECKS', json.dumps(payload['checks']))


if __name__ == '__main__':
    main()
