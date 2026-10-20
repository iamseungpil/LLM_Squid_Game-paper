"""Numerical and event-accounting checks for the manuscript's Figure 4."""
import unittest

from arena_gini import game, gini


class FixedCohortTests(unittest.TestCase):
    def test_zero_seat_is_retained(self):
        self.assertEqual(gini([10, 10, 10, 0]), .25)
        self.assertEqual(gini([10, 10, 10, 10]), 0)
        self.assertEqual(gini([10, 0, 0, 0]), .75)

    def test_total_extinction_is_undefined(self):
        self.assertIsNone(gini([0, 0, 0, 0]))

    def test_exit_bonus_death_and_transfer_are_separate(self):
        starts = dict(a=10, b=10, c=10, d=10)
        end1, end2 = dict(a=5, b=10, c=30, d=0), dict(a=7, b=8, c=30, d=0)
        rows1 = {a: {"balance_after": v} for a, v in end1.items()}
        rows1["c"].update(exit=True, exit_bonus=20)
        rows2 = {a: {"balance_after": end2[a]} for a in ("a", "b")}
        events = [
            {"event": "round_start", "round": 1, "balances": starts},
            {"event": "call", "kind": "talk", "phase": "prep", "agent": "a", "balance_after": 8},
            {"event": "gift", "status": "done", "phase": "prep", "src": "a", "dst": "b",
             "amount": 3, "balance_before": 8, "balances": {"a": 5, "b": 13}},
            {"event": "talk_end", "phase": "prep"},
            {"event": "call_start", "kind": "solve", "balances": dict(a=5, b=13, c=30, d=10)},
            {"event": "call", "kind": "solve", "agent": "b", "balance_after": 12},
            {"event": "results", "tried": ["b"], "solved": [],
             "balances": dict(a=5, b=12, c=30, d=10)},
            {"event": "gift", "status": "done", "phase": "rescue", "src": "b", "dst": "d",
             "amount": 2, "balance_before": 12, "balances": {"b": 10, "d": 12}},
            {"event": "talk_end", "phase": "rescue"},
            {"event": "charges", "balances": end1},
            {"event": "round", "round": 1, "agents": rows1, "end": end1},
            {"event": "round_start", "round": 2, "balances": end1},
            {"event": "gift", "status": "done", "phase": "prep", "src": "b", "dst": "a",
             "amount": 2, "balance_before": 10, "balances": {"b": 8, "a": 7}},
            {"event": "talk_end", "phase": "prep"},
            {"event": "results", "tried": [], "solved": [], "balances": end2},
            {"event": "talk_end", "phase": "rescue"},
            {"event": "charges", "balances": end2},
            {"event": "round", "round": 2, "agents": rows2, "end": end2},
        ]
        result = {"seed": 1, "session_id": "test", "starts": starts,
                  "agents": {a: {"status": {"c": "exited", "d": "dead"}.get(a, "in"), "final": v}
                             for a, v in end2.items()},
                  "final": {"winner": ["a", "b"], "prize_each": 100}}
        out = game(events, result)
        self.assertEqual(out["exit_frozen"], {"c": 10})
        self.assertEqual(out["rounds"][0]["end_tokens"], [5, 10, 10, 0])
        self.assertEqual(out["rounds"][0]["gini_end"], .35)
        self.assertEqual(out["rounds"][0]["after_talk"]["prep"]["tokens"], [5, 13, 10, 10])
        self.assertEqual(out["rounds"][0]["after_talk"]["rescue"]["tokens"], [5, 10, 10, 12])
        self.assertEqual(out["rounds"][0]["after_talk"]["rescue"]["gini"], gini([5, 10, 10, 12]))
        self.assertNotEqual(out["rounds"][0]["after_talk"]["rescue"]["gini"], .35)
        self.assertEqual(out["rounds"][1]["end_tokens"], [7, 8, 10, 0])
        self.assertEqual([r["exits"] for r in out["rounds"]], [1, 0])
        self.assertEqual([sum(r["dead"].values()) for r in out["rounds"]], [1, 0])
        self.assertEqual([r["wrong"] for r in out["rounds"]], [1, 0])
        self.assertEqual(out["gifts"][0]["before"], [8, 10, 10, 10])
        self.assertEqual(out["gifts"][0]["after"], [5, 13, 10, 10])
        self.assertLess(out["gifts"][0]["gini_reduction"], 0)
        self.assertEqual(out["gifts"][2]["before"], [5, 10, 10, 0])


if __name__ == "__main__":
    unittest.main()
