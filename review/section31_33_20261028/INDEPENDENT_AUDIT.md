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
