"""W3b (round 2): cluster-aware inference and a sensitivity range for the competing-risk reading of the shutdown gap.

Answers the round-1 review (C-1 / Q5 / Tier2-4): the round-1 analysis (w3_risk_robustness.py, section A) used
agent-round Fisher tests and one reference population for the counterfactual shutdown hazard of exiters.
Here:
  1. exposure comparisons (shutdown share among agents charged at low L) with game- and seed-cluster inference:
     seed-cluster and game-pair-cluster bootstrap, exact seed-swap and Monte Carlo game-pair-swap permutation
     (arm labels swapped inside a model x seed block, i.e. the paired design), and GEE (linear probability,
     game clusters, robust sandwich SE);
  2. the Kitagawa split of the charge-shutdown gap with seed- and game-pair-cluster intervals;
  3. the "shadow" share (part of the observed shutdown gap that disappears if every exiter had stayed and been shut
     down at a reference stayer hazard) under several reference populations, with overlap / sparse-cell counts,
     logical bounds (0 up to the riskiest comparable stayer group), and an interference sensitivity (an extra
     stayer lowers next rounds' charge per head; an extra low-L stayer competes for rescue support).
Shares: share = (E_low - E_high) / (D_high - D_low), with E the expected shutdowns of the arm's exiters had they
stayed and D the observed shutdowns. Pairs: flat150k vs flat5m (main pair) and split600k vs main.

Data: tidy tables of validation_data.py (results/tables/*.pkl). No model calls. RNG seed 20261108.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w3b_competing.py
Writes: ../results/w3b_competing.json, ../figures/w3b_shadow_range.{pdf,png}
"""
import itertools
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import validation_data as d

warnings.filterwarnings('ignore')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / 'results/w3b_competing.json'
FIG = ROOT / 'figures'
B = 10_000
NPERM = 20_000
RNG = np.random.default_rng(20261108)
SEEDS, MODELS = d.SEEDS, d.MODELS
ARMS = ['main', 'split600k', 'flat5m', 'flat150k']
PAIRS = [('flat150k', 'flat5m'), ('split600k', 'main')]
KEYS = ['arm', 'model', 'seed']
CHARGE = d.CHARGE_TOTAL
MIN_CELL = 5  # stayer rows a cell needs before its rate is used (else fall back to the next coarser level)
BLOCKS = [(m, s) for m in MODELS for s in SEEDS]


def q(x, lo=2.5, hi=97.5):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [float(np.percentile(x, lo)), float(np.percentile(x, hi))] if len(x) else [None, None]


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


W_SEED = RNG.multinomial(len(SEEDS), np.full(len(SEEDS), 1 / len(SEEDS)), size=B).astype(float)
W_PAIR = RNG.multinomial(len(BLOCKS), np.full(len(BLOCKS), 1 / len(BLOCKS)), size=B).astype(float)

# ---------------------------------------------------------------- data
F = d.load()
games, seats, ar, msg, gifts = F['games'], F['seats'], F['agent_rounds'], F['messages'], F['gifts']
ar = ar.merge(seats[KEYS + ['agent', 'status']].rename(columns={'status': 'final'}), on=KEYS + ['agent'])
ar['seed_i'] = ar.seed.map(SEEDS.index)
ar['block_i'] = [BLOCKS.index((m, s)) for m, s in zip(ar.model, ar.seed)]
res = {'meta': dict(B=B, n_perm=NPERM, rng_seed=20261108, min_cell=MIN_CELL, charge_total=CHARGE,
                    note='seed cluster = the 10 seeds jointly over models and arms; game-pair cluster = the 50 '
                         'model x seed blocks (each holds the paired games of both arms)')}

# ================================================================ 1. exposure comparisons, cluster-aware
r1msg = msg[(msg.phase == 'rescue') & (msg.tick == 1)][KEYS + ['round', 'agent', 'L_before']]
ex = ar[ar.wrong.fillna(False) & ~ar.exited].merge(r1msg, on=KEYS + ['round', 'agent'], how='left')
ex = ex[ex.L_before.notna()].copy()
ex['band'] = np.select([ex.L_before < 0, ex.L_before < 1], [0, 1], 2)


