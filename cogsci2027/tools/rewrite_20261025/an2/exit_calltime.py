import json, glob, os, random, collections
R = 'raw'; rng = random.Random(1919)
rows = []
for f in sorted(glob.glob(os.path.join(R, '*', 'events.jsonl'))):
    part = {}; solver = {}; bal = {}
    for l in open(f):
        e = json.loads(l); ev = e['event']; s = e.get('session_id')
        if ev == 'round_start': part[(s, e['round'])] = len(e['taking_part'])
        elif ev == 'vote': solver[(s, e['round'])] = e.get('rep')
        elif ev == 'call_start' and e.get('kind') == 'talk' and e.get('phase') == 'prep': bal[(s, e['round'], e['tick'])] = e['balances']
        elif ev == 'call' and e.get('kind') == 'talk' and e.get('phase') == 'prep':
            k = (s, e['round']); b = bal.get((s, e['round'], e.get('tick')), {}).get(e['agent'])
            if b is None or solver.get(k) == e['agent']: continue
            rows.append(dict(s=s, marg=b / (24000 / part[k]), exit=bool((e.get('parsed') or {}).get('exit')), solo=part[k] == 1))
B = [('≥4', 4, 99), ('2–4', 2, 4), ('1–2', 1, 2), ('<1', 0, 1)]; res = []
print('prep calls', len(rows), 'exits', sum(r['exit'] for r in rows))
for lab, lo, hi in B:
    G = [r for r in rows if lo <= r['marg'] < hi]; k = sum(r['exit'] for r in G); gs = sorted({r['s'] for r in G}); bs = []
    for _ in range(2000):
        rr = [r for g in rng.choices(gs, k=len(gs)) for r in G if r['s'] == g]; bs.append(sum(r['exit'] for r in rr) / len(rr))
    bs.sort(); G2 = [r for r in G if not r['solo']]
    res.append(dict(band=lab, n=len(G), k=k, p=k / len(G), ci=[bs[50], bs[1950]], n_nosolo=len(G2), k_nosolo=sum(r['exit'] for r in G2)))
    print(res[-1])
json.dump(res, open('an2/exit_band.json', 'w'))
