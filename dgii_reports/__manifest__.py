# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>
# © 2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Eneldo Serrata <eneldo@marcos.do>

{
    'name': "Declaraciones DGII",
    
    'summary': """
        Este módulo extiende las funcionalidades del l10n_do_accounting,
        integrando los reportes de declaraciones fiscales""",
    
    'author': "Indexa, SRL, Iterativo SRL",
    'license': 'LGPL-3',
    "category": "Localization",
    'version': '17.0.0.0.0',
    # any module necessary for this one to work correctly
    'depends': [
        'web',
        'account',
        'l10n_do',
        'l10n_do_accounting'
    ],
    
    # always loaded
    'data': [
        'data/invoice_service_type_detail_data.xml',
        # 'data/account_tax_data.xml',
        'data/action_server.xml',
        
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        
        'views/res_partner_views.xml',
        'views/account_account_views.xml',
        'views/account_invoice_views.xml',
        'views/dgii_report_views.xml',
        'views/account_tax_views.xml',
        'views/res_config_settings_views.xml',
        
        'wizard/dgii_report_regenerate_wizard_views.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
            'dgii_reports/static/src/scss/dgii_reports.scss',
            'dgii_reports/static/src/js/widget.js',
            'dgii_reports/static/src/js/custom_clipboard_value.js',
            'dgii_reports/static/src/js/percentage_copy_clipboard.js',
            'dgii_reports/static/src/xml/copy_clipboard_number_field.xml',
            'dgii_reports/static/src/xml/copy_clipboard_percentage.xml',
            'dgii_reports/static/src/xml/dgii_reports_widget_template.xml',
        ]
    },
    
    # 'post_init_hook': 'update_taxes'
}