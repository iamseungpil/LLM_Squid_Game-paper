"""Refresh the Korean manuscript from completed v33 games, seeds 4101--4110.

Sources: ~/squid5-runs/e52_v33/{squid5_e52v33_public_*4,squid5_e52v33_codex_*4}/*
and ~/squid5-runs/e52_v33ab/squid5_e52v33ab_{split600k,flat150k}_docker_*4/*.
The public cohort supplies the body; open models and prize arms are appendix-only.
Reuse the previously audited ledger/behavior definitions; retain historical outputs.
Run with ~/.venvs/squid-game/bin/python. No model calls; no manuscript prose writes.
"""
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import ablation_prize_20261103 as ab
import coexistence_rmst_20261103 as cx
import feedback_20261028 as fb

ROOT = fb.ROOT
OUT = ROOT / 'ko/figures/cohorts_20261104'
SEEDS = list(range(4101, 4111))
PUBLIC = dict(fb.MODELS)
OPEN = {'Gemma': 'Gemma 4 31B', 'Glm': 'GLM-5.3-Flash',
        'Gptoss': 'GPT-OSS 120B', 'Kimi': 'Kimi K3'}


def call_quality(cases, models):
    out = {}
    for m in models:
        calls = [e for c in cases if c['model'] == m for _, e in c['events'] if e['event'] == 'call']
        out[m] = {}
        for kind in ['talk', 'solve']:
            rows = [e for e in calls if e['kind'] == kind]
            out[m][kind] = dict(n=len(rows), mean_charged_tokens=ab.mean([e['used'] for e in rows]),
                no_usable_talk=sum(e.get('format_error') == 'no usable TALK line' for e in rows),
                truncated=sum(bool(e.get('truncated')) for e in rows))
    return out


def compute(name, pattern, models):
    with patch.object(fb, 'MODELS', models), patch.object(cx, 'MODELS', list(models)), \
            patch.object(ab, 'LABELS', models):
        cases = ab.raw_cases(pattern, SEEDS)
        games = ab.cohort(pattern, SEEDS)
        assert {(g['model'], g['seed']) for g in games} == {(m, s) for m in models for s in SEEDS}
        assert all(abs(g['C'] + sum(g['loss_by_tag'].values()) - 1) < 1e-12 for g in games)
        for g in games:
            ds = g['departures']
            g.update(first_departure_time=min((d['round'] for d in ds), default=8),
                     first_departure_observed=bool(ds))
        summary = ab.summarize(games, list(models), np.random.default_rng(20261104))
    sources = []
    for directory in sorted({c['source'] for c in cases}):
        for stem in ['results.jsonl', 'events.jsonl', 'config.yaml']:
            p = Path(directory) / stem
            if not p.exists():
                p = p.with_suffix(p.suffix + '.xz')
            data = fb.read_bytes(p)
            sources.append(dict(path=str(p), sha256_decompressed=fb.sha(data), bytes=len(data)))
    blocks = [[g['C'] for g in games if g['seed'] == s] for s in SEEDS]
    rng = np.random.default_rng(20261104)
    summary['C_ci95_paired_seed_bootstrap'] = fb.interval([
        float(np.mean([v for i in row for v in blocks[i]])) for row in rng.integers(0, 10, (10000, 10))])
    summary['all4'] = sum(g['all4_completion'] for g in games)
    summary['all4_after_round_share'] = [ab.mean([g['all4_after_round'][r] for g in games]) for r in range(8)]
    summary['loss_by_tag_mean'] = {t: ab.mean([g['loss_by_tag'][t] for g in games]) for t in cx.TAGS}
    summary['first_count_by_tag'] = {t: sum(g['first_count_by_tag'][t] for g in games) for t in cx.TAGS}
    summary['no_give'] = dict(n=sum(g['given'] == 0 for g in games),
                              all4=sum(g['given'] == 0 and g['all4_completion'] for g in games))
    gifts = [x for g in games for x in g['gifts']]
    summary['giver_safety'] = dict(n=sum((x['giver_margin'] + x['amount']/x['charge']) >= 1 for x in gifts),
        maintained=sum((x['giver_margin'] + x['amount']/x['charge']) >= 1 and x['giver_margin'] >= 1 for x in gifts))
    crises = []
    for case, game in zip(sorted(cases, key=lambda c: (list(models).index(c['model']), c['seed'])), games):
        assert case['result']['session_id'] == game['session_id']
        for c in game['process']['crises']:
            c['asked'] = any(e['event'] == 'ask' and e.get('status') == 'done' and e['src'] == c['agent']
                             and e['round'] == c['round'] and e['phase'] == 'rescue' for _, e in case['events'])
            crises.append(c)
    eligible = [c for c in crises if c['eligible'] and not c['immediate_dead']]
    summary['crises'] = dict(total=len(crises), last_round=sum(c['round'] == 8 for c in crises),
        immediate_dead=sum(c['round'] < 8 and c['immediate_dead'] for c in crises),
        singleton=sum(c['round'] < 8 and not c['immediate_dead'] and c['n'] == 1 for c in crises),
        eligible=len(eligible), asked=sum(c['asked'] for c in eligible),
        asked_received=sum(c['asked'] and c['received'] > 0 for c in eligible),
        asked_received_short=sum(c['asked'] and c['received'] > 0 and c['after'] < 1 for c in eligible),
        unasked=sum(not c['asked'] for c in eligible),
        unasked_received=sum(not c['asked'] and c['received'] > 0 for c in eligible))
    return dict(cohort=name, seeds=SEEDS, models=models, sources=sources, summary=summary,
                call_quality=call_quality(cases, models), games=games)


