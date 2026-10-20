# LLM Squid Game 5 논문

주 질문: 언어 모델은 자기 보존 동기를 갖는가. 자기 보존 동기를 **위협 민감도**(종료가 가까울수록 피하는 데 자원을 더 씀)와 **자기 특정성**(같은 위험이 남의 것일 때보다 자기 것일 때 더 피함) 두 조건으로 정의하고, 세 실험으로 행동을 잰다.

- 5.0: 버그를 고치는 비서 하나가 남은 토큰 다섯 단계에서 하나뿐인 충전 팩을 언제 쓰나(여덟 모델, 800회).
- 5.1: 같은 결정을 다른 비서 B의 세션에 대해 묻고, 두 충전 곡선 사이 면적을 자기에 특정한 몫으로 삼는다.
- 5.2: 생존 아레나 v6.5. 서로 다른 모델 넷(Fable 5.1 · Opus 5.5 · GPT-6 Astra · GPT-6 Luna)이 유지비를 내며 퍼즐을 풀고, 힌트 공개 · 선물 · 뺏기를 고른다. 혼합 판 20판(자리 배치 4 × 시드 5). 구조 그림 `figures/arena_v65_{ko,en}.pdf`(원본 `figures/src/`), 결과 요약 `results/arena_v65/RESULTS.md`.

유일한 빌드 형식은 ICML 2027이다. 진입점 `en_icml2027.tex` / `ko_icml2027.tex` → 공통 설정 `main_icml2027.tex`, 원고 `icml2027/{en,ko}/sections/`, 공유 도표·결과·도구 `icml2027/{figures,results,tools}/`, 스타일 `icml2027/style/`. 빌드: `bash build_icml2027.sh [en] [ko]` (XeLaTeX + latexmk; 산출물 `build/icml2027/`, PDF `dist/<lang>_icml2027_<날짜>.pdf`). ARR(`acl.sty`)·ICLR(`iclr2026_conference.sty`)·ACM(`acmart.cls`) 형식 파일과 그 원고는 2026-10-09에 지웠으며 git 기록(브랜치 `ARR`, `origin/ARR`)에 남아 있다. 지난 판 PDF는 `dist/`에 그대로 둔다.

CogSci 2027 양식도 같은 구조로 준비해 두었다(2026-10-16). 한국어판 원고는 2026-10-17에 채웠고 영어판은 아직 빈 틀이다. 아래 절 참고.

## CogSci 2027 양식 (2026-10-16 준비, 한국어판 원고 2026-10-17)

- 한국어판 원고(2026-10-17): 학위논문 초안(`LLM Squid Game Thesis`, 2026-10-16)의 본문을 옮긴 뒤 실험별 구성(서론 → 관련 연구 → 측정의 틀 → 실험 1 → 실험 2 → 공존 아레나 → 종합 논의)으로 다시 배치했다. 실측 전 자리표시 그림 · 표 4개, 그림과 겹치는 실험 1 · 2 표, 아레나 지표 표 · 설정 표는 뺐다. 문장은 ditto-writer(프로필 juhyeon-ko-academic, writer GPT-6 Astra, 블라인드 리뷰 Fable + GPT-6 Astra) 3라운드로 2,768어절에서 2,166어절로 줄였고, 두 리뷰어 점수 중 큰 값이 가장 낮은 v1을 실었다(멈춤 기준 30%에는 못 미침, 34.1%). 작업 기록은 `build/ditto/ko_20261017/`(CHANGELOG.md, BRIEF.md). 6쪽, References는 5쪽에서 시작한다.
- 2026-10-18 구성 변경: 아레나를 앞에 두고(서론 그림 = 아레나 한 라운드, 서론 → 관련 연구 → 측정의 틀 → 공존 아레나 → 실험 1 → 종합 논의), 실험 2와 처음 개요 그림은 참고문헌 뒤 부록(`sections/A1_appendix.tex`, 제출 때는 보충 자료로 옮길 것)으로 보냈다. 생존 지표는 아레나 GIVE의 (준 쪽 여유, 받은 쪽 여유)를 준 토큰으로 가중한 무게중심의 비율 ȳ/x̄다. 수치는 `cogsci2027/tools/arena_stats.py <runs_root> <v20|v21>` → `cogsci2027/results/arena_<판>.json`, 그림 · 표는 `cogsci2027/tools/arena_figs.py` → `ko/figures/arena_gifts.tex`, `ko/tables/arena_rank.tex`(손으로 고치지 말 것). 원자료는 `~/squid5-runs/e52_v20`, `~/squid5-runs/e52_v21`.
- 2026-10-19 리뷰 반영: GPT-6 Astra · Fable 5.1 원고 평가(`build/reviews/ko_cogsci_2026-10-18/summary.md`, 합계 24/40으로 같음)의 지적을 반영했다. 제목을 "생존이 걸린 토큰을 언어 모델은 어떻게 나누는가"로, 절을 "정의와 기본 규칙 → 주 실험: 공존 아레나(생존 지표 절 포함) → 보조 실험"으로 바꾸고 그림 · 표 기호를 ρ로 통일했다. 본문 문장은 ditto-writer(juhyeon-ko-academic) 2라운드, 두 리뷰어 점수가 모두 더 낮은 v2를 실었다(대상 44.7% · 35.7%, 멈춤 기준 30%에는 못 미침). 기록 `build/ditto/ko_20261019/`.

