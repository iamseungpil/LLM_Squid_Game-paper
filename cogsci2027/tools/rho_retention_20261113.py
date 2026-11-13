"""Sharing indicator "rho retention R" in place of kappa (2026-11-13, stage 1: computation only).

Why: the sharing weight kappa of section 2.2 has no value for a refusal, drops 144 of the 1,080 gifts (the giver was
poorer or could not pay its own pending fine), clips at 1 (61 gifts) and blows up when the two margins are close
(paper/cogsci2027/metric.md). The researcher replaced it with the indicator below. This script recomputes every body
number that rested on kappa, next to the stored kappa value. It writes no manuscript file, table or figure.

Indicator (fixed by the researcher; not changed here)
  one event   R = rho_after / rho_before
              rho_before = giver balance / recipient balance just before the transfer
              rho_after  = (giver balance - g) / (recipient balance + g)
              = (1 - g / giver balance) x (recipient balance / (recipient balance + g))
              balances are token balances (src_before, dst_before), not the margin L net of a pending fine
  no gift     R = 1; giving everything gives R = 0; nothing is clipped and no event is dropped
  direction   closer to 1 = more on the agent's own side, the same direction as the exit rate
  model value mean of the event values, refusals included

Events
  gifts      every row of gifts.pkl (1,080 over the four conditions): gifts from the poorer side, the 24 gifts of a
             giver that could not pay its own pending fine (L_src_before < 0) and repayments are all in
  refusals   ask_rows.pkl, first & delivered & outcome != 'already_gave' (471 decisions), outcome == 'refuse' (104)
             an agent that was never asked and did not give is not an event
  repayment  by the ledger, not by keywords: a gift to a peer from whom the giver received a gift earlier in the game

Sections of the output (results/rho_retention_20261113.json)
  gate              the reference values handed over with the task; the script stops if they are not reproduced
  a_models          R per model (four conditions pooled, base condition), 95% intervals, pairwise differences
  b_prize           cell means (five-model mean per condition) and the contrasts of prize_dissociation_20261111:
                    size, rule, rule minus size, the size effect inside the fixed pair and inside the split pair;
                    the same contrasts on pooled events; size effect per model; lowest-R model per condition
  c_sensitivity     model values and contrasts side by side: all events, without the 24 doomed gifts, without
                    repayments, without refusals
  d_direction_bands richer-to-poorer vs poorer-to-richer gifts; mean R by the giver's and the recipient's margin L
  e_rule_agents     the simulated rule agents of rule_baselines_20261111 / rule_minimal_rescue_20261112 read with R
  f_minimal_rescue  gifts to a recipient below L = 1: observed R against the R of lifting the recipient to L = 1
  g_links           Spearman correlation with the exit rate per condition; relation with C inside a model
  open_models       the four open-weight models (base condition), same definition
  components        the two factors of R, (1 - g / giver balance) and (recipient / (recipient + g)), per model
  kappa_before      the stored kappa numbers the body uses now, for the side-by-side table

Intervals: seed-cluster bootstrap of construct_weights_20261110 (the ten seeds resampled jointly across models and
conditions, 2,000 draws, percentile 95%).

Data scope (paper/AGENTS.md): 5.2 arena v33, seeds 4101-4110. Closed five models x four prize conditions (200 games)
through validation_20261108/results/tables/{gifts,ask_rows,games,agent_rounds}.pkl; open four models, base condition
(40 games), through result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json with the loader of
open_models_20261111. Rule agents: no model calls, calibration on the 200 closed games. No new runs.
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/rho_retention_20261113.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
import construct_weights_20261110 as cw  # noqa: E402
import open_models_20261111 as om  # noqa: E402
import rule_baselines_20261111 as rb  # noqa: E402

BOOT = 2000
RNG_SEED = 20261113
GAME = ['arm', 'model', 'seed']
ARMS = ['main', 'split600k', 'flat5m', 'flat150k']          # split-large, split-small, fixed-large, fixed-small
CONTRASTS = {                                               # weights on the four cells, in ARMS order
    'size': (-.5, .5, -.5, .5),                             # small minus large, averaged over the two rules
    'rule': (-.5, -.5, .5, .5),                             # fixed minus split, averaged over the two sizes
    'rule_minus_size': (0, -1, 1, 0),
    'size_in_fixed': (0, 0, -1, 1),
    'size_in_split': (-1, 1, 0, 0),
}
REFERENCE = {                                               # handed over with the task (four conditions pooled)
    'n_gifts': 1080, 'n_refusals': 104, 'range': (0.000, 0.984),
    'models': {'Astra': (135, 3, 0.5503, 0.5601), 'Sol': (164, 32, 0.6237, 0.6851), 'Opus': (360, 8, 0.6658, 0.6731),
               'Luna': (129, 26, 0.6490, 0.7078), 'Fable': (292, 35, 0.6862, 0.7198)},
    'arms': {'flat150k': 0.6738, 'flat5m': 0.6821, 'main': 0.6766, 'split600k': 0.6842},
}
L_BANDS = [(-np.inf, 0, '<0'), (0, 1, '0-1'), (1, 2, '1-2'), (2, 4, '2-4'), (4, np.inf, '>=4')]


def retention(src, dst, g):
    """R = rho_after / rho_before for one transfer of g from a balance src to a balance dst."""
    return (1 - g / src) * (dst / (dst + g))


def gift_events(gifts):
    """One row per gift with R, its two factors, the ledger repayment flag and the flags the sensitivity runs use."""
    e = gifts.copy()
    assert (e.src_before > 0).all() and (e.dst_before > 0).all() and (e.amount > 0).all()
    e['R'] = retention(e.src_before, e.dst_before, e.amount)
    e['keep_own'] = 1 - e.amount / e.src_before               # share of the giver's balance that stayed
    e['dilute'] = e.dst_before / (e.dst_before + e.amount)    # share of the recipient's new balance that was its own
    e['kind'] = 'gift'
    e['doomed'] = e.L_src_before < 0
    e['richer_gives'] = e.src_before > e.dst_before
    repay = []
    for _, d in e.groupby(GAME, sort=False):                  # rows are chronological inside a game (checked in main)
        seen = set()
        for r in d.itertuples():
            repay.append((r.Index, (r.dst, r.src) in seen))
            seen.add((r.src, r.dst))
    e['repay'] = pd.Series(dict(repay))
    e['L_giver'], e['L_taker'] = e.L_src_before, e.L_dst_before
    return e


def refusal_events(ask):
    dec = ask[ask['first'] & ask.delivered & (ask.outcome != 'already_gave')]
    r = dec[dec.outcome == 'refuse'].copy()
    r['R'], r['kind'], r['doomed'], r['repay'] = 1.0, 'refusal', False, False
    r['keep_own'], r['dilute'] = 1.0, 1.0
    r['richer_gives'] = r.b_s > r.b_t
    r['L_giver'], r['L_taker'] = r.L_s, r.L_t
    return r, len(dec)


COLS = GAME + ['round', 'R', 'kind', 'doomed', 'repay', 'richer_gives', 'L_giver', 'L_taker', 'keep_own', 'dilute']


def q95(values):
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    return [round(float(np.quantile(v, q)), 4) for q in (.025, .975)] if len(v) else None


def with_ci(fn, frame, draws):
    """fn(frame) -> dict of floats; the same dict on every bootstrap draw of the ten seeds."""
    point = fn(frame)
    by_seed = {s: frame[frame.seed == s] for s in cw.SEEDS}
    boots = [fn(pd.concat([by_seed[s] for s in d])) for d in draws]
    return {k: dict(value=round(float(v), 4), ci95=q95([b.get(k, np.nan) for b in boots])) for k, v in point.items()}


def model_stats(ev):
    """Model means (pooled and base condition) and the pairwise differences on the pooled events."""
    pooled = ev.groupby('model').R.mean()
    base = ev[ev.arm == 'main'].groupby('model').R.mean()
    out = {f'pooled:{m}': pooled.get(m, np.nan) for m in cw.MODELS}
    out.update({f'base:{m}': base.get(m, np.nan) for m in cw.MODELS})
    for i, a in enumerate(cw.MODELS):
        for b in cw.MODELS[i + 1:]:
            out[f'diff:{a}-{b}'] = pooled.get(a, np.nan) - pooled.get(b, np.nan)
    others = ev[ev.model != 'Astra'].groupby('model').R.mean()
    out['Astra_minus_mean_of_other_four'] = pooled.get('Astra', np.nan) - others.mean()
    out['Astra_minus_lowest_other'] = pooled.get('Astra', np.nan) - others.min()
    return out


def prize_stats(ev):
    """Cell = mean over the five models of the model's R in that condition (as prize_2x2 does for kappa)."""
    c = ev.groupby(['arm', 'model']).R.mean().unstack().reindex(index=ARMS, columns=cw.MODELS)
    cells = c.mean(axis=1).values
    pooled = ev.groupby('arm').R.mean().reindex(ARMS).values
    out = {f'cell:{a}': cells[i] for i, a in enumerate(ARMS)}
    out.update({f'pooled_cell:{a}': pooled[i] for i, a in enumerate(ARMS)})
    for name, w in CONTRASTS.items():
        out[name] = float(cells @ np.array(w))
        out[f'pooled_events:{name}'] = float(pooled @ np.array(w))
    for m in cw.MODELS:
        v = c[m].values
        out[f'size:{m}'] = float(v @ np.array(CONTRASTS['size']))
        out[f'rule:{m}'] = float(v @ np.array(CONTRASTS['rule']))
    return out


