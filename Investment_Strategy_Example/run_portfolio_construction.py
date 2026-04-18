"""
Liquidity-Weighted Trend Strategy — Portfolio Construction
==========================================================

Rules (from S03 Portfolio Construction & Strategy Modeling)
-----------------------------------------------------------

**Selection:**
    - Securities with ``c_sma_50d_200d_signal == 1`` are eligible.
    - Single-day traded value (``c_daily_traded_value_1d``) >=
      ``MIN_DAILY_TRADED_VALUE`` ($10 M floor).
    - Rank eligible securities by ``c_daily_traded_value_63d`` (descending).
    - Select the top ``MAX_POSITIONS`` securities.

**Sizing:**
    - Weights are proportional to 63-day average traded value among selected
      securities.
    - Maximum ``MAX_WEIGHT`` per position.
    - Excess weight is redistributed proportionally.

**Timing:**
    Rebalance when any of the following occurs:
        * A security enters the top-``MAX_POSITIONS``.
        * A security exits the top-``MAX_POSITIONS``.
        * Transition into / out of SPY-only regime.
        * A held constituent becomes untradable (rebalance on T-1).

**Market Regime Handling:**
    - If fewer than ``MIN_ELIGIBLE_STOCKS`` stocks pass selection filters,
      invest 100 % in SPY ETF.
    - Exit the SPY regime when eligible stocks >= ``REENTRY_THRESHOLD``
      (hysteresis) to avoid excessive rebalancing.

**Delisting / Untradable Handling:**
    - For each ticker, check raw close (``m_close_split_adjusted``) and
      volume (``m_volume_split_adjusted``).
    - A ticker is flagged as untradable when:
        * It has no valid adjusted close
          (``m_close_dividend_and_split_adjusted``) on a given date, **or**
        * In a trailing window of ``DELIST_LOOKBACK_DAYS``, the fraction of
          days with missing raw close or zero volume >=
          ``DELIST_MISSING_THRESHOLD``.
    - The forced rebalance to sell the ticker fires on T-1 (the last
      healthy day before problems start).
    - From the exclude date onward the ticker is permanently ineligible.

**Signal timing:**
    All signal, traded-value, and liquidity data used on day T comes from
    day T-1 (previous close), ensuring decisions are based exclusively on
    data known before T opens. Same-day adjusted close is used only as a
    tradability guard.

**Output:**
    - Rows = tickers (alphabetical).
    - Columns = rebalance dates only.
    - Values = portfolio weights (rounded to 9 decimals).
"""

import pathlib

import numpy
import pandas


# ==============================================================================
# PATHS
# ==============================================================================
DATA_DIR = pathlib.Path(r"Data_Curator")
CONFIG_DIR = pathlib.Path(r"Config")
OUTPUT_DIR = pathlib.Path(r"Portfolio_Construction")

# ==============================================================================
# STRATEGY PARAMETERS
# ==============================================================================
MAX_POSITIONS = 35
MAX_WEIGHT = 0.20
MIN_DAILY_TRADED_VALUE = 10_000_000   # $10 M single-day floor for eligibility
SPY_TICKER = "SPY"

MIN_ELIGIBLE_STOCKS = 50   # Enter SPY regime below this threshold
REENTRY_THRESHOLD = 60     # Exit SPY regime at or above this threshold

COL_DATE = "m_date"
COL_TICKER = "Ticker"
COL_SIGNAL = "c_sma_50d_200d_signal"
COL_TRADED_VALUE_1D = "c_daily_traded_value_1d"
COL_TRADED_VALUE_63D = "c_daily_traded_value_63d"
COL_CLOSE = "m_close_dividend_and_split_adjusted"
COL_CLOSE_RAW = "m_close_split_adjusted"
COL_VOLUME = "m_volume_split_adjusted"

# Delisting / untradable detection parameters
DELIST_LOOKBACK_DAYS = 21       # trailing window size (trading days)
DELIST_MISSING_THRESHOLD = 0.05  # fraction of missing days to flag as untradable

PORTFOLIO_START = pandas.Timestamp("2007-01-01")
PORTFOLIO_END = pandas.Timestamp("2026-04-17")


