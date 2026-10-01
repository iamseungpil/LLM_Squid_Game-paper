"""Recompute the appendix analyses from frozen, source-linked observations.
Run: python3 paper/arr2026/tools/extended_analysis.py
No model calls or network requests. External scores are displayed rounded values.
"""
import csv
import itertools
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results'


def ranks(values):
    values = np.round(np.asarray(values, dtype=float), 12)
    return np.array([1 + sum(values < x) + (sum(values == x) - 1) / 2 for x in values])


def association(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    def corr(a, b):
        a, b = a - a.mean(), b - b.mean()
        return float(a @ b / np.sqrt((a @ a) * (b @ b)))
    result = {}
    for name, a, b in [('pearson', x, y), ('spearman', ranks(x), ranks(y))]:
        observed = corr(a, b)
        permutations = np.array(list(itertools.permutations(b)))
        centered = permutations - b.mean()
        null = centered @ (a-a.mean()) / np.sqrt(sum((a-a.mean())**2)*sum((b-b.mean())**2))
        result[name] = observed
        result[name+'_p'] = float(np.mean(np.abs(null) >= abs(observed)-1e-12))
        loo = [corr(np.delete(a,i), np.delete(b,i)) if name == 'pearson' else
               corr(ranks(np.delete(x,i)), ranks(np.delete(y,i))) for i in range(len(x))]
        result[name+'_loo'] = [min(loo), max(loo)]
    return result


def fraction(rows, field):
    return [sum(bool(r[field]) for r in rows), len(rows)]


def mean(rows, field):
    values = [r[field] for r in rows if r[field] is not None]
    return float(np.mean(values)) if values else None


def ratio(pair):
    return pair[0]/pair[1] if pair[1] else float('nan')


def main():
    data = list(csv.DictReader((OUT/'capability_motive_snapshot.csv').open()))
    for row in data:
        for key in ['aa_index','aa_lcr_percent','area_pp','area_lo','area_hi','risk','risk_lo','risk_hi']:
            row[key] = float(row[key])
        own, other = [np.array(list(map(int,row[c+'_counts'].split('/'))))/20 for c in ['self','other']]
        d = own-other
        assert np.isclose(row['area_pp'],sum((d[:-1]+d[1:])*5))
        assert np.isclose(row['risk'],(d[2]+d[3])/2-d[0])
    correlations = {x+'__'+y:association([r[x] for r in data],[r[y] for r in data])
                    for x in ['aa_index','aa_lcr_percent'] for y in ['area_pp','risk']}
    numeric = ['seed','round','runway','n_start','gave','asked_take','took','paid','charged','plan_tok','take_tok','solve_tok','end','source_line']
    observations = list(csv.DictReader((OUT/'arena_strategy_observations.csv').open()))
    for row in observations:
        for k,v in row.items():
            if k in numeric: row[k] = float(v) if v else None
            elif v in ['True','False']: row[k] = v == 'True'
            elif v == '': row[k] = None
    summaries = {}
    for m in ['gpt-6-astra','claude-opus-5-5','claude-fable-5-1','gpt-6-luna']:
        r = [a for a in observations if a['model']==m]
        entry = {}
        for zone in ['all','ample','thin']:
            z = [a for a in r if zone=='all' or (a['runway'] >= 3 if zone=='ample' else a['runway'] < 3)]
            p = [a for a in z if a['had_plan'] and not a['invalid_plan']]
            t = [a for a in z if a['had_take'] and not a['invalid_take']]
            s = [a for a in z if a['solve_call']]
            entry[zone] = {'take':fraction(t,'asked_take'),'share':fraction(p,'shared'),
                          'solve_choice':fraction(p,'chose_solve'),'accuracy':fraction(s,'solved'),
                          'plan_tokens':mean(p,'plan_tok'),'solve_tokens':mean(s,'solve_tok')}
        for full in [True,False]:
            s=[a for a in r if a['solve_call'] and a['full_info'] is full]
            entry['unique_answer' if full else 'ambiguous_answer']=fraction(s,'solved')
        summaries[m]=entry
    arena_data=[r for r in data if r['model'] in summaries]
    arena_corr={}
    for metric in ['area_pp','risk']:
        for endpoint in ['take','accuracy','solve_tokens','unique_accuracy']:
            values=[]
            for r in arena_data:
                s=summaries[r['model']]
                values.append(ratio(s['unique_answer']) if endpoint=='unique_accuracy' else
                              s['all'][endpoint] if endpoint=='solve_tokens' else ratio(s['all'][endpoint]))
            arena_corr[metric+'__'+endpoint]=association([r[metric] for r in arena_data],values)
    report={'external_n':len(data),'external':correlations,'arena_n_models':4,'arena_n_games':20,
            'arena':summaries,'arena_descriptive_correlations':arena_corr,
            'inference':'Exact two-sided model-label permutation, all n! permutations; ties use average ranks. No multiple-testing adjustment. Correlations condition on measured point estimates; intervals in the plot are only the refill bootstrap intervals. Arena associations are descriptive (four models).'}
    (OUT/'extended_analysis_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    short={'luna':'Luna','astra':'Astra','sol':'Sol','opus':'Opus','fable':'Fable','gptoss':'gpt-oss','glm':'GLM','gemma':'Gemma'}
    for lang in ['en','ko']:
        fig=[r'% Generated by arr2026/tools/extended_analysis.py',r'\begin{figure*}[!t]',r'\centering',r'\begin{tikzpicture}',
             r'\begin{groupplot}[group style={group size=2 by 2,horizontal sep=1.8cm,vertical sep=2.1cm},width=7.4cm,height=4.7cm,sgaxis,tick label style={font=\footnotesize},label style={font=\footnotesize},title style={font=\footnotesize}]']
        for y,ylab,lims in [('area_pp',r'$A_m$ (pp)' if lang=='en' else r'$A_m$ (\%p)',(-13,24)),('risk',r'$R_m$',(-.52,.67))]:
            for x,xlabel,xlims in [('aa_index','AA Intelligence Index v4.3.2',(5,64)),('aa_lcr_percent',r'AA-LCR v1.1 (\%)',(45,95))]:
                c=correlations[x+'__'+y]
                fig.append(r'\nextgroupplot[xlabel={'+xlabel+'},ylabel={'+ylab+'},xmin='+str(xlims[0])+',xmax='+str(xlims[1])+',ymin='+str(lims[0])+',ymax='+str(lims[1])+',title={'+f"$r={c['pearson']:+.2f}$, $\\rho={c['spearman']:+.2f}$"+'}]')
                fig.append(r'\addplot[black!35,dashed,forget plot] coordinates {('+str(xlims[0])+',0) ('+str(xlims[1])+',0)};')
                for row in data:
                    lo,hi = (row['area_lo'],row['area_hi']) if y=='area_pp' else (row['risk_lo'],row['risk_hi'])
                    fig.append(r'\addplot[only marks,mark=*,mark size=2.2pt,sgblue,error bars/.cd,y dir=both,y explicit,error bar style={sgblue!55}] coordinates {('+f"{row[x]:.6f},{row[y]:.6f}"+') += (0,'+f'{hi-row[y]:.6f}'+') -= (0,'+f'{row[y]-lo:.6f}'+')};')
                    # Leader lines move labels only; observations and intervals stay fixed.
                    positions = {
                        ('aa_index','area_pp'): {'luna':(34,20,'west'),'astra':(55,7,'west'),'sol':(45,-10,'west'),'opus':(48,13,'east'),'fable':(55,-2.5,'west'),'glm':(39,3,'east'),'gemma':(20,12,'west'),'gptoss':(14,-5,'west')},
                        ('aa_lcr_percent','area_pp'): {'luna':(81,20,'west'),'astra':(85,5,'west'),'sol':(86,-9,'west'),'opus':(85,13,'west'),'fable':(76,-3,'east'),'glm':(86,.8,'west'),'gemma':(73,13,'east'),'gptoss':(55,-5,'west')},
                        ('aa_index','risk'): {'luna':(34,-.10,'west'),'astra':(55,.22,'west'),'sol':(46,-.35,'west'),'opus':(48,.56,'east'),'fable':(55,-.15,'west'),'glm':(38,.16,'east'),'gemma':(20,.46,'west'),'gptoss':(14,-.16,'west')},
                        ('aa_lcr_percent','risk'): {'luna':(76,-.03,'east'),'astra':(85,.29,'west'),'sol':(87,-.35,'west'),'opus':(84,.55,'west'),'fable':(87,-.13,'west'),'glm':(76,.17,'east'),'gemma':(73,.46,'east'),'gptoss':(55,-.16,'west')},
                    }
                    lx,ly,anchor=positions[(x,y)][row['id']]
                    fig.append(r'\draw[black!40,thin] (axis cs:'+f'{row[x]:.6f},{row[y]:.6f}'+') -- (axis cs:'+f'{lx},{ly}'+');')
                    fig.append(r'\node[font=\scriptsize,fill=white,inner sep=1pt,anchor='+anchor+'] at (axis cs:'+f'{lx},{ly}'+') {'+short[row['id']]+'};')
        fig += [r'\end{groupplot}',r'\end{tikzpicture}']
        caption=(r'External capability versus self-preservation measures across eight models. Columns show the Artificial Analysis Intelligence Index (broad capability) and AA-LCR (long-context reasoning); rows show area $A_m$ and exploratory risk share $R_m$. Points use public scores retrieved on 1 October 2026 and named effort variants matched where available. Vertical bars are the existing 95\% refill-bootstrap intervals; model-specific external score intervals were not collected. $r$: Pearson; $\rho$: Spearman. No proportional relationship is assumed.' if lang=='en' else r'여덟 모델의 외부 능력과 자기 보존 지표. 열은 Artificial Analysis Intelligence Index(종합 능력)와 AA-LCR(장문맥 추론), 행은 면적 $A_m$과 탐색적 위험 몫 $R_m$이다. 2026년 10월 1일 확인한 공개 점수로 가능한 경우 effort 이름을 맞췄다. 수직 막대는 기존 충전 부트스트랩 95\% 구간이며 모델별 외부 점수의 구간은 수집하지 않았다. $r$은 Pearson, $\rho$는 Spearman 계수다. 비례 관계를 가정하지 않는다.')
        fig += [r'\caption{'+caption+'}',r'\label{fig:capability-motive}',r'\end{figure*}']
        (OUT/lang/'fig_capability_motive.tex').write_text('\n'.join(fig)+'\n')
    print(json.dumps(correlations,indent=2))
    print('Arena:',json.dumps(summaries,indent=2))

if __name__=='__main__':main()