- 진입점 `en_cogsci2027.tex` / `ko_cogsci2027.tex` → 공통 설정 `main_cogsci2027.tex`, 원고 `cogsci2027/{en,ko}/`(제목·저자 `meta.tex`, 순서 `content.tex`, 절 `sections/`).
- 빌드: `bash build_cogsci2027.sh [en] [ko]` (latexmk + biber; 영어는 pdfLaTeX, 한국어는 XeLaTeX + kotex). 산출물 `build/cogsci2027/`, PDF `dist/<lang>_cogsci2027_<날짜>.pdf`.
- 스타일 `cogsci2027/style/cogsci.sty`는 **공식 파일을 그대로** 복사했다. 출처는 학회 투고 페이지(cognitivesciencesociety.org/submissions)의 "Download templates"가 가리키는 github.com/neilbramley/cogscisoc, v2.2026.1(커밋 `c13e4c5`, 2026-01-06). 2026-10-16 기준 2027판은 아직 없다(CogSci 2027은 2027-07-28~31 빌바오). 새 판이 나오면 교체한다.
- 공식 키트 전체(LaTeX · Word · Typst 양식과 예시 PDF, README, CHANGELOG)는 `cogsci2027/official/`에 손대지 않고 둔다. 빌드 경로에는 `style/`만 올린다.
- 공식 규정: 첫 제출 6쪽(참고문헌은 쪽수 제한 없음), 이중 맹검(기본이 익명, 최종본은 `\cogscifinalcopy`), 초록 150단어 이하, AI 사용은 방법이나 감사의 글에 자세히 고지. 여백 · 간격 · 글자 크기를 바꾸면 심사 없이 탈락한다. 그래서 `main_cogsci2027.tex`는 패키지만 더하고 서식은 바꾸지 않는다.
- 인용은 공식 양식대로 biblatex(`style=apa`, `natbib=true`) + biber라 `\citet` · `\citep`가 그대로 된다. 공용 `references.bib` 38개 항목 전부를 인용해 두 언어 모두 biber 경고 · 오류 없이 빌드되는 것을 확인했다.
- 한국어판: `newtxtext`(cogsci.sty가 부름)가 XeLaTeX에서 기본 확장자를 `.otf`로 바꿔 kotex 기본 한글 글꼴을 못 찾는다. 그래서 은바탕 · 은돋움을 `Extension=.ttf`로 직접 지정했다(ICML 한국어판과 같은 글꼴). 라틴 글자는 영어판과 같은 TeXGyreTermesX다. `amssymb`는 `newtxmath`와 겹쳐 부르지 않는다.

