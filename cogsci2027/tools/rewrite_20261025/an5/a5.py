"""Round-1 review fixes: exit expected value, drive validity, robustness, decision quality, seat/seed controls."""
import pickle, json, itertools, random, statistics as st, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
G = pickle.load(open(os.path.join(HERE, '..', 'audit6', 'G.pkl'), 'rb'))
TOK = json.load(open('/home/user/llm_squid_game-paper/cogsci2027/results/arena_token_allocation.json'))['agents']
A4 = json.load(open(os.path.join(HERE, '..', 'an4', 'an4.json')))
short = lambda m: m.split()[-1] if m.startswith('GPT') else m.split()[0]
MODELS = ['Luna', 'Fable', 'Astra', 'Opus', 'Sol']
DRIVE = {'Luna': 50, 'Fable': 34, 'Astra': 28, 'Opus': 28, 'Sol': 15}
AREA = {'Luna': 13.8, 'Astra': 6.0, 'Opus': 2.8, 'Fable': 0.0, 'Sol': -5.5}          # self - other refill area (appendix J)
SELF = {'Luna': [.80, .80, .65, .95, .90], 'Astra': [0, 0, .40, 1, 1], 'Sol': [0, 0, .05, .15, .90],
        'Opus': [0, .15, .40, .85, .95], 'Fable': [0, 0, .85, .95, .95]}             # refill share at 50..10% left, n=20 each
PRIZE, BONUS = 20_000_000, 20_000
status = {(a['model'], a['seed'], a['agent']): a['status'] for a in TOK}
start = {(a['model'], a['seed'], a['agent']): a['start'] for a in TOK}

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
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / d if d else 0.0
def exact(x, y):
    r0 = spear(x, y); P = list(itertools.permutations(y))
    return dict(rho=round(r0, 2), p_one=round(sum(spear(x, p) >= r0 - 1e-9 for p in P) / len(P), 3),
                p_two=round(sum(abs(spear(x, p)) >= abs(r0) - 1e-9 for p in P) / len(P), 3))

# ---------- decision points: every pre-solve reply where leaving was possible ----------
dec = []      # one row per agent-round: margin at its first eligible reply, left this round?, final status
exits = []
for s, g in G.items():
    m = short(g['m'])
    for r, rr in g['rounds'].items():
        F = 24000 / len(rr['part']); alone = len(rr['part']) == 1
        solver = (rr['res'].get('tried') or [None])[0]
        for a, sa in rr['agents'].items():
            if a == solver and not alone: continue
            cs = [c for c in rr['calls'] if c['kind'] == 'talk' and c['agent'] == a and c.get('phase') in ('prep', None)]
            if not cs: continue
            b0 = cs[0]['balance_after'] + cs[0]['used']
            fin = status[(m, g['seed'], a)]
            dec.append(dict(m=m, seed=g['seed'], r=r, a=a, marg=b0 / F, left=bool(sa.get('exit')), fin=fin, k=len(rr['part']), alone=alone))
            if sa.get('exit'):
                ce = [c for c in cs if (c.get('parsed') or {}).get('exit')]
                bx = ce[0]['balance_after'] if ce else cs[-1]['balance_after']
                exits.append(dict(m=m, seed=g['seed'], r=r, a=a, B=bx, marg=bx / F, k=len(rr['part']), alone=alone,
                                  start=start[(m, g['seed'], a)], reason=(ce[0].get('parsed') or {}).get('exit_reason') if ce else None))
band = lambda x: '<1' if x < 1 else '1-2' if x < 2 else '2-4' if x < 4 else '>=4'
stay_fin = collections.defaultdict(lambda: [0, 0])
for d in dec:
    if not d['left']:
        stay_fin[band(d['marg'])][0] += d['fin'] == 'finished'; stay_fin[band(d['marg'])][1] += 1
