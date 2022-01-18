from grblogtools.parsers.continuous import ContinuousParser
from grblogtools.parsers.header import HeaderParser
from grblogtools.parsers.nodelog import NodeLogParser
from grblogtools.parsers.norel import NoRelParser
from grblogtools.parsers.presolve import PresolveParser
from grblogtools.parsers.termination import TerminationParser


class SingleLogParser:
    """Parses one log. The class expects start_parsing to be called once for each
    line, until it returns true, after which it expects continue_parsing to be
    called once for each remaining line in sequence."""

    def __init__(self):

        # Parsers in sequence.
        self.header_parser = HeaderParser()
        self.presolve_parser = PresolveParser()
        self.norel_parser = NoRelParser()
        self.continuous_parser = ContinuousParser()
        self.nodelog_parser = NodeLogParser()
        self.termination_parser = TerminationParser()

        # State
        self.started = False
        self.current_parser = self.header_parser
        self.future_parsers = [
            self.presolve_parser,
            self.norel_parser,
            self.continuous_parser,
            self.nodelog_parser,
        ]

    def get_summary(self):
        """Return a summary dictionary, which is just a merged result of the
        sub-parser results."""
        summary = {}
        summary.update(self.header_parser.get_summary())
        summary.update(self.presolve_parser.get_summary())
        summary.update(self.norel_parser.get_summary())
        summary.update(self.continuous_parser.get_summary())
        summary.update(self.nodelog_parser.get_summary())
        summary.update(self.termination_parser.get_summary())
        return summary

    def get_nodelog_progress(self):
        """Return the progress of the tree search."""
        return self.nodelog_parser.get_progress()

    def get_norel_progress(self):
        """Return the progress of the No-Relaxation heuristic."""
        return self.norel_parser.get_progress()

    def get_rootlp_progress(self):
        """Return the progress of the continuous algorithm."""
        return self.continuous_parser.get_progress()

    def parse(self, line: str) -> bool:
        """Parse the given log line.

        Args:
            line (str): A line in the log file.

        Returns:
            bool: Return True if the given line is matched.
        """
        # Initially, only check the header parser until started.
        if not self.started:
            assert self.current_parser is self.header_parser
            matched = self.current_parser.start_parsing(line)
            if matched:
                self.started = True
            return matched

        # First try the current parser.
        assert self.current_parser not in self.future_parsers
        if self.current_parser.continue_parsing(line):
            return True

        # Check if any future parsers should take over.
        for i, parser in enumerate(self.future_parsers):
            if parser.start_parsing(line):
                self.current_parser = parser
                self.future_parsers = self.future_parsers[i + 1 :]
                return True

        # Check if the line matches any pattern of the termination parser.
        self.termination_parser.parse(line)

        # Nothing matched.
        return False
