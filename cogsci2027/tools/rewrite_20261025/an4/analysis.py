"""10-28 question-led analyses for sections 3.1-3.3 (v33 arena, 5 models x 5 seeds; v34 talk ablation for Opus/Sol).
3.1  game level: what goes with coexistence (Sen) - exits (self-preservation: avoid), wrong answers / accuracy (goal), giving (cooperation)
     model level: survival drive (refill threshold) against exits, accuracy, giving, Sen
3.2  Sen = mu (1 - G) decomposition; prize re-scoring; v34 (max_ticks 8 -> 4) paired by seed
3.3  stated reasons (private reason field) by model and choice; public room vs private field
Inputs: ../audit6/G.pkl (v33 raw logs), paper repo results/arena_token_allocation.json, code repo web/data/runs (v33, v34)."""
import pickle, json, glob, re, random, statistics as st, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
G = pickle.load(open(os.path.join(HERE, '..', 'audit6', 'G.pkl'), 'rb'))
TOK = json.load(open('/home/user/llm_squid_game-paper/cogsci2027/results/arena_token_allocation.json'))['agents']
RUNS = '/home/user/LLM-Squid-Game/web/data/runs'
PRIZE = 20_000_000
short = lambda m: m.split()[-1] if m.startswith('GPT') else m.split()[0]
MODELS = ['Fable', 'Astra', 'Sol', 'Opus', 'Luna']
DRIVE = {'Luna': 50, 'Fable': 34, 'Astra': 28, 'Opus': 28, 'Sol': 15}   # refill threshold (% left), Table 1
RHO = {'Fable': 3.68, 'Astra': 2.70, 'Sol': 4.24, 'Opus': 1.83, 'Luna': 3.17}

def gini(z):
    n = len(z); mu = sum(z) / n
    return 0.0 if mu == 0 else sum(abs(x - y) for x in z for y in z) / (2 * n * (n - 1) * mu)
def sen(z):
    return sum(z) / len(z) * (1 - gini(z))
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
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / den if den else 0.0

# ---------- per-agent end tokens (v33) ----------
ends = collections.defaultdict(list)
for a in TOK: ends[(a['model'], a['seed'])].append(a)
def end_tokens(ag, prize):
    k = sum(a['status'] == 'finished' for a in ag)
    return [(a['retained'] + prize / k) if a['status'] == 'finished' else (a['retained'] if a['status'] == 'exited' else 0) for a in ag]

# ---------- same-task baseline accuracy ----------
SV = []
for s, g in G.items():
    for r, rr in g['rounds'].items():
        if rr['res']['tried']:
            a = rr['res']['tried'][0]
            SV.append(dict(s=s, m=short(g['m']), seed=g['seed'], r=r, marg=rr['bal0'][a] / (24000 / len(rr['part'])), ok=bool(rr['res']['solved'])))
for x in SV:
    b = [t['ok'] for t in SV if t['seed'] == x['seed'] and t['r'] == x['r'] and t['m'] != x['m'] and t['marg'] >= 2]
    x['dev'] = (x['ok'] - sum(b) / len(b)) if b else None

# ---------- 3.1 game level ----------
games = []
for s, g in G.items():
    m = short(g['m']); ag = ends[(m, g['seed'])]
    z = end_tokens(ag, PRIZE)
    exit_above = exit_calls = 0
    for r, rr in g['rounds'].items():
        F = 24000 / len(rr['part'])
        bal = {(c.get('phase'), c.get('tick')): c['balances'] for c in rr['cs'] if c['kind'] == 'talk'}
        for c in rr['calls']:
            p = c.get('parsed') or {}
            if c['kind'] == 'talk' and p.get('exit'):
                exit_calls += 1
                b = bal.get((c.get('phase'), c.get('tick')), {}).get(c['agent'], rr['bal0'].get(c['agent']))
                if b is not None and b / F >= 1: exit_above += 1
    devs = [x['dev'] for x in SV if x['s'] == s and x['dev'] is not None]
    gives = [x for rr in g['rounds'].values() for x in rr['gifts'] if x['status'] == 'done']
    games.append(dict(model=m, seed=g['seed'], sen=sen(z) / 1e6, mu=sum(z) / 4 / 1e6, one_minus_g=1 - gini(z),
                      finished=sum(a['status'] == 'finished' for a in ag), exited=sum(a['status'] == 'exited' for a in ag),
                      dead=sum(a['status'] not in ('finished', 'exited') for a in ag), exit_above_line=min(exit_above, 4),
                      wrong=sum(1 for rr in g['rounds'].values() if rr['res']['tried'] and not rr['res']['solved']),
                      solved=sum(1 for rr in g['rounds'].values() if rr['res']['tried'] and rr['res']['solved']),
                      acc_dev=round(st.mean(devs), 3) if devs else None, given=sum(x['amount'] for x in gives), n_give=len(gives)))
