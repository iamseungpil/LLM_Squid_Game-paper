"""W4b (review round 2, Q6 / Tier1-2 / structure-2): common support, out-of-sample validation and
model contrasts for the exit decision. Existing data only; no model calls.

Input: the exit-opportunity table built by w4_cost_text.py (imported, so running this script also
rewrites the w4 outputs, which are deterministic).  Unit: an exit opportunity = an agent that may
EXIT at a round (not that round's solver), with L at the first TALK-before-SOLVE tick.

Parts
  G  common support. Decision states are cut into L band x round band (state cells) and
     L band x round band x runway band (cost cells). For every model: share of its opportunities and
     exits that lie in cells where all five models (or the compared pair) are observed. In the shared
     cells, pairwise exit-rate differences (lower-C model minus higher-C model) standardised with overlap weights w_c = nA nB / (nA + nB);
     95% intervals resample seeds (each seed carries one game per model, so this is the game cluster);
     p values are exact sign-flip tests that swap the two models' games within seeds (2^10); Holm over pairs.
  H  leave-one-seed-out prediction of EXIT: log loss, Brier, calibration by decile and per-model
     observed / expected, for specs with and without cost terms (own earlier talk cost, previous-round
     talk cost, runway) and with and without model effects. Loss differences get game-cluster bootstrap CIs.
  I  model contrasts (log odds) with and without cost terms, cluster-robust by game, Wald test of all
     model effects, the ten pairwise contrasts with Holm. Includes the round-1 spec with p = 0.184.

Outputs: paper/cogsci2027/validation_20261108/results/w4b_cost_validation.json, paper/cogsci2027/validation_20261108/figures/w4b_validation.{pdf,png},
         paper/cogsci2027/validation_20261108/ko/parts/w4_tab_{support,loso,contrast}.tex
Run (from paper/cogsci2027/validation_20261108/tools):  ~/.venvs/squid-game/bin/python w4b_cost_validation.py
"""
import itertools
import json
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

import w4_cost_text as w4

VAL = w4.VAL
OUT_JSON = VAL / 'results/w4b_cost_validation.json'
ORDER = w4.ORDER
PAIRS = list(itertools.combinations(ORDER, 2))
RNG = np.random.default_rng(20261109)
NBOOT = 4000
f1 = w4.f1

# ----------------------------------------------------------------------------------------------
# Exit opportunities with the cost terms
# ----------------------------------------------------------------------------------------------
AR = w4.AR_sorted
prev = AR.groupby(['arm', 'seed', 'model', 'agent']).talk_gen.shift()       # own talk spend, previous round
EO = w4.EO.copy()
EO['prev_talk'] = prev.reindex(EO.index).fillna(EO.tbar).clip(lower=1)    # round 1: model mean (as own_lag)
EO['log_prev'] = np.log(EO.prev_talk)
L_EDGES, L_LAB = [0, 0.5, 1, 2, np.inf], ['<0.5', '0.5-1', '1-2', '>=2']
R_EDGES, R_LAB = [0, 1, 3, 8], ['1', '2-3', '4-8']
W_EDGES, W_LAB = [0, 10, 40, 100, np.inf], ['<10', '10-40', '40-100', '>=100']
EO['Lb'] = pd.cut(EO.L_prep, L_EDGES, right=False, labels=L_LAB).astype(str)
EO['Rb'] = pd.cut(EO['round'], R_EDGES, labels=R_LAB).astype(str)
EO['Wb'] = pd.cut(EO.runway, W_EDGES, right=False, labels=W_LAB).astype(str)
LF_EDGES = [0, 0.5, 1, 1.5, 2, 4, np.inf]                                 # finer L bands (sensitivity)
EO['Lf'] = pd.cut(EO.L_prep, LF_EDGES, right=False).astype(str)
EO['cell_state'] = EO.Lb + '|' + EO.Rb
EO['cell_fine'] = EO.Lf + '|' + EO.Rb
EO['cell_cost'] = EO.cell_state + '|' + EO.Wb
for c in ['cell_state', 'cell_fine', 'cell_cost']:                        # pooled arms: cells within arm
    EO[c + '_arm'] = EO.arm + '|' + EO[c]
MAIN = EO[EO.arm == 'main'].copy()
SEEDS = np.array(sorted(MAIN.seed.unique()))
assert len(MAIN) == 960 and MAIN.y.sum() == 61

