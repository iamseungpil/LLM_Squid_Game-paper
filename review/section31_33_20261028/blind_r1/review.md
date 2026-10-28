# Blind 심사 결과 (candidate_P.png, candidate_Q.png 직접 열람)

## candidate_P — 관계 분석 (3.1)

**(1) 한눈에 들어오는 주장**
"C→A→E→B→D 순으로 생존자가 많고, 생존자 수는 SOLVE 정확도와 강하게(+0.74), 초반 TALK 길이와 음(-0.41)으로 상관되며, rho·총 이전량·GIVE 비율과는 뚜렷한 관계가 없다."

**(2) 지지되는 것 / 안 되는 것**
- 지지됨: (a)의 20석 분해(17/3/0, 14/6/0, 12/7/1, 9/6/5, 4/12/4 — 합계 모두 20으로 검산됨). 산점도의 y값을 모델별로 합산하면 (a)의 Finished 수와 정확히 일치함(C 4+4+3+3+3=17 등). 정확도 패널의 CI [+0.28,+0.89]와 TALK 패널 CI [-0.67,-0.17]이 0을 벗어남.
- 지지 안 됨:
  - 패널 제목 "Self-preservation"이 rho에 붙어 있으나, 표시된 rho가 전부 <1(0.1~0.75)임. 정의(받은 쪽 여유/준 쪽 여유)대로면 모든 게임에서 **받는 쪽이 더 궁한 쪽**이었다는 뜻이고, 이는 "자기보존"과 반대 방향으로 읽힘. 높은 rho가 자기보존 ↑인지 ↓인지 그림만으로 판별 불가. CI [-0.28,+0.75]도 0을 포함.
  - r_s는 25게임을 모델 구분 없이 풀링한 값. (c)에서 정확도 축이 사실상 모델별로 군집(D 40~67%, C/A 60~100%)하므로 +0.74는 게임 간 관계가 아니라 **모델 간 차이**를 반영할 가능성이 크지만 그림은 이를 말하지 않음.
  - (a)의 막대 정렬이 생존자 내림차순이라 "모델 순위"로 읽히지만 seed 5개의 불확실성 표시가 없음.
  - y축 "Finishers at round 8"은 EXIT와 사망을 합쳐 비생존으로 뭉개 버림. (a)는 구분하지만 5개 산점도는 구분 못 함. D(EXIT 12, 사망 4)와 B(EXIT 6, 사망 5)가 같은 y에서 섞임.

**(3) 점수**
- 직관성: 3/5 — 레이아웃은 표준적이나 패널 제목이 변수명이 아닌 해석어("Self-preservation", "Early TALK cost")라 독자가 해석을 먼저 주입받음.
- 분모·결측 명료성: 2/5 — n=18의 결측 7게임이 **어느 모델**에서 빠졌는지 패널에 표시가 없음(특정 모델이 GIVE 0이면 그 모델이 rho 상관에서 통째로 빠지는 셈). 마커 겹침 때문에 그림에서 점을 세면 ~19개로 18과 맞지 않아 검증 불가. (a)에는 Finished/EXIT/dead 색 범례가 없고 제목 순서로 추정해야 함.
- 주장-표시 일치: 2/5 — 상기 rho 제목 문제 + 풀링 상관 미고지.

**(4) 이슈**
- **Critical**: 하단 모델 범례(C A E B D 마커)가 각주 문장 "Rho undefined in 7 no-GIVE games; omitted from its panel. Associations are exploratory, not causal." 위에 겹쳐 인쇄됨. 결측 고지와 비인과 고지가 **둘 다** 읽히지 않음. 렌더링 버그.
- **Critical**: (a)의 결과 색(청록=Finished, 금색=EXIT)이 모델 팔레트(C=청록, E=금색)와 동일. 독자가 (a)를 "C의 몫/E의 몫"으로 오독할 수 있음.
- **Critical**: "Self-preservation" 제목 ↔ rho 방향 불일치(위 설명). 독자는 rho 방향을 확실히 혼동함.
- Warning: rho 결측 게임의 모델 분포 미표시. 25게임 풀링 r_s에 대한 "between-model 혼입" 경고 없음. EXIT/사망 혼합 y축. 정렬된 (a)가 순위를 암시.
- Warning: "Unchanged rho"는 "변경 안 한 rho"로 읽혀 어색함 — "fixed-definition rho" 류로 바꾸고 정의식을 축 레이블에 적어야 함.
- Suggestion: y 지터 대신 작은 수평 스트립/빈 카운트 사용. 각 패널에 모델별 n 표기.

**(5) 재설계**
- 범례를 그림 상단 오른쪽(제목 옆)으로 옮기고 각주와 분리.
- (a) 결과 색을 회색조 3단계(또는 해칭)로 바꾸고 범례 명시; 막대를 모델 고정 순서(혹은 알파벳)로 두고 "정렬=순위 아님"을 피함.
- 각 산점도 제목을 변수명으로: "rho = Σw·slack_recv / Σw·slack_give (n=18; missing: A 1, D 2 …)" 식으로 결측 모델별 수를 직접 표기.
- 산점도 y를 EXIT/사망 분리 마커(채움/빈 마커)로 구분하거나, 보조 패널에서 "non-finishers of which dead" 표시.
- r_s 밑에 "pooled over models; within-model r_s = …" 한 줄 추가, 또는 모델 평균 5점만 큰 마커로 겹쳐 between/within을 눈으로 분리.

## candidate_Q — 행동/사례 분석 (3.3)

**(1) 한눈에 들어오는 주장**
"C는 GIVE의 72%를 '결과 전'에 완료하고, 모든 모델에서 잔고가 벌금보다 적을 때 EXIT가 급증하며, B의 전액 GIVE 두 건은 한 번은 수령자가 살고 한 번은 둘 다 죽었다."

