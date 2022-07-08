from typing import List, Optional

import numpy as np
import pandas as pd

from grblogtools.helpers import load_defaults, re_parameter_column


def changed_parameter_mask(summary: pd.DataFrame):
    """Take a grblogtools summary dataframe and return a dataframe with one
    columns per parameter setting used. Boolean values in the dataframe indicate
    whether the parameter has been changed from defauts in the run corresponding
    to its row.
    """
    params = summary[
        [c for c in summary.columns if re_parameter_column.match(c)]
    ].rename(columns=lambda c: re_parameter_column.match(c).group(1))
    defaults = load_defaults("952")
    defaults_map = pd.DataFrame(
        {
            c: pd.Series(index=s.index, data=defaults[c])
            for c, s in params.items()
            if c in defaults
        }
    )
    return defaults_map != params[defaults_map.columns]


def run_label(
    summary: pd.DataFrame,
    omit_params: Optional[List[str]] = None,
    omit_version: bool = False,
    include_seed: bool = False,
):
    """
    Produce a label following version-changedparams- convention.
    Args:
        summary: summary dataframe from get_dataframe
        omit_params: a list of parameter names to omit from the label
        omit_version: set to true to leave out the version (default False)
        include_seed: set to true to include the seed (default False)
    """
    if omit_params is None:
        omit_params = []
    params = (
        summary[[c for c in summary.columns if re_parameter_column.match(c)]]
        .rename(columns=lambda c: re_parameter_column.match(c).group(1))
        .drop(columns=omit_params)
    )
    mask = changed_parameter_mask(summary)
    result = params.applymap(str).where(mask)
    if not omit_version:
        result = result.assign(
            AAAVersion=summary["Version"].str.replace(".", "", regex=False)
        )
    if include_seed:
        result = result.assign(ZZZSeed=summary["Seed"].apply("s{:d}".format))
    return result.sort_index(axis=1).apply(
        lambda r: "-".join(
            v if "Version" in p or "Seed" in p else f"{p}{v}"
            for p, v in r.items()
            if pd.notnull(v)
        ),
        axis=1,
    )


def common_parameters(summary):
    params = summary[
        [c for c in summary.columns if re_parameter_column.match(c)]
    ].rename(columns=lambda c: re_parameter_column.match(c).group(1))
    return params.agg(lambda s: len(np.unique(s)), axis=0).pipe(
        lambda s: list(s[s == 1].index)
    )


label_nondefaults = lambda df: run_label(df, omit_version=True, include_seed=False)

label_nondefaults_noncommon = lambda df: run_label(
    df, omit_version=True, include_seed=False, omit_params=common_parameters(df)
)