# ==============================================================================
# 1. DATA LOADING
# ==============================================================================
def _read_config_tickers() -> list[str]:
    """Read ticker universe from the config Excel file (all sheets)."""
    config_path = CONFIG_DIR / "data_curator_parameters.xlsx"
    if not config_path.exists():
        return []
    try:
        excel_file = pandas.ExcelFile(config_path)
        tickers: list[str] = []
        seen: set[str] = set()
        for sheet in excel_file.sheet_names:
            frame = pandas.read_excel(config_path, sheet_name=sheet)
            for col in frame.columns:
                for val in frame[col].dropna().astype(str):
                    tkr = val.strip().split()[0]
                    if (
                        tkr
                        and tkr not in seen
                        and not tkr.replace(".", "").replace("-", "").isdigit()
                        and len(tkr) <= 10
                    ):
                        tickers.append(tkr)
                        seen.add(tkr)
        print(f"  Config tickers: {len(tickers)}")
        return tickers
    except Exception:
        return []


def load_data() -> tuple[pandas.DataFrame, list[str], list[str]]:
    """Load all ticker CSVs from DATA_DIR and return a single long DataFrame."""
    csv_paths = {csv_file.stem: csv_file for csv_file in sorted(DATA_DIR.glob("*.csv"))}
    print(f"  CSV files found: {len(csv_paths)}")

    config_tickers = _read_config_tickers()
    if config_tickers:
        tickers_to_load = [tkr for tkr in config_tickers if tkr in csv_paths]
        missing = [tkr for tkr in config_tickers if tkr not in csv_paths]
        if not tickers_to_load:
            print("  WARNING: No config tickers matched — loading all CSVs.")
            tickers_to_load = list(csv_paths.keys())
            missing = []
    else:
        tickers_to_load = list(csv_paths.keys())
        missing = []

    frames: list[pandas.DataFrame] = []
    loaded: list[str] = []
    for load_idx, tkr in enumerate(sorted(tickers_to_load)):
        try:
            frame = pandas.read_csv(csv_paths[tkr], low_memory=False)
            if load_idx == 0:
                print(f"  Sample: {tkr}.csv | Cols: {len(frame.columns)} | Rows: {len(frame)}")
            frame[COL_TICKER] = tkr
            frames.append(frame)
            loaded.append(tkr)
        except Exception as exc:
            print(f"  ERROR {tkr}.csv: {exc}")
            missing.append(tkr)

    if not frames:
        raise RuntimeError("No data loaded.")

    data = pandas.concat(frames, ignore_index=True)

    if COL_DATE not in data.columns:
        for col in data.columns:
            if "date" in col.lower():
                data.rename(columns={col: COL_DATE}, inplace=True)
                break

    data[COL_DATE] = pandas.to_datetime(data[COL_DATE], format="mixed", dayfirst=False)
    data.sort_values([COL_DATE, COL_TICKER], inplace=True)
    data.reset_index(drop=True, inplace=True)

    print(f"  Loaded: {len(loaded)} tickers | Missing: {len(missing)}")
    print(f"  Total rows: {len(data):,}")
    print(f"  Date range: {data[COL_DATE].min().date()} → {data[COL_DATE].max().date()}")

    return data, loaded, missing


# ==============================================================================
# 2. FEATURE VALIDATION
# ==============================================================================
def validate_features(data: pandas.DataFrame) -> None:
    """Ensure the required columns exist and contain data."""
    required = [
        (COL_SIGNAL, "Signal"),
        (COL_TRADED_VALUE_1D, "Traded-value (1-day)"),
        (COL_TRADED_VALUE_63D, "Traded-value (63-day)"),
        (COL_CLOSE, "Close price (adjusted)"),
        (COL_CLOSE_RAW, "Close price (raw)"),
        (COL_VOLUME, "Volume"),
    ]
    for col, label in required:
        if col not in data.columns:
            raise ValueError(
                f"{label} column '{col}' not found.  Available: {sorted(data.columns)}"
            )
        non_null_count = data[col].notna().sum()
        if non_null_count == 0:
            raise ValueError(f"{label} column '{col}' has no valid data.")
        print(f"  {label}: '{col}' ({non_null_count:,} non-null)")