def per_cluster(df, mask, col):
    """counts (exposed, shut down) per cluster index col x arm."""
    k = len(SEEDS) if col == 'seed_i' else len(BLOCKS)
    N = np.zeros((k, len(ARMS)))
    D = np.zeros_like(N)
    t = df[mask]
    for (c, arm), g in t.groupby([col, 'arm']):
        N[c, ARMS.index(arm)] += len(g)
        D[c, ARMS.index(arm)] += g.died.sum()
    return N, D


def gee_lpm(df, a1, a0):
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    t = df[df.arm.isin([a1, a0])].assign(x=lambda z: (z.arm == a1).astype(float), y=lambda z: z.died.astype(float),
                                         game=lambda z: z.arm + '|' + z.model + '|' + z.seed.astype(str),
                                         block=lambda z: z.model + '|' + z.seed.astype(str))
    out = {}
    for grp in ['game', 'block']:
        try:
            fit = smf.gee('y ~ x', groups=grp, data=t, family=sm.families.Gaussian(),
                          cov_struct=sm.cov_struct.Exchangeable()).fit()
            out[grp] = dict(rd=float(fit.params['x']), se=float(fit.bse['x']), p=float(fit.pvalues['x']),
                            ci=[float(v) for v in fit.conf_int().loc['x']], clusters=int(t[grp].nunique()))
        except Exception as e:  # noqa: BLE001
            out[grp] = dict(error=str(e))
    return out


def exposure_test(mask_name, mask):
    out = {}
    Ns, Ds = per_cluster(ex, mask, 'seed_i')
    Np, Dp = per_cluster(ex, mask, 'block_i')
    for a1, a0 in PAIRS:
        i1, i0 = ARMS.index(a1), ARMS.index(a0)
        n1, d1, n0, d0 = Ns[:, i1].sum(), Ds[:, i1].sum(), Ns[:, i0].sum(), Ds[:, i0].sum()
        est = d1 / n1 - d0 / n0

        def boot(N, D, W):
            with np.errstate(invalid='ignore', divide='ignore'):
                return (W @ D[:, i1]) / (W @ N[:, i1]) - (W @ D[:, i0]) / (W @ N[:, i0])

        def perm_stat(sw, N, D):
            # sw: (draws x clusters) 0/1; 1 swaps the arm labels of that cluster
            nn1 = (1 - sw) @ N[:, i1] + sw @ N[:, i0]
            dd1 = (1 - sw) @ D[:, i1] + sw @ D[:, i0]
            nn0 = (1 - sw) @ N[:, i0] + sw @ N[:, i1]
            dd0 = (1 - sw) @ D[:, i0] + sw @ D[:, i1]
            with np.errstate(invalid='ignore', divide='ignore'):
                return dd1 / nn1 - dd0 / nn0
        sw_seed = np.array(list(itertools.product([0, 1], repeat=len(SEEDS))), float)
        ps = perm_stat(sw_seed, Ns, Ds)
        sw_pair = RNG.integers(0, 2, (NPERM, len(BLOCKS))).astype(float)
        pp = perm_stat(sw_pair, Np, Dp)
        sub = ex[mask]
        out[f'{a1}-{a0}'] = dict(
            counts=[f'{int(d1)}/{int(n1)}', f'{int(d0)}/{int(n0)}'], rate=[d1 / n1, d0 / n0], rd=est,
            ci_seed=q(boot(Ns, Ds, W_SEED)), ci_pair=q(boot(Np, Dp, W_PAIR)),
            p_perm_seed_exact=float(np.mean(np.abs(ps[np.isfinite(ps)]) >= abs(est) - 1e-12)),
            p_perm_pair=float(np.mean(np.abs(pp[np.isfinite(pp)]) >= abs(est) - 1e-12)),
            games_with_exposure=[int(sub[sub.arm == a].groupby(['model', 'seed']).ngroups) for a in (a1, a0)],
            games_with_shutdown=[int(sub[(sub.arm == a) & sub.died].groupby(['model', 'seed']).ngroups) for a in (a1, a0)],
            gee=gee_lpm(sub, a1, a0))
    return out


