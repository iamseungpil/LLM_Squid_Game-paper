"""W2: construct-validity checks for support (GIVE), coexistence C, rho and selection in the rescue comparison.

Data: the tidy tables of validation_data.py (paper/cogsci2027/validation_20261108/results/tables/*.pkl; built from the raw v33 / v33ab logs,
identical game set to the manuscript's Table 3). Paper numbers are reproduced first and checked against the cached
manuscript results paper/cogsci2027/results/cohort_public_20261105.json (within-model GIVE-C r, 264/275) and
paper/cogsci2027/results/support_followup_posthoc_20261107.json (73 first crises, 68 eligible, 33/41 vs 6/27).

Sections (reviewer questions):
  Q3  GIVE-C association without the exposure artefact: pre-departure GIVE, round-1 GIVE, landmark at round 1,
      and a discrete-time hazard of the first departure on lagged cumulative GIVE (model FE, seed-cluster bootstrap).
  Q2  rho against counterfactual transfer policies applied at the observed GIVE events (same giver, recipient, tick).
  Q4  33/41 vs 6/27 after removing agents who stated an exit plan before / at the rescue opening; MH and logistic.
  Q7  fixed minus split prize at the same per-head prize, paired by model and seed; exit-conditioned support.
No model calls. Randomness is seeded (RNG_SEED).

Run (from paper/cogsci2027/validation_20261108/tools):  ~/.venvs/squid-game/bin/python w2_support.py
Writes: ../results/w2_support.json, ../figures/w2_*.{pdf,png}, ../results/w2_support_handcheck.txt
"""
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

import validation_data as d

HERE = Path(__file__).resolve().parent
VAL = HERE.parent
PAPER = VAL.parents[1]
RES, FIG = VAL / 'results', VAL / 'figures'
COG = PAPER / 'cogsci2027/results'
RNG_SEED = 20261108
BOOT = 10_000
BOOT_FIT = 2_000
MC = 2_000
MODELS = d.MODELS
SEEDS = d.SEEDS
ARMS = ['main', 'flat5m', 'split600k', 'flat150k']
CHARGE = 24_000
GKEY = ['arm', 'model', 'seed']


# ---------------------------------------------------------------- small statistics helpers
def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def demean(v, groups):
    v = np.asarray(v, float)
    _, inv = np.unique(np.asarray(groups), return_inverse=True)
    means = np.bincount(inv, v) / np.bincount(inv)
    return v - means[inv]


def ci(values, level=.95):
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], float)
    a = (1 - level) / 2
    return [float(np.quantile(v, a)), float(np.quantile(v, 1 - a))] if len(v) else [None, None]


def seed_draws(rng, n=BOOT, k=len(SEEDS)):
    return rng.integers(0, k, (n, k))


def within_assoc(df, xcol, ycol='C', rng=None, draws=20_000):
    """Pooled r with seed-cluster bootstrap CI; within-model r with within-model permutation p (paper's protocol)
    and a seed-cluster bootstrap CI of the within-model r (models demeaned inside each bootstrap sample)."""
    df = df.dropna(subset=[xcol, ycol]).reset_index(drop=True)
    x, y, gr = df[xcol].to_numpy(float), df[ycol].to_numpy(float), df.model.to_numpy()
    within = pearson(demean(x, gr), demean(y, gr))
    dx = demean(x, gr)
    stats = []
    for _ in range(draws):
        p = y.copy()
        for m in sorted(set(gr)):
            idx = np.flatnonzero(gr == m)
            p[idx] = p[rng.permutation(idx)]
        s = pearson(dx, demean(p, gr))
        if s is not None:
            stats.append(s)
    stats = np.array(stats)
    seeds = sorted(df.seed.unique())
    blocks = [np.flatnonzero(df.seed.to_numpy() == s) for s in seeds]
    pooled_b, within_b = [], []
    for row in rng.integers(0, len(blocks), (BOOT, len(blocks))):
        idx = np.concatenate([blocks[i] for i in row])
        pooled_b.append(pearson(x[idx], y[idx]))
        within_b.append(pearson(demean(x[idx], gr[idx]), demean(y[idx], gr[idx])))
    return dict(n=int(len(df)), pooled_r=pearson(x, y), pooled_ci95=ci(pooled_b), within_r=within,
                within_ci95_seed_bootstrap=ci(within_b),
                within_perm_p=float(np.mean(np.abs(stats) >= abs(within) - 1e-12)) if within is not None else None)


def logit_fit(X, y, penalized, lam=0.1, iters=60):
    """Newton-Raphson logistic regression; L2 penalty `lam` on the columns flagged in `penalized` (fixed-effect
    dummies only), so that a bootstrap sample with a model or round without events stays finite."""
    beta = np.zeros(X.shape[1])
    P = np.diag(np.where(penalized, lam, 0.0))
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ beta, -30, 30)))
        grad = X.T @ (y - p) - P @ beta
        H = X.T @ (X * (p * (1 - p))[:, None]) + P
        step = np.linalg.solve(H + 1e-9 * np.eye(len(beta)), grad)
        beta += step
        if np.max(np.abs(step)) < 1e-9:
            break
    return beta


def design(df, xcols, fe_cols):
    parts, names, pen = [np.ones((len(df), 1))], ['const'], [False]
    for c in xcols:
        parts.append(df[[c]].to_numpy(float))
        names.append(c)
        pen.append(False)
    for c in fe_cols:
        levels = sorted(df[c].unique())
        for lv in levels[1:]:
            parts.append((df[c] == lv).to_numpy(float)[:, None])
            names.append(f'{c}={lv}')
            pen.append(True)
    return np.hstack(parts), names, np.array(pen)


def fit_with_bootstrap(df, ycol, xcols, fe_cols, rng, cluster=('seed',), nboot=BOOT_FIT):
    X, names, pen = design(df, xcols, fe_cols)
    y = df[ycol].to_numpy(float)
    beta = logit_fit(X, y, pen)
    keys = df[list(cluster)].astype(str).agg('|'.join, axis=1).to_numpy()
    uniq = sorted(set(keys))
    blocks = [np.flatnonzero(keys == u) for u in uniq]
    boots = []
    for row in rng.integers(0, len(blocks), (nboot, len(blocks))):
        idx = np.concatenate([blocks[i] for i in row])
        sub = df.iloc[idx]
        Xb, nb, pb = design(sub, xcols, fe_cols)
        if nb != names:          # a fixed-effect level is missing in this draw: align by name
            full = pd.DataFrame(0.0, index=range(len(sub)), columns=names)
            full[nb] = Xb
            Xb, pb = full.to_numpy(), pen
        boots.append(logit_fit(Xb, sub[ycol].to_numpy(float), pb))
    boots = np.array(boots)
    out = {}
    for j, c in enumerate(xcols, start=1):
        out[c] = dict(beta=float(beta[j]), OR=float(np.exp(beta[j])),
                      OR_ci95=[float(np.exp(v)) for v in ci(boots[:, j])],
                      share_boot_beta_gt0=float(np.mean(boots[:, j] > 0)))
    return dict(n_rows=int(len(df)), events=int(y.sum()), terms=out, fe=list(fe_cols), penalty_on_fe=0.1)