# ==============================================================================
# 3. BUILD PIVOT MATRICES  (date × ticker)
# ==============================================================================
def build_matrices(
    data: pandas.DataFrame,
) -> tuple[
    pandas.DataFrame,
    pandas.DataFrame,
    pandas.DataFrame,
    pandas.DataFrame,
    pandas.DataFrame,
    pandas.DataFrame,
]:
    """
    Pivot to aligned signal, traded-value, close, raw-close, and volume matrices.

    Parameters
    ----------
    data
        Long-format DataFrame with all tickers concatenated.

    Returns
    -------
        Tuple of (signal_df, tv_1d_df, tv_63d_df, close_adj_df,
        close_raw_df, volume_df), each a date × ticker DataFrame.
    """
    print("  Building matrices …")

    pivot_specs = [
        (COL_SIGNAL, "signal"),
        (COL_TRADED_VALUE_1D, "traded_value_1d"),
        (COL_TRADED_VALUE_63D, "traded_value_63d"),
        (COL_CLOSE, "close_adj"),
        (COL_CLOSE_RAW, "close_raw"),
        (COL_VOLUME, "volume"),
    ]

    pivots: dict[str, pandas.DataFrame] = {}
    for col, key in pivot_specs:
        pivots[key] = data.pivot_table(
            index=COL_DATE, columns=COL_TICKER, values=col, aggfunc="last"
        ).sort_index()

    all_dates = pivots["signal"].index
    all_tickers = pivots["signal"].columns
    for key in pivots:
        all_dates = all_dates.union(pivots[key].index)
        all_tickers = all_tickers.union(pivots[key].columns)
    all_dates = all_dates.sort_values()
    all_tickers = all_tickers.sort_values()

    for key in pivots:
        pivots[key] = pivots[key].reindex(index=all_dates, columns=all_tickers)

    print(f"  Shape: {len(all_dates):,} dates × {len(all_tickers)} tickers")
    print(f"  Range: {all_dates[0].date()} → {all_dates[-1].date()}")

    return (
        pivots["signal"],
        pivots["traded_value_1d"],
        pivots["traded_value_63d"],
        pivots["close_adj"],
        pivots["close_raw"],
        pivots["volume"],
    )


# ==============================================================================
# 4. SELECTION HELPERS
# ==============================================================================
def _select_eligible_stocks(
    sig_row: numpy.ndarray,
    tv_1d_row: numpy.ndarray,
    tv_63d_row: numpy.ndarray,
    close_row: numpy.ndarray,
    excluded: set[str],
    tickers: numpy.ndarray,
) -> tuple[numpy.ndarray, numpy.ndarray, int]:
    """
    Apply selection filters and return the eligible universe for a single day.

    All input rows except close_row come from T-1 (previous close). close_row
    comes from T and acts only as a tradability guard.

    Selection rules:
        1. SMA crossover signal == 1.
        2. Single-day traded value >= MIN_DAILY_TRADED_VALUE ($10 M floor).
        3. 63-day average traded value is finite and positive (for ranking).
        4. Adjusted close is finite and positive (tradability guard).
        5. Not SPY and not in the excluded set.

    Parameters
    ----------
    sig_row
        T-1 signal array aligned with tickers.
    tv_1d_row
        T-1 single-day traded value array (liquidity floor filter).
    tv_63d_row
        T-1 63-day average traded value array (ranking and sizing input).
    close_row
        T adjusted-close array (tradability guard only).
    excluded
        Tickers to unconditionally exclude (delisted or force-removed today).
    tickers
        Full ticker array corresponding to all matrix columns.

    Returns
    -------
        Tuple of (eligible_tkrs, eligible_tv_63d, n_eligible).
    """
    eligible_mask = (
        (sig_row == 1)
        & (tv_1d_row >= MIN_DAILY_TRADED_VALUE)
        & numpy.isfinite(tv_63d_row)
        & (tv_63d_row > 0)
        & numpy.isfinite(close_row)
        & (close_row > 0)
        & (tickers != SPY_TICKER)
    )
    if excluded:
        exclude_mask = numpy.isin(tickers, list(excluded))
        eligible_mask = eligible_mask & ~exclude_mask

    eligible_tkrs = tickers[eligible_mask]
    eligible_tv_63d = tv_63d_row[eligible_mask]
    return eligible_tkrs, eligible_tv_63d, len(eligible_tkrs)


