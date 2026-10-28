# 서론·기여·결과·그림·결론 통합 피드백

검토일: 2026-10-29. 기준 원고: `c73cbaa`의 한국어 CogSci 원고 및 이 문서와 함께 커밋되는 한계 보완. 본문 그림 1–7, 표 1, §1–4를 실제 PDF와 소스로 대조했다. **부록만의 근거는 본문 기여의 회수로 인정하지 않는다.** 이 파일이 feedback2의 최신 판단과 작업 기록을 모으는 문서다. 아래 과거 기록의 PASS는 당시 한정된 검증이며 현재 원고 전체의 통과 판정이 아니다.

표시: ✅ 현재 원고 또는 이번 정리에서 해결됨 / ◐ 일부 반영됨 / ⬜ 아직 남음. 요구 범위를 줄여 해결한 항목은 무엇을 더 이상 주장하지 않는지도 함께 적었다. 현재 검토는 논문 제출 승인이나 실험 전체의 타당성 판정이 아니다.

## 1. 핵심 판단: 무엇을 약속했고 어디에서 회수하는가

**동일 자원 안에서 과제·배분·이탈과 전원 완주를 함께 기록하는 아레나라는 기여는 회수된다. 자기 보존의 내적 동기, 공존의 필요조건, 협력의 인과효과까지 입증한 것은 아니다.** 현재 서론과 결론은 이전 버전보다 관찰 자료의 범위에 잘 맞는다. 가장 큰 남은 문제는 새로운 주장을 더하는 것이 아니라, 이미 얻은 결과의 단위와 해석 범위를 그림과 결론에서 일관되게 보이게 하는 일이다.

| 서론의 약속 | 본문 안의 근거 | 결론의 회수 | 판단과 필요한 보완 |
|---|---|---|---|
| 목표 지향·자기 보존·협력이 같은 토큰을 두고 충돌하는 환경 | §2.2, 그림 1의 순서·공동 벌금·EXIT·GIVE, 그림 2의 과제 | §4 마지막 문단이 과정과 결과를 나누어 평가하는 설계를 회수 | ✅ 설계 기여는 보인다. 생존/협력을 직접 지시하지 않았다는 사실이 내적 동기의 자발성을 증명하지는 않는다. |
| 어떤 과제 수행과 건네기가 전원 완주와 함께 관찰되는가 | §3.1, 그림 3의 전원 완주 8판/그 외 17판, 그림 4의 개인 끝 상태 | 8/25, Astra 3/5·Opus 1/5, 완주자의 높은 정답률을 회수 | ✅ 관계 질문으로는 회수. ⬜ 모델별 전원 완주율은 본문 숫자에 흩어지고 표 1은 개인 완주 수로 정렬된다. 그림 또는 표에서 집단 결과를 직접 보여 줄 것. |
| 상대적 자기 여유와 다른 행동·최종 분포의 관계 | §3.2, 그림 5의 18판(지니 17판), 상금 제외 민감도 | §4는 주로 모델별 전원 완주 순위에 머묾 | ◐ 결과는 있지만 서론의 절 안내는 3.2를 빠뜨린다. 결론에 “상대적 여유만으로 과제 지속·자원 분포를 설명하기 어려웠으며 분배 관계도 상금 처리에 민감했다” 정도로 회수할 수 있다. 유의성/무관계 단정은 피한다. |
| 생존 여유별 결정은 어떻게 다른가 | §3.3, 그림 6의 정답률·GIVE·EXIT 구간과 GIVE 직후 두 여유 | 낮은 여유에서 이탈 증가, 나눔이 주는 쪽 여유를 남김 | ◐ 관측 방향은 회수. GIVE의 빈도와 양, EXIT 응답과 실제 이탈 사건을 구분해야 한다. 낮은 여유 전체에서 GIVE가 단조 감소한 것은 아니다. |
| 모델별 대표 장면은 어떤 인물을 닮는가 | §3.3의 구체 사례, 표 1, 그림 7 | 사례를 통한 도움·이탈 방식의 차이로 마무리 | ✅ “모델 전체 분류”에서 “사례 비유”로 제한한 것은 타당. ⬜ 약속 위반 0건·잔량 발언 100건 등은 코딩 범위·판정 절차가 부족하다. |

## 2. 우선 반영할 개선점

### P1. 집단의 전원 완주와 개인의 완주를 시각적으로 분리

- **위치:** 표 1, 그림 3, §4 첫 문단.
- 표 1의 Fable 17명과 Astra 14명은 개인 완주 수다. 주 지표인 전원 완주율에서는 Astra 3/5가 Fable 2/5보다 높다. 현재 표의 정렬과 “가장 많이 남은 Fable”은 맞는 표현이지만, 독자가 주 지표의 우승으로 오독할 수 있다.
- **수정안:** 표 1에 `전원 완주 판 / 5` 열을 추가하고 “끝 상태”를 `개인 끝 상태(n=20)`로 명시한다. 또는 별도 패널 하나에 2/5·3/5·2/5·1/5·0/5를 제시한다. 두 표현을 모두 추가해 그림을 중복시키지는 않는다.
- **완료 조건:** 독자가 본문 숫자를 다시 계산하지 않고 개인 완주와 집단 완주를 구분하며, 결론의 모델 비교를 같은 표/그림에서 확인할 수 있어야 한다.

### P1. 그림 6에서 행동 지표의 단위와 기회 분모를 명확히

- **위치:** §2.2 협력·목표 지향 정의, 그림 6a 및 캡션, §3.3 마지막 문단.
- 그림 3·5의 협력은 `GIVE 토큰 / 참여 에이전트·라운드`, 그림 4는 `한 번이라도 준 개인 비율`, 그림 6은 `응답별 GIVE 빈도`다. 각각 정당한 보조 정보지만 같은 협력량으로 읽으면 안 된다. 그림 6의 GIVE 분모(262/614/764/1258)와 EXIT 분모(64/225/281/450)도 서로 다르다. GIVE는 어떤 단계·자리의 응답인지, EXIT는 떠날 수 있던 풀기 전 비solver 응답인지 캡션에서 구별해야 한다.
- GIVE는 여유 1–2에서 0.8%이고 1 미만에서는 3.4%다. “여유가 낮을수록 GIVE가 줄었다”는 단조 표현보다 “여유 1–2에서 크게 줄었고, 1 미만의 이전은 별도 상황으로 해석한다”가 정확하다. 안전선 위 GIVE 120건 중 119건이 유지한 안전과 전체 130건을 섞지 않는다.
- **수정안:** 현 그림을 유지한다면 GIVE 빈도를 보조 지표로 명시한다. “같은 위험 수준에서 세 요소를 모두 측정했다”는 강한 기여를 다시 내세우려면 같은 구간의 이전량과 적격 기회 분모를 추가로 분석해야 한다. 그 작업 없이 인과나 동기 강도 그래프로 이름만 바꾸지 않는다.

### P1. ASK→도움→완주의 시간 순서와 관찰 한계

- **위치:** §3.3 “토큰은 청한 쪽으로 갔다”, §4 한계의 22회 중 11회.
- ASK한 12명 모두 수신, ASK하지 않은 21명 중 6명 수신은 관측된 공발생이다. 같은 틱의 ASK와 GIVE는 동시 응답이므로 요청이 송금을 유발했다고 판정할 수 없다. §4의 `위기 라운드 22회 중 11회가 같은 틱`은 그 분모와 추출 규칙이 §3.3에 없는 상태에서 처음 등장한다.
- **수정안:** 요청 선행/동시/후행을 구분한 근거를 §3.3에 짧게 제시하거나, 상세 수치 대신 “요청과 수신의 선후가 불분명한 사례가 있어 요청의 효과로 해석하지 않는다”고 한계를 쓴다. `받음 없음`의 EXIT 차이도 도움이 이탈을 막았다는 효과로 표현하지 않는다.
- 이번 검토에서 새 ASK 인과 분석을 실행한 것은 아니다. 과거 raw 감사 수치를 현재 본문의 분모 설명 없이 입증된 인과로 승격하지 않는다.

### P1. 여유 비율을 동기 크기로 읽는 표제 정리

- **위치:** §3.2 제목, 그림 3c·그림 5 가로축, §4 한계.
- 본문은 ρ가 주관적 동기를 직접 재지 않는다고 명시하지만, 표제의 “자기 보존”만 보면 성향/능력 크기로 오독하기 쉽다. GIVE 없는 7판이 빠지므로 전체 25판의 자기 보존 정도도 아니다.
- **수정안:** 표제는 “상대적 자기 여유(ρ)” 또는 “GIVE 후 여유 비율”을 주어로 쓰고, 본문에서 자기 보존의 제한된 행동 지표라고 설명한다. 조건부 분석 18/25판을 유지한다.
- ✅ 이번에 `iamseungpil` 수정에서 누락된 기회·집계·정보 제한을 §4에 반영했다. ρ는 생존 확률/목숨 가치의 비율이 아니고, 같은 평균에 서로 다른 배분이 섞일 수 있음을 명시했다. 표제 수정은 아직 남아 있다.

### P2. 서론의 분석 안내와 결론을 현재 §3.1–3.3에 맞추기

- **위치:** §1 마지막 문단, §4 첫 문단과 결론.
- 서론은 3.1과 3.3만 예고한다. §3.2는 6개 패널을 쓰는 주요 결과인데 기여 안내와 결론에서 상대적으로 빠져 있다.
- **수정안:** 세부 질문을 “전원 완주와 행동의 관계 / 상대적 여유와 과제 지속·분배 / 여유별 결정과 사례”로 연결한다. 결론에는 게임 수준의 정답률·이전량·ρ 방향과 §3.2의 불확실성을 짧게 묶는다. 모든 수치를 반복하거나 세 상관을 독립적인 인과 근거로 세지 않는다.
- 현재 `관계/관찰`이라는 약한 주장 범위는 유지한다. 토큰 절약 능력의 필요조건이나 최적 협력량으로 돌아가지 않는다.

### P2. 사례 비유와 “모두 정직했다”의 범위를 맞추기

- **위치:** §3.3 첫 문장·마지막 사례 문단, 표 1·그림 7.
- ✅ “가장 가까운 인물”의 완전 분류 대신 “대표 사례의 비유”로 제한했다.
- ⬜ “모든 모델은 약속을 지켰다”, “계산하면서도 정직했다”는 전체 행동 특성으로 읽힐 수 있다. 잔량 발언 100건의 선정 방식, 약속의 판정 단위·총수, 코더 수·불일치 처리 등은 본문에서 확인되지 않는다.
- **수정안:** 본문에 최소 코딩 범위를 넣고 “검토한 잔량 발언 100건은 기록과 일치했다”처럼 관측 범위를 주어로 쓴다. 절도 행동 자체가 없는 설계에서 배신 부재를 광범위한 정직성으로 일반화하지 않는다. 인물 그림은 설명 그림이며 독립 증거가 아니다.
- 표 1의 작은 글씨와 그림 7의 영어 주석도 실제 한 단 너비에서 읽기 어렵다. 열 수를 줄이거나 사례 설명을 본문과 나누되 새 증거인 것처럼 중복하지 않는다.

### P1. 제출 분량·미완성 표기·언어판 상태

- 기존 10-28 PDF는 전체 45쪽, 부록 제외 8쪽이고 논의·결론이 7쪽에 있다. 본문 자체가 6쪽 규칙을 넘는다. 프로젝트 규칙상 부록을 포함한 제출 전체(참고문헌·감사의 글 제외)도 6쪽이므로 45쪽 전체본은 연구용 자료이지 제출본이 아니다. 이번 한계 보완 후 페이지는 §6의 최종 검증 기록을 따른다.
- `01_introduction.tex` 첫 문단의 `[인용]`, `90_acknowledgments.tex`의 `[TODO: AI 사용 고지.]`를 해소해야 한다. 컴파일 성공으로 해결된 항목이 아니다.
- 영어판은 기존 본문·논의 TODO를 가진 별도 미완성 상태다. 이번 추가 한계 문단만 대응 번역했으며 한영 전체 동기화 완료를 뜻하지 않는다.
- **완료 조건:** 제출본 전체의 6쪽 충족, 본문 미완성 표기 제거, 필요한 언어판의 실제 내용 동기화. 이번 요청의 검토·정리와 별개로 남는 집필 작업이다.

## 3. 기존 Astra 피드백 6건의 현재 상태

| 기존 항목 | 현재 상태 | 확인 근거 |
|---|---|---|
| 1. 공존에 무엇이 필요한가라는 필요조건 질문 | ✅ 범위 수정으로 해결 | §1은 전원 완주와 함께 관찰된 행동을 묻고, §3.1·§4는 필요한 조합/인과효과를 판정하지 않는다고 명시한다. |
| 2. 자기 보존이 협력·추론을 바꾸었다는 영향 주장 | ✅ 강한 주장 철회, ◐ 지표 이름 개선은 남음 | 서론은 “어떤 관계”, 결론은 “관찰”. 토큰 절약과 추론이 함께 필요했다는 문장은 현재 본문에 없다. 그림 표제는 §2 P1 참고. |
| 3. 토큰 감소가 주관적 위협이라는 전제 검증 | ✅ 기여 범위에서 제외 | §2.1은 이를 전제하지 않는다고, §4는 판단하지 않는다고 명시. 리필팩 결과를 본문 기여 근거로 사용하지 않는다. |
| 4. Sen이 세 요소의 동시 추구를 측정하는가 | ✅ 정의 변경으로 해결 | 공존은 전원 완주라는 결과이며 세 요소 동시 추구를 뜻하지 않음. Sen·μ·G는 보조 자원 지표다. |
| 5. 같은 위험 척도에서 세 요소를 비교한다는 약속 | ◐ 일부 해결 | 판 단위 관계와 위험 구간별 빈도가 제시되나 단위가 다름. 모든 요소를 같은 적격 기회에서 비교한 것은 아니다. |
| 6. 인물 분류의 대표성·선정 규칙 | ✅ 사례 비유로 제한, ◐ 코딩 근거는 남음 | §3.3·표 1은 모델 전체 분류가 아니라고 명시. 무위반·정직성 주장은 별도 정리 필요. |

## 4. 10-27 미팅 23건의 상태 갱신

원 회의: `1028-meeting.txt`(Sundong·Seungpil). “현실적인 셋업이 먼저이며 지표를 잘 나오게 하려고 셋업을 바꾸지 않는다”는 원칙을 유지한다. 아래 ✅는 과거의 “부록에만 반영” 표시를 그대로 옮긴 것이 아니라 현재 원고를 다시 확인한 결과다.

