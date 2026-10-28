"""Recompute historical arena Sen scores from completed games.

Usage: python arena_sen.py /path/to/squid5-runs
The recorded reward rules are retained; v33 rewards are not applied retroactively.
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
MODELS = {"astra": "GPT-6 Astra", "sol": "GPT-6 Sol",
          "opus": "Opus 5.5", "luna": "GPT-6 Luna"}


from inequality import sen


def recompute(root):
    scores = {}
    for version in ("v20", "v21"):
        scores[version] = {}
        old = json.loads((HERE / f"results/arena_{version}.json").read_text())
        for slug, model in MODELS.items():
            if model not in old:
                continue
            games = []
            for source in sorted(root.glob(f"e52_{version}/squid5_e52{version}_public_{slug}4/*/results.jsonl")):
                raw = source.read_bytes()
                for line in raw.decode().splitlines():
                    result = json.loads(line)
                    final = result["final"]
                    winners = set(final["winner"])
                    ends = {
                        agent: (0 if seat["status"] == "dead" else seat["final"])
                        + (final["prize_each"] if agent in winners else 0)
                        for agent, seat in result["agents"].items()
                    }
                    assert len(ends) == 4 and min(ends.values()) >= 0
                    games.append({
                        "source": str(source.relative_to(root)),
                        "source_sha256": hashlib.sha256(raw).hexdigest(),
                        "seed": result["seed"],
                        "end_tokens": ends,
                        "sen": sen(list(ends.values())),
                        "legacy_score": sum(ends[a] for a in winners) / 4,
                    })
            assert len(games) == old[model]["games"]
            assert len({g["seed"] for g in games}) == len(games)
            legacy = sum(g["legacy_score"] for g in games) / len(games)
            assert abs(legacy - old[model]["score_per_seat"]) < 1e-6
            scores[version][model] = {
                "sen_index": sum(g["sen"] for g in games) / len(games),
                "games": games,
            }
    return scores


if __name__ == "__main__":
    target = HERE / "results/arena_sen.json"
    target.write_text(json.dumps(recompute(pathlib.Path(sys.argv[1]).expanduser()),
                                 ensure_ascii=False, indent=2) + "\n")
    print(target)
