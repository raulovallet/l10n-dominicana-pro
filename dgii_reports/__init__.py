# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>

from . import controllers
from . import models
from . import wizard


def post_init(env):
    companies = env['res.company'].search([('chart_template', '=', 'do')])
    for company in companies:
        Template = env['account.chart.template'].with_company(company)
        print(Template)
        for xml_id, tax_data in Template._get_do_info_account_tax().items():
            tax = Template.ref(xml_id, raise_if_not_found=False)
            print(tax)
            if tax and 'l10n_do_tax_type' in tax_data:
                tax.l10n_do_tax_type = tax_data['l10n_do_tax_type']
                tax.isr_retention_type = tax_data['isr_retention_type']
