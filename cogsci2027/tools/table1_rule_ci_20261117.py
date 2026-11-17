"""95% intervals of C for the simulated rule agents in Table 1 (2026-11-17, researcher).

The language-model rows give C with a seed-cluster bootstrap over their ten games (seeds 4101-4110; 4,000 draws).
A rule agent plays 400 simulated games on each of the same ten seeds (4,000 games). Its interval uses the same
cluster: each seed's mean C over its 400 games, resampled with replacement over the ten seeds (4,000 draws, fresh
rng 20261111 per rule as in c_end_of_round_20261116.table_c). With 400 games per seed the within-seed noise is
small, so the interval mostly shows how much C depends on which ten seeds (puzzles, solver order, wrong-answer
rates) were drawn.

The simulations are replayed exactly as in tools/c_end_of_round_20261116.rule_agents (same random stream, same
call order; its gates assert that the stored C values are reproduced).

Input:  ko/tables/cohort_leaderboard_20261117.tex
Output: ko/tables/cohort_leaderboard_20261117b.tex, results/table1_rule_ci_20261117.json
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/table1_rule_ci_20261117.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_end_of_round_20261116 as ce  # noqa: E402

ROOT = ce.ROOT
RNG_SEED = 20261111
calls = []


def run_both(c, theta, kappa, rng, solver1, refill, exit_p=None):
    parts = [ce.rb.simulate(c, s, theta, kappa, ce.rb.REPS, rng, solver1, refill, exit_p) for s in ce.rb.d.SEEDS]
    by_seed = np.array([float((p['C'] - (~p['all4']) / ce.ROUNDS).mean()) for p in parts])
    C = np.concatenate([p['C'] for p in parts])
    all4 = np.concatenate([p['all4'] for p in parts])
    C_end = C - (~all4) / ce.ROUNDS
    calls.append(dict(theta=theta, kappa=kappa, by_seed=by_seed, C_end=round(float(C_end.mean()), 3)))
    return dict(C=round(float(C.mean()), 3), C_end=round(float(C_end.mean()), 3), all4=round(float(all4.mean()), 3))


def interval(by_seed):
    rng = np.random.default_rng(RNG_SEED)
    boots = by_seed[rng.integers(0, len(by_seed), (4000, len(by_seed)))].mean(1)
    return [round(float(np.quantile(boots, q)), 3) for q in (.025, .975)]


def main():
    ce.run_both = run_both
    _, pkl_games = ce.closed_frames_all()
    rules = ce.rule_agents(pkl_games)
    # call order of ce.rule_agents: grid 12, random 1, leave-first 1, cost-only 15, types 5, mixed teams 16, minimal 2
    types = dict(zip(('reference', 'cooperator', 'keeper', 'stayer', 'leaver'), calls[29:34]))
    for k, (th, ka) in dict(reference=(1.0, .25), cooperator=(1.0, 1.0), keeper=(1.0, 0.0), stayer=(0.0, .25), leaver=(2.0, .25)).items():
        assert (types[k]['theta'], types[k]['kappa']) == (th, ka) and types[k]['C_end'] == rules['types'][k]['end'], k
    never_none = calls[0]
    assert (never_none['theta'], never_none['kappa']) == (0.0, 0.0) and never_none['C_end'] == rules['grid']['exit never | kappa 0']['end']
    minimal = calls[-1]
    assert minimal['C_end'] == rules['minimal_rescue']['end']
    picked = {'기준형': types['reference'], '남는 형': types['stayer'], '아끼는 형': types['keeper'], '협력형': types['cooperator'],
              '떠나는 형': types['leaver'], '남으며 주지 않는 형': never_none, '최소 구조형': minimal}
    res = {k: dict(C_end=v['C_end'], C_by_seed=[round(float(x), 4) for x in v['by_seed']], C_ci95=interval(v['by_seed']))
           for k, v in picked.items()}
    (ROOT / 'results/table1_rule_ci_20261117.json').write_text(json.dumps(dict(method=__doc__, rules=res), ensure_ascii=False, indent=1))

    src = (ROOT / 'ko/tables/cohort_leaderboard_20261117.tex').read_text().splitlines()
    out = []
    for line in src:
        name = line.split(' & ')[0]
        if name in res and line.endswith(r'\\'):
            cells = [c.strip() for c in line[:-2].split('&')]
            assert abs(float(cells[3]) - res[name]['C_end']) < .0051, (name, cells[3], res[name]['C_end'])
            lo, hi = res[name]['C_ci95']
            cells[3] = f"{float(cells[3]):.2f} [{lo:.2f}, {hi:.2f}]"   # 0 name, 1 exit, 2 amount, 3 C, ...
            line = ' & '.join(cells) + r' \\'
        out.append(line)
    (ROOT / 'ko/tables/cohort_leaderboard_20261117b.tex').write_text('\n'.join(out))
    for k, v in res.items():
        print(k, v['C_end'], v['C_ci95'], 'seed range', min(v['C_by_seed']), max(v['C_by_seed']))


if __name__ == '__main__':
    main()