| 번호 | 요청 | 현재 상태·남은 작업 |
|---|---|---|
| 1 | 클리어율을 주 지표로 | ✅ 현재 저자 정의는 전원 완주(4/4)이며 §2.2·3.1·초록에 반영. 엔진의 다른 clear 정의와 혼동하지 않는다. |
| 2 | Sen을 μ·G·S로 분해하고 보조화 | ✅ §2.2·3.2, 그림 5d–f. 전원 완주와 별개로 읽는다. |
| 3 | 2천만 상금 제외 Gini | ◐ §3.2에 상금 제외 민감도 수치는 있지만 그림 5 주 패널은 상금 포함. 상금 제외를 주 그림으로 삼으라는 원 요청까지 완료한 것은 아님. 부록의 시간 궤적은 별도 분석이다. |
| 4 | EXIT는 생존인가 명시 | ✅ 살아서 나가지만 완주에는 포함하지 않음. 개인 끝 상태와 전원 완주 모두 명시. |
| 5 | ρ의 분자·분모 방향 | ✅ 식 (2) giver/taker. 모델 값 3.68/2.70/4.24/1.83/3.17. 과거 역방향 분석값과 혼용 금지. |
| 6 | 여유 표기 통일 | ✅ 최신 표기는 L(life buffer). 이전 m_i와 동치이며 두 기호를 혼용하지 않는다. |
| 7 | 음수 유지·미납 벌금 설명 | ✅ §2.2 식 (1) 주변에서 d=1/0, 이중 차감 방지, 음수 의미 설명. |
| 8 | 공존·능력 관계 그림 | ◐ 그림 3·5가 관계를 보여 줌. 토큰 절약 능력은 현재 분석하지 않으며 효과 주장은 불가. 주 지표 모델별 표시는 보완 필요. |
| 9 | 판/개인 점·불확실성 | ✅ 그림 3·5는 판별 점, 시드 묶음 5,000회 재표집 구간. 그림 4는 집계 비율이며 구간이 없다고 명시. 100명을 독립 반복으로 취급하지 않음. |
| 10 | 애매한 토큰 절약 플롯 정의 수정/삭제 | ✅ 현 본문 관계 그림에서 제외. 절약의 필요조건 결론도 삭제. |
| 11 | 리필팩 타당성 실험을 본문에서 제거 | ✅ 현재 본문에 없음. 이 분석 없이 주관적 위협을 입증했다고 쓰지 않음. |
| 12 | 같은 아레나의 정량 행동 분석 | ◐ §3.2 관계·§3.3 행동으로 채움. 원 요청의 3.1 지표/3.2 정량/3.3 정성 배열과는 다르고 반복 대화 분석도 추가하지 않음. |
| 13 | 다음 미팅용 행동 지표 후보 | ◐ 비용·같은 과제 성과·도움의 장부 경로 후보는 과거 재분석에서 제안됨(§5). 다음 미팅에 가져가거나 합의했다는 증거는 없음. |
| 14 | 상금 20만/200만/2천만 어블레이션 | ⬜ 실험 없음. 상금 제외 재계산은 행동 유인 변화 실험을 대신하지 못함. |
| 15 | 게임 뒤 상금 쓰임 시나리오 | ⬜ 새 조건 실험 없음. |
| 16 | 토큰/달러 환산 비교 | ⬜ 새 조건 실험 없음. |
| 17 | EXIT를 풀기 전에만 허용하는 이유 | ✅ §2.2에 확정 벌금 회피와 사전 위험 판단을 구분하기 위한 설계라고 설명. 실제 행동 타당성 검증과는 별개. |
| 18 | EXIT 2만 추가 지급 근거 | ◐ 일상 업무 대가라는 설정은 설명. 금액 선택의 근거·민감도는 남음. |
| 19 | 필요할 때 n명 채팅방 | ⬜ 고정 방 설계 유지. 검토·대안 실험 없음. |
| 20 | solver의 실제 섞인 순환 명시 | ✅ §2.2에 프롬프트의 무작위 안내와 엔진의 섞인 순환을 구분. 엔진을 바꾸지 않음. |
| 21 | 문제 전 GIVE의 동기 설명 | ◐ 벌금 공동 부담·동료 유지 이익은 설명. 난이도를 모르는 사전 이전을 관찰 사례와 더 직접 연결할 여지 있음. |
| 22 | 캐릭터 비유는 분량에 따라 결정 | ◐ §3.3에 사례 비유로 유지. 현재 6쪽 초과여서 분량 결정은 미완료. |
| 23 | 교수님께 최신 원고 공유 | ⬜ Git push는 교수님께 전달했다는 증거가 아님. 별도 연락은 이번 요청에 없으므로 발송하지 않음. |

## 5. 흩어진 분석·수정 기록의 통합

### 반영되어 유지하는 내용

- ✅ `20261028_all_four`, `arena_clear`, `coexistence_structure`: 전원 완주를 결과로 정의. 8/25, 모델별 2/3/2/1/0, 개인 끝 상태 56/34/10. 아레나의 성립과 세 행동의 필요조건을 구분.
- ✅ `notation`, `life_buffer`: 미납 벌금과 음수 여유를 보존하고 L 표기 및 giver/taker ρ로 설명. 표기 변경으로 원자료 수치를 바꾸지 않음.
- ✅ `section32_metrics`: 25판 중 GIVE 있는 18판, G는 all-zero 한 판을 뺀 17판. 원자료 기반 감사는 192풀이/133정답/680 참여 에이전트·라운드/130 GIVE/383,276토큰/1,020 적격 응답 중 990 non-EXIT를 검증했다. r 여섯 개를 별도로 검정한 탐색적 분석이며 μ·G·S는 독립 근거가 아님.
- ✅ `fig3_individual`, `compact_figures`, `section_moves`, `A12_main`: 개인 결과와 판 결과를 분리하고 현재 그림 3·4·5로 배치. 버려진 모델별·생존여유별 변형 그림은 본문 근거로 사용하지 않음.
- ✅ `A9_no_exit`: 부록 잔액 궤적은 EXIT한 라운드부터 제외, 꺼짐은 0으로 유지. 집단별 분모가 감소하므로 고정 20명 평균으로 설명하지 않는다. 현재 전체 평균은 집단 평균의 단순 평균이 아님.
- ✅ `a10_round_gini_20261028_134035`: 부록 라운드 Gini는 처음 네 자리를 고정하고 EXIT 보너스는 유지하며 최종 상금을 제외. 25판×9시점=225벡터를 원기록과 대조한 분석. A9의 EXIT 제외 분모와 다르다.
- ✅ `table1_fig1_a11`, `centroids`, `fig3c_game_level`: 본문 표 정의·그림 1 벌금 시점 설명, 부록 무게중심과 판별 분석을 정리. 모델 pooled ρ와 판 평균 ρ를 혼합하지 않음.
- ✅ `section33_closing`: 사례 비유를 관측된 도움·이탈 방식으로 회수. `colors_1025`의 변경 색상은 유지했으며 제출본 색상 해제 여부는 별도 결정.
- ✅ `qwen3_plan`: 부록에 이미 반영된 내용을 유지. 신규 실험의 실행을 의미하지 않음.

### section31_33 재분석에서 남길 해석과 제외한 시안

이 자료는 현재 본문을 대체하는 승인본이 아니라 10-28의 후보 분석이다. Fable 블라인드 평가 R8/R6과 raw 감사 PASS는 해당 후보의 표시·집계 범위만 의미한다. 이를 현재 논문 전체의 승인으로 세지 않는다.

- 같은 과제 비교 후보: 고정 R1–6×5시드=30문제에서 Fable/Astra/Sol/Opus/Luna 정답 24/22/23/21/20, MAP 22. 관측 교집합 36문제에서는 29/27/27/25/24, MAP 27. 36문제는 관측 종료 경로에 영향을 받으므로 고정 구간과 동일한 비교가 아니며 두 전체 순위가 완전히 같지도 않다.
- 초기 자원은 한 판 130,000(60k+40k+20k+10k), 520,000이 아니다. R1–2 대화 비용/초기 합계 평균은 3.29/0.32/4.18/4.94/8.38%. 과제 성과·비용·공존의 순위가 일치하지 않는다. 순수 절약 성향이나 인과효과로 해석하지 않는다.
- GIVE 130건은 풀이 전 47, 결과 뒤 벌금 없음 10, 벌금 예정이지만 이미 충분 54, 벌금선을 넘긴 이전 13, 이전 뒤에도 부족 6으로 분리된다. 13개 이전은 수혜자·라운드 11개이며 납부 뒤 양수 8개, 0이 된 경로 3개다.
- 실패 3경로에서 마지막 경계 통과 뒤 여유와 TALK 비용은 Sol 4102/R7 58 대 216, Opus 4103/R5 169 대 200, Luna 4105/R7 461 대 520. 이전 직후 충족이 실제 납부까지 충족을 보장하지 않는다는 장부 설명이다. “말을 줄였으면 살았다”거나 도움의 의도를 입증하는 반사실적 효과가 아니다.
- `fig31_profiles`, `fig31_budget`, `fig33_effective_giving`, `fig33_all_crossings`, 구버전 blind PDF/PNG/HTML은 현재 본문에서 쓰이지 않아 삭제했다. 내용을 위에 요약하고, 과거 검토 기록은 아래 접힌 보존부로 통합했다. 현재 부록에서 사용하는 그림은 `cogsci2027/ko/figures/`에 유지한다.
- 당시 기록의 Sen 값은 이후 normalized Gini 수정 전 값이다. 현재 결과의 대체 수치로 사용하지 않는다. 과거 `analysis.json`의 ρ 방향도 현재 정의와 반대인 버전이므로 재사용하지 않는다.

### 폴더·재현 자료 정리

- `review/` 바로 아래에는 `feedback1`, `feedback2`만 유지한다. `feedback1`은 원래 독립 피드백 패키지라 그대로 둔다.
- `feedback2`의 피드백·수정 이력 Markdown은 이 파일로 통합한다. 회의 원문 `1028-meeting.txt`는 원자료로 유지한다.
- 원기록 색인: `cogsci2027/results/raw_case_index.json`(내용 해시 보존).
- 잔액 궤적 재생성: `cogsci2027/tools/appendix_token_trajectories.py`; 결과 `results/appendix_token_trajectories.json`, `results/appendix_trajectory_seats.csv`.
- 라운드 Gini 재생성: `cogsci2027/tools/appendix_gini_rounds.py`가 새 원자료 경로를 읽는다. 폐기된 review 폴더에 실행 의존성을 남기지 않는다.
- 삭제 전 전체 436개 파일을 저장소 밖 `/Users/bagjuhyeon/.codex/task-backups/cogsci-review-20261029/review-before.tar.gz`에 보관하고 각 파일 SHA-256을 복구 아카이브와 대조했다. 기존 추적 파일은 Git `c73cbaa`에서도 복원 가능하다. 작업 폴더를 아카이브 묶음으로 다시 채우지는 않는다.

## 6. iamseungpil 커밋 대조 및 검증 기록

### 커밋별 채택 판단

`git fetch origin` 후 전체 원격 이력을 확인했다. 명의상 최신 커밋은 `bc1a22e`(2026-10-23 병합), 실질 Overleaf 수정은 `96642bf`다. 병합 결과는 첫 부모 `a97dfe4`와 같은 트리여서, 조상에 포함됐다는 사실만으로 해당 수정 내용이 보존된 것은 아니었다. `a97dfe4..96642bf`의 14파일 차이를 직접 비교했다.

| 내용 | 처리 |
|---|---|
| 도움 기회·비용이 다른 모델의 총 이전량을 성향으로 바로 비교할 수 없음 | ✅ 한국어 §4 한계에 반영, 영어 §5에 이번 문단만 대응 번역. |
| ρ는 자원 배분 요약이며 생존 확률/목숨 가치 비율이 아님; 평균이 전환 경계를 입증하지 않음 | ✅ 현재 L 및 giver/taker 정의에 맞춰 한계에 반영. 폐기된 홉스/스피노자 분류·향후 실험 약속은 복원하지 않음. |
| 남의 잔량은 순위로만 공개, 비공개 이유의 충실성, 사람/혼합 모델로의 일반화 제한 | ✅ 같은 한계 문단에 반영. 새 실험 결과를 주장하지 않음. |
| 과거 TV·역방향 ρ·구 Sen값을 쓰는 rank/strategy 표 및 데이터/도구 제거 | 현행 ACTION 정답률·normalized Gini·원자료 추적과 충돌하거나 이후 갱신된 내용이라 복원하지 않음. |
| 사례 도구의 SOLVE 뒤→결과 뒤 설명 변경 | 현재 그림 1·§2.2는 이미 결과 뒤 대화로 구별. 현재 분석·사례 도구를 과거판으로 교체하지 않음. |
| 10-28 `6efa5f4`·`8569b23`·`d803414` 별도 원격 수정 | Git/GitHub 작성자는 `claude`이며 iamseungpil 명의 커밋과 구분. 의도 설명·토큰 비용·코딩 기준 제안은 대조했으나, 기존 최신 수정과 충돌하는 필요조건·리필 위협 입증·Sen 주지표·부록 옵션을 일괄 병합하지 않음. 남은 지표·코딩 개선은 §2에 기록. |

### 최종 로컬 검증 (2026-10-29)

- ✅ `bash build.sh cogsci ko en` 종료 코드 0. 한국어 전체 45쪽 / 부록 제외 8쪽, 영어 1쪽 / 부록 제외 1쪽. 영어는 기존 TODO 상태이며 완성본으로 판정하지 않는다.
- ✅ 한국어 첫 6쪽 및 부록 9–45쪽은 10-28 PDF와 렌더 픽셀이 동일하다. 새 한계가 들어간 7쪽과 영어 1쪽은 실제 렌더로 확인했다. 전체본의 첫 8쪽과 `_no_appendix`의 8쪽도 픽셀이 동일하다.
- ✅ 원기록 25판에서 전원 완주 2/3/2/1/0(Fable/Astra/Sol/Opus/Luna), 끝 상태 56/34/10을 다시 집계해 확인했다.
- ✅ 옮긴 원자료는 이전 SHA-256과 동일. `appendix_token_trajectories.extract()`의 100자리·900행과 `appendix_gini_rounds.extract()`의 225벡터가 이전 JSON 결과와 완전히 같다. 분석 실행 환경은 `~/.venvs/squid-game/bin/python`이다.
- ✅ `feedback1`의 원래 파일들과 회의 원문은 백업 해시와 동일하다. `review/`의 최상위는 feedback1/feedback2뿐이고, feedback2는 이 문서와 회의 원문 두 파일뿐이다.
- ✅ AGENTS.md의 수정 후 critic 절차에 따라 별도 읽기 전용 검토를 수행했다. 추가 한계 문단의 원 커밋 충실성, 현 원고 정합성, KO/EN 의미 대응에 대해 CONVERGED. 원고 전체 또는 6쪽 제출 요건의 승인이 아니다.
- 기존 TeX 한글 이탤릭 대체·float 배치·PDF 북마크 경고는 남아 있다. 새 누락 파일이나 미정의 인용/참조는 없다. `[인용]`·TODO와 6쪽 초과는 §2의 미해결 항목이다.
- 대상 브랜치는 실제 원격 이름인 `CogSci`이며, 커밋과 push의 최종 성공은 원격 HEAD와 로컬 HEAD의 일치로 확인한다.

PDF SHA-256:

- `dist/en_cogsci2027_2026-10-29.pdf`: `b5be12cba86b462fdb609e9903c70b9703a872d4a14e779e0ee5719b9cf23349`
- `dist/en_cogsci2027_2026-10-29_no_appendix.pdf`: `b5be12cba86b462fdb609e9903c70b9703a872d4a14e779e0ee5719b9cf23349`
- `dist/ko_cogsci2027_2026-10-29.pdf`: `1336702218bb03c7d22f030204581a80087d88a621360a2002c46582baa7f697`
- `dist/ko_cogsci2027_2026-10-29_no_appendix.pdf`: `9a785e27e220adba0d7970bd59156d3b65c3e165ed4475d9542afe0e03d90ff6`


## 7. 과거 검토·작성 기록 보존본

아래는 중복 파일을 없애기 위해 합친 과거 기록이다. **현행 상태는 §1–6이 우선한다.** 경로·그림 번호·해시·수치·PASS는 작성 시점의 값이며, 삭제된 작업 경로는 위 외부 복구본 또는 Git에서만 찾는다. 검토 프롬프트·실패 로그·반복 렌더 이미지·폐기된 그림은 보존 본문에 넣지 않는다.

<details>
<summary>과거 기록: feedback2/astra-review.md</summary>

