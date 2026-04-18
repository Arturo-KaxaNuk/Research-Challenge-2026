"""
Liquidity-Weighted Trend Strategy — Portfolio Construction
==========================================================

Rules (from S03 Portfolio Construction & Strategy Modeling)
-----------------------------------------------------------

**Selection:**
    - Securities with ``c_sma_50d_200d_signal == 1`` are eligible.
    - Rank eligible securities by ``c_daily_traded_value_63d`` (descending).
    - Select the top 35 securities.

**Sizing:**
    - Weights are proportional to traded value among selected securities.
    - Maximum 20 % weight per position.
    - Excess weight is redistributed proportionally.

**Market Regime Handling:**
    - If fewer than ``MIN_ELIGIBLE_STOCKS`` (default 35) stocks are eligible,
      invest 100 % in SPY ETF.
    - Exit the SPY regime when eligible stocks >= ``REENTRY_THRESHOLD``
      (configurable) to avoid excessive rebalancing.

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

**Rebalancing (event-driven):**
    Rebalance when any of the following occurs:
        * A security enters the top-35.
        * A security exits the top-35.
        * Transition into / out of SPY-only regime.
        * A held constituent becomes untradable (rebalance on T-1).

**Output:**
    - Rows = tickers (alphabetical).
    - Columns = rebalance dates only.
    - Values = portfolio weights (rounded to 9 decimals).
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ==============================================================================
# PATHS
# ==============================================================================
DATA_DIR = Path(r"Data_Curator")
CONFIG_DIR = Path(r"Config")
OUTPUT_DIR = Path(r"Portfolio_Construction")

# ==============================================================================
# STRATEGY PARAMETERS
# ==============================================================================
MAX_POSITIONS = 10
MAX_WEIGHT = 0.20
SPY_TICKER = "SPY"

MIN_ELIGIBLE_STOCKS = 35   # Below this → 100 % SPY
REENTRY_THRESHOLD = 40     # Must reach this to EXIT SPY regime

COL_DATE = "m_date"
COL_TICKER = "Ticker"
COL_SIGNAL = "c_sma_50d_200d_signal"
COL_TRADED_VALUE = "c_daily_traded_value_63d"
COL_CLOSE = "m_close_dividend_and_split_adjusted"
COL_CLOSE_RAW = "m_close_split_adjusted"
COL_VOLUME = "m_volume_split_adjusted"

# Delisting / untradable detection parameters
DELIST_LOOKBACK_DAYS = 21       # trailing window size (trading days)
DELIST_MISSING_THRESHOLD = 0.3  # if >= 30 % of days missing → untradable

PORTFOLIO_START = pd.Timestamp("2015-01-01")
PORTFOLIO_END = pd.Timestamp("2026-01-31")


# ==============================================================================
# 1. DATA LOADING
# ==============================================================================
def _read_config_tickers():
    """Read ticker universe from the config Excel file (all sheets)."""
    path = CONFIG_DIR / "parameters_datacurator.xlsx"
    if not path.exists():
        return []
    try:
        xls = pd.ExcelFile(path)
        tickers, seen = [], set()
        for sheet in xls.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            for col in df.columns:
                for val in df[col].dropna().astype(str):
                    tkr = val.strip().split()[0]
                    if (tkr
                            and tkr not in seen
                            and not tkr.replace(".", "").replace("-", "").isdigit()
                            and len(tkr) <= 10):
                        tickers.append(tkr)
                        seen.add(tkr)
        print(f"  Config tickers: {len(tickers)}")
        return tickers
    except Exception:
        return []


def load_data():
    """Load all ticker CSVs from DATA_DIR and return a single long DataFrame."""
    csv_paths = {p.stem: p for p in sorted(DATA_DIR.glob("*.csv"))}
    print(f"  CSV files found: {len(csv_paths)}")

    config_tickers = _read_config_tickers()
    if config_tickers:
        tickers_to_load = [t for t in config_tickers if t in csv_paths]
        missing = [t for t in config_tickers if t not in csv_paths]
        if not tickers_to_load:
            print("  WARNING: No config tickers matched — loading all CSVs.")
            tickers_to_load = list(csv_paths.keys())
            missing = []
    else:
        tickers_to_load = list(csv_paths.keys())
        missing = []

    frames, loaded = [], []
    for i, tkr in enumerate(sorted(tickers_to_load)):
        try:
            df = pd.read_csv(csv_paths[tkr])
            if i == 0:
                print(f"  Sample: {tkr}.csv | Cols: {len(df.columns)} | Rows: {len(df)}")
            df[COL_TICKER] = tkr
            frames.append(df)
            loaded.append(tkr)
        except Exception as exc:
            print(f"  ERROR {tkr}.csv: {exc}")
            missing.append(tkr)

    if not frames:
        raise RuntimeError("No data loaded.")

    data = pd.concat(frames, ignore_index=True)

    # Normalise date column
    if COL_DATE not in data.columns:
        for c in data.columns:
            if "date" in c.lower():
                data.rename(columns={c: COL_DATE}, inplace=True)
                break

    data[COL_DATE] = pd.to_datetime(data[COL_DATE], format="mixed", dayfirst=False)
    data.sort_values([COL_DATE, COL_TICKER], inplace=True)
    data.reset_index(drop=True, inplace=True)

    print(f"  Loaded: {len(loaded)} tickers | Missing: {len(missing)}")
    print(f"  Total rows: {len(data):,}")
    print(f"  Date range: {data[COL_DATE].min().date()} → {data[COL_DATE].max().date()}")

    return data, loaded, missing


# ==============================================================================
# 2. FEATURE VALIDATION
# ==============================================================================
def validate_features(data):
    """Ensure the required columns exist and contain data."""
    required = [
        (COL_SIGNAL, "Signal"),
        (COL_TRADED_VALUE, "Traded-value"),
        (COL_CLOSE, "Close price (adjusted)"),
        (COL_CLOSE_RAW, "Close price (raw)"),
        (COL_VOLUME, "Volume"),
    ]
    for col, label in required:
        if col not in data.columns:
            raise ValueError(
                f"{label} column '{col}' not found.  Available: {sorted(data.columns)}"
            )
        n = data[col].notna().sum()
        if n == 0:
            raise ValueError(f"{label} column '{col}' has no valid data.")
        print(f"  {label}: '{col}' ({n:,} non-null)")


# ==============================================================================
# 3. BUILD PIVOT MATRICES  (date × ticker)
# ==============================================================================
def build_matrices(data):
    """Pivot to aligned signal, traded-value, close, raw-close, and volume matrices."""
    print("  Building matrices …")

    pivot_specs = [
        (COL_SIGNAL, "signal"),
        (COL_TRADED_VALUE, "traded_value"),
        (COL_CLOSE, "close_adj"),
        (COL_CLOSE_RAW, "close_raw"),
        (COL_VOLUME, "volume"),
    ]

    pivots = {}
    for col, key in pivot_specs:
        pivots[key] = data.pivot_table(
            index=COL_DATE, columns=COL_TICKER, values=col, aggfunc="last"
        ).sort_index()

    # Align on the union of all dates and tickers
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
        pivots["traded_value"],
        pivots["close_adj"],
        pivots["close_raw"],
        pivots["volume"],
    )


# ==============================================================================
# 4. WEIGHT HELPERS
# ==============================================================================
def _cap_and_redistribute(weights: pd.Series, cap: float) -> pd.Series:
    """Iteratively cap at `cap` and redistribute excess proportionally."""
    w = weights.copy()
    for _ in range(100):
        over = w > cap
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        under = (w > 0) & (~over)
        if under.sum() == 0 or w[under].sum() == 0:
            break
        w[under] += excess * w[under] / w[under].sum()
    return w.clip(upper=cap)


def _compute_stock_weights(eligible_tickers, traded_values):
    """
    Selection + Sizing (stock regime only):
      1. Rank eligible by traded value descending
      2. Keep top MAX_POSITIONS (35)
      3. Weight ∝ traded value
      4. Cap at MAX_WEIGHT (20 %), redistribute excess
    Returns pd.Series of weights (sums to 1) or empty Series.
    """
    tv = traded_values.reindex(eligible_tickers).dropna()
    tv = tv[tv > 0].sort_values(ascending=False)

    if tv.empty:
        return pd.Series(dtype=float)

    selected = tv.head(MAX_POSITIONS)
    raw = selected / selected.sum()
    capped = _cap_and_redistribute(raw, MAX_WEIGHT)
    capped = capped / capped.sum()
    return capped[capped > 1e-10]


# ==============================================================================
# 5. DELISTING / UNTRADABLE DETECTION
# ==============================================================================
def detect_untradable_tickers(close_adj_df, close_raw_df, volume_df, trading_dates):
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

    Parameters
    ----------
    close_adj_df : pd.DataFrame
        Date x ticker matrix of dividend-and-split-adjusted close prices.
    close_raw_df : pd.DataFrame
        Date x ticker matrix of split-adjusted (raw) close prices.
    volume_df : pd.DataFrame
        Date x ticker matrix of split-adjusted volume.
    trading_dates : pd.DatetimeIndex
        Dates within the backtest window.

    Returns
    -------
    ticker_exclude_from : dict[str, pd.Timestamp]
        ``{ticker: first_date_to_EXCLUDE}``
    force_remove_on : dict[pd.Timestamp, set[str]]
        ``{date: set_of_tickers}`` — forced rebalance dates.
    """
    # Restrict to backtest trading dates
    raw_arr = close_raw_df.reindex(index=trading_dates).values
    vol_arr = volume_df.reindex(index=trading_dates).values
    adj_arr = close_adj_df.reindex(index=trading_dates).values
    tickers = close_raw_df.columns.values
    n_dates = len(trading_dates)

    # good_day = has valid raw close AND volume > 0
    good_day = (
        np.isfinite(raw_arr) & (raw_arr > 0)
        & np.isfinite(vol_arr) & (vol_arr > 0)
    )

    # has_adj = has valid adjusted close
    has_adj = np.isfinite(adj_arr) & (adj_arr > 0)

    ticker_exclude_from = {}
    force_remove_on = {}

    for j, tkr in enumerate(tickers):
        if tkr == SPY_TICKER:
            continue

        # Skip tickers with no adjusted close data at all
        if not has_adj[:, j].any():
            continue

        # Walk forward to find the first unhealthy date
        first_bad_idx = None
        for i in range(n_dates):
            # Check 1: no adjusted close → immediately bad
            if not has_adj[i, j]:
                first_bad_idx = i
                break

            # Check 2: trailing window health
            if i >= DELIST_LOOKBACK_DAYS - 1:
                window = good_day[i - DELIST_LOOKBACK_DAYS + 1: i + 1, j]
                missing_frac = 1.0 - window.mean()
                if missing_frac >= DELIST_MISSING_THRESHOLD:
                    first_bad_idx = i
                    break

        if first_bad_idx is None:
            continue  # ticker is healthy throughout the backtest

        exclude_date = trading_dates[first_bad_idx]

        if first_bad_idx > 0:
            remove_date = trading_dates[first_bad_idx - 1]
        else:
            # Bad from the very first day — just exclude, no forced rebalance
            ticker_exclude_from[tkr] = exclude_date
            continue

        ticker_exclude_from[tkr] = exclude_date
        force_remove_on.setdefault(remove_date, set()).add(tkr)

    # ── Report ──
    if ticker_exclude_from:
        print(f"  Untradable tickers detected: {len(ticker_exclude_from)}")
        for tkr in sorted(ticker_exclude_from):
            exc = ticker_exclude_from[tkr].date()
            rm = "N/A"
            for dt, tks in force_remove_on.items():
                if tkr in tks:
                    rm = dt.date()
                    break
            print(f"    {tkr}: exclude from {exc}, force-remove on {rm}")
    else:
        print(f"  Untradable tickers detected: 0")

    if force_remove_on:
        print(f"  Force-remove rebalance dates: {len(force_remove_on)}")
        for dt in sorted(force_remove_on):
            print(f"    {dt.date()}: remove {sorted(force_remove_on[dt])}")

    return ticker_exclude_from, force_remove_on


