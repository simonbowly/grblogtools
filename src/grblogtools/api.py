"""Top level API for parsing log files.

Examples:

    import grblogtools.api as glt
    result = glt.parse("data/*.log")
    result.summary()  # summary dataframe (like get_dataframe)

Similar for dataframes

"""

import glob
from pathlib import Path

import pandas as pd

from grblogtools.helpers import fill_default_parameters
from grblogtools.parsers.single_log import SingleLogParser


def strip_model_and_seed(row):
    """
    If the log path contains the model name, return everything to the left.
    Otherwise, just return the log stem.

    i.e. with Model = 'glass4'
        data/912-Cuts0-glass4-0.log -> 912-Cuts0
        data/some-log.log -> some-log
    """
    log_stem = Path(row["LogFilePath"]).stem
    run, mid, _ = log_stem.partition(row["Model"])
    if mid and run:
        return run.rstrip("-")
    return log_stem


class ParseResult:
    def __init__(self):
        self.parsers = []

    def progress(self):
        nodelog = pd.DataFrame(
            [row for _, parser in self.parsers for row in parser.get_nodelog_progress()]
        )
        norel = pd.DataFrame(
            [row for _, parser in self.parsers for row in parser.get_norel_progress()]
        )
        rootlp = pd.DataFrame(
            [row for _, parser in self.parsers for row in parser.get_rootlp_progress()]
        )
        return {
            "rootlp": rootlp,
            "norel": norel,
            "nodelog": nodelog,
        }

    def summary(self):
        """Construct and return a summary dataframe for all parsed logs."""
        summary = pd.DataFrame(
            [
                dict(parser.get_summary(), LogFilePath=logfile)
                for logfile, parser in self.parsers
            ]
        )
        # Post-processing to match old API
        parameters = pd.DataFrame(
            [parser.header_parser.get_parameters() for _, parser in self.parsers]
        )
        if "Seed" in parameters.columns:
            seed = parameters[["Seed"]].fillna(0).astype(int)
            parameters = parameters.drop(columns=["Seed"])
        else:
            seed = None
        parameters = parameters.rename(columns=lambda c: c + " (Parameter)")
        summary = (
            summary.rename(columns={"ReadingTime": "ReadTime"})
            .join(parameters)
            .assign(
                ModelFile=lambda df: df["ModelFilePath"].apply(
                    lambda p: Path(p).parts[-1].partition(".")[0]
                ),
                Model=lambda df: df["ModelFile"],
                Log=lambda df: df.apply(strip_model_and_seed, axis=1),
            )
        )
        if seed is not None:
            summary = summary.join(seed)
        # TODO fill_default_parameters could be much cleaner now, without column regexes
        summary = fill_default_parameters(summary)
        return summary

    def parse(self, logfile: str) -> None:
        """Parse a single file. The log file may contain multiple run logs."""
        parser = SingleLogParser()
        subsequent = SingleLogParser()
        log_count = 0
        with open(logfile) as infile:
            lines = iter(infile)
            for line in lines:
                if not parser.parse(line):
                    assert not subsequent.started
                    if subsequent.parse(line):
                        # The current parser did not match but an empty parser
                        # matched a header line.
                        log_count += 1
                        self.parsers.append((f"{logfile}({log_count})", parser))
                        parser = subsequent
                        subsequent = SingleLogParser()

        if log_count:
            log_count += 1
            self.parsers.append((f"{logfile}({log_count})", parser))
        else:
            self.parsers.append((logfile, parser))


def parse(arg: str) -> ParseResult:
    """Main entry point function.

    Args:
        arg (str): A glob pattern matchine log files.

    TODO extend this, a list of patterns, or a vararg of patterns, should also work.
    """

    result = ParseResult()
    for logfile in glob.glob(arg):
        result.parse(logfile)

    return result


def get_dataframe(logfiles, timelines=False):
    """Compatibility function for the legacy API.

    Args:
        logfiles (str): Path pattern to log files.
        timeliens (bool, optional): Return the timeline progress if set to True.
            Default False.
    """
    result = parse(*logfiles)
    if not timelines:
        return result.summary()
    return result.summary(), result.progress()
