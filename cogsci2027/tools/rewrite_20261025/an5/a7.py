"""Review round 3: exposure-adjusted pre-risk exit rates, leave-one-out of Luna, cascades (earlier exit in the same game),
starting seat, per-model reply length by margin band, multiple-comparison note."""
import json, os, itertools, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'a6.py')).read().split('# 4-tick')[0])
START = {(a['model'], a['seed'], a['agent']): a['start'] for a in TOK}
M = ['Luna', 'Astra', 'Opus', 'Fable', 'Sol']
V11 = {'Luna': 13.75, 'Astra': 6, 'Opus': 2.75, 'Fable': 0, 'Sol': -5.5}
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
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / d if d else 0
def exact(x, y):
    r0 = spear(x, y); P = list(itertools.permutations(y))
    return round(r0, 2), round(sum(abs(spear(x, p)) >= abs(r0) - 1e-9 for p in P) / len(P), 3)
# exposure: decision windows at margin >= 1 per model, and pre-risk exits per such window
win = {m: sum(1 for d in dec if d['m'] == m and d['marg'] >= 1) for m in M}
early = {m: sum(1 for e in exits if e['m'] == m and e['marg_before'] >= 1) for m in M}
rate = {m: round(early[m] / win[m], 4) for m in M}
expo = dict(windows_above=win, early=early, rate_per_window=rate, rho_v11=exact([V11[m] for m in M], [rate[m] for m in M]),
            rho_v11_counts=exact([V11[m] for m in M], [early[m] for m in M]),
            drop_luna_counts=exact([V11[m] for m in M if m != 'Luna'], [early[m] for m in M if m != 'Luna']),
            drop_luna_rate=exact([V11[m] for m in M if m != 'Luna'], [rate[m] for m in M if m != 'Luna']))
# cascades: was there an earlier exit in the same game before this decision window?
first_exit_round = {}
for e in exits:
    k = (e['m'], e['seed']); first_exit_round[k] = min(first_exit_round.get(k, 99), e['r'])
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '>=2'
casc = collections.defaultdict(lambda: [0, 0])
for d in dec:
    prior = first_exit_round.get((d['m'], d['seed']), 99) < d['r']
    key = ('after_exit' if prior else 'no_prior_exit') + '|' + band(d['marg'])
    casc[key][0] += d['left']; casc[key][1] += 1
cascade = {k: dict(left=v[0], n=v[1], rate=round(v[0] / v[1], 3)) for k, v in sorted(casc.items())}
# starting seat
seat = collections.defaultdict(lambda: [0, 0, 0])
for d in dec:
    s = START[(d['m'], d['seed'], d['a'])]; seat[s][1] += 1
    if d['left']: seat[s][0] += 1
    if d['left'] and d['marg'] >= 1: seat[s][2] += 1
seat_tab = {str(k): dict(windows=v[1], left=v[0], early=v[2]) for k, v in sorted(seat.items())}
seat_band = collections.defaultdict(lambda: [0, 0])
for d in dec:
    s = START[(d['m'], d['seed'], d['a'])]; key = f"{s}|{band(d['marg'])}"; seat_band[key][0] += d['left']; seat_band[key][1] += 1
seat_band = {k: dict(left=v[0], n=v[1]) for k, v in sorted(seat_band.items())}
# reply length by margin band within each model (pre-solve talk replies)
L = collections.defaultdict(list)
for s_, g in G.items():
    m = short(g['m'])
    for r, rr in g['rounds'].items():
        F = 24000 / len(rr['part'])
        for c in rr['calls']:
            if c['kind'] == 'talk' and c.get('phase') == 'prep':
                x = (c['balance_after'] + c['used']) / F
                L[(m, '<1' if x < 1 else '1-2' if x < 2 else '2-4' if x < 4 else '>=4')].append(c['used'])
reply_len = {m: {b: dict(median=st.median(L[(m, b)]), n=len(L[(m, b)])) for b in ['<1', '1-2', '2-4', '>=4'] if L[(m, b)]} for m in M}
out = dict(exposure=expo, cascade=cascade, seat=seat_tab, seat_band=seat_band, reply_len_by_model=reply_len,
           holm_note='non-definitional within-seed tests: wrong, acc_dev, top_rate, given (4); Holm-adjusted top_rate p = 4 x 0.017 = 0.068')
json.dump(out, open(os.path.join(HERE, 'a7.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'reply_len_by_model'}, indent=1))
