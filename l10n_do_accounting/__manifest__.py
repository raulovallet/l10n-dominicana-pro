# -*- coding: utf-8 -*-
{
    'name': 'Fiscal Accounting (Rep. Dominicana)',
    'version': '17.0.0.2', #"version": "16.0.2.0.9",
    'summary': """"Este módulo implementa la administración y gestión de los números de
        comprobantes fiscales para el cumplimento de la norma 06-18 de la
        Dirección de Impuestos Internos en la República Dominicana.""",
    'description': """Este módulo implementa la administración y gestión de los números de
        comprobantes fiscales para el cumplimento de la norma 06-18 de la
        Dirección de Impuestos Internos en la República Dominicana.""",
    'author': 'Marcos, Guavana, Indexa, Iterativo SRL, Neotec',
    'category': 'Localization',
    'website': 'https://github.com/odoo-dominicana',
    'depends': ['base', 'web', 'account', 'l10n_do'],
    'data': [
        'data/ir_config_parameters.xml',
        'data/ir_cron_data.xml',
        'data/account_fiscal_type_data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'wizard/account_fiscal_sequence_validate_wizard_views.xml',
        'wizard/account_invoice_refund_views.xml',

        'views/account_invoice_views.xml',
        'views/account_journal_views.xml',
        'views/res_partner_views.xml',
        'views/account_fiscal_sequence_views.xml',
        'views/res_company_views.xml',
        'views/account_invoice_cancel_views.xml',

        'views/report_templates.xml',
        'views/report_invoice.xml',
        'views/layouts.xml',

    ],
    'demo': [
        'demo/res_partner_demo.xml',
        'demo/account_fiscal_sequence_demo.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}

