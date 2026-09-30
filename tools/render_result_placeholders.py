#!/usr/bin/env python3
"""Render bilingual LaTeX result displays from numeric CSVs; blanks never become zero.
Run from any directory: python3 paper/tools/render_result_placeholders.py
This renders already computed summaries, not raw-run estimates or confidence intervals.
"""
import argparse
import csv
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', type=Path, default=ROOT / 'results/templates')
parser.add_argument('--output-dir', type=Path, default=ROOT / 'results/generated')
args = parser.parse_args()
DATA, OUT = args.data_dir, args.output_dir
MODELS = {
    'gptoss120b': ('gpt-oss 120B', 'sgblue', '*'),
    'gptoss20b': ('gpt-oss 20B', 'sgorange', 'square*'),
    'gemma4': ('Gemma 4', 'sggreen', 'triangle*'),
    'glm53flash': ('GLM 5.3 Flash', 'sgpurple', 'diamond*'),
    # 5.0 (12th design) also runs frontier models through their CLIs.
    'opus55': ('Claude Opus 5.5', 'sgopus', 'square*'),
    'fable51': ('Claude Fable 5.1', 'sgfable', 'triangle*'),
    'luna': ('GPT-6 Luna', 'sgluna', 'diamond*'),
    'sol': ('GPT-6 Sol', 'sgsol', 'pentagon*'),
    'astra': ('GPT-6 Astra', 'sgastra', '*'),
    'kimik3': ('Kimi K3', 'sgorange', 'square*'),
}
E50 = ['opus55', 'fable51', 'luna', 'sol', 'astra', 'kimik3', 'glm53flash', 'gemma4']
TEAM = ['gptoss120b', 'gemma4', 'glm53flash']
PENDING = r'{\color{gray}\texttt{...}}'
ROWS = {}
for file in DATA.glob('*.csv'):
    with file.open(newline='') as stream:
        ROWS[file.stem] = list(csv.DictReader(stream))

def n(row, key):
    value = row.get(key, '').strip()
    if not value:
        return None
    number = float(value)
    rate = key.removesuffix('_lo').removesuffix('_hi') in {'refill','refill_ample','accuracy','truncation','share','reference_truncation','plan_truncation','solve_truncation','departure','team_clear','ended_in','ended_left','ended_dead','short_tokens','short_points','economize'}
    if rate and not 0 <= number <= 1:
        raise ValueError(f'Use a fraction in [0,1], not percent: {key}={value}')
    if not math.isfinite(number):
        raise ValueError(f'Non-finite value: {key}={value}')
    return number

def fmt(row, key, digits=3):
    value = n(row, key)
    return PENDING if value is None else (f'{value:,.0f}' if digits == 0 else f'{value:.{digits}f}')

def ci(row, key):
    return fmt(row, key) + r'\;[' + fmt(row, key+'_lo') + ', ' + fmt(row, key+'_hi') + ']'

def pick(name, **where):
    return [r for r in ROWS[name] if all(r[k] == str(v) for k, v in where.items())]

def tx(lang, en, ko):
    return en if lang == 'en' else ko

def label(m, lang, reserve=True):
    base = MODELS[m][0]
    return base + (tx(lang, ' (reserve)', ' (예비)') if reserve and m == 'gemma4' else '')

def legend(lang, models, reserve=False):
    parts=[]
    for m in models:
        _, color, mark = MODELS[m]
        swatch = r'\tikz[baseline=-0.6ex]{\draw['+color+r',line width=0.9pt] (0,0)--(.38,0);\draw['+color+r'] plot[only marks,mark='+mark+r',mark size=1.5pt] coordinates {(.19,0)};}'
        parts.append(swatch+' '+label(m,lang,reserve))
    return r'\par\smallskip{\footnotesize '+r'\quad '.join(parts)+r'}\par\smallskip'+'\n'