# ==============================================================================
# 6. EVENT-DRIVEN PORTFOLIO CONSTRUCTION
# ==============================================================================
def construct_portfolios(signal_df, tv_df, close_adj_df, close_raw_df, volume_df):
    """
    Walk every trading day in [PORTFOLIO_START, PORTFOLIO_END].

    Regime:
      • n_eligible < MIN_ELIGIBLE_STOCKS  →  SPY regime  (100 % SPY)
      • n_eligible >= REENTRY_THRESHOLD   →  stock regime

    Rebalancing triggers:
      • First trading day
      • Regime transition (SPY ↔ stocks)
      • Top-35 composition change
      • A held constituent is becoming untradable → forced rebalance on T-1

    Untradable handling:
      • Detected upfront via trailing-window health check on raw close & volume
      • Force-removed on the last healthy day (T-1)
      • Permanently excluded from the exclude date (T) onward
    """
    mask = (signal_df.index >= PORTFOLIO_START) & (signal_df.index <= PORTFOLIO_END)
    trading_dates = signal_df.index[mask]
    if trading_dates.empty:
        raise RuntimeError(
            f"No trading dates in [{PORTFOLIO_START.date()}, {PORTFOLIO_END.date()}]"
        )

    print(f"  Trading days: {len(trading_dates):,}")
    print(f"  Range:        {trading_dates[0].date()} → {trading_dates[-1].date()}")
    print(f"  SPY entry:    n_eligible < {MIN_ELIGIBLE_STOCKS}")
    print(f"  SPY exit:     n_eligible >= {REENTRY_THRESHOLD}")

    # ── Untradable detection (runs once upfront) ──
    ticker_exclude_from, force_remove_on = detect_untradable_tickers(
        close_adj_df, close_raw_df, volume_df, trading_dates
    )

    # Numpy arrays for speed
    sig_arr = signal_df.values
    tv_arr = tv_df.values
    close_arr = close_adj_df.values
    tickers = signal_df.columns.values
    date_idx = {d: i for i, d in enumerate(signal_df.index)}

    # State
    in_spy_regime = False
    prev_selected: frozenset | None = None
    prev_weights: pd.Series | None = None
    portfolios: dict[pd.Timestamp, pd.Series] = {}
    spy_entries = 0
    n_delisting_rebals = 0

    for dt in trading_dates:
        i = date_idx[dt]
        sig_row = sig_arr[i]
        tv_row = tv_arr[i]
        close_row = close_arr[i]

        # ── Tickers being force-removed today (their last healthy day) ──
        force_removing_today = force_remove_on.get(dt, set())

        # ── Build excluded set: already dead + being removed today ──
        excluded = set(force_removing_today)
        for tkr, exc_date in ticker_exclude_from.items():
            if dt >= exc_date:
                excluded.add(tkr)

        # ── Eligible stocks ──
        eligible_mask = (
            (sig_row == 1)
            & np.isfinite(tv_row)
            & (tv_row > 0)
            & np.isfinite(close_row)
            & (close_row > 0)
            & (tickers != SPY_TICKER)
        )
        if excluded:
            exclude_mask = np.isin(tickers, list(excluded))
            eligible_mask = eligible_mask & ~exclude_mask

        eligible_tkrs = tickers[eligible_mask]
        eligible_tv = tv_row[eligible_mask]
        n_eligible = len(eligible_tkrs)

        # ── Regime decision (with hysteresis) ──
        if in_spy_regime:
            should_spy = n_eligible < REENTRY_THRESHOLD
        else:
            should_spy = n_eligible < MIN_ELIGIBLE_STOCKS

        # ── Current top-N selection ──
        if should_spy:
            current_selected = frozenset()
        elif n_eligible >= MAX_POSITIONS:
            top_idx = np.argsort(-eligible_tv)[:MAX_POSITIONS]
            current_selected = frozenset(eligible_tkrs[top_idx])
        else:
            current_selected = frozenset(eligible_tkrs)

        # ── Do we need to rebalance? ──
        need_rebalance = False
        if prev_selected is None:
            need_rebalance = True                              # first day
        elif should_spy != in_spy_regime:
            need_rebalance = True                              # regime switch
        elif not should_spy and current_selected != prev_selected:
            need_rebalance = True                              # composition change

        # ── Force rebalance if a held ticker is being removed today ──
        if force_removing_today and not need_rebalance and prev_weights is not None:
            held_tickers = set(prev_weights.index)
            if force_removing_today & held_tickers:
                need_rebalance = True
                n_delisting_rebals += 1

        # ── Compute weights ──
        if need_rebalance:
            if should_spy:
                weights = pd.Series({SPY_TICKER: 1.0})
                if not in_spy_regime:
                    spy_entries += 1
            else:
                weights = _compute_stock_weights(
                    eligible_tkrs,
                    pd.Series(eligible_tv, index=eligible_tkrs),
                )
                if weights.empty:
                    weights = pd.Series({SPY_TICKER: 1.0})
                    should_spy = True
                    if not in_spy_regime:
                        spy_entries += 1

            portfolios[dt] = weights
            prev_weights = weights

        # ── Update state ──
        prev_selected = current_selected
        in_spy_regime = should_spy

    print(f"  Rebalance events:          {len(portfolios):,}")
    print(f"  Delisting-forced rebal.:   {n_delisting_rebals:,}")
    print(f"  SPY regime entries:        {spy_entries:,}")

    return portfolios