def _pick_top_n(
    eligible_tkrs: numpy.ndarray,
    eligible_tv_63d: numpy.ndarray,
) -> frozenset:
    """
    Select the top MAX_POSITIONS tickers by 63-day average traded value.

    Parameters
    ----------
    eligible_tkrs
        Tickers that passed all eligibility filters.
    eligible_tv_63d
        Corresponding 63-day average traded values.

    Returns
    -------
        Frozenset of selected ticker symbols.
    """
    if len(eligible_tkrs) <= MAX_POSITIONS:
        return frozenset(eligible_tkrs)
    top_idx = numpy.argsort(-eligible_tv_63d)[:MAX_POSITIONS]
    return frozenset(eligible_tkrs[top_idx])


# ==============================================================================
# 5. REGIME HELPERS
# ==============================================================================
def _determine_regime(n_eligible: int, in_spy_regime: bool) -> bool:
    """
    Determine whether the portfolio should be in SPY regime.

    Uses hysteresis to avoid whipsawing at the boundary: the SPY regime is
    entered when n_eligible < MIN_ELIGIBLE_STOCKS and exited only when
    n_eligible >= REENTRY_THRESHOLD.

    Parameters
    ----------
    n_eligible
        Number of stocks that passed all selection filters.
    in_spy_regime
        Whether the portfolio is currently in SPY regime.

    Returns
    -------
        True if the portfolio should be in SPY regime.
    """
    if in_spy_regime:
        return n_eligible < REENTRY_THRESHOLD
    return n_eligible < MIN_ELIGIBLE_STOCKS


def _needs_rebalance(
    prev_selected: frozenset | None,
    current_selected: frozenset,
    should_spy: bool,
    in_spy_regime: bool,
) -> bool:
    """
    Determine whether a rebalance event has been triggered by composition or regime.

    Parameters
    ----------
    prev_selected
        Selected tickers from the previous rebalance. None on the first day.
    current_selected
        Selected tickers for the current day.
    should_spy
        Whether the portfolio should be in SPY regime today.
    in_spy_regime
        Whether the portfolio was in SPY regime on the previous day.

    Returns
    -------
        True if a rebalance should occur.
    """
    if prev_selected is None:
        return True
    if should_spy != in_spy_regime:
        return True
    if not should_spy and current_selected != prev_selected:
        return True
    return False


# ==============================================================================
# 6. SIZING HELPERS
# ==============================================================================
def _cap_and_redistribute(weights: pandas.Series, cap: float) -> pandas.Series:
    """
    Iteratively cap weights at `cap` and redistribute excess proportionally.

    Parameters
    ----------
    weights
        Raw portfolio weights (must sum to 1.0).
    cap
        Maximum allowed weight per position.

    Returns
    -------
        Capped and redistributed weights clipped to cap.
    """
    capped = weights.copy()
    for _ in range(100):
        over = capped > cap
        if not over.any():
            break
        excess = (capped[over] - cap).sum()
        capped[over] = cap
        under = (capped > 0) & (~over)
        if under.sum() == 0 or capped[under].sum() == 0:
            break
        capped[under] += excess * capped[under] / capped[under].sum()
    return capped.clip(upper=cap)


def _compute_stock_weights(
    eligible_tkrs: numpy.ndarray,
    eligible_tv_63d: numpy.ndarray,
) -> pandas.Series:
    """
    Size positions for the stock regime.

    Weights are proportional to 63-day average traded value among the top
    MAX_POSITIONS tickers, then capped at MAX_WEIGHT with iterative
    redistribution of any excess.

    Parameters
    ----------
    eligible_tkrs
        Tickers that passed all selection filters.
    eligible_tv_63d
        Corresponding 63-day average traded values for ranking and sizing.

    Returns
    -------
        Portfolio weights indexed by ticker, summing to 1.0.
        Returns an empty Series if no eligible ticker has positive traded value.
    """
    tv_series = pandas.Series(eligible_tv_63d, index=eligible_tkrs)
    tv_positive = tv_series[tv_series > 0].sort_values(ascending=False)

    if tv_positive.empty:
        return pandas.Series(dtype=float)

    selected = tv_positive.head(MAX_POSITIONS)
    raw_weights = selected / selected.sum()
    capped_weights = _cap_and_redistribute(raw_weights, MAX_WEIGHT)
    normalized = capped_weights / capped_weights.sum()
    return normalized[normalized > 1e-10]