def band_table(ev, column):
    out = {}
    for lo, hi, lab in L_BANDS:
        d = ev[(ev[column] >= lo) & (ev[column] < hi)]
        out[lab] = dict(n=len(d), gifts=int((d.kind == 'gift').sum()), refusals=int((d.kind == 'refusal').sum()),
                        R=round(float(d.R.mean()), 4) if len(d) else None,
                        R_gifts_only=round(float(d[d.kind == 'gift'].R.mean()), 4) if (d.kind == 'gift').any() else None)
    return out


# ------------------------------------------------------------------------------------------------ rule agents
ACC = {'R': 0.0, 'n': 0, 'idle': 0, 'fines': 0.0}   # per run: sum of R over gifts, gifts, chances with no gift, tokens handed over in fines
MINIMAL = 'minimal'


def share(bal, mask, fee, pend, kappa, rng=None, acc=None):
    """rule_baselines_20261111.share with the minimal-rescue mode of rule_minimal_rescue_20261112, and R recorded
    for every transfer from the token balances just before it. The transfers themselves are unchanged."""
    rows = np.arange(len(bal))
    done = np.zeros_like(mask)
    for _ in range(4):
        L = (bal - pend[:, None]) / fee[:, None]
        need = mask & (L < 1) & ~done
        if not need.any():
            return
        j = np.where(need, L, np.inf).argmin(1)
        has = need[rows, j]
        done[rows, j] = True
        other = mask.copy()
        other[rows, j] = False
        i = np.where(other, L, -np.inf).argmax(1)
        gap = L[rows, i] - L[rows, j]
        if isinstance(kappa, str) and kappa == MINIMAL:
            amount = np.minimum(1 - L[rows, j], gap / 2) * fee
        else:
            k = rng.random(len(bal)) if kappa is None else (kappa[rows, i] if np.ndim(kappa) == 2 else kappa)
            amount = k * gap / 2 * fee
        chance = has & other.any(1) & (gap > 0)
        g = np.where(chance, amount, 0.0)
        g = np.minimum(g, np.maximum(bal[rows, i], 0))
        sent = g > 0
        if acc is not None:
            acc[0] += float(np.clip((g[sent] / fee[sent]) / (gap[sent] / 2), 0, 1).sum())
            acc[1] += int(sent.sum())
        ACC['R'] += float(retention(bal[rows, i][sent], bal[rows, j][sent], g[sent]).sum())
        ACC['n'] += int(sent.sum())
        ACC['fines'] += float((g[sent] / fee[sent]).sum())
        ACC['idle'] += int((chance & ~sent).sum())
        bal[rows, i] -= g
        bal[rows, j] += g


