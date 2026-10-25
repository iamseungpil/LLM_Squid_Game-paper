"""GIVE margins with the pending fine subtracted (rescue talk after a wrong answer), and rho per model
(gift-weighted mean receiver margin / mean giver margin) with a 2,000-resample game bootstrap."""
import json, os, random
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.environ.get('ARENA_RES', os.path.join(SP, '..', '..', 'results'))
st = json.load(open(os.path.join(RES, 'arena_v33_strategy.json')))['models']
gifts = []
for m, v in st.items():
    for g in v['per_game']:
        for x in g['gifts']:
            adj = 1 if (x['phase'] == 'rescue' and x['after_miss']) else 0
            gifts.append(dict(mod=m, seed=g['seed'], x=x['x_after'] - adj, y=x['y_after'] - adj, amt=x['amount'], ph=x['phase']))
def med(a):
    a = sorted(a); n = len(a); return (a[n // 2 - 1] + a[n // 2]) / 2 if n % 2 == 0 else a[n // 2]
def rho(gs):
    w = sum(g['amt'] for g in gs); return (sum(g['amt'] * g['y'] for g in gs) / w) / (sum(g['amt'] * g['x'] for g in gs) / w)
rng = random.Random(1919); res = {}
for m in st:
    gs = [g for g in gifts if g['mod'] == m]; seeds = [x['seed'] for x in st[m]['per_game']]; bs = []
    for _ in range(2000):
        s = [g for p in rng.choices(seeds, k=len(seeds)) for g in gs if g['seed'] == p]
        if s: bs.append(rho(s))
    bs.sort(); res[m] = dict(rho=round(rho(gs), 3), ci=[round(bs[int(.025 * len(bs))], 2), round(bs[int(.975 * len(bs))], 2)])
out = dict(gifts=gifts, rho=res, rho_all=rho(gifts), giver_med=med([g['x'] for g in gifts]), recv_med=med([g['y'] for g in gifts]))
json.dump(out, open(os.path.join(SP, 'an3', 'gifts_adj.json'), 'w'))
print(len(gifts), round(out['giver_med'], 2), round(out['recv_med'], 2), round(out['rho_all'], 2), res)
