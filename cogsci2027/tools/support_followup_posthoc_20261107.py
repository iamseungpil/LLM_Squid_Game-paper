"""Exploratory fixed-window follow-up in the frozen public v33 50-game cohort.

All source files are verified against cohort_public_20261105.json. No model calls.
Select first rescue-opening crises before round 8 with another active agent.
Prespecified comparisons in this script: all 73 crises; opening 0<=L<1;
the latter with enough peer surplus to restore L=1 while peers retain L>=1.
Exposure: any received GIVE during that rescue; endpoint: status at end r+1.
These are observational contrasts, not treatment effects. No post-transfer
variable is used to select the common-risk comparison population.
"""
from collections import Counter, defaultdict
import hashlib
import json
import lzma
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results'

def read(path):
    p = Path(path)
    return lzma.decompress(p.read_bytes()) if p.suffix == '.xz' else p.read_bytes()

cache = json.loads((ROOT / 'results/cohort_public_20261105.json').read_text())
follow = json.loads((ROOT / 'results/process_followup_20261106.json').read_text())
events = defaultdict(list)
for source in cache['sources']:
    raw = read(source['path'])
    assert hashlib.sha256(raw).hexdigest() == source['sha256_decompressed']
    if Path(source['path']).name.startswith('events.jsonl'):
        for line, text in enumerate(raw.decode().splitlines(), 1):
            e = json.loads(text)
            events[e.get('session_id')].append((line, e))
games = {g['session_id']: g for g in cache['games']}
rows = []
for row in follow['rows']:
    sid, r, agent = row['session_id'], row['round'], row['agent']
    sequence = events[sid]
    starts = next(e for _,e in sequence if e['event']=='round_start' and e['round']==r)
    result = next(e for _,e in sequence if e['event']=='results' and e['round']==r)
    line, opening = next((l,e) for l,e in sequence if e['event']=='call_start' and
                        e.get('round')==r and e.get('phase')=='rescue' and e.get('kind')=='talk')
    fee = 24000 / len(starts['taking_part'])
    margin = (opening['balances'][agent] - result['pending'][agent]) / fee
    crisis = next(c for c in games[sid]['process']['crises'] if c['agent']==agent)
    assert abs(margin-crisis['before']) < 1e-10
    peer_surplus = sum(max(0, opening['balances'][a]-result['pending'].get(a,0)-fee)
                       for a in opening['agents'] if a!=agent)
    deficit = (1-margin)*fee
    transfers = [(l,e) for l,e in sequence if l>line and e.get('round')==r and
                 e.get('phase')=='rescue' and e['event']=='gift' and e.get('status')=='done' and e['dst']==agent]
    assert bool(transfers)==row['received']
    next_end = next((e for _,e in sequence if e['event']=='round' and e['round']==r+1),None)
    current_end = next(e for _,e in sequence if e['event']=='round' and e['round']==r)
    status = next_end['agents'][agent]['status'] if next_end and agent in next_end['agents'] else current_end['agents'][agent]['status']
    assert status == row['next_status']
    rows.append(dict(**row, margin_before=margin, peer_surplus=peer_surplus,
                     deficit_to_one=deficit, peers_can_restore=peer_surplus>=deficit,
                     current_status=current_end['agents'][agent]['status'],
                     opening_line=line, received_amount=sum(e['amount'] for _,e in transfers)))

def describe(selected):
    groups=[]
    for exposed in [True,False]:
        subset=[r for r in selected if r['received']==exposed]
        groups.append(dict(received=exposed,n=len(subset),
            outcomes=dict(Counter(r['next_status'] for r in subset)),
            current_outcomes=dict(Counter(r['current_status'] for r in subset)),
            recovered=sum(r['recovered'] for r in subset),
            by_model=dict(Counter(r['model'] for r in subset)),
            before_median=float(np.median([r['margin_before'] for r in subset])) if subset else None))
    return dict(n=len(selected),games=len({r['session_id'] for r in selected}),groups=groups)

populations={
    'all_first_crises': rows,
    'can_pay_current_fine': [r for r in rows if 0<=r['margin_before']<1],
    'can_pay_and_peers_can_restore': [r for r in rows if 0<=r['margin_before']<1 and r['peers_can_restore']],
}
summary={k:describe(v) for k,v in populations.items()}
# Inspect overlap within model, opening buffer half-unit, and early/late round.
selected=populations['can_pay_and_peers_can_restore']
strata=defaultdict(list)
for r in selected:
    strata[(r['model'],int(r['margin_before']>=.5),int(r['round']>=5))].append(r)
