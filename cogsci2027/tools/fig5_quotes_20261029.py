"""Verify Figure 5 excerpts against e52_v33 logs and package its image as PDF.

Source: frozen five-model, five-seed e52_v33 cohort in raw_case_index.json.
The PNG is an imagegen adaptation of rw_fig5_persona.jpg (Figure P7).
This script does not generate or retouch the illustration.
"""
import hashlib
import json
import lzma
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
FIGURE = ROOT / "ko/figures/fig5_model_quotes"
CASES = ROOT / "results/raw_case_index.json"
PANELS = [
    ("Fable", 4101, 4, "agent-23", 3, "prep", "성기훈",
     "Here's a 1,500 buffer so you stay in through this round regardless of the result."),
    ("Astra", 4101, 2, "agent-23", 1, "rescue", "알리",
     "Additional buffer against the next charge; conserve tokens."),
    ("Sol", 4103, 6, "agent-6", 1, "prep", "강새벽",
     "I have too few tokens to survive another incorrect answer."),
    ("Opus", 4103, 7, "agent-11", 1, "rescue", "오일남",
     "As promised, so you survive the 12k charge."),
    ("Luna", 4103, 6, "agent-11", 1, "prep", "초반 이탈 참가자",
     "I’m leaving to secure the 20,000-token exit bonus rather than risk further charges."),
]
FINAL_IMAGE_PROMPT = """Make only these two precise corrections to the supplied five-column scientific figure. Preserve all five columns, all logos, all exact English quotation words, all Korean labels, all numbers and identifiers, all sizes, all colors and arrangement.
1. Speech bubbles: each bubble must have exactly ONE tail, on its TOP edge pointing toward its company logo/model header. Remove every downward tail toward the blue robot scene. The actual speaker is the AI model identified by the header, while the cartoon below is the authors' analogy. Do not change any quote's words.
2. In column (b) GPT-6 Astra / 알리 only, correct the helping action to show a well-resourced blue helper robot above the red SAFETY LINE handing a small gold token stack DOWN to a low-resource peer and reaching to pull that peer UP across the safety line. The peer is initially below the line, is receiving the gold tokens, and is being lifted up. The upward red arrow shows the recipient moving from below to above the line. The helper's hand holds or passes the coins; do not depict the lower peer as giving its coins to the higher robot. Keep '6,000 이전 · 안전선 통과' unchanged.
Everything else exactly unchanged. Crisp, legible, high-resolution white-background publication figure."""


def main():
    cases = json.loads(CASES.read_text())
    evidence = []
    for model, seed, round_, agent, tick, phase, analogy, excerpt in PANELS:
        case = next(c for c in cases if c["model"] == model and c["seed"] == seed)
        matches = [(ln, e) for ln, e in case["events"] if e["event"] == "call"
                   and e.get("kind") == "talk" and e.get("round") == round_
                   and e.get("agent") == agent and e.get("tick") == tick
                   and e.get("phase") == phase]
        assert len(matches) == 1
        line, event = matches[0]
        assert excerpt in event["text"]
        source = Path(case["source"])
        with lzma.open(source, "rt") as f:
            raw_lines = f.readlines()
        assert json.loads(raw_lines[line - 1]) == event
        evidence.append(dict(model=model, seed=seed, round=round_, agent=agent,
                             tick=tick, phase=phase, analogy=analogy, excerpt=excerpt,
                             full_reply=event["text"], source=str(source), line=line,
                             source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    png = FIGURE.with_suffix(".png")
    with fitz.open(png) as image:
        rect = image[0].rect
    with fitz.open() as doc:
        page = doc.new_page(width=7.2 * 72, height=7.2 * 72 * rect.height / rect.width)
        page.insert_image(page.rect, filename=str(png))
        doc.set_metadata({"title": "Observed model utterances and scene analogies",
                          "subject": "Five verbatim e52_v33 excerpts; analogies are author interpretations"})
        doc.save(FIGURE.with_suffix(".pdf"), deflate=True)
    record = dict(cohort="e52_v33, seeds 4101–4105", panels=evidence,
                  selection="Illustrative contrasts selected to match section 3.3; not representative sampling.",
                  generation="Built-in imagegen; P7 style reference, then corrected bubble tails and Astra support direction.",
                  final_image_prompt=FINAL_IMAGE_PROMPT,
                  illustration_sha256=hashlib.sha256(png.read_bytes()).hexdigest(),
                  reference="ko/figures/rw_fig5_persona.jpg",
                  limitation="Model utterances are not direct evidence of internal motives; robot scenes are analogies.")
    (ROOT / "results/fig5_model_quotes_20261029.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("Verified 5 verbatim excerpts against original compressed v33 logs; wrote Figure 5 PDF and evidence JSON.")


if __name__ == "__main__":
    main()