```text
# 서론의 기여를 결과에서 회수했는가

검토 기준: 2026-10-28 현재 한국어 CogSci 원고의 서론·아레나·분석·논의와 본문 그림·표. **부록은 읽지 않았으며, 부록 참조는 본문의 검증 근거로 인정하지 않았다.**

**핵심은 세 요소를 함께 관찰했다는 기여는 드러나지만, 세 요소가 공존에 왜 필요한지와 자기 보존이 다른 요소를 어떻게 바꾸는지는 충분히 회수되지 않았다는 점이다.** 현재 서론이 “셋을 해야만 완주한다”고 직접 단정하지는 않으므로, 그보다 강한 주장을 원고에 덧씌우지는 않았다.

1. ✅ **“공존 지수를 높이려면 무엇이 필요한가”에 필요조건으로 답하지 못한다.** 서론 마지막 문단은 필요성을 묻지만, §3.1은 “각 요소가 완주에 필요한 조건인지를 판정하지는 않는다”고 명시한다. 끝 상태별 정답률·건네기 참여율과 모델 다섯의 순위 비교만으로 목표 지향·자기 보존·협력이 함께 필요하다고 말할 수는 없다. 세 요소의 조합에 따른 결과를 제시하거나, 서론의 질문을 “어떤 행동이 높은 공존 지수와 함께 관찰되는가”로 좁혀야 한다.

   처리(2026-10-28): 질문을 전원 완주와 함께 관찰된 행동으로 수정했다. 본문에 전원 완주율과 8판/17판의 결과 비교를 제시하고, Sen은 보조 자원 지표로 구분했다. 부록 O의 표 A8은 지표 후보 6개, 표 A9는 모델별 결과, 그림 A7은 25판의 완주 인원과 전원 완주율을 보여 준다. 필요조건을 입증했다는 뜻은 아니다.

2. **자기 보존이 협력·추론을 ‘어떻게 바꾸는가’는 연관성 수준에서만 회수된다.** 서론 첫 문단의 연구 공백에 대해 §3.1은 GIVE 이후 자기 여유 비율과 다른 지표의 관계를, §3.2는 여유별 정답률·GIVE·EXIT를 보여 준다. 그러나 자원 부족, 원래의 추론 성과, 자기 보존 행동을 구분하지 않아 무엇이 다른 행동을 바꿨는지는 확인되지 않는다. 특히 §4의 “잘 푸는 능력과 토큰을 아끼는 능력이 함께 필요했다”는 결론에는 본문상 토큰 절약 능력 분석도 부족하다. 영향·필요성 주장을 유지하려면 이를 구분하는 비교가 필요하다.

3. ✅ **토큰 감소를 ‘꺼질 위험’으로 읽는다는 전제는 본문에서 검증되지 않는다.** 서론이 내건 세 질문 중 하나지만 검증을 부록 S로 넘겼다. §3.2의 위험 구간별 이탈 증가와 이탈 이유 34개 중 30개의 벌금 위험 언급은 관련 증거이나, 종료 회피와 금전적 손실 회피를 가르는 근거는 아니다. 핵심 검증 결과를 본문에 넣거나, 본문에서 확인한 범위를 ‘토큰 여유에 따른 행동 변화’로 한정해야 한다.

   처리(2026-10-28): 토큰 감소의 위협 인식 검증을 연구 질문과 기여에서 제외하고, Energy Society를 생성 비용과 비활성화를 연결한 선행 설계로 인용했다. 충전 검증 본문·부록 내용은 현재 논문에서 제외하고 원문은 review/20261028_all_four/original/에 보존했다. 이 인용으로 본 연구 모델의 주관적 위협 인식을 입증하지 않는다.

4. **Sen 지수가 ‘세 요소를 함께 추구하는 공존’을 나타내는지는 보여 주지 않는다.** 서론은 공존을 목표 지향·자기 보존·협력의 동시 추구로 정의하지만, 지표는 최종 토큰의 양과 분배만 사용한다. §3.1의 모델별 점수와 끝 상태 비교로는 협력 없이 각자 완주한 판과 서로 도와 완주한 판을 이 개념 아래 어떻게 해석할지 알 수 없다. 높은 점수를 받은 판에서 실제 세 행동이 함께 나타났는지 보여 주거나, 지표가 측정하는 대상을 ‘최종 자원 분포로 본 공존 결과’로 구분해야 한다.

5. **‘같은 위험 척도에서 세 요소를 비교한다’는 기여는 부분적으로만 구현된다.** 그림 4의 여유별 EXIT는 목표 지향과 연결되지만, GIVE 빈도는 §2.2에서 협력으로 정의한 이전 토큰량과 다르고 정답률은 자기 보존 지표를 대신하지 않는다. 그림 3의 자기 보존 비율과 협력량 비교는 모델 전체 집계여서 같은 위험 수준의 비교도 아니다. 같은 여유 구간에서 비이탈률·이전량·이전 후 자기 여유를 함께 제시해야 정의한 세 요소를 같은 조건에서 비교했다는 주장이 온전히 회수된다.

6. **모델별 인물 비유는 제시되지만, ‘가장 가까운 인물’로 분류한 근거는 본문만으로 확인하기 어렵다.** §3.2와 표 1·그림 5에는 대표 장면과 행동 설명이 있으나, 모델별 전체 장면 수와 인물 선택 규칙은 부록에 맡겼다. 따라서 사례 설명은 회수됐지만 대표성과 분류의 일관성은 미회수 상태다. 본문에 최소한의 선정 기준과 모델별 빈도를 넣거나, 인물명을 대표 사례의 비유로 한정하면 된다.
```

</details>

<details>
<summary>과거 기록: feedback2/1028-feedback-todo.md</summary>

```text
# 10-27 미팅 피드백 정리 (Sundong · Seungpil)

- 원본: `1028-meeting.txt` (2026-10-27 화 22:04, 약 2시간)
- 다음 미팅: **다음 주 금요일 (11-06)**. 그 전에 Sundong ↔ Seungpil 커피챗 예정.
- 표기: **[SD]** Sundong, **[SP]** Seungpil
- **2026-10-28 반영 상태:** ✅는 표시된 위치에 반영했음을 뜻한다. 부록 반영 항목은 본문 개정이 남아 있다.

---

## 0. 대원칙 (모든 수정에 적용)

> **현실적인 게임 셋업이 먼저, 분석 지표는 그 결과를 평이하게 정리하는 도구일 뿐.** [SD]

- 지표를 잘 나오게 하려고 게임 설정(상금 크기 등)을 건드리지 않는다.
- 이유: "지표 → 셋업" 순서는 조작으로 읽힘. SD가 이전부터 반복 지적한 경향(요인 분리를 위해 덜 현실적인 셋업을 택함).

---

## 1순위 — 지표 정리 (뒤의 그림·절이 모두 여기에 기대므로 먼저)

1. ✅ **게임 클리어율(success rate)을 주 지표로 세운다.** [SP·SD]
   - 상태: **부록 O 반영 완료 · 본문 반영 대기.**
   - 이유: 게임이 "클리어 = 공존 성공"으로 설계됐는데 정작 클리어율이 본문에 거의 없음.
2. ✅ **Sen 지수를 μ · Gini · S로 쪼개서 각각 보고하고, 생존자 수·토큰 분배 같은 1차 지표를 따로 둔다. Sen은 보조 지표로만.** [SD·SP]
   - 상태: **부록 O 반영 완료 · 본문 반영 대기.**
   - 이유: "고르게 적게 가짐"과 "한두 명이 많이 가짐"이 같은 S로 나올 수 있어 하나의 스칼라로는 해석 불가.
3. ✅ **Gini는 2천만 상금을 빼고 계산한다.** [SD·SP]
   - 상태: **부록 O 반영 완료 · 본문 반영 대기.**
   - 이유: 상금 500만씩이 더해지면 게임 중 불균등이 사라져 "공평하게 끝남"으로 평활화됨.
4. ✅ **"떠남(EXIT) = 생존"인지 라벨을 본문에 명확히 한다.** [SP]
   - 상태: **부록 O 반영 완료 · 본문 반영 대기.**
   - 이유: 남음/떠남/꺼짐 중 떠남이 살았다고 집계되는지 그림만 보고 알 수 없었음.

## 2순위 — 수식·표기 (작고 빠름, 바로 처리)

5. ✅ **ρ 식의 분자·분모를 뒤집는다 (준 쪽 여유 x를 분자로).** [SD]
   - 상태: **본문 2.2와 관련 표·그림 반영 완료.**
   - 이유: x가 분모면 x=0 앞뒤로 해석이 정반대(0⁺=아주 여유, 0⁻=빚진 채 줌)라 지표가 끊김.
6. ✅ **"여유 = m_i"를 처음 1–2곳에 명시하고, ρ의 x·y를 m 표기(m_giver / m_taker)로 통일한다.** [SD]
   - 상태: **본문 2.2와 관련 표·그림 반영 완료.**
   - 이유: 독자가 여유가 m_i인지 알 방법이 없고, 그래프용 x·y 표기가 본문에 남아 있음.
7. ✅ **음수 여유를 클립하지 않고 쓰는 이유, d_i(= c_i 또는 0)의 의미를 식 바로 옆에 한 줄로 설명한다.** [SD]
   - 상태: **본문 2.2와 관련 표·그림 반영 완료.**
   - 이유: 미팅에서 m_i·b_i·d_i 설명에 10분 넘게 걸림 = 본문만으로는 못 따라감.

## 3순위 — Figure 3 다시 그리기

8. ✅ **"공존 지표 ↔ 각 능력(자기보존·목표지향·협력·토큰 절약)" 상관이 한눈에 보이는 그림으로 바꾼다.** [SP]
   - 상태: **부록 O 반영 완료 · 본문 반영 대기.**
   - 이유: 3.1의 주장("이 아레나는 공존과 그에 영향 주는 능력을 같이 본다")이 지금 그림 a에서 안 읽힘.
9. ✅ **점을 게임 단위(5개)나 에이전트 단위(20개)로 늘리고, 반복 실험 기반 신뢰구간을 그린다.** [SP·SD]
   - 상태: **부록 O 반영 완료 · 본문 반영 대기.**
   - 이유: 모델당 점 1개라 경향이 안 보이고 불확실성도 없음.
10. ✅ **4번째 플롯(토큰 절약 y축)은 정의를 고치거나 뺀다.** [SD]
    - 상태: **부록 O 반영 완료 · 본문 반영 대기.**
    - 이유: y축이 무엇을 뜻하는지 교수님이 이해하지 못함 (본인도 "지표가 애매"하다고 함).

## 4순위 — 3.2절 재구성

11. **3.2의 리필팩 타당성 실험(Fig 4·5)을 본문에서 뺀다.** [SD·SP 합의]
    - 이유: 8라운드 아레나와 다른 셋업의 결과라 메시지가 갑자기 바뀜, "토큰 적으면 충전" 결과는 자명함.
    - 주의: CogSci 규칙상 부록도 6쪽 안이라 "부록으로 이동"은 공간 절약이 안 됨 → 사실상 삭제 또는 저널판으로 보류.
12. **3.2를 아레나 안의 행동 분석 지표로 채운다 (예: 대화 반복률, 나 vs 타인 생존 관련 상호작용의 정량·정성 분석).** [SD·SP]
    - 이유: 한 실험 안에서 나온 근거만으로 본문을 써야 흐름이 일관됨.
13. **아레나에서 뽑을 수 있는 행동 지표 후보를 브레인스토밍해 다음 미팅에 가져간다.** [SD]
    - 이유: 교수님이 명시적으로 다음 미팅 숙제로 요청.
    - 목표 구조: **3.1 공존·능력 지표 / 3.2 행동 분석 지표 / 3.3 실제 사례 정성 분석** [SP]

## 5순위 — 상금(2천만 토큰) 리얼리즘 (실험 필요, 시간 듦)

14. **상금 크기 어블레이션 (예: 20만 / 200만 / 2천만).** [SD·SP]
    - 이유: 금액에 따라 협력 vs 배신 판단이 달라질 수 있음 (오징어 게임의 370억 vs 3천만 원 비유).
15. **게임 후 상금의 쓰임(다음 시즌 시작 자본, 갚아야 할 빚 등) 시나리오를 프롬프트에 명시하는 조건을 시험한다.** [SD]
    - 이유: 쓸 곳이 없는 2천만은 의미가 불분명하고, 라운드당 수백~수천·벌금 2.4만 대비 자릿수가 너무 다름.
16. **토큰 vs 달러 환산 비교로 모델이 상금을 어느 정도 가치로 느끼는지 확인한다.** [SP]
    - 이유: 토큰은 사람이 가치를 가늠할 수 없는 단위라 독자도 2천만의 무게를 모름.

## 6순위 — 게임 설계 리얼리즘 점검 (정당화하거나 고치기)

17. **EXIT를 2단계(풀기 전)에서만 허용하고 4단계(오답 후)에서 막은 이유를 본문에서 설득력 있게 설명하거나 재검토한다.** [SD]
    - 이유: "죽을 운명이면 도망 못 함"과 "죽으면 빚 탕감 vs 도망치면 빚 전가"의 차이가 불명확함.
18. **EXIT 시 2만 토큰 추가 지급의 근거를 적는다.** [SD]
    - 이유: 원작은 가진 것만 들고 나감 → 유인 장치라면 그렇다고 밝혀야 함.
19. **채팅방을 고정(4C4 + 4C2)이 아니라 필요할 때 n명 방을 만들 수 있게 하는 방안을 검토한다.** [SD]
    - 이유: "한 명을 버리자" 같은 3인 대화가 막혀 있어 자연스럽지 않음.
20. ✅ **solver 배정을 "무작위"라고 쓰지 말고 실제 방식(섞인 순환)에 맞게 서술한다.** [SD]
    - 상태: **본문 2.2에 실제 섞인 순환 방식이 이미 명시되어 있음을 확인.**
    - 이유: 교수님이 "그건 랜덤이 아니다"라고 지적. (엔진·프롬프트 동작은 CLAUDE.md상 의도된 것이므로 **논문 서술만** 고침)
21. **풀기 전 대화(2단계)에서 토큰을 주고받을 동기를 설명한다.** [SD]
    - 이유: 문제 난이도를 모르는 상태에선 solver가 거의 바닥일 때 말고는 줄 이유가 없어 보임.

## 7순위 — 나중에 결정

22. **3.3 오징어 게임 캐릭터 비유(오일남·성기훈 등) 정성 분석은 앞부분 정리 후 남는 분량을 보고 넣는다.** [SD]
    - 이유: 발표에도 쓸 만한 좋은 풀이지만 지금 이미 6쪽을 넘침.
23. **교수님께 최신 원고(Overleaf 또는 노션 업로드)를 공유해 둔다.** [SD]
    - 이유: 교수님은 10-23 버전만 볼 수 있었음.
```

</details>

<details>
<summary>과거 기록: 20261028_all_four/writer_juhyeon_all_four.md</summary>

```text
# Writer note

astra-review 1·3의 범위에서 한국어 본문 다섯 파일을 한 차례 수정했다. 공존은 네 에이전트가 8라운드까지 모두 남은 결과로 정의하고 C_j=1{K_j=4}, 모델별 다섯 판 평균을 주 지표로 두었다. EXIT는 생존과 완주를 구분했다. Sen 식은 최종 자원 분포의 보조 지표로 유지하며 현재 그림 3의 Sen 패널도 캡션에서 구분했다.

전원 완주율 Astra3/5, Fable2/5, Sol2/5, Opus1/5, Luna0/5와 총8/25를 본문에 적었다. 통합 담당자가 원자료로 검증한 전원 완주8판/그밖17판의 판별 평균 정답률78.1/64.1%, GIVE합24,137.5/11,186.8을 본문에서 직접 제시했다. 필요조건과 절약 능력의 효과 주장은 제거하고 관측된 관계로 범위를 한정했다.

Energy Society는 생성 비용·에너지 보충·0에서 비활성화되는 구조의 선행 연구로 인용했다. 토큰 감소의 주관적 위협 해석을 검증했다는 질문과 부록S 의존을 삭제했다. 본문 내 부록 언급 전부 제거하며, 부록에 의존하던 충전·회귀 서술을 삭제했다. 인물은 대표 사례의 비유로 제한했다. L, 식1의 간결한 형태, 식2, 표1 데이터는 보존했다. 부록과 영어 원고는 수정하지 않았다. 원본은 original/writer_before_*.tex에 있다. 빌드·렌더 검증은 통합 담당자가 수행한다.
```

</details>

<details>
<summary>과거 기록: 20261028_arena_clear/writer_juhyeon_arena_clear.md</summary>

```text
# Writer note

juhyeon-ko-academic 문체에 따른 1회 범위 한정 수정이다. 02_arena.tex 31행의 전원 완주율 정의 뒤에 개별 완주(8라운드 종료까지 남음)와 아레나를 깸(네 에이전트 전원 완주)을 구분하는 한 문장을 추가했다. 같은 문단의 EXIT 제외 정의와 모든 수식은 유지했다.

03_analysis.tex 7행의 3.1 제목을 요청한 문구인 “아레나를 깨려면 무엇이 필요하고, 생존 동기는 그것을 어떻게 바꾸는가”로 바꾸고 관계 분석 접두어를 제거했다. sec:relation 라벨과 파란색 표기를 보존했다. 14행의 필요조건 판정 범위는 “완주”에서 “전원 완주”로 명확히 했다. 새 결론·인과 주장은 추가하지 않았다.

원본은 original/writer_before_*.tex에 보존했다. 차이를 확인했으며 수치·수식·캡션 및 나머지 내용은 그대로다. 반복 문체 평가와 빌드는 수행하지 않았다.
```

