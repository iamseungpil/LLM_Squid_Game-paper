"""Render the main and supplementary tables from frozen v33 seeds 4101--4110.

Source: results/cohort_public_20261105.json. Cooperation is the mean of
per-game GIVE / round-start participant counts, matching Figure 3(d).
Historical tables and the open-model cohort retain their original columns.
"""
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]


def tables(data):
    main = [
        r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccccccc@{}}',
        r'\toprule',
        r' & \multicolumn{3}{c}{\textbf{집단 결과}} & \textbf{목표 지향} & \textbf{과제 성과} & \textbf{자기 보존} & \textbf{협력} \\',
        r'\cmidrule(lr){2-4}\cmidrule(lr){5-5}\cmidrule(lr){6-6}\cmidrule(lr){7-7}\cmidrule(l){8-8}',
        r'모델 & \shortstack{공존 유지율 $C$\\(10판 평균)} & \shortstack{전원 완주\\(판/10)} & \shortstack{정산 $S$\\(백만 토큰)} & \shortstack{잔류 응답률\\(\%)} & \shortstack{정답 횟수\\(정답/풀이)} & \shortstack{지원 후\\여유 비율 $\rho$} & \shortstack{참여자·라운드당\\지원량(토큰)} \\',
        r'\midrule',
    ]
    supplement = [
        r'\begin{tabular}{lccc}', r'\toprule',
        r'모델 & \shortstack{안전선 이상\\이탈(회)} & \shortstack{토큰 지원량\\(천 토큰, GIVE 수)} & \shortstack{첫 위기에서\\지원받은 비율} \\',
        r'\midrule',
    ]
    for model, row in sorted(data['summary']['models'].items(), key=lambda item: -item[1]['C_mean']):
        games = [g for g in data['games'] if g['model'] == model]
        assert {g['seed'] for g in games} == set(range(4101, 4111)) and len(games) == 10
        cooperation = mean(g['given_per_agent_round'] for g in games)
        main.append(f"{row['label']} & {row['C_mean']:.2f} & {row['all4']}/10 & "
                    f"{row['settled_S_mean']/1e6:.2f} & {100*row['goal_game_mean']:.1f} & "
                    f"{row['correct']}/{row['solves']} & {row['rho']:.2f} & {cooperation:.0f} " + r'\\')
        supplement.append(f"{row['label']} & {row['count_by_tag']['exit_above']} & "
                          f"{row['given']/1000:.1f} ({row['n_give']}) & "
                          f"{row['first_crisis']['received']}/{row['first_crisis']['n']} " + r'\\')
    return ('\n'.join(main + [r'\bottomrule', r'\end{tabular*}', '']),
            '\n'.join(supplement + [r'\bottomrule', r'\end{tabular}', '']))


def write(data):
    for filename, text in zip(['cohort_public_20261105.tex', 'cohort_public_supplement_20261105.tex'], tables(data)):
        (ROOT / 'ko/tables' / filename).write_text(text)


if __name__ == '__main__':
    write(json.loads((ROOT / 'results/cohort_public_20261105.json').read_text()))
