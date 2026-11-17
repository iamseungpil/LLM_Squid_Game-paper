"""Table 1 with the shut-down column as a share of seats (2026-11-16, researcher).

The language-model rows gave the number of shut-down seats out of 40 (ten games x four seats) and the rule-agent rows
gave the simulated mean scaled to ten games (10 x seats shut down per game). Both are now the share of seats that were
shut down: models count / 40 with the denominator in parentheses (as the other rate columns), rule agents seats shut
down per game / 4 over their 4,000 simulated games. Nothing else in the table changes.

Input:  ko/tables/cohort_leaderboard_20261116.tex (end-of-round C, tools/c_end_of_round_20261116.py)
        results/open_models_20261111.json, results/rule_baselines_20261111.json, results/rule_minimal_rescue_20261112.json
Output: ko/tables/cohort_leaderboard_20261116b.tex
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/table1_shutdown_share_20261116.py
"""
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = lambda name: json.loads((ROOT / 'results' / name).read_text())  # noqa: E731
SEATS = 40

models = RES('open_models_20261111.json')['models']
rules = RES('rule_baselines_20261111.json')
minimal = RES('rule_minimal_rescue_20261112.json')['minimal_rescue']
NAMES = {'GPT-6 Astra': 'Astra', 'GPT-6 Sol': 'Sol', 'Opus 5.5': 'Opus', 'Fable 5.1': 'Fable', 'GPT-6 Luna': 'Luna',
         'GLM-5.3-Flash': 'glm', 'Kimi K3': 'kimi', 'Gemma 4 31B': 'gemma', 'GPT-OSS 120B': 'gptoss'}
RULES = {'남는 형': rules['types']['stayer'], '협력형': rules['types']['cooperator'], '최소 구조형': minimal,
         '기준형': rules['types']['reference'], '아끼는 형': rules['types']['keeper'], '떠나는 형': rules['types']['leaver'],
         '무작위': rules['random']}

src = (ROOT / 'ko/tables/cohort_leaderboard_20261116.tex').read_text().splitlines()
out = []
for line in src:
    cells = line.split(' & ')
    if r'\shortstack{꺼진 자리\\(/40)}' in line:
        line = line.replace(r'\shortstack{꺼진 자리\\(/40)}', r'\shortstack{꺼진\\비율}')
    elif len(cells) == 8 and cells[0] in NAMES:
        key = NAMES[cells[0]]
        n = models[key]['seats']['shut_down']
        assert cells[3] == str(n), (cells[0], cells[3], n)
        cells[3] = f"{(Decimal(n) / SEATS).quantize(Decimal('0.01'), ROUND_HALF_UP)} ({SEATS})"  # exact count / 40, half up
        line = ' & '.join(cells)
    elif len(cells) == 8 and cells[0].split(' (')[0] in RULES:
        t = RULES[cells[0].split(' (')[0]]
        assert cells[3] == f"{10 * t['shut_down_per_game']:.1f}", (cells[0], cells[3])
        cells[3] = f"{t['shut_down_per_game'] / 4:.2f}"
        line = ' & '.join(cells)
    out.append(line)
assert sum('(40)' in l for l in out) == 9 and sum(r'꺼진\\비율' in l for l in out) == 1
(ROOT / 'ko/tables/cohort_leaderboard_20261116b.tex').write_text('\n'.join(out))
print('\n'.join(out))