# ----------------------------------------------------------------------------------------------
# G. Common support
# ----------------------------------------------------------------------------------------------


def count_array(df, cellcol):
    """n[seed, model, cell] and k[seed, model, cell] (opportunities, exits)."""
    cells = sorted(df[cellcol].unique())
    n = np.zeros((len(SEEDS), len(ORDER), len(cells)))
    k = np.zeros_like(n)
    si = {s: i for i, s in enumerate(SEEDS)}
    ci = {c: i for i, c in enumerate(cells)}
    for (s, m, c), g in df.groupby(['seed', 'model', cellcol]):
        n[si[s], ORDER.index(m), ci[c]] = len(g)
        k[si[s], ORDER.index(m), ci[c]] = g.y.sum()
    return cells, n, k


def std_diff(nA, kA, nB, kB):
    """Overlap-weighted difference of exit rates over cells with both groups observed (A - B)."""
    ok = (nA > 0) & (nB > 0)
    if not ok.any():
        return np.nan
    w = nA[ok] * nB[ok] / (nA[ok] + nB[ok])
    return float((w * (kA[ok] / nA[ok] - kB[ok] / nB[ok])).sum() / w.sum())


def support(df, cellcol):
    cells, n, k = count_array(df, cellcol)
    N, K = n.sum(0), k.sum(0)                      # model x cell
    common = (N > 0).all(0)
    out = dict(cells_total=len(cells), cells_common_all5=int(common.sum()), models={}, pairs={})
    for i, m in enumerate(ORDER):
        out['models'][m] = dict(opps=int(N[i].sum()), exits=int(K[i].sum()),
                                opps_common=int(N[i, common].sum()), exits_common=int(K[i, common].sum()),
                                share_common=f1(100 * N[i, common].sum() / N[i].sum()))
    # all-five standardised exit rate in the common cells, weights = harmonic mean of the five n
    if common.any():
        w = 1 / (1 / N[:, common]).sum(0)
        for i, m in enumerate(ORDER):
            out['models'][m]['std_rate_common'] = f1(100 * (w * K[i, common] / N[i, common]).sum() / w.sum())
    flips = np.array(list(itertools.product([0, 1], repeat=len(SEEDS))), bool)
    boot_idx = RNG.integers(0, len(SEEDS), size=(NBOOT, len(SEEDS)))
    for b, a in PAIRS:                       # a = the model with lower C in body Table 1; difference a - b
        ia, ib = ORDER.index(a), ORDER.index(b)
        both = (N[ia] > 0) & (N[ib] > 0)
        d = std_diff(N[ia], K[ia], N[ib], K[ib])
        rec = dict(cells=int(both.sum()),
                   share_a=f1(100 * N[ia, both].sum() / N[ia].sum()), share_b=f1(100 * N[ib, both].sum() / N[ib].sum()),
                   opps_a=int(N[ia, both].sum()), opps_b=int(N[ib, both].sum()),
                   exits_a=int(K[ia, both].sum()), exits_b=int(K[ib, both].sum()))
        if both.sum() == 0 or N[ia, both].sum() < 10 or N[ib, both].sum() < 10:
            rec.update(diff=None, ci=None, p=None)
            out['pairs'][f'{a}-{b}'] = rec
            continue
        na, ka, nb, kb = (x[:, :, both] for x in (n[:, ia:ia + 1], k[:, ia:ia + 1], n[:, ib:ib + 1], k[:, ib:ib + 1]))
        na, ka, nb, kb = na[:, 0], ka[:, 0], nb[:, 0], kb[:, 0]          # seed x shared cell
        bs = np.array([std_diff(na[ix].sum(0), ka[ix].sum(0), nb[ix].sum(0), kb[ix].sum(0)) for ix in boot_idx])
        perm = []
        for f in flips:
            fa = np.where(f[:, None], nb, na); fka = np.where(f[:, None], kb, ka)
            fb = np.where(f[:, None], na, nb); fkb = np.where(f[:, None], ka, kb)
            perm.append(std_diff(fa.sum(0), fka.sum(0), fb.sum(0), fkb.sum(0)))
        perm = np.array(perm)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        rec.update(diff=f1(100 * d), ci=[f1(100 * lo), f1(100 * hi)],
                   p=float((np.abs(perm) >= abs(d) - 1e-12).mean()))
        out['pairs'][f'{a}-{b}'] = rec
    tested = [kk for kk, v in out['pairs'].items() if v['p'] is not None]
    for kk, h in zip(tested, holm([out['pairs'][kk]['p'] for kk in tested])):
        out['pairs'][kk]['holm_p'] = h
    return out