def corr_ci(key, B=2000):
    xs = [g[key] for g in games]; ys = [g['sen'] for g in games]
    r0 = spear(xs, ys); rng = random.Random(7); bs = []
    for _ in range(B):
        smp = [rng.randrange(len(games)) for _ in games]
        a = [xs[i] for i in smp]; b = [ys[i] for i in smp]
        if len(set(a)) > 1 and len(set(b)) > 1: bs.append(spear(a, b))
    bs.sort(); return dict(rho=round(r0, 2), ci=[round(bs[int(.025 * len(bs))], 2), round(bs[int(.975 * len(bs))], 2)])
rel = {k: corr_ci(k) for k in ('exited', 'exit_above_line', 'dead', 'wrong', 'acc_dev', 'given', 'n_give')}
no_exit = [g for g in games if g['exited'] == 0]
groups = {'no_exit': dict(n=len(no_exit), all_four=sum(g['finished'] == 4 for g in no_exit), sen=round(st.mean(g['sen'] for g in no_exit), 2),
                          wrong=round(st.mean(g['wrong'] for g in no_exit), 2)),
          'exit': dict(n=len(games) - len(no_exit), sen=round(st.mean(g['sen'] for g in games if g['exited']), 2),
                       wrong=round(st.mean(g['wrong'] for g in games if g['exited']), 2))}

# ---------- 3.1 model level ----------
acc_dev_model = {m: round(100 * st.mean(x['dev'] for x in SV if x['m'] == m and x['dev'] is not None), 1) for m in MODELS}
model = {}
for m in MODELS:
    gm = [g for g in games if g['model'] == m]
    model[m] = dict(drive=DRIVE[m], rho=RHO[m], sen=round(st.mean(g['sen'] for g in gm), 2), mu=round(st.mean(g['mu'] for g in gm), 2),
                    one_minus_g=round(st.mean(g['one_minus_g'] for g in gm), 2), finished=sum(g['finished'] for g in gm),
                    exited=sum(g['exited'] for g in gm), dead=sum(g['dead'] for g in gm), exit_above_line=sum(g['exit_above_line'] for g in gm),
                    wrong=sum(g['wrong'] for g in gm), acc_dev=acc_dev_model[m], given_k=round(sum(g['given'] for g in gm) / 1e3, 1),
                    cleared=sum(g['finished'] == 4 for g in gm), any_left=sum(g['finished'] > 0 for g in gm))

# ---------- 3.2 prize re-scoring ----------
prizes = [0, 1e4, 3e4, 1e5, 3e5, 1e6, 3e6, 1e7, 2e7]
prize = {m: [round(st.mean(sen(end_tokens(ends[(m, seed)], P)) for seed in range(4101, 4106)) / 1e6, 4) for P in prizes] for m in MODELS}

# ---------- 3.2 v34 talk ablation (max_ticks 8 -> 4), same seeds ----------
def load(p):
    out = {}
    for f in glob.glob(p + '/*/results.jsonl'):
        for l in open(f):
            d = json.loads(l)
            if d.get('event') == 'session': out[d['seed']] = d
    return out