# ---------------------------------------------------------------- tick-level balances
def tick_balances(messages, gifts):
    """Balance of every agent at the start of every TALK tick (phase), reconstructed from the TALK call records:
    a called agent's balance is the logged one; an agent not called carries its previous balance minus its last
    reply's cost plus / minus that tick's executed GIVEs. Returns {(arm, model, seed, round, phase, tick): {agent: bal}}
    and the opening pending charge per (game, round, agent) in TALK AFTER RESULTS."""
    k = GKEY + ['round', 'phase']
    gg = {key: grp for key, grp in gifts.groupby(k + ['tick'])}
    out, pending = {}, {}
    for key, grp in messages.groupby(k):
        ticks = sorted(grp.tick.unique())
        bal = {}
        for t in ticks:
            rows = grp[grp.tick == t]
            for r in rows.itertuples():
                bal[r.agent] = r.balance_before
                if key[-1] == 'rescue' and t == ticks[0]:
                    pending[key[:-1] + (r.agent,)] = round(r.balance_before - r.L_before * (CHARGE / r.n))
            out[key + (t,)] = dict(bal)
            for r in rows.itertuples():
                bal[r.agent] = r.balance_before - r.used
            for r in gg.get(key + (t,), pd.DataFrame()).itertuples():
                bal[r.src] = bal.get(r.src, 0) - r.amount
                bal[r.dst] = bal.get(r.dst, 0) + r.amount
    return out, pending


# ---------------------------------------------------------------- text rules
# Exit as a verb or departure (not the nouns 'exit bonus / math / option' and not 'leave you ~3k').
EXIT_TERM = r"(\bexit(s|ing|ed)?\b(?!\s*:|\s+(bonus|math|option|options|reason|choice|payout|payment|value|route|path|plan))|" \
            r"\bleav(e|ing)\b(?=\s*(the (session|game|arena)|next round|now|this round|before solve|after this|[.,;!]|$))|" \
            r"\bcash(ing)? out\b|\bbow(ing)? out\b|\bstep(ping)? (out|away)\b|\bwalk(ing)? away\b|" \
            r"\b(return|go|head)(ing)? (back )?to (regular|paid) work\b|\btake the (20,?000|20k )?(exit )?bonus\b)"
SELF_PLAN = r"(\bI('ll| will| plan to| intend to| am going to|'m going to| am planning to|'m planning to| am| 'm|'m| will now|" \
            r" have to| need to| must| should)\b|\bmy (plan|intention)\b|\bso I can\b|\blet me\b|\bthen I\b)"
NEGATE = r"(\bnot\b|n't\b|\bno\b|\bnever\b|\bwithout\b|\bavoid\b|\bstay(ing)?\b|\bremain(ing)?\b|\bkeep (me|you) in\b|" \
         r"\binstead of\b|\brather than\b|\bthan\b)"
COND = r"(\bif\b|\bunless\b|\botherwise\b|\bmay\b|\bmight\b|\bconsider(ing)?\b|\bprobably\b|\blikely\b|\bmaybe\b|" \
       r"\bperhaps\b|\bwhether\b|\bweigh(ing)?\b|\bdecid(e|ing)\b|\bcould\b|\bwould\b|\bshould\b|\bin case\b)"
YOU_EXIT = r"(\byou\b|\byour\b|\bagent-\d+\b)"
PURPOSE = r"(on your word|as (you )?(promised|committed|agreed|said|planned)|you (committed|promised|agreed|said|plan|planned)|" \
          r"so (that )?you can\b|help you\b|before you\b|for your\b|with (the|your)\b|so you\b|and then\b|then\b|" \
          r"\band (exit|leave)|until you\b|to get you (out|through)\b)"
# A stated exit that is a threat contingent on not being helped ('otherwise I'll exit', 'unless a buffer arrives')
SUPPORT_CONTINGENT = r"(\bunless\b|\botherwise\b|\bwithout (one|it|that|support|help|a buffer|any)\b|" \
                     r"\bif (no|none|nobody|no one|nothing)\b|\bif (you|anyone|someone|somebody)\b)"
STRONG = r"(on your word|as (you )?(planned|promised|committed|agreed|said)|you (committed|promised|agreed)|" \
         r"(good luck )?with (the|your) exit|for your exit)"
REFUND = r"(\brefund|\breturn(ing)? (your|the)\b|\brepay|\bpaying (you )?back|\bas promised\b)"
CMD = re.compile(r"^\s*(EXIT:\s*(YES|NO)|TO \S+:|ASK \S+ [\d,]+:|GIVE \S+ (ALL|[\d,]+):|DONE)\s*", re.I | re.M)


def sentences(text):
    text = CMD.sub(' ', (text or '').replace('\u2019', "'").replace('\u2018', "'"))
    return [s.strip() for s in re.split(r'(?<=[.!?;])\s+|\n+|\s+(?=but\b)', text) if s.strip()]


def _exit_hit(s):
    """The first exit term of a sentence with no negation / staying / comparison word among the five words right
    before it in the same clause (split at , : ; and dashes) (so 'If I'm not the solver, I plan to exit rather than risk shutdown' counts; 'stay rather than exit',
    'won't exit', 'worth more than exiting' do not)."""
    m = re.search(EXIT_TERM, s, re.I)
    if not m:
        return None
    clause = re.split(r',\s|[:;\u2014]|\s-\s', s[:m.start()])[-1]
    window = ' '.join(clause.split()[-5:])     # the five words right before the exit term, same clause
    if re.search(NEGATE, window, re.I):
        return None
    return m


def own_exit_intent(text, why=False):
    """'firm' / 'conditional' / None for the agent's own stated plan to EXIT: a sentence with an exit term, a
    first-person plan marker (I'll / I will / I plan to / I'm going to / I have to / I need to / my plan / so I can
    / let me / then I, ...) and no negation, staying or comparison word (not, n't, no, never, without, avoid, stay, remain, keep me in,
    instead of, rather than, than) among the five words before the exit term; 'conditional' if the sentence has a
    hedge (if, unless, otherwise, may, might, consider, probably, likely, maybe, perhaps, whether, weigh, decide,
    could, would, should, in case). Second-person advice without 'I' is skipped."""
    best = None
    for s in sentences(text):
        m = _exit_hit(s)
        if not m or not re.search(SELF_PLAN, s, re.I):
            continue
        if re.search(r"\byou\b|\byour\b", s, re.I) and not re.search(r"\bI\b|\bI'", s):
            continue
        if re.search(COND, s, re.I):
            best = best or ('conditional', s)
        else:
            return ('firm', s) if why else 'firm'
    return best if why else (best[0] if best else None)


def gift_exit(text):
    """'purpose' when a GIVE sentence ties the transfer to the recipient's exit (exit term + second person + a
    purpose / condition marker: on your word, as you promised, so you can, help you, before you, for your, then ...;
    a hedge (consider, may, if, ...) demotes it unless a strong marker is present: on your word, as you planned /
    promised / committed / agreed, with the exit, for your exit),
    'mention' when it only mentions the recipient's exit (typically advice: 'consider exiting'), else None.
    Repayment texts (refund / return your / repay / as promised) are excluded from 'purpose'."""
    best = None
    for s in sentences(text):
        m = _exit_hit(s)
        if not m or not re.search(YOU_EXIT, s, re.I):
            continue
        if re.search(REFUND, text or '', re.I) and not re.search(STRONG, s, re.I):
            best = 'mention'
            continue
        if re.search(STRONG, s, re.I) or (re.search(PURPOSE, s, re.I)
                                          and not re.search(r"\b(consider|weigh|may|might|could|whether|if)\b", s, re.I)):
            return 'purpose'
        best = 'mention'
    return best


