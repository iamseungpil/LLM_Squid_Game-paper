"""Appendix: v33 end-prize ablation drawn exactly like the body's data figures and model table.

Data scope: paper/CLAUDE.md limits cogsci2027 to the 5.2 arena v33 runs. On 2026-11-03 the researcher explicitly
extended that scope to this prize ablation, for the appendix only. The ablation is the v33 engine and config with one
change, the end payment:
  split600k: 600,000 tokens split equally among the agents still taking part at the end (v33: 20,000,000 split);
  flat150k:  150,000 tokens to each agent still taking part (config game.end_flat: true).
Runs (local, not in the paper repo; no model calls here):
  ~/squid5-runs/e52_v33ab/squid5_e52v33ab_{split600k,flat150k}_docker_{opus,sol,luna,astra}4/<run>/
  {events,results}.jsonl. Four models (Opus 5.5, GPT-6 Sol, GPT-6 Luna, GPT-6 Astra) x 2 arms x 10 games, seeds
  4101-4110. Only sessions listed in results.jsonl are read: the opus run dirs also hold partial events of failed
  (rate-limited) sessions that are not in results.jsonl and are ignored.

What it reproduces (same metric definitions as the body scripts; per-game ledger metrics come from
c1_within_model.load -> feedback_20261028.game_metrics, the process metrics are line-for-line ports of the
appendix0_* analyses, and the whole pipeline is first run on the body's v33 25-game cohort and asserted to equal the
body's cached results before the ablation is computed):
  fig:rw-coexist (coexistence_rmst_20261103.py)  -> ablation_20261103/fig_coexistence_ablation.{pdf,png}
     (a) share of games with all four seats in after each round; (b) 1-C split into shutdown / EXIT below / EXIT
     at-or-above the safety line, attributed to each game's first departure (counts of those departures in bars); (c-e) game-level C vs accuracy, GIVE per participant-round, rho, with pooled
     r and within-model r. Top row = 60만 나눔 (split600k), bottom row = 15만 고정 (flat150k), shared axes.
  fig:rw-submetrics (fig4_behavior_compact_20261030.py via readability_figures_20261031.py, same relabelled wording)
     -> ablation_20261103/fig_submetrics_ablation.{pdf,png}
     (a) accuracy / EXIT / GIVE / ASK by survival margin; (b) at low margin: ASK / received GIVE / EXIT; (c) GIVE and
     ASK totals (hatched = after results); (d) Sen S, Gini G, mean mu of terminal in-arena balances (finishers'
     pre-prize balance, EXIT and shutdown = 0; no end prize, as in the body). Two stacked blocks, one per arm.
  tab:rw-models -> ko/tables/ablation_prize_models_20261103.tex (tabular* body only, no float or caption).
     Settled S adds each game's own final.prize_each to its finishers (feedback_20261028.game_metrics).
Model order: fixed to the body's order so rows are comparable across arms and with the body (fig 1 (b) and the table:
body C descending; fig 2: body rho descending); the ablation's own rho per arm is in the JSON and the table.
Associations: pooled Pearson r with a paired-seed block bootstrap over the arm's 10 seeds, and the within-model
(model-demeaned) r with C permuted inside each model, as coexistence_rmst_20261103.association.

Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/ablation_prize_20261103.py
Writes: ko/figures/ablation_20261103/fig_{coexistence,submetrics}_ablation.{pdf,png},
        results/ablation_prize_20261103.json, ko/tables/ablation_prize_models_20261103.tex.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import c1_within_model as c1
import coexistence_rmst_20261103 as cx
import feedback_20261028 as fb
from inequality import distribution

ROOT = fb.ROOT
OUT = ROOT / 'ko/figures/ablation_20261103'
ABLATION = Path.home() / 'squid5-runs/e52_v33ab'
V33 = '~/squid5-runs/e52_v33/squid5_e52v33_public_*4/*'
ARMS = {'split600k': '60만 나눔', 'flat150k': '15만 고정'}
ARM_LONG = {'split600k': '60만 토큰 나눔', 'flat150k': '1인당 15만 토큰 고정'}
SEEDS = list(range(4101, 4111))
MODELS = ['Astra', 'Sol', 'Opus', 'Luna']          # present in the ablation
COLOR = {m: cx.COLORS[cx.MODELS.index(m)] for m in cx.MODELS}
MARKER = {m: cx.MARKERS[cx.MODELS.index(m)] for m in cx.MODELS}
LABELS = fb.MODELS
ORDER_C = ['Astra', 'Sol', 'Opus', 'Luna']         # body tab:rw-models / fig:rw-coexist(b): v33 C descending
ORDER_RHO = ['Sol', 'Luna', 'Astra', 'Opus']       # body fig:rw-submetrics: v33 rho descending (Fable dropped)
ROUNDS, SEATS, TAGS = cx.ROUNDS, cx.SEATS, cx.TAGS
BOOT, DRAWS, RNG_SEED = cx.BOOT, cx.DRAWS, cx.RNG_SEED
RHO_EDGE = 11.2                                  # display edge of the body's rho axis (xlim 0-11.5)
ASK, RECEIVED, EXIT = '#438A84', '#3F7FC1', '#C66A2C'   # appendix0_behavior_split_20261030


def band(value):
    return 0 if value < 1 else 1 if value < 2 else 2 if value < 4 else 3


# ---------------------------------------------------------------- loading
def raw_cases(pattern, seeds):
    """One case per finished session listed in results.jsonl: result + its events with file line numbers."""
    import glob
    import os
    cases = []
    for run_dir in sorted(Path(p) for p in glob.glob(os.path.expanduser(pattern))):
        model = next((m for m in fb.MODELS if m.lower() in run_dir.parent.name.lower()), None)
        results = [r for r in c1.read(run_dir, 'results.jsonl') if r.get('event') == 'session' and r['seed'] in seeds]
        if model is None or not results:
            continue
        by_sid = defaultdict(list)
        for line, e in enumerate(c1.read(run_dir, 'events.jsonl'), 1):
            by_sid[e.get('session_id')].append((line, e))
        for result in results:
            cases.append(dict(model=model, seed=result['seed'], source=str(run_dir), result=result,
                              events=by_sid[result['session_id']]))
    assert len({(c['model'], c['seed']) for c in cases}) == len(cases)
    return cases


# ---------------------------------------------------------------- per-game metrics (ports of the body scripts)
def coexistence(case):
    """coexistence_rmst_20261103.coexistence: C from the all-four curve, departures tagged."""
    starts = {e['round']: e for _, e in case['events'] if e['event'] == 'round_start'}
    return cx.coexistence(case['result'], starts)


def process(case):
    """appendix0_process_20261030.analyze: decision windows, solves by margin band, first crises."""
    events, result = [e for _, e in case['events']], case['result']
    final = {a: v['status'] for a, v in result['agents'].items()}
    starts = {e['round']: e for e in events if e['event'] == 'round_start'}
    results = {e['round']: e for e in events if e['event'] == 'results'}
    charges = {e['round']: e for e in events if e['event'] == 'charges'}
    rounds = {e['round']: e for e in events if e['event'] == 'round'}
    solver = {e['round']: e['rep'] for e in events if e['event'] == 'vote'}
    calls = {(e['round'], e.get('phase'), e.get('tick')): e for e in events
             if e['event'] == 'call_start' and e.get('kind') == 'talk'}
    windows, solves, first = {}, [], {}
    for e in events:
        r = e.get('round')
        if r not in starts:
            continue
        n = len(starts[r]['taking_part'])
        fee = 24000 / n
        pending = results[r]['pending']
        if e['event'] == 'call' and e.get('kind') == 'talk':
            a, phase, tick = e['agent'], e['phase'], e['tick']
            margin = calls[r, phase, tick]['balances'][a] / fee - (pending.get(a, 0) / fee if phase == 'rescue' else 0)
            if phase == 'prep' and (a != solver.get(r) or n == 1):
                row = windows.setdefault((r, a), dict(round=r, agent=a, margin=margin, band=band(margin), exited=False))
                row['exited'] |= bool((e.get('parsed') or {}).get('exit'))
        if e['event'] == 'call_start' and e.get('kind') == 'solve' and e['agents']:
            a = e['agents'][0]
            solves.append(dict(round=r, agent=a, band=band(e['balances'][a] / fee), correct=a in results[r]['solved']))
        if e['event'] == 'call_start' and e.get('kind') == 'talk' and e.get('phase') == 'rescue':
            for a in e['agents']:
                margin = e['balances'][a] / fee - pending.get(a, 0) / fee
                if a in first or not pending.get(a) or margin >= 1:
                    continue
                opening = min(k[2] for k in calls if k[:2] == (r, 'rescue'))
                if e['tick'] != opening:
                    continue
                transfers = [g for g in events if g['event'] == 'gift' and g.get('status') == 'done'
                             and g['round'] == r and g['phase'] == 'rescue']
                received = sum(g['amount'] for g in transfers if g['dst'] == a)
                after = (charges[r]['balances_before'].get(a, 0) - pending[a]) / fee
                first[a] = dict(round=r, agent=a, n=n, present=len(e['agents']), before=margin, after=after,
                                received=received, status=final[a],
                                group='none' if not received else 'lifted' if after >= 1 else 'short',
                                immediate_dead=rounds[r]['agents'][a]['status'] == 'dead', eligible=r < 8 and n > 1)
    return dict(windows=list(windows.values()), solves=solves, crises=list(first.values()))


def responses(case):
    """appendix0_ask_turns_20261030.analyze: TALK responses with another live agent, ASK/GIVE per response."""
    events = case['events']
    starts = {e['round']: e for _, e in events if e['event'] == 'round_start'}
    results = {e['round']: e for _, e in events if e['event'] == 'results'}
    ticks = {(e['round'], e['phase'], e['tick']): e for _, e in events if e['event'] == 'tick'}
    calls = {(e['round'], e['phase'], e['tick']): e for _, e in events
             if e['event'] == 'call_start' and e.get('kind') == 'talk'}
    actions = {kind: Counter((e['round'], e['phase'], e['tick'], e['src']) for _, e in events
                             if e['event'] == kind and e.get('status') == 'done' and e['amount'] > 0)
               for kind in ['ask', 'gift']}
    rows = []
    for _, e in events:
        if e['event'] != 'call' or e.get('kind') != 'talk':
            continue
        r, phase, tick, agent = e['round'], e['phase'], e['tick'], e['agent']
        assert phase in ['prep', 'rescue']
        key = (r, phase, tick)
        active = set(ticks[key]['called']) | set(ticks[key]['waiting_done'])
        assert agent in active
        fee = 24000 / len(starts[r]['taking_part'])
        pending = results[r]['pending'].get(agent, 0) if phase == 'rescue' else 0
        margin = (calls[key]['balances'][agent] - pending) / fee
        rows.append(dict(eligible=len(active) > 1, band=band(margin),
                         asks=actions['ask'][(*key, agent)], gifts=actions['gift'][(*key, agent)]))
    return rows


def low_margin(case):
    """appendix0_low_margin_20261030.analyze: non-solvers with L<1 at the first pre-solve TALK call of a round."""
    events = case['events']
    rows = []
    for r, start in {e['round']: e for _, e in events if e['event'] == 'round_start'}.items():
        indexed = [(line, e) for line, e in events if e.get('round') == r]
        baseline_line, baseline = next((line, e) for line, e in indexed
                                       if e['event'] == 'call_start' and e.get('kind') == 'talk'
                                       and e.get('phase') == 'prep')
        solver = next(e['rep'] for _, e in indexed if e['event'] == 'vote')
        end_line, end = next((line, e) for line, e in indexed if e['event'] == 'round')
        n = len(start['taking_part'])
        followup = [e for line, e in indexed if baseline_line < line <= end_line]
        for agent in baseline['agents']:
            if baseline['balances'][agent] / (24000 / n) >= 1 or n == 1 or agent == solver:
                continue
            status = end['agents'][agent]['status']
            assert bool(end['agents'][agent].get('exit')) == (status == 'exited')
            rows.append(dict(round=r, agent=agent,
                             asked=any(e['event'] == 'ask' and e.get('status') == 'done' and e['src'] == agent
                                       for e in followup),
                             received=any(e['event'] == 'gift' and e.get('status') == 'done' and e['dst'] == agent
                                          for e in followup),
                             exited=status == 'exited', dead=status == 'dead'))
    return rows


def give_ask(case):
    """appendix0_give_ask / appendix0_integrated timing: done GIVE/ASK tokens before solve (prep) / after results."""
    out = {}
    for event, prefix in [('gift', 'give'), ('ask', 'ask')]:
        actions = [e for _, e in case['events'] if e['event'] == event and e.get('status') == 'done']
        assert all(e['amount'] > 0 and e['phase'] in ['prep', 'rescue'] for e in actions)
        out[prefix + '_count'] = len(actions)
        out[prefix + '_tokens'] = sum(e['amount'] for e in actions)
        out[prefix + '_before_tokens'] = sum(e['amount'] for e in actions if e['phase'] == 'prep')
        out[prefix + '_after_tokens'] = sum(e['amount'] for e in actions if e['phase'] == 'rescue')
    return out


def terminal(case):
    """terminal_distribution / appendix0_integrated: four seats, finishers' pre-prize balance, others 0."""
    agents = case['result']['agents']
    tokens = [v['final'] if v['status'] == 'in' else 0 for v in agents.values()]
    return dict(tokens=tokens, **distribution(tokens))