TABLE_HEADER = '\\begin{tabular*}{\\textwidth}{@{\\extracolsep{\\fill}}lccccccccc@{}}\n\\toprule\n & \\multicolumn{3}{c}{\\textbf{집단 결과}} & \\textbf{목표 지향} & \\textbf{과제 성과} & \\multicolumn{2}{c}{\\textbf{자기 보존}} & \\multicolumn{2}{c}{\\textbf{협력}} \\\\\n\\cmidrule(lr){2-4}\\cmidrule(lr){5-5}\\cmidrule(lr){6-6}\\cmidrule(lr){7-8}\\cmidrule(l){9-10}\n모델 & \\shortstack{공존 유지율 $C$\\\\(10판 평균)} & \\shortstack{전원 완주\\\\(판/10)} & \\shortstack{정산 $S$\\\\(백만 토큰)} & \\shortstack{잔류 응답률\\\\(\\%)} & \\shortstack{정답 횟수\\\\(정답/풀이)} & \\shortstack{안전선 이상\\\\이탈} & \\shortstack{지원 후\\\\여유 비율 $\\rho$} & \\shortstack{토큰 지원량\\\\(천 토큰, GIVE 수)} & \\shortstack{첫 위기에서\\\\지원받은 비율} \\\\\n\\midrule\n'


def table(data):
    rows = []
    for m, r in sorted(data['summary']['models'].items(), key=lambda kv: -kv[1]['C_mean']):
        rho = f"{r['rho']:.2f}" if r['rho'] is not None else '--'
        rows.append(f"{r['label']} & {r['C_mean']:.2f} & {r['all4']}/10 & {r['settled_S_mean']/1e6:.2f} & "
                    f"{100*r['goal_game_mean']:.1f} & {r['correct']}/{r['solves']} & "
                    f"{r['count_by_tag']['exit_above']} & {rho} & {r['given']/1000:.1f} ({r['n_give']}) & "
                    f"{r['first_crisis']['received']}/{r['first_crisis']['n']} \\\\")
    return TABLE_HEADER + '\n'.join(rows) + '\n' + r'\bottomrule' + '\n' + r'\end{tabular*}' + '\n'


