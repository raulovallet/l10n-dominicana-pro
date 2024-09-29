# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('do', 'account.tax')
    def _get_do_info_account_tax(self):
        return {
            'tax_18_sale': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_18_sale_incl': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_18_of_10': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_tip_sale': {'l10n_do_tax_type': 'tip', 'isr_retention_type': False},
            'ret_5_income_gov': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '07'},
            'tax_tip_purch': {'l10n_do_tax_type': 'tip', 'isr_retention_type': False},
            'tax_18_purch': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_18_purch_incl': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_16_purch': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_16_purch_incl': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_9_purch': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_9_purch_incl': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_8_purch': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_8_purch_incl': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_18_purch_serv': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_18_purch_serv_incl': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_18_10_total_mount': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_18_property_cost': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'ret_10_income_person': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '02'},
            'ret_100_tax_person': {'l10n_do_tax_type': 'ritbis', 'isr_retention_type': False},
            'ret_100_tax_security': {'l10n_do_tax_type': 'ritbis', 'isr_retention_type': False},
            'tax_18_serv_cost': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'ret_10_income_rent': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '01'},
            'ret_10_income_dividend': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
            'ret_2_income_person': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
            'ret_2_income_transfer': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
            'tax_18_importation': {'l10n_do_tax_type': 'itbis', 'isr_retention_type': False},
            'tax_10_telco': {'l10n_do_tax_type': 'isc', 'isr_retention_type': False},
            'tax_2_telco': {'l10n_do_tax_type': 'other', 'isr_retention_type': False},
            'tax_0015_bank': {'l10n_do_tax_type': 'other', 'isr_retention_type': False},
            'ret_100_tax_nonprofit': {'l10n_do_tax_type': 'ritbis', 'isr_retention_type': False},
            'ret_30_tax_moral': {'l10n_do_tax_type': 'ritbis', 'isr_retention_type': False},
            'ret_75_tax_nonformal': {'l10n_do_tax_type': 'ritbis', 'isr_retention_type': False},
            'ret_27_income_remittance': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
        }


