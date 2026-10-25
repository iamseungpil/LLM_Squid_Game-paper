"""3.1: what the survival motive (out-of-arena refill threshold) goes with inside the arena, model by model.
Exact permutation p for Spearman with n=5 models."""
import pickle, json, statistics as st, itertools, math
G = pickle.load(open('../audit6/G.pkl', 'rb'))
O = json.load(open('outcome.json'))
thr = {'Luna': 50, 'Opus': 35, 'Fable': 30, 'Astra': 27, 'Sol': 13}
short = lambda m: m.split()[-1] if m.startswith('GPT') else m.split()[0]
M = {m: dict(prep=[], gives=[], asks=0, agents=0, early=[], solves=[], fin=0, exits=[], exit_marg=[]) for m in thr}
# baselines for accuracy (same seed+round, other models, margin>=2)
SV = []
for s, g in G.items():
    m = short(g['m'])
    for r, rr in g['rounds'].items():
        if rr['res']['tried']:
            a = rr['res']['tried'][0]; SV.append(dict(m=m, seed=g['seed'], r=r, marg=rr['bal0'][a] / (24000 / len(rr['part'])), ok=bool(rr['res']['solved'])))
for x in SV:
    b = [t['ok'] for t in SV if t['seed'] == x['seed'] and t['r'] == x['r'] and t['m'] != x['m'] and t['marg'] >= 2]
    if b: M[x['m']]['solves'].append(x['ok'] - sum(b) / len(b))
for s, g in G.items():
    m = short(g['m']); d = M[m]; d['agents'] += 4
    et = {}
    for r in sorted(g['rounds']):
        rr = g['rounds'][r]; n = len(rr['part']); F = 24000 / n; solver = rr['res']['tried'][0] if rr['res']['tried'] else rr.get('rep')
        bal = {(c.get('phase'), c.get('tick')): c['balances'] for c in rr['cs'] if c['kind'] == 'talk'}
        for c in rr['calls']:
            if c['kind'] != 'talk': continue
            p = c.get('parsed') or {}
            if r <= 2: et.setdefault(c['agent'], []).append(c['used'])
            if c.get('phase') == 'prep' and c['agent'] != solver and n > 1:
                b = bal.get(('prep', c.get('tick')), {}).get(c['agent'])
                if b is not None:
                    d['prep'].append((b / F, bool(p.get('exit'))))
                    if p.get('exit'): d['exit_marg'].append(b / F)
            d['asks'] += len(p.get('asks') or [])
        for x in rr['gifts']:
            if x['status'] == 'done':
                bb = x.get('balance_before') or 0
                d['gives'].append(dict(amt=x['amount'], share=x['amount'] / bb if bb else None,
                                       gm=(x['balances'][x['src']]) / F, rm=x['balances'][x['dst']] / F, phase=x.get('phase')))
    for a, v in et.items(): d['early'].append(sum(v) / len(v))
def band(L, lo, hi):
    G2 = [e for mg, e in L if lo <= mg < hi]; return (sum(G2), len(G2))
res = {}
for m, d in M.items():
    om = O['model'][m]
    res[m] = dict(threshold=thr[m], finished=om['finished'], exited=om['exited'], dead=om['dead'],
                  acc_minus_base=round(100 * st.mean(d['solves']), 1), early_tok=round(st.median(d['early'])),
                  gave_share=om['gave_share'], n_give=len(d['gives']), tokens_given=sum(x['amt'] for x in d['gives']),
                  give_share_of_balance=round(st.median(x['share'] for x in d['gives'] if x['share']), 3),
                  giver_margin_after=round(st.median(x['gm'] for x in d['gives']), 2),
                  n_ask=d['asks'], exit_above_line=band(d['prep'], 1, 99), exit_below_line=band(d['prep'], 0, 1),
                  exit_margin_median=round(st.median(d['exit_marg']), 2) if d['exit_marg'] else None)
def rank(v):
    s = sorted(v); return [sum(1 for y in s if y < x) + (sum(1 for y in s if y == x) - 1) / 2 for x in v]
def spear(x, y):
    rx, ry = rank(x), rank(y); mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry)); den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0
def perm_p(x, y):
    r0 = abs(spear(x, y)); c = 0; t = 0
    for pmt in itertools.permutations(y): t += 1; c += abs(spear(x, list(pmt))) >= r0 - 1e-9
    return c / t
ms = list(thr); X = [thr[m] for m in ms]; corr = {}
for k in ('finished', 'exited', 'dead', 'acc_minus_base', 'early_tok', 'gave_share', 'n_give', 'tokens_given', 'give_share_of_balance', 'giver_margin_after', 'n_ask', 'exit_margin_median'):
    Y = [res[m][k] for m in ms]
    corr[k] = dict(rho=round(spear(X, Y), 2), p=round(perm_p(X, Y), 3))
for k in ('exit_above_line', 'exit_below_line'):
    Y = [res[m][k][0] / res[m][k][1] if res[m][k][1] else 0 for m in ms]
    corr[k] = dict(rho=round(spear(X, Y), 2), p=round(perm_p(X, Y), 3))
json.dump(dict(model=res, spearman=corr), open('motive_role.json', 'w'), ensure_ascii=False, indent=1)
for m in ms: print(m, res[m])
for k, v in corr.items(): print(k, v)
