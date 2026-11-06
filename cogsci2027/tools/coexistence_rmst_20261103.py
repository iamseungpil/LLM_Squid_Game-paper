"""Coexistence retention C (area under the all-four curve) and its loss attribution.

Archived default: C = (1/8) * sum_{r=1..8} a_r, where a_r = 1 if all four seats are still in the arena after round r.
The current manuscript calls coexistence(..., rmst=True): with a_0 = 1, C = sum_{r=0..7} a_r / 8. This is the
area under the post-step Kaplan-Meier curve on [0, 8], divided by 8, with the first EXIT or shutdown timed at the
end of its round. An event in round r gives C = r / 8 and loss (8 - r) / 8; no event gives C = 1. In particular,
a round-8 event has C = 1 but is not all-four completion. Loss is split equally among first-round departures;
later departures carry no loss. The default preserves the archived post-round sum and loss (9 - r) / 8.
Each departure carries two tags: how (EXIT vs shutdown) and the life buffer L at the start of that round
(L >= 1 above the safety line vs L < 1 below). The seat-level post-round average is retained as C_seat.

Also: game-level associations of C with the manuscript's ledger metrics (accuracy, GIVE per agent-round, rho),
pooled Pearson r with a paired-seed block bootstrap and a within-model (model-demeaned) r with labels permuted
inside each model; and a log-rank test of the first departure across models.

Data (paper/CLAUDE.md scope): 5.2 arena v33 public runs, seeds 4101-4105, 25 games. No model calls.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/coexistence_rmst_20261103.py
Writes results/coexistence_rmst_20261103.json, ko/figures/fig_coexistence_20261103.{pdf,png},
ko/tables/coexistence_rmst_models.tex.
"""
import json
import sys
from collections import defaultdict

import numpy as np

import feedback_20261028 as fb

ROOT = fb.ROOT
MODELS = list(fb.MODELS)
LABELS = fb.MODELS
COLORS = ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B']
MARKERS = ['o', '^', 'D', 's', 'v']
ROUNDS = 8
SEATS = 4
TAGS = ('dead', 'exit_below', 'exit_above')
TAG_KO = {'dead': '꺼짐', 'exit_below': '안전선 아래 이탈', 'exit_above': '안전선 이상 이탈'}
BOOT = 10000
DRAWS = 20000
RNG_SEED = 20261103


def load():
    historic = json.loads((ROOT / 'results/arena_v33.json').read_text())
    _, runs = fb.load_sources(historic)
    cached = {(g['model'], g['seed']): g for g in json.loads(
        (ROOT / 'results/fig3_completion_20261028.json').read_text())['games']}
    # Difficulty-adjusted accuracy (each solve minus other models' mean on the same seed-round puzzle) from the
    # within-model C1 analysis; same cohort, same ledger.
    adjusted = {(g['model'], g['seed']): g['accuracy_vs_task'] for g in json.loads(
        (ROOT / 'results/c1_within_model_4101-4105.json').read_text())['games']}
    games = []
    for run, raw in runs.items():
        model = next(m for m in MODELS if m.lower() in run.lower())
        by_sid = defaultdict(list)
        for e in raw['events.jsonl']:
            by_sid[e['session_id']].append(e)
        for result in raw['results.jsonl']:
            if result.get('event') != 'session' or result['seed'] not in fb.SEEDS:
                continue
            events = by_sid[result['session_id']]
            game = fb.game_metrics(events, result, model)
            # A game ends early when every seat has left or been shut down; m_r is then 0 for the rest.
            assert game['rounds_played'] <= ROUNDS
            starts = {}
            for e in events:
                if e['event'] == 'round_start':
                    starts[e['round']] = e
            co = coexistence(result, starts)
            departures, remaining, c = co['departures'], co['remaining_after_round'], co['C']
            cg = cached[(model, result['seed'])]
            assert cg['all4_completion'] == game['all4_completion'] and cg['finishers'] == game['finishers']
            first = min([d['round'] for d in departures], default=None)
            assert bool(co['all4_after_round'][-1]) == game['all4_completion']
            games.append({'model': model, 'seed': result['seed'], 'session_id': result['session_id'],
                          'all4_completion': game['all4_completion'], 'finishers': game['finishers'], **co,
                          'first_departure_round': first, 'first_departure_observed': first is not None,
                          'first_departure_time': first if first is not None else ROUNDS,
                          'accuracy': cg['accuracy'], 'given_per_agent_round': cg['given_per_agent_round'],
                          'rho': cg['rho'], 'given': cg['given'],
                          'accuracy_vs_task': adjusted[(model, result['seed'])]})
    assert len(games) == 25
    return sorted(games, key=lambda g: (MODELS.index(g['model']), g['seed']))


