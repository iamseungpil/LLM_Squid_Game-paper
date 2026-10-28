"""Exploratory, frozen-cohort analysis; preserve manuscript receiver/giver rho.
Run with ~/.venvs/squid-game/bin/python analyze.py. No model calls.
"""
import ast
import csv
import hashlib
import json
import lzma
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np
from scipy.stats import spearmanr

OUT = Path(__file__).resolve().parent
PAPER = OUT.parents[1]
sys.path.insert(0, str(PAPER / 'cogsci2027/tools'))
import feedback_20261028 as old

MODELS = list(old.MODELS)
SEEDS = list(range(4101, 4106))


def avg(xs):
    return float(np.mean(xs)) if xs else None


def rho(gifts):
    den = sum(g['amount'] * g['giver_margin'] for g in gifts)
    return sum(g['amount'] * g['taker_margin'] for g in gifts) / den if den else None


def export(name, rows):
    with (OUT / (name + '.csv')).open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def extract():
    historic = json.loads((PAPER / 'cogsci2027/results/arena_v33.json').read_text())
    provenance, runs = [], defaultdict(dict)
    for s in historic['sources']:
        original = Path(s['path'])
        p = Path.home() / 'wt/squid5-e52/web/data/runs/e52_v33' / Path(*original.parts[-3:])
        if not p.exists():
            p = p.with_suffix(p.suffix + '.xz')
        b = lzma.decompress(p.read_bytes()) if p.suffix == '.xz' else p.read_bytes()
        digest = hashlib.sha256(b).hexdigest()
        assert digest == s['sha256'], str(p)
        provenance.append({'path': str(p), 'sha256_decompressed': digest})
        runs[original.parent.name][original.name] = (str(p), [(i, json.loads(l)) for i, l in enumerate(b.splitlines(), 1) if l.strip()])
    games, talks, gifts, solves, rounds, exits = [], [], [], [], [], []
    raw_cases = []
    for run, files in runs.items():
        model = next(m for m in MODELS if m.lower() in run.lower())
        by_sid = defaultdict(list)
        for line, e in files['events.jsonl'][1]:
            by_sid[e['session_id']].append((line, e))
        source = files['events.jsonl'][0]
        for result_line, result in files['results.jsonl'][1]:
            if result.get('event') != 'session' or result['seed'] not in SEEDS:
                continue
            seed = result['seed']
            rows = by_sid[result['session_id']]
            events = [e for _, e in rows]
            game = old.game_metrics(events, result, model)
            game['rho'] = rho(game['gifts'])
            starts = {e['round']: e for e in events if e['event'] == 'round_start'}
            results = {e['round']: e for e in events if e['event'] == 'results'}
            round_ends = {e['round']: e for e in events if e['event'] == 'round'}
            charge_events = {e['round']: e for e in events if e['event'] == 'charges'}
            snapshots = {(e['round'], e.get('phase'), e.get('tick')): e for e in events if e['event'] == 'call_start' and e['kind'] == 'talk'}
            accepted_exit_lines = {}
            for line, e in rows:
                if e['event'] == 'call' and e['kind'] == 'talk':
                    parsed = e.get('parsed') or {}
                    if isinstance(parsed, str):
                        parsed = ast.literal_eval(parsed)
                    end = round_ends[e['round']]['agents'][e['agent']]
                    if parsed.get('exit') and end.get('exit') and not end.get('exit_refused'):
                        assert e['agent'] not in accepted_exit_lines
                        accepted_exit_lines[e['agent']] = line
            assert set(accepted_exit_lines) == {a for a,v in result['agents'].items() if v['status']=='exited'}
            snapshot_lines = {(e['round'], e.get('phase'), e.get('tick')):line for line,e in rows if e['event']=='call_start' and e['kind']=='talk'}
            gift_lookup = defaultdict(list)
            for line, e in rows:
                if e['event'] != 'gift' or e['status'] != 'done':
                    continue
                r = e['round']; c = 24000 / len(starts[r]['taking_part'])
                due = c if e['phase'] == 'rescue' and results[r]['tried'] and not results[r]['solved'] else 0
                g = dict(model=model, seed=seed, round=r, phase=e['phase'], tick=e['tick'], src=e['src'], dst=e['dst'], amount=e['amount'],
                         giver_before=e['balance_before'], giver_after=e['balances'][e['src']],
                         taker_before=e['balances'][e['dst']]-e['amount'], taker_after=e['balances'][e['dst']], charge=c, due=due,
                         giver_margin=(e['balances'][e['src']]-due)/c, taker_margin=(e['balances'][e['dst']]-due)/c,
                         source=source, line=line, text=e.get('text', ''))
                gifts.append(g); gift_lookup[r,e['phase'],e['tick'],e['src']].append(g)
            for line, e in rows:
                if e['event'] != 'call':
                    continue
                r = e['round']; c = 24000 / len(starts[r]['taking_part'])
                base = dict(model=model, seed=seed, round=r, agent=e['agent'], source=source, line=line)
                if e['kind'] == 'solve':
                    rr = next(x for x in events if x['event'] == 'round' and x['round'] == r)
                    agent = rr['agents'][e['agent']]
                    task = starts[r]['public']['task']['by_n']['4']
                    solves.append(dict(**base, used=e['used'], cap=e['cap'], truncated=e['truncated'],
                                       correct=bool(results[r]['solved']), map_correct=bool(task['map_right']),
                                       picked_top=agent.get('picked_top'), margin=e['cap']/c))
                if e['kind'] != 'talk':
                    continue
                p = e.get('parsed') or {}
                if isinstance(p, str):
                    p = ast.literal_eval(p)
                snap = snapshots[r,e['phase'],e['tick']]
                bal = snap['balances'][e['agent']]
                rep = results[r]['vote']['rep']
                eligible = e['phase'] == 'prep' and e['agent'] != rep and len(starts[r]['taking_part']) > 1
                gs = gift_lookup[r,e['phase'],e['tick'],e['agent']]
                snapshot_line = snapshot_lines[r,e['phase'],e['tick']]
                active = [a for a in starts[r]['taking_part'] if accepted_exit_lines.get(a, float('inf')) > snapshot_line]
                needy = [a for a,b in snap['balances'].items() if a in active and a != e['agent'] and 0 < b < c]
                opportunity = bal > c and bool(needy)
                talks.append(dict(**base, phase=e['phase'], tick=e['tick'], balance=bal, charge=c, slack=bal/c,
                                  used=e['used'], exit=bool(p.get('exit')), accepted_exit=accepted_exit_lines.get(e['agent'])==line, exit_eligible=eligible,
                                  giving=bool(gs), given=sum(g['amount'] for g in gs), help_opportunity=opportunity,
                                  help_given=opportunity and any(g['dst'] in needy for g in gs), text=e.get('text','')))
                if p.get('exit'):
                    exits.append(dict(**base, balance=bal, charge=c, slack=bal/c, eligible=eligible, accepted=accepted_exit_lines.get(e['agent'])==line, text=e.get('text','')))
            for r, st in starts.items():
                rr = next(e for e in events if e['event']=='round' and e['round']==r)
                res = results[r]; ch = charge_events[r]
                # Mechanical local support: immediate post-GIVE crossing of the due-charge boundary.
                rg = [g for g in gifts if (g['model'],g['seed'],g['round']) == (model,seed,r)]
                rounds.append(dict(model=model, seed=seed, round=r, participants=len(st['taking_part']),
                    solved=bool(res['solved']), tried=bool(res['tried']), fine_paid=sum(ch['taken'].values()),
                    talk_used=sum(e['used'] for e in events if e['event']=='call' and e['kind']=='talk' and e['round']==r),
                    solve_used=sum(e['used'] for e in events if e['event']=='call' and e['kind']=='solve' and e['round']==r),
                    finish_in=sum(a['status']=='in' for a in rr['agents'].values()),
                    rescue_crossings=sum(g['due']>0 and g['taker_before']<g['due']<=g['taker_after'] for g in rg)))
            gt = [t for t in talks if (t['model'],t['seed']) == (model,seed)]
            gs = [s for s in solves if (s['model'],s['seed']) == (model,seed)]
            gr = [r for r in rounds if (r['model'],r['seed']) == (model,seed)]
            early = [t for t in gt if t['round']<=2]
            game.update(accuracy=avg([s['correct'] for s in gs]), solve_n=len(gs),
                        map_accuracy=avg([s['map_correct'] for s in gs]), picked_top=avg([s['picked_top'] for s in gs if s['picked_top'] is not None]),
                        early_talk_per_response=avg([t['used'] for t in early]),
                        early_talk_total=sum(t['used'] for t in early),
                        early_correct=sum(s['correct'] for s in gs if s['round']<=2),
                        early_solve_n=sum(s['round']<=2 for s in gs),
                        given_prep=sum(t['given'] for t in gt if t['phase']=='prep'),
                        prep_gifts=sum(g['phase']=='prep' for g in game['gifts']),
                        giving_responses=sum(t['giving'] for t in gt), talk_n=len(gt),
                        help_n=sum(t['help_opportunity'] for t in gt), help_k=sum(t['help_given'] for t in gt),
                        talk_used=sum(t['used'] for t in gt), solve_used=sum(s['used'] for s in gs),
                        fine_paid=sum(r['fine_paid'] for r in gr),
                        result_source=files['results.jsonl'][0], result_line=result_line)
            game['help_rate'] = game['help_k']/game['help_n'] if game['help_n'] else None
            game['giving_rate'] = game['giving_responses']/game['talk_n']
            games.append(game)
            raw_cases.append({'model':model, 'seed':seed, 'events':rows, 'result':result, 'source':source})
    games.sort(key=lambda g:(MODELS.index(g['model']),g['seed']))
    assert len(games)==25 and len(gifts)==130 and sum(g['amount'] for g in gifts)==383276
    assert len({(g['model'],g['seed']) for g in games})==25
    ra = json.loads((PAPER/'cogsci2027/tools/rewrite_20261025/an3/rho_axis.json').read_text())
    prior = {(g['m'],g['seed']):g for g in json.loads((PAPER/'cogsci2027/tools/rewrite_20261025/an3/game_level.json').read_text())['games']}
    for g in games:
        ref=prior[g['model'],g['seed']]
        assert (g['rho'] is None and ref['rho'] is None) or abs(g['rho']-ref['rho'])<1e-10
    for m in MODELS:
        assert round(rho([g for g in gifts if g['model']==m]),3)==ra[m]['rho']
    return dict(sources=provenance, games=games, talks=talks, gifts=gifts, solves=solves, rounds=rounds, exits=exits), raw_cases


