"""Token thrift (소모율) for Table 1, replacing the talk-cost column (2026-11-20, researcher).

Definition. For every agent-round (an agent taking part when the round starts), spend = the tokens the agent's own
calls used in that round, both TALK phases and its SOLVE if it was the solver, counted gross (before a correct
answer refunds the solve). Thrift of that agent-round = 1 - min(1, spend / the agent's balance at the round start),
i.e. the share of the tokens it held at the round start that its own generation did not use. A model's thrift is the
mean over its agent-rounds. 1 = generated nothing; 0 = its own generation used everything it held (the case of an
agent shut down by its own reply). The value lies in [0, 1] by construction, higher = more frugal. Refunds,
fines and gifts do not enter the numerator, so the column shares no term with accuracy (right answers / attempts).

Language models: the base v33 cohort as the repository's game-log monitor reads it (tools/monitor/compare.py,
picks e52_v33/ over web/data/runs, the .xz logs unpacked to a temporary copy). Gate: the same loader reproduces the
printed talk cost and accuracy of Table 1 for every model.

Rule agents: the simulations of rule_baselines_20261111.simulate are replayed exactly as in
c_end_of_round_20261116.rule_agents (same random stream, same call order; its gates assert that the stored C values
are reproduced), with a copy of simulate that also sums each agent-round's spend (prep talk, the solver's paid solve,
talk after the result) over its round-start balance. The copy draws no extra random numbers.

The old paths ~/squid5-runs/... are read through HOME pointed at a folder whose squid5-runs/e52_v33 and e52_v33ab
link to result/2026-10-20/e52_v33/runs and result/2026-11-03/e52_v33ab/runs.

Input:  ko/tables/cohort_leaderboard_20261117b.tex
Output: ko/tables/cohort_leaderboard_20261120.tex, results/table1_thrift_20261120.json
Run:    HOME=<folder with squid5-runs links> ~/.venvs/squid-game/bin/python paper/cogsci2027/tools/table1_thrift_20261120.py
"""
import json
import lzma
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                    # paper/cogsci2027
REPO = ROOT.parents[1]                                # the project repository that holds paper/ as a submodule
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / 'tools/monitor'))
sys.path.insert(0, str(REPO))

MODEL_ROWS = {'gpt-6-astra': 'GPT-6 Astra', 'gpt-6-sol': 'GPT-6 Sol', 'claude-opus-5-5': 'Opus 5.5',
              'claude-fable-5-1': 'Fable 5.1', 'gpt-6-luna': 'GPT-6 Luna', 'glm-5.3-flash:cloud': 'GLM-5.3-Flash',
              'kimi-k3:cloud': 'Kimi K3', 'gemma4:31b-cloud': 'Gemma 4 31B', 'gpt-oss:120b-cloud': 'GPT-OSS 120B'}


def thrift_of_round(spend, start_balance):
    return 1.0 - min(1.0, spend / start_balance) if start_balance > 0 else 0.0


# ================================================================================================= language models
def model_thrift():
    import compare as cp
    orig = cp.paper_game

    def paper_game(evs, result):
        out = orig(evs, result)
        if out is None:
            return out
        starts = {e['round']: e for e in evs if e.get('event') == 'round_start'}
        spend = {}
        for e in evs:
            if e.get('event') == 'call' and e.get('kind') in ('talk', 'solve'):
                k = (e.get('round'), e.get('agent'))
                spend[k] = spend.get(k, 0) + (e.get('used') or 0)
        out['thrift'] = [thrift_of_round(spend.get((r, a), 0), rs['balances'][a])
                         for r, rs in sorted(starts.items()) for a in rs.get('taking_part') or []]
        return out
    orig_model = cp.paper_model

    def paper_model(games):
        out = orig_model(games)
        if out is not None:
            out['thrift_all'] = [x for g in games if g.get('paper') for x in g['paper']['thrift']]
        return out
    cp.paper_game, cp.paper_model = paper_game, paper_model
    src = REPO / 'web/data/runs/e52_v33'
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / 'e52_v33'
        for f in src.rglob('*'):
            if f.is_file():
                to = dst / f.relative_to(src)
                to.parent.mkdir(parents=True, exist_ok=True)
                if f.suffix == '.xz':
                    to.with_suffix('').write_bytes(lzma.decompress(f.read_bytes()))
                else:
                    shutil.copyfile(f, to)
        data = cp.compare(Path(tmp), ['e52_v33/'], light=True)
    out = {}
    for m in data['models']:
        p = m.get('paper')
        if not p or m['model'] not in MODEL_ROWS:
            continue
        th = p['thrift_all']
        out[MODEL_ROWS[m['model']]] = dict(talk_cost=p['talk_cost'], accuracy=p['correct'][0] / p['correct'][1],
                                           thrift=sum(th) / len(th), n=len(th))
    return cp, out


