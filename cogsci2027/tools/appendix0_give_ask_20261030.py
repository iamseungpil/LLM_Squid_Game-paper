"""GIVE/ASK action counts and token totals in the fixed e52_v33 25-game cohort.

Source: raw_case_index.json, five games per model, seeds4101--4105; verify raw
hashes against appendix0_process. Count status=done events, not responses.
ASK done means a registered request, not fulfillment. Include repeated requests
and retransfers in gross amounts. Bars show five-game totals, without game dots.
Hatching within GIVE volume marks transfers back to a previous giver in the same
game (full event amount, not debt-capped/netted or verified loan repayment).
Sort by current pooled, pending-fine-adjusted
rho (giver / receiver). No opportunity or participation-duration normalization.
"""
import hashlib
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/rewrite_20261025/figs'))
import paper_style as ps


def analyze():
    source = ROOT / 'results/raw_case_index.json'
    process = json.loads((ROOT / 'results/appendix0_process_20261030.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == process['source_sha256']
    for path, digest in process['raw_sources'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    cases = json.loads(source.read_text())
    current = json.loads((ROOT / 'results/appendix0_integrated_20261030.json').read_text())['models']
    historic = json.loads((ROOT / 'results/arena_v33.json').read_text())['models']
    order = sorted(current, key=lambda m: current[m]['rho']['value'], reverse=True)
    models = {}
    for model in order:
        games = []
        subset = sorted((c for c in cases if c['model'] == model), key=lambda c: c['seed'])
        assert [c['seed'] for c in subset] == list(range(4101, 4106))
        for case in subset:
            row = dict(seed=case['seed'], session=case['result']['session_id'])
            for event, prefix in [('gift', 'give'), ('ask', 'ask')]:
                actions = [e for _, e in case['events'] if e['event'] == event and e.get('status') == 'done']
                assert all(e['amount'] > 0 for e in actions)
                row[prefix + '_count'] = len(actions)
                row[prefix + '_tokens'] = sum(e['amount'] for e in actions)
            prior, returned = set(), 0
            for _, event in case['events']:
                if event['event'] != 'gift' or event.get('status') != 'done':
                    continue
                if (event['dst'], event['src']) in prior:
                    returned += event['amount']
                prior.add((event['src'], event['dst']))
            row['return_tokens'] = returned
            games.append(row)
        totals = {k: sum(g[k] for g in games) for k in ['give_count', 'give_tokens', 'ask_count', 'ask_tokens']}
        ref = next(v for k, v in historic.items() if model in k)
        assert totals == dict(give_count=ref['gifts'], give_tokens=ref['given'], ask_count=len(ref['asks']), ask_tokens=ref['asked'])
        totals['return_tokens'] = sum(g['return_tokens'] for g in games)
        assert totals['return_tokens'] == sum(p['return_tokens'] for p in current[model]['timing'].values())
        assert 0 <= totals['return_tokens'] <= totals['give_tokens']
        models[model] = dict(rho=current[model]['rho']['value'], totals=totals, games=games)
    assert sum(m['totals']['give_count'] for m in models.values()) == 130
    assert sum(m['totals']['ask_count'] for m in models.values()) == 90
    out = dict(definition=__doc__, source=str(source.relative_to(ROOT)), source_sha256=process['source_sha256'], order=order, models=models)
    (ROOT / 'results/appendix0_give_ask_20261030.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
    return out


def plot(data):
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'font.size': 7})
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.1))
    fig.subplots_adjust(left=.06, right=.99, bottom=.26, top=.85, wspace=.35)
    metrics = [('give_count', 1, '(a) GIVE 횟수', '건', 50),
               ('give_tokens', 1000, '(b) GIVE 이전 총량', '천 토큰', 145),
               ('ask_count', 1, '(c) ASK 횟수', '건', 50),
               ('ask_tokens', 1000, '(d) ASK 요청 총량', '천 토큰', 145)]
    for ax, (key, scale, title, unit, ymax) in zip(axes, metrics):
        for x, model in enumerate(data['order']):
            row = data['models'][model]
            total = row['totals'][key] / scale
            ax.bar(x, total, width=.7, color='#D8E3ED', edgecolor='#697D8E', linewidth=.6)
            ax.text(x, total+ymax*.025, f'{total:.1f}' if scale > 1 else str(int(total)), ha='center', fontsize=6.5)
            if key == 'give_tokens' and row['totals']['return_tokens']:
                returned = row['totals']['return_tokens'] / scale
                ax.bar(x, returned, bottom=total-returned, width=.7,
                       color='none', edgecolor='#697D8E', linewidth=.6, hatch='////')
        ax.set(title=title, ylabel=unit, ylim=(0, ymax), xticks=range(5),
               xticklabels=[f"{m}\n({data['models'][m]['rho']:.2f})" for m in data['order']])
        ax.set_title(title, fontsize=8)
        ax.tick_params(axis='x', labelsize=6)
        ax.tick_params(axis='y', labelsize=6)
        ax.set_axisbelow(True)
        ax.grid(axis='y')
    fig.text(.5, .02, '막대: 모델별 5판 합계 · 빗금: 앞서 준 상대에게 되돌려 준 양 · 괄호: ρ (내림차순)', ha='center', fontsize=6.5)
    ps.save(fig, str(ROOT / 'ko/figures/fig_appendix0_give_ask_20261030'))
    plt.close(fig)


if __name__ == '__main__':
    data = analyze()
    plot(data)
    print(json.dumps({m: r['totals'] for m, r in data['models'].items()}, ensure_ascii=False, indent=2))
