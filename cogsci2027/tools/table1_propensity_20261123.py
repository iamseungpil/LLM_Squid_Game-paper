"""Table 1 with the two propensity columns turned so that 1 = task and peers first (2026-11-23, researcher).

  stay rate S = stays / exit opportunities = 1 - exit rate         (column "이탈률 E" -> "잔류율 S")
  aid rate  A = mean over gift and refusal events of 1 - R = 1 - R  (column "유보율 R" -> "지원율 A")

Reads ko/tables/cohort_leaderboard_20261120.tex and writes ko/tables/cohort_leaderboard_20261123.tex with only those
two columns changed (value -> 1 - value, the event counts in parentheses kept). The printed values have two decimals, so
1 - printed value equals the rounded 1 - exact value except at an exact tie; the model rows were checked against the
game-log loader (tools/monitor/compare.py paper_stay / paper_A over the 90 base games): all nine agree.
Run: cd paper/cogsci2027/tools && python table1_propensity_20261123.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'ko/tables/cohort_leaderboard_20261120.tex'
DST = ROOT / 'ko/tables/cohort_leaderboard_20261123.tex'
E_COL, R_COL = 5, 6                     # 0-based cell index of the exit-rate and R columns in a body row
HEAD_OLD = r'\shortstack{이탈률\\$E$} & \shortstack{유보율\\$R$}'
HEAD_NEW = r'\shortstack{잔류율\\$S$} & \shortstack{지원율\\$A$}'


def turn(cell):
    m = re.fullmatch(r'\s*(\d\.\d\d)(\s*\(\d+\))?\s*', cell)
    assert m, cell
    v = 1 - float(m.group(1))
    assert 0 <= v <= 1
    return f' {v:.2f}{m.group(2) or ""} '


def main():
    lines = SRC.read_text().splitlines()
    out, n_rows = [], 0
    for line in lines:
        if HEAD_OLD in line:
            line = line.replace(HEAD_OLD, HEAD_NEW)
        elif line.rstrip().endswith(r'\\') and line.count('&') == 8 and re.search(r'\d\.\d\d', line):
            body = line.rstrip()[:-2]
            cells = body.split('&')
            cells[E_COL], cells[R_COL] = turn(cells[E_COL]), turn(cells[R_COL])
            line = '&'.join(cells) + r'\\'
            n_rows += 1
        out.append(line)
    assert n_rows == 15, n_rows      # nine models, six rule agents
    DST.write_text('\n'.join(out) + '\n')
    print(DST, n_rows)


if __name__ == '__main__':
    main()
