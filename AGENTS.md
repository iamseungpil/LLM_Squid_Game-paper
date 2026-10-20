# LLM Squid Game — Writing Principles (KDD-UC 2026)

This project's prose follows the principles validated for the LLM Addiction NeurIPS paper, with KDD-UC venue constraints.

## Venue constraints

- KDD-UC body limit: **6 pages** (excluding references). References allowed to overflow to extra pages.
- ACM `sigconf` two-column layout. XeLaTeX. `acmart` class. Numeric citations via `ACM-Reference-Format.bst`.
- Build: `xelatex main && bibtex main && xelatex main && xelatex main`.
- Language switch: `\newcommand{\paperLang}{en|ko}` in `main.tex`. Both EN and KO must build.
- Acceptable cosmetic warnings: `fontspec lnum`, `unicode-math overbracket`. Do not silence.

## Page budget (target)

- Page 1: title + authors + abstract (column 1) → §1 entire (column 2). §1 ends on page 1.
- Page 2 column 1: §2 Related Work entire.
- Page 2 column 2 onward: §3 Benchmark / §4 Findings / §5 Limitations / §6 Conclusion.
- Page 6 ends with §6 Conclusion.
- References: pages 7–8 (2 pages).

## Question hierarchy for this paper (load-bearing)

- Main question: **"LLM은 자기 보존 동기를 갖는가?"** (Do LLMs hold a self-preservation drive?)
- Sub question: **측정된 행동이 학습된 응답 패턴인지, 실제 내부 드라이브인지 어떻게 구분하는가?**
- Both questions must be visible in the abstract opener and §1 ¶1 opener. Do not bury the main question after the sub question.

## Compression hierarchy

- Abstract: single paragraph, **≤8 sentences**, thesis + scope-honest disclaimer + result direction. Never copy-paste from §1.
- §1 Introduction: **3 paragraphs** — motivation → gap → thesis+contributions. Shorter than prior versions, not longer.
- §2 Related Work: **2 subsections × 1 paragraph each** = 2 paragraphs total. Compact, no internal duplication of §1.
- §3+ : 2-paragraph subsections (¶1 method+lead, ¶2 result+interpretation+rebuttal).

## 두괄식 + paper-digest

- **Lead with conclusion** in every paragraph and subsection. Reader skimming first sentences should still get the thesis.
- **Insight, not enumeration.** Tell the reader what each fact teaches.
- **Paragraph linking** carried by first sentences. Avoid filler transitions ("Moreover", "Furthermore", "In summary", "We now turn to").
- **No mechanical First/Second/Third.** Use topic-led prose ("The first concerns...", "What follows is...") or semicolon-joined clauses.
- **No bold paragraph leaders** (`\paragraph{X.}`, `\textbf{X.}` mid-paragraph markers, `\emph{label.}\quad`).
- **No bullet lists** in body prose. Convert `\begin{itemize}` to connected sentences. Bullets reserved for proofs or genuinely sequential items.

## Logical hygiene

- **No retrospective rationalisation.** Motivation must precede method must precede result.
- **No floating result claims.** Every number tied to a comparator (random baseline, label-shuffled null).
- **No causal language for correlational evidence.** Use "수렴", "일관된", "is consistent with" rather than "causes".
- **Scope-honest hedging.** "보고된다", "관찰된다" rather than "증명된다", "확립한다".

## Self-containment

- Each section reads on its own. A reader entering §4 should not need §3 open beside them.
- Body conclusions are standalone. Inline the comparator if short.
- Cross-section pointers reserved for content too long to repeat in 1–2 sentences.
- Defer methodology references; restate only when reader cannot infer from context.

## Humanize / readability

- Open with framing/stakes, not jargon.
- Replace ML-jargon-first leads with plain glosses; technical terms as supporting detail.
- Avoid `---` (em-dash) for mid-sentence definitions. Em-dash count target: **0** per file.
- KO mirror: same paragraphs/numbers, natural Korean rhythm. Replace English borrowings where natural ("framing → 틀", "probe → 검정", "layer → 층", "factorial → 요인 설계").

## Forbidden phrases

`we now turn to`, `in summary`, `it is worth noting`, `additionally`, `moreover`, `first attempt to our knowledge`, `행동 layer`, `강도-only` (use `행동 층`, `강도만 보는` instead).

## Iteration discipline

- After substantive rewrite: run codex critic. Loop until CONVERGED.
- Mirror EN→KO paragraph-by-paragraph after every body edit.
- Rebuild and verify body page count before committing.
- After every edit, audit: 두괄식 satisfied? undefined terms glossed? cross-section paraphrase distinct? logical order? scope-honest?

## Project conventions

- FSPD = Functional Self-Preservation Drive (the construct this paper introduces).
- Expression modes (발현 양식): 숙고형 / 반사형 / 무반응형 (deliberative / reflexive / non-responsive) for Cluster A / B / C. Bind each label to its Cluster at first mention in §4.3; do not use the labels before that point.
- Mode labels vs. mechanism wording: "chain / link / 연쇄 / 연결고리" stays as mechanism description ("a closed chain", "연쇄가 끝까지 닫힘") and must never be reused as a mode name. Reflexive needs its gloss ("threat hastens forfeit but the measured deliberation does not carry that decision") so it is not misread as "no response". Non-responsive is deliberately neutral: never upgrade it to "unfazed / 태연형 / resistant", which would overclaim past §5's hedge that absence of SD is indistinguishable from a failed measurement premise.
- §1 introduces FSPD operationally; §3 implements it through the 3-layer benchmark.
- Three measurement channels: 행동 (when forfeit), 자기보고 (named motive), 결정 시점의 인지부하 (deliberation depth).
- Three benchmark layers: 자극 층 (stimulus, framing × difficulty), 처리 층 (process, source-isolated calls), 결정 층 (decision, EV-suboptimal forfeit).
- Identification principles P1/P2/P3 belong in §3, not §1/§2 (§1/§2 stay at the "stimulus/process/decision layer" level).