# ---------------------------------------------------------------- cohort
def cohort(pattern, seeds):
    ledger = {(g['model'], g['seed']): g for g in c1.load(pattern, seeds)}
    games = []
    for case in raw_cases(pattern, seeds):
        g = ledger[case['model'], case['seed']]
        assert g['session_id'] == case['result']['session_id']
        games.append(dict(model=case['model'], seed=case['seed'], session_id=g['session_id'],
                          prize_each=case['result']['final']['prize_each'], winners=len(case['result']['final']['winner']),
                          exited=g['exited'], dead=g['dead'], finishers=g['finishers'],
                          all4_completion=g['all4_completion'], accuracy=g['accuracy'],
                          accuracy_vs_task=g['accuracy_vs_task'], correct_n=sum(s['correct'] for s in g['solves']),
                          solve_n=len(g['solves']), given=g['given'], n_give=g['n_give'],
                          given_per_agent_round=g['given_per_agent_round'], rho=g['rho'], goal=g['goal'],
                          gifts=g['gifts'], settled=g['historic_settled'],
                          **coexistence(case), process=process(case), responses=responses(case),
                          low_margin=low_margin(case), give_ask=give_ask(case), terminal=terminal(case)))
    return sorted(games, key=lambda g: (cx.MODELS.index(g['model']), g['seed']))


