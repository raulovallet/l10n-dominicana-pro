{
    'name': "Fiscal POS (Rep. Dominicana)",
    'summary': """Incorpora funcionalidades de facturación con NCF al POS.""",
    'author': "Guavana, Indexa, Iterativo SRL",
    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '16.0.2.0.1',
    'depends': [
        'base',
        'point_of_sale',
        'l10n_do_accounting',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_config_settings_views.xml',
        'views/pos_order_views.xml',
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            '/l10n_do_pos/static/src/scss/*',
            
            '/l10n_do_pos/static/src/js/models.js',
            '/l10n_do_pos/static/src/js/PaymentScreen.js',
            '/l10n_do_pos/static/src/js/TicketScreen.js',
            '/l10n_do_pos/static/src/js/buttons/SetFiscalTypeButton.js',

            '/l10n_do_pos/static/src/xml/PaymentScreen.xml',
            '/l10n_do_pos/static/src/xml/SetFiscalTypeButton.xml',
            '/l10n_do_pos/static/src/xml/TicketScreen.xml',
        ],
    },
    'installable': True,
}
