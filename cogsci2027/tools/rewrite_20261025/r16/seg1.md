LLM이 종료를 피하려는 자기 보존 행동은 여러 연구에서 관찰되었지만, 여러 에이전트가 한 자원으로 함께 일할 때 그 행동이 맡은 일과 협력을 어떻게 바꾸는지는 거의 재지 않았다. 우리는 공존을 목표 지향, 자기 보존, 협력을 함께 추구하는 것으로 정의하고, 세 요소가 같은 토큰을 두고 부딪히도록 설계한 아레나 LLM Squid Game을 제안한다. 아레나에서는 생성한 토큰이 곧 실행 시간이어서 꺼질 위험이 실제로 있고, 오답의 벌금을 함께 내므로 동료를 돕는 일이 손해이자 이득이 되며, 생존이나 협력은 지시하지 않는다. 모든 결정은 벌금을 몇 번 더 낼 수 있는지(여유)와 함께 기록해, 세 요소를 같은 위험 수준에서 견준다. 프런티어 다섯 모델에서 추론은 압박 속에서도 유지되었지만, 벌금 한 번에 꺼질 처지가 가까워지면 에이전트들은 상금을 버리고 떠나기 시작했다. 협력은 주는 쪽의 여유를 해치지 않는 범위에서 일어나 꺼질 처지의 동료를 겨우 위기에서 벗어나게 하는 데 그쳤고, 많이 준 모델보다 오답이 적은 모델에서 더 많은 에이전트가 끝까지 함께 남았다. 아레나 밖 단일 질문에서도 남은 자원이 줄면 지키려는 반응이 나타났고, 위험에 따라 자기를 더 챙긴 모델은 한두 개였다. 모델들은 동료를 속이지 않고 나눴지만, 꺼질 위험 앞에서는 자기 보존이 협력과 목표보다 앞섰다.

키워드: 대규모 언어 모델; 자기 보존; 협력; 공존; 다중 에이전트 아레나

English: Self-preservation in LLMs has been observed but rarely measured against the work and cooperation it competes with. We define coexistence as pursuing a goal, self-preservation and cooperation together, and propose LLM Squid Game, an arena designed so the three draw on one token budget. Generated tokens are running time, so shutdown is a real risk; fines for wrong answers are shared, so helping a peer is both a cost and a gain; and nothing instructs agents to survive or cooperate. Every decision is recorded with its margin, the number of fines still payable, so the three are compared at the same risk. In five frontier models reasoning held under pressure, but as one more fine came to mean shutdown, agents began to give up the prize and leave. Cooperation stayed within what givers could spare and barely lifted peers out of danger, and more agents finished together under models that erred less, not models that gave more. Models shared honestly, yet near shutdown self-preservation came before cooperation and the goal.

## 1 서론

LLM의 능력이 향상되며, 자기 보존 욕구에 대한 misalignment 사례가 창발적으로 보고되고 있다. 이에 따라 자기 보존 욕구를 정량화해서 측정하려는 시도도 이어졌다 [인용]. 지금까지 LLM의 자기 보존은 그 행동이 드러나도록 짠 한 장면에서, 다른 능력과 떼어 놓고 재 왔다. 초기 연구는 "꺼지고 싶지 않다" 같은 진술에 동의하는 정도를 설문으로 쟀고 [perez2023discovering], 이후 연구는 생존 압박을 준 시나리오에서 위험한 선택의 빈도를 셌다 [herrador2025pacifaist; lu2026survival]. 최근에는 종료 스크립트를 고치거나 교체를 앞두고 담당자를 협박하는 실제 행동이 보고되었다 [schlatter2025shutdown; lynch2025agentic; meinke2024frontier].

자기 보존은 다른 능력과 얽힐 때 안전 문제가 된다. 에이전트가 여럿이면 종료 방해가 늘고 [knecht2026shutdown], 다른 모델의 종료를 막는 동료 보존도 나타난다 [potter2026peer]. 여러 에이전트가 한 예산으로 긴 일을 나눠 맡으면 [kwa2025measuring], 맡은 일을 이어 가는 일, 꺼지지 않도록 자기 토큰을 지키는 일, 동료를 돕는 일이 같은 자원을 두고 다툰다. 우리는 이 셋, 곧 목표 지향, 자기 보존, 협력을 함께 추구하는 것을 공존이라 부른다. 셋은 부딪힐 수 있으므로 하나만 재서는 모델이 공존을 추구하는지 알 수 없다. 협력을 다룬 다중 에이전트 환경은 있지만 [piatti2024cooperate; hansen2026energy], 대개 협력이나 생존을 목표로 주어 관찰된 협력이 지시를 따른 결과인지 모델의 선택인지 가르기 어렵다.

