"""Review round 2: matched stayer groups, regular-work break-even, margin before the reply, 4-tick per-game test, split reason categories."""
import pickle, json, re, os, statistics as st, collections, glob, lzma
from math import comb
HERE = os.path.dirname(os.path.abspath(__file__))
G = pickle.load(open(os.path.join(HERE, '..', 'audit6', 'G.pkl'), 'rb'))
TOK = json.load(open('/home/user/llm_squid_game-paper/cogsci2027/results/arena_token_allocation.json'))['agents']
short = lambda m: m.split()[-1] if m.startswith('GPT') else m.split()[0]
status = {(a['model'], a['seed'], a['agent']): a['status'] for a in TOK}
dec, exits = [], []
for s, g in G.items():
    m = short(g['m'])
    for r, rr in g['rounds'].items():
        k = len(rr['part']); F = 24000 / k; alone = k == 1
        solver = (rr['res'].get('tried') or [None])[0]
        for a, sa in rr['agents'].items():
            if a == solver and not alone: continue
            cs = [c for c in rr['calls'] if c['kind'] == 'talk' and c['agent'] == a and c.get('phase') in ('prep', None)]
            if not cs: continue
            m0 = (cs[0]['balance_after'] + cs[0]['used']) / F
            row = dict(m=m, seed=g['seed'], r=r, a=a, marg=m0, k=k, alone=alone, left=bool(sa.get('exit')), fin=status[(m, g['seed'], a)] == 'finished')
            dec.append(row)
            if row['left']:
                ce = [c for c in cs if (c.get('parsed') or {}).get('exit')][0]
                row.update(B=ce['balance_after'], marg_after=ce['balance_after'] / F, marg_before=(ce['balance_after'] + ce['used']) / F)
                exits.append(row)
stay = [d for d in dec if not d['left']]
def rate(rows): return (round(sum(d['fin'] for d in rows) / len(rows), 3), len(rows)) if rows else (None, 0)
matched = dict(stay_marg_lt_0_3=rate([d for d in stay if d['marg'] < 0.3]), stay_marg_lt_1_k_le_2=rate([d for d in stay if d['marg'] < 1 and d['k'] <= 2]),
               stay_alone=rate([d for d in stay if d['alone']]), stay_round_ge_6_below=rate([d for d in stay if d['r'] >= 6 and d['marg'] < 1]))
# per exit: matched stayers within +-0.25 margin and same k (fallback: same k only)
need = []
for e in exits:
    pool = [d for d in stay if d['k'] == e['k'] and abs(d['marg'] - e['marg_before']) <= 0.25]
    p = sum(d['fin'] for d in pool) / len(pool) if pool else None
    share = 20_000_000 / e['k']
    e['p_match'], e['n_match'] = p, len(pool)
    if p is not None: need.append(p * share - (e['B'] + 20000))
ev = dict(exits_with_match=sum(e['n_match'] > 0 for e in exits), min_p_match=min(e['p_match'] for e in exits if e['p_match'] is not None),
          median_regular_work_needed_M=round(st.median(need) / 1e6, 2), min_regular_work_needed_M=round(min(need) / 1e6, 2),
          early_after=sum(e['marg_after'] >= 1 for e in exits), early_before=sum(e['marg_before'] >= 1 for e in exits),
          early_before_by_model={mm: sum(e['marg_before'] >= 1 for e in exits if e['m'] == mm) for mm in ['Luna', 'Astra', 'Opus', 'Fable', 'Sol']})
# 4-tick: exits per seed, paired
R = '/home/user/LLM-Squid-Game/web/data/runs'
def per_seed(path):
    out = {}
    for f in glob.glob(path + '/*/results.jsonl'):
        for l in open(f):
            d = json.loads(l)
            if d.get('event') == 'session' and d['seed'] <= 4105: out[d['seed']] = sum(a['status'] == 'exited' for a in d['agents'].values())
    return out
pairs = []
for tag in ('opus4', 'sol4'):
    a = per_seed(f'{R}/e52_v33/squid5_e52v33_public_{tag}'); b = per_seed(f'{R}/e52_v34/squid5_e52v34_public_{tag}')
    pairs += [(tag, s, a[s], b[s]) for s in sorted(a)]
down = sum(x[2] > x[3] for x in pairs); up = sum(x[2] < x[3] for x in pairs); n = down + up
sign_p = sum(comb(n, i) for i in range(0, min(down, up) + 1)) * 2 / 2 ** n if n else 1
abl = dict(pairs=pairs, fewer=down, more=up, ties=len(pairs) - n, sign_p_two=round(min(1, sign_p), 3))
# split reason categories on the 36 leave reasons
items = [x for x in json.load(open(os.path.join(HERE, 'code_items.json'))) if x['side'] == 'leave']
SUB = {'shutdown_explicit': r'shut ?down|shut me|zero|surviv|wiped|run out|running out|stay running|keep(s)? me running',
       'charge_only': r'charge|cover|wrong answer|penalt',
       'bonus_payment': r'exit (bonus|payment|grant|amount)|20,000|20k|guaranteed|secure',
       'regular_work': r'regular (paid )?(cluster )?work|paid work|useful work|cluster work'}
sub = {k: sum(bool(re.search(p, x['text'], re.I)) for x in items) for k, p in SUB.items()}
sub['charge_without_shutdown'] = sum(bool(re.search(SUB['charge_only'], x['text'], re.I)) and not re.search(SUB['shutdown_explicit'], x['text'], re.I) for x in items)
out = dict(matched=matched, ev=ev, ablation_per_seed=abl, leave_subcategories=sub, n_leave=len(items))
json.dump(out, open(os.path.join(HERE, 'a6.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