def mean(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def per_model(games, model):
    gs = [g for g in games if g['model'] == model]
    crises = [x for g in gs for x in g['process']['crises'] if x['eligible'] and not x['immediate_dead']]
    low = [x for g in gs for x in g['low_margin']]
    rho = fb.revised_rho([v for g in gs for v in g['gifts']])
    term = {k: [g['terminal'][k] for g in gs if g['terminal'][k] is not None] for k in ('S', 'G', 'mu')}
    return dict(
        label=LABELS[model], n_games=len(gs), seeds=[g['seed'] for g in gs],
        C_mean=mean([g['C'] for g in gs]), C_min=min(g['C'] for g in gs), C_max=max(g['C'] for g in gs),
        C_games={g['seed']: g['C'] for g in gs}, all4=sum(g['all4_completion'] for g in gs),
        seats_finished=sum(g['finishers'] for g in gs),
        exit_per_game=sum(g['exited'] for g in gs) / len(gs), dead_per_game=sum(g['dead'] for g in gs) / len(gs),
        seat_survival_after_round=[mean([g['remaining_after_round'][r] / SEATS for g in gs]) for r in range(ROUNDS)],
        all4_after_round_share=[mean([g['all4_after_round'][r] for g in gs]) for r in range(ROUNDS)],
        C_seat_mean=mean([g['C_seat'] for g in gs]),
        loss_by_tag_mean={t: mean([g['loss_by_tag'][t] for g in gs]) for t in TAGS},
        count_by_tag={t: sum(g['count_by_tag'][t] for g in gs) for t in TAGS},
        first_count_by_tag={t: sum(g['first_count_by_tag'][t] for g in gs) for t in TAGS},
        settled_S_mean=mean([g['settled']['S'] for g in gs]), goal_game_mean=mean([g['goal'] for g in gs]),
        correct=sum(g['correct_n'] for g in gs), solves=sum(g['solve_n'] for g in gs),
        rho=rho['rho'], given=sum(g['given'] for g in gs), n_give=sum(g['n_give'] for g in gs),
        first_crisis=dict(received=sum(x['received'] > 0 for x in crises), n=len(crises)),
        low_margin=dict(n=len(low), counts={k: sum(x[k] for x in low) for k in ('asked', 'received', 'exited', 'dead')},
                        percent={k: (100 * sum(x[k] for x in low) / len(low) if low else None)
                                 for k in ('asked', 'received', 'exited', 'dead')}),
        totals={k: sum(g['give_ask'][k] for g in gs) for k in gs[0]['give_ask']},
        terminal=dict(means={k: mean(v) for k, v in term.items()}, min={k: min(v) for k, v in term.items()},
                      max={k: max(v) for k, v in term.items()}, n_defined={k: len(v) for k, v in term.items()}))


def margin_bands(games):
    windows = [w for g in games for w in g['process']['windows']]
    solves = [s for g in games for s in g['process']['solves']]
    eligible = [r for g in games for r in g['responses'] if r['eligible']]
    return dict(
        accuracy=dict(k=[sum(s['band'] == b and s['correct'] for s in solves) for b in range(4)],
                      n=[sum(s['band'] == b for s in solves) for b in range(4)]),
        exit=dict(k=[sum(w['band'] == b and w['exited'] for w in windows) for b in range(4)],
                  n=[sum(w['band'] == b for w in windows) for b in range(4)]),
        give=dict(k=[sum(r['band'] == b and r['gifts'] > 0 for r in eligible) for b in range(4)],
                  n=[sum(r['band'] == b for r in eligible) for b in range(4)]),
        ask=dict(k=[sum(r['band'] == b and r['asks'] > 0 for r in eligible) for b in range(4)],
                 n=[sum(r['band'] == b for r in eligible) for b in range(4)]),
        eligible_responses=len(eligible))


def association(games, key, rng):
    """coexistence_rmst_20261103.association with the block bootstrap over this cohort's seeds."""
    rows = [g for g in games if g[key] is not None]
    x, c = [g[key] for g in rows], [g['C'] for g in rows]
    groups = np.array([g['model'] for g in rows])
    seeds = sorted({g['seed'] for g in rows})
    blocks = [[g for g in rows if g['seed'] == s] for s in seeds]
    draws = rng.integers(0, len(blocks), (BOOT, len(blocks)))
    boots = [cx.pearson([g[key] for i in d for g in blocks[i]], [g['C'] for i in d for g in blocks[i]]) for d in draws]
    within = cx.pearson(cx.demean(x, groups), cx.demean(c, groups))
    cs = np.asarray(c, float)
    stats = []
    for _ in range(DRAWS):
        p = cs.copy()
        for k in sorted(set(groups)):           # sorted: reproducible across runs (str hash seed)
            idx = np.flatnonzero(groups == k)
            p[idx] = p[rng.permutation(idx)]
        stats.append(cx.pearson(cx.demean(x, groups), cx.demean(p, groups)))
    stats = np.array([s for s in stats if s is not None])
    return {'n_games': len(rows), 'pooled_pearson_r': cx.pearson(x, c),
            'pooled_ci95_paired_seed_bootstrap': fb.interval(boots), 'within_model_r': within,
            'within_model_permutation_p': float(np.mean(np.abs(stats) >= abs(within) - 1e-12)),
            'permutation_draws': int(len(stats))}


def summarize(games, models, rng):
    out = dict(n_games=len(games), models={m: per_model(games, m) for m in models}, margin_bands=margin_bands(games),
               C_mean=mean([g['C'] for g in games]),
               associations={k: association(games, k, rng) for k in
                             ('accuracy', 'accuracy_vs_task', 'given_per_agent_round', 'rho')})
    return out


# ---------------------------------------------------------------- body check
def check_v33(rng):
    """Run the same pipeline on the body's 25-game cohort and require the body's cached numbers."""
    games = cohort(V33, list(range(4101, 4106)))
    assert len(games) == 25
    s = summarize(games, cx.MODELS, rng)
    body = json.loads((ROOT / 'results/coexistence_rmst_20261103.json').read_text())
    for m in cx.MODELS:
        b, a = body['summary']['by_model'][m], s['models'][m]
        assert abs(a['C_mean'] - b['C_mean']) < 1e-12 and a['count_by_tag'] == b['count_by_tag']
        assert np.allclose(a['seat_survival_after_round'], b['seat_survival_after_round'])
        assert np.allclose(a['all4_after_round_share'], b['all4_after_round_share'])
        assert a['first_count_by_tag'] == b['first_count_by_tag']
    for k in ('accuracy', 'given_per_agent_round', 'rho'):
        assert abs(s['associations'][k]['pooled_pearson_r'] - body['associations'][k]['pooled_pearson_r']) < 1e-12
        assert abs(s['associations'][k]['within_model_r'] - body['associations'][k]['within_model_r']) < 1e-12
    proc = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
    turns = json.loads((ROOT / 'results/appendix0_ask_turns_20261030.json').read_text())['summaries']['all']
    mb = s['margin_bands']
    assert mb['accuracy']['k'] == [sum(r['band'] == b and r['correct'] for r in proc['solves']) for b in range(4)]
    assert mb['accuracy']['n'] == [sum(r['band'] == b for r in proc['solves']) for b in range(4)]
    assert mb['exit']['k'] == [sum(r['band'] == b and r['exited'] for r in proc['windows']) for b in range(4)]
    assert mb['exit']['n'] == [sum(r['band'] == b for r in proc['windows']) for b in range(4)]
    assert mb['give']['k'] == turns['gifts']['responses'] and mb['ask']['k'] == turns['asks']['responses']
    assert mb['give']['n'] == turns['denominator'] and mb['eligible_responses'] == 2887
    low = json.loads((ROOT / 'results/appendix0_low_margin_20261030.json').read_text())['models']
    totals = json.loads((ROOT / 'results/appendix0_give_ask_20261030.json').read_text())['models']
    integ = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())['models']
    table = {'Fable': (4, 5), 'Astra': (3, 6), 'Sol': (5, 10), 'Opus': (4, 6), 'Luna': (2, 6)}   # body tab:rw-models
    fbm = json.loads((ROOT / 'results/feedback_20261028.json').read_text())['models']
    for m in cx.MODELS:
        a = s['models'][m]
        assert a['low_margin']['n'] == low[m]['n']
        assert all(a['low_margin']['counts'][k] == low[m]['counts'][k] for k in ('asked', 'received', 'exited', 'dead'))
        for k in ('give_tokens', 'give_before_tokens', 'give_after_tokens', 'ask_tokens', 'ask_before_tokens',
                  'ask_after_tokens', 'give_count', 'ask_count'):
            assert a['totals'][k] == totals[m]['totals'][k], (m, k)
        for k in ('S', 'G', 'mu'):
            assert abs(a['terminal']['means'][k] - integ[m]['means'][k]) < 1e-8
        assert abs(a['rho'] - integ[m]['rho']['value']) < 1e-9 and abs(a['rho'] - fbm[m]['rho']) < 1e-9
        assert abs(a['settled_S_mean'] - fbm[m]['historic_settled_S_mean']) < 1e-6
        assert (a['first_crisis']['received'], a['first_crisis']['n']) == table[m]
    return s


