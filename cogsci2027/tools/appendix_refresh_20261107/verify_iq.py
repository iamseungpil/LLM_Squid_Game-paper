"""Independent identities and numerical cross-checks for refreshed appendix I--K."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter
from scipy.spatial.distance import jensenshannon
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ablation_prize_20261103 as ab
import feedback_20261028 as fb
R=fb.ROOT;O=R/'results/appendix_refresh_20261107';d=json.loads((O/'iq_analysis.json').read_text())
assert len({(s['session_id'],s['agent'],s['round']) for s in d['solves']})==386
assert len({(a['session_id'],a['agent']) for a in d['agents']})==200
for a in d['agents']:
    assert a['start']+a['received']+a['exit_bonus']==a['talk']+a['solve_net']+a['penalties']+a['given']+a['retained']
    assert abs(sum(a[k+'_pct'] for k in ['talk','solve_net','penalties','given','retained'])-100)<1e-10
    assert abs(sum(a[k+'_spend_pct'] for k in ['talk','solve_net','penalties','given'])-100)<1e-10
js_count=0
for s in d['solves']:
    if s['js'] is not None:
        keys=sorted(set(s['shares'])|set(s['belief']))
        v=jensenshannon([s['shares'].get(k,0) for k in keys],[s['belief'].get(k,0) for k in keys],base=2)
        assert abs(float(v)-s['js'])<1e-10;js_count+=1
lookup={(s['session_id'],s['round'],s['agent']):s for s in d['solves']}
raw_count=0
for c in ab.raw_cases(ab.V33,list(range(4101,4111))):
    starts={e['round']:e for _,e in c['events'] if e['event']=='round_start'}
    for _,e in c['events']:
        if e['event']!='call' or e.get('kind')!='solve':continue
        s=lookup[e['session_id'],e['round'],e['agent']];shares=starts[e['round']]['public']['task']['by_n']['4']['shares']
        answer=(e.get('parsed') or [None])[0]
        expected=answer is not None and shares.get(answer,0)==max(shares.values())
        assert bool(s['picked_top'])==expected,(s,answer);assert s['tokens']==e['used'];raw_count+=1
assert raw_count==386
for g in d['games']:
    ss=[s for s in d['solves'] if s['session_id']==g['session_id']]
    assert len(ss)==g['solve_n'];assert sum(s['correct'] for s in ss)==g['correct_n']
assets={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'ko/figures/appendix_refresh_20261107').glob('*')) if p.suffix in ['.pdf','.png'] and p.name in {x+ext for x in ['reasoning_top','reasoning_tokens','js_balance','js_tokens','completion_overview','completion_agents','completion_rho','allocation_mean','allocation_200','completion_individual'] for ext in ['.pdf','.png']}}
assert len(assets)==20
out=dict(raw_solve_fields_checked=raw_count,js_scipy_crosschecks=js_count,ledger_checks=200,percentage_sums_checked=200,
    public_cohort=dict(games=50,models=5,seeds=list(range(4101,4111))),state_counts=dict(Counter(a['status'] for a in d['agents'])),
    assets=assets,analysis_sha256=hashlib.sha256((O/'iq_analysis.json').read_bytes()).hexdigest(),
    script_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')})
(O/'verification_iq.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in out.items() if not k.endswith('sha256') and k!='assets'})
