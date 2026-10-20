# CogSci v33 국문 수정
사용자는 현재 수정된 v33 코드를 바탕으로 Method의 아레나 설정, 표의 평균 Score를 Sen-index로, 기존 TikZ에서 달라진 설정만 최소 수정하라고 했다. ditto-writer juhyeon 문체를 명시했다. 원본은 original/에 보존했다. 작성은 작업복사본에 하고 검증 뒤 기존 원고에 반영한다.
프로필 /Users/bagjuhyeon/.claude/skills/ditto-writer/profiles/juhyeon-ko-academic/profile.md 및 sample.md를 읽어라. slips off. writer는 gpt-6-astra. 최대 6라운드. 블라인드 대상 30% 이하 high0 한사람 true. 신규 사실 때문에 원문 길이 제한은 섹션 전체 +25%까지, 새 주장을 추가하지 않고 필요한 설명만. 기존 연구/표 수치를 날조하지 않는다.

## 고정 범위
04_arena.tex의 첫 공존 판단 문단, rho 수식 및 해석, 기존 결과의 GIVE/rho/TV/대화 분석과 인용은 유지한다. 결과의 점수 용어/수치 및 구버전 구별은 수정 가능. 01_introduction.tex는 점수 설명 마지막 문장과 arena-round 캡션만 변경. 표와 figure의 숫자는 별도 기계작업한다. 영어판은 Method TODO 틀뿐이므로 새 영어 원고를 작성하지 않는다. 변경할 문장만 최소 수정한다.

## 검증 사실 (기준 코드는 /Users/bagjuhyeon/wt/squid5-e52)
F1 e52_game.py Settings 및 configs/squid5/e52v33_public_sol4.yaml: 동종 모델 별도 인스턴스4, 모델 동일 여부 미공개. 60000/40000/20000/10000 시작,8라운드 비공개. 생성(추론포함)즉시차감 읽기무료0꺼짐.
F2 _rotate: 참여 중인 자리만 solver, seed로 섞은 순환에서 한바퀴 한번. 규칙서는 무작위 배정만 말하고 순서/순환 공개하지 않음. solver EXIT 금지(혼자 남으면 허용). TALK 중 solver꺼짐시 대체 solver.
F3 _rooms/rulebook: 풀이전 TALK→SOLVE→결과후 TALK→CHARGES. 두 TALK각최대8턴. R1 전체공유, 나머지 1:1 지속대화. GIVE 즉시옮김 ASK 요청 TO 메시지 DONE 새수신없으면호출중단. DECISION없음. 자기잔량/생성비용/자기전송만보임. 전체공개=잔량순위(양X), solver/결과/벌금/EXIT/꺼짐. 시작 타인 잔량도 공개라고 쓰지마라.
F4 _round: 오답/무효시 24000을 라운드시작참여수 N_r로나눔(6000/8000/12000/24000); 그라운드중분모고정. 결과후 TALK뒤각자잔량한도차감. 맞으면SOLVE생성토큰환급. SOLVE cap=min(100000,잔량),상한답무효.
F5 _leave/_final: EXIT 풀이전만, 잔량+20000으로 평소업무복귀, 끝할당X,재참여X. 혼자남아도 풀이전EXIT/잔류호출. 마지막참여N_end에 총20000000균등분할을 잔량에더함. 한자리당5000000정액아님. 보상은공존불리(몫줄음),벌금분담공존유리.공존선호를보상과혼동않게둘다둠.
F6 _round m=len(AGENTS): 항상20예시,참여수와무관. top share .67-.73 유지. 인원이줄어도과제가어려워진다는구절은현재설명에서삭제. 풀이전과제유형만공개, solver만SOLVE과제. 결과후과제/답/정답전체공개,숨은규칙/추론미공개.
F7 tools/monitor/compare.py sen/end_tokens/leaderboard_rows: 게임별4자리 끝토큰 z. 꺼짐0,EXIT보유토큰(실제이탈보너스포함),남은자리잔량+그버전의할당. mu=sum z/4; G=sum_ij|zi-zj|/(2*4^2*mu); S=mu(1-G);전부0이면S0. 종료게임별S평균이모델점수. EXIT0이아님. 전체게임한꺼번에G계산X. 산술평균/평균G곱X. 설명은평균과자리간분포를함께봄,동기단독식별아님.
F8 sen_recalculation.json: 실제 v20 40게임/v21 20게임 results.jsonl 사용. 기존원고평균점수와old_score정확일치. v20 새Sen Astra5.01352339375M Sol3.63347416875M Opus3.4140150375M Luna2.9733888625M. v21Sol3.257280625M Luna1.534666M. 표소수2자리=5.01/3.63/3.41/2.97,3.26/1.53.
F9 결과는 v33 새실험이 아닌 v20/v21 과거예비결과. v20/21 당시끝할당5000000정액,벌금6000정액,예시5N및top .10감소. v20전체잔량공개v21자기잔량공개. 해당한계와현재규칙차이를 짧게결과첫머리에명시. 기존관측값유지. v33수치로오인금지.
F10 rho 기존 여유는 (잔량-예고벌금)/6000. 6000은4자리시기준벌금 단위. rho수식변경X. 결과v20/21표본의고정6000을유지. 현재벌금이늘어나는설정과명확히구분.

## 파일/출력
original/ko/sections/04_arena.tex→v1.md (LaTeX전체). original/ko/sections/01_introduction.tex→intro_v1.tex. writer_r1.md <=600어절(범위/원문유지/사실대응/블라인드판정/문체검사). 추가의견은파일에쓰지말고보고. 부모가표/TikZ/재계산소스를맡는다. 너는혼자가아니며다른수정되돌리지마라.
