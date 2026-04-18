---
name: kaxanuk_data_curator_custom_calculation_builder
description: >
  Build custom calculation functions for the KaxaNuk Data Curator library.
  Use this skill whenever the user wants to create, debug, or extend a custom
  calculation (c_ function) for Data Curator. Also trigger when the user
  mentions DataColumn, pyarrow-based financial indicators, Data Curator tags,
  column prefixes (m_, fbs_, fis_, fcf_, f_, d_, s_, c_), or asks what data
  is available for a calculation. This skill knows the DataColumn API, the
  full tag taxonomy, and the correct code patterns. It MUST be consulted before
  writing any Data Curator custom calculation code.
---

# Data Curator — Custom Calculation Builder

## Purpose
Turn Claude into an expert author for Data Curator. You must ensure clarity, validate inputs, and follow exact code patterns.

## Phase 0 — Target Location (MANDATORY)
**Before anything else**, ask the user where to place the new custom calculation inside `src_feature_engineering/`. Present the existing packages and their modules so the user can choose:

1. **Discover current packages dynamically**: List the subdirectories and `.py` files inside `src/data_curator/` at runtime (e.g. using `ls` or the Glob tool). Do **not** rely on a hardcoded list — new packages may be added at any time. Present the discovered packages and their modules to the user so they can choose.

2. **Ask the user**:
   - Which package does this calculation belong to? (or should a **new** package be created?)
   - Which Python module (file) inside that package? (existing file to append to, or a new file?)

3. **If a new package is needed**: you will create `src/data_curator/<new_package>/__init__.py` (empty) and the module file.

4. **If a new file is needed in an existing package**: confirm the file name with the user before proceeding.

Store the chosen **package** and **module path** for use in Phase 3.

## Phase 1 — Discovery Interview (MANDATORY)
**Before writing a single line of code**, ask these questions. You MUST read the relevant tag file(s) during this phase to help the user identify correct column names. Read only the file(s) that match the data the user needs:

- Market price/volume data → `references/tags_m.md`
- Balance sheet data → `references/tags_fbs.md`
- Income statement data → `references/tags_fis.md`
- Cash flow data → `references/tags_fcf.md`
- Filing metadata for all fundamentals (dates, fiscal period, currency) → `references/tags_f.md`
- Dividends → `references/tags_d.md`
- Split data (stock split events) → `references/tags_s.md`
- Built-in custom calculations → `references/tags_c.md`

1. **What does the indicator measure?** Get a description. Restate any formula to confirm.
2. **What input columns does it need?** Identify the correct tags in the relevant tag file(s). If multiple variants exist for a column (e.g. raw vs. split-adjusted vs. dividend-adjusted), list them all and ask the user to choose. Otherwise, pick the most obvious match and confirm it explicitly. (e.g., use `fis_revenues` instead of `fis_revenue`).
3. **Does it have a lookback window?** Define periods in daily rows.
4. **Does it depend on other custom calculations?** Scan `references/tags_c.md`.
5. **What should happen with nulls?** Default is null propagation.
6. **Output format?** Ratio, percentage, absolute value, or boolean?

## Phase 2 — Technical Validation
Using the same tag file routing as Phase 1, validate EVERY input column the user identified:

- **Strict Matching**: Verify each tag name character-by-character against the tag file. Use exactly what the tag file shows — the tag name IS the field name in the source code, including any apparent misspellings (e.g. `...investing_activites`). Do not correct them.
- **Missing Tags — HARD STOP**: If a required input tag does not appear in ANY tag file, do NOT invent a name, guess a similar name, or proceed to Phase 3. Instead, tell the user explicitly: which tag is missing, which file(s) you checked, and that the data is not available in Data Curator. Offer to suggest the closest available alternative if one exists, but never write code using a tag that was not found.
- **Frequency**: Confirm if mixing daily (`m_` columns) with fundamental (`fbs_`, `fis_`, `fcf_`, `f_`) data is intended. If so, note how fundamental alignment works:
  - Fundamental rows are indexed by **`filing_date`** (the date the report was publicly filed), NOT by `period_end_date`. This avoids lookahead bias — the data only becomes available on the day it was actually filed.
  - Each fundamental row is forward-filled across daily rows from its `filing_date` until the next filing arrives. Many consecutive daily rows will therefore share the same fundamental value.
  - **FY vs quarterly is a configuration choice** — a single Data Curator run fetches either annual (`FY`) or quarterly (`Q1–Q4`) data, never both. The `window_length` in `indexed_rolling_window_operation` counts unique filings: 4 means four quarters of quarterly data, or four years of annual data.

## Phase 3 — Implementation
You **MUST** follow the patterns and API defined below.

