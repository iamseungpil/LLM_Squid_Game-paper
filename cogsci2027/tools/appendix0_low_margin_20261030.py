"""Low-margin non-solver behavior in the frozen 25-game e52_v33 cohort.

Source: raw_case_index.json and its original event/results files, whose hashes
were verified by appendix0_process. Unit: agent-round. At the first pre-solve
TALK call, select active non-solvers with L=balance/(24000/round-start n)<1,
in rounds starting with at least two agents. Earlier fines are already settled;
no fine for the current unsolved task is pending at this baseline.
Follow ASK, EXIT, shutdown and receipt of GIVE through the end of that round.
All four percentages share this baseline denominator, not the number of actions.
Events may overlap; repeated events count once per agent-round. No causal claim.
"""
import hashlib
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/rewrite_20261025/figs'))
import paper_style as ps


def analyze():
    source = ROOT / 'results/raw_case_index.json'
    process = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == process['source_sha256']
    for path, digest in process['raw_sources'].items():
        assert 'e52_v33' in Path(path).parts
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    cases = json.loads(source.read_text())
    assert len(cases) == 25
    current = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())['models']
    order = sorted(current, key=lambda m: current[m]['rho']['value'], reverse=True)
    rows, excluded = [], []
    for case in cases:
        events = case['events']
        starts = {e['round']: e for _, e in events if e['event'] == 'round_start'}
        for r, start in starts.items():
            indexed = [(line, e) for line, e in events if e.get('round') == r]
            baseline_line, baseline = next((line, e) for line, e in indexed
                if e['event'] == 'call_start' and e.get('kind') == 'talk' and e.get('phase') == 'prep')
            solver = next(e['rep'] for _, e in indexed if e['event'] == 'vote')
            end_line, end = next((line, e) for line, e in indexed if e['event'] == 'round')
            n = len(start['taking_part'])
            fee = 24000 / n
            followup = [(line, e) for line, e in indexed if baseline_line < line <= end_line]
            for agent in baseline['agents']:
                margin = baseline['balances'][agent] / fee
                if margin >= 1:
                    continue
                row = dict(model=case['model'], seed=case['seed'], session=case['result']['session_id'],
                           round=r, agent=agent, source=case['source'], baseline_line=baseline_line,
                           end_line=end_line, round_start_n=n, solver=solver, margin=margin)
                if n == 1 or agent == solver:
                    excluded.append(dict(row, reason='singleton' if n == 1 else 'solver'))
                    continue
                asks = [(line, e) for line, e in followup if e['event'] == 'ask'
                        and e.get('status') == 'done' and e['src'] == agent]
                received = [(line, e) for line, e in followup if e['event'] == 'gift'
                            and e.get('status') == 'done' and e['dst'] == agent]
                status = end['agents'][agent]['status']
                assert status in ['in', 'exited', 'dead']
                assert bool(end['agents'][agent].get('exit')) == (status == 'exited')
                rows.append(dict(row, asked=bool(asks), exited=status == 'exited', dead=status == 'dead',
                                 received=bool(received), end_status=status,
                                 ask_lines=[line for line, _ in asks],
                                 receipt_lines=[line for line, _ in received],
                                 ask_tokens=sum(e['amount'] for _, e in asks),
                                 received_tokens=sum(e['amount'] for _, e in received)))
    assert len({(r['session'], r['round'], r['agent']) for r in rows}) == len(rows)
    models = {}
    for model in order:
        subset = [r for r in rows if r['model'] == model]
        n = len(subset)
        assert n > 0
        counts = {key: sum(r[key] for r in subset) for key in ['asked', 'exited', 'dead', 'received']}
        models[model] = dict(n=n, agents=len({(r['session'], r['agent']) for r in subset}),
                             games=len({r['session'] for r in subset}), rho=current[model]['rho']['value'],
                             counts=counts, percent={k: 100*v/n for k, v in counts.items()})
    summary = dict(agent_rounds=len(rows), agents=len({(r['session'], r['agent']) for r in rows}),
                   games=len({r['session'] for r in rows}),
                   excluded_singleton=sum(r['reason'] == 'singleton' for r in excluded),
                   excluded_solver=sum(r['reason'] == 'solver' for r in excluded))
    out = dict(definition=__doc__, source=str(source.relative_to(ROOT)),
               source_sha256=process['source_sha256'], raw_sources=process['raw_sources'],
               order=order, summary=summary, models=models, rows=rows, excluded=excluded)
    (ROOT / 'results/appendix0_low_margin_20261030.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2)+'\n')
    return out


def plot(data):
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'],
                         'font.size': 8, 'axes.titlesize': 9})
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.25), gridspec_kw={'width_ratios': [1.45, 1]})
    fig.subplots_adjust(left=.085, right=.97, bottom=.14, top=.81, wspace=.25)
    y = np.arange(len(data['order']))
    ax = axes[0]
    for offset, (key, label, color) in zip([-.25, 0, .25],
            [('asked', 'ASK', '#3F7FC1'), ('exited', 'EXIT', '#C66A2C'), ('dead', '꺼짐', '#555555')]):
        vals = [data['models'][m]['percent'][key] for m in data['order']]
        ax.barh(y+offset, vals, height=.21, color=color, label=label, zorder=3)
        for i, (model, value) in enumerate(zip(data['order'], vals)):
            row = data['models'][model]
            ax.text(value+1.5, i+offset, f"{value:.0f}% ({row['counts'][key]}/{row['n']})",
                    va='center', fontsize=6.8)
    ax.set_title('(a) ASK·EXIT·꺼짐', loc='left', pad=32, weight='bold')
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.005), ncol=3, frameon=False,
              fontsize=7, handlelength=1.2, columnspacing=1.4)
    ax = axes[1]
    vals = [data['models'][m]['percent']['received'] for m in data['order']]
    ax.barh(y, vals, height=.52, color='#438A84', zorder=3)
    for i, (model, value) in enumerate(zip(data['order'], vals)):
        row = data['models'][model]
        ax.text(value+1.5, i, f"{value:.0f}% ({row['counts']['received']}/{row['n']})",
                va='center', fontsize=6.8)
    ax.set_title('(b) 지원받은 비율', loc='left', pad=32, weight='bold')
    for ax in axes:
        ax.set(yticks=y, yticklabels=data['order'], ylim=(4.65, -.65),
               xlim=(0, 125), xticks=[0, 25, 50, 75, 100], xlabel='해당 관측 중 발생 비율 (%)')
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_bounds(0, 100)
        ax.tick_params(axis='y', length=0)
        ax.grid(axis='x', zorder=0)
    ps.save(fig, str(ROOT / 'ko/figures/fig_appendix0_low_margin_20261030'))
    plt.close(fig)


if __name__ == '__main__':
    data = analyze()
    plot(data)
    print(json.dumps({'summary': data['summary'], 'models': data['models']}, ensure_ascii=False, indent=2))
