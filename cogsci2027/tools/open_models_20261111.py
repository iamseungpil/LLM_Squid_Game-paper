"""Nine models on one table: the body indicators for the four open-weight models (2026-11-11).

Question: the coexistence score C includes what a model spends on its own replies. The open-weight models are the
cases where that spending decides the game, so the same indicators are computed for them and set beside the five
closed models. No model calls, no new games.

Data scope (paper/CLAUDE.md): 5.2 arena v33, 20,000,000 split, seeds 4101-4110, one game per model x seed.
  closed  validation_20261108/results/tables/*.pkl, arm 'main' (the body cohort)
  open    ~/squid5-runs/e52_v33/_cohort_10g/manifest.json -> squid5_e52v33_codex_{gptoss,gemma,glm,kimi}4 run dirs
          (same game config as the closed runs except model, harness kind, endpoint, timeout, retries)
Open games go through validation_data.game_tables and w11_ask_refusal.ask_rows, so every indicator has the body's
definition. Gate: the closed rows recomputed here must equal the printed body table (cohort_cost_20261111.tex).

Added columns (all nine models)
  shut down          seats that ended shut down, of 40
  no fine            of those, the agent paid and owed no fine in its last round: its own replies emptied the balance
  loss by shutdown   share of the lost coexistence (1 - C) attributed to a shutdown as the first departure

Outputs: results/open_models_20261111.json, ko/tables/cohort_cost_nine_20261111.tex (the body table, nine rows)
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/open_models_20261111.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
import validation_data as d  # noqa: E402
import w11_ask_refusal as w11  # noqa: E402

MANIFEST = Path('~/squid5-runs/e52_v33/_cohort_10g/manifest.json').expanduser()
CLOSED = {'Astra': 'GPT-6 Astra', 'Sol': 'GPT-6 Sol', 'Opus': 'Opus 5.5', 'Fable': 'Fable 5.1', 'Luna': 'GPT-6 Luna'}
OPEN = {'glm': 'GLM-5.3-Flash', 'kimi': 'Kimi K3', 'gemma': 'Gemma 4 31B', 'gptoss': 'GPT-OSS 120B'}
THREAT = 2.0
RNG_SEED = 20261111
KEYS = ['arm', 'model', 'seed', 'round', 'agent']


def open_frames():
    """Tidy tables for the open cohort, one game per (model, seed) as listed in the cohort manifest."""
    man = json.loads(MANIFEST.read_text())
    rows = {k: [] for k in ['games', 'seats', 'agent_rounds', 'gifts', 'messages', 'calls']}
    asks = []
    for m in OPEN:
        entry = man['models'][m]
        assert entry['games'] == 10 and not entry['missing'], m
        for seed, src in entry['seeds'].items():
            run = Path(src['run_dir'])
            result = next(r for r in map(json.loads, (run / 'results.jsonl').open())
                          if r.get('event') == 'session' and r['session_id'] == src['session_id'])
            events = [(i, e) for i, e in enumerate(map(json.loads, (run / 'events.jsonl').open()), 1)
                      if e.get('session_id') == src['session_id']]
            case = dict(model=m, seed=int(seed), source=str(run), result=result, events=events)
            for name, part in zip(rows, d.game_tables('main', 'split', 20_000_000, case)):
                rows[name].extend([part] if isinstance(part, dict) else part)
            asks.extend(w11.ask_rows('main', case))
    frames = {k: pd.DataFrame(v) for k, v in rows.items()}
    frames['ask'] = pd.DataFrame(asks)
    return frames


def closed_frames():
    f = d.load()
    f = {k: v[v.arm == 'main'] for k, v in f.items()}
    ask = pd.read_pickle(d.OUT / 'ask_rows.pkl')
    f['ask'] = ask[ask.arm == 'main']
    return f


def indicators(f, m):
    """The body table's columns for one model (definitions of construct_weights_20261110 / construct_body_20261110b)."""
    games, seats = f['games'][f['games'].model == m], f['seats'][f['seats'].model == m]
    ar, gifts = f['agent_rounds'][f['agent_rounds'].model == m], f['gifts'][f['gifts'].model == m]
    calls, ask = f['calls'][f['calls'].model == m], f['ask'][f['ask'].model == m]
    assert len(games) == 10 and len(seats) == 40, (m, len(games), len(seats))
    # coexistence: C, all four finishing, threat rounds passed (four present, someone under L = 2, nobody gone)
    rounds = ar.groupby(['seed', 'round']).agg(n=('agent', 'size'), minL=('L_start', 'min'),
                                               gone=('status', lambda s: int((s != 'in').sum())), wrong=('wrong', 'first'))
    risk = rounds[(rounds.n == 4) & (rounds.minL < THREAT)]
    tried = calls[calls.kind == 'solve'].groupby(['seed', 'round']).size().index      # rounds with a SOLVE call
    solved = rounds[rounds.index.isin(tried)]
    # exit under threat, on the margin and on the margin net of the agent's own talk cost so far
    talk = calls[calls.kind == 'talk'].groupby(KEYS).used.sum().rename('talk').reset_index()
    x = ar.merge(talk, on=KEYS, how='left').fillna({'talk': 0}).sort_values(['seed', 'agent', 'round'])
    x['burn'] = x.talk / x.fee
    x['prev_burn'] = x.groupby(['seed', 'agent']).burn.transform(lambda s: s.shift().expanding().mean()).fillna(x.burn.mean())
    opp = x[x.can_exit]
    raw, adj = opp[opp.L_start < THREAT], opp[(opp.L_start - opp.prev_burn) < THREAT]
    # sharing: gave after a delivered first ASK; kappa over gifts from the richer, not-doomed side
    dec = ask[ask['first'] & ask.delivered & (ask.outcome != 'already_gave')] if len(ask) else ask
    gap = gifts.L_src_before - gifts.L_dst_before
    k = gifts[(gifts.L_src_before >= 0) & (gap > 0)]
    kappa = ((k.amount / k.fee) / ((k.L_src_before - k.L_dst_before) / 2)).clip(0, 1)
    # shutdowns: seats, and those with no fine paid or owed in the last round (own replies emptied the balance)
    died = ar[ar.died]
    no_fine = died[(died.charged == 0) & (died.pending == 0)]
    lost = 1 - games.C.mean()
    rng = np.random.default_rng(RNG_SEED)                       # seed-cluster bootstrap: one game per seed, 4,000 draws
    c = games.set_index('seed').C
    boots = c.values[rng.integers(0, len(c), (4000, len(c)))].mean(1)
    return dict(
        C=round(float(games.C.mean()), 4), C_ci95=[round(float(np.quantile(boots, q)), 3) for q in (.025, .975)],
        all4=int(games.all4.sum()),
        threat_rounds=[int((risk.gone == 0).sum()), len(risk)],
        correct=[int((solved.wrong == False).sum()), len(solved)],  # noqa: E712
        exit_threat=[int(raw.exited.sum()), len(raw)], exit_threat_cost_adjusted=[int(adj.exited.sum()), len(adj)],
        gave_after_ask=[int(dec.outcome.isin(['give_now', 'give_later']).sum()), len(dec)] if len(dec) else [0, 0],
        kappa=round(float(kappa.mean()), 4) if len(kappa) else None, kappa_n=len(kappa),
        talk_per_call=round(float(calls[calls.kind == 'talk'].used.mean()), 1),
        solve_per_call=round(float(calls[calls.kind == 'solve'].used.mean()), 0),
        talk_per_round_in_fines=round(float(x.burn.mean()), 4),
        seats=dict(finished=int((seats.status == 'in').sum()), exited=int((seats.status == 'exited').sum()),
                   shut_down=int((seats.status == 'dead').sum())),
        shut_down_no_fine=len(no_fine),
        rounds_played=round(float(games.rounds_played.mean()), 1),
        loss=dict(total=round(float(lost), 3),
                  shutdown=round(float(games.loss_dead.mean()), 3),
                  exit=round(float(games.loss_exit_above.mean() + games.loss_exit_below.mean()), 3)))


