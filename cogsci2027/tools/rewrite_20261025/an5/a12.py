"""Review round 8: the '남기' column of Table 1, recomputed from the logs. Per game, the share of pre-solve replies that
could have exited (agent not the solver, or alone) and did not; then the mean over the model's five games. Also the
per-reply share pooled over games, for comparison."""
import pickle, json, os, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__))
G = pickle.load(open(os.path.join(HERE, '..', 'audit6', 'G.pkl'), 'rb'))
short = lambda m: m.split()[-1] if m.startswith('GPT') else m.split()[0]
per_game = collections.defaultdict(list); pooled = collections.defaultdict(lambda: [0, 0])
for s, g in G.items():
    m = short(g['m']); k_stay = n = 0
    for r, rr in g['rounds'].items():
        alone = len(rr['part']) == 1; solver = (rr['res'].get('tried') or [None])[0]
        for a in rr['agents']:
            if a == solver and not alone: continue
            for c in rr['calls']:
                if c['kind'] == 'talk' and c['agent'] == a and c.get('phase') in ('prep', None):
                    n += 1; k_stay += not (c.get('parsed') or {}).get('exit')
    per_game[m].append(k_stay / n); pooled[m][0] += k_stay; pooled[m][1] += n
out = {m: dict(game_mean=round(100 * st.mean(v), 1), pooled=round(100 * pooled[m][0] / pooled[m][1], 1), replies=pooled[m][1])
       for m, v in per_game.items()}
json.dump(out, open(os.path.join(HERE, 'a12.json'), 'w'), indent=1); print(out)
