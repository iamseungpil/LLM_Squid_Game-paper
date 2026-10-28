# Blind 그림 심사 (3.1 관계 / 3.3 행동·사례 / 완주 결과표)

세 파일을 모두 Read로 열어 실제 이미지를 확인했고, 패널 간 숫자 정합성(합계, 차감, 비율)을 직접 재계산했다.

---

## 1. fig31_relations.png — 관계 분석 (3.1)

**(1) 설명 없이 읽히는 핵심 주장**
"5모델×5시드 25판에서 SOLVE 정확도와 초반 TALK 비용은 완주자 수와 상관을 보이지만, 세 가지 '주기' 지표(ρ, 총 이전량, GIVE 응답 빈도)는 완주와 뚜렷한 관계가 없다."

**(2) 지지되는 것 / 과잉 주장**
- 지지됨: (a) 끝 상태 합계가 모델마다 정확히 20이고 table31의 완주 좌석(14/17/4/9/12)과 일치. (d) 분모 n=18과 "No GIVE 7 games" 띠(A1, C1, D2, B1, E2 = 7)가 fig33(a) 각주와 일치. ρ 공식이 축 라벨에 명시되어 있고 "Lower rho = donor retains more relative margin"은 공식 방향(받은 쪽/준 쪽)과 부합. 각주가 pooled 상관의 between/within 혼합, 5 seed cluster의 CI 한계, EXIT≠사망, No-GIVE는 0이 아닌 undefined임을 명시 — 탐색적·기술적 결과로서 자명하게 전달된다.
- 과잉/미비:
  - (b) "Correct/attempted SOLVE"와 완주자 수의 r_s=+0.74는 게임 규칙상 거의 기계적이다(오답→벌금→잔고 고갈→사망). 그림은 인과를 주장하지 않지만, 이 상관이 "능력"이 아니라 규칙 구조의 반영일 수 있음을 각주에 한 줄 추가해야 한다.
  - (c) "rounds 1-2"만 쓴 이유가 그림 어디에도 없다. 생존 편향(후반 라운드엔 살아남은 에이전트만 있음) 회피가 이유라면 명시해야 한다. 지금은 지표 선택이 임의로 보이는 유일한 지점이다.
  - (d) ρ 정의에 "negative values retained"라고 썼는데, 분모(Σw·m_giver)가 음수이면 "lower rho = donor retains more"의 해석이 뒤집힌다. 표시된 범위(0.1~0.75)가 모두 양수라 지금 데이터에선 문제가 없지만, 그 사실(18판 모두 분자·분모 양수)을 명시해야 한다. 또 m(margin)이 무엇인지(잔고−벌금?)가 그림에 정의되어 있지 않다.
  - (b),(c)의 x값은 게임당 시도 수/TALK 응답 수로 나눈 비율인데 분모 크기가 게임마다 다르다. 점 크기나 각주로 분모 범위를 알려주면 좋다.

**(3) 점수** — 직관성 3 / 분모·결측 명료성 4 / 주장–표시 일치 4

**(4) 분류**
- Critical: 없음
- Warning: (b) 규칙상 거의 기계적인 상관임을 미표기; (c) rounds 1-2 선택 근거 부재; (d) 음수 마진 시 ρ 해석 반전 가능성 미표기, m 정의 부재
- Suggestion: 상단 범례 순서 A,C,D,B,E가 비알파벳이라 "Model order is fixed"만으로는 낯설다(한 줄 근거); (a)의 E "Dead 1" 세그먼트 숫자가 좁은 빗금 안에 끼어 있음; (b)(e)(f)에서 겹치는 점(예: 100%에 B·C, x=0에 7판)은 수직 오프셋이 있어도 구분이 어려우므로 jitter 폭 소폭 확대.

**(5) 구체적 변경**
- (b) 부제 또는 각주: "Accuracy and finishing are mechanically linked by the fine rule; not an ability estimate."
- (c) 제목에 "(rounds 1-2 only, to avoid survivorship in later rounds)" 추가.
- (d) 각주: "m = balance − pending fine after GIVE; all 18 games have positive numerator and denominator."