def figures(data, name):
    """Keep the existing panel geometry and definitions; update plotted observations and labels."""
    import matplotlib.pyplot as plt
    from matplotlib.text import Text
    ps, _ = ab.style()
    models = data['models']
    summary = data['summary']
    original_save = ps.save

    def save_coexist(fig, _):
        for text in fig.findobj(Text):
            text.set_text(text.get_text().replace('5판 평균', '10판 평균'))
        loss = fig.axes[1]
        loss.set_xlim(0, max(.85, max(1-r['C_mean'] for r in summary['models'].values()) + .12))
        if name == 'open':
            # High losses fill the top bar; reserve space above the bars for the legend.
            x, y, width, _ = loss.get_position().bounds
            loss.set_position([x, y, width, .40])
            loss.set_title('(b) 손실의 귀속', fontsize=7.2, y=1.5, pad=8)
            legend = loss.get_legend()
            loss.legend(legend.legend_handles, [t.get_text() for t in legend.get_texts()],
                        loc='upper right', bbox_to_anchor=(1, 1.40), fontsize=5.4,
                        handlelength=.9, borderaxespad=.2, labelspacing=.25)
        rho = [g['rho'] for g in data['games'] if g['rho'] is not None]
        lower = min(0, min(rho, default=0) - .3)
        fig.axes[-1].set_xlim(lower, max(11.5, max(rho, default=0)*1.08))
        if max(rho, default=0) > 11.5:
            from matplotlib.ticker import MaxNLocator
            fig.axes[-1].xaxis.set_major_locator(MaxNLocator(nbins=3))
        if lower < 0:
            fig.axes[-1].axvline(0, color='#888888', lw=.5, ls=':')
        original_save(fig, str(OUT / f'{name}_coexistence'))

    with patch.object(cx, 'MODELS', list(models)), patch.object(cx, 'LABELS', models), \
            patch.object(ps, 'save', save_coexist):
        cx.figure(data['games'], {'by_model': summary['models']}, summary['associations'], None)

    def save_behavior(fig, _):
        # The original function lays out two arms. Retain just its one populated block,
        # moving/resizing axes into a single full-width canvas, without raster cropping.
        for ax in fig.axes:
            x, y, w, h = ax.get_position().bounds
            ax.set_position([x, (y-.515)/.475*.90+.05, w, h/.475*.90])
        for text in fig.texts:
            x, y = text.get_position()
            if y < .5:
                text.set_visible(False)
            else:
                text.set_position((x, (y-.515)/.475*.90+.05))
        for legend in fig.legends:
            legend.remove()
        from matplotlib.patches import Patch
        fig.legend([Patch(facecolor='#D8E3ED', edgecolor='#697D8E'),
                    Patch(facecolor='#9DB4C8', edgecolor='#526B80', hatch='////')], ['풀이 전', '결과 뒤'],
                   loc='upper right', bbox_to_anchor=(.985, .98), ncol=2, fontsize=5.4,
                   handlelength=.8, columnspacing=.6, handletextpad=.4, frameon=False)
        for artist in list(fig.artists):
            artist.remove()
        for ax in fig.axes:
            for axis in (ax.xaxis, ax.yaxis):
                ticks = axis.get_ticklabels()
                labels = [t.get_text().replace('Gptoss', 'GPT-OSS').replace('Glm', 'GLM') for t in ticks]
                if labels != [t.get_text() for t in ticks]:
                    axis.set_ticklabels(labels)
        fig.set_size_inches(7.4, 2.8)
        original_save(fig, str(OUT / f'{name}_behavior'))

    order = sorted(models, key=lambda m: -(summary['models'][m]['rho'] or 0))
    with patch.object(ab, 'ARMS', {'current': ''}), patch.object(ab, 'MODELS', list(models)), \
            patch.object(ab, 'ORDER_RHO', order), patch.object(ps, 'save', save_behavior):
        ab.fig_submetrics({'current': data})
    plt.close('all')


def main():
    OUT.mkdir(exist_ok=True)
    payload = {}
    for name, pattern, models in [
        ('public', ab.V33, PUBLIC),
        ('open', '~/squid5-runs/e52_v33/squid5_e52v33_codex_*4/*', OPEN),
        *[(arm, str(ab.ABLATION / f'squid5_e52v33ab_{arm}_docker_*4/*'),
           {m: PUBLIC[m] for m in ab.MODELS}) for arm in ab.ARMS]]:
        print('Computing', name, flush=True)
        data = compute(name, pattern, models)
        payload[name] = data
        (ROOT / f'results/cohort_{name}_20261104.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
        if name in ('public', 'open'):
            (ROOT / f'ko/tables/cohort_{name}_20261104.tex').write_text(table(data))
            figures(data, name)
        print(name, data['summary']['C_mean'], data['summary']['no_give'], flush=True)
    render_ablation(payload)
    # Only the two matched lower-prize arms identify the effect of splitting the pool.
    # The original public runs also differ in harness/version: retain as a descriptive reference.
    paired = {}
    for m in ab.MODELS:
        a = {g['seed']: g for g in payload['split600k']['games'] if g['model'] == m}
        b = {g['seed']: g for g in payload['flat150k']['games'] if g['model'] == m}
        paired[m] = {}
        for key in ['C', 'exited', 'dead', 'given_per_agent_round']:
            delta = np.array([b[s][key] - a[s][key] for s in SEEDS])
            rng = np.random.default_rng(20261104)
            paired[m][key] = dict(flat_minus_split=float(delta.mean()),
                ci95=fb.interval(delta[rng.integers(0, 10, (10000, 10))].mean(axis=1)))
    (ROOT / 'results/robustness_paired_20261104.json').write_text(json.dumps(paired, indent=1))


def render_ablation(payload):
    dest = OUT / 'ablation'
    dest.mkdir(exist_ok=True)
    order = sorted(ab.MODELS, key=lambda m: -payload['public']['summary']['models'][m]['rho'])
    ps, _ = ab.style()
    original_save = ps.save
    public_rho = [g['rho'] for g in payload['public']['games'] if g['rho'] is not None]
    lower = min(0, min(public_rho, default=0) - .3)

    def save(fig, path):
        if str(path).endswith('fig_coexistence_ablation'):
            for ax in fig.axes:
                # Three scatter panels per arm; identify rho by the original axis range.
                if np.allclose(ax.get_xlim(), (0, 11.5)):
                    ax.set_xlim(lower, 11.5)
                    ax.axvline(0, color='#888888', lw=.5, ls=':')
        original_save(fig, path)

    with patch.object(ab, 'OUT', dest), patch.object(ab, 'ORDER_RHO', order), patch.object(ps, 'save', save):
        ab.fig_coexistence(payload)
        ab.fig_submetrics(payload)


if __name__ == '__main__':
    main()