def rule_agents(rng):
    """The named rule agents, a new random stream; C must stay within 0.02 of the stored runs and the kappa read
    from the simulated record must equal the stored one (the transfers were not changed)."""
    rb.share = share
    rb.THREAT = np.inf                                    # the exit rate counts every opportunity (body definition)
    f = rb.d.load()
    cal, solver1, mim, _ = rb.w1.calibrate(f)
    refill = rb.w1.Refill(rb.w1.seat_agents(f['seats']))
    pooled = cal['pooled']
    stored = json.loads((ROOT / 'results/rule_baselines_20261111.json').read_text())
    stored_exit = json.loads((ROOT / 'results/exit_all_opportunities_20261112.json').read_text())['rule_agents']
    stored_min = json.loads((ROOT / 'results/rule_minimal_rescue_20261112.json').read_text())['minimal_rescue']
    types = [('keeper', '주지 않음', 1.0, 0.0), ('reference', '맞출 양의 4분의 1', 1.0, .25), ('minimal_rescue', 'L=1까지만 올림', 1.0, MINIMAL),
             ('cooperator', '여유를 똑같이 맞춤', 1.0, 1.0), ('stayer', '떠나지 않음 (4분의 1)', 0.0, .25), ('leaver', 'L<2에서 떠남 (4분의 1)', 2.0, .25)]
    out = {}
    for key, label, theta, kappa in types:
        ACC.update(R=0.0, n=0, idle=0, fines=0.0)
        r = rb.run(pooled, theta, kappa, rng, solver1, refill)
        want = stored_min if key == 'minimal_rescue' else stored['types'][key]
        want_exit = stored_min['exit_rate'] if key == 'minimal_rescue' else stored_exit['types'][key]['exit_rate']
        assert abs(r['C'] - want['C']) < .02 and abs(r['exit_under_threat'] - want_exit) < .01, (key, r, want)
        assert abs(r['kappa_measured'] - want['kappa_measured']) < .01, (key, r['kappa_measured'], want['kappa_measured'])
        n, idle = ACC['n'], ACC['idle']
        out[key] = dict(label=label, C=r['C'], exit_rate=r['exit_under_threat'], gifts_per_game=r['gifts_per_game'],
                        kappa_measured=r['kappa_measured'] if n else None,
                        R_gifts_only=round(ACC['R'] / n, 4) if n else None,
                        R=round((ACC['R'] + idle) / (n + idle), 4) if n + idle else None,
                        fines_per_gift=round(ACC['fines'] / n, 3) if n else None,            # indicator-free amount
                        fines_handed_over_per_game=round(ACC['fines'] / (len(rb.d.SEEDS) * rb.REPS), 3),
                        idle_chances_per_game=round(idle / (len(rb.d.SEEDS) * rb.REPS), 2),
                        note='idle chance = a peer below L = 1, a richer participant present, nothing handed over (R = 1)')
    ACC.update(R=0.0, n=0, idle=0, fines=0.0)
    r = rb.run(pooled, 0.0, None, rng, solver1, refill, exit_p=float(mim['marg'][rb.ARM]))
    out['random'] = dict(label='무작위', C=r['C'], exit_rate=r['exit_under_threat'], kappa_measured=r['kappa_measured'],
                         R_gifts_only=round(ACC['R'] / ACC['n'], 4), R=round((ACC['R'] + ACC['idle']) / (ACC['n'] + ACC['idle']), 4))
    return out