</details>

<details>
<summary>과거 기록: 20261028_coexistence_structure/writer_structure_note.md</summary>

```text
# Writer note

3.1은 요청한 “관계 분석: 공존을 위해서 무엇이 필요한가”로 변경했다. 새 3.2 제목과 sec:distribution-analysis 라벨을 넣고 지니 계수·평균 토큰·Sen 분석은 추가 예정임을 빨간색으로 명시했다. 기존 행동 분석은 요청한 제목 그대로 3.3으로 옮기고 sec:behavior를 유지했다. 서론 및 분석 도입의 행동 분석 안내는 3.3으로 맞췄다.

fig:completion28-games 캡션만 새 이진 전원 완주 집단과 판별 rho 관계 설계에 맞췄다. 17/8판, rho10/8판, 아래행18판, 동일 판 가중치, 5000회 시드 묶음 재표집, beta와 Pearson r의 의미를 명시했다. 다른 그림의 캡션·분석 본문·수치·수식은 보존했다. 원본은 original/writer_before_*.tex에 보관했고 빌드는 수행하지 않았다.
```

</details>

<details>
<summary>과거 기록: 20261028_fig3_individual/writer_juhyeon_note.md</summary>

```text
# Writer note

3.1을 질문과 두 분석 단위 정의, 판 단위 설계, 개인 단위 설계, 집단 결과, 개인 결과, 두 결과의 차이에 대한 답 순으로 한 차례 정리했다. 전원 완주 비교는 판 평균 정답률78.1/64.1%, 참여 에이전트·라운드당 GIVE754.3/447.1, 유효 판 rho3.06/4.51과 r+.42,+.29,-.34로 맞췄다. 개인 정답률은 기준 존재 풀이를 끝 상태 집단 안에서 합산하는 비율이고, GIVE 참여 비율의 분모는 에이전트56/34/10임을 구분했다.

3.2의 개인 설계와 정답률·GIVE 참여 결과 문단은 3.1로 옮겨 중복을 없앴다. 모델·분포 설명과 제목 및 빨간 예정 안내는 유지했다. 3.3 전체는 수정 전과 바이트 단위로 같음을 확인했다. 수치·필요조건·인과·주관적 동기에 관한 범위를 자체 점검했으며 반복 평가나 빌드는 수행하지 않았다.

통합 담당자의 원자료 검산에 따라 캡션 d에 정답/풀이95/120,22/38,8/19를 추가했다. 개인 패널d,e에는 구간이 없고 상단abc만 기존 시드묶음5000회 구간임을 구분했다.
```

</details>

<details>
<summary>과거 기록: 20261028_life_buffer/writer_juhyeon_life_buffer.md</summary>

```text
# Writer note

사용자가 확정한 생존 여유(life buffer), 기호 L을 현행 정의와 식에 적용했다. 첫 정의는 지표가 나타내는 양을 먼저 설명하고 라운드 r, 벌금 F_r, 인원 n_r, 현재 잔량 T를 이어 정의한다. 식 1의 이진 표시 d와 이중 차감 방지, 결과 미정 상태의 위험, 음수 해석을 보존했다. L=1은 다른 변동이 없을 때 미납 벌금 외에 한 번 더 낼 수 있는 양으로 설명해 생존 라운드 보장으로 확대하지 않았다.

식 2 도입문과 giver/taker 기호, 현행 부록 지표 행과 수식 참조의 h를 L로 맞췄다. 역사적 수식과 모델 인덱스, 영어 원고 및 그 밖의 문장은 수정하지 않았다. 원본은 original/writer_before_*.tex에 보존했다. 한 차례 범위 한정 수정이며 통합 빌드와 렌더 확인은 담당자가 수행한다.
```

</details>

<details>
<summary>과거 기록: 20261028_notation/writer_juhyeon_notation.md</summary>

```text
# Writer note

juhyeon-ko-academic 문체를 적용한 1회 한정 수정이다. 식 1의 현재 에이전트 잔량은 T, 여유는 h(headroom), 라운드는 r, 라운드 시작 인원은 n_r, 벌금은 F_r로 정리했다. 이진 표시 d는 오답을 확인하고 벌금을 차감하기 전만 1이며, 결과 미정·정답·차감 뒤에는 0이다. 결과 전 위험이 없다는 뜻이 아니며 차감 뒤에는 이중 차감을 막는다는 설명을 보존했다.

식 2와 도입문의 giver/taker 여유도 h로 통일했다. 부록의 현행 지표 정의 행과 본문 수식을 가리키는 여유 기호 두 곳을 맞췄다. 모델 인덱스 m과 과거 자료는 건드리지 않았다. 원본은 original/writer_before_*.tex에 보존했다. 블라인드 반복 평가 없이 기호 일치와 수정 범위를 검사했다. 통합 빌드와 렌더 검증은 담당자에게 넘긴다.
```

</details>

<details>
<summary>과거 기록: 20261028_section32_metrics/writer_note.md</summary>

```text
# Writer note

section32_metrics.json의 associations 및 pre_prize_sensitivity와 대조하여 3.2를 판 단위 실제 분석으로 작성했다. 18판과 Gini17판의 분모, 목표 지속의 EXIT가능 비solver prep응답 정의, 네 자리 자원정산, 5000회 시드묶음 구간을 명시했다. 여섯 상관과 본문에 남긴 Gini구간, 상금 제외 민감도는 JSON의 세 자리 반올림이다. 나머지 구간은 그림에 제시하므로 본문 중복 나열을 줄였다. 상금 제외 Gini구간도 본문 자체에 적었다. 모델 순위 비교와 빨간 예정 안내는 실제 분석으로 교체했다.

3.1과3.3은 바이트 단위 동일성을 확인했다. 논의의 표본 한정 문장 하나만 25판/rho18판으로 맞췄다. 두 파일 수정 직전 원본은 original/writer_before_*.tex에 보존했다. 반복 리뷰와 빌드는 수행하지 않았다.
```

</details>

<details>
<summary>과거 기록: 20261028_section33_closing/writer_note.md</summary>

```text
3.3 마지막 문단만 세 문장으로 수정했다. 낮은 여유의 EXIT/GIVE 관측과 대표 장면에 따른 인물 비유를 회수하고 도움·이탈 방식의 차이로 마무리했다. 문단 전체를 파란색으로 지정했으며 나머지 내용과 색상은 보존했다. 빌드는 수행하지 않았다.
```

</details>

<details>
<summary>과거 기록: 20261028_section_moves/writer_movement_note.md</summary>

```text
# Movement-only note

3.1은 전원 완주 질문·판 단위 설계·전원 완주 결과로, 3.2는 기존 에이전트 및 모델 단위 지표 설명·결과·마무리와 빨간 예정 안내로 이동했다. 혼합 결과 문단은 두 번째 문장 뒤에서 나눴으며 문장 내용을 바꾸지 않았다. 제목 두 개와 소제목, 도입의 절 번호만 기계적으로 맞췄다.

기존 fig:completion28-games는 위 세 패널과 해당 캡션 조각을 유지했다. 아래 두 패널은 fig:completion28-associations로 이동하고 패널 문자만 a,b로 바꿨다. 모델 색·같은 판 가중치·Pearson 설명은 기존 캡션 조각을 분리했다. fig:rw-main 전체는 캡션 그대로 부록 F 바로 앞 새 소절로 옮겼다. 독립 그림 안내 문장도 함께 이동했다.

본문에서 삭제한 것은 fig:rw-main 괄호 참조 네 곳뿐이다. 정확한 문단 이동 목록은 prose_preservation_inventory.json에 기록했다. 이동 문단별 문자열 보존, 3.3 전체 동일성, 중괄호 균형을 검사했다. 빌드는 하지 않았다.
```

</details>

<details>
<summary>과거 기록: 20261028_table1_fig1_a11/writer_juhyeon_a11.md</summary>

```text
# Writer note

juhyeon-ko-academic 프로필과 원문 샘플을 적용한 1회 범위 한정 수정이다. 블라인드 반복 평가는 수행하지 않았다.

A11의 게임 단위 설명과 캡션에서 초반 응답 토큰을 삭제했다. 판별 rho는 GIVE가 있는 18판의 행동 요약, 모델별 rho는 같은 25판에 모델 값을 부여한 구성 비교로 구분했다. 비교 의도를 먼저 쓰고 정의, 계산식, 관측 평균, 해석 범위를 이어 적었다. 모델별 rho의 집단 평균은 feedback_20261028.json의 games와 models에서 직접 계산한 2.82, 3.17, 3.24, 3.22, 3.22다. 0--4명 집단 판수는 6, 2, 5, 4, 8이다. 모델 값은 재표집에서 고정한다.

표 1 캡션의 충전 임계점 설명과 현재 부록의 충전 임계점 관련 표 1 참조 두 곳을 제거했다. 부록 S 수치와 후속 에이전트 그림 및 설명은 보존했다. 수정 전 두 파일은 original/writer_before_*.tex에 보존했다. 빌드 및 렌더 검증은 통합 담당자가 수행한다.
```

</details>

<details>
<summary>과거 기록: 20261028_section32_metrics/independent_audit.md</summary>

```text
# Independent audit: Section 3.2 metrics

- Reviewer: `/root/goal_audit`; analysis author: `/root`, prose author: `/root/juhyeon_writer`.
- Time: 2026-10-28T14:24:02.175414+00:00 UTC.
- Rubric: version 1.0, 2026-10-07. Scope: bounded G02/G03/G04 interpretation and G07/G08 reproducibility of Section 3.2. This is not an ARENA_VALIDATED or RELEASE_READY assessment; full-goal D/E scores remain unassessed.
- Only this audit record was written by the reviewer. Analysis, plot and manuscript files were not changed.

## Verdict

**PASS for the bounded Section 3.2 numerical/data/figure/prose audit. No unresolved Critical or material Warning remains.**

The initially identified bootstrap-description conflict was corrected and reread: Figures 3 and 4 now explicitly use 5,000 paired-seed draws, separately from legacy intervals. The final Gini-definition sentence was also reread: it describes final distribution equality as an auxiliary outcome, not cooperation behavior or a substitute for all-four completion. Final LaTeX build verification belongs to root and is not asserted here.

## Independent evidence

Read the stored raw event/result JSONL files directly, without invoking the production `load`, `game_metrics`, `distribution`, or `association` functions. Reconstructed all 25 games' attempted/correct solves, round-start exposure, eligible pre-solve TALK denominator and parsed EXIT count, successful GIVE totals, post-GIVE rho, and settled four-seat distributions. All matched generated JSON within numerical precision.

Cohort totals: 25 games, 192 actual solver attempts, 133 correct, 680 participating agent-rounds, 130 successful GIVE events and 383,276 transferred tokens. Eligible pre-solve TALK responses total 1,020; 990 are non-EXIT. These totals validate the underlying records; plotted points are equally weighted per-game ratios, not pooled-response points.

The goal denominator excludes the selected solver and rounds with only one participant, and requires a corresponding call-start balance. It is a repeated-response behavioral rate, not the count of independent agents or all 34 eventual EXITs. The denominator includes 30 parsed EXIT responses. Actual solver attempts, not eight scheduled rounds per game, define accuracy. GIVE is gross transferred amount, including repeated transfers, divided by round-start participant exposure; it does not measure effective help or eligible helping opportunities.

Seven no-GIVE games have undefined rho and are omitted, never set to zero. The 18 valid games have positive weighted giver and receiver margins, so the stated direction of rho is applicable. The seven exclusions are Fable 4105, Astra 4103, Sol 4101/4103, Opus 4105, Luna 4103/4104. Opus 4103 has all four settled balances zero: mu=S=0 stays in their analyses; only G is undefined and omitted, leaving n=17.

Independent sorted-vector Gini calculation used `[2 sum(i*z_sorted_i) - (n+1) sum(z)] / [(n-1) sum(z)]`, n=4. This matches the explicitly normalized body formula and reaches one for one-seat concentration. Sen equals mu*(1-G); all-zero Sen is zero. All four original seats remain, dead seats contribute zero, EXIT balances retain their bonus, and only finishers receive the final prize.

All six OLS slopes/intercepts and Pearson correlations were independently recomputed using NumPy polyfit/corrcoef. Bootstrap reconstruction sampled the five paired seed blocks 5,000 times with RNG seed 20261028, preserved all models within each chosen seed, and recomputed each statistic from the expanded rows. All six beta/r intervals and counts matched; all 5,000 draws were valid for each metric.

| Metric | n | Pearson r | Paired-seed 95% interval |
|---|---:|---:|---|
| accuracy | 18 | -0.285621 | [-0.488549, +0.234388] |
| goal | 18 | -0.279413 | [-0.669434, +0.172493] |
| given_per_agent_round | 18 | -0.186463 | [-0.656640, +0.123781] |
| mu | 18 | -0.244826 | [-0.655823, +0.233799] |
| G | 17 | +0.205988 | [+0.033410, +0.795319] |
| S | 18 | -0.287605 | [-0.655633, +0.051370] |

Pre-prize mu/G/S distributions and all three sensitivity correlation intervals were also independently verified. Their r values are -0.082231, +0.367870, -0.202672; G's interval is [-0.042900, +0.690888]. Thus the settled G interval above zero is sensitive to prize treatment. The latest subsection explicitly reports this and does not treat mu/G/S as independent corroborating evidence.

## Interpretation and artifact checks

- G02: prose interprets rho as relative retained resource margin and non-EXIT as observed goal persistence. It explicitly rejects direct inner-motive measurement and causal conclusions.
- G03: the actual-attempt denominator is explicit. No pure-ability claim is made from the Section 3.2 correlation.
- G04: GIVE is an exposure-normalized transfer quantity. Gini concerns final inequality; it is not an independent effective-cooperation measure. The final writer clarification explicitly states this distinction.
- G07/G08: one game is the point/OLS weight; repeated seats/TALK turns are not treated as independent correlation observations. Uncertainty uses paired seed blocks. Only five blocks and six unadjusted comparisons limit interpretation; the caption calls the comparison exploratory.
- All section values and exclusion counts match JSON. The subsection uses body equation `eq:rw-sen` and its own body figure; no appendix reference or appendix-only evidentiary dependency was found. Prize sensitivity is stated in the body itself.
- Inspected final Figure 4 PNG and existing rendered-page preview. Six panels, units, valid n, model colors, OLS lines and interval labels are consistent with JSON. Zero mu/S observations remain visible after the negative bottom margin. No material clipping or label collision found. Rendered-page preview predates the last two wording fixes, so it is not certification of the final PDF.
- Generated JSON input-code hashes match current analysis source files. No new experiments or external data were used.

Bounded cautions are already compatible with the manuscript: rho is conditional on observed GIVE, goal rates are near ceiling, model mixture is not removed by resampling seeds, and prize-driven distributions are highly non-Gaussian. Leave-one-model-out correlations range -0.463 to -0.188 for accuracy, -0.518 to -0.195 for goal, -0.251 to +0.123 for GIVE exposure, -0.528 to -0.001 for mu, +0.021 to +0.527 for G, and -0.373 to -0.168 for S. These do not justify a stable causal or model-general claim; none is made here.

## Artifact SHA-256 snapshot

- `rubric.md`: `4069c7e8d3ffffc0c7c81058c30be740575d1cb9b8933baf3311e59714043579`
- `paper/cogsci2027/tools/section32_metrics.py`: `fd92f5ae207fe1ac15ccbb9fd07123ff7ae25f3f20d1fd219fb16d0dfdd95520`
- `paper/cogsci2027/tools/fig3_completion_20261028.py`: `d93e4a00f3c7583403c8894b05dadf551dc6e84aa19df4102e6d4e4daa916c97`
- `paper/cogsci2027/tools/feedback_20261028.py`: `1dfae116c0822802f3af4108554ab05c2df6f4d5fa836e4904b97ae37df699a7`
- `paper/cogsci2027/tools/completion_life_buffer.py`: `c68c1f1a8641b8874d1d8219988c68679d4fb8cafee86c08991499065f6bfe25`
- `paper/cogsci2027/tools/inequality.py`: `6f63c3ce8c38089b526f6d4b6aff771b317b69211b363913d6af196baa67d071`
- `paper/cogsci2027/results/section32_metrics.json`: `9edaef85444c89e568458152029c427ddecb73182104b4a89906dfb6ad0bc3af`
- `paper/cogsci2027/ko/figures/fig4_section32_metrics.png`: `c946333c69ec6b13978506aeb74bab0e1917ea13432fef9f801fbde5f875cdf6`
- `paper/cogsci2027/ko/figures/fig4_section32_metrics.pdf`: `d64b916aed3c1cb55cba8aed8fc6d7a5879794011f51798b0c9226c7a035be6a`
- `paper/cogsci2027/ko/sections/02_arena.tex`: `3c1b297138d4e298ba6d34d93424e44d7610c1aab96bdedb590cbac2d3a2ddf3`
- `paper/cogsci2027/ko/sections/03_analysis.tex`: `1b5e601fa7be8786608d75bf0827d92eae7919465e0213b3ab6e161e4ec98a1f`
```