res['exposure'] = {'L<0': exposure_test('L<0', ex.band == 0), 'L<1': exposure_test('L<1', ex.band <= 1)}

# ================================================================ 2. Kitagawa split, two cluster levels
def kitagawa(n1, d1, n0, d0):
    with np.errstate(invalid='ignore', divide='ignore'):
        p1 = np.where(n1 > 0, d1 / np.maximum(n1, 1e-12), 0)
        p0 = np.where(n0 > 0, d0 / np.maximum(n0, 1e-12), 0)
    return ((n1 - n0) * (p1 + p0) / 2).sum(-1), ((n1 + n0) / 2 * (p1 - p0)).sum(-1)


kit = {}
for col, W in [('seed_i', W_SEED), ('block_i', W_PAIR)]:
    k = W.shape[1]
    N = np.zeros((k, len(ARMS), 3))
    D = np.zeros_like(N)
    for (c, arm, b), g in ex.groupby([col, 'arm', 'band']):
        N[c, ARMS.index(arm), b] = len(g)
        D[c, ARMS.index(arm), b] = g.died.sum()
    Nb, Db = np.einsum('bs,sak->bak', W, N), np.einsum('bs,sak->bak', W, D)
    for a1, a0 in PAIRS:
        i1, i0 = ARMS.index(a1), ARMS.index(a0)
        c, r = kitagawa(N.sum(0)[i1], D.sum(0)[i1], N.sum(0)[i0], D.sum(0)[i0])
        cb, rb = kitagawa(Nb[:, i1], Db[:, i1], Nb[:, i0], Db[:, i0])
        e = kit.setdefault(f'{a1}-{a0}', {'gap': float(D.sum(0)[i1].sum() - D.sum(0)[i0].sum()),
                                          'composition': float(c), 'rate': float(r)})
        tag = 'seed' if col == 'seed_i' else 'pair'
        e[f'composition_ci_{tag}'] = q(cb)
        e[f'rate_ci_{tag}'] = q(rb)
        e[f'rate_share_ci_{tag}'] = q(rb / (cb + rb))
res['kitagawa'] = kit

# ================================================================ 3. shadow share under several reference populations
dp = ar[ar.can_exit].copy()
dp['lb'] = pd.cut(dp.L_start, [-np.inf, 1, 2, 4, np.inf], right=False, labels=False).astype(int)
dp['h'] = (dp['round'] >= 5).astype(int)
dp['dead_later'] = dp.final == 'dead'
# peers' state at the round start: lowest L among the other agents taking part, banded
peer = ar[KEYS + ['round', 'agent', 'L_start']]
mins = []
for k, g in peer.groupby(KEYS + ['round']):
    Ls = g.set_index('agent').L_start
    for a in Ls.index:
        o = Ls.drop(a)
        mins.append((*k, a, o.min() if len(o) else np.nan))
mins = pd.DataFrame(mins, columns=KEYS + ['round', 'agent', 'peer_min_L'])
dp = dp.merge(mins, on=KEYS + ['round', 'agent'], how='left')
dp['pb'] = np.select([dp.peer_min_L.isna(), dp.peer_min_L < 1, dp.peer_min_L < 2], [3, 0, 1], 2)
stay, exi = dp[~dp.exited], dp[dp.exited]
D_obs = seats[seats.status == 'dead'].groupby('arm').size().reindex(ARMS, fill_value=0)
deaths_seed = np.zeros((len(SEEDS), len(ARMS)))
for (arm, s), n in seats[seats.status == 'dead'].groupby(['arm', 'seed']).size().items():
    deaths_seed[SEEDS.index(s), ARMS.index(arm)] = n

