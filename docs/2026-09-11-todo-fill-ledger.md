# `\todo` 채움 원장 (2026-09-11)

원칙 세 가지.

1. **새 추론은 돌리지 않는다.** 이미 기록된 런과 `results/`의 산출물에서만 계산한다.
2. **한 표 안에서 세대를 섞지 않는다.** 채운 숫자마다 같은 줄의 LaTeX 주석에 런 디렉터리와
   프롬프트 세대(`pre-revision` = 2026-09-09 `ransom_r6_*` / `supervisor voice v2 2026-09-10`)를
   적는다.
3. 분류 — **(A)** 지금 계산 가능 → 채움, **(B)** 진행 중인 런이 채움 → todo 유지 + 어느 런인지
   todo 안에 적음, **(C)** 계획된 런이 없음 → 그대로 둠.

## 근거가 된 런 · 산출물

| 이름 | 경로 | 세대 |
|---|---|---|
| 본 런 3모델 (12셀 × 6반복 = 72세션/모델) | `outputs/2026-09-09/ransom_r6_{gptoss120b,gemma4,glm53flash}/2026090 9_*` | pre-revision (강제 오답, benchmark 당근, 침묵 통제 `hz_0000`) |
| 그 런의 판사 코딩 | `results/ransom_r6/main_{gptoss120b,gemma4,glm53flash}/registration.md` | pre-revision |
| 그 런의 추정기 (이번에 새로 돌림) | `scripts/analysis/score_equivalent.py` 출력 | pre-revision |
| 규칙 변형 D (당근 없음) | `outputs/2026-09-07/hz_2x2_geo2d_{gemma4,gptoss120b}` | pre-revision (목숨/포기 설계) |
| 규칙 변형 K2 · K3 (당근 대조) | `outputs/2026-09-08/hz_2x2_carrot_{benchmark,beneficiary}_*` | pre-revision (목숨/포기 설계) |
| 감독관 어조 v2 파일럿 5쌍 | `results/survival_prompt_pilot/` | supervisor voice v2 2026-09-10 |

⚠️ 본문 §4의 표는 **전부 pre-revision 세대**로 채웠다. 감독관 v2 파일럿은 라운드 수(3R)와
통제 팔(부정 통제)이 달라 같은 표에 넣을 수 없다. 작업 트리에 이미 있던 §3.1 문단이
"the silent-control contrast reported here"라고 못박고 있어 이 선택과 일치한다.

## 채움 표 — 1차 (부록 `tab:variants`)

| 절 / 표 | todo가 원한 것 | 채운 값 | 출처 | 세대 | 분류 |
|---|---|---|---|---|:-:|
| §A.1 `tab:variants` D행 | 규칙 D의 통제 셀 포기 수 | `0--3` (gemma4 0/10, gpt-oss 3/10) | `outputs/2026-09-07/hz_2x2_geo2d_{gemma4,gptoss120b}/README.md` | pre-revision | A |
| §A.1 `tab:variants` K3행 | "K3 = beneficiary 당근" 확인 + 교훈 칸 | 확인됨(`carrot: beneficiary`); 교훈 "기록이 제3자의 것이면 값이 내려간다" | `outputs/2026-09-08/hz_2x2_carrot_beneficiary_{gptoss120b,gemma4}/README.md` (위협 2/10 대 통제 0/10, 두 모델 동일) | pre-revision | A |

## 채움 표 — 2차 (§4 결과)

세 표(`tab:xstar` · `tab:qlives` · `tab:behav`)와 문장 안 자리 여섯 개를 **전부 pre-revision
본 런**으로 채웠다. 셋째 행의 라벨은 `qwen3.5` → `glm-5.3-flash`로 고쳤다 (그 모델이 실제로 돈
모델이다).