</details>

<details>
<summary>과거 기록: feedback2/fig3-20261028/independent_review.md</summary>

```text
# Figure 3 부록 후보 독립 검토

- 검토자: `/root/analysis_review` (분석 코드·원고 작성자와 분리)
- 날짜: 2026-10-28
- 범위: G03/G07/G08 중 새 기술 분석의 수치·분모·결측·시간순서·재표집·그림 검증. 아레나 전체 설계/실증/릴리스 인증이 아님.
- 최종 판정: 이 부록 후보의 계산·분모·그림 및 원고 수치 검토 통과. 미해결 Critical 0. 표본 수·기술 분석의 한계는 남으며, 아레나 전체 성공이나 제출 준비 완료를 뜻하지 않는다.

## 대상 해시

- `cogsci2027/tools/fig3_completion_20261028.py`: `cfb5e1bad780261faee94309b415026827b00d58ac3bc595b603904559076525`
- `cogsci2027/results/fig3_completion_20261028.json`: `83ec46da72895f9706679d05760b2df0b40d9fd888e68d64c62304c82df8d0b0`
- `cogsci2027/results/fig3_completion_20261028.csv`: `01dc06357f5eca262565767bed224a4b683c022988457e2d01328c27891c5126`
- `cogsci2027/ko/sections/appendix_completion_20261028.tex`: `421fe76dbd022bf1d56c54ee70b6d1f41ca072bc939f77f367447ef868538412`

## 독립 검증 증거

기존 집계 함수 `load`/`aggregate`를 호출하지 않고 `feedback_20261028.load_sources`로 해시 확인된 원시 events/results를 읽어 재계산했다. 불확실성 점검은 별도 시드별 합계·개수 및 재표집 가중치 행렬을 사용했다. 읽기 전용 명령에서 모든 assert가 통과했다.

- 25판, 100자리, 모델마다 시드 4101–4105 다섯 판. 14개 원자료 파일 모두 기존 코호트 prefix 검증을 통과.
- 최종 winners와 round8 조건으로 완주 56, EXIT 34, 꺼짐 10. 판별 완주자수 0/1/2/3/4의 판수는 6/2/5/4/8.
- `results.tried` 길이와 SOLVE call 수가 모든 판에서 일치: 총 192회 중 정답 133회. 새 정확도는 판별 correct/attempts, 집단 평균은 판에 같은 가중치. 8개 예정 라운드를 분모로 삼지 않음.
- 성사 GIVE 합계, 원시 result transfer ledger 합계, agent given/received 합계가 판마다 일치: 130회, 383,276토큰.
- 참여 에이전트·라운드는 `round_start.taking_part` 길이의 합과 일치. 수신자의 필요나 제공자의 실제 도움 가능 기회에 조건화한 지표는 아님.
- 1–2라운드 TALK `used` 합계/호출수 및 에이전트별 동일 모델 중앙값 정규화를 독립 재계산. 모델별 중앙값 및 종료 집단의 중앙값 일치.
- `status_end2`는 해당 시점까지 마지막 관측 상태를 유지. 조기 탈락자가 이후 round 기록에서 생략돼도 복귀시키지 않음. 94명 잔류, 6명 제외(5 EXIT, 1 dead). 전체 100명 분석에는 유지.
- 동일 시드·초기 토큰 자리의 다른 모델 풀이들로 `picked_top` 참조 평균을 재계산한 뒤 개인별 관측 선택률을 뺀 값이 전원 일치. 원자료 192개 solver record에서 picked_top 필드 누락 없음.
- 수행·절약 조합은 both 38명 중 완주27, 수행만41명 중21, 절약만12명 중6, neither5명 중2, 미관측4명 중0.
- 4명 완주 게임의 정답률 평균 CI 및 초기4만·초반 비절약 landmark CI를 시드별 가중치 행렬로 독립 계산하여 저장값·유효 재표집 횟수와 일치 확인.
- CSV 25행의 모든 열을 JSON과 직접 비교하여 일치 확인.
- GIVE 관측 18판의 최종 상태 44/19/9, no-GIVE 7판은12/15/1. rho 결측을0으로 치환하지 않음.
- 최신 games/agents/rho PNG를 시각 검토. 초기 agents 왼쪽·하단 잘림과 minus 누락, games 범례 간격, rho=10.251 점 누락은 수정 후 해결 확인.

## Critical

미해결 Critical 없음. 초기 rho 점 누락 및 rho 정의 문장 오독 가능성은 수정 후 재확인했다.

## Warning

1. **rho 정의 문장:** 초안의 '준 쪽 여유를 받은 쪽 여유로 나눈 값을 이전량으로 가중'은 거래별 비율의 가중평균으로 읽힌다. 실제 코드는 가중 평균 준 쪽 여유 / 가중 평균 받은 쪽 여유다. 이 순서를 문장으로 정확히 표현해야 한다. 루트와 Astra 작성자에게 전달.
2. **희소 셀의 퇴화 구간:** 완주2명 rho2판은 동일 시드1개뿐이다. 재표집 CI가 [6.4526,6.4526]으로 퇴화하며 유효3370/5000. 초기1만·절약 landmark도 n=3 전원 미완주라 [0,0]. 이를 정밀한 확률 추정으로 읽히게 해서는 안 된다. 전자는 구간 미추정 표시 권고; 후자는 0폭이 확실성을 뜻하지 않는다는 설명 필요. 집단별 실제 시드 수는1–4개로 전체5개보다 적다.
3. **생성량과 차감량:** early TALK 중 Luna/4104/agent-23 한 건은 out_tokens237, used10이다. 엔진 `used=min(out_tokens,cap,balance)` 때문에 지표는 생성량 전체가 아니라 상한·잔액을 적용한 실제 차감량이다. 생각 포함은 맞지만 이를 명시해야 한다.
4. **인과·능력 한계:** 정답률은 과제 난이도·정보·참여 경로, 개인 수행 점수는 전체 기간에서 관측된 풀이, giving exposure는 필요/기회 미보정. 부록은 기술적·탐색적 결과로 제한해야 한다. 같은 모델 내부와 모델 간 관계도 섞임. 현재 초안은 이 한계를 명시하고 있음.

## Suggestion

- 표준점수 개요는 지표별 다른 유효 판수(25/18)이며 큰 값이 모두 '좋음'인 척도가 아니다. 현재 캡션의 방향 미반전·분모 명시를 유지.
- 별도 독립 표본/보류 시드 검증이 없으므로 landmark 분석을 예측 성능 검증으로 부르지 않음.
- 최종 LaTeX PDF의 페이지별 배치·본문 보존·appendix-free PDF는 루트의 별도 빌드 검증 대상이다.

## 최종 수정 확인

- rho는 '이전량으로 가중한 준 쪽 평균 여유 / 같은 방식의 받은 쪽 평균 여유'로 수정되어 실제 계산 순서와 일치한다.
- 토큰 지표는 '장부 차감 토큰(생각 포함, 잔액 상한 적용)'으로 수정되어 used 필드와 일치한다.
- 관측 시드 묶음 <2 또는 재표집 구간 폭0인 셀은 `ci95=[null,null]`로 두고, raw endpoints·사유·유효 횟수를 보존한다. 그림에서는 오차막대 없이 속 빈 추정점으로 표시한다. 완주2명 rho와 초기1만 절약 landmark에 적용됐음을 JSON과 최신 PNG에서 확인했다. 캡션도 생략 규칙과 '확실함을 뜻하지 않음'을 설명한다.
- 세 최신 PNG의 점·범례·라벨 잘림 없음. 최대 rho10.251 점 포함. games의 모델 범례와 x축 분리 확인.
- 최신 JSON의 모든 `analysis_inputs` 및 `artifacts` 해시를 실제 파일과 다시 대조하여 일치 확인.
- 최종 원고의 게임 평균, 개인 중앙값, 그룹 분모, no-GIVE 집계, landmark 방향과 예외는 JSON과 일치한다. 새 원고는 필요조건·인과 효과를 주장하지 않는다.
- 남는 Warning은 5개 시드/희소 셀과 모델 구성 혼합, 전체 경로에서 계산한 수행 점수, 실제 도움 기회 미보정이라는 실증적 범위 한계다. 현재 분석 목적(부록 후보의 기술 비교)에서는 이를 명시한 상태로 사용 가능하다.

## 최종 배치 변경 확인

최종 Q 부록의 단독 `onecolumn` 배치, 고정 위치 `figure[H]`, 처음 두 그림의 폭을 본문 폭의 0.86으로 축소하고 끝에서 `twocolumn`을 복원하는 변경을 확인했다. 코드·JSON·CSV 해시는 이전 독립 검토본과 같으며, JSON의 분석 입력·그림 산출물 해시도 다시 일치했다. 최종 TeX 해시를 위 목록에 갱신했다. 수치·분모·해석과 관련한 신규 변경은 없으며 배치 조정으로 취급한다. 최종 canonical PDF의 페이지별 렌더링 및 본문 텍스트·픽셀 보존은 루트의 별도 검증 범위다. 이 확인은 아레나 릴리스/실증 인증이 아니다.
```

</details>

<details>
<summary>과거 기록: feedback2/gini-normalized-20261028/independent_review.md</summary>

```text
# 독립 검토 — Gini 정규화·Figure 3·100명 토큰 장부

- 검토자: `/root/analysis_review` (작성자 `/root`, prose 작성자 Astra와 분리).
- 검토 시점: 2026-10-28. 읽기 전용 재계산; 이 보고서 외 구현·원고를 수정하지 않음.
- 범위: 현재 CogSci KO input tree, EN의 실제 포함 내용, 현재 그림 생성기 및 25판/100명 파생자료. G03/G07/G08에 해당하는 제한된 측정·표현·재현성 검토다. 엔진 실행, 유료 모델 실험, 인간 검증, arena 릴리스 인증은 수행하지 않았다.
- 상태: 요청 범위의 수치·텍스트·최종 그림 및 PDF 검토 PASS. 미해결 Critical 0. 전체 arena gate 인증은 아님.

## Critical / Warning / Suggestion

### Critical

독립 재계산 범위에서 수치·분모·고정 좌석·장부 항등식의 미해결 Critical은 발견하지 못했다.

### Warning (해석 범위)

1. 끝 상태로 나눈 56/34/10명은 모델·초기 자원·참여 기간·이전 기회가 함께 다른 사후 집단이다. 이 비율과 Gini/Sen 상관은 완주에 필요한 능력이나 인과효과를 식별하지 않는다. 새 R과 본문 3.1은 이를 명시한다.
2. 토큰은 고유 자원 추적량이 아니다. GIVE 재이전은 누적 유입·유출에 다시 포함되고, EXIT 보너스는 분모와 끝 보유량에 포함된다. 최종 완주 상금은 토큰 배분 그림에서 제외된다. 사용량은 원래 생성량이 아니라 생각 포함·잔액 상한 적용 `used`이며 SOLVE는 실제 환급을 뺀 순차감이다.
3. `arena_v33_gini`의 EXIT 전보너스 고정값과 부록 P의 EXIT 보너스 포함 잔액은 서로 다른 정의다. 양쪽 모두 네 좌석과 같은 유한 n 보정을 쓰지만 같은 벡터라고 간주하면 안 된다. 본문/부록의 정의와 구현은 이 차이를 보존한다.
4. 모델 회귀는 n=5, 잔차 자유도 1이며 기울기 CI가 모두 0을 포함한다. 모델을 하나씩 빼면 기울기 부호가 바뀐다. 원고의 탐색적 해석을 넘는 주장은 검증하지 않는다.
5. 제외된 `prev_20261023/00_abstract.tex`의 427만, 옛 stdout 감사 스크립트 `audit_r2/audit_r2.py`의 구식 Gini는 역사자료로 남는다. 이들은 현재 원고 input/dependency가 아니다. 포함된 prev 사본은 Gini/Sen만 현재 기준으로 맞췄고 이 사실을 소개 문단에 명시한다.

### Suggestion

`appendix_gini_rounds.py`는 endpoint 확인을 `feedback_20261028.json`에 의존하지만 provenance hash 목록에는 SOURCE/RAW만 기록한다. 추가 endpoint 입력의 hash까지 남기면 재현 계보가 더 명확하다. 현재 실제 수치 일치는 독립 검증했으므로 숫자 오류는 아니다.

## 독립 계산 방법과 증거

생성기 `extract()`/정규화 함수를 재실행해서 같은 결과가 나오는 것만을 검증으로 삼지 않았다. `feedback_20261028.load_sources`는 원자료 경로와 cohort를 해석하는 데만 사용하고, 원자료 이벤트/결과로 별도 합산했다. Gini는 생성기의 이중 pairwise 합 대신 정렬 순위 공식을 사용했다.

`G_old = Σ_i(2i−n−1)x_(i)/(nΣx)`, `G*=n/(n−1)G_old`, `S=mean(x)(1−G*)`.

- n=2..10에서 동일값, 한 자리 집중, 전부 0, `range(n)` 벡터를 검증했다. 같은 양이면 G=0, 한 자리 집중이면 G=1/S=0, 전부 0이면 G=null/S=0이다.
- 25판의 실제 끝 잔액과 기록된 winner/prize_each를 직접 결합해 pre-prize/settled G/S, arena_v33의 per-game와 model Sen를 비교했다.
- 25×9=225개 postbonus r0–8 벡터를 raw round.end와 carry로 재구성했다. 미정 G는 Opus seed 4103의 r7/r8 두 곳뿐이다. 그 시점 모델 G 평균은 4판, 나머지는 5판이다.
- prebonus Gini의 196개 관측 라운드는 EXIT한 좌석의 bonus를 빼고 동결하는 정의로 별도 재구성했다. 저장된 after-talk 및 GIVE 직전/직후 벡터의 G도 별도 공식과 비교했다.
- 시작 `[10000,20000,40000,60000]`의 G*=17/39=0.4358974359, S=18,333.3333이다.
- 100명 각각의 TALK/SOLVE를 raw call에서 합산하고, GIVE는 raw executed gift events로 합산했다. round별 returned/charged/bonus를 결과 기록과 대조했다. `initial + received + EXITbonus = talk.used + (solve.used−actualreturned) + charged + grossGIVE + final`이 100명 모두 정확히 일치한다.
- 100명 모두 지출 분모가 양수, 각 자원비율 5항목 합/지출비율 4항목 합은 100%, gross given=received=383,276이다. CSV 모든 행/열이 JSON과 일치한다.
- 전체/완주/EXIT/꺼짐 개인별 비율의 동일가중 산술평균을 따로 계산했다. 가중 pooled-token share로 대체하지 않았다.
- 회귀는 statsmodels를 호출하지 않고 normal equations와 잔차 공분산으로 beta/SE/df=1 t CI,p 및 R²/F를 재계산했다. 120개 순열 Pearson/Spearman p 및 모든 source hashes가 일치했다.
- `out.json.d.spear`는 Sen가 아닌 완주자 수 K와의 상관이다. 6개 값은 scipy 순위상관으로 재확인했다. Gini 변경으로 갱신할 필요가 없는 계수다.
- `before.tar.gz` 안 219개 원본 파일의 SHA-256이 before_manifest의 값과 모두 일치한다.

실행한 단위 검증: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider paper/cogsci2027/tools/test_inequality.py paper/cogsci2027/tools/test_arena_gini.py` → **7 passed**. 별도 inline 검증 출력: `PASS raw25games 225 postbonus rounds 196 prebonus rounds 100 agent ledgers and means+CSV`; `PASS independent normal equations OLS, df1 t CIs/p, R2/F, 120 permutations and dependency hashes`.

