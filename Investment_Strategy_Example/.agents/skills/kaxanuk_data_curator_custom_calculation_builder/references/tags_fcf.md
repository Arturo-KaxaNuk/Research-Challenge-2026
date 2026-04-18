# Data Curator — Cash Flow Tags (fcf_)

Source: `FundamentalDataRowCashFlow` in `entities/fundamental_data_row_cash_flow.py`

| Tag                                                          | Python Type              |
|--------------------------------------------------------------|--------------------------|
| `fcf_accounts_payable_change`                                | `decimal.Decimal | None` |
| `fcf_accounts_receivable_change`                             | `decimal.Decimal | None` |
| `fcf_capital_expenditure`                                    | `decimal.Decimal | None` |
| `fcf_cash_and_cash_equivalents_change`                       | `decimal.Decimal | None` |
| `fcf_cash_exchange_rate_effect`                              | `decimal.Decimal | None` |
| `fcf_common_stock_dividend_payments`                         | `decimal.Decimal | None` |
| `fcf_common_stock_issuance_proceeds`                         | `decimal.Decimal | None` |
| `fcf_common_stock_repurchase`                                | `decimal.Decimal | None` |
| `fcf_deferred_income_tax`                                    | `decimal.Decimal | None` |
| `fcf_depreciation_and_amortization`                          | `decimal.Decimal | None` |
| `fcf_dividend_payments`                                      | `decimal.Decimal | None` |
| `fcf_free_cash_flow`                                         | `decimal.Decimal | None` |
| `fcf_interest_payments`                                      | `decimal.Decimal | None` |
| `fcf_inventory_change`                                       | `decimal.Decimal | None` |
| `fcf_investment_sales_maturities_and_collections_proceeds`   | `decimal.Decimal | None` |
| `fcf_investments_purchase`                                   | `decimal.Decimal | None` |
| `fcf_net_business_acquisition_payments`                      | `decimal.Decimal | None` |
| `fcf_net_cash_from_operating_activities`                     | `decimal.Decimal | None` |
| `fcf_net_cash_from_investing_activites`                      | `decimal.Decimal | None` |
| `fcf_net_cash_from_financing_activities`                     | `decimal.Decimal | None` |
| `fcf_net_common_stock_issuance_proceeds`                     | `decimal.Decimal | None` |
| `fcf_net_debt_issuance_proceeds`                             | `decimal.Decimal | None` |
| `fcf_net_income`                                             | `decimal.Decimal | None` |
| `fcf_net_income_tax_payments`                                | `decimal.Decimal | None` |
| `fcf_net_longterm_debt_issuance_proceeds`                    | `decimal.Decimal | None` |
| `fcf_net_shortterm_debt_issuance_proceeds`                   | `decimal.Decimal | None` |
| `fcf_net_stock_issuance_proceeds`                            | `decimal.Decimal | None` |
| `fcf_other_financing_activities`                             | `decimal.Decimal | None` |
| `fcf_other_investing_activities`                             | `decimal.Decimal | None` |
| `fcf_other_noncash_items`                                    | `decimal.Decimal | None` |
| `fcf_other_working_capital`                                  | `decimal.Decimal | None` |
| `fcf_period_end_cash`                                        | `decimal.Decimal | None` |
| `fcf_period_start_cash`                                      | `decimal.Decimal | None` |
| `fcf_preferred_stock_dividend_payments`                      | `decimal.Decimal | None` |
| `fcf_preferred_stock_issuance_proceeds`                      | `decimal.Decimal | None` |
| `fcf_property_plant_and_equipment_purchase`                  | `decimal.Decimal | None` |
| `fcf_stock_based_compensation`                               | `decimal.Decimal | None` |
| `fcf_working_capital_change`                                 | `decimal.Decimal | None` |

**Note:** `fcf_net_cash_from_investing_activites` has a typo ("activites")
in the source code entity — use it exactly as-is, typo included.

**Frequency:** Quarterly/Annual, forward-filled to daily.
