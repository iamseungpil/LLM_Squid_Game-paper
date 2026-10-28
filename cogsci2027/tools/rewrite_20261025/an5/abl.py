"""v33 (8 ticks) vs v34 (4 ticks), Opus and Sol, seeds 4101-4105: exit per decision window and per reply, by margin band."""
import json, lzma, glob, collections, os
R = '/home/user/LLM-Squid-Game/web/data/runs'
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '2-4' if x < 4 else '>=4'
def windows(path):
    ev = [json.loads(l) for f in glob.glob(path + '/*/events.jsonl.xz') for l in lzma.open(f, 'rt')]
    seeds = {e['session_id']: e['seed'] for e in ev if e['event'] == 'session_start'}
    part = {(e['session_id'], e['round']): e['taking_part'] for e in ev if e['event'] == 'round_start'}
    solver = {(e['session_id'], e['round']): (e.get('tried') or [None])[0] for e in ev if e['event'] == 'results'}
    calls = collections.defaultdict(list)
    for e in ev:
        if e['event'] == 'call' and e.get('kind') == 'talk' and e.get('phase') == 'prep' and seeds.get(e['session_id'], 0) <= 4105:
            calls[(e['session_id'], e['round'], e['agent'])].append(e)
    W = []
    for (sid, r, a), cs in calls.items():
        tp = part.get((sid, r), []); alone = len(tp) == 1
        if a == solver.get((sid, r)) and not alone: continue
        F = 24000 / max(1, len(tp))
        W.append(dict(marg=(cs[0]['balance_after'] + cs[0]['used']) / F, replies=len(cs),
                      left=any((c.get('parsed') or {}).get('exit') for c in cs)))
    return W
out = {}
for m, tag in (('Opus', 'opus4'), ('Sol', 'sol4')):
    for v in ('33', '34'):
        W = windows(f'{R}/e52_v{v}/squid5_e52v{v}_public_{tag}')
        bb = {}
        for b in ('<1', '1-2', '2-4', '>=4'):
            w = [x for x in W if band(x['marg']) == b]
            bb[b] = dict(windows=len(w), left=sum(x['left'] for x in w))
        out[f'{m}|v{v}'] = dict(windows=len(W), left=sum(x['left'] for x in W), replies=sum(x['replies'] for x in W),
                               per_window=round(sum(x['left'] for x in W) / len(W), 3), per_reply=round(sum(x['left'] for x in W) / sum(x['replies'] for x in W), 4),
                               replies_per_window=round(sum(x['replies'] for x in W) / len(W), 2), by_band=bb)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'abl.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
