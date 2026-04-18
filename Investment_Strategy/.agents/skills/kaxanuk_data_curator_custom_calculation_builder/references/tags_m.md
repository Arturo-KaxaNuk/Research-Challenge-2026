# Data Curator — Market Data Tags (m_)

Source: `MarketDataDailyRow` in `entities/market_data_daily_row.py`

| Tag                                         | Python Type             |
|---------------------------------------------|-------------------------|
| `m_date`                                    | `datetime.date`         |
| `m_open`                                    | `decimal.Decimal | None`|
| `m_high`                                    | `decimal.Decimal | None`|
| `m_low`                                     | `decimal.Decimal | None`|
| `m_close`                                   | `decimal.Decimal | None`|
| `m_volume`                                  | `int | None`            |
| `m_vwap`                                    | `decimal.Decimal | None`|
| `m_open_split_adjusted`                     | `decimal.Decimal | None`|
| `m_high_split_adjusted`                     | `decimal.Decimal | None`|
| `m_low_split_adjusted`                      | `decimal.Decimal | None`|
| `m_close_split_adjusted`                    | `decimal.Decimal | None`|
| `m_volume_split_adjusted`                   | `int | None`            |
| `m_vwap_split_adjusted`                     | `decimal.Decimal | None`|
| `m_open_dividend_and_split_adjusted`        | `decimal.Decimal | None`|
| `m_high_dividend_and_split_adjusted`        | `decimal.Decimal | None`|
| `m_low_dividend_and_split_adjusted`         | `decimal.Decimal | None`|
| `m_close_dividend_and_split_adjusted`       | `decimal.Decimal | None`|
| `m_volume_dividend_and_split_adjusted`      | `int | None`            |
| `m_vwap_dividend_and_split_adjusted`        | `decimal.Decimal | None`|

**Frequency:** Daily. One row per trading day.
**Validation:** All numeric fields must be non-negative. Low ≤ High enforced
for each adjustment level.
