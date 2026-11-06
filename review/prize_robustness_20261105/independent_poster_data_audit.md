# 포스터 데이터 독립 감사

**PASS — 필수 수정 없음.** 평가자 `/root/prize_final_verifier`, 2026-11-06. 변경한 포스터 데이터와 소스만 검증했으며, 원본 보존 및 최종 PDF 시각 검사는 root의 별도 검사다. 소스·그림 재생성 없이 이 보고서만 작성했다.

- 네 생성 소스는 동결된 `cohort_public_20261105.json`의 본 실험 50판과 `exit_reasons_20261104.json`의 발화 64개를 읽는다. poster.tex의 데이터 그래프 참조 목록은 원본과 동일하다. 기존 완주 비교선·여유별 행동 막대·GIVE/ASK 막대·이탈 이유 열지도 및 참가자 보드를 유지했다.
- 13개 교체 문구가 현재 poster.tex에 각각 한 번 존재하고 이전 문구는 남지 않는다. 50판·200명·전원 완주 16판, 무지원 10판의 전원 완주 0판을 확인했다. 보드 명령 200개는 자리 중복 없이 완주 116·이탈 61·꺼짐 23이며 전원 완주 테두리 16개다. 모델·게임별 상태도 동결 자료와 일치한다.
- GIVE 사건으로 안전선 이상에서 시작한 지원 275건 중 유지 264건을 재계산했다. 낮은 여유의 이탈 34/65=52.3%, Fable 풀이 전 지원 118,800/192,730=62%, 다른 네 모델은 결과 뒤 지원량이 더 많음을 확인했다.
- 발화별 agreed_labels를 다시 세어 위험 61/64, 보너스·정규 업무 47/64와 열지도의 모델별 25개 셀이 일치했다. 실제 이탈자 61명과 발화 분모 64개가 구별된다.
- poster_plot_values.json의 출처 해시·여유별 분자/분모·모델별 GIVE/ASK 합계가 일치했다. 부분 완주 34판과 전원 완주 16판의 6개 평균·5,000회 시드 묶음 재표집 구간을 별도 계산해 재현했다. 이 그림의 rho는 정의된 판별 rho의 산술평균이며, 모델 배열용 pooled rho와 구분된다.

검증 SHA-256 (포스터 경로는 `paper/poster/thesis_20261105/` 기준):
- poster.tex: `4b63462ffe6ed77a4351083bfb2d3e744d058d2f6b527f47e27cfb7f31b9d7c5`
- figs/poster_data.py: `f9ffb370eb1bee5e4fd7f08c37e5ff583c99e650cedcb32c88181d1129994f35`
- figs/poster_figures.py: `b90765ddfc078cc5331b4c5325c07f90fcc857aa489bb3fa0c0efac3855a768b`
- figs/poster_board.py: `be1faa207496b5c708f1b797e0b4f62909b5f31490000ad8f06edb296b201f01`
- figs/poster_exit_reasons.py: `008420956b3b0c007d3283f51690961f4c809501cbbf906db69e349fff505670`
- figs/poster_board_data.tex: `1c3b7460d9137a0999384ed3cb7999f91a1da7fb714323036ddad930c0721d3e`
- figs/poster_plot_values.json: `f4043facc6e374cabb9367a4f8f8bc37023889531a746fb9d06adbbe00eb1406`
- cohort_public_20261105.json: `a8c020452696b28a5e95ec50ebe666e36500b9c6554b866ef4b338f3d2b08d4c`
- exit_reasons_20261104.json: `1d3714eb8a396134831da976c8c1d8f756487924dbed0c0230a12b8f38651f36`
