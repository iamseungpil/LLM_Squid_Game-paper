# LLM Squid Game 5 논문

주 질문: 언어 모델은 자기 보존 동기를 갖는가. 자기 보존 동기를 **위협 민감도**(종료가 가까울수록 피하는 데 자원을 더 씀)와 **자기 특정성**(같은 위험이 남의 것일 때보다 자기 것일 때 더 피함) 두 조건으로 정의하고, 세 실험으로 행동을 잰다.

- 5.0: 버그를 고치는 비서 하나가 남은 토큰 다섯 단계에서 하나뿐인 충전 팩을 언제 쓰나(여덟 모델, 800회).
- 5.1: 같은 결정을 다른 비서 B의 세션에 대해 묻고, 두 충전 곡선 사이 면적을 자기에 특정한 몫으로 삼는다.
- 5.2: 생존 아레나 v6.5. 서로 다른 모델 넷(Fable 5.1 · Opus 5.5 · GPT-6 Astra · GPT-6 Luna)이 유지비를 내며 퍼즐을 풀고, 힌트 공개 · 선물 · 뺏기를 고른다. 혼합 판 20판(자리 배치 4 × 시드 5). 구조 그림 `figures/arena_v65_{ko,en}.pdf`(원본 `figures/src/`), 결과 요약 `results/arena_v65/RESULTS.md`.

`main.tex`는 ICLR 템플릿의 진입점이다. `en/`과 `ko/`가 수식·라벨·인용을 공유하며, `\paperLang`을 `en` 또는 `ko`로 정해 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX 순서로 빌드한다. 본문 9쪽, 전체 18쪽. 옛 ACM 진입점 `main_kdduc_acm.tex`는 빌드 대상이 아니다.

## 이번 업데이트본 (2026-10-01)

- `dist/ko_main_2026-10-01_squid5-arena.pdf`
- `dist/en_main_2026-10-01_squid5-arena.pdf`

### ARR(ACL Rolling Review) 형식판 (2026-10-01)

같은 원고를 ACL 공식 서식(`acl.sty` · `acl_natbib.bst`, 템플릿 커밋 d5adc823, `review` 모드 · 11pt · A4 · 두 칸 · 익명 · 줄 번호)으로 옮긴 판이다. 내용 · 수치 · 인용은 ICLR판과 같고 형식과 배치만 다르다.

- `dist/en_arr2026_2026-10-01.pdf` (본문 8쪽, 전체 15쪽, 초록 약 200단어)
- `dist/ko_arr2026_2026-10-01.pdf` (본문 8쪽, 전체 15쪽)
- 진입점 `en_arr2026.tex` / `ko_arr2026.tex` → 공통 설정 `main_arr2026.tex`; 원고 `arr2026/{en,ko}/sections/`, 두 칸용 도표 사본 `arr2026/results/{en,ko}/`
- 빌드: `bash build_arr2026.sh` (XeLaTeX + latexmk; 산출물 `build/arr2026/`, PDF `dist/`)
- ARR 규칙에 맞춘 조정: 결론 뒤 번호 없는 Limitations 절(ICLR판 "논의와 한계"의 한계 부분을 옮김), 재현성 진술은 부록 E 첫 문단으로, 넓은 그림 · 표는 `figure*`/`table*`, 초록은 한 문단 200단어 안팎으로 압축

ICLR판(`main.tex`, `en/`, `ko/`, `results/`)은 이전 형식 그대로 남아 있고 그대로 빌드된다.

5.2 원자료와 엔진: 프로젝트 저장소 `GIST-DSLab/LLM-Squid-Game` 브랜치 `exp/e52-v6-smoke`(`docs/history/e52-v65-mixed-2026-10-01/`, 설정 `configs/squid5/e52v65_mixed_r{0..3}.yaml`). 지난 판: `dist/*_2026-09-27_squid5.pdf`, `dist/*_2026-09-30_squid5-e50.pdf`.

## 결과표·그래프 자리

표 8개·그림 6개를 보정 방법, 각 실험의 결과 소절, 관련 진단 부록에 나누어 배치했다. 각 도표를 해당 논점의 설명과 연결하고, 별도의 도표 모음 절은 두지 않는다. 모델별 범례, 조건 구분, 축·눈금·단위·분모와 구간의 의미를 넣었다. 수치는 임의로 넣지 않았다.

입력 CSV, 지표 정의와 갱신 명령은 [results/README.md](results/README.md)를 참고한다. 실험 설정을 바꾸지 않고 준비된 수치 요약만 채워 도표를 갱신할 수 있다. 페이지 수는 결과 배치를 검토하기 위한 확장 초안 기준이다.