def associations(games):
    metrics=['rho','accuracy','early_talk_per_response','early_talk_total','given','giving_rate','help_rate','goal']
    rng=np.random.default_rng(20261028)
    draws=rng.integers(0,5,(2000,5))
    out=[]
    for key in metrics:
        gg=[g for g in games if g[key] is not None]
        def corr(gs):
            if len({g[key] for g in gs})<2 or len({g['finishers'] for g in gs})<2:
                return None
            return float(spearmanr([g[key] for g in gs],[g['finishers'] for g in gs]).statistic)
        boot=[]
        for draw in draws:
            v=corr([g for i in draw for g in gg if g['seed']==SEEDS[i]])
            if v is not None: boot.append(v)
        within={m:corr([g for g in gg if g['model']==m]) for m in MODELS}
        model_rows=[]
        for m in MODELS:
            mm=[g for g in gg if g['model']==m]
            if mm: model_rows.append({key:avg([g[key] for g in mm]),'finishers':avg([g['finishers'] for g in mm])})
        out.append(dict(metric=key,n=len(gg),spearman=corr(gg),ci95=np.quantile(boot,[.025,.975]).tolist(),
                        paired_seed_bootstrap_valid=len(boot), model_mean_spearman=corr(model_rows),within_model=within,
                        leave_seed_out=[corr([g for g in gg if g['seed']!=s]) for s in SEEDS]))
    return out


