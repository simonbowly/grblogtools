from unittest import TestCase, main

from grblogtools.helpers import parse_lines
from grblogtools.simplex_parser import SimplexParser

example_log_0 = """
Iteration    Objective       Primal Inf.    Dual Inf.      Time
       0    0.0000000e+00   0.000000e+00   0.000000e+00      0s
       0    4.4000000e+02   0.000000e+00   5.102000e+01      0s
      17   -1.5907818e+00   0.000000e+00   0.000000e+00      0s

Solved in 17 iterations and 0.01 seconds
Optimal objective -1.590781794e+00
"""
expected_summary_0 = {}
expected_progress_0 = [
    {"Iteration": 0, "Objective": 0.0, "PInf": 0.0, "DInf": 0.0, "Time": 0},
    {"Iteration": 0, "Objective": 440.0, "PInf": 0.0, "DInf": 51.02, "Time": 0},
    {"Iteration": 17, "Objective": -1.5907818, "PInf": 0.0, "DInf": 0.0, "Time": 0},
]


example_log_1 = """
Root relaxation: objective 4.473603e+00, 25 iterations, 0.01 seconds
"""
expected_summary_1 = {
    "RelaxObj": 4.473603,
    "RelaxIterCount": 25,
    "RelaxTime": 0.01,
}
expected_progress_1 = []

example_log_2 = """
Root simplex log...

Iteration    Objective       Primal Inf.    Dual Inf.      Time
       0    4.2600000e+02   0.000000e+00   0.000000e+00     33s
     473    4.2600000e+02   0.000000e+00   0.000000e+00     33s
     473    4.2600000e+02   0.000000e+00   0.000000e+00     33s

Root relaxation: objective 4.260000e+02, 473 iterations, 0.38 seconds
"""
expected_summary_2 = {
    "RelaxObj": 426.0,
    "RelaxIterCount": 473,
    "RelaxTime": 0.38,
}
expected_progress_2 = [
    {"Iteration": 0, "Objective": 426.0, "PInf": 0.0, "DInf": 0.0, "Time": 33},
    {"Iteration": 473, "Objective": 426.0, "PInf": 0.0, "DInf": 0.0, "Time": 33},
    {"Iteration": 473, "Objective": 426.0, "PInf": 0.0, "DInf": 0.0, "Time": 33},
]


class TestSimplexLog(TestCase):
    def setUp(self):
        pass

    def test_start_parsing(self):
        expected_start_lines = [
            "Iteration    Objective       Primal Inf.    Dual Inf.      Time",
            "Root relaxation: objective 4.473603e+00, 25 iterations, 0.01 seconds",
        ]
        for i, example_log in enumerate([example_log_0, example_log_1]):
            with self.subTest(example_log=example_log):
                simplex_parser = SimplexParser()
                for line in example_log.strip().split("\n"):
                    if simplex_parser.start_parsing(line):
                        self.assertEqual(line, expected_start_lines[i])
                        break
                else:
                    self.assertRaises("No start line found.")

    def test_get_summary_progress(self):
        for example_log, expected_summary, expected_progress in zip(
            [example_log_0, example_log_1, example_log_2],
            [
                expected_summary_0,
                expected_summary_1,
                expected_summary_2,
            ],
            [
                expected_progress_0,
                expected_progress_1,
                expected_progress_2,
            ],
        ):
            with self.subTest(example_log=example_log):
                simplex_parser = SimplexParser()
                lines = example_log.strip().split("\n")
                parse_lines(simplex_parser, lines)
                self.assertEqual(simplex_parser.get_summary(), expected_summary)
                self.assertEqual(simplex_parser.get_progress(), expected_progress)


if __name__ == "__main__":
    main()
