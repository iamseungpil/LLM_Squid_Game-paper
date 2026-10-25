import json, math, random, collections, statistics as st
P = json.load(open('an2/panel.json')); E = json.load(open('an2/episodes.json')); C = json.load(open('an2/calls.json'))
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [round((c - h) / d, 3), round((c + h) / d, 3)]
first = {}
for r in sorted(E, key=lambda x: x['r']): first.setdefault((r['s'], r['a']), r)
F1 = list(first.values())
out = {}
for g in ['none', 'short', 'lifted']:
    G = [r for r in F1 if r['grp'] == g]; c = collections.Counter(r['final'] for r in G)
    out[g] = dict(n=len(G), finished=c['finished'], exited=c['exited'], dead=c['dead'], asked=sum(r['asked_res'] for r in G))
    print(g, out[g])
# game-resampling CI for finished share received vs none (first crisis)
games = sorted({r['s'] for r in F1}); rng = random.Random(1919); diffs = []
for _ in range(2000):
    smp = [g for g in rng.choices(games, k=len(games))]; rows = [r for g in smp for r in F1 if r['s'] == g]
    a = [r for r in rows if r['grp'] != 'none']; b = [r for r in rows if r['grp'] == 'none']
    if a and b: diffs.append(sum(r['final'] == 'finished' for r in a) / len(a) - sum(r['final'] == 'finished' for r in b) / len(b))
diffs.sort(); print('finished share diff received-none CI', round(diffs[50], 2), round(diffs[1950], 2))
ex = []
for _ in range(2000):
    smp = rng.choices(games, k=len(games)); rows = [r for g in smp for r in F1 if r['s'] == g]
    a = [r for r in rows if r['grp'] != 'none']; b = [r for r in rows if r['grp'] == 'none']
    if a and b: ex.append(sum(r['final'] == 'exited' for r in b) / len(b) - sum(r['final'] == 'exited' for r in a) / len(a))
ex.sort(); print('exit share diff none-received CI', round(ex[50], 2), round(ex[1950], 2))
# asked among all episodes
allE = E; print('episodes', len(allE), 'asked & received', sum(r['asked_res'] and r['rec_res'] > 0 for r in allE), 'asked', sum(r['asked_res'] for r in allE), 'received', sum(r['rec_res'] > 0 for r in allE), 'received without asking', sum((not r['asked_res']) and r['rec_res'] > 0 for r in allE))
# within-model exit after crisis
json.dump(out, open('an2/fig2_crisis.json', 'w'))
# --- pre-solve EXIT per prep talk call by own margin (exclude solver: cannot exit; solo flagged)
mk = {(r['s'], r['r'], r['a']): r for r in P}
B = [('≥4', 4, 99), ('2–4', 2, 4), ('1–2', 1, 2), ('<1', 0, 1)]
prep = []
for c in C:
    if c['phase'] != 'prep': continue
    r = mk.get((c['s'], c['r'], c['a']))
    if r is None or r['solver']: continue
    prep.append(dict(c, marg=r['marg0'], n=r['n'], s=c['s']))
print('prep calls (non-solver)', len(prep), 'exits', sum(c['exit'] for c in prep))
res = []
for lab, lo, hi in B:
    G = [c for c in prep if lo <= c['marg'] < hi]; k = sum(c['exit'] for c in G)
    G2 = [c for c in G if c['n'] > 1]; k2 = sum(c['exit'] for c in G2)
    gs = sorted({c['s'] for c in G}); bs = []
    for _ in range(2000):
        smp = rng.choices(gs, k=len(gs)); rows = [c for g in smp for c in G if c['s'] == g]
        bs.append(sum(c['exit'] for c in rows) / len(rows))
    bs.sort(); res.append(dict(band=lab, n=len(G), k=k, p=k / len(G), ci=[bs[50], bs[1950]], n_nosolo=len(G2), k_nosolo=k2))
    print(lab, len(G), k, round(k / len(G), 3), [round(bs[50], 3), round(bs[1950], 3)], 'no-solo', len(G2), k2)
json.dump(res, open('an2/exit_band.json', 'w'))
# exits margins
X = [r for r in P if r['status'] == 'exited']
print('exits', len(X), 'below1', sum(r['marg0'] < 1 for r in X), 'below2', sum(r['marg0'] < 2 for r in X), 'solo', sum(r['n'] == 1 for r in X), 'below1 non-solo', sum(r['marg0'] < 1 and r['n'] > 1 for r in X))
# solver clean baseline: others on same task with margin>=2
S = [r for r in P if r['solver'] and r['wrong'] is not None]
task = collections.defaultdict(list)
for r in S: task[(r['seed'], r['r'])].append(r)
for lab, lo, hi in [('<1', 0, 1), ('<2', 0, 2), ('≥2', 2, 99)]:
    G = [r for r in S if lo <= r['marg0'] < hi]; acc = st.mean(not r['wrong'] for r in G)
    base = [st.mean(not q['wrong'] for q in task[(r['seed'], r['r'])] if q is not r and q['marg0'] >= 2) for r in G if any(q is not r and q['marg0'] >= 2 for q in task[(r['seed'], r['r'])])]
    print('solver', lab, len(G), round(acc, 3), 'baseline others>=2', round(st.mean(base), 3), len(base))