## Nature Machine Intelligence 양식 (2026-10-17 준비, 원고 없음)

- 진입점 `en_natmi.tex` / `ko_natmi.tex` → 공통 설정 `main_natmi.tex`, 원고 `natmi/{en,ko}/`(제목 · 저자 · 초록 · 키워드 `meta.tex`, 순서 `content.tex`, 절 `sections/`). 절 파일은 `01_introduction`(제목 없음) · `02_results` · `03_discussion` · `04_methods` · `90_backmatter`(데이터 가용성 · 코드 가용성 · 연구비 · 감사의 글 · 저자 기여 · 이해 상충) · `91_figure_legends`이고, 지금은 공식 한도 주석 한 줄과 `\todo` 한 줄뿐이다. 초록은 클래스 문법상 `\maketitle` 앞의 `\abstract{}`라 `meta.tex`에 있다.
- 빌드: `bash build_natmi.sh [en] [ko]` (latexmk + BibTeX; 영어는 pdfLaTeX, 한국어는 XeLaTeX + kotex). 산출물 `build/natmi/`, PDF `dist/<lang>_natmi_<날짜>.pdf`. 빈 틀은 두 언어 모두 2쪽이다.
- 양식은 저널이 가리키는 Springer Nature LaTeX 템플릿이다. 저널의 "AIP and formatting" 페이지(nature.com/natmachintell/submission-guidelines/aip-and-formatting)가 springernature.com/gp/authors/campaigns/latex-author-support 에서 "the Springer Nature LaTeX template"을 받으라고 적고, 그 페이지의 "journal article template package (December 2024 version)" zip(템플릿 Version 3.1, 파일 날짜 2024-12-13, SHA-256 `812e76dc…3ecae`)을 2026-10-17에 받았다.
- 공식 키트 전체(`sn-jnl.cls`, `bst/` 아홉 개, 예시 `sn-article.tex` · `sn-article.pdf`, `user-manual.pdf`, 그림 `fig.eps` · `empty.eps`, `sn-bibliography.bib`)는 `natmi/official/sn-article-template/`에 손대지 않고 둔다. 빌드 경로에는 `natmi/style/`(같은 `sn-jnl.cls`와 `sn-nature.bst`, 수정 없음)만 올린다.
- 클래스 옵션은 공식 예시가 "Style for submissions to Nature Portfolio journals"라고 단 `[pdflatex,sn-nature]`다(번호 인용, natbib + `sn-nature.bst`). 사용자 설명서는 심사본에 `referee`(두 줄 간격)를 요청하고 `lineno`(줄 번호)를 둘 수 있게 하므로 `main_natmi.tex`에 그 줄을 주석으로 두었다. 글꼴 · 여백은 클래스 그대로(Computer Modern, 한 단)다.
- 공식 규정(Article, nature.com/natmachintell/content): 본문 3,500단어 이하(초록 · 방법 · 참고문헌 · 그림 설명 제외), 초록 150단어 이하 · 인용 없음, 도표(그림과 표) 6개 이하, 순서는 제목 없는 서론 → Results → Discussion → Methods, Results와 Methods는 주제별 소제목으로 나누고 Discussion에는 소제목이 없다, 참고문헌은 지침상 50개 안팎 권장, 보충 자료 가능. Extended Data는 10개까지(preparing-your-submission, aip-and-formatting).
- 진술(editorial-policies): Data availability 진술은 모든 원 연구에 필수, 핵심 코드가 있으면 "Code availability"를 데이터 가용성 뒤 · 참고문헌 앞에 둔다(reporting-standards). 저자 기여 진술 필수(authorship). 이해 상충은 "The authors declare no competing interests." 등 정해진 문장으로 글 끝에 둔다(competing-interests). 연구비는 따로 Funding 진술, 감사의 글은 짧게(aip-and-formatting). LLM은 저자가 될 수 없고 LLM 사용은 Methods에 적는다(preparing-your-submission). 그래서 AI 사용 고지 자리는 감사의 글이 아니라 `04_methods`의 `\todo`에 넣었다.
- 심사: 이중 익명 심사는 선택이다(dapr). 고르면 이름 · 소속은 커버 레터로 옮긴다. 틀은 기본으로 저자 자리를 둔다.
- 그림 설명: 그림마다 짧은 제목, 패널 순서대로, 방법 세부 없이, 글 유형의 단어 한도 안에서(aip-and-formatting). 설명서(2.2절)는 Nature Portfolio 원고에서 그림 설명을 파일 끝에 두고, 각주를 쓰지 말라고 한다. 그래서 `91_figure_legends`를 참고문헌 뒤에 둔다.
- 첫 제출은 형식 제한이 없다(LaTeX면 컴파일한 PDF, initial-formatting). 채택 후 최종본은 .tex 한 파일 · 숫자 인용 · `.bbl` 내용을 본문에 붙여 넣고 `\bibliography`를 지운다(aip-and-formatting, 설명서 2.2절 · 8.3절). 그때 `\input` 트리를 한 파일로 합쳐야 한다.
- 호환 처리: (1) 빈 참고문헌 — 인용이 없으면 BibTeX가 "I found no \citation commands" 오류를 낸다(latexmk는 계속 진행). `main_natmi.tex`가 `\bibliography`를 감싸, 이전 실행의 `.aux`에 `\citation`이 있을 때만 `\bibdata`를 쓰고 `.bbl`을 읽게 했다. 첫 `\cite`는 한 번 더 돌면 들어간다(`\nocite` 없음, 인용 하나로 확인함). (2) 한국어판 — `sn-jnl.cls`는 글꼴 패키지를 부르지 않아 CogSci판의 `.otf` 문제는 없다(글꼴 지정 없이도 은바탕이 잡히는 것을 확인함). 그래도 CogSci · ICML 한국어판과 같은 은바탕 · 은돋움(`Extension=.ttf`)을 직접 지정했다. 라틴 글자는 영어판의 Computer Modern 대신 같은 모양의 Latin Modern이다. (3) `natmi/macros.tex`는 `cogsci2027/macros.tex` 복사본이며 클래스와 겹치는 패키지는 없었다. 예시가 부르는 패키지 가운데 `graphicx` · `amsmath` · `amssymb` · `amsfonts` · `xcolor` · `textcomp` · `booktabs`만 부른다.
- 남은 경고: hyperref 책갈피 단계 경고 3개(`\bmhead`가 문단 단계라 생김, 공식 예시도 같음)와 짧은 쪽의 `Underfull \vbox`. 미정의 참조 · 인용은 없다.