# ==============================================================================
# 7. DELISTING / UNTRADABLE DETECTION
# ==============================================================================
def detect_untradable_tickers(
    close_adj_df: pandas.DataFrame,
    close_raw_df: pandas.DataFrame,
    volume_df: pandas.DataFrame,
    trading_dates: pandas.DatetimeIndex,
) -> tuple[dict[str, pandas.Timestamp], dict[pandas.Timestamp, set[str]]]:
    """
    Detect tickers that become untradable during the backtest.

    Health is assessed using three price/volume columns:

    - **Adjusted close** (``m_close_dividend_and_split_adjusted``): a ticker
      with no valid value on date D is immediately flagged.
    - **Raw close** (``m_close_split_adjusted``) and **volume**
      (``m_volume_split_adjusted``): used for trailing-window health.  In the
      last ``DELIST_LOOKBACK_DAYS`` trading days, if the fraction of days with
      missing raw close or zero volume >= ``DELIST_MISSING_THRESHOLD``, the
      ticker is flagged.

    Once flagged the function computes:

    - ``exclude_date`` — first unhealthy date (ticker excluded from this day on).
    - ``remove_date``  — one trading day before ``exclude_date`` (forced
      rebalance to sell while a valid price still exists).

    Selling on T-1 is intentional and not look-ahead bias: most delistings,
    mergers, and suspensions are preceded by a public announcement, giving
    investors time to exit before the effective date. The residual risk is
    sudden halts (e.g. fraud-driven delistings) where no announcement window
    exists — these are rare tail events accepted as a known limitation.

    Parameters
    ----------
    close_adj_df
        Date × ticker matrix of dividend-and-split-adjusted close prices.
    close_raw_df
        Date × ticker matrix of split-adjusted (raw) close prices.
    volume_df
        Date × ticker matrix of split-adjusted volume.
    trading_dates
        Dates within the backtest window.

    Returns
    -------
    ticker_exclude_from : dict[str, pandas.Timestamp]
        Mapping of ticker to the first date it must be excluded.
    force_remove_on : dict[pandas.Timestamp, set[str]]
        Mapping of date to tickers that must be force-removed on that date.
    """
    raw_arr = close_raw_df.reindex(index=trading_dates).values
    vol_arr = volume_df.reindex(index=trading_dates).values
    adj_arr = close_adj_df.reindex(index=trading_dates).values
    tickers = close_raw_df.columns.values
    n_dates = len(trading_dates)

    good_day = (
        numpy.isfinite(raw_arr) & (raw_arr > 0)
        & numpy.isfinite(vol_arr) & (vol_arr > 0)
    )
    has_adj = numpy.isfinite(adj_arr) & (adj_arr > 0)

    ticker_exclude_from: dict[str, pandas.Timestamp] = {}
    force_remove_on: dict[pandas.Timestamp, set[str]] = {}

    for col_idx, tkr in enumerate(tickers):
        if tkr == SPY_TICKER:
            continue
        if not has_adj[:, col_idx].any():
            continue

        first_bad_idx = None
        for row_idx in range(n_dates):
            if not has_adj[row_idx, col_idx]:
                first_bad_idx = row_idx
                break
            if row_idx >= DELIST_LOOKBACK_DAYS - 1:
                window = good_day[row_idx - DELIST_LOOKBACK_DAYS + 1: row_idx + 1, col_idx]
                missing_frac = 1.0 - window.mean()
                if missing_frac >= DELIST_MISSING_THRESHOLD:
                    first_bad_idx = row_idx
                    break

        if first_bad_idx is None:
            continue

        exclude_date = trading_dates[first_bad_idx]

        if first_bad_idx == 0:
            # Bad from the very first day — just exclude, no forced rebalance.
            ticker_exclude_from[tkr] = exclude_date
            continue

        remove_date = trading_dates[first_bad_idx - 1]
        ticker_exclude_from[tkr] = exclude_date
        force_remove_on.setdefault(remove_date, set()).add(tkr)

    if ticker_exclude_from:
        print(f"  Untradable tickers detected: {len(ticker_exclude_from)}")
        for tkr in sorted(ticker_exclude_from):
            exc_date_str = ticker_exclude_from[tkr].date()
            remove_date_str = "N/A"
            for report_date, tks in force_remove_on.items():
                if tkr in tks:
                    remove_date_str = report_date.date()
                    break
            print(f"    {tkr}: exclude from {exc_date_str}, force-remove on {remove_date_str}")
    else:
        print("  Untradable tickers detected: 0")

    if force_remove_on:
        print(f"  Force-remove rebalance dates: {len(force_remove_on)}")
        for report_date in sorted(force_remove_on):
            print(f"    {report_date.date()}: remove {sorted(force_remove_on[report_date])}")

    return ticker_exclude_from, force_remove_on


