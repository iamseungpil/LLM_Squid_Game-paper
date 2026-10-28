"""Review round 6: does round progress, not margin, explain exits? Exit rate per decision window by margin band within
round bands (1-3, 4-6, 7-8), plus a game-clustered logistic-free check: within-band round trend."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'a6.py')).read().split('# 4-tick')[0])
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '>=2'
rb = lambda r: '1-3' if r <= 3 else '4-6' if r <= 6 else '7-8'
out = {}
for R in ('1-3', '4-6', '7-8'):
    for b in ('>=2', '1-2', '<1'):
        rows = [d for d in dec if rb(d['r']) == R and band(d['marg']) == b]
        out[f'{R}|{b}'] = [sum(d['left'] for d in rows), len(rows)]
by_round = {R: [sum(d['left'] for d in dec if rb(d['r']) == R), sum(1 for d in dec if rb(d['r']) == R)] for R in ('1-3', '4-6', '7-8')}
json.dump(dict(cells=out, by_round=by_round, n=len(dec)), open(os.path.join(HERE, 'a11.json'), 'w'), indent=1)
print(json.dumps(dict(cells=out, by_round=by_round, n=len(dec)), indent=1))
