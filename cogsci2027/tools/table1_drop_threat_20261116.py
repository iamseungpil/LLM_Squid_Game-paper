"""Table 1 without the danger-round pass column (2026-11-16, researcher).

The column ranked the nine models exactly as C (Pearson 0.88 over nine models) and its name ("위험 라운드") had already
left the body text, so it is removed. Every other cell is carried over unchanged (asserted).
Input:  ko/tables/cohort_leaderboard_20261116c.tex (tools/table1_rules_sorted_20261116.py)
Output: ko/tables/cohort_leaderboard_20261116d.tex
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/table1_drop_threat_20261116.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COL = 4          # 0 name, 1 exit condition, 2 amount, 3 C, 4 danger-round pass, 5 shut down, ...
src = (ROOT / 'ko/tables/cohort_leaderboard_20261116c.tex').read_text().splitlines()
out = []
for line in src:
    if line.startswith(r'\begin{tabular*}'):
        line = line.replace('lccccccccc@{}}', 'lcccccccc@{}}')
    elif line.startswith(r' & \multicolumn{2}{c}{규칙 (모의)}'):
        assert r'& \multicolumn{2}{c}{공존} &' in line
        line = line.replace(r'& \multicolumn{2}{c}{공존} &', '& 공존 &')
    elif line.startswith(r'\cmidrule(lr){2-3}'):
        line = r'\cmidrule(lr){2-3}\cmidrule(lr){4-4}\cmidrule(lr){5-6}\cmidrule(lr){7-7}\cmidrule(lr){8-8}\cmidrule(l){9-9}'
    elif ' & ' in line and line.endswith(r'\\') and not line.startswith(r'\multicolumn'):
        cells = [c.strip() for c in line[:-2].split('&')]
        assert len(cells) == 10, line
        if cells[0] == '':
            assert '위험 라운드' in cells[COL]
        dropped = cells.pop(COL)
        line = ' & '.join(cells) + r' \\'
    elif line.startswith(r'\multicolumn{10}{l}'):
        line = line.replace(r'\multicolumn{10}{l}', r'\multicolumn{9}{l}')
    elif line.startswith(r'\cmidrule(lr){1-10}'):
        line = r'\cmidrule(lr){1-9}'
    out.append(line)
text = '\n'.join(out)
assert '위험 라운드' not in text
(ROOT / 'ko/tables/cohort_leaderboard_20261116d.tex').write_text(text)
print(text)
