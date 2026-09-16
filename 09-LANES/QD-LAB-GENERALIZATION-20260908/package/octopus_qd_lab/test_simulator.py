import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import numpy as np
from environment import (GENOME_DIM, unpack, evaluate, quality, segment_blocked, _blocked,
                         _raycast, START, START_THETA)
from map_elites import Archive, Config, run, uniform_crossover, gaussian_mutation


class SimulatorTests(unittest.TestCase):
    def test_genome_shape(self):
        layers = unpack(np.arange(74))
        self.assertEqual([a.shape for a in layers], [(1, 6, 8), (1, 1, 8), (1, 8, 2), (1, 1, 2)])
        np.testing.assert_array_equal(np.concatenate([a.ravel() for a in layers]), np.arange(74))
        for g in (np.zeros(73), np.full(74, np.nan)):
            with self.assertRaises(ValueError):
                unpack(g)

    def test_idle_cannot_win(self):
        self.assertEqual(float(quality(0, 0, 0)), 0)
        self.assertEqual(float(quality(.5, 0, 0)), 1)
        g = np.zeros(74)
        g[-2] = -40
        fitness, _, _ = evaluate(g)
        self.assertLess(fitness[0], 1e-12)

    def test_swept_collision(self):
        # Crosses the first wall, a pillar, or passes unobstructed.
        a = np.array([[.5, .29], [.2, .15], [.9, .1]])
        b = np.array([[.5, .35], [.4, .15], [.9, .2]])
        np.testing.assert_array_equal(segment_blocked(a, b), [True, True, False])

    def test_raycast_and_episode(self):
        sensors = _raycast(START[None, :], np.array([START_THETA]))
        self.assertTrue(np.isfinite(sensors).all())
        self.assertTrue(((sensors >= 0) & (sensors <= 1)).all())
        # The central forward ray hits first wall at y=.30.
        self.assertAlmostEqual(sensors[0, 2], .24 / .30)
        g = np.random.default_rng(8).normal(size=(12, GENOME_DIM))
        f, bd, info = evaluate(g, True)
        f2, bd2, _ = evaluate(g)
        np.testing.assert_array_equal(f, f2)
        np.testing.assert_array_equal(bd, bd2)
        self.assertFalse(_blocked(info["traj"].reshape(-1, 2)).any())
        for t in range(1, len(info["traj"])):
            self.assertFalse(segment_blocked(info["traj"][t-1], info["traj"][t]).any())
        self.assertTrue(((f >= 0) & (f <= 1)).all())

    def test_archive_replacement_and_timestamps(self):
        a = Archive(8)
        info = {k: np.zeros(3) for k in a.meta}
        a.add_batch(np.zeros((3, 74)), [.4, .3, .7], np.tile([.2, .2], (3, 1)),
                    2, np.arange(3), np.full((3, 2), -1), ["mut"]*3, info)
        i, j = a.cell([.2, .2])
        self.assertEqual(a.fitness[i, j], .7)
        self.assertEqual(a.ids[i, j], 2)
        a.add_batch(np.zeros((1, 74)), [.8], [[.2, .2]], 9, [3], [[1, 2]], ["line"],
                    {k: [0] for k in a.meta})
        self.assertEqual(a.first_generation[i, j], 2)
        self.assertEqual(a.last_generation[i, j], 9)
        self.assertEqual(a.cell([1., 1.]), (7, 7))
        with self.assertRaises(ValueError):
            a.cell([np.nan, 0])

    def test_operators(self):
        rng = np.random.default_rng(6)
        z, o = np.zeros(74), np.ones(74)
        child = uniform_crossover(z, o, rng)
        self.assertTrue(np.isin(child, [0, 1]).all())
        self.assertGreater(child.sum(), 0)
        self.assertLess(child.sum(), 74)
        np.testing.assert_array_equal(gaussian_mutation(o, rng, rate=0), o)

    def test_repeatability_budget_monotonicity_and_npz(self):
        config = Config(grid=16, initial=24, batch=12, generations=3)
        a, h, s = run(7, config, verbose=False)
        b, h2, s2 = run(7, config, verbose=False)
        self.assertEqual(h, h2)
        self.assertEqual(s, s2)
        np.testing.assert_array_equal(a.genomes, b.genomes)
        self.assertEqual(h[-1]["evals"], 60)
        self.assertEqual(h[0]["gen"], 0)
        self.assertGreater(h[1]["reused_parent_ids"], 0)
        for metric in ("coverage", "qd_score", "n_elites"):
            self.assertTrue(np.all(np.diff([r[metric] for r in h]) >= -1e-12))
        self.assertTrue(all(0 <= r["center_free_coverage"] <= 1 for r in h))
        for mode in ("random", "mutation", "crossover"):
            _, hh, _ = run(7, config, mode, verbose=False)
            self.assertEqual(hh[-1]["evals"], h[-1]["evals"])
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.npz"
            a.save(p)
            aa = Archive.load(p)
            np.testing.assert_array_equal(a.genomes, aa.genomes)
            np.testing.assert_array_equal(a.first_generation, aa.first_generation)


if __name__ == "__main__":
    unittest.main()
