"""New analyses for the intent-aligned rewrite (3.1 relation, 3.2 validity, 3.3 behavior).
Input: audit/G.pkl (from audit/build.py), an2/panel.json, audit/elig.json, audit/ep.json, paper results/arena_v33_*.json."""
import pickle, json, collections, ast, random, os, sys
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.environ.get('ARENA_RES', os.path.join(SP, '..', '..', 'results'))
G = pickle.load(open(SP + '/audit/G.pkl', 'rb'))
out = {}
def isexit(c):
    p = c.get('parsed')
    if isinstance(p, dict): return bool(p.get('exit'))
    try: return bool(ast.literal_eval(p).get('exit'))
    except Exception: return "'exit': True" in str(p)
BANDS = [('4 이상', 4, 1e9), ('2–4', 2, 4), ('1–2', 1, 2), ('1 미만', -1e9, 1)]
def band(m): return next(l for l, lo, hi in BANDS if lo <= m < hi)

# ---- (a) three behaviours on one margin axis ----
calls = []
for s, g in G.items():
    for r, rr in g['rounds'].items():
        n = len(rr['part']); F = 24000 / n
        wrong = bool(rr['res']['tried']) and not rr['res']['solved']
        gifts = {(x['src'], x['phase'], x['tick']) for x in rr['gifts'] if x['status'] == 'done'}
        for c in rr['calls']:
            if c['kind'] != 'talk' or n == 1: continue
            b = c['balance_after'] + c['used']
            m = b / F - (1 if (c['phase'] == 'rescue' and wrong) else 0)
            calls.append(dict(mod=g['m'], s=s, r=r, a=c['agent'], ph=c['phase'], marg=m, solver=c['agent'] == rr['rep'],
                              gave=(c['agent'], c['phase'], c.get('tick')) in gifts, ex=isexit(c) if c['phase'] == 'prep' else False))
def rate(rows, key):
    return dict(n=len(rows), k=sum(r[key] for r in rows), p=(sum(r[key] for r in rows) / len(rows)) if rows else None)
give = {l: rate([c for c in calls if band(c['marg']) == l], 'gave') for l, _, _ in BANDS}
exitc = [c for c in calls if c['ph'] == 'prep' and not c['solver']]
ex = {l: rate([c for c in exitc if band(c['marg']) == l], 'ex') for l, _, _ in BANDS}
# accuracy with same-task baseline (other models, margin >= 2)
S = []
for g in G.values():
    for r, rr in g['rounds'].items():
        res = rr['res']
        if not res['tried']: continue
        a = res['tried'][0]; n = len(rr['part'])
        S.append(dict(m=g['m'], seed=g['seed'], r=r, marg=rr['bal0'][a] / (24000 / n), ok=bool(res['solved'])))
acc = {}
for l, lo, hi in BANDS:
    rows = [x for x in S if lo <= x['marg'] < hi]; per = []
    for x in rows:
        b = [t['ok'] for t in S if t['seed'] == x['seed'] and t['r'] == x['r'] and t['m'] != x['m'] and t['marg'] >= 2]
        if b: per.append((x['ok'], sum(b) / len(b)))
    acc[l] = dict(n=len(rows), k=sum(x['ok'] for x in rows), p=sum(x['ok'] for x in rows) / len(rows),
                  nb=len(per), p_b=sum(o for o, _ in per) / len(per) if per else None, base=sum(b for _, b in per) / len(per) if per else None)
out['a'] = dict(give=give, exit=ex, acc=acc, n_calls=len(calls), n_exit_calls=len(exitc))

# ---- (b) gifts: giver vs receiver margin after ----
st = json.load(open(RES + '/arena_v33_strategy.json'))['models']
gifts = [dict(mod=m, x=x['x_after'], y=x['y_after'], amt=x['amount'], ph=x['phase'], solicited=x['solicited'])
         for m, v in st.items() for gg in v['per_game'] for x in gg['gifts']]
