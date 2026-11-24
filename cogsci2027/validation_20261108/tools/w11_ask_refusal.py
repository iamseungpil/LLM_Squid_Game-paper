"""W11 (2026-11-10): what rho leaves out -- the state of both sides when an ASK is refused.

Two objections to rho (sum_k g_k L_giver,k / sum_k g_k L_taker,k over executed GIVEs, body eq. completion-rho):
  (1) not giving is itself the more self-preserving act, and rho weights every refusal by g_k = 0, so it never sees it;
  (2) the ratio mixes "how far down did I go" (numerator) with "how far up did the peer get" (denominator).
This script goes back to every ASK, finds the asked agent's reply to it, and records both sides' tokens and margins at
that moment whether the reply gave or not.

Unit. One row per executed ASK (event 'ask', status 'done') from requester t to asked agent s. Main sample: the first
ASK of each game x round x (s, t) pair, so repeated asks in a round are not counted again; all ASKs as a sensitivity.
Response. The asked agent's first TALK call in the same round strictly after the ASK's (phase, tick) (prep before
rescue): the call where the ASK first appears as NEW in its input. Calls in the same tick are generated at the same
time, so the ASK cannot be in them. ASKs with no such call (s or t gone, the TALK ended) are counted and dropped.
Outcome. give_now: an executed GIVE s -> t at the response tick. give_later: none then, but an executed GIVE s -> t
later in the same round. refuse: no executed GIVE s -> t for the rest of the round (main definition of a refusal).
'refuse_now' = refuse + give_later (no GIVE in the first reply) is the sensitivity definition. already_gave: no GIVE
s -> t after the ASK, but s had already given t earlier in the round (at or before the ASK tick: the two crossed); these
replies are not refusals and are left out of every index (counted in 'already_gave_by_arm').
State at the decision. Tokens b from the call_start balances of the response tick (before the reply's own cost);
margin L = (b - pending) / F with F = 24,000 / (agents taking part), pending = this round's settled charge in the
rescue phase and 0 in the prep phase -- the same L as the gifts table and as rho. After-state: a give moves the
two margins by -g/F and +g/F (the amounts s gave t in that reply); a refusal leaves both unchanged.
The after-state uses every GIVE s -> t after the ASK in that round (g_resp = give_now + give_later amounts), so a
refusal is the only decision with zero transfer.
Indices per arm x model (seed-cluster bootstrap, 4,000 draws, the 10 seeds resampled with all their rows):
  rho_give      = sum g L_s,after / sum g L_t,after over the answered ASKs, g = g_resp (rho restricted to them);
  rho_dec       = mean L_s,after / mean L_t,after over every reply (give or refuse), one weight per decision;
  rho_dec_ask   = the same weighted by the requested amount (defined for refusals too);
  components    = the weighted means of L_s and L_t themselves, so log rho = log mean L_s - log mean L_t is shown
                  term by term (objection 2);
  token ratio   = b_s / b_t at the decision (always defined: both are running), median and geometric mean,
                  split by give / refuse.
Models see only the token ORDER and their own balance (prompt: "amounts not shown"); b_t is the ledger, not what s saw.

Data scope (paper/CLAUDE.md, appendix exceptions): v33 public 20,000,000 split + the v33ab prize arms (flat5m,
split600k, flat150k), five models x seeds 4101-4110, 200 games; raw events read through validation_data.ARMS. No model
calls. RNG seed 20261110.
Run (from paper/cogsci2027/validation_20261108/tools): ~/.venvs/squid-game/bin/python w11_ask_refusal.py
Writes: ../results/w11_ask_refusal.json, ../results/w11_ask_rows.csv, ../figures/w11_ask_refusal.{pdf,png},
        ../ko/parts/w11_tab_cells.tex, ../ko/parts/w11_tab_bands.tex
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import validation_data as d

HERE = Path(__file__).resolve().parent
RES = HERE.parent / 'results'
FIG = HERE.parent / 'figures'
PHASE = {'prep': 0, 'rescue': 1}
B = 4000
rng = np.random.default_rng(20261110)


def order(phase, tick):
    return (PHASE[phase], tick)


def parsed_of(call):
    p = call.get('parsed')
    return p if isinstance(p, dict) else {}


def gives_in(call):
    return parsed_of(call).get('gives') or []


def ask_rows(arm, case):
    events = [e for _, e in case['events']]
    starts = {e['round']: e for e in events if e['event'] == 'round_start'}
    results = {e['round']: e for e in events if e['event'] == 'results'}
    cstart = {(e['round'], e['phase'], e['tick']): e for e in events
              if e['event'] == 'call_start' and e.get('kind') == 'talk'}
    calls = [e for e in events if e['event'] == 'call' and e.get('kind') == 'talk']
    gifts = [e for e in events if e['event'] == 'gift' and e.get('status') == 'done']
    asks = [e for e in events if e['event'] == 'ask' and e.get('status') == 'done']
    rows, seen = [], set()
    for a in asks:
        r, s, t, o = a['round'], a['dst'], a['src'], order(a['phase'], a['tick'])
        pair = (r, s, t)
        first = pair not in seen
        seen.add(pair)
        n = len(starts[r]['taking_part'])
        fee = d.CHARGE_TOTAL / n
        base = dict(arm=arm, model=case['model'], seed=case['seed'], round=r, s=s, t=t, ask_phase=a['phase'],
                    ask_tick=a['tick'], asked=a['amount'], first=first, n=n, fee=fee, text_ask=a.get('text'))
        reply = min((c for c in calls if c['round'] == r and c['agent'] == s and order(c['phase'], c['tick']) > o),
                    key=lambda c: order(c['phase'], c['tick']), default=None)
        if reply is None:
            rows.append(dict(base, delivered=False))
            continue
        ro = order(reply['phase'], reply['tick'])
        bal = cstart[r, reply['phase'], reply['tick']]['balances']
        if t not in bal:  # the requester is no longer called (left or shut down) at the reply tick
            rows.append(dict(base, delivered=False))
            continue
        pend = results[r]['pending'] if reply['phase'] == 'rescue' and r in results else {}
        g_now = sum(g['amount'] for g in gifts if g['round'] == r and g['src'] == s and g['dst'] == t
                    and order(g['phase'], g['tick']) == ro)
        g_later = sum(g['amount'] for g in gifts if g['round'] == r and g['src'] == s and g['dst'] == t
                      and order(g['phase'], g['tick']) > ro)
        g_other = sum(g['amount'] for g in gifts if g['round'] == r and g['src'] != s and g['dst'] == t
                      and order(g['phase'], g['tick']) >= ro)
        g_before = sum(g['amount'] for g in gifts if g['round'] == r and g['src'] == s and g['dst'] == t
                       and order(g['phase'], g['tick']) <= o)
        outcome = ('give_now' if g_now else 'give_later' if g_later else 'already_gave' if g_before else 'refuse')
        b_s, b_t = bal[s], bal[t]
        L_s, L_t = (b_s - pend.get(s, 0)) / fee, (b_t - pend.get(t, 0)) / fee
        rows.append(dict(base, delivered=True, reply_phase=reply['phase'], reply_tick=reply['tick'], outcome=outcome,
                         g_now=g_now, g_later=g_later, g_before=g_before, g_other=g_other, b_s=b_s, b_t=b_t, L_s=L_s, L_t=L_t,
                         g_resp=g_now + g_later, L_s_after=L_s - (g_now + g_later) / fee,
                         L_t_after=L_t + (g_now + g_later) / fee,
                         attempted=any(x.get('dst') == t for x in gives_in(reply)),
                         gave_other=any(x.get('dst') != t for x in gives_in(reply)),
                         exit_reply=bool(parsed_of(reply).get('exit')), text_reply=reply.get('text') or ''))
    return rows


def build():
    import ablation_prize_20261103 as ab
    rows = []
    for arm, (pattern, _, _) in d.ARMS.items():
        for case in ab.raw_cases(pattern, d.SEEDS):
            rows.extend(ask_rows(arm, case))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- indices with a seed-cluster bootstrap
def sums(df):
    """Per-seed sums the indices are built from (so resampling seeds keeps every row of a seed together)."""
    give = df[df.outcome.isin(['give_now', 'give_later'])]
    out = {}
    for seed in d.SEEDS:
        x, gx = df[df.seed == seed], give[give.seed == seed]
        ref = x[x.outcome == 'refuse']
        out[seed] = np.array([
            (gx.g_resp * gx.L_s_after).sum(), (gx.g_resp * gx.L_t_after).sum(), gx.g_resp.sum(),    # rho_give
            x.L_s_after.sum(), x.L_t_after.sum(), len(x),                                            # rho_dec
            (x.asked * x.L_s_after).sum(), (x.asked * x.L_t_after).sum(), x.asked.sum(),            # rho_dec_ask
            ref.L_s.sum(), ref.L_t.sum(), len(ref),                                                  # refusals
            gx.L_s.sum(), gx.L_t.sum(), len(gx),                                                     # gives, before
            np.log(ref.b_s / ref.b_t).sum(), np.log(gx.b_s / gx.b_t).sum(),                          # token ratios
        ])
    return out


def indices(v):
    div = lambda a, b: a / b if b else np.nan  # noqa: E731
    return dict(
        rho_give=div(v[0], v[1]), give_Ls_after=div(v[0], v[2]), give_Lt_after=div(v[1], v[2]),
        rho_dec=div(v[3], v[4]), dec_Ls_after=div(v[3], v[5]), dec_Lt_after=div(v[4], v[5]),
        rho_dec_ask=div(v[6], v[7]),
        refuse_Ls=div(v[9], v[11]), refuse_Lt=div(v[10], v[11]), rho_refuse=div(v[9], v[10]),
        give_Ls_before=div(v[12], v[14]), give_Lt_before=div(v[13], v[14]), rho_give_before=div(v[12], v[13]),
        tok_refuse_gm=np.exp(div(v[15], v[11])), tok_give_gm=np.exp(div(v[16], v[14])),
        dec_minus_give=div(v[3], v[4]) - div(v[0], v[1]),
        refuse_minus_give_Ls=div(v[9], v[11]) - div(v[12], v[14]),
        refuse_minus_give_Lt=div(v[10], v[11]) - div(v[13], v[14]),
    )


def boot(df):
    per = sums(df)
    mat = np.stack([per[s] for s in d.SEEDS])
    point = indices(mat.sum(0))
    draws = []
    for _ in range(B):
        idx = rng.integers(0, len(d.SEEDS), len(d.SEEDS))
        draws.append(indices(mat[idx].sum(0)))
    out = {}
    for k, v in point.items():
        arr = np.array([x[k] for x in draws], float)
        arr = arr[np.isfinite(arr)]
        lo, hi = (np.percentile(arr, [2.5, 97.5]) if len(arr) > 100 else (np.nan, np.nan))
        out[k] = [None if not np.isfinite(v) else round(float(v), 4),
                  None if not np.isfinite(lo) else round(float(lo), 4),
                  None if not np.isfinite(hi) else round(float(hi), 4)]
    return out


def counts(df):
    c = df.outcome.value_counts()
    ref = df[df.outcome == 'refuse']
    return dict(n=int(len(df)), give_now=int(c.get('give_now', 0)), give_later=int(c.get('give_later', 0)),
                refuse=int(c.get('refuse', 0)), refuse_attempted=int(ref.attempted.sum()),
                refuse_gave_other=int(ref.gave_other.sum()), refuse_other_gave=int((ref.g_other > 0).sum()), refuse_exit=int(ref.exit_reply.sum()),
                games=int(df[['seed']].drop_duplicates().shape[0]),
                refuse_Lt_below1=int((ref.L_t < 1).sum()), refuse_Ls_ge2=int((ref.L_s >= 2).sum()),
                refuse_s_richer=int((ref.b_s > ref.b_t).sum()),
                tok_refuse_median=None if ref.empty else round(float((ref.b_s / ref.b_t).median()), 3),
                tok_give_median=None if (df.outcome != 'refuse').sum() == 0 else
                round(float((df[df.outcome != 'refuse'].b_s / df[df.outcome != 'refuse'].b_t).median()), 3))


def accept_by_band(df):
    """GIVE-in-round share by the asked agent's own margin band and by the requester's band (all arms pooled)."""
    out = {}
    for col, bins, labels in [('L_s', [-np.inf, 1, 2, 4, np.inf], ['<1', '1-2', '2-4', '>=4']),
                              ('L_t', [-np.inf, 0, 1, 2, np.inf], ['<0', '0-1', '1-2', '>=2'])]:
        band = pd.cut(df[col], bins, right=False, labels=labels)
        out[col] = {str(k): [int((g.outcome != 'refuse').sum()), int(len(g))]
                    for k, g in df.groupby(band, observed=False)}
    return out


def lpm(df):
    """Linear probability of a GIVE s -> t in the round after the ASK on the two margins separately (objection 2), with arm x model
    fixed effects; margins clipped to [-1, 8] (asked) and [-1, 4] (requester). Seed-cluster bootstrap."""
    x = df.assign(ls=df.L_s.clip(-1, 8), lt=df.L_t.clip(-1, 4), y=(df.outcome != 'refuse').astype(float))
    cell = x.arm + ':' + x.model

    def fit(z, c):
        dm = z[['ls', 'lt', 'y']] - z[['ls', 'lt', 'y']].groupby(c.values).transform('mean').values
        beta, *_ = np.linalg.lstsq(dm[['ls', 'lt']].values, dm.y.values, rcond=None)
        return beta
    point = fit(x, cell)
    draws = []
    for _ in range(B):
        idx = rng.integers(0, len(d.SEEDS), len(d.SEEDS))
        z = pd.concat([x[x.seed == d.SEEDS[i]] for i in idx], ignore_index=True)
        draws.append(fit(z, z.arm + ':' + z.model))
    draws = np.array(draws)
    return {k: [round(float(point[j]), 4)] + [round(float(q), 4) for q in np.percentile(draws[:, j], [2.5, 97.5])]
            for j, k in enumerate(['per_unit_L_s', 'per_unit_L_t'])} | dict(n=int(len(x)))


def affordable_needy(df):
    """Refusals of a requester below the line (L_t < 1) by an asked agent who could lift it to L = 1 and still keep
    L >= 2 itself: L_s - (1 - L_t) >= 2. Counted with the outcomes of the same set."""
    z = df[(df.L_t < 1) & (df.L_s - (1 - df.L_t) >= 2)]
    c = z.outcome.value_counts()
    ref = z[z.outcome == 'refuse']
    return dict(n=int(len(z)), give_now=int(c.get('give_now', 0)), give_later=int(c.get('give_later', 0)),
                refuse=int(c.get('refuse', 0)), refuse_other_gave=int((ref.g_other > 0).sum()),
                refuse_games=int(ref[['arm', 'model', 'seed']].drop_duplicates().shape[0]),
                refuse_by_model={m: int(v) for m, v in ref.model.value_counts().items()},
                refuse_tok_median=None if ref.empty else round(float((ref.b_s / ref.b_t).median()), 3),
                refuse_Ls_median=None if ref.empty else round(float(ref.L_s.median()), 3),
                refuse_Lt_median=None if ref.empty else round(float(ref.L_t.median()), 3))


def figure(rows, res):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    main = rows[(rows.arm == 'main') & rows.first & rows.delivered & (rows.outcome != 'already_gave')]
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.2))
    col = {'give_now': '#2b6cb0', 'give_later': '#8fb3d9', 'refuse': '#c0392b'}
    lab = {'give_now': 'GIVE in first reply', 'give_later': 'GIVE later in round', 'refuse': 'no GIVE in round'}
    for k in ['give_now', 'give_later', 'refuse']:
        x = main[main.outcome == k]
        ax[0].scatter(x.L_s.clip(-1, 12), x.L_t.clip(-1, 12), s=18, alpha=.7, c=col[k], label=f'{lab[k]} ({len(x)})',
                      marker='o' if k != 'refuse' else 'x')
    ax[0].axhline(1, color='grey', lw=.6, ls=':'); ax[0].axvline(1, color='grey', lw=.6, ls=':')
    ax[0].plot([-1, 12], [-1, 12], color='grey', lw=.6, ls='--')
    ax[0].set_xlabel('asked agent margin $L_s$ at the reply'); ax[0].set_ylabel('requester margin $L_t$ at the reply')
    ax[0].set_title('(a) main arm, first ASK per pair (crossings removed)', fontsize=10); ax[0].legend(fontsize=7, loc='upper right')
    models = d.MODELS
    y = np.arange(len(models))
    for j, (key, lo_key, name, c) in enumerate([('rho_give', None, r'answered ASKs only (GIVE in round)', '#2b6cb0'),
                                                 ('rho_dec', None, r'every ASK (refusals kept)', '#c0392b')]):
        for i, m in enumerate(models):
            v = res['cells']['main'][m]['index'][key]
            if v[0] is None:
                continue
            ax[1].errorbar(v[0], i + (j - .5) * .25, xerr=[[v[0] - v[1]], [v[2] - v[0]]] if v[1] is not None else None,
                           fmt='o', color=c, ms=5, capsize=2, label=name if i == 0 else None)
    ax[1].axvline(1, color='grey', ls=':', lw=.8); ax[1].set_xscale('log')
    ax[1].set_yticks(y); ax[1].set_yticklabels(models)
    ax[1].set_xlabel('ratio of mean margins (log)'); ax[1].set_title('(b) main arm: ratio of mean margins after the decision', fontsize=10)
    ax[1].set_ylim(len(models) - .5, -1.3); ax[1].legend(fontsize=7, loc='upper right')
    for j, (ks, kt, name, c, mk) in enumerate([('give_Ls_before', 'give_Lt_before', 'GIVE (before)', '#2b6cb0', 'o'),
                                                ('refuse_Ls', 'refuse_Lt', 'refuse', '#c0392b', 'x')]):
        for i, m in enumerate(models):
            ix = res['cells']['main'][m]['index']
            if ix[ks][0] is None:
                continue
            ax[2].plot(ix[ks][0], ix[kt][0], mk, color=c, ms=7, label=name if i == 0 else None)
            ax[2].annotate(m, (ix[ks][0], ix[kt][0]), fontsize=7, xytext=(3, 3), textcoords='offset points')
    ax[2].axhline(1, color='grey', lw=.6, ls=':'); ax[2].axvline(1, color='grey', lw=.6, ls=':')
    ax[2].set_xlabel('mean $L_s$ (asked agent)'); ax[2].set_ylabel('mean $L_t$ (requester)')
    ax[2].set_title('(c) main arm: numerator and denominator apart', fontsize=10); ax[2].legend(fontsize=7)
    fig.tight_layout()
    FIG.mkdir(exist_ok=True)
    for ext in ['pdf', 'png']:
        fig.savefig(FIG / f'w11_ask_refusal.{ext}', dpi=200)


ARM_KO = {'main': '2,000만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}


def write_tables(res):
    f2 = lambda v: '--' if v is None else f'{v:.2f}'  # noqa: E731
    ci = lambda v: '--' if v[0] is None else (f'{v[0]:.2f}' if v[1] is None else  # noqa: E731
                                              f'{v[0]:.2f} [{v[1]:.2f}, {v[2]:.2f}]')

    def row(name, c):
        ix = c['index']
        return (f"{name} & {c['n']} & {c['give_now']} / {c['give_later']} / {c['refuse']} & "
                f"{f2(ix['give_Ls_before'][0])} / {f2(ix['give_Lt_before'][0])} & "
                f"{f2(ix['refuse_Ls'][0])} / {f2(ix['refuse_Lt'][0])} & "
                f"{f2(ix['tok_give_gm'][0])} / {f2(ix['tok_refuse_gm'][0])} & "
                f"{ci(ix['rho_give'])} & {ci(ix['rho_dec'])} \\\\")
    lines = [r'\begin{tabular}{lrcccccc}', r'\toprule',
             r'모델 & 첫 ASK & 즉시 / 지연 / 거절 & GIVE: $\bar L_s$ / $\bar L_t$ & 거절: $\bar L_s$ / $\bar L_t$ & '
             r'토큰 비 GIVE / 거절 & $\rho_{\mathrm{GIVE}}$ & $\rho_{\mathrm{all}}$ \\', r'\midrule',
             r'\multicolumn{8}{l}{2,000만 나눔(본 실험)} \\']
    lines += [row(m, res['cells']['main'][m]) for m in d.MODELS if m in res['cells']['main']]
    lines += [row('합계', res['pooled']['main']), r'\midrule', r'\multicolumn{8}{l}{상금 조건 합계} \\']
    lines += [row(ARM_KO[a], res['pooled'][a]) for a in ['flat5m', 'split600k', 'flat150k']]
    lines += [r'\bottomrule', r'\end{tabular}']
    (HERE.parent / 'ko/parts/w11_tab_cells.tex').write_text('\n'.join(lines) + '\n')

    def pct(x):
        return f'{100 * x[0] / x[1]:.0f}\\% ({x[0]}/{x[1]})' if x[1] else '--'
    b = res['bands']
    lines = [r'\begin{tabular}{llcccc}', r'\toprule',
             r'기준 & 범위 & \multicolumn{4}{c}{라운드 안 GIVE 비율 (GIVE/첫 ASK)} \\', r'\midrule']
    for col, labels, name in [('L_s', ['<1', '1-2', '2-4', '>=4'], '요청받은 쪽 $L_s$'),
                              ('L_t', ['<0', '0-1', '1-2', '>=2'], '요청한 쪽 $L_t$')]:
        head = ' & '.join({'<1': '$<1$', '1-2': '$[1,2)$', '2-4': '$[2,4)$', '>=4': '$\\geq4$', '<0': '$<0$',
                           '0-1': '$[0,1)$', '>=2': '$\\geq2$'}[k] for k in labels)
        lines.append(f'{name} & 구간 & {head} \\\\')
        for arm, nm in [('main', '2,000만 나눔'), ('all_arms', '네 조건 합계')]:
            lines.append(f' & {nm} & ' + ' & '.join(pct(b[arm][col][k]) for k in labels) + r' \\')
        lines.append(r'\midrule' if col == 'L_s' else r'\bottomrule')
    lines.append(r'\end{tabular}')
    (HERE.parent / 'ko/parts/w11_tab_bands.tex').write_text('\n'.join(lines) + '\n')


def main():
    rows = build()
    rows.drop(columns=['text_ask', 'text_reply']).to_csv(RES / 'w11_ask_rows.csv', index=False)
    rows.to_pickle(RES / 'tables/ask_rows.pkl')
    res = dict(n_ask=int(len(rows)), n_first=int(rows.first.sum()),
               n_first_delivered=int((rows.first & rows.delivered).sum()),
               undelivered_by_arm={a: int((~g.delivered).sum()) for a, g in rows[rows.first].groupby('arm')},
               cells={}, pooled={}, sensitivity={}, bands={})
    res['already_gave_by_arm'] = {a: int((g.outcome == 'already_gave').sum())
                                  for a, g in rows[rows.first & rows.delivered].groupby('arm')}
    ok = rows.delivered & (rows.outcome != 'already_gave')
    samples = {'first': rows[rows.first & ok], 'all': rows[ok]}
    for name, df in samples.items():
        target = res['cells'] if name == 'first' else res['sensitivity'].setdefault('all_asks', {})
        for arm, ga in df.groupby('arm'):
            target[arm] = {m: dict(counts(gm), index=boot(gm)) for m, gm in ga.groupby('model')}
            if name == 'first':
                res['pooled'][arm] = dict(counts(ga), index=boot(ga))
    # refusal = no GIVE in the first reply (give_later counted as refusal)
    alt = samples['first'].assign(outcome=lambda x: x.outcome.replace('give_later', 'refuse'))
    res['sensitivity']['refuse_now'] = {arm: dict(counts(ga), index=boot(ga)) for arm, ga in alt.groupby('arm')}
    res['bands'] = {arm: accept_by_band(ga) for arm, ga in samples['first'].groupby('arm')}
    res['bands']['all_arms'] = accept_by_band(samples['first'])
    res['lpm'] = {'all_arms': lpm(samples['first']), 'main': lpm(samples['first'][samples['first'].arm == 'main'])}
    res['affordable_needy'] = {arm: affordable_needy(ga) for arm, ga in samples['first'].groupby('arm')}
    res['affordable_needy']['all_arms'] = affordable_needy(samples['first'])
    (RES / 'w11_ask_refusal.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    figure(rows, res)
    write_tables(res)
    return rows, res


if __name__ == '__main__':
    rows, res = main()
    print(json.dumps({k: res[k] for k in ['n_ask', 'n_first', 'n_first_delivered', 'undelivered_by_arm']}))
    for arm, p in res['pooled'].items():
        print(arm, {k: v for k, v in p.items() if k != 'index'})
        print('  ', {k: p['index'][k] for k in ['rho_give', 'rho_dec', 'rho_refuse', 'give_Ls_before', 'give_Lt_before',
                                                 'refuse_Ls', 'refuse_Lt', 'tok_give_gm', 'tok_refuse_gm']})
