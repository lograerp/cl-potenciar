from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import date_utils, format_date

AMOUNT_FIELDS = ("debit", "credit", "balance")


class TrialBalanceMonthlyReport(models.AbstractModel):
    """Sumas y saldos de OCA con el debe / haber / saldo abierto por mes.

    El saldo inicial, los totales y el saldo final son los del reporte
    original para todo el rango; acá solo se agrega el detalle mensual.
    """

    _name = "report.gc_odoo_account_report_custom.trial_balance_monthly"
    _description = "Sumas y saldos mensual"
    _inherit = "report.account_financial_report.trial_balance"

    @api.model
    def _get_monthly_field_name(self, index, field):
        return "m%d_%s" % (index, field)

    @api.model
    def _get_monthly_periods(self, date_from, date_to):
        """Parte el rango en meses calendario, recortados al desde / hasta."""
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        periods = []
        while date_from <= date_to:
            period_end = min(date_utils.end_of(date_from, "month"), date_to)
            periods.append(
                {
                    "name": format_date(
                        self.env, date_from, date_format="MMMM yyyy"
                    ).capitalize(),
                    "date_from": date_from,
                    "date_to": period_end,
                }
            )
            date_from = period_end + relativedelta(days=1)
        return periods

    def _get_monthly_amounts(self, data, periods):
        """Devuelve, por período, {account_id: {debit, credit, balance}}."""
        monthly_amounts = []
        for period in periods:
            domain = self._get_period_ml_domain(
                data["account_ids"],
                data["journal_ids"],
                data["partner_ids"],
                data["company_id"],
                period["date_to"],
                period["date_from"],
                data["only_posted_moves"],
                data["show_partner_details"],
            )
            groups = self.env["account.move.line"].read_group(
                domain=domain,
                fields=["account_id", *AMOUNT_FIELDS],
                groupby=["account_id"],
            )
            monthly_amounts.append({group["account_id"][0]: group for group in groups})
        return monthly_amounts

    def _get_report_values(self, docids, data):
        res = super()._get_report_values(docids, data)
        periods = self._get_monthly_periods(data["date_from"], data["date_to"])
        monthly_amounts = self._get_monthly_amounts(data, periods)
        for line in res["trial_balance"]:
            if line["type"] == "group_type":
                account_ids = line["account_ids"]
            else:
                account_ids = [line["id"]]
            for index, amounts in enumerate(monthly_amounts):
                for field in AMOUNT_FIELDS:
                    line[self._get_monthly_field_name(index, field)] = sum(
                        amounts[account_id][field]
                        for account_id in account_ids
                        if account_id in amounts
                    )
        res["periods"] = periods
        res["monthly_field_name"] = self._get_monthly_field_name
        if res["show_hierarchy"] and res["limit_hierarchy_level"]:
            res["trial_balance"] = self._filter_hierarchy_level(
                res["trial_balance"],
                res["show_hierarchy_level"],
                res["hide_parent_hierarchy_level"],
            )
        return res

    def _filter_hierarchy_level(self, lines, level, hide_parent_levels):
        """Mismo criterio que el sumas y saldos original para limitar niveles."""
        return [
            line
            for line in lines
            if level > line["level"]
            and (not hide_parent_levels or level - 1 == line["level"])
        ]