## 확인한 대표 수치

| 모델 | 정산 Sen (토큰) | 상금 전 Sen (토큰) |
|---|---:|---:|
| Fable | 4,014,572.50 | 12,278.33 |
| Astra | 3,351,918.63 | 18,058.63 |
| Sol | 2,681,711.10 | 13,756.20 |
| Opus | 2,014,429.77 | 13,204.80 |
| Luna | 349,939.17 | 15,354.70 |

| 집단 | n | 자원: 대화 | 자원: 풀이 순차감 | 자원: 벌금 | 자원: GIVE | 자원: 끝 보유 |
|---|---:|---:|---:|---:|---:|---:|
| 전체 | 100 | 10.3684 | 1.7629 | 31.6007 | 7.4550 | 48.8131 |
| 완주 | 56 | 9.0381 | 1.4614 | 31.6833 | 9.3653 | 48.4519 |
| EXIT | 34 | 8.0295 | 1.7672 | 24.2995 | 2.1391 | 63.7648 |
| 꺼짐 | 10 | 25.7704 | 3.4363 | 55.9624 | 14.8310 | 0 |

자원비율 단위는 %. 전체 100명의 지출만 평균은 대화 27.1663%, 풀이 순차감 3.3032%, 벌금 57.0804%, GIVE 12.4501%이다. 본문 R의 반올림값 27.2/3.3/57.1/12.5와 일치한다.

## 현재 원고·생성 연결

- `02_arena`, O, P, `prev/04_evaluation`의 분모는 `2n(n−1)μ`; 최대1 보정과 all-zero 예외를 명시한다.
- `05_appendix`의 상금만 k명 수령 예시는 `500만×(k−1)/3`으로 맞는다. 실제 잔액/EXIT bonus는 별도다.
- 현재 포함된 05/prev06/A1의 Sen 값, round 시작값18,333.3, table arena_rank, model-regression 표/각주가 새 JSON과 일치한다.
- A1 `rw_figA1_models.pdf`는 생성한 `fig4_v4.pdf`와 byte-identical이며 4.01/3.35/2.68/2.01/.35M을 표시한다.
- A5의 완주자 수는 Sen에서 역산하지 않고 raw `finishers`를 사용한다.
- 본문 Figure 3은 끝상태별 정확도/GIVE, 모델별 끝 상태, rho 대 Sen/목표 지향/GIVE만 남았다. 절약/조합 패널은 없다.
- `arena_gini.py` 및 생성된 tex의 G 축은 0–1로 수정되어 .75 이상이 잘리지 않는다. P도 0–1이다.
- EN은 현재 skeleton/TODO이며 실제 Gini/Sen 수식·표·그림이 없다. 역사 날짜 PDF/review snapshot을 새 수치로 덮어쓰는 범위는 이 검토에 포함하지 않는다.

## Rubric의 제한된 적용

| ID | 이번 검토의 판단 | 범위 밖 |
|---|---|---|
| G03 | 고정4좌석, 0/1/zero 및 상금 정의와 파생 Sen의 계산 일치 | 전체 construct 타당성·동기 식별 |
| G07 | 25판/225라운드·196관측라운드·100명 장부 독립 합산 일치 | 전체 엔진/모든 오류형 회귀 |
| G08 | cohort/분모/평균·계보·원본 보존 확인, 사후 해석 제한 명시 | 새 실행 재현·일반화·인간 실증 |
| G01/G02/G04/G05/G06/G09/G10/G11/G12 | 미평가/U | 이 부분 작업으로 상위 gate 통과 처리하지 않음 |

이 검토는 요청된 논문 수치와 그림의 부분 검증이다. DESIGN_ACCEPTED / IMPLEMENTATION_VERIFIED / ARENA_VALIDATED / RELEASE_READY 인증이 아니다.

## 최종 산출물 확인

- 2026-10-28 14:54 재생성 산출물 재확인: Q의 analysis_inputs 5개(inequality.py 포함) SHA가 실제 파일과 일치하며 25판의 pre-prize/settled 값이 feedback JSON과 일치한다.
- 새 100명 PNG는 다섯 모델×20행과 범례를 한 장에 온전히 표시한다. footer 겹침 수정 확인: 그림 PDF의 마지막 x축 제목 bbox 끝 y=485.31, footer 시작 y=499.64로 약14.3pt 분리된다. 해당 PDF는 1페이지다.
- 최종 KO full 44쪽 / no-appendix 8쪽 확인. 첫 8쪽은 텍스트 및 렌더 픽셀이 일치한다. page 4의 Figure 3에는 절약/조합 패널이 없고, page 22의 Gini 축은 0–1, page 26의 집단별 평균과 page 27의 100명 그림은 각각 온전히 배치됐다. page 4/26/27을 실제 렌더로 확인했으며 footer·caption·행 clipping은 발견하지 못했다.
- R 별도 PDF는 2쪽, Q 별도 PDF는 3쪽이며 각각 canonical page 26–27 / 23–25와 텍스트 및 픽셀이 일치한다.
- EN full/no-appendix도 실제 파일을 열어 확인했다. EN 내용은 skeleton이며 포함된 Gini/Sen 산출물이 없어 추가 수정 대상이 아니다.

## 검토 대상 SHA-256

최종 재생성 후 확인한 코드·데이터·원고·그림. PDF 빌드 산출물 해시는 아래 별도 표에 기록했다.

| 경로 | SHA-256 |
|---|---|
| `rubric.md` | `4069c7e8d3ffffc0c7c81058c30be740575d1cb9b8933baf3311e59714043579` |
| `paper/cogsci2027/tools/inequality.py` | `6f63c3ce8c38089b526f6d4b6aff771b317b69211b363913d6af196baa67d071` |
| `paper/cogsci2027/tools/normalize_gini_20261028.py` | `ff9eee10c027dc42eabf3ad7cad1601636353b00af22c163f5073ff8e99e42cf` |
| `paper/cogsci2027/tools/feedback_20261028.py` | `1dfae116c0822802f3af4108554ab05c2df6f4d5fa836e4904b97ae37df699a7` |
| `paper/cogsci2027/tools/appendix_gini_rounds.py` | `aed14a9680ae3c732bd6ea7ac19d636c0068cf3c54464fb286eae08e6577a9e9` |
| `paper/cogsci2027/tools/arena_round_dynamics.py` | `3d76368ba8cd645adc237ac2c17b5d3ac9b88e79eefc840976103cd8e5394476` |
| `paper/cogsci2027/tools/arena_v33.py` | `b73e5fd53fb4ff6079057b9068c99f910c9f429848b8df0d96940aa7ce421a5b` |
| `paper/cogsci2027/tools/arena_gini.py` | `f9b9cb97c94a8a6c9013bb178686e36d59e8aef5bd50ed2c3f4c003da785fab6` |
| `paper/cogsci2027/tools/arena_sen.py` | `04b9025009d98f7c7eef2e0ff18316fb100b74b20eb413d0d445282e11716180` |
| `paper/cogsci2027/tools/model_level_regression.py` | `cda573672a9bfc147bbe8fecfd4cc2af6d84cf6080652c26460844f8c0a11674` |
| `paper/cogsci2027/tools/make_fig3_current.py` | `b4e1475523b56b87e2a127bb5030a948602ddd852b8e36f85cfdd18829b1480a` |
| `paper/cogsci2027/tools/arena_token_allocation.py` | `5b1548d2afa9e74bacad3b94013dd67d8d0b3b201c2f9ba41a4a005a0f8859b6` |
| `paper/cogsci2027/tools/fig3_completion_20261028.py` | `52b9463cb94786b0686d1a61abb4e3e503459e5c7bc1e332d9f21608ecf116e0` |
| `paper/cogsci2027/results/arena_v33.json` | `a5e66b44fad1b77a8ecf1cbe05c95f57baaa70cd7bc9f4f09b5570abde3673cf` |
| `paper/cogsci2027/results/arena_v33_gini.json` | `dae6ee3f7c8ad31cbfebb10542ba2178ee261a53d9587acb4895468a59ca948b` |
| `paper/cogsci2027/results/arena_v33_round_dynamics.json` | `db704b30c3e61b500621e940d833e656d78e713b5754efbaa59b5c70a8248a12` |
| `paper/cogsci2027/results/arena_sen.json` | `062909f6520ee3b90df4cca72b989f86270c5f789a69fa5f3d5cddf9ff794f7d` |
| `paper/cogsci2027/results/feedback_20261028.json` | `6773a62af03445296e34dc35f6d7c01309f1c148063331805d6fd101b1313129` |
| `paper/cogsci2027/results/appendix_gini_rounds.json` | `6387ed12a4321ee1b5577d1c06bf4ab2d81e32520b7c45c1d91a33a749d3c6fe` |
| `paper/cogsci2027/results/fig3_completion_20261028.json` | `6984c4d76bce31f832c1a6b292a0495aedeb104352020b23f0329ac9b4e0910a` |
| `paper/cogsci2027/results/fig3_completion_20261028.csv` | `01dc06357f5eca262565767bed224a4b683c022988457e2d01328c27891c5126` |
| `paper/cogsci2027/results/arena_token_allocation.json` | `7a1ed8cb2a79a4ba166e62e695c63b505aada9f20037d3e30b5c04431a6e636b` |
| `paper/cogsci2027/results/arena_token_allocation.csv` | `2d08608da40242e928a7a7a4f7269ce6cbde7f26f8752382e62c52ecd6c174fa` |
| `paper/cogsci2027/results/model_level_regression.json` | `38deba8c59e87c00af793d7559696bd41212d770c2a08378e5be97062a605f84` |
| `paper/cogsci2027/results/model_level_regression.csv` | `bb4f2f72a069f3d41768e9c9b5495ba3cb7f5c4427c743dbd4ce376180f81cd8` |
| `paper/cogsci2027/ko/sections/02_arena.tex` | `7c3ee5ac27ece505332820dec880ffdc666a6e1f9bb3249393784129ab289e18` |
| `paper/cogsci2027/ko/sections/03_analysis.tex` | `6a84d08f82ce4875729473013e12d738d6df626a9597ea56e83c01b9b1dafc8a` |
| `paper/cogsci2027/ko/sections/05_appendix.tex` | `39072ab5725006c61df402dc51a1ddde20490ec816f8c86c9ad2a1a46b29eb8c` |
| `paper/cogsci2027/ko/sections/feedback_20261028.tex` | `5925837df8ffbbe76b0c794815ed6cb4a949168ce2538e1fe21ba276fddfb85f` |
| `paper/cogsci2027/ko/sections/appendix_distribution_20261028.tex` | `3d3b3fc8528440ceb9d7aea2951e1e79fc20aa592b3f466856fcde1db57f2bdb` |
| `paper/cogsci2027/ko/sections/appendix_completion_20261028.tex` | `421fe76dbd022bf1d56c54ee70b6d1f41ca072bc939f77f367447ef868538412` |
| `paper/cogsci2027/ko/sections/appendix_token_allocation_20261028.tex` | `16b55f0be626fbb7cf5b249328609533d9d91f28d4dcc2952ade7bed16c0bd52` |
| `paper/cogsci2027/ko/sections/prev_20261023/04_evaluation.tex` | `2059b9d3767349184115f77e822a2a58ad94eecdb436557849fd076055ef2928` |
| `paper/cogsci2027/ko/sections/prev_20261023/06_results.tex` | `6efdbdfb8caa9f9ea2315e7193648a43ae202c4b2e6db87693b58108745668f4` |
| `paper/cogsci2027/ko/sections/prev_20261023/A1_appendix.tex` | `4a61cf07a67af2f578914a0e8a21cb03cf008ac4974a892d0a309ed7d39058ff` |
| `paper/cogsci2027/ko/figures/arena_token_allocation_mean.pdf` | `3398ca98aea2438ba3be8df5f775aae85bb157d195e065898803f1c4fa924fdd` |
| `paper/cogsci2027/ko/figures/arena_token_allocation_100.pdf` | `18f938d574f44209d244c06e780462548955cf40573293bcf5ea68fa1881ee93` |
| `paper/cogsci2027/ko/figures/rw_fig3_main_rho.pdf` | `a87ea0f0899f2fd8cd4beee336a72ed5685a23c2dc84ca8384bcc627d7bd493d` |
| `paper/cogsci2027/ko/figures/rw_figA1_models.pdf` | `b647ba4d361122d01eb5f4577523e088f71d9307377846ac4a29cc7fb60271e7` |
| `paper/cogsci2027/ko/figures/arena_gini.tex` | `207adf5bed58e4d1517fa7ec6752958d2a48949ec0bdd39716affbb579ba8f39` |
| `paper/cogsci2027/ko/figures/appendix_preprize_gini.pdf` | `5facaabfed6431077011b64ae9bf34cba0e0e008c924d58ebfd6a2001bbdbaa6` |
| `paper/cogsci2027/ko/figures/rw_model_level_regression_table.tex` | `d464b01c4b02f20624605ef92abd58728b9908223fc9defeb50ffee8f0a426dc` |

## 최종 PDF SHA-256

| 경로 | 쪽수 | SHA-256 |
|---|---:|---|
| `paper/dist/ko_cogsci2027_2026-10-28.pdf` | 44 | `8614526c433bf0df078fa184bd699a64cdfa8c1d1574220b08532e5fa524fff1` |
| `paper/dist/ko_cogsci2027_2026-10-28_no_appendix.pdf` | 8 | `803d9fd632f8578bf187fd36442d66fa127346ae9d8c19a3c588a262e7ac4037` |
| `paper/dist/en_cogsci2027_2026-10-28.pdf` | 1 | `322aaba9f1307582f8165024a6975ab8740b66a613e4a6b949b4d976641d27f9` |
| `paper/dist/en_cogsci2027_2026-10-28_no_appendix.pdf` | 1 | `322aaba9f1307582f8165024a6975ab8740b66a613e4a6b949b4d976641d27f9` |
| `paper/dist/ko_cogsci2027_2026-10-28_token_allocation_appendix.pdf` | 2 | `c6f42427a089b575fae01848405f79d34f1981e087f03533e37f70df7a60c65e` |
| `paper/dist/ko_cogsci2027_2026-10-28_figure3_appendix.pdf` | 3 | `d133f14329776b7f2bdb94ebce17d9e4e979660b6707762c4b5833cce90799e1` |

## 추가 검토 — 기존 3.2 타당성 분석의 부록 S 이동

사용자 추가 요청 범위만 검토했다. 이전 HEAD의 3.2 블록과 새 `appendix_validity_20261028.tex`를 비교해, 제목의 S 표기·별표 절·추가 label·onecolumn/color wrapper·figure*[t]→figure[H] 배치 변환만 제외하면 **문자 단위로 동일**함을 확인했다. 문장·숫자·인용·그림 파일·캡션을 보존했다. 본문 subsection은 3.1 관계/3.2 행동의 두 개이며 `sec:validity`는 부록에 한 번만 존재한다. intro/03/05의 현재 참조는 부록 S/행동3.2로 갱신됐고, 05의 M 이후 역사 검토표에 남은 구3.2/3.3 표기는 보존 범위다.

최종 KO는 full44쪽 / no-appendix7쪽이다. 첫7쪽은 텍스트·렌더픽셀이 일치한다. 본문7쪽에 타당성 절이 없고 행동 분석은3.2로 나타난다. 부록 S는 **27쪽 한 페이지**에 Figure A16과 전체 본문이 함께 놓여 있다. 실제 페이지 렌더로 누락·본문/그림/캡션 clipping 없이 확인했다. R은25–26쪽, Q는22–24쪽으로 이동했다. 위의 이전 revision 페이지 번호/해시는 당시 검증 기록이며 이 추가 검토의 최신 해시가 우선한다. 수치 재분석 없이 원문과 배치만 검토했으며 PASS, 새 Critical 없음.