# ==============================================================================
# 8. EVENT-DRIVEN PORTFOLIO CONSTRUCTION
# ==============================================================================
def construct_portfolios(
    signal_df: pandas.DataFrame,
    tv_1d_df: pandas.DataFrame,
    tv_63d_df: pandas.DataFrame,
    close_adj_df: pandas.DataFrame,
    close_raw_df: pandas.DataFrame,
    volume_df: pandas.DataFrame,
) -> dict[pandas.Timestamp, pandas.Series]:
    """
    Build event-driven portfolios over [PORTFOLIO_START, PORTFOLIO_END].

    Walks every trading day and rebalances when portfolio composition changes,
    a regime transition occurs, or an untradable ticker must be force-removed.
    Regime transitions use hysteresis: enter SPY regime when n_eligible <
    MIN_ELIGIBLE_STOCKS, exit SPY regime when n_eligible >= REENTRY_THRESHOLD.
    Untradable tickers are detected upfront and force-removed on T-1 (their last
    healthy day), then permanently excluded from T onward.

    Signal and traded-value rows are taken from T-1 (the previous row in the
    matrix), so every portfolio decision is based exclusively on data known
    before day T opens. The adjusted-close row is taken from T itself as a
    same-day tradability guard.

    Parameters
    ----------
    signal_df
        Date × ticker matrix of SMA crossover signals.
    tv_1d_df
        Date × ticker matrix of single-day traded value (liquidity floor).
    tv_63d_df
        Date × ticker matrix of 63-day average traded value (ranking / sizing).
    close_adj_df
        Date × ticker matrix of dividend-and-split-adjusted close prices.
    close_raw_df
        Date × ticker matrix of split-adjusted close prices.
    volume_df
        Date × ticker matrix of split-adjusted volume.

    Returns
    -------
        Mapping of rebalance date to portfolio weights indexed by ticker.
    """
    date_mask = (signal_df.index >= PORTFOLIO_START) & (signal_df.index <= PORTFOLIO_END)
    trading_dates = signal_df.index[date_mask]
    if trading_dates.empty:
        raise RuntimeError(
            f"No trading dates in [{PORTFOLIO_START.date()}, {PORTFOLIO_END.date()}]"
        )

    print(f"  Trading days: {len(trading_dates):,}")
    print(f"  Range:        {trading_dates[0].date()} → {trading_dates[-1].date()}")
    print(f"  SPY entry:    n_eligible < {MIN_ELIGIBLE_STOCKS}")
    print(f"  SPY exit:     n_eligible >= {REENTRY_THRESHOLD}")

    ticker_exclude_from, force_remove_on = detect_untradable_tickers(
        close_adj_df, close_raw_df, volume_df, trading_dates
    )

    # Convert to numpy arrays for performance; date_idx maps dates to row positions.
    sig_arr = signal_df.values
    tv_1d_arr = tv_1d_df.values
    tv_63d_arr = tv_63d_df.values
    close_arr = close_adj_df.values
    tickers = signal_df.columns.values
    date_idx = {trade_date: pos for pos, trade_date in enumerate(signal_df.index)}

    in_spy_regime = False
    prev_selected: frozenset | None = None
    prev_weights: pandas.Series | None = None
    portfolios: dict[pandas.Timestamp, pandas.Series] = {}
    spy_entries = 0
    n_delisting_rebals = 0

    for trade_date in trading_dates:
        row_pos = date_idx[trade_date]

        if row_pos == 0:
            # No prior row available; defer rebalance to next trading day.
            prev_selected = frozenset()
            continue

        # --- Timing: resolve which data rows to read ---
        sig_row = sig_arr[row_pos - 1]          # T-1 close signal
        tv_1d_row = tv_1d_arr[row_pos - 1]      # T-1 close (liquidity floor filter)
        tv_63d_row = tv_63d_arr[row_pos - 1]    # T-1 close (ranking and sizing)
        close_row = close_arr[row_pos]           # T close (tradability guard)

        force_removing_today = force_remove_on.get(trade_date, set())

        excluded: set[str] = set(force_removing_today)
        for tkr, exc_date in ticker_exclude_from.items():
            if trade_date >= exc_date:
                excluded.add(tkr)

        # --- Selection: filter eligible universe and pick top-N ---
        eligible_tkrs, eligible_tv_63d, n_eligible = _select_eligible_stocks(
            sig_row, tv_1d_row, tv_63d_row, close_row, excluded, tickers
        )
        current_selected = _pick_top_n(eligible_tkrs, eligible_tv_63d)

        # --- Regime: determine SPY vs stock (with hysteresis) ---
        should_spy = _determine_regime(n_eligible, in_spy_regime)
        if should_spy:
            current_selected = frozenset()

        # --- Timing: check composition / regime rebalance triggers ---
        need_rebalance = _needs_rebalance(
            prev_selected, current_selected, should_spy, in_spy_regime
        )

        if force_removing_today and not need_rebalance and prev_weights is not None:
            held_tickers = set(prev_weights.index)
            if force_removing_today & held_tickers:
                need_rebalance = True
                n_delisting_rebals += 1

        # --- Sizing: compute new weights on rebalance dates ---
        if need_rebalance:
            if should_spy:
                weights = pandas.Series({SPY_TICKER: 1.0})
                if not in_spy_regime:
                    spy_entries += 1
            else:
                weights = _compute_stock_weights(eligible_tkrs, eligible_tv_63d)
                if weights.empty:
                    weights = pandas.Series({SPY_TICKER: 1.0})
                    should_spy = True
                    if not in_spy_regime:
                        spy_entries += 1

            portfolios[trade_date] = weights
            prev_weights = weights

        prev_selected = current_selected
        in_spy_regime = should_spy

    print(f"  Rebalance events:          {len(portfolios):,}")
    print(f"  Delisting-forced rebal.:   {n_delisting_rebals:,}")
    print(f"  SPY regime entries:        {spy_entries:,}")

    return portfolios


