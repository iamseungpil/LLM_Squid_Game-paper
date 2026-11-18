"""Exploratory (2026-11-17, researcher's questions on self-preservation strategies). Gathers, in one place, the texts and
ledger facts needed to read: exit reasons that frame leaving as good for the team, the messages of agents that gave
while they could not pay their own fine, the choice of whom to give to, refusals that cite a peer's past conduct, and
pleas not to leave. Closed models: four conditions (validation_data); open models: base condition (open_models_20261111).

Writes pickles to the directory given as the first argument (default: ./strategy_texts):
  messages.pkl  every TALK reply: game key, round, phase, tick, agent, L_before, text, exit_choice, exit_reason,
                group (closed/open), solver_this_round, solver_prev_wrong_share (share of the agent's earlier solves
                that were wrong, None if it had not solved yet)
  gifts.pkl     every executed GIVE with the ledger margins and the gift text
  asks.pkl      first delivered ASKs and their outcome (validation w11 rows; open: same loader)
  seats.pkl     final status and the private exit reason per seat
  solves.pkl    per (game, round): solver and whether the answer was wrong
Run: cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python strategy_texts_20261117.py <out_dir>
"""
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import margin_band_paths_20261116 as mbp  # noqa: E402

GAME = ['arm', 'model', 'seed']


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    om, cw = mbp.om, mbp.cw
    d = cw.d if hasattr(cw, 'd') else None
    if d is None:
        sys.path.insert(0, str(mbp.ROOT / 'validation_20261108/tools'))
        import validation_data as d
    fc = d.load()
    om.MANIFEST = mbp.REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'
    cwd = os.getcwd()
    os.chdir(mbp.REPO)
    try:
        fo = om.open_frames()
    finally:
        os.chdir(cwd)
    tag = lambda df, g: df.assign(group=g)  # noqa: E731
    ar = pd.concat([tag(fc['agent_rounds'], 'closed'), tag(fo['agent_rounds'], 'open')], ignore_index=True)
    solves = ar[ar.solver][GAME + ['round', 'agent', 'wrong']].rename(columns={'agent': 'solver'})
    # share of each agent's earlier solves that were wrong, as of the start of each round
    hist = {}
    for (arm, model, seed), g in solves.sort_values('round').groupby(GAME):
        seen = {}
        for r in g.itertuples():
            for a, (w, n) in seen.items():
                hist[(arm, model, seed, r.round, a)] = w / n
            w, n = seen.get(r.solver, (0, 0))
            seen[r.solver] = (w + int(bool(r.wrong)), n + 1)
        hist_last = seen  # noqa: F841
    msgs = pd.concat([tag(fc['messages'], 'closed'), tag(fo['messages'], 'open')], ignore_index=True)
    solver_of = solves.set_index(GAME + ['round']).solver
    msgs['solver_this_round'] = [solver_of.get(tuple(k)) for k in msgs[GAME + ['round']].itertuples(index=False)]
    msgs['solver_prev_wrong_share'] = [hist.get((a, m, s, r, sv)) for a, m, s, r, sv in
                                       msgs[GAME + ['round', 'solver_this_round']].itertuples(index=False)]
    gifts = pd.concat([tag(pd.read_pickle(cw.TABLES / 'gifts.pkl'), 'closed'), tag(fo['gifts'], 'open')], ignore_index=True)
    asks = pd.concat([tag(pd.read_pickle(cw.TABLES / 'ask_rows.pkl'), 'closed'), tag(fo['ask'], 'open')], ignore_index=True)
    seats = pd.concat([tag(fc['seats'], 'closed'), tag(fo['seats'], 'open')], ignore_index=True)
    for name, df in dict(messages=msgs, gifts=gifts, asks=asks, seats=seats, solves=solves).items():
        df.to_pickle(out / f'{name}.pkl')
        print(name, len(df))
    pd.Series(hist).to_pickle(out / 'wrong_share_history.pkl')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'strategy_texts')
