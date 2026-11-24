"""W2c (round 4, Astra B-2 / Q2): observed rho against the minimal-structure policy on the SAME event set.

Round 1 (w2_support.q2) computed the minimal-structure rho ("lift the recipient exactly to L = 1") only on GIVEs whose
recipient was below L = 1, weighted by the lift amounts, while observed rho used every GIVE weighted by the observed
amounts. This script pairs the two on identical events and identical weights.

Event sets (one row of the gifts table = one executed GIVE k):
  all   every GIVE;
  low   recipient below L = 1 just before the GIVE (L_dst_before < 1);
  high  recipient at or above L = 1 just before the GIVE (L_dst_before >= 1).
Minimal structure at event k: transfer m_k = min(ceil((1 - L_dst_before) F), giver balance) if L_dst_before < 1, else
  m_k = 0 (zero transfer: the recipient is already at the line; a 1-token transfer moves L by 1/F < 2e-4, so it is the
  same number). Post-transfer margins: giver L_src_before - m_k / F, recipient L_dst_before + m_k / F.
Weights:
  native   observed rho weighted by g_k, minimal rho weighted by m_k (defined only where sum m_k > 0, i.e. 'low';
           on 'all' it reduces to the round-1 number because m_k = 0 on 'high');
  obs_w    both weighted by the observed amounts g_k (common weights);
  equal    both weighted 1 per event (common weights).
Paired ratio obs / min and difference obs - min per arm x model with a seed-cluster bootstrap (per-seed sums of the
numerators and denominators of both, the same resampled seeds for both; 4,000 draws). A cell is 'below' when the 95%
interval of the ratio lies below 1 (observed rho lower than the minimal structure: the givers moved more margin to the
recipient than the minimal structure), 'above' when it lies above 1, otherwise 'inside'.
Also: per-event share with g_k >= m_k on 'low' (gave at least the minimal-structure amount), and the random-recipient
and random-amount policies of round 1 recomputed on the same three event sets with common weights g_k (random amount
also with its native random weights), 2,000 Monte Carlo draws; observed rho compared with their 95% MC range.

Data: tidy tables of validation_data.py. No model calls. RNG seed 20261108.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w2c_rho_paired.py
Writes: ../results/w2c_rho_paired.json, ../figures/w2c_rho_paired.{pdf,png}
"""
import json
from pathlib import Path

import numpy as np

import validation_data as d
import w2_support as w

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'results/w2c_rho_paired.json'
FIG = HERE.parent / 'figures'
B, MC = 4_000, 2_000
RNG = np.random.default_rng(20261108)
SEEDS, MODELS, ARMS = d.SEEDS, d.MODELS, w.ARMS
SETS = ['all', 'low', 'high']


def q(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))] if len(x) else [None, None]


def rnd(x, k=4):
    if isinstance(x, dict):
        return {str(kk): rnd(v, k) for kk, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v, k) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else round(float(x), k)
    if isinstance(x, np.integer):
        return int(x)
    return x


def ratio(w_, ls, lt):
    den = np.sum(w_ * lt)
    return float(np.sum(w_ * ls) / den) if len(w_) and den != 0 else np.nan


def verdict(ci95):
    lo, hi = ci95
    if lo is None:
        return None
    return 'below' if hi < 1 else 'above' if lo > 1 else 'inside'


F = d.load()
gi = F['gifts'].copy()
tb, pend = w.tick_balances(F['messages'], gi)
gi['x'] = gi.amount / gi.fee
gi['m'] = np.where(gi.L_dst_before < 1,
                   np.minimum(np.ceil(np.maximum(0, (1 - gi.L_dst_before) * gi.fee)), gi.src_before), 0.0)
gi['Ls_min'] = gi.L_src_before - gi.m / gi.fee
gi['Lt_min'] = gi.L_dst_before + gi.m / gi.fee
gi['one'] = 1.0
peers = []
for r in gi.itertuples():
    bal = tb[(r.arm, r.model, r.seed, r.round, r.phase, r.tick)]
    cand = [(b - (pend.get((r.arm, r.model, r.seed, r.round, a), 0) if r.phase == 'rescue' else 0)) / r.fee
            for a, b in bal.items() if a != r.src and b > 0]
    peers.append(cand)
gi['peerL'] = peers
MASK = {'all': lambda g: np.ones(len(g), bool), 'low': lambda g: (g.L_dst_before < 1).to_numpy(),
        'high': lambda g: (g.L_dst_before >= 1).to_numpy()}
# (weight column for observed, weight column for minimal)
WEIGHTS = {'native': ('amount', 'm'), 'obs_w': ('amount', 'amount'), 'equal': ('one', 'one')}

res = {'meta': dict(B=B, MC=MC, rng_seed=20261108, sets=SETS, weights=list(WEIGHTS),
                    minimal_for_high='zero transfer (m_k = 0)')}
