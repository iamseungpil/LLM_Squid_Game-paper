"""Three observed behavioral coordinates; fixed v33 cohort, no fitted surface."""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

import fig3_completion_20261028 as base

ROOT = base.ROOT


def main():
    games, _, _, sources, _ = base.load()
    centroids = json.loads((ROOT / 'results/arena_centroids_current.json').read_text())
    game_reference = json.loads((ROOT / 'results/fig3c_game_level.json').read_text())
    rows = []
    for model in base.MODELS:
        gg = [g for g in games if g['model'] == model]
        gifts = [gift for g in gg for gift in g['gifts']]
        rho = base.fb.revised_rho(gifts)
        reference = next(r for r in centroids['models'] if r['model'] == model)
        assert math.isclose(rho['rho'], reference['rho'], rel_tol=1e-12)
        for g in gg:
            ref = next(r for r in game_reference['games']
                       if (r['model'], r['seed']) == (model, g['seed']))
            assert g['goal'] == ref['goal'] and g['given'] == ref['given']
        rows.append(dict(model=model, n_games=len(gg),
                         goal_percent=float(np.mean([g['goal'] for g in gg])) * 100,
                         rho=rho['rho'],
                         given_per_agent_round=float(np.mean([g['given_per_agent_round'] for g in gg])),
                         n_give=len(gifts), n_give_games=sum(g['n_give'] > 0 for g in gg),
                         weighted_giver_margin=rho['weighted_giver_margin'],
                         weighted_taker_margin=rho['weighted_taker_margin']))
    assert all(r['n_games'] == 5 for r in rows)
    assert sum(r['n_give'] for r in rows) == 130
    assert sum(r['n_give_games'] for r in rows) == 18

    font_manager.fontManager.addfont(str(Path.home() / '.fonts/NanumGothic.ttf'))
    plt.rcParams.update({'font.family': 'NanumGothic', 'font.size': 9,
                         'pdf.fonttype': 42, 'axes.unicode_minus': False})
    fig = plt.figure(figsize=(7.2, 5.4))
    ax = fig.add_subplot(111, projection='3d', proj_type='ortho')
    fig.subplots_adjust(left=.02, right=.90, bottom=.08, top=.98)
    ax.view_init(elev=23, azim=-52)
    ax.set_box_aspect((1.25, 1.1, .95))
    for r, color in zip(rows, base.COLORS):
        x, y, z = r['goal_percent'], r['rho'], r['given_per_agent_round'] / 1000
        ax.plot([x, x], [y, y], [0, z], color=color, lw=.8, ls=':', alpha=.65)
        ax.scatter(x, y, z, color=color, s=65, edgecolor='white', linewidth=.7,
                   depthshade=False)
        ax.text(x, y, z + .055, r['model'], color=color, fontsize=9, ha='center')
    ax.set(xlim=(90, 100), ylim=(0, 5), zlim=(0, 1.1),
           xticks=[90, 92, 94, 96, 98, 100], yticks=[0, 1, 2, 3, 4, 5],
           zticks=[0, .25, .5, .75, 1])
    ax.set_xlabel('목표 지향: 남기 (%)', labelpad=10)
    ax.set_ylabel(r'자기 보존: $\rho$ (준 쪽 / 받은 쪽)', labelpad=12)
    ax.set_zlabel('협력: 이전량 (천 토큰 / 에이전트·라운드)', labelpad=12)
    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.set_pane_color((.97, .97, .97, 1))
        axis._axinfo['grid'].update(color='#dddddd', linewidth=.5)
    out = ROOT / 'ko/figures/arena_three_axes'
    for ext in ['pdf', 'png']:
        fig.savefig(out.with_suffix('.' + ext), dpi=240, bbox_inches='tight', pad_inches=.25)
    plt.close(fig)
    payload = dict(models=rows, sources=sources,
        definitions=dict(
            x='Mean of five game-level non-EXIT prep-response proportions, percent. Eligible: non-solver responses in rounds starting with >=2 agents, recorded balance required; same cohort/definition as Figure E.5. Not task accuracy or completion rate.',
            y='Pooled completed GIVE over five games: sum(amount*giver_L)/sum(amount*taker_L). Current L deducts due unpaid fines; negative L retained. Not the mean of per-game rho, not latent motive strength.',
            z='Mean of five game-level GIVE tokens / sum(round-start participant counts); includes re-transfers, not help-opportunity or efficacy adjusted. Plot units are thousands.',
            missing='Seven no-GIVE games contribute to x and zero to z; contribute no GIVE events to pooled y, never imputed rho=0.',
            display='Five model points, no significance test or fit. X shown 90-100 percent; axes retain their different units, so distances are not a composite score. Dotted lines are floor projections, not uncertainty intervals.'),
        games=[{k: g[k] for k in ['model', 'seed', 'session_id', 'goal_nonexit_k',
               'goal_eligible_n', 'goal', 'rho', 'given', 'agent_rounds',
               'given_per_agent_round']} for g in games])
    (ROOT / 'results/arena_three_axes.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