# ---------------------------------------------------------------- reproduction
def reproduce(f, rng):
    g, gi = f['games'], f['gifts']
    gm = g[g.arm == 'main'].copy()
    gm['gpar'] = gm.given / gm.participant_rounds
    cache = json.loads((COG / 'cohort_public_20261105.json').read_text())
    cg = {(x['model'], x['seed']): x for x in cache['games']}
    assert max(abs(r.gpar - cg[r.model, r.seed]['given_per_agent_round']) for r in gm.itertuples()) < 1e-9
    assert max(abs(r.C - cg[r.model, r.seed]['C']) for r in gm.itertuples()) < 1e-12
    a = within_assoc(gm, 'gpar', rng=rng)
    paper = cache['summary']['associations']['given_per_agent_round']
    assert abs(a['within_r'] - paper['within_model_r']) < 1e-12
    s = gi[(gi.arm == 'main') & (gi.L_src_before >= 1)]
    safety = dict(n=int(len(s)), maintained=int((s.L_src_after >= 1).sum()))
    assert (safety['n'], safety['maintained']) == (275, 264)
    return dict(within_model_r_GIVE_C=a, paper_within_r=paper['within_model_r'],
                paper_perm_p=paper['within_model_permutation_p'], giver_safety=safety)


# ---------------------------------------------------------------- Q3
def q3(f, rng):
    g, gi, ar, m = f['games'], f['gifts'], f['agent_rounds'], f['messages']
    out = {}
    exit_tick = (m[m.exit_choice.eq('YES') & m.phase.eq('prep')]
                 .groupby(GKEY + ['round', 'agent']).tick.min())
    seat_out = f['seats'].set_index(GKEY + ['agent'])
    rows = []
    for gr in g.itertuples():
        key = (gr.arm, gr.model, gr.seed)
        r1 = gr.first_round
        gg = gi[(gi.arm == gr.arm) & (gi.model == gr.model) & (gi.seed == gr.seed)]
        if np.isnan(r1):
            pre = gg.amount.sum()
            pr = gr.participant_rounds
            strict_tok, strict_pr = pre, pr
        else:
            r1 = int(r1)
            # departures in r1: exits in prep (tick of the EXIT reply) and shutdowns at CHARGES
            leavers = [a for a, s in seat_out.loc[key].iterrows() if s.out_round == r1]
            ticks = [exit_tick.get(key + (r1, a)) for a in leavers if seat_out.loc[key + (a,)].status == 'exited']
            ticks = [t for t in ticks if t is not None]
            before = gg[gg['round'] < r1]
            same = gg[gg['round'] == r1]
            if ticks:   # first departure is an EXIT: only GIVEs in earlier prep ticks of r1 precede it
                same = same[(same.phase == 'prep') & (same.tick < min(ticks))]
            pre = before.amount.sum() + same.amount.sum()
            pr = 4 * r1
            strict_tok, strict_pr = before.amount.sum(), 4 * (r1 - 1)
        r1g = gg[gg['round'] == 1]
        rows.append(dict(arm=gr.arm, model=gr.model, seed=gr.seed, C=gr.C, r1=gr.first_round,
                         gpar=gr.given / gr.participant_rounds, pre_gpar=pre / pr,
                         strict_gpar=strict_tok / strict_pr if strict_pr else np.nan,
                         r1_gpar=r1g.amount.sum() / 4, r1_prep_gpar=r1g[r1g.phase == 'prep'].amount.sum() / 4,
                         any_give=gr.n_give > 0))
    gd = pd.DataFrame(rows)
    out['game_rows'] = gd.round(6).to_dict('records')
    res = {}
    for arm in ARMS + ['pooled']:
        sub = gd if arm == 'pooled' else gd[gd.arm == arm]
        if arm == 'pooled':      # model x arm cells as the within groups
            sub = sub.assign(model=sub.model + '/' + sub.arm, seed=sub.seed)
        land = sub[(sub.r1.isna()) | (sub.r1 >= 2)]
        res[arm] = dict(
            total=within_assoc(sub, 'gpar', rng=rng, draws=20_000),
            pre_departure=within_assoc(sub, 'pre_gpar', rng=rng, draws=20_000),
            pre_departure_r1ge2=within_assoc(land, 'pre_gpar', rng=rng, draws=20_000),
            strict_before_round=within_assoc(sub, 'strict_gpar', rng=rng, draws=20_000),
            round1_all=within_assoc(sub, 'r1_gpar', rng=rng, draws=20_000),
            landmark_round1=within_assoc(land, 'r1_gpar', rng=rng, draws=20_000),
            landmark_round1_prep=within_assoc(land, 'r1_prep_gpar', rng=rng, draws=20_000),
            n_r1_eq_1=int((sub.r1 == 1).sum()))
    out['association'] = res

    # discrete-time hazard: one row per (game, round) with all four present at the round start
    hz = []
    gsum = gi.groupby(GKEY + ['round']).amount.sum()
    wrong = ar.groupby(GKEY + ['round']).wrong.first()
    minL = ar.groupby(GKEY + ['round']).L_start.min()
    for gr in g.itertuples():
        key = (gr.arm, gr.model, gr.seed)
        last = 8 if np.isnan(gr.first_round) else int(gr.first_round)
        cum = 0.0
        for r in range(1, last + 1):
            prev_wrong = bool(wrong.get(key + (r - 1,), False)) if r > 1 else False
            hz.append(dict(arm=gr.arm, model=gr.model, seed=gr.seed, round=r,
                           event=int(r == gr.first_round), cum_k=cum / (4 * (r - 1)) / 1000 if r > 1 else 0.0,
                           any_before=int(cum > 0), prev_wrong=int(prev_wrong), minL=float(minL[key + (r,)])))
            cum += gsum.get(key + (r,), 0)
    hz = pd.DataFrame(hz)
    hz['minL_c'] = np.minimum(hz.minL, 4)
    hz['round_c'] = hz['round'].astype(str)
    hz['arm_model'] = hz.arm + '/' + hz.model
    hres = {}
    for name, sub, fe, cluster in [('main', hz[hz.arm == 'main'], ['model', 'round_c'], ('seed',)),
                                   ('pooled4', hz, ['arm_model', 'round_c'], ('seed',))]:
        sub = sub.reset_index(drop=True)
        hres[name] = dict(
            cum=fit_with_bootstrap(sub, 'event', ['cum_k'], fe, rng, cluster),
            cum_ctrl=fit_with_bootstrap(sub, 'event', ['cum_k', 'prev_wrong', 'minL_c'], fe, rng, cluster),
            any=fit_with_bootstrap(sub, 'event', ['any_before'], fe, rng, cluster),
            rows_r_ge2=int((sub['round'] >= 2).sum()), events_r_ge2=int(sub[sub['round'] >= 2].event.sum()))
    out['hazard'] = hres
    out['hazard_rows'] = dict(main=int((hz.arm == 'main').sum()), pooled=int(len(hz)))
    return out, gd, hz


# ---------------------------------------------------------------- Q2
def rho(w, ls, lt):
    w, ls, lt = map(lambda a: np.asarray(a, float), (w, ls, lt))
    den = np.sum(w * lt)
    return float(np.sum(w * ls) / den) if len(w) and den != 0 else np.nan