cells = {}
draws = RNG.integers(0, len(SEEDS), (B, len(SEEDS)))
for arm in ARMS:
    ga = gi[gi.arm == arm].reset_index(drop=True)
    xs = ga.x.to_numpy()
    for mdl in MODELS:
        g0 = ga[ga.model == mdl].reset_index(drop=True)
        cell = {}
        for s in SETS:
            g = g0[MASK[s](g0)].reset_index(drop=True)
            out = dict(n=int(len(g)), games=int(g.seed.nunique()))
            if g.empty:
                cell[s] = out
                continue
            for wn, (wo, wm) in WEIGHTS.items():
                parts = dict(obs=(g[wo] * g.L_src_after, g[wo] * g.L_dst_after),
                             min=(g[wm] * g.Ls_min, g[wm] * g.Lt_min))
                pt = {k: (float(n.sum() / dd.sum()) if dd.sum() != 0 else np.nan) for k, (n, dd) in parts.items()}
                bs = {}
                for k, (n, dd) in parts.items():
                    ns = np.array([n[g.seed == sd].sum() for sd in SEEDS])
                    ds = np.array([dd[g.seed == sd].sum() for sd in SEEDS])
                    with np.errstate(divide='ignore', invalid='ignore'):
                        bs[k] = ns[draws].sum(1) / ds[draws].sum(1)
                if not np.isfinite(pt['min']):
                    out[wn] = dict(obs=pt['obs'], obs_ci95=q(bs['obs']), min=None)
                    continue
                rat = bs['obs'] / bs['min']
                ci_r = q(rat)
                out[wn] = dict(obs=pt['obs'], obs_ci95=q(bs['obs']), min=pt['min'], min_ci95=q(bs['min']),
                               ratio=pt['obs'] / pt['min'], ratio_ci95=ci_r,
                               diff=pt['obs'] - pt['min'], diff_ci95=q(bs['obs'] - bs['min']), verdict=verdict(ci_r))
            if s == 'low':
                ge = (g.amount >= g.m).to_numpy(float)
                ns = np.array([ge[g.seed == sd].sum() for sd in SEEDS])
                cs = np.array([(g.seed == sd).sum() for sd in SEEDS])
                with np.errstate(divide='ignore', invalid='ignore'):
                    out['share_g_ge_m'] = float(ge.mean())
                    out['share_g_ge_m_ci95'] = q(ns[draws].sum(1) / cs[draws].sum(1))
                out['median_g_over_m'] = float(np.median(g.amount / g.m.where(g.m > 0)))
            # random policies on the same events (round-1 definitions), common weights g_k
            npeer = np.array([len(p) for p in g.peerL])
            pad = np.full((len(g), max(npeer.max(), 1)), np.nan)
            for i, p in enumerate(g.peerL):
                pad[i, :len(p)] = p
            amt_g, Ls_a, Lt_a, x = g.amount.to_numpy(), g.L_src_after.to_numpy(), g.L_dst_after.to_numpy(), g.x.to_numpy()
            Lsb, Ltb, fee, cap = g.L_src_before.to_numpy(), g.L_dst_before.to_numpy(), g.fee.to_numpy(), g.src_before.to_numpy()
            rr, ra_g, ra_n, rr_n = [], [], [], []
            for _ in range(MC):
                pick = np.floor(RNG.random(len(g)) * np.maximum(npeer, 1)).astype(int)
                tl = np.where(npeer > 0, pad[np.arange(len(g)), pick], np.nan)
                ok = ~np.isnan(tl)
                rr.append(ratio(amt_g[ok], Ls_a[ok], tl[ok] + x[ok]))
                amt = np.minimum(RNG.choice(xs, len(g)) * fee, cap)
                ra_n.append(ratio(amt, Lsb - amt / fee, Ltb + amt / fee))
                ra_g.append(ratio(amt_g, Lsb - amt / fee, Ltb + amt / fee))
            ok_n = int((npeer > 0).sum())
            obs_ok = ratio(amt_g[npeer > 0], Ls_a[npeer > 0], Lt_a[npeer > 0])
            o = out['obs_w']['obs']
            for nm, v, ref in [('random_recipient', rr, obs_ok), ('random_amount_obs_w', ra_g, o),
                               ('random_amount_native', ra_n, o)]:
                r95 = q(v)
                out[nm] = dict(mean=float(np.nanmean(v)), mc95=r95, obs_ref=ref,
                               verdict=('below' if ref < r95[0] else 'above' if ref > r95[1] else 'inside'))
            out['random_recipient']['events_with_peer'] = ok_n
            cell[s] = out
        cells[f'{arm}|{mdl}'] = cell
res['cells'] = cells

