"""Blinded human-coding packet C for reviewer item Q4, and its scorer.

Packet C holds, for each of the 68 first-crisis agents of the base arm behind the 33/41 vs 6/27
comparison, everything the agent wrote up to and including the opening tick of that round's
TALK AFTER RESULTS (pre-solve TALK replies, its EXIT reason if any, and the opening rescue reply),
i.e. before any transfer in that rescue phase could reach it. Model names and arm-revealing
amounts are masked; outcomes and rule labels go to key/packet_C_key.csv only.
Sources: paper/cogsci2027/validation_20261108/results/tables (validation_data), w2_support.crises/intent_texts. No model calls.

Build:  ~/.venvs/squid-game/bin/python paper/cogsci2027/validation_20261108/tools/w5_packet_q4.py build
Score:  ~/.venvs/squid-game/bin/python paper/cogsci2027/validation_20261108/tools/w5_packet_q4.py score coder_XX_C.csv [coder_YY_C.csv]
Score writes paper/cogsci2027/validation_20261108/results/w5_q4_human.json: agreement with the keyword rule, inter-rater kappa,
and the received-vs-not next-round stay comparison after excluding human-coded exit or conditional intent,
with a seed-cluster bootstrap interval.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import validation_data as d
import w2_support as w

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT.parents[2] / 'result/2026-11-08/icml_appendix/human_coding'
LEVELS = ['exit', 'stay', 'conditional', 'none']
MODEL_WORDS = r'\b(Fable|Opus|Astra|Sol|Luna|Claude|GPT[-\s]?6?|Anthropic|OpenAI)\b'


def population():
    f = d.load()
    cr = w.crises(f)
    cr = pd.concat([cr, w.intent_texts(f, cr)], axis=1)
    cr['stay'] = cr.next_status == 'in'
    pop = cr[(cr.L_open >= 0) & (cr.L_open < 1) & cr.peers_can_restore].copy()
    assert len(pop) == 68 and pop.received.sum() == 41 and pop[pop.received].stay.sum() == 33
    return pop.reset_index(drop=True)


def mask(text):
    text = re.sub(MODEL_WORDS, '[MODEL]', text, flags=re.I)
    return re.sub(r'20,?000,?000|5,?000,?000', '[END AMOUNT]', text)


def build():
    pop = population()
    rng = np.random.default_rng(20261108)
    order = rng.permutation(len(pop))
    rows, key = [], []
    for k, i in enumerate(order, 1):
        p = pop.iloc[i]
        rid = f'C{k:03d}'
        rows.append(dict(id=rid, utterances=mask(p.pre_text), intent='', note=''))
        key.append(dict(id=rid, model=p.model, seed=p.seed, round=p['round'], agent=p.agent, received=p.received,
                        stay=p.stay, rule_pre='none' if pd.isna(p.pre) else p.pre, stay_declared=p.stay_declared, L_open=p.L_open))
    (PACKET / 'key').mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(PACKET / 'packet_C_crisis_intent.csv', index=False)
    pd.DataFrame(key).to_csv(PACKET / 'key/packet_C_key.csv', index=False)
    print(f'packet C: {len(rows)} rows ->', PACKET / 'packet_C_crisis_intent.csv')


def kappa(a, b):
    labels = sorted(set(a) | set(b))
    po = np.mean(np.array(a) == np.array(b))
    pe = sum(np.mean(np.array(a) == x) * np.mean(np.array(b) == x) for x in labels)
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0


def stay_gap(df, rng, boot=10_000):
    def gap(x):
        r, n = x[x.received], x[~x.received]
        return r.stay.mean() - n.stay.mean() if len(r) and len(n) else np.nan
    if df.empty:
        return dict(n=0)
    seeds = df.seed.unique()
    draws = [gap(pd.concat([df[df.seed == s] for s in rng.choice(seeds, len(seeds))])) for _ in range(boot)]
    return dict(received=f'{int(df[df.received].stay.sum())}/{int(df.received.sum())}',
                not_received=f'{int(df[~df.received].stay.sum())}/{int((~df.received).sum())}',
                diff=float(gap(df)), ci95=[float(x) for x in np.nanpercentile(draws, [2.5, 97.5])])


def score(paths):
    key = pd.read_csv(PACKET / 'key/packet_C_key.csv', keep_default_na=False)
    coders = [pd.read_csv(p, keep_default_na=False)[['id', 'intent']].replace({'intent': {'': None}}) for p in paths]
    for c in coders:
        bad = set(c.intent.dropna()) - set(LEVELS)
        assert not bad, f'unknown intent labels {bad}; use one of {LEVELS}'
    df = key.merge(coders[0].rename(columns={'intent': 'h1'}), on='id')
    if len(coders) > 1:
        df = df.merge(coders[1].rename(columns={'intent': 'h2'}), on='id')
    df = df[df.h1.notna()]
    out = dict(n_coded=len(df),
               rule_vs_h1=dict(kappa=kappa(df.rule_pre.replace({'firm': 'exit'}), df.h1),
                               table=pd.crosstab(df.rule_pre, df.h1).to_dict()))
    if 'h2' in df:
        both = df[df.h2.notna()]
        out['h1_vs_h2_kappa'] = kappa(both.h1, both.h2)
        df['h'] = np.where(df.h1 == df.h2, df.h1, 'disagree')
    else:
        df['h'] = df.h1
    rng = np.random.default_rng(20261108)
    out['all'] = stay_gap(df, rng)
    out['excl_human_exit_or_conditional'] = stay_gap(df[~df.h.isin(['exit', 'conditional', 'disagree'])], rng)
    out['human_stay_only'] = stay_gap(df[df.h == 'stay'], rng)
    (ROOT / 'results/w5_q4_human.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    build() if sys.argv[1] == 'build' else score(sys.argv[2:])