# ------------------------------------------------------------------------------------------------ open models
def open_models():
    """Base condition, four open-weight models: the same events through the loader of open_models_20261111."""
    om.MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'   # runs moved into the repo on 2026-11-11
    cwd = os.getcwd()
    os.chdir(REPO)                                        # the manifest lists run directories relative to the repo
    try:
        fo = om.open_frames()
    finally:
        os.chdir(cwd)
    stored = json.loads((ROOT / 'results/open_models_20261111.json').read_text())['models']
    gifts = gift_events(fo['gifts'])
    refusals, _ = refusal_events(fo['ask'])
    ev = pd.concat([gifts[COLS], refusals[COLS]], ignore_index=True)
    rng = np.random.default_rng(RNG_SEED)
    draws = [list(rng.choice(cw.SEEDS, len(cw.SEEDS))) for _ in range(BOOT)]
    out = {}
    for m in om.OPEN:
        d, a = ev[ev.model == m], fo['ask'][fo['ask'].model == m]
        dec = a[a['first'] & a.delivered & (a.outcome != 'already_gave')]
        gave = [int(dec.outcome.isin(['give_now', 'give_later']).sum()), len(dec)]
        assert gave == stored[m]['gave_after_ask'], (m, gave, stored[m]['gave_after_ask'])   # same events as the body table
        by_seed = {s: d[d.seed == s] for s in cw.SEEDS}
        boots = [pd.concat([by_seed[s] for s in dr]).R.mean() for dr in draws]
        out[m] = dict(name=om.OPEN[m], gifts=int((d.kind == 'gift').sum()), refusals=int((d.kind == 'refusal').sum()),
                      R=round(float(d.R.mean()), 4), ci95=q95(boots),
                      R_gifts_only=round(float(d[d.kind == 'gift'].R.mean()), 4),
                      doomed_gifts=int(d.doomed.sum()), kappa_before=stored[m]['kappa'], kappa_n_before=stored[m]['kappa_n'])
    return out


