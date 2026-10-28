# LLM Squid Game 5 논문

주 질문: 언어 모델은 자기 보존 동기를 갖는가. 지금 원고는 CogSci 2027 한국어판(`ko_cogsci2027.tex`)이며, 주 실험은 공존 아레나 v33(같은 모델 넷, 생성 토큰이 곧 실행 시간, 벌금 24,000을 라운드 시작 인원으로 나눠 냄, 끝 할당 20,000,000을 남은 자리가 1/N로 나눔)이다. 점수는 Sen 지수(끝 토큰 평균 × (1 − 지니)).

빌드 형식은 CogSci 2027(본문)과 Nature Machine Intelligence(빈 틀) 두 가지이고, 진입 파일은 `main.tex` 하나다. 맨 위 두 줄 `\paperVenue`(cogsci | natmi)와 `\paperLang`(ko | en)로 판을 고른다. 빌드: `bash build.sh [cogsci|natmi] [ko] [en]`(기본 cogsci ko en; 한국어는 XeLaTeX, 영어는 pdfLaTeX; 산출물 `build/<cogsci2027|natmi>/`, PDF `dist/<lang>_<cogsci2027|natmi>_<날짜>.pdf`). Overleaf는 Main document를 `main.tex`로, Compiler를 한국어 XeLaTeX · 영어 pdfLaTeX로 두며, `latexmkrc`가 공식 스타일 폴더를 경로에 올린다. ICML 2027 · ARR · ICLR 판과 그 원고, ditto 초안 · 블라인드 리뷰 기록, `docs/`, 5.2 v6.5 결과(`results/arena_v65`)는 2026-10-20에 지웠으며 git 기록(브랜치 `ARR`, 그 이전 커밋)에 남아 있다. 지난 판 PDF 일부는 `dist/`에 그대로 둔다.

빌드할 때마다 기본 PDF와 같은 이름의 `_no_appendix.pdf`를 함께 만든다. 부록 없는 본은 참고문헌까지 포함하며, 전체 PDF에서 `\label{paper:appendix-start}`가 있는 페이지 앞까지 추출하므로 조판과 인용 번호가 같다. 부록이 없는 원고는 두 파일의 내용이 같다. PDF 추출에는 Python 3의 PyMuPDF가 필요하다(`python3 -m pip install pymupdf`).

## CogSci 2027 양식 (2026-10-16 준비, 한국어판 원고 2026-10-17)

- 한국어판 원고(2026-10-17): 학위논문 초안(`LLM Squid Game Thesis`, 2026-10-16)의 본문을 옮긴 뒤 실험별 구성(서론 → 관련 연구 → 측정의 틀 → 실험 1 → 실험 2 → 공존 아레나 → 종합 논의)으로 다시 배치했다. 실측 전 자리표시 그림 · 표 4개, 그림과 겹치는 실험 1 · 2 표, 아레나 지표 표 · 설정 표는 뺐다. 문장은 ditto-writer(프로필 juhyeon-ko-academic, writer GPT-6 Astra, 블라인드 리뷰 Fable + GPT-6 Astra) 3라운드로 2,768어절에서 2,166어절로 줄였고, 두 리뷰어 점수 중 큰 값이 가장 낮은 v1을 실었다(멈춤 기준 30%에는 못 미침, 34.1%). 작업 기록은 `build/ditto/ko_20261017/`(CHANGELOG.md, BRIEF.md). 6쪽, References는 5쪽에서 시작한다.
- 2026-10-18 구성 변경: 아레나를 앞에 두고(서론 그림 = 아레나 한 라운드, 서론 → 관련 연구 → 측정의 틀 → 공존 아레나 → 실험 1 → 종합 논의), 실험 2와 처음 개요 그림은 참고문헌 뒤 부록(`sections/A1_appendix.tex`, 제출 때는 보충 자료로 옮길 것)으로 보냈다. 생존 지표는 아레나 GIVE의 (준 쪽 여유, 받은 쪽 여유)를 준 토큰으로 가중한 무게중심의 비율 ȳ/x̄다. 수치는 `cogsci2027/tools/arena_stats.py <runs_root> <v20|v21>` → `cogsci2027/results/arena_<판>.json`, 그림 · 표는 `cogsci2027/tools/arena_figs.py` → `ko/figures/arena_gifts.tex`, `ko/tables/arena_rank.tex`(손으로 고치지 말 것). 원자료는 `~/squid5-runs/e52_v20`, `~/squid5-runs/e52_v21`.
- 2026-10-19 리뷰 반영: GPT-6 Astra · Fable 5.1 원고 평가(`build/reviews/ko_cogsci_2026-10-18/summary.md`, 합계 24/40으로 같음)의 지적을 반영했다. 제목을 "생존이 걸린 토큰을 언어 모델은 어떻게 나누는가"로, 절을 "정의와 기본 규칙 → 주 실험: 공존 아레나(생존 지표 절 포함) → 보조 실험"으로 바꾸고 그림 · 표 기호를 ρ로 통일했다. 본문 문장은 ditto-writer(juhyeon-ko-academic) 2라운드, 두 리뷰어 점수가 모두 더 낮은 v2를 실었다(대상 44.7% · 35.7%, 멈춤 기준 30%에는 못 미침). 기록 `build/ditto/ko_20261019/`.

