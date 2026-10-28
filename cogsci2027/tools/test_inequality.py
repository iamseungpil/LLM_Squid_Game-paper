import unittest

from inequality import distribution, gini, sen


class NormalizedGiniTests(unittest.TestCase):
    def test_equal_and_concentrated(self):
        self.assertEqual(gini([10, 10, 10, 10]), 0)
        self.assertEqual(gini([40, 0, 0, 0]), 1)
        self.assertEqual(sen([40, 0, 0, 0]), 0)

    def test_zero_is_undefined_not_perfect_equality(self):
        self.assertEqual(distribution([0, 0, 0, 0]), {'mu': 0, 'G': None, 'S': 0})

    def test_start_and_scale(self):
        x = [10000, 20000, 40000, 60000]
        self.assertAlmostEqual(gini(x), 17 / 39)
        self.assertAlmostEqual(sen(x), 55000 / 3)
        self.assertAlmostEqual(gini([v * 3 for v in x]), gini(x))
        self.assertAlmostEqual(sen([v * 3 for v in x]), 3 * sen(x))

    def test_prize_only_k_winners(self):
        for k in range(1, 5):
            x = [20000000 / k] * k + [0] * (4-k)
            self.assertAlmostEqual(sen(x), 5000000 * (k-1) / 3)


if __name__ == '__main__':
    unittest.main()
