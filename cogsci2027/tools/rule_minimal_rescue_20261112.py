"""One more rule agent: minimal rescue (2026-11-12).

Question: the rule agents of rule_baselines_20261111 share by "kappa x half the margin gap", which is the formula of
the sharing indicator itself, so the measured kappa equals the planted one by construction. The researcher asked for
a sharing rule written as a behaviour instead: "lift a peer to L = 1 and no further". If the indicator orders this
agent between the one that never gives and the one that equalises the two margins, kappa reads the amount of
sharing without the rule being stated in kappa.

Rule (one knob away from the reference agent, which leaves below L = 1 and gives a quarter of the gap):
  exit     leaves at its first opportunity once its round-start margin L is below 1
  sharing  when a peer taking part is below L = 1 (after a pending charge), the participant with the largest margin
           gives what lifts that peer to L = 1, but never more than half the margin gap (it does not make the peer
           richer than itself) and never more than it holds
This is the "minimal rescue" amount the paper compares the observed kappa with (construct_weights_20261110, kappa_min).

Simulator, calibration and replicate count are those of rule_baselines_20261111 (no model calls; costs and the
wrong-answer probability pooled over the 200 logged games of the five closed models, 10 seeds x 400 replicates).
The random stream is new, so the reference agent is run again here as a check against the stored values.
Exit rate = exits / all exit opportunities (the body's definition since 2026-11-12).

Data scope (paper/CLAUDE.md): calibration on 5.2 arena v33, seeds 4101-4110, base + three prize conditions.
Output: results/rule_minimal_rescue_20261112.json
Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/rule_minimal_rescue_20261112.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import rule_baselines_20261111 as rb  # noqa: E402

MINIMAL = 'minimal'
_share = rb.share


def share(bal, mask, fee, pend, kappa, rng=None, acc=None):
    """rule_baselines_20261111.share with one more mode: kappa == 'minimal' lifts the peer to L = 1 only."""
    if not (isinstance(kappa, str) and kappa == MINIMAL):
        return _share(bal, mask, fee, pend, kappa, rng, acc)
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
        lift = 1 - L[rows, j]
        g = np.where(has & other.any(1) & (gap > 0), np.minimum(lift, gap / 2) * fee, 0.0)
        g = np.minimum(g, np.maximum(bal[rows, i], 0))
        if acc is not None:
            sent = g > 0
            acc[0] += float(np.clip((g[sent] / fee[sent]) / (gap[sent] / 2), 0, 1).sum())
            acc[1] += int(sent.sum())
        bal[rows, i] -= g
        bal[rows, j] += g


def main():
    rb.share = share
    rb.THREAT = np.inf                                   # count every exit opportunity
    rng = np.random.default_rng(20261112)
    f = rb.d.load()
    cal, solver1, _, _ = rb.w1.calibrate(f)
    refill = rb.w1.Refill(rb.w1.seat_agents(f['seats']))
    pooled = cal['pooled']
    stored = json.loads((ROOT / 'results/rule_baselines_20261111.json').read_text())['types']['reference']
    stored_exit = json.loads((ROOT / 'results/exit_all_opportunities_20261112.json').read_text())['rule_agents']['types']['reference']['exit_rate']
    ref = rb.run(pooled, 1.0, .25, rng, solver1, refill)
    assert abs(ref['C'] - stored['C']) < .02 and abs(ref['exit_under_threat'] - stored_exit) < .01, (ref, stored['C'], stored_exit)
    mini = rb.run(pooled, 1.0, MINIMAL, rng, solver1, refill)
    out = dict(method=__doc__.split('Data scope')[0].strip(),
               minimal_rescue=dict(label='최소 구조형', theta=1.0, sharing='lift the peer to L = 1 only',
                                   exit_rate=mini.pop('exit_under_threat'), **mini),
               reference_rerun=dict(C=ref['C'], exit_rate=ref['exit_under_threat'], kappa_measured=ref['kappa_measured'],
                                    stored_C=stored['C'], stored_exit_rate=stored_exit))
    (ROOT / 'results/rule_minimal_rescue_20261112.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: out[k] for k in ('minimal_rescue', 'reference_rerun')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