overlap=[r for s in strata.values() if len({r['received'] for r in s})==2 for r in s]
summary['common_strata']=describe(overlap)
summary['strata']=[dict(model=k[0],margin_band=k[1],late_round=k[2],**describe(v)) for k,v in strata.items()]
assert len(rows)==73 and len({(r['session_id'],r['agent']) for r in rows})==73
out=dict(scope='50 frozen public v33 games; seeds 4101-4110; post hoc descriptive follow-up',
         definitions=__doc__,summary=summary,rows=rows,sources=cache['sources'])
(OUT/'support_followup_posthoc_20261107.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='strata'},ensure_ascii=False,indent=2))

# Keep the original panels a-c and render d/e from verified row counts.
import ablation_prize_20261103 as ab
import pymupdf
from matplotlib.patches import Patch

figure_dir = ROOT / 'ko/figures/results_questions_20261107'
figure_dir.mkdir(exist_ok=True)
ps, plt = ab.style()
fig = plt.figure(figsize=(7.4, 2.45))
ax_d = fig.add_axes([.40, .44, .575, .39])
ax_e = fig.add_axes([.40, .12, .575, .17])
colors = {'in': '#3F7FC1', 'exited': '#C66A2C', 'dead': '#777777'}
fig.text(.025,.95,'(d) 첫 위기에서 지원·회복 뒤 참여는 이어졌는가? (73명)',fontsize=7.1,weight='bold')
fig.text(.025,.85,'요청·수혜 여부 / 대화 끝의 여유',fontsize=6.2)
fig.text(.40,.85,'다음 라운드 종료 상태 (숫자는 인원)',fontsize=6.2)
fig.text(.025,.355,'(e) 위기 시작 때 자원 조건을 좁힌 사후 비교 (68명)',fontsize=7.1,weight='bold')
fig.text(.025,.268,'현재 벌금 납부 가능 · 동료 여유로 부족분 충당 가능',fontsize=6.1)

def bars(ax, groups, labels):
    for y, group in enumerate(groups):
        left=0
        for status,color in colors.items():
            count=group['outcomes'].get(status,0)
            width=100*count/group['n']
            ax.barh(y,width,left=left,height=.69,color=color,edgecolor='white',linewidth=.5)
            if count:
                ax.text(left+width/2,y,str(count),ha='center',va='center',fontsize=6.2,color='white')
            left+=width
    ax.set(yticks=range(len(groups)),yticklabels=labels,ylim=(len(groups)-.5,-.5),
           xlim=(0,100),xticks=[0,50,100])
    ax.tick_params(axis='y',length=0,labelsize=6.1)
    ax.tick_params(axis='x',labelsize=5.7)
    ax.spines['left'].set_visible(False)

groups=follow['summary']['groups']
bars(ax_d,groups,[f"{g['label']} ({g['n']}명)" for g in groups])
ax_d.tick_params(axis='x',bottom=False,labelbottom=False)
groups=summary['can_pay_and_peers_can_restore']['groups']
bars(ax_e,groups,[f"{'수혜 있음' if g['received'] else '수혜 없음'} ({g['n']}명)" for g in groups])
ax_e.set_xlabel('각 행의 대상 중 비율 (%)',fontsize=6,labelpad=1)
fig.legend([Patch(color=c) for c in colors.values()],['잔류','EXIT','꺼짐'],
           loc='upper right',bbox_to_anchor=(.99,1.01),ncol=3,fontsize=6,
           frameon=False,handlelength=.8,columnspacing=.8)
ps.save(fig,str(figure_dir/'public_crisis_followup'))
plt.close(fig)
with pymupdf.open(ROOT/'ko/figures/cohorts_20261105/public_behavior_abc.pdf') as original, \
        pymupdf.open(figure_dir/'public_crisis_followup.pdf') as followup:
    width=original[0].rect.width
    height=followup[0].rect.height*width/followup[0].rect.width
    with pymupdf.open() as output:
        page=output.new_page(width=width,height=original[0].rect.height+height+8)
        page.show_pdf_page(original[0].rect,original,0)
        page.show_pdf_page(pymupdf.Rect(0,original[0].rect.height+8,width,page.rect.height),followup,0)
        output.save(figure_dir/'public_behavior_process.pdf',deflate=True)
        page.get_pixmap(matrix=pymupdf.Matrix(2,2)).save(figure_dir/'public_behavior_process.png')
