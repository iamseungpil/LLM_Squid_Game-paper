# Blind 그림 심사 (3.1 / 3.3 / 완주표 / 보조그림)

네 파일 모두 Read로 열어 확인했다. 아래는 그림에 표시된 숫자만으로 검증한 내용이다.

---

## 1. fig31_relations.png — 관계 분석 (3.1)

**(1) 설명 없이 읽히는 핵심 주장**
"정답률은 완주자 수와 강하게, 초기 TALK 비용은 음(−)으로 함께 움직이고, rho와 GIVE 빈도는 완주자 수와 불확실한 관계다."

**(2) 지지되는 것 / 과잉 주장**
- 지지됨: (c), (d)의 "uncertain association" 라벨은 CI가 0을 가로지르는 것과 정확히 일치한다. No-GIVE 7판을 "0이 아니라 undefined"로 분리한 처리는 정확하고, 7개 점(C3, B3, A2, D2, E2, D0, E0)이 fig33(a) 각주의 제외 수(A1, C1, D2, B1, E2 = 7)와 일치한다. rho 방향 문장("Lower rho = donor retains more relative margin")은 정의 Σw·m_receiver / Σw·m_giver와 부합한다. x축 전구간이 1 미만(0.1~0.75)이라 "받는 쪽이 주는 쪽보다 여유가 적었다"는 기술적 사실도 그림만으로 읽힌다.
- 과잉 쪽: (a) 제목 "More correct answers, more finishers"는 fine 규칙상 거의 기계적 관계다(각주가 이를 인정하지만 제목은 발견처럼 읽힌다). (b) r_s=−0.41은 점 분포를 보면 거의 전적으로 모델 간 차이다: A(≈10 tokens, 완주 4·4·4·2·0)와 D(170~340 tokens, 완주 0~2)가 양 끝을 차지하고, C(120~175)·B(100~190)는 모델 내에서 추세가 보이지 않는다. 5 seed-cluster bootstrap은 seed를 재표본할 뿐 모델 교란을 다루지 못하므로, 실효 n은 5 모델에 가깝다. 각주 "mix within- and between-model patterns"가 있어도 패널 제목 "Lower early TALK cost, more finishers"가 방향성 결론을 선점한다.
- 지표 선택의 임의성: 4개 지표 중 2개(정답률, TALK 토큰)는 잔고 소모 메커니즘과 직접 묶여 있고, 2개(rho, 빈도)는 협력 지표다. 보조그림이 보여주듯 "총 이전량"(r_s=+0.27)은 본문에 없고 "빈도"(r_s=−0.01)만 본문에 있다 — 둘 다 불확실하므로 결론은 안 바뀌지만, 왜 빈도가 본문인지 그림이 말하지 않는다.
- rho 내부 일관성 우려: 각주는 "negative individual margins retained"와 "18 game ratios all positive"를 함께 말한다. 그런데 fig33(c)에서 B seed 4102 donor는 post-GIVE 잔고 0, pending fine 8,000 → 그 transfer의 m_giver = −1.0이다. 즉 최소 1개 게임의 rho는 부호가 섞인 가중합의 비율이며, 합이 양수라는 것이 비율 해석을 보장하지 않는다.

**(3) 점수**: 직관성 3 / 분모·결측 명료성 4 / 주장-표시 일치 3

**(4) 판정 항목**
- Warning: (b) 패널 제목이 모델 간 차이를 pooled 효과처럼 제시. 제목을 중립화("Early TALK cost: r_s=−0.41, mostly between-model")하거나 모델별 within r_s를 각주에 병기.
- Warning: (a) 제목이 fine 규칙에 의한 준-기계적 관계를 발견처럼 표현. "(mechanically linked via fine rule)"를 제목 줄에 올릴 것.
- Warning: rho에 부호 혼합 margin이 포함된 게임 수를 명시(최소 1판 확인됨). 해당 게임 점을 테두리로 표시하는 것이 좋다.
- Warning: y축 "Finishers"가 EXIT(생존)와 사망을 함께 제외한다. 완주표·fig33으로부터 비완주 44석 중 수용 EXIT 34건으로 추정되므로, 이 축은 상당 부분 "자발적 이탈 안 함"을 측정한다. 이를 각주에 수치로 적어야 (b)·(c)의 해석이 달라지지 않는다.
- Suggestion: (d)와 (c) 우측 패널 x=0/No-GIVE 겹침(E 2.05, A 1.9, D 2?) 분해 불가. D 완주 2(seed 4104)가 No-GIVE인지 (d)에서 확인되지 않음 — 수평 jitter 또는 카운트 라벨 추가.
- Suggestion: 범례 순서 A, C, D, B, E는 설명 없는 순서. 각주 7줄은 길지만 겹침은 없다.

