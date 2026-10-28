"""Review round 4: Wilson intervals for exit rates by margin, the same without Luna and per model, and a rough count of seats
that would have finished had no one left (stayers' finish rate in the same margin band)."""
import json, os, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'a6.py')).read().split('# 4-tick')[0])
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '>=2'
def wilson(k, n, z=1.96):
    if n == 0: return None
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]
def table(rows):
    t = {}
    for b in ('>=2', '1-2', '<1'):
        r = [d for d in rows if band(d['marg']) == b]; k = sum(d['left'] for d in r)
        t[b] = dict(left=k, n=len(r), rate=round(k / len(r), 3) if r else None, ci=wilson(k, len(r)))
    return t
out = dict(all=table(dec), without_luna=table([d for d in dec if d['m'] != 'Luna']),
           per_model={m: table([d for d in dec if d['m'] == m]) for m in ['Luna', 'Astra', 'Opus', 'Fable', 'Sol']})
stay_rate = {b: sum(d['fin'] for d in dec if not d['left'] and band(d['marg']) == b) / max(1, sum(1 for d in dec if not d['left'] and band(d['marg']) == b)) for b in ('>=2', '1-2', '<1')}
out['stay_finish_rate'] = {b: round(v, 3) for b, v in stay_rate.items()}
out['would_have_finished_if_stayed'] = round(sum(stay_rate[band(e['marg_before'])] for e in exits), 1)
out['would_have_finished_split'] = {b: round(sum(stay_rate[band(e['marg_before'])] for e in exits if band(e['marg_before']) == b), 1) for b in ('>=2', '1-2', '<1')}
json.dump(out, open(os.path.join(HERE, 'a8.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'per_model'}, indent=1))
for m, t in out['per_model'].items(): print(m, {b: (x['left'], x['n']) for b, x in t.items()})
