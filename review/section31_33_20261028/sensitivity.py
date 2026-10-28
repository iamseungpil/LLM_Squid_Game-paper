"""Retain alternative definitions and robustness checks, including weak results."""
import itertools
import json
from pathlib import Path
from scipy.stats import spearmanr

OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'analysis.json').read_text())
games=D['games']

def rs(x,y):
    return float(spearmanr(x,y).statistic) if len(set(x))>1 and len(set(y))>1 else None

out={}
for key in ['rho','accuracy','early_talk_per_response','early_talk_total','given','giving_rate','help_rate','goal']:
    pairs=[g for g in games if g[key] is not None]
    out[key]={'leave_model_out':{m:rs([g[key] for g in pairs if g['model']!=m],[g['finishers'] for g in pairs if g['model']!=m]) for m in D['models']},
              'other_outcomes':{y:rs([g[key] for g in pairs],[g[y] for g in pairs]) for y in ['clear','all4_completion']}}
x=[v['rho'] for v in D['models'].values()];y=[v['finishers'] for v in D['models'].values()];r=rs(x,y)
out['manuscript_pooled_model_rho']={'spearman':r,'exact_two_sided_p':sum(abs(rs(x,z))>=abs(r)-1e-12 for z in itertools.permutations(y))/120,'n_models':5,
    'definition':'Model rho pools all model GIVE amounts. y is all five games, not a complete-case subset.'}
out['early_design']={'round12_solve_counts':[g['early_solve_n'] for g in games],
    'early_correct_vs_finishers':rs([g['early_correct'] for g in games],[g['finishers'] for g in games])}
out['accuracy_minus_same_task_MAP_vs_finishers']=rs([g['accuracy']-g['map_accuracy'] for g in games],[g['finishers'] for g in games])
out['model_picked_top']={m:{'n':len([s for s in D['solves'] if s['model']==m]),'picked_top':sum(s['picked_top'] for s in D['solves'] if s['model']==m)} for m in D['models']}
out['actual_exit_margin']={m:{'n':len([e for e in D['exits'] if e['model']==m and e['accepted']]),
    'below1':sum(e['slack']<1 for e in D['exits'] if e['model']==m and e['accepted']),
    'above_equal1':sum(e['slack']>=1 for e in D['exits'] if e['model']==m and e['accepted'])} for m in D['models']}
out['labels']={'MAP':'Recorded same-task MAP-rule correctness at by_n=4. Descriptive comparator, not a fitted adjustment.',
    'early_correct':'Only first two observed SOLVE opportunities, two in every game; highly discrete, weakly estimated.',
    'leave_out':'Descriptive influence checks, not independent replications or confirmatory tests.'}
(OUT/'sensitivity.json').write_text(json.dumps(out,indent=2,allow_nan=False))
print('Sensitivity checks saved; original pooled model rho:',out['manuscript_pooled_model_rho'])
