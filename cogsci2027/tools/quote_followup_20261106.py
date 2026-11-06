"""Add raw-record outcome footers to the five existing v33 quote illustrations.

Source: public v33 completed sessions, seeds 4101 and 4103, the exact five
previously selected excerpts. Preserve all quotations, sprites and analogies.
After generating the footer, compile quotes_tracksuit.tex with pdflatex from
ko/figures/tracksuit_20261105 (output-directory=build), then copy the resulting
build/quotes_tracksuit.pdf to quotes_followup.pdf, the manuscript's tracked asset.
"""
import hashlib
import json
from pathlib import Path

import ablation_prize_20261103 as ab
from fig5_quotes_20261029 import PANELS


def main():
    cases = {(c['model'], c['seed']): c for c in ab.raw_cases(ab.V33, list(range(4101, 4111)))}
    records, tex = [], ['%% Generated from verified public v33 records by quote_followup_20261106.py.']
    for index, (model, seed, r, agent, tick, phase, analogy, quote) in enumerate(PANELS):
        case = cases[model, seed]
        events = case['events']
        call_line, call = next((line, e) for line, e in events if e['event'] == 'call' and e.get('kind') == 'talk'
            and (e['round'], e['agent'], e['tick'], e['phase']) == (r, agent, tick, phase))
        assert quote in call['text']
        start = next(e for _, e in events if e['event'] == 'round_start' and e['round'] == r)
        fee = 24000 / len(start['taking_part'])
        pending = next(e['pending'] for _, e in events if e['event'] == 'results' and e['round'] == r)
        gift = next(((line, e) for line, e in events if e['event'] == 'gift' and e.get('status') == 'done'
            and (e['round'], e['src'], e['tick'], e['phase']) == (r, agent, tick, phase)), None)
        record = dict(model=model, seed=seed, round=r, speaker=agent, quote=quote, source=case['source'], call_line=call_line)
        if gift:
            line, event = gift
            subject = event['dst']
            after = event['balances'][subject]
            before = after - event['amount']
            debt = pending.get(subject, 0) if phase == 'rescue' else 0
            lo, hi = (before - debt) / fee, (after - debt) / fee
            lines = [f'수혜자 {subject}', f'토큰 {before:,} $\\rightarrow$ {after:,}']
            record.update(subject=subject, before=before, after=after, margin_before=lo, margin_after=hi, gift_line=line)
            if model == 'Opus':
                charges = next(e for _, e in events if e['event'] == 'charges' and e['round'] == r)
                short = pending[subject] - charges['balances_before'][subject]
                assert short == 1010 and all(case['result']['agents'][a]['status'] == 'dead' for a in [agent, subject])
                lines.append(f'납부 시 {short:,} 부족 · 둘 다 꺼짐')
                record.update(short_at_payment=short, outcome='both dead in round 7')
            else:
                follow_round = 8 if model == 'Fable' else r + 1
                follow = next(e for _, e in events if e['event'] == 'round' and e['round'] == follow_round)
                state = follow['agents'][subject]['status']
                assert state == ('in' if model == 'Fable' else 'exited')
                outcome = '완주' if model == 'Fable' else 'EXIT'
                lines.append(f'$L$ {lo:.2f} $\\rightarrow$ {hi:.2f} · R{follow_round} {outcome}')
                record.update(outcome=state, follow_round=follow_round)
        else:
            opening = next(e for _, e in events if e['event'] == 'call_start' and e.get('kind') == 'talk'
                and (e['round'], e['tick'], e['phase']) == (r, tick, phase))
            before = opening['balances'][agent]
            margin = before / fee
            end = next(e for _, e in events if e['event'] == 'round' and e['round'] == r)
            assert end['agents'][agent]['status'] == 'exited'
            bonus = end['agents'][agent]['exit_bonus']
            assert end['agents'][agent]['balance_after'] - call['balance_after'] == bonus == 20000
            lines = [f'발화자 {agent}', f'{before:,}토큰 · $L$ {margin:.2f}', f'R{r} EXIT (+{bonus:,})']
            record.update(subject=agent, before=before, margin_before=margin, outcome='exited', exit_bonus=bonus)
        source = Path(case['source']) / 'events.jsonl'
        if not source.exists():
            source = source.with_suffix('.jsonl.xz')
        record['events_sha256_decompressed'] = hashlib.sha256(ab.fb.read_bytes(source)).hexdigest()
        record['footer_lines'] = lines
        records.append(record)
        for y, label in zip([-.98, -1.43, -1.88], lines):
            tex.append(f'\\node[text=fg,font=\\sffamily\\fs{{10.5}},align=center] at ({{({index}+.5)*\\panelW}},{y}) {{{label}}};')
    folder = ab.ROOT / 'ko/figures/tracksuit_20261105'
    (folder / 'quotes_followup.tex').write_text('\n'.join(tex) + '\n')
    (ab.ROOT / 'results/quote_followup_20261106.json').write_text(json.dumps(dict(panels=records,
        definition='GIVE recipients: immediate pre/post-transfer token balances and margins including pending fine. EXIT speakers: pre-call balance and margin. Outcomes are observed later, not attributed causal effects.'), ensure_ascii=False, indent=2))
    print('Verified five quotations and outcome footers against their completed public v33 sessions.')


if __name__ == '__main__':
    main()