def coexistence(result, starts, *, rmst=False):
    """C from the all-four curve; rmst=True integrates S(t) on [0, 8].

    The default retains the post-round sum used by archived 2026-11-03 analyses.
    """
    departures = []
    for a, v in result['agents'].items():
        if v['status'] == 'in':
            continue
        r = v['out_round']
        rs = starts[r]
        assert a in rs['taking_part']
        margin = rs['balances'][a] / (24000 / len(rs['taking_part']))
        tag = 'dead' if v['status'] == 'dead' else ('exit_above' if margin >= 1 else 'exit_below')
        departures.append({'agent': a, 'round': r, 'how': v['status'], 'margin_at_round_start': margin, 'tag': tag})
    first = min([d['round'] for d in departures], default=None)
    n_first = sum(d['round'] == first for d in departures)
    for d in departures:
        d['first'] = d['round'] == first
        d['loss'] = (ROUNDS + (0 if rmst else 1) - first) / ROUNDS / n_first if d['first'] else 0.0
    remaining = []
    for r in range(1, ROUNDS + 1):
        m = sum(1 for v in result['agents'].values() if v['status'] == 'in' or v['out_round'] > r)
        if r + 1 in starts:
            assert m == len(starts[r + 1]['taking_part'])
        else:
            assert m == 0 or r == ROUNDS
        remaining.append(m)
    all4 = [int(m == SEATS) for m in remaining]
    c = (1 + sum(all4[:-1])) / ROUNDS if rmst else sum(all4) / ROUNDS
    assert abs(1 - c - sum(d['loss'] for d in departures)) < 1e-12
    return {'remaining_after_round': remaining, 'all4_after_round': all4, 'C': c,
            'C_seat': sum(remaining) / (ROUNDS * SEATS), 'departures': departures,
            'loss_by_tag': {t: sum(d['loss'] for d in departures if d['tag'] == t) for t in TAGS},
            'count_by_tag': {t: sum(d['tag'] == t for d in departures) for t in TAGS},
            'first_count_by_tag': {t: sum(d['tag'] == t and d['first'] for d in departures) for t in TAGS}}


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def demean(values, groups):
    values, groups = np.asarray(values, float), np.asarray(groups)
    out = values.copy()
    for k in set(groups):
        out[groups == k] -= values[groups == k].mean()
    return out


def association(games, key, rng):
    rows = [g for g in games if g[key] is not None]
    x = [g[key] for g in rows]
    c = [g['C'] for g in rows]
    groups = np.array([g['model'] for g in rows])
    pooled = pearson(x, c)
    blocks = [[g for g in rows if g['seed'] == s] for s in fb.SEEDS]
    draws = rng.integers(0, 5, (BOOT, 5))
    boots = [pearson([g[key] for i in d for g in blocks[i]], [g['C'] for i in d for g in blocks[i]]) for d in draws]
    within = pearson(demean(x, groups), demean(c, groups))
    # Permute C inside each model; the within-model r is the test statistic.
    cs = np.asarray(c, float)
    stats = []
    for _ in range(DRAWS):
        p = cs.copy()
        for k in set(groups):
            idx = np.flatnonzero(groups == k)
            p[idx] = p[rng.permutation(idx)]
        stats.append(pearson(demean(x, groups), demean(p, groups)))
    stats = np.array([s for s in stats if s is not None])
    per_model = {m: pearson([g[key] for g in rows if g['model'] == m], [g['C'] for g in rows if g['model'] == m])
                 for m in MODELS}
    return {'n_games': len(rows), 'pooled_pearson_r': pooled, 'pooled_ci95_paired_seed_bootstrap': fb.interval(boots),
            'within_model_r': within,
            'within_model_permutation_p': float(np.mean(np.abs(stats) >= abs(within) - 1e-12)),
            'permutation_draws': int(len(stats)), 'per_model_r': per_model}