**판정: PASS** (Warning 반영 권고, 데이터와 표시는 일치)

---

## 2. fig33_behavior.png — 행동/사례 분석 (3.3)

**(1) 설명 없이 읽히는 핵심 주장**
"GIVE가 SOLVE 결과 전에 완료되는 비율은 모델별로 다르고, EXIT 요청은 잔고가 벌금 1배 미만일 때 집중되며, 전액 GIVE 두 사례 모두 GIVE가 벌금 경계 위/아래 위치를 바꾸지 않았다."

**(2) 지지되는 것 / 과잉 주장**
- 지지됨:
  - (a) 열린 점 개수가 각 모델의 GIVE 발생 게임 수(5−NoGIVE)와 정확히 일치(A4, C4, D3, B4, E3). C(26/36)와 나머지(≤32%)의 차이는 게임 단위 점에서도 보인다.
  - (b) 열 합산: Below 1 = 17/64(27%), 1~<2 = 12/225(5%), ≥2 = 1/731(0.1%). 제목의 방향은 pooled로도 모델별로도 지지된다. "Repeated responses, not independent agents" 및 "The 100% cell is 3/3"을 명시한 점은 좋다.
  - (c) 3,235+15,820=19,055, 18,603−8,000=10,603 ✓. 제목 "no fine-threshold crossing"이 정확(수신자 전후 모두 8,000 위, 기부자 전후 모두 아래).
  - (d) 12,061+132=12,193, 11,523+6=11,529, 12,000−11,529=471, 11,529−10,990=539 ✓. "GIVE changes neither agent's position above/below the pending fine in either case" ✓. 사건 순서(Results→GIVE→fine), EXIT가 SOLVE 후엔 불가하다는 점, 사망=잔고 고갈을 각주로 분리해 EXIT/사망 오독을 막았다. 사례 선정 기준(130건 중 전액 GIVE 2/130 전부)이 명시되어 cherry-picking이 아님을 보여준다.
- 과잉/미비:
  - (b) 색상이 %로 인코딩되어 n=3인 A의 100% 셀이 그림에서 가장 진하다. 각주 경고가 있어도 시각적 무게가 제목을 과장한다. n<10 셀은 빗금 처리하거나 채도를 n으로 제한해야 한다.
  - (b) EXIT 요청 합(A5, C3, D11, B5, E6)이 fig31(a)의 EXIT 좌석(A6, C3, D12, B6, E7)과 C를 제외하고 모두 1씩 적다. "round-start n>1, non-solver" 필터 때문으로 보이지만 그림에 설명이 없어 독자가 두 그림을 대조하면 불일치로 읽는다. 제외된 EXIT 수와 이유를 각주에 적어야 한다.
  - (a) 제목 "Before-result and after-result giving differ"는 무엇이 무엇과 다른지 불명확하다(모델 간 차이인지, 전/후 빈도 차이인지). 표시된 것은 "결과 전 GIVE 완료 비율의 모델별 차이"다.
  - (d) 제목 "TALK cost precedes GIVE"와 부제 "joint balance 12,193 → 11,529"는 "TALK만 안 했으면 공동 잔고가 벌금(12,000)을 넘었다"는 반사실을 암시한다. 각주 "Timing is descriptive, not proof of benefit"가 있지만, 패널 제목 자체는 인과 쪽으로 기울어 있다. 또한 (b)의 "fine"(round-start 잠재 share)과 (c,d)의 "fine"(오답 후 확정)이 다른 개념인데 같은 단어를 쓴다 — 각주에 밝혀두긴 했다.
- 겹침: (c) 범례(Donor/Receiver)가 "18,603" 라벨 바로 위에 붙어 거의 닿는다. (d) "11,523" 라벨이 기부자 하강선 위에, "11,529"가 수신자 상승선 끝에 겹치며, 좌하단 범례가 수신자 132→6 선분과 근접한다.

**(3) 점수** — 직관성 3 / 분모·결측 명료성 4 / 주장–표시 일치 3

