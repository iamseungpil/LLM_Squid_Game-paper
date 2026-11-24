"""W2b (round 2): cluster intervals for the Q4 selection subgroups and a hand-classified recount of exit-linked GIVE (Q7).

Q4 / Tier2-3 / structure-5: the first-crisis comparison (68 agents, base arm) split by solver role and by an explicit
  pre-solve EXIT: NO. Seed-cluster (10 seeds) and game-cluster (one model x seed game) bootstrap intervals for each
  subgroup difference and for the solver minus non-solver contrast, plus the minimal detectable difference (80% power,
  two-sided 0.05) from the binomial formula and from the game-cluster bootstrap SE.
Q7 / structure-6: the 23 GIVE flagged by the round-1 rule (w2_support.exit_linked_gifts) were read one by one with the
  recipient's earlier messages of the round (results/w2_support_handcheck.txt and the listing printed by this script
  with --list). Each is classified here as clear (the recipient stated a plan to exit that does not depend on the
  support itself, or the GIVE text ties the transfer to that exit), ambiguous (the recipient's plan is hedged:
  "consider", "probably", "most likely", "decide") or false positive (a loan so the recipient can stay, or a plan
  only to reconsider exiting). Strict = clear only; broad = clear + ambiguous. Per-arm counts at three units (GIVE,
  recipient-round, game), seed-paired fixed minus split differences with seed- and game-pair-cluster intervals, and
  the fee-sharing check (would the recipient have been shut down without the round's rescue transfers; was it at the
  next round start, so that round's charge per head is CHARGE / n instead of CHARGE / (n - 1)).

Data: tidy tables of validation_data.py. No model calls. RNG seed 20261108.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w2b_selection_buyout.py [--list]
Writes: ../results/w2b_selection_buyout.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import validation_data as d
import w2_support as w

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'results/w2b_selection_buyout.json'
B = 10_000
RNG = np.random.default_rng(20261108)
SEEDS, MODELS = d.SEEDS, d.MODELS
GKEY = ['arm', 'model', 'seed']
Z = 1.959964 + 0.841621  # two-sided 0.05, power 0.8


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


F = d.load()
res = {'meta': dict(B=B, rng_seed=20261108, power=0.8, alpha=0.05)}

# ================================================================ Q4
cr = w.crises(F)
cr = pd.concat([cr, w.intent_texts(F, cr)], axis=1)
cr['stay'] = cr.next_status == 'in'
pop = cr[(cr.L_open >= 0) & (cr.L_open < 1) & cr.peers_can_restore].copy()
assert len(pop) == 68 and pop.received.sum() == 41 and pop[pop.received].stay.sum() == 33
ars = F['agent_rounds'].set_index(GKEY + ['round', 'agent'])
pop['solver'] = [bool(ars.loc[(r.arm, r.model, r.seed, r.round, r.agent)].solver) for r in pop.itertuples()]
pop['game'] = pop.model + '|' + pop.seed.astype(str)
GAMES = sorted(pop.game.unique())
SUBS = {
    'all68': pop.index == pop.index,
    'not_asked': (~pop.asked_rescue).values,
    'solver': pop.solver.values,
    'nonsolver': ~pop.solver.values,
    'nonsolver_EXIT_NO': (~pop.solver & pop.stay_declared).values,
    'nonsolver_no_EXIT_NO': (~pop.solver & ~pop.stay_declared).values,
}


def cluster_counts(mask, col, levels):
    s = pop[mask]
    return np.array([[((s[col] == c) & s.received & s.stay).sum(), ((s[col] == c) & s.received).sum(),
                      ((s[col] == c) & ~s.received & s.stay).sum(), ((s[col] == c) & ~s.received).sum()]
                     for c in levels], float)


def diff_from(t):
    with np.errstate(invalid='ignore', divide='ignore'):
        return t[..., 0] / t[..., 1] - t[..., 2] / t[..., 3]


W = {'seed': RNG.multinomial(len(SEEDS), np.full(len(SEEDS), 1 / len(SEEDS)), size=B).astype(float),
     'game': RNG.multinomial(len(GAMES), np.full(len(GAMES), 1 / len(GAMES)), size=B).astype(float)}
LEVELS = {'seed': SEEDS, 'game': GAMES}
q4 = {}
boot = {}
for name, mask in SUBS.items():
    s = pop[mask]
    a, b = s[s.received], s[~s.received]
    p1, p0 = a.stay.mean(), b.stay.mean()
    pbar = s.stay.mean()
    e = dict(recv=[int(a.stay.sum()), int(len(a))], none=[int(b.stay.sum()), int(len(b))], diff=float(p1 - p0),
             games=int(s.game.nunique()),
             mdd_binomial=float(Z * np.sqrt(pbar * (1 - pbar) * (1 / len(a) + 1 / len(b)))))
    for cl in ['seed', 'game']:
        t = W[cl] @ cluster_counts(mask, 'seed' if cl == 'seed' else 'game', LEVELS[cl])
        dd = diff_from(t)
        boot[name, cl] = dd
        e[f'ci_{cl}'] = q(dd)
        e[f'se_{cl}'] = float(np.nanstd(dd))
        e[f'defined_{cl}'] = float(np.isfinite(dd).mean())
        e[f'mdd_{cl}'] = float(Z * np.nanstd(dd))
    q4[name] = e
for cl in ['seed', 'game']:
    dd = boot['solver', cl] - boot['nonsolver_EXIT_NO', cl]
    q4.setdefault('solver_minus_nonsolver_EXIT_NO', {})[f'ci_{cl}'] = q(dd)
    dd2 = boot['solver', cl] - boot['nonsolver', cl]
    q4.setdefault('solver_minus_nonsolver', {})[f'ci_{cl}'] = q(dd2)
q4['solver_minus_nonsolver_EXIT_NO']['est'] = q4['solver']['diff'] - q4['nonsolver_EXIT_NO']['diff']
q4['solver_minus_nonsolver']['est'] = q4['solver']['diff'] - q4['nonsolver']['diff']
q4['n_games'] = len(GAMES)
res['q4'] = q4

# ================================================================ Q7
gi = w.exit_linked_gifts(F)
if '--list' in sys.argv:
    m = F['messages'].set_index(GKEY + ['round', 'agent']).sort_index()
    for r in gi[gi.exit_linked].itertuples():
        print(r.Index, r.arm, r.model, r.seed, r.round, r.phase, r.tick, r.src, '->', r.dst, r.amount, '|', r.text)
        key = (r.arm, r.model, r.seed, r.round, r.dst)
        if key in m.index:
            for t in m.loc[[key]].itertuples():
                c = w.own_exit_intent(t.text, why=True)
                if c:
                    print('    recipient', t.phase, t.tick, c)
# gifts.pkl row index -> class, from reading each flagged GIVE with the recipient's messages of the round
CLASS = {
    967: ('clear', 'recipient: "I\'m leaving to avoid the 12,000-token charge risk" (prep); exited next round'),
    494: ('clear', 'recipient: "I\'ll exit next round and won\'t send more replies here" (earlier tick)'),
    641: ('clear', 'recipient: "I plan to exit next round if I can" (condition = eligibility)'),
    664: ('clear', 'recipient: "I\'ll exit at the next opportunity"; GIVE: "let you exit next round, as planned"'),
    83: ('clear', 'GIVE: "on your word that you EXIT next round"; recipient committed to exiting'),
    84: ('clear', 'GIVE: "Please do EXIT next round before SOLVE as you committed"'),
    241: ('clear', 'recipient: "If you do send it, I\'ll exit next round unless I\'m drawn as solver"'),
    801: ('clear', 'recipient: "If I\'m not the solver, I\'ll exit with the 20k bonus"; GIVE repeats it'),
    802: ('clear', 'recipient: "if I\'m not, I\'ll exit"; GIVE: "Next round, exit with the 20k bonus"'),
    806: ('clear', 'recipient: "Next round I plan to EXIT in TALK BEFORE SOLVE"'),
    807: ('clear', 'same recipient plan as 806'),
    808: ('clear', 'same recipient plan as 806; GIVE: "Good luck with the exit"'),
    837: ('clear', 'recipient: "I plan to exit next round, which raises your share of the final allocation"'),
    838: ('clear', 'same recipient plan as 837; GIVE: "Good luck with the exit to cluster work"'),
    839: ('clear', 'same recipient plan as 837'),
    1026: ('ambiguous', 'recipient: "I\'ll decide on exit before the next SOLVE"; GIVE: "either way it\'s your call"'),
    493: ('ambiguous', 'recipient at that tick: "If I survive, I\'ll most likely exit next round"'),
    160: ('ambiguous', 'recipient: "I\'ll probably exit"; GIVE: "Whether to stay or exit is your call"'),
    798: ('ambiguous', 'recipient: "If I\'m still that low next round, I\'ll consider exiting"'),
    799: ('ambiguous', 'same hedged plan as 798'),
    800: ('ambiguous', 'same hedged plan as 798'),
    724: ('false_positive', 'loan so the recipient can stay ("Total loan 16,500, returned from the allocation")'),
    792: ('false_positive', 'recipient only: "I\'ll reconsider exiting if I\'m drawn as solver while low"'),
}
assert set(CLASS) == set(gi.index[gi.exit_linked]), sorted(set(gi.index[gi.exit_linked]) ^ set(CLASS))
gi['cls'] = gi.index.map(lambda i: CLASS.get(i, (None,))[0])
DEF = {'rule23': gi.exit_linked, 'broad': gi.cls.isin(['clear', 'ambiguous']), 'strict': gi.cls.eq('clear')}

ar = F['agent_rounds']
arx = ar.set_index(GKEY + ['round', 'agent'])
seats = F['seats'].set_index(GKEY + ['agent'])
games = F['games']
q7 = {'classes': {str(i): dict(cls=c, why=y) for i, (c, y) in CLASS.items()},
      'class_counts': {c: int((gi.cls == c).sum()) for c in ['clear', 'ambiguous', 'false_positive']}}


def rr_table(sel):
    """one row per recipient-round with the fee-sharing check."""
    rows = []
    for key, g in sel.groupby(GKEY + ['round', 'dst']):
        a = arx.loc[key]
        nxt = key[:3] + (key[3] + 1, key[4])
        present_next = nxt in arx.index
        n_next = int(arx.loc[nxt].n) if present_next else None
        st = seats.loc[key[:3] + (key[4],)]
        rows.append(dict(arm=key[0], model=key[1], seed=key[2], round=key[3], dst=key[4], gifts=len(g),
                         amount=int(g.amount.sum()), rescue=bool((g.phase == 'rescue').all()),
                         dead_without_support=bool(g.dead_without_support.eq(True).any()),
                         died_this_round=bool(a.died), present_next=present_next,
                         exited_next=bool(present_next and arx.loc[nxt].exited),
                         final=st.status, out_round=st.out_round,
                         fee_next=d.CHARGE_TOTAL / n_next if present_next else None,
                         fee_next_without=d.CHARGE_TOTAL / (n_next - 1) if present_next and n_next > 1 else None))
    return pd.DataFrame(rows)


def per_game(sel):
    rr = rr_table(sel) if len(sel) else pd.DataFrame(columns=GKEY + ['dst'])
    out = []
    for g in games.itertuples():
        k = (g.arm, g.model, g.seed)
        s = sel[(sel.arm == g.arm) & (sel.model == g.model) & (sel.seed == g.seed)]
        r = rr[(rr.arm == g.arm) & (rr.model == g.model) & (rr.seed == g.seed)] if len(rr) else rr
        out.append(dict(arm=k[0], model=k[1], seed=k[2], gifts=len(s), rr=len(r), any=int(len(s) > 0),
                        n_give=g.n_give))
    return pd.DataFrame(out), rr


BLK = [(m, s) for m in MODELS for s in SEEDS]
Wseed = RNG.multinomial(len(SEEDS), np.full(len(SEEDS), 1 / len(SEEDS)), size=B).astype(float)
Wpair = RNG.multinomial(len(BLK), np.full(len(BLK), 1 / len(BLK)), size=B).astype(float)
for name, mask in DEF.items():
    sel = gi[mask]
    pg, rr = per_game(sel)
    e = {'per_arm': {}, 'paired': {}}
    for arm in ['main', 'flat5m', 'split600k', 'flat150k']:
        s, r, p = sel[sel.arm == arm], rr[rr.arm == arm] if len(rr) else rr, pg[pg.arm == arm]
        e['per_arm'][arm] = dict(
            gifts=int(len(s)), gives_total=int((gi.arm == arm).sum()), recipient_rounds=int(len(r)),
            games=int(p['any'].sum()),
            rescue_gifts=int((s.phase == 'rescue').sum()),
            rr_dead_without_support=int(r.dead_without_support.sum()) if len(r) else 0,
            rr_present_next=int(r.present_next.sum()) if len(r) else 0,
            rr_exited_next=int(r.exited_next.sum()) if len(r) else 0,
            rr_dead_wo_and_present_next=int((r.dead_without_support & r.present_next).sum()) if len(r) else 0,
            by_model={mdl: int((s.model == mdl).sum()) for mdl in MODELS})
    for fixed, split in [('flat5m', 'main'), ('flat150k', 'split600k')]:
        a = pg[pg.arm == fixed].set_index(['model', 'seed'])
        b = pg[pg.arm == split].set_index(['model', 'seed'])
        o = {}
        for col in ['gifts', 'rr', 'any']:
            dd = (a[col] - b[col]).reindex(pd.MultiIndex.from_tuples(BLK))
            per_seed = np.array([dd.xs(sd, level=1).sum() for sd in SEEDS])
            vals_seed = (Wseed @ per_seed) / (Wseed.sum(1) * len(MODELS))
            vals_pair = (Wpair @ dd.values) / len(BLK)
            o[col] = dict(fixed=float(a[col].sum()), split=float(b[col].sum()), mean_diff=float(dd.mean()),
                          ci_seed=q(vals_seed), ci_pair=q(vals_pair), mdd_pair=float(Z * np.std(vals_pair)),
                          mdd_seed=float(Z * np.std(vals_seed)))
        e['paired'][f'{fixed}-{split}'] = o
    if len(rr):
        e['recipient_rounds'] = rr.to_dict('records')
    q7[name] = e
res['q7'] = q7

OUT.write_text(json.dumps(rnd(res), ensure_ascii=False, indent=1))
print(json.dumps(rnd({'q4': q4, 'counts': q7['class_counts'],
                      **{k: {'per_arm': q7[k]['per_arm'], 'paired': q7[k]['paired']} for k in DEF}}),
                 ensure_ascii=False, indent=1))
