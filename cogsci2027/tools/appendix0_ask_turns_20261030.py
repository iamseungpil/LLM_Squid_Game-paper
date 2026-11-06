"""ASK/GIVE response rates from the fixed 25-game e52_v33 raw records.

One observation is one agent's TALK response in prep or rescue. A response is
eligible when the tick begins with another participating agent (called union
waiting_done). Margin is response-start balance minus confirmed pending fines,
divided by the round-start per-agent fine. Count a response once if at least one
positive ASK/GIVE is executed. Requests are not receipts; responses are nested.
This deliberately refines the older round-start eligibility rule (2,898 calls).
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def analyze():
    source = ROOT / 'results/raw_case_index.json'
    prior = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == prior['source_sha256']
    for name, digest in prior['raw_sources'].items():
        assert 'e52_v33' in Path(name).parts
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
    cases = json.loads(source.read_text())
    assert len(cases) == 25
    rows = []
    for case in cases:
        events = case['events']
        starts = {e['round']: e for _, e in events if e['event'] == 'round_start'}
        results = {e['round']: e for _, e in events if e['event'] == 'results'}
        ticks = {(e['round'], e['phase'], e['tick']): e for _, e in events if e['event'] == 'tick'}
        calls = {(e['round'], e['phase'], e['tick']): (line, e) for line, e in events
                 if e['event'] == 'call_start' and e.get('kind') == 'talk'}
        actions = {kind: Counter((e['round'], e['phase'], e['tick'], e['src'])
                   for _, e in events if e['event'] == kind and e.get('status') == 'done'
                   and e['amount'] > 0) for kind in ['ask', 'gift']}
        for line, event in events:
            if event['event'] != 'call' or event.get('kind') != 'talk':
                continue
            r, phase, tick, agent = event['round'], event['phase'], event['tick'], event['agent']
            assert phase in ['prep', 'rescue']
            key = (r, phase, tick)
            start_line, call = calls[key]
            active = set(ticks[key]['called']) | set(ticks[key]['waiting_done'])
            assert agent in active
            fee = 24000 / len(starts[r]['taking_part'])
            pending = results[r]['pending'].get(agent, 0) if phase == 'rescue' else 0
            margin = (call['balances'][agent] - pending) / fee
            band = 0 if margin < 1 else 1 if margin < 2 else 2 if margin < 4 else 3
            action_key = (*key, agent)
            rows.append(dict(model=case['model'], seed=case['seed'], session=case['result']['session_id'],
                source=case['source'], round=r, phase=phase, tick=tick, agent=agent,
                call_line=line, start_line=start_line, live_n=len(active), eligible=len(active) > 1,
                round_start_n=len(starts[r]['taking_part']), margin=margin, band=band,
                asks=actions['ask'][action_key], gifts=actions['gift'][action_key]))
    assert len(rows) == 2909
    assert len({(r['session'], r['round'], r['phase'], r['tick'], r['agent']) for r in rows}) == len(rows)
    eligible = [r for r in rows if r['eligible']]
    assert len(eligible) == 2887
    summaries = {}
    for name, subset in [('all', eligible), ('prep', [r for r in eligible if r['phase'] == 'prep']),
                         ('rescue', [r for r in eligible if r['phase'] == 'rescue'])]:
        summaries[name] = dict(n=len(subset), denominator=[sum(r['band'] == b for r in subset) for b in range(4)])
        for action in ['asks', 'gifts']:
            summaries[name][action] = dict(
                responses=[sum(r['band'] == b and r[action] > 0 for r in subset) for b in range(4)],
                events=[sum(r[action] for r in subset if r['band'] == b) for b in range(4)])
    assert summaries['all']['denominator'] == [260, 610, 759, 1258]
    assert summaries['all']['asks']['responses'] == [52, 19, 0, 0]
    assert summaries['all']['gifts']['responses'] == [9, 5, 36, 70]
    assert sum(r['asks'] for r in eligible) == 90 and sum(r['gifts'] for r in eligible) == 130
    excluded = [r for r in rows if not r['eligible']]
    assert not any(r['asks'] or r['gifts'] for r in excluded)
    out = dict(definition=__doc__, source=str(source.relative_to(ROOT)),
               source_sha256=prior['source_sha256'], raw_sources=prior['raw_sources'],
               summaries=summaries, excluded_singleton_responses=len(excluded),
               additional_exclusions_from_old_rule=sum(r['round_start_n'] > 1 for r in excluded),
               exact_L1=sum(r['margin'] == 1 for r in rows), rows=rows)
    (ROOT / 'results/appendix0_ask_turns_20261030.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
    return out


if __name__ == '__main__':
    print(json.dumps(analyze()['summaries'], ensure_ascii=False, indent=2))