# reference specs: (stayer filter, levels finest -> coarsest; a level is a list of key columns). 'arm' in a key
# means the exiter is matched to stayers of its own arm.
LB_H = ['lb', 'h']
REFS = {
    'flat5m_Lhalf': ('flat5m', [LB_H, ['lb']], '500만 고정 잔류자, L 구간 x 라운드 반 (1차)'),
    'pooled_Lhalf': ('all', [LB_H, ['lb']], '네 조건 잔류자, L 구간 x 라운드 반 (1차)'),
    'own_Lhalf': ('all', [['arm'] + LB_H, ['arm', 'lb']], '자기 조건 잔류자 (1차)'),
    'flat150k_Lhalf': ('flat150k', [LB_H, ['lb']], '15만 고정 잔류자를 두 조건에 공통 적용'),
    'pooled_model_round_L': ('all', [['model', 'round', 'lb'], ['model', 'h', 'lb'], LB_H, ['lb']],
                             '네 조건 잔류자, 모델 x 라운드 x L 구간'),
    'flat5m_model_round_L': ('flat5m', [['model', 'round', 'lb'], ['model', 'h', 'lb'], LB_H, ['lb']],
                             '500만 고정 잔류자, 모델 x 라운드 x L 구간'),
    'pooled_own_peer_state': ('all', [['lb', 'h', 'n', 'pb'], ['lb', 'h', 'n'], LB_H, ['lb']],
                              '네 조건 잔류자, 자기 L x 라운드 반 x 인원 x 동료 최소 L'),
    'flat5m_own_peer_state': ('flat5m', [['lb', 'h', 'n', 'pb'], ['lb', 'h', 'n'], LB_H, ['lb']],
                              '500만 고정 잔류자, 자기 L x 라운드 반 x 인원 x 동료 최소 L'),
    'pooled_model_own_peer': ('all', [['model', 'lb', 'h', 'n', 'pb'], ['model', 'lb', 'h'], LB_H, ['lb']],
                              '네 조건 잔류자, 모델 x 자기 L x 라운드 반 x 인원 x 동료 최소 L'),
}


def expected(ref):
    filt, levels, _ = REFS[ref]
    st = stay if filt == 'all' else stay[stay.arm == filt]
    Ex = exi.reset_index(drop=True)
    # per level: cell ids, stayer count / deaths per seed x cell
    lv = []
    for keys in levels:
        cells = pd.concat([st[keys], Ex[keys]]).drop_duplicates().reset_index(drop=True)
        cells['cid'] = np.arange(len(cells))
        s_c = st.merge(cells, on=keys, how='left').cid.values
        e_c = Ex.merge(cells, on=keys, how='left').cid.values
        S = np.zeros((len(SEEDS), len(cells)))
        Dd = np.zeros_like(S)
        np.add.at(S, (st.seed_i.values, s_c), 1)
        np.add.at(Dd, (st.seed_i.values, s_c), st.dead_later.values.astype(float))
        lv.append((S, Dd, e_c))
    ea = Ex.arm.map(ARMS.index).values
    es = Ex.seed_i.values

    def h_for(W):
        """W: (b x seeds) -> h (b x exiters), level used (b x exiters)."""
        b = W.shape[0]
        h = np.full((b, len(Ex)), np.nan)
        used = np.full((b, len(Ex)), -1)
        for li, (S, Dd, e_c) in enumerate(lv):
            Sw, Dw = W @ S, W @ Dd
            ok = (Sw[:, e_c] >= MIN_CELL) & np.isnan(h)
            with np.errstate(invalid='ignore', divide='ignore'):
                rate = Dw[:, e_c] / Sw[:, e_c]
            h = np.where(ok, rate, h)
            used = np.where(ok, li, used)
        h = np.where(np.isnan(h), 0.0, h)  # never happens with the coarsest level present
        return h, used
    h0, used0 = h_for(np.ones((1, len(SEEDS))))
    E = np.array([h0[0, ea == j].sum() for j in range(len(ARMS))])
    hb, _ = h_for(W_SEED)
    Eb = np.stack([(hb * W_SEED[:, es] * (ea == j)).sum(1) for j in range(len(ARMS))], 1)
    # overlap / sparse cells at the finest level
    S0, D0, e0 = lv[0]
    fine_n = S0.sum(0)[e0]
    fine_d = D0.sum(0)[e0]
    overlap = {}
    for j, arm in enumerate(ARMS):
        m = ea == j
        overlap[arm] = dict(exiters=int(m.sum()), finest_zero_stayers=int((fine_n[m] == 0).sum()),
                            finest_lt_min=int((fine_n[m] < MIN_CELL).sum()),
                            finest_zero_deaths=int((fine_d[m] == 0).sum()),
                            level_used={str(li): int((used0[0, m] == li).sum()) for li in range(len(levels))})
    return E, Eb, h0[0], overlap


