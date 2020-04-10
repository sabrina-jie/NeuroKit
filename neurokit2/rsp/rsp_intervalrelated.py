# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

from .rsp_rrv import rsp_rrv


def rsp_intervalrelated(data, sampling_rate=1000):
    """
    Performs RSP analysis on longer periods of data (typically > 10 seconds),
    such as resting-state data.

    Parameters
    ----------
    data : DataFrame, dict
        A DataFrame containing the different processed signal(s) as
        different columns, typically generated by `rsp_process()` or
        `bio_process()`. Can also take a dict containing sets of
        separately processed DataFrames.
    sampling_rate : int
        The sampling frequency of the signal (in Hz, i.e., samples/second).

    Returns
    -------
    DataFrame
        A dataframe containing the analyzed RSP features. The analyzed
        features consist of the following:
        - *"RSP_Rate_Mean"*: the mean heart rate.
        - *"RSP_Amplitude_Mean"*: the mean respiratory amplitude.
        - *"RSP_RRV"*: the different respiratory rate variability metrices.
        See `rsp_rrv()` docstrings for details.

    See Also
    --------
    bio_process, rsp_eventrelated

    Examples
    ----------
    >>> import neurokit2 as nk
    >>>
    >>> # Download data
    >>> data = nk.data("bio_resting_5min_100hz")
    >>>
    >>> # Process the data
    >>> df, info = nk.rsp_process(data["RSP"], sampling_rate=100)

    >>> # Single dataframe is passed
    >>> nk.rsp_intervalrelated(df)
    >>>
    >>> epochs = nk.epochs_create(df, events=[0, 15000], sampling_rate=100, epochs_end=150)
    >>> nk.rsp_intervalrelated(epochs)
    """
    intervals = {}

    # Format input
    if isinstance(data, pd.DataFrame):
        rate_cols = [col for col in data.columns if 'RSP_Rate' in col]
        if len(rate_cols) == 1:
            intervals.update(_rsp_intervalrelated_formatinput(data))
            intervals.update(_rsp_intervalrelated_rrv(data, sampling_rate))
        else:
            raise ValueError("NeuroKit error: rsp_intervalrelated(): Wrong"
                             "input, we couldn't extract breathing rate."
                             "Please make sure your DataFrame"
                             "contains an `RSP_Rate` column.")
        amp_cols = [col for col in data.columns if 'RSP_Amplitude' in col]
        if len(amp_cols) == 1:
            intervals["RSP_Amplitude_Mean"] = data[amp_cols[0]].values.mean()
        else:
            raise ValueError("NeuroKit error: rsp_intervalrelated(): Wrong"
                             "input, we couldn't extract respiratory amplitude."
                             "Please make sure your DataFrame"
                             "contains an `RSP_Amplitude` column.")

        rsp_intervals = pd.DataFrame.from_dict(intervals,
                                               orient="index").T

    elif isinstance(data, dict):
        for index in data:
            intervals[index] = {}  # Initialize empty container

            # Format dataframe
            data[index] = data[index].set_index('Index').drop(['Label'], axis=1)

            # Rate and Amplitude
            intervals[index] = _rsp_intervalrelated_formatinput(data[index],
                                                                intervals[index])

            # RRV
            intervals[index] = _rsp_intervalrelated_rrv(data[index], sampling_rate,
                                                        intervals[index])

        rsp_intervals = pd.DataFrame.from_dict(intervals, orient="index")

    return rsp_intervals

# =============================================================================
# Internals
# =============================================================================


def _rsp_intervalrelated_formatinput(data, output={}):
    # Sanitize input
    colnames = data.columns.values
    if len([i for i in colnames if "RSP_Rate" in i]) == 0:
        raise ValueError("NeuroKit error: rsp_intervalrelated(): Wrong"
                         "input, we couldn't extract breathing rate."
                         "Please make sure your DataFrame"
                         "contains an `RSP_Rate` column.")
        return output
    if len([i for i in colnames if "RSP_Amplitude" in i]) == 0:
            raise ValueError("NeuroKit error: rsp_intervalrelated(): Wrong"
                             "input we couldn't extract respiratory amplitude."
                             "Please make sure your DataFrame"
                             "contains an `RSP_Amplitude` column.")
            return output

    rate = data["RSP_Rate"].values
    amplitude = data["RSP_Amplitude"].values

    output["RSP_Rate_Mean"] = np.mean(rate)
    output["RSP_Amplitude_Mean"] = np.mean(amplitude)

    return output


def _rsp_intervalrelated_rrv(data, sampling_rate, output={}):

    rrv = rsp_rrv(data, sampling_rate=sampling_rate)
    for column in rrv.columns:
        output[column] = float(rrv[column])

    return output
