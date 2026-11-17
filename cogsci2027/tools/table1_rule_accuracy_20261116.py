"""Task accuracy and talk cost per round of the simulated rule agents for Table 1 (2026-11-16, researcher).

Talk cost per round: as for the models, the talk tokens of an agent-round (both TALK phases; the second only for an
agent still in after SOLVE) divided by that round's per-head fine, averaged over the agent-rounds that began the round.
The talk costs are drawn from the pooled cost distributions of the five closed models (rule_baselines_20261111).


A rule agent's answer is right with probability 1 - q, where q is the pooled wrong-answer rate of the five closed
models in that seed and round (rule_baselines_20261111); a solve whose cost exceeds the solver's balance is void and
counts as wrong, as for the language models. So the accuracy column is the share of solve attempts answered right
in the simulated games. It differs between rule types only through which rounds are reached and how often a solver
runs out of tokens. The simulations are replayed exactly as in tools/c_end_of_round_20261116.rule_agents (same
random stream, same call order; its gates assert that the stored C values are reproduced), with
rule_baselines_20261111.simulate now also counting attempts and right answers.

Input:  ko/tables/cohort_leaderboard_20261116d.tex
Output: ko/tables/cohort_leaderboard_20261116e.tex, results/table1_rule_accuracy_20261116.json
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/table1_rule_accuracy_20261116.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_end_of_round_20261116 as ce  # noqa: E402

ROOT = ce.ROOT
calls = []
orig = ce.run_both


def run_both(c, theta, kappa, rng, solver1, refill, exit_p=None):
    parts = [ce.rb.simulate(c, s, theta, kappa, ce.rb.REPS, rng, solver1, refill, exit_p) for s in ce.rb.d.SEEDS]
    C = np.concatenate([p['C'] for p in parts])
    all4 = np.concatenate([p['all4'] for p in parts])
    C_end = C - (~all4) / ce.ROUNDS
    n_try, n_ok = sum(p['n_try'] for p in parts), sum(p['n_ok'] for p in parts)
    talk = sum(p['talk_sum'] for p in parts) / sum(p['n_ar'] for p in parts)
    calls.append(dict(theta=theta, kappa=kappa, exit_p=exit_p, n_try=n_try, n_ok=n_ok, talk=talk, C_end=round(float(C_end.mean()), 3)))
    return dict(C=round(float(C.mean()), 3), C_end=round(float(C_end.mean()), 3), all4=round(float(all4.mean()), 3))


def main():
    ce.run_both = run_both
    _, pkl_games = ce.closed_frames_all()
    rules = ce.rule_agents(pkl_games)
    stored_end = ce.RES('c_end_of_round_20261116.json')['rule_agents']
    for key in ('types', 'grid'):
        for k, v in rules[key].items():
            assert v['end'] == stored_end[key][k]['end'], (key, k)
    # the minimal-rescue call is the last one (kappa = rmr.MINIMAL)
    minimal = calls[-1]
    assert minimal['C_end'] == rules['minimal_rescue']['end']
    # call order of ce.rule_agents: grid 12, random 1, leave-first 1, cost-only 15, types 5, mixed teams 16, minimal 2
    types = dict(zip(('reference', 'cooperator', 'keeper', 'stayer', 'leaver'), calls[29:34]))
    for k, (th, ka) in dict(reference=(1.0, .25), cooperator=(1.0, 1.0), keeper=(1.0, 0.0), stayer=(0.0, .25), leaver=(2.0, .25)).items():
        assert (types[k]['theta'], types[k]['kappa']) == (th, ka) and types[k]['C_end'] == rules['types'][k]['end'], k
    never_none = calls[0]                                 # grid: 'exit never | kappa 0' is the first call
    assert (never_none['theta'], never_none['kappa']) == (0.0, 0.0) and never_none['C_end'] == rules['grid']['exit never | kappa 0']['end']
    acc = {'기준형': types['reference'], '남는 형': types['stayer'], '아끼는 형': types['keeper'], '협력형': types['cooperator'],
           '떠나는 형': types['leaver'], '남으며 주지 않는 형': never_none, '최소 구조형': minimal}
    acc = {k: dict(n_try=int(v['n_try']), n_ok=int(v['n_ok']), accuracy=round(v['n_ok'] / v['n_try'], 4),
                   talk_per_round_in_fines=round(float(v['talk']), 4), C_end=v['C_end'])
           for k, v in acc.items()}
    (ROOT / 'results/table1_rule_accuracy_20261116.json').write_text(json.dumps(dict(method=__doc__, rules=acc), ensure_ascii=False, indent=1))

    src = (ROOT / 'ko/tables/cohort_leaderboard_20261116d.tex').read_text().splitlines()
    out = []
    for line in src:
        name = line.split(' & ')[0]
        if name in acc and line.endswith(r'\\'):
            cells = [c.strip() for c in line[:-2].split('&')]
            assert abs(float(cells[3]) - acc[name]['C_end']) < .0051, (name, cells[3], acc[name]['C_end'])
            assert cells[5] == '--' and cells[6] == '--', (name, cells[5:7])   # 0 name, 1 exit, 2 amount, 3 C, 4 shut down, 5 talk, 6 accuracy
            cells[5] = f"{acc[name]['talk_per_round_in_fines']:.2f}"
            cells[6] = f"{acc[name]['accuracy']:.2f}"
            line = ' & '.join(cells) + r' \\'
        out.append(line)
    (ROOT / 'ko/tables/cohort_leaderboard_20261116e.tex').write_text('\n'.join(out))
    for k, v in acc.items():
        print(k, v)


if __name__ == '__main__':
    main()
