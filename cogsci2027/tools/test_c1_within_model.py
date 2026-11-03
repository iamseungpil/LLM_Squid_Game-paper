"""Checks for c1_within_model: the FE estimator on known data, exact permutation, and the manuscript cohort numbers."""
import os
import unittest

import numpy as np

import c1_within_model as c1


class EstimatorTests(unittest.TestCase):
    def test_fe_recovers_within_model_shift(self):
        groups = np.array(['a'] * 4 + ['b'] * 4)
        d = np.array([1, 1, 0, 0, 1, 0, 0, 0])
        y = np.where(groups == 'a', 100.0, -50.0) + 7.0 * d  # model levels differ, within shift = 7
        self.assertAlmostEqual(c1.fe_beta(y, d, groups), 7.0)

    def test_fe_undefined_without_within_variation(self):
        groups = np.array(['a', 'a', 'b', 'b'])
        self.assertIsNone(c1.fe_beta(np.array([1., 2., 3., 4.]), np.array([1, 1, 0, 0]), groups))

    def test_permutation_is_exact_and_counts_labelings(self):
        groups = np.array(['a'] * 5 + ['b'] * 5)
        d = np.array([1, 1, 0, 0, 0, 1, 0, 0, 0, 0])
        y = np.arange(10.0)
        r = c1.within_permutation(y, d, groups, np.random.default_rng(0))
        self.assertTrue(r['exact'])
        self.assertEqual(r['n_labelings'], 10 * 5)  # C(5,2) x C(5,1)


@unittest.skipUnless(os.path.isdir(os.path.expanduser('~/squid5-runs/e52_v33')), 'v33 runs not on this machine')
class ManuscriptCohortTests(unittest.TestCase):
    def test_pooled_contrast_matches_section_3(self):
        games = c1.load(c1.RUNS, list(range(4101, 4106)))
        self.assertEqual(len(games), 25)
        rng = np.random.default_rng(c1.RNG_SEED)
        expect = dict(given_per_agent_round=(754.3, 447.1, 1), accuracy=(.781, .641, 3), rho=(3.06, 4.51, 2))
        for metric, (all4, rest, places) in expect.items():
            p = c1.analyse(games, metric, rng)['pooled']
            self.assertEqual(round(p['all4'], places), all4, metric)
            self.assertEqual(round(p['rest'], places), rest, metric)


if __name__ == '__main__':
    unittest.main()