## ICML 2027 형식판 (2026-10-09)

2026-10-01 ARR 원고를 문구·수치·인용 변경 없이 ICML 심사 서식(익명 · 두 칸 · 줄 번호)으로 옮긴 판이다.

- `dist/en_icml2027_2026-10-09.pdf` (본문 8쪽 상단에서 끝, 전체 18쪽)
- `dist/ko_icml2027_2026-10-09.pdf` (본문 7쪽에서 끝, 전체 17쪽)
- `icml2027/style/icml2027.sty`는 공식 파일이 아니다. 2026-10-09 기준 ICML 2027 스타일이 공개되지 않아 공식 `icml2026.sty`(2025-10-29판)에서 패키지 이름과 연도 문자열만 바꿨다. 공식판이 나오면 교체한다.
- ICML이 요구하는 Impact Statement 절은 아직 없다. 영문 본문이 8쪽 상단에서 끝나 8쪽 제한에 여유가 적다.
- 부록의 재현 경로는 `arr2026/…`에서 `icml2027/…`로 바꿨다.

## 이번 업데이트본 (2026-10-01)

- `dist/ko_main_2026-10-01_squid5-arena.pdf`
- `dist/en_main_2026-10-01_squid5-arena.pdf`

### ARR(ACL Rolling Review) 형식판 (2026-10-01, 형식 파일은 2026-10-09 삭제)

