from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_do_tax_type = fields.Selection(
        selection=[
            ('itbis', 'ITBIS'),
            ('ritbis', 'ITBIS Withholding'),
            # TODO: investigate Subject to proportionality and ITBIS carried to cost
            #('prop', 'Subject to proportionality'),
            #('itbis_cost', 'ITBIS carried to cost'),
            ('isr', 'ISR Withholding'),
            ('isc', 'Selective Consumption Tax (SCT)'),
            ('other', 'Other taxes'),
            ('tip', 'Legal tip'),
            ('rext', 'Overseas payments (law 253-12)'),
            ('none', 'Non deductible')
        ],
        default="none",
        string="Tax DGII Type",
    )
    isr_retention_type = fields.Selection(
        selection=[
            ('01', 'Rentals'),
            ('02', 'Fees for Services'),
            ('03', 'Other Incomes'),
            ('04', 'Presumed Income'),
            ('05', 'Interest Paid to Legal Entities'),
            ('06', 'Interests Paid to Individuals'),
            ('07', 'Withholding by State Providers'),
            ('08', 'Mobile Games')
        ],
        string="ISR Withholding Type",
    )


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    l10n_do_tax_type = fields.Selection(
        selection=[
            ('itbis', 'ITBIS'),
            ('ritbis', 'ITBIS Withholding'),
            # TODO: investigate Subject to proportionality and ITBIS carried to cost
            #('prop', 'Subject to proportionality'),
            #('itbis_cost', 'ITBIS carried to cost'),
            ('isr', 'ISR Withholding'),
            ('isc', 'Selective Consumption Tax (SCT)'),
            ('other', 'Other taxes'),
            ('tip', 'Legal tip'),
            ('rext', 'Overseas payments (law 253-12)'),
            ('none', 'Non deductible')
        ],
        default="none",
        string="Tax DGII Type",
    )
    isr_retention_type = fields.Selection(
        selection=[
            ('01', 'Rentals'),
            ('02', 'Fees for Services'),
            ('03', 'Other Incomes'),
            ('04', 'Presumed Income'),
            ('05', 'Interest Paid to Legal Entities'),
            ('06', 'Interests Paid to Individuals'),
            ('07', 'Withholding by State Providers'),
            ('08', 'Mobile Games')
        ],
        string="ISR Withholding Type",
    )

    def _get_tax_vals(self, company, tax_template_to_tax):
        self.ensure_one()
        
        vals = super(AccountTaxTemplate, self)._get_tax_vals(company, tax_template_to_tax)
        
        vals.update({
            'isr_retention_type': self.isr_retention_type,
            'l10n_do_tax_type': self.l10n_do_tax_type,
        })
        
        return vals
