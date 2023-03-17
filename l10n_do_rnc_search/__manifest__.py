# -*- coding: utf-8 -*-
{
    'name': "RNC DGII Search",

    'summary': """
      Buscador de RNC en DGII
          """,

    'description': """
         Buscador de RNC en DGII

         Este es un modulo bifurcado de https://github.com/AstraTechRD/l10n_do_rnc_search
         por tanto los derechos de creacion y agradecimientos de le atribuyen a su empresa
         matriz Astra Tech SRL y su creador @jeffryjdelarosa .

         Este modulo seguira obteniendo fix de su repositorio original y los fix o nuevas
         funcionaliades creadas por Neotec SRL seran enviadas por iguala  su repositorio original.
    """,

    'website': 'https://astratech.com.do',
    'author': 'Astra Tech SRL',
    'category': 'Localization',
    'version': '15.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_do_accounting'],

    'assets': {
        'web.assets_backend': [
            'l10n_do_rnc_search/static/src/js/l10n_do_accounting.js',
            'l10n_do_rnc_search/static/src/xml/l10n_do_accounting.xml'
        ]
    },

    # always loaded
    'data': [
        'data/ir_config_parameters.xml',
        'views/res_partner_views.xml',
    ],
    'auto_install': True,
    "license": "LGPL-3",

}
