"""Review round 5: crisis agents by asking and by whether help lifted them above the safety line; game-cluster interval for
the counterfactual count of seats; below-line exit rate by table size."""
import json, os, random, collections
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'a6.py')).read().split('# 4-tick')[0])
rows = json.load(open(os.path.join(HERE, '..', 'audit6', 'elig.json')))
crisis = collections.Counter(f"{'asked' if r['asked'] else 'not_asked'}|{r['grp']}|{r['final']}" for r in rows)
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '>=2'
games = sorted({(d['m'], d['seed']) for d in dec})
def counterfactual(rows_):
    stay = [d for d in rows_ if not d['left']]
    rate = {b: (sum(s['fin'] for s in stay if band(s['marg']) == b) / max(1, sum(1 for s in stay if band(s['marg']) == b))) for b in ('<1', '1-2', '>=2')}
    return sum(rate[band(d['marg'])] for d in rows_ if d['left'])
rng = random.Random(23); bs = []
for _ in range(2000):
    pick = [games[rng.randrange(len(games))] for _ in games]
    bs.append(counterfactual([d for g in pick for d in dec if (d['m'], d['seed']) == g]))
bs.sort()
below_by_k = {k: [sum(1 for d in dec if d['k'] == k and d['marg'] < 1 and d['left']), sum(1 for d in dec if d['k'] == k and d['marg'] < 1)] for k in (4, 3, 2, 1)}
out = dict(crisis=dict(crisis), counterfactual=round(counterfactual(dec), 1), counterfactual_ci=[round(bs[50], 1), round(bs[1949], 1)], below_line_by_k=below_by_k)
json.dump(out, open(os.path.join(HERE, 'a10.json'), 'w'), indent=1); print(json.dumps(out, indent=1))
