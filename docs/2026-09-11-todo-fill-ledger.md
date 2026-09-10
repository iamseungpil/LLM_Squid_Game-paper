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
