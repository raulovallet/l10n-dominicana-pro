# -*- coding: utf-8 -*-
# Modified by Jenrax SRL on 2025-01-30
{
    'name': 'Search RNC name',
    'summary': """
        This module searches for the company name by entering a Taxpayer Registration Number (RNC), if the company is valid.
    """,

    'description': """
        This module searches for the company name by entering a Taxpayer Registration Number (RNC), if the company is valid.
    """,
    'author': "Guavana",
    'website': "https://www.guavana.com",
    'license': 'LGPL-3',
    'category': 'Localization',
    'version': '16.0.1.1.1',
    'depends': [
        'base',
        'contacts',
        'l10n_do',
        'l10n_do_accounting',
        'base_vat'
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml"
    ],
    'installable': True,
}
