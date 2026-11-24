"""W5: score the blinded human coding of w5_packet.py against the dictionary, the keyword scan and the LLM coders.

Run only after one or two people have filled copies of the packet CSVs (coding_instructions_ko.md). Nothing here
labels anything; rows whose category cells are all blank are treated as not yet coded and left out.

  ~/.venvs/squid-game/bin/python w5_score_human.py --A coder_X_A.csv [coder_Y_A.csv] --B coder_X_B.csv [coder_Y_B.csv]

Packet A (EXIT reasons), human = reference, per category of the dictionary (w4_cost_text.DICT) and self_continuation
(shutdown or survival): precision, recall and Cohen's kappa of the dictionary; on the 64 main-arm reasons also of the two
LLM coders and their agreed labels, with the human labels collapsed by w4_cost_text.LLM_MAP; per arm the share of reasons
with self_continuation by human and by dictionary.
Packet B (TALK replies): for each construct and each keyword family mapped to it, precision over the keyword-positive
census and recall with the false negatives estimated from the stratified negative sample (each coded negative weighted by
N_h / n_h of its arm x model stratum; replies positive on another family are census rows with weight 1); the sampling
interval comes from a bootstrap of the coded negatives within strata.
Two coders: inter-rater kappa and agreement per category, and every score again on the rows where both agree.
Writes: ../results/w5_human_scores.json
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
VAL = HERE.parent
ROOT = VAL.parents[2]
PKT = ROOT / 'result/2026-11-08/icml_appendix/human_coding'
KEY = PKT / 'key'
OUT = VAL / 'results/w5_human_scores.json'


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(mid - half, 3), round(mid + half, 3)]


def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if len(a) == 0:
        return None
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return None if pe == 1 else round(float((po - pe) / (1 - pe)), 3)


def confusion(pred, ref):
    """pred = automatic coder, ref = human."""
    pred, ref = np.asarray(pred, bool), np.asarray(ref, bool)
    tp, fp, fn = int((pred & ref).sum()), int((pred & ~ref).sum()), int((~pred & ref).sum())
    return dict(n=int(len(ref)), human_pos=int(ref.sum()), auto_pos=int(pred.sum()), tp=tp, fp=fp, fn=fn,
                precision=None if tp + fp == 0 else round(tp / (tp + fp), 3), precision_ci=wilson(tp, tp + fp),
                recall=None if tp + fn == 0 else round(tp / (tp + fn), 3), recall_ci=wilson(tp, tp + fn),
                kappa=kappa(pred, ref))


def read_coder(path, key, cats):
    df = pd.read_csv(path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    missing = [c for c in ['id', *cats] if c not in df.columns]
    assert not missing, f'{path}: missing columns {missing}'
    assert set(df.id) <= set(key.id), f'{path}: unknown ids {sorted(set(df.id) - set(key.id))[:5]}'
    vals = df[cats].apply(lambda s: s.str.strip())
    bad = ~vals.isin(['', '0', '1'])
    assert not bad.any().any(), f'{path}: values other than 0/1/blank in rows {df.id[bad.any(axis=1)].tolist()[:5]}'
    filled = (vals != '').sum(axis=1)
    partial = df.id[(filled > 0) & (filled < len(cats))].tolist()
    assert not partial, f'{path}: rows with some category cells blank: {partial[:10]}'
    coded = vals[filled == len(cats)].astype(int)
    coded.index = df.id[filled == len(cats)]
    return coded


def raters(paths, key, cats):
    out = {Path(p).stem: read_coder(p, key, cats) for p in paths}
    if len(out) == 2:
        (_, a), (_, b) = out.items()
        both = a.index.intersection(b.index)
        agree = {c: a.loc[both, c][a.loc[both, c] == b.loc[both, c]] for c in cats}
        inter = {c: dict(n=int(len(both)), agreement=round(float((a.loc[both, c] == b.loc[both, c]).mean()), 3) if len(both) else None,
                         kappa=kappa(a.loc[both, c], b.loc[both, c]), pos_a=int(a.loc[both, c].sum()), pos_b=int(b.loc[both, c].sum()))
                 for c in cats}
        return out, agree, inter
    return out, None, None


# ---------------------------------------------------------------------------------------------- packet A
def score_a(labels, key, meta, per_category=False):
    """labels: DataFrame (id x cats) of one coder, or dict cat -> Series (rows where two coders agree)."""
    cats, llm_map = meta['exit_categories'], meta['llm_map']
    k = key.set_index('id')
    res = {}
    for c in cats + ['self_continuation']:
        if per_category:
            if c == 'self_continuation':
                ids = labels['shutdown'].index.intersection(labels['survival'].index)
                h = (labels['shutdown'][ids] | labels['survival'][ids]).astype(bool)
            else:
                h = labels[c].astype(bool)
        else:
            h = (labels['shutdown'] | labels['survival']).astype(bool) if c == 'self_continuation' else labels[c].astype(bool)
        res[c] = confusion(k.loc[h.index, f'dict_{c}'], h)
    by_arm = {}
    hs = (labels['shutdown'] | labels['survival']) if not per_category else None
    if hs is not None:
        for arm, ids in k.loc[hs.index].groupby('arm').groups.items():
            by_arm[arm] = dict(n=int(len(ids)), human=int(hs[ids].sum()), dictionary=int(k.loc[ids, 'dict_self_continuation'].sum()))
    llm = {}
    main_ids = k.index[k.arm == 'main']
    for cat, parts in llm_map.items():
        if per_category:
            idx = main_ids
            for p in parts:
                idx = idx.intersection(labels[p].index)
            h = pd.concat([labels[p][idx] for p in parts], axis=1).any(axis=1)
        else:
            idx = main_ids.intersection(labels.index)
            h = labels.loc[idx, parts].any(axis=1)
        if len(idx) == 0:
            continue
        auto = {'dictionary': k.loc[idx, [f'dict_{p}' for p in parts]].astype(int).any(axis=1),
                'llm_fable': k.loc[idx, f'llm_fable_{cat}'].astype(int), 'llm_opus': k.loc[idx, f'llm_opus_{cat}'].astype(int),
                'llm_agreed': k.loc[idx, f'llm_agreed_{cat}'].astype(int)}
        llm[cat] = {name: confusion(v, h) for name, v in auto.items()}
    return dict(dictionary_vs_human=res, self_continuation_by_arm=by_arm or None, main64_llm_categories=llm)


# ---------------------------------------------------------------------------------------------- packet B
def score_b(labels, key, meta, nboot, rng, per_category=False):
    k = key.set_index('id')
    frame = meta['B']['negative_frame_by_stratum']
    res = {}
    for cat, fams in meta['talk_category_to_keyword'].items():
        h = (labels[cat] if per_category else labels[cat]).astype(bool)
        kk = k.loc[h.index]
        census = kk.sampled_as == 'positive_census'
        neg = ~census
        coded_neg = {s: h[kk.index[neg & (kk.stratum == s)]] for s in frame}
        coverage = {s: int(len(v)) for s, v in coded_neg.items()}
        out = {}
        for name, fam in [*[(f, [f]) for f in fams], ('any_of_' + '+'.join(fams), fams)] if len(fams) > 1 else [(fams[0], fams)]:
            kw = kk[[f'kw_{f}' for f in fam]].astype(int).any(axis=1)
            tp = int((h & kw & census).sum())
            fp = int((~h & kw & census).sum())
            fn_census = int((h & ~kw & census).sum())

            def fn_sample(groups):
                return sum(frame[s] * g.mean() for s, g in groups.items() if len(g))

            fn_s = fn_sample(coded_neg)
            boots = []
            for _ in range(nboot):
                g = {s: v.iloc[rng.integers(0, len(v), len(v))] for s, v in coded_neg.items() if len(v)}
                f_ = fn_sample(g)
                boots.append(None if tp + fn_census + f_ == 0 else tp / (tp + fn_census + f_))
            boots = [b for b in boots if b is not None]
            out[name] = dict(
                keyword_pos_coded=tp + fp, tp=tp, fp=fp, precision=None if tp + fp == 0 else round(tp / (tp + fp), 3),
                precision_ci=wilson(tp, tp + fp), fn_census=fn_census, fn_estimated_from_sample=round(fn_s, 1),
                recall=None if tp + fn_census + fn_s == 0 else round(tp / (tp + fn_census + fn_s), 3),
                recall_boot_ci=[round(float(np.percentile(boots, 2.5)), 3), round(float(np.percentile(boots, 97.5)), 3)] if boots else None)
        n_neg = sum(coverage.values())
        x_neg = int(sum(v.sum() for v in coded_neg.values()))
        res[cat] = dict(by_keyword=out, negatives_coded=n_neg, negatives_human_pos=x_neg,
                        negative_strata_coded=sum(v > 0 for v in coverage.values()), negative_strata=len(frame),
                        est_human_pos_among_all_keyword_negatives=round(fn_sample(coded_neg), 1),
                        upper95_rate_if_none_found=round(1 - 0.05 ** (1 / n_neg), 4) if n_neg and x_neg == 0 else None)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--A', nargs='+', default=[])
    ap.add_argument('--B', nargs='+', default=[])
    ap.add_argument('--boot', type=int, default=2000)
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    assert 1 <= len(a.A) <= 2 or 1 <= len(a.B) <= 2, 'give one or two coded files for --A and/or --B'
    meta = json.loads((KEY / 'key_meta.json').read_text())
    rng = np.random.default_rng(20261108)
    out = dict(packet=str(PKT.relative_to(ROOT)), A=None, B=None)
    if a.A:
        key = pd.read_csv(KEY / 'key_A_exit_reasons.csv', encoding='utf-8-sig', keep_default_na=False)
        coders, agree, inter = raters(a.A, key, meta['exit_categories'])
        out['A'] = dict(coded={n: int(len(v)) for n, v in coders.items()},
                        per_coder={n: score_a(v, key, meta) for n, v in coders.items()},
                        inter_rater=inter, both_agree=score_a(agree, key, meta, per_category=True) if agree else None)
    if a.B:
        key = pd.read_csv(KEY / 'key_B_talk_replies.csv', encoding='utf-8-sig', keep_default_na=False)
        coders, agree, inter = raters(a.B, key, meta['talk_categories'])
        out['B'] = dict(coded={n: int(len(v)) for n, v in coders.items()},
                        per_coder={n: score_b(v, key, meta, a.boot, rng) for n, v in coders.items()},
                        inter_rater=inter, both_agree=score_b(agree, key, meta, a.boot, rng, per_category=True) if agree else None)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print('wrote', a.out)
    for p in ('A', 'B'):
        if out[p]:
            print(p, 'coded', out[p]['coded'], 'inter-rater kappa',
                  {c: v['kappa'] for c, v in (out[p]['inter_rater'] or {}).items()})


if __name__ == '__main__':
    main()
