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
        r"Root relaxation: objective (?P<RelaxObj>[^,]+), (?P<RelaxIterCount>\d+) iterations, (?P<RelaxTime>[^\s]+) seconds"
    )

    def __init__(self):
        """Initialize the Simplex parser."""
        self._summary = {}
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
                the simplex method.
        """
        progress_match = SimplexParser.simplex_progress_pattern.match(line)
        if progress_match:
            self._progress.append(typeconvert_groupdict(progress_match))
            return True

        mip_relaxation_match = SimplexParser.simplex_mip_relaxation_pattern.match(line)
        if mip_relaxation_match:
            self._summary.update(typeconvert_groupdict(mip_relaxation_match))
            return False

        return False

    def get_summary(self) -> dict:
        """Return the current parsed summary.

        It returns an empty dictionary when solving an LP.
        """
        return self._summary

    def get_progress(self) -> list:
        """Return the detailed progress in simplex method if exists."""
        return self._progress