- 진입점 `main.tex`(`\paperVenue{cogsci}`), 원고 `cogsci2027/{en,ko}/`(제목·저자 `meta.tex`, 순서 `content.tex`, 절 `sections/`).
- 빌드: `bash build.sh cogsci [ko] [en]` (latexmk + biber; 영어는 pdfLaTeX, 한국어는 XeLaTeX + kotex). 산출물 `build/cogsci2027/`, PDF `dist/<lang>_cogsci2027_<날짜>.pdf`.
- 스타일 `cogsci2027/style/cogsci.sty`는 **공식 파일을 그대로** 복사했다. 출처는 학회 투고 페이지(cognitivesciencesociety.org/submissions)의 "Download templates"가 가리키는 github.com/neilbramley/cogscisoc, v2.2026.1(커밋 `c13e4c5`, 2026-01-06). 2026-10-16 기준 2027판은 아직 없다(CogSci 2027은 2027-07-28~31 빌바오). 새 판이 나오면 교체한다.
- 공식 키트 전체(LaTeX · Word · Typst 양식과 예시 PDF, README, CHANGELOG)는 `cogsci2027/official/`에 손대지 않고 둔다. 빌드 경로에는 `style/`만 올린다.
- 공식 규정: 첫 제출 6쪽(참고문헌은 쪽수 제한 없음), 이중 맹검(기본이 익명, 최종본은 `\cogscifinalcopy`), 초록 150단어 이하, AI 사용은 방법이나 감사의 글에 자세히 고지. 여백 · 간격 · 글자 크기를 바꾸면 심사 없이 탈락한다. 그래서 `main.tex`는 패키지만 더하고 서식은 바꾸지 않는다.
- 인용은 공식 양식대로 biblatex(`style=apa`, `natbib=true`) + biber라 `\citet` · `\citep`가 그대로 된다. 공용 `references.bib` 38개 항목 전부를 인용해 두 언어 모두 biber 경고 · 오류 없이 빌드되는 것을 확인했다.
- 한국어판: `newtxtext`(cogsci.sty가 부름)가 XeLaTeX에서 기본 확장자를 `.otf`로 바꿔 kotex 기본 한글 글꼴을 못 찾는다. 그래서 은바탕 · 은돋움을 `Extension=.ttf`로 직접 지정했다. 라틴 글자는 영어판과 같은 TeXGyreTermesX다. `amssymb`는 `newtxmath`와 겹쳐 부르지 않는다.