def holm(ps):
    ps = np.asarray(ps, float)
    order = np.argsort(ps)
    adj = np.empty_like(ps)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i])
        adj[i] = min(1.0, run)
    return [float(x) for x in adj]


SUPPORT = {'main': {'state': support(MAIN, 'cell_state'), 'state_fine': support(MAIN, 'cell_fine'),
                    'cost': support(MAIN, 'cell_cost')},
           'all4': {'state': support(EO, 'cell_state_arm'), 'state_fine': support(EO, 'cell_fine_arm'),
                    'cost': support(EO, 'cell_cost_arm')}}

# ----------------------------------------------------------------------------------------------
# H. Leave-one-seed-out prediction
# ----------------------------------------------------------------------------------------------
COST = ['log_own', 'log_prev', 'log_run']
SPECS = {  # name: (terms, model effects)
    'null': ([], False),
    'model': ([], True),
    'L': (['logL'], False),
    'L_cost': (['logL'] + COST, False),
    'L_model': (['logL'], True),
    'L_own_model': (['logL', 'log_own'], True),          # round-1 table: model Wald p = 0.184
    'L_cost_model': (['logL'] + COST, True),
    'run_model': (['log_run'], True),
}


def glm(df, terms, fe, arm_fe):
    return sm.GLM(df.y, w4.design(df, terms, fe, arm_fe), family=sm.families.Binomial())


def loso(df, arm_fe=False):
    pred = {}
    for name, (terms, fe) in SPECS.items():
        p = pd.Series(np.nan, index=df.index)
        for s in SEEDS:
            tr, te = df[df.seed != s], df[df.seed == s]
            r = glm(tr, terms, fe, arm_fe).fit()
            X = w4.design(te, terms, fe, arm_fe).reindex(columns=r.params.index, fill_value=0.0)
            p[te.index] = 1 / (1 + np.exp(-(X.values @ r.params.values)))
        pred[name] = p.clip(1e-6, 1 - 1e-6)
    y = df.y.values
    gid = pd.factorize(df.gid)[0]
    G = gid.max() + 1
    boot = RNG.integers(0, G, size=(2000, G))
    ll_obs = {k: -(y * np.log(v) + (1 - y) * np.log(1 - v)).values for k, v in pred.items()}
    out = {}
    for name, p in pred.items():
        pv = p.values
        dec = pd.qcut(pv, 10, labels=False, duplicates='drop')
        cal = [dict(mean_pred=f1(100 * pv[dec == j].mean(), 2), obs=f1(100 * y[dec == j].mean(), 2), n=int((dec == j).sum()))
               for j in range(dec.max() + 1)]
        slope = sm.GLM(y, sm.add_constant(np.log(pv / (1 - pv))), family=sm.families.Binomial()).fit().params
        oe = {m: [int(y[(df.model == m).values].sum()), f1(pv[(df.model == m).values].sum())] for m in ORDER}
        out[name] = dict(logloss=f1(ll_obs[name].mean(), 4), brier=f1(((pv - y) ** 2).mean(), 4),
                         calib_slope=f1(slope[1], 2), calib_ratio_E_over_O=f1(pv.sum() / y.sum(), 3),
                         ece_decile=f1(sum(c['n'] * abs(c['mean_pred'] - c['obs']) for c in cal) / len(y), 2),
                         deciles=cal, obs_exp_by_model=oe)
    comps = [('L_cost', 'L'), ('L_model', 'L'), ('L_cost_model', 'L_model'), ('L_cost_model', 'L_cost'),
             ('L_own_model', 'L_model'), ('L', 'null'), ('run_model', 'L_model')]
    diffs = {}
    for a, b in comps:
        dl = ll_obs[a] - ll_obs[b]
        db = (pred[a].values - y) ** 2 - (pred[b].values - y) ** 2
        per_g = np.bincount(gid, dl, G)
        per_gb = np.bincount(gid, db, G)
        cnt = np.bincount(gid, None, G)
        bs = per_g[boot].sum(1) / cnt[boot].sum(1)
        bsb = per_gb[boot].sum(1) / cnt[boot].sum(1)
        diffs[f'{a}_minus_{b}'] = dict(logloss=f1(dl.mean(), 4), logloss_ci=[f1(x, 4) for x in np.percentile(bs, [2.5, 97.5])],
                                       brier=f1(db.mean(), 5), brier_ci=[f1(x, 5) for x in np.percentile(bsb, [2.5, 97.5])])
    return dict(n=int(len(df)), exits=int(y.sum()), specs=out, diffs=diffs), pred


