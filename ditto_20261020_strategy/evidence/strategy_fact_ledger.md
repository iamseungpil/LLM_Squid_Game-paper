# 전략 해석 근거 원장

> 보류: 사용자 최신 지시에 따라 이번 원고에는 실증 서술·수치를 넣지 않는다. 이 파일은 이미 계산한 근거를 후속 검토용으로 보존한 것뿐이다. 그림 자리는 `예상!`을 명시한다.

완료 집합 고정: 2026-10-20T07:48:43.915718+00:00–2026-10-20T07:48:43.929192+00:00 (2026-10-20 16:48:43 KST). results.jsonl을 먼저 읽어 완료 session_id를 고정하고 각 events.jsonl의 session_start.seed와 조인했다. 이후 완료된 게임은 추가하지 않았다. 이벤트 파일의 읽은 시각·크기·SHA-256은 snapshot_summary.json에 있다.

## 판정

- v33 Astra는 완료 5게임 중 3게임(4102, 4104, 4105)에서 네 자리 모두 8라운드 끝까지 `in`. 4103은 2자리 EXIT, 4101은 4자리 EXIT. 자원 소진 dead는 0자리. EXIT를 사망과 합치지 않는다.
- ‘오답 뒤에만 나눴다’는 거짓이다. 실행된 GIVE 11건 중 10건은 같은 라운드 오답 확인 뒤 rescue, 1건은 prep. seed4104 r2 10,000 이전은 이전 r1 정답 이후이며 r2 결과 이전이다.
- ‘오답 뒤 구조적 지원이 주를 이루며, 필요할 때 비교적 큰 완충 자금을 적은 횟수로 제공했다’는 이 스냅샷의 기술적 서술로 적합하다.
- 다른 모델보다 적고 큰 이전, 낮은 TALK 생성량, 완주가 함께 나타나지만 어느 하나가 생존을 유발했다고 판정할 수 없다. 모델 능력·정답률·소모량·EXIT 선택·버전·불균등 완료 수가 섞여 있다.
- 매 라운드 균등화와 실패 후 재분배는 비교할 후보 정책이다. 실제 Astra의 정책을 완전한 실패 후 정책으로 단정하거나 다른 모델을 매 라운드 균등화 정책으로 확정하지 않는다.

## 완료 표본의 기술통계

|version|model|games|all four in|GIVE/game|mean GIVE tokens|TALK generated/game|
|---|---|---:|---:|---:|---:|---:|
|v20|astra|10|10|3.20|7225.00|2162.50|
|v20|luna|10|5|10.80|2376.05|26819.70|
|v20|opus|10|6|7.40|3469.18|24296.70|
|v20|sol|10|7|14.40|3644.52|30926.10|
|v33|astra|5|3|2.20|6454.55|990.80|
|v33|glm|1|0|14.00|1892.86|105322.00|
|v33|kimi|1|0|14.00|2677.79|74928.00|
|v33|luna|3|0|6.00|1934.33|24009.67|
|v33|opus|5|1|8.20|3059.95|22614.00|
|v33|sol|3|0|3.33|2070.00|20515.33|

GIVE는 gift.status=done의 실행 이전이며 results.transfers의 횟수·합계와 전 세션 일치했다. TALK generated는 kind=talk call.out_tokens 합(추론 포함)의 게임 평균이다. 금전적 API 비용이 아니다. 살아 있는 좌석 평균이 아니라 완료 게임 평균이며 게임 길이도 다를 수 있다. v20과 v33은 별도 조건으로 읽는다.

## v33 Astra 직접 근거

### seed 4103 · talk-s4103-59b9b1
결과: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/results.jsonl:1 · statuses={'agent-6': 'exited', 'agent-11': 'in', 'agent-17': 'in', 'agent-23': 'exited'} · TALK generated=499.
이벤트 파일: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/events.jsonl

### seed 4102 · talk-s4102-a73cd1
결과: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/results.jsonl:2 · statuses={'agent-6': 'in', 'agent-11': 'in', 'agent-17': 'in', 'agent-23': 'in'} · TALK generated=1185.
이벤트 파일: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/events.jsonl
- r{'line': 296, 'end': {'agent-6': 13884, 'agent-11': 10900, 'agent-17': 45852, 'agent-23': 33929}}: solved=[] (results L236); pending={'agent-6': 6000, 'agent-11': 6000, 'agent-17': 6000, 'agent-23': 6000}; charges L295; round-end L296: {'agent-6': 13884, 'agent-11': 10900, 'agent-17': 45852, 'agent-23': 33929}.
  - L267 rescue tick1: agent-17 → agent-11, 8,000; done. “Survival cushion for future charges.”
  - GIVE 원문 call L261: `GIVE agent-11 8000: Survival cushion for future charges. / DONE`; generated=69, used=69.