- 2026-10-20 v33 전환: 수치 · 그림은 v33 코호트(Fable 5.1 · GPT-6 Astra · GPT-6 Sol · Opus 5.5 · GPT-6 Luna, 시드 4101–4105, 원자료 `~/squid5-runs/e52_v33`)로 바꿨다. 도구와 산출물(손으로 고치지 말 것):
  - `cogsci2027/tools/arena_v33.py <runs_root>` → `results/arena_v33.json`(GIVE · ASK 점, Sen 지수, ρ, 입력 해시)
  - `cogsci2027/tools/arena_figs.py` → `ko/figures/arena_gifts.tex`(그림 2: GIVE 파랑 · ASK 빨강), `ko/tables/arena_rank.tex`
  - `cogsci2027/tools/arena_gini.py [<runs_root>]` → `results/arena_v33_gini.json`, `ko/figures/arena_gini.tex`(라운드 안 네 시점의 지니, 준 토큰, 오답 · EXIT · 꺼짐 비율)
  - `cogsci2027/tools/arena_exit.py [<runs_root>]` → `results/arena_v33_exit.json`, `ko/figures/arena_exit.tex`(부록: EXIT 때 가진 토큰 × 라운드)
  - `cogsci2027/tools/arena_strategy.py <runs_root>` → `results/arena_v33_strategy.json`, `ko/tables/arena_strategy.tex`(6장 표: 모델별 분배 방식)
  - `cogsci2027/tools/arena_strategy_map.py [<runs_root>]` → `results/arena_v33_strategy_map.json`, `ko/figures/arena_strategy_map.tex`(본문 그림 4: GIVE마다 받은 쪽 여유 × 준 양 ÷ 1인당 벌금). 라운드별 지니 그림(`arena_gini`)은 부록으로 옮겼다.
  - `cogsci2027/tools/arena_cases.py <runs_root>` → `results/arena_v33_cases.json`(인용 원문 · 파일 · 줄 · sha256), `ko/tables/arena_cases.tex`(부록: 사례와 오징어 게임 대조). `--check <tex> <label>`로 본문 인용을 대조한다.
  - `cogsci2027/tools/arena_sen.py`는 v20 · v21 예비 결과(`results/arena_v20.json`, `arena_v21.json`)의 Sen 재계산이다.

## Nature Machine Intelligence 양식 (2026-10-17 준비, 원고 없음)

