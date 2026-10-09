==========================================
gc_odoo_monthly_balance_custom
==========================================

Monthly Trial Balance (Sumas y saldos mensual) on top of the OCA
``account_financial_report`` Trial Balance.

------------------------------------------
Key Features
------------------------------------------

- New menu under Accounting > Reporting > OCA accounting reports, next to the Trial Balance.
- Same filters as the OCA Trial Balance.
- Shows on screen (with amounts linked to their journal items) or exports to XLSX the Debit / Credit / Balance columns for each month between the selected dates, plus initial balance, period totals and ending balance.
- Initial balance, totals and ending balance are the ones computed by the OCA report for the whole range.

------------------------------------------
Not supported
------------------------------------------

- Partner details, analytic grouping and foreign currency columns.

------------------------------------------
Tests
------------------------------------------

Run with ``--test-tags /gc_odoo_monthly_balance_custom``.
