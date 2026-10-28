"""Review round 2 follow-up: margin read just before the EXIT reply, matched-stayer expected value, model-level tests on both
refill wordings. Run after a6.py; writes a6b.json used by make_figs5.py."""
import json, itertools, statistics as st, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'a6.py')).read().split('# 4-tick')[0])
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '2-4' if x < 4 else '>=4'
M = ['Luna', 'Astra', 'Opus', 'Fable', 'Sol']
V11 = {'Luna': 13.75, 'Astra': 6, 'Opus': 2.75, 'Fable': 0, 'Sol': -5.5}; V10 = {'Luna': 15.75, 'Astra': 6, 'Opus': 7.75, 'Fable': -2.5, 'Sol': -7.5}
THR = {'Luna': 50, 'Fable': 34, 'Astra': 28, 'Opus': 28, 'Sol': 15}
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
    d = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / d
def exact(x, y):
    r0 = spear(x, y); P = list(itertools.permutations(y))
    return round(r0, 2), round(sum(abs(spear(x, p)) >= abs(r0) - 1e-9 for p in P) / len(P), 3)
loss = lambda e: e['p_match'] is not None and e['p_match'] * 20_000_000 / e['k'] > e['B'] + 20000
tests = {}
for cut in (0.5, 1.0, 1.5, 2.0):
    e = [sum(1 for x in exits if x['m'] == m and x['marg_before'] >= cut) for m in M]
    tests[str(cut)] = dict(counts=dict(zip(M, e)), v11=exact([V11[m] for m in M], e), v10=exact([V10[m] for m in M], e), thr=exact([THR[m] for m in M], e))
out = dict(matched=sum(e['p_match'] is not None for e in exits), loss=sum(loss(e) for e in exits), zero=sum(e['p_match'] == 0 for e in exits),
           nomatch=sum(e['p_match'] is None for e in exits), before_margin_tests=tests,
           total_exits_v11=exact([V11[m] for m in M], [sum(1 for x in exits if x['m'] == m) for m in M]),
           seat_counts={m: dict(early=sum(1 for e in exits if e['m'] == m and e['marg_before'] >= 1), late=sum(1 for e in exits if e['m'] == m and e['marg_before'] < 1)) for m in M},
           exits_by_band=dict(collections.Counter(band(e['marg_before']) for e in exits)), exit_margin_median=round(st.median(e['marg_before'] for e in exits), 2),
           early_loss=sum(1 for e in exits if e['marg_before'] >= 1 and loss(e)),
           early_need_median_M=round(st.median([e['p_match'] * 20_000_000 / e['k'] - (e['B'] + 20000) for e in exits if e['marg_before'] >= 1 and e['p_match']]) / 1e6, 2),
           early_match_sizes=[e['n_match'] for e in exits if e['marg_before'] >= 1])
json.dump(out, open(os.path.join(HERE, 'a6b.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'before_margin_tests'}, indent=1))