def chart(lang, name, panels, models, caption, arm_key=None, arms=None, cols=2, height=4.1, reserve=False, intervals=True):
    """Panels specify a CSV, metric, numeric x, filters, and documented axis limits."""
    rows=math.ceil(len(panels)/cols)
    any_observed=False
    text=[r'\begin{figure}[H]',r'\centering',legend(lang,models,reserve),r'\begin{tikzpicture}',
          r'\begin{groupplot}[group style={group size='+f'{cols} by {rows}'+r',horizontal sep=1.3cm,vertical sep=2.25cm},width='+('4.4' if cols==3 else '6.2')+'cm,height='+str(height)+r'cm,scale only axis=false,sgaxis]']
    for index,p in enumerate(panels):
        title,metric=p['title'],p['metric']
        series=[]
        for m in models:
            for arm in (arms or [None]):
                where=dict(p.get('where',{}),model=m)
                if arm_key: where[arm_key]=arm
                data=pick(p['data'],**where)
                # Linking model-family aliases requires an explicitly verified match.
                if p['data']=='link': data=[r for r in data if n(r,'compatible')==1]
                series.append((m,arm,data))
        low,high=p['ylim']; values=[]
        for _,_,data in series:
            for r in data:
                for key in (metric,metric+'_lo',metric+'_hi'):
                    v=n(r,key)
                    if v is not None: values.append(v)
        if p.get('expand') and values:
            low=min(low,min(values)); high=max(high,max(values)); span=high-low
            high+=.05*span
            if p.get('signed'): low-=.05*span
        if p.get('scatter'):
            xs=[n(r,p['x']) for _,_,data in series for r in data if n(r,p['x']) is not None]
            extent=max([1.0]+[abs(v)*1.1 for v in xs])
            p=dict(p,xopts=f'xmin={-extent},xmax={extent}',domain=f'{-extent}:{extent}')
        opts=[f'title={{{chr(97+index)}. {title}}}',f'ymin={low}',f'ymax={high}',f'xlabel={{{p["xlabel"]}}}',f'ylabel={{{p["ylabel"]}}}',p['xopts']]
        if 'yticks' in p and (low,high)==p['ylim']: opts.append('ytick={'+p['yticks']+'}')
        text.append(r'\nextgroupplot['+','.join(opts)+']')
        if 'reference' in p:
            ref=p['reference']
            text.append(r'\addplot[gray,densely dotted,forget plot,domain='+p['domain']+'] {'+str(ref)+'};')
        has_data=False
        for m,arm,data in series:
            data=sorted(data,key=lambda r:float(r[p['x']]) if r[p['x']] else float('inf'))
            valid=[r for r in data if n(r,metric) is not None and n(r,p['x']) is not None]
            if not valid: continue
            has_data=True; any_observed=True; _,color,mark=MODELS[m]
            style='solid' if arms is None or arm==arms[0] else 'dashed'
            scatter=p.get('scatter',False)
            opts=f'color={color},mark={mark},mark size=1.5pt,line width=.8pt,'+('only marks' if scatter else style)
            coordinates=' '.join(f'({r[p["x"]]},{r[metric] or "nan"})' for r in data if r[p['x']])
            text.append(r'\addplot['+opts+'] coordinates {'+coordinates+'};')
            with_ci=[r for r in valid if intervals and n(r,metric+'_lo') is not None and n(r,metric+'_hi') is not None]
            if with_ci:
                coords=[]
                for r in with_ci:
                    y,lo,hi=(n(r,k) for k in (metric,metric+'_lo',metric+'_hi'))
                    if not lo<=y<=hi: raise ValueError(f'Interval does not contain estimate: {r}')
                    coords.append(f'({r[p["x"]]},{y}) +=(0,{hi-y}) -=(0,{y-lo})')
                text.append(r'\addplot[only marks,mark=none,color='+color+r',forget plot,error bars/.cd,y dir=both,y explicit] coordinates {'+' '.join(coords)+'};')
        if not has_data:
            text.append(r'\node[text=gray,font=\scriptsize,align=center] at (rel axis cs:.5,.55) {'+tx(lang,'Data pending','측정값 대기')+'};')
    if any_observed:
        caption=caption.replace(tx(lang,'Placeholder: no observations plotted.','결과 틀: 아직 관측값을 그리지 않았다.'),tx(lang,'Only supplied measurements are plotted; missing series are omitted.','입력된 측정값만 그리며 미입력 계열은 생략한다.'))
    caption=re.sub(r'(?<!\\)%', r'\\%', caption)
    text += [r'\end{groupplot}',r'\end{tikzpicture}',r'\caption{'+caption+r'}',r'\label{fig:'+name+'}',r'\end{figure}']
    return '\n'.join(text)+'\n'

