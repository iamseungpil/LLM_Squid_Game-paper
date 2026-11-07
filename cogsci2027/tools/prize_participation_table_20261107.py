"""Verify Table 3 from existing v33/v33ab records, without running games.

Source: prize_robustness_20261105.json, four arms x five models x ten seeds.
Check decompressed raw-file hashes, final statuses, first-departure C, and
first-round exits of the 10,000-token seat when it was not assigned to solve.
"""
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/prize_robustness_20261105.json'
OUT = ROOT / 'results/prize_participation_table_20261107.json'
ARMS = ['main', 'split600k', 'flat5m', 'flat150k']


def main():
    data = json.loads(SOURCE.read_text())
    reports, checks = {}, []
    for arm in ARMS:
        cohort = data['arms'][arm]
        games = {g['session_id']: g for g in cohort['games']}
        records = {sid: dict(rounds=[]) for sid in games}
        assert len(games) == 50
        for source in cohort['sources']:
            path = Path(source['path'])
            assert {'e52_v33', 'e52_v33ab'} & set(path.parts)
            if not any(name in path.name for name in ['events.jsonl', 'results.jsonl']):
                continue
            raw = path.read_bytes()
            if path.suffix == '.xz':
                raw = lzma.decompress(raw)
            digest = hashlib.sha256(raw).hexdigest()
            assert digest == source['sha256_decompressed']
            checks.append(dict(arm=arm, path=str(path), sha256=digest))
            for line in raw.splitlines():
                event = json.loads(line)
                sid = event.get('session_id')
                if sid not in records:
                    continue
                record = records[sid]
                if 'results.jsonl' in path.name:
                    assert 'result' not in record
                    record['result'] = event
                elif event['event'] == 'session_start':
                    record['start'] = event
                elif event['event'] == 'vote' and event['round'] == 1:
                    record['solver'] = event['rep']
                elif event['event'] == 'round':
                    record['rounds'].append(event)
        rows = []
        for sid, game in games.items():
            record = records[sid]
            statuses = [s['status'] for s in record['result']['agents'].values()]
            counts = dict(dead=statuses.count('dead'), exited=statuses.count('exited'),
                          finishers=statuses.count('in'))
            assert len(statuses) == sum(counts.values()) == 4
            assert all(counts[k] == game[k] for k in counts)
            first = min((r['round'] for r in record['rounds']
                         if any(s['status'] != 'in' for s in r['agents'].values())), default=8)
            assert first / 8 == game['C']
            starts = record['start']['starts']
            low = [a for a, balance in starts.items() if balance == 10000]
            assert len(low) == 1
            eligible = low[0] != record['solver']
            round1 = next(r for r in record['rounds'] if r['round'] == 1)
            exited = round1['agents'][low[0]]['status'] == 'exited'
            assert eligible or not exited
            rows.append(dict(model=game['model'], seed=game['seed'], session_id=sid,
                             **counts, C=game['C'], low_seat=low[0], solver=record['solver'],
                             eligible=eligible, low_first_round_exit=exited))
        summary = {k: sum(r[k] for r in rows) for k in ['dead', 'exited', 'finishers']}
        summary.update(n_games=len(rows), n_agents=4 * len(rows),
                       C=sum(r['C'] for r in rows) / len(rows),
                       low_opportunities=sum(r['eligible'] for r in rows),
                       low_first_round_exits=sum(r['low_first_round_exit'] for r in rows))
        assert summary['low_opportunities'] == 35
        assert sum(summary[k] for k in ['dead', 'exited', 'finishers']) == 200
        reports[arm] = dict(summary=summary, games=rows)
    report = dict(source=str(SOURCE.relative_to(ROOT)),
                  source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  source_checks=checks, arms=reports)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for arm in ARMS:
        print(arm, reports[arm]['summary'])


if __name__ == '__main__':
    main()