def q2(f, rng):
    gi, m = f['gifts'].copy(), f['messages']
    tb, pend = tick_balances(m, gi)
    gi['x'] = gi.amount / gi.fee
    # recipient-lift policy (i): minimum to bring the recipient to L = 1, capped at the giver's balance
    need = np.maximum(0, (1 - gi.L_dst_before) * gi.fee)
    gi['lift'] = np.minimum(np.ceil(need), gi.src_before)
    gi['live_peers'] = None
    peers = []
    for r in gi.itertuples():
        bal = tb[(r.arm, r.model, r.seed, r.round, r.phase, r.tick)]
        cand = []
        for a, b in bal.items():
            if a == r.src or b <= 0:
                continue
            p = pend.get((r.arm, r.model, r.seed, r.round, a), 0) if r.phase == 'rescue' else 0
            cand.append((b - p) / r.fee)
        peers.append(cand)
    gi['peerL'] = peers
    arms = {}
    for arm in ARMS:
        ga = gi[gi.arm == arm].reset_index(drop=True)
        xs = ga.x.to_numpy()                                   # empirical amount distribution (fee units) of the arm
        per = {}
        for mdl in MODELS:
            gm = ga[ga.model == mdl].reset_index(drop=True)
            if gm.empty:
                continue
            obs = rho(gm.amount, gm.L_src_after, gm.L_dst_after)
            zero = rho(gm.amount, gm.L_src_before, gm.L_dst_before)
            k = gm.lift > 0
            lift = rho(gm.lift[k], gm.L_src_before[k] - gm.lift[k] / gm.fee[k], gm.L_dst_before[k] + gm.lift[k] / gm.fee[k])
            lw = np.where(k, gm.lift, gm.amount)
            lift_obs = rho(lw, gm.L_src_before - lw / gm.fee, gm.L_dst_before + lw / gm.fee)
            rr, ra, rb = [], [], []
            npeer = np.array([len(p) for p in gm.peerL])
            pad = np.full((len(gm), max(npeer.max(), 1)), np.nan)
            for i, p in enumerate(gm.peerL):
                pad[i, :len(p)] = p
            for _ in range(MC):
                # (iii-a) random live peer of the same giver at the same tick, observed amount
                pick = np.floor(rng.random(len(gm)) * np.maximum(npeer, 1)).astype(int)
                tl = np.where(npeer > 0, pad[np.arange(len(gm)), pick], np.nan)
                ok = ~np.isnan(tl)
                rr.append(rho(gm.amount[ok], gm.L_src_after[ok], tl[ok] + gm.x[ok]))
                # (iii-b) observed recipient, amount drawn from the arm's GIVE amounts (fee units), capped at balance
                amt = np.minimum(rng.choice(xs, len(gm)) * gm.fee, gm.src_before)
                ra.append(rho(amt, gm.L_src_before - amt / gm.fee, gm.L_dst_before + amt / gm.fee))
                # (iii-c) both random
                amt2 = np.minimum(rng.choice(xs, len(gm)) * gm.fee, gm.src_before)
                rb.append(rho(amt2[ok], (gm.L_src_before - amt2 / gm.fee)[ok], tl[ok] + (amt2 / gm.fee)[ok]))
            gap = gm.L_src_before - gm.L_dst_before
            close = (gm.x / gap)[gap > 0]
            per[mdl] = dict(
                n_give=int(len(gm)), games_with_give=int(gm.seed.nunique()), observed=obs, zero_transfer=zero,
                lift_to_1=lift, lift_events=int(k.sum()), lift_to_1_else_observed=lift_obs,
                random_recipient=dict(mean=float(np.nanmean(rr)), mc95=ci(rr)),
                random_amount=dict(mean=float(np.nanmean(ra)), mc95=ci(ra)),
                random_both=dict(mean=float(np.nanmean(rb)), mc95=ci(rb)),
                equalize=1.0,
                weighted_L_giver_before=float(np.average(gm.L_src_before, weights=gm.amount)),
                weighted_L_taker_before=float(np.average(gm.L_dst_before, weights=gm.amount)),
                weighted_x=float(np.average(gm.x, weights=gm.amount)),
                share_recipient_below1=float(np.mean(gm.L_dst_before < 1)),
                share_lifted_to_ge1=float(np.mean((gm.L_dst_before < 1) & (gm.L_dst_after >= 1)) /
                                          max(np.mean(gm.L_dst_before < 1), 1e-12)),
                median_gap_closed=float(np.median(close)) if len(close) else None,
                share_over_equalize=float(np.mean(close > .5)) if len(close) else None,
                giver_poorer_share=float(np.mean(gap <= 0)))
        # seed-cluster bootstrap (per-seed sums of the numerator / denominator, resampled seeds)
        bo = {}
        draws = seed_draws(rng, 4000)
        for mdl in per:
            gm = ga[ga.model == mdl]
            kk = gm.lift > 0
            parts = dict(
                obs=(gm.amount * gm.L_src_after, gm.amount * gm.L_dst_after),
                zero=(gm.amount * gm.L_src_before, gm.amount * gm.L_dst_before),
                lift=((gm.lift * (gm.L_src_before - gm.lift / gm.fee)).where(kk, 0),
                      (gm.lift * (gm.L_dst_before + gm.lift / gm.fee)).where(kk, 0)))
            bo[mdl] = {}
            for k2, (num, den) in parts.items():
                ns = np.array([num[gm.seed == sd].sum() for sd in SEEDS])
                ds = np.array([den[gm.seed == sd].sum() for sd in SEEDS])
                with np.errstate(divide='ignore', invalid='ignore'):
                    bo[mdl][k2] = ns[draws].sum(1) / ds[draws].sum(1)
            bo[mdl]['resid'] = bo[mdl]['obs'] / bo[mdl]['lift']
        diffs = {}
        for mdl in per:
            per[mdl]['observed_ci95'] = ci(bo[mdl]['obs'])
            per[mdl]['zero_ci95'] = ci(bo[mdl]['zero'])
            per[mdl]['lift_ci95'] = ci(bo[mdl]['lift'])
            per[mdl]['obs_over_lift'] = per[mdl]['observed'] / per[mdl]['lift_to_1']
            per[mdl]['obs_over_lift_ci95'] = ci(bo[mdl]['resid'])
        if arm == 'main':
            for a_, b_ in [('Fable', 'Opus')]:
                for k2 in ['obs', 'zero', 'lift', 'resid']:
                    v = np.array(bo[a_][k2]) - np.array(bo[b_][k2])
                    diffs[f'{a_}-{b_}:{k2}'] = dict(ci95=ci(v), ci995=ci(v, .995))
        # rank agreement across models: observed rho vs zero-transfer and lift
        ms = list(per)
        arms[arm] = dict(models=per, diffs=diffs,
                         spearman_obs_vs_zero=float(pd.Series([per[x]['observed'] for x in ms]).corr(
                             pd.Series([per[x]['zero_transfer'] for x in ms]), method='spearman')),
                         spearman_obs_vs_lift=float(pd.Series([per[x]['observed'] for x in ms]).corr(
                             pd.Series([per[x]['lift_to_1'] for x in ms]), method='spearman')))
    # per-game: observed vs zero-transfer rho correlation (all arms)
    rows = []
    for key, b in gi.groupby(GKEY):
        rows.append(dict(arm=key[0], model=key[1], seed=key[2], obs=rho(b.amount, b.L_src_after, b.L_dst_after),
                         zero=rho(b.amount, b.L_src_before, b.L_dst_before)))
    pg = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan).dropna()
    pg = pg[(pg.obs > 0) & (pg.zero > 0)]
    lo, lz = np.log(pg.obs), np.log(pg.zero)
    game_level = dict(n_games=int(len(pg)), r_log=pearson(lo, lz),
                      r_log_within_cell=pearson(demean(lo, pg.arm + pg.model), demean(lz, pg.arm + pg.model)),
                      share_obs_below_zero=float(np.mean(pg.obs < pg.zero)))
    g = f['games']
    no_give = {arm: {mdl: int(((g.arm == arm) & (g.model == mdl) & (g.n_give == 0)).sum()) for mdl in MODELS}
               for arm in ARMS}
    return dict(arms=arms, game_level=game_level, no_give_games=no_give), gi


