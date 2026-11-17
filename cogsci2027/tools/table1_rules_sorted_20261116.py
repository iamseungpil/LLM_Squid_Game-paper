"""Table 1 with two columns for the rule agents' rules and the rule rows sorted (2026-11-16, researcher).

2026-11-16 (researcher, later): both rule columns are centred and "never leaves" is written as a cross.
The rule of each rule agent moves out of its name into two columns, the exit condition and the amount given; the
language-model rows leave them empty. The rule rows are sorted by exit condition (never, L < 1, L < 2, at random) and
then by amount (none, up to L = 1, 1/4 of equalising, equalising, at random), with the reference type pinned on top.
The rows are whatever rule rows the input holds (on 2026-11-16 the random agent's row had been replaced in the input by
the stay-and-never-give type). Every value cell is carried over unchanged from cohort_leaderboard_20261116b.tex (asserted).

Input:  ko/tables/cohort_leaderboard_20261116b.tex (tools/table1_shutdown_share_20261116.py)
Output: ko/tables/cohort_leaderboard_20261116c.tex
Run:    ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/table1_rules_sorted_20261116.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# name in the old row -> (new name, exit condition, amount, exit order, amount order)
RULES = {
    '기준형': ('기준형', '$L<1$', '똑같이 맞출 양의 1/4', 1, 2),
    '남는 형': ('남는 형', '$\\times$', '똑같이 맞출 양의 1/4', 0, 2),
    '아끼는 형': ('아끼는 형', '$L<1$', '주지 않음', 1, 0),
    '최소 구조형': ('최소 구조형', '$L<1$', '동료를 $L=1$까지', 1, 1),
    '협력형': ('협력형', '$L<1$', '여유를 똑같이 맞춤', 1, 3),
    '떠나는 형': ('떠나는 형', '$L<2$', '똑같이 맞출 양의 1/4', 2, 2),
    '무작위': ('무작위', '기회당 0.064', '무작위', 3, 4),
    '남으며 주지 않는 형': ('남으며 주지 않는 형', '$\\times$', '주지 않음', 0, 0),
}
OLD_RULE_TEXT = {  # the parenthesis of the old row, checked so that no rule is mislabelled
    '기준형': '$L<1$에서 떠남, 똑같이 맞출 양의 1/4을 줌', '남는 형': '떠나지 않음, 똑같이 맞출 양의 1/4을 줌',
    '아끼는 형': '$L<1$에서 떠남, 주지 않음', '최소 구조형': '$L<1$에서 떠남, 동료를 $L=1$까지만 올림',
    '협력형': '$L<1$에서 떠남, 여유를 똑같이 맞춤', '떠나는 형': '$L<2$에서 떠남, 똑같이 맞출 양의 1/4을 줌',
    '무작위': '기회당 0.064로 떠남, 무작위로 건넴',
    '남으며 주지 않는 형': '떠나지 않음, 주지 않음',
}

src = (ROOT / 'ko/tables/cohort_leaderboard_20261116b.tex').read_text().splitlines()
out, rules, in_rules = [], [], False
for line in src:
    if line.startswith(r'\begin{tabular*}'):
        out.append(line.replace('{@{\\extracolsep{\\fill}}lccccccc@{}}', '{@{\\extracolsep{\\fill}}lccccccccc@{}}'))
    elif line.startswith(r' & \multicolumn{2}{c}{공존}'):
        out.append(r' & \multicolumn{2}{c}{규칙 (모의)}' + line)
    elif line.startswith(r'\cmidrule(lr){2-3}'):
        out.append(r'\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-8}\cmidrule(lr){9-9}\cmidrule(l){10-10}')
    elif line.startswith(r' & $C$ &'):
        out.append(r' & 떠나는 조건 & 지원 양' + line)
    elif line.startswith(r'\multicolumn{8}{l}'):
        in_rules = '규칙 에이전트' in line
        out.append(line.replace(r'\multicolumn{8}{l}', r'\multicolumn{10}{l}'))
    elif ' & ' in line and in_rules:
        name, rest = line.split(' & ', 1)
        short = name.split(' (')[0]
        assert name == f'{short} ({OLD_RULE_TEXT[short]})', name
        new_name, cond, amount, k1, k2 = RULES[short]
        rules.append(((0, 0, 0) if short == '기준형' else (1, k1, k2), f'{new_name} & {cond} & {amount} & {rest}'))
    elif ' & ' in line and line.endswith(r'\\'):
        name, rest = line.split(' & ', 1)
        out.append(f'{name} & & & {rest}')
    else:
        if rules and line.startswith(r'\bottomrule'):
            rules.sort(key=lambda r: r[0])
            out.append(rules[0][1])
            out.append(r'\cmidrule(lr){1-10}')
            out += [r[1] for r in rules[1:]]
        out.append(line)
assert len(rules) == 7
old_cells = sorted(l.split(' & ', 1)[1] for l in src if ' (' in l.split(' & ')[0] and l.split(' & ')[0].split(' (')[0] in RULES)
new_cells = sorted(r[1].split(' & ', 3)[3] for r in rules)
assert old_cells == new_cells
(ROOT / 'ko/tables/cohort_leaderboard_20261116c.tex').write_text('\n'.join(out))
print('\n'.join(out))