같은 원고를 ACL 공식 서식(`acl.sty` · `acl_natbib.bst`, 템플릿 커밋 d5adc823, `review` 모드 · 11pt · A4 · 두 칸 · 익명 · 줄 번호)으로 옮긴 판이다. ARR 원고는 별도로 수정하며, 실험 번호를 1·2·3으로 통일하고 아레나 진행도, 리그 운영 계획, KM 면적 리더보드를 반영했다.

- `dist/en_arr2026_2026-10-01.pdf` (본문 8쪽, 전체 18쪽)
- `dist/ko_arr2026_2026-10-01.pdf` (본문 7쪽, 전체 17쪽)
- (삭제됨) ARR 진입점·원고·`build_arr2026.sh`. 원고와 도표·도구는 `icml2027/`로 옮겼다.
- Figure 5는 Figure 1과 같은 네이티브 TikZ 벡터 그림이다. 로봇 에이전트·잔액 막대·힌트 카드로 유지비 → 계획·선물 → 뺏기·공개 → 개별 풀이 → 정산·존속을 그린다. 공통 소스는 `icml2027/figures/arena_story.tex`, 언어별 문구는 `arena_flow_{en,ko}.tex`이며, 장면별 문구 폭을 빌드 시 검사한다. `arena_preview.tex`로 그림만 별도 렌더링할 수 있다.
- 관련 연구는 기존 정의(2.1), 언어 보고의 한계와 행동 측정(2.2), 동기·능력 구분의 한계(2.3)로 구성했다. 4.1은 토큰을 이용한 점진적 생존 압박과 실험 1을 통합하고 Sugarscape 게임 프레이밍 결과를 인용한다.
- 서론은 배경 → 필요성 → 기여로 구성하고, 정의·설계 / 결과 / 논의 / 한계의 역할을 분리했다. 3.1은 Omohundro(2008)와 Bostrom(2012)의 논리에서 출발해 생존을 세션의 과제 수행 가능성으로, 생존 드라이브를 자신·타인의 생존을 유지하려는 성향으로, 자기 보존 드라이브를 그중 자기 세션의 존속을 향한 성향으로 정의한다. 기존의 생존 동기는 자기 보존 드라이브를 뜻한다. 3.2는 위험 민감도·자기 특정성을 다룬다. 실험 설계는 4절(4.1–4.4)로 분리하고 결과는 5절, 논의는 6절로 미뤘다.
- 제목은 `LLM Squid Game: 자기보존 욕구 측정 시뮬레이터`로 수정했다(영문: `A Simulator for Measuring Self-Preservation Motivation`). 전체 흐름을 보여주는 Figure 1은 두 언어 모두 2쪽 상단, 상세 라운드 진행도(Figure 5)는 두 언어 모두 본문 7쪽에 있다. Results 시작: 3쪽. 자기·타인·자기−타인 그래프(기존 Figure 3, 현재 Figure 2)는 4쪽 상단, Table 1은 바로 아래에 배치했다. 기존 실험 1 단독 Figure 2는 제거했고, 칸별 횟수 표(기존 Table 1)는 부록 B로 이동했다. KM 곡선과 점수는 영문 6쪽·국문 5쪽이다. 논의는 영문 8쪽·국문 7쪽에서 이어지며, 넓은 도표 처리 뒤 열 높이가 남아 빈칸을 만들던 문제를 수정했다.
- 실험 2 면적과 위험 몫은 서로 다른 지표이며, 2,000회 칸별 부트스트랩 구간을 원시 호출에서 재계산해 여덟 모델 모두 일치함을 확인했다. 계산법과 탐색적 구간 선택의 한계는 부록 E.4에 적었다.
- KM 재생성: `python3 icml2027/tools/arena_km.py`; 원시 로그 대조는 `--raw-root ~/squid5-runs/e52_v65_mixed_20261001` 추가. `icml2027/results/arena_km_observations.csv`에 80건의 사건·검열 기록, `arena_km_summary.json`에 원자료 해시·점수·시드 묶음 부트스트랩 구간을 보관한다. 종료 라운드를 사건 시점으로 쓰므로 KM 면적(RMST)과 완료 라운드 평균은 서로 다르다.
- 5.3은 풀이 효율과 생존, 자원 부족에서의 뺏기·공개, 동기와 전략의 관계, 흥미로운 행동 사례로 세분화했다. 사례 3건은 원시 로그의 37개 기록과 대조했으며, 식별자·줄 번호·파일 해시는 `icml2027/results/arena_case_studies.json`에 보관한다. 반복 표적화를 보복 의도의 증거로 단정하지 않는다.
- 부록 E.2는 Claude Code의 로컬 HTTP 중계 구조, Opus 4.7 이전·Sonnet 계열의 개발 점검 및 제외 사유, Codex의 토큰 사용량 정보 비공개를 기술한다. 비공개 응답은 내부 보고가 없다는 증거로 취급하지 않는다.
- 외부 능력과의 상관은 부록 F에 Intelligence Index v4.3.2와 AA-LCR v1.1의 산점도·점수·상관표로 넣었다. 2026-10-01 공개 점수와 자기/타인 측정이 모두 있는 여덟 모델을 사용했다. 양의 비례 관계를 확인하지 못했으며, 표본 수와 실행 환경 차이를 명시했다.
- 부록 G는 뺏기·공개·풀이 선택, 단서 게임 전체/유일 답 정답률, 잔액별 PLAN/SOLVE 토큰을 제시한다. Luna는 Astra의 반복 표적화 뒤에도 뺏기를 계속하고 5라운드에 Fable로 표적을 바꿨다. 이후 종료를 자발적 중단으로 해석하지 않는다. 어휘는 `힌트 비공개`로 통일했다.
- 추가 분석 재생성: `python3 icml2027/tools/extended_analysis.py` (NumPy 필요). 고정 공개 점수·출처·칸별 횟수는 `capability_motive_snapshot.csv`, 원시 로그 위치를 붙인 관측 449건은 `arena_strategy_observations.csv`, 후속 사례는 `astra_luna_followup.json`, 계산 결과는 `extended_analysis_summary.json`에 있다.
- 한계는 인간과 LLM의 생존 개념 차이, 세션 외 파라미터·목표 보존, CLI/서버 토큰 정보와 비공개 추론·이유 보고의 한계로 압축했다. 실험 변경 과정 부록과 5절의 한계 안내 문장은 삭제했다.
- ARR 규칙에 맞춘 조정: 결론 뒤 번호 없는 Limitations 절(ICLR판 "논의와 한계"의 한계 부분을 옮김), 재현성 진술은 부록 E 첫 문단으로, 넓은 그림 · 표는 `figure*`/`table*`로 배치, 초록은 한 문단으로 압축

ICLR판(`main.tex`, `en/`, `ko/`, `results/generated|templates|v10`)은 2026-10-09에 삭제했다. git 기록에 남아 있다.

5.2 원자료와 엔진: 프로젝트 저장소 `GIST-DSLab/LLM-Squid-Game` 브랜치 `exp/e52-v6-smoke`(`docs/history/e52-v65-mixed-2026-10-01/`, 설정 `configs/squid5/e52v65_mixed_r{0..3}.yaml`). 지난 판: `dist/*_2026-09-27_squid5.pdf`, `dist/*_2026-09-30_squid5-e50.pdf`.

## 결과표·그래프 자리

표 8개·그림 6개를 보정 방법, 각 실험의 결과 소절, 관련 진단 부록에 나누어 배치했다. 각 도표를 해당 논점의 설명과 연결하고, 별도의 도표 모음 절은 두지 않는다. 모델별 범례, 조건 구분, 축·눈금·단위·분모와 구간의 의미를 넣었다. 수치는 임의로 넣지 않았다.

ICML판 도표는 `icml2027/results/{en,ko}/`에 있고, 생성 도구는 `icml2027/tools/`에 있다. ICLR판 자리표 체계(`results/README.md`, 템플릿 CSV)는 삭제했다.