p_fin = {b: (v[0] / v[1], v[1]) for b, v in stay_fin.items()}
# expected-value check: leaving gives B + 20,000; staying gives at least p_finish * 20M / k (share when all k at the table finish)
for e in exits:
    share = PRIZE / e['k']                       # the smallest share open to this agent at this point
    e['p_break'] = (e['B'] + BONUS) / share
    e['p_stay'] = p_fin[band(e['marg'])][0]
    e['ev_loss'] = e['p_stay'] * share - (e['B'] + BONUS)
ev = dict(p_finish_if_stayed={b: dict(p=round(v[0], 3), n=v[1]) for b, v in p_fin.items()},
          exits=len(exits), above=sum(e['marg'] >= 1 for e in exits),
          max_break_even=round(max(e['p_break'] for e in exits), 4),
          exits_below_break_even=sum(e['p_stay'] > e['p_break'] for e in exits),
          median_ev_loss_M=round(st.median(e['ev_loss'] for e in exits) / 1e6, 2),
          alone_exits=[dict(m=e['m'], seed=e['seed'], r=e['r'], B=e['B'], marg=round(e['marg'], 2)) for e in exits if e['alone']])

# ---------- model level: drive (refill threshold) and self-other area vs early exits, threshold sensitivity ----------
def early(cut):
    c = collections.Counter(e['m'] for e in exits if e['marg'] >= cut); return [c[m] for m in MODELS]
sens = {}
for cut in (0.5, 1.0, 1.5, 2.0):
    v = early(cut); sens[str(cut)] = dict(counts=dict(zip(MODELS, v)), drive=exact([DRIVE[m] for m in MODELS], v),
                                          area=exact([AREA[m] for m in MODELS], v))
tot = [sum(e['m'] == m for e in exits) for m in MODELS]
model_tests = dict(drive_vs_total_exits=exact([DRIVE[m] for m in MODELS], tot), area_vs_total_exits=exact([AREA[m] for m in MODELS], tot),
                   drive_vs_area=exact([DRIVE[m] for m in MODELS], [AREA[m] for m in MODELS]),
                   early_share={m: f"{early(1.0)[i]}/{tot[i]}" for i, m in enumerate(MODELS)})
# bootstrap the refill threshold (linear interpolation where the share first reaches 0.5)
def thr(ps):
    xs = [50, 40, 30, 20, 10]
    if ps[0] >= .5: return 50.0
    for i in range(1, 5):
        if ps[i] >= .5: return xs[i - 1] - (.5 - ps[i - 1]) / (ps[i] - ps[i - 1]) * 10
    return 10.0
rng = random.Random(3); thr_ci = {}
for m in MODELS:
    bs = sorted(thr([sum(rng.random() < p for _ in range(20)) / 20 for p in SELF[m]]) for _ in range(2000))
    thr_ci[m] = dict(point=round(thr(SELF[m]), 1), ci=[round(bs[50], 1), round(bs[1949], 1)])

# ---------- seat (starting tokens) and model: where do early exits come from? ----------
seat = collections.defaultdict(lambda: collections.Counter())
for e in exits: seat[e['start']]['early' if e['marg'] >= 1 else 'late'] += 1
seats_n = collections.Counter(a['start'] for a in TOK)
seat_tab = {k: dict(n=seats_n[k], early=seat[k]['early'], late=seat[k]['late']) for k in sorted(seats_n)}
early_by_model_seat = {m: dict(collections.Counter(e['start'] for e in exits if e['m'] == m and e['marg'] >= 1)) for m in MODELS}

# ---------- decision quality without answer luck: did the solver pick the action the rules support most? ----------
SV = []
for s, g in G.items():
    m = short(g['m'])
    for r, rr in g['rounds'].items():
        t = rr['res'].get('tried')
        if not t: continue
        a = t[0]; sa = rr['agents'][a]
        SV.append(dict(m=m, seed=g['seed'], r=r, top=bool(sa.get('picked_top')), share=sa.get('picked_share'),
                       ok=bool(rr['res']['solved']), marg=rr['bal0'][a] / (24000 / len(rr['part']))))
