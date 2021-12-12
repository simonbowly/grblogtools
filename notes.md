# Refactor attempt 2

From discussion with Maliheh about better breaking down the code into modules.

## Current approach

In `get_log_info` (assume we have a single log file at this point? are we able to parse multiple logs in one file?):

0. Passed a list of log lines
1. Scan forward to find the header, slice loglines to remove previous
2. Scan forward to find termination
3. Scan entire log (in reverse) to get presolve info (why in reverse? forward actually seems more sensible?)

General pattern for summary regexes is "if match, unpack the groupdict into the values dict". This could be abstracted as lineparser (pattern, callback) where the default callback is just to update the summary dict passed in.

## Issues

Currently many section parsers scan the entire log, and this could be improved. Section parsers could be classes, with start triggers and main parsing loops, e.g.

```python

class SectionFlag(Enum):
    """ boolean returns for logstart and logparse might be sufficient? """
    NOTHING: 0
    START: 1
    CONTINUE: 2
    END: 3

class NoRelLogParser:

    norel_log_start = re.compile("Starting NoRel heuristic")
    norel_primal_regex = re.compile(
        "Found heuristic solution:\sobjective\s(?P<Incumbent>[^\s]+)"
    )
    norel_elapsed_time = re.compile(
        "Elapsed time for NoRel heuristic:\s(?P<Time>\d+)s"
    )
    norel_elapsed_bound = re.compile(
        "Elapsed time for NoRel heuristic:\s(?P<Time>\d+)s\s\(best\sbound\s(?P<BestBd>[^\s]+)\)"
    )

    def __init__(self):
        """ Makes sense as a class, as we should keep some state as lines are
        traversed. """
        self.values = {}  # Could be a dataclass with defined fields?
                          # However this would come with some lock-in.
        self.norel_log = []
        self.norel_incumbent = {}

    def logstart(self, line: str) -> SectionFlag:
        """ Called by the main parsing loop when we are in previous sections
        of the log, to detect the start of norel. """
        if norel_log_start.match(line):
            return SectionFlag.START
        return SectionFlag.NOTHING

    def logparse(self, line: str) -> SectionFlag:
        """ Called by the mian parsing loop when we are currently in the norel
        section. Stops being called once either we return a sentinel value to
        indicate the end of the log, or when another parser steps in to take over.
        """
        if match := norel_primal_regex.match(line):
            self.values['NoRelBestSolution'] = float(match.group('Incumbent'))
            # store incumbent info to combine with the next timing line
            self.norel_incumbent = result.groupdict()
        elif match := norel_elapsed_time.match(line):
            self.values['NoRelTime'] = float(match.group('Time'))
            self.norel_log.append(result.groupdict() | self.norel_incumbent)
        elif match := norel_elapsed_bound.match(line):
            self.values['NoRelBestBound'] = float(match.group('BestBd'))
            self.values['NoRelTime'] = float(match.group('Time'))
            self.norel_log.append(result.groupdict() | self.norel_incumbent)
        return SectionFlag.CONTINUE

    def get_summary(self):
        return self.values

    def get_timelines(self):
        return self.norel_log


def main_parsing_loop(loglines: Iterable[str]):
    section_parsers = [HeaderParser(), NoRelLogParser(), SimplexParser(), ..., TerminationParser()]
    # Just do one pass to populate all the section parsers.
    current_section_parser = None
    for line in loglines:
        # If there is an active parser, pass it the current line.
        if current_section_parser:
            flag = current_section_parser.logparse(line)
            if flag == SectionFlag.END:
                current_section_parser = None
        # Check if any other section should take control.
        for parser in section_parsers:
            flag = parser.logstart(line)
            if flag == SectionFlag.START:
                current_section_parser = parser
    # ... after termination
    summary = {}
    for section_parser in section_parsers:
        summary.update(section_parser.get_summary())
    # specially check the parsers which indicate they have timelines?
```

The logic for `main_parsing_loop` needs more thought:

1. We know the sections are coming in a certain order, so should only ask subsequent section parsers if they want to take control (i.e. drop parsers from the front of `section_parsers`).
2. We should create only the header parser initially, and create fresh section parsers once the header is seen (this would make it easier to parse multiple logs in the same file).
3. Termination section should be treated separately (nothing should follow it, once it completes, we should collect and combine information from all parsers to return).
    * There are 3 end-of-log conditions to handle: end of log lines, `TerminationParser` indicates end of section, and `HeaderParser` indicates start of section (new log). At all these points, we should collect and yield the log data from the main loop, then continue on to the next log with fresh parsers.
4. There may be a generic parser that always needs to be called (i.e. for the "various" patterns if it is not clear in which section they would appear). However, the better we can narrow down which section each regex should be called in, the faster the overall log traversal should be.