# verdict counts over the 20 arm x model cells
cnt = {}
for s in SETS:
    for wn in WEIGHTS:
        vs = [c[s].get(wn, {}).get('verdict') for c in cells.values() if s in c and c[s].get('n')]
        cnt[f'{s}|{wn}'] = {v: vs.count(v) for v in ['below', 'inside', 'above', None] if vs.count(v)}
    for nm in ['random_recipient', 'random_amount_obs_w', 'random_amount_native']:
        vs = [c[s][nm]['verdict'] for c in cells.values() if c[s].get('n')]
        cnt[f'{s}|{nm}'] = {v: vs.count(v) for v in ['below', 'inside', 'above'] if vs.count(v)}
res['verdict_counts'] = cnt
for s in SETS:
    for wn in WEIGHTS:
        mins = [c[s][wn]['min'] for c in cells.values() if c[s].get(wn, {}).get('min') is not None]
        if mins:
            res.setdefault('min_range', {})[f'{s}|{wn}'] = [min(mins), max(mins)]

# Fable - Opus (main) on the paired common-weight ratio, all events and low events
fo = {}
for s in ['all', 'low']:
    for wn in ['obs_w', 'equal', 'native']:
        if wn == 'native' and s != 'low':
            continue
        vals = {}
        for mdl in ['Fable', 'Opus']:
            g = gi[(gi.arm == 'main') & (gi.model == mdl)]
            g = g[MASK[s](g)]
            wo, wm = WEIGHTS[wn]
            b = {}
            for k, (n, dd) in dict(obs=(g[wo] * g.L_src_after, g[wo] * g.L_dst_after),
                                   min=(g[wm] * g.Ls_min, g[wm] * g.Lt_min)).items():
                ns = np.array([n[g.seed == sd].sum() for sd in SEEDS])
                ds = np.array([dd[g.seed == sd].sum() for sd in SEEDS])
                with np.errstate(divide='ignore', invalid='ignore'):
                    b[k] = ns[draws].sum(1) / ds[draws].sum(1)
            vals[mdl] = b
        c = cells
        fo[f'{s}|{wn}'] = dict(
            min_diff=c['main|Fable'][s][wn]['min'] - c['main|Opus'][s][wn]['min'],
            min_diff_ci95=q(vals['Fable']['min'] - vals['Opus']['min']),
            ratio_diff=c['main|Fable'][s][wn]['ratio'] - c['main|Opus'][s][wn]['ratio'],
            ratio_diff_ci95=q(vals['Fable']['obs'] / vals['Fable']['min'] - vals['Opus']['obs'] / vals['Opus']['min']))
res['fable_minus_opus_main'] = fo

OUT.write_text(json.dumps(rnd(res), ensure_ascii=False, indent=1))

# ---------------------------------------------------------------- figure: paired ratio obs / min per cell
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
plt.rcParams['font.family'] = ['AppleGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
arm_lab = {'main': '2,000만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
panels = [('low', 'native', '(a) $L<1$ 수혜, 각자의 이전량 가중'), ('low', 'obs_w', '(b) $L<1$ 수혜, 관측 금액 가중'),
          ('low', 'equal', '(c) $L<1$ 수혜, 사건당 같은 가중'), ('all', 'obs_w', '(d) 전체 GIVE, 관측 금액 가중')]
fig, axes = plt.subplots(1, 4, figsize=(7.0, 3.0), sharey=True)
labels = [f'{arm_lab[a]} {m}' for a in ARMS for m in MODELS]
for ax, (s, wn, title) in zip(axes, panels):
    for i, (a, m) in enumerate([(a, m) for a in ARMS for m in MODELS]):
        e = cells[f'{a}|{m}'][s][wn]
        y = len(labels) - 1 - i
        col = {'below': '#3F7FC1', 'above': '#C66A2C', 'inside': '#555'}[e['verdict']]
        ax.plot(e['ratio_ci95'], [y, y], color=col, lw=1.0)
        ax.plot(e['ratio'], y, 'o', color=col, ms=3)
    for k in range(1, len(ARMS)):
        ax.axhline(len(labels) - .5 - 5 * k, color='#ddd', lw=.5)
    ax.axvline(1, color='#999', ls='--', lw=.6)
    ax.set_xscale('log')
    ax.set_xticks([.25, .5, 1, 2, 4]); ax.set_xticklabels(['0.25', '0.5', '1', '2', '4'])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlim(.15, 12)
    ax.set_title(title, fontsize=6.4)
    ax.set_xlabel(r'관측 $\rho$ / 최소 구조 $\rho$', fontsize=6)
    ax.tick_params(labelsize=5.6)
axes[0].set_yticks(range(len(labels))); axes[0].set_yticklabels(labels[::-1], fontsize=5.4)
fig.tight_layout(w_pad=.4)
for ext in ['pdf', 'png']:
    fig.savefig(FIG / f'w2c_rho_paired.{ext}', dpi=220)
plt.close(fig)

print(json.dumps(rnd({'verdict_counts': cnt, 'min_range': res['min_range'], 'fable_minus_opus_main': fo}), indent=1))
