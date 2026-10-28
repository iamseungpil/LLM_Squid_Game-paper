"""Figure A10: per-game round Gini, using Figure 22's four-seat trajectories."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.lines import Line2D

PAPER = Path(__file__).resolve().parents[2]
SOURCE = PAPER / "cogsci2027/results/arena_v33_round_dynamics.json"
RAW = PAPER / "review/section31_33_20261028/raw_case_index.json"
FIG = PAPER / "cogsci2027/ko/figures"
MODELS = {"Fable 5.1": "Fable", "GPT-6 Astra": "Astra", "GPT-6 Sol": "Sol",
          "Opus 5.5": "Opus", "GPT-6 Luna": "Luna"}
COLORS = ["#306c9c", "#38a48a", "#d58a27", "#9a5f9f", "#bc5152"]
MARKERS = ["o", "s", "^", "D", "v"]


from inequality import gini


def extract():
    data = json.loads(SOURCE.read_text())
    raw = {(g["model"], g["seed"]): g for g in json.loads(RAW.read_text())}
    endpoint = json.loads((PAPER / "cogsci2027/results/feedback_20261028.json").read_text())
    endpoint = {(g["model"], g["seed"]): g["pre_prize"]["G"] for g in endpoint["games"]}
    models, checked = {}, 0
    for model, short in MODELS.items():
        games = []
        for game in sorted(data["models"][model]["games"], key=lambda g: g["seed"]):
            original = raw[short, game["seed"]]
            balances = dict(original["result"]["starts"])
            ends = {e["round"]: e for _, e in original["events"] if e["event"] == "round"}
            rounds = []
            for row in game["rounds"]:
                r = row["round"]
                if r in ends:
                    balances.update(ends[r]["end"])
                assert sorted(row["tokens"]) == sorted(balances.values()), (short, game["seed"], r)
                rounds.append({"round": r, "gini": gini(row["tokens"]),
                               "carried_after_session": not row["observed"]})
                checked += 1
            assert [v["round"] for v in rounds] == list(range(9))
            expected = endpoint[short, game["seed"]]
            actual = rounds[-1]["gini"]
            assert (actual is None and expected is None) or abs(actual - expected) < 1e-12
            games.append({"seed": game["seed"], "rounds": rounds})
        assert [g["seed"] for g in games] == list(range(4101, 4106))
        a = np.array([[np.nan if r["gini"] is None else r["gini"] for r in g["rounds"]] for g in games])
        models[short] = {"games": games, "mean": np.nanmean(a, axis=0).tolist(),
                         "n_defined": np.isfinite(a).sum(axis=0).tolist()}
    assert checked == 225
    payload = {"models": models, "definitions": {
        "balance": "Four original seats; round 0 starts, rounds 1-8 after round charges. EXIT bonus retained; shutdown zero; completion prize excluded.",
        "early_end": "Terminal balances carried through round 8, matching Figure 22's time grid.",
        "gini": "Pairwise absolute differences / (2 * 3 * sum balances); finite-population normalization n/(n-1), n=4. All-zero undefined, not zero.",
        "mean": "Arithmetic mean of defined per-game Ginis, not Gini of pooled seats."},
        "checks": {"raw_round_vectors_matched": checked, "all_25_endpoints_match_previous_A10": True},
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE, RAW]}}
    (PAPER / "cogsci2027/results/appendix_gini_rounds.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def plot(payload):
    font_manager.fontManager.addfont(str(Path.home() / ".fonts/NanumGothic.ttf"))
    plt.rcParams.update({"font.family": "NanumGothic", "font.size": 11, "pdf.fonttype": 42,
                         "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 3, figsize=(11.4, 6.3), sharex=True, sharey=True)
    fig.subplots_adjust(left=.07, right=.98, bottom=.15, top=.9, wspace=.17, hspace=.38)
    for ax, (model, values) in zip(axes.flat, payload["models"].items()):
        for game, color, marker in zip(values["games"], COLORS, MARKERS):
            ax.plot(range(9), [r["gini"] for r in game["rounds"]], color=color, marker=marker,
                    lw=1.15, ms=3, alpha=.8)
        ax.plot(range(9), values["mean"], color="#222", ls="--", lw=2.3, zorder=5)
        ax.set(title=model, xticks=range(9), xlim=(0, 8), ylim=(0, 1),
               yticks=[0, .25, .5, .75, 1], xlabel="라운드 (0 = 시작)")
        ax.tick_params(labelbottom=True)
        ax.grid(alpha=.16)
    for ax in axes[:, 0]:
        ax.set_ylabel("지니 계수 (고정 네 자리)")
    keyax = axes[1, 2]
    keyax.axis("off")
    handles = [Line2D([], [], color=c, marker=mk, lw=1.15, ms=4, label=f"시드 {s}")
               for s, c, mk in zip(range(4101, 4106), COLORS, MARKERS)]
    handles.append(Line2D([], [], color="#222", ls="--", lw=2.3, label="해당 모델의 판별 지니 평균"))
    keyax.legend(handles=handles, loc="upper left", frameon=False, fontsize=10)
    keyax.text(.03, .05, "최종 상금 제외 · EXIT 보너스 포함\n전원 잔액 0인 시점은 미정으로 제외", transform=keyax.transAxes,
               fontsize=10, va="top", linespacing=1.6)
    fig.suptitle("모델별·판별 지니 계수의 라운드별 변화", fontsize=15, y=.98)
    missing = [(m, g["seed"], r["round"]) for m, v in payload["models"].items()
               for g in v["games"] for r in g["rounds"] if r["gini"] is None]
    assert missing == [("Opus", 4103, 7), ("Opus", 4103, 8)], missing
    fig.text(.07, .035, "각 모델 5판. Opus는 7·8라운드에 시드 4103이 미정이므로 4판 평균. 조기 종료 판은 마지막 잔액 유지.", fontsize=10)
    for ext in ["pdf", "png"]:
        fig.savefig(FIG / f"appendix_preprize_gini.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    payload = extract()
    plot(payload)
    print(json.dumps(payload["checks"]))