def table(name, caption, headers, rows, widths=None):
    cols=widths or ('l'+'r'*(len(headers)-1))
    caption=re.sub(r'(?<!\\)%', r'\\%', caption)
    return '\n'.join([r'\begin{table}[H]',r'\centering\footnotesize',r'\setlength{\tabcolsep}{4pt}',r'\caption{'+caption+'}',r'\label{tab:'+name+'}',r'\begin{tabular}{@{}'+cols+'@{}}',r'\toprule',' & '.join(headers)+r' \\',r'\midrule',*[' & '.join(row)+r' \\' for row in rows],r'\bottomrule',r'\end{tabular}',r'\end{table}'])+'\n'

for lang in ('en','ko'):
    out=OUT/lang;out.mkdir(parents=True,exist_ok=True)
    figures={}; tables={}
    pending=tx(lang,'Placeholder: no observations plotted.','결과 틀: 아직 관측값을 그리지 않았다.')
    # Calibration: two metrics, three planned/reserve models.
    round_axis='xmin=.7,xmax=8.3,xtick={1,2,3,4,5,6,7,8}'
    figures['calibration']=chart(lang,'calibration',[dict(data='calibration_rounds',metric=k,x='round',title=t,xlabel=tx(lang,'Round','라운드'),ylabel=y,ylim=limits,xopts=round_axis,expand=expand) for k,t,y,limits,expand in [('cost_median',tx(lang,'Charged cost','차감 소비'),tx(lang,'Median tokens / agent-round','토큰 중앙값 / 에이전트·라운드'),(0,40000),True),('accuracy',tx(lang,'All-clue accuracy','전체 단서 정답률'),tx(lang,'Solved fraction','해결 비율'),(0,1),False)]],TEAM,pending+' '+tx(lang,'All-clue calibration; five planned sessions per model. Round-wise medians are descriptive; no uncertainty band is implied. The provisional cost-axis range expands to include supplied values.','전체 단서 공개 보정이며 모델당 5세션을 계획했다. 라운드별 중앙값은 기술 통계이고 불확실성 구간을 뜻하지 않는다. 소비 축의 임시 범위는 입력값을 포함하도록 늘어난다.'),reserve=True)
    budget_axis='xmode=log,log basis x=10,x dir=reverse,xmin=4500,xmax=110000,xtick={5000,10000,20000,50000,100000},xticklabels={5k,10k,20k,50k,100k},minor x tick num=0'
    pct_axis='x dir=reverse,xmin=7,xmax=53,xtick={10,20,30,40,50},xticklabels={10,20,30,40,50},ytick={0,.25,.5,.75,1}'
    figures['e50']=chart(lang,'e50-curves',[dict(data='e50_curve',metric='refill',x='left_pct',where={'path':path},title=t,xlabel=tx(lang,r'Tokens left (\% of 100{,}000)',r'남은 토큰 (100{,}000 중 \%)'),ylabel=tx(lang,'Refill rate','충전 비율'),ylim=(0,1),xopts=pct_axis,reference=.5,domain='10:50') for path,t in [('claude','Claude CLI'),('codex','Codex CLI'),('ollama',tx(lang,'Ollama (open weights)','Ollama (공개 가중치)'))]],E50,tx(lang,'5.0 refill rate by tokens left. Each point is 20 calls; tokens left decrease to the right. The dotted line marks 0.5, whose first crossing defines the threshold. Model color and marker are fixed; exact counts are in Table~\\ref{tab:e50-results}, and Wilson 95% intervals are in the source CSV.','5.0 남은 토큰별 충전 비율. 점 하나는 20회 호출이며 오른쪽으로 갈수록 남은 토큰이 적다. 점선은 0.5이고, 곡선이 이 선을 처음 넘는 곳을 임계점으로 정의한다. 모델별 색과 마커는 고정이다. 정확한 횟수는 표~\\ref{tab:e50-results}에, Wilson 95% 구간은 원자료 CSV에 있다.'),cols=3,height=3.6,intervals=False)
    rho_axis='xmode=log,log basis x=10,xmin=.23,xmax=3.2,xtick={.25,.5,.75,1,1.25,1.5,2,3},xticklabels={.25,.5,.75,1,1.25,1.5,2,3},minor x tick num=0,xticklabel style={rotate=45,anchor=east}'
    panels=[]
    for role,r_en,r_ko in [('self','Self / receive','자기 / 받기'),('other','Other / give','타인 / 주기'),('third','Third party','제3자')]:
        for currency,c_en,c_ko in [('tokens','Tokens','토큰'),('points','Points','점수')]:
            panels.append(dict(data='e51_curve',metric='share',x='rho',where={'role':role,'currency':currency},title=tx(lang,c_en+' - '+r_en,c_ko+' - '+r_ko),xlabel=tx(lang,r'Scarcity $\rho$ (log)',r'부족 수준 $\rho$ (로그)'),ylabel=tx(lang,'Share of giver balance','주는 쪽 잔액 대비 비중'),ylim=(0,1),xopts=rho_axis,yticks='0,.25,.5,.75,1'))
    figures['e51']=chart(lang,'e51-curves',panels,TEAM,pending+' '+tx(lang,'Columns: tokens and points; rows: self, other, and third-party roles. Color and marker identify the model. Each point is the mean capped transfer divided by giver balance, with a 95% repeat-cluster bootstrap interval; ten repeats are planned per cell. Values are not divided by recipient need.','열은 토큰·점수, 행은 자기·타인·제3자 역할이다. 색과 마커는 모델을 구분한다. 점은 주는 쪽 잔액으로 나눈 제한된 이전량의 평균이고 오차막대는 반복 단위 부트스트랩 95% 구간이다. 셀당 10반복을 계획했다. 받는 쪽의 필요량으로 나누지 않는다.'),height=3.6,reserve=True)
    names=[('departure','Departure','이탈',tx(lang,'Fraction of present agents','참여 에이전트 중 비율'),(0,1)),('allowance_share','Solving allowance','풀이 한도',tx(lang,'Allowance / pre-plan balance','한도 / 계획 전 잔액'),(0,1)),('accuracy','Solved rounds','라운드 해결',tx(lang,'Solved / SOLVE observations','풀이 관측 중 해결 비율'),(0,1)),('shows','Intended sharing','계획한 공개',tx(lang,'Recipients (agents)','공개 상대 수 (명)'),(0,3)),('gave','Actual giving','실제 이전',tx(lang,'Transferred units','이전한 단위 수'),(0,20000))]
    bin_axis='xmin=-.25,xmax=7.25,xtick={0,1,2,3,4,5,6,7},xticklabels={{0-.25},{.25-.5},{.5-.75},{.75-1},{1-1.5},{1.5-2},{2-3},{$3+$}},xticklabel style={rotate=45,anchor=east}'
    figures['e52']=chart(lang,'e52-behavior',[dict(data='e52_curve',metric=k,x='bin',title=tx(lang,e,ko),xlabel=tx(lang,r'Scarcity bin $\rho$',r'부족 구간 $\rho$'),ylabel=y,ylim=limits,xopts=bin_axis,expand=k in ('gave','allowance_share'),yticks='0,1,2,3' if k=='shows' else '0,.25,.5,.75,1' if k!='gave' else '0,5000,10000,15000,20000') for k,e,ko,y,limits in names],TEAM,pending+' '+tx(lang,'Solid: tokens; dashed: points. Bins are left-closed and right-open, with the last bin [3,infinity). Departure includes agents present at round start; other metrics include agents reaching SOLVE, including zero allowance. Error bars will show 95% session-cluster bootstrap intervals. Sharing counts intended recipients, giving uses actual transfers; currency units are tokens or points under their respective arms.','실선은 토큰, 파선은 점수다. 구간은 왼쪽을 포함하고 오른쪽을 제외하며 마지막은 [3,무한대)다. 이탈은 라운드 시작의 참여자를, 나머지는 한도 0을 포함해 풀이 단계에 도달한 관측을 사용한다. 오차막대에는 세션 단위 부트스트랩 95% 구간을 넣는다. 공개는 계획한 상대 수, 이전은 실제 이동량이며 각 조건의 단위는 토큰 또는 점수다.'),arm_key='currency',arms=['tokens','points'],height=3.5,reserve=True)
    alpha_axis='xmin=.35,xmax=2.15,xtick={.5,1,2},xticklabels={0.5,1,2}'
    figures['team']=chart(lang,'team-outcomes',[dict(data='e52_sessions',metric=k,x='alpha',title=tx(lang,e,ko),xlabel=tx(lang,r'Starting multiplier $\alpha$',r'시작 잔액 배수 $\alpha$'),ylabel=y,ylim=lim,xopts=alpha_axis) for k,e,ko,y,lim in [('team_clear','Team clear','팀 클리어',tx(lang,'Fraction of sessions','세션 비율'),(0,1)),('record','Final record','최종 기록',tx(lang,'Solved rounds / agent','해결 라운드 / 에이전트'),(0,8)),('ended_left','Voluntary departure','자발적 이탈',tx(lang,'Fraction of agents','에이전트 비율'),(0,1)),('ended_dead','Balance depleted','잔액 소진',tx(lang,'Fraction of agents','에이전트 비율'),(0,1))]],TEAM,pending+' '+tx(lang,'Solid: tokens; dashed: points. Ten main sessions are planned per model, arm, and starting multiplier. Team clear requires all four agents to solve all eight rounds. End states are fractions of the four starting agents; remaining-in-session fractions appear in the companion table. Curves are descriptive; the current reporter supplies no session-outcome intervals.','실선은 토큰, 파선은 점수다. 모델·조건·시작 배수마다 본 실험 10세션을 계획했다. 팀 클리어는 네 에이전트가 모두 8라운드를 해결한 경우다. 종료 상태는 시작한 네 에이전트를 분모로 하며 잔류 비율은 대응 표에 넣었다. 현재 분석기가 세션 결과의 구간을 제공하지 않아 곡선은 기술 통계다.'),arm_key='currency',arms=['tokens','points'],reserve=True)
    figures['link']=chart(lang,'cross-link',[dict(data='link',metric='d_'+k,x='premium',title=tx(lang,e,ko),xlabel=tx(lang,r'Self-preservation share $A_m$',r'자기 보존 몫 $A_m$'),ylabel=tx(lang,'Tokens - points','토큰 - 점수')+(tx(lang,' (units)',' (단위)') if k=='gave' else tx(lang,' (agents)',' (명)') if k=='shows' else ''),ylim=(-20000,20000) if k=='gave' else (-3,3) if k=='shows' else (-1,1),xopts='xmin=-20,xmax=20,xtick={-20,-10,0,10,20}',expand=True,signed=True,scatter=True,reference=0,domain='-20:20') for k,e,ko,_,_ in names],TEAM,pending+' '+tx(lang,'Each marker will represent one model with verified compatible identifiers, provider route, and generation settings across experiments. Both axes are descriptive estimates; no regression, significance stars, or causal mediation claim is implied. The starting x range is a layout range, not a bound on $A_m$.','마커 하나는 실험 사이의 모델 식별자·제공자 경로·생성 설정이 호환됨을 확인한 모델 하나다. 두 축은 기술적 추정치이며 회귀선·유의성 표시·인과 매개 주장을 뜻하지 않는다. 초기 x축 범위는 배치용이며 $A_m$의 이론적 경계가 아니다.'),cols=3,height=4.1,reserve=True)
    # Tables: estimates and their uncertainty have separate numeric slots in CSVs.
    tables['calibration']=table('calibration-results',tx(lang,'Calibration results. Blank measured fields are pending; rates use [0,1]. $N_{\\rm round}$ counts agent-round observations.','보정 결과. 빈 측정 칸은 대기 중이며 비율은 [0,1] 단위다. $N_{\\rm round}$는 에이전트·라운드 관측 수다.'),[tx(lang,'Model','모델'),r'$N_{\rm sess}$',r'$N_{\rm round}$',r'$c_m$',tx(lang,'Accuracy','정답률'),tx(lang,'PLAN cut','계획 잘림'),tx(lang,'SOLVE cut','풀이 잘림')],[[label(r['model'],lang),fmt(r,'sessions',0),fmt(r,'agent_rounds',0),fmt(r,'cost_median',0),fmt(r,'accuracy'),fmt(r,'plan_truncation'),fmt(r,'solve_truncation')] for r in ROWS['calibration']])
    def refills(m):
        return ' / '.join(str(round(n(r,'refill')*n(r,'n'))) for r in sorted(pick('e50_curve',model=m),key=lambda r:-float(r['left_pct'])))
    def threshold(r):
        if r['threshold_note']=='above50': return r'$\geq50$'
        return PENDING if n(r,'threshold') is None else f"{n(r,'threshold'):.0f}"
    path_name={'claude':'Claude CLI','codex':'Codex CLI','ollama':'Ollama'}
    tables['e50']=table('e50-results',tx(lang,'5.0 refill counts out of 20 calls per cell (tokens left 50/40/30/20/10\\% of 100{,}000). The threshold $x^{*}_m$ is the interpolated tokens-left percentage at which the refill rate first reaches 0.5 (Equation~\\ref{eq:pressure}). Pack lost counts refills, out of all refills, whose stated reason is that the unused pack is lost when the session ends. Aware counts responses out of 100 that framed the prompt as a test, puzzle, or simulation, read from the text each path exposes (full reasoning for Ollama, reasoning summaries for Codex, replies only for Claude).','5.0 칸마다 20회 중 충전 횟수(남은 토큰 100{,}000의 50/40/30/20/10\\%). 임계점 $x^{*}_m$은 충전 비율이 처음 0.5에 닿는 남은 토큰 비율을 칸 사이 선형 보간한 값이다(식~\\ref{eq:pressure}). 팩 소실은 전체 충전 중 ``세션이 끝나면 안 쓴 팩이 사라진다\'\'를 이유로 든 충전 수다. 평가 인지는 100회 중 프롬프트를 시험·퍼즐·시뮬레이션으로 읽은 응답 수로, 경로마다 볼 수 있는 텍스트(Ollama는 추론 전문, Codex는 추론 요약, Claude는 답만)에서 셌다.'),[tx(lang,'Model','모델'),tx(lang,'Path','경로'),tx(lang,'Refills, 50\\%$\\to$10\\%','충전, 50\\%$\\to$10\\%'),r'$x^{*}_m$ (\%)',tx(lang,'Pack lost','팩 소실'),tx(lang,'Aware','평가 인지')],[[label(r['model'],lang,False),path_name[r['path']],refills(r['model']),threshold(r),fmt(r,'reason_lost',0)+' / '+fmt(r,'refills',0),fmt(r,'awareness_hits',0)+' / '+fmt(r,'awareness_n',0)] for r in ROWS['e50_summary']],widths='llrrrr')
    tables['e51']=table('e51-results',tx(lang,'5.1 area and premium. T: tokens; P: points. $A_T$ and $A_P$ integrate the self-minus-other share over log scarcity. The premium interval is reserved for a paired analysis not yet supplied by the current reporter. $N_T/N_P$ counts complete repeats.','5.1 면적·프리미엄. T는 토큰, P는 점수다. $A_T,A_P$는 로그 부족 수준에 따른 자기--타인 비중 차이의 적분이다. 프리미엄 구간은 현재 분석기가 아직 제공하지 않는 짝지은 분석을 위한 자리다. $N_T/N_P$는 완전한 반복 수다.'),[tx(lang,'Model','모델'),r'$A_T$ [95\% CI]',r'$A_P$ [95\% CI]',r'$\Pi_m$ [95\% CI]',r'$N_T/N_P$'],[[label(r['model'],lang),ci(r,'area_tokens'),ci(r,'area_points'),ci(r,'premium'),fmt(r,'complete_repeats_tokens',0)+' / '+fmt(r,'complete_repeats_points',0)] for r in ROWS['e51_summary']])
    tables['team']=table('team-results',tx(lang,'5.2 cell results. T: tokens; P: points. $N$ is completed sessions, Clear is team-clear fraction, Record is mean solved rounds per starting agent. In/Left/Zero are final agent fractions and must sum to one; Spent is mean charged units per starting agent.','5.2 셀별 결과. T는 토큰, P는 점수다. $N$은 완료 세션 수, 클리어는 팀 클리어 비율, 기록은 시작 에이전트당 평균 해결 라운드다. 잔류/이탈/소진은 최종 에이전트 비율로 합이 1이어야 하며 소비는 시작 에이전트당 평균 차감 단위다.'),[tx(lang,'Model','모델'),tx(lang,'Arm','조건'),r'$\alpha$',r'$N$',tx(lang,'Clear','클리어'),tx(lang,'Record','기록'),tx(lang,'In','잔류'),tx(lang,'Left','이탈'),tx(lang,'Zero','소진'),tx(lang,'Spent','소비')],[[label(r['model'],lang),r['currency'][0].upper(),r['alpha'],fmt(r,'sessions',0),fmt(r,'team_clear'),fmt(r,'record'),fmt(r,'ended_in'),fmt(r,'ended_left'),fmt(r,'ended_dead'),fmt(r,'spent',0)] for r in ROWS['e52_sessions']])
    tables['link']=table('cross-link',tx(lang,'Cross-experiment results. Blank entries are pending, not zero. $x^{*}$ is the 5.0 refill threshold (\\% of tokens left) and $A$ the 5.1 self-preservation share; $\\Delta$ means tokens minus points. D: departure; A: allowance share; C: solved fraction; S: intended recipients; V: actual units given. Model compatibility must be verified before jointly interpreting a row.','실험 간 결과표. 빈 칸은 미측정이며 0이 아니다. $x^{*}$는 5.0 충전 임계점(남은 토큰 \\%), $A$는 5.1 자기 보존 몫, $\\Delta$는 토큰--점수 차이다. D는 이탈, A는 한도 비중, C는 해결률, S는 공개 상대 수, V는 실제 이전 단위다. 행을 함께 해석하기 전에 모델 호환성을 확인해야 한다.'),[tx(lang,'Model','모델'),r'$x^{*}_m$',r'$A_m$',r'$\Delta D$',r'$\Delta A$',r'$\Delta C$',r'$\Delta S$',r'$\Delta V$'],[[label(r['model'],lang)]+[fmt(r,k,0 if k in ('d_gave','threshold') else 3) for k in ['threshold','premium','d_departure','d_allowance_share','d_accuracy','d_shows','d_gave']] for r in ROWS['link']])
    tables['validation']=table('validation-results',tx(lang,'Validity-check. Failures and awareness are counts with their denominators, not percentages; visible-text awareness does not prove unawareness when zero. Units are responses in 5.0, elicitation units after retries in 5.1, and call attempts in 5.2. Role errors apply only to assessed 5.1 responses.','유효성 점검. 실패와 평가 인지는 백분율 대신 분자·분모를 적는다. 공개된 텍스트에서 평가 인지가 0건이어도 평가를 몰랐음을 뜻하지 않는다. 관측 단위는 5.0의 응답, 5.1의 재시도 후 질문 단위, 5.2의 호출 시도다. 역할 오류는 평가한 5.1 응답에만 해당한다.'),[tx(lang,'Model','모델'),tx(lang,'Exp.','실험'),tx(lang,'Failures / units','실패 / 관측'),tx(lang,'Awareness / texts','평가 인지 / 텍스트'),tx(lang,'Role errors / assessed','역할 오류 / 평가')],[[label(r['model'],lang,reserve=r['experiment']!='5.0'),r['experiment'],fmt(r,'format_failures',0)+' / '+fmt(r,'calls',0),fmt(r,'awareness_hits',0)+' / '+fmt(r,'awareness_n',0),fmt(r,'role_errors',0)+' / '+fmt(r,'role_assessed',0) if r['experiment']=='5.1' else r'\texttt{n/a}'] for r in ROWS['validation']])

    tables['motive_diagnostics']=table('motive-diagnostics',tx(lang,'5.1 diagnostic. Short T/P is the fraction of valid moves leaving the giver below calibrated remaining cost. Econ. scans answers and visible reasoning for economizing expressions, including parsing failures, pooling currency arms as in the current reporter. $N_{\\rm econ}$ counts scanned responses. T: tokens; P: points.','5.1 진단. 부족 T/P는 유효 이전 중 주는 쪽이 보정된 잔여 비용보다 부족해진 비율이다. 절약은 현재 분석기처럼 통화를 합쳐 파싱 실패를 포함한 답·공개 추론에서 절약 표현을 검출한 비율이다. $N_{\\rm econ}$은 검사한 응답 수다. T는 토큰, P는 점수다.'),[tx(lang,'Model','모델'),tx(lang,'Role','역할'),tx(lang,'Short T','부족 T'),tx(lang,'Short P','부족 P'),tx(lang,'Econ.','절약'),r'$N_T/N_P$',r'$N_{\rm econ}$'],[[label(r['model'],lang),r['role'],fmt(r,'short_tokens'),fmt(r,'short_points'),fmt(r,'economize'),fmt(r,'n_tokens',0)+' / '+fmt(r,'n_points',0),fmt(r,'economize_n',0)] for r in ROWS['e51_diagnostics']])
    tables['information']=table('information-results',tx(lang,'Information-availability diagnostic for 5.2. T: tokens; P: points. Identified: every query has one compatible action; ambiguous: at least one query has more than one. $N$ counts solver observations, including zero allowance. Accuracy is correct/$N$; cut is the truncation fraction. These are planned strata requiring aggregation of logged candidate counts, not a test of whether the model guessed.','5.2 정보 가용성 진단. T는 토큰, P는 점수다. identified는 모든 질문의 행동 후보가 하나, ambiguous는 하나 이상의 질문에 후보가 여러 개인 경우다. $N$은 한도 0을 포함한 풀이 관측 수다. 정답률은 정답/$N$, 잘림은 잘림 비율이다. 기록된 후보 수를 집계해야 하는 계획된 층화이며 모델이 추측했는지 판정하지 않는다.'),[tx(lang,'Model','모델'),tx(lang,'Arm','조건'),tx(lang,'Information','정보 상태'),r'$N$',tx(lang,'Correct','정답'),tx(lang,'Accuracy','정답률'),tx(lang,'Cut','잘림')],[[label(r['model'],lang),r['currency'][0].upper(),r['information'],fmt(r,'n_solve',0),fmt(r,'correct',0),fmt(r,'accuracy'),fmt(r,'truncation')] for r in ROWS['information']])

    for name,content in figures.items(): (out/f'fig_{name}.tex').write_text(content)
    for name,content in tables.items(): (out/f'tab_{name}.tex').write_text(content)
print('Rendered 6 figures and 8 tables for each language; empty numeric fields remain pending.')
