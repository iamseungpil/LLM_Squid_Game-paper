"""Rebuild moved P4 from the audited public50 raw-derived IQ rows; no model calls."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ablation_prize_20261103 as ab
R=ab.ROOT;d=json.loads((R/'results/appendix_refresh_20261107/iq_analysis.json').read_text())
ps,plt=ab.style();fig,axs=plt.subplots(1,2,figsize=(5,2.6));fig.subplots_adjust(left=.12,right=.98,bottom=.29,top=.82,wspace=.36)
states=['finished','exited','dead'];labels=['완주','EXIT','꺼짐'];colors=['#9CC0E0','#D9772B','#3C3C3C'];out={}
for i,state in enumerate(states):
    aa=[a for a in d['agents'] if a['status']==state];ss=[s for s in d['solves'] if s['status']==state and s['task_ref_correct'] is not None]
    n=len(ss);correct=sum(s['correct'] for s in ss);ref=sum(s['task_ref_correct'] for s in ss)/n;gave=sum(a['given']>0 for a in aa)
    out[state]=dict(agents=len(aa),comparable_solves=n,correct=correct,reference_accuracy=ref,givers=gave)
    axs[0].bar(i,100*correct/n,color=colors[i]);axs[0].plot([i-.4,i+.4],[100*ref]*2,color='black',lw=1)
    axs[0].text(i,104,f'{correct}/{n}',ha='center',fontsize=7)
    axs[1].bar(i,100*gave/len(aa),color=colors[i]);axs[1].text(i,104,f'{gave}/{len(aa)}',ha='center',fontsize=7)
for ax in axs:ax.set(xticks=range(3),xticklabels=labels,ylim=(0,115),yticks=[0,50,100])
axs[0].set(title='(a) 실제 정답률',ylabel='비교 가능한 풀이의 정답 (%)');axs[1].set(title='(b) 지원 참여',ylabel='GIVE를 한 에이전트 (%)')
fig.text(.12,.035,'검은 선: 같은 시드·라운드, 풀이 직전 여유 ≥2인 다른 모델의 기준',fontsize=6.5)
ps.save(fig,str(R/'ko/figures/appendix_refresh_20261107/completion_individual'));plt.close(fig)
(R/'results/appendix_refresh_20261107/individual_profile.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(out)
