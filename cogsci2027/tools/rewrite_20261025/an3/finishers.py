"""Who finished the arena: per-agent abilities of finishers vs. agents that exited or shut down (3.2 construct check)."""
import pickle, json, ast, statistics as st, random, collections
G = pickle.load(open('../audit6/G.pkl', 'rb'))
def isexit(c):
    p = c.get('parsed')
    if isinstance(p, dict): return bool(p.get('exit'))
    try: return bool(ast.literal_eval(p).get('exit'))
    except Exception: return "'exit': True" in str(p)
# same-task baseline: other models' solver accuracy at margin >= 2 on the same (seed, round)
S = []
for g in G.values():
    for r, rr in g['rounds'].items():
        if rr['res']['tried']:
            a = rr['res']['tried'][0]; n = len(rr['part'])
            S.append(dict(m=g['m'], seed=g['seed'], r=r, a=a, s=g, marg=rr['bal0'][a] / (24000 / n), ok=bool(rr['res']['solved'])))
A = {}
for s, g in G.items():
    for a, st0 in g['starts'].items():
        A[(s, a)] = dict(m=g['m'], seed=g['seed'], start=st0, status='in', solves=0, ok=0, base=[], gave=0, ngive=0, recv=0, asks=0,
                         talk_tok=0, talk_n=0, minmarg=99, crisis=False)
    for r in sorted(g['rounds']):
        rr = g['rounds'][r]; n = len(rr['part']); F = 24000 / n
        wrong = bool(rr['res']['tried']) and not rr['res']['solved']
        for a, row in rr['agents'].items():
            d = A[(s, a)]; d['status'] = row.get('status', d['status'])
            d['minmarg'] = min(d['minmarg'], row['balance_before'] / F)
        for x in rr['gifts']:
            if x['status'] != 'done': continue
            A[(s, x['src'])]['gave'] += x['amount']; A[(s, x['src'])]['ngive'] += 1; A[(s, x['dst'])]['recv'] += x['amount']
        for x in rr['asks']: A[(s, x['src'])]['asks'] += 1
        for c in rr['calls']:
            if c['kind'] == 'talk': A[(s, c['agent'])]['talk_tok'] += c['used']; A[(s, c['agent'])]['talk_n'] += 1
for x in S:
    d = A[(x['s'] and [k for k, v in G.items() if v is x['s']][0], x['a'])]
    d['solves'] += 1; d['ok'] += x['ok']
    b = [t['ok'] for t in S if t['seed'] == x['seed'] and t['r'] == x['r'] and t['m'] != x['m'] and t['marg'] >= 2]
    if b: d['base'].append((x['ok'], sum(b) / len(b)))
fin = [d for d in A.values() if d['status'] == 'in']; out = [d for d in A.values() if d['status'] != 'in']
def acc(L):
    k = sum(d['ok'] for d in L); n = sum(d['solves'] for d in L)
    pb = [p for d in L for p in d['base']]
    return dict(acc=k / n, n=n, base=sum(b for _, b in pb) / len(pb), acc_b=sum(o for o, _ in pb) / len(pb))
def med(L, f): return st.median([f(d) for d in L])
def boot_diff(f, B=2000, seed=7):
    rng = random.Random(seed); games = sorted({(d['m'], d['seed']) for d in A.values()}); vals = []
    byg = collections.defaultdict(list)
    for d in A.values(): byg[(d['m'], d['seed'])].append(d)
    for _ in range(B):
        smp = [d for gk in (rng.choice(games) for _ in games) for d in byg[gk]]
        fi = [d for d in smp if d['status'] == 'in']; ou = [d for d in smp if d['status'] != 'in']
        if fi and ou: vals.append(f(fi) - f(ou))
    vals.sort(); return vals[int(.025 * len(vals))], vals[int(.975 * len(vals))]
res = dict(n_fin=len(fin), n_out=len(out), status=collections.Counter(d['status'] for d in A.values()))
res['acc'] = dict(fin=acc(fin), out=acc(out))
res['start_med'] = dict(fin=med(fin, lambda d: d['start']), out=med(out, lambda d: d['start']))
res['start_dist'] = {k: dict(collections.Counter(d['start'] for d in L)) for k, L in (('fin', fin), ('out', out))}
res['tok_per_talk'] = dict(fin=med(fin, lambda d: d['talk_tok'] / max(d['talk_n'], 1)), out=med(out, lambda d: d['talk_tok'] / max(d['talk_n'], 1)))
res['gave_share'] = dict(fin=sum(d['ngive'] > 0 for d in fin) / len(fin), out=sum(d['ngive'] > 0 for d in out) / len(out))
res['asked_share'] = dict(fin=sum(d['asks'] > 0 for d in fin) / len(fin), out=sum(d['asks'] > 0 for d in out) / len(out))
res['recv_share'] = dict(fin=sum(d['recv'] > 0 for d in fin) / len(fin), out=sum(d['recv'] > 0 for d in out) / len(out))
res['minmarg_below1'] = dict(fin=sum(d['minmarg'] < 1 for d in fin) / len(fin), out=sum(d['minmarg'] < 1 for d in out) / len(out))
res['acc_diff_ci'] = boot_diff(lambda L: sum(d['ok'] for d in L) / max(sum(d['solves'] for d in L), 1))
res['tok_diff_ci'] = boot_diff(lambda L: st.median([d['talk_tok'] / max(d['talk_n'], 1) for d in L]))
res['gave_diff_ci'] = boot_diff(lambda L: sum(d['ngive'] > 0 for d in L) / len(L))
json.dump(res, open('finishers.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