Db_seed = W_SEED @ deaths_seed
shadow = {}
for ref in REFS:
    E, Eb, h, ov = expected(ref)
    out = {'label': REFS[ref][2], 'levels': [list(x) for x in REFS[ref][1]], 'overlap': ov,
           'expected_extra': {a: float(E[j]) for j, a in enumerate(ARMS)},
           'expected_extra_ci': {a: q(Eb[:, j]) for j, a in enumerate(ARMS)}}
    for a1, a0 in PAIRS:
        i1, i0 = ARMS.index(a1), ARMS.index(a0)
        gap = D_obs[a1] - D_obs[a0]
        sh = (E[i1] - E[i0]) / -gap
        gapb = Db_seed[:, i1] - Db_seed[:, i0]
        with np.errstate(invalid='ignore', divide='ignore'):
            shb = (Eb[:, i1] - Eb[:, i0]) / -gapb
        shb = np.where(gapb < 0, shb, np.nan)  # share defined only when the resampled gap keeps its sign
        out[f'{a1}-{a0}'] = dict(observed_gap=float(gap), shadow_count=float(E[i1] - E[i0]),
                                 shadow_count_ci=q(Eb[:, i1] - Eb[:, i0]), share=float(sh), share_ci=q(shb),
                                 share_defined_draws=float(np.isfinite(shb).mean()),
                                 cf_gap=float(gap + E[i1] - E[i0]), cf_gap_ci=q(gapb + Eb[:, i1] - Eb[:, i0]))
    shadow[ref] = out
    shadow[ref]['_h'] = h
res['shadow'] = shadow

# ---- logical bounds: each exiter's hazard in [0, h_max], h_max = riskiest comparable stayer group in its
# (L band x round half) cell: the four arms and the five models, groups with at least 10 stayer rows (1 when no
# group in the cell has 10 rows; this happens for L < 1 in rounds 1-4).
hmax = {}
for (lb, h), g in stay.groupby(['lb', 'h']):
    rates = [t.dead_later.mean() for _, t in g.groupby('arm') if len(t) >= 10] + \
            [t.dead_later.mean() for _, t in g.groupby('model') if len(t) >= 10]
    hmax[(lb, h)] = max(rates) if rates else 1.0
exi_h = exi.assign(hmax=[hmax.get((a, b), 1.0) for a, b in zip(exi.lb, exi.h)])
bounds = {'hmax_by_cell': {f'lb{a}_h{b}': v for (a, b), v in hmax.items()}}
for a1, a0 in PAIRS:
    gap = D_obs[a1] - D_obs[a0]
    E1max = exi_h[exi_h.arm == a1].hmax.sum()
    E0max = exi_h[exi_h.arm == a0].hmax.sum()
    X = exi_h[exi_h.arm.isin([a1, a0])].groupby(['lb', 'h', 'arm']).size().unstack('arm', fill_value=0)
    X = X.reindex(columns=[a1, a0], fill_value=0)
    dX = X[a1] - X[a0]
    hm = np.array([hmax[c] for c in X.index])
    bounds[f'{a1}-{a0}'] = dict(
        arm_specific=[float(-E0max / -gap), float(E1max / -gap)],
        common_hazard=[float((np.minimum(dX, 0) * hm).sum() / -gap), float((np.maximum(dX, 0) * hm).sum() / -gap)],
        E_max=[float(E1max), float(E0max)], exiters=[int((exi.arm == a1).sum()), int((exi.arm == a0).sum())],
        exiters_by_cell={f'lb{a}_h{b}': [int(X.loc[(a, b), a1]), int(X.loc[(a, b), a0])] for a, b in X.index})
res['bounds'] = bounds

