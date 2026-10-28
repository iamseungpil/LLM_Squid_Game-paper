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
