from odoo import models


class TrialBalanceReportWizard(models.TransientModel):
    _inherit = "trial.balance.report.wizard"

    def _prepare_monthly_report_data(self):
        data = self._prepare_report_data()
        # El reporte mensual solo abre por cuenta (y grupo de cuentas)
        data.update(
            show_partner_details=False,
            foreign_currency=False,
            grouped_by=False,
        )
        return data

    def _export_monthly(self, report_xmlid):
        self.ensure_one()
        return self.env.ref(report_xmlid).report_action(
            self, data=self._prepare_monthly_report_data(), config=False
        )

    def button_export_monthly_html(self):
        return self._export_monthly(
            "gc_odoo_account_report_custom.action_report_trial_balance_monthly_html"
        )

    def button_export_monthly_xlsx(self):
        return self._export_monthly(
            "gc_odoo_account_report_custom.action_report_trial_balance_monthly_xlsx"
        )