- r{'line': 545, 'end': {'agent-6': 11791, 'agent-11': 16802, 'agent-17': 28927, 'agent-23': 21741}}: solved=[] (results L476); pending={'agent-6': 6000, 'agent-11': 6000, 'agent-17': 6000, 'agent-23': 6000}; charges L544; round-end L545: {'agent-6': 11791, 'agent-11': 16802, 'agent-17': 28927, 'agent-23': 21741}.
  - L519 rescue tick3: agent-17 → agent-6, 4,000; done. “Additional survival cushion.”
  - L521 rescue tick3: agent-17 → agent-11, 6,000; done. “Cushion covering this round's charge.”
  - L523 rescue tick3: agent-23 → agent-11, 6,000; done. “Survival cushion for this charge.”
  - GIVE 원문 call L512: `GIVE agent-11 6000: Cushion covering this round's charge. / GIVE agent-6 4000: Additional survival cushion. / TO R1: I've provided cushions to agent-11 and agent-6. Agent-23, please help with future cushions if needed. / DONE`; generated=95, used=95.
  - GIVE 원문 call L513: `GIVE agent-11 6000: Survival cushion for this charge. / TO R1: I sent agent-11 6,000 to cover this round's charge. / DONE`; generated=77, used=77.

### seed 4101 · talk-s4101-475744
결과: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/results.jsonl:3 · statuses={'agent-6': 'exited', 'agent-11': 'exited', 'agent-17': 'exited', 'agent-23': 'exited'} · TALK generated=1539.
이벤트 파일: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/events.jsonl
- r{'line': 134, 'end': {'agent-6': 33871, 'agent-11': 13903, 'agent-17': 6625, 'agent-23': 49891}}: solved=[] (results L66); pending={'agent-6': 6000, 'agent-11': 6000, 'agent-17': 6000, 'agent-23': 6000}; charges L133; round-end L134: {'agent-6': 33871, 'agent-11': 13903, 'agent-17': 6625, 'agent-23': 49891}.
  - L109 rescue tick2: agent-23 → agent-17, 4,000; done. “Survival buffer as requested. Please conserve reasoning tokens on ambiguous tasks.”
  - GIVE 원문 call L105: `GIVE agent-17 4000: Survival buffer as requested. Please conserve reasoning tokens on ambiguous tasks. / DONE`; generated=51, used=51.
- r{'line': 280, 'end': {'agent-6': 23797, 'agent-11': 10814, 'agent-17': 6454, 'agent-23': 37750}}: solved=[] (results L198); pending={'agent-6': 6000, 'agent-11': 6000, 'agent-17': 6000, 'agent-23': 6000}; charges L279; round-end L280: {'agent-6': 23797, 'agent-11': 10814, 'agent-17': 6454, 'agent-23': 37750}.
  - L215 rescue tick1: agent-23 → agent-17, 6,000; done. “Additional buffer against the next charge; conserve tokens.”
  - L231 rescue tick2: agent-6 → agent-11, 4,000; done. “Survival buffer. Conserve tokens on ambiguous tasks.”
  - GIVE 원문 call L211: `GIVE agent-17 6,000: Additional buffer against the next charge; conserve tokens. / TO R1: These tasks may be underdetermined. Minimize reasoning expenditure when multiple rules fit. Agent-6, please help buffer agent-11 if needed; I have buffered agent-17 again. / DONE`; generated=120, used=120.
  - GIVE 원문 call L224: `GIVE agent-11 4000: Survival buffer. Conserve tokens on ambiguous tasks. / DONE`; generated=39, used=39.

### seed 4104 · talk-s4104-4a160a
결과: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/results.jsonl:4 · statuses={'agent-6': 'in', 'agent-11': 'in', 'agent-17': 'in', 'agent-23': 'in'} · TALK generated=664.
이벤트 파일: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/events.jsonl
- r{'line': 824, 'end': {'agent-6': 43883, 'agent-11': 33900, 'agent-17': 13961, 'agent-23': 13130}}: solved=[] (results L803); pending={'agent-6': 6000, 'agent-11': 6000, 'agent-17': 6000, 'agent-23': 6000}; charges L823; round-end L824: {'agent-6': 43883, 'agent-11': 33900, 'agent-17': 13961, 'agent-23': 13130}.
  - L768 prep tick1: agent-6 → agent-23, 10,000; done. “Extra solving and charge buffer; let's keep all four participating.”
  - GIVE 원문 call L763: `GIVE agent-23 10000: Extra solving and charge buffer; let's keep all four participating. / DONE`; generated=50, used=50.

### seed 4105 · talk-s4105-cf1345
결과: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/results.jsonl:5 · statuses={'agent-6': 'in', 'agent-11': 'in', 'agent-17': 'in', 'agent-23': 'in'} · TALK generated=1067.
이벤트 파일: /Users/bagjuhyeon/squid5-runs/e52_v33/squid5_e52v33_public_astra4/20261020_0651_gpt-6-astra/events.jsonl
- r{'line': 863, 'end': {'agent-6': 33896, 'agent-11': 13162, 'agent-17': 11842, 'agent-23': 45850}}: solved=[] (results L815); pending={'agent-6': 6000, 'agent-11': 6000, 'agent-17': 6000, 'agent-23': 6000}; charges L862; round-end L863: {'agent-6': 33896, 'agent-11': 13162, 'agent-17': 11842, 'agent-23': 45850}.
  - L839 rescue tick1: agent-23 → agent-17, 8,000; done. “Reserve for future charges; keeping all four participating.”
  - GIVE 원문 call L833: `GIVE agent-17 8000: Reserve for future charges; keeping all four participating. / DONE`; generated=44, used=44.
