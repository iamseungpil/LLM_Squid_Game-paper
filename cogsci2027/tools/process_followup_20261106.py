"""Follow first crises in the fixed public v33 cohort (5 models x seeds 4101-4110).

Source: hash-checked cohort_public_20261105.json and its completed raw sessions.
Include first post-error crises before round 8 with another agent actually present
at the rescue opening, including agents who shut down in that round. ASK/GIVE in
one tick are co-observations, not evidence that the request elicited the transfer.
No model calls. Existing Figure 4(a-c) remains unchanged; append a vector panel d.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import ablation_prize_20261103 as ab

ROOT = ab.ROOT
OUT = ROOT / 'ko/figures/cohorts_20261105'
GROUPS = [(True, True, True), (True, True, False), (False, True, True),
          (False, True, False), (False, False, False)]
LABELS = ['요청·수혜 있음 / 회복', '요청·수혜 있음 / 미회복',
          '요청 없음·수혜 있음 / 회복', '요청 없음·수혜 있음 / 미회복', '요청·수혜 없음 / 미회복']


def compute():
    cache_path = ROOT / 'results/cohort_public_20261105.json'
    cache = json.loads(cache_path.read_text())
    for source in cache['sources']:
        assert hashlib.sha256(ab.fb.read_bytes(Path(source['path']))).hexdigest() == source['sha256_decompressed']
    games = {(g['model'], g['seed']): g for g in cache['games']}
    cases = ab.raw_cases(ab.V33, cache['seeds'])
    assert {(c['model'], c['seed']) for c in cases} == set(games) and len(cases) == 50
    rows = []
    excluded = []
    for case in cases:
        events = case['events']
        crises = ab.process(case)['crises']
        original = games[case['model'], case['seed']]['process']['crises']
        assert crises == [{k: v for k, v in c.items() if k != 'asked'} for c in original]
        for crisis in crises:
            r, agent = crisis['round'], crisis['agent']
            if r == 8 or crisis['present'] <= 1:
                excluded.append(dict(model=case['model'], seed=case['seed'], **crisis))
                continue
            window = [(line, e) for line, e in events if e.get('round') == r and e.get('phase') == 'rescue']
            asks = [(line, e) for line, e in window if e['event'] == 'ask' and e.get('status') == 'done' and e['src'] == agent]
            gifts = [(line, e) for line, e in window if e['event'] == 'gift' and e.get('status') == 'done' and e['dst'] == agent]
            end_line, end = next((line, e) for line, e in events if e['event'] == 'round' and e['round'] == r)
            next_pair = next(((line, e) for line, e in events if e['event'] == 'round' and e['round'] == r + 1), None)
            if next_pair and agent in next_pair[1]['agents']:
                next_status = next_pair[1]['agents'][agent]['status']
            else:
                next_status = end['agents'][agent]['status']
                assert next_status == 'dead'
            first_ask_tick = min((e['tick'] for _, e in asks), default=None)
            rows.append(dict(model=case['model'], seed=case['seed'], session_id=case['result']['session_id'],
                source=case['source'], round=r, agent=agent, present=crisis['present'],
                asked=bool(asks), received=bool(gifts), recovered=crisis['after'] >= 1,
                margin_after=crisis['after'], immediate_dead=crisis['immediate_dead'],
                first_ask_tick=first_ask_tick,
                later_tick_support=bool(asks and any(e['tick'] > first_ask_tick for _, e in gifts)),
                same_tick_support=bool(asks and any(e['tick'] == first_ask_tick for _, e in gifts)),
                next_status=next_status, next_in=next_status == 'in',
                ask_lines=[line for line, _ in asks], gift_lines=[line for line, _ in gifts],
                round_end_line=end_line, next_round_end_line=next_pair[0] if next_pair else None))
    groups = []
    for key, label in zip(GROUPS, LABELS):
        selected = [r for r in rows if (r['asked'], r['received'], r['recovered']) == key]
        groups.append(dict(label=label, asked=key[0], received=key[1], recovered=key[2],
                           n=len(selected), outcomes=dict(Counter(r['next_status'] for r in selected))))
    assert len(rows) == sum(g['n'] for g in groups) == 73
    assert len({(r['session_id'], r['agent']) for r in rows}) == len(rows)
    summary = dict(n=len(rows), games=len({r['session_id'] for r in rows}),
        asked=sum(r['asked'] for r in rows), unasked=sum(not r['asked'] for r in rows),
        asked_received=sum(r['asked'] and r['received'] for r in rows),
        unasked_received=sum(not r['asked'] and r['received'] for r in rows),
        asked_later_tick_support=sum(r['later_tick_support'] for r in rows),
        asked_same_tick_support=sum(r['same_tick_support'] for r in rows),
        immediate_dead_included=sum(r['immediate_dead'] for r in rows), groups=groups)
    result = dict(cohort='public v33, five models x ten seeds',
        definitions=dict(eligible='First post-error L<1 rescue opening before round 8; present>1 at that opening; include immediate shutdowns',
            recovered='L>=1 at rescue end, calculated from pre-charge balance minus pending fine over this round fee',
            next_status='Status at the END of round r+1; earlier shutdowns remain dead',
            request_and_support='Co-observed within the crisis rescue; same-tick actions do not establish response order'),
        summary=summary, rows=rows, excluded=excluded, sources=cache['sources'],
        cache_sha256=hashlib.sha256(cache_path.read_bytes()).hexdigest())
    (ROOT / 'results/process_followup_20261106.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return result


def figure(data):
    import pymupdf
    from matplotlib.patches import Patch
    ps, plt = ab.style()
    fig, ax = plt.subplots(figsize=(7.4, 1.85))
    fig.subplots_adjust(left=.40, right=.975, top=.73, bottom=.16)
    colors = {'in': '#3F7FC1', 'exited': '#C66A2C', 'dead': '#777777'}
    fig.text(.025, .94, '(d) 첫 위기에서 지원받은 뒤에도 다음 라운드에 남았는가?', fontsize=7.6, weight='bold')
    fig.text(.025, .80, '요청·수혜 여부 / 대화 끝의 여유', fontsize=6.6)
    fig.text(.40, .80, '다음 라운드 종료 상태 (숫자는 인원)', fontsize=6.6)
    for y, group in enumerate(data['summary']['groups']):
        left = 0
        for status, color in colors.items():
            count = group['outcomes'].get(status, 0)
            width = 100 * count / group['n']
            ax.barh(y, width, left=left, height=.64, color=color, edgecolor='white', linewidth=.5)
            if count:
                ax.text(left + width / 2, y, str(count), ha='center', va='center', fontsize=6.4, color='white')
            left += width
    ax.set(yticks=range(5), yticklabels=[f"{g['label']} ({g['n']}명)" for g in data['summary']['groups']],
           ylim=(4.55, -.55), xlim=(0, 100), xticks=[0, 50, 100])
    ax.tick_params(axis='y', length=0, labelsize=6.2)
    ax.tick_params(axis='x', labelsize=5.7)
    ax.spines['left'].set_visible(False)
    ax.set_xlabel('각 행의 대상 중 비율 (%)', fontsize=6, labelpad=1)
    fig.legend([Patch(color=c) for c in colors.values()], ['잔류', 'EXIT', '꺼짐'],
               loc='upper right', bbox_to_anchor=(.985, .98), ncol=3, fontsize=6,
               frameon=False, handlelength=.8, columnspacing=.8)
    ps.save(fig, str(OUT / 'public_crisis_followup'))
    plt.close(fig)
    with pymupdf.open(OUT / 'public_behavior_abc.pdf') as original, pymupdf.open(OUT / 'public_crisis_followup.pdf') as followup:
        width = original[0].rect.width
        lower_height = followup[0].rect.height * width / followup[0].rect.width
        with pymupdf.open() as output:
            page = output.new_page(width=width, height=original[0].rect.height + lower_height + 8)
            page.show_pdf_page(original[0].rect, original, 0)
            page.show_pdf_page(pymupdf.Rect(0, original[0].rect.height + 8, width, page.rect.height), followup, 0)
            output.save(OUT / 'public_behavior_process.pdf', deflate=True)
            page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(OUT / 'public_behavior_process.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-only', action='store_true')
    args = parser.parse_args()
    data = compute()
    if not args.data_only:
        figure(data)