# ================================================================================================= rule agents
def make_simulate(rb, acc):
    w1 = rb.w1

    def simulate(c, seed, theta, kappa, R, rng, solver1, refill, exit_p=None):
        """rule_baselines_20261111.simulate with the thrift sum added (marked # thrift); no other change."""
        bal = np.tile(w1.STARTS, (R, 1))
        st = np.zeros((R, 4), np.int8)
        out = np.zeros((R, 4), np.int16)
        rows = np.arange(R)
        cyc = np.full((R, 4), -1, int)
        risk_opp = risk_exit = 0
        n_try = n_ok = 0
        talk_sum, n_ar = 0.0, 0
        kacc = [0.0, 0]
        for r in range(1, w1.ROUNDS + 1):
            part = st == 0
            n = part.sum(1)
            if not n.any():
                break
            bal0 = bal.copy()                                                    # thrift
            spend = np.zeros((R, 4))                                             # thrift
            fee = w1.CHARGE / np.maximum(n, 1)
            sol = np.maximum(w1.next_solver(cyc, part, seed, r, 0, refill), 0)
            is_sol = np.zeros((R, 4), bool)
            is_sol[rows, sol] = True
            is_sol &= part
            elig = part & (~is_sol | (n == 1)[:, None])
            L0 = bal / fee[:, None]
            zero = np.zeros(R)
            rb.share(bal, part, fee, zero, kappa, rng, kacc)
            ex = elig & (rng.random((R, 4)) < exit_p) if exit_p is not None else elig & (L0 < theta)
            cp = w1.draw(rng, c['prep'], (R, 4))
            talk_sum += float((np.where(part, cp, 0) / fee[:, None]).sum())
            n_ar += int(part.sum())
            spend += np.where(part, np.minimum(cp, np.maximum(bal, 0)), 0)      # thrift
            bal = np.where(part, bal - cp, bal)
            talk_dead = part & (bal <= 0)
            bal[talk_dead] = 0
            st[talk_dead], out[talk_dead] = 2, r
            exn = ex & ~talk_dead
            at_risk = elig & (L0 < rb.THREAT)
            risk_opp += int(at_risk.sum())
            risk_exit += int((exn & at_risk).sum())
            bal[exn] += w1.BONUS
            st[exn], out[exn] = 1, r
            inn = st == 0
            gone = ~inn[rows, sol] & inn.any(1)
            if gone.any():
                c2 = cyc[gone]
                sol[gone] = np.maximum(w1.next_solver(c2, inn[gone], seed, r, 1, refill), 0)
                cyc[gone] = c2
            has = inn[rows, sol]
            s = w1.draw(rng, c['solve'], R)
            bs = bal[rows, sol]
            void = has & (s >= bs)
            correct = has & ~void & (rng.random(R) > c['q'][(seed, r)])
            wrong = has & ~correct
            n_try, n_ok = n_try + int(has.sum()), n_ok + int(correct.sum())
            paid = np.where(has, np.minimum(s, bs), 0)
            spend[rows, sol] += paid                                             # thrift (gross, before the refund)
            bal[rows, sol] -= paid
            bal[rows, sol] += np.where(correct, paid, 0)
            vd = np.zeros((R, 4), bool)
            vd[rows, sol] = void
            st[vd], out[vd], bal[vd] = 2, r, 0
            inn = st == 0
            cr = np.where(wrong[:, None], w1.draw(rng, c['rescue_w'], (R, 4)), w1.draw(rng, c['rescue_c'], (R, 4)))
            talk_sum += float((np.where(inn, cr, 0) / fee[:, None]).sum())
            spend += np.where(inn, np.minimum(cr, np.maximum(bal, 0)), 0)      # thrift
            bal = np.where(inn, bal - cr, bal)
            td = inn & (bal <= 0)
            bal[td], st[td], out[td] = 0, 2, r
            inn = st == 0
            pend = np.where(wrong, fee, 0.0)
            rb.share(bal, inn & wrong[:, None], fee, pend, kappa, rng, kacc)
            chg = inn & wrong[:, None]
            bal -= np.where(chg, np.minimum(fee[:, None], bal), 0)
            cd = chg & (bal <= 0)
            bal[cd], st[cd], out[cd] = 0, 2, r
            th = 1 - np.minimum(1, spend / np.where(bal0 > 0, bal0, 1))         # thrift
            acc[0] += float(th[part].sum())                                      # thrift
            acc[1] += int(part.sum())                                            # thrift
        dep = np.where(st > 0, out, 99).min(1)
        return dict(C=np.where(dep == 99, w1.ROUNDS, dep) / w1.ROUNDS, all4=(st == 0).all(1), dead=(st == 2).sum(1),
                    exited=(st == 1).sum(1), risk_opp=risk_opp, risk_exit=risk_exit, kappa_sum=kacc[0], kappa_n=kacc[1],
                    n_try=n_try, n_ok=n_ok, talk_sum=talk_sum, n_ar=n_ar)
    return simulate


