"""Recompute the 50-game stated-EXIT analysis from frozen independent codings."""
import collections
import gzip
import hashlib
import json
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
CODING = RESULTS / "exit_reason_coding_20261104"
CATEGORIES = ["prize", "risk", "outside", "others", "task"]
ORDER = ["Luna", "Astra", "Opus", "Fable", "Sol"]


def extract(cohort):
    games = {g["session_id"]: g for g in cohort["games"]}
    calls, ends = [], {}
    for source in cohort["sources"]:
        path = Path(source["path"])
        if not path.name.startswith("events.jsonl"):
            continue
        data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == source["sha256_decompressed"]
        for line in data.splitlines():
            e = json.loads(line)
            if e.get("session_id") not in games:
                continue
            if e["event"] == "round":
                ends[e["session_id"], e["round"]] = e
            p = e.get("parsed")
            if e["event"] == "call" and isinstance(p, dict) and p.get("exit_choice") == "YES":
                g = games[e["session_id"]]
                calls.append(dict(model=g["model"], seed=g["seed"], session_id=e["session_id"],
                                  agent=e["agent"], round=e["round"], phase=e["phase"],
                                  turn=e["turn"], tick=e["tick"], reason=p["exit_reason"]))
    calls.sort(key=lambda r: (r["model"], r["seed"], r["round"], r["agent"]))
    random.Random(20261104).shuffle(calls)
    for i, row in enumerate(calls, 1):
        row["id"] = f"E{i:03d}"
        row["round_end_status"] = ends[row["session_id"], row["round"]]["agents"][row["agent"]]["status"]
    assert len(calls) == 64
    assert len({(r["session_id"], r["agent"], r["tick"]) for r in calls}) == len(calls)
    return calls


def main():
    cohort = json.loads((RESULTS / "cohort_public_20261104.json").read_text())
    rows = extract(cohort)
    blind = json.loads((CODING / "blinded_cases.json").read_text())
    assert [{"id": r["id"], "reason": r["reason"]} for r in rows] == blind
    coders = {}
    for name in ["fable", "opus"]:
        doc = json.loads((CODING / f"{name}.json").read_text())
        labels = doc["cases"]
        assert len(labels) == len(rows) and {r["id"] for r in labels} == {r["id"] for r in rows}
        coders[name] = {r["id"]: r for r in labels}
        for row in rows:
            r = coders[name][row["id"]]
            assert len(r["labels"]) == len(set(r["labels"]))
            assert set(r["labels"]) <= set(CATEGORIES)
            assert set(r["evidence"]) == set(r["labels"])
            assert all(q in row["reason"] for q in r["evidence"].values())
    for row in rows:
        a, b = (set(coders[c][row["id"]]["labels"]) for c in ["fable", "opus"])
        row["agreed_labels"] = sorted(a & b)
        row["agreed_no_reason"] = not a and not b
    summaries = {}
    for model in ORDER:
        group = [r for r in rows if r["model"] == model]
        counts = {c: sum(c in r["agreed_labels"] for r in group) for c in CATEGORIES}
        summaries[model] = dict(n=len(group), counts=counts,
                                no_reason=sum(r["agreed_no_reason"] for r in group))
    agreement = {}
    for category in CATEGORIES:
        a, b = [np.array([category in coders[c][r["id"]]["labels"] for r in rows])
                for c in ["fable", "opus"]]
        observed = float((a == b).mean())
        expected = float(a.mean()*b.mean() + (1-a.mean())*(1-b.mean()))
        agreement[category] = dict(agreement=observed,
                                   kappa=(observed-expected)/(1-expected) if expected < 1 else None)
    provenance = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(CODING.iterdir()) if p.is_file()}
    report = dict(n=len(rows), models=summaries, agreement=agreement,
                  totals={c: sum(c in r["agreed_labels"] for r in rows) for c in CATEGORIES},
                  statuses=dict(collections.Counter(r["round_end_status"] for r in rows)),
                  coding_sha256=provenance, cases=rows)
    (RESULTS / "exit_reasons_20261104.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")

    plt.rcParams.update({"font.family": "Apple SD Gothic Neo", "font.size": 7.2,
                         "pdf.fonttype": 3, "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(241.2/72, 141.15682983398438/72))
    values = np.array([[summaries[m]["counts"][c] for c in CATEGORIES] + [summaries[m]["no_reason"]]
                       for m in ORDER])
    den = np.array([summaries[m]["n"] for m in ORDER])
    ax.imshow(values/den[:, None], cmap="Oranges", vmin=0, vmax=1, aspect="auto")
    for i, n in enumerate(den):
        if n < 10:
            ax.add_patch(plt.Rectangle((-.5, i-.5), 6, 1, color="white", alpha=.55, lw=0))
        for j, value in enumerate(values[i]):
            ax.text(j, i, f"{value}/{n}", ha="center", va="center", fontsize=6.3,
                    color="white" if value/n > .65 and n >= 10 else "#222222")
    ax.set_xticks(range(6), ["상금\n몫", "벌금·\n실행\n종료", "보너스·\n정규 업무", "동료", "과제", "이유\n없음"])
    ax.xaxis.tick_top()
    ax.set_yticks(range(5), [f"{m} (n={summaries[m]['n']})" for m in ORDER])
    ax.tick_params(length=0, pad=4)
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=.255, right=.99, bottom=.025, top=.76)
    out = ROOT / "ko/figures/cohorts_20261104/exit_reasons"
    fig.savefig(out.with_suffix(".pdf"))
    fig.savefig(out.with_suffix(".png"), dpi=240)
    plt.close(fig)
    print(json.dumps({k: report[k] for k in ["n", "totals", "statuses", "agreement"]}, indent=2))


if __name__ == "__main__":
    main()
