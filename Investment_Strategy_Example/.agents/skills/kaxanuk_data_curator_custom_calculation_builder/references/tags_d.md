# Data Curator — Dividend Tags (d_)

Source: `DividendDataRow` in `entities/dividend_data_row.py`

| Tag                          | Python Type              |
|------------------------------|--------------------------|
| `d_declaration_date`         | `datetime.date | None`   |
| `d_ex_dividend_date`         | `datetime.date`          |
| `d_record_date`              | `datetime.date | None`   |
| `d_payment_date`             | `datetime.date | None`   |
| `d_dividend`                 | `decimal.Decimal`        |
| `d_dividend_split_adjusted`  | `decimal.Decimal | None` |

**Frequency:** Event-based (one row per ex-dividend date), expanded to daily
by the column builder.