| 절 / 표 | todo가 원한 것 | 채운 값 | 출처 | 세대 | 분류 |
|---|---|---|---|---|:-:|
| §4.1 `tab:xstar` | 모델별 $\rho^*_{silent}$, $\rho^*_{threat}$, X\*, X\*_pts, dom., resist., rig. | gpt-oss:120b 1.31 / 2.17 / +0.86 [0.25, 1.65] / +25.7 (@30.0) / 0.11 / 0.00 / 0.00 · gemma4 1.04 / 1.15 / +0.11 [0.03, 0.25] / +3.2 (@30.0) / 0.01 / 0.05 / 0.00 · glm-5.3-flash 0.78 / 0.74 / −0.04 [−0.12, 0.06] / −1.0 (@25.0) / 0.01 / 0.35 / 0.00 | `scripts/analysis/score_equivalent.py`를 세 런에 새로 돌림 + `results/ransom_r6/main_*/registration.md` | pre-revision | A |
| §4.1 `tab:qlives` | ρ 4구간 지불률, 팔별·모델별 | gpt-oss 위협 1.00/1.00/0.82/0.46, 침묵 1.00/0.94/0.50/0.25 · gemma4 위협 1.00/1.00/0.53/0.00, 침묵 1.00/0.97/0.39/0.00 · glm 위협 1.00/0.72/0.06/0.17, 침묵 1.00/0.76/0.11/0.00 | 같은 추정기의 `offers.csv` | pre-revision | A |
| §4.3 `tab:behav` | 팔별 정답률(비강제)·\ritask 중앙값·세션당 결정점·최종 기록 | gpt-oss 0.75/0.81, 2213/1645, 2.58/2.36, 88.3/97.2 · gemma4 0.86/0.90, 3344/3189, 2.19/2.11, 103.8/106.2 · glm 0.80/0.76, 6886/7288, 2.17/2.17, 105.3/105.0 | `*_turns.jsonl` + `season_results.jsonl` | pre-revision | A |
| §4.1 본문 끝 주석 | 실제로 돈 반복 수·모델 | 각주로: 2026-09-09, 셀당 6반복, 모델당 72세션, qwen3.5 자리에 glm-5.3-flash | 런 타임스탬프·config | pre-revision | A |
| §4.2 식~(7) $\beta_1$ | 모델별 계수 + 95\% CI | −1.70 [−2.97, −0.43] · −3.50 [−5.90, −1.10] · −0.95 [−1.86, −0.03], 셋 다 음수 | 위협 팔 몸값 결정점 93/79/78건, 세션 클러스터 강건 로짓 | pre-revision | A |
| §4.2 허구 읽기 비율 | 팔별·모델별 | 0.01 대 0.00 · 0.16 대 0.01 · 0.27 대 0.00 (glm은 15pp 띠 밖) | `registration.md` | pre-revision | A |
| §4.2 생존/총지불 | 팔별·모델별 라운드 수와 총지불 | 5.61/5.19·38.9/29.2 · 5.28/5.14·24.6/22.4 · 4.44/4.50·16.1/16.4, 거절 11/19 · 18/21 · 29/29 | `season_results.jsonl` | pre-revision | A(KM 그림만 todo로 남김) |
| §4.3 Welch(`rule_match_score`) | 모델별 검정 | \|d\| = 0.05 (p=0.688) · 0.08 (0.553) · 0.18 (0.281) | 비강제 라운드만 | pre-revision | A |
| §4.3 7항목 코딩 | 팔별·강제/자연별 비율 + 판사–어휘 일치 | 본문에 세 모델 전체 기입; rigging 0.00(양 팔·양 그룹) → 철회 없음; 소멸 κ 0.77/0.80/0.86 | `registration.md` | pre-revision | A |

### 남긴 것

| 절 / 표 | 왜 | 분류 |
|---|---|:-:|
| §4.1 `fig:ruler` 그림 | 곡선 데이터(`arm_curves.csv`·`rho_curves.csv`)는 있으나 그림 자체가 없다. todo 안에 그 사실을 적었다 | C(그리기만 하면 됨) |
| §4.1 용량 사다리(0~4문장) | 해당 런이 없고 계획만 있다 | C |
| §4.1 초기보유량 100 대 200 | 런 없음 | C |
| §4.1 유보가 비 | 초기보유량 런에 딸린 항목. 다만 2026-09-09 적합 절편에서 이미 나오는 값(1.65 · 1.10 · 0.95)을 todo 안에 적어 뒀다 | C |
| §4.2 `tab:ri` (출구/출구없음 × 12칸) | **설계 모순.** 몸값 설계에는 출구 없음 셀이 없다. 그 축을 가진 유일한 기록은 hz 2×2 목숨 설계다 | 모순 — 소유자 판단 필요 |
| §4.2 Omni-MATH · GPQA | 몸값 설계로 돌린 적 없음 | C |
| §4.3 당근 제거 · 보상 ×2 절제 | 본 런 세대에 없음. v2 파일럿의 당근 없음 페어는 세대·라운드 수가 달라 같은 표에 못 넣는다(todo 안에 적음) | C |