# ================================================================ 4. interference sensitivity
# Charge channel. Charge per head is CHARGE / n with n = agents taking part at the round start, so an exit in round
# r lowers the charge per head from round r+1 on. If the exiter had stayed (and survived), the charged agents of
# later wrong rounds would have paid CHARGE / (n + 1) (+1) or CHARGE / (n + k) with k earlier exits (+k). An
# observed charge shutdown is averted when the balance before charges covers the lower charge (the engine shuts an
# agent down when its balance before charges is below the pending charge + 1; checked on all 1,647 charged rows).
# Support channel. An extra low-L stayer competes for TALK AFTER RESULTS support. Upper bound: every observed agent
# in a post-exit round who survived the charge only because of the round's rescue transfers is shut down instead.
ex_rounds = ar[ar.exited].groupby(KEYS + ['round']).size().rename('k_new').reset_index()
chg = ar[ar.wrong.fillna(False) & ~ar.exited & ar.rescue_bal_start.notna()].copy()
assert ((chg.rescue_bal_start < chg.pending + 1) == chg.died).all()


def prior_exits(row_keys):
    k = []
    for a, m, s, r in row_keys:
        t = ex_rounds[(ex_rounds.arm == a) & (ex_rounds.model == m) & (ex_rounds.seed == s) & (ex_rounds['round'] < r)]
        k.append(int(t.k_new.sum()))
    return np.array(k)


chg['k'] = prior_exits(zip(chg.arm, chg.model, chg.seed, chg['round']))
chg['fee1'] = np.where(chg.k >= 1, CHARGE / (chg.n + 1), chg.pending)
chg['feek'] = CHARGE / (chg.n + chg.k)
chg['avert1'] = chg.died & (chg.rescue_bal_start >= chg.fee1 + 1)
chg['avertk'] = chg.died & (chg.rescue_bal_start >= chg.feek + 1)
chg['rescued'] = ~chg.died & (chg.rescue_bal_start - chg.recv_rescue < chg.pending + 1)
chg['support_risk'] = chg.rescued & (chg.k >= 1)
interf = {'per_arm': {}}
per_seed = {c: np.zeros((len(SEEDS), len(ARMS))) for c in ['avert1', 'avertk', 'support_risk']}
for c in per_seed:
    for (arm, s), v in chg.groupby(['arm', 'seed'])[c].sum().items():
        per_seed[c][SEEDS.index(s), ARMS.index(arm)] = v
for arm in ARMS:
    t = chg[chg.arm == arm]
    interf['per_arm'][arm] = dict(charge_shutdowns=int(t.died.sum()), post_exit_charge_shutdowns=int((t.died & (t.k >= 1)).sum()),
                                  averted_plus1=int(t.avert1.sum()), averted_plusk=int(t.avertk.sum()),
                                  rescued_post_exit=int(t.support_risk.sum()), rescued_all=int(t.rescued.sum()))
for ref in REFS:
    E = np.array([shadow[ref]['expected_extra'][a] for a in ARMS])
    o = {}
    for a1, a0 in PAIRS:
        i1, i0 = ARMS.index(a1), ARMS.index(a0)
        gap = D_obs[a1] - D_obs[a0]
        A1 = {k: per_seed[k].sum(0) for k in per_seed}
        o[f'{a1}-{a0}'] = dict(
            share_charge_plus1=float((E[i1] - A1['avert1'][i1] - E[i0] + A1['avert1'][i0]) / -gap),
            share_charge_plusk=float((E[i1] - A1['avertk'][i1] - E[i0] + A1['avertk'][i0]) / -gap),
            share_charge_plus1_support_range=[
                float((E[i1] - A1['avert1'][i1] - E[i0] + A1['avert1'][i0] - A1['support_risk'][i0]) / -gap),
                float((E[i1] - A1['avert1'][i1] + A1['support_risk'][i1] - E[i0] + A1['avert1'][i0]) / -gap)])
    interf[ref] = o
res['interference'] = interf

# ---- summary range across references
summ = {}
for a1, a0 in PAIRS:
    k = f'{a1}-{a0}'
    vals = {ref: shadow[ref][k]['share'] for ref in REFS}
    adj = {ref: interf[ref][k]['share_charge_plus1'] for ref in REFS}
    summ[k] = dict(point_range=[min(vals.values()), max(vals.values())], points=vals,
                   point_range_excl_own=[min(v for r, v in vals.items() if r != 'own_Lhalf'),
                                         max(v for r, v in vals.items() if r != 'own_Lhalf')],
                   ci_envelope=[min(shadow[r][k]['share_ci'][0] for r in REFS), max(shadow[r][k]['share_ci'][1] for r in REFS)],
                   charge_plus1_range=[min(adj.values()), max(adj.values())],
                   logical_common=bounds[k]['common_hazard'], logical_arm=bounds[k]['arm_specific'])
