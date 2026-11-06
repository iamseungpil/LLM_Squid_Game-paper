# 상금 ablation 독립 데이터 감사

판정: **PASS — 이번 데이터·집계 변경 범위**. 필수 수정 없음. 전체 아레나의 ARENA_VALIDATED/RELEASE_READY 판정은 아니다. G01–G06, G09, G11–G12의 전체 요건은 이번 감사에서 미평가다.

평가자: `/root/prize_final_verifier`; 2026-11-06. 분석 작성자와 별도 에이전트로 검증했다. 기존 성공 JSON을 신뢰하는 데 그치지 않고, 별도 Python 계산으로 원시 사건·결과·설정을 읽고 합계와 구간을 재계산했다. 소스·원고·그림을 수정하거나 모델을 호출하지 않았다.

| 범위 | 직접 확인한 증거 |
|---|---|
| G07 지표 | 190판 모두 완료 session ID로 원시 사건을 골랐다. GIVE 성공 사건 합과 결과 장부의 transfers 합이 같았다. 각 판의 총 GIVE를 라운드 시작 참여자 수 합으로 나누고 모델별 10판을 평균한 값이 보고서와 일치했다. 지원 후 잔액에서 해당 벌금을 뺀 여유를 다시 계산했으며, 모든 GIVE의 금액 가중 분자/분모를 합친 rho도 일치했다. C는 최초 이탈 라운드/8과 일치했다. |
| G08 코호트·비교 | 새 6개 작업은 각각 시드 4101–4110의 완료 10판이다. main 50, flat5m 50, split600k 50, flat150k 40으로 총 190판이다. 기존 main·flat150k의 게임 배열과 원시 출처가 동결본과 동일했다. 72개 원시 출처 해시와 6개 실행 설정 해시가 일치했다. 시작 잔액·상금 외 설정·모델·high 추론 설정을 대조했다. 본 실험의 시드별 퍼즐과 ablation 1,089라운드가 모두 같았다. |
| G08 불확실성 | 본문 그림 57개 점과 57개 95% 구간을 독립 재계산했다. 90개 조건 차이와 대응 시드 부트스트랩 구간도 일치했다. 10,000회 재표집, rho 분모 0인 표본 제외 수까지 확인했다. Fable/flat150k는 누락 상태이며 0으로 대체되지 않았다. |
| G10 실행·한도 | 새 Fable·Opus flat5m의 중단 세션 각 하나가 완료 분석에서 제외됐다. 기존 저상금 자료에도 미완료 세션 3개가 남아 있으며 동일하게 제외됐다. 두 Fable 대기 지점의 원시 파일 prefix 해시, 재개 session ID, 추가 성공 호출 수·출력 토큰(16/7,876 및 25/4,751)을 현재 파일에서 재확인했다. 계정 배정은 jobs.json의 요청 범위와 일치한다. |

Table 1과 보조 표는 동결 자료에서 생성한 문자열과 현재 TeX가 정확히 같다. 협력은 참여자·라운드당 지원량 하나, 자기 보존은 rho 하나다. 안전선 이상 이탈·GIVE 총량/횟수·첫 위기 지원 비율은 보조 표에 있다.

해석 한계: 역사적 본 실험과 추가 조건의 실행 시점·CLI/하네스가 다르므로 조건 차이를 순수한 인과 효과로 단정할 수 없다. 모든 관측 셀의 pooled rho 점추정이 1보다 크다는 사실은 개별 지원이나 모든 신뢰구간이 1보다 크다는 뜻이 아니다. 계정 잔여 구독량/청구 비용은 이 감사로 확인되지 않았다. PDF 조판과 포스터는 별도 검증 대상이다.

검증 대상 SHA-256:
- rubric.md: `4069c7e8d3ffffc0c7c81058c30be740575d1cb9b8933baf3311e59714043579`
- results/prize_robustness_20261105.json: `bd0d6379cf66bd6d9b93477662acc638ad695cc205480769649b516c5a54c0c7`
- tools/prize_robustness_20261105.py: `1a1934d9ee9b4aa287ef085fa17d80edc926c6f7923094705923d79629593a48`
- tools/plot_prize_robustness_20261105.py: `3785b2a2e91eaaaa90a723dd08ed81d37f111ee6649f7cec5d4f63f6f6170cf0`
- tools/table1_metrics_20261105.py: `20e8be717ef207f0e53dbec14e39d4c1c788ba0d15ff2d38b770511f3471de1d`
- ko/figures/prize_robustness_20261105/plotted_values.json: `40624d6f1dfffaa02f490755d1ad1c73051c4cd09519a49071d1491852e76768`

위 상대 경로는 rubric.md를 제외하고 paper/cogsci2027 기준이다. 실행·한도 증거는 `.scratch/prize-robustness-20261105/`의 jobs.json, experiment_provenance.json, 완료 및 quota_resume_validation 기록과 해당 원시 run 디렉터리다.
