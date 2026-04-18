# Data Curator — Fundamental/Derived Tags (f_)

Source: `FundamentalDataRow` in `entities/fundamental_data_row.py`

| Tag                    | Python Type                    |
|------------------------|--------------------------------|
| `f_accepted_date`      | `datetime.datetime | None`     |
| `f_filing_date`        | `datetime.date`                |
| `f_fiscal_period`      | `str` (FY, Q1, Q2, Q3, Q4)    |
| `f_fiscal_year`        | `int`                          |
| `f_period_end_date`    | `datetime.date`                |
| `f_reported_currency`  | `str` (3-char ISO, e.g. USD)   |

**Important:** f_ tags contain filing-level metadata only (dates, period identifiers,
currency). They apply to ALL fundamental filings and are available alongside any
`fbs_`, `fis_`, or `fcf_` column. For financial statement data, use `fbs_`
(balance sheet), `fis_` (income statement), or `fcf_` (cash flow).