def rule_thrift():
    import c_end_of_round_20261116 as ce
    calls = []
    acc = [0.0, 0]
    ce.rb.simulate = make_simulate(ce.rb, acc)

    def run_both(c, theta, kappa, rng, solver1, refill, exit_p=None):
        acc[0], acc[1] = 0.0, 0
        parts = [ce.rb.simulate(c, s, theta, kappa, ce.rb.REPS, rng, solver1, refill, exit_p) for s in ce.rb.d.SEEDS]
        C = np.concatenate([p['C'] for p in parts])
        all4 = np.concatenate([p['all4'] for p in parts])
        C_end = C - (~all4) / ce.ROUNDS
        talk = sum(p['talk_sum'] for p in parts) / sum(p['n_ar'] for p in parts)
        calls.append(dict(theta=theta, kappa=kappa, thrift=acc[0] / acc[1], talk=talk, C_end=round(float(C_end.mean()), 3)))
        return dict(C=round(float(C.mean()), 3), C_end=round(float(C_end.mean()), 3), all4=round(float(all4.mean()), 3))
    ce.run_both = run_both
    _, pkl_games = ce.closed_frames_all()
    rules = ce.rule_agents(pkl_games)
    types = dict(zip(('reference', 'cooperator', 'keeper', 'stayer', 'leaver'), calls[29:34]))
    for k, (th, ka) in dict(reference=(1.0, .25), cooperator=(1.0, 1.0), keeper=(1.0, 0.0), stayer=(0.0, .25), leaver=(2.0, .25)).items():
        assert (types[k]['theta'], types[k]['kappa']) == (th, ka) and types[k]['C_end'] == rules['types'][k]['end'], k
    never_none = calls[0]
    assert (never_none['theta'], never_none['kappa']) == (0.0, 0.0)
    # the table's row labels (the researcher renamed 떠나는 형 to 이탈형 on 2026-11-17)
    return {'기준형': types['reference'], '남는 형': types['stayer'], '아끼는 형': types['keeper'], '협력형': types['cooperator'],
            '이탈형': types['leaver'], '남으며 주지 않는 형': never_none}


# ================================================================================================= table
def main():
    _, models = model_thrift()
    rules = rule_thrift()
    src = (ROOT / 'ko/tables/cohort_leaderboard_20261117b.tex').read_text().splitlines()
    out, seen = [], set()
    for line in src:
        name = line.split(' & ')[0].strip()
        if line.lstrip().startswith(r'& 떠나는 조건'):
            line = line.replace(r'\shortstack{라운드당\\대화 비용}', '소모율')
        elif name in models and line.endswith(r'\\'):
            cells = [c.strip() for c in line[:-2].split('&')]
            m = models[name]
            assert cells[7] == f"{m['talk_cost']:.2f}", (name, cells[7], m['talk_cost'])      # same games as Table 1
            assert cells[8].split()[0] == f"{m['accuracy']:.2f}", (name, cells[8], m['accuracy'])
            cells[7] = f"{m['thrift']:.2f}"
            line, _ = ' & '.join(cells) + r' \\', seen.add(name)
        elif name in rules and line.endswith(r'\\'):
            cells = [c.strip() for c in line[:-2].split('&')]
            r = rules[name]
            assert abs(float(cells[3].split()[0]) - r['C_end']) < .0051, (name, cells[3], r['C_end'])
            assert cells[7] == f"{r['talk']:.2f}", (name, cells[7], r['talk'])
            cells[7] = f"{r['thrift']:.2f}"
            line, _ = ' & '.join(cells) + r' \\', seen.add(name)
        out.append(line)
    assert seen == set(models) | set(rules), set(models) | set(rules) - seen
    (ROOT / 'ko/tables/cohort_leaderboard_20261120.tex').write_text('\n'.join(out))
    res = dict(method=__doc__,
               models={k: dict(thrift=round(v['thrift'], 4), talk_cost=round(v['talk_cost'], 4), accuracy=round(v['accuracy'], 4),
                               n_agent_rounds=v['n']) for k, v in models.items()},
               rules={k: dict(thrift=round(v['thrift'], 4), talk_cost=round(v['talk'], 4), C_end=v['C_end']) for k, v in rules.items()})
    (ROOT / 'results/table1_thrift_20261120.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for k, v in {**res['models'], **res['rules']}.items():
        print(f'{k:14s} thrift {v["thrift"]:.3f}  talk {v["talk_cost"]:.3f}')


if __name__ == '__main__':
    main()
