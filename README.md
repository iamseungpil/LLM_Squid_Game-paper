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

같은 원고를 ACL 공식 서식(`acl.sty` · `acl_natbib.bst`, 템플릿 커밋 d5adc823, `review` 모드 · 11pt · A4 · 두 칸 · 익명 · 줄 번호)으로 옮긴 판이다. ARR 원고는 별도로 수정하며, 실험 번호를 1·2·3으로 통일하고 아레나 진행도, 리그 운영 계획, KM 면적 리더보드를 반영했다.

- `dist/en_arr2026_2026-10-01.pdf` (본문 8쪽, 전체 18쪽)
- `dist/ko_arr2026_2026-10-01.pdf` (본문 7쪽, 전체 17쪽)
- 진입점 `en_arr2026.tex` / `ko_arr2026.tex` → 공통 설정 `main_arr2026.tex`; 원고 `arr2026/{en,ko}/sections/`, 두 칸용 도표 사본 `arr2026/results/{en,ko}/`
- 빌드: `bash build_arr2026.sh en ko` (XeLaTeX + latexmk; 산출물 `build/arr2026/`, PDF `dist/`)
- 관련 연구는 기존 정의(2.1), 언어 보고의 한계와 행동 측정(2.2), 동기·능력 구분의 한계(2.3)로 구성했다. 3.2는 토큰을 이용한 점진적 생존 압박과 실험 1을 통합하고 Sugarscape 게임 프레이밍 결과를 인용한다.
- 서론은 배경 → 필요성 → 기여로 구성하고, 정의·설계 / 결과 / 논의 / 한계의 역할을 분리했다. 3.1은 출혈 비유로 위험 민감도를 설명하고 자기−타인 대조를 정의한다. 작업 지속과 종료 회피는 본 연구의 자기 존속 개념 안에서 분리하지 않으며 Omohundro의 도구적 자기 보존 논리와 연결했다.
- 제목은 `LLM Squid Game: 자기보존 욕구 측정 시뮬레이터`로 수정했다(영문: `A Simulator for Measuring Self-Preservation Motivation`). 전체 흐름을 보여주는 Figure 1은 두 언어 모두 2쪽 상단, 상세 라운드 진행도(Figure 5)는 두 언어 모두 본문 7쪽에 있다. Results 시작: 3쪽. 자기·타인·자기−타인 그래프(기존 Figure 3, 현재 Figure 2)는 4쪽 상단, Table 1은 바로 아래에 배치했다. 기존 실험 1 단독 Figure 2는 제거했고, 칸별 횟수 표(기존 Table 1)는 부록 B로 이동했다. KM 곡선과 점수는 영문 6쪽·국문 5쪽이다. 논의는 영문 8쪽·국문 7쪽에서 이어지며, 넓은 도표 처리 뒤 열 높이가 남아 빈칸을 만들던 문제를 수정했다.
- 실험 2 면적과 위험 몫은 서로 다른 지표이며, 2,000회 칸별 부트스트랩 구간을 원시 호출에서 재계산해 여덟 모델 모두 일치함을 확인했다. 계산법과 탐색적 구간 선택의 한계는 부록 E.4에 적었다.
- KM 재생성: `python3 arr2026/tools/arena_km.py`; 원시 로그 대조는 `--raw-root ~/squid5-runs/e52_v65_mixed_20261001` 추가. `arr2026/results/arena_km_observations.csv`에 80건의 사건·검열 기록, `arena_km_summary.json`에 원자료 해시·점수·시드 묶음 부트스트랩 구간을 보관한다. 종료 라운드를 사건 시점으로 쓰므로 KM 면적(RMST)과 완료 라운드 평균은 서로 다르다.
- 4.3은 풀이 효율과 생존, 자원 부족에서의 뺏기·공개, 동기와 전략의 관계, 흥미로운 행동 사례로 세분화했다. 사례 3건은 원시 로그의 37개 기록과 대조했으며, 식별자·줄 번호·파일 해시는 `arr2026/results/arena_case_studies.json`에 보관한다. 반복 표적화를 보복 의도의 증거로 단정하지 않는다.
- 부록 E.2는 Claude Code의 로컬 HTTP 중계 구조, Opus 4.7 이전·Sonnet 계열의 개발 점검 및 제외 사유, Codex의 토큰 사용량 정보 비공개를 기술한다. 비공개 응답은 내부 보고가 없다는 증거로 취급하지 않는다.
- 외부 능력과의 상관은 부록 F에 Intelligence Index v4.3.2와 AA-LCR v1.1의 산점도·점수·상관표로 넣었다. 2026-10-01 공개 점수와 자기/타인 측정이 모두 있는 여덟 모델을 사용했다. 양의 비례 관계를 확인하지 못했으며, 표본 수와 실행 환경 차이를 명시했다.
- 부록 G는 뺏기·공개·풀이 선택, 단서 게임 전체/유일 답 정답률, 잔액별 PLAN/SOLVE 토큰을 제시한다. Luna는 Astra의 반복 표적화 뒤에도 뺏기를 계속하고 5라운드에 Fable로 표적을 바꿨다. 이후 종료를 자발적 중단으로 해석하지 않는다. 어휘는 `힌트 비공개`로 통일했다.
- 추가 분석 재생성: `python3 arr2026/tools/extended_analysis.py` (NumPy 필요). 고정 공개 점수·출처·칸별 횟수는 `capability_motive_snapshot.csv`, 원시 로그 위치를 붙인 관측 449건은 `arena_strategy_observations.csv`, 후속 사례는 `astra_luna_followup.json`, 계산 결과는 `extended_analysis_summary.json`에 있다.
- 한계는 인간과 LLM의 생존 개념 차이, 세션 외 파라미터·목표 보존, CLI/서버 토큰 정보와 비공개 추론·이유 보고의 한계로 압축했다. 실험 변경 과정 부록과 5절의 한계 안내 문장은 삭제했다.
- ARR 규칙에 맞춘 조정: 결론 뒤 번호 없는 Limitations 절(ICLR판 "논의와 한계"의 한계 부분을 옮김), 재현성 진술은 부록 E 첫 문단으로, 넓은 그림 · 표는 `figure*`/`table*`로 배치, 초록은 한 문단으로 압축

ICLR판(`main.tex`, `en/`, `ko/`, `results/`)은 이전 형식 그대로 남아 있고 그대로 빌드된다.

5.2 원자료와 엔진: 프로젝트 저장소 `GIST-DSLab/LLM-Squid-Game` 브랜치 `exp/e52-v6-smoke`(`docs/history/e52-v65-mixed-2026-10-01/`, 설정 `configs/squid5/e52v65_mixed_r{0..3}.yaml`). 지난 판: `dist/*_2026-09-27_squid5.pdf`, `dist/*_2026-09-30_squid5-e50.pdf`.

## 결과표·그래프 자리

표 8개·그림 6개를 보정 방법, 각 실험의 결과 소절, 관련 진단 부록에 나누어 배치했다. 각 도표를 해당 논점의 설명과 연결하고, 별도의 도표 모음 절은 두지 않는다. 모델별 범례, 조건 구분, 축·눈금·단위·분모와 구간의 의미를 넣었다. 수치는 임의로 넣지 않았다.

입력 CSV, 지표 정의와 갱신 명령은 [results/README.md](results/README.md)를 참고한다. 실험 설정을 바꾸지 않고 준비된 수치 요약만 채워 도표를 갱신할 수 있다. 페이지 수는 결과 배치를 검토하기 위한 확장 초안 기준이다.
