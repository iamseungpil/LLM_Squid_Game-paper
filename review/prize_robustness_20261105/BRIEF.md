# BRIEF — prize robustness

## Scope
사용자 요청: 기존 논문 골격을 보존하고 결과절에 상금 구조·크기 robustness 절 하나와 비교 그림을 추가한다. 500만 고정 다섯 모델 및 Fable 60만 나눔을 각각 10판(4101–4110) 채운 뒤 작성한다. 기존 다른 절은 보호한다. 사용자 추가 요청으로 Table 1 협력을 참여자·라운드당 지원량 하나로 통일하고, 안전선 이상 이탈·첫 위기 지원 비율·GIVE 총량은 부록 보조 표로 옮긴다.

## Style
프로필 juhyeon-ko-academic, 샘플 1,331어절, reliability high, slips off. Writer는 ditto_table_writer 에이전트(현재 모델 상속). 후속 본문 작성도 writer에게 맡긴다. 최종 새 절은 이력 없는 Anthropic Fable 및 OpenAI 리뷰어로 독립 검토한다. 프로필 경로: /Users/bagjuhyeon/.agent-skills/modes/day/codex/skills/ditto-writer/profiles/juhyeon-ko-academic/profile.md. Anchors와 sample.md를 함께 읽는다.
원칙: /Users/bagjuhyeon/.agent-skills/modes/day/codex/skills/ditto-writer/references/principles.md 및 저장소 docs/paper-writing-principles.md. 질문 회수·결론 선행·연결된 문단·필요한 숫자만 사용한다. 기존 원문 표 캡션은 original/에 보존했다. 신설 절은 원문이 없어 결과 전 문장을 만들지 않는다.

## Content ledger
- Main 조건: 2,000만 나눔, 전원 완주 시 개인 500만.
- 높은 고정 조건: 개인 500만, 남은 인원과 무관.
- 작은 나눔: 총60만, 전원 완주 시 개인15만.
- 작은 고정: 개인15만, 기존 네 모델만. Fable의 이 칸은 요청된 보충 범위가 아니므로 미관측으로 명시.
- C는 RMST/8. 협력은 각 판 GIVE 총량 / 라운드 시작 참여자 수의 합을 구해 10판 평균. rho는 모델별 GIVE를 합쳐 산출.
- 모든 조건 같은 게임 설정·시드·effort. 실행 시점·CLI 이력이 다르므로 주장 범위를 결과와 provenance에 맞춘다.
- 상금에 둔감해야만 robustness라는 결론을 전제하지 않는다. 변화하는 행동과 유지되는 측정 관계를 구분한다. 내적 동기/인과 증명으로 확대하지 않는다.
- 본문의 주장은 새 본문 그림 자체로 지지해야 한다. 부록만 근거로 쓰지 않는다.

## Progress
초기 원고 push: CogSci 5c78ba5, 원격 검증. 신규60판을 모두 완료했고 각 모델·조건10시드의 원시 기록을 검증했다. results/prize_robustness_20261105.json은 main50·flat5m50·split600k50·flat150k40의 총190판을 포함한다. 기존source해시와 상금외설정·실지급액·1089개ablation퍼즐라운드 대조를 통과했다. ko/figures/prize_robustness_20261105의 새본문3패널과 부록3행그림을 생성·시각검사했고, 본문57점은 집계값과 일치한다.
표 정리 writer 완료, 원시source30개 해시 및 50판 지원량 독립 대조 통과, PDF p5 / 보조표Q.1 p72 렌더 확인. 새 결과절3.4와부록O를작성하고r1전체PDF75쪽/부록제외9쪽을검증했다. r3까지허용문단의반복결말·도입문만정리했고새두독자의수정대상점수25.3/24.7,high0,한사람예로수렴했다. 최종full/bodyPDF75/9쪽과16target일치를검증했다. 검토는 수정prose와 인접고정문맥으로 만든 완성문서 발췌를 이력없는 두 독자에게 주며, 실제full/bodyPDF 정확성은 별도 검증한다. 실험·검증 기록은 저장소 .scratch/prize-robustness-20261105/.
포스터는 poster/thesis_20261105에187파일 원본복사·해시확인. 새50판 결과를 기존그래프형태로 반영한 임시 미리보기두버전은1쪽으로검증했다. 논문완료뒤실제포스터에13수치문구와3board배치교체를적용했고두버전각1쪽/overfull0/15핵심문구일치·렌더·독립데이터감사를통과했다. thesis원본187파일은해시불변이다.
