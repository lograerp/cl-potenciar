{
    'name': 'Personalización de Reportes de Cuenta',
    'version': '16.0.3.1.0',
    'summary': 'Permite personalizar reportes de cuenta',
    'author': 'GauchoCode',
    'depends': ['account_financial_report','base','account'],
    'data': [
        "report/aged_partner_balance.xml",
        "views/res_partner.xml",
        "views/account_move_tree.xml",
        "report/report_aged_partner_balance_inherit.xml",
        "report/trial_balance_monthly.xml",
        "report/templates/trial_balance_monthly.xml",
        "wizard/trial_balance_monthly_wizard_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'gc_odoo_account_report_custom/static/src/js/report_action.esm.js',
        ],
    },
    'installable': True,
    'license': 'AGPL-3',
}