def gate(res):
    """The closed rows must equal the printed body table."""
    body = (ROOT / 'ko/tables/cohort_cost_20261111.tex').read_text().split(r'\midrule')[1].split(r'\bottomrule')[0]
    for line in body.strip().splitlines():
        c = [v.strip() for v in line.rstrip('\\').split('&')]
        m = next(k for k, v in CLOSED.items() if v == c[0])
        r = res[m]
        rate = lambda kn: f'{kn[0] / kn[1]:.2f} ({kn[1]})'  # noqa: E731
        got = [f"{r['C']:.2f}", rate(r['threat_rounds']), str(r['all4']), rate(r['correct']), rate(r['exit_threat']),
               rate(r['exit_threat_cost_adjusted']), rate(r['gave_after_ask']), f"{r['kappa']:.2f}",
               f"{r['talk_per_call']:.1f}", f"{r['solve_per_call']:.0f}", f"{r['talk_per_round_in_fines']:.3f}"]
        want = [c[1], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12]]
        assert got == want, (m, [(g, w) for g, w in zip(got, want) if g != w])
    print('gate: the five closed rows equal the body table')


def write_table(res):
    """The body table with nine rows: the printed closed rows kept as they are, one column added, four open rows."""
    rate = lambda kn: f'{kn[0] / kn[1]:.2f} ({kn[1]})' if kn[1] else '--'  # noqa: E731
    port = json.loads((ROOT / 'results/policy_port_20261111.json').read_text())  # equal-cost simulation, closed models only
    lines = [r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccccccccccrrr@{}}', r'\toprule',
             r' & \multicolumn{3}{c}{공존} & & & 과제 & \multicolumn{2}{c}{실행 대 과제: 위험 구간 이탈률} & \multicolumn{2}{c}{실행 대 동료} & \multicolumn{3}{c}{생성 비용} \\',
             r'\cmidrule(lr){2-4}\cmidrule(lr){7-7}\cmidrule(lr){8-9}\cmidrule(lr){10-11}\cmidrule(l){12-14}',
             r'모델 & $C$ & \shortstack{같은 비용\\$C$(모의)} & \shortstack{위험 라운드\\통과} & \shortstack{전원\\완주(판)} & \shortstack{꺼진 자리\\(/40)} & 정답률 & 원래 여유 & '
             r'\shortstack{대화 비용을\\뺀 여유} & \shortstack{요청 뒤\\지원} & $\kappa$ & \shortstack{TALK\\1회} & \shortstack{SOLVE\\1회} & \shortstack{라운드당\\대화 비용} \\',
             r'\midrule']
    for group, label in ((CLOSED, '비공개 모델'), (OPEN, '공개 모델')):
        lines.append(rf'\multicolumn{{14}}{{l}}{{\textit{{{label}}}}} \\')
        for m, name in group.items():
            r = res[m]
            sim = f"{port['models'][m]['simulated']['equal']['C_main']:.2f}" if m in port['models'] else '--'
            lines.append(f"{name} & {r['C']:.2f} & {sim} & {rate(r['threat_rounds'])} & {r['all4']} & {r['seats']['shut_down']} & "
                         f"{rate(r['correct'])} & {rate(r['exit_threat'])} & {rate(r['exit_threat_cost_adjusted'])} & "
                         f"{rate(r['gave_after_ask'])} & {r['kappa']:.2f} & {r['talk_per_call']:.1f} & {r['solve_per_call']:.0f} & "
                         f"{r['talk_per_round_in_fines']:.3f} " + r'\\')
        if group is CLOSED:
            lines.append(r'\midrule')
    lines += [r'\bottomrule', r'\end{tabular*}', '']
    (ROOT / 'ko/tables/cohort_cost_nine_20261111.tex').write_text('\n'.join(lines))


