"""Appendix 0: descriptive coexistence processes in the fixed 25-game e52_v33 cohort.

Read raw_case_index.json and verify every indexed event against its original v33
events.jsonl.xz. No other experiment, imputed motive or fitted causal effect.
First crises are measured at the first post-result TALK call, with confirmed
pending fines deducted. Follow-up includes deaths during the crisis round. Exclude
round 8 and round-start singleton games, before comparing later outcomes.
The game comparison fixes exposure at its first eligible crisis, conditional on
all four agents still being present at that opening post-result TALK call.
"""
import hashlib
import json
import lzma
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/raw_case_index.json'


def band(value):
    return 0 if value < 1 else 1 if value < 2 else 2 if value < 4 else 3


def analyze():
    cases = json.loads(SOURCE.read_text())
    assert len(cases) == 25
    assert len({(c['model'], c['seed']) for c in cases}) == 25
    assert set(c['seed'] for c in cases) == set(range(4101, 4106))
    assert set(Counter(c['model'] for c in cases).values()) == {5}
    cache, hashes = {}, {}
    windows, responses, solves, gifts, crises, games = [], [], [], [], [], []
    for c in cases:
        path = Path(c['source'])
        assert 'e52_v33' in path.parts
        if str(path) not in cache:
            raw = lzma.open(path, 'rt').read() if path.suffix == '.xz' else path.read_text()
            cache[str(path)] = [json.loads(line) for line in raw.splitlines()]
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        for line, event in c['events']:
            assert cache[str(path)][line - 1] == event
        events = [e for _, e in c['events']]
        result = c['result']
        result_path = path.with_name('results.jsonl')
        result_rows = [json.loads(line) for line in result_path.read_text().splitlines()]
        assert result in result_rows
        hashes[str(result_path)] = hashlib.sha256(result_path.read_bytes()).hexdigest()
        sid = result['session_id']
        base = dict(model=c['model'], seed=c['seed'], session=sid)
        final = {a: v['status'] for a, v in result['agents'].items()}
        all_four = all(v == 'in' for v in final.values())
        games.append(dict(base, all_four=all_four, finished=sum(v == 'in' for v in final.values())))
        starts = {e['round']: e for e in events if e['event'] == 'round_start'}
        results = {e['round']: e for e in events if e['event'] == 'results'}
        charges = {e['round']: e for e in events if e['event'] == 'charges'}
        rounds = {e['round']: e for e in events if e['event'] == 'round'}
        solver = {e['round']: e['rep'] for e in events if e['event'] == 'vote'}
        calls = {(e['round'], e.get('phase'), e.get('tick')): e for e in events
                 if e['event'] == 'call_start' and e.get('kind') == 'talk'}
        giving = {(e['round'], e['phase'], e['tick'], e['src']) for e in events
                  if e['event'] == 'gift' and e.get('status') == 'done'}
        local_windows, first = {}, {}
        for e in events:
            r = e.get('round')
            if r not in starts:
                continue
            n = len(starts[r]['taking_part'])
            fee = 24000 / n
            pending = results[r]['pending']
            if e['event'] == 'call' and e.get('kind') == 'talk':
                a, phase, tick = e['agent'], e['phase'], e['tick']
                call = calls[r, phase, tick]
                margin = call['balances'][a] / fee - (pending.get(a, 0) / fee if phase == 'rescue' else 0)
                responses.append(dict(base, round=r, agent=a, margin=margin, band=band(margin),
                                      gave=(r, phase, tick, a) in giving))
                if phase == 'prep' and (a != solver.get(r) or n == 1):
                    row = local_windows.setdefault((r, a), dict(base, round=r, agent=a,
                        margin=margin, band=band(margin), exited=False))
                    row['exited'] |= bool((e.get('parsed') or {}).get('exit'))
            if e['event'] == 'call_start' and e.get('kind') == 'solve' and e['agents']:
                a = e['agents'][0]
                margin = e['balances'][a] / fee
                solves.append(dict(base, round=r, agent=a, band=band(margin),
                                   correct=a in results[r]['solved'],
                                   picked_top=rounds[r]['agents'][a]['picked_top']))
            if e['event'] == 'gift' and e.get('status') == 'done':
                src, dst, amount = e['src'], e['dst'], e['amount']
                ds = pending.get(src, 0) / fee if e['phase'] == 'rescue' else 0
                dd = pending.get(dst, 0) / fee if e['phase'] == 'rescue' else 0
                gifts.append(dict(base, round=r, src=src, dst=dst, phase=e['phase'], amount=amount,
                    giver_before=e['balance_before'] / fee - ds,
                    giver_after=e['balances'][src] / fee - ds,
                    receiver_before=(e['balances'][dst] - amount) / fee - dd,
                    receiver_after=e['balances'][dst] / fee - dd,
                    giver_finished=final[src] == 'in', receiver_finished=final[dst] == 'in', all_four=all_four))
            if e['event'] == 'call_start' and e.get('kind') == 'talk' and e.get('phase') == 'rescue':
                for a in e['agents']:
                    margin = e['balances'][a] / fee - pending.get(a, 0) / fee
                    if a in first or not pending.get(a) or margin >= 1:
                        continue
                    # Only the opening call of this phase defines the crisis.
                    opening = min(k[2] for k in calls if k[:2] == (r, 'rescue'))
                    if e['tick'] != opening:
                        continue
                    transfers = [g for g in events if g['event'] == 'gift' and g.get('status') == 'done'
                                 and g['round'] == r and g['phase'] == 'rescue']
                    received = sum(g['amount'] for g in transfers if g['dst'] == a)
                    given = sum(g['amount'] for g in transfers if g['src'] == a)
                    donors = sorted({g['src'] for g in transfers if g['dst'] == a})
                    after = (charges[r]['balances_before'].get(a, 0) - pending[a]) / fee
                    legacy = margin + (received - given) / fee
                    group = 'none' if not received else 'lifted' if after >= 1 else 'short'
                    row = dict(base, round=r, agent=a, n=n, present=len(e['agents']), before=margin, after=after,
                        legacy_after=legacy, received=received, given=given, group=group,
                        legacy_group='none' if not received else 'lifted' if legacy >= 1 else 'short',
                        status=final[a], immediate_dead=rounds[r]['agents'][a]['status'] == 'dead',
                        donors=donors, all_donors_finished=bool(donors) and all(final[d] == 'in' for d in donors),
                        all_four=all_four, eligible=r < 8 and n > 1)
                    first[a] = row
        windows.extend(local_windows.values())
        crises.extend(first.values())
    assert len(windows) == 491 and sum(x['exited'] for x in windows) == 34
    assert len(responses) == 2909 and len(solves) == 192
    assert sum(x['correct'] for x in solves) == 133
    assert len(gifts) == 130 and sum(x['amount'] for x in gifts) == 383276
    assert sum(x['all_four'] for x in games) == 8
    eligible = [x for x in crises if x['eligible']]
    grouped = {}
    for group in ['none', 'short', 'lifted']:
        rows = [x for x in eligible if x['group'] == group]
        grouped[group] = dict(n=len(rows), games=len({x['session'] for x in rows}),
            **{s: sum(x['status'] == s for x in rows) for s in ['in', 'exited', 'dead']},
            joint_donors=sum(x['status'] == 'in' and x['all_donors_finished'] for x in rows),
            all_four=sum(x['all_four'] for x in rows))
    for game in games:
        rows = [x for x in eligible if x['session'] == game['session']]
        game['crises'] = len(rows)
        first_round = min((x['round'] for x in rows), default=None)
        first_rows = [x for x in rows if x['round'] == first_round]
        game['first_crisis_round'] = first_round
        game['landmark_eligible'] = bool(first_rows) and first_rows[0]['present'] == 4
        game['coverage'] = None
        if game['landmark_eligible']:
            game['coverage'] = 'all_lifted' if all(x['group'] == 'lifted' for x in first_rows) else 'gap'
    summary = dict(crisis_total=len(crises), eligible=len(eligible), groups=grouped,
        group_changes=sum(x['group'] != x['legacy_group'] for x in eligible),
        gifts_safe_before=sum(x['giver_before'] >= 1 for x in gifts),
        gifts_safe_both=sum(x['giver_before'] >= 1 and x['giver_after'] >= 1 for x in gifts),
        needy_gifts=sum(x['receiver_before'] < 1 for x in gifts),
        both_safe_lifts=sum(x['receiver_before'] < 1 <= x['receiver_after'] and x['giver_after'] >= 1 for x in gifts),
        game_coverage={g: dict(n=sum(x['coverage'] == g for x in games),
                              all_four=sum(x['coverage'] == g and x['all_four'] for x in games))
                       for g in ['all_lifted', 'gap']},
        landmark_games=sum(x['landmark_eligible'] for x in games),
        no_eligible_crisis=sum(x['first_crisis_round'] is None for x in games),
        prior_attrition=sum(x['first_crisis_round'] is not None and not x['landmark_eligible'] for x in games))
    out = dict(source=str(SOURCE.relative_to(ROOT)), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        raw_sources=hashes, summary=summary, windows=windows, responses=responses, solves=solves,
        gifts=gifts, crises=crises, games=games)
    (ROOT / 'results/appendix0_process_20261030.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    analyze()