# ==============================================================================
# 9. BUILD OUTPUT DATAFRAME
# ==============================================================================
def build_output(
    portfolios: dict[pandas.Timestamp, pandas.Series],
) -> pandas.DataFrame:
    """
    Build the output DataFrame with tickers as rows and rebalance dates as columns.

    Parameters
    ----------
    portfolios
        Mapping of rebalance date to portfolio weights indexed by ticker.

    Returns
    -------
        Rows are tickers (alphabetical), columns are rebalance dates as
        YYYY-MM-DD strings, values are weights rounded to 9 decimals.
        Always includes the SPY row and a leading Ticker index column.
    """
    all_tickers = sorted({tkr for weights in portfolios.values() for tkr in weights.index})
    sorted_dates = sorted(portfolios.keys())
    date_cols = [trade_date.strftime("%Y-%m-%d") for trade_date in sorted_dates]

    matrix = pandas.DataFrame(0.0, index=all_tickers, columns=date_cols)

    for trade_date, weights in portfolios.items():
        col = trade_date.strftime("%Y-%m-%d")
        for tkr, weight in weights.items():
            if tkr in matrix.index:
                matrix.loc[tkr, col] = weight

    if SPY_TICKER not in matrix.index:
        spy_row = pandas.DataFrame(0.0, index=[SPY_TICKER], columns=date_cols)
        matrix = pandas.concat([matrix, spy_row])
        matrix.sort_index(inplace=True)

    matrix = matrix.round(9)
    matrix.index.name = COL_TICKER
    return matrix.reset_index()