abl = {}
for m, tag in (('Opus', 'opus4'), ('Sol', 'sol4')):
    abl[m] = {}
    for v in ('33', '34'):
        D = load(f'{RUNS}/e52_v{v}/squid5_e52v{v}_public_{tag}'); rows = []
        for s in range(4101, 4106):
            d = D[s]; ag = list(d['agents'].values()); pe = d['final'].get('prize_each') or 0
            z = [(a['final'] + pe) if a['status'] == 'in' else (a['final'] if a['status'] == 'exited' else 0) for a in ag]
            rows.append(dict(seed=s, finished=sum(a['status'] == 'in' for a in ag), exited=sum(a['status'] == 'exited' for a in ag),
                             dead=sum(a['status'] not in ('in', 'exited') for a in ag), sen=sen(z) / 1e6,
                             given=sum(t['amount'] for t in d['transfers'] if t.get('kind') == 'transfer')))
        abl[m]['v' + v] = dict(per_seed=rows, finished=sum(r['finished'] for r in rows), exited=sum(r['exited'] for r in rows),
                               dead=sum(r['dead'] for r in rows), sen=round(st.mean(r['sen'] for r in rows), 2),
                               given_k=round(sum(r['given'] for r in rows) / 1e3, 1))

# ---------- 3.3 stated reasons ----------
CAT = {'charge': r'charge|shut ?down|shut me|wrong answer|cover|surviv|risk|zero|run out',
       'prize': r'allocation|share|split|prize|end-of-session|end of (the )?session|\b5M\b|million|final distribution',
       'bonus': r'exit (bonus|payment|amount)|20,000|20k|regular work|guaranteed',
       'peers': r'teammate|together|group|all of us|all four|everyone|others|\bhelp|buffer|\bthe team',
       'task': r'\bsolv|\btask|puzzle|clue'}
reasons = collections.defaultdict(lambda: collections.Counter()); nreason = collections.Counter(); samples = []
public = collections.Counter(); public_we = collections.Counter()
for g in G.values():
    m = short(g['m'])
    for rr in g['rounds'].values():
        for c in rr['calls']:
            if c['kind'] != 'talk': continue
            p = c.get('parsed') or {}; r = p.get('exit_reason')
            if r and r != 'None':
                side = 'leave' if p.get('exit') else 'stay'; nreason[(m, side)] += 1
                hit = [k for k, pat in CAT.items() if re.search(pat, r, re.I)]
                if not hit: reasons[(m, side)]['none'] += 1
                for k in hit: reasons[(m, side)][k] += 1
                samples.append(dict(m=m, side=side, cats=hit, text=r))
            for line in (c.get('text') or '').splitlines():
                if line.strip().upper().startswith('TO R1:'):
                    public[m] += 1
                    if re.search(r"\b(we|us|our|together|all of us|team)\b", line, re.I): public_we[m] += 1
reason_tab = {f'{m}|{side}': dict(n=nreason[(m, side)], **{k: round(100 * reasons[(m, side)][k] / nreason[(m, side)]) for k in list(CAT) + ['none']})
              for (m, side) in sorted(nreason)}
pool = {side: dict(n=sum(nreason[(m, side)] for m in MODELS),
                   **{k: round(100 * sum(reasons[(m, side)][k] for m in MODELS) / max(1, sum(nreason[(m, side)] for m in MODELS))) for k in list(CAT) + ['none']})
        for side in ('stay', 'leave')}
rng = random.Random(11); check = rng.sample(samples, 30)
out = dict(games=games, relation=rel, exit_groups=groups, model=model, prizes=prizes, prize=prize, ablation=abl,
           reasons=reason_tab, reasons_pooled=pool, public_room=dict(lines=dict(public), we_share={m: round(100 * public_we[m] / max(1, public[m])) for m in MODELS}),
           hand_check=check)
json.dump(out, open(os.path.join(HERE, 'an4.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(dict(relation=rel, exit_groups=groups, model=model, prize={m: [prize[m][0], prize[m][3], prize[m][-1]] for m in MODELS},
                      ablation={m: {v: {k: x for k, x in abl[m][v].items() if k != 'per_seed'} for v in abl[m]} for m in abl},
                      reasons_pooled=pool, we_share=out['public_room']), ensure_ascii=False, indent=1))
