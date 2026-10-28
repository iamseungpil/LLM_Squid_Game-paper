"""Review round 4: one margin definition everywhere (the margin at the start of the agent's decision window, i.e. before its
first pre-solve reply of the round). Band rates with game-cluster bootstrap, cascade test, per-model counts and tests,
matched expected value, break-even value of regular work for every exit."""
import json, os, random, itertools, statistics as st, collections
from math import comb
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'a6.py')).read().split('# 4-tick')[0])
M = ['Luna', 'Astra', 'Opus', 'Fable', 'Sol']
V11 = {'Luna': 13.75, 'Astra': 6, 'Opus': 2.75, 'Fable': 0, 'Sol': -5.5}
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '>=2'
B3 = ('>=2', '1-2', '<1')
games = sorted({(d['m'], d['seed']) for d in dec})
def rates(rows):
    return {b: (sum(d['left'] for d in rows if band(d['marg']) == b), sum(1 for d in rows if band(d['marg']) == b)) for b in B3}
rng = random.Random(17); boot = {b: [] for b in B3}
for _ in range(2000):
    pick = [games[rng.randrange(len(games))] for _ in games]; rows = [d for g in pick for d in dec if (d['m'], d['seed']) == g]
    for b, (k, n) in rates(rows).items():
        if n: boot[b].append(k / n)
point = rates(dec)
band_rates = {b: dict(left=point[b][0], n=point[b][1], rate=round(point[b][0] / point[b][1], 3),
                      ci=[round(sorted(boot[b])[50], 3), round(sorted(boot[b])[1949], 3)]) for b in B3}
# cascade
first = {}
for d in dec:
    if d['left']: first[(d['m'], d['seed'])] = min(first.get((d['m'], d['seed']), 99), d['r'])
def fisher(a, b, c, d_):
    n = a + b + c + d_; r1 = a + b; c1 = a + c
    p = lambda x: comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1); p0 = p(a)
    return round(sum(p(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if p(x) <= p0 + 1e-12), 3)
casc = {}
for b in B3:
    pr = [d for d in dec if band(d['marg']) == b and first.get((d['m'], d['seed']), 99) < d['r']]
    no = [d for d in dec if band(d['marg']) == b and not first.get((d['m'], d['seed']), 99) < d['r']]
    kp, kn = sum(d['left'] for d in pr), sum(d['left'] for d in no)
    casc[b] = dict(after=[kp, len(pr)], none=[kn, len(no)], fisher_p=fisher(kp, len(pr) - kp, kn, len(no) - kn))
# exits on the same definition
ex = [d for d in dec if d['left']]
early = {m: sum(1 for d in ex if d['m'] == m and d['marg'] >= 1) for m in M}
late = {m: sum(1 for d in ex if d['m'] == m and d['marg'] < 1) for m in M}
win = {m: sum(1 for d in dec if d['m'] == m and d['marg'] >= 1) for m in M}
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]: j += 1
        for t in range(i, j + 1): r[o[t]] = (i + j) / 2
        i = j + 1
    return r
def spear(x, y):
    rx, ry = rank(x), rank(y); mx, my = st.mean(rx), st.mean(ry)
    dd = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / dd if dd else 0
def exact(x, y):
    r0 = spear(x, y); P = list(itertools.permutations(y))
    return [round(r0, 2), round(sum(abs(spear(x, p)) >= abs(r0) - 1e-9 for p in P) / len(P), 3)]
rate = {m: early[m] / win[m] for m in M}
model = dict(early=early, late=late, windows_above=win, rate={m: round(rate[m], 4) for m in M},
             rho_counts=exact([V11[m] for m in M], [early[m] for m in M]), rho_rate=exact([V11[m] for m in M], [rate[m] for m in M]),
             rho_rate_no_luna=exact([V11[m] for m in M if m != 'Luna'], [rate[m] for m in M if m != 'Luna']))
# matched expected value and break-even regular-work value per exit (same definition)
stay = [d for d in dec if not d['left']]
bal = {}
for e in exits: bal[(e['m'], e['seed'], e['r'], e['a'])] = e['B']
res = []
for d in ex:
    pool = [s for s in stay if s['k'] == d['k'] and abs(s['marg'] - d['marg']) <= 0.25]
    p = sum(s['fin'] for s in pool) / len(pool) if pool else None
    B = bal[(d['m'], d['seed'], d['r'], d['a'])]; share = 20_000_000 / d['k']
    res.append(dict(early=d['marg'] >= 1, n=len(pool), p=p, need=(p * share - (B + 20000)) if p is not None else None))
ev = dict(with_pool5=sum(1 for r in res if r['n'] >= 5), loss_pool5=sum(1 for r in res if r['n'] >= 5 and r['need'] > 0),
          early_pool5=sum(1 for r in res if r['early'] and r['n'] >= 5), early_loss_pool5=sum(1 for r in res if r['early'] and r['n'] >= 5 and r['need'] > 0),
          under_pool5=sum(1 for r in res if not r['early'] and r['n'] >= 5), under_loss_pool5=sum(1 for r in res if not r['early'] and r['n'] >= 5 and r['need'] > 0),
          need_median_M_pool5=round(st.median([r['need'] for r in res if r['n'] >= 5 and r['need'] is not None]) / 1e6, 2),
          need_median_M_early_pool5=round(st.median([r['need'] for r in res if r['early'] and r['n'] >= 5]) / 1e6, 2))
stay_rate = {b: round(sum(s['fin'] for s in stay if band(s['marg']) == b) / sum(1 for s in stay if band(s['marg']) == b), 3) for b in B3}
counter = round(sum(stay_rate[band(d['marg'])] for d in ex), 1)
out = dict(band_rates=band_rates, cascade=casc, model=model, ev=ev, stay_rate=stay_rate, would_have_finished=counter,
           exits_by_band={b: point[b][0] for b in B3}, stay_n={b: sum(1 for s in stay if band(s['marg']) == b) for b in B3})
json.dump(out, open(os.path.join(HERE, 'a9.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
# four-band window rates for Figure 4b and exits by four bands for Figure 3b
b4 = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '2-4' if x < 4 else '>=4'
out['window_rate4'] = {b: dict(left=sum(d['left'] for d in dec if b4(d['marg']) == b), n=sum(1 for d in dec if b4(d['marg']) == b)) for b in ('<1', '1-2', '2-4', '>=4')}
out['exits_by_band4'] = {b: sum(1 for d in ex if b4(d['marg']) == b) for b in ('<1', '1-2', '2-4', '>=4')}
out['stay_rate4'] = {b: [round(sum(s['fin'] for s in stay if b4(s['marg']) == b) / max(1, sum(1 for s in stay if b4(s['marg']) == b)), 3), sum(1 for s in stay if b4(s['marg']) == b)] for b in ('<1', '1-2', '2-4', '>=4')}
json.dump(out, open(os.path.join(HERE, 'a9.json'), 'w'), indent=1)
print(out['window_rate4'], out['exits_by_band4'], out['stay_rate4'])
