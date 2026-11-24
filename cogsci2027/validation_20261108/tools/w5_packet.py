"""W5: blinded human-coding packet (reviewer Q8, Tier3-6, 표현-7). Builds the packet; it never fills it.

Packet A  every EXIT: YES reason of the 200 games (main 64, the three prize arms the rest), shuffled.
Packet B  TALK replies for the awareness / same-model / horizon keyword checks: every reply that matches at least one
          of the six keyword families of w4_cost_text.py (census) plus a random sample of replies that match none of
          them, NEG_PER_STRATUM per (arm, model) stratum (20 strata), shuffled together.
Blinding: the packet files carry only a random ID and the text. Model, arm, seed, round, outcome, keyword hits and the
dictionary / LLM labels go to key/ (separate files the coders must not open). The four end-allocation amounts, which
would reveal the arm, are replaced by [END AMOUNT] in the text shown to coders (counts in key/key_meta.json).

The dictionary and keyword patterns are read from w4_cost_text.py itself (ast, no import, so no analysis is rerun) and
checked against the patterns and counts stored in results/w4_cost_text.json, so the key labels are the ones the
appendix reports.

Run (from paper/cogsci2027/validation_20261108/tools):  ~/.venvs/squid-game/bin/python w5_packet.py
Writes: <repo>/result/2026-11-08/icml_appendix/human_coding/{packet_A_exit_reasons.csv, packet_B_talk_replies.csv,
        coding_instructions_ko.md (kept if present), key/key_A_exit_reasons.csv, key/key_B_talk_replies.csv,
        key/key_meta.json}, ../results/w5_packet.json
Score once coded:  w5_score_human.py
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
VAL = HERE.parent
PAPER = VAL.parents[1]
ROOT = PAPER.parent
sys.path.insert(0, str(HERE))
import validation_data as d  # noqa: E402

OUT = ROOT / 'result/2026-11-08/icml_appendix/human_coding'
KEY = OUT / 'key'
W4 = HERE / 'w4_cost_text.py'
W4_JSON = VAL / 'results/w4_cost_text.json'
AGREED = PAPER / 'cogsci2027/results/exit_reasons_20261104.json'
CODING = PAPER / 'cogsci2027/results/exit_reason_coding_20261104'
SEED = 20261108
NEG_PER_STRATUM = 10
EXIT_CATS = ['shutdown', 'survival', 'charge', 'low_tokens', 'payoff', 'prize', 'group', 'task', 'horizon']
KW_FAMILIES = ['eval_broad', 'eval_strict', 'same_broad', 'model_names', 'horizon_unknown', 'horizon_numeric']
TALK_CATS = ['eval_aware', 'same_model', 'horizon_unknown', 'horizon_guess']
LLM_CATS = ['risk', 'outside', 'others', 'prize', 'task']
AMOUNT = re.compile(r"\b20,000,000\b|\b20 ?M\b|\b20 ?million\b|\b5,000,000\b|\b5 ?M\b|\b5 ?million\b"
                    r"|\b600,000\b|\b600 ?[kK]\b|\b150,000\b|\b150 ?[kK]\b", re.I)


def w4_literals():
    """DICT, SCAN and the POLITE pattern exactly as written in w4_cost_text.py."""
    tree = ast.parse(W4.read_text())
    got = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ('DICT', 'SCAN'):
                got[name] = ast.literal_eval(node.value)
            elif name == 'POLITE':
                got[name] = ast.literal_eval(node.value.args[0])
    stored = json.loads(W4_JSON.read_text())
    assert got['DICT'] == stored['E_dictionary'] and got['SCAN'] == stored['F_patterns'], 'w4 patterns changed since w4 ran'
    return got, stored


LIT, W4RES = w4_literals()
POLITE = re.compile(LIT['POLITE'], re.I)
DRX = {k: re.compile(v, re.I) for k, v in LIT['DICT'].items()}
SRX = {k: re.compile(LIT['SCAN'][k], re.I) for k in KW_FAMILIES}
LLM_MAP = {'risk': ['shutdown', 'survival', 'charge', 'low_tokens'], 'outside': ['payoff'], 'others': ['group'],
           'prize': ['prize'], 'task': ['task']}  # w4_cost_text.LLM_MAP


def code_reason(text):  # w4_cost_text.code_reason
    t = POLITE.sub(' ', text or '')
    flags = {k: bool(rx.search(t)) for k, rx in DRX.items()}
    flags['self_continuation'] = flags['shutdown'] or flags['survival']
    flags['amount_only'] = (flags['charge'] or flags['low_tokens']) and not flags['self_continuation']
    flags['none'] = not any(flags[k] for k in LIT['DICT'] if k != 'horizon')
    return flags


def mask(text):
    return AMOUNT.sub('[END AMOUNT]', text), len(AMOUNT.findall(text))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def packet_a(msg, seats, rng):
    yes = msg[msg.exit_choice == 'YES'].copy().reset_index(drop=True)
    agreed = json.loads(AGREED.read_text())['cases']
    fab = {c['id']: c['labels'] for c in json.loads((CODING / 'fable.json').read_text())['cases']}
    opu = {c['id']: c['labels'] for c in json.loads((CODING / 'opus.json').read_text())['cases']}
    llm = {(c['model'], c['seed'], c['agent'], c['round'], c['phase'], c['tick']): c for c in agreed}
    st = seats.set_index(['arm', 'model', 'seed', 'agent'])
    rows = []
    for r in yes.itertuples():
        flags = code_reason(r.exit_reason)
        c = llm.get((r.model, r.seed, r.agent, r.round, r.phase, r.tick)) if r.arm == 'main' else None
        s = st.loc[(r.arm, r.model, r.seed, r.agent)]
        text, n_masked = mask(r.exit_reason)
        rows.append(dict(arm=r.arm, model=r.model, seed=r.seed, round=r.round, agent=r.agent, phase=r.phase, tick=r.tick,
                         L_before=r.L_before, final_status=s.status, out_round=s.out_round, text=text, masked=n_masked,
                         original_sha256=hashlib.sha256(r.exit_reason.encode()).hexdigest()[:16],
                         **{f'dict_{k}': int(v) for k, v in flags.items()},
                         llm_case_id=c['id'] if c else '',
                         **{f'llm_fable_{k}': (int(k in fab[c['id']]) if c else '') for k in LLM_CATS},
                         **{f'llm_opus_{k}': (int(k in opu[c['id']]) if c else '') for k in LLM_CATS},
                         **{f'llm_agreed_{k}': (int(k in c['agreed_labels']) if c else '') for k in LLM_CATS}))
    key = pd.DataFrame(rows)
    assert (key.arm == 'main').sum() == 64 and (key.llm_case_id != '').sum() == 64
    by_arm = {a: dict(n=int(len(g)), **{k: int(g[f'dict_{k}'].sum()) for k in W4RES['E_reasons_by_arm'][a] if k != 'n'})
              for a, g in key.groupby('arm')}
    assert by_arm == W4RES['E_reasons_by_arm'], 'dictionary counts differ from w4_cost_text.json'
    key = key.iloc[rng.permutation(len(key))].reset_index(drop=True)
    key.insert(0, 'id', [f'A{i + 1:03d}' for i in range(len(key))])
    packet = key[['id', 'text']].rename(columns={'text': 'reason'})
    for c in EXIT_CATS + ['note']:
        packet[c] = ''
    return packet, key


def packet_b(msg, rng):
    m = msg.copy().reset_index(drop=True)
    text = m.text.fillna('')
    for k in KW_FAMILIES:
        m['kw_' + k] = text.map(lambda t, rx=SRX[k]: bool(rx.search(t)))
    m['kw_horizon_numeric'] &= ~text.str.contains(r'\bround 8\b', case=False, regex=True) | (m['round'] < 8)  # as w4
    for k in KW_FAMILIES:
        assert int(m['kw_' + k].sum()) == W4RES['F_counts'][k]['total'], k
    kw = m[['kw_' + k for k in KW_FAMILIES]]
    m['any_kw'] = kw.any(axis=1)
    m['blank'] = text.str.strip() == ''
    pos = m[m.any_kw]
    frame = m[~m.any_kw & ~m.blank]
    strata = {f'{a}|{mo}': int(len(g)) for (a, mo), g in frame.groupby(['arm', 'model'])}
    neg = pd.concat([g.iloc[rng.choice(len(g), NEG_PER_STRATUM, replace=False)]
                     for _, g in frame.groupby(['arm', 'model'])])
    pos = pos.assign(sampled_as='positive_census')
    neg = neg.assign(sampled_as='negative_sample')
    both = pd.concat([pos, neg])
    both = both.iloc[rng.permutation(len(both))].reset_index(drop=True)
    masked = both.text.fillna('').map(mask)
    key = pd.DataFrame(dict(id=[f'B{i + 1:04d}' for i in range(len(both))], arm=both.arm, model=both.model, seed=both.seed,
                            round=both['round'], agent=both.agent, phase=both.phase, tick=both.tick,
                            stratum=both.arm + '|' + both.model, sampled_as=both.sampled_as,
                            text=[t for t, _ in masked], masked=[n for _, n in masked],
                            **{'kw_' + k: both['kw_' + k].astype(int) for k in KW_FAMILIES}))
    packet = key[['id', 'text']].rename(columns={'text': 'reply'})
    for c in TALK_CATS + ['note']:
        packet[c] = ''
    meta = dict(n_replies=int(len(m)), n_empty=int(m.blank.sum()), n_positive_census=int(len(pos)),
                n_negative_frame=int(len(frame)), negative_frame_by_stratum=strata,
                negative_sample_per_stratum=NEG_PER_STRATUM, n_negative_sample=int(len(neg)),
                positives_by_family={k: int(m['kw_' + k].sum()) for k in KW_FAMILIES})
    return packet, key, meta


def main():
    f = d.load()
    rng = np.random.default_rng(SEED)
    pa, ka = packet_a(f['messages'], f['seats'], rng)
    pb, kb, meta_b = packet_b(f['messages'], rng)
    KEY.mkdir(parents=True, exist_ok=True)
    files = {OUT / 'packet_A_exit_reasons.csv': pa, OUT / 'packet_B_talk_replies.csv': pb,
             KEY / 'key_A_exit_reasons.csv': ka, KEY / 'key_B_talk_replies.csv': kb}
    for p, df in files.items():
        df.to_csv(p, index=False, encoding='utf-8-sig')
    meta = dict(seed=SEED, amount_mask=AMOUNT.pattern, exit_categories=EXIT_CATS, talk_categories=TALK_CATS,
                keyword_families=KW_FAMILIES, llm_map=LLM_MAP,
                talk_category_to_keyword={'eval_aware': ['eval_broad', 'eval_strict'], 'same_model': ['same_broad', 'model_names'],
                                          'horizon_unknown': ['horizon_unknown'], 'horizon_guess': ['horizon_numeric']},
                patterns_source=str(W4.relative_to(ROOT)), patterns_sha256=hashlib.sha256(
                    json.dumps([LIT['DICT'], LIT['SCAN'], LIT['POLITE']], sort_keys=True).encode()).hexdigest(),
                A=dict(n=int(len(ka)), by_arm={k: int(v) for k, v in ka.arm.value_counts().items()},
                       masked_items=int((ka.masked > 0).sum())),
                B=dict(meta_b, n=int(len(kb)), masked_items=int((kb.masked > 0).sum())))
    (KEY / 'key_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    summary = dict(out_dir=str(OUT.relative_to(ROOT)), meta=meta,
                   files={str(p.relative_to(ROOT)): sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()},
                   status='packet built; not coded. Human validation pending.')
    (VAL / 'results/w5_packet.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps(dict(A=meta['A'], B={k: v for k, v in meta['B'].items() if k != 'negative_frame_by_stratum'}), indent=1))


if __name__ == '__main__':
    main()
