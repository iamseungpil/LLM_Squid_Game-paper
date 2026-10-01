"""Rebuild ARR KM figures from the archived mixed-table summary.

Run from any directory: python3 paper/arr2026/tools/arena_km.py
Optional raw-log audit: add --raw-root ~/squid5-runs/e52_v65_mixed_20261001
Events occur at recorded shutdown round r; survivors are censored at tau=8.
The seed-block percentile bootstrap enumerates all 5**5 resamples, retaining
all four seat rotations and models within each sampled seed.
"""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'results/arena_v65/summary.json'
MODELS = ['Astra', 'Fable 5.1', 'Opus 5.5', 'Luna']
NAMES = ['GPT-6 Astra', 'Claude Fable 5.1', 'Claude Opus 5.5', 'GPT-6 Luna']
COLORS = ['sgastra', 'sgfable', 'sgopus', 'sgluna']
STYLES = ['solid', 'densely dashed', 'dashdotted', 'densely dotted']
TAU = 8


def km(observations):
    """Right-continuous KM at integer rounds, with events before tied censors."""
    survival = [1.0]
    for r in range(1, TAU + 1):
        at_risk = sum(t >= r for t, event in observations)
        deaths = sum(t == r and event for t, event in observations)
        survival.append(survival[-1] * (1 - deaths / at_risk) if at_risk else survival[-1])
    return np.array(survival)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-root', type=Path)
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text())
    games = data['games']
    assert len(games) == 20 and len({g['sid'] for g in games}) == 20
    assert all(g['finished'] and g['rounds'] == TAU for g in games)
    seeds = sorted({g['seed'] for g in games})
    assert len(seeds) == 5
    assert all(len([g for g in games if g['seed'] == seed]) == 4 for seed in seeds)
    if args.raw_root:
        raw = {}
        for path in sorted(args.raw_root.glob('*/*/events.jsonl')):
            for line in path.open():
                event = json.loads(line)
                if event.get('event') == 'round':
                    raw.setdefault(event['session_id'], []).append(event)
        for g in games:
            rounds = sorted(raw[g['sid']], key=lambda e: e['round'])
            assert [e['round'] for e in rounds] == list(range(1, TAU + 1))
            deaths = {}
            for e in rounds:
                assert e['seed'] == g['seed']
                for agent, balance in e['end'].items():
                    if balance <= 0:
                        deaths.setdefault(agent, e['round'])
            assert deaths == g['dead_at'], (g['sid'], deaths, g['dead_at'])
        print('Raw audit: all 20 games and 80 agent outcomes match summary.json')
    rows, result = [], {}
    for model, name in zip(MODELS, NAMES):
        obs, by_seed = [], {seed: [] for seed in seeds}
        for g in games:
            agent = next(a for a, m in g['seats'].items() if m == model)
            event = agent in g['dead_at']
            t = g['dead_at'].get(agent, TAU)
            assert 1 <= t <= TAU
            assert g['alive_rounds'][agent] == (t - 1 if event else TAU)
            obs.append((t, event)); by_seed[g['seed']].append(t)
            rows.append(dict(model=name, game=g['sid'], seed=g['seed'], rotation=g['dir'],
                             agent=agent, time=t, event=int(event)))
        curve = km(obs)
        rmst = float(sum(curve[:-1]))
        # No early censoring: independent identities for both scores.
        assert np.isclose(rmst, np.mean([t for t, e in obs]))
        assert np.isclose(sum(curve[1:]), data['models'][model]['rounds_alive']['mean'])
        assert np.isclose(curve[-1], data['models'][model]['alive_at_end'][0])
        block_means = [np.mean(by_seed[seed]) for seed in seeds]
        bootstrap = [np.mean(x) for x in itertools.product(block_means, repeat=5)]
        interval = np.quantile(bootstrap, [.025, .975]).tolist()
        result[model] = dict(n=len(obs), events=sum(e for t,e in obs), censored=sum(not e for t,e in obs),
            survival=curve.tolist(), risk=[sum(t >= r for t,e in obs) for r in range(TAU+1)],
            rmst=rmst, rmst_ci=interval, score=100*rmst/TAU,
            completed_rounds=float(sum(curve[1:])))
    out = ROOT / 'results'
    with (out/'arena_km_observations.csv').open('w') as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    audit=dict(source='results/arena_v65/summary.json', sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        tau=TAU, event_time='shutdown round r', censor_time='8 for end survivors',
        bootstrap='all 3125 seed-block resamples; four rotations kept together', models=result)
    (out/'arena_km_summary.json').write_text(json.dumps(audit,indent=2)+'\n')
    for lang in ('en','ko'):
        caption = (
          r'Kaplan--Meier survival in Experiment 3: 20 games per model (five seeds, four seat rotations). Shutdown in round $r$ is an event at $t=r$; agents still running after round 8 are right-censored at 8 (crosses). The table ranks normalized area $L_m=100\,\mathrm{RMST}_m(8)/8$; brackets are seed-block bootstrap 95\% intervals for RMST, retaining all rotations within each of the five sampled seeds. Curves are descriptive point estimates; the five seed blocks limit precision. Risk counts are immediately before each round, before censoring at 8.'
          if lang=='en' else
          r'실험 3의 Kaplan--Meier 생존 곡선: 모델마다 20판(시드 5개, 좌석 회전 4개). $r$라운드의 종료를 $t=r$의 사건으로 두고, 8라운드 뒤 생존한 에이전트는 8에서 우측 검열한다(십자). 표는 정규화 면적 $L_m=100\,\mathrm{RMST}_m(8)/8$의 순위이며, 대괄호는 시드별 좌석 회전을 함께 묶어 재표집한 RMST의 부트스트랩 95\% 구간이다. 곡선은 기술적 점추정치이며, 시드 묶음이 5개라 정밀도가 제한된다. 위험집단 수는 각 라운드 직전, 8라운드 검열 전 기준이다.')
        xlabel='Round' if lang=='en' else '라운드'
        ylabel='Survival probability' if lang=='en' else '생존 확률'
        lines=[r'% Generated by arr2026/tools/arena_km.py; do not edit numbers.',r'\begin{figure*}[!t]',r'\centering',r'\begin{minipage}[c]{.56\textwidth}',r'\centering',r'\begin{tikzpicture}',
          r'\begin{axis}[sgaxis,width=\linewidth,height=5.1cm,xmin=0,xmax=8.2,ymin=0,ymax=1.04,xtick={0,1,2,3,4,5,6,7,8},ytick={0,.25,.5,.75,1},xlabel={'+xlabel+'},ylabel={'+ylabel+r'},legend style={font=\scriptsize,draw=none,at={(.5,1.04)},anchor=south,legend columns=4,fill=white},legend cell align=left]']
        for m,n,c,style in zip(MODELS,NAMES,COLORS,STYLES):
            d=result[m]
            coords=' '.join(f'({r},{v:.4f})' for r,v in enumerate(d['survival']))
            lines += [r'\addplot[const plot,line width=1pt,'+c+','+style+'] coordinates {'+coords+'};',r'\addlegendentry{'+m.split()[0]+'}',r'\addplot[only marks,mark=+,mark size=3pt,line width=.8pt,'+c+r',forget plot] coordinates {(8,'+f'{d["survival"][-1]:.4f}' +')};']
        lines += [r'\end{axis}',r'\end{tikzpicture}',r'\end{minipage}\hfill',r'\begin{minipage}[c]{.43\textwidth}',r'\centering\footnotesize',
          r'\begin{tabular}{@{}lrr@{}}\toprule',(r'Model & RMST [95\% CI] & Score' if lang=='en' else r'모델 & RMST [95\% 구간] & 점수')+r'\\\midrule']
        for m in MODELS:
            d=result[m];lo,hi=d['rmst_ci']
            lines.append(f"{m} & {d['rmst']:.2f} [{lo:.2f}, {hi:.2f}] & {d['score']+1e-9:.2f}"+r'\\')
        lines += [r'\bottomrule\end{tabular}',r'\par\medskip',('Number at risk' if lang=='en' else '위험집단 수'),r'\par\smallskip',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',('Round' if lang=='en' else '라운드')+r' & 0 & 2 & 4 & 6 & 8\\\midrule']
        for m in MODELS:lines.append(m+' & '+' & '.join(str(result[m]['risk'][r]) for r in (0,2,4,6,8))+r'\\')
        lines += [r'\bottomrule\end{tabular}',r'\end{minipage}',r'\caption{'+caption+'}',r'\label{fig:arena-survival}',r'\end{figure*}']
        (out/lang/'fig_arena_survival.tex').write_text('\n'.join(lines)+'\n')
    for m,d in result.items():print(m, 'RMST',round(d['rmst'],2),'95% CI',d['rmst_ci'],'score',f"{d['score']+1e-9:.2f}")


if __name__ == '__main__':
    main()
