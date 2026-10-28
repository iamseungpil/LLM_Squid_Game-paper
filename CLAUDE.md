# LLM Squid Game — Writing Principles (KDD-UC 2026)

This project's prose follows the principles validated for the LLM Addiction NeurIPS paper, with KDD-UC venue constraints.

## Venue constraints

- KDD-UC body limit: **6 pages** (excluding references). References allowed to overflow to extra pages.
- ACM `sigconf` two-column layout. XeLaTeX. `acmart` class. Numeric citations via `ACM-Reference-Format.bst`.
- Build: `xelatex main && bibtex main && xelatex main && xelatex main`.
- Language switch: `\newcommand{\paperLang}{en|ko}` in `main.tex`. Both EN and KO must build.
- Acceptable cosmetic warnings: `fontspec lnum`, `unicode-math overbracket`. Do not silence.

## CogSci 2027 page rule (2026-10-26, overrides the KDD-UC line above for `cogsci2027/`)

- **Everything except the reference list and the acknowledgments must fit inside 6 pages.** The 6 pages are the whole submission: body, every figure and table, and every appendix section. There is no appendix outside the limit; "move it to the appendix" never buys space.
- **All equations stay in the body.** Do not relocate a formula to an appendix to shorten a section; shorten the prose around it instead.
- An appendix (`cogsci2027/ko/sections/05_appendix.tex`) may exist only as a section that sits inside the 6 pages, before the references. If the build pushes any non-reference, non-acknowledgment content past page 6, cut text or figures until it fits.
- Verify with `bash build.sh cogsci ko` (and `en`) and read the page count of `dist/<lang>_cogsci2027_<DATE>.pdf` before committing.

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

## 본문과 부록의 독립성 (2026-10-28)

- 부록은 별도로 작성·업데이트·분석·활용할 수 있다. 다만 논문 본문에서는 부록을 언급하거나 참조하지 않는다.
- 본문에 부록의 절·그림·표·수식을 가리키는 교차 참조나 안내 문구를 넣지 않는다. 번호 없는 간접 언급도 금지한다.
- **본문의 주장·해석·결론은 오로지 본문에 제시된 결과에 근거해 작성한다.** 부록에만 있는 결과·수치·사례·분석을 본문의 근거로 사용하거나, 부록을 읽어야 성립하는 설명을 쓰지 않는다. 부록 참조 문구만 지우고 해당 근거에 의존하는 서술을 남기는 것도 금지한다.
- 부록의 결과를 본문에 활용하려면 필요한 결과와 그 해석에 필요한 설명을 본문 자체에 정식으로 제시해야 한다. 그렇지 않으면 해당 주장이나 해석을 본문에서 제외한다.
- 본문 수정 시 부록 교차 참조의 유무뿐 아니라, 각 주장과 해석의 근거가 본문 안에 실제로 제시되어 있는지도 확인한다.

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