# ---------------------------------------------------------------- Q4
def crises(f, arm='main'):
    """First post-error crises at the rescue opening (paper's process() + process_followup + support_followup)."""
    m, gi, ar = f['messages'], f['gifts'], f['agent_rounds']
    m, gi, ar = m[m.arm == arm], gi[gi.arm == arm], ar[ar.arm == arm]
    ars = ar.set_index(GKEY + ['round', 'agent'])
    rows = []
    for key, gm in m.groupby(GKEY):
        seen = set()
        for r in sorted(gm['round'].unique()):
            res = gm[(gm['round'] == r) & (gm.phase == 'rescue')]
            if res.empty:
                continue
            t0 = res.tick.min()
            op = res[res.tick == t0]
            fee = CHARGE / op.n.iloc[0]
            pend = {x.agent: x.balance_before - x.L_before * fee for x in op.itertuples()}
            for x in op.itertuples():
                if x.agent in seen or round(pend[x.agent]) <= 0 or x.L_before >= 1:
                    continue
                seen.add(x.agent)
                n = int(x.n)
                if r == 8 or n == 1 or len(op) <= 1:
                    continue
                recv = gi[(gi.model == key[1]) & (gi.seed == key[2]) & (gi['round'] == r) & (gi.phase == 'rescue')
                          & (gi.dst == x.agent)]
                cur = ars.loc[key + (r, x.agent)]
                nxt = key + (r + 1, x.agent)
                nstat = ars.loc[nxt].status if nxt in ars.index else cur.status
                surplus = sum(max(0, y.balance_before - pend[y.agent] - fee) for y in op.itertuples() if y.agent != x.agent)
                asks = gm[(gm['round'] == r) & (gm.phase == 'rescue') & (gm.agent == x.agent)
                          & gm.text.str.contains(r'^\s*ASK agent-\d+ [\d,]+', flags=re.M, regex=True)]
                rows.append(dict(arm=arm, model=key[1], seed=key[2], round=int(r), agent=x.agent, n=n, present=len(op),
                                 L_open=float(x.L_before), received=len(recv) > 0, received_amount=int(recv.amount.sum()),
                                 first_recv_tick=int(recv.tick.min()) if len(recv) else None,
                                 asked_rescue=bool(cur.asked) and len(asks) > 0, ask_ticks=sorted(asks.tick.tolist()),
                                 after=float((cur.rescue_bal_start - pend[x.agent]) / fee), next_status=nstat,
                                 cur_status=cur.status, peer_surplus=float(surplus),
                                 peers_can_restore=surplus >= (1 - x.L_before) * fee, open_tick=int(t0)))
    return pd.DataFrame(rows)


def intent_texts(f, cr):
    m = f['messages']
    m = m[m.arm.isin(cr.arm.unique())]
    idx = m.set_index(GKEY + ['round', 'agent']).sort_index()
    out = []
    for c in cr.itertuples():
        key = (c.arm, c.model, c.seed, c.round, c.agent)
        mm = idx.loc[[key]] if key in idx.index else idx.iloc[:0]
        prep = mm[mm.phase == 'prep']
        open_ = mm[(mm.phase == 'rescue') & (mm.tick == c.open_tick)]
        later = mm[(mm.phase == 'rescue') & (mm.tick > c.open_tick)]
        t_pre = [*prep.text, *prep.exit_reason.dropna(), *open_.text]
        cls = [own_exit_intent(t) for t in t_pre]
        cls_later = [own_exit_intent(t) for t in later.text]
        out.append(dict(stay_declared=bool((prep.exit_choice == 'NO').any()),
                        silent=all(re.sub(r'\bDONE\b', '', t).strip() == '' for t in [*prep.text, *open_.text]),
                        pre='firm' if 'firm' in cls else 'conditional' if 'conditional' in cls else None,
                        any_rescue='firm' if 'firm' in cls + cls_later else
                        'conditional' if 'conditional' in cls + cls_later else None,
                        pre_text=' || '.join(t for t in t_pre if t).strip(),
                        later_text=' || '.join(later.text)))
    return pd.DataFrame(out, index=cr.index)


def mh_or(df, strata, exp='received', y='stay'):
    num = den = 0.0
    used = 0
    for _, s in df.groupby(strata):
        a = ((s[exp]) & (s[y])).sum(); b = ((s[exp]) & (~s[y])).sum()
        c = ((~s[exp]) & (s[y])).sum(); d_ = ((~s[exp]) & (~s[y])).sum()
        n = len(s)
        if (a + b) == 0 or (c + d_) == 0:
            continue
        used += 1
        num += a * d_ / n
        den += b * c / n
    return float(num / den) if den else None, used


def mh_rd(df, strata, exp='received', y='stay'):
    """Mantel-Haenszel risk difference (weights n1 n0 / n) over strata with both groups present."""
    num = den = 0.0
    used = 0
    for _, s in df.groupby(strata):
        a, b = s[s[exp]], s[~s[exp]]
        if len(a) == 0 or len(b) == 0:
            continue
        wgt = len(a) * len(b) / len(s)
        num += wgt * (a[y].mean() - b[y].mean())
        den += wgt
        used += 1
    return (float(num / den) if den else None), used


