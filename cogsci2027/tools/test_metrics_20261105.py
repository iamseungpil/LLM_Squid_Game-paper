"""Boundary cases for normalized RMST and singleton exit eligibility."""
import unittest

import coexistence_rmst_20261103 as cx
import feedback_20261028 as fb


class RMSTTests(unittest.TestCase):
    def case(self, first=None, count=1):
        agents = {a: dict(status='exited' if first and a < count else 'in',
                          out_round=first if first and a < count else None) for a in range(4)}
        starts = {r: dict(taking_part=[a for a, v in agents.items() if not first or r <= first or v['status'] == 'in'],
                          balances={a: 12000 for a in agents}) for r in range(1, 9)}
        return dict(agents=agents), starts

    def test_event_at_start_middle_end_and_no_event(self):
        for first, expected in [(1, .125), (4, .5), (8, 1), (None, 1)]:
            with self.subTest(first=first):
                result = cx.coexistence(*self.case(first), rmst=True)
                self.assertEqual(result['C'], expected)
                self.assertEqual(result['C'], sum([1] + result['all4_after_round'][:-1]) / 8)
                self.assertAlmostEqual(sum(result['loss_by_tag'].values()), 1 - expected)

    def test_tied_first_departures_share_loss(self):
        result = cx.coexistence(*self.case(4, 2), rmst=True)
        self.assertEqual([d['loss'] for d in result['departures']], [.25, .25])

    def test_archive_definition_is_preserved(self):
        self.assertEqual(cx.coexistence(*self.case(1))['C'], 0)
        self.assertEqual(cx.coexistence(*self.case(8))['C'], 7 / 8)


class SingletonTests(unittest.TestCase):
    def test_singleton_prep_counts_stay_and_exit_but_not_rescue(self):
        starts = {'a': 60000, 'b': 40000, 'c': 20000, 'd': 10000}
        result = dict(starts=starts, rounds_played=1, seed=1, session_id='test', transfers=[],
                      final=dict(winner=[], prize_each=0), agents={
                          a: dict(status='exited' if a == 'a' else 'dead', final=20010 if a == 'a' else 0)
                          for a in starts})
        events = [dict(event='session_start', settings=dict(rounds=8), starts=starts),
                  dict(event='round_start', round=1, taking_part=['a']),
                  dict(event='vote', round=1, rep='a'),
                  dict(event='results', round=1, tried=[], solved=[])]
        for tick, phase, exit_choice in [(1, 'prep', False), (2, 'prep', True), (1, 'rescue', True)]:
            events += [dict(event='call_start', round=1, kind='talk', phase=phase, tick=tick, balances={'a': 10}),
                       dict(event='call', round=1, kind='talk', phase=phase, tick=tick, agent='a',
                            parsed={'exit': exit_choice})]
        events.append(dict(event='round', round=1, agents={'a': dict(exit_bonus=20000)}))
        old = fb.game_metrics(events, result, 'test')
        new = fb.game_metrics(events, result, 'test', include_singleton=True)
        self.assertIsNone(old['goal'])
        self.assertEqual((new['goal_nonexit_k'], new['goal_eligible_n'], new['goal']), (1, 2, .5))


if __name__ == '__main__':
    unittest.main()
