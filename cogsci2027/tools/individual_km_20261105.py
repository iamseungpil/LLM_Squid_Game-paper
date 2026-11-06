"""Individual participation curve for the appendix; same public v33 cohort as Figure 3.

Sources: hash-verified results.jsonl files under ~/squid5-runs/e52_v33/
squid5_e52v33_public_*4, recorded in cohort_public_20261105.json (seeds 4101--4110).
EXIT and shutdown are events at round end; finishers are censored after round 8.
Run with ~/.venvs/squid-game/bin/python. No model calls or manuscript prose writes.
"""
import json
from pathlib import Path

import numpy as np

import ablation_prize_20261103 as ab
import coexistence_rmst_20261103 as cx
import feedback_20261028 as fb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ko/figures/cohorts_20261105/individual_km'


def main():
    source = ROOT / 'results/cohort_public_20261105.json'
    cohort = json.loads(source.read_text())
    raw = {}
    for entry in cohort['sources']:
        path = Path(entry['path'])
        if path.name.startswith('results.jsonl'):
            data = fb.read_bytes(path)
            assert fb.sha(data) == entry['sha256_decompressed']
            for line in data.splitlines():
                result = json.loads(line)
                assert result['session_id'] not in raw
                raw[result['session_id']] = result

    models = {}
    for model, label in cohort['models'].items():
        games = [g for g in cohort['games'] if g['model'] == model]
        assert len(games) == 10
        agents = []
        for game in games:
            seats = list(raw[game['session_id']]['agents'].values())
            assert len(seats) == 4
            assert all(a['status'] in ('in', 'exited', 'dead') for a in seats)
            for r, n in enumerate(game['remaining_after_round'], 1):
                assert sum(a['status'] == 'in' or a['out_round'] > r for a in seats) == n
            agents.extend(seats)
        risk, survival = len(agents), 1.0
        curve, events, at_risk = [1.0], [], []
        for r in range(1, 9):
            d = sum(a['status'] != 'in' and a['out_round'] == r for a in agents)
            at_risk.append(risk)
            if risk:
                survival *= 1 - d / risk
            else:
                assert d == 0
            risk -= d
            direct = sum(a['status'] == 'in' or a['out_round'] > r for a in agents) / len(agents)
            assert np.isclose(survival, direct, atol=1e-12)
            curve.append(direct)
            events.append(d)
        finishers = sum(a['status'] == 'in' for a in agents)
        assert finishers == sum(g['finishers'] for g in games) == risk
        models[model] = dict(label=label, games=10, agents=len(agents),
                             at_risk=at_risk, events=events, remaining_share=curve,
                             finishers=finishers, completion_rate=curve[-1])

    ps, plt = ab.style()
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    for model in sorted(models, key=lambda m: -models[m]['completion_rate']):
        data = models[model]
        index = cx.MODELS.index(model)
        ax.step(range(9), np.array(data['remaining_share']) * 100, where='post',
                color=cx.COLORS[index], marker=cx.MARKERS[index], lw=1.4,
                markersize=3.5, label=f"{data['label']} ({data['finishers']}/40)")
    ax.set(xlim=(-.2, 8.25), ylim=(-2, 104), xticks=range(9), yticks=range(0, 101, 25),
           xlabel='라운드', ylabel='아레나에 남은 에이전트 (%)')
    ax.grid(axis='y', alpha=.6)
    fig.legend(loc='lower center', ncol=3, bbox_to_anchor=(.53, .01),
               columnspacing=1.1, handlelength=1.8, fontsize=7.5)
    fig.subplots_adjust(left=.13, right=.98, top=.96, bottom=.29)
    ps.save(fig, str(OUT))
    plt.close(fig)
    report = dict(source=str(source.relative_to(ROOT)), source_sha256=fb.sha(source.read_bytes()),
                  event='EXIT or shutdown at round end', censoring='finishers after round 8',
                  denominator='40 initially participating agents per model (10 games)',
                  rounds=list(range(9)), models=models)
    (ROOT / 'results/individual_km_20261105.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({m: (d['finishers'], d['remaining_share']) for m, d in models.items()}, indent=2))


if __name__ == '__main__':
    main()