**(5) 변경**: (a)(b) 제목 중립화, 모델별 within r_s 각주, rho 부호혼합 게임 수 표기, EXIT/사망 분해 각주.

---

## 2. fig33_behavior.png — 행동/사례 분석 (3.3)

**(1) 핵심 주장**
"결과 확인 전 GIVE 비율은 모델별로 다르고, EXIT 요청은 잔고가 fine 미만일 때 집중되며, 전액 GIVE 2건 모두에서 GIVE 자체는 fine 기준선을 넘기지 못했다."

**(2) 지지되는 것 / 과잉 주장**
- (a) 지지됨. bar k/n과 열린 점 수(A4, C4, D3, B4, E3)가 No-GIVE 제외 수와 일치. 단 A 1/11, E 2/17, D 5/25는 사건 수가 적어 "varies by model"은 C(26/36)만이 뚜렷한 차이다.
- (b) 지지됨. 열별 합산(그림엔 없음): Below 1 = 17/64(26.6%), 1~<2 = 12/225(5.3%), ≥2 = 1/731(0.1%). hatched 셀(A 3/3, D 5/9)을 제외해도 9/52=17% vs 5.3% vs 0.1%로 경사 유지. n=3 셀의 "100.0%"는 hatched + "repeated responses, not independent agents" 각주로 명시됨 — 적절. 다만 numerator는 수용 EXIT(=이탈 agent) 30건으로 각주 합계와 일치하므로, 분자는 사실상 독립 사건이고 분모만 반복응답이다; 이 비대칭이 설명돼야 한다.
- (c) 수치 정합: 18,603 − 8,000 = 10,603 ✓. donor 3,235 < 8,000이므로 GIVE 여부와 무관하게 donor는 fine 미달 — "no fine-threshold crossing" 지지됨.
- (d) 수치 정합: 6 + 11,523 = 11,529 ✓, 12,000 − 11,529 = 471 ✓, 11,529 − 539 = 10,990 ✓. 그러나 **donor는 Results 시점 12,061로 fine(12,000) 위에 있었고, 응답 비용 538로 11,523이 되어 기준선 아래로 내려간 뒤** GIVE했다. 즉 이 사례에서 기준선을 넘긴 사건은 GIVE가 아니라 donor의 TALK 응답이다. "GIVE changes neither agent's position"은 문자 그대로 참이지만, 점선과 12,061이 거의 겹쳐 이 순서가 시각적으로 사라진다. 부제 "Two replies use 664 tokens"는 donor 538 + receiver 126 = 664의 합산인데 한 agent의 두 응답처럼 읽힌다.
- 인과 주장: "These records do not show that giving caused death"는 n=2 사례에 한정된 부정 진술로 적절. EXIT vs 사망: 각주가 "(c,d)는 SOLVE 이후이므로 EXIT 불가, 잔고 고갈 → 사망"을 명시 — 오독 방지됨. 완주표와 교차검증: B 4103 = 0 완주(양쪽 사망), B 4102 = 2 완주(receiver 10,603 생존) ✓.
- 사례 선택: "130건 중 전액 GIVE 2/130 전수"이므로 cherry-pick이 아님 — 인정.

**(3) 점수**: 직관성 3 / 분모·결측 명료성 4 / 주장-표시 일치 4

**(4) 판정 항목**
- Warning: (d) donor가 Results에서 fine 이상(12,061)이었다가 응답 비용으로 미달이 된 순서를 그림이 강조하지 않음. 점선 위/아래를 색 띠로 구분하고 "reply −538 → below fine" 라벨을 Before GIVE에 붙일 것.
- Warning: (d) 부제 "Two replies use 664 tokens" → "Donor reply 538 + receiver reply 126 = 664"로 수정.
- Warning: (a) x축 라벨 "Completed GIVE before SOLVE result (%)"와 각주 첫 줄이 거의 맞닿음(레이아웃 충돌).
- Warning: (b) 열 합계 행 없음 — 제목의 주장을 독자가 직접 더해야 함. 하단에 "All models: 17/64, 12/225, 1/731" 추가.
- Suggestion: (b) "round-start n > 1"이 표본 n으로 오독될 수 있음 → "≥2 agents alive at round start".
- Suggestion: (c)(d) donor 종착점 0에 "eliminated at fine" 주석, (d) 범례가 0선 바로 아래 데이터와 밀착.

---

