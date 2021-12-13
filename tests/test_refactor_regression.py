"""
Temporary test against the current 'correct' outputs (for fearless refactoring).
There's always a chance the current code has bugs, so a failure of this test is
not necessarily an issue, it's more an indication to re-check so that nothing is
inadvertently lost along the way.

Uses feather format to store the comparison dataframe, so pyarrow needs to be
installed. This is also temporarily added to the tox config.

It would be best to remove this test after the refactor.

Notes:
- NoRel timeline is already tested specifically in test_load.test_norel_timeline
"""

import pathlib

import pandas as pd
import pytest
import grblogtools as glt

HERE = pathlib.Path(__file__).parent


def df_assert_equal(ordered, expected, name):
    assert list(ordered.columns) == list(
        expected.columns
    ), f"Regresion in {name} dataframe: mismatched column names"
    for c in ordered.columns:
        assert (
            (expected[c] == ordered[c]) | ordered[c].isnull()
        ).all(), f"Regression in column '{c}' of {name} dataframe (mismatched values)"
        assert (
            expected[c].isnull() == ordered[c].isnull()
        ).all(), f"Regression in column {c} of {name} dataframe (mismatched nulls)"


def test_summary():
    summary = glt.get_dataframe(["data/*.log"])
    ordered = (
        summary.sort_values("LogFilePath")
        .reset_index(drop=True)
        .sort_index(axis="columns")
    )
    expected = pd.read_feather(HERE / "assets/summary.feather")
    df_assert_equal(ordered, expected, name="summary")


def test_nodelog_timelines():
    _, timelines = glt.get_dataframe(["data/912-glass4-*.log"], timelines=True)
    nodelog = timelines["nodelog"]
    ordered = (
        nodelog.sort_values(["LogFilePath", "Time"])
        .sort_index(axis="columns")
        .reset_index(drop=True)
    )
    expected = pd.read_feather(HERE / "assets/nodelog.feather")
    df_assert_equal(ordered, expected, name="nodelog")


@pytest.mark.skip(reason="no rootlp log data to test against")
def test_rootlp_timelines():
    """RootLP timeline has no test data (TODO add an example log)"""
    _, timelines = glt.get_dataframe(["data/912-glass4-*.log"], timelines=True)
    rootlplog = timelines["rootlp"]
