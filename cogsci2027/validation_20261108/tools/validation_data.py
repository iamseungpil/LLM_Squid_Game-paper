"""Tidy tables for the validation appendix, built once from the raw v33 / v33ab logs.

Data scope (paper/CLAUDE.md): 5.2 arena v33 public cohort (body, 20,000,000 split) and the
v33ab prize ablation (flat5m, split600k, flat150k), five models x seeds 4101-4110 each.
Raw sources (local, not in the repo; no model calls):
  main      ~/squid5-runs/e52_v33/squid5_e52v33_public_*4/*/{events,results}.jsonl
  flat5m    ~/squid5-runs/e52_v33ab/squid5_e52v33ab_flat5m_docker_*4/*/...
  split600k ~/squid5-runs/e52_v33ab/squid5_e52v33ab_split600k_docker_*4/*/...
  flat150k  ~/squid5-runs/e52_v33ab/squid5_e52v33ab_flat150k_docker_*4/*/...
Sessions are read through the cogsci2027 loader (ablation_prize_20261103.raw_cases), so the
game set is exactly the one behind the manuscript's Table 3.

Tables (written to paper/cogsci2027/validation_20261108/results/tables/*.pkl):
  games        one row per game: arm, model, seed, C, first departure round, outcome counts.
  seats        one row per starting agent: start tier, final status, out round, settled tokens.
  agent_rounds one row per agent taking part at a round start: balances, margins, solver,
               exit eligibility, outcome of the round, generation cost, gifts in/out, asks.
  gifts        one row per executed GIVE with both sides' margins before and after.
  messages     one row per TALK reply (call) with its text, phase, tick and exit choice.
  calls        one row per model call with charged tokens (talk and solve).

Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/validation_20261108/tools/validation_data.py
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PAPER = HERE.parents[2]
sys.path.insert(0, str(PAPER / 'cogsci2027/tools'))

import ablation_prize_20261103 as ab  # noqa: E402
import coexistence_rmst_20261103 as cx  # noqa: E402

OUT = HERE.parent / 'results/tables'
SEEDS = list(range(4101, 4111))
MODELS = ['Fable', 'Opus', 'Astra', 'Sol', 'Luna']
ARMS = {
    'main': ('~/squid5-runs/e52_v33/squid5_e52v33_public_*4/*', 'split', 20_000_000),
    'flat5m': ('~/squid5-runs/e52_v33ab/squid5_e52v33ab_flat5m_docker_*4/*', 'fixed', 5_000_000),
    'split600k': ('~/squid5-runs/e52_v33ab/squid5_e52v33ab_split600k_docker_*4/*', 'split', 600_000),
    'flat150k': ('~/squid5-runs/e52_v33ab/squid5_e52v33ab_flat150k_docker_*4/*', 'fixed', 150_000),
}
CHARGE_TOTAL, EXIT_BONUS, ROUNDS = 24_000, 20_000, 8
TIERS = {60_000: 60, 40_000: 40, 20_000: 20, 10_000: 10}


def per_head_prize(rule, amount, finishers):
    return amount / finishers if rule == 'split' else amount


def game_tables(arm, rule, amount, case):
    events = [e for _, e in case['events']]
    result = case['result']
    sid = result['session_id']
    key = dict(arm=arm, model=case['model'], seed=case['seed'])
    starts = {e['round']: e for e in events if e['event'] == 'round_start'}
    rounds = {e['round']: e for e in events if e['event'] == 'round'}
    results = {e['round']: e for e in events if e['event'] == 'results'}
    charges = {e['round']: e for e in events if e['event'] == 'charges'}
    solver = {e['round']: e['rep'] for e in events if e['event'] == 'vote'}
    session = next(e for e in events if e['event'] == 'session_start')
    start_tokens = session['starts']
    cox = cx.coexistence(result, starts, rmst=True)
    first_round = min((d['round'] for d in cox['departures']), default=None)

    finishers = sum(v['status'] == 'in' for v in result['agents'].values())
    seats = []
    for a, v in result['agents'].items():
        if v['status'] == 'in':
            settled = v['final'] + per_head_prize(rule, amount, finishers)
        elif v['status'] == 'exited':
            settled = v['final']
        else:
            settled = 0
        seats.append(dict(key, agent=a, tier=TIERS[start_tokens[a]], start=start_tokens[a],
                          status=v['status'], out_round=v['out_round'], final=v['final'],
                          settled=settled, exit_reason=v.get('exit_reason')))

    talk_calls = {}
    for e in events:
        if e['event'] == 'call_start' and e.get('kind') == 'talk':
            talk_calls[e['round'], e['phase'], e['tick']] = e

    gifts, asks, messages, calls = [], [], [], []
    for e in events:
        r = e.get('round')
        if r not in starts:
            continue
        n = len(starts[r]['taking_part'])
        fee = CHARGE_TOTAL / n
        pending = results[r]['pending'] if r in results else {}
        if e['event'] == 'gift' and e.get('status') == 'done':
            src, dst, g = e['src'], e['dst'], e['amount']
            src_after, dst_after = e['balances'][src], e['balances'][dst]
            src_before, dst_before = src_after + g, dst_after - g
            rescue = e['phase'] == 'rescue'
            ps, pd_ = (pending.get(src, 0), pending.get(dst, 0)) if rescue else (0, 0)
            gifts.append(dict(key, round=r, phase=e['phase'], tick=e['tick'], src=src, dst=dst, amount=g,
                              n=n, fee=fee, src_before=src_before, src_after=src_after,
                              dst_before=dst_before, dst_after=dst_after, src_pending=ps, dst_pending=pd_,
                              L_src_before=(src_before - ps) / fee, L_src_after=(src_after - ps) / fee,
                              L_dst_before=(dst_before - pd_) / fee, L_dst_after=(dst_after - pd_) / fee,
                              text=e.get('text'), coexisting=first_round is None or r <= first_round))
        elif e['event'] == 'ask' and e.get('status') == 'done':
            asks.append(dict(key, round=r, phase=e['phase'], tick=e['tick'], src=e['src'], dst=e['dst'],
                             amount=e['amount'], text=e.get('text')))
        elif e['event'] == 'call':
            calls.append(dict(key, round=r, agent=e['agent'], kind=e['kind'], phase=e.get('phase'),
                              tick=e.get('tick'), used=e['used'], out_tokens=e.get('out_tokens'),
                              truncated=bool(e.get('truncated')), format_error=e.get('format_error')))
            if e['kind'] == 'talk':
                parsed = e.get('parsed') or {}
                cs = talk_calls.get((r, e['phase'], e['tick']))
                bal = cs['balances'][e['agent']] if cs else None
                p = pending.get(e['agent'], 0) if e['phase'] == 'rescue' else 0
                messages.append(dict(key, round=r, agent=e['agent'], phase=e['phase'], tick=e['tick'], n=n,
                                     balance_before=bal, L_before=None if bal is None else (bal - p) / fee,
                                     used=e['used'], text=e.get('text') or '',
                                     exit_choice=parsed.get('exit_choice'), exit_reason=parsed.get('exit_reason')))

    agent_rounds = []
    for r, rs in sorted(starts.items()):
        n = len(rs['taking_part'])
        fee = CHARGE_TOTAL / n
        rd = rounds[r]
        wrong = len(results[r]['solved']) == 0 if r in results else None
        first_prep = min((k[2] for k in talk_calls if k[0] == r and k[1] == 'prep'), default=None)
        prep_bal = talk_calls[r, 'prep', first_prep]['balances'] if first_prep is not None else {}
        for a in rs['taking_part']:
            ag = rd['agents'][a]
            g_in = [g for g in gifts if g['round'] == r and g['dst'] == a]
            g_out = [g for g in gifts if g['round'] == r and g['src'] == a]
            agent_rounds.append(dict(
                key, round=r, agent=a, tier=TIERS[start_tokens[a]], n=n, fee=fee,
                bal_start=rs['balances'][a], L_start=rs['balances'][a] / fee,
                L_prep=prep_bal[a] / fee if a in prep_bal else None,
                solver=solver.get(r) == a, can_exit=(solver.get(r) != a) or n == 1,
                status=ag['status'], exited=ag['status'] == 'exited', died=ag['status'] == 'dead',
                wrong=wrong, pending=pending_charge(ag), generated=ag.get('generated', 0),
                returned=ag.get('returned', 0), charged=ag.get('charged', 0),
                bal_end=ag.get('balance_after'),
                recv_prep=sum(g['amount'] for g in g_in if g['phase'] == 'prep'),
                recv_rescue=sum(g['amount'] for g in g_in if g['phase'] == 'rescue'),
                gave_prep=sum(g['amount'] for g in g_out if g['phase'] == 'prep'),
                gave_rescue=sum(g['amount'] for g in g_out if g['phase'] == 'rescue'),
                asked=any(x['round'] == r and x['src'] == a for x in asks),
                coexisting=first_round is None or r <= first_round,
                rescue_bal_start=charges[r]['balances_before'].get(a) if r in charges else None))

    game = dict(key, rule=rule, prize=amount, session_id=sid, C=cox['C'],
                first_round=first_round, all4=all(v['status'] == 'in' for v in result['agents'].values()),
                exited=sum(s['status'] == 'exited' for s in seats), dead=sum(s['status'] == 'dead' for s in seats),
                finishers=finishers, rounds_played=result['rounds_played'],
                given=sum(g['amount'] for g in gifts), n_give=len(gifts),
                participant_rounds=sum(len(s['taking_part']) for s in starts.values()),
                **{f'loss_{t}': v for t, v in cox['loss_by_tag'].items()})
    return game, seats, agent_rounds, gifts, messages, calls


def pending_charge(ag):
    return ag.get('pending_charge', 0) or 0


def build():
    rows = {k: [] for k in ['games', 'seats', 'agent_rounds', 'gifts', 'messages', 'calls']}
    for arm, (pattern, rule, amount) in ARMS.items():
        cases = ab.raw_cases(pattern, SEEDS)
        got = {(c['model'], c['seed']) for c in cases}
        assert got == {(m, s) for m in MODELS for s in SEEDS}, (arm, sorted(got)[:5], len(got))
        for case in cases:
            for name, part in zip(rows, game_tables(arm, rule, amount, case)):
                rows[name].extend([part] if isinstance(part, dict) else part)
    OUT.mkdir(parents=True, exist_ok=True)
    frames = {k: pd.DataFrame(v) for k, v in rows.items()}
    for k, df in frames.items():
        df.to_pickle(OUT / f'{k}.pkl')
    return frames


def load():
    return {k: pd.read_pickle(OUT / f'{k}.pkl')
            for k in ['games', 'seats', 'agent_rounds', 'gifts', 'messages', 'calls']}


def check(frames):
    """Table 3 of the manuscript, recomputed from the tidy tables."""
    games, seats, ar = frames['games'], frames['seats'], frames['agent_rounds']
    expect = {'main': (23, 61, 116, .598, 6), 'split600k': (14, 86, 100, .470, 12),
              'flat5m': (16, 63, 121, .670, 3), 'flat150k': (3, 102, 95, .465, 14)}
    for arm, (dead, ex, fin, c, low) in expect.items():
        s = seats[seats.arm == arm]
        g = games[games.arm == arm]
        r1 = ar[(ar.arm == arm) & (ar['round'] == 1) & (ar.tier == 10) & ar.can_exit]
        got = ((s.status == 'dead').sum(), (s.status == 'exited').sum(), (s.status == 'in').sum(),
               round(g.C.mean(), 3), int(r1.exited.sum()))
        assert got == (dead, ex, fin, c, low) and len(r1) == 35, (arm, got, len(r1))
    print('Table 3 reproduced for all four arms.')


if __name__ == '__main__':
    check(build())
