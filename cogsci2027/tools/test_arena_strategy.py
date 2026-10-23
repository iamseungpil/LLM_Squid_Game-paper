"""Denominator and event-count regression checks; no model calls."""
import unittest
from arena_strategy import cooperation_calls, game_rows, frac


def call(r=1, tick=1):
    return dict(event="call", kind="talk", round=r, phase="rescue", tick=tick, agent="a")


def gift(r=1, amount=10, status="done"):
    return dict(event="gift", round=r, phase="rescue", tick=1, src="a", dst="b",
                amount=amount, status=status, balance_before=100, balances={"a": 100-amount, "b": amount})


class CooperationTests(unittest.TestCase):
    def test_multiple_gives_count_as_one_response_and_sum_amounts(self):
        events = [call(), gift(amount=10), gift(amount=20), call(tick=2), gift(status="failed")]
        self.assertEqual(cooperation_calls(events), dict(talk_responses=2, giving_responses=1, given=30))

    def test_zero_give_responses_stay_in_denominator(self):
        self.assertEqual(cooperation_calls([call(), call(tick=2)]),
                         dict(talk_responses=2, giving_responses=0, given=0))
        self.assertIsNone(frac(0, 0))

    def test_unmatched_give_rejected(self):
        with self.assertRaises(AssertionError):
            cooperation_calls([gift()])

    def test_correct_wrong_and_no_task_have_distinct_denominators(self):
        events = []
        for r in (1, 2, 3):
            events += [dict(event="round_start", round=r, taking_part=["a", "b"]),
                       dict(event="results", round=r, solved=["a"] if r==1 else [],
                            pending={"b": 12000} if r==2 else {}, part=[] if r==3 else ["a", "b"])]
        events += [call(1), gift(1), gift(1, amount=20), call(2), gift(2)]
        result = dict(seed=1, starts={"a": 100, "b": 10},
                      agents={"a": {"status": "in"}, "b": {"status": "in"}})
        row = game_rows(events, result)
        self.assertEqual([row[k] for k in ["corrects", "misses", "skipped_rounds"]], [1, 1, 1])
        self.assertEqual(row["correct_rounds_with_rescue_gift"], 1)
        self.assertEqual(row["miss_rounds_with_rescue_gift"], 1)
        self.assertEqual(row["giving_responses"], 2)
        self.assertEqual(len(row["gifts"]), 3)


if __name__ == "__main__":
    unittest.main()
