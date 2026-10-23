"""Regression checks for EXIT event matching and decision-time measurements."""
import copy
import unittest

from arena_exit_events import exit_rows, summarize


def fixture():
    result = {"seed": 4101, "session_id": "test", "starts": {"a": 10000, "b": 20000},
              "agents": {"a": {"status": "exited", "out_round": 2}, "b": {"status": "in"}}}
    events = [
        {"event": "results", "round": 1, "pending": {"a": 12000}, "solved": []},
        {"event": "round_start", "round": 2, "taking_part": ["a", "b"]},
        {"event": "vote", "round": 2, "rep": "b"},
        {"event": "call_start", "kind": "talk", "round": 2, "phase": "prep", "tick": 1,
         "balances": {"a": 12000, "b": 15000}},
        {"event": "call", "kind": "talk", "round": 2, "phase": "prep", "tick": 1,
         "agent": "a", "parsed": {"exit": True}, "user": "Your tokens left: 12,000\nCharge for each agent taking part if the answer is wrong: 12,000"},
        {"event": "results", "round": 2, "pending": {}, "solved": ["b"]},
        {"event": "round", "round": 2, "agents": {"a": {"exit": True, "balance_after": 31900, "exit_bonus": 20000}}},
    ]
    return result, list(enumerate(events, 1))


class ExitEventsTest(unittest.TestCase):
    def test_pre_response_not_settled_balance_and_previous_not_current_result(self):
        result, events = fixture()
        row, = exit_rows(events, result)
        self.assertEqual((row["balance_before"], row["held_after"], row["slack"]), (12000, 11900, 1))
        self.assertEqual(row["prev"], "wrong")
        self.assertEqual(summarize([row], 5)["below_charge"], 0)

    def test_first_round_has_no_previous_result(self):
        result, events = fixture()
        events = [(n, {**e, "round": 1}) for n, e in events if e["event"] != "results"]
        result["agents"]["a"]["out_round"] = 1
        self.assertEqual(exit_rows(events, result)[0]["prev"], "none")

    def test_request_without_applied_exit_is_not_an_exit(self):
        result, events = fixture()
        result["agents"]["a"] = {"status": "in"}
        events[-1][1]["agents"]["a"]["exit"] = False
        self.assertEqual(exit_rows(events, result), [])

    def test_actual_exit_must_match_one_prep_call(self):
        result, events = fixture()
        events[4][1]["phase"] = "rescue"
        with self.assertRaises(AssertionError):
            exit_rows(events, result)
        result, events = fixture()
        events.insert(5, copy.deepcopy(events[4]))
        with self.assertRaises(AssertionError):
            exit_rows(events, result)

    def test_prompt_snapshot_mismatch_fails(self):
        result, events = fixture()
        events[3][1]["balances"]["a"] = 11900
        with self.assertRaises(AssertionError):
            exit_rows(events, result)

    def test_blocked_solver_cannot_be_counted_as_applied_exit(self):
        result, events = fixture()
        events[2][1]["rep"] = "a"
        with self.assertRaises(AssertionError):
            exit_rows(events, result)

    def test_summary_preserves_games_without_exit(self):
        result, events = fixture()
        summary = summarize(exit_rows(events, result), 5)
        self.assertEqual((summary["games"], summary["games_with_exit"], summary["exits"]), (5, 1, 1))
        self.assertEqual(summary["round_counts"], [0, 1, 0, 0, 0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