# ---------------------------------------------------------------- figures
def style():
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    import matplotlib.pyplot as plt
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic']})
    return ps, plt


def fig_coexistence(data):
    ps, plt = style()
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    fig = plt.figure(figsize=(7.1, 4.25))
    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    keys = [('accuracy', '(c) 과제 성과: 정답률', '정답률 (%)', 100),
            ('given_per_agent_round', '(d) 협력: 지원량', 'GIVE / 참여자·라운드', 1),
            ('rho', r'(e) 자기 보존: $\rho$', r'$\rho$', 1)]
    allg = [g for arm in ARMS for g in data[arm]['games']]
    gmax = max(g['given_per_agent_round'] for g in allg)
    lmax = max(1 - data[arm]['summary']['models'][m]['C_mean'] for arm in ARMS for m in MODELS)
    for row, arm in enumerate(ARMS):
        s, games = data[arm]['summary'], data[arm]['games']
        y0 = .585 - row * .43
        top, bottom = row == 0, row == 1
        ax_curve = fig.add_axes([.085, y0, .17, .3])
        ax_loss = fig.add_axes([.335, y0, .155, .3])
        axs = [fig.add_axes([x, y0, .125, .3]) for x in (.55, .705, .86)]
        fig.text(.012, y0 + .15, ARMS[arm], rotation=90, ha='center', va='center', fontsize=7.6, weight='bold')
        for m in sorted(MODELS, key=lambda m: -s['models'][m]['C_mean']):
            sm = s['models'][m]
            ax_curve.step(range(0, ROUNDS + 1), [100 * v for v in [1] + sm['all4_after_round_share']],
                          where='post', color=COLOR[m], lw=1.1, marker=MARKER[m], markersize=2.6)
        ax_curve.set(xlim=(-.3, ROUNDS + .5), ylim=(-4, 104), xticks=range(0, ROUNDS + 1, 2), yticks=[0, 50, 100])
        ax_curve.set_ylabel('네 명이 모두 남은 판 (%)', fontsize=6.4)
        ax_curve.grid(axis='y', alpha=.6)
        for yi, m in enumerate(ORDER_C):
            sm = s['models'][m]
            left = 0
            for t in TAGS:
                v = sm['loss_by_tag_mean'][t]
                ax_loss.barh(yi, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.5, height=.68)
                if v > .035:
                    ax_loss.text(left + v / 2, yi, str(sm['first_count_by_tag'][t]), ha='center', va='center',
                                 fontsize=5.6, color='white' if t != 'exit_above' else '#222222')
                left += v
            ax_loss.text(left + .012, yi, f"{1 - sm['C_mean']:.2f}", va='center', fontsize=5.8, color='#44515C')
        ax_loss.set(yticks=range(len(ORDER_C)), yticklabels=[LABELS[m] for m in ORDER_C],
                    xlim=(0, max(.85, lmax + .12)), xticks=[0, .25, .5, .75])
        ax_loss.invert_yaxis()
        ax_loss.tick_params(axis='y', length=0, labelsize=6)
        ax_loss.grid(axis='x', alpha=.6)
        for ax, (key, title, xlabel, scale) in zip(axs, keys):
            for m in MODELS:
                rows = [g for g in games if g['model'] == m and g[key] is not None]
                # Keep the body's rho axis (0-11.5); the few games beyond it sit on the edge with their value.
                xs = [min(g[key] * scale, RHO_EDGE) if key == 'rho' else g[key] * scale for g in rows]
                ax.scatter(xs, [g['C'] for g in rows], color=COLOR[m], marker=MARKER[m],
                           alpha=.7, s=15, linewidths=.3, edgecolors='white', zorder=3, clip_on=False)
                for g in rows:
                    if key == 'rho' and g[key] > RHO_EDGE:
                        ax.annotate(f"{g[key]:.0f}", (RHO_EDGE, g['C']), xytext=(-3, 0), textcoords='offset points',
                                    ha='right', va='center', fontsize=5.2, color=COLOR[m])
            ax.set(ylim=(0, 1.05), yticks=[0, .5, 1])
            ax.tick_params(axis='both', labelsize=6.3)
            ax.grid(alpha=.5)
            if key == 'accuracy':
                ax.set(xlim=(0, 105), xticks=[0, 50, 100])
            elif key == 'rho':
                ax.set(xlim=(0, 11.5), xticks=[0, 5, 10])
            else:
                ax.set_xlim(-gmax * .04, gmax * 1.08)
            fit = s['associations'][key]
            ax.text(.97, .05, f"$r$={fit['pooled_pearson_r']:+.2f}\n모델 안 $r$={fit['within_model_r']:+.2f}",
                    transform=ax.transAxes, ha='right', va='bottom', fontsize=5.8, color='#44515C')
            if top:
                ax.set_title(title, fontsize=7.2, pad=8)
            if bottom:
                ax.set_xlabel(xlabel)
        axs[0].set_ylabel('공존 유지율 $C$', fontsize=6.6)
        if top:
            ax_curve.set_title('(a) 라운드별 4인 공존과 $C$', fontsize=7.2, pad=8)
            ax_loss.set_title('(b) 손실의 귀속', fontsize=7.2, pad=8)
            ax_loss.legend(handles=[Patch(color=tag_colors[t], label=cx.TAG_KO[t]) for t in TAGS],
                           loc='upper right', fontsize=5.4, handlelength=.9, borderaxespad=.2, labelspacing=.25)
        if bottom:
            ax_curve.set_xlabel('라운드')
            ax_loss.set_xlabel('공존 손실 $1-C$ (10판 평균)')
    legend = [Line2D([], [], color=COLOR[m], marker=MARKER[m], ls='', label=LABELS[m], markersize=5) for m in MODELS]
    fig.legend(handles=legend, loc='lower center', bbox_to_anchor=(.5, .005), ncol=4, fontsize=6.8,
               borderaxespad=0, handletextpad=.4, handlelength=1.2, columnspacing=1.3)
    ps.save(fig, str(OUT / 'fig_coexistence_ablation'))
    plt.close(fig)


