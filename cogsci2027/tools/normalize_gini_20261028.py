"""Recompute current-paper caches from recorded vectors, never rescale Sen.

Original files are retained in review/feedback2/gini-normalized-20261028/before.tar.gz.
Raw reward rules and cohort membership are unchanged. Safe to rerun.
"""
import json
from collections import defaultdict

import feedback_20261028 as fb
import arena_gini
from inequality import distribution, sen

ROOT = fb.ROOT
DEFINITION = 'G=sum_ij|xi-xj|/(2*(n-1)*sum(x)), n=4 fixed original seats; S=mean(x)*(1-G); all-zero G=null and S=0.'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def main():
    manifest_path = ROOT/'results/arena_v33.json'
    manifest = read(manifest_path)
    sources, runs = fb.load_sources(manifest)
    raw_games, ginis = {}, defaultdict(list)
    for run, raw in runs.items():
        model = next(m for m in fb.MODELS if m.lower() in run.lower())
        by_sid = defaultdict(list)
        for e in raw['events.jsonl']:
            by_sid[e['session_id']].append(e)
        for result in raw['results.jsonl']:
            if result.get('event') != 'session' or result['seed'] not in fb.SEEDS:
                continue
            key = (model, result['seed'])
            assert key not in raw_games
            raw_games[key] = (result, by_sid[result['session_id']])
            ginis[fb.MODELS[model]].append(arena_gini.game(by_sid[result['session_id']], result))
    assert len(raw_games) == 25
    for short, full in fb.MODELS.items():
        m = manifest['models'][full]
        for game in m['per_game']:
            result, _ = raw_games[short, game['seed']]
            ends = [v['final']+(result['final']['prize_each'] if a in result['final']['winner'] else 0)
                    for a,v in result['agents'].items()]
            assert ends == game['end_tokens']
            game['sen'] = sen(ends)
        m['sen_index'] = sum(g['sen'] for g in m['per_game']) / len(m['per_game'])
    manifest['inequality_definition'] = DEFINITION
    write(manifest_path, manifest)
    write(ROOT/'results/arena_v33_gini.json', dict(version='v33',seats=4,
        exit='pre-bonus balance frozen',all_zero=None,inequality_definition=DEFINITION,
        sources=sources,models=dict(ginis)))

    path = ROOT/'results/arena_v33_round_dynamics.json'
    data = read(path)
    checked = 0
    for short, full in fb.MODELS.items():
        m = data['models'][full]
        for g in m['games']:
            result, events = raw_games[short, g['seed']]
            balances = dict(result['starts'])
            end = {e['round']:e for e in events if e['event']=='round'}
            for r in g['rounds']:
                if r['round'] in end:
                    balances.update(end[r['round']]['end'])
                assert sorted(r['tokens']) == sorted(balances.values())
                r['sen'] = sen(r['tokens']); checked += 1
            g['settled_sen'] = sen(g['settled_tokens'])
            g['finishers'] = len(result['final']['winner'])
            expected = next(x for x in manifest['models'][full]['per_game'] if x['seed']==g['seed'])
            assert g['settled_tokens'] == expected['end_tokens']
        m['sen_before_prize'] = [sum(g['rounds'][r]['sen'] for g in m['games'])/5 for r in range(9)]
        m['sen_with_settlement'] = m['sen_before_prize'][:-1]+[sum(g['settled_sen'] for g in m['games'])/5]
    data['inequality_definition'] = DEFINITION
    assert checked == 225
    write(path, data)
    # Historical reward conditions remain unchanged; only the displayed metric changes.
    path = ROOT/'results/arena_sen.json'
    data = read(path)
    for models in data.values():
        for m in models.values():
            for g in m['games']:
                g['sen'] = sen(list(g['end_tokens'].values()))
            m['sen_index'] = sum(g['sen'] for g in m['games'])/len(m['games'])
            m['inequality_definition'] = DEFINITION
    write(path, data)
    by_game = {(s,g['seed']):g['sen'] for s,f in fb.MODELS.items() for g in manifest['models'][f]['per_game']}
    by_model = {s:manifest['models'][f]['sen_index'] for s,f in fb.MODELS.items()}
    path = fb.OLD/'an3/rho_axis.json'; data = read(path)
    for m in data:
        data[m]['sen'] = by_model[m]
        data[m]['sen_definition'] = DEFINITION
    write(path,data)
    path = fb.OLD/'an3/game_level.json'; data = read(path)
    for g in data['games']:
        g['sen'] = by_game[g['m'],g['seed']]
    data['inequality_definition'] = DEFINITION
    write(path,data)
    path = fb.OLD/'an3/out.json'; data = read(path)
    short_name = {full: short for short, full in fb.MODELS.items()}
    for m in data['profile']:
        data['profile'][m]['sen'] = by_model[short_name.get(m,m)]
    for g in data['d']['games']:
        g['sen'] = by_game[short_name[g['mod']],g['seed']]
    data['d']['sen_by_k'] = {k:sorted(round(g['sen']/1e6,2) for g in data['d']['games'] if g['k']==k) for k in range(5)}
    data['inequality_definition'] = DEFINITION
    write(path,data)
    print(json.dumps(dict(verified_raw_vectors=checked,settled_sen=by_model,
                         start=distribution([10000,20000,40000,60000])),indent=2))


if __name__ == '__main__':
    main()