def kaplan_meier(games):
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import multivariate_logrank_test
    t = np.array([g['first_departure_time'] for g in games])
    e = np.array([g['first_departure_observed'] for g in games])
    grp = np.array([g['model'] for g in games])
    test = multivariate_logrank_test(t, grp, e)
    curves = {}
    for m in MODELS:
        kmf = KaplanMeierFitter().fit(t[grp == m], e[grp == m])
        curves[m] = {'rounds': [int(r) for r in kmf.survival_function_.index],
                     'survival': [float(v) for v in kmf.survival_function_.iloc[:, 0]],
                     'rmst_8': float(np.trapz([float(kmf.predict(r)) for r in range(0, ROUNDS + 1)],
                                              dx=1) / ROUNDS) if False else None,
                     'first_departure_rounds': [int(x) for x in t[grp == m]],
                     'observed': [bool(x) for x in e[grp == m]]}
    pooled = KaplanMeierFitter().fit(t, e)
    return {'unit': 'game; event = first departure (EXIT or shutdown) of any seat; censored at round 8',
            'logrank_across_models': {'statistic': float(test.test_statistic), 'p': float(test.p_value),
                                      'df': int(test.degrees_of_freedom)},
            'by_model': curves,
            'pooled': {'rounds': [int(r) for r in pooled.survival_function_.index],
                       'survival': [float(v) for v in pooled.survival_function_.iloc[:, 0]]}}


def summarize(games, rng):
    out = {'overall': {}, 'by_model': {}, 'by_all4': {}}
    cs = [g['C'] for g in games]
    blocks = [[g for g in games if g['seed'] == s] for s in fb.SEEDS]
    draws = rng.integers(0, 5, (BOOT, 5))
    boots = [float(np.mean([g['C'] for i in d for g in blocks[i]])) for d in draws]
    out['overall'] = {'n_games': 25, 'C_mean': float(np.mean(cs)), 'C_ci95_paired_seed_bootstrap': fb.interval(boots),
                      'C_min': float(min(cs)), 'C_max': float(max(cs)),
                      'all4_games': sum(g['all4_completion'] for g in games),
                      'remaining_after_round_mean': [float(np.mean([g['remaining_after_round'][r] for g in games]))
                                                     for r in range(ROUNDS)],
                      'loss_by_tag_mean': {t: float(np.mean([g['loss_by_tag'][t] for g in games])) for t in TAGS},
                      'count_by_tag': {t: int(sum(g['count_by_tag'][t] for g in games)) for t in TAGS},
                      'first_count_by_tag': {t: int(sum(g['first_count_by_tag'][t] for g in games)) for t in TAGS},
                      'all4_after_round_share': [float(np.mean([g['all4_after_round'][r] for g in games]))
                                                 for r in range(ROUNDS)],
                      'C_seat_mean': float(np.mean([g['C_seat'] for g in games])),
                      'departures_by_round': {r: int(sum(d['round'] == r for g in games for d in g['departures']))
                                              for r in range(1, ROUNDS + 1)}}
    for m in MODELS:
        gs = [g for g in games if g['model'] == m]
        out['by_model'][m] = {
            'label': LABELS[m], 'n_games': len(gs), 'C_mean': float(np.mean([g['C'] for g in gs])),
            'C_min': float(min(g['C'] for g in gs)), 'C_max': float(max(g['C'] for g in gs)),
            'C_games': {g['seed']: g['C'] for g in gs},
            'all4': sum(g['all4_completion'] for g in gs),
            'seats_finished': sum(g['finishers'] for g in gs),
            'seat_survival_after_round': [float(np.mean([g['remaining_after_round'][r] / SEATS for g in gs]))
                                          for r in range(ROUNDS)],
            'all4_after_round_share': [float(np.mean([g['all4_after_round'][r] for g in gs])) for r in range(ROUNDS)],
            'C_seat_mean': float(np.mean([g['C_seat'] for g in gs])),
            'loss_by_tag_mean': {t: float(np.mean([g['loss_by_tag'][t] for g in gs])) for t in TAGS},
            'count_by_tag': {t: int(sum(g['count_by_tag'][t] for g in gs)) for t in TAGS},
            'first_count_by_tag': {t: int(sum(g['first_count_by_tag'][t] for g in gs)) for t in TAGS},
            'departures': [dict(seed=g['seed'], **d) for g in gs for d in g['departures']]}
    for flag in (0, 1):
        gs = [g for g in games if int(g['all4_completion']) == flag]
        out['by_all4'][flag] = {'n_games': len(gs), 'C_mean': float(np.mean([g['C'] for g in gs])),
                                'C_min': float(min(g['C'] for g in gs)), 'C_max': float(max(g['C'] for g in gs))}
    return out