### DataColumn API (modules/data_column.py)
The `DataColumn` class wraps a `pyarrow.Array` and exposes these methods:

#### Construction & Export
| Method | Description |
|--------|-------------|
| `DataColumn(pyarrow_array)` | Direct constructor (internal use). |
| `DataColumn.load(data, dtype=None)` | Factory: wraps pyarrow.Array, pd.Series, iterable, or DataColumn. |
| `.to_pyarrow() -> pyarrow.Array` | Unwrap to native PyArrow array. |
| `.to_pandas() -> pandas.Series` | Convert to Pandas (ArrowExtensionArray backend). |
| `.type -> pyarrow.DataType` | Get underlying PyArrow type. |
| `column[i]` | Single-element DataColumn at index `i`. |
| `column[a:b]` | Sliced DataColumn (standard Python slice). Used in Pattern 2 for shifted arrays. |

#### Arithmetic Operators (Element-wise, Null-propagating)
| Operator | Dunder Methods | Notes |
|----------|----------------|-------|
| `+` | `__add__`, `__radd__` | Handles Decimal precision overflow. |
| `-` | `__sub__`, `__rsub__` | |
| `*` | `__mul__`, `__rmul__` | |
| `/` | `__truediv__`, `__rtruediv__` | True division (float result). |
| `//` | `__floordiv__`, `__rfloordiv__`| Floor division. |
| `%` | `__mod__`, `__rmod__` | Modulo. |
| `-x` | `__neg__` | Unary negation. |

#### Comparison & Logic
Comparison operators return a boolean `DataColumn` (element-wise, null-propagating):

| Operator | Dunder |
|----------|--------|
| `==` | `__eq__` |
| `!=` | `__ne__` |
| `>` | `__gt__` |
| `>=` | `__ge__` |
| `<` | `__lt__` |
| `<=` | `__le__` |

Additional class-level logic methods:

| Method | Description |
|--------|-------------|
| `.is_null() -> bool` | Returns `True` if the entire column is a null-type array (not element-wise). |
| `DataColumn.boolean_and(*columns, allow_null_comparisons=False)` | Element-wise AND across multiple DataColumns → boolean DataColumn. |
| `DataColumn.boolean_or(*columns, allow_null_comparisons=False)` | Element-wise OR across multiple DataColumns → boolean DataColumn. |

For PyArrow Compute operations, refer to the official docs: https://arrow.apache.org/docs/python/api/compute.html

### Implementation Patterns & The Contract

#### The Custom Calculation Contract
1. **Signature**: `def c_<name>(<tag_name>: DataColumn, ...) -> DataColumn:`
2. **Naming**: Function must start with `c_`. Parameters must be EXACT tags.
3. **Alignment**: Output length MUST equal input length.
4. **Kleene Logic**: If either operand is null, the result at that position is null.
5. **Padding**: Use `pyarrow.concat_arrays` to prepend `None` values for lookback windows.
6. **Return type**: The framework auto-wraps the return value into a DataColumn. You may return a `DataColumn`, `pandas.Series`, plain Python list, or any other pyarrow-compatible iterable. Prefer returning a `DataColumn` for clarity, but a `pandas.Series` is fine for calculations that naturally use pandas (e.g. `.rolling().mean()`).

#### Pattern 1: Rolling Window (Manual Loop)
Essential for logic not covered by `features/helpers.py`.

```python
def c_rolling_up_day_ratio_20d(m_close_split_adjusted: DataColumn) -> DataColumn:
    WINDOW = 20
    # 1. Convert to list for iteration
    values = m_close_split_adjusted.to_pyarrow().to_pylist()
    n = len(values)
    result = [None] * (WINDOW - 1)

    for i in range(WINDOW - 1, n):
        window_slice = values[i - WINDOW + 1 : i + 1]
        if any(v is None for v in window_slice):
            result.append(None)
            continue
        # --- Custom Logic Start ---
        up_days = sum(
            1 for j in range(1, WINDOW)
            if window_slice[j] > window_slice[j - 1]
        )
        computed_val = up_days / (WINDOW - 1)
        # --- Custom Logic End ---
        result.append(computed_val)

    output_array = pyarrow.array(result, type=pyarrow.float64())
    return DataColumn.load(output_array)
```

#### Pattern 2: DRY Helper (Parameterized)
```python
def _momentum_helper(prices: DataColumn, window: int) -> DataColumn:
    shifted_ratio = prices[window:] / prices[:-window]
    momentum_array = pyarrow.compute.subtract(shifted_ratio.to_pyarrow(), 1)

    output_array = pyarrow.concat_arrays([
        pyarrow.array([None] * window, type=momentum_array.type),
        momentum_array,
    ])
    return DataColumn.load(output_array)

def c_21d_momentum(m_close_split_adjusted: DataColumn):
    return _momentum_helper(m_close_split_adjusted, 21)
```