LOSO_MAIN, PRED_MAIN = loso(MAIN)
LOSO_ALL, _ = loso(EO.copy(), arm_fe=True)

# ----------------------------------------------------------------------------------------------
# I. Model contrasts with and without cost terms (full sample, cluster-robust by game)
# ----------------------------------------------------------------------------------------------


def contrasts(df, terms, arm_fe=False):
    r = glm(df, terms, True, arm_fe).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(df.gid)[0]})
    names = list(r.params.index)
    V = r.cov_params().values
    b = r.params.values

    def vec(m1, m2):
        v = np.zeros(len(names))
        if m1 != 'Astra':
            v[names.index('m_' + m1)] += 1
        if m2 != 'Astra':
            v[names.index('m_' + m2)] -= 1
        return v
    from scipy.stats import norm
    pairs = {}
    for a, bb in PAIRS:
        v = vec(bb, a)                 # log odds of the later (lower-C) model minus the earlier one
        est, se = v @ b, np.sqrt(v @ V @ v)
        pairs[f'{bb}-{a}'] = dict(logodds=f1(est, 2), ci=[f1(est - 1.96 * se, 2), f1(est + 1.96 * se, 2)], se=f1(se, 2),
                                  p=float(2 * norm.sf(abs(est / se))))
    for kk, h in zip(pairs, holm([v['p'] for v in pairs.values()])):
        pairs[kk]['holm_p'] = h
    wald = w4.wald_models(r)
    cost = {t: [f1(r.params[t], 3), f1(r.bse[t], 3), float(r.pvalues[t])] for t in terms if t != 'logL'}
    return dict(wald=wald, pairs=pairs, cost_coef=cost, aic=f1(r.aic, 1),
                vs_astra={m: pairs[f'{m}-Astra'] for m in ORDER[1:]})


CONTRAST = {'main': {k: contrasts(MAIN, SPECS[k][0]) for k in ['L_model', 'L_own_model', 'L_cost_model']},
            'all4': {k: contrasts(EO, SPECS[k][0], arm_fe=True) for k in ['L_model', 'L_own_model', 'L_cost_model']}}
# how much of each cost term is between-model (R^2 of the term on model dummies, main)
COST_BETWEEN = {t: f1(sm.OLS(MAIN[t], w4.design(MAIN, [], True)).fit().rsquared, 3) for t in COST}
COST_BETWEEN_ALL = {t: f1(sm.OLS(EO[t], w4.design(EO, [], True)).fit().rsquared, 3) for t in COST}
# common support (state cells) logistic: logL + model on the opportunities in all-five common cells
_cs_cells = [c for c in MAIN.cell_state.unique() if MAIN[MAIN.cell_state == c].model.nunique() == 5]
CONTRAST['main_state_support'] = {'L_model': contrasts(MAIN[MAIN.cell_state.isin(_cs_cells)], ['logL'])}

# ----------------------------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------------------------
RESULT = dict(
    notes=dict(bands=dict(L=L_LAB, round=R_LAB, runway=W_LAB),
               runway='tokens at the first TALK-before-SOLVE tick / own model mean talk spend per agent-round (w4)',
               cost_terms='log_own = own mean talk spend per round in earlier rounds; log_prev = own talk spend in the '
                          'previous round; round 1 filled with the model mean; log_run = log runway',
               contrast_sign='pair key X-Y = X minus Y; X is the model with lower C in body Table 1'),
    G_support=SUPPORT, H_loso_main=LOSO_MAIN, H_loso_all4_armFE=LOSO_ALL, I_contrasts=CONTRAST,
    I_cost_between_model_R2=COST_BETWEEN, I_cost_between_model_R2_all4=COST_BETWEEN_ALL,
)
OUT_JSON.write_text(json.dumps(RESULT, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))

# ----------------------------------------------------------------------------------------------
# Tables (booktabs, Korean headers)
# ----------------------------------------------------------------------------------------------
TAB = VAL / 'ko/parts'
PAIR_KEYS = [f'{b}-{a}' for a, b in PAIRS]
DASH = '--'