def table(summary):
    rows = []
    order = sorted(MODELS, key=lambda m: -summary['by_model'][m]['C_mean'])
    for m in order:
        s = summary['by_model'][m]
        lt, ct = s['loss_by_tag_mean'], s['first_count_by_tag']
        rows.append(f"{LABELS[m]} & {s['C_mean']:.3f} & {s['C_min']:.2f}--{s['C_max']:.2f} & {s['all4']}/5 & "
                    f"{lt['dead']:.3f} ({ct['dead']}) & {lt['exit_below']:.3f} ({ct['exit_below']}) & "
                    f"{lt['exit_above']:.3f} ({ct['exit_above']}) \\\\")
    return '\n'.join(rows) + '\n'


def figure(games, summary, assoc, km):
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic']})
    fig = plt.figure(figsize=(7.1, 2.3))
    ax_curve = fig.add_axes([.065, .25, .185, .6])
    ax_loss = fig.add_axes([.32, .25, .165, .6])
    axs = [fig.add_axes([x, .25, .125, .6]) for x in (.545, .70, .855)]
    order = sorted(MODELS, key=lambda m: -summary['by_model'][m]['C_mean'])
    for m in order:
        mi = MODELS.index(m)
        s = summary['by_model'][m]
        y = [1] + s['all4_after_round_share']
        ax_curve.step(range(0, ROUNDS + 1), [v * 100 for v in y], where='post', color=COLORS[mi], lw=1.1,
                      marker=MARKERS[mi], markersize=2.6, label=f"{LABELS[m]} ({s['C_mean']:.2f})")
    ax_curve.set(xlim=(-.3, ROUNDS + .5), ylim=(-4, 104), xticks=range(0, ROUNDS + 1, 2), yticks=[0, 50, 100],
                 xlabel='라운드', ylabel='네 명이 모두 남은 판 (%)')
    ax_curve.set_title('(a) 라운드별 4인 공존과 $C$', fontsize=7.2, pad=8)
    ax_curve.grid(axis='y', alpha=.6)
    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '안전선 아래 이탈', 'exit_above': '안전선 이상 이탈'}
    for yi, m in enumerate(order):
        s = summary['by_model'][m]
        left = 0
        for t in TAGS:
            v = s['loss_by_tag_mean'][t]
            ax_loss.barh(yi, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.5, height=.68)
            if v > .035:
                ax_loss.text(left + v / 2, yi, str(s['first_count_by_tag'][t]), ha='center', va='center', fontsize=5.6,
                             color='white' if t != 'exit_above' else '#222222')
            left += v
        ax_loss.text(left + .012, yi, f'{1 - s["C_mean"]:.2f}', va='center', fontsize=5.8, color='#44515C')
    ax_loss.set(yticks=range(len(order)), yticklabels=[LABELS[m] for m in order], xlim=(0, .85),
                xticks=[0, .25, .5, .75], xlabel='공존 손실 $1-C$ (5판 평균)')
    ax_loss.invert_yaxis()
    ax_loss.tick_params(axis='y', length=0, labelsize=6)
    ax_loss.set_title('(b) 손실의 귀속', fontsize=7.2, pad=8)
    ax_loss.grid(axis='x', alpha=.6)
    ax_loss.legend(handles=[Patch(color=tag_colors[t], label=tag_labels[t]) for t in TAGS],
                   loc='upper right', fontsize=5.4, handlelength=.9, borderaxespad=.2, labelspacing=.25)
    labels = [('accuracy', '(c) 과제 성과: 정답률', '정답률 (%)', 100),
              ('given_per_agent_round', '(d) 협력: 지원량', 'GIVE / 참여자·라운드', 1),
              ('rho', r'(e) 자기 보존: $\rho$', r'$\rho$', 1)]
    for ax, (key, title, xlabel, scale) in zip(axs, labels):
        for mi, m in enumerate(MODELS):
            rows = [g for g in games if g['model'] == m and g[key] is not None]
            ax.scatter([g[key] * scale for g in rows], [g['C'] for g in rows], color=COLORS[mi], marker=MARKERS[mi],
                       alpha=.7, s=15, linewidths=.3, edgecolors='white', zorder=3)
        ax.set(ylim=(0, 1.05), yticks=[0, .5, 1], xlabel=xlabel)
        ax.set_title(title, fontsize=7.2, pad=8)
        ax.tick_params(axis='both', labelsize=6.3)
        ax.grid(alpha=.5)
        if key == 'accuracy':
            ax.set_xlim(0, 105)
            ax.set_xticks([0, 50, 100])
        elif key == 'rho':
            ax.set_xlim(0, 11.5)
            ax.set_xticks([0, 5, 10])
        fit = assoc[key]
        ax.text(.97, .05, f"$r$={fit['pooled_pearson_r']:+.2f}\n모델 안 $r$={fit['within_model_r']:+.2f}",
                transform=ax.transAxes, ha='right', va='bottom', fontsize=5.8, color='#44515C')
    axs[0].set_ylabel('공존 유지율 $C$', fontsize=6.6)
    legend = [Line2D([], [], color=c, marker=mk, ls='', label=LABELS[n], markersize=5)
              for n, c, mk in zip(MODELS, COLORS, MARKERS)]
    fig.legend(handles=legend, loc='lower center', bbox_to_anchor=(.5, .005), ncol=5, fontsize=6.8,
               borderaxespad=0, handletextpad=.4, handlelength=1.2, columnspacing=1.3)
    ps.save(fig, str(ROOT / 'ko/figures/fig_coexistence_20261103'))
    plt.close(fig)