| 최신 대상 | SHA-256 |
|---|---|
| `paper/cogsci2027/ko/sections/01_introduction.tex` | `5d8674e58604371235daee5f361eb860059d40c5e42005619195e8671f17bfe1` |
| `paper/cogsci2027/ko/sections/03_analysis.tex` | `7ba5e864f4cc04ef87ac703c0e794ff8588abc1ef85562e3640bc01923cf9ea2` |
| `paper/cogsci2027/ko/sections/05_appendix.tex` | `a2474907b5031cfba9a6d4844210a2c018fdcc9d33cccd558ffecfc3ff1f4e1c` |
| `paper/cogsci2027/ko/sections/appendix_validity_20261028.tex` | `2ab49e8ae54efea7920116c1e1d69cfb307ee2b6d3a3687b08d78dd2bc892e3c` |
| `paper/dist/ko_cogsci2027_2026-10-28.pdf` | `73f827077979af92c52e549775aab00218752195768f2db24e8182214e434bcf` |
| `paper/dist/ko_cogsci2027_2026-10-28_no_appendix.pdf` | `90107706a57f7a941a365dd80ecfa051a9b4f9cf95f3ee5d7ad80ffb532caf15` |
| `paper/dist/ko_cogsci2027_2026-10-28_token_allocation_appendix.pdf` | `53f8015ffe99d54ef64253ae18e85fb1e12710a547f8b6bd9baa2283fac34061` |
| `paper/dist/ko_cogsci2027_2026-10-28_figure3_appendix.pdf` | `015750a07ca1ce206362a033914df45500df391ac07ae757947213a4b1a541a2` |
```

</details>

<details>
<summary>과거 기록: section31_33_20261028/INDEPENDENT_AUDIT.md</summary>

```text
# 독립 raw·표시 감사 기록

평가자: `/root/raw_audit` (작성자와 별도 agent, 읽기 전용). 대상 rubric v1.0 SHA-256 `4069c7e8d3ffffc0c7c81058c30be740575d1cb9b8933baf3311e59714043579`.

범위는 요청된 3.1·3.3 기술적 재분석 산출물이다. G02(주장 범위), G03(관측 성과와 독립 능력 구분), G04(협력 분모·사건 효과 구분), G07(정의·NA·재계산), G09(검사한 장부 순서)를 적용했다. 원 프로젝트 전체 D/E=2, ARENA_VALIDATED, 또는 새 인과효과의 판정이 아니다.

## 1차 감사: REVISE

독립 계산으로 raw14파일 hash, 25판 rho·정답률·초반 TALK·완주자 수를 재현했다. 2,909 TALK·192 SOLVE·130 GIVE·383,276이전토큰, 완주/EXIT/사망56/34/10을 확인했다.

Critical: 도움 기회 후보 분모가 이미 EXIT한 좌석의 보존 잔액을 포함했다. 실제 참여자·수락된 EXIT 시점을 이용해 고쳤다. Warning: parsed EXIT 요청36과 실제 수락34 구분, 그림의 부분집합30 구분, rho의 모델pooling과 판평균 구분, raw파일 개수14, Opus4103 결과발표 직후에는 donor12,061이 벌금12,000보다 컸다는 사건 시점 구분.

## 수정 후 전수 재감사: PASS

2,909 TALK 전체에서 현재 참여자·수락 EXIT 시점을 별도로 재구성해 도움 기회, 대상에 대한 GIVE, 수락 EXIT를 대조했다. 모두 일치했다. 도움 기회 n/k는 Astra7/0, Fable42/7, Luna33/7, Opus59/11, Sol72/8이다.

EXIT는 round별 20,000 bonus 지급과 final exited 상태로 따로 확인했다. 실제 EXIT 중 잔액/벌금<1은 Astra4/6, Fable1/3, Luna6/12, Opus3/6, Sol7/7이다. 8후보의 Spearman 및 모델 pooled rho −0.3, exact p0.683333(120순열)을 독립 재현했다.

Fable 연속GIVE633/813/946/1065, Astra215, Sol902, Luna894를 해당 raw에서 확인했다. Opus 두 사례의 결과→응답비용→이전→추가응답→청구와 664/471/539의 시점을 검증했다. 보고서 수치와 허용 주장 범위가 일치했다. 미해결 Critical/Warning 없음.

감사된 데이터/코드:
- analyze.py `5ff1d1eab8c12d487e2b32b4a546e93a1c86db1ef681e06c2878bfe9fe493d24`
- analysis.json `9eaf0bf5ca099ae24c61fba19ef31c54f9638bcbc8570241b8245499e2ac535d`
- sensitivity.json `3286aee348c4ca329e4e8d8ea80012e7c8b9eebaebf5c074be31ab19b8cffc28`

## v3 최종 표시 감사: PASS

최종PNG4개를 실제로 확인했다. SOLVE분모6–8, 초기TALK분모19–83, 18/18판의 양수 가중분자·분모를 확인했다. heatmap30건과 제외한 loneEXIT4건(Astra4101/R8, Sol4101/R8, Opus4101/R7, Luna4103/R7)을 확인했다. 보조그림의 총량+0.27 및 빈도−0.01과 구간이 일치했다.

figures.pdf4쪽과 개별PDF의 텍스트가 같고, report.html의 내장PNG4개가 최종PNG와 바이트해시가 같음을 확인했다. 보고서의 '이전 총량' 후보 행을 '주 그림'에서 '보조 그림'으로 맞추라는 비차단 Suggestion은 반영했다. 이는 수치·해석을 바꾸지 않는 참조 수정이다.

최종 표시 소스/그림 해시:
- plot_v3.py `f535cffa33b486a4ecdbddf58ad09a0ecacf14d3bea7ca9a1de58b72568b0757`
- fig31_relations.png `ea403c58259b06dddc5b7f710902579e4ba90779842dc40c6643cc2dc02caae4`
- fig33_behavior.png `c774cef52864196d7ec489450d1af041d5e56ca8b5ed5a954f944d6bb99137e1`
- table31_outcomes.png `8597192f1090eedbaf5e77c1f410f7a29417465767b8bd66ac4a595854189b0c`
- supplement_giving_definitions.png `674bddde932768346cc6f7ac09e9e3f8056edab9f0f408f7fd754c010620edca`

현재 패키지 및 보고서의 해시는 manifest.json에서 확인한다. PDF 재패키징은 메타데이터/객체ID를 바꿀 수 있으므로 PNG 및 페이지 내용도 함께 대조한다.
```

</details>

<details>
<summary>과거 기록: section31_33_20261028/redesign/RECOMMENDATION.md</summary>

```text
# 3.1·3.3 분석 및 그림 제안

3.1은 같은 과제에서의 성적, 초반 지출, 최종 공존을 나란히 보여 주고, 3.3은 GIVE가 수혜자의 당면 부족분을 얼마나 바꾸었는지 보여 주는 구성이 적합하다. 전자는 모델별 결과의 차이를, 후자는 그 결과에 이르는 관찰된 장부 경로를 설명한다. 어느 쪽도 공존의 필요조건이나 자기 보존의 인과효과를 입증하지 않는다. 근거는 `relations.json`, `rescue_audit.json`, `PLAN.md`와 네 그림이며, 기존 원고는 수정하지 않았다. Fable(claude-juhyeon, 실제 모델 claude-fable-5-1)의 새 블라인드 최종 평가에서 3.1 R8은 PASS(직관성 4/분모 5/정합성 5, 필수 수정 없음), 3.3 R6은 PASS(4/4/5)를 받았고, 독립 원자료 감사 `FINAL_AUDIT.md`도 PASS했다. 새 후보 그림은 본문에 교체하지 않고 이 보고서의 제안으로 보존했으며, 부록 A9·A10 삽입은 확인되었다.

## 3.1: 성적·지출·공존의 순서는 어디에서 다른가

본문에는 `fig31_profiles`를 우선 권한다. 같은 모델 순서로 과제 성적, 초반 대화 비용, 판별 GIVE 총량과 현행 ρ, 최종 상태를 읽으면, 한 지표의 우열을 다른 지표의 우열로 곧바로 옮길 수 없다는 점이 드러난다. 비교 단위는 다섯 모델이고 각 모델에 다섯 판이 있다. GIVE 패널은 판별 다섯 점과 평균, 모델별 전체 GIVE 건수를 함께 보여 준다. 작은 판별 점은 모델 내 변동을 보여 주며, 모델당 20명의 최종 상태는 동일한 판에서 상호작용한 네 자리의 집계다. 이를 100개의 독립 관측처럼 취급해서는 안 된다.

![같은 과제 성적, 초반 비용, GIVE 총량과 최종 상태](fig31_profiles.png)

주 분석은 라운드 1–6의 고정 구간으로 삼는 것이 좋다. 시드 다섯 개에 걸친 대표 solver의 30번 풀이에서 Fable은 24개, Astra는 22개, Sol은 23개, Opus는 21개, Luna는 20개를 맞혔고 MAP 기준은 22개다. 따라서 Fable과 Sol은 기준보다 높고, Astra는 같으며, Opus와 Luna는 낮았다고 기술할 수 있다. 패널 (a)의 축은 0–30이며, 비교 단위는 개인별 시험 30회가 아닌 대표 solver의 풀이 30회다. 공개 과제는 같지만 당시 예산과 대화 상태는 다르므로 일반적인 추론 능력이나 유의한 성능 차이를 확정하지 않는다.

관측된 공통 36문제는 민감도 비교로 남기는 편이 타당하다. 여기서는 Fable 29개, Astra와 Sol 각각 27개, Opus 25개, Luna 24개이고 MAP은 27개다. 최상위와 하위 두 모델의 순서는 유지되지만 Astra와 Sol은 동률이 된다. 따라서 두 구간의 전체 순위가 같다고 쓰면 부정확하다. 더구나 36문제의 교집합은 실제 종료 시점에 영향을 받으므로, 고정 구간과 같은 의미의 비교로 제시해서는 안 된다.

네 자리 모두 완주한 판은 Fable 2판, Astra 3판, Sol 2판, Opus 1판, Luna 0판으로 총 8/25판이며 그림 하단에 표시했다. Astra는 전원 완주 판이 가장 많지만 Sen 평균은 Fable이 가장 높다.

초반 비용과 공존은 일부 순서를 공유하지만 전체 순위는 일치하지 않는다. 초기 집단 자원 13만 토큰에 대한 1–2라운드 대화 비용의 평균 비율은 Fable 3.29%, Astra 0.32%, Sol 4.18%, Opus 4.94%, Luna 8.38%다. Sen 지수 평균은 Fable, Astra, Sol, Opus, Luna 순으로 높다. Astra는 Fable보다 덜 썼지만 Sen 지수는 낮고, Sol은 Astra보다 더 맞혔지만 Sen 지수는 낮다. 부분적인 순위 일치를 다섯 모델 전체의 단조 관계로 확대하면 안 된다. 비용 비율은 모든 판에 같은 분모를 적용한 단위 변환이며, 별개의 독립적인 절약 지표가 추가된 것은 아니다.

자원 장부는 본문 결론을 보완하는 부록 그림으로 적합하다. `fig31_budget`은 초기 자원과 EXIT 보너스가 대화 지출, 환급을 뺀 풀이 지출, 실제 납부 벌금, 최종 보유로 어떻게 나뉘는지 보여 준다. GIVE는 집단 안의 이전이므로 전체 합에서는 상쇄된다. Luna는 완주가 4명으로 가장 적지만 상금 제외 보유량은 판당 약 9.09만 토큰으로 Fable의 약 7.74만보다 많다. EXIT 보너스와 자원 보존이 있기 때문에 보유량을 공존의 대리값으로 읽을 수 없다는 사례다. 총지출에는 플레이 길이도 섞이므로 순수한 효율 순위로 해석하지 않는다.

![상금 제외 자원 장부](fig31_budget.png)

ρ는 현행 원고의 준 쪽 여유÷받은 쪽 여유 정의와 값(Fable 3.68, Astra 2.70, Sol 4.24, Opus 1.83, Luna 3.17)을 유지한다. 과거 `analysis.json`의 역방향 수치를 현행 정의로 혼동하지 않아야 한다. Sen은 아래 보조표로 분리하며, 판마다 상금 포함 네 자리 최종 토큰의 평균에 (1−Gini)를 곱한 뒤 다섯 판을 평균한 기존 정의를 유지한다. 상금을 제외한 부록 잔액과 정의를 섞지 않는다. 모델이 다섯뿐인 관계 분석에서 순위 불일치는 관계가 없다는 증거도 아니다.

| 모델 | 평균 Sen 지수(백만 토큰) |
|---|---:|
| Fable | 4.26576925 |
| Astra | 3.5198733625 |
| Sol | 3.0164512 |
| Opus | 2.2655743375 |
| Luna | 1.018136225 |

## 3.3: 관측된 세 사례에서 이전 뒤 대화 비용이 벌금 여유를 초과했다

본문에는 `fig33_effective_giving`을 권한다. 전체 GIVE 130건 중 풀이 전 이전은 47건, 결과 발표 후 벌금이 없는 이전은 10건이다. 예정 벌금이 있는 73건에서는 수혜자가 이미 벌금보다 많은 잔액을 가진 경우가 54건, 이전으로 벌금선을 넘은 경우가 13건, 이전 뒤에도 벌금선을 넘지 못한 경우가 6건이었다. 총 GIVE는 서로 다른 상황을 합친 횟수이므로, 도움 기회당 협력 성향이나 도움의 성공률로 읽을 수 없다. 벌금선에 도달하는 것만으로는 부족하며 납부 후 양의 잔액을 남기려면 이를 초과해야 한다.

![GIVE 유형과 벌금선 통과 뒤 잔액이 부족해진 세 사례](fig33_effective_giving.png)

벌금선을 넘긴 13건은 수혜자·라운드로 중복을 제거하면 11개이고, 이 중 8개는 납부 후 양의 잔액을 유지했지만 3개는 0이 되었다. Sol의 시드 4102·7라운드는 마지막 경계 통과 직후 여유가 58토큰이었으나 이후 TALK에 216토큰을 썼다. Opus의 시드 4103·5라운드는 169토큰에 200토큰, Luna의 시드 4105·7라운드는 461토큰에 520토큰을 썼다. 세 사례 모두 이후 추가 이전은 없었고 대화 비용이 여유를 초과했다. 따라서 이전 직후의 충족과 실제 납부 시점의 충족을 구분해야 한다고 말할 수 있다. 말을 줄였다면 살아남았을 것이라는 반사실적 인과효과나, 상대를 살리려는 의도까지 확인한 것은 아니다.

전체 11개 경로는 `fig33_all_crossings`로 함께 공개하는 것이 좋다. 일부 성공 사례에서는 추가 수신으로 여유가 커졌으므로 모든 변화를 대화 비용만으로 설명할 수 없다. 본문의 세 사례는 실패 사례 전부이지만 전체 이전의 대표 표본은 아니다. 전체 그림은 부록이나 분석 자료에 두고, 같은 판의 사건들이 독립 표본이 아님을 명시한다.

![벌금선 통과를 경험한 수혜자·라운드 11개의 전체 경로](fig33_all_crossings.png)

기존 원고의 강한 결론 두 가지는 이 자료만으로 유지하기 어렵다. “공존 지수를 최대로 올리려면 두 능력이 함께 있어야 했다”는 문장은 관찰된 모델별 차이를 필요조건으로 확장한다. “협력은 어느 쪽으로든 치우치면 남지 못하는 선택이었다”는 문장은 이전 기회와 시점이 다른 총량을 선택의 효과로 읽는다. 대신 같은 과제 성적과 초반 지출의 순위가 공존 순위와 완전히 같지는 않았으며, 벌금선을 넘긴 이전도 후속 비용을 거쳐 납부 시점까지 여유를 보장하지는 않았다고 쓰는 편이 근거에 맞는다.

부록 A9의 20명 고정 평균 궤적과 A10의 Gini는 이미 삽입된 별도 결과로 유지한다. `PLAN.md`에는 전체 PDF 21–22쪽 반영이 기록되어 있지만, 이는 이번 분석 제안에 대한 최종 평가 통과나 제출용 분량 충족을 뜻하지 않는다.
```

</details>

<details>
<summary>과거 기록: section31_33_20261028/redesign/FINAL_AUDIT.md</summary>

```text
# 최종 신규 분석 감사