**(4) 분류**
- Critical: 없음(각주로 주요 오독은 방어됨)
- Warning: (b) n=3 셀의 최대 채도; (b) EXIT 요청 수 vs EXIT 좌석 수 불일치 미설명; (d) 제목의 반사실적 뉘앙스; (c)(d) 라벨–선·범례 겹침
- Suggestion: (a) 제목을 "Share of GIVE completed before the SOLVE result varies by model"로; (a)에도 "pooled events are repeated responses within games" 한 줄; "complete transfer sequences"의 'complete'가 전액(full-balance)인지 기록 완전성인지 불분명하므로 "full-balance"로 통일.

**(5) 구체적 변경**
- (b) 각주: "Excluded: k EXITs occurring at round-start n=1 or by the solver (A1, D1, B1, E1)." 및 n<10 셀 빗금.
- (d) 제목을 "Two replies (664 tokens) occur before GIVE; receiver ends 471 short"처럼 기술형으로.
- (c) 범례를 좌상단 빈 공간(Results 위)으로 이동; (d) "11,523"을 선 왼쪽으로, "11,529"를 선 오른쪽 위로 오프셋.

**판정: REVISE** (수치는 정확하나 시각 가중·불일치·겹침 수정 필요)

---

## 3. table31_outcomes.png — 완주 결과표

**(1) 설명 없이 읽히는 핵심 주장**
"25판 중 19판에서 최소 1명이 완주했지만 4명 전원 완주는 8판뿐이며, 완주 좌석은 56/100이다."

**(2) 지지되는 것 / 과잉 주장**
- 히트맵 행 합(14/17/4/9/12), ≥1 완주(4,5,3,3,4=19), 전원 완주(3,2,0,1,2=8), 좌석(56/100) 모두 재계산 일치. fig31(a),(b)의 점 분포와도 일치. "Completion = end of round 8, not eight correct answers", "EXIT is alive but does not count as finishing"으로 EXIT/사망/완주 정의가 분명하다. 제목은 데이터가 그대로 보여주는 기술적 사실이며 과잉 주장 없음.
- 눈에 띄지만 언급되지 않은 점: seed 4101은 C를 제외한 모든 모델이 0 — 시드 효과가 강하다. 이는 fig31의 paired-seed bootstrap을 정당화하는 근거이므로 한 줄 언급하면 그림 간 연결이 좋아진다.
- 레이아웃: x축 라벨 "Seed (same five IDs…)"와 바로 아래 각주 "All 25 games: …"가 거의 붙어 있어 한 덩어리로 읽힌다. 색상 범례(colorbar)는 없지만 셀 숫자가 있어 문제 없음.

**(3) 점수** — 직관성 5 / 분모·결측 명료성 5 / 주장–표시 일치 5

**(4) 분류**
- Critical/Warning: 없음
- Suggestion: 각주와 x축 라벨 간격 확보; "Seed 4101: 0 finishers for four of five models" 한 줄 추가.

**판정: PASS**

---

## 종합

- 지표 선택의 임의성: fig31(c)의 "rounds 1-2"만 근거가 없다. 나머지는 정의가 축에 명시되고, 유의하지 않은 지표도 숨기지 않고 그대로 보여 cherry-picking으로 보이지 않는다.
- ρ 방향: 공식·설명·데이터 범위 모두 일관. 다만 음수 마진 시 해석 반전 가능성을 명시해야 한다.
- n=3/반복응답: fig33(b)에서 텍스트로는 경고했으나 색상이 이를 무력화한다.
- EXIT vs 사망, 사건 순서: 세 그림 모두 각주로 분리했고 사례 패널의 순서·수치가 정확하다. 인과 주장은 없으며, fig33(d) 제목만 반사실 뉘앙스가 있다.

```json
{"viewed_images":["fig31_relations.png","fig33_behavior.png","table31_outcomes.png"],"fig31":{"intuitive":3,"denominators":4,"alignment":4,"verdict":"PASS"},"fig33":{"intuitive":3,"denominators":4,"alignment":3,"verdict":"REVISE"},"outcomes":{"intuitive":5,"denominators":5,"alignment":5,"verdict":"PASS"},"critical":[]}
```