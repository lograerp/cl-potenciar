/** @odoo-module **/
import {ReportAction} from "@web/webclient/actions/reports/report_action";
import {patch} from "web.utils";

const HTML_REPORT_NAME = "gc_odoo_account_report_custom.trial_balance_monthly";
const XLSX_REPORT_NAME = "gc_odoo_account_report_custom.trial_balance_monthly_xlsx";

// Habilita el botón "Export" de account_financial_report en el sumas y saldos
// mensual, que no sigue la convención de nombres de los reportes de OCA.
patch(ReportAction.prototype, "gc_odoo_account_report_custom.ReportAction", {
    setup() {
        this._super.apply(this, arguments);
        if (this.props.report_name === HTML_REPORT_NAME) {
            this.isAccountFinancialReport = true;
        }
    },

    /**
     * @param {String} str
     * @returns {String}
     */
    _get_xlsx_name(str) {
        if (str === HTML_REPORT_NAME) {
            return XLSX_REPORT_NAME;
        }
        return this._super.apply(this, arguments);
    },
});