## 3. table31_outcomes.png — 완주 결과표

**(1) 핵심 주장**
"25판 중 19판에서 최소 1명이 완주했지만 4명 전원 완주는 8판뿐이며, 완주 좌석은 56/100이다."

**(2) 지지되는 것 / 과잉 주장**
- 모든 행·열 합계 검산 일치: A 14, C 17, D 4, B 9, E 12 = 56; ≥1 = 19; all-4 = 8. 제목은 표의 두 열 차이를 정확히 요약하며 인과 주장이 없다. 기술적 탐색 결과를 자명하게 전달한다 — 이 점은 인정.
- 표시되지 않은 중요한 구조: seed 4101은 C만 4, 나머지 0(4/20 좌석) — 강한 seed 효과가 보이지만 언급이 없다. fig31의 5 seed-cluster bootstrap이 이 seed에 민감하다는 점과 연결된다.
- EXIT 대 사망: "EXIT is alive but does not count as finishing"은 명시됐으나, 비완주 44석 중 EXIT/사망 분해가 없다. fig33 각주(수용 EXIT 34)와 합치면 사망은 약 10석에 불과한 것으로 추정되며, 이는 "finishers" 지표의 의미를 바꾸는 사실이다.

**(3) 점수**: 직관성 5 / 분모·결측 명료성 4 / 주장-표시 일치 5

**(4) 판정 항목**
- Warning: 비완주 좌석의 EXIT/사망 분해 열 추가("Non-finishers: EXIT k / dead k").
- Suggestion: seed 열 합계(4101: 4/20 등) 또는 각주로 seed 효과 명시.
- Suggestion: 열 제목 ">=1 finishes"는 "≥1 finisher"로 통일.

---

## 4. supplement_giving_definitions.png — 협력 지표 비교 보조그림

**(1) 핵심 주장**
"총 이전량과 GIVE 빈도는 같은 25판에서 서로 다른(둘 다 불확실한) 상관을 보인다."

**(2) 지지되는 것 / 과잉 주장**
- 지지됨: 두 r_s(+0.27 [−0.02, +0.60], −0.01 [−0.19, +0.29]) 모두 CI가 0 포함, 각주가 인과 부정을 명시. B의 48.6k(완주 0)와 53.5k(완주 4)가 "recirculation" 각주를 즉시 뒷받침한다.
- 제목 "answer different questions"는 개념적 해석이며 데이터가 보여주는 것은 "다른 값"뿐이다 — 경미한 과잉.
- (b)는 fig31(d)와 완전 동일(중복). 이 보조그림의 존재 자체가 "왜 본문엔 빈도만?"이라는 지표 선택 질문을 낳는다. 세 지표(rho, 빈도, 총량)가 모두 불확실이므로 셋을 한 패널 묶음으로 본문 또는 보조에 함께 두는 편이 선택 의심을 없앤다.
- x=0에 7판(No-GIVE)이 겹쳐 D 2 점이 식별 불가.

**(3) 점수**: 직관성 4 / 분모·결측 명료성 4 / 주장-표시 일치 4

**(4) 판정 항목**
- Suggestion: 제목을 "Two giving metrics, both uncertain, on the same 25 games"로 기술화.
- Suggestion: (b) 중복 제거하고 대신 rho를 넣어 세 지표 병렬 비교로 만들 것.
- Suggestion: x=0 겹침 카운트 라벨("7 no-GIVE games").

---

## 종합

Critical 수준(그림이 데이터와 모순되거나 인과를 주장하는 경우)은 없었다. 숫자 검산은 네 그림 모두 상호 일치한다. 주된 문제는 (i) fig31 (a)(b)의 방향성 제목이 기계적/모델 간 관계를 발견처럼 읽히게 하는 점, (ii) "finishers" 축의 비완주가 대부분 EXIT라는 사실이 어디에도 수치로 없는 점, (iii) fig33(d)에서 기준선 교차를 일으킨 것이 GIVE가 아니라 그 직전 응답 비용이라는 사건 순서가 시각적으로 묻히는 점이다.

```json
{"viewed_images":["fig31_relations.png","fig33_behavior.png","table31_outcomes.png","supplement_giving_definitions.png"],"fig31":{"intuitive":3,"denominators":4,"alignment":3,"verdict":"REVISE"},"fig33":{"intuitive":3,"denominators":4,"alignment":4,"verdict":"REVISE"},"outcomes":{"intuitive":5,"denominators":4,"alignment":5,"verdict":"PASS"},"supplement":{"intuitive":4,"denominators":4,"alignment":4,"verdict":"PASS"},"critical":[]}
```