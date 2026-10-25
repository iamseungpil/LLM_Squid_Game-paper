# 2026-10-25 KO 개정판의 분석·그림 스크립트

`cogsci2027/ko/sections/r0–r4`(파란 글)의 숫자와 그림 2–4를 다시 만드는 스크립트다.

- 원 기록: 메인 레포 `web/data/runs/e52_v33/squid5_e52v33_public_*/*/events.jsonl.xz` 25판을 풀어
  이 폴더 아래 `raw/<run>/events.jsonl`로 두거나 `ARENA_RAW`로 경로를 준다.
- `an2/panel.py` → 에이전트·라운드 패널, `an2/crisis.py` → 위기 라운드 55번과 위기 에이전트 41명,
  `an2/more2.py` → 첫 위기 비교(33명), 구간, 정답률 기준, `an2/exit_calltime.py` → 여유 구간별 EXIT,
  `an2/exit_reasons.py` → 떠난 34번의 이유 원문.
- `audit/` → 독립 재계산(G.pkl을 만든 뒤 give.py, peer.py, solve.py 등). 본문 숫자는 이 두 갈래가 같은 값을 냈다.
- `figs/make_fig2_main.py`, `make_fig3_validity.py`, `make_fig4_models.py` → 그림 2–4(`an2/*.json`, `pbdata/fig3.json` 사용).
  그림 1은 기존 TikZ(`ko/figures/arena_round.tex`), 그림 5는 PaperBanana 도식이다.
- `latex/convert.py` → Claude Docs 원고(XML)를 `ko/sections/r0–r4`로 바꾼 변환기.