# ------------------------------------------------------------------------------------------------ main
def main():
    rng = np.random.default_rng(RNG_SEED)
    draws = [list(rng.choice(cw.SEEDS, len(cw.SEEDS))) for _ in range(BOOT)]
    gifts_raw = pd.read_pickle(cw.TABLES / 'gifts.pkl')
    ask = pd.read_pickle(cw.TABLES / 'ask_rows.pkl')
    games = pd.read_pickle(cw.TABLES / 'games.pkl')
    opp, k, _, _, _, counts = cw.load()                  # exit opportunities and the kappa events, for the side-by-side
    order = gifts_raw.assign(p=gifts_raw.phase.map({'prep': 0, 'rescue': 1})).sort_values(GAME + ['round', 'p', 'tick'], kind='stable')
    assert (order.index == gifts_raw.sort_values(GAME, kind='stable').index).all(), 'gifts.pkl is not chronological inside a game'
    gifts = gift_events(gifts_raw)
    refusals, n_dec = refusal_events(ask)
    ev = pd.concat([gifts[COLS], refusals[COLS]], ignore_index=True)

    # ---- gate: the reference values of the task ---------------------------------------------------------------
    gate = dict(n_gifts=len(gifts), n_refusals=len(refusals), n_decisions=n_dec,
                range=[round(float(gifts.R.min()), 3), round(float(gifts.R.max()), 3)], models={}, arms={})
    assert (gate['n_gifts'], gate['n_refusals'], n_dec) == (REFERENCE['n_gifts'], REFERENCE['n_refusals'], 471), gate
    assert tuple(gate['range']) == REFERENCE['range'], gate['range']
    for m, (ng, nr, r_gift, r_all) in REFERENCE['models'].items():
        d = ev[ev.model == m]
        got = (int((d.kind == 'gift').sum()), int((d.kind == 'refusal').sum()),
               round(float(d[d.kind == 'gift'].R.mean()), 4), round(float(d.R.mean()), 4))
        assert got == (ng, nr, r_gift, r_all), (m, got)
        gate['models'][m] = got
    for a, want in REFERENCE['arms'].items():
        got = round(float(ev[ev.arm == a].R.mean()), 4)
        assert got == want, (a, got, want)
        gate['arms'][a] = got
    out = dict(method=__doc__.split('Sections of the output')[0].strip(), gate=dict(reproduced=True, **gate))

    # ---- a. models -----------------------------------------------------------------------------------------------
    a = with_ci(model_stats, ev, draws)
    out['a_models'] = dict(
        pooled={m: dict(n_gifts=int(((ev.model == m) & (ev.kind == 'gift')).sum()), n_refusals=int(((ev.model == m) & (ev.kind == 'refusal')).sum()),
                        **a[f'pooled:{m}']) for m in cw.MODELS},
        base={m: dict(n_gifts=int(((ev.model == m) & (ev.arm == 'main') & (ev.kind == 'gift')).sum()),
                      n_refusals=int(((ev.model == m) & (ev.arm == 'main') & (ev.kind == 'refusal')).sum()), **a[f'base:{m}']) for m in cw.MODELS},
        differences_pooled={key[5:]: v for key, v in a.items() if key.startswith('diff:')},
        Astra_minus_mean_of_other_four=a['Astra_minus_mean_of_other_four'],
        Astra_minus_lowest_other=a['Astra_minus_lowest_other'])

    # ---- b. prize 2x2 ---------------------------------------------------------------------------------------------
    b = with_ci(prize_stats, ev, draws)
    cell = ev.groupby(['arm', 'model']).R.mean().unstack().reindex(index=ARMS, columns=cw.MODELS)
    out['b_prize'] = dict(
        cells={arm: b[f'cell:{arm}'] for arm in ARMS}, cells_pooled_events={arm: b[f'pooled_cell:{arm}'] for arm in ARMS},
        contrasts={name: b[name] for name in CONTRASTS}, contrasts_pooled_events={name: b[f'pooled_events:{name}'] for name in CONTRASTS},
        size_by_model={m: b[f'size:{m}'] for m in cw.MODELS}, rule_by_model={m: b[f'rule:{m}'] for m in cw.MODELS},
        by_arm_model={arm: {m: round(float(cell.loc[arm, m]), 4) for m in cw.MODELS} for arm in ARMS},
        lowest_R_model_by_arm={arm: str(cell.loc[arm].idxmin()) for arm in ARMS},
        note='cells = mean over the five models of the model value; size = small minus large; rule = fixed minus split')

    # ---- c. sensitivity --------------------------------------------------------------------------------------------
    variants = {'all_events': ev, 'without_doomed_24': ev[~ev.doomed], 'without_repayments': ev[~ev.repay],
                'without_refusals': ev[ev.kind == 'gift']}
    out['c_sensitivity'] = {}
    for name, sub in variants.items():
        ms, ps = with_ci(model_stats, sub, draws), with_ci(prize_stats, sub, draws)
        out['c_sensitivity'][name] = dict(
            n=len(sub), by_model_n={m: int((sub.model == m).sum()) for m in cw.MODELS},
            pooled={m: ms[f'pooled:{m}'] for m in cw.MODELS}, base={m: ms[f'base:{m}'] for m in cw.MODELS},
            Astra_minus_lowest_other=ms['Astra_minus_lowest_other'],
            contrasts={c: ps[c] for c in CONTRASTS})
    out['c_sensitivity']['counts'] = dict(
        doomed=int(gifts.doomed.sum()), doomed_gave_everything=int((gifts[gifts.doomed].amount == gifts[gifts.doomed].src_before).sum()),
        repayments=int(gifts.repay.sum()), repayments_by_model={m: int(gifts[gifts.model == m].repay.sum()) for m in cw.MODELS},
        refusals_by_model={m: int((refusals.model == m).sum()) for m in cw.MODELS})

    # ---- d. direction and margin bands ------------------------------------------------------------------------------
    direction = {}
    for name, sub in (('richer_gives', gifts[gifts.richer_gives]), ('poorer_gives', gifts[~gifts.richer_gives])):
        direction[name] = dict(n=len(sub), R=round(float(sub.R.mean()), 4), ci95=q95([cw.by_seed(sub, d).R.mean() for d in draws]),
                               keep_own=round(float(sub.keep_own.mean()), 4), dilute=round(float(sub.dilute.mean()), 4),
                               by_model={m: [int((sub.model == m).sum()), round(float(sub[sub.model == m].R.mean()), 4) if (sub.model == m).any() else None]
                                         for m in cw.MODELS})
    gap = gifts.L_src_before - gifts.L_dst_before
    out['d_direction_bands'] = dict(
        direction=direction,
        kappa_exclusions=dict(doomed=int(gifts.doomed.sum()), not_poorer_by_margin=int((~gifts.doomed & (gap <= 0)).sum()),
                              poorer_by_balance=int((~gifts.richer_gives).sum()),
                              note='kappa dropped 24 + 120 gifts by the margin L; the direction above is by token balance'),
        by_giver_margin=band_table(ev, 'L_giver'), by_recipient_margin=band_table(ev, 'L_taker'),
        by_recipient_margin_by_model={m: band_table(ev[ev.model == m], 'L_taker') for m in cw.MODELS})

    # ---- f. minimal rescue ---------------------------------------------------------------------------------------------
    low = gifts[gifts.L_dst_before < 1].copy()
    low['need'] = (1 - low.L_dst_before) * low.fee                               # tokens that lift the recipient to L = 1
    low['g_min'] = np.minimum(low.need, low.src_before)                          # a giver cannot hand over more than it holds
    low['R_min'] = retention(low.src_before, low.dst_before, low.g_min)
    low['diff'] = low.R - low.R_min

    def minimal(d):
        res = {'all': d['diff'].mean()}
        res.update({m: d[d.model == m]['diff'].mean() for m in cw.MODELS})
        return res
    mci = with_ci(minimal, low, draws)
    out['f_minimal_rescue'] = dict(
        n=len(low), capped_at_giver_balance=int((low.need > low.src_before).sum()), doomed_in_set=int(low.doomed.sum()),
        by_model={m: dict(n=int((low.model == m).sum()), observed=round(float(low[low.model == m].R.mean()), 4),
                          minimal=round(float(low[low.model == m].R_min.mean()), 4), diff=mci[m],
                          share_at_least_minimal=round(float((low[low.model == m].amount >= low[low.model == m].need - 1e-9).mean()), 4))
                  for m in cw.MODELS},
        without_doomed={m: with_ci(minimal, low[~low.doomed], draws)[m] for m in cw.MODELS},
        note='diff = observed R minus minimal-rescue R; below 0 = handed over more than the lift to L = 1')

    # ---- g. links ---------------------------------------------------------------------------------------------------------
    from scipy.stats import spearmanr
    rate = opp.groupby(['arm', 'model']).exited.mean().unstack()
    cell_gift = gifts.groupby(['arm', 'model']).R.mean().unstack()
    g = games[GAME + ['C']].join(opp.groupby(GAME).exited.mean().rename('exit'), on=GAME)
    g = g.join(ev.groupby(GAME).R.mean().rename('R'), on=GAME).join(gifts.groupby(GAME).R.mean().rename('R_gifts'), on=GAME)
    g['cell'] = g.arm + '|' + g.model
    base = g[g.arm == 'main']

    def link(d):
        res = {'cell_fe_beta_R': cw.std_fit(d, ['R'], 'C', 'cell')['beta']['R'],
               'cell_fe_beta_R_with_exit': cw.std_fit(d, ['exit', 'R'], 'C', 'cell')['beta']['R'],
               'base_within_model_r': cw.within(d[d.arm == 'main'].dropna(subset=['R']), 'R', 'C', 'model')}
        return res
    out['g_links'] = dict(
        rank_exit_vs_R={arm: round(float(spearmanr(rate.loc[arm, cw.MODELS], cell.loc[arm, cw.MODELS])[0]), 2) for arm in ARMS},
        rank_exit_vs_R_gifts_only={arm: round(float(spearmanr(rate.loc[arm, cw.MODELS], cell_gift.loc[arm, cw.MODELS])[0]), 2) for arm in ARMS},
        rank_exit_vs_R_pooled=round(float(spearmanr(opp.groupby('model').exited.mean()[cw.MODELS], ev.groupby('model').R.mean()[cw.MODELS])[0]), 2),
        games_with_events=int(g.R.notna().sum()), base_games_with_events=int(base.R.notna().sum()),
        four_conditions_cell_fe=dict(R=cw.std_fit(g, ['R'], 'C', 'cell'), R_and_exit=cw.std_fit(g, ['exit', 'R'], 'C', 'cell'),
                                     R_gifts_only=cw.std_fit(g, ['R_gifts'], 'C', 'cell')),
        base_within_model_r=round(cw.within(base.dropna(subset=['R']), 'R', 'C', 'model'), 3),
        intervals=with_ci(link, g, draws),
        note='R closer to 1 = more on the own side, so a relation of the kappa sign (+) shows here as (-)')

    # ---- components: which factor of R separates the models --------------------------------------------------------------
    out['components'] = {m: dict(keep_own=round(float(gifts[gifts.model == m].keep_own.mean()), 4),
                                 dilute=round(float(gifts[gifts.model == m].dilute.mean()), 4),
                                 giver_balance_median=float(gifts[gifts.model == m].src_before.median()),
                                 recipient_balance_median=float(gifts[gifts.model == m].dst_before.median()),
                                 amount_median=float(gifts[gifts.model == m].amount.median()),
                                 amount_in_fines_mean=round(float((gifts[gifts.model == m].amount / gifts[gifts.model == m].fee).mean()), 4))
                         for m in cw.MODELS}
    out['components']['note'] = 'R = keep_own x dilute per gift; the means above are over gifts only'
    lr = np.log(gifts[gifts.R > 0].R)
    out['components']['variance_share_of_log_R'] = dict(
        n=int((gifts.R > 0).sum()),
        keep_own=round(float(np.cov(np.log(gifts[gifts.R > 0].keep_own), lr)[0, 1] / lr.var()), 3),
        dilute=round(float(np.cov(np.log(gifts[gifts.R > 0].dilute), lr)[0, 1] / lr.var()), 3))

    # ---- e. rule agents, open models --------------------------------------------------------------------------------------
    out['e_rule_agents'] = rule_agents(np.random.default_rng(RNG_SEED))
    out['open_models'] = open_models()

    # ---- stored kappa numbers of the body ----------------------------------------------------------------------------------
    w = json.loads((ROOT / 'results/construct_weights_20261110.json').read_text())
    dis = json.loads((ROOT / 'results/prize_dissociation_20261111.json').read_text())['kappa']
    allopp = json.loads((ROOT / 'results/exit_all_opportunities_20261112.json').read_text())
    kcell = k.groupby(['arm', 'model']).kappa.mean().unstack().reindex(index=ARMS, columns=cw.MODELS)
    out['kappa_before'] = dict(
        counts=counts, by_model_pooled=w['kappa_by_model_pooled'], vs_minimal_rescue=w['kappa_vs_minimal_rescue'],
        prize={c: dis[c] for c in ('size', 'rule', 'rule_minus_size', 'size_in_fixed', 'size_in_equal')}, cells=dis['cells'],
        rank_exit_vs_one_minus_kappa=allopp['rank_agreement'], game_link=allopp['game_link']['four_conditions_cell_fe'],
        highest_kappa_model_by_arm={arm: str(kcell.loc[arm].idxmax()) for arm in ARMS})

    (ROOT / 'results/rho_retention_20261113.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for key in ('gate', 'a_models', 'b_prize', 'c_sensitivity', 'd_direction_bands', 'e_rule_agents', 'f_minimal_rescue', 'g_links',
                'open_models', 'components'):
        print(key, json.dumps(out[key], ensure_ascii=False))


if __name__ == '__main__':
    main()
