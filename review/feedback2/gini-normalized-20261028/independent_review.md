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