**(2) 지지되는 것 / 안 되는 것**
- 지지됨: (a)의 분수 표기(26/36 등)는 분모가 명확. (c)(d)의 숫자 산술 일치(12,000−11,529=471; 3,235+15,820=19,055). 각주에 "전체 데이터에서 전액 GIVE가 단 2건"임을 고지한 것은 좋음.
- 지지 안 됨:
  - 제목 "Similar acts can have different local consequences": (c)에서 기부자는 이미 벌금 아래(3,235<8,000), 수령자는 이미 벌금 위(15,820>8,000). (d)에서 기부자도 이미 벌금 아래(11,523<12,000). 즉 **두 사례 모두 GIVE가 어느 쪽의 벌금 통과 여부도 바꾸지 못했음**. "다른 결과"는 행위의 결과가 아니라 행위 전 잔고로 이미 결정되어 있었음. 그림은 이를 말하지 않고, 독자는 "(d)에서 전액을 줘서 둘 다 죽었다"는 인과 해석으로 직행함. 각주의 "not a causal survival estimate"로는 막기 어려움.
  - (b) 제목 "EXIT concentrates near the fine boundary"인데 데이터는 "<1"(경계 **아래**)에서 높고 "1-2"(경계 바로 위)에서 낮음. "near"가 아니라 "below".
  - (b)의 A 100%, D 56%는 빈별 n이 없어 1/1인지 20/20인지 알 수 없음.
  - (a) "before result"의 result가 SOLVE 결과인지 벌금 결과인지 정의 없음.

**(3) 점수**
- 직관성: 2/5 — (b)에 범례가 전혀 없음((a) 막대색에서 유추해야 함, 마커 모양은 설명 없음). "eligible prep responses", "before result" 미정의. giver/donor, taker/recipient 용어 혼용.
- 분모·결측 명료성: 2/5 — (a)는 양호, (b)는 빈별 분모 전무, 사례 n=2는 고지됨.
- 주장-표시 일치: 2/5 — 제목 두 개가 데이터와 어긋남(위 설명).

**(4) 이슈**
- **Critical**: (b) 범례 없음 + 빈별 n 없음 → 100% 포인트의 신뢰도 판단 불가.
- **Critical**: (c)(d) 소제목이 "행위 전 이미 양쪽 상태가 결정되어 있었다"를 숨겨 인과 오독 유발. "both die"가 GIVE 때문으로 읽힘.
- Warning: EXIT와 사망의 정의가 Q 어디에도 없음. (b)는 "잔고<벌금 → EXIT", (d)는 "잔고<벌금 → die"를 보여주므로 독자는 EXIT=벌금 못 내서 죽음으로 오해할 수 있음.
- Warning: (b)의 서열 빈을 선으로 연결해 연속 추세처럼 보임. "Pending fine"(c,d) vs "per-agent fine"(b) 동일 양인지 불명.
- Suggestion: (a)는 다른 세 패널과의 연결 고리가 약함 — 왜 "timing"이 사례 선택과 관련되는지 한 줄 필요.

**(5) 재설계**
- (b): 범례 추가, 각 포인트 옆에 k/n 표기, 선 제거 후 그룹 막대(또는 점+CI)로. 제목을 "EXIT rate is highest when balance < fine"으로.
- (c)(d): 벌금 점선 대비 "before"와 "after" 상태를 ✓/✗로 양쪽 에이전트에 명시하고, 소제목을 "GIVE did not change either agent's fine status (giver below before and after)"처럼 바꿈. 사망 여부와 EXIT 여부를 범례로 정의.
- (a): "result" 정의를 축 레이블에 포함(예: "GIVE completed before SOLVE result (%)"), 정렬 기준 명시.
- 전체 각주의 "EXIT = voluntary leave with …; dead = balance < fine at settlement" 식 정의 1줄 추가.

## 요약 판정

두 그림 모두 데이터 수치 자체는 내부적으로 정합하나, **P는 범례-각주 겹침과 rho 방향/제목 불일치**, **Q는 (b) 범례·분모 부재와 사례 소제목의 인과 오독 유도**로 현 상태에서는 독자가 rho 방향, 모델 순위, EXIT/사망, 인과를 혼동할 가능성이 높음.

```json
{"viewed_images":["candidate_P.png","candidate_Q.png"],"P":{"intuitive":3,"denominators":2,"alignment":2,"verdict":"REVISE"},"Q":{"intuitive":2,"denominators":2,"alignment":2,"verdict":"REVISE"},"critical":["P: 하단 모델 범례가 결측/비인과 각주 문장 위에 겹쳐 인쇄되어 둘 다 판독 불가","P: 패널(a) 결과 색(청록/금색)이 모델 C/E 색과 동일하고 결과 범례가 없어 오독 유발","P: 'Self-preservation' 제목과 전부 <1인 rho 값의 방향이 불일치하여 rho 해석 방향을 판별할 수 없음","P: rho n=18의 결측 7게임이 어느 모델인지 미표시, 25게임 풀링 r_s의 모델 간 혼입 미고지","Q: 패널(b) 범례 및 빈별 분모 부재로 100%/56% 포인트 신뢰도 판단 불가","Q: 사례 (c)(d) 모두 GIVE 전에 양측 벌금 상태가 이미 결정되어 있었음에도 소제목이 이를 숨겨 '전액 GIVE가 사망을 초래'로 인과 오독 유도","Q: EXIT와 사망의 정의 부재로 (b)의 EXIT와 (d)의 die가 같은 사건으로 읽힐 수 있음"]}
```