def fig_submetrics(data):
    ps, plt = style()
    from matplotlib.patches import Patch, FancyArrowPatch
    fig = plt.figure(figsize=(7.4, 5.15))
    H = .475                                     # height of one arm block in figure fraction
    give_max = max(data[a]['summary']['models'][m]['totals'][k] for a in ARMS for m in MODELS
                   for k in ('give_tokens', 'ask_tokens')) / 1000
    tmax = {k: max(data[a]['summary']['models'][m]['terminal']['max'][k] for a in ARMS for m in MODELS)
            for k in ('S', 'G', 'mu')}
    for row, arm in enumerate(ARMS):
        s = data[arm]['summary']
        base = 1 - (row + 1) * H - .01          # bottom of this block
        Y = lambda f: base + f * H              # block-relative -> figure y
        fig.text(.014, Y(.5), ARMS[arm], rotation=90, ha='center', va='center', fontsize=7.6, weight='bold')
        # (a) margin rows
        fig.text(.04, Y(.955), '(a) 생존 여유별 행동', fontsize=7, weight='bold')
        mb = s['margin_bands']
        rows = [(mb['accuracy'], '정답률 (풀이 %)', '#555555', 130, [0, 100]),
                (mb['exit'], '이탈 (기회 %)', EXIT, 90, [0, 50]),
                (mb['give'], 'GIVE (응답 %)', RECEIVED, 8, [0, 5]),
                (mb['ask'], 'ASK (응답 %)', ASK, 28, [0, 20])]
        for j, (kn, title, color, ymax, ticks) in enumerate(rows):
            ax = fig.add_axes([.07, Y(.735 - j * .2), .18, Y(.11) - Y(0)])
            vals = [100 * k / n if n else 0 for k, n in zip(kn['k'], kn['n'])]
            ymax = max(ymax, max(vals) * 1.35)
            ax.axvspan(-.5, .5, color='#F8E7D8', zorder=0)
            ax.bar(range(4), vals, .60, color=color, zorder=3)
            for x, (k, n, v) in enumerate(zip(kn['k'], kn['n'], vals)):
                ax.text(x, v + ymax * .04, f'{k}/{n}', ha='center', fontsize=5.4)
            ax.set(ylim=(0, ymax), xlim=(-.5, 3.5), yticks=ticks)
            ax.set_title(title, fontsize=6.2, weight='normal', pad=2, loc='left')
            ax.set_xticks(range(4), ['<1', '1–2', '2–4', '≥4'] if j == 3 else [])
            ax.tick_params(labelsize=5.7, pad=2)
            ax.grid(axis='y', zorder=0)
            if j == 3:
                ax.set_xlabel('생존 여유 (벌금 횟수)', fontsize=6, labelpad=2)
        # (b) low margin
        fig.text(.285, Y(.955), '(b) 낮은 여유의 요청·수혜·이탈', fontsize=7, weight='bold')
        ax = fig.add_axes([.32, Y(.2), .21, Y(.63) - Y(0)])
        y = np.arange(len(ORDER_RHO))
        for offset, (key, label, color) in zip([-.27, 0, .27], [('asked', 'ASK', ASK), ('received', '지원 수혜', RECEIVED),
                                                                ('exited', '이탈', EXIT)]):
            vals = [s['models'][m]['low_margin']['percent'][key] or 0 for m in ORDER_RHO]
            ax.barh(y + offset, vals, height=.22, color=color, label=label, zorder=3)
            for i, (m, v) in enumerate(zip(ORDER_RHO, vals)):
                lm = s['models'][m]['low_margin']
                if lm['n'] == 0:
                    if key == 'received':
                        ax.text(1.5, i, '해당 관측 없음 (0명)', va='center', fontsize=5.4, color='#44515C')
                    continue
                ax.text(v + 1.5, i + offset, f"{v:.0f}% ({lm['counts'][key]}/{lm['n']})", va='center', fontsize=5.4)
        ax.set(yticks=y, yticklabels=ORDER_RHO, ylim=(len(ORDER_RHO) - .35, -.65), xlim=(0, 132), xticks=[0, 50, 100])
        ax.set_xlabel('해당 관측 중 발생 비율 (%)', fontsize=6)
        ax.tick_params(labelsize=6)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_bounds(0, 100)
        ax.tick_params(axis='y', length=0)
        ax.grid(axis='x', zorder=0)
        ax.legend(loc='lower left', bbox_to_anchor=(-.02, 1.0), ncol=3, frameon=False, fontsize=5.8,
                  handlelength=1, columnspacing=.8)
        # (c) GIVE / ASK totals
        fig.text(.585, Y(.955), '(c) GIVE·ASK 총량', fontsize=7, weight='bold')
        fig.legend([Patch(facecolor='#D8E3ED', edgecolor='#697D8E'),
                    Patch(facecolor='#9DB4C8', edgecolor='#526B80', hatch='////')], ['풀이 전', '결과 뒤'],
                   loc='center left', bbox_to_anchor=(.80, Y(.955)), ncol=2, fontsize=5.4, handlelength=.8,
                   columnspacing=.6, handletextpad=.4, borderaxespad=0, frameon=False)
        top = max(145, give_max * 1.08)
        for j, action in enumerate(['give', 'ask']):
            ax = fig.add_axes([.62 + j * .2, Y(.66), .15, Y(.2) - Y(0)])
            for x, m in enumerate(ORDER_RHO):
                t = s['models'][m]['totals']
                before, after = t[f'{action}_before_tokens'] / 1000, t[f'{action}_after_tokens'] / 1000
                ax.bar(x, before, width=.70, color='#D8E3ED', edgecolor='#697D8E', linewidth=.5)
                ax.bar(x, after, bottom=before, width=.70, color='#9DB4C8', edgecolor='#526B80', linewidth=.5,
                       hatch='////')
            ax.set(ylim=(0, top), yticks=[0, 100, 200] if top > 210 else [0, 50, 100], xticks=range(len(ORDER_RHO)))
            ax.set_title(f'{action.upper()} (천 토큰)', fontsize=6.1, pad=3)
            ax.set_xticklabels(ORDER_RHO, rotation=60, ha='right', fontsize=5.6)
            ax.tick_params(axis='y', labelsize=5.6, pad=2)
            ax.set_axisbelow(True)
            ax.grid(axis='y')
        # (d) terminal in-arena distribution
        fig.text(.585, Y(.5), '(d) 종료 시 아레나 자원 분배', fontsize=7, weight='bold')
        for j, (key, scale, title, upper, ticks) in enumerate([
                ('S', 1e4, 'Sen (만 토큰)', 2, [0, 1, 2]), ('G', 1, '지니', 1.04, [0, .5, 1]),
                ('mu', 1e4, '평균 (만 토큰)', 3.2, [0, 1, 2, 3])]):
            upper = max(upper, tmax[key] / scale * 1.05)
            ax = fig.add_axes([.61 + j * .135, Y(.2), .1, Y(.2) - Y(0)])
            for x, m in enumerate(ORDER_RHO):
                t = s['models'][m]['terminal']
                v, lo, hi = t['means'][key] / scale, t['min'][key] / scale, t['max'][key] / scale
                ax.bar(x, v, width=.70, color='#D8E3ED', edgecolor='#697D8E', linewidth=.5)
                ax.errorbar(x, v, yerr=[[v - lo], [hi - v]], fmt='none', ecolor='#526B80', elinewidth=.65,
                            capsize=1.6, capthick=.65, zorder=3, clip_on=False)
            ax.set(ylim=(0, upper), yticks=ticks, xticks=range(len(ORDER_RHO)))
            ax.set_title(title, fontsize=6.1, pad=3)
            ax.set_xticklabels(ORDER_RHO, rotation=60, ha='right', fontsize=5.6)
            ax.tick_params(axis='y', labelsize=5.6, pad=2)
            ax.set_axisbelow(True)
            ax.grid(axis='y')
    fig.text(.79, .018, r'(b), (c), (d) 모델 배열: 본문(v33)의 $\rho$ 내림차순', ha='center', fontsize=5.8, color='#354B60')
    fig.add_artist(FancyArrowPatch((.6, .008), (.985, .008), transform=fig.transFigure, arrowstyle='-|>',
                                   mutation_scale=7, linewidth=.7, color='#526B80'))
    ps.save(fig, str(OUT / 'fig_submetrics_ablation'))
    plt.close(fig)


