"""Read-only raw and cached cohort checks for the current appendix O/P/Q assets."""
import json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import feedback_20261028 as fb
import ablation_prize_20261103 as ab
import coexistence_rmst_20261103 as cx
from inequality import distribution
ROOT=fb.ROOT;SEEDS=list(range(4101,4111))
prize=json.loads((ROOT/'results/prize_robustness_20261105.json').read_text())
opened=json.loads((ROOT/'results/cohort_open_20261105.json').read_text())
cohorts=dict(prize['arms'],open=opened);out={};sources={}
for arm,d in cohorts.items():
    for src in d['sources']:
        p=Path(src['path']);raw=fb.read_bytes(p);assert fb.sha(raw)==src['sha256_decompressed'],str(p)
        sources[str(p)]=src['sha256_decompressed']
    patterns={'main':ab.V33,'open':'~/squid5-runs/e52_v33/squid5_e52v33_codex_*4/*'}
    pat=patterns.get(arm,f'~/squid5-runs/e52_v33ab/squid5_e52v33ab_{arm}_docker_*4/*')
    with patch.object(fb,'MODELS',d['models']):cases=ab.raw_cases(pat,SEEDS)
    expected={(g['model'],g['seed']):g for g in d['games']};assert len(cases)==len(expected)
    rows=[]
    for c in cases:
        g=expected[c['model'],c['seed']];e=[e for _,e in c['events']];r=c['result']
        independent=fb.game_metrics(e,r,c['model'],include_singleton=True)
        for key in ['given','n_give','rho','goal','finishers','exited','dead','all4_completion']:assert independent[key]==g[key],(arm,key)
        rounds=[z for z in e if z['event']=='round'];starts=[z for z in e if z['event']=='round_start']
        first=min((z['round'] for z in rounds if any(v['status']!='in' for v in z['agents'].values())),default=8)
        assert first/8==g['C'];assert g['given']/sum(len(z['taking_part']) for z in starts)==g['given_per_agent_round']
        terminal=[v['final'] if v['status']=='in' else 0 for v in r['agents'].values()]
        assert sorted(terminal)==sorted(g['terminal']['tokens'])
        for key,value in distribution(terminal).items():
            assert value==g['terminal'][key],(arm,key,value,g['terminal'][key])
        for key,value in independent['historic_settled'].items():
            assert value==g['settled'][key],(arm,'settled',key)
        rows.append(dict(model=c['model'],seed=c['seed'],C=g['C'],rho=g['rho'],finishers=g['finishers']))
    out[arm]=dict(games=len(rows),models=d['models'],seeds=SEEDS,raw_recomputed_metrics_match=True)
public=cohorts['main'];km=json.loads((ROOT/'results/individual_km_20261105.json').read_text())
for m,v in km['models'].items():
    gs=[g for g in public['games'] if g['model']==m]
    curve=[1]+[sum(g['remaining_after_round'][r] for g in gs)/40 for r in range(8)]
    assert curve==v['remaining_share'];assert sum(g['finishers'] for g in gs)==v['finishers']
out['individual_km']=dict(models=5,agents=200,curves_match=True)
out['sources']=sources
(ROOT/'results/appendix_refresh_20261107/current_opq_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='sources'})