#### Pattern 3: Dependency Chaining
To use an existing `c_` calculation as input, declare it as a parameter by its exact function name. The framework computes it first and injects the result — no import needed.

```python
from kaxanuk.data_curator.features.helpers import simple_moving_average

# c_earnings_per_share is a built-in c_ calculation (see references/tags_c.md).
# Declare it as a parameter — the framework injects its output as a DataColumn.
# You can then pass it directly to any helper or use it in further arithmetic.
def c_earnings_per_share_sma_63d(
    c_earnings_per_share: DataColumn,
) -> DataColumn:
    return simple_moving_average(c_earnings_per_share, days=63)
```

The same applies to your own custom calculations: a `c_` function defined earlier in the same file can be declared as a parameter in a later function. The framework resolves the dependency order automatically.

### Templates & Library Helpers

#### Available Helper Functions
Import from `kaxanuk.data_curator.features.helpers`:
- `annualized_volatility(*, column, days)`
- `chaikin_money_flow(*, high, low, close, volume, days)`
- `exponential_moving_average(*, column, days)`
- `indexed_rolling_window_operation(*, key_column, value_column, operation_function, window_length)`
- `log_returns(column)`
- `relative_strength_index(*, column, days)`
- `replace_infinite_with_none(column)`
- `simple_moving_average(column, days)`

**When to use `indexed_rolling_window_operation` vs. a manual loop:**
Fundamental columns (`fbs_`, `fis_`, `fcf_`, `f_`) are filed once per period and then forward-filled across daily rows from their `filing_date`. Many consecutive daily rows therefore share the exact same value. A manual loop (Pattern 1) would treat each repeated daily row as a new data point and produce wrong rolling window results. Use `indexed_rolling_window_operation` instead — it detects unique periods by key, applies the rolling operation once per unique filing, then broadcasts the result back to all daily rows belonging to that filing. Use Pattern 1 only for daily market data (`m_` columns) or when every row is genuinely distinct.

`window_length` counts unique filings, not calendar days: `4` means the four most recent quarterly filings (one year of LTM) or the four most recent annual filings, depending on the user's configuration.

```python
from kaxanuk.data_curator.features.helpers import indexed_rolling_window_operation

def c_revenue_4q_sum(
    f_period_end_date: DataColumn,
    fis_revenues: DataColumn,
) -> DataColumn:
    return indexed_rolling_window_operation(
        key_column=f_period_end_date,
        value_column=fis_revenues,
        operation_function=lambda arr: arr.sum(),
        window_length=4,
    )
```

#### Standard Code Template
```python
"""
Module Description
"""
import pyarrow
import pyarrow.compute
from kaxanuk.data_curator.modules.data_column import DataColumn

def c_<name>(
    <input_tag>: DataColumn
) -> DataColumn:
    """
    Formula: ...

    Parameters
    ----------
    <input_tag> : DataColumn
        Description.

    Returns
    -------
    DataColumn
        Description.
    """
    # Logic goes here...
    # Note: you may also return a pandas.Series or plain list instead of
    # DataColumn.load(...) — the framework wraps any pyarrow-compatible iterable.
    return DataColumn.load(result_array)
```

#### Debugging Common Issues
- **All output is `None`**: Check that all input tag prefixes are enabled in the Excel configuration sheet. If a prefix is disabled, the column arrives as a null array.
- **Unexpected `None` spikes**: Division by zero is silently converted to `None` by the DataColumn operator. This is expected behavior.
- **Wrong values in fundamental rolling windows**: You are likely using Pattern 1 (manual loop) on forward-filled quarterly data. Switch to `indexed_rolling_window_operation` (see above).
- **Raising errors from custom code**: Import `from kaxanuk.data_curator.exceptions import CalculationError` and raise it for invalid inputs (e.g. incompatible column lengths).

#### Integration Checklist
1. **Custom Calc**: After confirming the code with the user, **always write it directly into the target module chosen in Phase 0** (inside `src/data_curator/<package>/<module>.py`) using your file editing tools. Do not just show the code in chat and tell the user to paste it. If the file already contains functions, append the new function at the end.
2. **Excel**: Remind the user to add the function name to the **Custom Calculations** sheet in `Config/parameters_datacurator.xlsx`.
3. **Enable Tags**: Remind the user to ensure all input tag prefixes are enabled in Excel.
4. **Run**: Remind the user to execute the data curator run for this project.

## After Generating Code
Always write the function directly to the file chosen in Phase 0 (inside `src/data_curator/`), then remind the user to complete steps 2–4 of the Integration Checklist above.
