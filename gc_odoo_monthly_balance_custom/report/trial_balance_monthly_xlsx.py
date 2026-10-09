from itertools import groupby

from odoo import _, models

from .trial_balance_monthly import AMOUNT_FIELDS

AMOUNT_HEADERS = {"debit": "Debe", "credit": "Haber", "balance": "Saldo"}


class TrialBalanceMonthlyXslx(models.AbstractModel):
    _name = "report.gc_odoo_monthly_balance_custom.trial_balance_xlsx"
    _description = "Sumas y saldos mensual XLSX"
    _inherit = "report.a_f_r.report_trial_balance_xlsx"

    def _get_report_name(self, report, data=False):
        report_name = _("Sumas y saldos mensual")
        company = self.env["res.company"].browse(data.get("company_id", False))
        if company:
            report_name += " - {} - {}".format(company.name, company.currency_id.name)
        return report_name

    def _get_report_columns(self, report):
        monthly_report = self.env[
            "report.gc_odoo_monthly_balance_custom.trial_balance_monthly"
        ]
        columns = [
            {"header": _("Código"), "field": "code", "width": 10},
            {"header": _("Cuenta"), "field": "name", "width": 60},
            {
                "header": _("Saldo inicial"),
                "field": "initial_balance",
                "type": "amount",
                "width": 14,
            },
        ]
        periods = monthly_report._get_monthly_periods(report.date_from, report.date_to)
        for index, period in enumerate(periods):
            columns += [
                {
                    "header": _(AMOUNT_HEADERS[field]),
                    "field": monthly_report._get_monthly_field_name(index, field),
                    "type": "amount",
                    "width": 14,
                    "group": period["name"],
                }
                for field in AMOUNT_FIELDS
            ]
        columns += [
            {
                "header": _(AMOUNT_HEADERS[field]),
                "field": field,
                "type": "amount",
                "width": 14,
                "group": _("Total"),
            }
            for field in AMOUNT_FIELDS
        ]
        columns.append(
            {
                "header": _("Saldo final"),
                "field": "ending_balance",
                "type": "amount",
                "width": 14,
            }
        )
        return dict(enumerate(columns))

    def write_array_header(self, report_data):
        """Agrega una fila con el mes sobre sus columnas Debe / Haber / Saldo."""
        sheet = report_data["sheet"]
        row_pos = report_data["row_pos"]
        header_format = report_data["formats"]["format_header_center"]
        for group, columns in groupby(
            report_data["columns"].items(), key=lambda item: item[1].get("group")
        ):
            positions = [col_pos for col_pos, _column in columns]
            if group and len(positions) > 1:
                sheet.merge_range(
                    row_pos, positions[0], row_pos, positions[-1], group, header_format
                )
            else:
                for col_pos in positions:
                    sheet.write(row_pos, col_pos, group or "", header_format)
        report_data["row_pos"] += 1
        res = super().write_array_header(report_data)
        # Código y cuenta quedan fijos al desplazarse por los meses
        sheet.freeze_panes(report_data["row_pos"], 2)
        return res

    def _generate_report_content(self, workbook, report, data, report_data):
        res_data = self.env[
            "report.gc_odoo_monthly_balance_custom.trial_balance_monthly"
        ]._get_report_values(report, data)
        self.write_array_header(report_data)
        for balance in res_data["trial_balance"]:
            self.write_line_from_dict(balance, report_data)