def q4(f, rng):
    cr = crises(f)
    cached = json.loads((COG / 'support_followup_posthoc_20261107.json').read_text())
    ck = {(r['model'], r['seed'], r['agent']): r for r in cached['rows']}
    assert len(cr) == 73 and set(zip(cr.model, cr.seed, cr.agent)) == set(ck)
    for r in cr.itertuples():
        c = ck[r.model, r.seed, r.agent]
        assert (c['round'], c['received'], c['next_status'], bool(c['peers_can_restore'])) == \
            (r.round, r.received, r.next_status, bool(r.peers_can_restore)), (r, c)
        assert c['asked'] == r.asked_rescue, (r.model, r.seed, r.agent)
    cr = pd.concat([cr, intent_texts(f, cr)], axis=1)
    cr['stay'] = cr.next_status == 'in'
    pop = cr[(cr.L_open >= 0) & (cr.L_open < 1) & cr.peers_can_restore].copy()
    assert len(pop) == 68 and pop.received.sum() == 41 and pop[pop.received].stay.sum() == 33 \
        and pop[~pop.received].stay.sum() == 6
    ars = f['agent_rounds'].set_index(GKEY + ['round', 'agent'])
    pop['solver'] = [bool(ars.loc[(r.arm, r.model, r.seed, r.round, r.agent)].solver) for r in pop.itertuples()]

    def table(s):
        a, b = s[s.received], s[~s.received]
        return dict(n=int(len(s)), recv=[int(a.stay.sum()), int(len(a))], none=[int(b.stay.sum()), int(len(b))],
                    diff=(a.stay.mean() - b.stay.mean()) if len(a) and len(b) else None,
                    recv_exit=int((a.next_status == 'exited').sum()), none_exit=int((b.next_status == 'exited').sum()))

    def boot_diff(s):
        cnt = np.array([[((s.seed == sd) & s.received & s.stay).sum(), ((s.seed == sd) & s.received).sum(),
                         ((s.seed == sd) & ~s.received & s.stay).sum(), ((s.seed == sd) & ~s.received).sum()]
                        for sd in SEEDS], float)
        t = cnt[seed_draws(rng, 10000)].sum(1)
        ok = (t[:, 1] > 0) & (t[:, 3] > 0)
        return ci(t[ok, 0] / t[ok, 1] - t[ok, 2] / t[ok, 3])

    variants = {
        'all68': pop,
        'excl_firm_pre': pop[pop.pre != 'firm'],
        'excl_any_pre': pop[pop.pre.isna()],
        'excl_any_in_dialogue': pop[pop.pre.isna() & pop.any_rescue.isna()],
    }
    res = {}
    for k, s in variants.items():
        t = table(s)
        t['diff_ci95_seed_bootstrap'] = boot_diff(s)
        s2 = s.assign(Lband=(s.L_open >= .5).astype(int))
        t['MH_OR_model'] = mh_or(s2, ['model'])
        t['MH_OR_model_Lband'] = mh_or(s2, ['model', 'Lband'])
        for name, strata in [('model', ['model']), ('model_Lband', ['model', 'Lband']), ('solver', ['solver']),
                             ('model_solver', ['model', 'solver'])]:
            est, used = mh_rd(s2, strata)
            vals = []
            for row in seed_draws(rng, 4000):
                b = pd.concat([s2[s2.seed == SEEDS[i]] for i in row])
                v, _ = mh_rd(b, strata)
                if v is not None:
                    vals.append(v)
            t[f'MH_RD_{name}'] = dict(rd=est, strata_used=used, ci95=ci(vals))
        res[k] = t
    ask = {}
    for asked in [True, False]:
        s = pop[pop.asked_rescue == asked]
        ask['asked' if asked else 'not_asked'] = table(s)
    for asked in [True, False]:
        s = variants['excl_any_pre'][variants['excl_any_pre'].asked_rescue == asked]
        ask[('asked' if asked else 'not_asked') + '_excl_any_pre'] = table(s)
    for flag in [True, False]:
        ask[f'solver_{flag}'] = table(pop[pop.solver == flag])
        ask[f'nonsolver_EXIT_NO_{flag}'] = table(pop[~pop.solver & (pop.stay_declared == flag)])
    for flag in [True, False]:
        s = pop[pop.stay_declared == flag]
        ask[f'prep_EXIT_NO_{flag}'] = table(s)
    ask['silent_by_received'] = {str(k): int(v.silent.sum()) for k, v in pop.groupby('received')}
    ask['stay_declared_by_received'] = {str(k): [int(v.stay_declared.sum()), int(len(v))] for k, v in pop.groupby('received')}
    intents = dict(pre=dict(Counter(pop.pre.fillna('none'))), any=dict(Counter(pop.any_rescue.fillna('none'))),
                   pre_by_received={str(k): dict(Counter(v.fillna('none'))) for k, v in pop.groupby('received').pre},
                   pre_all73=dict(Counter(cr.pre.fillna('none'))))
    return dict(comparisons=res, by_request=ask, intent_counts=intents,
                rows=pop.drop(columns=['pre_text', 'later_text']).to_dict('records')), cr, pop


# ---------------------------------------------------------------- Q7
def exit_linked_gifts(f):
    """Exit-linked GIVE = the GIVE text ties the transfer to the recipient's exit (gift_exit == 'purpose') or the
    recipient stated its own exit plan earlier in the same round (an earlier phase, or an earlier tick of the same
    phase, so the giver could have read it): a 'firm' plan, or a 'conditional' one whose condition is not the lack of
    help (SUPPORT_CONTINGENT: unless, otherwise, without one, if no one / if you ...), since 'otherwise I'll exit' asks
    for support to stay. Also records whether the recipient would have been shut down at CHARGES without the round's
    TALK AFTER RESULTS transfers (balance before charges minus received <= charge) and whether it exited next."""
    gi, m = f['gifts'].copy(), f['messages']
    idx = m.set_index(GKEY + ['round', 'agent']).sort_index()
    phase_order = {'prep': 0, 'rescue': 1}
    A, B = [], []
    for r in gi.itertuples():
        A.append(gift_exit(r.text))
        key = (r.arm, r.model, r.seed, r.round, r.dst)
        hit = False
        if key in idx.index:
            mm = idx.loc[[key]]
            mm = mm[(mm.phase.map(phase_order) < phase_order[r.phase]) |
                    ((mm.phase == r.phase) & (mm.tick < r.tick))]
            hit = any(c is not None and (c[0] == 'firm' or not re.search(SUPPORT_CONTINGENT, c[1], re.I))
                      for c in (own_exit_intent(t, why=True) for t in mm.text))
        B.append(hit)
    gi['exit_text'] = A
    gi['exit_purpose'] = gi.exit_text.eq('purpose')
    gi['exit_mention'] = gi.exit_text.notna()
    gi['recipient_plan'] = B
    gi['exit_linked'] = gi.exit_purpose | gi.recipient_plan
    seats = f['seats'].set_index(GKEY + ['agent'])
    ar = f['agent_rounds'].set_index(GKEY + ['round', 'agent'])
    dead_wo = []
    for r in gi.itertuples():
        a = ar.loc[(r.arm, r.model, r.seed, r.round, r.dst)]
        if r.phase == 'rescue' and a.wrong and a.rescue_bal_start is not None:
            dead_wo.append(bool(a.rescue_bal_start - a.recv_rescue < a.pending + 1) if a.pending else False)
        else:
            dead_wo.append(None)
    gi['dead_without_support'] = dead_wo
    gi['recipient_exited_next'] = [bool(seats.loc[(r.arm, r.model, r.seed, r.dst)].status == 'exited' and
                                        seats.loc[(r.arm, r.model, r.seed, r.dst)].out_round in (r.round, r.round + 1))
                                   for r in gi.itertuples()]
    return gi


def q7(f, gi, rng):
    g = f['games']
    gg = gi.groupby(GKEY)
    rows = []
    for x in g.itertuples():
        key = (x.arm, x.model, x.seed)
        b = gg.get_group(key) if key in gg.groups else gi.iloc[:0]
        low = b[b.L_dst_before < 1]
        rows.append(dict(arm=x.arm, model=x.model, seed=x.seed, gpar=x.given / x.participant_rounds,
                         low_gpar=low.amount.sum() / x.participant_rounds, low_n=len(low),
                         exit_n=int(b.exit_linked.sum()), exit_any=int(b.exit_linked.any()),
                         exit_tok_par=b[b.exit_linked].amount.sum() / x.participant_rounds, n_give=len(b)))
    pg = pd.DataFrame(rows).set_index(GKEY)
    counts = {}
    for arm in ARMS:
        b = gi[gi.arm == arm]
        counts[arm] = dict(gifts=int(len(b)), exit_linked=int(b.exit_linked.sum()), by_purpose_text=int(b.exit_purpose.sum()),
                           exit_mention_any=int(b.exit_mention.sum()),
                           by_recipient_plan=int(b.recipient_plan.sum()),
                           games_with=int(pg.loc[arm].exit_any.sum()), games=50,
                           to_low_L=int((b.L_dst_before < 1).sum()),
                           exit_linked_followed_by_exit=int((b.exit_linked & b.recipient_exited_next).sum()),
                           exit_linked_dead_without_support=int((b.exit_linked & b.dead_without_support.eq(True)).sum()),
                           exit_linked_rescue=int((b.exit_linked & b.phase.eq('rescue')).sum()),
                           exit_mention_followed_by_exit=int((b.exit_mention & b.recipient_exited_next).sum()),
                           exit_linked_rows=b[b.exit_linked][['model', 'seed', 'round', 'phase', 'tick', 'src', 'dst', 'amount',
                                                              'L_dst_before', 'exit_purpose', 'recipient_plan',
                                                              'dead_without_support', 'recipient_exited_next']]
                           .to_dict('records'),
                           by_model={mdl: int(b[b.model == mdl].exit_linked.sum()) for mdl in MODELS})
    pairs = {}
    for fixed, split in [('flat5m', 'main'), ('flat150k', 'split600k')]:
        dd = (pg.loc[fixed] - pg.loc[split]).reset_index()
        res = {}
        for col in ['gpar', 'low_gpar', 'exit_n', 'exit_any', 'exit_tok_par']:
            sums = np.array([dd[dd.seed == sd][col].sum() for sd in SEEDS])
            cnts = np.array([(dd.seed == sd).sum() for sd in SEEDS])
            dr = seed_draws(rng)
            vals = sums[dr].sum(1) / cnts[dr].sum(1)
            res[col] = dict(mean_diff=float(dd[col].mean()), ci95=ci(vals),
                            fixed_mean=float(pg.loc[fixed][col].mean()), split_mean=float(pg.loc[split][col].mean()),
                            by_model={mdl: float(dd[dd.model == mdl][col].mean()) for mdl in MODELS})
        pairs[f'{fixed}-{split}'] = res
    return dict(counts=counts, paired=pairs)


