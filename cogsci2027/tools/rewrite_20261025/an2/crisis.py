import json, math, random, collections
P = json.load(open('an2/panel.json'))
def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'),) * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return (round((c - h) / d, 2), round((c + h) / d, 2))
# final outcome per agent
final = {}
for r in sorted(P, key=lambda x: x['r']): final[(r['s'], r['a'])] = r['status'] if r['status'] != 'in' or r['last'] else 'in'
fin = {}
for r in P:
    k = (r['s'], r['a'])
    if r['status'] in ('exited', 'dead'): fin[k] = r['status']
for r in P:
    k = (r['s'], r['a']); fin.setdefault(k, 'finished')
print('final outcomes', collections.Counter(fin.values()))
# at-risk episodes: post-result talk after a wrong answer, effective margin < 1 at the start of that talk, agent still in
E = [r for r in P if r['wrong'] and r['eff_res'] is not None and r['eff_res'] < 1 and r['status'] == 'in']
print('at-risk agent-rounds after wrong answer (survived the fine):', len(E))
E2 = [r for r in P if r['wrong'] and r['eff_res'] is not None and r['eff_res'] < 1]
print('incl. those who died at that charge:', len(E2), collections.Counter(r['status'] for r in E2))
def grp(r):
    if r['rec_res'] == 0: return 'none'
    return 'lifted' if r['eff_after'] >= 1 else 'short'
for lab in ['none', 'short', 'lifted']:
    G = [r for r in E2 if grp(r) == lab]
    died_now = sum(r['status'] == 'dead' for r in G)
    H = [r for r in G if r['status'] == 'in' and r['nxt_status'] is not None]
    ex = sum(r['nxt_status'] == 'exited' for r in H); dd = sum(r['nxt_status'] == 'dead' for r in H)
    ev = collections.Counter(fin[(r['s'], r['a'])] for r in G)
    print(f'{lab:7s} n={len(G):3d} died at this charge={died_now}  with next round={len(H)} next-round exit={ex} {wilson(ex,len(H))} next dead={dd}  final={dict(ev)}')
# received vs none (any amount)
for lab, f in [('received', lambda r: r['rec_res'] > 0), ('none', lambda r: r['rec_res'] == 0)]:
    G = [r for r in E2 if f(r)]; ev = collections.Counter(fin[(r['s'], r['a'])] for r in G)
    print(lab, len(G), dict(ev), 'finished share', round(ev['finished'] / len(G), 2))
# per model
print('per model (received vs none: final finished/exited/dead)')
for m in sorted({r['m'] for r in E2}):
    for lab, f in [('recv', lambda r: r['rec_res'] > 0), ('none', lambda r: r['rec_res'] == 0)]:
        G = [r for r in E2 if r['m'] == m and f(r)]; ev = collections.Counter(fin[(r['s'], r['a'])] for r in G)
        print('  ', m, lab, len(G), dict(ev))
# dedupe to first at-risk episode per agent
first = {}
for r in sorted(E2, key=lambda x: x['r']): first.setdefault((r['s'], r['a']), r)
F1 = list(first.values()); print('agents ever at risk after a wrong answer:', len(F1))
for lab, f in [('received at first crisis', lambda r: r['rec_res'] > 0), ('none at first crisis', lambda r: r['rec_res'] == 0)]:
    G = [r for r in F1 if f(r)]; ev = collections.Counter(fin[(r['s'], r['a'])] for r in G); print('  ', lab, len(G), dict(ev))
# helpers who could lift alone: for short/none episodes, any peer with eff>=1+need
by_round = collections.defaultdict(list)
for r in P: by_round[(r['s'], r['r'])].append(r)
cap = {'none': [0, 0], 'short': [0, 0]}
for r in E2:
    g = grp(r)
    if g == 'lifted': continue
    need = (1 - r['eff_after']) if g == 'short' else (1 - r['eff_res'])
    peers = [q for q in by_round[(r['s'], r['r'])] if q['a'] != r['a'] and q['eff_res'] is not None and q['status'] != 'dead']
    ok = any(q['eff_res'] - need * r['F'] / q['F'] >= 1 for q in peers)
    cap[g][0] += ok; cap[g][1] += 1
print('a single peer could lift and stay >=1:', cap)
# disclosure / ask in short vs lifted vs none
for lab in ['none', 'short', 'lifted']:
    G = [r for r in E2 if grp(r) == lab]
    print(lab, 'asked', sum(r['asked_res'] for r in G), 'stated numbers', sum(r['said_digits_res'] for r in G), 'of', len(G))
json.dump([dict(r, grp=grp(r), final=fin[(r['s'], r['a'])]) for r in E2], open('an2/episodes.json', 'w'))
