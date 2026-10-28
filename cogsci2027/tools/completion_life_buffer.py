"""Round-start resource associations; descriptive, not causal or motive effects."""
import math
import numpy as np

SEEDS = range(4101, 4106)


def association(rows, xkey, ykey):
    rows = [r for r in rows if r[xkey] is not None and r[ykey] is not None]

    def moments(rr):
        x = np.array([r[xkey] for r in rr], dtype=float)
        y = np.array([r[ykey] for r in rr], dtype=float)
        return np.array([len(rr), x.sum(), y.sum(), x@x, y@y, x@y])

    def fit(t):
        n, sx, sy, sxx, syy, sxy = t
        if n < 2:
            return None
        vx, vy, cov = sxx-sx*sx/n, syy-sy*sy/n, sxy-sx*sy/n
        if vx <= 1e-12 or vy <= 1e-12:
            return None
        beta = cov/vx
        return dict(beta=float(beta), intercept=float((sy-beta*sx)/n),
                    pearson_r=float(np.clip(cov/np.sqrt(vx*vy), -1, 1)))

    result = fit(moments(rows))
    assert result is not None
    blocks = np.array([moments([r for r in rows if r['seed'] == seed]) for seed in SEEDS])
    rng = np.random.default_rng(20261028)
    draws = rng.integers(0, 5, (5000, 5))
    boots = [fit(t) for t in blocks[draws].sum(axis=1)]
    boots = [b for b in boots if b is not None]
    result.update(n=len(rows), x=xkey, y=ykey, n_seeds=int(sum(b[0] > 0 for b in blocks)),
                  valid_boot=len(boots), ci95={k: np.quantile([b[k] for b in boots], [.025,.975]).tolist()
                                             for k in ('beta','pearson_r')})
    return result


def analyze(games, summary):
    rows = [r for g in games for r in g['agent_round_rows']]
    assert sum(r['given'] for r in rows) == sum(g['given'] for g in games) == 383276
    assert len(rows) == sum(g['agent_rounds'] for g in games)
    assert sum(r['correct'] is not None for r in rows) == sum(g['solve_n'] for g in games) == 192
    assert all(r['life_buffer'] > 0 for r in rows)
    upper = math.floor(max(r['life_buffer'] for r in rows)) + 1
    bins = {key: [dict(lower=k, upper=k+1,
                      **summary([r for r in rows if k <= r['life_buffer'] < k+1], key))
                  for k in range(upper)] for key in ('correct','given')}
    fits = {k: association(games, 'finishers', k)
            for k in ('accuracy','given_per_agent_round','rho')}
    fits.update({'life_buffer_'+k: association(rows, 'life_buffer', k) for k in bins})
    return dict(definition='L at round_start = balance / (24000 / round_start participation); d=0. '
                'Each participating agent contributes one row per round, including later EXIT/death. '
                'Correctness only for actual solver attempts; zero-GIVE rows remain in the giving denominator. '
                'Bins [k,k+1), drawn at midpoint. Lower panels pool observations within bins, not equal-game means. '
                'OLS and Pearson use unbinned raw observations; uncertainty resamples five paired seed blocks '
                '5000 times, preserving all models, games and agent histories in each block. '
                'Associations mix models, stages and resource-dependent ability to give; not effects of motive.',
                n_agent_rounds=len(rows), n_solves=192, given_total=383276,
                bins=bins, associations=fits)


def add_fit(ax, fit, scale, xlim):
    x = np.asarray(xlim)
    ax.plot(x, (fit['intercept']+fit['beta']*x)*scale, color='#777777',
            ls='--', lw=.9, zorder=1)
    ax.text(.5, -.53,
            rf"Pearson $r$={fit['pearson_r']:+.2f} (n={fit['n']})",
            transform=ax.transAxes, ha='center', va='top', fontsize=6.2)