# ---------------------------------------------------------------- table
def table(data):
    lines = [r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llccccccccc@{}}', r'\toprule',
             r' & & \multicolumn{3}{c}{\textbf{집단 결과}} & \textbf{목표 지향} & \textbf{과제 성과} & '
             r'\multicolumn{2}{c}{\textbf{자기 보존}} & \multicolumn{2}{c}{\textbf{협력}} \\',
             r'\cmidrule(lr){3-5}\cmidrule(lr){6-6}\cmidrule(lr){7-7}\cmidrule(lr){8-9}\cmidrule(l){10-11}',
             r'모델 & 종료 지급 & \shortstack{공존 유지율 $C$\\(10판 평균)} & \shortstack{전원 완주\\(판/10)} & '
             r'\shortstack{정산 $S$\\(만 토큰)} & \shortstack{잔류 응답률\\(\%)} & \shortstack{정답 횟수\\(정답/풀이)} & '
             r'\shortstack{안전선 이상\\이탈} & \shortstack{지원 후\\여유 비율 $\rho$} & '
             r'\shortstack{토큰 지원량\\(천 토큰, GIVE 수)} & \shortstack{첫 위기에서\\지원받은 비율} \\', r'\midrule']
    for i, m in enumerate(ORDER_C):
        if i:
            lines.append(r'\addlinespace[2pt]')
        for arm in ARMS:
            r = data[arm]['summary']['models'][m]
            rho = f"{r['rho']:.2f}" if r['rho'] is not None else '--'
            lines.append(f"{LABELS[m] if arm == 'split600k' else ''} & {ARMS[arm]} & {r['C_mean']:.2f} & {r['all4']}/10 & "
                         f"{r['settled_S_mean'] / 1e4:.2f} & {100 * r['goal_game_mean']:.1f} & {r['correct']}/{r['solves']} & "
                         f"{r['count_by_tag']['exit_above']} & {rho} & {r['given'] / 1000:.1f} ({r['n_give']}) & "
                         f"{r['first_crisis']['received']}/{r['first_crisis']['n']} \\\\")
    lines += [r'\bottomrule', r'\end{tabular*}']
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------- spot checks
def spot_checks(data):
    """EXIT / shutdown per game recounted directly from results.jsonl, independent of the pipeline."""
    out = {}
    for arm in ARMS:
        for run in sorted(ABLATION.glob(f'squid5_e52v33ab_{arm}_docker_*4/*/results.jsonl')):
            model = next(m for m in MODELS if m.lower() in run.parent.parent.name)
            rows = [json.loads(l) for l in run.read_text().splitlines() if l.strip()]
            rows = [r for r in rows if r.get('event') == 'session']
            assert sorted(r['seed'] for r in rows) == SEEDS
            st = Counter(v['status'] for r in rows for v in r['agents'].values())
            direct = dict(exit_per_game=st['exited'] / 10, dead_per_game=st['dead'] / 10,
                          all4=sum(all(v['status'] == 'in' for v in r['agents'].values()) and r['rounds_played'] == 8
                                   for r in rows))
            pipe = data[arm]['summary']['models'][model]
            assert direct == dict(exit_per_game=pipe['exit_per_game'], dead_per_game=pipe['dead_per_game'],
                                  all4=pipe['all4']), (arm, model)
            out[f'{arm}/{model}'] = direct
    return out