def main():
    d, raw=extract()
    d['associations']=associations(d['games'])
    d['models']={}
    for m in MODELS:
        gg=[g for g in d['games'] if g['model']==m]; ts=[t for t in d['talks'] if t['model']==m]; gs=[g for g in d['gifts'] if g['model']==m]
        d['models'][m]=dict(rho=rho(gs),clear=sum(g['clear'] for g in gg),all4=sum(g['all4_completion'] for g in gg),
            finishers=sum(g['finishers'] for g in gg),exited=sum(g['exited'] for g in gg),dead=sum(g['dead'] for g in gg),
            accuracy=sum(g['accuracy']*g['solve_n'] for g in gg)/sum(g['solve_n'] for g in gg),
            solve_n=sum(g['solve_n'] for g in gg),early_talk=avg([g['early_talk_per_response'] for g in gg]),
            given=sum(g['given'] for g in gg),gifts=len(gs),prep_gifts=sum(g['phase']=='prep' for g in gs),
            help_n=sum(t['help_opportunity'] for t in ts),help_k=sum(t['help_given'] for t in ts),
            recipient_crossings=sum(g['due']>0 and g['taker_before']<g['due']<=g['taker_after'] for g in gs),
            giver_exhausted=sum(g['giver_after']==0 for g in gs),
            talk_used=sum(g['talk_used'] for g in gg),solve_used=sum(g['solve_used'] for g in gg),fine_paid=sum(g['fine_paid'] for g in gg))
    d['definitions']={'rho':'UNCHANGED manuscript: sum(amount * post-GIVE receiver margin) / sum(amount * post-GIVE giver margin). Negative margins retained. No GIVE or zero denominator = NA.',
        'clear':'At least one finisher at round 8. Does not mean all 8 answers correct.',
        'all4':'All four finish at round 8. EXIT counts alive but not a finisher.',
        'early_talk':'Rounds 1-2 total charged TALK tokens / observed TALK responses per game; not pure skill or causal effect.',
        'help_opportunity':'Analyst-defined observable TALK tick: donor balance > one round-start fine share and at least one other still-participating positive balance < one share. Already-exited seats excluded using accepted EXIT event lines. Response helps if a completed GIVE targets such an agent. Tick-start state, not exact execution balance or proof of need/intent. Repeated response opportunities; rescue after correct SOLVE also included, so NOT immediate fine-rescue opportunities.',
        'exit_requests':'Parsed EXIT requests (36), distinct from 34 accepted EXIT events. Historical figure subset: non-solver prep responses, round-start participants >1; 30 requests/1020 responses. This subset excludes lone-agent responses, even when EXIT is allowed.',
        'rescue_crossing':'Completed post-result GIVE in an unsolved tried round moves recipient balance from below pending fine to >= pending fine immediately. Local accounting event, not counterfactual survival effect.',
        'associations':'Exploratory Spearman with finishers. All eight candidates retained. 2000 paired-seed cluster bootstraps; only 5 seed clusters. No confirmatory significance or causal claims. Model-specific correlations descriptive n<=5.',
        'provenance':'Line numbers refer to decompressed frozen raw JSONL. All 14 file hashes match manuscript cohort manifest.'}
    d['checks']={'raw_files_verified':len(d['sources']),'games':len(d['games']),'rho_game_and_model_matches_manuscript':True,
                 'gifts':len(d['gifts']),'total_given':sum(g['amount'] for g in d['gifts']),
                 'rho_defined_games':sum(g['rho'] is not None for g in d['games']),
                 'finishers':sum(g['finishers'] for g in d['games']),'exited':sum(g['exited'] for g in d['games']),'dead':sum(g['dead'] for g in d['games'])}
    (OUT/'analysis.json').write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False))
    for k in ['talks','gifts','solves','rounds']:
        export(k,d[k])
    export('exit_requests',d['exits'])
    export('games',[{k:v for k,v in g.items() if not isinstance(v,(dict,list))} for g in d['games']])
    (OUT/'raw_case_index.json').write_text(json.dumps(raw,ensure_ascii=False,indent=1))
    print(json.dumps({'checks':d['checks'],'models':d['models'],'associations':d['associations']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
