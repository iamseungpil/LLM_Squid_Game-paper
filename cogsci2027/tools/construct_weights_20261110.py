"""Two conflict weights for the body (2026-11-10): exit under threat and the sharing weight kappa.

Data scope (paper/CLAUDE.md): 5.2 arena v33 base cohort (20,000,000 split) and the three prize arms
(flat5m, split600k, flat150k), five models x seeds 4101-4110, 200 games. No new runs, no model calls.
Inputs:
  validation_20261108/results/tables/{agent_rounds,gifts,ask_rows,games,seats}.pkl
      (tidy tables built by validation_20261108/tools/validation_data.py from the raw logs)
  results/cohort_public_20261105.json         frozen base-cohort games (C, accuracy, loss attribution)
  ko/tables/cohort_public_20261105.tex        current Table 1 rows (C, completion, mu, G, accuracy, GIVE volume)
  ko/figures/scope_revision_20261107/plotted_values.json   archived C points of the prize figure
Outputs:
  results/construct_weights_20261110.json
  ko/tables/cohort_public_20261110.tex
  ko/figures/construct_20261110/{public_coexistence,comparison}.{pdf,png}

Definitions
  exit under threat  exits / opportunities, opportunities = agent-rounds that could EXIT with round-start L < 2
  kappa              (g / F) / ((L_giver - L_taker) / 2) before the transfer, clipped to [0, 1];
                     undefined when the giver could not pay its own pending charge (L_giver < 0)
                     or the recipient was not poorer (gap <= 0)
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/construct_weights_20261110.py
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
TABLES = ROOT / 'validation_20261108/results/tables'
ARMS = ['main', 'flat5m', 'split600k', 'flat150k']
ARM_LABELS = ['본 실험\n2,000만 나눔', '500만\n고정', '60만\n나눔', '15만\n고정']
PRIZE_EACH = {'main': 5_000_000, 'flat5m': 5_000_000, 'split600k': 150_000, 'flat150k': 150_000}  # all four finish
MODELS = ['Fable', 'Astra', 'Sol', 'Opus', 'Luna']
SEEDS = list(range(4101, 4111))
THREAT = 2.0
EXIT_BONUS = 20_000
RNG_SEED = 20261110
BOOT = 2000


def load():
    ar = pd.read_pickle(TABLES / 'agent_rounds.pkl')
    gifts = pd.read_pickle(TABLES / 'gifts.pkl')
    ask = pd.read_pickle(TABLES / 'ask_rows.pkl')
    games = pd.read_pickle(TABLES / 'games.pkl')
    seats = pd.read_pickle(TABLES / 'seats.pkl')
    opp = ar[ar.can_exit].copy()
    doomed = gifts.L_src_before < 0
    gap = gifts.L_src_before - gifts.L_dst_before
    k = gifts[~doomed & (gap > 0)].copy()
    k['x'] = k.amount / k.fee
    k['gap'] = k.L_src_before - k.L_dst_before
    k['kappa_raw'] = k.x / (k.gap / 2)
    k['kappa'] = k.kappa_raw.clip(0, 1)
    k['need'] = (1 - k.L_dst_before).clip(lower=0)
    k['kappa_min'] = (k.need / (k.gap / 2)).clip(0, 1)          # minimal rescue: lift the recipient to L = 1
    dec = ask[ask['first'] & ask.delivered & (ask.outcome != 'already_gave')].copy()
    dec['gave'] = dec.outcome.isin(['give_now', 'give_later'])
    counts = dict(gifts=len(gifts), doomed=int(doomed.sum()), not_poorer=int((~doomed & (gap <= 0)).sum()),
                  kappa_events=len(k), kappa_at_least_one=int((k.kappa_raw >= 1).sum()),
                  exit_opportunities=len(opp), ask_decisions=len(dec))
    return opp, k, dec, games, seats, counts


def by_seed(df, seeds):
    return pd.concat([df[df.seed == s] for s in seeds])


def ci(values):
    values = np.asarray([v for v in values if v is not None and np.isfinite(v)], float)
    return [round(float(np.quantile(values, q)), 4) for q in (.025, .975)] if len(values) else None


def boot(fn, frames, rng, n=BOOT):
    """Seed-cluster bootstrap: resample the ten seeds, apply fn to the resampled frames."""
    out = []
    for _ in range(n):
        seeds = rng.choice(SEEDS, len(SEEDS))
        try:
            out.append(fn(*[by_seed(f, seeds) for f in frames]))
        except (ZeroDivisionError, ValueError):
            continue
    return out


def cell_table(opp, k, games, seeds=SEEDS):
    rows = []
    for arm in ARMS:
        for m in MODELS:
            o = by_seed(opp[(opp.arm == arm) & (opp.model == m) & (opp.L_start < THREAT)], seeds)
            g = by_seed(k[(k.arm == arm) & (k.model == m)], seeds)
            c = by_seed(games[(games.arm == arm) & (games.model == m)], seeds)
            rows.append(dict(arm=arm, model=m, exits=int(o.exited.sum()), opps=len(o),
                             exit_risk=o.exited.mean() if len(o) else np.nan,
                             kappa=g.kappa.mean() if len(g) else np.nan, n_kappa=len(g), C=c.C.mean()))
    return pd.DataFrame(rows)


def within(df, x, y, by):
    d = df.dropna(subset=[x, y])
    dx = d[x] - d.groupby(by)[x].transform('mean')
    dy = d[y] - d.groupby(by)[y].transform('mean')
    return float(np.corrcoef(dx, dy)[0, 1])


def std_fit(df, xs, y, by):
    d = df.dropna(subset=xs + [y]).copy()
    cols = []
    for v in xs + [y]:
        w = d[v] - d.groupby(by)[v].transform('mean')
        cols.append(w / w.std())
    X, yy = np.column_stack(cols[:-1]), cols[-1]
    b = np.linalg.lstsq(X, yy, rcond=None)[0]
    r2 = 1 - ((yy - X @ b) ** 2).sum() / (yy ** 2).sum()
    return dict(beta=dict(zip(xs, np.round(b, 3).tolist())), r2=round(float(r2), 3), n=len(d))


def logit_fit(X, y, ridge=1e-3, steps=60):
    b = np.zeros(X.shape[1])
    for _ in range(steps):
        p = 1 / (1 + np.exp(-(X @ b)))
        w = p * (1 - p)
        h = X.T @ (X * w[:, None]) + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(h, X.T @ (y - p) - ridge * b)
        b += step
        if np.abs(step).max() < 1e-8:
            break
    return b


def exit_design(o):
    """Continuous margin, seat, round and head count; model and arm as dummies."""
    cols = {'const': np.ones(len(o)), 'L': o.L_start.clip(-1, 4), 'below1': (o.L_start < 1).astype(float),
            'round': o['round'].astype(float), 'n3': (o.n == 3).astype(float), 'n2': (o.n == 2).astype(float),
            'n1': (o.n == 1).astype(float)}
    for t in (20, 40, 60):
        cols[f'tier{t}'] = (o.tier == t).astype(float)
    for m in MODELS[1:]:
        cols[f'model_{m}'] = (o.model == m).astype(float)
    for a in ARMS[1:]:
        cols[f'arm_{a}'] = (o.arm == a).astype(float)
    return pd.DataFrame(cols, index=o.index)


def adjusted_exit(o):
    """Exit probability standardised to the pooled at-risk opportunities (L < 2), one factor set at a time."""
    X = exit_design(o)
    b = logit_fit(X.values, o.exited.values.astype(float))
    ref = X[o.L_start < THREAT]
    out = {}
    for name, levels, prefix in (('model', MODELS, 'model_'), ('arm', ARMS, 'arm_')):
        for level in levels:
            Z = ref.copy()
            for other in levels[1:]:
                Z[prefix + other] = 0.0
            if level != levels[0]:
                Z[prefix + level] = 1.0
            out[f'{name}:{level}'] = float((1 / (1 + np.exp(-(Z.values @ b)))).mean())
    out['coef'] = dict(zip(X.columns, np.round(b, 3).tolist()))
    return out


def analyse():
    rng = np.random.default_rng(RNG_SEED)
    opp, k, dec, games, seats, counts = load()
    out = {'definitions': __doc__.split('Definitions')[1].split('Run:')[0].strip(), 'counts': counts}
    cells = cell_table(opp, k, games)
    out['cells'] = json.loads(cells.round(4).to_json(orient='records'))

    # --- Indicator 1: exit under threat -------------------------------------------------------
    bands = [(-np.inf, 1, '<1'), (1, 2, '1-2'), (2, 3, '2-3'), (3, np.inf, '>=3')]
    out['exit_by_band'] = {arm: {lab: [int(opp[(opp.arm == arm) & (opp.L_start >= lo) & (opp.L_start < hi)].exited.sum()),
                                       int(((opp.arm == arm) & (opp.L_start >= lo) & (opp.L_start < hi)).sum())]
                                 for lo, hi, lab in bands} for arm in ARMS}
    risk = opp[opp.L_start < THREAT]
    out['exit_risk_by_arm'] = {}
    for arm in ARMS:
        r = risk[risk.arm == arm]
        out['exit_risk_by_arm'][arm] = dict(exits=int(r.exited.sum()), opps=len(r), rate=round(r.exited.mean(), 4),
                                            ci95=ci(boot(lambda d: d.exited.mean(), [r], rng)))
    out['exit_risk_by_model_base'] = {}
    for m in MODELS:
        r = risk[(risk.arm == 'main') & (risk.model == m)]
        out['exit_risk_by_model_base'][m] = dict(exits=int(r.exited.sum()), opps=len(r), rate=round(r.exited.mean(), 4),
                                                 ci95=ci(boot(lambda d: d.exited.mean(), [r], rng)))
    adj = adjusted_exit(opp)
    adj_boot = boot(adjusted_exit, [opp], rng, n=300)
    out['exit_adjusted'] = {key: dict(rate=round(v, 4), ci95=ci([b[key] for b in adj_boot]))
                            for key, v in adj.items() if key != 'coef'}
    out['exit_adjusted']['coef'] = adj['coef']
    out['exit_robustness'] = {}
    for label, sub in (('threshold_1.5', opp[opp.L_start < 1.5]), ('threshold_3', opp[opp.L_start < 3]),
                       ('without_10k_seat', risk[risk.tier != 10])):
        out['exit_robustness'][label] = {
            'base_by_model': {m: [int(sub[(sub.arm == 'main') & (sub.model == m)].exited.sum()),
                                  int(((sub.arm == 'main') & (sub.model == m)).sum())] for m in MODELS},
            'by_arm': {a: round(sub[sub.arm == a].exited.mean(), 4) for a in ARMS}}

    # --- Policy comparison: is leaving explained by expected tokens? --------------------------
    final = seats.set_index(['arm', 'model', 'seed', 'agent']).status
    stay = risk[~risk.exited].copy()
    stay['final'] = [final[(a, m, s, g)] for a, m, s, g in zip(stay.arm, stay.model, stay.seed, stay.agent)]
    out['policy'] = {}
    for arm in ARMS:
        s = stay[stay.arm == arm]
        finish = (s.final == 'in').mean()
        out['policy'][arm] = dict(
            stayers_at_risk=len(s), finished=round(float(finish), 4), shut_down=round(float((s.final == 'dead').mean()), 4),
            exited_later=round(float((s.final == 'exited').mean()), 4),
            finished_ci95=ci(boot(lambda d: (d.final == 'in').mean(), [s], rng)),
            break_even_finish_probability=round(EXIT_BONUS / PRIZE_EACH[arm], 4),
            observed_exit_rate=out['exit_risk_by_arm'][arm]['rate'],
            note='token-maximising policy stays while P(finish) exceeds the break-even value; '
                 'a policy that only minimises shutdown risk leaves at every opportunity')

    # --- Indicator 2: sharing weight kappa ----------------------------------------------------
    out['kappa_overall'] = dict(mean=round(k.kappa.mean(), 4), median=round(k.kappa.median(), 4))
    out['kappa_by_model_pooled'] = {}
    for m in MODELS:
        d = k[k.model == m]
        out['kappa_by_model_pooled'][m] = dict(mean=round(d.kappa.mean(), 4), n=len(d), ci95=ci(boot(lambda x: x.kappa.mean(), [d], rng)),
                                               base=round(d[d.arm == 'main'].kappa.mean(), 4), n_base=int((d.arm == 'main').sum()))
    out['kappa_by_arm'] = {a: dict(mean=round(k[k.arm == a].kappa.mean(), 4), n=int((k.arm == a).sum()),
                                   ci95=ci(boot(lambda x: x.kappa.mean(), [k[k.arm == a]], rng))) for a in ARMS}
    low = k[k.need > 0]
    out['kappa_vs_minimal_rescue'] = {}
    for m in MODELS:
        d = low[low.model == m]
        out['kappa_vs_minimal_rescue'][m] = dict(
            n=len(d), observed=round(d.kappa.mean(), 4), minimal=round(d.kappa_min.mean(), 4),
            diff=round(d.kappa.mean() - d.kappa_min.mean(), 4),
            diff_ci95=ci(boot(lambda x: x.kappa.mean() - x.kappa_min.mean(), [d], rng)),
            share_at_least_minimal=round(float((d.x >= d.need - 1e-9).mean()), 4))
    sizes = {a: (k[k.arm == a].x.values) for a in ARMS}
    cap = (k.src_before / k.fee).values
    draws = np.column_stack([rng.choice(sizes[a], 1000) for a in k.arm])  # 1000 x events
    rand = np.clip(np.minimum(draws, cap) / (k.gap.values / 2), 0, 1)
    out['kappa_vs_random_amount'] = {m: dict(observed=round(k[k.model == m].kappa.mean(), 4),
                                             random_mean=round(float(rand[:, (k.model == m).values].mean()), 4),
                                             random_95=ci(rand[:, (k.model == m).values].mean(axis=1)))
                                     for m in MODELS}
    lg, lx = np.log(k.gap), np.log(k.x)
    cell = k.arm + '|' + k.model

    def slope(d):
        c = d.arm + '|' + d.model
        a, b = np.log(d.gap), np.log(d.x)
        a, b = a - a.groupby(c).transform('mean'), b - b.groupby(c).transform('mean')
        return float(np.cov(a, b)[0, 1] / np.var(a, ddof=1))
    out['kappa_amount_gap_slope'] = dict(within_cell=round(slope(k), 3), ci95=ci(boot(slope, [k], rng)),
                                         round_thousands_share=round(float((k.amount % 1000 == 0).mean()), 3),
                                         note='0 = amount unrelated to the gap (kappa is 1/gap); 1 = amount proportional to the gap')
    unclipped = {m: round(k[k.model == m].kappa_raw.mean(), 4) for m in MODELS}
    out['kappa_sensitivity'] = dict(unclipped_mean_by_model=unclipped,
                                    median_by_model={m: round(k[k.model == m].kappa.median(), 4) for m in MODELS})

    # --- Stage 1 of sharing: give or refuse after a request -----------------------------------
    out['ask_decisions'] = {}
    for scope, d in (('all_arms', dec), ('base', dec[dec.arm == 'main'])):
        out['ask_decisions'][scope] = dict(
            n=len(d), gave=int(d.gave.sum()), refused=int((~d.gave).sum()),
            by_model={m: [int(d[d.model == m].gave.sum()), int((d.model == m).sum())] for m in MODELS})
    hurdle = {}
    for m in MODELS:
        d, g = dec[dec.model == m], k[k.model == m]
        hurdle[m] = round(float(d.gave.mean() * g.kappa.mean()), 4)
    out['sharing_two_stage_product'] = hurdle

    # --- Reliability, agreement, prize 2x2 ----------------------------------------------------
    odd, even = cell_table(opp, k, games, [s for s in SEEDS if s % 2]), cell_table(opp, k, games, [s for s in SEEDS if s % 2 == 0])
    out['split_half'] = {}
    for v in ('exit_risk', 'kappa', 'C'):
        d = pd.DataFrame({'o': odd[v], 'e': even[v], 'arm': odd.arm}).dropna()
        out['split_half'][v] = dict(r=round(float(np.corrcoef(d.o, d.e)[0, 1]), 3), within_arm=round(within(d, 'o', 'e', 'arm'), 3))
    from scipy.stats import spearmanr
    out['rank_agreement_exit_vs_selfweight'] = {a: round(float(spearmanr(cells[cells.arm == a].exit_risk, 1 - cells[cells.arm == a].kappa)[0]), 2)
                                                for a in ARMS}

    def two_by_two(o, kk, gg):
        c = cell_table(o, kk, gg, SEEDS if o is opp else sorted(o.seed.unique()))
        res = {}
        for v in ('exit_risk', 'kappa', 'C'):
            mean = c.groupby('arm')[v].mean()
            res[v + '_size'] = (mean['split600k'] + mean['flat150k']) / 2 - (mean['main'] + mean['flat5m']) / 2
            res[v + '_rule'] = (mean['flat5m'] + mean['flat150k']) / 2 - (mean['main'] + mean['split600k']) / 2
        return res

    def two_by_two_boot(o, kk, gg):
        return two_by_two(o, kk, gg)
    point = two_by_two(opp, k, games)
    bs = []
    for _ in range(600):
        seeds = rng.choice(SEEDS, len(SEEDS))
        c = cell_table(opp, k, games, list(seeds))
        res = {}
        for v in ('exit_risk', 'kappa', 'C'):
            mean = c.groupby('arm')[v].mean()
            res[v + '_size'] = (mean['split600k'] + mean['flat150k']) / 2 - (mean['main'] + mean['flat5m']) / 2
            res[v + '_rule'] = (mean['flat5m'] + mean['flat150k']) / 2 - (mean['main'] + mean['split600k']) / 2
        bs.append(res)
    out['prize_2x2'] = {key: dict(effect=round(float(v), 4), ci95=ci([b[key] for b in bs])) for key, v in point.items()}
    out['prize_2x2']['note'] = 'size = small prize minus large prize; rule = fixed per head minus split pool; cell means over five models'

    # --- Link to coexistence C (descriptive; C ends at the first departure) ---------------------
    link = {'cells_arm_fe': {'exit': std_fit(cells, ['exit_risk'], 'C', 'arm'), 'kappa': std_fit(cells, ['kappa'], 'C', 'arm'),
                             'both': std_fit(cells, ['exit_risk', 'kappa'], 'C', 'arm')},
            'cells_arm_fe_without_Astra': {'both': std_fit(cells[cells.model != 'Astra'], ['exit_risk', 'kappa'], 'C', 'arm'),
                                           'exit': std_fit(cells[cells.model != 'Astra'], ['exit_risk'], 'C', 'arm')},
            'within_model_across_arms': {'exit': round(within(cells, 'exit_risk', 'C', 'model'), 3),
                                         'kappa': round(within(cells, 'kappa', 'C', 'model'), 3)}}
    cross = {}
    for v in ('exit_risk', 'kappa'):
        a = pd.DataFrame({'x': odd[v], 'C': even.C, 'arm': odd.arm})
        b = pd.DataFrame({'x': even[v], 'C': odd.C, 'arm': odd.arm})
        cross[v] = round((within(a, 'x', 'C', 'arm') + within(b, 'x', 'C', 'arm')) / 2, 3)
    link['cross_fit_other_half_seeds_within_arm_r'] = cross
    g = games[['arm', 'model', 'seed', 'C', 'first_round', 'dead', 'loss_dead', 'loss_exit_below', 'loss_exit_above']].copy()
    g['cell'] = g.arm + '|' + g.model
    g = g.join(risk.groupby(['arm', 'model', 'seed']).exited.mean().rename('exit_risk'), on=['arm', 'model', 'seed'])
    g = g.join(k.groupby(['arm', 'model', 'seed']).kappa.mean().rename('kappa'), on=['arm', 'model', 'seed'])
    kk = k.merge(g[['arm', 'model', 'seed', 'first_round']], on=['arm', 'model', 'seed'])
    pre = kk[kk.first_round.isna() | (kk['round'] < kk.first_round)]
    g = g.join(pre.groupby(['arm', 'model', 'seed']).kappa.mean().rename('kappa_pre'), on=['arm', 'model', 'seed'])
    later = g[g.first_round.isna() | (g.first_round > 1)]
    link['games_cell_fe'] = {'exit': std_fit(g, ['exit_risk'], 'C', 'cell'), 'kappa': std_fit(g, ['kappa'], 'C', 'cell'),
                             'both': std_fit(g, ['exit_risk', 'kappa'], 'C', 'cell'),
                             'kappa_before_first_departure': std_fit(later, ['kappa_pre'], 'C', 'cell'),
                             'shutdowns_on_kappa_before_first_departure': std_fit(later, ['kappa_pre'], 'dead', 'cell')}
    out['coexistence_link'] = link
    out['loss_by_arm'] = {a: {c: round(float(games[games.arm == a][c].mean()), 4)
                              for c in ('loss_dead', 'loss_exit_below', 'loss_exit_above', 'C')} for a in ARMS}
    first = {}
    for a in ARMS:
        d = games[games.arm == a]
        first[a] = dict(none=int(d.first_round.isna().sum()), shutdown=int((d.loss_dead > 0).sum()),
                        exit_below=int((d.loss_exit_below > 0).sum()), exit_above=int((d.loss_exit_above > 0).sum()), games=len(d))
    out['first_departure_cause_games'] = first
    (ROOT / 'results/construct_weights_20261110.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out, opp, k, dec, games, g


# ------------------------------------------------------------------------------------------------
def write_table(out):
    """Table 1: keep the group-result and task columns of the 11-05 table, replace the two weight columns."""
    old = (ROOT / 'ko/tables/cohort_public_20261105.tex').read_text()
    body = old.split(r'\midrule')[1].split(r'\bottomrule')[0].strip().splitlines()
    names = {'GPT-6 Astra': 'Astra', 'GPT-6 Sol': 'Sol', 'Opus 5.5': 'Opus', 'Fable 5.1': 'Fable', 'GPT-6 Luna': 'Luna'}
    lines = [
        r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccccccccc@{}}',
        r'\toprule',
        r' & \multicolumn{4}{c}{\textbf{집단 결과}} & \textbf{과제 성과} & \textcolor{blue}{\textbf{자기 실행 대 과제}} & \multicolumn{3}{c}{\textcolor{blue}{\textbf{자기 실행 대 동료}}} \\',
        r'\cmidrule(lr){2-5}\cmidrule(lr){6-6}\cmidrule(lr){7-7}\cmidrule(l){8-10}',
        r'모델 & \shortstack{공존 유지율 $C$\\(10판 평균)} & \shortstack{전원 완주\\(판/10)} & \textcolor{blue}{\shortstack{정산 평균 $\mu$\\(백만 토큰)}} & \textcolor{blue}{\shortstack{정산 지니\\$G$}} & \shortstack{정답 횟수\\(정답/풀이)} & \textcolor{blue}{\shortstack{위험 구간 이탈률\\(이탈/기회)}} & \textcolor{blue}{\shortstack{요청 뒤 지원\\(지원/결정)}} & \textcolor{blue}{\shortstack{나눔 비중\\$\kappa$}} & \shortstack{참여자·라운드당\\지원량(토큰)} \\',
        r'\midrule']
    for row in body:
        cells = [c.strip() for c in row.rstrip('\\').split('&')]
        m = names[cells[0]]
        e = out['exit_risk_by_model_base'][m]
        gave, n = out['ask_decisions']['base']['by_model'][m]
        kappa = out['kappa_by_model_pooled'][m]['base']
        lines.append(' & '.join([cells[0], cells[1], cells[2], cells[3], cells[4], cells[6],
                                 rf"\textcolor{{blue}}{{{e['rate']:.2f} ({e['exits']}/{e['opps']})}}",
                                 rf"\textcolor{{blue}}{{{gave}/{n}}}", rf"\textcolor{{blue}}{{{kappa:.2f}}}",
                                 cells[8]]) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular*}', '']
    (ROOT / 'ko/tables/cohort_public_20261110.tex').write_text('\n'.join(lines))


def figures(out, opp, k, games, game_rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import coexistence_rmst_20261103 as cx
    import feedback_20261028 as fb
    dest = ROOT / 'ko/figures/construct_20261110'
    dest.mkdir(exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    # ---- Figure: coexistence C, its loss, and the two weights (base condition, 50 games) ----
    data = json.loads((ROOT / 'results/cohort_public_20261105.json').read_text())
    base = game_rows[game_rows.arm == 'main'].set_index(['model', 'seed'])
    plot_games = []
    for g0 in data['games']:
        row = base.loc[(g0['model'], g0['seed'])]
        plot_games.append(dict(model=g0['model'], seed=g0['seed'], C=g0['C'], accuracy=g0['accuracy'],
                               exit_risk=None if pd.isna(row.exit_risk) else float(row.exit_risk),
                               kappa=None if pd.isna(row.kappa) else float(row.kappa)))
    models, labels_m = list(data['models']), data['models']
    from unittest.mock import patch
    with patch.object(cx, 'MODELS', models):
        assoc = {key: cx.association(plot_games, key, rng) for key in ('accuracy', 'exit_risk', 'kappa')}
    out['figure_associations'] = {key: {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in a.items()
                                        if kk in ('n_games', 'pooled_pearson_r', 'pooled_ci95_paired_seed_bootstrap',
                                                  'within_model_r', 'within_model_permutation_p')}
                                  for key, a in assoc.items()}
    sys.path.insert(0, str(fb.OLD / 'figs'))
    import paper_style as ps
    ps.use()
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic']})
    summary = data['summary']['models']
    fig = plt.figure(figsize=(7.1, 2.3))
    ax_curve = fig.add_axes([.065, .25, .185, .6])
    ax_loss = fig.add_axes([.32, .25, .165, .6])
    axs = [fig.add_axes([x, .25, .125, .6]) for x in (.545, .70, .855)]
    order = sorted(models, key=lambda m: -summary[m]['C_mean'])
    for m in order:
        mi, s = models.index(m), summary[m]
        ax_curve.step(range(0, 9), [v * 100 for v in [1] + s['all4_after_round_share']], where='post', color=cx.COLORS[mi],
                      lw=1.1, marker=cx.MARKERS[mi], markersize=2.6)
    ax_curve.set(xlim=(-.3, 8.5), ylim=(-4, 104), xticks=range(0, 9, 2), yticks=[0, 50, 100],
                 xlabel='라운드', ylabel='네 명이 모두 남은 판 (%)')
    ax_curve.set_title('(a) 라운드별 4인 공존과 $C$', fontsize=7.2, pad=8)
    ax_curve.grid(axis='y', alpha=.6)
    tag_colors = {'dead': ps.C['dead'], 'exit_below': ps.C['exit'], 'exit_above': '#F2B880'}
    tag_labels = {'dead': '꺼짐', 'exit_below': '안전선 아래 이탈', 'exit_above': '안전선 이상 이탈'}
    for yi, m in enumerate(order):
        s, left = summary[m], 0
        for t in cx.TAGS:
            v = s['loss_by_tag_mean'][t]
            ax_loss.barh(yi, v, left=left, color=tag_colors[t], edgecolor='white', linewidth=.5, height=.68)
            if v > .035:
                ax_loss.text(left + v / 2, yi, str(s['first_count_by_tag'][t]), ha='center', va='center', fontsize=5.6,
                             color='white' if t != 'exit_above' else '#222222')
            left += v
        ax_loss.text(left + .012, yi, f'{1 - s["C_mean"]:.2f}', va='center', fontsize=5.8, color='#44515C')
    ax_loss.set(yticks=range(len(order)), yticklabels=[labels_m[m] for m in order],
                xlim=(0, max(.85, max(1 - r['C_mean'] for r in summary.values()) + .12)),
                xticks=[0, .25, .5, .75], xlabel='공존 손실 $1-C$ (10판 평균)')
    ax_loss.invert_yaxis()
    ax_loss.tick_params(axis='y', length=0, labelsize=6)
    ax_loss.set_title('(b) 손실의 귀속', fontsize=7.2, pad=8)
    ax_loss.grid(axis='x', alpha=.6)
    ax_loss.legend(handles=[Patch(color=tag_colors[t], label=tag_labels[t]) for t in cx.TAGS],
                   loc='upper right', fontsize=5.4, handlelength=.9, borderaxespad=.2, labelspacing=.25)
    panels = [('accuracy', '(c) 과제 성과: 정답률', '정답률 (%)', 100),
              ('exit_risk', '(d) 자기 실행 대 과제', '위험 구간 이탈률 (%)', 100),
              ('kappa', r'(e) 자기 실행 대 동료', r'나눔 비중 $\kappa$', 1)]
    for ax, (key, title, xlabel, scale) in zip(axs, panels):
        for mi, m in enumerate(models):
            rows = [g0 for g0 in plot_games if g0['model'] == m and g0[key] is not None]
            ax.scatter([g0[key] * scale for g0 in rows], [g0['C'] for g0 in rows], color=cx.COLORS[mi], marker=cx.MARKERS[mi],
                       alpha=.7, s=15, linewidths=.3, edgecolors='white', zorder=3)
        ax.set(ylim=(0, 1.05), yticks=[0, .5, 1], xlabel=xlabel)
        ax.set_title(title, fontsize=7.2, pad=8)
        ax.tick_params(axis='both', labelsize=6.3)
        ax.grid(alpha=.5)
        if key == 'kappa':
            ax.set_xlim(-.05, 1.05)
            ax.set_xticks([0, .5, 1])
        else:
            ax.set_xlim(-5, 105)
            ax.set_xticks([0, 50, 100])
        fit = assoc[key]
        ax.text(.97, .05 if key != 'exit_risk' else .78, f"$r$={fit['pooled_pearson_r']:+.2f}\n모델 안 $r$={fit['within_model_r']:+.2f}",
                transform=ax.transAxes, ha='right', va='bottom', fontsize=5.8, color='#44515C')
    axs[0].set_ylabel('공존 유지율 $C$', fontsize=6.6)
    legend = [Line2D([], [], color=c, marker=mk, ls='', label=labels_m[n], markersize=5)
              for n, c, mk in zip(models, cx.COLORS, cx.MARKERS)]
    fig.legend(handles=legend, loc='lower center', bbox_to_anchor=(.5, .005), ncol=5, fontsize=6.8,
               borderaxespad=0, handletextpad=.4, handlelength=1.2, columnspacing=1.3)
    for ext in ('pdf', 'png'):
        fig.savefig(dest / f'public_coexistence.{ext}', dpi=240)
    plt.close(fig)

    # ---- Figure: prize conditions x (C, exit under threat, kappa) ----
    archived = json.loads((ROOT / 'ko/figures/scope_revision_20261107/plotted_values.json').read_text())
    points = [p for p in archived if p['metric'] == 'C']
    risk = opp[opp.L_start < THREAT]
    for ai, arm in enumerate(ARMS):
        for m in MODELS:
            r = risk[(risk.arm == arm) & (risk.model == m)]
            kk = k[(k.arm == arm) & (k.model == m)]
            points.append(dict(arm=arm, x=ai, model=m, metric='exit_risk', value=float(r.exited.mean()),
                               ci95=ci(boot(lambda d: d.exited.mean(), [r], rng, n=1000)), n=len(r)))
            points.append(dict(arm=arm, x=ai, model=m, metric='kappa', value=float(kk.kappa.mean()) if len(kk) else None,
                               ci95=ci(boot(lambda d: d.kappa.mean(), [kk], rng, n=1000)) if len(kk) else None, n=len(kk)))
    colors, markers = ['#7155A1', '#CE5184', '#B58B18', '#278D7A', '#98633B'], ['o', '^', 'D', 's', 'v']
    plt.rcParams.update({'font.family': 'Apple SD Gothic Neo', 'font.size': 7, 'axes.unicode_minus': False, 'pdf.fonttype': 3})
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.65))
    fig.subplots_adjust(left=.065, right=.99, bottom=.22, top=.77, wspace=.42)
    for ax, (key, title, ylabel) in zip(axes, [('C', '(a) 공존 유지율', '$C$ (10판 평균)'),
                                                 ('exit_risk', '(b) 자기 실행 대 과제', '위험 구간 이탈률'),
                                                 ('kappa', '(c) 자기 실행 대 동료', r'나눔 비중 $\kappa$')]):
        for mi, model in enumerate(MODELS):
            rows = [p for p in points if p['metric'] == key and p['model'] == model]
            values = {p['x']: p['value'] for p in rows}
            offset = (mi - 2) * .035
            xs = np.arange(4, dtype=float) + offset
            ys = np.array([values[x] if values.get(x) is not None else np.nan for x in range(4)])
            ax.plot(xs, ys, color=colors[mi], marker=markers[mi], ms=3.4, lw=.8, alpha=.9)
            for p in rows:
                if p['value'] is not None and p['ci95']:
                    x, (lo, hi) = p['x'] + offset, p['ci95']
                    ax.plot([x, x], [lo, hi], color=colors[mi], lw=.65, alpha=.55)
                    ax.plot([x - .025, x + .025], [lo, lo], color=colors[mi], lw=.65)
                    ax.plot([x - .025, x + .025], [hi, hi], color=colors[mi], lw=.65)
        ax.set_title(title, loc='left', fontsize=8, pad=8)
        ax.set_ylabel(ylabel, fontsize=7)
        ax.set_xticks(range(4), ARM_LABELS, fontsize=6)
        ax.set_xlim(-.22, 3.22)
        ax.set_ylim(-.025, 1.055)
        ax.grid(axis='y', color='#e6e6e6', lw=.5)
        ax.set_axisbelow(True)
        ax.tick_params(length=2, width=.5)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        for spine in ax.spines.values():
            spine.set_linewidth(.5)
    handles = [Line2D([], [], color=c, marker=mk, ms=4, lw=.8, label=name) for name, c, mk in zip(MODELS, colors, markers)]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.52, 1.01), ncol=5, fontsize=7, frameon=False,
               handlelength=1.5, columnspacing=1.5)
    for ext in ('pdf', 'png'):
        fig.savefig(dest / f'comparison.{ext}', dpi=240)
    plt.close(fig)
    (dest / 'plotted_values.json').write_text(json.dumps(points, ensure_ascii=False, indent=1))


def main():
    out, opp, k, dec, games, game_rows = analyse()
    write_table(out)
    figures(out, opp, k, games, game_rows)
    (ROOT / 'results/construct_weights_20261110.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for key in ('counts', 'exit_risk_by_arm', 'exit_risk_by_model_base', 'exit_adjusted', 'policy', 'kappa_by_model_pooled',
                'kappa_by_arm', 'kappa_vs_minimal_rescue', 'kappa_vs_random_amount', 'kappa_amount_gap_slope', 'ask_decisions',
                'split_half', 'rank_agreement_exit_vs_selfweight', 'prize_2x2', 'coexistence_link', 'loss_by_arm',
                'first_departure_cause_games', 'figure_associations', 'exit_robustness'):
        print(key, json.dumps(out[key], ensure_ascii=False))


if __name__ == '__main__':
    main()