def neg(t):
    return re.sub(r'-(?=\d)', '$-$', t)


def _pp(rec):
    if rec.get('diff') is None:
        return DASH
    star = r'$^{*}$' if rec['holm_p'] < .05 else ''
    return f"{rec['diff']:+.1f} [{rec['ci'][0]:.1f}, {rec['ci'][1]:.1f}]{star}"


def _holm(rec):
    return DASH if rec.get('holm_p') is None else f"{rec['holm_p']:.3f}"


def tab_support():
    S = SUPPORT
    L = [r'\begin{tabular}{lrrrrrrrr}', r'\toprule',
         r' & \multicolumn{4}{c}{기본 조건 50판} & \multicolumn{4}{c}{네 조건 200판(칸은 조건 안)} \\',
         r'\cmidrule(lr){2-5}\cmidrule(l){6-9}',
         r' & \multicolumn{2}{c}{여유$\times$라운드 칸} & \multicolumn{2}{c}{$+$활주 칸} & \multicolumn{2}{c}{여유$\times$라운드 칸} & \multicolumn{2}{c}{$+$활주 칸} \\',
         r'\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(l){8-9}',
         r'쌍 & 차이(\%p) & Holm $p$ & 차이(\%p) & Holm $p$ & 차이(\%p) & Holm $p$ & 차이(\%p) & Holm $p$ \\', r'\midrule']
    for k in PAIR_KEYS:
        cells = []
        for arm in ['main', 'all4']:
            for c in ['state', 'cost']:
                r = S[arm][c]['pairs'][k]
                cells += [_pp(r), _holm(r)]
        L.append(k.replace('-', r' $-$ ') + ' & ' + neg(' & '.join(cells)) + r' \\')
    L += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'w4_tab_support.tex').write_text('\n'.join(L) + '\n')


SPEC_KO = {'null': '상수만', 'model': '모델', 'L': r'$\log L$', 'L_cost': r'$\log L$ $+$ 비용',
           'L_model': r'$\log L$ $+$ 모델', 'L_own_model': r'$\log L$ $+$ 자기 이전 비용 $+$ 모델',
           'L_cost_model': r'$\log L$ $+$ 비용 $+$ 모델', 'run_model': r'$\log$ 활주 $+$ 모델'}


def tab_loso():
    L = [r'\begin{tabular}{lrrrrrrr}', r'\toprule',
         r' & \multicolumn{4}{c}{기본 조건(960 기회, 61 이탈)} & \multicolumn{3}{c}{네 조건, 조건 효과 포함(3,670, 312)} \\',
         r'\cmidrule(lr){2-5}\cmidrule(l){6-8}',
         r'설명 변수 & 로그 손실 & Brier & 보정 기울기 & 십분위 오차(\%p) & 로그 손실 & Brier & 보정 기울기 \\', r'\midrule']
    for k in ['null', 'model', 'L', 'L_cost', 'L_model', 'L_own_model', 'L_cost_model', 'run_model']:
        a, b = LOSO_MAIN['specs'][k], LOSO_ALL['specs'][k]
        sl_a = DASH if k == 'null' else f"{a['calib_slope']:.2f}"
        L.append(f"{SPEC_KO[k]} & {a['logloss']:.4f} & {a['brier']:.4f} & {sl_a} & {a['ece_decile']:.2f} & "
                 f"{b['logloss']:.4f} & {b['brier']:.4f} & {b['calib_slope']:.2f} \\\\")
    L += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'w4_tab_loso.tex').write_text('\n'.join(L) + '\n')


