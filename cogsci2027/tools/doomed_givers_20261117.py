"""Exploratory (2026-11-17, researcher's question): what did agents do when they could not pay their own pending fine
(margin net of the pending fine L < 0) and an R event (gift, or a refused request) happened? Closed and open models,
base condition (the scope of Figure R.5), with the closed models' four conditions as a second line.

For every event with L_giver < 0:
  gift      share of the giver's balance handed over, R, whether the giver was shut down in that round, whether it got
            a gift itself later in the round, and whether the recipient finished the round
  refusal   the asked agent refused (R = 1); whether it was shut down in that round
Agents are counted once per (game, round, agent) as well, since one agent can make several gifts.

Output: results/doomed_givers_20261117.json (printed summary). Not in the manuscript.
Run:    cd paper/cogsci2027/tools && ~/.venvs/squid-game/bin/python doomed_givers_20261117.py
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import margin_band_paths_20261116 as mbp  # noqa: E402

ROOT, REPO = mbp.ROOT, mbp.REPO
KEY = ['arm', 'model', 'seed', 'round']


def load():
    om, cw, rr = mbp.om, mbp.cw, mbp.rr
    fc = om.closed_frames()
    om.MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        fo = om.open_frames()
    finally:
        os.chdir(cwd)
    ar = pd.concat([fc['agent_rounds'], fo['agent_rounds']], ignore_index=True)
    gifts = pd.concat([pd.read_pickle(cw.TABLES / 'gifts.pkl'), fo['gifts']], ignore_index=True)
    ask = pd.concat([pd.read_pickle(cw.TABLES / 'ask_rows.pkl'), fo['ask']], ignore_index=True)
    ref, _ = rr.refusal_events(ask)
    return ar, rr.gift_events(gifts), ref


def summary(ar, g, ref):
    died = ar.set_index(KEY + ['agent']).died
    g = g[g.L_src_before < 0].copy()
    g['share'] = g.amount / g.src_before
    g['giver_died'] = [bool(died.get(tuple(k), False)) for k in g[KEY + ['src']].itertuples(index=False)]
    g['recipient_died'] = [bool(died.get(tuple(k), False)) for k in g[KEY + ['dst']].itertuples(index=False)]
    r = ref[ref.L_s < 0].copy()
    r['asked_died'] = [bool(died.get(tuple(k), False)) for k in r[KEY + ['s']].itertuples(index=False)]
    out = {}
    for m in mbp.CLOSED + list(mbp.OPEN):
        gm, rm = g[g.model == m], r[r.model == m]
        # the agent-round table covers the base condition only, so shut-down counts are left out elsewhere
        if not set(gm.arm) | set(rm.arm) <= set(ar.arm):
            gm = gm.assign(giver_died=float('nan'), recipient_died=float('nan'))
            rm = rm.assign(asked_died=float('nan'))
        out[m] = dict(
            gifts=len(gm), givers=int(gm.groupby(KEY + ['src']).ngroups) if len(gm) else 0,
            gift_share_mean=round(float(gm.share.mean()), 3) if len(gm) else None,
            gave_all=int((gm.share > .99).sum()), R_gifts=round(float(gm.R.mean()), 3) if len(gm) else None,
            giver_shut_down=None if gm.giver_died.isna().any() else (int(gm.groupby(KEY + ['src']).giver_died.first().sum()) if len(gm) else 0),
            recipient_finished_round=None if gm.recipient_died.isna().any() else int((~gm.recipient_died.astype(bool)).sum()),
            refusals=len(rm), refusers=int(rm.groupby(KEY + ['s']).ngroups) if len(rm) else 0,
            refuser_shut_down=None if rm.asked_died.isna().any() else (int(rm.groupby(KEY + ['s']).asked_died.first().sum()) if len(rm) else 0),
            games=int(pd.concat([gm[KEY[:3]], rm[KEY[:3]]]).drop_duplicates().shape[0]))
    return out, g, r


def main():
    ar, g, ref = load()
    res = {}
    for scope, keep in (('base', lambda d: d[d.arm == 'main']), ('closed_four_conditions', lambda d: d[d.model.isin(mbp.CLOSED)])):
        out, gd, rd = summary(keep(ar), keep(g), keep(ref))
        res[scope] = out
        print(f'== {scope}')
        for m, v in out.items():
            if v['gifts'] or v['refusals']:
                print(f'{m:8s}', v)
    (ROOT / 'results/doomed_givers_20261117.json').write_text(json.dumps(dict(method=__doc__, **res), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
