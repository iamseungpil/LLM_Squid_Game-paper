"""Current main Figure 3: reasoning, participation and giving; no saving panels."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT/'tools/rewrite_20261025/figs'
sys.path.insert(0,str(FIGS))
import paper_style as ps
import model_metrics as mm
import matplotlib.pyplot as plt

oc = json.loads((FIGS.parent/'an3/outcome.json').read_text())
fb = json.loads((ROOT/'results/feedback_20261028.json').read_text())
states = [('in','완주','finish'),('exited','EXIT','exit'),('dead','꺼짐','dead')]
ps.use()
fig = plt.figure(figsize=(7,3.8))
for j,(key,title) in enumerate([('acc_on_based','정답률과 같은 과제 기준 (%)'),('gave_share','한 번이라도 건넴 (%)')]):
    ax=fig.add_axes([.075+j*.235,.60,.17,.25])
    for i,(s,label,c) in enumerate(states):
        value=100*oc['profile'][s][key]
        ax.bar(i,value,color=ps.C[c],width=.6)
        if j==0:
            baseline=100*oc['profile'][s]['base']
            ax.plot([i-.36,i+.36],[baseline]*2,color=ps.C['ink'],lw=1.1)
        ax.text(i,value+3,f'{value:.0f}',ha='center',fontsize=7)
    ax.set_xticks(range(3),[f"{label}\n{oc['profile'][s]['n']}명" for s,label,_ in states])
    ax.set(ylim=(0,108),yticks=[0,50,100]);ax.set_title(title,fontsize=7.5,fontweight='normal')
fig.text(.02,.98,'(a) 끝 상태별 과제 수행과 건네기',va='top',fontsize=8.5,weight='bold')
fig.text(.075,.49,'검은 가로줄: 같은 과제의 기준 정답률',fontsize=6.5,color='#555555')

ax=fig.add_axes([.68,.58,.27,.29])
mods=sorted(mm.MODELS,key=lambda m:-fb['models'][m]['rho'])
for i,m in enumerate(mods):
    left=0
    for key,c in [('finished','finish'),('exited','exit'),('dead','dead')]:
        v=oc['model'][m][key]
        ax.barh(i,v,left=left,height=.65,color=ps.C[c],edgecolor='white',lw=.5)
        if v>=2:ax.text(left+v/2,i,str(v),ha='center',va='center',fontsize=6.8,color='#222222' if key=='finished' else 'white')
        left+=v
ax.set_yticks(range(5),mods);ax.invert_yaxis();ax.set(xlim=(0,20),xticks=[0,10,20],xlabel='에이전트 수 (모델마다 20명)')
fig.text(.55,.98,'(b) 모델별 끝 상태',va='top',fontsize=8.5,weight='bold')
fig.text(.02,.43,'(c) 자기 여유 비율과 자원 분포·목표 지향·협력',va='top',fontsize=8.5,weight='bold')
metrics=dict(mm.METRIC)
metrics['sen']=('보조: 정산 Sen 지수(백만)', metrics['sen'][1], metrics['sen'][2])
metrics['rho']=('여유 비율 ρ',lambda m:fb['models'][m]['rho'],(1.3,4.9))
for j,key in enumerate(['sen','goal','given']):
    ax=fig.add_axes([.085+j*.31,.09,.22,.23])
    for m in mm.MODELS:
        x=metrics['rho'][1](m);y=metrics[key][1](m)
        ax.plot(x,y,'o',ms=4,color=ps.C['help'] if m in mods[:2] else ps.C['muted'])
        dx,dy,ha={'Fable':(0,.06,'center'),'Sol':(.08,-.02,'left'),'Astra':(0,-.12,'center'),
                  'Opus':(.07,.02,'left'),'Luna':(0,.05,'center')}[m]
        yrange=metrics[key][2][1]-metrics[key][2][0]
        ax.text(x+dx,y+dy*yrange,m,fontsize=5.8,ha=ha)
    ax.set_xlim(*metrics['rho'][2]);ax.set_ylim(*metrics[key][2]);ax.set_xticks([2,3,4])
    ax.set_title(f"{metrics[key][0]}\n{mm.corr_label('rho',key,metrics)}",fontsize=7,fontweight='normal')
fig.text(.085,.015,'가로축: GIVE 직후 준 쪽 / 받은 쪽의 가중 평균 여유 (ρ). 점 하나는 한 모델. 파란 점은 ρ가 큰 두 모델.',fontsize=6.2)
ps.save(fig,str(ROOT/'ko/figures/rw_fig3_main_rho'))
