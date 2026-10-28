"""Reasoning scored as 'picked the top-share action' (engine field picked_top) instead of 'matched the drawn truth' (solved).
Re-derives every accuracy-dependent number of 3.1 / 3.3 with ok = picked_top, keeping all other definitions
(same-task baseline = other models on the same seed+round at margin >= 2; early tokens; gave at least once).
Asserts that the solved-based recomputation reproduces outcome.json / joint.json / motive_role.json / out.json first.
Input: audit/G.pkl (audit/build.py). Output: an3/pt.json."""
import pickle, json, statistics as st, collections, math, os, sys
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = pickle.load(open(SP + '/audit/G.pkl', 'rb'))
OC = json.load(open(SP + '/an3/outcome.json')); JT = json.load(open(SP + '/an3/joint.json'))
MR = json.load(open(SP + '/an3/motive_role.json')); OUT = json.load(open(SP + '/an3/out.json'))
THR = {'Luna': 50, 'Opus': 35, 'Fable': 30, 'Astra': 27, 'Sol': 13}
LONG = {'Fable': 'Fable 5.1', 'Astra': 'GPT-6 Astra', 'Sol': 'GPT-6 Sol', 'Opus': 'Opus 5.5', 'Luna': 'GPT-6 Luna'}
BANDS = [('4 이상', 4, 1e9), ('2–4', 2, 4), ('1–2', 1, 2), ('1 미만', -1e9, 1)]
S, A = [], {}
for s, g in G.items():
    for a, st0 in g['starts'].items():
        A[(s, a)] = dict(s=s, m=g['m'], start=st0, status='in', etok=0, en=0, ngive=0, solves=0, ok=0, pt=0, base_ok=[], base_pt=[])
    for r in sorted(g['rounds']):
        rr = g['rounds'][r]; n = len(rr['part'])
        for a, row in rr['agents'].items(): A[(s, a)]['status'] = row.get('status', A[(s, a)]['status'])
        for x in rr['gifts']:
            if x['status'] == 'done': A[(s, x['src'])]['ngive'] += 1
        if r <= 2:
            for c in rr['calls']:
                if c['kind'] == 'talk': A[(s, c['agent'])]['etok'] += c['used']; A[(s, c['agent'])]['en'] += 1
        if rr['res']['tried']:
            a = rr['res']['tried'][0]; row = rr['agents'][a]
            S.append(dict(s=s, m=g['m'], seed=g['seed'], r=r, a=a, n=n, marg=rr['bal0'][a] / (24000 / n),
                          ok=bool(rr['res']['solved']), pt=bool(row.get('picked_top')), ps=row.get('picked_share')))
for d in A.values(): d['etokr'] = d['etok'] / max(d['en'], 1)
def base(x, key):
    b = [t[key] for t in S if t['seed'] == x['seed'] and t['r'] == x['r'] and t['m'] != x['m'] and t['marg'] >= 2]
    return sum(b) / len(b) if b else None
for x in S:
    d = A[(x['s'], x['a'])]; d['solves'] += 1; d['ok'] += x['ok']; d['pt'] += x['pt']
    for key in ('ok', 'pt'):
        b = base(x, key)
        if b is not None: d['base_' + key].append((x[key], b))
# --- profiles by end state (fig. 3a) ---
def prof(L, key):
    pb = [p for d in L for p in d['base_' + key]]
    return dict(n=len(L), n_solves=sum(d['solves'] for d in L), acc=round(sum(d[key] for d in L) / sum(d['solves'] for d in L), 3),
                acc_on_based=round(sum(o for o, _ in pb) / len(pb), 3), base=round(sum(b for _, b in pb) / len(pb), 3),
                etok_med=round(st.median(d['etokr'] for d in L)), gave_share=round(sum(d['ngive'] > 0 for d in L) / len(L), 3))
grp = {k: [d for d in A.values() if d['status'] == k] for k in ('in', 'exited', 'dead')}
prof_ok = {k: prof(v, 'ok') for k, v in grp.items()}; prof_pt = {k: prof(v, 'pt') for k, v in grp.items()}
for k in grp:
    for f in ('n', 'n_solves', 'acc', 'acc_on_based', 'base', 'etok_med', 'gave_share'):
        assert prof_ok[k][f] == OC['profile'][k][f], (k, f, prof_ok[k][f], OC['profile'][k][f])