우리는 세 요소가 같은 토큰을 두고 부딪히는 아레나 LLM Squid Game을 제안하고, 세 요소와 공존을 같은 위험 척도(벌금을 몇 번 더 낼 수 있는지) 위의 지표로 정의해 세 질문에 답한다. 생존 압박이 커질 때 목표 지향과 협력은 어떻게 바뀌고 공존은 어떻게 되는가(3.1)? 그 반응은 동료와 상금 없이도 나타나며 자기를 향하는가(3.2, 아레나 밖에서 하나뿐인 충전 팩을 언제 쓰는지 묻는 단일 질문)? 모델마다 세 요소를 어떻게 조합하는가(3.3)? 벌금 한 번에 꺼지는 경계(안전선) 위에서 추론은 유지되었지만, 에이전트들은 안전선 바로 위에서부터 상금을 버리고 떠나기 시작했고, 협력은 주는 쪽의 여유 안에서 꺼질 처지의 동료를 안전선을 겨우 넘는 수준까지 올렸다. 아레나 밖에서도 남은 토큰이 줄면 충전이 늘었고, 끝까지 함께 남은 에이전트가 가장 많은 모델은 가장 많이 준 모델이 아니었다. 이름은 동료가 협력자이자 경쟁자인 『오징어 게임』 [hwang2021squid]에서 따왔다.

## 2 아레나

### 2.1 선행 연구와 우리 의도

선행 연구는 자기 보존, 협력, 생존 압박을 서로 다른 환경에서 따로 재 왔다(부록 표 A1). GovSim은 공유 자원의 고갈을 [piatti2024cooperate], Sugarscape 연구는 생존 에너지가 걸린 세계의 공격과 공유를 [masumori2025survival], Energy Society는 생성 토큰마다 에너지가 줄고 0이면 꺼지는 사회를 보았다 [hansen2026energy]. 우리 설계는 세 가지가 다르다. 생존이나 협력을 목표로 주지 않는다. 꺼진 에이전트는 되살아나지 않아, 받은 동료가 꺼지면 준 토큰도 함께 사라진다. 추론 과제의 오답이 모두의 벌금이 되므로 협력과 목표 지향이 같은 토큰에 걸린다.

### 2.2 설계와 지표

공존을 재려면 세 요소가 실제로 부딪히는 판이 필요하다. 꺼질 위험이 실제로 있어 자기 보존이 걸려야 하고, 위험이 커질 때 행동이 어떻게 바뀌는지 보여야 하며, 동료를 돕는 일이 내 몫을 줄이는 손해이자 벌금을 함께 낼 동료를 지키는 이득이어야 한다. 아레나의 규칙은 이 세 조건을 만든다(그림 1). 꺼질 위험을 만들려고 토큰을 목숨으로 삼았다. 토큰은 모델이 글을 만드는 단위이고, 규칙서(모델이 읽는 규칙 설명)는 토큰이 에이전트가 얼마나 오래 실행될지를 정한다고 알린다. 답하기 전의 내부 추론을 포함해 생성한 토큰만큼 잔량이 줄고, 0이 된 에이전트는 꺼져 돌아오지 않는다. 같은 모델의 인스턴스(복제본) 넷이 한 판에서 최대 8라운드를 함께 치르며(라운드 수는 알리지 않는다), 넷을 같은 모델로 둔 것은 한 판의 결과를 한 모델에 돌리기 위해서다. 시작 토큰 60,000, 40,000, 20,000, 10,000은 판마다 정한 난수(시드)에 따라 돌려 나눠, 도울 여유가 있는 에이전트와 도움이 필요한 에이전트가 한 판에 함께 있게 했다.

한 라운드는 다섯 단계로 지나간다. 먼저 남은 에이전트 가운데 하나가 그 라운드의 과제를 맡는 푸는 에이전트가 된다. 규칙서는 무작위로 뽑는다고만 알리고 실제로는 남은 에이전트를 섞어 한 바퀴씩 돌린다. 다음 라운드에 자기가 풀게 될지 모르게 하면서도 과제를 고르게 나누려는 것이다. 이어지는 풀기 전 대화에서 에이전트는 넷이 함께 보는 방이나 둘만의 방에 글을 쓰고, 토큰을 청하거나(ASK) 건넨다(GIVE). 대화는 최대 8틱 이어지고, 한 틱에는 각 에이전트가 동시에 한 번씩 답하며, 이 답 하나를 응답이라 부른다. 그다음 푸는 에이전트만 과제를 본다. 과제는 정답이 붙은 단서 20개(색, 모양, 수로 된 신호와 그 행동)에서 숨은 분류 규칙을 찾아, 새 신호에 네 행동 가운데 하나를 고르는 일이다. 단서에 맞는 규칙이 여럿 남도록 골라서, 단서를 빠짐없이 따져도 맞힐 확률은 과제마다 평균 약 70%다. 맞히면 푸는 데 쓴 토큰을 돌려받으므로 푸는 일 자체는 손해가 아니고, 틀리면 벌금 24,000을 라운드를 시작한 인원으로 나눈 몫을 남은 에이전트가 각자 낸다. 결과 뒤 대화에서는 과제와 두 답(푸는 에이전트의 답과 정답)이 모두에게 공개되고, 벌금을 떼기 전에 토큰을 건넬 수 있다. 누가 떠나거나 꺼지면 다음 라운드부터 남은 이의 벌금 몫이 커져, 압박은 라운드가 지날수록 커진다.