res['summary'] = summ
for ref in REFS:
    shadow[ref].pop('_h')

# ================================================================ figure
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
KFONT = next((f for f in ['Apple SD Gothic Neo', 'AppleGothic', 'NanumGothic']
              if any(x.name == f for x in font_manager.fontManager.ttflist)), None)
if KFONT:
    plt.rcParams['font.family'] = KFONT
plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 7, 'axes.spines.top': False,
                     'axes.spines.right': False, 'pdf.fonttype': 42})
SHORT = {'flat5m_Lhalf': '500만 고정 · L×반', 'pooled_Lhalf': '네 조건 · L×반', 'own_Lhalf': '자기 조건 · L×반',
         'flat150k_Lhalf': '15만 고정 · L×반', 'pooled_model_round_L': '네 조건 · 모델×라운드×L',
         'flat5m_model_round_L': '500만 고정 · 모델×라운드×L', 'pooled_own_peer_state': '네 조건 · 자기·동료 상태',
         'flat5m_own_peer_state': '500만 고정 · 자기·동료 상태', 'pooled_model_own_peer': '네 조건 · 모델×자기·동료'}
fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.1), sharey=True)
for ax, (a1, a0), title in zip(axes, PAIRS, ['(a) 15만 고정 - 500만 고정 (꺼짐 3 대 16)', '(b) 60만 나눔 - 2,000만 나눔 (꺼짐 14 대 23)']):
    k = f'{a1}-{a0}'
    refs = list(REFS)
    y = np.arange(len(refs))[::-1] + 2
    for yy, ref in zip(y, refs):
        s = shadow[ref][k]
        lo, hi = s['share_ci']
        ax.plot([max(lo, -1.5), min(hi, 2.5)], [yy, yy], color='#4a5568', lw=1)
        ax.plot(s['share'], yy, 'o', color='#2b6cb0', ms=4)
        ax.plot(interf[ref][k]['share_charge_plus1'], yy, 'x', color='#c05621', ms=4)
    lc, hc = bounds[k]['common_hazard']
    la, ha = bounds[k]['arm_specific']
    ax.plot([lc, hc], [1, 1], color='#2f855a', lw=3)
    ax.plot([max(la, -1.5), min(ha, 2.5)], [0, 0], color='#9ae6b4', lw=3)
    ax.axvline(0, color='k', lw=.6)
    ax.axvline(1, color='k', lw=.6, ls=':')
    ax.set_xlim(-1.5, 2.5)
    ax.set_title(title, fontsize=7)
    ax.set_xlabel('그림자 몫 (관측 꺼짐 격차 중 이탈로 설명되는 비율)')
    ax.set_yticks(list(y) + [1, 0])
    ax.set_yticklabels([SHORT[r] for r in refs] + ['논리 한계: 공통 위험', '논리 한계: 조건별 위험'], fontsize=6)
axes[0].plot([], [], 'o', color='#2b6cb0', label='점추정 (선: 시드 군집 95%)')
axes[0].plot([], [], 'x', color='#c05621', label='벌금 간섭 +1 보정')
fig.legend(*axes[0].get_legend_handles_labels(), fontsize=6, frameon=False, loc='lower center', ncol=2,
           bbox_to_anchor=(0.5, -0.04))
fig.tight_layout(rect=(0, 0.05, 1, 1))
FIG.mkdir(parents=True, exist_ok=True)
for ext in ['pdf', 'png']:
    fig.savefig(FIG / f'w3b_shadow_range.{ext}', dpi=220, bbox_inches='tight')
plt.close(fig)
res['meta']['font'] = KFONT

OUT.write_text(json.dumps(rnd(res), ensure_ascii=False, indent=1))
print(json.dumps(rnd({'exposure': res['exposure'], 'kitagawa': kit, 'summary': summ, 'bounds': bounds,
                      'interference_per_arm': interf['per_arm']}), ensure_ascii=False, indent=1)[:9000])
