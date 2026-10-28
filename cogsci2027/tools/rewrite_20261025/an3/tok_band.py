"""3.2: tokens per pre-solve reply by margin band (non-solver replies, same filter as the EXIT bands)."""
import pickle, json, statistics as st
G = pickle.load(open('../audit6/G.pkl', 'rb'))
B = [('1 미만', 0, 1), ('1–2', 1, 2), ('2–4', 2, 4), ('4 이상', 4, 99)]
tok = {b: [] for b, _, _ in B}
for s, g in G.items():
    for r, rr in g['rounds'].items():
        n = len(rr['part']); F = 24000 / n
        solver = rr['res']['tried'][0] if rr['res']['tried'] else rr.get('rep')
        bal = {(c.get('phase'), c.get('tick')): c['balances'] for c in rr['cs'] if c['kind'] == 'talk'}
        for c in rr['calls']:
            if c['kind'] != 'talk' or c.get('phase') != 'prep' or c['agent'] == solver or n == 1: continue
            b0 = bal.get(('prep', c.get('tick')), {}).get(c['agent'])
            if b0 is None: continue
            for lab, lo, hi in B:
                if lo <= b0 / F < hi: tok[lab].append(c['used'])
out = {b: dict(n=len(v), med=st.median(v), mean=round(st.mean(v))) for b, v in tok.items()}
json.dump(out, open('tok_band.json', 'w'), ensure_ascii=False, indent=1); print(out)
