# Data Curator — Built-in Custom Calculation Tags (c_)

Source: `features/calculations.py`

These are pre-built calculations that ship with Data Curator. They can be
used as inputs to your own custom `c_` functions (dependency chaining).

## Volatility
- `c_annualized_volatility_5d_log_returns_dividend_and_split_adjusted`
- `c_annualized_volatility_21d_log_returns_dividend_and_split_adjusted`
- `c_annualized_volatility_63d_log_returns_dividend_and_split_adjusted`
- `c_annualized_volatility_252d_log_returns_dividend_and_split_adjusted`

## Valuation Ratios
- `c_book_to_price` → needs: `fbs_assets`, `fbs_liabilities`, `fbs_preferred_stock_value`, `c_market_cap`
- `c_book_value_per_share` → needs: `fbs_assets`, `fbs_liabilities`, `fbs_preferred_stock_value`, `fis_weighted_average_basic_shares_outstanding`
- `c_earnings_per_share` → needs: `fis_net_income`, `fis_weighted_average_basic_shares_outstanding`
- `c_earnings_to_price`
- `c_market_cap` → needs: `m_close_split_adjusted`, `fis_weighted_average_diluted_shares_outstanding`
- `c_sales_to_price`

## Volume / Liquidity
- `c_daily_traded_value` → needs: `m_close`, `m_volume`
- `c_daily_traded_value_sma_5d` → needs: `c_daily_traded_value`
- `c_daily_traded_value_sma_21d` → needs: `c_daily_traded_value`
- `c_daily_traded_value_sma_63d` → needs: `c_daily_traded_value`
- `c_daily_traded_value_sma_252d` → needs: `c_daily_traded_value`
- `c_chaikin_money_flow_21d_dividend_and_split_adjusted`
- `c_chaikin_money_flow_21d_split_adjusted`

## Moving Averages
- `c_simple_moving_average_5d_close_dividend_and_split_adjusted`
- `c_simple_moving_average_5d_close_split_adjusted`
- `c_simple_moving_average_21d_close_dividend_and_split_adjusted`
- `c_simple_moving_average_21d_close_split_adjusted`
- `c_simple_moving_average_63d_close_dividend_and_split_adjusted`
- `c_simple_moving_average_63d_close_split_adjusted`
- `c_simple_moving_average_252d_close_dividend_and_split_adjusted`
- `c_simple_moving_average_252d_close_split_adjusted`
- `c_exponential_moving_average_5d_close_dividend_and_split_adjusted`
- `c_exponential_moving_average_5d_close_split_adjusted`
- `c_exponential_moving_average_21d_close_dividend_and_split_adjusted`
- `c_exponential_moving_average_21d_close_split_adjusted`
- `c_exponential_moving_average_63d_close_dividend_and_split_adjusted`
- `c_exponential_moving_average_63d_close_split_adjusted`
- `c_exponential_moving_average_252d_close_dividend_and_split_adjusted`
- `c_exponential_moving_average_252d_close_split_adjusted`

## Returns / Momentum
- `c_log_returns_dividend_and_split_adjusted`
- `c_log_difference_high_to_low`

## Revenue / Earnings (LTM)
- `c_last_twelve_months_net_income`
- `c_last_twelve_months_revenue`
- `c_last_twelve_months_revenue_per_share`

## Technical Indicators
- `c_macd_26d_12d_dividend_and_split_adjusted`
- `c_macd_26d_12d_split_adjusted`
- `c_macd_signal_9d_dividend_and_split_adjusted`
- `c_macd_signal_9d_split_adjusted`
- `c_rsi_14d_dividend_and_split_adjusted`
- `c_rsi_14d_split_adjusted`