def tab_contrast():
    cols = [('main', 'L_model'), ('main', 'L_own_model'), ('main', 'L_cost_model'), ('all4', 'L_model'), ('all4', 'L_cost_model')]
    L = [r'\begin{tabular}{lrrrrr}', r'\toprule',
         r' & \multicolumn{3}{c}{기본 조건} & \multicolumn{2}{c}{네 조건(조건 효과)} \\', r'\cmidrule(lr){2-4}\cmidrule(l){5-6}',
         r'쌍 & $\log L$ $+$ 모델 & \shortstack{$+$자기 이전\\비용} & $+$비용 3항 & $\log L$ $+$ 모델 & $+$비용 3항 \\', r'\midrule']
    for k in PAIR_KEYS:
        cells = []
        for arm, sp in cols:
            r = CONTRAST[arm][sp]['pairs'][k]
            star = r'$^{*}$' if r['holm_p'] < .05 else ''
            cells.append(f"{r['logodds']:+.2f} [{r['ci'][0]:.2f}, {r['ci'][1]:.2f}]{star}")
        L.append(k.replace('-', r' $-$ ') + ' & ' + neg(' & '.join(cells)) + r' \\')
    L.append(r'\midrule')
    w = [CONTRAST[arm][sp]['wald'] for arm, sp in cols]
    L.append(r'모델 효과 Wald & ' + ' & '.join(f"$\\chi^2_{{{x['df']}}}={x['stat']:.1f}$, $p={x['p']:.3f}$" if x['p'] >= .001
                                            else f"$\\chi^2_{{{x['df']}}}={x['stat']:.1f}$, $p<0.001$" for x in w) + r' \\')
    L += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'w4_tab_contrast.tex').write_text('\n'.join(L) + '\n')


for _fn in [tab_support, tab_loso, tab_contrast]:
    _fn()

# ----------------------------------------------------------------------------------------------
# Figure: out-of-sample calibration and common-support contrasts
# ----------------------------------------------------------------------------------------------
INK, MUTED = '#2b2b2b', '#6b6b6b'


def fig_validation():
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={'width_ratios': [1, 1.25]})
    a = ax[0]
    a.plot([0, 60], [0, 60], color=MUTED, lw=0.8, ls='--')
    for k, col, mk in [('L', '#4C6FB0', 'o'), ('L_model', '#C0504D', 's'), ('L_cost_model', '#D9B26A', '^')]:
        dec = LOSO_MAIN['specs'][k]['deciles']
        a.plot([c['mean_pred'] for c in dec], [c['obs'] for c in dec], marker=mk, color=col, lw=1.2, ms=5,
               label=f"{SPEC_KO[k]} (로그 손실 {LOSO_MAIN['specs'][k]['logloss']:.3f})")
    a.set_xlabel('시드 제외 예측 이탈 확률 (%, 십분위 평균)'); a.set_ylabel('관측 이탈 비율 (%)')
    a.set_xlim(0, 60); a.set_ylim(0, 60); a.grid(color='#eeeeee', lw=0.6)
    a.legend(frameon=False, fontsize=7.5, loc='upper left')
    a.set_title('(a) 시드 제외 보정 (기본 조건 960 기회)', loc='left', fontsize=9.5)
    b = ax[1]
    ys = np.arange(len(PAIR_KEYS))
    for j, (arm, c, col, lab) in enumerate([('main', 'state', '#4C6FB0', '기본, 여유x라운드'),
                                             ('all4', 'state', '#C0504D', '네 조건, 여유x라운드'),
                                             ('all4', 'cost', '#D9B26A', '네 조건, +활주')]):
        first = True
        for i, k in enumerate(PAIR_KEYS):
            r = SUPPORT[arm][c]['pairs'][k]
            if r.get('diff') is None:
                continue
            y = i + (j - 1) * 0.25
            filled = r['holm_p'] < .05
            b.errorbar(r['diff'], y, xerr=[[r['diff'] - r['ci'][0]], [r['ci'][1] - r['diff']]], fmt='o', ms=4.5,
                       color=col, mfc=col if filled else 'white', lw=1, capsize=1.5, label=lab if first else None)
            first = False
    b.axvline(0, color=MUTED, lw=0.8)
    b.set_yticks(ys, [k.replace('-', ' - ') for k in PAIR_KEYS], fontsize=8); b.invert_yaxis()
    b.set_xlabel('공통 칸의 이탈 비율 차이 (%p, 겹침 가중, 시드 재표집 95% 구간)')
    b.grid(axis='x', color='#eeeeee', lw=0.6)
    b.legend(frameon=False, fontsize=7.5, loc='upper center', bbox_to_anchor=(0.45, -0.16), ncol=3)
    b.set_title('(b) 공통 상태 범위의 쌍 비교 (채운 점: Holm p<0.05)', loc='left', fontsize=9.5)
    fig.tight_layout()
    for ext in ['pdf', 'png']:
        fig.savefig(VAL / f'figures/w4b_validation.{ext}', dpi=200)
    plt.close(fig)


fig_validation()
print('wrote', OUT_JSON, 'figures/w4b_validation.pdf', 'ko/parts/w4_tab_{support,loso,contrast}.tex')
