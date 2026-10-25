"""Build agent-round panel from the raw v33 arena logs (hashes match arena_v33.json sources)."""
import json, glob, os, collections
R = os.path.join(os.path.dirname(__file__), '..', 'raw')
MODEL = {'astra': 'GPT-6 Astra', 'sol': 'GPT-6 Sol', 'luna': 'GPT-6 Luna', 'opus': 'Opus 5.5', 'fable': 'Fable 5.1'}
def model_of(d):
    for k, v in MODEL.items():
        if k in d: return v
rows = []; calls = []
for f in sorted(glob.glob(os.path.join(R, '*', 'events.jsonl'))):
    m = model_of(f); S = collections.defaultdict(dict)
    for l in open(f):
        e = json.loads(l); ev = e['event']; s = e.get('session_id'); g = S[s]
        if ev == 'session_start': g['seed'] = e['seed']; g['start'] = e['starts']; g['rounds'] = {}
        elif ev == 'round_start':
            g['rounds'][e['round']] = dict(part=e['taking_part'], bal0=e['balances'], gifts=[], asks=[], rescue_start=None, prep_start=None, msgs=[])
        elif ev == 'call_start' and e.get('kind') == 'talk':
            rr = g['rounds'][e['round']]; key = 'prep_start' if e.get('phase') == 'prep' else 'rescue_start'
            if rr[key] is None: rr[key] = e['balances']
            rr.setdefault('cs', []).append(e)
        elif ev == 'results':
            rr = g['rounds'][e['round']]; rr['solver'] = (e['tried'] or [None])[0]; rr['wrong'] = bool(e['tried']) and not e['solved']
        elif ev in ('gift', 'ask'): g['rounds'][e['round']]['gifts' if ev == 'gift' else 'asks'].append(e)
        elif ev == 'room_msg': g['rounds'][e['round']]['msgs'].append(e)
        elif ev == 'call' and e.get('kind') == 'talk':
            calls.append(dict(m=m, s=s, r=e['round'], a=e['agent'], phase=e.get('phase'), tick=e.get('tick'), exit=bool((e.get('parsed') or {}).get('exit')), text=e.get('text', '')))
        elif ev == 'round': g['rounds'][e['round']]['agents'] = e['agents']
    for s, g in S.items():
        rounds = g['rounds']; last = max(rounds)
        for r, rr in sorted(rounds.items()):
            n = len(rr['part']); F = 24000 / n
            for a in rr['part']:
                ag = rr['agents'][a]
                rec_res = sum(x['amount'] for x in rr['gifts'] if x['dst'] == a and x['phase'] == 'rescue' and x['status'] == 'done')
                rec_prep = sum(x['amount'] for x in rr['gifts'] if x['dst'] == a and x['phase'] == 'prep' and x['status'] == 'done')
                gave_res = sum(x['amount'] for x in rr['gifts'] if x['src'] == a and x['phase'] == 'rescue' and x['status'] == 'done')
                b_res = (rr['rescue_start'] or {}).get(a)
                eff_res = None if b_res is None else b_res / F - (1 if rr.get('wrong') else 0)
                eff_after = None if b_res is None else (b_res + rec_res - gave_res) / F - (1 if rr.get('wrong') else 0)
                nxt = rounds.get(r + 1); nxt_status = None; nxt_n = None
                if nxt and a in nxt['part']: nxt_status = nxt['agents'][a]['status']; nxt_n = len(nxt['part'])
                rows.append(dict(m=m, s=s, seed=g['seed'], r=r, a=a, n=n, F=F, start=g['start'][a], bal0=rr['bal0'][a], marg0=rr['bal0'][a] / F,
                    solver=rr.get('solver') == a, wrong=rr.get('wrong'), b_res=b_res, eff_res=eff_res, eff_after=eff_after, rec_res=rec_res, rec_prep=rec_prep,
                    gave_res=gave_res, status=ag['status'], exit_flag=ag.get('exit'), nxt_status=nxt_status, nxt_n=nxt_n, last=(r == last),
                    asked_res=any(x['src'] == a and x['phase'] == 'rescue' for x in rr['asks']),
                    said_digits_res=any(x['src'] == a and x['phase'] == 'rescue' and any(ch.isdigit() for ch in (x.get('text') or '')) for x in rr['msgs'])))
json.dump(rows, open(os.path.join(os.path.dirname(__file__), 'panel.json'), 'w'))
json.dump(calls, open(os.path.join(os.path.dirname(__file__), 'calls.json'), 'w'))
print(len(rows), 'agent-rounds;', len(calls), 'talk calls;', len({r['s'] for r in rows}), 'games')
st = collections.Counter(r['status'] for r in rows); print(st)