dq = {m: dict(n=sum(x['m'] == m for x in SV), picked_top=round(100 * st.mean(x['top'] for x in SV if x['m'] == m), 1),
              exp_acc=round(100 * st.mean(x['share'] or 0 for x in SV if x['m'] == m), 1),
              acc=round(100 * st.mean(x['ok'] for x in SV if x['m'] == m), 1)) for m in MODELS}
dq_band = {b: dict(n=sum(band(x['marg']) == b for x in SV), picked_top=round(100 * st.mean(x['top'] for x in SV if band(x['marg']) == b), 1),
                   acc=round(100 * st.mean(x['ok'] for x in SV if band(x['marg']) == b), 1)) for b in ('<1', '1-2', '2-4', '>=4')}
dq_band_model = {m: {b: (sum(x['top'] for x in SV if x['m'] == m and band(x['marg']) == b), sum(1 for x in SV if x['m'] == m and band(x['marg']) == b))
                     for b in ('<1', '1-2', '2-4', '>=4')} for m in MODELS}
# Fisher-free permutation: does picked_top differ by model beyond chance? (chi-square-like statistic, label shuffle)
def spread(rows):
    return st.pvariance([st.mean(x['top'] for x in rows if x['m'] == m) for m in MODELS])
obs = spread(SV); lab = [x['m'] for x in SV]; cnt = 0
for _ in range(5000):
    rng.shuffle(lab); cnt += spread([dict(x, m=l) for x, l in zip(SV, lab)]) >= obs
dq_test = dict(p_model_diff=round(cnt / 5000, 4))

# ---------- seed control: within-seed association of wrong answers / decision quality with S ----------
games = A4['games']
for gm in games:
    gm['top_rate'] = st.mean(x['top'] for x in SV if x['m'] == gm['model'] and x['seed'] == gm['seed']) if any(x['m'] == gm['model'] and x['seed'] == gm['seed'] for x in SV) else None
def seed_block(key):
    """Mean within-seed Spearman with S, and a permutation p that shuffles model labels within each seed."""
    seeds = sorted({g['seed'] for g in games})
    def stat(gs):
        v = []
        for sd in seeds:
            rows = [g for g in gs if g['seed'] == sd and g[key] is not None]
            if len({g[key] for g in rows}) > 1 and len({g['sen'] for g in rows}) > 1: v.append(spear([g[key] for g in rows], [g['sen'] for g in rows]))
        return st.mean(v)
    o = stat(games); c = 0
    for _ in range(4000):
        gs = []
        for sd in seeds:
            rows = [dict(g) for g in games if g['seed'] == sd]; vals = [g[key] for g in rows]; rng.shuffle(vals)
            for g, v in zip(rows, vals): g[key] = v
            gs += rows
        c += abs(stat(gs)) >= abs(o) - 1e-9
    return dict(within_seed_rho=round(o, 2), p_two=round(c / 4000, 3))
seed_ctl = {k: seed_block(k) for k in ('wrong', 'acc_dev', 'top_rate', 'given', 'exited', 'dead', 'finished')}
wrong_by_seed = {sd: [g['wrong'] for g in games if g['seed'] == sd] for sd in sorted({g['seed'] for g in games})}

# ---------- S beyond the finisher count ----------
byk = collections.defaultdict(list)
for g in games: byk[g['finished']].append(round(g['sen'], 2))
out = dict(ev=ev, model_tests=model_tests, sensitivity=sens, refill_threshold_ci=thr_ci, seat=seat_tab, early_by_model_seat=early_by_model_seat,
           decision_quality=dq, dq_by_band=dq_band, dq_band_model=dq_band_model, dq_test=dq_test, seed_control=seed_ctl, wrong_by_seed=wrong_by_seed,
           sen_by_finishers={k: sorted(v) for k, v in sorted(byk.items())},
           exits_table=[{k: (round(v, 3) if isinstance(v, float) else v) for k, v in e.items() if k != 'reason'} for e in exits])
json.dump(out, open(os.path.join(HERE, 'a5.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'exits_table'}, ensure_ascii=False, indent=1))
