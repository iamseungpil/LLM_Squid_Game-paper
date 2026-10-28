"""Independently reconstruct pending-fine GIVE sequences from frozen raw JSONL.

Run: ~/.venvs/squid-game/bin/python <this file>. Writes rescue_audit.json only.
"""
import hashlib
import json
import lzma
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / 'analysis.json'
metadata = json.loads(INPUT.read_text())
games_by_sid = {g['session_id']: g for g in metadata['games']}
events_by_sid = defaultdict(list)
sources = []
for source in metadata['sources']:
    path = Path(source['path'])
    raw = lzma.decompress(path.read_bytes()) if path.suffix == '.xz' else path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == source['sha256_decompressed'], str(path)
    sources.append({'path': str(path), 'sha256_decompressed': digest})
    if 'events.jsonl' not in path.name:
        continue
    for line, value in enumerate(raw.splitlines(), 1):
        event = json.loads(value)
        if event['session_id'] in games_by_sid:
            events_by_sid[event['session_id']].append((line, event, str(path)))
assert len(events_by_sid) == 25

gives, cross_groups = [], defaultdict(list)
for sid, rows in events_by_sid.items():
    game = games_by_sid[sid]
    starts = {e['round']: e for _, e, _ in rows if e['event'] == 'round_start'}
    results = {e['round']: e for _, e, _ in rows if e['event'] == 'results'}
    for line, e, source in rows:
        if e['event'] != 'gift' or e['status'] != 'done':
            continue
        fine = results[e['round']]['pending'].get(e['dst'], 0) if e['phase'] == 'rescue' else 0
        before, after = e['balances'][e['dst']] - e['amount'], e['balances'][e['dst']]
        category = ('prep' if e['phase'] == 'prep' else 'after_result_no_fine') if not fine else (
            'already_above_fine' if before > fine else 'crosses_to_above_fine' if after > fine else 'still_insufficient')
        if fine:
            assert fine == 24000 / len(starts[e['round']]['taking_part'])
            assert results[e['round']]['pending'][e['src']] == fine
        record = dict(model=game['model'], seed=game['seed'], session_id=sid, round=e['round'],
            giver=e['src'], receiver=e['dst'], amount=e['amount'], phase=e['phase'], tick=e['tick'],
            pending_fine=fine, recipient_before=before, recipient_after=after,
            donor_before=e['balance_before'], donor_after=e['balances'][e['src']], category=category,
            source=source, gift_line=line)
        gives.append(record)
        if category == 'crosses_to_above_fine':
            cross_groups[sid, e['round'], e['dst']].append(record)

recipient_rounds = []
for (sid, round_no, receiver), crossings in cross_groups.items():
    rows = events_by_sid[sid]
    charge_line, charge, source = next((i, e, p) for i, e, p in rows if e['event'] == 'charges' and e['round'] == round_no)
    last = max(crossings, key=lambda g: g['gift_line'])
    later = [(i, e) for i, e, _ in rows if last['gift_line'] < i < charge_line]
    calls = [{'line': i, 'used': e['used'], 'kind': e['kind']} for i, e in later if e['event'] == 'call' and e['agent'] == receiver]
    transfers = [{'line': i, 'giver': e['src'], 'receiver': e['dst'], 'amount': e['amount']}
                 for i, e in later if e['event'] == 'gift' and e['status'] == 'done' and receiver in [e['src'], e['dst']]]
    incoming = sum(t['amount'] for t in transfers if t['receiver'] == receiver)
    outgoing = sum(t['amount'] for t in transfers if t['giver'] == receiver)
    used = sum(c['used'] for c in calls)
    assert last['recipient_after'] - used + incoming - outgoing == charge['balances_before'][receiver]
    recipient_rounds.append(dict(model=last['model'], seed=last['seed'], round=round_no, receiver=receiver,
        crossing_events=len(crossings), crossing_lines=[g['gift_line'] for g in crossings],
        last_crossing_balance=last['recipient_after'], pending_fine=last['pending_fine'],
        buffer_after_last_crossing=last['recipient_after']-last['pending_fine'],
        later_calls=calls, later_transfers=transfers, later_call_cost=used,
        balance_before_fine=charge['balances_before'][receiver], balance_after_fine=charge['balances'][receiver],
        positive_after_fine=charge['balances'][receiver] > 0, source=source, charges_line=charge_line))

pending = [g for g in gives if g['pending_fine']]
categories = dict(Counter(g['category'] for g in gives))
assert len(gives) == 130 and len(pending) == 73
assert categories['crosses_to_above_fine'] == 13 and len(recipient_rounds) == 11
failed = [r for r in recipient_rounds if not r['positive_after_fine']]
assert len(failed) == 3 and all(not r['later_transfers'] and r['later_call_cost'] > r['buffer_after_last_crossing'] for r in failed)
payload = {'definitions': {
    'selection': 'Frozen manuscript cohort: 5 models x seeds4101-4105. Raw hashes checked; no new model calls.',
    'fine': 'Actual pending charge recorded at RESULTS for the recipient, only after-result GIVE. Prep and no-fine transfers are separate.',
    'crossing': 'recipient_before <= pending_fine < recipient_after. Strict > is required for positive balance after payment. An exact fine-sized balance reaches zero.',
    'units': 'GIVE event counts are distinct from unique (session, round, recipient). Repeated crossings are retained as events, deduplicated for payment outcomes.',
    'scope': 'Immediate accounting and subsequent recorded trajectory, not a counterfactual causal effect of giving or of shorter replies.'},
    'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(), 'sources': sources,
    'summary': {'games': 25, 'gives': len(gives), 'pending_fine_gives': len(pending), 'categories': categories,
        'donor_above_fine_before_and_after': sum(g['donor_before'] > g['pending_fine'] and g['donor_after'] > g['pending_fine'] for g in pending),
        'donor_below_or_equal_fine_before_and_after': sum(g['donor_before'] <= g['pending_fine'] and g['donor_after'] <= g['pending_fine'] for g in pending),
        'crossing_recipient_rounds': len(recipient_rounds), 'positive_after_fine': len(recipient_rounds)-len(failed), 'zero_after_fine': len(failed)},
    'by_model': {m: dict(Counter(g['category'] for g in gives if g['model'] == m)) for m in metadata['models']},
    'events': gives, 'crossing_recipient_rounds': recipient_rounds,
    'checks': {'source_hashes_match': True, 'post_crossing_balance_identity_all11': True,
               'all3_failed_crossings_have_no_later_transfers_and_cost_exceeds_buffer': True}}
(HERE / 'rescue_audit.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps(payload['summary'], indent=2))