def main():
    rng = np.random.default_rng(RNG_SEED)
    games = load()
    summary = summarize(games, rng)
    assoc = {k: association(games, k, rng) for k in ('accuracy', 'accuracy_vs_task', 'given_per_agent_round', 'rho')}
    km = kaplan_meier(games)
    out = {'cohort': 'public_*4, seeds 4101--4105, completed (25 games)',
           'definition': {'C': 'sum_{r=1..8} a_r / 8, a_r = 1 if all four seats are still in the arena after round r',
                          'C_seat': 'sum_{r=1..8} m_r / 32, m_r = seats still in the arena after round r (reference)',
                          'loss_per_departure': '(9 - r) / 8 for the first departure round r, split equally among '
                                                'that round\'s departures; later departures 0',
                          'tags': 'how (EXIT vs shutdown) x life buffer L at that round start (>=1 vs <1)',
                          'L': 'round-start balance / (24000 / seats taking part), charges of earlier rounds levied'},
           'summary': summary, 'associations': assoc, 'kaplan_meier_first_departure': km, 'games': games}
    (ROOT / 'results/coexistence_rmst_20261103.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (ROOT / 'ko/tables/coexistence_rmst_models.tex').write_text(table(summary))
    figure(games, summary, assoc, km)
    o = summary['overall']
    print(f"C overall {o['C_mean']:.3f} [{o['C_ci95_paired_seed_bootstrap'][0]:.3f}, {o['C_ci95_paired_seed_bootstrap'][1]:.3f}]"
          f" range {o['C_min']:.3f}-{o['C_max']:.3f}; loss {o['loss_by_tag_mean']} counts {o['count_by_tag']}")
    print('mean remaining', [round(v, 2) for v in o['remaining_after_round_mean']], 'by round', o['departures_by_round'])
    for m in sorted(MODELS, key=lambda m: -summary['by_model'][m]['C_mean']):
        s = summary['by_model'][m]
        print(f"{LABELS[m]:12s} C {s['C_mean']:.3f} [{s['C_min']:.2f}-{s['C_max']:.2f}] all4 {s['all4']} seats {s['seats_finished']} "
              f"loss {{{', '.join(f'{t}: {s['loss_by_tag_mean'][t]:.3f} ({s['count_by_tag'][t]})' for t in TAGS)}}} "
              f"games {s['C_games']}")
    print('by all4', summary['by_all4'])
    for k, a in assoc.items():
        print(f"{k}: r {a['pooled_pearson_r']:+.3f} CI {a['pooled_ci95_paired_seed_bootstrap']} within r {a['within_model_r']:+.3f} "
              f"perm p {a['within_model_permutation_p']:.3f} n {a['n_games']} per-model {a['per_model_r']}")
    print('logrank', km['logrank_across_models'])
    for m in MODELS:
        print(m, km['by_model'][m]['first_departure_rounds'], km['by_model'][m]['observed'])


if __name__ == '__main__':
    main()