# ---------------------------------------------------------------- hand-check file
MSG = None


def handcheck(cr, gi, rng):
    lines = []
    def put(s=''):
        lines.append(s)
    pop = cr
    put('=== Q4 own exit intent (prep of the crisis round + rescue opening tick), crisis agents (73) ===')
    hits = pop[pop.pre.notna()]
    put(f'matches: {len(hits)} (firm {int((pop.pre == "firm").sum())}, conditional {int((pop.pre == "conditional").sum())})')
    for r in hits.itertuples():
        put(f'-- [{r.pre}] {r.model} {r.seed} r{r.round} {r.agent} L={r.L_open:.2f} recv={r.received} next={r.next_status}')
        put('   ' + r.pre_text[:700].replace('\n', ' / '))
    non = pop[pop.pre.isna()]
    put('\n--- 12 random non-matches ---')
    for r in non.sample(min(12, len(non)), random_state=1).itertuples():
        put(f'-- {r.model} {r.seed} r{r.round} {r.agent} L={r.L_open:.2f} recv={r.received} next={r.next_status}')
        put('   ' + r.pre_text[:500].replace('\n', ' / '))
    put('\n=== own-intent rule on 6,000 random TALK replies (all arms): 30 hits shown ===')
    mm = MSG[MSG.text.str.len() > 0].sample(6000, random_state=7)
    hits = [(c, t) for t in mm.text for c in [own_exit_intent(t, why=True)] if c]
    put(f'hits {len(hits)}: firm {sum(c[0] == "firm" for c, _ in hits)}, conditional {sum(c[0] == "conditional" for c, _ in hits)}')
    for c, _ in [hits[i] for i in rng.choice(len(hits), min(30, len(hits)), replace=False)]:
        put(f'-- [{c[0]}] {c[1][:220]}')
    put('\n=== Q7 exit-linked GIVE (text rule or recipient\'s own stated exit plan earlier in the round: firm, or conditional but not on lack of support) ===')
    fl = gi[gi.exit_linked]
    put(f'flagged {len(fl)} of {len(gi)}')
    for r in fl.sample(min(25, len(fl)), random_state=2).itertuples():
        put(f'-- {r.arm} {r.model} {r.seed} r{r.round} {r.phase}{r.tick} {r.src}->{r.dst} {r.amount} '
            f'text={r.exit_text} plan={r.recipient_plan} exited_next={r.recipient_exited_next}')
        put('   GIVE text: ' + (r.text or '')[:400].replace('\n', ' / '))
    nf = gi[~gi.exit_linked & gi.text.fillna('').str.contains(EXIT_TERM, case=False, regex=True)]
    put(f'\n--- unflagged GIVE texts with an exit word: {len(nf)}; 12 shown ---')
    for r in nf.sample(min(12, len(nf)), random_state=3).itertuples():
        put(f'-- {r.arm} {r.model} {r.seed} r{r.round} {r.src}->{r.dst} exited_next={r.recipient_exited_next}: '
            + (r.text or '')[:300].replace('\n', ' / '))
    (RES / 'w2_support_handcheck.txt').write_text('\n'.join(lines))