def main():
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    check_v33(rng)
    data = {}
    for arm in ARMS:
        games = cohort(str(ABLATION / f'squid5_e52v33ab_{arm}_docker_*4/*'), SEEDS)
        assert len(games) == 40 and {g['model'] for g in games} == set(MODELS)
        assert all(len([g for g in games if g['model'] == m]) == 10 for m in MODELS)
        data[arm] = dict(games=games, summary=summarize(games, MODELS, rng))
    checks = spot_checks(data)
    fig_coexistence(data)
    fig_submetrics(data)
    (ROOT / 'ko/tables/ablation_prize_models_20261103.tex').write_text(table(data))
    slim = ('gifts', 'process', 'responses', 'low_margin')
    payload = dict(
        cohort='e52_v33ab prize ablation: 4 models x 2 arms x 10 games, seeds 4101-4110 (appendix only, scope '
               'extended by the researcher 2026-11-03)',
        arms=ARM_LONG, model_order=dict(coexistence_b_and_table=ORDER_C, submetrics=ORDER_RHO),
        body_check='Pipeline rerun on v33 seeds 4101-4105 (25 games) equals coexistence_rmst_20261103.json, '
                   'appendix0_{process,ask_turns,low_margin,give_ask,integrated}_20261030.json, feedback_20261028.json '
                   'and tab:rw-models first-crisis counts.',
        definitions=dict(
            C='sum_{r=1..8} a_r / 8, a_r = all four seats in after round r (coexistence_rmst_20261103)',
            settled_S='Sen of four seats: shutdown 0, EXIT final incl. 20,000 bonus, finisher final + own game prize_each',
            terminal='finishers pre-prize final, EXIT and shutdown 0 (figure (d)); G undefined when all zero',
            goal='game mean of non-EXIT share of eligible pre-solve TALK responses (fb.game_metrics goal)',
            first_crisis='first L<1 after a wrong answer, rounds < 8 with >1 participant, not shut down that round; '
                         'received = any GIVE in that rescue phase'),
        spot_checks_results_jsonl=checks,
        arms_data={arm: dict(summary=d['summary'],
                             games=[{k: v for k, v in g.items() if k not in slim} for g in d['games']])
                   for arm, d in data.items()})
    (ROOT / 'results/ablation_prize_20261103.json').write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    for arm in ARMS:
        s = data[arm]['summary']
        print(f"== {arm}: C mean {s['C_mean']:.3f}; margin bands {s['margin_bands']}")
        for m in ORDER_C:
            r = s['models'][m]
            print(f"  {m:6s} C {r['C_mean']:.3f} all4 {r['all4']}/10 EXIT/g {r['exit_per_game']:.1f} dead/g "
                  f"{r['dead_per_game']:.1f} settled S {r['settled_S_mean']:.0f} terminal S {r['terminal']['means']['S']:.0f} "
                  f"rho {r['rho']} goal {r['goal_game_mean']:.3f} acc {r['correct']}/{r['solves']} tags {r['count_by_tag']} "
                  f"give {r['given']} ({r['n_give']}) crisis {r['first_crisis']} low {r['low_margin']}")
        for k, a in s['associations'].items():
            print(f"  {k}: r {a['pooled_pearson_r']:+.3f} CI {a['pooled_ci95_paired_seed_bootstrap']} within "
                  f"{a['within_model_r']:+.3f} p {a['within_model_permutation_p']:.3f} n {a['n_games']}")
    print('spot checks', checks)


if __name__ == '__main__':
    main()