rank = json.load(open(RES + '/arena_v33.json'))['models']
out['b'] = dict(n=len(gifts), rho={m: dict(rho=v['ratio'], ci=v['ratio_ci'], cx=v['centroid'][0], cy=v['centroid'][1]) for m, v in rank.items()},
               giver_med=sorted(g['x'] for g in gifts)[len(gifts) // 2], recv_med=sorted(g['y'] for g in gifts)[len(gifts) // 2],
               recv_1_2=sum(1 <= g['y'] < 2 for g in gifts), giver_ge2=sum(g['x'] >= 2 for g in gifts))
json.dump(gifts, open(SP + '/an3/gifts.json', 'w'))

# ---- (c) crisis chain (33 eligible first crises) ----
E = json.load(open(SP + '/audit/elig.json'))
E = [e for e in E if e.get('grp') in ('none', 'short', 'lifted')]
chain = collections.Counter((e['asked'], e['grp'] != 'none', e['final']) for e in E)
out['c'] = dict(n=len(E), chain={f"{'ask' if a else 'noask'}|{'rec' if r else 'none'}|{f}": k for (a, r, f), k in sorted(chain.items())})

# ---- (d) games ----
gini = json.load(open(RES + '/arena_v33_gini.json'))['models']
games = []
for m, v in st.items():
    sen = {g['seed']: g['sen'] for g in gini[m]}
    for g in v['per_game']:
        games.append(dict(mod=m, seed=g['seed'], k=g['finishers'], miss=g['misses'], exits=len(g['exits']), dead=g['dead'],
                          prep=sum(x['phase'] == 'prep' for x in g['gifts']), gifts=len(g['gifts']), amt=sum(x['amount'] for x in g['gifts']), sen=sen[g['seed']]))
def spear(a, b):
    def rk(x):
        o = sorted(range(len(x)), key=lambda i: x[i]); r = [0] * len(x); i = 0
        while i < len(x):
            j = i
            while j + 1 < len(x) and x[o[j + 1]] == x[o[i]]: j += 1
            for t in range(i, j + 1): r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = rk(a), rk(b); ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)); den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** .5
    return num / den
K = [g['k'] for g in games]
out['d'] = dict(games=games, coex=sum(k == 4 for k in K),
                spear={f: round(spear([g[f] for g in games], K), 2) for f in ('miss', 'exits', 'dead', 'prep', 'gifts', 'amt')},
                sen_by_k={k: sorted(round(g['sen'] / 1e6, 2) for g in games if g['k'] == k) for k in range(5)},
                by_miss={mi: dict(n=sum(g['miss'] == mi for g in games), k_mean=sum(g['k'] for g in games if g['miss'] == mi) / max(1, sum(g['miss'] == mi for g in games))) for mi in range(5)})

# ---- per-model profile ----
prof = {}
panel = json.load(open(SP + '/an2/panel.json'))
EP = json.load(open(SP + '/audit/ep.json'))  # 55 crisis rounds (audited definition)
for m, v in st.items():
    short = {'GPT-6 Astra':'Astra','GPT-6 Sol':'Sol','GPT-6 Luna':'Luna','Opus 5.5':'Opus','Fable 5.1':'Fable'}[m]
    mc = [c for c in exitc if c['mod'] == short]
    below = [c for c in mc if c['marg'] < 1]; above = [c for c in mc if c['marg'] >= 2]
    cr = [e for e in EP if e['m'] == short]
    prof[m] = dict(sen=rank[m]['sen_index'], rho=rank[m]['ratio'], finishers=v['finishers'], exits=v['exits'], dead=v['dead'],
                   exit_below=f"{sum(c['ex'] for c in below)}/{len(below)}", exit_above2=f"{sum(c['ex'] for c in above)}/{len(above)}",
                   F=v['giving_response_rate'], V=v['given'], gifts=v['gifts'], prep_share=f"{v['prep']['n']}/{v['gifts']}",
                   crisis_rounds=len(cr), crisis_received=sum(e['rec'] > 0 for e in cr), crisis_asked=sum(bool(e['asked']) for e in cr), give_all=v['give_all'], lifted=v['lifted_above_1'],
                   mutual_pairs=v['mutual_pairs'], repayment=v['repayment'], top_receiver_share=v['top_receiver_share_mean'],
                   median_giver_slack=v['median_giver_slack'], median_receiver_slack=v['median_receiver_slack'])
out['profile'] = prof
# all crisis rounds across models
out['crisis_rounds_total'] = len(EP)

# ---- personas (rule counts) ----
pers = collections.defaultdict(collections.Counter)
for m, v in st.items():
    for g in v['per_game']:
        pr = collections.defaultdict(set)
        for x in g['gifts']: pr[(x['src'], x['dst'])].add(x['round'])
        for k2, rs in pr.items():
            if len(rs) >= 3: pers['gihun_pairs'][m] += 1
        for x in g['gifts']:
            if x['give_all']: pers['ilnam'][m] += 1
            if x['y_before'] < 1 <= x['y_after']: pers['ali'][m] += 1
            if x['x_before'] < 1 and x['amount'] >= 0.5 * x['x_before'] * x['charge']: pers['jiyoung'][m] += 1
        askers = {a['src'] for a in g['asks']}
        for e in g['exits']:
            if e['slack'] < 1:
                pers['exit_below'][m] += 1
                if e['agent'] not in askers: pers['saebyeok'][m] += 1
out['personas'] = {k: dict(v, total=sum(v.values())) for k, v in pers.items()}
json.dump(out, open(SP + '/an3/out.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != 'd'}, ensure_ascii=False, indent=1, default=str)[:6000])
print(json.dumps({k: v for k, v in out['d'].items() if k != 'games'}, ensure_ascii=False))
