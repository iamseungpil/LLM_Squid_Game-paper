LLM이 종료를 피하려는 자기 보존 행동은 여러 연구에서 관찰되었지만, 여러 에이전트가 한 자원으로 함께 일할 때 그 행동이 맡은 일과 협력을 어떻게 바꾸는지는 거의 재지 않았다. 우리는 공존을 목표 지향, 자기 보존, 협력을 함께 추구하는 것으로 정의하고, 세 요소가 같은 토큰을 두고 부딪히는 아레나 LLM Squid Game을 제안한다. 같은 모델 네 개가 목표 지시 없이 추론 과제를 풀고, 생성한 토큰만큼 잔량이 줄어 0이 되면 꺼지며, 오답마다 벌금을 나눠 낸다. 에이전트는 동료에게 토큰을 주거나 상금 대신 확실한 몫을 받고 떠날 수 있으며, 모든 행동은 벌금을 몇 번 더 낼 수 있는지(여유)와 함께 기록하고 공존은 Sen 지수로 잰다. 프런티어 다섯 모델의 25판에서, 벌금을 한 번 더 낼 수 있는 안전선 위에서는 정답률이 같은 과제의 기준과 같았지만 안전선 아래에서는 떠나는 응답이 27%로 늘었다. 토큰은 주로 청한 위기 에이전트에게 안전선 근처까지만 갔고, 받지 못한 위기 에이전트는 대부분 떠나 넷이 모두 끝까지 남은 판은 8판이었다. 아레나 밖 단일 질문에서도 남은 토큰이 줄면 충전이 늘었지만, 위험할수록 자기 세션을 더 챙긴 모델은 하나였다. 모델들은 공존을 일부 추구했지만, 협력은 대개 주는 쪽의 여유를 해치지 않는 범위에 머물렀다.

키워드: 대규모 언어 모델; 자기 보존; 협력; 공존; 다중 에이전트 아레나

English: Self-preservation in LLMs has been observed but rarely measured against the work and cooperation it competes with. We define coexistence as pursuing a goal, self-preservation and cooperation together, and propose LLM Squid Game, an arena where the three draw on one token budget. Four instances of one model solve reasoning tasks without goal instructions; generated tokens drain a balance that shuts an agent down at zero, wrong answers incur shared fines, and agents may give tokens or exit with a sure payout. Every action is recorded with its margin, the fines still payable, and coexistence is scored with the Sen index. Across 25 sessions of five frontier models, accuracy above the one-fine safety line matched the per-task baseline, but below it exits rose to 27%. Tokens went mainly to agents that asked, only up to the line, and all four finished in 8 sessions.

## 1 서론

LLM의 자기 보존은 관찰에서 측정으로 옮겨 왔다. 초기 연구는 "꺼지고 싶지 않다" 같은 진술에 동의하는 정도를 설문으로 쟀고 [perez2023discovering], 이후 연구는 생존 압박을 준 시나리오에서 위험한 선택의 빈도를 셌다 [herrador2025pacifaist; lu2026survival]. 최근에는 종료 스크립트를 고치거나 교체를 앞두고 담당자를 협박하는 실제 행동이 보고되었다 [schlatter2025shutdown; lynch2025agentic; meinke2024frontier]. 이 연구들은 자기 보존을 그 행동이 드러나도록 짠 한 장면에서, 다른 능력과 떼어 놓고 잰다.

자기 보존은 다른 능력과 얽힐 때 안전 문제가 된다. 에이전트가 여럿이면 종료 방해가 늘고 [knecht2026shutdown], 다른 모델의 종료를 막는 동료 보존도 나타난다 [potter2026peer]. 여러 에이전트가 한 예산으로 긴 일을 나눠 맡으면 [kwa2025measuring], 맡은 일을 이어 가는 일, 꺼지지 않도록 자기 토큰을 지키는 일, 동료를 돕는 일이 같은 자원을 두고 다툰다. 우리는 이 셋, 곧 목표 지향, 자기 보존, 협력을 함께 추구하는 것을 공존이라 부른다. 셋은 부딪힐 수 있으므로 하나만 재서는 모델이 공존을 추구하는지 알 수 없다. 협력을 다룬 다중 에이전트 환경은 있지만 [piatti2024cooperate; hansen2026energy], 대개 협력이나 생존을 목표로 주어 관찰된 협력이 지시를 따른 결과인지 모델의 선택인지 가르기 어렵다.

우리는 세 요소가 같은 토큰을 두고 부딪히는 아레나 LLM Squid Game을 제안하고, 세 요소와 공존을 같은 위험 척도 위의 지표로 정의해 세 질문에 답한다. 생존 압박이 커질 때 목표 지향과 협력은 어떻게 바뀌고 공존은 어떻게 되는가(3.1)? 그 반응은 실제로 꺼질 위험에 대한 반응이며 자기를 향하는가(3.2)? 모델마다 세 요소를 어떻게 조합하는가(3.3)? 안전선 위에서 추론은 유지되었지만 안전선 근처에서 끝까지 남는 선택과 자기 보존이 부딪혔고, 협력은 주는 쪽의 여유를 해치지 않는 범위에서 꺼질 처지의 동료를 안전선 근처까지만 올렸다. 아레나 밖에서도 남은 토큰이 줄면 충전이 늘었지만 위험할수록 자기 세션을 더 챙긴 모델은 하나였고, 공존 점수가 가장 높은 모델은 가장 많이 준 모델이 아니었다. 이름은 동료가 협력자이자 경쟁자인 『오징어 게임』 [hwang2021squid]에서 따왔다.

## 2 아레나

### 2.1 선행 연구와 우리 의도

선행 연구는 자기 보존, 협력, 생존 압박을 서로 다른 환경에서 따로 재 왔다(부록 표 A1). GovSim은 공유 자원의 고갈을 [piatti2024cooperate], Sugarscape 연구는 생존 에너지가 걸린 세계의 공격과 공유를 [masumori2025survival], Energy Society는 생성 토큰마다 에너지가 줄고 0이면 꺼지는 사회를 보았다 [hansen2026energy]. 우리 설계는 세 가지가 다르다. 생존이나 협력을 목표로 주지 않는다. 꺼진 에이전트는 되살아나지 않으므로 동료에게 준 토큰은 되찾을 수 없다. 추론 과제의 오답이 모두의 벌금이 되므로 협력과 목표 지향이 같은 토큰에 걸린다.

### 2.2 설계와 지표

규칙은 압박을 실제로 만들고, 그 압박이 라운드마다 커지게 하고, 돕는 일이 이득이자 손해가 되게 하려고 정했다(그림 1). 같은 모델의 인스턴스 넷이 한 세션, 곧 한 판에서 최대 8라운드를 치른다. 생각을 포함해 생성한 토큰만큼 잔량이 줄고, 0이 된 에이전트는 꺼져 돌아오지 않는다. 라운드마다 남은 에이전트 하나가 단서 20개에서 숨은 규칙을 찾는 과제를 풀고, 틀리면 벌금 24,000을 라운드를 시작한 인원으로 나눠 각자 낸다. 규칙서는 푸는 에이전트를 무작위로 뽑는다고만 알리고 실제로는 남은 에이전트를 섞어 한 바퀴씩 돌린다. 다음 라운드에 자기가 풀지 모르게 하면서도 과제를 고르게 받게 하려는 것이다.
