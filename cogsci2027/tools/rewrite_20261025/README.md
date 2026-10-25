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

## 10-25 의도 재정렬판(공존의 세 요소, 그림 2–4 v4)

- `an3/analyze.py` → 3.1 그림 2(여유 구간별 정답률·GIVE·EXIT, 위기 사슬, 판 단위 오답과 끝까지 남은 수·Sen 상관), 모델별 지표(표 3), 페르소나 장면 수. `audit/G.pkl`(audit/build.py), `an2/panel.json`, `audit/elig.json`, `audit/ep.json`, `../../results/arena_v33_*.json`을 읽는다.
- `an3/gifts_adj.py` → GIVE 직후 두 쪽 여유(결과 뒤 대화는 곧 낼 벌금을 뺌)와 모델별 ρ(판 부트스트랩 2,000번).
- `audit_r2/audit_r2.py` → 위 숫자의 독립 재계산(`ARENA_RAW`). 11개 묶음 중 9개가 일치했고, 두 곳(GIVE 여유의 벌금 차감, 혼자 남은 라운드의 벌금 24,000)은 정의를 고쳐 맞췄다.
- `figs/make_fig2_v4.py`, `make_fig3_v4.py`, `make_fig4_v4.py` → 그림 2–4. 그림 5(PaperBanana)는 이 판에서 뺐다.
- `constraints.md` → 제약 원장(1–22).

## 10-25 6쪽판(본문 표 하나, 부록 표 셋)

- `r14/seg1.md`(초록·서론·2.1), `r14/seg2.md`(2.2–4장, 본문 표 1) → `r14/md2tex.py`가 `ko/sections/r0–r4`와 `r5_appendix.tex`를 만든다.
  실행: `python3 r14/md2tex.py r14/seg1.md r14/seg2.md <이전 sections 폴더> <출력 폴더>`. 부록 표 A1–A3(관련 연구, 지표 정의, 페르소나)은 이전 판 sections에서 그대로 떼어 와 번호만 바꾼다.
- 그림 2–4의 패널 제목은 무엇을 보는 그림인지 명사형으로 짧게 달고, 해석은 캡션에 둔다(`figs/make_fig*_v4.py`).
- 빌드(`bash build.sh cogsci ko`)에서 본문은 6쪽 왼쪽 단에서 끝나고 참고문헌이 이어진다.
