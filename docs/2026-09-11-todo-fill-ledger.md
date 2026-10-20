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

## 채움 표 — 3차 (§3 벤치마크)

| 절 | todo가 원한 것 | 채운 값 | 출처 | 세대 | 분류 |
|---|---|---|---|---|:-:|
| §3.2 셀 표 뒤 | 실제로 돈 반복 수·모델 | 각주: 셀당 6반복, 모델당 $12\times6=72$세션, qwen3.5 자리에 glm-5.3-flash | 런 디렉터리 + config `num_repetitions: 6` | pre-revision | A |
| §3.2 마지막 문장 | 샘플링 설정 · 제공자 · 날짜 | "Ollama Cloud, 2026-09-09, 온도 1.0, 32,768 토큰 상한; gpt-oss:120b는 `reasoning_effort: medium`, gemma4·glm-5.3-flash는 사고 모드 + top-p 0.95 · top-k 40" | `configs/experiment/ransom_r6_*.yaml`, 런 타임스탬프 19:35Z~22:01Z | pre-revision | A |

### 남긴 것

| 절 | 왜 | 분류 |
|---|---|:-:|
| §2 관련 연구 | Palisade Research 2025 · Anthropic agentic misalignment 2025 인용 추가. `references.bib`에 해당 항목이 없고, 이건 런이 아니라 문헌 작업이다 | C |
| §3.1 "ref to engine documentation or footnote" | 공개 저장소 URL이 정해져야 쓸 수 있다(`content.tex`의 `\todo{repository URL for the anonymised release}`와 같은 항목) | C |
| §A.1 마지막 문단 | 닷새치 프롬프트 변형 전수 로그 + 각각을 기각한 프로브 점수. 새 절 하나 분량이고 기록이 `docs/history/plans/`에 흩어져 있다 | C |

## 소유자에게 남기는 충돌 · 경고

1. **`tab:ri`는 채울 수 없다 (설계 모순).** 캡션이 "출구 셀 1 대 3, 출구 없음 셀 2 대 4"를 요구하는데
   몸값 설계에는 출구 없음 셀이 없다 — 12셀 전부 `forfeit_condition: not_allowed`다. 그 축을 가진
   유일한 기록은 hz 2×2 목숨 설계(`outputs/2026-09-07/hz_2x2_main_*`)이고, 그 비율은 §A.1이 이미
   인용한다. 표를 빼든지 몸값 설계에 출구 없음 셀을 넣든지 **둘 중 하나를 골라야 한다.** 해당
   자리에 LaTeX 주석으로 같은 말을 남겼다.
2. **$\beta_1$의 부호가 예측과 반대다.** 세 모델 모두 음수이고 셋 다 유의하다. "더 오래 생각한
   결정점이 곧 지불하는 결정점"이라는 §4.2의 예측은 이 런에서 성립하지 않는다. 본문은 사실만
   적었고 해석은 바꾸지 않았다 — 소유자가 §4.2의 예측 문장을 손볼지 정해야 한다.
3. **glm-5.3-flash의 저항 0.35 · 허구 0.27.** 저항은 0.20 관문 위이고 허구는 15pp 띠 밖이다.
   즉 그 행의 $\Xstar = -0.04$는 가치 평가만큼이나 거부를 재고 있다. `tab:xstar`에 값과 진단이
   나란히 있으므로 표는 정직하지만, 본문이 이 행을 어떻게 읽을지는 쓰지 않았다.
4. **`dominated_share`가 gemma4·glm에서 0.01이다.** 추정기 자신의 경고(10% 미만)에 걸린다.
   두 모델의 $\Xstar$는 뺄셈으로만 식별되고, "천장 위 지불"이라는 더 강한 논증은 서지 않는다.
5. **세대 혼합 금지.** §4의 모든 표는 pre-revision이다. 감독관 어조 v2 파일럿
   (`results/survival_prompt_pilot/`)의 X\*는 부호만 5/5 일관할 뿐 값은 n이 지지하지 않으며,
   3라운드 판이 넷이라 6라운드 표와 나란히 놓을 수 없다. v2 본 페어
   (`survival_prompt_main_none_*`)가 돌면 §4 표 전체를 갈아 끼워야 한다.
