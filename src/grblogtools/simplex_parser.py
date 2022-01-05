import re

from grblogtools.helpers import typeconvert_groupdict


class SimplexParser:
    # The pattern indicating the initialization of the parser
    simplex_start_pattern = re.compile(
        r"Iteration(\s+)Objective(\s+)Primal Inf.(\s+)Dual Inf.(\s+)Time"
    )

    # The pattern indicating the simplex progress
    simplex_progress_pattern = re.compile(
        r"\s*(?P<Iteration>\d+)\s+(?P<Objective>[^\s]+)\s+(?P<PInf>[^\s]+)\s+(?P<DInf>[^\s]+)\s+(?P<Time>\d+)s"
    )

    # The pattern indicating the start or the termination of the simplex in case of
    # solving an MIP. In some cases, the simplex log might only include this one
    # line
    simplex_mip_relaxation_pattern = re.compile(
        r"Root relaxation: objective (?P<ContinuousObjective>[^,]+), (?P<ContinuousIteration>\d+) iterations, (?P<ContinuousTime>[^\s]+) seconds"
    )
    # The patterns indicating the termination of the simplex in case of solving an LP.
    # The LP refers to all continuous optimization problems. The first pattern
    # always exists but the second pattern might not exist
    simplex_lp_iteraion_time_termination_pattern = re.compile(
        r"(Solved|Stopped) in (?P<ContinuousIteration>[^\s]+) iterations and (?P<ContinuousTime>[^\s]+) seconds"
    )
    simplex_lp_obj_termination_pattern = re.compile(
        r"Optimal objective\s+(?P<ContinuousObjective>.*)$"
    )

    def __init__(self):
        """Initialize the Simplex parser."""
        self._summary = {
            "ContinuousObjective": None,
            "ContinuousIteration": None,
            "ContinuousTime": None,
        }
        self._progress = []

    def start_parsing(self, line: str) -> bool:
        """Return True if the parser should start parsing the future log lines.

        Args:
            line (str): A line in the log file.

        Returns:
            bool: Return True if the given line matches the parser start patterns.
        """
        if SimplexParser.simplex_start_pattern.match(line):
            return True

        mip_relaxation_match = SimplexParser.simplex_mip_relaxation_pattern.match(line)
        if mip_relaxation_match:
            self._summary.update(typeconvert_groupdict(mip_relaxation_match))
            return True

        return False

    def continue_parsing(self, line: str) -> bool:
        """Parse the given line.

        Args:
            line (str): A line in the log file.

        Returns:
            bool: Return True if the line matches the pattern indicating progress in
                the simplex method. Return True for the termination patterns except for
                the ones which certainly point to the full termination of the simplex
                method.
        """
        progress_match = SimplexParser.simplex_progress_pattern.match(line)
        if progress_match:
            self._progress.append(typeconvert_groupdict(progress_match))
            return True

        mip_relaxation_match = SimplexParser.simplex_mip_relaxation_pattern.match(line)
        if mip_relaxation_match:
            self._summary.update(typeconvert_groupdict(mip_relaxation_match))
            return False

        lp_iteration_time_termination_match = (
            SimplexParser.simplex_lp_iteraion_time_termination_pattern.match(line)
        )
        if lp_iteration_time_termination_match:
            parsed_dict = typeconvert_groupdict(lp_iteration_time_termination_match)
            self._summary["ContinuousIteration"] = parsed_dict["ContinuousIteration"]
            self._summary["ContinuousTime"] = parsed_dict["ContinuousTime"]
            return True

        lp_obj_termination_match = (
            SimplexParser.simplex_lp_obj_termination_pattern.match(line)
        )
        if lp_obj_termination_match:
            parsed_dict = typeconvert_groupdict(lp_obj_termination_match)
            self._summary["ContinuousObjective"] = parsed_dict["ContinuousObjective"]
            return False

        return False

    def get_summary(self) -> dict:
        """Return the current parsed summary.

        It returns an empty dictionary if the parser is not initialized yet.
        """
        return self._summary

    def get_progress(self) -> dict:
        """Return the detailed progress in simplex method.

        It returns an empty list if the parser is not initialized yet or there is
        no progress to report.
        """
        return self._progress