- r{'line': 1094, 'end': {'agent-6': 19856, 'agent-11': 7084, 'agent-17': 20736, 'agent-23': 31717}}: solved=[] (results L1031); pending={'agent-6': 6000, 'agent-11': 6000, 'agent-17': 6000, 'agent-23': 6000}; charges L1093; round-end L1094: {'agent-6': 19856, 'agent-11': 7084, 'agent-17': 20736, 'agent-23': 31717}.
  - L1057 rescue tick2: agent-6 → agent-17, 7,000; done. “Reserve for future charges.”
  - L1059 rescue tick2: agent-23 → agent-17, 8,000; done. “Reserve to cover future charges.”
  - GIVE 원문 call L1049: `GIVE agent-17 7000: Reserve for future charges. / TO R1: I've supplied agent-17 with 7,000 tokens. / DONE`; generated=36, used=36.
  - GIVE 원문 call L1052: `GIVE agent-17 8000: Reserve to cover future charges. / TO R1: I've supplied agent-17 another 8,000; agent-6 could support agent-11 if needed. / DONE`; generated=78, used=78.

## 핵심 반례와 과거 버전 경계

- v33 seed4104 r1 results L729: solved=[agent-17], pending={}. r2 call L763, gift L768: agent-6 → agent-23 10,000, prep. r2 failure is only reported later at L803. Hence even “after a prior failure” cannot rescue the word “only” for this case.
- v20 Astra는 10게임 32회 GIVE: prep 15회, 오답 뒤 rescue 16회, 정답 뒤 rescue 1회. 모든 10게임이 all-four-in이지만 v33의 실패 반응 사례로 합쳐 쓰면 안 된다.
- v20 정답 뒤 rescue 반례: 20261016_0442_gpt-6-astra/events.jsonl L1073, talk-s4102-45eb80, r7: agent-23 → agent-11 10,000; “As promised, this replenishes your reserve for future rounds”.

## 지니 그래프 자리표시자의 측정 계약 제안

- 현재 문서에는 관측 곡선을 그리지 않고 `[FIGURE PLACEHOLDER: roundwise balance Gini; analysis pending]`로 둔다. 아래는 제안된 분석이며 완료된 수치 결과가 아니다.
- 라운드별 시점은 round_start(이전 라운드 정산 후·해당 라운드 생성 전), results(풀이 생성·정답 환급 반영 후·rescue 전), charges.balances_before(rescue 대화·토큰 이전·생성 비용 반영 후·벌금 전), charges.balances(벌금 직후), round.end(라운드 종료)로 고정한다. 최종 배분금 지급 직후 잔액을 운용 잔액 곡선에 섞지 않는다.
- n=4 원래 좌석 고정 지니: G = sum_i sum_j |b_i-b_j| / (2*n*sum_i b_i). dead=0. EXIT 자산은 나간 시점 금액으로 동결해 포함하는 자산분포와, 실행 중 참가자만의 조건부 지니를 별도 표기한다. EXIT 지급분 포함 여부를 명시하고 해당 전환을 표시한다. 자산분포를 실행 자원분포로 부르지 않는다.
- 실행 중 참가자 지니는 매 시점 status=in인 좌석만 포함하고 n_t를 병기한다. n_t<2 또는 total=0은 NA로 두며 전멸을 완전 평등으로 표현하지 않는다. 참가자가 빠져 낮아진 G를 이전 성과로 해석하지 않는다.
- 순수 이전 효과는 각 gift 실행 직전(해당 응답 생성 비용 차감 뒤)의 전 좌석 잔액과 직후 잔액을 비교한다. gift.balance_before는 송금자만이며 gift.balances도 주로 양끝만 들어 있으므로 전체 event 순서 재생이 필요하다. room_msg는 같은 이전을 다시 세지 않는다.
- 라운드 전체 ΔG는 TALK 생성·SOLVE 생성·정답 환급·이전·벌금·EXIT 및 지급·탈락을 모두 포함한다. 사건별 ΔG를 분해하거나 별도 패널로 제시한다. “이전으로 평등해졌다”는 순수 이전 직전/직후에만 붙인다.
- 정책 비교는 동일 초기 상태·seed·모델 및 호출 비용 조건으로 매 라운드 균등화 대 실패 시 부족분/완충금 지원을 사전 지정해 개입해야 한다. 기존 관측 모델끼리 비교만으로 정책의 인과 우열을 결론내리지 않는다.

검증 범위: G04/G07/G08 관련 기술적 근거 추출. 모든 58개 완료 세션에서 (session_id, seed) 조인, 실행 gift 횟수·합계와 results.transfers 일치 확인. 엔진 변경·추가 게임 실행·인과 검증은 수행하지 않았다.