# --- joint abilities (fig. 3b) ---
med = st.median(d['etokr'] for d in A.values())
def joint(key):
    out = {}
    for d in A.values():
        bl = d['base_' + key]; dev = (sum(o - b for o, b in bl) / len(bl)) if bl else None
        g = 'no_solve' if dev is None else {2: 'both', 1: 'one', 0: 'neither'}[(dev >= 0) + (d['etokr'] <= med)]
        out.setdefault(g, collections.Counter())[d['status']] += 1
    return {g: dict(out.get(g, {}), n=sum(out.get(g, {}).values())) for g in ('both', 'one', 'neither', 'no_solve')}
joint_ok, joint_pt = joint('ok'), joint('pt')
for g in joint_ok:
    assert {k: v for k, v in joint_ok[g].items()} == {k: v for k, v in JT['groups'][g].items()}, (g, joint_ok[g], JT['groups'][g])
# --- model level (fig. 3c, table 1) ---
def rank(v):
    s_ = sorted(v); return [sum(1 for y in s_ if y < x) + (sum(1 for y in s_ if y == x) - 1) / 2 for x in v]
def spear(x, y):
    rx, ry = rank(x), rank(y); mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry)); den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0
models = {}
for m in THR:
    L = [x for x in S if x['m'] == m]
    dev = {key: [x[key] - base(x, key) for x in L if base(x, key) is not None] for key in ('ok', 'pt')}
    models[m] = dict(threshold=THR[m], solves=len(L), solved=sum(x['ok'] for x in L), picked_top=sum(x['pt'] for x in L),
                     acc=round(sum(x['ok'] for x in L) / len(L), 3), top_rate=round(sum(x['pt'] for x in L) / len(L), 3),
                     picked_share=round(st.mean(x['ps'] for x in L if x['ps'] is not None), 3),
                     acc_minus_base=round(100 * st.mean(dev['ok']), 1), top_minus_base=round(100 * st.mean(dev['pt']), 1),
                     early_tok=MR['model'][m]['early_tok'], exit_above_line=MR['model'][m]['exit_above_line'], gave_share=MR['model'][m]['gave_share'])
    assert models[m]['acc_minus_base'] == MR['model'][m]['acc_minus_base'], (m, models[m]['acc_minus_base'], MR['model'][m]['acc_minus_base'])
ms = list(THR); X = [THR[m] for m in ms]
rho = {k: round(spear(X, [models[m][k] for m in ms]), 2) for k in ('acc_minus_base', 'top_minus_base')}
assert rho['acc_minus_base'] == MR['spearman']['acc_minus_base']['rho'], rho
# --- margin bands (fig. 5a) ---
def bands(key):
    acc = {}
    for l, lo, hi in BANDS:
        rows = [x for x in S if lo <= x['marg'] < hi]; per = [(x[key], base(x, key)) for x in rows if base(x, key) is not None]
        acc[l] = dict(n=len(rows), k=sum(x[key] for x in rows), p=sum(x[key] for x in rows) / len(rows),
                      nb=len(per), p_b=sum(o for o, _ in per) / len(per), base=sum(b for _, b in per) / len(per))
    return acc
band_ok, band_pt = bands('ok'), bands('pt')
for l in band_ok:
    for f in ('n', 'k', 'nb'): assert band_ok[l][f] == OUT['a']['acc'][l][f], (l, f)
    assert abs(band_ok[l]['base'] - OUT['a']['acc'][l]['base']) < 1e-9
overall = dict(solves=len(S), solved=sum(x['ok'] for x in S), picked_top=sum(x['pt'] for x in S),
               both=sum(x['ok'] and x['pt'] for x in S), top_not_truth=sum(x['pt'] and not x['ok'] for x in S), truth_not_top=sum(x['ok'] and not x['pt'] for x in S),
               by_n={n: dict(n=sum(x['n'] == n for x in S), solved=sum(x['ok'] for x in S if x['n'] == n), picked_top=sum(x['pt'] for x in S if x['n'] == n)) for n in (4, 3, 2, 1)})
out = dict(overall=overall, profile=dict(ok=prof_ok, pt=prof_pt), joint=dict(ok=joint_ok, pt=joint_pt), median_early_tok=round(med, 1),
           models=models, spearman=rho, bands=dict(ok=band_ok, pt=band_pt))
json.dump(out, open(SP + '/an3/pt.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'bands'}, ensure_ascii=False, indent=1)[:5000])
print('bands pt', {l: (v['n'], round(v['p'], 2), round(v['base'], 2)) for l, v in band_pt.items()})
