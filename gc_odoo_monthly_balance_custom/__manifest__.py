{
    'name': 'Sumas y Saldos Mensual',
    'version': '16.0.1.0.0',
    'summary': 'Sumas y saldos de OCA abierto por mes',
    'author': 'GauchoCode',
    'depends': ['account_financial_report'],
    'data': [
        "report/trial_balance_monthly.xml",
        "report/templates/trial_balance_monthly.xml",
        "wizard/trial_balance_monthly_wizard_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'gc_odoo_monthly_balance_custom/static/src/js/report_action.esm.js',
        ],
    },
    'installable': True,
    'license': 'AGPL-3',
}