# ==============================================================================
# 7. BUILD OUTPUT DATAFRAME
# ==============================================================================
def build_output(portfolios):
    """
    Output format:
      • Rows    = tickers (alphabetical)
      • Columns = rebalance dates only (YYYY-MM-DD strings)
      • Values  = portfolio weights rounded to 9 decimals
    """
    all_tickers = sorted({t for w in portfolios.values() for t in w.index})
    sorted_dates = sorted(portfolios.keys())
    date_cols = [d.strftime("%Y-%m-%d") for d in sorted_dates]

    matrix = pd.DataFrame(0.0, index=all_tickers, columns=date_cols)

    for dt, weights in portfolios.items():
        col = dt.strftime("%Y-%m-%d")
        for tkr, wt in weights.items():
            if tkr in matrix.index:
                matrix.loc[tkr, col] = wt

    # Guarantee SPY row exists
    if SPY_TICKER not in matrix.index:
        spy_row = pd.DataFrame(0.0, index=[SPY_TICKER], columns=date_cols)
        matrix = pd.concat([matrix, spy_row])
        matrix.sort_index(inplace=True)

    matrix = matrix.round(9)
    matrix.index.name = COL_TICKER
    return matrix.reset_index()


# ==============================================================================
# 8. SUMMARY
# ==============================================================================
def print_summary(portfolios, output_df, loaded, missing):
    """Print strategy diagnostics."""
    spy_only = [
        w for w in portfolios.values()
        if SPY_TICKER in w.index and abs(w[SPY_TICKER] - 1.0) < 1e-6
    ]
    stock_only = [
        w for w in portfolios.values()
        if not (SPY_TICKER in w.index and abs(w[SPY_TICKER] - 1.0) < 1e-6)
    ]

    avg_pos = np.mean([len(w) for w in stock_only]) if stock_only else 0
    max_wt = max((w.max() for w in stock_only), default=0)

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
    print(f"    SPY entry:           < {MIN_ELIGIBLE_STOCKS} eligible")
    print(f"    SPY exit:            >= {REENTRY_THRESHOLD} eligible")
    print()
    print(f"  100 % SPY rebalances:  {len(spy_only)}")
    print(f"  Stock-regime rebal.:   {len(stock_only)}")
    print(f"  Avg positions (stock): {avg_pos:.1f}")
    print(f"  Max weight observed:   {max_wt:.6f}  (limit {MAX_WEIGHT})")
    print()

    # SPY leak check
    spy_leak = sum(1 for w in stock_only if SPY_TICKER in w.index)
    if spy_leak:
        print(f"  ⚠  SPY appears in {spy_leak} stock-regime portfolios (unexpected)")
    else:
        print(f"  ✓  SPY only present in SPY-regime rebalances")

    # Weight-sum check
    bad_sums = [(d, w.sum()) for d, w in portfolios.items() if abs(w.sum() - 1.0) > 1e-4]
    if bad_sums:
        print(f"  ⚠  {len(bad_sums)} rebalance(s) with weight sum ≠ 1.0")
    else:
        print(f"  ✓  All rebalance weights sum to 1.0")

    # Cap check
    cap_violations = [
        (d, w.max()) for d, w in portfolios.items() if w.max() > MAX_WEIGHT + 1e-6
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
# 9. MAIN
# ==============================================================================
def run():
    print("=" * 70)
    print("  LIQUIDITY-WEIGHTED TREND STRATEGY — Portfolio Construction")
    print(f"  Period: {PORTFOLIO_START.date()} → {PORTFOLIO_END.date()}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1 — Load
    print("\n[1] Loading data …")
    data, loaded, missing = load_data()

    # 2 — Validate
    print("\n[2] Validating features …")
    validate_features(data)

    # 3 — Matrices
    print("\n[3] Building matrices …")
    signal_df, tv_df, close_adj_df, close_raw_df, volume_df = build_matrices(data)

    # 4 — Construct
    print("\n[4] Constructing portfolios …")
    portfolios = construct_portfolios(
        signal_df, tv_df, close_adj_df, close_raw_df, volume_df
    )

    # 5 — Output
    print("\n[5] Building output …")
    output_df = build_output(portfolios)

    # 6 — Save
    out_path = OUTPUT_DIR / "portfolio_weights.csv"
    output_df.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")
    print(f"  Shape: {output_df.shape[0]} tickers × {output_df.shape[1] - 1} dates")

    # 7 — Auxiliary reports
    if missing:
        pd.DataFrame({"Ticker": missing, "status": "file_not_found"}).to_csv(
            OUTPUT_DIR / "missing_ticker_files.csv", index=False
        )
    pd.DataFrame({"Ticker": loaded, "status": "loaded"}).to_csv(
        OUTPUT_DIR / "loaded_ticker_files.csv", index=False
    )

    # 8 — Summary
    print_summary(portfolios, output_df, loaded, missing)

    return output_df


if __name__ == "__main__":
    run()