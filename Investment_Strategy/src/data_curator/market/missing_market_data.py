
"""
Missing Market Data

Helper module for computing derived market data columns
such as daily traded value and its moving averages.
"""

# Here you'll find helper functions for calculating more complicated features:
from kaxanuk.data_curator.features import helpers
from kaxanuk.data_curator.modules.data_column import DataColumn

# =============================================================================
# Column Functions
# =============================================================================


def c_daily_traded_value_1d(
    m_volume_split_adjusted: DataColumn,
    m_close_split_adjusted: DataColumn,
) -> DataColumn:
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

def c_daily_traded_value_63d(c_daily_traded_value_1d: DataColumn) -> DataColumn:
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

def c_split_ratio(m_close_split_adjusted, m_close):
    """
    Calculate the split ratio from split-adjusted and unadjusted close prices.

    The split ratio represents the cumulative effect of all stock splits
    on the price. A ratio greater than 1 indicates the stock has undergone
    forward splits, while a ratio less than 1 indicates reverse splits.

    Parameters
    ----------
    m_close_split_adjusted : DataColumn
        Close price adjusted for stock splits.
    m_close : DataColumn
        Unadjusted (raw) close price.

    Returns
    -------
    DataColumn
        The split ratio for each date, calculated as
        split_adjusted_close / unadjusted_close.
    """
    return m_close_split_adjusted / m_close


def c_vwap(c_split_ratio, m_vwap_split_adjusted):
    """
    Calculate the unadjusted Volume Weighted Average Price (VWAP).

    Derives the raw VWAP by removing the split adjustment from the
    split-adjusted VWAP.

    Parameters
    ----------
    c_split_ratio : DataColumn
        The split ratio calculated from close prices.
    m_vwap_split_adjusted : DataColumn
        VWAP adjusted for stock splits.

    Returns
    -------
    DataColumn
        The unadjusted VWAP, calculated as
        vwap_split_adjusted / split_ratio.
    """
    return m_vwap_split_adjusted / c_split_ratio


def c_dividend_split_ratio(m_close_dividend_and_split_adjusted, m_close):
    """
    Calculate the combined dividend and split adjustment ratio.

    This ratio captures the cumulative effect of both dividends and stock
    splits on the price. Useful for calculating total return metrics.

    Parameters
    ----------
    m_close_dividend_and_split_adjusted : DataColumn
        Close price adjusted for both dividends and stock splits.
    m_close : DataColumn
        Unadjusted (raw) close price.

    Returns
    -------
    DataColumn
        The dividend and split ratio for each date, calculated as
        dividend_and_split_adjusted_close / unadjusted_close.
    """
    return m_close_dividend_and_split_adjusted / m_close


def c_vwap_dividend_and_split_adjusted(c_dividend_split_ratio, c_vwap):
    """
    Calculate the VWAP adjusted for both dividends and stock splits.

    Applies the dividend and split adjustment ratio to the unadjusted VWAP
    to obtain a fully adjusted VWAP suitable for total return calculations.

    Parameters
    ----------
    c_dividend_split_ratio : DataColumn
        The combined dividend and split adjustment ratio.
    c_vwap : DataColumn
        The unadjusted VWAP.

    Returns
    -------
    DataColumn
        VWAP adjusted for dividends and splits, calculated as
        dividend_split_ratio * unadjusted_vwap.
    """
    return c_dividend_split_ratio * c_vwap
