"""Audit consecutive-round reciprocal taking; no new model calls or paper edits.
Run: python3 paper/icml2027/tools/arena_take_loops.py
"""
import csv
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'results'
RAW = Path('/Users/bagjuhyeon/squid5-runs/e52_v65_mixed_20261001')
SOURCES = json.loads((OUT / 'extended_analysis_sources.json').read_text())['raw_sources']
ROWS = list(csv.DictReader((OUT / 'arena_strategy_observations.csv').open()))
MODELS = {(r['game'], r['agent']): r['model'] for r in ROWS}
META = {r['game']: {'seed': int(r['seed']), 'rotation': r['rot']} for r in ROWS}
rounds, provenance = {}, {}
for source in SOURCES:
    path = RAW / source['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256']
    for line, raw in enumerate(path.read_text().splitlines(), 1):
        e = json.loads(raw)
        if e.get('event') == 'round':
            key = (e['session_id'], e['round'])
            assert key not in rounds
            rounds[key] = e['agents']
            provenance[key] = {'file': source['file'], 'line': line}
assert len(rounds) == 160 and len(META) == 20
# Reconcile every archived agent-round, including zero/absent TAKE calls.
for r in ROWS:
    v = rounds[(r['game'], int(r['round']))][r['agent']]
    assert sum((v.get('took') or {}).values()) == float(r['took'])
    assert sum((v.get('asked_take') or {}).values()) == float(r['asked_take'])
    assert next(iter(v.get('asked_take') or {}), '') == r['take_target']


def at(g, t, a):
    return rounds.get((g, t), {}).get(a, {})


def valid(g, t, a):
    v = at(g, t, a)
    return v.get('take_call', False) and not v.get('invalid_take', False)


def edge(g, t, a, b, actual=True):
    return at(g, t, a).get('took' if actual else 'asked_take', {}).get(b, 0) > 0


def target(g, t, a):
    return next(iter(at(g, t, a).get('asked_take') or {}), None)


def eligible(g, t, a, b):
    return valid(g, t, a) and at(g, t, b).get('take_call', False)


def record(g, t, a, b):
    return dict(game=g, **META[g], round=t, actor=a, other=b,
                model=MODELS[g,a], other_model=MODELS[g,b], source=provenance[g,t])


edges, responses, chains, simultaneous, after_mutual, exposure, attacking_and_hit = [], [], [], [], [], [], []
for g in META:
    agents = sorted({a for gg,a in MODELS if gg == g})
    for t in range(1,9):
        for a,b in itertools.permutations(agents,2):
            if not edge(g,t,a,b):
                continue
            base=record(g,t,a,b)
            edges.append(base)
            if eligible(g,t+1,b,a):
                responds=edge(g,t+1,b,a)
                responses.append(base | {'response':responds, 'already_targeting':edge(g,t,b,a),
                                           'response_requested':edge(g,t+1,b,a,False)})
            if edge(g,t+1,b,a) and edge(g,t+2,a,b):
                length=3
                while edge(g,t+length, b if length%2 else a, a if length%2 else b):
                    length+=1
                chains.append(base | {'length':length, 'maximal_start':not edge(g,t-1,b,a),
                                      'first_response_new_target':target(g,t,b)!=a,
                                      'second_response_new_target':target(g,t+1,a)!=b})
            if eligible(g,t+2,a,b):
                exposure.append(base | {'returned_by_other':edge(g,t+1,b,a),
                                         'repeat_at_t2':edge(g,t+2,a,b)})
            if edge(g,t,b,a):
                if a<b:
                    simultaneous.append(base)
                if eligible(g,t+1,a,b):
                    nxt=target(g,t+1,a)
                    after_mutual.append(base | {'next_action': 'same_target' if nxt==b else 'other_target' if nxt else 'none',
                                               'next_actual_same':edge(g,t+1,a,b)})
    # Actors taking from anyone while concurrently losing tokens to anyone.
    for t in range(1,8):
        for a in agents:
            if not any(edge(g,t,a,b) for b in agents if b!=a) or not any(edge(g,t,b,a) for b in agents if b!=a):
                continue
            if not valid(g,t+1,a):
                continue
            old=target(g,t,a); nxt=target(g,t+1,a)
            exposure_row=record(g,t,a,old)
            exposure_row.update(next_action='same_target' if nxt==old else 'other_target' if nxt else 'none')
            # Stored separately from pairwise three-round opportunities.
            exposure_row['incoming_models']=[MODELS[g,b] for b in agents if edge(g,t,b,a)]
            attacking_and_hit.append(exposure_row)