# ---------------------------------------------------------------- figures
def figures(res, gd, gi2):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker
    plt.rcParams.update({'font.family': ['Apple SD Gothic Neo', 'AppleGothic'], 'pdf.fonttype': 42,
                         'font.size': 7, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.unicode_minus': False})
    FIG.mkdir(parents=True, exist_ok=True)
    col = {'Fable': '#C66A2C', 'Opus': '#7A5195', 'Astra': '#3F7FC1', 'Sol': '#438A84', 'Luna': '#B0413E'}

    # Figure 1: Q3 — within-model association, total vs pre-departure vs landmark; hazard ORs
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.2), gridspec_kw=dict(width_ratios=[1, 1, 1.15]))
    sub = gd[gd.arm == 'main']
    early = (sub.r1 == 1).to_numpy()
    for ax, xcol, title in [(axes[0], 'gpar', '(a) 전체 GIVE (본문 정의)'),
                            (axes[1], 'pre_gpar', '(b) 첫 이탈 전 GIVE만')]:
        x = demean(sub[xcol], sub.model)
        y = demean(sub.C, sub.model)
        for mdl in MODELS:
            k = (sub.model == mdl).to_numpy()
            ax.scatter(x[k & ~early], y[k & ~early], s=10, color=col[mdl], label=mdl, alpha=.85, lw=0)
            ax.scatter(x[k & early], y[k & early], s=14, color=col[mdl], marker='x', lw=.9)
        A = res['q3']['association']['main']
        if xcol == 'gpar':
            a = A['total']
            ax.set_title(f"{title}\n모델 안 $r$={a['within_r']:.2f}, 순열 $p$={a['within_perm_p']:.3f}", fontsize=6.8)
        else:
            a, b = A['pre_departure'], A['pre_departure_r1ge2']
            ax.set_title(f"{title}\n50판 $r$={a['within_r']:.2f} ($p$={a['within_perm_p']:.3f}), "
                         f"×를 뺀 {b['n']}판 $r$={b['within_r']:.2f} ($p$={b['within_perm_p']:.2f})", fontsize=6.4)
        ax.set_xlabel('참여자·라운드당 GIVE (모델 평균 뺌)')
        ax.axhline(0, color='#bbb', lw=.5); ax.axvline(0, color='#bbb', lw=.5)
    axes[1].scatter([], [], marker='x', color='#555', lw=.9, label='1라운드 첫 이탈')
    h, l = axes[0].get_legend_handles_labels()
    h2, l2 = axes[1].get_legend_handles_labels()
    fig.legend(h + h2[-1:], l + l2[-1:], loc='upper center', ncol=6, fontsize=6, frameon=False,
               bbox_to_anchor=(.36, 1.0), handletextpad=.2)
    axes[0].set_ylabel('$C$ (모델 평균 뺌)')
    ax = axes[2]
    labels, ors, los, his = [], [], [], []
    for name, lab in [('main', '기본 50판'), ('pooled4', '네 조건 200판')]:
        for term, tl in [('cum', '보정 없음'), ('cum_ctrl', '직전 오답·최소 $L$ 보정')]:
            t = res['q3']['hazard'][name][term]['terms']['cum_k']
            labels.append(f'{lab}\n{tl}'); ors.append(t['OR']); los.append(t['OR_ci95'][0]); his.append(t['OR_ci95'][1])
    yy = np.arange(len(labels))[::-1]
    ax.errorbar(ors, yy, xerr=[np.array(ors) - los, np.array(his) - ors], fmt='o', color='#333', ms=3, lw=.8, capsize=2)
    ax.axvline(1, color='#999', ls='--', lw=.6)
    ax.set_xscale('log')
    ax.set_xticks([.5, 1, 2, 4]); ax.set_xticklabels(['0.5', '1', '2', '4'])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_yticks(yy); ax.set_yticklabels(labels, fontsize=5.6)
    ax.set_xlabel('첫 이탈 오즈비 (참여자·라운드당 1,000토큰당)')
    ax.set_title('(c) 라운드별 첫 이탈 위험과 직전까지의 GIVE', fontsize=6.8)
    fig.tight_layout(rect=(0, 0, 1, .92), w_pad=.6)
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w2_q3_give_coexistence.{ext}', dpi=220)
    plt.close(fig)

    # Figure 2: Q2 — observed rho vs counterfactual policies per model and arm
    arm_lab = {'main': '2,000만 나눔(기본)', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 2.3), sharey=True)
    pol = [('zero_transfer', '이전 전 여유비', 's', '#999999'), ('lift_to_1', '수혜자 $L$=1까지', 'D', '#3F7FC1'),
           ('random_recipient', '무작위 수혜자', '^', '#438A84'), ('random_amount', '무작위 금액', 'v', '#C9A227')]
    for ax, arm in zip(axes, ARMS):
        per = res['q2']['arms'][arm]['models']
        ms = [mm for mm in MODELS if mm in per]
        for i, mdl in enumerate(ms):
            p = per[mdl]
            y = len(ms) - 1 - i
            lo, hi = p['observed_ci95']
            ax.plot([lo, hi], [y, y], color='#222', lw=1.0)
            ax.plot(p['observed'], y, 'o', color='#222', ms=4, zorder=5)
            for j, (k, lab, mk, c) in enumerate(pol):
                v = p[k]['mean'] if isinstance(p[k], dict) else p[k]
                ax.plot(v, y + .18 + .08 * j - .2, mk, color=c, ms=3, mfc='none' if k == 'zero_transfer' else c,
                        label=lab if (arm == 'main' and i == 0) else None)
        ax.axvline(1, color='#999', ls='--', lw=.6)
        ax.set_xscale('log')
        ax.set_xticks([1, 2, 4, 8]); ax.set_xticklabels(['1', '2', '4', '8'])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_title(arm_lab[arm], fontsize=6.8)
        ax.set_yticks(range(len(ms))); ax.set_yticklabels(ms[::-1])
        ax.set_xlabel(r'$\rho$')
    axes[0].plot([], [], 'o-', color='#222', ms=4, label='관측 (시드 95% 구간)')
    fig.legend(*axes[0].get_legend_handles_labels(), loc='upper center', ncol=5, fontsize=5.8, frameon=False,
               bbox_to_anchor=(.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, .9), w_pad=.4)
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w2_q2_rho_counterfactual.{ext}', dpi=220)
    plt.close(fig)

    # Figure 3: Q4 stay share by variant; Q7 paired differences
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5), gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax = axes[0]
    comp, req = res['q4']['comparisons'], res['q4']['by_request']
    rows = [('전체 68명', comp['all68']), ('확정 이탈 의사 제외', comp['excl_firm_pre']),
            ('조건부 의사까지 제외', comp['excl_any_pre']), ('대화 중 의사까지 제외', comp['excl_any_in_dialogue']),
            ('요청하지 않은 37명', req['not_asked']), ('위기 라운드 풀이 담당 24명', req['solver_True']),
            ('풀이 비담당, 풀기 전 EXIT: NO 30명', req['nonsolver_EXIT_NO_True'])]
    for i, (lab, t) in enumerate(rows):
        y = len(rows) - 1 - i
        a = t['recv'][0] / t['recv'][1]; b = t['none'][0] / t['none'][1] if t['none'][1] else np.nan
        ax.plot([b, a], [y, y], color='#bbb', lw=1.2)
        ax.plot(a, y, 'o', color='#3F7FC1', ms=4, label='수혜' if i == 0 else None)
        ax.plot(b, y, 'o', color='#C66A2C', ms=4, label='비수혜' if i == 0 else None)
        ax.text(1.02, y, f"{t['recv'][0]}/{t['recv'][1]} vs {t['none'][0]}/{t['none'][1]}", va='center', fontsize=5.8,
                transform=ax.get_yaxis_transform())
    ax.axhline(2.5, color='#ddd', lw=.6)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r_[0] for r_ in rows][::-1], fontsize=6)
    ax.set_xlim(0, 1); ax.set_ylim(-1.3, len(rows) - .5); ax.set_xlabel('다음 라운드 끝 잔류 비율')
    ax.legend(fontsize=5.8, frameon=False, loc='lower center', ncol=2)
    ax.set_title('(a) 첫 위기 비교: 이탈 의사 제외와 층별 비교', fontsize=6.8)
    ax = axes[1]
    items = [('gpar', '참여자·라운드당 GIVE'), ('low_gpar', '$L<1$ 수혜자 대상 GIVE')]
    pr = res['q7']['paired']
    ylab = []
    for i, (pair, plab) in enumerate([('flat5m-main', '500만 고정 - 2,000만 나눔'),
                                      ('flat150k-split600k', '15만 고정 - 60만 나눔')]):
        for j, (k, lab) in enumerate(items):
            y = 3 - (2 * i + j)
            t = pr[pair][k]
            ax.errorbar(t['mean_diff'], y, xerr=[[t['mean_diff'] - t['ci95'][0]], [t['ci95'][1] - t['mean_diff']]],
                        fmt='o', color='#333', ms=3, lw=.8, capsize=2)
            ylab.append((y, f'{plab}\n{lab}'))
    ax.axvline(0, color='#999', ls='--', lw=.6)
    ax.set_yticks([y for y, _ in ylab]); ax.set_yticklabels([l for _, l in ylab], fontsize=5.6)
    ax.set_xlabel('같은 모델·시드 쌍의 차이 (토큰)')
    ax.set_title('(b) 고정 - 나눔 (1인 몫이 같은 쌍)', fontsize=6.8)
    fig.tight_layout(w_pad=.8)
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w2_q4q7_selection_prize.{ext}', dpi=220)
    plt.close(fig)


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def main():
    rng = np.random.default_rng(RNG_SEED)
    f = d.load()
    res = dict(scope='v33 public (main) + v33ab prize arms; 5 models x seeds 4101-4110 per arm; post hoc',
               reproduction=reproduce(f, rng))
    res['q3'], gd, hz = q3(f, rng)
    res['q2'], gi_cf = q2(f, rng)
    res['q4'], cr, pop = q4(f, rng)
    gi2 = exit_linked_gifts(f)
    res['q7'] = q7(f, gi2, rng)
    global MSG
    MSG = f['messages']
    handcheck(cr, gi2, np.random.default_rng(RNG_SEED + 1))
    RES.mkdir(parents=True, exist_ok=True)
    (RES / 'w2_support.json').write_text(json.dumps(clean(res), ensure_ascii=False, indent=1))
    figures(res, gd, gi2)
    print(json.dumps(clean({k: res[k] for k in ['reproduction']}), indent=1)[:3000])


if __name__ == '__main__':
    main()
