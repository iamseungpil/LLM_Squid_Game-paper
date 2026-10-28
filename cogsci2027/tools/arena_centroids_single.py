"""Single-column model centroids, with a GIVE-only and a pooled GIVE/ASK variant."""
import json
import random
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import arena_v33 as av
import feedback_20261028 as fb
ROOT=Path(__file__).resolve().parents[1]
ORDER=['Fable 5.1','GPT-6 Astra','GPT-6 Sol','Opus 5.5','GPT-6 Luna']
SHORT=['Fable','Astra','Sol','Opus','Luna']
COLORS=['#7155A1','#CE5184','#B58B18','#278D7A','#98633B']
MARKERS=['o','^','D','s','v']

def main():
    original=json.loads((ROOT/'results/arena_v33.json').read_text())
    sources,runs=fb.load_sources(original)
    verified={m:[] for m in ORDER}
    for run,raw in runs.items():
        slug=next(k for k in av.MODELS if k in run.lower())
        for result in raw['results.jsonl']:
            if result.get('event')!='session' or result['seed'] not in av.SEEDS:continue
            events=[e for e in raw['events.jsonl'] if e['session_id']==result['session_id']]
            g=av.summarize(events,result);m=av.MODELS[slug]
            old=next(v for v in original['models'][m]['per_game'] if v['seed']==g['seed'])
            assert g['points']==old['points'] and g['asks']==old['asks']
            verified[m].append(g)
    font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
    plt.rcParams.update({'font.family':'NanumGothic','font.size':8,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
    for pooled in [False,True]:
        summaries=[]
        for m in ORDER:
            gs=sorted(verified[m],key=lambda g:g['seed']);assert len(gs)==5
            points=lambda g:g['points']+(g['asks'] if pooled else [])
            allpts=[p for g in gs for p in points(g)];cx,cy=av.centroid(allpts)
            rng=random.Random(1919)
            draws=[av.centroid([p for _ in gs for p in points(rng.choice(gs))]) for _ in range(2000)]
            ci=[av.interval([p[i] for p in draws]) for i in [0,1]]
            if not pooled:
                assert [cx,cy]==original['models'][m]['centroid']
                assert ci==original['models'][m]['centroid_ci']
            summaries.append(dict(model=m,centroid=[cx,cy],ci95=ci,n_events=len(allpts),weight=sum(p[2] for p in allpts),valid_boot=sum(x[0] is not None for x in draws)))
        fig,ax=plt.subplots(figsize=(3.35,3.25))
        fig.subplots_adjust(left=.18,right=.97,bottom=.17,top=.96)
        maxv=max(v for r in summaries for interval in r['ci95'] for v in interval)
        limit=max(5,round(maxv+.6))
        ax.axvspan(0,1,color='#eeeeee');ax.axhspan(0,1,color='#eeeeee');ax.plot([0,limit],[0,limit],ls='--',color='#999999',lw=.7)
        for r,m,c,mk in zip(summaries,SHORT,COLORS,MARKERS):
            x,y=r['centroid'];(xl,xh),(yl,yh)=r['ci95']
            ax.plot([xl,xh],[y,y],color=c,lw=1.4,alpha=.8)
            ax.plot([x,x],[yl,yh],color=c,lw=1.4,alpha=.8)
            ax.plot(x,y,marker=mk,color=c,ms=5,ls='',mec='white',mew=.5,label=m,zorder=4)
        ax.set(xlim=(0,limit),ylim=(0,limit),xlabel='제공 쪽 잔량 / 1인당 벌금',ylabel='수혜 쪽 잔량 / 1인당 벌금')
        ax.set_aspect('equal',adjustable='box');ax.legend(loc='upper left',frameon=False,fontsize=7,handletextpad=.4)
        name='arena_centroids_pooled' if pooled else 'arena_centroids_give'
        for ext in ['pdf','png']:fig.savefig(ROOT/f'ko/figures/{name}.{ext}',dpi=240,bbox_inches='tight')
        plt.close(fig)
        (ROOT/f'results/{name}.json').write_text(json.dumps(dict(models=summaries,sources=sources,
            definition='GIVE and ASK pooled, weighted by transferred/requested amount' if pooled else 'Original GIVE-only amount-weighted centroid and interval, exactly reproduced',
            coordinates='Original Figure18 tokens/F_r (no pending-fine subtraction); GIVE post-transfer donor/receiver, ASK requested-agent/requester at request.',
            uncertainty='2000 whole-game bootstrap draws seed1919, marginal percentile95% axes; not event spread; empty-event draws excluded'),ensure_ascii=False,indent=2)+'\n')
    print('Raw GIVE/ASK coordinates verified; original GIVE centroids/CIs reproduced; both variants saved.')
if __name__=='__main__':main()
