
"""
Missing Market Data

Helper module for computing derived market data columns
such as daily traded value and its moving averages.
"""

# Here you'll find helper functions for calculating more complicated features:
from kaxanuk.data_curator.features import helpers

# =============================================================================
# Column Functions
# =============================================================================


def c_daily_traded_value_1d(
    m_volume_split_adjusted,
    m_close_split_adjusted,
):
    """
    Calculate the daily traded value (dollar volume) for a single day.

    Multiplies the split-adjusted closing price by the split-adjusted volume
    to obtain the total monetary value of shares traded in a given day.

    Parameters
    ----------
    m_volume_split_adjusted : numeric
        The split-adjusted trading volume for the day.
    m_close_split_adjusted : numeric
        The split-adjusted closing price for the day.

    Returns
    -------
    numeric
        The daily traded value (price * volume).
    """

    output = m_close_split_adjusted * m_volume_split_adjusted
    return output

def c_daily_traded_value_63d(c_daily_traded_value_1d):
    """
    Calculate the 63-day simple moving average of daily traded value.

    Uses a 63-trading-day window (approximately one calendar quarter)
    to smooth out short-term fluctuations in daily traded value,
    providing a measure of average liquidity over the period.

    Parameters
    ----------
    c_daily_traded_value_1d : numeric
        The single-day daily traded value, as computed by
        :func:`c_daily_traded_value_1d`.

    Returns
    -------
    numeric
        The 63-day simple moving average of daily traded value.
    """
    output = helpers.simple_moving_average(
        column=c_daily_traded_value_1d,
        days=63
    )
    return output