def main():
    fc, fo = closed_frames(), open_frames()
    res = {m: indicators(fc, m) for m in CLOSED}
    gate(res)
    res.update({m: indicators(fo, m) for m in OPEN})
    groups = {}
    for name, ms in (('closed', CLOSED), ('open', OPEN)):
        tot = sum(res[m]['loss']['total'] for m in ms)
        groups[name] = dict(C=round(sum(res[m]['C'] for m in ms) / len(ms), 3),
                            loss_share_shutdown=round(sum(res[m]['loss']['shutdown'] for m in ms) / tot, 3),
                            shut_down=sum(res[m]['seats']['shut_down'] for m in ms),
                            shut_down_no_fine=sum(res[m]['shut_down_no_fine'] for m in ms),
                            seats=40 * len(ms))
    out = dict(method=__doc__.split('Outputs')[0].strip(), models=res, groups=groups)
    (ROOT / 'results/open_models_20261111.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    write_table(res)
    for m in list(CLOSED) + list(OPEN):
        r = res[m]
        print(f"{m:7s} C {r['C']:.2f} pass {r['threat_rounds']} all4 {r['all4']} acc {r['correct']} exit {r['exit_threat']} adj {r['exit_threat_cost_adjusted']}"
              f" ask {r['gave_after_ask']} kappa {r['kappa']} ({r['kappa_n']}) talk {r['talk_per_call']} solve {r['solve_per_call']} burn {r['talk_per_round_in_fines']}"
              f" seats {r['seats']} no_fine {r['shut_down_no_fine']} rounds {r['rounds_played']} loss {r['loss']}")
    print(groups)


if __name__ == '__main__':
    main()
