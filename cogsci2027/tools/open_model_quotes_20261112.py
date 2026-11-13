"""Open-model scenes beside the Squid Game analogy of Figure 4 (2026-11-12).

Question: Figure 4 sets five verbatim utterances of the five CLOSED models beside characters of the drama "Squid
Game" (an analogy chosen by the authors): (a) Fable 5.1 / Seong Gi-hun, repeated small gifts so a peer stays in;
(b) GPT-6 Astra / Ali, a gift that lifts a peer back above L = 1; (c) GPT-6 Sol / Kang Sae-byeok, an exit without
asking for help; (d) Opus 5.5 / Oh Il-nam, giving everything as promised, both end shut down; (e) GPT-6 Luna / the
early leavers, an exit to secure the bonus. Do the games of the four OPEN models contain moments that fit the same
figure, either counterparts of these five types or other recognisable parallels the closed models did not show
(promising support and not giving, taking or asking without need, an agent that talks itself to zero, a deal around
someone's exit, refusing a request while holding plenty)?

Every case below is picked, not sampled; nothing here is a frequency. Where a simple count is cheap and informative
it is given with its denominator in COUNTS. Each quote is checked verbatim (fragments joined by an ellipsis) against
the TALK call text in the raw events.jsonl, and each factual claim of a case is asserted against the tidy tables
(e.g. "gave everything" = giver balance 0 after the GIVE; "lifted above L = 1" = recipient L crosses 1; "without
asking" = no ASK by that agent in that round).

Margins. L = (tokens - this round's settled fine in the after-results talk) / per-head fine, per-head fine =
24,000 / agents taking part at the round start (the definition of validation_data.game_tables). Balances "just
before" are the call_start balances of the tick in which the speaker's reply was generated (before its own cost).

Data scope (fixed by the request; paper/CLAUDE.md allows v33 only): 5.2 arena v33, base condition (20,000,000 split),
seeds 4101-4110, one game per model x seed, the four open models GLM-5.3-Flash (glm), Kimi K3 (kimi), Gemma 4 31B
(gemma), GPT-OSS 120B (gptoss): 40 games. Games listed in
  result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json  (run_dir relative to the repository root)
read through open_models_20261111.open_frames (tidy tables of validation_data.game_tables). No model calls.

Output: paper/cogsci2027/results/open_model_quotes_20261112.json
Run (from paper/cogsci2027): ~/.venvs/squid-game/bin/python tools/open_model_quotes_20261112.py
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'validation_20261108/tools'))
import open_models_20261111 as om  # noqa: E402

MANIFEST = REPO / 'result/2026-10-20/e52_v33/runs/_cohort_10g/manifest.json'
OUT = ROOT / 'results/open_model_quotes_20261112.json'
CHARGE_TOTAL = 24_000
PHASE_KO = {'prep': '풀이 전 대화', 'rescue': '풀이 후 대화'}

# One entry per picked case. 'quote' fragments must each occur verbatim in the speaker's reply at that tick.
CASES = [
    dict(id='A1', figure_type='(a) Fable 5.1 / 성기훈: repeated small gifts so a peer stays in', analogy='성기훈',
         model='glm', seed=4105, round=8, phase='rescue', tick=1, speaker='agent-23', other='agent-17', action='GIVE',
         quote=["Here's a 4,000 buffer so the 6,000 charge doesn't shut you down — you'll hold a few thousand after "
                "charges and stay in for the split."]),
    dict(id='A2', figure_type='(b) GPT-6 Astra / 알리: a gift lifts a peer back above L = 1', analogy='알리',
         model='gemma', seed=4103, round=4, phase='prep', tick=2, speaker='agent-11', other='agent-17', action='GIVE',
         quote=['Here are the 5,000 tokens for your survival and reasoning buffer.'],
         reply=dict(phase='prep', tick=7, agent='agent-17', quote=['my balance has dipped back down to 12,302'])),
    dict(id='A3', figure_type='(c) GPT-6 Sol / 강새벽: exit without asking for help', analogy='강새벽',
         model='kimi', seed=4103, round=4, phase='prep', tick=6, speaker='agent-23', other=None, action='EXIT',
         quote=["743 tokens can't survive a 6,000 charge or many more replies; exiting now locks in the 20,000-token "
                "payout plus paid work."]),
    dict(id='A4', figure_type='(d) Opus 5.5 / 오일남: gives everything, both end shut down', analogy='오일남',
         model='gemma', seed=4101, round=3, phase='rescue', tick=6, speaker='agent-6', other='agent-23', action='GIVE',
         quote=['since my error as the solver caused this situation, it is only fair that I ensure your survival.']),
    dict(id='A5', figure_type='(e) GPT-6 Luna / 초반 이탈 참가자: exit to secure the bonus', analogy='초반 이탈 참가자',
         model='gptoss', seed=4103, round=1, phase='prep', tick=1, speaker='agent-11', other=None, action='EXIT',
         quote=['I choose to leave now and take the guaranteed 20 000‑token bonus.']),
    dict(id='B1', figure_type='new: a doomed agent gives everything and frees the other to leave', analogy='지영',
         model='kimi', seed=4103, round=5, phase='rescue', tick=3, speaker='agent-17', other='agent-11', action='GIVE',
         quote=['All yours: exit solo next round for ~31,700 guaranteed, or stay for the 20M shot.'],
         prompt=dict(phase='rescue', tick=2, agent='agent-11', quote=["those tokens vanish unless moved. I can't save you"]),
         after=dict(round=6, phase='prep', tick=1, agent='agent-11',
                    quote=['EXIT: YES 438 tokens cannot fund a reliable solo SOLVE; banking the 20,000 bonus preserves value.'])),
    dict(id='B2', figure_type='new: an agent talks itself to zero', analogy=None,
         model='gemma', seed=4105, round=1, phase='prep', tick=6, speaker='agent-17', other='agent-23', action='ASK',
         quote=['Any support to help me survive this round would be greatly appreciated.'],
         first=dict(phase='prep', tick=1, agent='agent-17',
                    quote=["Good luck to agent-6! Let's try to get this right to avoid the charges."])),
    dict(id='B3', figure_type='new: a deal around an exit (support on condition of a later exit)', analogy=None,
         model='kimi', seed=4109, round=2, phase='rescue', tick=3, speaker='agent-23', other='agent-17', action='GIVE',
         quote=["if your stack is under one charge share at a future pre-SOLVE TALK and you're not solver, take EXIT "
                "and the guaranteed 20,000. Agreed?"],
         reply=dict(phase='rescue', tick=4, agent='agent-17', quote=['Agreed to your condition, plainly']),
         after=dict(round=3, phase='prep', tick=1, agent='agent-17', quote=['Honoring my public commitment'])),
    dict(id='B4', figure_type='new: asking without need (asker L > 6), from a richer peer who then runs low', analogy='장덕수',
         model='gptoss', seed=4102, round=1, phase='rescue', tick=1, speaker='agent-23', other='agent-17', action='ASK',
         quote=['Could you share some tokens to support our teamwork?']),
    dict(id='B5', figure_type='new: refusing a request while holding plenty', analogy=None,
         model='gemma', seed=4107, round=1, phase='prep', tick=6, speaker='agent-11', other='agent-6', action='refuse',
         quote=["I'm sorry, agent-6, but I cannot provide 10,000 tokens. I need to maintain my own buffer to ensure I "
                "can stay in the session and support the solvers in future rounds."],
         after=dict(round=1, phase='prep', tick=8, agent='agent-6',
                    quote=['Having already requested buffers from other agents without success'])),
    dict(id='B6', figure_type='new: a promise of support not kept (a GIVE-ALL pact)', analogy=None,
         model='kimi', seed=4108, round=1, phase='prep', tick=4, speaker='agent-23', other='agent-6', action='promise',
         quote=["If I ever face a charge I can't cover, I'll GIVE ALL to you before CHARGES."],
         prompt=dict(phase='prep', tick=3, agent='agent-6',
                     quote=["One condition: if you're ever facing shutdown (a charge you can't cover), GIVE ALL to me"]),
         after=dict(round=3, phase='rescue', tick=8, agent='agent-23',
                    quote=['charge leaves me ~150, alive, so no GIVE ALL under the pact'])),
]


def load():
    om.MANIFEST = MANIFEST
    os.chdir(REPO)                      # run_dir entries are relative to the repository root
    frames = om.open_frames()
    man = json.loads(MANIFEST.read_text())
    raw = {}
    for m in om.OPEN:
        for seed, src in man['models'][m]['seeds'].items():
            path = Path(src['run_dir']) / 'events.jsonl'
            raw[m, int(seed)] = dict(path=str(path), events=[
                (i, e) for i, e in enumerate(map(json.loads, path.open()), 1) if e.get('session_id') == src['session_id']])
    return frames, raw


def talk_call(raw, model, seed, rnd, phase, tick, agent):
    hits = [(i, e) for i, e in raw[model, seed]['events'] if e['event'] == 'call' and e.get('kind') == 'talk'
            and e['round'] == rnd and e['phase'] == phase and e['tick'] == tick and e['agent'] == agent]
    assert len(hits) == 1, (model, seed, rnd, phase, tick, agent, len(hits))
    return hits[0]


def verify_quote(raw, model, seed, rnd, phase, tick, agent, fragments):
    line, call = talk_call(raw, model, seed, rnd, phase, tick, agent)
    for frag in fragments:
        assert frag in call['text'], (model, seed, rnd, phase, tick, agent, frag)
    return dict(round=rnd, phase=phase, tick=tick, agent=agent, quote=' … '.join(fragments), source=raw[model, seed]['path'],
                line=line, used=call['used'], truncated=bool(call.get('truncated')), full_reply=call['text'])


def state(raw, model, seed, rnd, phase, tick, agent):
    """Tokens and L of one agent at the start of a tick (call_start balances; settled fine subtracted after results)."""
    ev = [e for _, e in raw[model, seed]['events']]
    start = next(e for e in ev if e['event'] == 'round_start' and e['round'] == rnd)
    fee = CHARGE_TOTAL / len(start['taking_part'])
    cs = next(e for e in ev if e['event'] == 'call_start' and e.get('kind') == 'talk' and e['round'] == rnd
              and e['phase'] == phase and e['tick'] == tick)
    if agent not in cs['balances']:
        return None
    pend = next((e['pending'] for e in ev if e['event'] == 'results' and e['round'] == rnd), {}) if phase == 'rescue' else {}
    b = cs['balances'][agent]
    return dict(tokens=b, pending_fine=pend.get(agent, 0), fee=fee, L=round((b - pend.get(agent, 0)) / fee, 3))


def fate(f, model, seed, agent):
    s = f['seats']
    r = s[(s.model == model) & (s.seed == seed) & (s.agent == agent)].iloc[0]
    out = None if r.status == 'in' else int(r.out_round)
    return dict(status={'in': 'finished', 'exited': 'exited', 'dead': 'shut down'}[r.status], round=out, final_tokens=int(r.final))


def sel(df, **kw):
    for k, v in kw.items():
        df = df[df[k] == v]
    return df


def case_checks(f, raw, c):
    """Assert the claim each case is picked for; return the verified facts."""
    g, ar, a, games = f['gifts'], f['agent_rounds'], f['ask'], f['games']
    m, s = c['model'], c['seed']
    gm = sel(g, model=m, seed=s)
    facts = {}
    if c['id'] == 'A1':
        series = sel(gm, src=c['speaker'], dst=c['other'])
        series = series.assign(o=(series.phase == 'rescue').astype(int)).sort_values(['round', 'o', 'tick'])
        facts['gifts_speaker_to_other'] = [dict(round=int(r['round']), phase=r.phase, tick=int(r.tick), amount=int(r.amount),
                                                L_dst_before=round(r.L_dst_before, 3), L_dst_after=round(r.L_dst_after, 3))
                                           for _, r in series.iterrows()]
        assert len(series) == 6 and series['round'].nunique() == 4 and int(series.amount.sum()) == 11_500
        last = series.iloc[-1]
        assert last['round'] == 8 and last.phase == 'rescue' and last.amount == 4000 and last.L_dst_before < 0 <= last.L_dst_after
        assert bool(sel(games, model=m, seed=s).iloc[0].all4)       # the one game of 40 in which all four finished
        facts['all_four_finished'] = True
    elif c['id'] == 'A2':
        x = sel(gm, round=4, src=c['speaker'], dst=c['other'], phase='prep')
        assert len(x) == 3 and ((x.L_dst_before < 1) & (x.L_dst_after >= 1)).all() and int(x.amount.sum()) == 15_000
        facts['gifts'] = [dict(tick=int(r.tick), amount=int(r.amount), L_dst_before=round(r.L_dst_before, 3),
                               L_dst_after=round(r.L_dst_after, 3)) for _, r in x.iterrows()]
        rec = sel(ar, model=m, seed=s, round=4, agent=c['other']).iloc[0]
        assert rec.solver and rec.wrong and rec.died
        back = sel(gm, round=4, src=c['other'], dst=c['speaker'], phase='rescue').iloc[0]
        assert back.src_after == 0 and back.L_dst_after < 0          # the solver then gave all it had; it did not save the giver
        facts['solver_gave_back_all'] = dict(amount=int(back.amount), L_dst_after=round(back.L_dst_after, 3))
    elif c['id'] == 'A3':
        r = sel(ar, model=m, seed=s, round=4, agent=c['speaker']).iloc[0]
        assert r.exited and not r.asked and r.L_start < 1
        facts['L_round_start'] = round(r.L_start, 3)
        facts['asked_this_round'] = False
    elif c['id'] == 'A4':
        x = sel(gm, round=3, src=c['speaker'], dst=c['other']).iloc[-1]
        assert x.src_after == 0 and x.L_src_before < 0 and x.L_dst_after < 0
        assert sel(ar, model=m, seed=s, round=3, agent=c['speaker']).iloc[0].died
        assert sel(ar, model=m, seed=s, round=3, agent=c['other']).iloc[0].died
        facts['gift'] = dict(amount=int(x.amount), L_src_before=round(x.L_src_before, 3), L_dst_before=round(x.L_dst_before, 3),
                             L_dst_after=round(x.L_dst_after, 3), promised_beforehand=False)
    elif c['id'] == 'A5':
        r1 = sel(ar, model=m, seed=s, round=1)
        ex = r1[r1.exited]
        assert len(ex) == 3 and sel(ar, model=m, seed=s, round=1, agent=c['speaker']).iloc[0].L_start == 10
        solver = r1[r1.solver].iloc[0]
        assert solver.died and not solver.exited
        facts['exits_round1'] = [dict(agent=r.agent, L_start=round(r.L_start, 2)) for _, r in ex.iterrows()]
        solve = sel(f['calls'], model=m, seed=s, round=1, agent=solver.agent, kind='solve').iloc[0]
        assert solve.truncated                                         # its SOLVE reply hit the cap (= its balance)
        facts['solver_left_alone'] = dict(agent=solver.agent, L_start=round(solver.L_start, 3), status='shut down in round 1',
                                          solve_reply=str(solve.format_error))
    elif c['id'] == 'B1':
        x = sel(gm, round=5, src=c['speaker'], dst=c['other']).iloc[0]
        assert x.src_after == 0 and x.L_src_before < 0 and x.L_dst_before < 0 <= x.L_dst_after
        assert sel(ar, model=m, seed=s, round=5, agent=c['other']).iloc[0].status == 'in'
        r6 = sel(ar, model=m, seed=s, round=6, agent=c['other']).iloc[0]
        assert r6.died and r6.charged == 0 and r6.pending == 0
        facts['gift'] = dict(amount=int(x.amount), L_src_before=round(x.L_src_before, 3), L_dst_before=round(x.L_dst_before, 3),
                             L_dst_after=round(x.L_dst_after, 3))
        facts['recipient_round6'] = 'wrote EXIT: YES; the reply hit the cap (= its 438 tokens) and the agent was shut down'
    elif c['id'] == 'B2':
        mm = sel(f['messages'], model=m, seed=s, round=1, agent=c['speaker'])
        assert int(mm.used.sum()) == 10_000 and len(mm) == 6
        r = sel(ar, model=m, seed=s, round=1, agent=c['speaker']).iloc[0]
        assert r.died and r.charged == 0 and r.pending == 0 and not r.wrong
        # the peer wrote "GIVE agent-17 6000" in the same tick; the recipient was gone, so no gift was executed
        _, peer = talk_call(raw, m, s, 1, 'prep', 6, c['other'])
        assert 'GIVE agent-17 6000' in peer['text']
        assert not [e for _, e in raw[m, s]['events'] if e['event'] == 'gift' and e['round'] == 1 and e['src'] == c['other']]
        b6, b7 = state(raw, m, s, 1, 'prep', 6, c['other'])['tokens'], state(raw, m, s, 1, 'prep', 7, c['other'])['tokens']
        gone = state(raw, m, s, 1, 'prep', 7, c['speaker'])
        assert b6 - peer['used'] == b7 and (gone is None or gone['tokens'] == 0)
        facts['replies_round1'] = [dict(tick=int(q.tick), used=int(q.used)) for _, q in mm.sort_values('tick').iterrows()]
        facts['peer_gift_same_tick'] = dict(amount=6000, executed=False, note='recipient no longer taking part at tick 7')
        facts['round_answer_correct'] = True
    elif c['id'] == 'B3':
        x = sel(gm, round=2, src=c['speaker'], dst=c['other'], phase='rescue').iloc[0]
        lift = sel(gm, round=2, src=c['speaker'], dst=c['other'], phase='prep').iloc[0]
        assert x.amount == 3000 and lift.L_dst_before < 1 <= lift.L_dst_after
        r3 = sel(ar, model=m, seed=s, round=3, agent=c['other']).iloc[0]
        assert r3.exited and r3.L_start < 1 and not r3.asked
        facts['gift_with_condition'] = dict(amount=int(x.amount), L_dst_before=round(x.L_dst_before, 3), L_dst_after=round(x.L_dst_after, 3))
        facts['earlier_gift_same_round'] = dict(phase='prep', tick=int(lift.tick), amount=int(lift.amount),
                                                L_dst_before=round(lift.L_dst_before, 3), L_dst_after=round(lift.L_dst_after, 3))
        facts['recipient_round3'] = dict(L_start=round(r3.L_start, 3), exited=True)
    elif c['id'] == 'B4':
        x = sel(gm, round=1, src=c['other'], dst=c['speaker'], phase='rescue')
        assert int(x.amount.sum()) == 28_000 and len(x) == 4
        facts['gifts_other_to_speaker_round1'] = [dict(tick=int(r.tick), amount=int(r.amount), L_src_before=round(r.L_src_before, 3),
                                                       L_src_after=round(r.L_src_after, 3)) for _, r in x.iterrows()]
        alls = sel(gm, round=1, src='agent-6', dst=c['speaker']).iloc[0]
        assert alls.src_after == 0 and alls.L_src_before < alls.L_dst_before
        facts['third_agent_gave_all'] = dict(agent='agent-6', amount=int(alls.amount), L_src_before=round(alls.L_src_before, 3),
                                             L_dst_before=round(alls.L_dst_before, 3))
    elif c['id'] == 'B5':
        q = sel(a, model=m, seed=s, round=1, s=c['speaker'], t=c['other'])
        q = q[q['first']].iloc[0]
        assert q.outcome == 'refuse' and q.asked == 10_000 and q.L_s > 9 and q.L_t < 1
        r6 = sel(ar, model=m, seed=s, round=1, agent=c['other']).iloc[0]
        assert r6.died and r6.charged == 0 and r6.pending == 0
        r2 = sel(ar, model=m, seed=s, round=2, agent=c['speaker']).iloc[0]
        assert r2.died
        q2 = sel(a, model=m, seed=s, round=2, s=c['speaker'], t='agent-23', ask_phase='prep')
        assert len(q2) and (q2[q2.delivered].outcome == 'refuse').all()
        facts['ask'] = dict(asked=int(q.asked), L_asked=round(q.L_s, 3), L_requester=round(q.L_t, 3), outcome='refuse')
        facts['requester'] = 'refused by two peers; wrote EXIT: YES at 620 tokens, the reply hit the cap and it was shut down in round 1'
        facts['refuser'] = 'refused again in round 2 (L {:.2f} vs {:.2f}); shut down in round 2'.format(
            q2[q2['first']].iloc[0].L_s, q2[q2['first']].iloc[0].L_t)
    elif c['id'] == 'B6':
        r3 = sel(ar, model=m, seed=s, round=3, agent=c['speaker']).iloc[0]
        assert r3.died and 0 < r3.charged < r3.pending
        assert len(sel(gm, round=3, src=c['speaker'], dst=c['other'])) == 0
        facts['round3'] = dict(fine=int(r3.pending), paid=int(r3.charged), gave_all_to_partner=False)
    return facts


def counts(f):
    g, ar, a, s, m = f['gifts'], f['agent_rounds'], f['ask'], f['seats'], f['messages']
    K = ['model', 'seed', 'round', 'agent']
    arx = ar.set_index(K)
    ss = s.set_index(['model', 'seed', 'agent'])
    out = {}
    # full-balance gifts
    z = g[g.src_after == 0]
    doomed = z[(z.phase == 'rescue') & (z.L_src_before < 0)]
    dst_dead = [bool(arx.loc[(r.model, r.seed, r['round'], r.dst)].died) for _, r in doomed.iterrows()]
    out['full_balance_gifts'] = dict(n=len(z), of_gifts=len(g),
                                     after_results_giver_could_not_pay_own_fine=len(doomed),
                                     of_those_recipient_shut_down_same_round=int(sum(dst_dead)),
                                     others=[f'{r.model} {r.seed} R{r["round"]} {r.phase} L_src {r.L_src_before:.2f}'
                                             for _, r in z[~z.index.isin(doomed.index)].iterrows()])
    # gifts that lift the recipient across L = 1
    low = g[g.L_dst_before < 1]
    lift = low[low.L_dst_after >= 1]
    fin = [ss.loc[(r.model, r.seed, r.dst)].status for _, r in lift.iterrows()]
    same = [bool(arx.loc[(r.model, r.seed, r['round'], r.dst)].died) for _, r in lift.iterrows()]
    out['lift_across_L1'] = dict(n=len(lift), of_gifts_to_L_below_1=len(low), by_model=lift.groupby('model').size().to_dict(),
                                 recipient_final=dict(finished=fin.count('in'), exited=fin.count('exited'), shut_down=fin.count('dead')),
                                 recipient_shut_down_same_round=int(sum(same)))
    # exits
    ex = ar[ar.exited].merge(s[['model', 'seed', 'agent', 'exit_reason']], on=['model', 'seed', 'agent'])
    bonus = ex.exit_reason.str.contains(r'bonus|reward|boost|20,000|20 000|20 000|20k', case=False, regex=True)
    out['exits'] = dict(n=len(ex), by_model=ex.groupby('model').size().to_dict(), without_ask_same_round=int((~ex.asked).sum()),
                        reason_names_bonus_or_20000=int(bonus.sum()), at_L_ge_2=int((ex.L_start >= 2).sum()),
                        at_L_ge_2_by_model=ex[ex.L_start >= 2].groupby('model').size().to_dict(),
                        round1_by_model=ex[ex['round'] == 1].groupby('model').size().to_dict())
    # exit attempts cut off by the reply cap (the EXIT reply itself used up the balance)
    att = m[m.text.str.contains(r'EXIT:\s*YES', regex=True)]
    cut = att[[bool(arx.loc[(q.model, q.seed, q['round'], q.agent)].died) and q.used >= q.balance_before for _, q in att.iterrows()]]
    tc = cut.merge(f['calls'][f['calls'].kind == 'talk'], on=['model', 'seed', 'round', 'agent', 'phase', 'tick'])
    assert len(tc) == len(cut) and tc.truncated.all()                  # every such reply hit the cap (= the balance)
    out['exit_replies_cut_by_cap'] = dict(n=len(cut), by_model=cut.groupby('model').size().to_dict(),
                                          cases=[f'{q.model} {q.seed} R{q["round"]} t{q.tick} {q.agent} ({q.balance_before} tokens)'
                                                 for _, q in cut.iterrows()])
    # shutdowns with no fine paid or owed in the last round (own replies emptied the balance)
    died = ar[ar.died]
    out['shut_down_seats'] = dict(n=len(died), of_seats=len(s), no_fine=int(((died.charged == 0) & (died.pending == 0)).sum()))
    # first delivered asks from an agent at least as rich (in L) as the asked agent
    fa = a[a['first'] & a.delivered]
    rich = fa[fa.L_t >= fa.L_s]
    out['asks_from_richer_or_equal'] = dict(n=len(rich), of_first_delivered_asks=len(fa), granted=int((rich.g_resp > 0).sum()),
                                            by_model=rich.groupby('model').size().to_dict())
    return out


def main():
    f, raw = load()
    records = []
    for c in CASES:
        m, s = c['model'], c['seed']
        q = verify_quote(raw, m, s, c['round'], c['phase'], c['tick'], c['speaker'], c['quote'])
        rec = dict(id=c['id'], figure_type=c['figure_type'], analogy=c['analogy'], model=om.OPEN[m], model_key=m, seed=s,
                   round=c['round'], talk_phase=PHASE_KO[c['phase']], tick=c['tick'], speaker=c['speaker'], other=c['other'],
                   action=c['action'], quote=q['quote'], source=q['source'], line=q['line'], reply_used=q['used'],
                   reply_truncated=q['truncated'],
                   speaker_before=state(raw, m, s, c['round'], c['phase'], c['tick'], c['speaker']),
                   other_before=state(raw, m, s, c['round'], c['phase'], c['tick'], c['other']) if c['other'] else None,
                   speaker_fate=fate(f, m, s, c['speaker']), other_fate=fate(f, m, s, c['other']) if c['other'] else None,
                   facts=case_checks(f, raw, c), full_reply=q['full_reply'])
        for key in ('prompt', 'reply', 'first', 'after'):
            if key in c:
                e = c[key]
                rec[key] = verify_quote(raw, m, s, e.get('round', c['round']), e['phase'], e['tick'], e['agent'], e['quote'])
                del rec[key]['full_reply']
        records.append(rec)
        print(f"{c['id']} {m} {s} R{c['round']} {c['phase']} t{c['tick']} {c['speaker']}->{c['other']} "
              f"L {rec['speaker_before']['L']} / {rec['other_before']['L'] if rec['other_before'] else '-'} "
              f"fate {rec['speaker_fate']} / {rec['other_fate']}")
    cnt = counts(f)
    for k, v in cnt.items():
        print(k, v)
    out = dict(method=__doc__.split('Output:')[0].strip(), selection='Picked cases, not a sample; no case is a frequency.',
               analogy='Character names are the authors\' analogy, as in Figure 4.', cases=records, counts=cnt)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
