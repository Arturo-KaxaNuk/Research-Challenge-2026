# Data Curator — Split Data Tags (s_)

Stock split event fields. Each row represents a single split event (identified
by `s_split_date`). The ratio is expressed as `s_numerator`:`s_denominator`
(e.g., 2:1 for a 2-for-1 split). Rows are expanded to daily by the column builder.

Source: `SplitDataRow` in `entities/split_data_row.py`

| Tag               | Python Type      |
|-------------------|------------------|
| `s_split_date`    | `datetime.date`  |
| `s_numerator`     | `float`          |
| `s_denominator`   | `float`          |

**Frequency:** Event-based (one row per split date), expanded to daily
by the column builder.