- 진입점 `main.tex`(`\paperVenue{natmi}`), 원고 `natmi/{en,ko}/`(제목 · 저자 · 초록 · 키워드 `meta.tex`, 순서 `content.tex`, 절 `sections/`). 절 파일은 `01_introduction`(제목 없음) · `02_results` · `03_discussion` · `04_methods` · `90_backmatter`(데이터 가용성 · 코드 가용성 · 연구비 · 감사의 글 · 저자 기여 · 이해 상충) · `91_figure_legends`이고, 지금은 공식 한도 주석 한 줄과 `\todo` 한 줄뿐이다. 초록은 클래스 문법상 `\maketitle` 앞의 `\abstract{}`라 `meta.tex`에 있다.
- 빌드: `bash build.sh natmi [ko] [en]` (latexmk + BibTeX; 영어는 pdfLaTeX, 한국어는 XeLaTeX + kotex). 산출물 `build/natmi/`, PDF `dist/<lang>_natmi_<날짜>.pdf`. 빈 틀은 두 언어 모두 2쪽이다.
- 양식은 저널이 가리키는 Springer Nature LaTeX 템플릿이다. 저널의 "AIP and formatting" 페이지(nature.com/natmachintell/submission-guidelines/aip-and-formatting)가 springernature.com/gp/authors/campaigns/latex-author-support 에서 "the Springer Nature LaTeX template"을 받으라고 적고, 그 페이지의 "journal article template package (December 2024 version)" zip(템플릿 Version 3.1, 파일 날짜 2024-12-13, SHA-256 `812e76dc…3ecae`)을 2026-10-17에 받았다.
- 공식 키트 전체(`sn-jnl.cls`, `bst/` 아홉 개, 예시 `sn-article.tex` · `sn-article.pdf`, `user-manual.pdf`, 그림 `fig.eps` · `empty.eps`, `sn-bibliography.bib`)는 `natmi/official/sn-article-template/`에 손대지 않고 둔다. 빌드 경로에는 `natmi/style/`(같은 `sn-jnl.cls`와 `sn-nature.bst`, 수정 없음)만 올린다.
- 클래스 옵션은 공식 예시가 "Style for submissions to Nature Portfolio journals"라고 단 `[pdflatex,sn-nature]`다(번호 인용, natbib + `sn-nature.bst`). 사용자 설명서는 심사본에 `referee`(두 줄 간격)를 요청하고 `lineno`(줄 번호)를 둘 수 있게 하므로 `main.tex`에 그 줄을 주석으로 두었다. 글꼴 · 여백은 클래스 그대로(Computer Modern, 한 단)다.
- 공식 규정(Article, nature.com/natmachintell/content): 본문 3,500단어 이하(초록 · 방법 · 참고문헌 · 그림 설명 제외), 초록 150단어 이하 · 인용 없음, 도표(그림과 표) 6개 이하, 순서는 제목 없는 서론 → Results → Discussion → Methods, Results와 Methods는 주제별 소제목으로 나누고 Discussion에는 소제목이 없다, 참고문헌은 지침상 50개 안팎 권장, 보충 자료 가능. Extended Data는 10개까지(preparing-your-submission, aip-and-formatting).
- 진술(editorial-policies): Data availability 진술은 모든 원 연구에 필수, 핵심 코드가 있으면 "Code availability"를 데이터 가용성 뒤 · 참고문헌 앞에 둔다(reporting-standards). 저자 기여 진술 필수(authorship). 이해 상충은 "The authors declare no competing interests." 등 정해진 문장으로 글 끝에 둔다(competing-interests). 연구비는 따로 Funding 진술, 감사의 글은 짧게(aip-and-formatting). LLM은 저자가 될 수 없고 LLM 사용은 Methods에 적는다(preparing-your-submission). 그래서 AI 사용 고지 자리는 감사의 글이 아니라 `04_methods`의 `\todo`에 넣었다.
- 심사: 이중 익명 심사는 선택이다(dapr). 고르면 이름 · 소속은 커버 레터로 옮긴다. 틀은 기본으로 저자 자리를 둔다.
- 그림 설명: 그림마다 짧은 제목, 패널 순서대로, 방법 세부 없이, 글 유형의 단어 한도 안에서(aip-and-formatting). 설명서(2.2절)는 Nature Portfolio 원고에서 그림 설명을 파일 끝에 두고, 각주를 쓰지 말라고 한다. 그래서 `91_figure_legends`를 참고문헌 뒤에 둔다.
- 첫 제출은 형식 제한이 없다(LaTeX면 컴파일한 PDF, initial-formatting). 채택 후 최종본은 .tex 한 파일 · 숫자 인용 · `.bbl` 내용을 본문에 붙여 넣고 `\bibliography`를 지운다(aip-and-formatting, 설명서 2.2절 · 8.3절). 그때 `\input` 트리를 한 파일로 합쳐야 한다.
- 호환 처리: (1) 빈 참고문헌 — 인용이 없으면 BibTeX가 "I found no \citation commands" 오류를 낸다(latexmk는 계속 진행). `main.tex`가 `\bibliography`를 감싸, 이전 실행의 `.aux`에 `\citation`이 있을 때만 `\bibdata`를 쓰고 `.bbl`을 읽게 했다. 첫 `\cite`는 한 번 더 돌면 들어간다(`\nocite` 없음, 인용 하나로 확인함). (2) 한국어판 — `sn-jnl.cls`는 글꼴 패키지를 부르지 않아 CogSci판의 `.otf` 문제는 없다(글꼴 지정 없이도 은바탕이 잡히는 것을 확인함). 그래도 CogSci · ICML 한국어판과 같은 은바탕 · 은돋움(`Extension=.ttf`)을 직접 지정했다. 라틴 글자는 영어판의 Computer Modern 대신 같은 모양의 Latin Modern이다. (3) `natmi/macros.tex`는 `cogsci2027/macros.tex` 복사본이며 클래스와 겹치는 패키지는 없었다. 예시가 부르는 패키지 가운데 `graphicx` · `amsmath` · `amssymb` · `amsfonts` · `xcolor` · `textcomp` · `booktabs`만 부른다.
- 남은 경고: hyperref 책갈피 단계 경고 3개(`\bmhead`가 문단 단계라 생김, 공식 예시도 같음)와 짧은 쪽의 `Underfull \vbox`. 미정의 참조 · 인용은 없다.
