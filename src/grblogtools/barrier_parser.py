import re

from grblogtools.helpers import typeconvert_groupdict


class BarrierParser:
    # The pattern indicating the initialization of the parser
    barrier_start_pattern = re.compile(
        r"Iter(\s+)Primal(\s+)Dual(\s+)Primal(\s+)Dual(\s+)Compl(\s+)Time"
    )

    # The pattern indicating the barrier progress
    barrier_progress_pattern = re.compile(
        r"\s*(?P<Iteration>\d+)(?P<Indicator>\s|\*)\s+(?P<PObj>[^\s]+)\s+(?P<DObj>[^\s]+)\s+(?P<PRes>[^\s]+)\s+(?P<DRes>[^\s]+)\s+(?P<Compl>[^\s]+)\s+(?P<Time>\d+)s"
    )

    # The pattern indicating the start or the termination of the barrier in case of
    # solving an MIP. In some cases, the barrier log might only include this one
    # line
    barrier_mip_relaxation_pattern = re.compile(
        r"Root relaxation: objective (?P<RelaxObj>[^,]+), (?P<RelaxIterCount>\d+) iterations, (?P<RelaxTime>[^\s]+) seconds"
    )

    barrier_crossover_pattern = re.compile(
        r"Push phase complete: Pinf (?P<PushPhasePInf>[^,]+), Dinf (?P<PushPhaseDInf>[^,]+)\s+(?P<PushPhaseEndTime>\d+)s"
    )

    def __init__(self):
        """Initialize the Barrier parser."""
        self._summary = {}
        self._crossover = {}
        self._progress = []

    def start_parsing(self, line: str) -> bool:
        """Return True if the parser should start parsing the future log lines.

        Args:
            line (str): A line in the log file.

        Returns:
            bool: Return True if the given line matches the parser start patterns.
        """
        if BarrierParser.barrier_start_pattern.match(line):
            return True

        mip_relaxation_match = BarrierParser.barrier_mip_relaxation_pattern.match(line)
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
                the barrier method.
        """
        progress_match = BarrierParser.barrier_progress_pattern.match(line)
        if progress_match:
            self._progress.append(typeconvert_groupdict(progress_match))
            return True

        crossover_match = BarrierParser.barrier_crossover_pattern.match(line)
        if crossover_match:
            self._crossover.update(typeconvert_groupdict(crossover_match))
            return True

        mip_relaxation_match = BarrierParser.barrier_mip_relaxation_pattern.match(line)
        if mip_relaxation_match:
            self._summary.update(typeconvert_groupdict(mip_relaxation_match))

        return False

    def get_summary(self) -> dict:
        """Return the current parsed summary.

        It returns an empty dictionary when solving an LP.
        """
        return self._summary

    def get_progress(self) -> list:
        """Return the detailed progress in simplex method if ."""
        return self._progress

    def get_crossover_summary(self) -> dict:
        """Return the crossover summary if exists."""
        return self._crossover