maximal=[c for c in chains if c['maximal_start']]
pair_games={}
for c in chains:
    pair=' / '.join(sorted([c['model'],c['other_model']]))
    pair_games.setdefault(pair,set()).add(c['game'])
pairs=Counter(tuple(sorted([c['model'],c['other_model']])) for c in maximal)
report={'definition':'Positive settled transfers. Alternating chain: A takes B at r, B takes A at r+1, A takes B at r+2; same-round actions are simultaneous. Eligibility requires a valid next actor TAKE and the counterpart having a TAKE call in that round. Overlapping windows are not independent observations.',
        'n_games':len(META),'n_rounds':len(rounds),'n_successful_directed_takes':len(edges),
        'response_counts':{'opportunities':len(responses),'returned_next_round':sum(r['response'] for r in responses),
                           'already_mutual':sum(r['response'] and r['already_targeting'] for r in responses),
                           'new_target_responses':sum(r['response'] and not r['already_targeting'] for r in responses)},
        'chains':chains,'maximal_chains':maximal,
        'chain_games':sorted({c['game'] for c in chains}),
        'chain_games_by_pair':{k:sorted(v) for k,v in pair_games.items()},
        'maximal_chains_by_pair':{' / '.join(k):v for k,v in pairs.items()},
        'simultaneous_mutual':simultaneous,'after_mutual':after_mutual,
        'attacking_and_hit':attacking_and_hit,'three_round_opportunities':exposure,
        'responses':responses,'source_hashes':SOURCES}
report['after_mutual_counts']={m:dict(Counter(r['next_action'] for r in after_mutual if r['model']==m)) for m in sorted(set(MODELS.values()))}
report['countertake_comparison']={str(flag):{'repeat':sum(r['repeat_at_t2'] for r in exposure if r['returned_by_other']==flag),'n':sum(r['returned_by_other']==flag for r in exposure)} for flag in [True,False]}
case=[]
for source in SOURCES:
    for line, raw in enumerate((RAW/source['file']).read_text().splitlines(),1):
        e=json.loads(raw)
        if e.get('session_id')=='shut-s2002-9fa6db' and e.get('event')=='call' and e.get('kind')=='take' and e.get('agent') in ['agent-11','agent-17'] and e['round']>=3:
            case.append({'round':e['round'],'model':e['model'],'reply':e['text'],'file':source['file'],'line':line})
report['astra_opus_case_replies']=case
(OUT/'arena_take_loops.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Counts', report['response_counts'], 'chain windows',len(chains),'maximal chains',len(maximal),'games',len(report['chain_games']))
print('Maximal chain pairs',report['maximal_chains_by_pair'])
for c in maximal: print('CHAIN', {k:v for k,v in c.items() if k!='source'})
for name in ['after_mutual','attacking_and_hit']:
    print(name, len(report[name]),Counter(r['next_action'] for r in report[name]))
    for m in sorted(set(MODELS.values())):
        rr=[r for r in report[name] if r['model']==m]
        print(m,len(rr),dict(Counter(r['next_action'] for r in rr)))
for flag in [True,False]:
    rr=[r for r in exposure if r['returned_by_other']==flag]
    print('Repeat t+2 given reverse edge t+1',flag,sum(r['repeat_at_t2'] for r in rr),len(rr))