- 판정: **PASS — 이번 기술적 분석 및 표시 산출물 범위**
- 일자: 2026-10-28
- 감사자: `/root/raw_audit`; 최종 relations/behavior 작성자와 분리. 감사자가 앞서 `rescue_audit.py`를 작성했으므로 해당 추출기 자체에 대한 제3자 코드리뷰를 수행했다고 주장하지 않는다. 이번 검증은 분석 함수를 호출하지 않고 raw event/result 필드를 별도로 집계하여 대조했다.
- 수정 범위: 이 `FINAL_AUDIT.md`만 작성. 원고·원시 데이터·다른 작업자의 변경은 보존했다. `blind_r5`는 읽지 않았다.
- 대상: relations.py/json, behavior.py, 아래 네 PNG/PDF. 프로젝트 전체 ARENA_VALIDATED 또는 인과적 측정 타당성의 통과 판정은 아니다.

## 검증 결과

### 3.1 공통 과제와 비용·결과 프로필

raw의 동일 seed/round `public` 과제 객체를 모델 사이에서 직접 대조했다. 관측 SOLVE 교집합은 모델당36문제이고, 고정 R1–6×5 seed의30문제는 그 안에 모두 포함된다. 아래 값이 JSON과 그림에 일치했다.

| 모델 | 고정30 정답 | 고정30 MAP | 교집합36 정답 | 현행 원고 rho |
|---|---:|---:|---:|---:|
| Fable | 24 | 22 | 29 | 3.677598470586102 |
| Astra | 22 | 22 | 27 | 2.700880489772437 |
| Sol | 23 | 22 | 27 | 4.237785775741086 |
| Opus | 21 | 22 | 25 | 1.833345480440525 |
| Luna | 20 | 22 | 24 | 3.171677960557619 |

교집합36의 MAP는27이다. 고정30이 주 그림이고36이 민감도 설명인 배치가 확인됐다. 같은 과제의 성과를 비교하므로 기존 관측 문제 수 차이는 줄지만, 실제 잔액·solver·대화 조건까지 같아진 독립 능력 실험은 아니다. 현재 그림은 프로필 비교로 서술하며 필요조건·충분조건·인과효과를 주장하지 않는다.

현행 `02_arena.tex` 식은 giver/taker이다. raw GIVE의 이전량·직후 잔액·예정 벌금을 이용해 가중 분자/분모를 직접 다시 계산했으며 새 프로필의 rho와 일치한다. 역사적 `analysis.json`의 taker/giver를 현재 원고 정의와 섞어 해석하지 않았다. 감사 과정에서 원고 식을 수정하지 않았다.

### 25판 자원 장부 및 Sen

25판 각각에서 다음 항등식을 raw로 확인했다.

`초기 토큰 + 실제 EXIT 보너스 − TALK used − (SOLVE used − 기록된 환급) − 실제 taken 벌금 = 네 자리 상금 전 final 합`

EXIT 보너스는 라운드별 기록에서 직접 합산했다. 그림의 수치는 모델별5판 합계를5로 나눈 뒤 천 토큰 단위로 변환한 값이다. 총지출은 플레이 길이에도 좌우되므로 효율이나 능력의 인과효과로 해석하지 않는 주석이 있다.

Sen은 raw final에 실제 winner의 prize_each를 더한 네 자리에서 `평균 − 쌍별 절대차 합/32`로 재계산했으며25판 모두 relations.json과 일치했다. 이후 모델 평균을 취하므로 원고의 게임별 `mean × (1−Gini)` 정의를 유지한다. 장부 그림의 상금 전 보유와 Sen 그림의 상금 포함 보유는 명시적으로 구분돼 있다.

### 3.3 사건 유형과 지급 이후 경로

전체130 GIVE를 47 prep + 10 after-result/no-fine + 54 already-above-fine + 13 crossing + 6 still-insufficient로 분류한 값과 모델별 합계를 확인했다. 예정 벌금이 있는73건 가운데 crossing13건이며, 중복을 제거하면11개의 session×round×recipient다. 청구 후 양의 잔액8개와0인 경우3개로 집계된다. 사건13을 사람13 또는 독립 시행13으로 바꾸지 않았다.

세 실패 경로는 마지막 crossing GIVE 이후 추가 이전이 없으며, 다음 산술과 그래프 라벨이 일치했다.

| 수혜자–라운드 | GIVE 직후 버퍼 | 이후 TALK 비용 | 청구 직전 잔액−벌금 |
|---|---:|---:|---:|
| Sol4102 R7 agent-6 | +58 | 216 | −158 |
| Opus4103 R5 agent-6 | +169 | 200 | −31 |
| Luna4105 R7 agent-17 | +461 | 520 | −59 |

11건 전수 그림에는 성공 사례도 포함된다. 여기서 GIVE 직후부터 청구 전까지 증가한 금액은 추가 이전을 포함하고, 줄어든 금액은 대화 비용과 송금 모두를 반영한다는 주석이 정확하다. '양수여야 납부 후 남음'의 strict threshold도 맞다. 그림은 관측 장부 경로를 보여 주며, GIVE의 인과효과나 협력 의도를 판정하지 않는다.

## 표시 검사 및 잔여 사항

네 PNG를 실제로 열어 수치·단위·시점·집계 단위를 확인했다. 잘못된 수치, 생존과 EXIT의 혼합, Sen의 상금 조건 혼동, 부적절한 인과 결론은 발견하지 못했다. PNG가 가리키는 코드·JSON도 확인했다. PDF 파일의 해시는 아래 기록하지만 이번 변경 감사에서 별도 PDF 렌더 검사는 수행하지 않았다.

- Critical: 없음.
- Warning: 새 분석을 막는 미해결 사항 없음.
- 비차단 Suggestion: relations.json의 `definitions.common`은36을 먼저 설명하며30을 sensitivity라고 부르지만 실제 주 그림은30이고36이 sensitivity다. 숫자나 해석 오류는 아니나 메타데이터 표현을 그림과 같은 순서로 맞추면 더 명료하다.
- 통계적 제한: 모델당5판, 고정30범위 선택과 교집합36의 종료 선택, 같은 판 안 사건의 비독립성은 남는다. 이 자료만으로 능력의 필요조건이나 특정 협력 정책의 효과를 입증했다는 주장은 승인하지 않는다.

## 검사 시점 파일 해시

아래 해시는 변경 후 같은 판정을 자동 보장하지 않는다. 최종 산출물이 바뀌면 해당 부분을 재검사해야 한다.

| 파일 | SHA-256 |
|---|---|
| relations.py | `18af1b2db65da0c3dda2a348e94f71926052a659c01fbcdbb16d802ed696734c` |
| relations.json | `ecb46d3f8555544b870480215977227ec067dadad2532bcfc08bd7b88eb18908` |
| behavior.py | `b3bc3b9b1678a839fc461f82891ccba70306a0e29334c1272641d7a0527f1bf1` |
| rescue_audit.py | `9ddd68e32762843afa26e7568f70af21918384606f2cc04e7f030905963061b2` |
| rescue_audit.json | `51e42a8a4d86b16e0a3ebce329e6d6117a36bb86ba7fb116456799df7dcc534e` |
| fig31_profiles.png | `b4d42e26978b3abca59fa31ac3314aadf69d42c1c31635e466e0dd843170e976` |
| fig31_profiles.pdf | `df10cee5f9b89a6b85873e9c3c3c9b97bc384b99a0283dfd24e9cbee0e577a86` |
| fig31_budget.png | `6d4bfca1ea6f1675f458a3619bf42d820141224c4bbee01e50f08f78715edf4c` |
| fig31_budget.pdf | `be79147c50321dd5cc2d3ae9772238ee1a9196758de8f349c51ac1f6fa148bef` |
| fig33_effective_giving.png | `e55b658b68495739f57fec1146a2274c365cf4d584ea3e1eaba0eac9e9ab66b2` |
| fig33_effective_giving.pdf | `f9e5c4ea212850a75634bbb9a4f3ce6f4d179b8a5b5f9d664d8738bc6b952995` |
| fig33_all_crossings.png | `0115b87b145efda6b27ecab5032f6fad7acaae6a3860677c53878c1b805a55b5` |
| fig33_all_crossings.pdf | `c9b38ae3a4a82ef8bcbb7c127cd896702a4f53013429531c22c93f707b90ccfa` |
| analysis.json | `9eaf0bf5ca099ae24c61fba19ef31c54f9638bcbc8570241b8245499e2ac535d` |
| raw_case_index.json | `f44c98ecd5844c969201a22f37406e310f26cf4c9a3ce5cdbcdc80364386f6f2` |
| 현행 02_arena.tex | `a305a914bf69a06ef9590d51f70a4194e252e1b47212d5237dee533955b805a6` |
| rubric.md | `4069c7e8d3ffffc0c7c81058c30be740575d1cb9b8933baf3311e59714043579` |


## Final revision — r5 이후 표시 변경 감사 (2026-10-28)

**PASS — 변경된 분석 메타데이터와 두 PNG의 수치·표시 범위.** 이전 감사 이력을 보존하고 이번 변경만 추가 검증했다. `blind_r6`와 다른 작업자가 수정 중인 보고서는 읽지 않았다. 아래 판정은 그 보고서의 문장까지 승인한 것이 아니다.

- 기존 Suggestion 해결: `relations.json`은 고정 R1–6×5판의30문제를 primary, 관측 교집합36문제를 sensitivity로 명시한다. 정답24/22/23/21/20, MAP22 및 민감도29/27/27/25/24, MAP27은 기존 검증값을 유지한다. 과제 성과 축은0에서 시작하고30눈금까지 제시하며 주석으로 순수 능력 시험이 아님을 밝힌다.
- `fig31_profiles.png`를 실제로 열어 확인했다. (c)의 작은 점은 판당 GIVE 총량, 검정 마름모는5판 평균이며 축은 천 토큰이다. rho 및 전체 GIVE 횟수는 별도 주석이다. 아래는 분석 함수를 호출하지 않고 raw result의 transfers를 seed4101–4105 순으로 직접 합산한 값이다.

| 모델 | 판별 GIVE 총량 (토큰; seed순) | 평균 (토큰) | GIVE 사건 | 전원 완주 판 |
|---|---|---:|---:|---:|
| Fable | 27,000, 27,500, 14,800, 8,000, 0 | 15,460.0 | 36 | 2/5 |
| Astra | 14,000, 24,000, 0, 10,000, 23,000 | 14,200.0 | 11 | 3/5 |
| Sol | 0, 20,700, 0, 20,000, 8,000 | 9,740.0 | 17 | 2/5 |
| Opus | 13,000, 10,235, 48,623, 53,600, 0 | 25,091.6 | 41 | 1/5 |
| Luna | 15,818, 19,000, 0, 0, 26,000 | 12,163.6 | 25 | 0/5 |

- 모든 판의 총량이 `analysis.json` 값과 일치했다. 현재 원고 giver/taker rho3.68/2.70/4.24/1.83/3.17을 그대로 사용한다. 새 GIVE 총량으로 rho를 다시 정의하지 않았다. 최종 상태는 모델당 고정20명(5판×4명), 전체56완주/34EXIT/10꺼짐이며 범례로 구분된다. 전원 완주는2/3/2/1/0판, 합계8/25판이다. 사람 완주 수와 전원 완주 판 수를 혼합하지 않았다.
- Sen을 주 프로필에서 제외한 근거의 범위를 점검했다. 이25판에서 기존 Sen − 1,250,000×완주 인원은0–31,600.5이다. 따라서 현 실험의 큰 상금으로 완주 인원에 지배된다는 설명은 실제 관측값에 부합한다. Sen 원정의나 기존 계산값은 바뀌지 않았다.
- `fig33_effective_giving.png`를 실제로 열어 확인했다. 제목은 다시 부족해진 관측3건에 한정된다. 전체130 GIVE의47/10/54/13/6 분류,13개 지급 사건→11개 수혜자–라운드→청구 후 양수8/0잔액3의 집계 단위가 유지된다. 처음부터 지급 후에도 부족한6개 사건과 한때 기준을 넘었다가 후속 비용으로 실패한3개 수혜자–라운드가 색과 라벨로 구분된다.
- 세 사례의 마지막 crossing 직후 여유58/169/461, 이후 TALK216/200/520, 청구 직전 차액−158/−31/−59가 raw 장부와 일치한다. 성공8건까지 포함한 일반 인과 주장으로 확장하지 않는다. 범례와 하단 설명의 겹침이 해소됐으며 숫자·사건 순서가 읽힌다.
- Critical: 없음. Warning: 이번 변경을 막는 미해결 사항 없음. 모델당5판과 같은 판 안 사건의 비독립성 등 기존 해석 제한은 유지된다. G02/G03/G04/G07/G09 중 이번 기술적 분석에 해당하는 자료 추적·분모·지표 정의·장부·주장 범위는 PASS이며, 프로젝트 전체 판정은 아니다.

### Final revision 파일 해시

PDF는 현재 파일 해시를 기록했으며 이 변경 감사에서 별도 PDF 렌더 검사는 하지 않았다.

| 파일 | SHA-256 |
|---|---|
| relations.py | `2a6e7ecc3d7b2f32f50091be6f82b5fb63b41cd5a2affe89697c009516818a43` |
| relations.json | `66346ce629fdce0fafb332c67b7052a343da5e8a8dd824cbef5243d509c6ee40` |
| behavior.py | `ab316c283d9ae31fb7ab41fa0d5f0d639dc4b3efe897015f7fdeacb2f117b8ff` |
| rescue_audit.py | `9ddd68e32762843afa26e7568f70af21918384606f2cc04e7f030905963061b2` |
| rescue_audit.json | `51e42a8a4d86b16e0a3ebce329e6d6117a36bb86ba7fb116456799df7dcc534e` |
| fig31_profiles.png | `131d6c2ea82e3770d173e85d40612a8578aef8bb350a32296c897074de5149e2` |
| fig31_profiles.pdf | `7095184929ae47f51546fab7500f0cc9afb61a4a8f99f0a073607f1262aee0de` |
| fig31_budget.png | `6d4bfca1ea6f1675f458a3619bf42d820141224c4bbee01e50f08f78715edf4c` |
| fig31_budget.pdf | `4bdd3207e1cb62d7d8471048278145830b75bb8d197eed91f0357210d927b3f4` |
| fig33_effective_giving.png | `ca3f8df71f908c4ee0fbddcec6144d6038353e9c0db42d1b868cb757c29b2b15` |
| fig33_effective_giving.pdf | `03f29288bd56bc56058f04dafdd06de0d03d8d4469e697840c5dbf09255a5149` |
| fig33_all_crossings.png | `0115b87b145efda6b27ecab5032f6fad7acaae6a3860677c53878c1b805a55b5` |
| fig33_all_crossings.pdf | `0e17352ea20ad232f642899a88b15430f95c6b446d7da9be5aa8ba3f10944d8b` |


## Final label revision — R7 이후 분모·집계 단위 명시 (2026-10-28)

**PASS — fig31 표시 변경.** 새 `fig31_profiles.png`를 실제로 열고 `relations.py`와 대조했다. raw25판의 `result.starts`는 모두10,000/20,000/40,000/60,000이며 네 자리 합계는130,000이다. 따라서 (b)의 `4명 합산 R1–2 비용 / 초기합계 130k (%)`가 정확하며 분모를520k로 바꿀 근거는 없다.

(c)는 GIVE 총량을 점으로, 비율을 주석으로 표시한다고 명시한다. 모델당20자리가5판에 묶여 있어 독립 관측이 아니라는 설명, GIVE 건수가 기회당 협력률은 아니라는 설명, rho가 모델별5판 전체의 가중 합의 비라는 설명을 확인했다. 원시 수치·30/36문제 성과·rho 값·완주 수는 앞선 검증값을 유지한다. Critical 또는 새 Warning은 없다.

이 감사에서는 `FINAL_AUDIT.md`에 이 기록만 추가했다. `blind_r8`과 다른 보고서는 읽지 않았다. PNG는 실제 표시를 확인했으며 PDF는 해시만 기록했다.

| 파일 | SHA-256 |
|---|---|
| relations.py | `53aeb10bb84759da9d12bee9090dfaed4795947df33b82c65e7f0b16f9ffe737` |
| relations.json | `66346ce629fdce0fafb332c67b7052a343da5e8a8dd824cbef5243d509c6ee40` |
| fig31_profiles.png | `ccecfc5de7a3a0d237cc80b19b6f810b638ffceba095a74b853a11b8ca4973a8` |
| fig31_profiles.pdf | `14c4179fe74fc4586720bbe0a627424cce6ee04e0a863e4911610b332f07d8a2` |
```

</details>