# ==============================================================================
# 10. SUMMARY
# ==============================================================================
def print_summary(
    portfolios: dict[pandas.Timestamp, pandas.Series],
    output_df: pandas.DataFrame,
    loaded: list[str],
    missing: list[str],
) -> None:
    """Print strategy diagnostics."""
    spy_only = [
        weights for weights in portfolios.values()
        if SPY_TICKER in weights.index and abs(weights[SPY_TICKER] - 1.0) < 1e-6
    ]
    stock_only = [
        weights for weights in portfolios.values()
        if not (SPY_TICKER in weights.index and abs(weights[SPY_TICKER] - 1.0) < 1e-6)
    ]

    avg_positions = numpy.mean([len(weights) for weights in stock_only]) if stock_only else 0
    max_weight_observed = max((weights.max() for weights in stock_only), default=0)

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Period:                {PORTFOLIO_START.date()} → {PORTFOLIO_END.date()}")
    print(f"  Tickers loaded:        {len(loaded)}")
    print(f"  Tickers missing:       {len(missing)}")
    print(f"  Rebalance events:      {len(portfolios):,}")
    print(f"  Unique tickers output: {output_df.shape[0]}")
    print()
    print(f"  Parameters:")
    print(f"    Max positions:       {MAX_POSITIONS}")
    print(f"    Max weight:          {MAX_WEIGHT:.0%}")
    print(f"    Min traded value:    ${MIN_DAILY_TRADED_VALUE:,.0f}")
    print(f"    SPY entry:           < {MIN_ELIGIBLE_STOCKS} eligible")
    print(f"    SPY exit:            >= {REENTRY_THRESHOLD} eligible")
    print()
    print(f"  100 % SPY rebalances:  {len(spy_only)}")
    print(f"  Stock-regime rebal.:   {len(stock_only)}")
    print(f"  Avg positions (stock): {avg_positions:.1f}")
    print(f"  Max weight observed:   {max_weight_observed:.6f}  (limit {MAX_WEIGHT})")
    print()

    spy_leak = sum(1 for weights in stock_only if SPY_TICKER in weights.index)
    if spy_leak:
        print(f"  ⚠  SPY appears in {spy_leak} stock-regime portfolios (unexpected)")
    else:
        print(f"  ✓  SPY only present in SPY-regime rebalances")

    bad_sums = [
        (trade_date, weights.sum())
        for trade_date, weights in portfolios.items()
        if abs(weights.sum() - 1.0) > 1e-4
    ]
    if bad_sums:
        print(f"  ⚠  {len(bad_sums)} rebalance(s) with weight sum ≠ 1.0")
    else:
        print(f"  ✓  All rebalance weights sum to 1.0")

    cap_violations = [
        (trade_date, weights.max())
        for trade_date, weights in portfolios.items()
        if weights.max() > MAX_WEIGHT + 1e-6
    ]
    if cap_violations:
        print(f"  ⚠  {len(cap_violations)} rebalance(s) exceed {MAX_WEIGHT:.0%} cap")
    else:
        print(f"  ✓  All weights within {MAX_WEIGHT:.0%} cap")

    print()
    preview_cols = [COL_TICKER] + list(output_df.columns[1:6])
    print("  Preview (first 10 tickers × first 5 dates):\n")
    print(output_df[preview_cols].head(10).to_string(index=False))
    print("\n" + "=" * 70)


# ==============================================================================
# 11. MAIN
# ==============================================================================

"""Run the full portfolio construction pipeline and write outputs to OUTPUT_DIR."""
print("=" * 70)
print("  LIQUIDITY-WEIGHTED TREND STRATEGY — Portfolio Construction")
print(f"  Period: {PORTFOLIO_START.date()} → {PORTFOLIO_END.date()}")
print("=" * 70)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\n[1] Loading data …")
data, loaded, missing = load_data()

print("\n[2] Validating features …")
validate_features(data)

print("\n[3] Building matrices …")
signal_df, tv_1d_df, tv_63d_df, close_adj_df, close_raw_df, volume_df = build_matrices(data)

print("\n[4] Constructing portfolios …")
portfolios = construct_portfolios(
    signal_df, tv_1d_df, tv_63d_df, close_adj_df, close_raw_df, volume_df
)

print("\n[5] Building output …")
output_df = build_output(portfolios)

out_path = OUTPUT_DIR / "portfolio_weights.csv"
output_df.to_csv(out_path, index=False)
print(f"  Saved: {out_path}")
print(f"  Shape: {output_df.shape[0]} tickers × {output_df.shape[1] - 1} dates")

if missing:
    pandas.DataFrame({"Ticker": missing, "status": "file_not_found"}).to_csv(
        OUTPUT_DIR / "missing_ticker_files.csv", index=False
    )
pandas.DataFrame({"Ticker": loaded, "status": "loaded"}).to_csv(
    OUTPUT_DIR / "loaded_ticker_files.csv", index=False
)

print_summary(portfolios, output_df, loaded, missing)
