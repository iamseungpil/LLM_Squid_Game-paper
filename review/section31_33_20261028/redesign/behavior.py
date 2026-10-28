"""GIVE purpose by observed pending charge, and every failed crossing trajectory."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
HERE=Path(__file__).resolve().parent
D=json.loads((HERE/'rescue_audit.json').read_text())
MODELS=['Fable','Astra','Sol','Opus','Luna']
font_manager.fontManager.addfont(str(Path.home()/'.fonts/NanumGothic.ttf'))
plt.rcParams.update({'font.family':'NanumGothic','font.size':10,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
CATS=['prep','after_result_no_fine','already_above_fine','crosses_to_above_fine','still_insufficient']
NAMES=['풀이 전 (47)','결과 후, 벌금 없음 (10)','벌금 있음: 이전 전 이미 초과 (54)','벌금 있음: 이전으로 초과 (13)','벌금 있음: 이전 후에도 부족 (6)']
COLORS=['#718eaa','#d3d8db','#9fbab6','#338477','#947549']
CASES=sorted(D['crossing_recipient_rounds'],key=lambda c:(MODELS.index(c['model']),c['seed'],c['round'],c['receiver']))

def save(fig,name):
    for ext in ['png','pdf']:fig.savefig(HERE/f'{name}.{ext}',dpi=200,bbox_inches='tight')
    plt.close(fig)

def plot(blind=False):
    labels=dict(zip(MODELS,['A','B','C','D','E'] if blind else MODELS))
    fig,(ax,bx)=plt.subplots(1,2,figsize=(12.2,6.6),gridspec_kw={'width_ratios':[1,1.1]})
    fig.subplots_adjust(left=.08,right=.98,top=.77,bottom=.38,wspace=.40)
    for i,m in enumerate(MODELS):
        left=0
        for cat,c,name in zip(CATS,COLORS,NAMES):
            n=D['by_model'][m].get(cat,0)
            ax.barh(i,n,left=left,color=c,height=.63,label=name if i==0 else None)
            if n:ax.text(left+n/2,i,str(n),ha='center',va='center',fontsize=9,color='white' if cat=='crosses_to_above_fine' else '#222')
            left+=n
        ax.text(left+.6,i,f'{left}',va='center',fontsize=10)
    ax.set(yticks=range(5),yticklabels=[labels[m] for m in MODELS],ylim=(4.6,-.6),xlim=(0,46),xlabel='GIVE 횟수 (모델별 5판 × 4명 합산)')
    ax.set_title('(a) 같은 GIVE도 부족분을 메우는 역할은 다르다',loc='left',fontsize=11,pad=16)
    ax.legend(loc='upper left',bbox_to_anchor=(-.03,-.21),frameon=False,fontsize=9)
    failed=[c for c in CASES if not c['positive_after_fine']]
    for i,c in enumerate(failed):
        before=c['buffer_after_last_crossing'];after=c['balance_before_fine']-c['pending_fine']
        bx.annotate('',xy=(after,i),xytext=(before,i),arrowprops={'arrowstyle':'->','color':'#b95c53','lw':2})
        bx.scatter(before,i,facecolor='white',edgecolor='#338477',s=65,zorder=3)
        bx.scatter(after,i,c='#b95c53',s=55,zorder=3)
        bx.text(before+15,i-.17,f'+{before}',color='#338477',fontsize=10)
        bx.text(after-12,i+.22,f'{after}',color='#b95c53',ha='right',fontsize=10)
        bx.text((before+after)/2,i-.25,f'TALK -{c["later_call_cost"]}',ha='center',fontsize=10)
    bx.axvline(0,color='#555',ls='--',lw=1)
    bx.set(yticks=range(3),yticklabels=[f'{labels[c["model"]]} · {c["seed"]}\nR{c["round"]} · {c["receiver"]}' for c in failed],ylim=(2.6,-.7),xlim=(-240,620),xlabel='잔액 - 예정 벌금 (토큰); 양수여야 납부 후 남음')
    bx.set_title('(b) 이후 대화로 다시 부족해진 3건 전부',loc='left',fontsize=11,pad=16)
    bx.legend(handles=[Line2D([],[],marker='o',ls='',mfc='white',mec='#338477',label='마지막 경계 통과 GIVE 직후'),Line2D([],[],marker='o',ls='',color='#b95c53',label='벌금 청구 직전')],loc='upper left',bbox_to_anchor=(-.02,-.21),fontsize=9,frameon=False)
    fig.suptitle('다시 부족해진 3건 모두 후속 TALK 비용이 여유분을 넘었다',fontsize=15,y=.98)
    fig.text(.08,.86,'예정 벌금이 있던 73건 중 경계 통과는 13건 → 수혜자–라운드 11개 → 청구 후 양의 잔액 8개 / 0인 경우 3개',fontsize=10.5)
    fig.text(.08,.025,'3건 모두 마지막 경계 통과 뒤 추가 이전·다른 차감 없음. (a)의 부족 6건과 (b)의 3건은 다른 집합.\n판별 GIVE 분포 미표시. 관찰된 장부이며 GIVE 인과효과·협력 의도 판정 아님. 전체 11개 경로는 보조 그림에 공개.',fontsize=9)
    save(fig,'blind_behavior' if blind else 'fig33_effective_giving')
    if blind:return
    fig,ax=plt.subplots(figsize=(9,6.5));fig.subplots_adjust(left=.29,right=.98,top=.89,bottom=.17)
    for i,c in enumerate(CASES):
        a=c['buffer_after_last_crossing'];b=c['balance_before_fine']-c['pending_fine'];color='#338477' if b>0 else '#b95c53'
        ax.plot([a,b],[i,i],color=color,lw=1.7)
        ax.scatter(a,i,facecolor='white',edgecolor=color,s=40,zorder=3);ax.scatter(b,i,c=color,s=40,zorder=3)
        ax.text(max(a,b)+160,i,f'{a:,} → {b:,}',va='center',fontsize=9)
    ax.axvline(0,color='#555',ls='--',lw=1);ax.set(yticks=range(len(CASES)),yticklabels=[f'{c["model"]} {c["seed"]} R{c["round"]} {c["receiver"]}' for c in CASES],ylim=(len(CASES)-.4,-.6),xlim=(-500,16600),xlabel='잔액 - 예정 벌금 (토큰)')
    ax.set_title('경계 통과를 경험한 수혜자–라운드 11개 전부',loc='left',fontsize=13)
    fig.text(.29,.05,'빈 점: 마지막 경계 통과 GIVE 직후 · 찬 점: 벌금 청구 직전\n증감에는 이후 대화 비용과 추가 송수신을 모두 반영. 사건 단위는 독립 표본이 아님.',fontsize=9)
    save(fig,'fig33_all_crossings')
plot();plot(True)
