# Data Curator — Income Statement Tags (fis_)

Source: `FundamentalDataRowIncomeStatement` in `entities/fundamental_data_row_income_statement.py`

| Tag                                                    | Python Type              |
|--------------------------------------------------------|--------------------------|
| `fis_basic_earnings_per_share`                         | `float | None`           |
| `fis_basic_net_income_available_to_common_stockholders`| `decimal.Decimal | None` |
| `fis_continuing_operations_income_after_tax`           | `decimal.Decimal | None` |
| `fis_costs_and_expenses`                               | `decimal.Decimal | None` |
| `fis_cost_of_revenue`                                  | `decimal.Decimal | None` |
| `fis_depreciation_and_amortization`                    | `decimal.Decimal | None` |
| `fis_diluted_earnings_per_share`                       | `float | None`           |
| `fis_discontinued_operations_income_after_tax`         | `decimal.Decimal | None` |
| `fis_earnings_before_interest_and_tax`                 | `decimal.Decimal | None` |
| `fis_earnings_before_interest_tax_depreciation_and_amortization` | `decimal.Decimal | None` |
| `fis_general_and_administrative_expense`               | `decimal.Decimal | None` |
| `fis_gross_profit`                                     | `decimal.Decimal | None` |
| `fis_income_before_tax`                                | `decimal.Decimal | None` |
| `fis_income_tax_expense`                               | `decimal.Decimal | None` |
| `fis_interest_expense`                                 | `decimal.Decimal | None` |
| `fis_interest_income`                                  | `decimal.Decimal | None` |
| `fis_net_income`                                       | `decimal.Decimal | None` |
| `fis_net_income_deductions`                            | `decimal.Decimal | None` |
| `fis_net_interest_income`                              | `decimal.Decimal | None` |
| `fis_net_total_other_income`                           | `decimal.Decimal | None` |
| `fis_nonoperating_income_excluding_interest`           | `decimal.Decimal | None` |
| `fis_operating_expenses`                               | `decimal.Decimal | None` |
| `fis_operating_income`                                 | `decimal.Decimal | None` |
| `fis_other_expenses`                                   | `decimal.Decimal | None` |
| `fis_other_net_income_adjustments`                     | `decimal.Decimal | None` |
| `fis_research_and_development_expense`                 | `decimal.Decimal | None` |
| `fis_revenues`                                         | `decimal.Decimal | None` |
| `fis_selling_and_marketing_expense`                    | `decimal.Decimal | None` |
| `fis_selling_general_and_administrative_expense`       | `decimal.Decimal | None` |
| `fis_weighted_average_basic_shares_outstanding`        | `int | None`             |
| `fis_weighted_average_diluted_shares_outstanding`      | `int | None`             |

**Frequency:** Quarterly/Annual, forward-filled to daily.
**Validation:** Shares outstanding must be non-negative.
