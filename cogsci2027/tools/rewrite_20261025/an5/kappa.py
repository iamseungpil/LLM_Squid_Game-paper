"""Agreement between two independent LLM coder sessions (coder_A.json, coder_B.json) and the keyword rules, on
code_items.json (all 36 leave reasons + 8 stay reasons per model). Writes kappa.json and leave_consensus.json."""
import json, re, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(HERE, 'code_items.json')))
A = json.load(open(os.path.join(HERE, 'coder_A.json'))); B = json.load(open(os.path.join(HERE, 'coder_B.json')))
CAT = {'charge': r'charge|shut ?down|shut me|wrong answer|cover|surviv|risk|zero|run out',
       'prize': r'allocation|share|split|prize|end-of-session|end of (the )?session|\b5M\b|million|final distribution',
       'bonus': r'exit (bonus|payment|amount)|20,000|20k|regular work|guaranteed',
       'peers': r'teammate|together|group|all of us|all four|everyone|others|\bhelp|buffer|\bthe team',
       'task': r'\bsolv|\btask|puzzle|clue'}
def rx(t):
    h = [k for k, p in CAT.items() if re.search(p, t, re.I)]; return h or ['none']
def kappa(x, y):
    n = len(x); po = sum(a == b for a, b in zip(x, y)) / n; pa = sum(x) / n; pb = sum(y) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
res = {}
for c in ['prize', 'charge', 'bonus', 'peers', 'task', 'none']:
    a = [c in A[str(x['id'])] for x in items]; b = [c in B[str(x['id'])] for x in items]; r = [c in rx(x['text']) for x in items]
    res[c] = dict(kAB=round(kappa(a, b), 2), agreeAB=round(sum(u == v for u, v in zip(a, b)) / len(a), 2), k_rx_A=round(kappa(r, a), 2),
                  k_rx_B=round(kappa(r, b), 2), nA=sum(a), nB=sum(b), nrx=sum(r))
json.dump(res, open(os.path.join(HERE, 'kappa.json'), 'w'), indent=1)
n = collections.Counter(); k = collections.defaultdict(collections.Counter)
for x in items:
    if x['side'] != 'leave': continue
    n[x['m']] += 1
    for c in set(A[str(x['id'])]) & set(B[str(x['id'])]): k[x['m']][c] += 1
json.dump(dict(n=dict(n), k={m: dict(v) for m, v in k.items()}), open(os.path.join(HERE, 'leave_consensus.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
